#!/usr/bin/env python3
"""Minimal JSON in/out wrapper for Neuraxon phase-3 integration POC."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "neuraxon.poc-wrapper.v1"
WRAPPER_VERSION = "0.1.0"


class POCWrapperError(Exception):
    """Expected wrapper error with a stable code for callers."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Neuraxon JSON in/out POC wrapper")
    parser.add_argument("--input", dest="input_json", required=True, help="Path to input JSON payload")
    parser.add_argument("--out", dest="output_json", required=True, help="Path to output JSON payload")
    return parser.parse_args()


def read_json(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise POCWrapperError("input_not_found", f"Input file not found: {path}") from exc
    except OSError as exc:
        raise POCWrapperError("input_read_error", f"Cannot read input file: {path}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise POCWrapperError("input_invalid_json", f"Input file is not valid JSON: {path}") from exc


def _must_non_empty_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise POCWrapperError("contract_validation_error", f"Field '{key}' must be a non-empty string")
    return value.strip()


def normalize_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise POCWrapperError("contract_validation_error", "Input root must be a JSON object")

    use_case = _must_non_empty_string(payload, "use_case")
    variant = _must_non_empty_string(payload, "variant")

    seed_raw = payload.get("seed", 0)
    if not isinstance(seed_raw, (int, str)):
        raise POCWrapperError("contract_validation_error", "Field 'seed' must be an int or string")
    seed = str(seed_raw)

    params_raw = payload.get("params", {})
    if params_raw is None:
        params_raw = {}
    if not isinstance(params_raw, dict):
        raise POCWrapperError("contract_validation_error", "Field 'params' must be an object")

    return {
        "use_case": use_case,
        "variant": variant,
        "seed": seed,
        "params": params_raw,
    }


def build_success_output(normalized: dict[str, Any]) -> dict[str, Any]:
    canonical_input = json.dumps(normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical_input.encode("utf-8")).hexdigest()

    placeholder_score = int(digest[:8], 16) % 1000

    return {
        "status": "ok",
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "wrapper_version": WRAPPER_VERSION,
            "request_fingerprint": digest[:16],
            "deterministic": True,
        },
        "result": {
            "mode": "placeholder",
            "use_case": normalized["use_case"],
            "variant": normalized["variant"],
            "seed": normalized["seed"],
            "placeholder_score": placeholder_score,
            "params_echo": normalized["params"],
        },
    }


def build_error_output(code: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "wrapper_version": WRAPPER_VERSION,
            "deterministic": True,
        },
        "error": {
            "code": code,
            "message": message,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True, sort_keys=True)
            handle.write("\n")
    except OSError as exc:
        raise POCWrapperError("output_write_error", f"Cannot write output file: {path}") from exc


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = Path(args.output_json)

    try:
        payload = read_json(input_path)
        normalized = normalize_payload(payload)
        result = build_success_output(normalized)
        write_json(output_path, result)
        print(f"Wrote POC output to {output_path}")
        return 0
    except POCWrapperError as exc:
        error_payload = build_error_output(exc.code, str(exc))
        try:
            write_json(output_path, error_payload)
        except POCWrapperError:
            pass
        print(f"ERROR [{exc.code}] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
