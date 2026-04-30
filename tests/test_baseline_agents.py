"""Tests for mock benchmark baseline agents."""

from __future__ import annotations

from neuraxon_agent.baselines import (
    AlwaysExecuteAgent,
    BaselineAgentState,
    RandomAgent,
    run_baseline_benchmarks,
)
from neuraxon_agent.benchmark import BenchmarkHarness, BenchmarkScenario
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS, load_mock_agent_scenarios
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def test_random_agent_implements_tissue_interface_and_uses_known_actions() -> None:
    agent = RandomAgent(seed=7)

    agent.observe({"type": "tool_request", "tool_name": "calendar"})
    action = agent.think(steps=5)
    deltas = agent.modulate("success")

    assert action.actie_type in MOCK_AGENT_ACTIONS
    assert 0.0 <= action.confidence <= 1.0
    assert action.raw_output == ()
    assert deltas == {}
    assert isinstance(agent.state, BaselineAgentState)
    assert agent.state.observation_count == 1
    assert agent.state.think_count == 1
    assert agent.state.modulation_count == 1


def test_always_execute_agent_implements_tissue_interface_and_ignores_input() -> None:
    agent = AlwaysExecuteAgent()

    agent.observe({"type": "ambiguous_prompt", "content": "maybe do a thing"})
    first = agent.think()
    agent.observe({"type": "failed_tool_call", "error": "timeout"})
    second = agent.think(steps=99)

    assert first.actie_type == "execute"
    assert second.actie_type == "execute"
    assert first.confidence == 1.0
    assert second.confidence == 1.0
    assert agent.modulate("failure") == {}
    assert agent.state.observation_count == 2
    assert agent.state.think_count == 2


def test_benchmark_harness_can_run_multiple_agent_factories() -> None:
    scenarios = [
        BenchmarkScenario(
            name="execute-case",
            observation_sequence=[{"type": "tool_request"}],
            expected_optimal_action="execute",
            difficulty=1,
        ),
        BenchmarkScenario(
            name="retry-case",
            observation_sequence=[{"type": "failed_tool_call"}],
            expected_optimal_action="retry",
            difficulty=3,
        ),
    ]
    harness = BenchmarkHarness()

    reports = harness.run_agents(
        scenarios,
        {
            "neuraxon": lambda: AgentTissue(
                NetworkParameters(
                    num_input_neurons=3,
                    num_hidden_neurons=5,
                    num_output_neurons=2,
                )
            ),
            "random": lambda: RandomAgent(seed=3),
            "always_execute": AlwaysExecuteAgent,
        },
    )

    assert set(reports) == {"neuraxon", "random", "always_execute"}
    assert reports["neuraxon"].scenario_count == 2
    assert reports["random"].scenario_count == 2
    assert reports["always_execute"].scenario_count == 2
    assert reports["always_execute"].success_count == 1


def test_baseline_runner_executes_all_mock_scenarios_with_expected_accuracy_shape() -> None:
    scenarios = load_mock_agent_scenarios()

    reports = run_baseline_benchmarks(scenarios, random_seed=0)

    assert set(reports) == {"random", "always_execute"}
    random_accuracy = reports["random"].success_count / reports["random"].run_count
    always_execute_accuracy = (
        reports["always_execute"].success_count / reports["always_execute"].run_count
    )

    assert 0.12 <= random_accuracy <= 0.22
    assert always_execute_accuracy == 40 / 140

    always_execute_results = reports["always_execute"].results
    execute_results = [r for r in always_execute_results if r.expected_optimal_action == "execute"]
    non_execute_results = [
        r for r in always_execute_results if r.expected_optimal_action != "execute"
    ]
    assert all(result.outcome == "success" for result in execute_results)
    assert all(result.outcome == "failure" for result in non_execute_results)
