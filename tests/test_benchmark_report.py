"""Tests for the published benchmark report."""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path("benchmarks/results/analysis/benchmark_report.md")


def test_benchmark_report_publishes_required_sections_and_assets() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    required_headings = [
        "# Neuraxon Agent Benchmark Report",
        "## 1. Samenvatting",
        "## 2. Benchmarkopzet",
        "## 3. Resultaten",
        "## 4. Per scenario type",
        "## 5. Interpretatie",
        "## 6. Statistische vergelijking",
        "## 7. Wat dit wel en niet bewijst",
        "## 8. Verdict",
        "## 9. Artefacten",
    ]
    for heading in required_headings:
        assert heading in report

    required_plot_links = [
        "plots/accuracy_by_agent.png",
        "plots/confidence_distribution.png",
        "plots/neuromodulator_trends.png",
        "plots/learning_curve.png",
    ]
    for plot_link in required_plot_links:
        assert plot_link in report


def test_benchmark_report_states_go_and_baseline_comparison() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "GO voor de volgende onderzoeksfase" in report
    assert "niet voor productie" in report
    assert "100.00%" in report
    assert "15.71%" in report
    assert "28.57%" in report
    assert "700" in report
    assert "significant beter" in report

    comparison_headers = ["Agent", "Runs", "Correct", "Accuracy", "Gem. confidence"]
    for header in comparison_headers:
        assert header in report


def test_benchmark_report_keeps_memory_and_visual_perception_out_of_scope() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "memory persistence" in report.lower()
    assert "visuele" in report.lower() or "visual" in report.lower()
    assert "niet bewezen" in report.lower()
    assert "generalisatie" in report.lower()
