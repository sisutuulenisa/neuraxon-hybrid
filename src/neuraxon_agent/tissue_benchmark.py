"""Run Neuraxon tissue benchmarks over built-in scenarios."""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

from neuraxon_agent.action_contract import normalize_benchmark_action
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
    dynamics_samples: list[dict[str, Any]]
    criticality_metrics: dict[str, float]
    modulation_effect: dict[str, float]
    decoded_action: str | None = None
    normalized_benchmark_action: str | None = None
    raw_decoder_output: list[int] | None = None
    action_source: str = "semantic_bridge"
    policy_mode: str = "semantic_bridge"


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
    policy_mode: str = "semantic_bridge"

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


@dataclass(frozen=True)
class PolicyAblationBenchmarkReport:
    """Benchmark bundle separating semantic-bridge and raw-network modes."""

    reports: dict[str, TissueBenchmarkReport]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report dictionary."""
        return {"reports": {mode: report.to_dict() for mode, report in self.reports.items()}}

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return this report as JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def write_json(self, path: str | Path) -> Path:
        """Write ablation benchmark data to *path* and return the path."""
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
    policy_mode: str = "semantic_bridge",
) -> TissueBenchmarkReport:
    """Run Neuraxon ``AgentTissue`` over scenarios for multiple seeds.

    By default this runs all built-in mock-agent scenarios across five seeds,
    producing at least 500 raw runs when the default scenario set has 100+
    scenarios. If ``output_path`` is provided, the raw report is also written as
    JSON for downstream metrics and visualization steps.
    """
    if steps_per_observation < 1:
        raise ValueError("steps_per_observation must be >= 1")
    if policy_mode not in {"semantic_bridge", "raw_network", "semantic_coverage_audit"}:
        raise ValueError(
            "policy_mode must be one of: semantic_bridge, raw_network, semantic_coverage_audit"
        )

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
            policy_mode=policy_mode,
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
        policy_mode=policy_mode,
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def run_policy_ablation_benchmark(
    scenarios: list[BenchmarkScenario] | None = None,
    *,
    seeds: Iterable[int] = DEFAULT_BENCHMARK_SEEDS,
    steps_per_observation: int = 10,
    params: NetworkParameters | None = None,
    output_path: str | Path | None = None,
) -> PolicyAblationBenchmarkReport:
    """Run benchmark slices for semantic bridge, raw network, and coverage audit modes."""
    seed_list = list(seeds)
    reports = {
        mode: run_neuraxon_tissue_benchmark(
            scenarios=scenarios,
            seeds=seed_list,
            steps_per_observation=steps_per_observation,
            params=params,
            policy_mode=mode,
        )
        for mode in ("semantic_bridge", "raw_network", "semantic_coverage_audit")
    }
    report = PolicyAblationBenchmarkReport(reports=reports)
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
    policy_mode: str,
) -> TissueBenchmarkResult:
    """Run one scenario while isolating global RNG state."""
    rng_state = random.getstate()
    try:
        random.seed(_scenario_seed(seed, scenario_index))
        tissue = AgentTissue(params, semantic_policy_enabled=policy_mode != "raw_network")
        start = perf_counter()
        action = None
        dynamics_samples: list[dict[str, Any]] = []
        previous_states: list[int] | None = None
        for observation_index, observation in enumerate(scenario.observation_sequence):
            tissue.observe(observation)
            for step_index in range(steps_per_observation):
                tissue.network.simulate_step()
                sample, previous_states = _capture_dynamics_sample(
                    tissue,
                    observation_index=observation_index,
                    step_index=step_index,
                    previous_states=previous_states,
                )
                dynamics_samples.append(sample)
            action = tissue.think(steps=0)
        if action is None:
            raise ValueError(f"scenario {scenario.name!r} has no observations")
        benchmark_action = normalize_benchmark_action(action.actie_type)
        expected_action = normalize_benchmark_action(scenario.expected_optimal_action)
        outcome = _score_action(benchmark_action, expected_action)
        modulation_effect = _apply_modulation_and_capture_effect(
            tissue,
            outcome=outcome,
            benchmark_action=benchmark_action,
        )
        elapsed = perf_counter() - start
    finally:
        random.setstate(rng_state)

    state = tissue.state
    raw_decoder_action = tissue.last_raw_decoder_action
    return TissueBenchmarkResult(
        seed=seed,
        scenario_name=scenario.name,
        scenario_type=scenario.scenario_type,
        expected_optimal_action=scenario.expected_optimal_action,
        difficulty=scenario.difficulty,
        observation_count=len(scenario.observation_sequence),
        action=benchmark_action,
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
        dynamics_samples=dynamics_samples,
        criticality_metrics=_summarize_criticality(dynamics_samples),
        modulation_effect=modulation_effect,
        decoded_action=action.actie_type,
        normalized_benchmark_action=benchmark_action,
        raw_decoder_output=(
            list(raw_decoder_action.raw_output) if raw_decoder_action is not None else None
        ),
        action_source=tissue.last_action_source or "raw_network",
        policy_mode=policy_mode,
    )


def _capture_dynamics_sample(
    tissue: AgentTissue,
    *,
    observation_index: int,
    step_index: int,
    previous_states: list[int] | None,
) -> tuple[dict[str, Any], list[int]]:
    """Capture deterministic per-step tissue dynamics without touching vendor code."""
    state = tissue.state
    all_states = _flat_trinary_states(tissue)
    distribution = _trinary_distribution(all_states)
    active_count = distribution["negative"] + distribution["positive"]
    previous_active_count = (
        sum(1 for value in previous_states if value != 0) if previous_states is not None else 0
    )
    changed_fraction = _changed_fraction(previous_states, all_states)
    sample = {
        "observation_index": observation_index,
        "step_index": step_index,
        "step_count": state.step_count,
        "activity": state.activity,
        "energy": state.energy,
        "active_count": active_count,
        "previous_active_count": previous_active_count,
        "changed_fraction": changed_fraction,
        "trinary_distribution": distribution,
        "neutral_state_occupancy": distribution["neutral"] / max(len(all_states), 1),
        "neuromodulator_levels": {
            "dopamine": state.dopamine,
            "serotonin": state.serotonin,
            "acetylcholine": state.acetylcholine,
            "norepinephrine": state.norepinephrine,
        },
    }
    return sample, all_states


def _flat_trinary_states(tissue: AgentTissue) -> list[int]:
    all_states: list[int] = []
    for group in tissue.network.get_all_states().values():
        all_states.extend(int(value) for value in group)
    return all_states


def _trinary_distribution(states: list[int]) -> dict[str, int]:
    return {
        "negative": sum(1 for value in states if value < 0),
        "neutral": sum(1 for value in states if value == 0),
        "positive": sum(1 for value in states if value > 0),
    }


def _changed_fraction(previous_states: list[int] | None, states: list[int]) -> float:
    if previous_states is None or not states:
        return 0.0
    paired = zip(previous_states, states)
    changed = sum(1 for before, after in paired if before != after)
    return changed / max(min(len(previous_states), len(states)), 1)


def _apply_modulation_and_capture_effect(
    tissue: AgentTissue,
    *,
    outcome: str,
    benchmark_action: str,
) -> dict[str, float]:
    before = {key: float(value) for key, value in tissue.network.neuromodulators.items()}
    tissue.modulate(outcome)
    after = {key: float(value) for key, value in tissue.network.neuromodulators.items()}
    post_action = tissue.think(steps=0)
    normalized_post_action = normalize_benchmark_action(post_action.actie_type)
    effect = {f"{key}_delta": after.get(key, 0.0) - before.get(key, 0.0) for key in after}
    effect["action_changed"] = 1.0 if normalized_post_action != benchmark_action else 0.0
    return effect


def _summarize_criticality(samples: list[dict[str, Any]]) -> dict[str, float]:
    activities = [float(sample["activity"]) for sample in samples]
    energies = [float(sample["energy"]) for sample in samples]
    neutral_occupancies = [float(sample["neutral_state_occupancy"]) for sample in samples]
    changed_fractions = [float(sample["changed_fraction"]) for sample in samples]
    branching_ratios = [
        float(sample["active_count"]) / float(sample["previous_active_count"])
        for sample in samples
        if float(sample["previous_active_count"]) > 0.0
    ]
    return {
        "activity_variance": _population_variance(activities),
        "transition_entropy": _binary_entropy(_mean(changed_fractions)),
        "neutral_state_occupancy": _mean(neutral_occupancies),
        "branching_ratio": _mean(branching_ratios),
        "energy_mean": _mean(energies),
    }


def _population_variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _binary_entropy(probability: float) -> float:
    p = min(1.0, max(0.0, probability))
    if p in {0.0, 1.0}:
        return 0.0
    return -(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _scenario_seed(seed: int, scenario_index: int) -> int:
    """Derive a deterministic per-scenario seed from a run seed."""
    return seed * 1_000_003 + scenario_index


def _score_action(action: str, expected_optimal_action: str) -> str:
    """Map action equality to benchmark outcome label."""
    return "success" if action == expected_optimal_action else "failure"
