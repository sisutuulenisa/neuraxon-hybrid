"""Perception layer — sensory input processing."""

from typing import Any


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
