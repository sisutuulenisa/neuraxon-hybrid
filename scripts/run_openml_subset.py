#!/usr/bin/env python3
"""Bounded OpenML mini-run with deterministic drift injection and ADWIN signals.

This script executes a compact calibration run on a fixed subset of OpenML tasks.
It is intentionally bounded (task count + sample budget) and outputs:
- run-level CSV
- machine-readable JSON summary
- compact markdown report with protocol proxy mapping
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RunConfig:
    suite: str
    task_ids: List[int]
    variants: List[str]
    seed: int
    max_samples_per_task: int
    warm_start_samples: int
    accuracy_window: int
    recovery_hold_steps: int
    drift_start_frac: float
    drift_end_frac: float
    collapse_threshold_frac: float
    adwin_delta: float
    adwin_clock: int
    adwin_max_buckets: int
    adwin_min_window_length: int
    adwin_grace_period: int


def _coerce_int(value: Any, *, field: str, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer, got {value!r}") from exc
    if parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}, got {parsed}")
    return parsed


def _coerce_float(value: Any, *, field: str, minimum: float, maximum: float | None = None) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a float, got {value!r}") from exc
    if parsed < minimum:
        raise ValueError(f"{field} must be >= {minimum}, got {parsed}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{field} must be <= {maximum}, got {parsed}")
    return parsed


def _load_manifest(path: Path) -> RunConfig:
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Manifest root must be an object")

    budget = data.get("budget", {}) or {}
    drift = data.get("drift", {}) or {}
    adwin = data.get("adwin", {}) or {}

    task_ids_raw = data.get("task_ids", [])
    if not isinstance(task_ids_raw, list) or len(task_ids_raw) != 3:
        raise ValueError("Manifest must contain exactly 3 task_ids")

    task_ids = [_coerce_int(t, field="task_ids[]", minimum=1) for t in task_ids_raw]

    variants_raw = data.get("variants", ["neuraxon_full_proxy", "baseline_classic"])
    if not isinstance(variants_raw, list) or not variants_raw:
        raise ValueError("Manifest variants must be a non-empty list")
    variants = [str(v).strip() for v in variants_raw if str(v).strip()]
    if not variants:
        raise ValueError("Manifest variants must contain at least one non-empty value")

    cfg = RunConfig(
        suite=str(data.get("suite", "OpenML-CC18")),
        task_ids=task_ids,
        variants=variants,
        seed=_coerce_int(data.get("seed", 20260227), field="seed", minimum=1),
        max_samples_per_task=_coerce_int(budget.get("max_samples_per_task", 2500), field="budget.max_samples_per_task", minimum=200),
        warm_start_samples=_coerce_int(budget.get("warm_start_samples", 120), field="budget.warm_start_samples", minimum=20),
        accuracy_window=_coerce_int(budget.get("accuracy_window", 128), field="budget.accuracy_window", minimum=20),
        recovery_hold_steps=_coerce_int(budget.get("recovery_hold_steps", 32), field="budget.recovery_hold_steps", minimum=5),
        drift_start_frac=_coerce_float(drift.get("start_frac", 0.50), field="drift.start_frac", minimum=0.10, maximum=0.80),
        drift_end_frac=_coerce_float(drift.get("end_frac", 0.75), field="drift.end_frac", minimum=0.20, maximum=0.95),
        collapse_threshold_frac=_coerce_float(
            drift.get("collapse_threshold_frac", 0.80),
            field="drift.collapse_threshold_frac",
            minimum=0.10,
            maximum=1.0,
        ),
        adwin_delta=_coerce_float(adwin.get("delta", 0.002), field="adwin.delta", minimum=1e-6, maximum=0.5),
        adwin_clock=_coerce_int(adwin.get("clock", 32), field="adwin.clock", minimum=1),
        adwin_max_buckets=_coerce_int(adwin.get("max_buckets", 5), field="adwin.max_buckets", minimum=1),
        adwin_min_window_length=_coerce_int(
            adwin.get("min_window_length", 5), field="adwin.min_window_length", minimum=1
        ),
        adwin_grace_period=_coerce_int(adwin.get("grace_period", 10), field="adwin.grace_period", minimum=1),
    )

    if cfg.drift_end_frac <= cfg.drift_start_frac:
        raise ValueError("drift.end_frac must be greater than drift.start_frac")

    if cfg.warm_start_samples >= cfg.max_samples_per_task:
        raise ValueError("budget.warm_start_samples must be lower than budget.max_samples_per_task")

    return cfg


def _encode_frame(df: "pd.DataFrame") -> "np.ndarray":
    import numpy as np
    import pandas as pd

    parts: List[np.ndarray] = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            numeric = pd.to_numeric(series, errors="coerce")
            if numeric.isna().all():
                values = np.zeros(len(series), dtype="float64")
            else:
                median = float(numeric.median())
                values = numeric.fillna(median).to_numpy(dtype="float64")
        else:
            text = series.fillna("<NA>").astype(str)
            codes, _ = pd.factorize(text, sort=True)
            values = codes.astype("float64")
        parts.append(values.reshape(-1, 1))

    if not parts:
        return np.zeros((len(df), 1), dtype="float64")

    return np.hstack(parts)


def _label_drift_map(classes: Sequence[Any]) -> Dict[Any, Any]:
    ordered = list(classes)
    if len(ordered) < 2:
        return {ordered[0]: ordered[0]} if ordered else {}

    if len(ordered) == 2:
        return {ordered[0]: ordered[1], ordered[1]: ordered[0]}

    return {ordered[i]: ordered[(i + 1) % len(ordered)] for i in range(len(ordered))}


def _make_model(variant: str, seed: int):
    from sklearn.linear_model import SGDClassifier

    if variant == "neuraxon_full_proxy":
        return SGDClassifier(
            loss="log_loss",
            alpha=1e-4,
            learning_rate="optimal",
            random_state=seed,
            average=True,
        )

    if variant == "baseline_classic":
        return SGDClassifier(
            loss="hinge",
            alpha=8e-4,
            learning_rate="optimal",
            random_state=seed,
            average=False,
        )

    raise ValueError(f"Unsupported variant: {variant}")


def _safe_mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def _safe_var(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return float(sum((x - mean) ** 2 for x in values) / len(values))


def _format_float(value: float | None, digits: int = 6) -> str:
    if value is None or isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return ""
    return f"{value:.{digits}f}"


def _get_stream_indices(task: "openml.tasks.OpenMLSupervisedTask", max_samples: int) -> List[int]:
    import numpy as np

    train_idx, test_idx = task.get_train_test_split_indices(repeat=0, fold=0, sample=0)
    ordered = np.concatenate([np.asarray(train_idx, dtype=int), np.asarray(test_idx, dtype=int)])
    if len(ordered) > max_samples:
        ordered = ordered[:max_samples]
    return ordered.tolist()


def _run_single(task_id: int, variant: str, cfg: RunConfig) -> Dict[str, Any]:
    import numpy as np
    import openml
    from river import drift

    t0 = time.perf_counter()

    task = openml.tasks.get_task(task_id)
    dataset = task.get_dataset()
    X_df, y_raw = task.get_X_and_y(dataset_format="dataframe")

    X_all = _encode_frame(X_df)
    y_all = np.asarray(y_raw)

    stream_idx = _get_stream_indices(task, cfg.max_samples_per_task)
    X_stream = X_all[stream_idx]
    y_stream = y_all[stream_idx]

    classes = np.unique(y_stream)
    if len(classes) < 2:
        raise ValueError(f"Task {task_id} has <2 classes in bounded stream")

    drift_map = _label_drift_map(classes)
    n = len(stream_idx)
    drift_start = int(n * cfg.drift_start_frac)
    drift_end = int(n * cfg.drift_end_frac)

    y_observed = y_stream.copy()
    for idx in range(drift_start, drift_end):
        y_observed[idx] = drift_map[y_observed[idx]]

    model = _make_model(variant=variant, seed=cfg.seed)

    adwin = drift.ADWIN(
        delta=cfg.adwin_delta,
        clock=cfg.adwin_clock,
        max_buckets=cfg.adwin_max_buckets,
        min_window_length=cfg.adwin_min_window_length,
        grace_period=cfg.adwin_grace_period,
    )

    warm = min(cfg.warm_start_samples, n - 1)
    for i in range(warm):
        if i == 0:
            model.partial_fit(X_stream[i : i + 1], [y_observed[i]], classes=classes)
        else:
            model.partial_fit(X_stream[i : i + 1], [y_observed[i]])

    correct_flags: List[int] = []
    rolling_acc_series: List[tuple[int, float]] = []
    recent = deque(maxlen=cfg.accuracy_window)
    drift_events: List[int] = []

    for i in range(warm, n):
        pred = model.predict(X_stream[i : i + 1])[0]
        correct = int(pred == y_observed[i])
        correct_flags.append(correct)

        recent.append(correct)
        rolling_acc = sum(recent) / len(recent)
        rolling_acc_series.append((i, rolling_acc))

        adwin.update(float(1 - correct))
        if adwin.drift_detected:
            drift_events.append(i)

        model.partial_fit(X_stream[i : i + 1], [y_observed[i]])

    pre_values = [acc for step, acc in rolling_acc_series if step < drift_start]
    drift_values = [acc for step, acc in rolling_acc_series if drift_start <= step < drift_end]
    recovery_values = [acc for step, acc in rolling_acc_series if step >= drift_end]

    pre_acc = _safe_mean(pre_values)
    drift_acc = _safe_mean(drift_values)
    recovery_acc = _safe_mean(recovery_values)
    overall_acc = _safe_mean([float(v) for v in correct_flags])

    collapse_rate = None
    recovery95_steps = None
    stability_var = _safe_var(recovery_values)

    if pre_acc is not None and drift_values:
        collapse_threshold = pre_acc * cfg.collapse_threshold_frac
        collapse_rate = float(sum(1 for value in drift_values if value < collapse_threshold) / len(drift_values))

    if pre_acc is not None and rolling_acc_series:
        threshold = pre_acc * 0.95
        hold = max(1, cfg.recovery_hold_steps)
        after_shift = [(step, acc) for step, acc in rolling_acc_series if step >= drift_start]
        for idx in range(0, max(0, len(after_shift) - hold + 1)):
            chunk = after_shift[idx : idx + hold]
            if all(acc >= threshold for _, acc in chunk):
                recovery95_steps = chunk[0][0] - drift_start
                break

    elapsed = time.perf_counter() - t0

    return {
        "task_id": task_id,
        "dataset_id": task.dataset_id,
        "dataset_name": dataset.name,
        "n_features": int(X_stream.shape[1]),
        "n_samples": int(n),
        "n_classes": int(len(classes)),
        "variant": variant,
        "status": "ok",
        "error_msg": "",
        "accuracy_overall": overall_acc,
        "accuracy_pre_drift": pre_acc,
        "accuracy_drift": drift_acc,
        "accuracy_recovery": recovery_acc,
        "collapse_rate_proxy": collapse_rate,
        "recovery95_steps_proxy": recovery95_steps,
        "stability_var_proxy": stability_var,
        "adwin_event_count": len(drift_events),
        "adwin_first_event_step": drift_events[0] if drift_events else None,
        "drift_start_step": drift_start,
        "drift_end_step": drift_end,
        "runtime_sec": elapsed,
        "adwin_params": {
            "delta": cfg.adwin_delta,
            "clock": cfg.adwin_clock,
            "max_buckets": cfg.adwin_max_buckets,
            "min_window_length": cfg.adwin_min_window_length,
            "grace_period": cfg.adwin_grace_period,
        },
    }


def _run_single_safe(task_id: int, variant: str, cfg: RunConfig) -> Dict[str, Any]:
    try:
        return _run_single(task_id=task_id, variant=variant, cfg=cfg)
    except Exception as exc:  # pragma: no cover - defensive path
        return {
            "task_id": task_id,
            "dataset_id": "",
            "dataset_name": "",
            "n_features": "",
            "n_samples": "",
            "n_classes": "",
            "variant": variant,
            "status": "error",
            "error_msg": f"{type(exc).__name__}: {exc}",
            "accuracy_overall": None,
            "accuracy_pre_drift": None,
            "accuracy_drift": None,
            "accuracy_recovery": None,
            "collapse_rate_proxy": None,
            "recovery95_steps_proxy": None,
            "stability_var_proxy": None,
            "adwin_event_count": None,
            "adwin_first_event_step": None,
            "drift_start_step": None,
            "drift_end_step": None,
            "runtime_sec": None,
            "adwin_params": {
                "delta": cfg.adwin_delta,
                "clock": cfg.adwin_clock,
                "max_buckets": cfg.adwin_max_buckets,
                "min_window_length": cfg.adwin_min_window_length,
                "grace_period": cfg.adwin_grace_period,
            },
        }


def _rows_to_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "task_id",
        "dataset_id",
        "dataset_name",
        "variant",
        "status",
        "error_msg",
        "n_samples",
        "n_features",
        "n_classes",
        "drift_start_step",
        "drift_end_step",
        "accuracy_overall",
        "accuracy_pre_drift",
        "accuracy_drift",
        "accuracy_recovery",
        "collapse_rate_proxy",
        "recovery95_steps_proxy",
        "stability_var_proxy",
        "adwin_event_count",
        "adwin_first_event_step",
        "runtime_sec",
        "adwin_params",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "accuracy_overall": _format_float(row.get("accuracy_overall")),
                    "accuracy_pre_drift": _format_float(row.get("accuracy_pre_drift")),
                    "accuracy_drift": _format_float(row.get("accuracy_drift")),
                    "accuracy_recovery": _format_float(row.get("accuracy_recovery")),
                    "collapse_rate_proxy": _format_float(row.get("collapse_rate_proxy")),
                    "recovery95_steps_proxy": ""
                    if row.get("recovery95_steps_proxy") is None
                    else str(int(row.get("recovery95_steps_proxy"))),
                    "stability_var_proxy": _format_float(row.get("stability_var_proxy")),
                    "runtime_sec": _format_float(row.get("runtime_sec"), digits=4),
                    "adwin_params": json.dumps(row.get("adwin_params", {}), sort_keys=True),
                }
            )


def _build_summary(rows: List[Dict[str, Any]], cfg: RunConfig, manifest_path: Path) -> Dict[str, Any]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(int(row["task_id"]), []).append(row)

    per_task: List[Dict[str, Any]] = []
    for task_id in cfg.task_ids:
        task_rows = grouped.get(task_id, [])
        ok_rows = [r for r in task_rows if r.get("status") == "ok"]

        best_overall = None
        best_recovery = None

        if ok_rows:
            best_overall = max(ok_rows, key=lambda r: (r.get("accuracy_overall") or -1.0, -(r.get("runtime_sec") or 1e9)))
            best_recovery = min(
                ok_rows,
                key=lambda r: (
                    r.get("recovery95_steps_proxy") if r.get("recovery95_steps_proxy") is not None else 10**9,
                    -(r.get("accuracy_recovery") or -1.0),
                ),
            )

        per_task.append(
            {
                "task_id": task_id,
                "dataset_name": ok_rows[0]["dataset_name"] if ok_rows else "",
                "rows": ok_rows,
                "best_variant_by_accuracy": best_overall.get("variant") if best_overall else None,
                "best_variant_by_recovery": best_recovery.get("variant") if best_recovery else None,
            }
        )

    return {
        "generated_at": _utc_now_iso(),
        "manifest_path": str(manifest_path),
        "config": {
            "suite": cfg.suite,
            "task_ids": cfg.task_ids,
            "variants": cfg.variants,
            "seed": cfg.seed,
            "budget": {
                "max_samples_per_task": cfg.max_samples_per_task,
                "warm_start_samples": cfg.warm_start_samples,
                "accuracy_window": cfg.accuracy_window,
                "recovery_hold_steps": cfg.recovery_hold_steps,
            },
            "drift": {
                "mode": "deterministic_label_permutation_D1_D2_D1",
                "start_frac": cfg.drift_start_frac,
                "end_frac": cfg.drift_end_frac,
                "collapse_threshold_frac": cfg.collapse_threshold_frac,
            },
            "adwin": {
                "delta": cfg.adwin_delta,
                "clock": cfg.adwin_clock,
                "max_buckets": cfg.adwin_max_buckets,
                "min_window_length": cfg.adwin_min_window_length,
                "grace_period": cfg.adwin_grace_period,
            },
        },
        "rows": rows,
        "task_summary": per_task,
    }


def _write_markdown_report(path: Path, summary: Dict[str, Any]) -> None:
    cfg = summary["config"]
    rows = summary["rows"]

    lines: List[str] = []
    lines.append("# OpenML drift mini-run report (bounded)")
    lines.append("")
    lines.append(f"- Generated at: `{summary['generated_at']}`")
    lines.append(f"- Suite: `{cfg['suite']}`")
    lines.append(f"- Task IDs: `{', '.join(str(t) for t in cfg['task_ids'])}`")
    lines.append(f"- Variants: `{', '.join(cfg['variants'])}`")
    lines.append(
        "- Budget: max_samples_per_task={max_samples_per_task}, warm_start_samples={warm_start_samples}, "
        "accuracy_window={accuracy_window}, recovery_hold_steps={recovery_hold_steps}".format(**cfg["budget"])
    )
    lines.append(
        "- Drift setup: mode={mode}, start_frac={start_frac}, end_frac={end_frac}, collapse_threshold_frac={collapse_threshold_frac}".format(
            **cfg["drift"]
        )
    )
    lines.append(
        "- ADWIN params: delta={delta}, clock={clock}, max_buckets={max_buckets}, min_window_length={min_window_length}, grace_period={grace_period}".format(
            **cfg["adwin"]
        )
    )
    lines.append("")
    lines.append("## Protocol mapping (proxy) ")
    lines.append("")
    lines.append("| Protocol field | Proxy in this mini-run | Definitie |")
    lines.append("|---|---|---|")
    lines.append("| `collapse_rate` | `collapse_rate_proxy` | % rolling-accuracy punten tijdens driftfase onder `collapse_threshold_frac * pre_drift_accuracy`. |")
    lines.append("| `recovery95_steps` | `recovery95_steps_proxy` | Aantal stappen vanaf drift-start tot rolling accuracy >= 95% van pre-drift voor `recovery_hold_steps` opeenvolgende punten. |")
    lines.append("| `stability_var` | `stability_var_proxy` | Variantie van rolling accuracy in recoverysegment (`D2->D1`). |")
    lines.append("| `sigma_branching` | n/a (niet direct meetbaar) | Niet geschat in deze bounded setup; ADWIN-eventdichtheid is enkel kwalitatief signaal. |")
    lines.append("")
    lines.append("## Run rows")
    lines.append("")
    lines.append("| task_id | dataset | variant | status | acc_pre | acc_drift | acc_recovery | collapse_rate_proxy | recovery95_steps_proxy | adwin_events |")
    lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|")

    for row in rows:
        lines.append(
            "| {task_id} | {dataset_name} | {variant} | {status} | {acc_pre} | {acc_drift} | {acc_rec} | {collapse} | {r95} | {adwin} |".format(
                task_id=row.get("task_id"),
                dataset_name=row.get("dataset_name") or "-",
                variant=row.get("variant") or "-",
                status=row.get("status") or "-",
                acc_pre=_format_float(row.get("accuracy_pre_drift"), 4) or "-",
                acc_drift=_format_float(row.get("accuracy_drift"), 4) or "-",
                acc_rec=_format_float(row.get("accuracy_recovery"), 4) or "-",
                collapse=_format_float(row.get("collapse_rate_proxy"), 4) or "-",
                r95=("-" if row.get("recovery95_steps_proxy") is None else str(int(row.get("recovery95_steps_proxy")))),
                adwin=("-" if row.get("adwin_event_count") is None else str(row.get("adwin_event_count"))),
            )
        )

    lines.append("")
    lines.append("## Compacte interpretatie")
    lines.append("")
    lines.append("- Dit is een **bounded externe kalibratie** (3 taken, beperkte samplebudgetten), geen brede suite-evaluatie.")
    lines.append("- ADWIN-events tonen detecteerbare shifts in de online errorstroom, maar zijn geen op zichzelf staand claim-PASS bewijs.")
    lines.append("- Proxies vullen protocolgaten richting collapse/recovery-signalen met expliciete detectorinstellingen.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded OpenML mini-calibration with ADWIN drift signals")
    parser.add_argument("--manifest", required=True, help="Path to OpenML mini-run manifest JSON")
    parser.add_argument("--out-dir", required=True, help="Output directory for CSV/JSON/report artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    out_dir = Path(args.out_dir)

    cfg = _load_manifest(manifest_path)

    rows: List[Dict[str, Any]] = []
    for task_id in cfg.task_ids:
        for variant in cfg.variants:
            rows.append(_run_single_safe(task_id=task_id, variant=variant, cfg=cfg))

    summary = _build_summary(rows=rows, cfg=cfg, manifest_path=manifest_path)

    out_dir.mkdir(parents=True, exist_ok=True)
    _rows_to_csv(out_dir / "openml_runs.csv", rows)
    (out_dir / "openml_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown_report(out_dir / "openml_report.md", summary)

    ok_count = sum(1 for row in rows if row.get("status") == "ok")
    print(f"Wrote {len(rows)} rows ({ok_count} ok) to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
