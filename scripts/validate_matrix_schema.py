#!/usr/bin/env python3
"""Validate matrix benchmark CSV schema for required columns."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "worker_count",
    "node_id",
    "throughput_steps_sec",
    "cost_per_1m_steps",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate benchmark CSV schema")
    parser.add_argument(
        "--raw-dir",
        default="benchmarks/results/raw",
        help="Directory with benchmark CSV files",
    )
    return parser.parse_args()


def _missing_or_empty(row: dict[str, str], column: str) -> bool:
    value = row.get(column)
    return value is None or str(value).strip() == ""


def validate_file(path: Path) -> list[str]:
    issues: list[str] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing_headers = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_headers:
            issues.append(f"Missing header(s): {', '.join(missing_headers)}")
            return issues

        row_count = 0
        for row_index, row in enumerate(reader, start=1):
            row_count += 1
            if any(_missing_or_empty(row, col) for col in REQUIRED_COLUMNS):
                bad_cols = [
                    col for col in REQUIRED_COLUMNS if _missing_or_empty(row, col)
                ]
                issues.append(f"row {row_index}: empty {', '.join(bad_cols)}")
        if row_count == 0:
            issues.append("No data rows")

    return issues


def main() -> int:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        print(f"ERROR: raw dir not found: {raw_dir}", file=sys.stderr)
        return 1

    csvs = sorted(raw_dir.glob("*.csv"))
    if not csvs:
        print(f"ERROR: no CSV files under {raw_dir}", file=sys.stderr)
        return 2

    failed = False
    for csv_path in csvs:
        issues = validate_file(csv_path)
        if issues:
            failed = True
            print(f"{csv_path}: FAIL")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"{csv_path}: ok")

    if failed:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
