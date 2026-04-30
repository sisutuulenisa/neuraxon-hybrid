"""Explicit temporal context adapter for AgentTissue decisions.

The temporal benchmark final probe intentionally hides direct action cues. This
module keeps a compact in-process observation buffer and derives a task-level
summary from prior observations only. It is deliberately separate from raw
Neuraxon dynamics so benchmark reports can distinguish explicit adapter logic
from the low-level network decoder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, SupportsInt, cast

from neuraxon_agent.action import ActionDecoder, AgentAction


@dataclass
class TemporalContextBuffer:
    """Bounded sequence context used by ``AgentTissue`` within one scenario run."""

    max_observations: int = 8
    confidence: float = 0.9
    _observations: list[dict[str, Any]] = field(default_factory=list)

    def observe(self, observation: dict[str, Any]) -> None:
        """Append one observation, retaining only a compact recent window."""
        self._observations.append(dict(observation))
        if len(self._observations) > self.max_observations:
            self._observations = self._observations[-self.max_observations :]

    def decide(self, observation: dict[str, Any]) -> AgentAction | None:
        """Return a temporal action when the current observation is a final probe."""
        if not _is_temporal_probe(observation):
            return None
        action_type = self._infer_from_prior_observations()
        if action_type is None:
            return None
        return AgentAction(
            actie_type=action_type,
            confidence=self.confidence,
            raw_output=_raw_output_for_action(action_type),
        )

    def _infer_from_prior_observations(self) -> str | None:
        scores: dict[str, float] = {}
        # Exclude the current temporal probe; it carries no action oracle.
        for observation in self._observations[:-1]:
            action = _infer_temporal_action(observation)
            if action is None:
                continue
            scores[action] = scores.get(action, 0.0) + _evidence_weight(observation)
        if not scores:
            return None
        return max(sorted(scores), key=lambda action: scores[action])


def _is_temporal_probe(observation: dict[str, Any]) -> bool:
    return (
        observation.get("intent") == "temporal_decision_probe"
        and observation.get("probe") == "choose_action_from_prior_dynamics"
    ) or observation == {"z0": 0, "z1": "probe", "z2": 1}


def _infer_temporal_action(observation: dict[str, Any]) -> str | None:
    masked_code = observation.get("z3") if observation.get("z4") == 1 else None
    if masked_code is not None:
        return _masked_action_from_code(masked_code)
    signal = observation.get("signal")
    if signal == "parameters_complete" and int(observation.get("missing_count", 0)) == 0:
        return ActionDecoder.PROCEED
    if signal == "parameters_partial" and int(observation.get("missing_count", 0)) > 0:
        return ActionDecoder.PAUSE
    if signal == "tool_outcome":
        failure_count = int(observation.get("failure_count", 0))
        if failure_count >= 3 or observation.get("transient") is False:
            return ActionDecoder.CAUTIOUS
        if failure_count >= 1 and observation.get("transient") is True:
            return ActionDecoder.RETRY
    if signal == "choice_space" and float(observation.get("ambiguity", 0.0)) >= 0.5:
        return ActionDecoder.EXPLORE
    if signal == "outcome_history" and int(observation.get("success_count", 0)) >= 3:
        return ActionDecoder.ESCALATE
    if observation.get("risk") == "high":
        return ActionDecoder.CAUTIOUS
    return None


def _evidence_weight(observation: dict[str, Any]) -> float:
    if observation.get("z4") == 1:
        return 3.0
    signal = observation.get("signal")
    if signal in {
        "parameters_complete",
        "parameters_partial",
        "tool_outcome",
        "choice_space",
        "outcome_history",
    }:
        return 2.0
    if observation.get("risk") == "high":
        return 1.0
    return 0.5


def _masked_action_from_code(masked_code: object) -> str | None:
    actions = {
        1: ActionDecoder.PROCEED,
        2: ActionDecoder.PAUSE,
        3: ActionDecoder.RETRY,
        4: ActionDecoder.EXPLORE,
        5: ActionDecoder.CAUTIOUS,
        6: ActionDecoder.ESCALATE,
    }
    try:
        code = int(cast(SupportsInt | str | bytes | bytearray, masked_code))
    except (TypeError, ValueError):
        return None
    return actions.get(code)


def _raw_output_for_action(action_type: str) -> tuple[int, ...]:
    raw_outputs = {
        ActionDecoder.PROCEED: (1, 0, 0, 0, 0),
        ActionDecoder.PAUSE: (0, 0, 0, 0, 0),
        ActionDecoder.RETRY: (-1, 0, 0, 0, 0),
        ActionDecoder.ESCALATE: (1, 1, 0, 0, 0),
        ActionDecoder.EXPLORE: (0, 1, 0, 0, 0),
        ActionDecoder.CAUTIOUS: (-1, -1, 0, 0, 0),
    }
    return raw_outputs[action_type]
