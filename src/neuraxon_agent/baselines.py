"""Baseline agents for benchmark comparisons."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from neuraxon_agent.action import AgentAction
from neuraxon_agent.benchmark import (
    BenchmarkHarness,
    BenchmarkReport,
    BenchmarkScenario,
    TissueFactory,
)
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS


@dataclass(frozen=True)
class BaselineAgentState:
    """Observable no-op state for baseline agents.

    Baselines intentionally do not maintain neuromodulator dynamics, but the
    benchmark harness expects a tissue-like ``state`` object. These counters make
    runs observable while keeping dopamine-like fields neutral.
    """

    observation_count: int
    think_count: int
    modulation_count: int
    dopamine: float = 0.0
    serotonin: float = 0.0
    acetylcholine: float = 0.0
    norepinephrine: float = 0.0


class RandomAgent:
    """Baseline that chooses a random action regardless of observation input."""

    def __init__(self, *, seed: int | None = None, actions: set[str] | None = None) -> None:
        self._actions = tuple(sorted(actions or MOCK_AGENT_ACTIONS))
        if not self._actions:
            raise ValueError("RandomAgent requires at least one action")
        self._rng = random.Random(seed)
        self._observation_count = 0
        self._think_count = 0
        self._modulation_count = 0
        self._last_observation: dict[str, Any] | None = None

    def observe(self, observation: dict[str, Any]) -> None:
        """Record that an observation was received."""
        self._last_observation = observation
        self._observation_count += 1

    def think(self, steps: int = 10) -> AgentAction:
        """Return one uniformly sampled action from the mock action space."""
        del steps
        self._think_count += 1
        return AgentAction(
            actie_type=self._rng.choice(self._actions),
            confidence=1 / len(self._actions),
            raw_output=(),
        )

    def modulate(self, outcome: str) -> dict[str, float]:
        """No-op modulation hook matching ``AgentTissue``."""
        del outcome
        self._modulation_count += 1
        return {}

    @property
    def state(self) -> BaselineAgentState:
        """Return observable neutral state for benchmark reporting."""
        return BaselineAgentState(
            observation_count=self._observation_count,
            think_count=self._think_count,
            modulation_count=self._modulation_count,
        )


class AlwaysExecuteAgent:
    """Baseline that always returns ``execute`` regardless of input."""

    def __init__(self) -> None:
        self._observation_count = 0
        self._think_count = 0
        self._modulation_count = 0
        self._last_observation: dict[str, Any] | None = None

    def observe(self, observation: dict[str, Any]) -> None:
        """Record that an observation was received."""
        self._last_observation = observation
        self._observation_count += 1

    def think(self, steps: int = 10) -> AgentAction:
        """Always choose the execute action."""
        del steps
        self._think_count += 1
        return AgentAction(actie_type="execute", confidence=1.0, raw_output=())

    def modulate(self, outcome: str) -> dict[str, float]:
        """No-op modulation hook matching ``AgentTissue``."""
        del outcome
        self._modulation_count += 1
        return {}

    @property
    def state(self) -> BaselineAgentState:
        """Return observable neutral state for benchmark reporting."""
        return BaselineAgentState(
            observation_count=self._observation_count,
            think_count=self._think_count,
            modulation_count=self._modulation_count,
        )


def run_baseline_benchmarks(
    scenarios: list[BenchmarkScenario],
    *,
    random_seed: int | None = 0,
    harness: BenchmarkHarness | None = None,
) -> dict[str, BenchmarkReport]:
    """Run built-in baseline agents over *scenarios*.

    Returns reports keyed by stable agent names so later benchmark/reporting
    steps can compare them with the Neuraxon tissue report.
    """
    runner = harness or BenchmarkHarness()
    seed_source = random.Random(random_seed)
    factories: dict[str, TissueFactory] = {
        "random": lambda: RandomAgent(seed=seed_source.randrange(2**32)),
        "always_execute": AlwaysExecuteAgent,
    }
    return runner.run_agents(scenarios, factories)
