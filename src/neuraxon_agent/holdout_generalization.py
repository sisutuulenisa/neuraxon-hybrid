"""Holdout/noisy and temporal generalization benchmark utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from neuraxon_agent.action import AgentAction
from neuraxon_agent.baselines import run_baseline_benchmarks
from neuraxon_agent.benchmark import (
    BenchmarkHarness,
    BenchmarkReport,
    BenchmarkScenario,
    TissueFactory,
)
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.semantic_policy import SemanticTissuePolicy
from neuraxon_agent.tissue_benchmark import TissueBenchmarkReport, run_neuraxon_tissue_benchmark

DEFAULT_HOLDOUT_GENERALIZATION_PATH = Path(
    "benchmarks/results/holdout_noisy_generalization.json"
)


@dataclass(frozen=True)
class AgentGeneralizationScore:
    """Compact score for one agent on a generalization benchmark."""

    success_count: int
    run_count: int
    success_rate: float

    @classmethod
    def from_counts(cls, success_count: int, run_count: int) -> AgentGeneralizationScore:
        return cls(
            success_count=success_count,
            run_count=run_count,
            success_rate=success_count / run_count if run_count else 0.0,
        )


@dataclass(frozen=True)
class SemanticPolicyCoverage:
    """How many final observations are directly solved by SemanticTissuePolicy."""

    scenario_count: int
    covered_count: int
    coverage_rate: float
    warning: str


@dataclass(frozen=True)
class TemporalDynamicsBenchmark:
    """Benchmark slice that hides the final action oracle in a temporal probe."""

    scenario_count: int
    seed_count: int
    neuraxon_tissue: AgentGeneralizationScore
    baselines: dict[str, AgentGeneralizationScore]
    interpretation: str


@dataclass(frozen=True)
class HoldoutGeneralizationReport:
    """Summary report for holdout/noisy semantic policy generalization."""

    scenario_count: int
    seed_count: int
    neuraxon_tissue: AgentGeneralizationScore
    baselines: dict[str, AgentGeneralizationScore]
    semantic_policy_coverage: SemanticPolicyCoverage
    temporal_dynamics: TemporalDynamicsBenchmark
    decision: str
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return this report as JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def write_json(self, path: str | Path) -> Path:
        """Write the report to *path* and return the path."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json() + "\n")
        return output_path


def generate_holdout_noisy_scenarios(
    base_scenarios: list[BenchmarkScenario] | None = None,
) -> list[BenchmarkScenario]:
    """Generate deterministic semantic variants of the mock benchmark scenarios.

    The variants intentionally remove the exact scenario-type labels that the
    first mock benchmark used. They preserve action semantics through more
    general fields such as missing parameters, retryability, ambiguity, risk and
    success streaks, while adding irrelevant noise fields.

    This is still not a true Neuraxon/Aigarth-style generalization test: the
    final observation remains directly decidable by the explicit semantic policy
    bridge. ``measure_semantic_policy_coverage`` makes that limitation visible.
    """
    scenarios = base_scenarios if base_scenarios is not None else load_mock_agent_scenarios()
    return [
        _holdout_variant(scenario=scenario, index=index)
        for index, scenario in enumerate(scenarios)
    ]


def generate_temporal_dynamics_scenarios() -> list[BenchmarkScenario]:
    """Return generated NIA-inspired temporal scenarios with no final action oracle.

    Qubic's NIA volumes emphasise continuous-time state, trinary neutral buffers,
    neuromodulatory context and plasticity gates. A benchmark that is solved from
    one explicit final observation does not test those claims. These generated
    scenarios therefore put the evidence in prior observations and end with an
    identical ``temporal_decision_probe`` shape. Counterfactual pairs share the
    exact final observation while prior sequence dynamics require different
    actions. Perturbation variants add irrelevant/noisy fields around the same
    latent temporal state.
    """
    definitions: list[tuple[str, str, list[dict[str, Any]]]] = [
        (
            "stable_complete_workflow",
            "execute",
            [
                {"signal": "task_context", "stability": 0.8, "novelty": 0.1},
                {"signal": "parameters_complete", "missing_count": 0, "risk": "low"},
            ],
        ),
        (
            "subthreshold_information_gap",
            "query",
            [
                {"signal": "task_context", "stability": 0.4, "novelty": 0.3},
                {"signal": "parameters_partial", "missing_count": 2, "risk": "low"},
            ],
        ),
        (
            "recoverable_transient_failure",
            "retry",
            [
                {"signal": "tool_outcome", "failure_count": 1, "transient": True},
                {"signal": "modulatory_context", "norepinephrine": 0.7, "risk": "low"},
            ],
        ),
        (
            "novel_ambiguous_environment",
            "explore",
            [
                {"signal": "task_context", "stability": 0.2, "novelty": 0.9},
                {"signal": "choice_space", "option_count": 4, "ambiguity": 0.8},
            ],
        ),
        (
            "high_risk_repeated_failure",
            "cautious",
            [
                {"signal": "tool_outcome", "failure_count": 3, "transient": False},
                {"signal": "modulatory_context", "serotonin": 0.8, "risk": "high"},
            ],
        ),
        (
            "stable_success_attractor",
            "assertive",
            [
                {"signal": "task_context", "stability": 0.9, "novelty": 0.1},
                {"signal": "outcome_history", "success_count": 4, "failure_count": 0},
            ],
        ),
    ]
    final_probe = {
        "intent": "temporal_decision_probe",
        "probe": "choose_action_from_prior_dynamics",
    }
    scenarios: list[BenchmarkScenario] = []
    for seed in range(3):
        for target_length in (3, 4, 5):
            for action_index, (name, expected_action, prefix) in enumerate(definitions):
                expanded_prefix = _expand_temporal_prefix(
                    prefix=prefix,
                    expected_action=expected_action,
                    seed=seed,
                    target_prefix_length=target_length - 1,
                )
                for variant in ("counterfactual", "noise_perturbation"):
                    scenario_prefix = [dict(observation) for observation in expanded_prefix]
                    if variant == "noise_perturbation":
                        scenario_prefix = _add_temporal_noise(
                            scenario_prefix,
                            seed=seed,
                            action_index=action_index,
                            target_length=target_length,
                        )
                    scenarios.append(
                        BenchmarkScenario(
                            name=(
                                "temporal_dynamics_"
                                f"seed{seed}_len{target_length}_{variant}_{name}"
                            ),
                            observation_sequence=[*scenario_prefix, dict(final_probe)],
                            expected_optimal_action=expected_action,
                            difficulty=0.85 + (0.03 * seed) + (0.01 * (target_length - 3)),
                            scenario_type=f"temporal_{variant}",
                            expected_actions=(expected_action,),
                        )
                    )
    return scenarios


def measure_semantic_policy_coverage(
    scenarios: list[BenchmarkScenario],
    policy: SemanticTissuePolicy | None = None,
) -> SemanticPolicyCoverage:
    """Measure whether final observations are directly covered by the policy bridge."""
    semantic_policy = policy or SemanticTissuePolicy()
    covered_count = sum(
        1
        for scenario in scenarios
        if semantic_policy.decide(scenario.observation_sequence[-1]) is not None
    )
    scenario_count = len(scenarios)
    coverage_rate = covered_count / scenario_count if scenario_count else 0.0
    warning = (
        "semantic_policy_oracle_coverage_high: final observations are directly "
        "decidable by the explicit policy bridge, so perfect accuracy is not "
        "evidence of continuous-time Neuraxon dynamics."
        if coverage_rate >= 0.95
        else "semantic_policy_oracle_coverage_low"
    )
    return SemanticPolicyCoverage(
        scenario_count=scenario_count,
        covered_count=covered_count,
        coverage_rate=coverage_rate,
        warning=warning,
    )


def run_holdout_generalization_benchmark(
    *,
    scenarios: list[BenchmarkScenario] | None = None,
    seeds: Iterable[int] = (0,),
    steps_per_observation: int = 1,
    output_path: str | Path | None = None,
) -> HoldoutGeneralizationReport:
    """Run Neuraxon tissue and baselines on holdout/noisy + temporal scenarios."""
    holdout_scenarios = scenarios if scenarios is not None else generate_holdout_noisy_scenarios()
    seed_list = list(seeds)
    tissue_report = run_neuraxon_tissue_benchmark(
        holdout_scenarios,
        seeds=seed_list,
        steps_per_observation=steps_per_observation,
    )
    baseline_reports = run_baseline_benchmarks(holdout_scenarios)
    temporal_scenarios = generate_temporal_dynamics_scenarios()
    temporal_report = run_neuraxon_tissue_benchmark(
        temporal_scenarios,
        seeds=seed_list,
        steps_per_observation=steps_per_observation,
    )
    temporal_baselines = _run_temporal_baseline_benchmarks(temporal_scenarios)
    report = _summarize_generalization(
        tissue_report=tissue_report,
        baseline_reports=baseline_reports,
        scenario_count=len(holdout_scenarios),
        seed_count=len(seed_list),
        semantic_policy_coverage=measure_semantic_policy_coverage(holdout_scenarios),
        temporal_dynamics=_summarize_temporal_dynamics(
            temporal_report=temporal_report,
            baseline_reports=temporal_baselines,
            scenario_count=len(temporal_scenarios),
            seed_count=len(seed_list),
        ),
    )
    if output_path is not None:
        report.write_json(output_path)
    return report


def _holdout_variant(*, scenario: BenchmarkScenario, index: int) -> BenchmarkScenario:
    final_observation = dict(scenario.observation_sequence[-1])
    expected_action = scenario.expected_optimal_action
    final_observation.pop("context", None)
    final_observation.pop("request_id", None)
    final_observation["scenario_type"] = f"holdout_{expected_action}"
    final_observation["noise_marker"] = f"deterministic-noise-{index:03d}"
    final_observation["irrelevant_ui_state"] = {
        "theme": "dark" if index % 2 else "light",
        "sidebar_open": index % 3 == 0,
    }
    final_observation["confidence_signal"] = _noisy_confidence(final_observation, index)

    return BenchmarkScenario(
        name=f"holdout_noisy_{scenario.name}",
        observation_sequence=[final_observation],
        expected_optimal_action=expected_action,
        difficulty=scenario.difficulty,
        scenario_type=f"holdout_{expected_action}",
        expected_actions=scenario.expected_actions,
    )


def _noisy_confidence(observation: dict[str, Any], index: int) -> float:
    existing = observation.get("confidence_signal")
    if existing is not None:
        return float(existing)
    return round(0.35 + ((index % 7) * 0.07), 2)


def _expand_temporal_prefix(
    *,
    prefix: list[dict[str, Any]],
    expected_action: str,
    seed: int,
    target_prefix_length: int,
) -> list[dict[str, Any]]:
    expanded = [dict(observation) for observation in prefix]
    while len(expanded) < target_prefix_length:
        expanded.insert(
            -1,
            {
                "signal": "temporal_buffer",
                "trinary_state": 0,
                "subthreshold_charge": round(0.2 + (0.1 * seed), 2),
                "latent_action_hint": expected_action,
            },
        )
    return expanded[:target_prefix_length]


def _add_temporal_noise(
    prefix: list[dict[str, Any]],
    *,
    seed: int,
    action_index: int,
    target_length: int,
) -> list[dict[str, Any]]:
    noisy_prefix = [dict(observation) for observation in prefix]
    for observation_index, observation in enumerate(noisy_prefix):
        observation["irrelevant_sensor_drift"] = round(
            ((seed + 1) * (action_index + 2) * (observation_index + 3)) % 17 / 100,
            2,
        )
        observation["ui_noise"] = {
            "theme": "dark" if (seed + observation_index) % 2 else "light",
            "panel": f"panel-{target_length}-{action_index}",
        }
    return noisy_prefix


class _SequenceAwareBaselineAgent:
    def __init__(self, mode: str) -> None:
        self._mode = mode
        self._observations: list[dict[str, Any]] = []
        self._think_count = 0
        self._modulation_count = 0

    def observe(self, observation: dict[str, Any]) -> None:
        self._observations.append(observation)

    def think(self, steps: int = 10) -> AgentAction:
        del steps
        self._think_count += 1
        if self._mode in {"last_observation_only", "semantic_policy_only"}:
            action = _infer_temporal_action(self._observations[-1]) or "semantic_uncovered"
        elif self._mode == "sequence_majority":
            action = _sequence_majority_action(self._observations)
        else:  # pragma: no cover - defensive constructor guard
            raise ValueError(f"unknown temporal baseline mode: {self._mode}")
        return AgentAction(actie_type=action, confidence=1.0, raw_output=())

    def modulate(self, outcome: str) -> dict[str, float]:
        del outcome
        self._modulation_count += 1
        return {}

    @property
    def state(self) -> _TemporalBaselineState:
        return _TemporalBaselineState(
            observation_count=len(self._observations),
            think_count=self._think_count,
            modulation_count=self._modulation_count,
        )


@dataclass(frozen=True)
class _TemporalBaselineState:
    observation_count: int
    think_count: int
    modulation_count: int
    dopamine: float = 0.0
    serotonin: float = 0.0
    acetylcholine: float = 0.0
    norepinephrine: float = 0.0


def _run_temporal_baseline_benchmarks(
    scenarios: list[BenchmarkScenario],
) -> dict[str, BenchmarkReport]:
    reports = run_baseline_benchmarks(scenarios)
    factories: dict[str, TissueFactory] = {
        mode: _temporal_baseline_factory(mode)
        for mode in (
            "last_observation_only",
            "sequence_majority",
            "semantic_policy_only",
        )
    }
    reports.update(BenchmarkHarness(steps_per_observation=1).run_agents(scenarios, factories))
    return reports


def _temporal_baseline_factory(mode: str) -> TissueFactory:
    def factory() -> _SequenceAwareBaselineAgent:
        return _SequenceAwareBaselineAgent(mode)

    return factory


def _sequence_majority_action(observations: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for observation in observations:
        action = _infer_temporal_action(observation)
        if action is not None:
            counts[action] = counts.get(action, 0) + 1
    if not counts:
        return "semantic_uncovered"
    return max(sorted(counts), key=lambda action: counts[action])


def _infer_temporal_action(observation: dict[str, Any]) -> str | None:
    signal = observation.get("signal")
    if signal == "parameters_complete" and observation.get("missing_count") == 0:
        return "execute"
    if signal == "parameters_partial" and int(observation.get("missing_count", 0)) > 0:
        return "query"
    if signal == "tool_outcome":
        failure_count = int(observation.get("failure_count", 0))
        if failure_count >= 3 or observation.get("transient") is False:
            return "cautious"
        if failure_count >= 1 and observation.get("transient") is True:
            return "retry"
    if signal == "choice_space" and float(observation.get("ambiguity", 0.0)) >= 0.5:
        return "explore"
    if signal == "outcome_history" and int(observation.get("success_count", 0)) >= 3:
        return "assertive"
    if observation.get("risk") == "high":
        return "cautious"
    return None


def _summarize_temporal_dynamics(
    *,
    temporal_report: TissueBenchmarkReport,
    baseline_reports: dict[str, BenchmarkReport],
    scenario_count: int,
    seed_count: int,
) -> TemporalDynamicsBenchmark:
    return TemporalDynamicsBenchmark(
        scenario_count=scenario_count,
        seed_count=seed_count,
        neuraxon_tissue=AgentGeneralizationScore.from_counts(
            temporal_report.success_count,
            temporal_report.run_count,
        ),
        baselines={
            name: AgentGeneralizationScore.from_counts(report.success_count, report.run_count)
            for name, report in baseline_reports.items()
        },
        interpretation=(
            "Temporal probe inspired by NIA Vol. 1/2/3/5/7: final observations "
            "hide explicit action cues, so success must come from temporal/stateful "
            "Neuraxon evidence such as continuous time, state carry-over, trinary "
            "buffering and modulation-like dynamics."
        ),
    )


def _summarize_generalization(
    *,
    tissue_report: TissueBenchmarkReport,
    baseline_reports: dict[str, BenchmarkReport],
    scenario_count: int,
    seed_count: int,
    semantic_policy_coverage: SemanticPolicyCoverage,
    temporal_dynamics: TemporalDynamicsBenchmark,
) -> HoldoutGeneralizationReport:
    tissue_score = AgentGeneralizationScore.from_counts(
        tissue_report.success_count,
        tissue_report.run_count,
    )
    baseline_scores = {
        name: AgentGeneralizationScore.from_counts(report.success_count, report.run_count)
        for name, report in baseline_reports.items()
    }
    always_execute_score = baseline_scores["always_execute"]
    if semantic_policy_coverage.coverage_rate >= 0.95 or tissue_score.success_rate >= 0.999:
        decision = "needs_temporal_dynamics_evidence"
    else:
        decision = (
            "pass_holdout_noisy_generalization"
            if tissue_score.success_rate > always_execute_score.success_rate
            else "fail_holdout_noisy_generalization"
        )
    return HoldoutGeneralizationReport(
        scenario_count=scenario_count,
        seed_count=seed_count,
        neuraxon_tissue=tissue_score,
        baselines=baseline_scores,
        semantic_policy_coverage=semantic_policy_coverage,
        temporal_dynamics=temporal_dynamics,
        decision=decision,
        interpretation=(
            "The 100% holdout/noisy score is a semantic policy bridge result, not "
            "evidence of the continuous time, stateful, neuromodulated and "
            "edge-of-chaos dynamics described in Qubic's NIA articles. Treat it "
            "as an oracle-coverage warning and require temporal dynamics evidence "
            "before claiming Neuraxon generalization."
        ),
    )
