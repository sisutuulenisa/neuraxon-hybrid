"""Tests for semantic observation routing in the tissue decision layer."""

from __future__ import annotations

from neuraxon_agent.action_contract import normalize_benchmark_action
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.semantic_policy import SemanticTissuePolicy
from neuraxon_agent.tissue import AgentTissue


def _first_observation(scenario_type: str) -> dict:
    for scenario in load_mock_agent_scenarios():
        if scenario.scenario_type == scenario_type:
            return dict(scenario.observation_sequence[-1])
    raise AssertionError(f"missing scenario type: {scenario_type}")


def test_semantic_policy_routes_representative_mock_observations() -> None:
    policy = SemanticTissuePolicy()

    expected_by_type = {
        "simple_tool_call": "execute",
        "missing_params_tool_call": "query",
        "failed_tool_call": "retry",
        "ambiguous_prompt": "explore",
        "error_recovery": "cautious",
        "complex_multi_step": "execute",
        "success_streak": "assertive",
    }

    for scenario_type, expected_action in expected_by_type.items():
        action = policy.decide(_first_observation(scenario_type))
        assert action is not None, scenario_type
        assert normalize_benchmark_action(action.actie_type) == expected_action
        assert action.confidence == 1.0


def test_agent_tissue_uses_semantic_policy_before_random_network_output() -> None:
    tissue = AgentTissue()
    tissue.observe(_first_observation("ambiguous_prompt"))

    action = tissue.think(steps=0)

    assert action.actie_type == "EXPLORE"
    assert normalize_benchmark_action(action.actie_type) == "explore"


def test_semantic_policy_covers_full_mock_dataset() -> None:
    policy = SemanticTissuePolicy()
    scenarios = load_mock_agent_scenarios()

    successes = 0
    for scenario in scenarios:
        action = policy.decide(dict(scenario.observation_sequence[-1]))
        assert action is not None, scenario.name
        if normalize_benchmark_action(action.actie_type) == scenario.expected_optimal_action:
            successes += 1

    assert successes == len(scenarios)
