"""Reward-driven multi-episode plasticity benchmark.

This benchmark intentionally separates behaviour changes from internal tissue
state changes. The generated final observation carries only an opaque feedback
cue, so the correct action is not directly readable from a single final
observation. Training episodes apply reward/punishment after the agent acts, and
post-training evaluation replays the same cue observations to measure whether
later decisions changed or improved.
"""

from __future__ import annotations

import json
import random
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from neuraxon_agent.action import AgentAction
from neuraxon_agent.action_contract import normalize_benchmark_action
from neuraxon_agent.baselines import AlwaysExecuteAgent, RandomAgent
from neuraxon_agent.persistence import load_state, save_state
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters

DEFAULT_REWARD_PLASTICITY_PATH = Path("benchmarks/results/reward_plasticity.json")
DEFAULT_REWARD_PLASTICITY_MARKDOWN_PATH = Path("benchmarks/results/reward_plasticity.md")
_REWARD_ACTIONS = ("execute", "query", "retry", "explore")


class PlasticityAgent(Protocol):
    """Minimal agent interface required by the plasticity benchmark."""

    def observe(self, observation: dict[str, Any]) -> None: ...

    def think(self, steps: int = 10) -> AgentAction: ...

    def modulate(self, outcome: str) -> dict[str, float]: ...

    @property
    def state(self) -> Any: ...


@dataclass(frozen=True)
class RewardPlasticityEpisode:
    """One opaque-cue episode for reward-driven learning evaluation."""

    episode_id: str
    feedback_cue: str
    expected_action: str
    training_observation: dict[str, Any]
    final_observation: dict[str, Any]


@dataclass(frozen=True)
class FeedbackEvent:
    """Feedback application evidence for one episode."""

    episode_id: str
    expected_action: str
    action: str
    outcome: str
    neuromodulator_delta: dict[str, float]


@dataclass(frozen=True)
class PlasticityModeMetrics:
    """Before/after behavioural metrics for one benchmark mode."""

    mode: str
    before_accuracy: float
    after_accuracy: float
    accuracy_delta: float
    decision_change_rate: float
    internal_state_changed: bool
    training_feedback_count: int
    before_actions: list[str]
    after_actions: list[str]
    feedback_events: list[FeedbackEvent]


@dataclass(frozen=True)
class RewardPlasticityBenchmarkReport:
    """Complete reward-driven plasticity benchmark report."""

    seed: int
    episode_count: int
    modes: dict[str, PlasticityModeMetrics]
    verdict: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable report dictionary."""
        return asdict(self)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return this report as JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def write_json(self, path: str | Path) -> Path:
        """Write this report to *path* as UTF-8 JSON."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json() + "\n", encoding="utf-8")
        return output_path

    def write_markdown(self, path: str | Path) -> Path:
        """Write a compact human-readable plasticity report."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_render_markdown_report(self), encoding="utf-8")
        return output_path


def generate_reward_plasticity_episodes(
    *,
    seed: int = 0,
    episode_count: int = 24,
) -> list[RewardPlasticityEpisode]:
    """Generate deterministic opaque-cue episodes.

    The training observation contains a cue and reward label, but the final
    observation intentionally omits expected-action fields and known benchmark
    scenario types. A single final observation therefore cannot reveal the
    correct action without prior feedback association.
    """
    if episode_count < 1:
        raise ValueError("episode_count must be >= 1")

    rng = random.Random(seed)
    actions = list(_REWARD_ACTIONS)
    rng.shuffle(actions)
    episodes: list[RewardPlasticityEpisode] = []
    for index in range(episode_count):
        action = actions[index % len(actions)]
        cue = f"cue-{rng.randrange(10_000):04d}-{index % len(actions)}"
        training_observation = {
            "type": "reward_feedback",
            "feedback_cue": cue,
            "reward_signal": "positive_if_action_matches_hidden_cue",
            "episode_index": index,
            "minimal_bridge": True,
        }
        final_observation = {
            "type": "opaque_feedback_cue",
            "feedback_cue": cue,
            "episode_index": index,
            "minimal_bridge": True,
        }
        episodes.append(
            RewardPlasticityEpisode(
                episode_id=f"reward-plasticity-{seed}-{index}",
                feedback_cue=cue,
                expected_action=action,
                training_observation=training_observation,
                final_observation=final_observation,
            )
        )
    return episodes


def run_reward_plasticity_benchmark(
    *,
    seed: int = 0,
    episode_count: int = 24,
    steps_per_observation: int = 10,
    params: NetworkParameters | None = None,
    output_path: str | Path | None = None,
    markdown_path: str | Path | None = None,
) -> RewardPlasticityBenchmarkReport:
    """Run cold, trained, persisted, semantic, raw, and baseline comparisons."""
    if steps_per_observation < 1:
        raise ValueError("steps_per_observation must be >= 1")
    episodes = generate_reward_plasticity_episodes(seed=seed, episode_count=episode_count)
    benchmark_params = params or NetworkParameters()

    modes: dict[str, PlasticityModeMetrics] = {
        "cold_tissue": _evaluate_untrained_mode(
            mode="cold_tissue",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent_factory=lambda: AgentTissue(
                benchmark_params,
                semantic_policy_enabled=False,
                temporal_context_enabled=False,
            ),
        ),
        "feedback_trained_tissue": _evaluate_feedback_trained_mode(
            mode="feedback_trained_tissue",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent=AgentTissue(
                benchmark_params,
                semantic_policy_enabled=False,
                temporal_context_enabled=False,
            ),
        ),
        "raw_network_only": _evaluate_feedback_trained_mode(
            mode="raw_network_only",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent=AgentTissue(
                benchmark_params,
                semantic_policy_enabled=False,
                temporal_context_enabled=False,
            ),
        ),
        "semantic_bridge": _evaluate_feedback_trained_mode(
            mode="semantic_bridge",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent=AgentTissue(
                benchmark_params,
                semantic_policy_enabled=True,
                temporal_context_enabled=True,
            ),
        ),
        "persisted_checkpoint": _evaluate_persisted_checkpoint_mode(
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            params=benchmark_params,
        ),
        "random": _evaluate_feedback_trained_mode(
            mode="random",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent=RandomAgent(seed=seed, actions=set(MOCK_AGENT_ACTIONS)),
        ),
        "always_execute": _evaluate_feedback_trained_mode(
            mode="always_execute",
            episodes=episodes,
            steps_per_observation=steps_per_observation,
            agent=AlwaysExecuteAgent(),
        ),
    }

    report = RewardPlasticityBenchmarkReport(
        seed=seed,
        episode_count=len(episodes),
        modes=modes,
        verdict=_verdict(modes),
        claim_boundary=(
            "No broad Qubic/Neuraxon intelligence claim is made from adapter-only behavior; "
            "this benchmark only reports whether reward feedback changed later decisions."
        ),
    )
    if output_path is not None:
        report.write_json(output_path)
    if markdown_path is not None:
        report.write_markdown(markdown_path)
    return report


def _evaluate_untrained_mode(
    *,
    mode: str,
    episodes: list[RewardPlasticityEpisode],
    steps_per_observation: int,
    agent_factory: Any,
) -> PlasticityModeMetrics:
    before_agent = agent_factory()
    after_agent = agent_factory()
    before_actions = _evaluate_actions(before_agent, episodes, steps_per_observation)
    after_actions = _evaluate_actions(after_agent, episodes, steps_per_observation)
    return _metrics(
        mode=mode,
        episodes=episodes,
        before_actions=before_actions,
        after_actions=after_actions,
        feedback_events=[],
        before_state=_state_signature(before_agent),
        after_state=_state_signature(after_agent),
    )


def _evaluate_feedback_trained_mode(
    *,
    mode: str,
    episodes: list[RewardPlasticityEpisode],
    steps_per_observation: int,
    agent: PlasticityAgent,
) -> PlasticityModeMetrics:
    before_state = _state_signature(agent)
    before_actions: list[str] = []
    feedback_events: list[FeedbackEvent] = []
    for episode in episodes:
        agent.observe(episode.final_observation)
        action = normalize_benchmark_action(agent.think(steps=steps_per_observation).actie_type)
        before_actions.append(action)
        outcome = "success" if action == episode.expected_action else "failure"
        before_modulators = _neuromodulators(agent)
        agent.observe(episode.training_observation)
        agent.modulate(outcome)
        after_modulators = _neuromodulators(agent)
        feedback_events.append(
            FeedbackEvent(
                episode_id=episode.episode_id,
                expected_action=episode.expected_action,
                action=action,
                outcome=outcome,
                neuromodulator_delta=_delta(before_modulators, after_modulators),
            )
        )
    trained_state = _state_signature(agent)
    after_actions = _evaluate_actions(agent, episodes, steps_per_observation)
    after_state = _state_signature(agent)
    return _metrics(
        mode=mode,
        episodes=episodes,
        before_actions=before_actions,
        after_actions=after_actions,
        feedback_events=feedback_events,
        before_state=before_state,
        after_state=after_state if after_state != trained_state else trained_state,
    )


def _evaluate_persisted_checkpoint_mode(
    *,
    episodes: list[RewardPlasticityEpisode],
    steps_per_observation: int,
    params: NetworkParameters,
) -> PlasticityModeMetrics:
    agent = AgentTissue(
        params,
        semantic_policy_enabled=False,
        temporal_context_enabled=False,
    )
    before_state = _state_signature(agent)
    before_actions: list[str] = []
    feedback_events: list[FeedbackEvent] = []
    for episode in episodes:
        agent.observe(episode.final_observation)
        action = normalize_benchmark_action(agent.think(steps=steps_per_observation).actie_type)
        before_actions.append(action)
        outcome = "success" if action == episode.expected_action else "failure"
        before_modulators = _neuromodulators(agent)
        agent.observe(episode.training_observation)
        agent.modulate(outcome)
        after_modulators = _neuromodulators(agent)
        feedback_events.append(
            FeedbackEvent(
                episode_id=episode.episode_id,
                expected_action=episode.expected_action,
                action=action,
                outcome=outcome,
                neuromodulator_delta=_delta(before_modulators, after_modulators),
            )
        )
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint = Path(tmpdir) / "plasticity-checkpoint.json"
        save_state(agent, str(checkpoint))
        loaded = load_state(str(checkpoint))
        after_actions = _evaluate_actions(loaded, episodes, steps_per_observation)
        after_state = _state_signature(loaded)
    return _metrics(
        mode="persisted_checkpoint",
        episodes=episodes,
        before_actions=before_actions,
        after_actions=after_actions,
        feedback_events=feedback_events,
        before_state=before_state,
        after_state=after_state,
    )


def _evaluate_actions(
    agent: PlasticityAgent,
    episodes: list[RewardPlasticityEpisode],
    steps_per_observation: int,
) -> list[str]:
    actions: list[str] = []
    for episode in episodes:
        agent.observe(episode.final_observation)
        actions.append(normalize_benchmark_action(agent.think(steps=steps_per_observation).actie_type))
    return actions


def _metrics(
    *,
    mode: str,
    episodes: list[RewardPlasticityEpisode],
    before_actions: list[str],
    after_actions: list[str],
    feedback_events: list[FeedbackEvent],
    before_state: dict[str, float | int],
    after_state: dict[str, float | int],
) -> PlasticityModeMetrics:
    before_accuracy = _accuracy(episodes, before_actions)
    after_accuracy = _accuracy(episodes, after_actions)
    return PlasticityModeMetrics(
        mode=mode,
        before_accuracy=before_accuracy,
        after_accuracy=after_accuracy,
        accuracy_delta=after_accuracy - before_accuracy,
        decision_change_rate=sum(
            1 for before, after in zip(before_actions, after_actions) if before != after
        )
        / len(episodes),
        internal_state_changed=before_state != after_state,
        training_feedback_count=len(feedback_events),
        before_actions=before_actions,
        after_actions=after_actions,
        feedback_events=feedback_events,
    )


def _accuracy(episodes: list[RewardPlasticityEpisode], actions: list[str]) -> float:
    correct = sum(
        1 for episode, action in zip(episodes, actions) if action == episode.expected_action
    )
    return correct / len(episodes)


def _neuromodulators(agent: PlasticityAgent) -> dict[str, float]:
    network = getattr(agent, "network", None)
    if network is None:
        return {}
    return {key: float(value) for key, value in network.neuromodulators.items()}


def _delta(
    before: dict[str, float],
    after: dict[str, float],
) -> dict[str, float]:
    return {key: after.get(key, 0.0) - before.get(key, 0.0) for key in sorted(after)}


def _state_signature(agent: PlasticityAgent) -> dict[str, float | int]:
    state = agent.state
    keys = (
        "energy",
        "activity",
        "step_count",
        "dopamine",
        "serotonin",
        "acetylcholine",
        "norepinephrine",
        "observation_count",
        "think_count",
        "modulation_count",
    )
    signature: dict[str, float | int] = {}
    for key in keys:
        if hasattr(state, key):
            value = getattr(state, key)
            if isinstance(value, (float, int)):
                signature[key] = value
    return signature


def _verdict(modes: dict[str, PlasticityModeMetrics]) -> str:
    trained_modes = [
        metrics
        for name, metrics in modes.items()
        if name in {"feedback_trained_tissue", "raw_network_only", "persisted_checkpoint"}
    ]
    if any(metrics.accuracy_delta > 0.0 for metrics in trained_modes):
        return "behavioral_plasticity_observed"
    if any(metrics.internal_state_changed for metrics in trained_modes):
        return "internal_state_changed_without_behavioral_improvement"
    return "no_plasticity_observed"


def _render_markdown_report(report: RewardPlasticityBenchmarkReport) -> str:
    lines = [
        "# Reward-driven plasticity benchmark",
        "",
        f"Verdict: `{report.verdict}`",
        "",
        report.claim_boundary,
        "",
        "No broad Qubic/Neuraxon intelligence claim is made from adapter-only behavior.",
        "",
        "| Mode | Before accuracy | After accuracy | Accuracy delta | "
        "Decision-change rate | Internal state changed |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for mode, metrics in report.modes.items():
        lines.append(
            "| "
            f"{mode} | {metrics.before_accuracy:.3f} | {metrics.after_accuracy:.3f} | "
            f"{metrics.accuracy_delta:.3f} | {metrics.decision_change_rate:.3f} | "
            f"{metrics.internal_state_changed} |"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "- Before/after accuracy measures observable behaviour, not just neuromodulator state.",
            "- Decision-change rate records whether later actions changed after feedback.",
            "- If accuracy does not improve, the verdict remains limited even when "
            "internal state changes.",
            "",
        ]
    )
    return "\n".join(lines)
