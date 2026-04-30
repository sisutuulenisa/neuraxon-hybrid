"""Tests for the published benchmark report."""

from __future__ import annotations

from pathlib import Path

REPORT_PATH = Path("benchmarks/results/analysis/benchmark_report.md")


def test_benchmark_report_publishes_required_sections_and_assets() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    required_headings = [
        "# Neuraxon Agent Benchmark Report",
        "## 1. Samenvatting",
        "## 2. Methodologie",
        "## 3. Resultaten",
        "## 4. Analyse",
        "## 5. Limitaties",
        "## 6. Aanbevelingen voor v0.2.0",
        "## Go/No-Go beslissing",
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


def test_benchmark_report_states_explicit_no_go_and_baseline_comparison() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "NO-GO" in report
    assert "nog niet productie-waardig" in report
    assert "15.71%" in report
    assert "28.57%" in report
    assert "110" in report
    assert "niet beter dan random" in report
    assert "significant slechter" in report

    comparison_headers = ["Agent", "Runs", "Successes", "Accuracy", "Gemiddelde confidence"]
    for header in comparison_headers:
        assert header in report


def test_benchmark_report_defers_memory_persistence_until_tissue_is_useful() -> None:
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert "memory persistence" in report.lower()
    assert "uitstellen" in report.lower()
    assert "eerst" in report.lower()
    assert "nuttige beslissingen" in report.lower()
