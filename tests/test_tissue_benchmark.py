"""Tests for running Neuraxon tissue across benchmark scenarios."""

from __future__ import annotations

import json

from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue_benchmark import run_neuraxon_tissue_benchmark
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def test_neuraxon_tissue_benchmark_runs_each_scenario_for_each_seed() -> None:
    scenarios = load_mock_agent_scenarios()[:3]

    report = run_neuraxon_tissue_benchmark(
        scenarios=scenarios,
        seeds=[0, 1],
        steps_per_observation=1,
        params=NetworkParameters(
            num_input_neurons=3,
            num_hidden_neurons=5,
            num_output_neurons=2,
        ),
    )

    assert report.agent_name == "neuraxon_tissue"
    assert report.scenario_count == 3
    assert report.seed_count == 2
    assert report.run_count == 6
    assert len(report.results) == 6
    assert {result.seed for result in report.results} == {0, 1}
    assert {result.scenario_name for result in report.results} == {
        scenario.name for scenario in scenarios
    }


def test_neuraxon_tissue_benchmark_collects_complete_raw_metrics() -> None:
    scenario = load_mock_agent_scenarios()[:1]

    report = run_neuraxon_tissue_benchmark(
        scenarios=scenario,
        seeds=[42],
        steps_per_observation=1,
        params=NetworkParameters(
            num_input_neurons=3,
            num_hidden_neurons=5,
            num_output_neurons=2,
        ),
    )

    result = report.results[0]
    assert result.seed == 42
    assert result.scenario_name == scenario[0].name
    assert result.scenario_type == scenario[0].scenario_type
    assert result.expected_optimal_action == scenario[0].expected_optimal_action
    assert result.observation_count == len(scenario[0].observation_sequence)
    assert result.action
    assert 0.0 <= result.confidence <= 1.0
    assert result.outcome in {"success", "failure"}
    assert result.elapsed_seconds >= 0.0
    assert set(result.neuromodulator_levels) == {
        "dopamine",
        "serotonin",
        "acetylcholine",
        "norepinephrine",
    }
    assert set(result.state) == {
        "energy",
        "activity",
        "step_count",
        "num_neurons",
        "num_synapses",
    }


def test_neuraxon_tissue_benchmark_default_run_has_at_least_500_runs() -> None:
    report = run_neuraxon_tissue_benchmark(steps_per_observation=1)

    assert report.scenario_count >= 100
    assert report.seed_count == 5
    assert report.run_count >= 500
    assert len(report.results) == report.run_count


def test_neuraxon_tissue_benchmark_exports_raw_json(tmp_path) -> None:
    output_path = tmp_path / "neuraxon-tissue-raw.json"

    report = run_neuraxon_tissue_benchmark(
        scenarios=load_mock_agent_scenarios()[:2],
        seeds=[0, 1],
        steps_per_observation=1,
        output_path=output_path,
        params=NetworkParameters(
            num_input_neurons=3,
            num_hidden_neurons=5,
            num_output_neurons=2,
        ),
    )

    payload = json.loads(output_path.read_text())
    assert payload == report.to_dict()
    assert payload["agent_name"] == "neuraxon_tissue"
    assert payload["run_count"] == 4
    assert len(payload["results"]) == 4
