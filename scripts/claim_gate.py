#!/usr/bin/env python3
"""Evaluate Neuraxon claim-gate status from benchmark artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate protocol thresholds against benchmark raw CSV outputs"
    )
    parser.add_argument(
        "--raw-dir",
        default="benchmarks/results/raw",
        help="Directory with raw benchmark CSV files",
    )
    parser.add_argument(
        "--protocol-doc",
        default="docs/TEST_PROTOCOL_PHASE1_2.md",
        help="Protocol markdown that defines thresholds",
    )
    parser.add_argument(
        "--claim-eval-doc",
        default="docs/CLAIM_EVAL_002.md",
        help="Optional claim evaluation markdown metadata",
    )
    parser.add_argument(
        "--out",
        default="benchmarks/results/summary/claim_gate.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Return non-zero exit code when overall gate is FAIL",
    )
    return parser.parse_args()


def _extract_float(text: str, pattern: str, label: str) -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError(f"Could not parse threshold for {label}")
    return float(match.group(1))


def _extract_band(text: str, pattern: str, label: str) -> tuple[float, float]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        raise ValueError(f"Could not parse threshold band for {label}")
    return float(match.group(1)), float(match.group(2))


def load_protocol_thresholds(protocol_path: Path) -> dict[str, Any]:
    if not protocol_path.exists():
        raise FileNotFoundError(f"Missing protocol doc: {protocol_path}")

    text = protocol_path.read_text(encoding="utf-8")

    sigma_min, sigma_max = _extract_band(
        text,
        r"mediane\s+`?sigma`?\s+in\s+band\s+\*\*\[\s*([0-9.]+)\s*,\s*([0-9.]+)\s*\]\*\*",
        "soc.sigma_band",
    )

    return {
        "source": str(protocol_path),
        "phase1": {
            "repro_smoke_success_required": int(
                _extract_float(text, r"\*\*Pass:\*\*\s*([0-9.]+)\s*/\s*[0-9.]+\s*smoke-runs", "phase1.repro")
            ),
            "crash_rate_max_pct": _extract_float(text, r"crash-rate\s*=\s*([0-9.]+)%", "phase1.crash"),
            "nan_rate_max_pct": _extract_float(text, r"NaN-rate\s*=\s*([0-9.]+)%", "phase1.nan"),
            "timeout_rate_max_pct": _extract_float(
                text, r"timeout-rate\s*(?:<=|≤)\s*([0-9.]+)%", "phase1.timeout"
            ),
        },
        "claim1": {
            "t90_factor": _extract_float(
                text,
                r"`T90_full\s*<=\s*([0-9.]+)\s*\*\s*min\(T90_fastOnly",
                "claim1.t90_factor",
            ),
            "forgetting_factor": _extract_float(
                text,
                r"`F_full\s*<=\s*([0-9.]+)\s*\*\s*min\(F_fastOnly",
                "claim1.forgetting_factor",
            ),
            "stability_factor": _extract_float(
                text,
                r"`SV_full\s*<=\s*([0-9.]+)\s*\*\s*min\(SV_fastOnly",
                "claim1.stability_factor",
            ),
        },
        "claim2": {
            "sigma_min": sigma_min,
            "sigma_max": sigma_max,
            "collapse_rate_max_pct": _extract_float(
                text,
                r"collapse-rate\s*\*\*(?:<=|≤)\s*([0-9.]+)%\*\*",
                "claim2.collapse_rate",
            ),
            "r95_max_steps": _extract_float(text, r"`R95\s*(?:<=|≤)\s*([0-9.]+)`", "claim2.r95"),
        },
        "claim3": {
            "eff_min": _extract_float(text, r"`eff\s*(?:>=|≥)\s*([0-9.]+)`", "claim3.eff"),
            "success_rate_min_pct": _extract_float(
                text, r"success-rate\s*`(?:>=|≥)\s*([0-9.]+)%`", "claim3.success"
            ),
            "inter_node_deviation_max_pct": _extract_float(
                text,
                r"inter-node\s+score-afwijking\s*`(?:<=|≤)\s*([0-9.]+)%`",
                "claim3.inter_node",
            ),
            "cost_ratio_max": _extract_float(
                text, r"kost\s+per\s+1M\s+steps\s*`(?:<=|≤)\s*([0-9.]+)x`", "claim3.cost_ratio"
            ),
        },
    }


def load_raw_rows(raw_dir: Path) -> tuple[list[Path], list[dict[str, str]]]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Missing raw results directory: {raw_dir}")

    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found under: {raw_dir}")

    rows: list[dict[str, str]] = []
    for csv_path in files:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                row["_source_file"] = str(csv_path)
                rows.append(row)

    if not rows:
        raise ValueError(f"No data rows found in CSV files under: {raw_dir}")

    return files, rows


def parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    value = raw.strip()
    if value == "":
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def parse_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on", "collapse", "collapsed"}:
        return True
    if value in {"0", "false", "no", "n", "off", "", "none"}:
        return False
    return None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _mean_for(rows: list[dict[str, str]], use_case: str, variant: str, metric: str) -> float | None:
    vals: list[float] = []
    for row in rows:
        if row.get("use_case") != use_case or row.get("variant") != variant:
            continue
        val = parse_float(row.get(metric))
        if val is not None:
            vals.append(val)
    return _mean(vals)


def _first_metric_column(rows: list[dict[str, str]], candidates: list[str]) -> str | None:
    for key in candidates:
        for row in rows:
            if key in row and (row.get(key, "").strip() != ""):
                return key
    return None


def evaluate_phase1(rows: list[dict[str, str]], thresholds: dict[str, float]) -> dict[str, Any]:
    total_runs = len(rows)
    successful_runs = 0
    timeout_runs = 0
    crash_runs = 0
    nan_hits = 0
    required_missing = 0

    required_aliases = {
        "seed": ["seed"],
        "model_variant": ["model_variant", "variant"],
        "steps": ["steps"],
        "score": ["score", "score_main"],
        "runtime_sec": ["runtime_sec"],
    }

    for row in rows:
        status = (row.get("status") or "").strip().lower()
        if status == "ok":
            successful_runs += 1
        else:
            err = (row.get("error_msg") or "").lower()
            if "timeout" in err:
                timeout_runs += 1
            else:
                crash_runs += 1

        for metric_name in ["runtime_sec", "steps", "score_main", "drift_recovery_t90", "forgetting_delta"]:
            raw = row.get(metric_name)
            if raw is None or raw.strip() == "":
                continue
            parsed = parse_float(raw)
            if parsed is None:
                nan_hits += 1

        for aliases in required_aliases.values():
            if not any((row.get(alias) or "").strip() != "" for alias in aliases):
                required_missing += 1

    crash_rate_pct = (100.0 * crash_runs / total_runs) if total_runs else 100.0
    nan_rate_pct = (100.0 * nan_hits / total_runs) if total_runs else 100.0
    timeout_rate_pct = (100.0 * timeout_runs / total_runs) if total_runs else 100.0
    completeness_pct = (100.0 * (1.0 - (required_missing / (total_runs * 5)))) if total_runs else 0.0

    checks = {
        "reproducibility": {
            "required_successes": thresholds["repro_smoke_success_required"],
            "actual_successes": successful_runs,
            "pass": successful_runs >= thresholds["repro_smoke_success_required"],
        },
        "basic_stability": {
            "crash_rate_pct": crash_rate_pct,
            "crash_rate_max_pct": thresholds["crash_rate_max_pct"],
            "nan_rate_pct": nan_rate_pct,
            "nan_rate_max_pct": thresholds["nan_rate_max_pct"],
            "timeout_rate_pct": timeout_rate_pct,
            "timeout_rate_max_pct": thresholds["timeout_rate_max_pct"],
            "pass": (
                crash_rate_pct <= thresholds["crash_rate_max_pct"]
                and nan_rate_pct <= thresholds["nan_rate_max_pct"]
                and timeout_rate_pct <= thresholds["timeout_rate_max_pct"]
            ),
        },
        "logging_auditability": {
            "required_fields": ["seed", "model_variant", "steps", "score", "runtime_sec"],
            "missing_field_cells": required_missing,
            "completeness_pct": completeness_pct,
            "pass": required_missing == 0,
        },
    }

    status = "PASS" if all(item["pass"] for item in checks.values()) else "FAIL"
    reasons: list[str] = []
    if not checks["reproducibility"]["pass"]:
        reasons.append("phase1.reproducibility")
    if not checks["basic_stability"]["pass"]:
        reasons.append("phase1.basic_stability")
    if not checks["logging_auditability"]["pass"]:
        reasons.append("phase1.logging_auditability")

    return {
        "status": status,
        "total_runs": total_runs,
        "checks": checks,
        "fail_reasons": reasons,
    }


def evaluate_claim1(rows: list[dict[str, str]], thresholds: dict[str, float]) -> dict[str, Any]:
    use_cases = sorted({row.get("use_case", "") for row in rows if row.get("use_case")})
    per_use_case: dict[str, Any] = {}
    claim_fail_reasons: list[str] = []

    stability_metric = _first_metric_column(rows, ["stability_var", "sv"])
    metric_to_column = {
        "t90": "drift_recovery_t90",
        "forgetting": "forgetting_delta",
        "stability": stability_metric,
    }

    metric_factors = {
        "t90": thresholds["t90_factor"],
        "forgetting": thresholds["forgetting_factor"],
        "stability": thresholds["stability_factor"],
    }

    for use_case in use_cases:
        variants = sorted({row.get("variant", "") for row in rows if row.get("use_case") == use_case})
        baselines = [v for v in variants if v.startswith("baseline_")]

        per_metric: dict[str, Any] = {}
        use_case_pass = True

        for metric_name, col_name in metric_to_column.items():
            full = _mean_for(rows, use_case, "neuraxon_full", col_name) if col_name else None
            wfast = _mean_for(rows, use_case, "neuraxon_wfast_only", col_name) if col_name else None
            wslow = _mean_for(rows, use_case, "neuraxon_wslow_only", col_name) if col_name else None
            baseline_values = {
                b: _mean_for(rows, use_case, b, col_name) for b in baselines
            } if col_name else {}
            baseline_values = {k: v for k, v in baseline_values.items() if v is not None}
            best_baseline = min(baseline_values.values()) if baseline_values else None

            has_inputs = all(v is not None for v in [full, wfast, wslow, best_baseline])
            threshold_value = None
            comparison_pass = False

            if has_inputs:
                threshold_value = metric_factors[metric_name] * min(wfast, wslow, best_baseline)
                comparison_pass = bool(full <= threshold_value)
            else:
                use_case_pass = False

            if not comparison_pass:
                use_case_pass = False

            per_metric[metric_name] = {
                "metric_column": col_name,
                "factor": metric_factors[metric_name],
                "full_mean": full,
                "wfast_mean": wfast,
                "wslow_mean": wslow,
                "best_baseline_mean": best_baseline,
                "baseline_means": baseline_values,
                "threshold": threshold_value,
                "pass": comparison_pass,
                "missing_inputs": not has_inputs,
            }

        if not use_case_pass:
            claim_fail_reasons.append(f"claim1.{use_case}")

        per_use_case[use_case] = {
            "status": "PASS" if use_case_pass else "FAIL",
            "metrics": per_metric,
        }

    claim_status = "PASS" if per_use_case and all(v["status"] == "PASS" for v in per_use_case.values()) else "FAIL"
    if not per_use_case:
        claim_fail_reasons.append("claim1.no_use_case_data")

    return {
        "status": claim_status,
        "per_use_case": per_use_case,
        "fail_reasons": claim_fail_reasons,
    }


def evaluate_claim2(rows: list[dict[str, str]], thresholds: dict[str, float]) -> dict[str, Any]:
    use_case_rows = [row for row in rows if row.get("use_case") == "usecase_b_perturbation"]
    sigma_col = _first_metric_column(use_case_rows, ["sigma", "sigma_branching"])
    collapse_col = _first_metric_column(use_case_rows, ["collapse_flag", "collapse"])
    recovery_col = _first_metric_column(use_case_rows, ["recovery95_steps", "r95", "R95"])

    missing_metrics: list[str] = []
    if sigma_col is None:
        missing_metrics.append("sigma")
    if collapse_col is None:
        missing_metrics.append("collapse_flag")
    if recovery_col is None:
        missing_metrics.append("recovery95_steps")

    sigma_median = None
    sigma_pass = False
    collapse_rate_pct = None
    collapse_pass = False
    r95_median = None
    r95_pass = False

    if sigma_col:
        sigma_values = [parse_float(row.get(sigma_col)) for row in use_case_rows]
        sigma_values = [v for v in sigma_values if v is not None]
        if sigma_values:
            sigma_median = statistics.median(sigma_values)
            sigma_pass = thresholds["sigma_min"] <= sigma_median <= thresholds["sigma_max"]
        else:
            missing_metrics.append("sigma_values")

    if collapse_col:
        collapse_values = [parse_bool(row.get(collapse_col)) for row in use_case_rows]
        collapse_values = [v for v in collapse_values if v is not None]
        if collapse_values:
            collapse_rate_pct = 100.0 * (sum(1 for v in collapse_values if v) / len(collapse_values))
            collapse_pass = collapse_rate_pct <= thresholds["collapse_rate_max_pct"]
        else:
            missing_metrics.append("collapse_values")

    if recovery_col:
        r95_values = [parse_float(row.get(recovery_col)) for row in use_case_rows]
        r95_values = [v for v in r95_values if v is not None]
        if r95_values:
            r95_median = statistics.median(r95_values)
            r95_pass = r95_median <= thresholds["r95_max_steps"]
        else:
            missing_metrics.append("recovery95_values")

    status = "PASS" if (not missing_metrics and sigma_pass and collapse_pass and r95_pass) else "FAIL"
    reasons = []
    if missing_metrics:
        reasons.append("claim2.missing_metrics")
    if not sigma_pass:
        reasons.append("claim2.sigma")
    if not collapse_pass:
        reasons.append("claim2.collapse")
    if not r95_pass:
        reasons.append("claim2.r95")

    return {
        "status": status,
        "use_case": "usecase_b_perturbation",
        "metrics": {
            "sigma": {
                "column": sigma_col,
                "median": sigma_median,
                "band": [thresholds["sigma_min"], thresholds["sigma_max"]],
                "pass": sigma_pass,
            },
            "collapse_rate": {
                "column": collapse_col,
                "value_pct": collapse_rate_pct,
                "max_pct": thresholds["collapse_rate_max_pct"],
                "pass": collapse_pass,
            },
            "recovery95": {
                "column": recovery_col,
                "median_steps": r95_median,
                "max_steps": thresholds["r95_max_steps"],
                "pass": r95_pass,
            },
        },
        "missing_metrics": sorted(set(missing_metrics)),
        "fail_reasons": reasons,
    }


def evaluate_claim3(rows: list[dict[str, str]], thresholds: dict[str, float]) -> dict[str, Any]:
    worker_col = _first_metric_column(rows, ["worker_count"])
    throughput_col = _first_metric_column(rows, ["throughput_steps_sec"])
    node_col = _first_metric_column(rows, ["node_id"])
    cost_col = _first_metric_column(rows, ["cost_per_1m_steps"])

    missing_metrics: list[str] = []
    if worker_col is None:
        missing_metrics.append("worker_count")
    if throughput_col is None:
        missing_metrics.append("throughput_steps_sec")
    if node_col is None:
        missing_metrics.append("node_id")
    if cost_col is None:
        missing_metrics.append("cost_per_1m_steps")

    eff = None
    eff_pass = False
    success_rate_pct = None
    success_pass = False
    inter_node_deviation_pct = None
    inter_node_pass = False
    cost_ratio = None
    cost_pass = False

    parsed_rows: list[dict[str, Any]] = []
    for row in rows:
        worker = parse_float(row.get(worker_col)) if worker_col else None
        throughput = parse_float(row.get(throughput_col)) if throughput_col else None
        cost = parse_float(row.get(cost_col)) if cost_col else None
        node = (row.get(node_col) or "").strip() if node_col else ""
        status = (row.get("status") or "").strip().lower()

        parsed_rows.append(
            {
                "worker_count": int(worker) if worker is not None else None,
                "throughput": throughput,
                "cost": cost,
                "node": node,
                "status": status,
                "score_main": parse_float(row.get("score_main")),
            }
        )

    if worker_col and throughput_col:
        throughput_1 = _mean([r["throughput"] for r in parsed_rows if r["worker_count"] == 1 and r["throughput"] is not None])
        throughput_4 = _mean([r["throughput"] for r in parsed_rows if r["worker_count"] == 4 and r["throughput"] is not None])
        if throughput_1 and throughput_4 and throughput_1 > 0:
            eff = throughput_4 / (4.0 * throughput_1)
            eff_pass = eff >= thresholds["eff_min"]
        else:
            missing_metrics.append("throughput_1_or_4")

    if worker_col:
        distributed_rows = [r for r in parsed_rows if r["worker_count"] is not None and r["worker_count"] > 1]
        if distributed_rows:
            success_rate_pct = 100.0 * (
                sum(1 for r in distributed_rows if r["status"] == "ok") / len(distributed_rows)
            )
            success_pass = success_rate_pct >= thresholds["success_rate_min_pct"]
        else:
            missing_metrics.append("distributed_runs")

    if node_col:
        per_node_scores: dict[str, list[float]] = {}
        for row in parsed_rows:
            if not row["node"] or row["score_main"] is None:
                continue
            per_node_scores.setdefault(row["node"], []).append(row["score_main"])

        per_node_means = [_mean(values) for values in per_node_scores.values()]
        per_node_means = [v for v in per_node_means if v is not None]

        if len(per_node_means) >= 2:
            mean_score = _mean(per_node_means)
            if mean_score and mean_score != 0:
                inter_node_deviation_pct = (max(per_node_means) - min(per_node_means)) / abs(mean_score) * 100.0
                inter_node_pass = inter_node_deviation_pct <= thresholds["inter_node_deviation_max_pct"]
            else:
                missing_metrics.append("inter_node_mean_score")
        else:
            missing_metrics.append("multi_node_scores")

    if worker_col and cost_col:
        cost_1 = _mean([r["cost"] for r in parsed_rows if r["worker_count"] == 1 and r["cost"] is not None])
        cost_4 = _mean([r["cost"] for r in parsed_rows if r["worker_count"] == 4 and r["cost"] is not None])
        if cost_1 and cost_4 and cost_1 > 0:
            cost_ratio = cost_4 / cost_1
            cost_pass = cost_ratio <= thresholds["cost_ratio_max"]
        else:
            missing_metrics.append("cost_1_or_4")

    status = "PASS" if (not missing_metrics and eff_pass and success_pass and inter_node_pass and cost_pass) else "FAIL"
    reasons = []
    if missing_metrics:
        reasons.append("claim3.missing_metrics")
    if not eff_pass:
        reasons.append("claim3.efficiency")
    if not success_pass:
        reasons.append("claim3.success_rate")
    if not inter_node_pass:
        reasons.append("claim3.inter_node_deviation")
    if not cost_pass:
        reasons.append("claim3.cost_ratio")

    return {
        "status": status,
        "metrics": {
            "efficiency": {
                "value": eff,
                "min_required": thresholds["eff_min"],
                "pass": eff_pass,
            },
            "success_rate": {
                "value_pct": success_rate_pct,
                "min_pct": thresholds["success_rate_min_pct"],
                "pass": success_pass,
            },
            "inter_node_deviation": {
                "value_pct": inter_node_deviation_pct,
                "max_pct": thresholds["inter_node_deviation_max_pct"],
                "pass": inter_node_pass,
            },
            "cost_ratio": {
                "value": cost_ratio,
                "max": thresholds["cost_ratio_max"],
                "pass": cost_pass,
            },
        },
        "missing_metrics": sorted(set(missing_metrics)),
        "fail_reasons": reasons,
    }


def load_claim_eval_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")
    date_match = re.search(r"\*\*Datum:\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
    claim_rows: list[dict[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) != 3:
            continue
        if parts[0].lower() == "claim" or parts[0].startswith("---"):
            continue
        claim_rows.append({"claim": parts[0], "status": parts[1], "reason": parts[2]})

    return {
        "path": str(path),
        "date": date_match.group(1) if date_match else None,
        "claim_table": claim_rows,
    }


def evaluate_gate(
    raw_files: list[Path],
    rows: list[dict[str, str]],
    protocol_thresholds: dict[str, Any],
    claim_eval_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    phase1 = evaluate_phase1(rows, protocol_thresholds["phase1"])
    claim1 = evaluate_claim1(rows, protocol_thresholds["claim1"])
    claim2 = evaluate_claim2(rows, protocol_thresholds["claim2"])
    claim3 = evaluate_claim3(rows, protocol_thresholds["claim3"])

    checks = {
        "phase1_hardening": phase1["status"],
        "claim1_dual_weight_plasticity": claim1["status"],
        "claim2_soc": claim2["status"],
        "claim3_upow_compute_scale": claim3["status"],
    }

    overall_status = "PASS" if all(v == "PASS" for v in checks.values()) else "FAIL"

    fail_reasons: list[str] = []
    for key, status in checks.items():
        if status != "PASS":
            fail_reasons.append(key)

    return {
        "schema_version": "claim-gate-poc-v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "overall_status": overall_status,
        "checks": checks,
        "fail_reasons": fail_reasons,
        "inputs": {
            "raw_files": [str(path) for path in raw_files],
            "raw_rows": len(rows),
            "protocol_doc": protocol_thresholds.get("source"),
            "claim_eval_doc": claim_eval_metadata.get("path") if claim_eval_metadata else None,
        },
        "protocol_thresholds": protocol_thresholds,
        "results": {
            "phase1": phase1,
            "claim1_dual_weight_plasticity": claim1,
            "claim2_soc": claim2,
            "claim3_upow_compute_scale": claim3,
        },
        "metadata": {
            "claim_eval_002": claim_eval_metadata,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    args = parse_args()

    out_path = Path(args.out)
    try:
        protocol_thresholds = load_protocol_thresholds(Path(args.protocol_doc))
        raw_files, rows = load_raw_rows(Path(args.raw_dir))
        claim_eval_metadata = load_claim_eval_metadata(Path(args.claim_eval_doc))
        payload = evaluate_gate(raw_files, rows, protocol_thresholds, claim_eval_metadata)
        write_json(out_path, payload)
    except Exception as exc:  # pragma: no cover - runtime guard
        error_payload = {
            "schema_version": "claim-gate-poc-v1",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "overall_status": "FAIL",
            "error": str(exc),
        }
        write_json(out_path, error_payload)
        print(f"Claim gate evaluation failed: {exc}")
        print(f"Wrote gate artifact: {out_path}")
        return 3

    status = payload["overall_status"]
    print(f"Claim gate status: {status}")
    print(f"Wrote gate artifact: {out_path}")

    if args.strict_exit and status != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
