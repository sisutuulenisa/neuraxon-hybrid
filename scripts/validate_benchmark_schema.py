#!/usr/bin/env python3
"""Validate benchmark CSV outputs contain required schema columns.

This is intentionally schema-oriented (column presence only):
- validates all raw CSV files under benchmarks/results/raw contain
  the required base, benchmark and UPOW columns.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import List

REQUIRED_COLUMNS = [
    "run_id",
    "ts_utc",
    "use_case",
    "variant",
    "seed",
    "status",
    "error_msg",
    "runtime_sec",
    "steps",
    "score_main",
    "drift_recovery_t90",
    "forgetting_delta",
    "worker_count",
    "node_id",
    "throughput_steps_sec",
    "cost_per_1m_steps",
]


def _collect_csvs(raw_dir: Path) -> List[Path]:
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.glob("*.csv"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-dir",
        default="benchmarks/results/raw",
        help="Directory containing benchmark raw CSV files",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    csv_files = _collect_csvs(raw_dir)

    missing_any = False
    if not csv_files:
        print(f"[error] No CSV files found in {raw_dir}")
        return 1

    for csv_path in csv_files:
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
        missing = [field for field in REQUIRED_COLUMNS if field not in header]
        if missing:
            missing_any = True
            print(f"[error] {csv_path}: missing columns: {', '.join(missing)}")

    if missing_any:
        return 1

    print(f"[ok] Validated {len(csv_files)} raw CSV schema files in {raw_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
