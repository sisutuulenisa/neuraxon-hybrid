"""Real-time streaming simulation loop for agent tissue."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from neuraxon_agent.tissue import AgentTissue, TissueState


@dataclass
class StreamEvent:
    """Event emitted during streaming simulation."""
    step: int
    action: str
    confidence: float
    state: TissueState
    timestamp: float


class StreamingLoop:
    """Runs AgentTissue in a real-time streaming mode with callbacks."""

    def __init__(self, tissue: AgentTissue, callback: Callable[[StreamEvent], None] | None = None) -> None:
        self.tissue = tissue
        self.callback = callback
        self._running = False

    def run(self, observation_stream: list[dict[str, Any]], steps_per_obs: int = 10, delay: float = 0.0) -> list[StreamEvent]:
        """Process a stream of observations and emit events."""
        events: list[StreamEvent] = []
        self._running = True
        for i, obs in enumerate(observation_stream):
            if not self._running:
                break
            self.tissue.observe(obs)
            action = self.tissue.think(steps=steps_per_obs)
            event = StreamEvent(
                step=i,
                action=action.actie_type,
                confidence=action.confidence,
                state=self.tissue.state,
                timestamp=time.time(),
            )
            events.append(event)
            if self.callback:
                self.callback(event)
            if delay > 0:
                time.sleep(delay)
        self._running = False
        return events

    def stop(self) -> None:
        self._running = False
