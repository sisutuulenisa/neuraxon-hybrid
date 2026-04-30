"""Diagnose Neuraxon tissue action mapping failures."""

from __future__ import annotations

import csv
import itertools
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from neuraxon_agent.action import ActionDecoder
from neuraxon_agent.action_contract import (
    benchmark_action_coverage,
    normalize_benchmark_action,
)
from neuraxon_agent.benchmark import BenchmarkScenario
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.tissue_benchmark import DEFAULT_BENCHMARK_SEEDS
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters

DEFAULT_DIAGNOSTICS_DIR = Path("benchmarks/results/diagnostics")


@dataclass(frozen=True)
class DiagnosticOutputPaths:
    """Files emitted by a diagnostic run."""

    trace_json: Path
    confusion_csv: Path
    report_md: Path


@dataclass(frozen=True)
class ObservationTrace:
    """Per-observation data captured at a pipeline boundary."""

    observation: dict[str, Any]
    encoded_input: list[int]
    raw_output_after_think: tuple[int, ...]


@dataclass(frozen=True)
class ActionMappingTrace:
    """One traced scenario/seed run through perception, tissue, and decoder."""

    seed: int
    scenario_name: str
    scenario_type: str
    expected_action: str
    decoded_action: str
    normalized_action: str
    raw_output: tuple[int, ...]
    confidence: float
    outcome: str
    observation_trace: list[ObservationTrace]


@dataclass(frozen=True)
class ActionMappingDiagnostics:
    """Summary of action-mapping diagnostics."""

    root_cause: str
    run_count: int
    success_count: int
    expected_actions: set[str]
    decoder_actions: set[str]
    normalized_decoder_actions: set[str]
    observed_actions: set[str]
    missing_decoder_actions: set[str]
    missing_observed_expected_actions: set[str]
    confusion_matrix: dict[str, dict[str, int]]
    traces: list[ActionMappingTrace]
    output_paths: DiagnosticOutputPaths

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        payload = asdict(self)
        payload["expected_actions"] = sorted(self.expected_actions)
        payload["decoder_actions"] = sorted(self.decoder_actions)
        payload["normalized_decoder_actions"] = sorted(self.normalized_decoder_actions)
        payload["observed_actions"] = sorted(self.observed_actions)
        payload["missing_decoder_actions"] = sorted(self.missing_decoder_actions)
        payload["missing_observed_expected_actions"] = sorted(
            self.missing_observed_expected_actions
        )
        payload["output_paths"] = {
            "trace_json": str(self.output_paths.trace_json),
            "confusion_csv": str(self.output_paths.confusion_csv),
            "report_md": str(self.output_paths.report_md),
        }
        return payload


def diagnose_tissue_action_mapping(
    scenarios: list[BenchmarkScenario] | None = None,
    *,
    seeds: Iterable[int] = DEFAULT_BENCHMARK_SEEDS,
    steps_per_observation: int = 10,
    params: NetworkParameters | None = None,
    output_dir: str | Path = DEFAULT_DIAGNOSTICS_DIR,
) -> ActionMappingDiagnostics:
    """Trace the tissue benchmark pipeline and explain action mismatches.

    The diagnostic deliberately does not change scoring or decoder behavior. It
    captures the current pipeline so a follow-up fix can target the real failure
    point instead of guessing.
    """
    if steps_per_observation < 1:
        raise ValueError("steps_per_observation must be >= 1")

    scenario_list = scenarios if scenarios is not None else load_mock_agent_scenarios()
    seed_list = list(seeds)
    if not seed_list:
        raise ValueError("at least one seed is required")

    network_params = params or NetworkParameters()
    traces = [
        _trace_one_scenario(
            scenario=scenario,
            seed=seed,
            scenario_index=scenario_index,
            steps_per_observation=steps_per_observation,
            params=network_params,
        )
        for seed in seed_list
        for scenario_index, scenario in enumerate(scenario_list)
    ]

    expected_actions = {scenario.expected_optimal_action for scenario in scenario_list}
    coverage = benchmark_action_coverage(expected_actions)
    decoder_actions = coverage.decoder_actions
    normalized_decoder_actions = {normalize_benchmark_action(action) for action in decoder_actions}
    observed_actions = {trace.normalized_action for trace in traces}
    confusion_matrix = _build_confusion_matrix(traces)
    missing_decoder_actions = coverage.unreachable_benchmark_actions
    missing_observed_expected_actions = expected_actions - observed_actions
    success_count = sum(1 for trace in traces if trace.outcome == "success")
    root_cause = _classify_root_cause(
        missing_decoder_actions=missing_decoder_actions,
        missing_observed_expected_actions=missing_observed_expected_actions,
        success_count=success_count,
    )

    output_paths = DiagnosticOutputPaths(
        trace_json=Path(output_dir) / "action_mapping_traces.json",
        confusion_csv=Path(output_dir) / "action_confusion_matrix.csv",
        report_md=Path(output_dir) / "action_mapping_diagnostic_report.md",
    )
    diagnostics = ActionMappingDiagnostics(
        root_cause=root_cause,
        run_count=len(traces),
        success_count=success_count,
        expected_actions=expected_actions,
        decoder_actions=decoder_actions,
        normalized_decoder_actions=normalized_decoder_actions,
        observed_actions=observed_actions,
        missing_decoder_actions=missing_decoder_actions,
        missing_observed_expected_actions=missing_observed_expected_actions,
        confusion_matrix=confusion_matrix,
        traces=traces,
        output_paths=output_paths,
    )
    _write_outputs(diagnostics)
    return diagnostics


def enumerate_decoder_actions(num_output_neurons: int) -> set[str]:
    """Return all action strings reachable from the current ActionDecoder."""
    decoder = ActionDecoder(num_output_neurons)
    actions: set[str] = set()
    for raw_output in itertools.product((-1, 0, 1), repeat=num_output_neurons):
        actions.add(decoder.decode(list(raw_output)).actie_type)
    return actions


def _trace_one_scenario(
    *,
    scenario: BenchmarkScenario,
    seed: int,
    scenario_index: int,
    steps_per_observation: int,
    params: NetworkParameters,
) -> ActionMappingTrace:
    """Trace one scenario while isolating global RNG state."""
    rng_state = random.getstate()
    try:
        random.seed(_scenario_seed(seed, scenario_index))
        tissue = AgentTissue(params)
        observation_trace: list[ObservationTrace] = []
        action = None
        for observation in scenario.observation_sequence:
            tissue.observe(observation)
            action = tissue.think(steps=steps_per_observation)
            encoded_input = tissue.encoder.get_history()[-1]
            observation_trace.append(
                ObservationTrace(
                    observation=dict(observation),
                    encoded_input=encoded_input,
                    raw_output_after_think=action.raw_output,
                )
            )
        if action is None:
            raise ValueError(f"scenario {scenario.name!r} has no observations")
    finally:
        random.setstate(rng_state)

    normalized_action = normalize_benchmark_action(action.actie_type)
    outcome = "success" if normalized_action == scenario.expected_optimal_action else "failure"
    return ActionMappingTrace(
        seed=seed,
        scenario_name=scenario.name,
        scenario_type=scenario.scenario_type,
        expected_action=scenario.expected_optimal_action,
        decoded_action=action.actie_type,
        normalized_action=normalized_action,
        raw_output=action.raw_output,
        confidence=action.confidence,
        outcome=outcome,
        observation_trace=observation_trace,
    )


def _scenario_seed(seed: int, scenario_index: int) -> int:
    """Derive the same deterministic per-scenario seed as the benchmark runner."""
    return seed * 1_000_003 + scenario_index


def _build_confusion_matrix(
    traces: list[ActionMappingTrace],
) -> dict[str, dict[str, int]]:
    """Build expected-action -> decoded-action counts."""
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    for trace in traces:
        matrix[trace.expected_action][trace.decoded_action] += 1
    return {expected: dict(actual_counts) for expected, actual_counts in matrix.items()}


def _classify_root_cause(
    *,
    missing_decoder_actions: set[str],
    missing_observed_expected_actions: set[str],
    success_count: int,
) -> str:
    """Classify the dominant diagnosis from reachability and run evidence."""
    if missing_decoder_actions and success_count == 0:
        return "action_vocabulary_mismatch"
    if missing_observed_expected_actions:
        return "network_never_reaches_expected_actions"
    if success_count == 0:
        return "mapping_or_scoring_mismatch"
    return "partially_working"


def _write_outputs(diagnostics: ActionMappingDiagnostics) -> None:
    """Write trace JSON, confusion CSV, and markdown report."""
    diagnostics.output_paths.trace_json.parent.mkdir(parents=True, exist_ok=True)
    diagnostics.output_paths.trace_json.write_text(
        json.dumps(diagnostics.to_dict(), indent=2, sort_keys=True) + "\n"
    )
    _write_confusion_csv(diagnostics)
    diagnostics.output_paths.report_md.write_text(_render_report(diagnostics))


def _write_confusion_csv(diagnostics: ActionMappingDiagnostics) -> None:
    """Write confusion matrix in long CSV format."""
    with diagnostics.output_paths.confusion_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["expected_action", "decoded_action", "count"],
        )
        writer.writeheader()
        for expected_action in sorted(diagnostics.confusion_matrix):
            actual_counts = diagnostics.confusion_matrix[expected_action]
            for decoded_action, count in sorted(actual_counts.items()):
                writer.writerow(
                    {
                        "expected_action": expected_action,
                        "decoded_action": decoded_action,
                        "count": count,
                    }
                )


def _render_report(diagnostics: ActionMappingDiagnostics) -> str:
    """Render the diagnostic conclusion as Markdown."""
    expected = ", ".join(sorted(diagnostics.expected_actions))
    decoder = ", ".join(sorted(diagnostics.decoder_actions))
    normalized_decoder = ", ".join(sorted(diagnostics.normalized_decoder_actions))
    observed = ", ".join(sorted(diagnostics.observed_actions))
    missing_decoder = ", ".join(sorted(diagnostics.missing_decoder_actions)) or "none"
    missing_observed = ", ".join(sorted(diagnostics.missing_observed_expected_actions)) or "none"

    lines = [
        "# Neuraxon Tissue Action Mapping Diagnostic",
        "",
        "## Verdict",
        f"- Root cause classification: `{diagnostics.root_cause}`.",
        f"- Runs inspected: {diagnostics.run_count}.",
        f"- Successful runs under current benchmark scoring: {diagnostics.success_count}.",
        "",
        "## Core Finding",
        f"- The mock benchmark expects: `{expected}`.",
        f"- ActionDecoder emits: `{decoder}`.",
        f"- ActionDecoder normalized benchmark actions: `{normalized_decoder}`.",
        f"- The traced tissue runs observed after normalization: `{observed}`.",
        f"- Expected actions missing from decoder vocabulary: `{missing_decoder}`.",
        f"- Expected actions not observed in traced runs: `{missing_observed}`.",
        "",
        "Benchmark scoring now uses the normalized benchmark action contract, "
        "so the previous pure string-vocabulary mismatch is no longer the main "
        "failure mode. Any remaining misses are now evidence about which normalized "
        "actions the tissue actually reaches, before learning, memory, or visual "
        "perception enter the picture.",
        "",
        "## Non-goals for the next fix",
        "- Do not implement memory persistence yet; persistence would only store "
        "decisions from a mismatched action contract.",
        "- Do not add visual perception yet; the action contract must be fixed on "
        "simple mock scenarios first.",
        "",
        "## Recommended follow-up",
        "1. Re-run the full benchmark and compare normalized Neuraxon accuracy "
        "against random and always-execute baselines.",
        "2. Diagnose remaining decision-quality gaps separately from scoring compatibility.",
        "3. Only revisit memory persistence or visual perception after the simple "
        "mock-scenario action policy beats baseline behavior.",
        "",
        "## Artefacts",
        f"- Trace JSON: `{diagnostics.output_paths.trace_json}`",
        f"- Confusion CSV: `{diagnostics.output_paths.confusion_csv}`",
        "",
    ]
    return "\n".join(lines)
