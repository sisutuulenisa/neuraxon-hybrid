"""Modulation layer — dynamic parameter adjustment and homeostasis."""

from typing import Any


class Modulation:
    """Adjusts internal parameters to maintain stability and adapt behavior."""

    def __init__(self, params: dict[str, float] | None = None) -> None:
        self.params = params or {"gain": 1.0, "threshold": 0.5}

    def adjust(self, feedback: dict[str, Any]) -> dict[str, float]:
        """Update parameters based on environmental feedback."""
        error = feedback.get("error", 0.0)
        self.params["gain"] += 0.01 * error
        self.params["threshold"] -= 0.005 * error
        return dict(self.params)
