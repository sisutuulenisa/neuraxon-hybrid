#!/usr/bin/env python3
"""Simple smoke runner for Neuraxon v1/v2 without external deps."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "Neuraxon"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    ("v1", UPSTREAM / "neuraxon.py"),
    ("v2", UPSTREAM / "neuraxon2.py"),
]


def run_target(name: str, script: Path) -> dict:
    proc = subprocess.run(
        ["python3", str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    out_file = LOG_DIR / f"smoke_{name}.log"
    out_file.write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    return {
        "name": name,
        "script": str(script),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "log": str(out_file),
    }


def main() -> int:
    summary = [run_target(name, script) for name, script in TARGETS]

    summary_file = LOG_DIR / "smoke_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if all(item["ok"] for item in summary) else 1


if __name__ == "__main__":
    raise SystemExit(main())
