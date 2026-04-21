"""Tests for neuraxon-agent CLI."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from neuraxon_agent.cli import main


def test_cli_help() -> None:
    assert main(["--help"]) == 0


def test_cli_think() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "obs.json"
        out = Path(tmpdir) / "act.json"
        inp.write_text(json.dumps({"observation": {"type": "prompt", "content": "hi"}}))
        rc = main(["think", "-i", str(inp), "-o", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "action" in data
        assert "confidence" in data


def test_cli_modulate() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "out.json"
        out = Path(tmpdir) / "res.json"
        inp.write_text(json.dumps({"outcome": "success"}))
        rc = main(["modulate", "-i", str(inp), "-o", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "state" in data


def test_cli_evolve() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "evo.json"
        rc = main(["evolve", "-g", "1", "-e", "1", "--seed", "42", "-o", str(out)])
        assert rc == 0
        data = json.loads(out.read_text())
        assert "summary" in data


def test_cli_no_command() -> None:
    assert main([]) == 2
