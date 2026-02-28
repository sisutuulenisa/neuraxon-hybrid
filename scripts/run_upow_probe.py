#!/usr/bin/env python3
"""Run a fixed UPOW worker-scaling probe matrix (1/2/4 workers).

This wrapper runs the matrix generator with multiple worker counts and writes:
- the full run CSV (throughput/cost per run)
- a summary CSV with success-rate and node-variance per (worker_count, use_case, variant)
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, pvariance
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run UPOW worker-scaling probe matrix (1/2/4)"
    )
    parser.add_argument("--manifest", required=True, help="Path to benchmark matrix manifest")
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV path for probe rows (includes worker_count columns)",
    )
    parser.add_argument(
        "--worker-counts",
        default="1,2,4",
        help="Comma-separated worker counts to sweep",
    )
    parser.add_argument(
        "--ts-utc",
        default=None,
        help="Optional fixed ISO UTC timestamp passed through to run_matrix",
    )
    parser.add_argument(
        "--enable-mlflow",
        action="store_true",
        help="Enable MLflow tracking for the probe run",
    )
    return parser.parse_args()


def _normalize_workers(value: str) -> List[str]:
    workers = [token.strip() for token in value.split(",") if token.strip()]
    if not workers:
        raise ValueError("--worker-counts must contain at least one integer")
    normalized: List[str] = []
    for token in workers:
        if int(token) <= 0:
            raise ValueError("worker counts must be positive integers")
        normalized.append(token)
    return normalized


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _node_to_int(node_id: str) -> int:
    match = re.search(r"(\d+)$", str(node_id))
    return int(match.group(1)) if match else 0


def _summarize_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (row.get("worker_count", ""), row.get("use_case", ""), row.get("variant", ""))
        groups[key].append(row)

    out: List[Dict[str, Any]] = []
    for (worker_count, use_case, variant), samples in sorted(groups.items()):
        total = len(samples)
        if total == 0:
            continue

        ok = sum(1 for row in samples if row.get("status") == "ok")
        throughput = [_safe_float(row.get("throughput_steps_sec", "0")) for row in samples]
        cost = [_safe_float(row.get("cost_per_1m_steps", "0")) for row in samples]
        nodes = [_node_to_int(row.get("node_id", "0")) for row in samples]
        node_variance = pvariance(nodes) if len(set(nodes)) > 1 else 0.0

        out.append(
            {
                "worker_count": worker_count,
                "use_case": use_case,
                "variant": variant,
                "run_count": total,
                "ok_count": ok,
                "success_rate": f"{ok / total:.4f}",
                "node_variance": f"{node_variance:.6f}",
                "throughput_mean_steps_sec": f"{mean(throughput):.6f}",
                "cost_per_1m_steps_mean": f"{mean(cost):.6f}",
            }
        )

    return out


def _write_summary(rows: List[Dict[str, Any]], path: Path) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    manifest = Path(args.manifest)
    out_path = Path(args.out)

    if not manifest.exists():
        raise FileNotFoundError(f"manifest not found: {manifest}")

    workers = _normalize_workers(args.worker_counts)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: List[str] = [
        sys.executable,
        str(Path(__file__).with_name("run_matrix.py")),
        "--manifest",
        str(manifest),
        "--out",
        str(out_path),
        "--worker-counts",
        ",".join(workers),
    ]
    if args.ts_utc:
        cmd.extend(["--ts-utc", args.ts_utc])
    if args.enable_mlflow:
        cmd.append("--enable-mlflow")

    subprocess.run(cmd, check=True)

    with out_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    summary_rows = _summarize_rows(rows)
    summary_path = out_path.with_suffix(".summary.csv")
    _write_summary(summary_rows, summary_path)

    print(f"UPOW probe complete -> {out_path}")
    print(f"UPOW summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
