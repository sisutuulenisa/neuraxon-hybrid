"""Tests for benchmark metrics, CSV exports, and PNG visualizations."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from neuraxon_agent.benchmark import BenchmarkScenario
from neuraxon_agent.benchmark_analysis import analyze_benchmark_results


def _sample_scenarios() -> list[BenchmarkScenario]:
    return [
        BenchmarkScenario(
            name="simple-success",
            scenario_type="simple_tool_call",
            observation_sequence=[{"event": "tool_ready"}],
            expected_optimal_action="execute",
            expected_actions=("execute",),
            difficulty=0.2,
        ),
        BenchmarkScenario(
            name="needs-query",
            scenario_type="missing_params_tool_call",
            observation_sequence=[{"event": "missing_parameter"}],
            expected_optimal_action="query",
            expected_actions=("query",),
            difficulty=0.6,
        ),
        BenchmarkScenario(
            name="retry-failure",
            scenario_type="failed_tool_call",
            observation_sequence=[{"event": "tool_failed"}],
            expected_optimal_action="retry",
            expected_actions=("retry",),
            difficulty=0.8,
        ),
    ]


def _write_tissue_raw(path: Path) -> None:
    payload = {
        "agent_name": "neuraxon_tissue",
        "scenario_count": 3,
        "seed_count": 2,
        "run_count": 6,
        "success_count": 3,
        "total_elapsed_seconds": 0.3,
        "results": [
            {
                "seed": 0,
                "scenario_name": "simple-success",
                "scenario_type": "simple_tool_call",
                "expected_optimal_action": "execute",
                "difficulty": 0.2,
                "observation_count": 1,
                "action": "execute",
                "confidence": 0.8,
                "outcome": "success",
                "elapsed_seconds": 0.01,
                "state": {
                    "energy": 0.9,
                    "activity": 0.1,
                    "step_count": 1,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.7,
                    "serotonin": 0.5,
                    "acetylcholine": 0.4,
                    "norepinephrine": 0.3,
                },
            },
            {
                "seed": 0,
                "scenario_name": "needs-query",
                "scenario_type": "missing_params_tool_call",
                "expected_optimal_action": "query",
                "difficulty": 0.6,
                "observation_count": 1,
                "action": "execute",
                "confidence": 0.4,
                "outcome": "failure",
                "elapsed_seconds": 0.02,
                "state": {
                    "energy": 0.8,
                    "activity": 0.2,
                    "step_count": 2,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.4,
                    "serotonin": 0.45,
                    "acetylcholine": 0.5,
                    "norepinephrine": 0.55,
                },
            },
            {
                "seed": 0,
                "scenario_name": "retry-failure",
                "scenario_type": "failed_tool_call",
                "expected_optimal_action": "retry",
                "difficulty": 0.8,
                "observation_count": 1,
                "action": "retry",
                "confidence": 0.7,
                "outcome": "success",
                "elapsed_seconds": 0.03,
                "state": {
                    "energy": 0.7,
                    "activity": 0.3,
                    "step_count": 3,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.65,
                    "serotonin": 0.55,
                    "acetylcholine": 0.45,
                    "norepinephrine": 0.35,
                },
            },
            {
                "seed": 1,
                "scenario_name": "simple-success",
                "scenario_type": "simple_tool_call",
                "expected_optimal_action": "execute",
                "difficulty": 0.2,
                "observation_count": 1,
                "action": "execute",
                "confidence": 0.75,
                "outcome": "success",
                "elapsed_seconds": 0.01,
                "state": {
                    "energy": 0.9,
                    "activity": 0.1,
                    "step_count": 1,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.72,
                    "serotonin": 0.52,
                    "acetylcholine": 0.42,
                    "norepinephrine": 0.32,
                },
            },
            {
                "seed": 1,
                "scenario_name": "needs-query",
                "scenario_type": "missing_params_tool_call",
                "expected_optimal_action": "query",
                "difficulty": 0.6,
                "observation_count": 1,
                "action": "query",
                "confidence": 0.6,
                "outcome": "success",
                "elapsed_seconds": 0.02,
                "state": {
                    "energy": 0.8,
                    "activity": 0.2,
                    "step_count": 2,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.6,
                    "serotonin": 0.5,
                    "acetylcholine": 0.48,
                    "norepinephrine": 0.4,
                },
            },
            {
                "seed": 1,
                "scenario_name": "retry-failure",
                "scenario_type": "failed_tool_call",
                "expected_optimal_action": "retry",
                "difficulty": 0.8,
                "observation_count": 1,
                "action": "execute",
                "confidence": 0.3,
                "outcome": "failure",
                "elapsed_seconds": 0.03,
                "state": {
                    "energy": 0.7,
                    "activity": 0.3,
                    "step_count": 3,
                    "num_neurons": 5,
                    "num_synapses": 4,
                },
                "neuromodulator_levels": {
                    "dopamine": 0.35,
                    "serotonin": 0.4,
                    "acetylcholine": 0.55,
                    "norepinephrine": 0.6,
                },
            },
        ],
    }
    path.write_text(json.dumps(payload))


def test_analyze_benchmark_results_exports_summary_csvs_and_pngs(tmp_path) -> None:
    raw_path = tmp_path / "neuraxon_tissue_raw.json"
    output_dir = tmp_path / "analysis"
    _write_tissue_raw(raw_path)

    analysis = analyze_benchmark_results(
        tissue_raw_path=raw_path,
        output_dir=output_dir,
        scenarios=_sample_scenarios(),
    )

    assert {summary.agent_name for summary in analysis.agent_summaries} == {
        "neuraxon_tissue",
        "random",
        "always_execute",
    }
    assert analysis.output_paths.summary_csv == output_dir / "benchmark_summary.csv"
    assert analysis.output_paths.scenario_type_csv == output_dir / "scenario_type_breakdown.csv"
    assert analysis.output_paths.statistical_tests_csv == output_dir / "statistical_tests.csv"
    assert set(analysis.output_paths.plots) == {
        "accuracy_by_agent",
        "confidence_distribution",
        "neuromodulator_trends",
        "learning_curve",
    }

    summary_rows = list(csv.DictReader(analysis.output_paths.summary_csv.open()))
    assert {row["agent_name"] for row in summary_rows} == {
        "neuraxon_tissue",
        "random",
        "always_execute",
    }
    tissue_row = next(row for row in summary_rows if row["agent_name"] == "neuraxon_tissue")
    assert tissue_row["run_count"] == "6"
    assert tissue_row["success_count"] == "4"
    assert tissue_row["accuracy"] == "0.666667"
    assert float(tissue_row["confidence_stddev"]) > 0

    for plot_path in analysis.output_paths.plots.values():
        assert plot_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert plot_path.stat().st_size > 100


def test_analyze_benchmark_results_breaks_down_scenario_types_and_stats(tmp_path) -> None:
    raw_path = tmp_path / "neuraxon_tissue_raw.json"
    output_dir = tmp_path / "analysis"
    _write_tissue_raw(raw_path)

    analysis = analyze_benchmark_results(
        tissue_raw_path=raw_path,
        output_dir=output_dir,
        scenarios=_sample_scenarios(),
    )

    breakdown_rows = list(csv.DictReader(analysis.output_paths.scenario_type_csv.open()))
    tissue_breakdown = [row for row in breakdown_rows if row["agent_name"] == "neuraxon_tissue"]
    assert {row["scenario_type"] for row in tissue_breakdown} == {
        "simple_tool_call",
        "missing_params_tool_call",
        "failed_tool_call",
    }
    assert all(row["run_count"] == "2" for row in tissue_breakdown)

    stat_rows = list(csv.DictReader(analysis.output_paths.statistical_tests_csv.open()))
    assert {row["baseline_agent"] for row in stat_rows} == {"random", "always_execute"}
    assert all(row["metric"] == "accuracy" for row in stat_rows)
    assert all(row["p_value_approx"] for row in stat_rows)
    assert all(row["significant_at_0_05"] in {"true", "false"} for row in stat_rows)

    tissue_summary = next(
        summary for summary in analysis.agent_summaries if summary.agent_name == "neuraxon_tissue"
    )
    assert tissue_summary.recovery_time_mean == 1.0
    assert tissue_summary.learning_curve_start_accuracy == 1.0
    assert tissue_summary.learning_curve_end_accuracy == 0.5
