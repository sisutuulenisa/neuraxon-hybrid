#!/usr/bin/env python3
"""Generate a run matrix CSV from a manifest of use_cases, variants and seeds."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List

FIELDS = [
    "run_id",
    "ts_utc",
    "use_case",
    "variant",
    "seed",
    "status",
    "error_msg",
]


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


def _normalize_manifest(data: Dict[str, Any]) -> Dict[str, List[str]]:
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

    return {"use_cases": use_cases, "variants": variants, "seeds": seeds}


def _sanitize_fragment(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "na"


def _default_ts_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_rows(
    use_cases: List[str],
    variants: List[str],
    seeds: List[str],
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

        # Stub execution (phase-2 bootstrap): mark each generated run as OK.
        rows.append(
            {
                "run_id": run_id,
                "ts_utc": ts_utc,
                "use_case": use_case,
                "variant": variant,
                "seed": seed,
                "status": "ok",
                "error_msg": "",
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
    rows = build_rows(normalized["use_cases"], normalized["variants"], normalized["seeds"], ts_utc=ts_utc)
    write_csv(out_path, rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
