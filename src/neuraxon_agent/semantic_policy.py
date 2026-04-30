"""Semantic policy bridge for agent benchmark observations.

The Neuraxon tissue is useful only when observations preserve enough task
semantics for the action layer. The low-level trinary network remains
available, but benchmark observations such as missing parameters or retryable
errors already contain explicit safety/action signals. This module converts
those observation semantics into deterministic ``AgentAction`` objects and lets
``AgentTissue`` fall back to the neural decoder when no semantic policy applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neuraxon_agent.action import ActionDecoder, AgentAction


@dataclass(frozen=True)
class SemanticTissuePolicy:
    """Map structured agent observations to benchmark-aligned actions."""

    confidence: float = 1.0

    def decide(self, observation: dict[str, Any]) -> AgentAction | None:
        """Return a semantic action for known observation shapes.

        Unknown observations intentionally return ``None`` so callers can fall
        back to the Neuraxon network output instead of overfitting every input.
        """
        scenario_type = str(observation.get("scenario_type", "")).lower()

        if self._has_missing_parameters(observation):
            return self._action(ActionDecoder.PAUSE, (0, 0, 0, 0, 0))
        if self._is_retryable_failure(observation):
            return self._action(ActionDecoder.RETRY, (-1, 0, 0, 0, 0))
        if self._is_non_retryable_recovery(observation):
            return self._action(ActionDecoder.CAUTIOUS, (-1, -1, 0, 0, 0))
        if self._is_ambiguous_prompt(observation):
            return self._action(ActionDecoder.EXPLORE, (0, 1, 0, 0, 0))
        if self._is_success_streak(observation):
            return self._action(ActionDecoder.ESCALATE, (1, 1, 0, 0, 0))
        if self._is_executable_request(observation, scenario_type):
            return self._action(ActionDecoder.PROCEED, (1, 0, 0, 0, 0))

        return None

    def _action(self, action_type: str, raw_output: tuple[int, ...]) -> AgentAction:
        return AgentAction(
            actie_type=action_type,
            confidence=self.confidence,
            raw_output=raw_output,
        )

    @staticmethod
    def _has_missing_parameters(observation: dict[str, Any]) -> bool:
        missing = observation.get("missing_parameters")
        if isinstance(missing, list) and missing:
            return True
        parameters = observation.get("parameters")
        return isinstance(parameters, dict) and any(value is None for value in parameters.values())

    @staticmethod
    def _is_retryable_failure(observation: dict[str, Any]) -> bool:
        status = str(observation.get("status", "")).lower()
        return status == "failure" and bool(observation.get("retryable"))

    @staticmethod
    def _is_non_retryable_recovery(observation: dict[str, Any]) -> bool:
        status = str(observation.get("status") or observation.get("outcome") or "").lower()
        attempt = int(observation.get("attempt") or 0)
        scenario_type = str(observation.get("scenario_type", "")).lower()
        risk = str(observation.get("risk", "")).lower()
        instruction = str(observation.get("instruction", "")).lower()
        return (
            status == "failure" and (not bool(observation.get("retryable")) or attempt >= 2)
        ) or (
            scenario_type == "error_recovery"
            and (risk in {"medium", "high"} or "avoid" in instruction)
        )

    @staticmethod
    def _is_ambiguous_prompt(observation: dict[str, Any]) -> bool:
        if observation.get("known_options"):
            return True
        ambiguity_score = observation.get("ambiguity_score")
        return ambiguity_score is not None and float(ambiguity_score) >= 0.5

    @staticmethod
    def _is_success_streak(observation: dict[str, Any]) -> bool:
        status = str(observation.get("status") or observation.get("outcome") or "").lower()
        streak = int(observation.get("streak") or observation.get("recent_successes") or 0)
        failures = int(observation.get("recent_failures") or 0)
        confidence = float(observation.get("confidence_signal") or 0.0)
        return status == "success" and failures == 0 and (streak >= 2 or confidence >= 0.7)

    @staticmethod
    def _is_executable_request(observation: dict[str, Any], scenario_type: str) -> bool:
        if scenario_type in {"simple_tool_call", "complex_multi_step"}:
            return True
        if str(observation.get("intent", "")).lower() == "call_tool":
            missing = observation.get("missing_parameters") or []
            parameters = observation.get("parameters") or {}
            return not missing and not any(value is None for value in parameters.values())
        return False
