"""Tissue layer — structural connective substrate for the agent."""

from typing import Any


class Tissue:
    """Represents the connective tissue that binds perception, action, and memory."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.state: dict[str, Any] = {}

    def bind(self, component: object, role: str) -> None:
        """Attach a component to the tissue under a named role."""
        self.state[role] = component

    def signal(self, role: str, payload: Any) -> Any:
        """Send a signal to a bound component and return its response."""
        target = self.state.get(role)
        if target is None:
            raise RuntimeError(f"No component bound for role: {role}")
        if callable(target):
            return target(payload)
        return getattr(target, "handle", lambda x: x)(payload)
