#!/usr/bin/env python3
"""Summarize run CSV files per (use_case, variant)."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Tuple

OUT_FIELDS = ["use_case", "variant", "total", "ok", "error"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize run CSV files")
    parser.add_argument("--in", dest="inputs", action="append", required=True, help="Input CSV (repeatable)")
    parser.add_argument("--out", required=True, help="Output summary CSV")
    return parser.parse_args()


def _key(use_case: str, variant: str) -> Tuple[str, str]:
    uc = use_case.strip() if use_case else "unknown_use_case"
    vr = variant.strip() if variant else "unknown_variant"
    return uc, vr


def summarize(inputs: list[str]) -> Dict[Tuple[str, str], Dict[str, int]]:
    agg: Dict[Tuple[str, str], Dict[str, int]] = {}

    for csv_path in inputs:
        path = Path(csv_path)
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                use_case, variant = _key(row.get("use_case", ""), row.get("variant", ""))
                bucket = agg.setdefault((use_case, variant), {"total": 0, "ok": 0, "error": 0})
                bucket["total"] += 1

                status = (row.get("status", "") or "").strip().lower()
                if status == "ok":
                    bucket["ok"] += 1
                else:
                    bucket["error"] += 1

    return agg


def write_summary(out_path: Path, summary: Dict[Tuple[str, str], Dict[str, int]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUT_FIELDS)
        writer.writeheader()

        for (use_case, variant) in sorted(summary.keys()):
            bucket = summary[(use_case, variant)]
            writer.writerow(
                {
                    "use_case": use_case,
                    "variant": variant,
                    "total": bucket["total"],
                    "ok": bucket["ok"],
                    "error": bucket["error"],
                }
            )


def main() -> int:
    args = parse_args()
    summary = summarize(args.inputs)
    out_path = Path(args.out)
    write_summary(out_path, summary)

    total_groups = len(summary)
    total_rows = sum(bucket["total"] for bucket in summary.values())
    print(f"Wrote {total_groups} groups ({total_rows} rows) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
