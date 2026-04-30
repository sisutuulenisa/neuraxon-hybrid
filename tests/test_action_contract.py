"""Tests for aligning decoded actions with benchmark action labels."""

from __future__ import annotations

from dataclasses import dataclass

from neuraxon_agent.action import ActionDecoder, AgentAction
from neuraxon_agent.action_contract import (
    ACTION_DECODER_TO_BENCHMARK_ACTION,
    benchmark_action_coverage,
    normalize_benchmark_action,
)
from neuraxon_agent.benchmark import BenchmarkHarness, BenchmarkScenario
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS


@dataclass(frozen=True)
class _FakeState:
    dopamine: float = 0.0
    serotonin: float = 0.0
    acetylcholine: float = 0.0
    norepinephrine: float = 0.0


class _FixedActionAgent:
    def __init__(self, action: AgentAction) -> None:
        self._action = action

    def observe(self, observation: dict) -> None:
        self.observation = observation

    def think(self, steps: int = 10) -> AgentAction:
        return self._action

    def modulate(self, outcome: str) -> dict[str, float]:
        self.outcome = outcome
        return {}

    @property
    def state(self) -> _FakeState:
        return _FakeState()


def test_action_contract_maps_decoder_outputs_to_benchmark_vocabulary() -> None:
    assert ACTION_DECODER_TO_BENCHMARK_ACTION == {
        "PROCEED": "execute",
        "PAUSE": "query",
        "RETRY": "retry",
        "ESCALATE": "assertive",
        "EXPLORE": "explore",
        "CAUTIOUS": "cautious",
    }

    for decoder_action, benchmark_action in ACTION_DECODER_TO_BENCHMARK_ACTION.items():
        assert normalize_benchmark_action(decoder_action) == benchmark_action

    for benchmark_action in MOCK_AGENT_ACTIONS:
        assert normalize_benchmark_action(benchmark_action) == benchmark_action


def test_action_contract_covers_every_defined_decoder_action() -> None:
    coverage = benchmark_action_coverage(MOCK_AGENT_ACTIONS)

    assert coverage.decoder_actions == set(ActionDecoder.get_all_defined_actions())
    assert coverage.unmapped_decoder_actions == set()
    assert coverage.covered_benchmark_actions == {
        "execute",
        "query",
        "retry",
        "explore",
        "assertive",
        "cautious",
    }
    assert coverage.unreachable_benchmark_actions == set()


def test_benchmark_harness_scores_normalized_decoder_actions() -> None:
    scenario = BenchmarkScenario(
        name="normalized-proceed",
        scenario_type="contract",
        observation_sequence=[{"tool_result": "success"}],
        expected_optimal_action="execute",
        expected_actions=("execute",),
        difficulty=1.0,
    )
    harness = BenchmarkHarness(
        tissue_factory=lambda: _FixedActionAgent(
            AgentAction(actie_type="PROCEED", confidence=1.0, raw_output=(1,))
        )
    )

    report = harness.run([scenario])
    result = report.results[0]

    assert result.decoded_action == "PROCEED"
    assert result.action == "execute"
    assert result.expected_optimal_action == "execute"
    assert result.outcome == "success"
    assert report.success_count == 1


def test_benchmark_harness_keeps_unreachable_actions_visible() -> None:
    scenario = BenchmarkScenario(
        name="cautious-unreachable",
        scenario_type="contract",
        observation_sequence=[{"tool_result": "timeout"}],
        expected_optimal_action="cautious",
        expected_actions=("cautious",),
        difficulty=1.0,
    )
    harness = BenchmarkHarness(
        tissue_factory=lambda: _FixedActionAgent(
            AgentAction(actie_type="PAUSE", confidence=1.0, raw_output=(0,))
        )
    )

    result = harness.run([scenario]).results[0]

    assert result.decoded_action == "PAUSE"
    assert result.action == "query"
    assert result.outcome == "failure"
