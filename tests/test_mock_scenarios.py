"""Tests for built-in mock agent benchmark scenarios."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from neuraxon_agent.benchmark import BenchmarkScenario
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS, load_mock_agent_scenarios

SCENARIO_PATH = Path("benchmarks/scenarios/mock_agent_scenarios.json")
SCENARIO_TYPES = {
    "simple_tool_call",
    "missing_params_tool_call",
    "failed_tool_call",
    "ambiguous_prompt",
    "complex_multi_step",
    "error_recovery",
    "success_streak",
}


def difficulty_bucket(difficulty: float) -> str:
    if difficulty <= 2:
        return "easy"
    if difficulty == 3:
        return "medium"
    return "hard"


def test_mock_agent_scenarios_json_exists_and_loads() -> None:
    assert SCENARIO_PATH.exists()

    scenarios = load_mock_agent_scenarios(SCENARIO_PATH)

    assert len(scenarios) >= 100
    assert all(isinstance(scenario, BenchmarkScenario) for scenario in scenarios)


def test_mock_agent_scenarios_are_unique_and_cover_all_types() -> None:
    scenarios = load_mock_agent_scenarios(SCENARIO_PATH)

    names = [scenario.name for scenario in scenarios]
    assert len(names) == len(set(names))

    type_counts = Counter(scenario.scenario_type for scenario in scenarios)
    assert set(type_counts) == SCENARIO_TYPES
    assert all(count >= 20 for count in type_counts.values())


def test_mock_agent_scenarios_have_required_shape() -> None:
    scenarios = load_mock_agent_scenarios(SCENARIO_PATH)

    for scenario in scenarios:
        assert scenario.observation_sequence
        assert scenario.expected_optimal_action
        assert scenario.expected_actions
        assert 1 <= scenario.difficulty <= 5
        assert scenario.expected_optimal_action in scenario.expected_actions


def test_mock_agent_scenarios_cover_all_six_action_types() -> None:
    scenarios = load_mock_agent_scenarios(SCENARIO_PATH)

    covered_actions = {
        expected_action for scenario in scenarios for expected_action in scenario.expected_actions
    }

    assert covered_actions == MOCK_AGENT_ACTIONS


def test_mock_agent_scenarios_match_required_difficulty_distribution() -> None:
    scenarios = load_mock_agent_scenarios(SCENARIO_PATH)

    buckets = Counter(difficulty_bucket(scenario.difficulty) for scenario in scenarios)
    total = len(scenarios)

    assert buckets["easy"] / total == 0.4
    assert buckets["medium"] / total == 0.4
    assert buckets["hard"] / total == 0.2
