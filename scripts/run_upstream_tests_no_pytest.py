#!/usr/bin/env python3
"""Run upstream test functions without requiring pytest package."""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "upstream" / "Neuraxon"
TEST_FILE = UPSTREAM / "tests" / "test_neuraxon.py"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def ensure_fake_pytest() -> None:
    if "pytest" in sys.modules:
        return
    fake = types.ModuleType("pytest")
    fake.main = lambda *args, **kwargs: 0
    sys.modules["pytest"] = fake


def load_test_module():
    ensure_fake_pytest()
    sys.path.insert(0, str(UPSTREAM))
    spec = importlib.util.spec_from_file_location("test_neuraxon", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def run() -> int:
    mod = load_test_module()

    results = []
    failures = 0

    test_functions = [
        (name, getattr(mod, name))
        for name in dir(mod)
        if name.startswith("test_") and callable(getattr(mod, name))
    ]

    for name, fn in sorted(test_functions):
        item = {"test": name, "ok": True, "error": ""}
        try:
            fn()
        except Exception:
            item["ok"] = False
            item["error"] = traceback.format_exc()
            failures += 1
        results.append(item)

    summary = {
        "total": len(results),
        "passed": len(results) - failures,
        "failed": failures,
        "results": results,
    }

    out = LOG_DIR / "upstream_tests_no_pytest.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
