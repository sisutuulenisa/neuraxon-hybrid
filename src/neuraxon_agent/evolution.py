"""Evolutionary training for agent behaviour using Aigarth hybrid algorithm."""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from neuraxon_agent.vendor.MultiNeuraxon2 import NeuraxonAigarthHybrid
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


@dataclass
class EvolutionConfig:
    """Configuration for agent evolution."""
    seasons: int = 5
    episodes_per_season: int = 10
    seed: int | None = None
    task_scenarios: list[dict[str, Any]] | None = None


def _normalize_config(config: EvolutionConfig | dict[str, Any] | None) -> EvolutionConfig:
    """Return an ``EvolutionConfig`` for public API inputs."""
    if config is None:
        return EvolutionConfig()
    if isinstance(config, EvolutionConfig):
        return config
    return EvolutionConfig(**config)


class AgentEvolution:
    """Wraps NeuraxonAigarthHybrid to evolve agent networks on task scenarios."""

    def __init__(
        self,
        params: NetworkParameters | None = None,
        config: EvolutionConfig | dict[str, Any] | None = None,
    ) -> None:
        self.params = params or NetworkParameters()
        self.config = _normalize_config(config)
        if self.config.seed is not None:
            random.seed(self.config.seed)
        self.hybrid = NeuraxonAigarthHybrid(self.params)
        self._history: list[dict[str, Any]] = []

    def _build_dataset(self) -> list[tuple[list[int], list[int]]]:
        """Convert task scenarios into (input, expected_output) pairs."""
        scenarios = self.config.task_scenarios or _default_scenarios()
        dataset: list[tuple[list[int], list[int]]] = []
        for sc in scenarios:
            inp = _encode_observation(sc.get("observation", {}))
            expected = _encode_action(sc.get("expected_action", "idle"))
            dataset.append((inp, expected))
        return dataset

    def evaluate_fitness(self) -> float:
        """Evaluate and return the best fitness in the current population."""
        dataset = self._build_dataset()
        self.hybrid.evaluate_fitness(dataset)
        return self.hybrid.best().fitness

    def evolve(self) -> dict[str, Any]:
        """Run evolution for configured seasons/episodes and return summary."""
        if self.config.seed is not None:
            random.seed(self.config.seed)
        dataset = self._build_dataset()
        initial_best = self.evaluate_fitness()
        self.hybrid.evolve(
            dataset,
            seasons=self.config.seasons,
            episodes=self.config.episodes_per_season,
        )
        final_best = self.evaluate_fitness()
        summary = {
            "initial_fitness": initial_best,
            "final_fitness": final_best,
            "improvement": final_best - initial_best,
            "seasons": self.config.seasons,
            "episodes": self.config.episodes_per_season,
            "population_size": len(self.hybrid.population),
            "seed": self.config.seed,
        }
        self._history.append(summary)
        return summary

    def best_agent_weights(self) -> list[int]:
        """Return the circle weights of the best evolved agent."""
        return self.hybrid.best().circle_weights[:]

    def save(self, path: str) -> None:
        """Save evolution state to JSON."""
        data = {
            "config": asdict(self.config),
            "history": self._history,
            "best_weights": self.best_agent_weights(),
            "best_fitness": self.hybrid.best().fitness,
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str) -> AgentEvolution:
        """Load evolution state from JSON."""
        data = json.loads(Path(path).read_text())
        config = EvolutionConfig(**data.get("config", {}))
        instance = cls(config=config)
        instance._history = data.get("history", [])
        return instance

    @property
    def history(self) -> list[dict[str, Any]]:
        return self._history[:]


def _default_scenarios() -> list[dict[str, Any]]:
    """Default tool-selection training scenarios."""
    return [
        {"observation": {"type": "prompt", "content": "hello"}, "expected_action": "respond"},
        {"observation": {"type": "tool_result", "status": "error"}, "expected_action": "retry"},
        {"observation": {"type": "tool_result", "status": "success"}, "expected_action": "execute"},
        {"observation": {"type": "prompt", "content": "what is"}, "expected_action": "query"},
        {"observation": {"type": "tool_result", "status": "partial"}, "expected_action": "explore"},
        {"observation": {"type": "session_end"}, "expected_action": "idle"},
    ]


def _encode_observation(obs: dict[str, Any]) -> list[int]:
    """Simple trinary encoding for observations."""
    obs_type = obs.get("type", "")
    status = obs.get("status", "")
    if obs_type == "prompt":
        return [1, 0, 0]
    elif obs_type == "tool_result":
        if status == "success":
            return [0, 1, 0]
        elif status == "error":
            return [0, -1, 0]
        elif status == "partial":
            return [0, 0, 1]
        return [0, 0, 0]
    elif obs_type == "session_end":
        return [-1, 0, 0]
    return [0, 0, 0]


def _encode_action(action: str) -> list[int]:
    """Simple trinary encoding for expected actions."""
    mapping = {
        "idle": [0, 0],
        "execute": [1, 0],
        "query": [-1, 0],
        "respond": [0, 1],
        "explore": [0, -1],
        "retry": [1, 1],
    }
    return mapping.get(action, [0, 0])
