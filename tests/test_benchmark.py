"""Tests for benchmark scenario harness."""

from __future__ import annotations

import json

from neuraxon_agent.benchmark import BenchmarkHarness, BenchmarkScenario
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def make_tissue() -> AgentTissue:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    return AgentTissue(params)


def test_benchmark_scenario_dataclass_keeps_required_fields() -> None:
    scenario = BenchmarkScenario(
        name="simple-success",
        observation_sequence=[{"type": "prompt", "content": "hello"}],
        expected_optimal_action="PAUSE",
        difficulty=0.25,
    )

    assert scenario.name == "simple-success"
    assert scenario.observation_sequence == [{"type": "prompt", "content": "hello"}]
    assert scenario.expected_optimal_action == "PAUSE"
    assert scenario.difficulty == 0.25


def test_harness_collects_action_confidence_outcome_timing_and_modulators() -> None:
    harness = BenchmarkHarness(tissue_factory=make_tissue, steps_per_observation=1)
    scenario = BenchmarkScenario(
        name="one-step",
        observation_sequence=[{"type": "prompt", "content": "hello"}],
        expected_optimal_action="PAUSE",
        difficulty=0.1,
    )

    report = harness.run([scenario])

    assert report.scenario_count == 1
    assert report.run_count == 1
    result = report.results[0]
    assert result.scenario_name == "one-step"
    assert result.action in {
        "execute",
        "query",
        "retry",
        "assertive",
        "explore",
        "cautious",
    }
    assert result.decoded_action in {
        "PROCEED",
        "PAUSE",
        "RETRY",
        "ESCALATE",
        "EXPLORE",
        "CAUTIOUS",
    }
    assert 0.0 <= result.confidence <= 1.0
    assert result.outcome in {"success", "failure"}
    assert result.elapsed_seconds >= 0.0
    assert set(result.neuromodulator_levels) == {
        "dopamine",
        "serotonin",
        "acetylcholine",
        "norepinephrine",
    }


def test_harness_exports_valid_json_with_all_required_fields() -> None:
    harness = BenchmarkHarness(tissue_factory=make_tissue, steps_per_observation=1)
    scenario = BenchmarkScenario(
        name="json-export",
        observation_sequence=[{"type": "prompt", "content": "hello"}],
        expected_optimal_action="PAUSE",
        difficulty=0.2,
    )

    payload = harness.run([scenario]).to_json()
    data = json.loads(payload)

    assert data["scenario_count"] == 1
    assert data["run_count"] == 1
    assert data["success_count"] in {0, 1}
    assert isinstance(data["total_elapsed_seconds"], float)
    result = data["results"][0]
    assert result["scenario_name"] == "json-export"
    assert result["expected_optimal_action"] == "PAUSE"
    assert result["difficulty"] == 0.2
    assert "action" in result
    assert "decoded_action" in result
    assert "confidence" in result
    assert "outcome" in result
    assert "elapsed_seconds" in result
    assert "neuromodulator_levels" in result
    assert "observation_count" in result


def test_harness_runs_100_scenarios_without_crashing() -> None:
    scenarios = [
        BenchmarkScenario(
            name=f"scenario-{i}",
            observation_sequence=[{"type": "prompt", "content": f"item {i}"}],
            expected_optimal_action="PAUSE",
            difficulty=(i % 10) / 10,
        )
        for i in range(100)
    ]
    harness = BenchmarkHarness(tissue_factory=make_tissue, steps_per_observation=1)

    report = harness.run(scenarios)

    assert report.scenario_count == 100
    assert report.run_count == 100
    assert len(report.results) == 100
    json.loads(report.to_json())
