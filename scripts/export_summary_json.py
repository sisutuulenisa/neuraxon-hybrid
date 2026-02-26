#!/usr/bin/env python3
"""Export claim summary CSV to a dashboard-friendly JSON file."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_IN = "benchmarks/results/summary/claim_summary.csv"
DEFAULT_OUT = "dashboard/data/claim_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export claim summary CSV to JSON")
    parser.add_argument("--in", dest="input_csv", default=DEFAULT_IN, help=f"Input CSV (default: {DEFAULT_IN})")
    parser.add_argument("--out", dest="output_json", default=DEFAULT_OUT, help=f"Output JSON (default: {DEFAULT_OUT})")
    return parser.parse_args()


def parse_int(value: str | None) -> int:
    if value is None:
        return 0
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return 0


def read_rows(csv_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            total = parse_int(raw.get("total"))
            ok = parse_int(raw.get("ok"))
            error = parse_int(raw.get("error"))

            rows.append(
                {
                    "use_case": (raw.get("use_case") or "").strip(),
                    "variant": (raw.get("variant") or "").strip(),
                    "total": total,
                    "ok": ok,
                    "error": error,
                    "ok_rate": round((ok / total) if total else 0.0, 4),
                }
            )
    return rows


def build_payload(rows: list[dict[str, Any]], source_csv: Path) -> dict[str, Any]:
    total_runs = sum(row["total"] for row in rows)
    ok_runs = sum(row["ok"] for row in rows)
    error_runs = sum(row["error"] for row in rows)

    return {
        "source_csv": source_csv.as_posix(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "totals": {
            "groups": len(rows),
            "runs_total": total_runs,
            "runs_ok": ok_runs,
            "runs_error": error_runs,
            "ok_rate": round((ok_runs / total_runs) if total_runs else 0.0, 4),
        },
        "rows": rows,
    }


def main() -> int:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_json = Path(args.output_json)

    rows = read_rows(input_csv)
    payload = build_payload(rows, input_csv)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

    print(f"Wrote {len(rows)} groups to {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
