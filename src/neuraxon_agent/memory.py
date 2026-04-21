"""Memory layer — experience storage and retrieval."""

from typing import Any


class Memory:
    """Simple episodic memory for the agent."""

    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = capacity
        self.episodes: list[dict[str, Any]] = []

    def store(self, episode: dict[str, Any]) -> None:
        """Store an episode, respecting capacity."""
        if len(self.episodes) >= self.capacity:
            self.episodes.pop(0)
        self.episodes.append(episode)

    def recall(self, n: int = 5) -> list[dict[str, Any]]:
        """Recall the last n episodes."""
        return self.episodes[-n:]

    def clear(self) -> None:
        """Erase all stored episodes."""
        self.episodes.clear()
