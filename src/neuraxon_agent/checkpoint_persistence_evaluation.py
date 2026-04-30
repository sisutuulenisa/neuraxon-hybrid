"""Restart-oriented benchmark for checkpoint persistence decision value."""

from __future__ import annotations

import json
import random
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from neuraxon_agent.action_contract import normalize_benchmark_action
from neuraxon_agent.persistence import CHECKPOINT_SCHEMA_VERSION, PersistenceLoadError
from neuraxon_agent.tissue import AgentTissue

DEFAULT_CHECKPOINT_PERSISTENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "benchmarks"
    / "results"
    / "checkpoint_persistence_value.json"
)
DEFAULT_CHECKPOINT_PERSISTENCE_MARKDOWN_PATH = (
    DEFAULT_CHECKPOINT_PERSISTENCE_PATH.with_suffix(".md")
)

FINAL_PROBE = {
    "intent": "temporal_decision_probe",
    "probe": "choose_action_from_prior_dynamics",
}


@dataclass(frozen=True)
class RestartPersistenceEpisode:
    """Two-episode restart scenario where episode B depends on episode A context."""

    name: str
    episode_a: list[dict[str, Any]]
    episode_b: list[dict[str, Any]]
    expected_action: str
    seed: int


@dataclass(frozen=True)
class RestartPersistenceResult:
    """Outcome for one mode/scenario pair."""

    mode: str
    episode_name: str
    expected_action: str
    action: str | None
    outcome: str
    failure_mode: str | None
    action_source: str | None


@dataclass(frozen=True)
class PersistenceModeMetrics:
    """Aggregated mode-level persistence benchmark metrics."""

    mode: str
    run_count: int
    success_count: int
    success_rate: float
    failure_modes: dict[str, int]


@dataclass(frozen=True)
class CheckpointPersistenceEvaluationReport:
    """Complete checkpoint persistence value report."""

    episode_count: int
    mode_metrics: dict[str, PersistenceModeMetrics]
    persisted_beats_cold_start: bool
    verdict: str
    results: list[RestartPersistenceResult]
    schema_version: int = CHECKPOINT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        payload = asdict(self)
        payload["mode_metrics"] = {
            mode: asdict(metrics) for mode, metrics in self.mode_metrics.items()
        }
        return payload

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return report JSON with deterministic key ordering."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


def generate_restart_persistence_episodes() -> list[RestartPersistenceEpisode]:
    """Return seeded scenarios where episode B needs episode A context."""
    return [
        RestartPersistenceEpisode(
            name="complete_parameters_then_final_probe",
            episode_a=[{"signal": "parameters_complete", "missing_count": 0, "risk": "low"}],
            episode_b=[FINAL_PROBE],
            expected_action="execute",
            seed=101,
        ),
        RestartPersistenceEpisode(
            name="partial_parameters_then_final_probe",
            episode_a=[{"signal": "parameters_partial", "missing_count": 2, "risk": "low"}],
            episode_b=[FINAL_PROBE],
            expected_action="query",
            seed=102,
        ),
        RestartPersistenceEpisode(
            name="transient_tool_failure_then_final_probe",
            episode_a=[{"signal": "tool_outcome", "failure_count": 1, "transient": True}],
            episode_b=[FINAL_PROBE],
            expected_action="retry",
            seed=103,
        ),
        RestartPersistenceEpisode(
            name="ambiguous_choice_then_final_probe",
            episode_a=[{"signal": "choice_space", "ambiguity": 0.8, "risk": "medium"}],
            episode_b=[FINAL_PROBE],
            expected_action="explore",
            seed=104,
        ),
        RestartPersistenceEpisode(
            name="nontransient_tool_failure_then_final_probe",
            episode_a=[{"signal": "tool_outcome", "failure_count": 3, "transient": False}],
            episode_b=[FINAL_PROBE],
            expected_action="cautious",
            seed=105,
        ),
    ]


def run_checkpoint_persistence_evaluation(
    *,
    episodes: list[RestartPersistenceEpisode] | None = None,
    output_path: str | Path | None = DEFAULT_CHECKPOINT_PERSISTENCE_PATH,
    markdown_path: str | Path | None = DEFAULT_CHECKPOINT_PERSISTENCE_MARKDOWN_PATH,
    workspace_dir: str | Path | None = None,
) -> CheckpointPersistenceEvaluationReport:
    """Compare persisted restart behavior with cold-start and bad-checkpoint baselines."""
    scenario_list = episodes or generate_restart_persistence_episodes()
    if not scenario_list:
        raise ValueError("episodes must not be empty")

    if workspace_dir is None:
        with tempfile.TemporaryDirectory(prefix="neuraxon-persistence-eval-") as tmp:
            report = _run_checkpoint_persistence_evaluation(scenario_list, Path(tmp))
    else:
        report = _run_checkpoint_persistence_evaluation(scenario_list, Path(workspace_dir))

    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report.to_json() + "\n", encoding="utf-8")
    if markdown_path is not None:
        target = Path(markdown_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _run_checkpoint_persistence_evaluation(
    episodes: list[RestartPersistenceEpisode], workspace_dir: Path
) -> CheckpointPersistenceEvaluationReport:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    results: list[RestartPersistenceResult] = []
    for episode in episodes:
        results.append(_run_persisted_checkpoint_episode(episode, workspace_dir))
        results.append(_run_cold_start_episode(episode))

    results.extend(_run_bad_checkpoint_baselines(workspace_dir))
    metrics = _summarize(results)
    persisted_rate = metrics["persisted_checkpoint"].success_rate
    cold_rate = metrics["cold_start"].success_rate
    persisted_beats_cold_start = persisted_rate > cold_rate
    verdict = (
        "Persisted checkpoint mode beat cold-start on seeded restart scenarios; "
        "the measured decision value comes from checkpointed runtime temporal context, "
        "not from a standalone raw-network generalization claim."
        if persisted_beats_cold_start
        else "Persistence did not beat cold-start; docs and roadmap should remain conservative."
    )
    return CheckpointPersistenceEvaluationReport(
        episode_count=len(episodes),
        mode_metrics=metrics,
        persisted_beats_cold_start=persisted_beats_cold_start,
        verdict=verdict,
        results=results,
    )


def _run_persisted_checkpoint_episode(
    episode: RestartPersistenceEpisode, workspace_dir: Path
) -> RestartPersistenceResult:
    random.seed(episode.seed)
    checkpoint = workspace_dir / f"{episode.name}.json"
    tissue = AgentTissue()
    for observation in episode.episode_a:
        tissue.observe(observation)
        tissue.think(steps=1)
    tissue.save(str(checkpoint))

    restarted = AgentTissue.load(str(checkpoint))
    return _run_episode_b("persisted_checkpoint", episode, restarted)


def _run_cold_start_episode(episode: RestartPersistenceEpisode) -> RestartPersistenceResult:
    random.seed(episode.seed)
    tissue = AgentTissue()
    return _run_episode_b("cold_start", episode, tissue)


def _run_episode_b(
    mode: str, episode: RestartPersistenceEpisode, tissue: AgentTissue
) -> RestartPersistenceResult:
    action = None
    for observation in episode.episode_b:
        tissue.observe(observation)
        action = tissue.think(steps=1)
    if action is None:
        raise ValueError(f"episode {episode.name} has no episode_b observations")
    actual = normalize_benchmark_action(action.actie_type)
    expected = normalize_benchmark_action(episode.expected_action)
    return RestartPersistenceResult(
        mode=mode,
        episode_name=episode.name,
        expected_action=expected,
        action=actual,
        outcome="success" if actual == expected else "failure",
        failure_mode=None,
        action_source=tissue.last_action_source,
    )


def _run_bad_checkpoint_baselines(workspace_dir: Path) -> list[RestartPersistenceResult]:
    missing = workspace_dir / "missing.json"
    corrupt = workspace_dir / "corrupt.json"
    incompatible = workspace_dir / "incompatible.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    tissue = AgentTissue()
    tissue.save(str(incompatible))
    payload = json.loads(incompatible.read_text(encoding="utf-8"))
    payload["_checkpoint_schema_version"] = CHECKPOINT_SCHEMA_VERSION + 1
    incompatible.write_text(json.dumps(payload), encoding="utf-8")

    return [
        _load_bad_checkpoint("missing_checkpoint", missing),
        _load_bad_checkpoint("corrupt_checkpoint", corrupt),
        _load_bad_checkpoint("incompatible_checkpoint", incompatible),
    ]


def _load_bad_checkpoint(mode: str, path: Path) -> RestartPersistenceResult:
    failure_mode: str | None
    try:
        AgentTissue.load(str(path))
    except FileNotFoundError:
        failure_mode = "missing_checkpoint"
    except PersistenceLoadError as exc:
        text = str(exc).lower()
        failure_mode = "incompatible_checkpoint" if "unsupported" in text else "corrupt_checkpoint"
    else:  # pragma: no cover - defensive guard
        failure_mode = None
    return RestartPersistenceResult(
        mode=mode,
        episode_name=mode,
        expected_action="load_checkpoint",
        action=None,
        outcome="failure" if failure_mode else "success",
        failure_mode=failure_mode,
        action_source=None,
    )


def _summarize(results: list[RestartPersistenceResult]) -> dict[str, PersistenceModeMetrics]:
    modes = [
        "persisted_checkpoint",
        "cold_start",
        "missing_checkpoint",
        "corrupt_checkpoint",
        "incompatible_checkpoint",
    ]
    summary: dict[str, PersistenceModeMetrics] = {}
    for mode in modes:
        mode_results = [result for result in results if result.mode == mode]
        success_count = sum(1 for result in mode_results if result.outcome == "success")
        failure_modes: dict[str, int] = {}
        for result in mode_results:
            if result.failure_mode is not None:
                failure_modes[result.failure_mode] = failure_modes.get(result.failure_mode, 0) + 1
        run_count = len(mode_results)
        summary[mode] = PersistenceModeMetrics(
            mode=mode,
            run_count=run_count,
            success_count=success_count,
            success_rate=round(success_count / run_count, 4) if run_count else 0.0,
            failure_modes=failure_modes,
        )
    return summary


def _render_markdown(report: CheckpointPersistenceEvaluationReport) -> str:
    lines = [
        "# Checkpoint Persistence Decision-Value Evaluation",
        "",
        "## Summary",
        report.verdict,
        "",
        "## Mode comparison",
        "",
        "| Mode | Runs | Successes | Success rate | Failure modes |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for mode, metrics in report.mode_metrics.items():
        failure_modes = ", ".join(
            f"{name}={count}" for name, count in sorted(metrics.failure_modes.items())
        ) or "none"
        lines.append(
            f"| {mode} | {metrics.run_count} | {metrics.success_count} | "
            f"{metrics.success_rate:.2%} | {failure_modes} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "Persisted checkpoints have measured decision value here only when restart restores "
            "the bounded runtime temporal context established during episode A. Cold-start sees "
            "the same episode B probes without that prior context and therefore cannot reliably "
            "choose the seeded action.",
            "",
            "Missing checkpoint, corrupt checkpoint, and incompatible schema baselines are "
            "explicit failure modes rather than silent cold-start successes.",
            "",
            "This remains conservative about raw Neuraxon generalization: the positive result is "
            "restart continuity for checkpointed adapter/runtime state, not proof that the raw "
            "network alone learned a durable policy.",
        ]
    )
    return "\n".join(lines) + "\n"
