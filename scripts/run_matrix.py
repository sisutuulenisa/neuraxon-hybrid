#!/usr/bin/env python3
"""Generate deterministic benchmark run CSV output from a matrix manifest.

Optional: enable local MLflow tracking for the same matrix execution:
- one parent run per invocation
- nested child run per (use_case, variant, seed)
- key metrics + per-row artifacts
- fixed tags: protocol_version, claim_eval_version, git_commit
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, Iterable, List, Optional

BASE_FIELDS = [
    "run_id",
    "ts_utc",
    "trace_id",
    "use_case",
    "variant",
    "seed",
    "status",
    "error_msg",
]
METRIC_FIELDS = [
    "runtime_sec",
    "steps",
    "score_main",
    "drift_recovery_t90",
    "forgetting_delta",
]
UPOW_FIELDS = [
    "worker_count",
    "node_id",
    "throughput_steps_sec",
    "cost_per_1m_steps",
]
FIELDS = BASE_FIELDS + METRIC_FIELDS + UPOW_FIELDS

DEFAULT_MAX_STEPS = 20_000
DEFAULT_MAX_RUNTIME_SEC = 1_800.0
DEFAULT_VARIANT_PROFILE = {
    "adapt": 0.060,
    "momentum": 0.88,
    "noise": 0.018,
    "runtime_per_step_sec": 0.0045,
}
VARIANT_PROFILES: Dict[str, Dict[str, float]] = {
    "neuraxon_full": {"adapt": 0.085, "momentum": 0.93, "noise": 0.010, "runtime_per_step_sec": 0.0042},
    "neuraxon_wfast_only": {"adapt": 0.112, "momentum": 0.78, "noise": 0.020, "runtime_per_step_sec": 0.0038},
    "neuraxon_wslow_only": {"adapt": 0.048, "momentum": 0.96, "noise": 0.009, "runtime_per_step_sec": 0.0046},
    "baseline_classic": {"adapt": 0.033, "momentum": 0.66, "noise": 0.022, "runtime_per_step_sec": 0.0032},
    "baseline_gru_small": {"adapt": 0.058, "momentum": 0.84, "noise": 0.016, "runtime_per_step_sec": 0.0048},
}
DEFAULT_USE_CASE_FLAGS = {
    "difficulty": 1.0,
    "runtime_scale": 1.0,
    "drift_recovery_t90": False,
    "forgetting_delta": False,
}
USE_CASE_FLAGS = {
    "usecase_a_drift": {
        "difficulty": 1.0,
        "runtime_scale": 1.0,
        "drift_recovery_t90": True,
        "forgetting_delta": True,
    },
    "usecase_b_perturbation": {
        "difficulty": 1.15,
        "runtime_scale": 1.18,
        "drift_recovery_t90": False,
        "forgetting_delta": False,
    },
}


def _value_from_item(item: Any, keys: Iterable[str], field_name: str) -> str:
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if value is not None and str(value).strip() != "":
                return str(value)
        raise ValueError(f"Missing identifier for {field_name}: {item}")
    value = str(item).strip()
    if not value:
        raise ValueError(f"Empty value for {field_name}")
    return value


def _normalize_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be a JSON object")

    use_cases_raw = data.get("use_cases", data.get("usecases", data.get("cases", [])))
    variants_raw = data.get("variants", [])
    seeds_raw = data.get("seeds", [])
    worker_counts_raw = data.get("worker_counts", [1])

    if not isinstance(use_cases_raw, list):
        raise ValueError("Manifest key 'use_cases' must be a list")
    if not isinstance(variants_raw, list):
        raise ValueError("Manifest key 'variants' must be a list")
    if not isinstance(seeds_raw, list):
        raise ValueError("Manifest key 'seeds' must be a list")

    use_cases = [
        _value_from_item(item, ("use_case", "name", "id"), "use_case")
        for item in use_cases_raw
    ]
    variants = [
        _value_from_item(item, ("variant", "name", "id"), "variant")
        for item in variants_raw
    ]
    seeds = [
        _value_from_item(item, ("seed", "id", "value"), "seed")
        for item in seeds_raw
    ]

    if not use_cases:
        use_cases = ["default"]
    if not variants:
        raise ValueError("Manifest must contain at least one variant")
    if not seeds:
        raise ValueError("Manifest must contain at least one seed")
    if not isinstance(worker_counts_raw, list):
        raise ValueError("Manifest key 'worker_counts' must be a list")
    if not worker_counts_raw:
        raise ValueError("Manifest key 'worker_counts' must contain at least one worker count")
    worker_counts = [
        str(_coerce_positive_int(item, None, f"worker_counts[{index}]"))
        for index, item in enumerate(worker_counts_raw)
    ]

    budget_raw = data.get("budget", {})
    if budget_raw is None:
        budget_raw = {}
    if not isinstance(budget_raw, dict):
        raise ValueError("Manifest key 'budget' must be an object when provided")

    max_steps = _coerce_positive_int(budget_raw.get("max_steps"), DEFAULT_MAX_STEPS, "budget.max_steps")
    max_runtime_sec = _coerce_positive_float(
        budget_raw.get("max_runtime_sec"),
        DEFAULT_MAX_RUNTIME_SEC,
        "budget.max_runtime_sec",
    )

    return {
        "use_cases": use_cases,
        "variants": variants,
        "seeds": seeds,
        "worker_counts": worker_counts,
        "budget": {"max_steps": max_steps, "max_runtime_sec": max_runtime_sec},
    }


def _coerce_positive_int(value: Any, fallback: int, field_name: str) -> int:
    if value is None:
        return fallback
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer, got: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be > 0, got: {parsed}")
    return parsed


def _coerce_positive_float(value: Any, fallback: float, field_name: str) -> float:
    if value is None:
        return fallback
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive number, got: {value!r}") from exc
    if parsed <= 0.0:
        raise ValueError(f"{field_name} must be > 0, got: {parsed}")
    return parsed


def _sanitize_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "na"


def _default_ts_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def _otel_trace_scope(name: str, attrs: Optional[Dict[str, Any]] = None):
    if not OTEL_ENABLED:
        yield None
        return
    assert OTEL_TRACER is not None
    with OTEL_TRACER.start_as_current_span(name) as span:
        for key, value in (attrs or {}).items():
            span.set_attribute(str(key), str(value))
        yield span


def _trace_id_from_span(span: Optional[Any]) -> str:
    if span is None:
        return uuid.uuid4().hex
    try:
        span_context = span.get_span_context()
        trace_id = getattr(span_context, "trace_id", 0)
        if trace_id:
            return f"{trace_id:032x}"
    except Exception:
        pass
    return uuid.uuid4().hex


def _otel_configure() -> tuple[bool, Any]:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return False, None
    try:
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    except ImportError as exc:
        print(f"OTel requested via OTEL_EXPORTER_OTLP_ENDPOINT={endpoint!r}, but dependencies missing: {exc}")
        return False, None

    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore
        exporter_kwargs = {"endpoint": endpoint}
    except ImportError:  # pragma: no cover
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
            exporter_kwargs = {"endpoint": endpoint}
        except ImportError as exc:
            print(f"OTel requested but OTLP exporter not installed: {exc}")
            return False, None

    service_name = os.getenv("OTEL_SERVICE_NAME", "neuraxon-phase5")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_kwargs)))
    trace.set_tracer_provider(provider)
    return True, trace.get_tracer("neuraxon.phase5.run_matrix")


OTEL_ENABLED = False
OTEL_TRACER = None


def _seed_to_int(seed: str) -> int:
    try:
        return int(seed)
    except ValueError:
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return int(digest[:16], 16)


def _stable_hash_int(parts: Iterable[str]) -> int:
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _fmt_float(value: float, digits: int = 6) -> str:
    return f"{value:.{digits}f}"


def _target_signal(use_case: str, step: int, total_steps: int) -> float:
    if use_case == "usecase_a_drift":
        progress = step / max(1, total_steps - 1)
        if progress < 0.35:
            return 0.20
        if progress < 0.70:
            return 0.82
        return 0.20

    if use_case == "usecase_b_perturbation":
        base = 0.52 + 0.18 * math.sin(step * 0.023) + 0.08 * math.sin(step * 0.007)
        if step % 977 < 22:
            base += 0.22
        if step % 541 < 17:
            base -= 0.18
        return _clamp(base)

    return _clamp(0.50 + 0.15 * math.sin(step * 0.01))


def _simulate_scores(use_case: str, variant: str, seed_int: int, steps: int) -> List[float]:
    profile = VARIANT_PROFILES.get(variant, DEFAULT_VARIANT_PROFILE)
    flags = USE_CASE_FLAGS.get(use_case, DEFAULT_USE_CASE_FLAGS)
    rng = random.Random(_stable_hash_int((use_case, variant, str(seed_int))))

    state = 0.50
    velocity = 0.0
    scores: List[float] = []

    for step in range(steps):
        target = _target_signal(use_case, step, steps)
        error = target - state
        velocity = profile["momentum"] * velocity + profile["adapt"] * error
        noise = (rng.random() - 0.5) * profile["noise"]
        state = _clamp(state + velocity + noise)
        score = max(0.0, 1.0 - flags["difficulty"] * abs(target - state))
        scores.append(score)

    return scores


def _drift_recovery_t90(scores: List[float]) -> float:
    total_steps = len(scores)
    phase_1_end = int(total_steps * 0.35)
    phase_2_end = int(total_steps * 0.70)
    if phase_1_end < 10 or phase_2_end <= phase_1_end:
        return 0.0

    start_score = scores[phase_1_end]
    stable_window = max(60, min(1500, (phase_2_end - phase_1_end) // 2))
    stable_score = fmean(scores[phase_2_end - stable_window : phase_2_end])
    if stable_score <= start_score:
        return 0.0

    threshold = start_score + 0.90 * (stable_score - start_score)
    hold_window = max(10, min(120, (phase_2_end - phase_1_end) // 40 or 10))

    for idx in range(phase_1_end, phase_2_end):
        right = idx + hold_window
        if right > phase_2_end:
            break
        if min(scores[idx:right]) >= threshold:
            return float(idx - phase_1_end)

    return float(phase_2_end - phase_1_end)


def _forgetting_delta(scores: List[float]) -> float:
    total_steps = len(scores)
    phase_1_end = int(total_steps * 0.35)
    phase_3_start = int(total_steps * 0.70)
    if phase_1_end < 10 or phase_3_start >= total_steps:
        return 0.0

    compare_window = max(40, min(1500, total_steps // 5))
    phase_1_ref = fmean(scores[max(0, phase_1_end - compare_window) : phase_1_end])
    phase_3_ref = fmean(scores[max(phase_3_start, total_steps - compare_window) : total_steps])
    return phase_1_ref - phase_3_ref


def _build_metrics(
    use_case: str,
    variant: str,
    seed: str,
    budget: Dict[str, float],
    worker_count: int,
    seed_int: int,
) -> Dict[str, str]:
    profile = VARIANT_PROFILES.get(variant, DEFAULT_VARIANT_PROFILE)
    flags = USE_CASE_FLAGS.get(use_case, DEFAULT_USE_CASE_FLAGS)

    jitter = 1.0 + (((seed_int % 19) - 9) / 500.0)
    per_step_sec = profile["runtime_per_step_sec"] * flags["runtime_scale"] * jitter
    fixed_overhead_sec = 0.25

    steps_by_budget = max(100, int((budget["max_runtime_sec"] - fixed_overhead_sec) / per_step_sec))
    steps = max(100, min(int(budget["max_steps"]), steps_by_budget))
    scores = _simulate_scores(use_case, variant, seed_int, steps)

    score_slice_start = max(0, steps // 2)
    score_main = fmean(scores[score_slice_start:]) if scores else 0.0
    runtime_single_worker_sec = fixed_overhead_sec + steps * per_step_sec
    scale = 1.0 + 0.35 * max(1, worker_count - 1)
    runtime_sec = runtime_single_worker_sec / scale
    throughput_steps_sec = steps / runtime_sec if runtime_sec > 0 else 0.0

    base_cost_per_step = 0.00018
    cost_per_1m_steps = base_cost_per_step * runtime_sec * worker_count * 1_000_000

    drift_recovery_t90 = ""
    forgetting_delta = ""
    if bool(flags.get("drift_recovery_t90")):
        drift_recovery_t90 = _fmt_float(_drift_recovery_t90(scores), digits=2)
    if bool(flags.get("forgetting_delta")):
        forgetting_delta = _fmt_float(_forgetting_delta(scores), digits=6)

    node_bucket = _stable_hash_int((use_case, variant, seed)) % 7

    return {
        "runtime_sec": _fmt_float(runtime_sec, digits=4),
        "steps": str(steps),
        "score_main": _fmt_float(score_main, digits=6),
        "drift_recovery_t90": drift_recovery_t90,
        "forgetting_delta": forgetting_delta,
        "worker_count": str(worker_count),
        "node_id": f"node_{node_bucket + 1}",
        "throughput_steps_sec": _fmt_float(throughput_steps_sec, digits=6),
        "cost_per_1m_steps": _fmt_float(cost_per_1m_steps, digits=6),
    }


def _empty_metrics() -> Dict[str, str]:
    return {field: "" for field in METRIC_FIELDS}


def build_rows(
    use_cases: List[str],
    variants: List[str],
    seeds: List[str],
    worker_counts: List[str],
    budget: Dict[str, float],
    ts_utc: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for idx, (use_case, variant, seed, worker_count) in enumerate(
        product(use_cases, variants, seeds, worker_counts),
        start=1,
    ):
        run_id = "run-{idx:04d}-{use_case}-{variant}-{seed}-w{worker_count}".format(
            idx=idx,
            use_case=_sanitize_fragment(use_case),
            variant=_sanitize_fragment(variant),
            seed=_sanitize_fragment(seed),
            worker_count=_sanitize_fragment(worker_count),
        )

        status = "ok"
        error_msg = ""
        metrics = _empty_metrics()
        trace_id = ""
        with _otel_trace_scope(
            "run_matrix_row",
            {
                "run_id": run_id,
                "use_case": use_case,
                "variant": variant,
                "seed": seed,
                "worker_count": worker_count,
            },
        ) as span:
            trace_id = _trace_id_from_span(span)
            try:
                if span is not None:
                    span.set_attribute("run.status", "ok")
                metrics = _build_metrics(
                    use_case=use_case,
                    variant=variant,
                    seed=seed,
                    budget=budget,
                    worker_count=int(worker_count),
                    seed_int=_seed_to_int(seed),
                )
            except Exception as exc:  # pragma: no cover - defensive path
                status = "error"
                error_msg = f"{type(exc).__name__}: {exc}"
                if span is not None:
                    span.set_attribute("run.status", "error")
                    span.record_exception(exc)

        rows.append(
            {
                "run_id": run_id,
                "ts_utc": ts_utc,
                "trace_id": trace_id,
                "use_case": use_case,
                "variant": variant,
                "seed": seed,
                "status": status,
                "error_msg": error_msg,
                **metrics,
            }
        )
    return rows
def write_csv(out_path: Path, rows: List[Dict[str, str]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _import_mlflow():
    try:
        import mlflow

        return mlflow
    except ImportError as exc:  # pragma: no cover - clear operator guidance
        raise SystemExit(
            "MLflow tracking requested, but 'mlflow' is not installed. "
            "Install dependency first (recommended: mlflow-skinny)."
        ) from exc


def _git_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit = proc.stdout.strip()
        return commit or "unknown"
    except Exception:
        return "unknown"


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _to_metric(value: str) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _track_matrix_mlflow(
    rows: List[Dict[str, str]],
    manifest_path: Path,
    out_path: Path,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    mlflow = _import_mlflow()

    repo_root = Path(__file__).resolve().parent.parent
    tracking_dir = Path(args.mlflow_tracking_dir).resolve()
    output_root = Path(args.mlflow_output_dir).resolve()
    tracking_dir.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_output_dir = output_root / f"matrix_{stamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    git_commit = args.git_commit or _git_commit(repo_root)
    common_tags = {
        "protocol_version": args.protocol_version,
        "claim_eval_version": args.claim_eval_version,
        "git_commit": git_commit,
    }

    mlflow.set_tracking_uri(tracking_dir.as_uri())
    mlflow.set_experiment(args.mlflow_experiment_name)

    child_records: List[Dict[str, Any]] = []

    run_name = args.mlflow_run_name or f"matrix_parent_{manifest_path.stem}_{stamp}"

    with mlflow.start_run(run_name=run_name) as parent_run:
        mlflow.set_tags(
            {
                **common_tags,
                "run_role": "parent",
                "manifest": manifest_path.name,
                "out_csv": out_path.name,
            }
        )
        mlflow.log_params(
            {
                "manifest_path": str(manifest_path.resolve()),
                "out_csv_path": str(out_path.resolve()),
                "row_count": len(rows),
                "tracking_dir": str(tracking_dir),
                "output_dir": str(run_output_dir),
                "otel_enabled": OTEL_ENABLED,
            }
        )

        if manifest_path.exists():
            mlflow.log_artifact(str(manifest_path.resolve()), artifact_path="inputs")
        if out_path.exists():
            mlflow.log_artifact(str(out_path.resolve()), artifact_path="outputs")

        for index, row in enumerate(rows, start=1):
            child_payload = {
                "ts_utc": _default_ts_utc(),
                "row_index": index,
                "row": row,
                "note": "matrix child run artifact",
            }
            child_artifact_name = (
                f"child_{index:04d}_{_sanitize_fragment(row['use_case'])}_"
                f"{_sanitize_fragment(row['variant'])}_{_sanitize_fragment(str(row['seed']))}.json"
            )
            child_artifact_path = run_output_dir / child_artifact_name
            _write_json(child_artifact_path, child_payload)

            child_run_name = (
                f"{_sanitize_fragment(row['use_case'])}__"
                f"{_sanitize_fragment(row['variant'])}__seed_{_sanitize_fragment(str(row['seed']))}"
            )
            with mlflow.start_run(run_name=child_run_name, nested=True) as child_run:
                mlflow.set_tags(
                    {
                        **common_tags,
                        "run_role": "child",
                        "use_case": row["use_case"],
                        "variant": row["variant"],
                        "status": row["status"],
                    }
                )
                mlflow.log_params(
                    {
                        "seed": row["seed"],
                        "run_id": row["run_id"],
                        "trace_id": row["trace_id"],
                        "row_index": index,
                    }
                )

                metrics: Dict[str, float] = {}
                for field in METRIC_FIELDS:
                    value = _to_metric(row.get(field, ""))
                    if value is not None:
                        metrics[field] = value
                if metrics:
                    mlflow.log_metrics(metrics)

                if row.get("status") != "ok" and row.get("error_msg"):
                    mlflow.log_param("error_msg", row["error_msg"])

                mlflow.log_artifact(str(child_artifact_path), artifact_path="row")

                child_records.append(
                    {
                        "row_index": index,
                        "run_id": child_run.info.run_id,
                        "artifact_uri": child_run.info.artifact_uri,
                        "use_case": row["use_case"],
                        "variant": row["variant"],
                        "seed": row["seed"],
                        "status": row["status"],
                        "metrics": metrics,
                        "source_artifact": str(child_artifact_path),
                    }
                )

        ok_rows = [row for row in rows if row.get("status") == "ok"]
        parent_metrics: Dict[str, float] = {
            "ok_runs": float(len(ok_rows)),
            "error_runs": float(len(rows) - len(ok_rows)),
        }
        if ok_rows:
            for field in METRIC_FIELDS:
                values = [_to_metric(row.get(field, "")) for row in ok_rows]
                usable = [value for value in values if value is not None]
                if usable:
                    parent_metrics[f"avg_{field}"] = fmean(usable)

        mlflow.log_metrics(parent_metrics)

        parent_summary = {
            "ts_utc": _default_ts_utc(),
            "experiment_name": args.mlflow_experiment_name,
            "tracking_dir": str(tracking_dir),
            "run_output_dir": str(run_output_dir),
            "parent_run_id": parent_run.info.run_id,
            "parent_artifact_uri": parent_run.info.artifact_uri,
            "tags": common_tags,
            "inputs": {
                "manifest_path": str(manifest_path.resolve()),
                "out_csv_path": str(out_path.resolve()),
                "row_count": len(rows),
            },
            "aggregate": {k: round(v, 6) for k, v in parent_metrics.items()},
            "children": child_records,
        }

        parent_summary_path = run_output_dir / "parent_summary.json"
        parent_summary_txt = run_output_dir / "parent_summary.txt"
        _write_json(parent_summary_path, parent_summary)
        parent_summary_txt.write_text(
            "\n".join(
                [
                    "Phase 5 MLflow matrix summary",
                    f"parent_run_id={parent_run.info.run_id}",
                    f"tracking_dir={tracking_dir}",
                    f"run_output_dir={run_output_dir}",
                    f"rows_total={len(rows)}",
                    f"rows_ok={len(ok_rows)}",
                    f"rows_error={len(rows) - len(ok_rows)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        mlflow.log_artifact(str(parent_summary_path), artifact_path="summary")
        mlflow.log_artifact(str(parent_summary_txt), artifact_path="summary")

    latest_payload = {
        "ts_utc": _default_ts_utc(),
        "tracking_dir": str(tracking_dir),
        "output_dir": str(run_output_dir),
        "parent_summary": str(run_output_dir / "parent_summary.json"),
    }
    latest_path = output_root / "latest_matrix_run.json"
    _write_json(latest_path, latest_payload)

    return {
        "tracking_dir": str(tracking_dir),
        "output_dir": str(run_output_dir),
        "latest": str(latest_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate run matrix CSV from JSON manifest",
        allow_abbrev=False,
    )
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--out", required=True, help="Path to output CSV")
    parser.add_argument(
        "--ts-utc",
        default=None,
        help="Optional fixed ISO UTC timestamp for deterministic output (e.g. 2026-02-26T00:00:00Z)",
    )
    parser.add_argument(
        "--enable-mlflow",
        "--mlflow-track",
        dest="enable_mlflow",
        action="store_true",
        help="Enable local MLflow tracking: one parent run + child run per matrix row",
    )
    parser.add_argument(
        "--mlflow-tracking-dir",
        default="benchmarks/results/mlflow/matrix/mlruns",
        help="Directory used as MLflow file-store root",
    )
    parser.add_argument(
        "--mlflow-output-dir",
        default="benchmarks/results/mlflow/matrix/outputs",
        help="Directory for reproducible MLflow run summaries",
    )
    parser.add_argument(
        "--mlflow-experiment-name",
        default="phase5_mlflow_matrix",
        help="MLflow experiment name",
    )
    parser.add_argument(
        "--mlflow-run-name",
        default=None,
        help="Optional parent run name override",
    )
    parser.add_argument(
        "--worker-counts",
        default=None,
        help="Optional comma-separated worker counts (override manifest worker_counts)",
    )
    parser.add_argument("--protocol-version", default="phase5.frontier.v1")
    parser.add_argument("--claim-eval-version", default="CLAIM_EVAL_002")
    parser.add_argument(
        "--git-commit",
        default=None,
        help="Optional override for git_commit tag (default: auto-detect)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    global OTEL_ENABLED, OTEL_TRACER
    OTEL_ENABLED, OTEL_TRACER = _otel_configure()

    manifest_path = Path(args.manifest)
    out_path = Path(args.out)
    ts_utc = args.ts_utc if args.ts_utc else _default_ts_utc()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    normalized = _normalize_manifest(data)
    worker_counts = normalized["worker_counts"]
    if args.worker_counts:
        worker_counts = [token.strip() for token in args.worker_counts.split(",") if token.strip()]
        if not worker_counts:
            raise ValueError("--worker-counts provided but no valid values parsed")

    rows = build_rows(
        normalized["use_cases"],
        normalized["variants"],
        normalized["seeds"],
        worker_counts=worker_counts,
        budget=normalized["budget"],
        ts_utc=ts_utc,
    )
    write_csv(out_path, rows)

    ok_count = sum(1 for row in rows if row.get("status") == "ok")
    print(f"Wrote {len(rows)} rows to {out_path} ({ok_count} ok, {len(rows) - ok_count} error)")

    if args.enable_mlflow:
        tracking_info = _track_matrix_mlflow(
            rows=rows,
            manifest_path=manifest_path,
            out_path=out_path,
            args=args,
        )
        print("MLflow matrix tracking complete")
        print(f"tracking_dir={tracking_info['tracking_dir']}")
        print(f"output_dir={tracking_info['output_dir']}")
        print(f"latest={tracking_info['latest']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
