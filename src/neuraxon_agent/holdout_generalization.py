"""Holdout/noisy generalization benchmark utilities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from neuraxon_agent.baselines import run_baseline_benchmarks
from neuraxon_agent.benchmark import BenchmarkReport, BenchmarkScenario
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue_benchmark import TissueBenchmarkReport, run_neuraxon_tissue_benchmark

DEFAULT_HOLDOUT_GENERALIZATION_PATH = Path(
    "benchmarks/results/holdout_noisy_generalization.json"
)


@dataclass(frozen=True)
class AgentGeneralizationScore:
    """Compact score for one agent on the holdout/noisy benchmark."""

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
class HoldoutGeneralizationReport:
    """Summary report for holdout/noisy semantic policy generalization."""

    scenario_count: int
    seed_count: int
    neuraxon_tissue: AgentGeneralizationScore
    baselines: dict[str, AgentGeneralizationScore]
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
    """
    scenarios = base_scenarios if base_scenarios is not None else load_mock_agent_scenarios()
    return [
        _holdout_variant(scenario=scenario, index=index)
        for index, scenario in enumerate(scenarios)
    ]


def run_holdout_generalization_benchmark(
    *,
    scenarios: list[BenchmarkScenario] | None = None,
    seeds: Iterable[int] = (0,),
    steps_per_observation: int = 1,
    output_path: str | Path | None = None,
) -> HoldoutGeneralizationReport:
    """Run Neuraxon tissue and baselines on holdout/noisy scenarios."""
    holdout_scenarios = scenarios if scenarios is not None else generate_holdout_noisy_scenarios()
    seed_list = list(seeds)
    tissue_report = run_neuraxon_tissue_benchmark(
        holdout_scenarios,
        seeds=seed_list,
        steps_per_observation=steps_per_observation,
    )
    baseline_reports = run_baseline_benchmarks(holdout_scenarios)
    report = _summarize_generalization(
        tissue_report=tissue_report,
        baseline_reports=baseline_reports,
        scenario_count=len(holdout_scenarios),
        seed_count=len(seed_list),
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


def _summarize_generalization(
    *,
    tissue_report: TissueBenchmarkReport,
    baseline_reports: dict[str, BenchmarkReport],
    scenario_count: int,
    seed_count: int,
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
        decision=decision,
        interpretation=(
            "This tests the semantic policy bridge against deterministic "
            "holdout/noisy variants, not autonomous learning by the raw "
            "Neuraxon network dynamics."
        ),
    )
