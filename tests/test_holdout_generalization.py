"""Holdout/noisy benchmark coverage for the semantic tissue policy."""

from __future__ import annotations

from neuraxon_agent.baselines import run_baseline_benchmarks
from neuraxon_agent.holdout_generalization import (
    generate_holdout_noisy_scenarios,
    run_holdout_generalization_benchmark,
)
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue_benchmark import run_neuraxon_tissue_benchmark


def test_holdout_noisy_scenarios_are_deterministic_and_semantically_balanced() -> None:
    base_scenarios = load_mock_agent_scenarios()

    first = generate_holdout_noisy_scenarios(base_scenarios)
    second = generate_holdout_noisy_scenarios(base_scenarios)

    assert first == second
    assert len(first) == len(base_scenarios)
    assert {scenario.expected_optimal_action for scenario in first} == {
        "execute",
        "query",
        "retry",
        "explore",
        "cautious",
        "assertive",
    }
    assert all(scenario.name.startswith("holdout_noisy_") for scenario in first)
    assert all(scenario.scenario_type.startswith("holdout_") for scenario in first)
    assert all("noise_marker" in scenario.observation_sequence[-1] for scenario in first)


def test_holdout_noisy_scenarios_do_not_rely_on_original_scenario_type_labels() -> None:
    scenarios = generate_holdout_noisy_scenarios(load_mock_agent_scenarios())

    observed_types = {
        scenario.observation_sequence[-1].get("scenario_type") for scenario in scenarios
    }

    assert "simple_tool_call" not in observed_types
    assert "complex_multi_step" not in observed_types
    assert "error_recovery" not in observed_types


def test_semantic_tissue_beats_always_execute_on_holdout_noisy_benchmark() -> None:
    scenarios = generate_holdout_noisy_scenarios(load_mock_agent_scenarios())

    tissue_report = run_neuraxon_tissue_benchmark(scenarios, seeds=(0,), steps_per_observation=1)
    baseline_reports = run_baseline_benchmarks(scenarios)

    assert tissue_report.success_count > baseline_reports["always_execute"].success_count
    assert tissue_report.success_count == tissue_report.run_count


def test_holdout_generalization_summary_is_serializable_and_critical() -> None:
    report = run_holdout_generalization_benchmark(seeds=(0,), steps_per_observation=1)

    payload = report.to_dict()

    assert payload["scenario_count"] == 140
    assert payload["neuraxon_tissue"]["success_rate"] == 1.0
    assert (
        payload["baselines"]["always_execute"]["success_rate"]
        < payload["neuraxon_tissue"]["success_rate"]
    )
    assert payload["decision"] == "pass_holdout_noisy_generalization"
    assert "semantic policy bridge" in payload["interpretation"]
