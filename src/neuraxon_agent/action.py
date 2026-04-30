"""Action layer — motor output and effector control.

Decodes trinary output states from Neuraxon networks into concrete
agent actions with confidence scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

#: Valid trinary states in a Neuraxon network.
TRINARY_STATES = (-1, 0, 1)


@dataclass(frozen=True)
class AgentAction:
    """A decoded agent action.

    Attributes
    ----------
    actie_type:
        The resolved action type (e.g. ``"PROCEED"``, ``"PAUSE"``).
    confidence:
        A float in ``[0.0, 1.0]`` indicating how certain the decoder
        is about this action. ``1.0`` means an exact pattern match.
    raw_output:
        The original list of trinary output neuron states.
    """

    actie_type: str
    confidence: float
    raw_output: tuple[int, ...]


class Action:
    """Translates decisions into executable actions.

    .. deprecated::
        This stub is retained for backward compatibility.
        Use :class:`ActionDecoder` and :class:`AgentAction` for new code.
    """

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    def act(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Execute a decision and record it in history."""
        result = {"status": "executed", "decision": decision}
        self.history.append(result)
        return result

    def last(self) -> dict[str, Any] | None:
        """Return the most recent action result, if any."""
        return self.history[-1] if self.history else None


class ActionDecoder:
    """Decode trinary output neuron states into agent actions.

    The decoder supports two modes:

    1. *Basis decoder* — one output neuron maps directly to a single action.
    2. *Multi-output decoder* — combinations of output neurons map to richer
       actions such as ``ESCALATE`` or ``EXPLORE``.

    The decoder is fully deterministic: the same input always yields the
    same ``AgentAction``.

    Parameters
    ----------
    num_output_neurons:
        Number of output neurons to expect. Must be ``>= 1``.
    """

    # Action definitions --------------------------------------------------------
    PROCEED = "PROCEED"
    PAUSE = "PAUSE"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"
    EXPLORE = "EXPLORE"
    CAUTIOUS = "CAUTIOUS"

    # Basis mapping for a single neuron -----------------------------------------
    _BASIS_MAP: dict[int, str] = {
        1: PROCEED,
        0: PAUSE,
        -1: RETRY,
    }

    # Multi-neuron exact pattern mappings ---------------------------------------
    # Tuple of trinary states -> action type
    _MULTI_MAP: dict[tuple[int, ...], str] = {
        (1, 1): ESCALATE,
        (0, 1): EXPLORE,
        (-1, -1): CAUTIOUS,
    }

    # Fallback heuristic for unmatched multi-neuron patterns --------------------
    # Sum thresholds -> action type
    _FALLBACK_SUM_MAP: dict[int, str] = {
        2: ESCALATE,
        1: PROCEED,
        0: PAUSE,
        -1: RETRY,
        -2: RETRY,
    }

    def __init__(self, num_output_neurons: int = 1) -> None:
        if num_output_neurons < 1:
            raise ValueError("num_output_neurons must be >= 1")
        self.num_output_neurons = num_output_neurons
        self._history: list[AgentAction] = []
        self._strategy: Callable[[list[int]], AgentAction]
        self._select_strategy()

    # ----------------------------------------------------------- internals ---
    def _select_strategy(self) -> None:
        """Choose decoding strategy based on output neuron count."""
        if self.num_output_neurons == 1:
            self._strategy = self._decode_basis
        else:
            self._strategy = self._decode_multi

    @staticmethod
    def _validate_output_states(output_states: list[int]) -> None:
        """Ensure output_states contains only valid trinary values."""
        if not output_states:
            raise ValueError("output_states must not be empty")
        for s in output_states:
            if s not in TRINARY_STATES:
                raise ValueError(f"Invalid trinary state {s!r}; expected one of {TRINARY_STATES}")

    def _decode_basis(self, output_states: list[int]) -> AgentAction:
        """Decode a single output neuron (basis decoder)."""
        state = output_states[0]
        action_type = self._BASIS_MAP.get(state, self.PAUSE)
        return AgentAction(
            actie_type=action_type,
            confidence=1.0,
            raw_output=tuple(output_states),
        )

    def _decode_multi(self, output_states: list[int]) -> AgentAction:
        """Decode multiple output neurons (multi-output decoder)."""
        pattern = tuple(output_states)

        # Exact pattern match → maximum confidence
        if pattern in self._MULTI_MAP:
            return AgentAction(
                actie_type=self._MULTI_MAP[pattern],
                confidence=1.0,
                raw_output=pattern,
            )

        # Fallback: use sum heuristic with scaled confidence
        total = sum(output_states)
        action_type = self._FALLBACK_SUM_MAP.get(total, self.PAUSE)

        # Confidence scales with how many neurons align with the majority sign
        # or are zero. For exact matches we already returned 1.0 above.
        confidence = self._compute_confidence(output_states, total)

        return AgentAction(
            actie_type=action_type,
            confidence=confidence,
            raw_output=pattern,
        )

    @staticmethod
    def _compute_confidence(output_states: list[int], total: int) -> float:
        """Compute a confidence score for fallback-decoded actions.

        The score reflects the degree of consensus among output neurons.
        """
        n = len(output_states)
        if n == 0:
            return 0.0

        # Count neurons that agree with the dominant direction (or are neutral)
        if total > 0:
            agreeing = sum(1 for s in output_states if s > 0)
        elif total < 0:
            agreeing = sum(1 for s in output_states if s < 0)
        else:
            agreeing = sum(1 for s in output_states if s == 0)

        return round(agreeing / n, 4)

    # ------------------------------------------------------------- public API ---
    def decode(self, output_states: list[int]) -> AgentAction:
        """Decode a list of trinary output states into an ``AgentAction``.

        Parameters
        ----------
        output_states:
            A list of integers where each element is in ``{-1, 0, 1}``.
            The list length should match ``num_output_neurons``; it will be
            padded with ``0`` or truncated silently to match.

        Returns
        -------
        AgentAction
            The decoded action with type, confidence, and raw output snapshot.
        """
        self._validate_output_states(output_states)

        # Normalise length
        if len(output_states) < self.num_output_neurons:
            output_states = output_states + [0] * (self.num_output_neurons - len(output_states))
        elif len(output_states) > self.num_output_neurons:
            output_states = output_states[: self.num_output_neurons]

        action = self._strategy(output_states)
        self._history.append(action)
        return action

    def last(self) -> AgentAction | None:
        """Return the most recent decoded action, if any."""
        return self._history[-1] if self._history else None

    def get_history(self) -> list[AgentAction]:
        """Return a shallow copy of the decoded action history."""
        return list(self._history)

    def reset(self) -> None:
        """Clear the action history."""
        self._history.clear()

    # ---------------------------------------------------------------- mappings ---
    @classmethod
    def get_basis_mapping(cls) -> dict[int, str]:
        """Return the basis (single-neuron) action mapping."""
        return cls._BASIS_MAP.copy()

    @classmethod
    def get_multi_mapping(cls) -> dict[tuple[int, ...], str]:
        """Return the exact multi-neuron pattern action mapping."""
        return cls._MULTI_MAP.copy()

    @classmethod
    def get_all_defined_actions(cls) -> list[str]:
        """Return the list of all defined action types."""
        return [
            cls.PROCEED,
            cls.PAUSE,
            cls.RETRY,
            cls.ESCALATE,
            cls.EXPLORE,
            cls.CAUTIOUS,
        ]
