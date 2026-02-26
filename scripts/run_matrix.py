#!/usr/bin/env python3
"""Generate deterministic benchmark run CSV output from a matrix manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, Iterable, List

BASE_FIELDS = [
    "run_id",
    "ts_utc",
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
FIELDS = BASE_FIELDS + METRIC_FIELDS

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


def _build_metrics(use_case: str, variant: str, seed: str, budget: Dict[str, float]) -> Dict[str, str]:
    profile = VARIANT_PROFILES.get(variant, DEFAULT_VARIANT_PROFILE)
    flags = USE_CASE_FLAGS.get(use_case, DEFAULT_USE_CASE_FLAGS)
    seed_int = _seed_to_int(seed)

    jitter = 1.0 + (((seed_int % 19) - 9) / 500.0)
    per_step_sec = profile["runtime_per_step_sec"] * flags["runtime_scale"] * jitter
    fixed_overhead_sec = 0.25

    steps_by_budget = max(100, int((budget["max_runtime_sec"] - fixed_overhead_sec) / per_step_sec))
    steps = max(100, min(int(budget["max_steps"]), steps_by_budget))
    scores = _simulate_scores(use_case, variant, seed_int, steps)

    score_slice_start = max(0, steps // 2)
    score_main = fmean(scores[score_slice_start:]) if scores else 0.0
    runtime_sec = fixed_overhead_sec + steps * per_step_sec

    drift_recovery_t90 = ""
    forgetting_delta = ""
    if bool(flags.get("drift_recovery_t90")):
        drift_recovery_t90 = _fmt_float(_drift_recovery_t90(scores), digits=2)
    if bool(flags.get("forgetting_delta")):
        forgetting_delta = _fmt_float(_forgetting_delta(scores), digits=6)

    return {
        "runtime_sec": _fmt_float(runtime_sec, digits=4),
        "steps": str(steps),
        "score_main": _fmt_float(score_main, digits=6),
        "drift_recovery_t90": drift_recovery_t90,
        "forgetting_delta": forgetting_delta,
    }


def _empty_metrics() -> Dict[str, str]:
    return {field: "" for field in METRIC_FIELDS}


def build_rows(
    use_cases: List[str],
    variants: List[str],
    seeds: List[str],
    budget: Dict[str, float],
    ts_utc: str,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for idx, (use_case, variant, seed) in enumerate(product(use_cases, variants, seeds), start=1):
        run_id = "run-{idx:04d}-{use_case}-{variant}-{seed}".format(
            idx=idx,
            use_case=_sanitize_fragment(use_case),
            variant=_sanitize_fragment(variant),
            seed=_sanitize_fragment(seed),
        )

        status = "ok"
        error_msg = ""
        metrics = _empty_metrics()
        try:
            metrics = _build_metrics(use_case=use_case, variant=variant, seed=seed, budget=budget)
        except Exception as exc:  # pragma: no cover - defensive path
            status = "error"
            error_msg = f"{type(exc).__name__}: {exc}"

        rows.append(
            {
                "run_id": run_id,
                "ts_utc": ts_utc,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate run matrix CSV from JSON manifest")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--out", required=True, help="Path to output CSV")
    parser.add_argument(
        "--ts-utc",
        default=None,
        help="Optional fixed ISO UTC timestamp for deterministic output (e.g. 2026-02-26T00:00:00Z)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    out_path = Path(args.out)
    ts_utc = args.ts_utc if args.ts_utc else _default_ts_utc()

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    normalized = _normalize_manifest(data)
    rows = build_rows(
        normalized["use_cases"],
        normalized["variants"],
        normalized["seeds"],
        budget=normalized["budget"],
        ts_utc=ts_utc,
    )
    write_csv(out_path, rows)

    ok_count = sum(1 for row in rows if row.get("status") == "ok")
    print(f"Wrote {len(rows)} rows to {out_path} ({ok_count} ok, {len(rows) - ok_count} error)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
