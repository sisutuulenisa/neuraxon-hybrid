"""Run Neuraxon tissue benchmarks over built-in scenarios."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

from neuraxon_agent.benchmark import BenchmarkScenario
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters

DEFAULT_BENCHMARK_SEEDS = (0, 1, 2, 3, 4)
DEFAULT_TISSUE_BENCHMARK_PATH = Path("benchmarks/results/neuraxon_tissue_raw.json")


@dataclass(frozen=True)
class TissueBenchmarkResult:
    """Raw result for one Neuraxon tissue scenario/seed run."""

    seed: int
    scenario_name: str
    scenario_type: str
    expected_optimal_action: str
    difficulty: float
    observation_count: int
    action: str
    confidence: float
    outcome: str
    elapsed_seconds: float
    state: dict[str, float | int]
    neuromodulator_levels: dict[str, float]


@dataclass(frozen=True)
class TissueBenchmarkReport:
    """Raw multi-seed Neuraxon tissue benchmark report."""

    agent_name: str
    scenario_count: int
    seed_count: int
    run_count: int
    success_count: int
    total_elapsed_seconds: float
    results: list[TissueBenchmarkResult]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report dictionary."""
        return asdict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return this report as JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def write_json(self, path: str | Path) -> Path:
        """Write raw benchmark data to *path* and return the path."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json() + "\n")
        return output_path


def run_neuraxon_tissue_benchmark(
    scenarios: list[BenchmarkScenario] | None = None,
    *,
    seeds: Iterable[int] = DEFAULT_BENCHMARK_SEEDS,
    steps_per_observation: int = 10,
    params: NetworkParameters | None = None,
    output_path: str | Path | None = None,
) -> TissueBenchmarkReport:
    """Run Neuraxon ``AgentTissue`` over scenarios for multiple seeds.

    By default this runs all built-in mock-agent scenarios across five seeds,
    producing at least 500 raw runs when the default scenario set has 100+
    scenarios. If ``output_path`` is provided, the raw report is also written as
    JSON for downstream metrics and visualization steps.
    """
    if steps_per_observation < 1:
        raise ValueError("steps_per_observation must be >= 1")

    scenario_list = scenarios if scenarios is not None else load_mock_agent_scenarios()
    seed_list = list(seeds)
    if not seed_list:
        raise ValueError("at least one seed is required")

    start = perf_counter()
    results = [
        _run_one_seeded_scenario(
            scenario=scenario,
            seed=seed,
            scenario_index=scenario_index,
            steps_per_observation=steps_per_observation,
            params=params,
        )
        for seed in seed_list
        for scenario_index, scenario in enumerate(scenario_list)
    ]
    total_elapsed = perf_counter() - start

    report = TissueBenchmarkReport(
        agent_name="neuraxon_tissue",
        scenario_count=len(scenario_list),
        seed_count=len(seed_list),
        run_count=len(results),
        success_count=sum(1 for result in results if result.outcome == "success"),
        total_elapsed_seconds=total_elapsed,
        results=results,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def _run_one_seeded_scenario(
    *,
    scenario: BenchmarkScenario,
    seed: int,
    scenario_index: int,
    steps_per_observation: int,
    params: NetworkParameters | None,
) -> TissueBenchmarkResult:
    """Run one scenario while isolating global RNG state."""
    rng_state = random.getstate()
    try:
        random.seed(_scenario_seed(seed, scenario_index))
        tissue = AgentTissue(params)
        start = perf_counter()
        action = None
        for observation in scenario.observation_sequence:
            tissue.observe(observation)
            action = tissue.think(steps=steps_per_observation)
        if action is None:
            raise ValueError(f"scenario {scenario.name!r} has no observations")
        outcome = _score_action(action.actie_type, scenario.expected_optimal_action)
        tissue.modulate(outcome)
        elapsed = perf_counter() - start
    finally:
        random.setstate(rng_state)

    state = tissue.state
    return TissueBenchmarkResult(
        seed=seed,
        scenario_name=scenario.name,
        scenario_type=scenario.scenario_type,
        expected_optimal_action=scenario.expected_optimal_action,
        difficulty=scenario.difficulty,
        observation_count=len(scenario.observation_sequence),
        action=action.actie_type,
        confidence=action.confidence,
        outcome=outcome,
        elapsed_seconds=elapsed,
        state={
            "energy": state.energy,
            "activity": state.activity,
            "step_count": state.step_count,
            "num_neurons": state.num_neurons,
            "num_synapses": state.num_synapses,
        },
        neuromodulator_levels={
            "dopamine": state.dopamine,
            "serotonin": state.serotonin,
            "acetylcholine": state.acetylcholine,
            "norepinephrine": state.norepinephrine,
        },
    )


def _scenario_seed(seed: int, scenario_index: int) -> int:
    """Derive a deterministic per-scenario seed from a run seed."""
    return seed * 1_000_003 + scenario_index


def _score_action(action: str, expected_optimal_action: str) -> str:
    """Map action equality to benchmark outcome label."""
    return "success" if action == expected_optimal_action else "failure"
