"""Perception layer — sensory input processing and trinary encoding."""

from __future__ import annotations

from typing import Any, Callable


class Perception:
    """Processes incoming sensory data into structured observations."""

    def __init__(self) -> None:
        self.observations: list[dict[str, Any]] = []

    def observe(self, raw: Any) -> dict[str, Any]:
        """Transform raw input into a structured observation."""
        observation = {"source": "raw", "data": raw, "timestamp": None}
        self.observations.append(observation)
        return observation

    def last(self) -> dict[str, Any] | None:
        """Return the most recent observation, if any."""
        return self.observations[-1] if self.observations else None


class PerceptionEncoder:
    """Encode agent observations into trinary (-1, 0, +1) input patterns for Neuraxon.

    The encoder maps heterogeneous observation sources (tool results, errors,
    session context, environment status, previous outcomes) into a fixed-length
    vector of trinary states suitable for ``network.set_input_states()``.

    Parameters
    ----------
    num_input_neurons:
        Length of the output vector. Must match the target network's
        ``NetworkParameters.num_input_neurons``.
    thresholds:
        Optional overrides for numerical threshold mapping.
    """

    # Default categorical mappings -------------------------------------------------
    _TOOL_RESULT_MAP: dict[str, int] = {
        "success": 1,
        "fail": -1,
        "timeout": 0,
    }

    _ERROR_TYPE_MAP: dict[str, int] = {
        "syntax": -1,
        "runtime": -1,
        "network": 0,
        "auth": 0,
    }

    _PREVIOUS_OUTCOME_MAP: dict[str, int] = {
        "success": 1,
        "fail": -1,
        "none": 0,
    }

    # Default numerical thresholds -------------------------------------------------
    _DEFAULT_THRESHOLDS: dict[str, tuple[float, float]] = {
        # (low, high)  ->  below low = -1, between = 0, above high = +1
        "cpu_percent": (30.0, 70.0),
        "memory_percent": (40.0, 80.0),
        "disk_percent": (50.0, 85.0),
        "duration_seconds": (60.0, 300.0),
        "turn_count": (5.0, 20.0),
        "token_count": (500.0, 2000.0),
    }

    def __init__(
        self,
        num_input_neurons: int = 5,
        thresholds: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        if num_input_neurons <= 0:
            raise ValueError("num_input_neurons must be positive")
        self.num_input_neurons = num_input_neurons
        self.thresholds = {**self._DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._history: list[list[int]] = []
        self._schema: list[tuple[str, Callable[[dict[str, Any]], int]]] = []
        self._build_schema()

    # ------------------------------------------------------------------ schema ---
    def _build_schema(self) -> None:
        """Register encoders in fixed order so output is deterministic."""
        self._schema = [
            ("tool_result", self._encode_tool_result),
            ("error_type", self._encode_error_type),
            ("session_health", self._encode_session_health),
            ("environment_health", self._encode_environment_health),
            ("previous_outcome", self._encode_previous_outcome),
        ]

    # ---------------------------------------------------------------- encoders ---
    def _encode_tool_result(self, obs: dict[str, Any]) -> int:
        raw = obs.get("tool_result")
        if raw is None:
            return 0
        return self._TOOL_RESULT_MAP.get(str(raw).lower(), 0)

    def _encode_error_type(self, obs: dict[str, Any]) -> int:
        raw = obs.get("error_type")
        if raw is None:
            return 1  # no error -> positive signal
        return self._ERROR_TYPE_MAP.get(str(raw).lower(), 0)

    def _encode_session_health(self, obs: dict[str, Any]) -> int:
        """Aggregate session metrics into a single trinary health signal."""
        signals: list[int] = []
        for key in ("duration_seconds", "turn_count", "token_count"):
            val = obs.get(key)
            if val is not None:
                signals.append(self._threshold_encode(float(val), *self.thresholds[key]))
        if not signals:
            return 0
        return self._aggregate_signals(signals)

    def _encode_environment_health(self, obs: dict[str, Any]) -> int:
        """Aggregate environment metrics into a single trinary health signal."""
        signals: list[int] = []
        for key in ("cpu_percent", "memory_percent", "disk_percent"):
            val = obs.get(key)
            if val is not None:
                signals.append(self._threshold_encode(float(val), *self.thresholds[key]))
        if not signals:
            return 0
        return self._aggregate_signals(signals)

    def _encode_previous_outcome(self, obs: dict[str, Any]) -> int:
        raw = obs.get("previous_outcome")
        if raw is None:
            return 0
        return self._PREVIOUS_OUTCOME_MAP.get(str(raw).lower(), 0)

    # ----------------------------------------------------------- helpers ---
    @staticmethod
    def _threshold_encode(value: float, low: float, high: float) -> int:
        """Map a scalar to {-1, 0, +1} using two thresholds."""
        if value < low:
            return -1
        if value > high:
            return 1
        return 0

    @staticmethod
    def _aggregate_signals(signals: list[int]) -> int:
        """Aggregate multiple trinary signals into one.

        Majority vote with tie-breaker towards 0.
        """
        counts = {-1: 0, 0: 0, 1: 0}
        for s in signals:
            counts[s] = counts.get(s, 0) + 1
        max_count = max(counts.values())
        winners = [k for k, v in counts.items() if v == max_count]
        if len(winners) == 1:
            return winners[0]
        return 0

    # ----------------------------------------------------------- public API ---
    def encode(self, observation: dict[str, Any]) -> list[int]:
        """Encode an observation dict into a trinary vector.

        Returns a list of length ``num_input_neurons`` containing only
        values from ``{-1, 0, 1}``.
        """
        base = [encoder(observation) for _, encoder in self._schema]

        # Pad or truncate to match num_input_neurons
        if len(base) < self.num_input_neurons:
            base.extend([0] * (self.num_input_neurons - len(base)))
        elif len(base) > self.num_input_neurons:
            base = base[: self.num_input_neurons]

        # Store for sequential encoding support
        self._history.append(base.copy())
        return base

    def encode_sequential(self, observation: dict[str, Any]) -> list[int]:
        """Encode with trend-awareness: compare against previous observation.

        Each position in the output reflects whether the raw encoded value
        is decreasing (-1), stable (0), or increasing (+1) compared to the
        previous step.
        """
        current = self.encode(observation)
        if len(self._history) < 2:
            return current
        previous = self._history[-2]
        return [
            0 if cur == prev else (1 if cur > prev else -1) for cur, prev in zip(current, previous)
        ]

    def reset(self) -> None:
        """Clear observation history."""
        self._history.clear()

    def get_history(self) -> list[list[int]]:
        """Return a shallow copy of the encoded observation history."""
        return [row.copy() for row in self._history]
