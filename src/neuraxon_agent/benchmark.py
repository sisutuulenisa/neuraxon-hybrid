"""Benchmark harness for Neuraxon agent scenarios.

The harness runs deterministic scenario definitions through an ``AgentTissue``
instance and records raw per-scenario metrics for later analysis.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any, Callable

from neuraxon_agent.tissue import AgentTissue

TissueFactory = Callable[[], AgentTissue]


@dataclass(frozen=True)
class BenchmarkScenario:
    """A benchmark scenario for evaluating an agent tissue.

    Attributes
    ----------
    name:
        Human-readable scenario identifier.
    observation_sequence:
        Ordered observations that will be fed into the tissue.
    expected_optimal_action:
        Action type considered optimal for the final observation.
    difficulty:
        Difficulty score for grouping/reporting benchmark runs.
    """

    name: str
    observation_sequence: list[dict[str, Any]]
    expected_optimal_action: str
    difficulty: float


@dataclass(frozen=True)
class BenchmarkResult:
    """Raw metrics collected for one scenario run."""

    scenario_name: str
    expected_optimal_action: str
    difficulty: float
    observation_count: int
    action: str
    confidence: float
    outcome: str
    elapsed_seconds: float
    neuromodulator_levels: dict[str, float]


@dataclass(frozen=True)
class BenchmarkReport:
    """Complete benchmark report for a harness run."""

    scenario_count: int
    run_count: int
    success_count: int
    total_elapsed_seconds: float
    results: list[BenchmarkResult]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this report."""
        return asdict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Export raw benchmark results as valid JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


class BenchmarkHarness:
    """Run benchmark scenarios and collect per-run metrics.

    Parameters
    ----------
    tissue_factory:
        Factory called once per scenario to create a fresh tissue. Passing a
        factory keeps benchmark scenarios isolated from each other.
    steps_per_observation:
        Number of tissue simulation steps to run after each observation.
    """

    def __init__(
        self,
        tissue_factory: TissueFactory | None = None,
        steps_per_observation: int = 10,
    ) -> None:
        if steps_per_observation < 1:
            raise ValueError("steps_per_observation must be >= 1")
        self.tissue_factory = tissue_factory or AgentTissue
        self.steps_per_observation = steps_per_observation

    def run(self, scenarios: list[BenchmarkScenario]) -> BenchmarkReport:
        """Run all *scenarios* and return a raw metrics report."""
        start = perf_counter()
        results = [self.run_one(scenario) for scenario in scenarios]
        total_elapsed = perf_counter() - start
        success_count = sum(1 for result in results if result.outcome == "success")
        return BenchmarkReport(
            scenario_count=len(scenarios),
            run_count=len(results),
            success_count=success_count,
            total_elapsed_seconds=total_elapsed,
            results=results,
        )

    def run_one(self, scenario: BenchmarkScenario) -> BenchmarkResult:
        """Run one scenario against a fresh tissue and collect raw metrics."""
        if not scenario.observation_sequence:
            raise ValueError("scenario observation_sequence must not be empty")

        tissue = self.tissue_factory()
        start = perf_counter()
        action = None
        for observation in scenario.observation_sequence:
            tissue.observe(observation)
            action = tissue.think(steps=self.steps_per_observation)

        if action is None:  # defensive; empty sequences are rejected above
            raise RuntimeError("scenario produced no action")

        outcome = self._score_action(action.actie_type, scenario.expected_optimal_action)
        tissue.modulate(outcome)
        elapsed = perf_counter() - start
        state = tissue.state

        return BenchmarkResult(
            scenario_name=scenario.name,
            expected_optimal_action=scenario.expected_optimal_action,
            difficulty=scenario.difficulty,
            observation_count=len(scenario.observation_sequence),
            action=action.actie_type,
            confidence=action.confidence,
            outcome=outcome,
            elapsed_seconds=elapsed,
            neuromodulator_levels={
                "dopamine": state.dopamine,
                "serotonin": state.serotonin,
                "acetylcholine": state.acetylcholine,
                "norepinephrine": state.norepinephrine,
            },
        )

    @staticmethod
    def _score_action(action: str, expected_optimal_action: str) -> str:
        """Map an action match to a simple benchmark outcome label."""
        return "success" if action == expected_optimal_action else "failure"
