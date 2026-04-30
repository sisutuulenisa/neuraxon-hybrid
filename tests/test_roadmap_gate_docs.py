"""Tests for roadmap gate documentation."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")


def test_readme_documents_current_benchmark_gate_for_deferred_work() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    lower = readme.lower()

    required_phrases = [
        "## roadmap gate",
        "current phase",
        "temporal benchmark",
        "policy-ablation",
        "criticality",
        "memory persistence remains deferred",
        "visual perception remains deferred",
        "#51",
        "#52",
        "#53",
        "#54",
        "#55",
    ]
    for phrase in required_phrases:
        assert phrase in lower

    assert "meaningfully above baselines" in lower
    assert "beyond hand-authored semantic routing" in lower
