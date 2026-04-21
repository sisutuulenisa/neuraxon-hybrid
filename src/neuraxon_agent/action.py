"""Action layer — motor output and effector control."""

from typing import Any


class Action:
    """Translates decisions into executable actions."""

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
