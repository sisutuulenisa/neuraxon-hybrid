"""Memory layer — experience storage and retrieval via Neuraxon pattern recall."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from neuraxon_agent.perception import PerceptionEncoder
from neuraxon_agent.action import AgentAction
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, NeuraxonApplication


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


@dataclass
class ExperiencePattern:
    """A single stored experience as a Neuraxon pattern."""

    name: str
    pattern: list[int]
    observation: dict[str, Any]
    action: AgentAction
    outcome: str
    created_at: float
    strength: float = 1.0
    access_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pattern": self.pattern,
            "observation": self.observation,
            "action": {
                "actie_type": self.action.actie_type,
                "confidence": self.action.confidence,
                "raw_output": list(self.action.raw_output),
            },
            "outcome": self.outcome,
            "created_at": self.created_at,
            "strength": self.strength,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExperiencePattern:
        action_data = data["action"]
        action = AgentAction(
            actie_type=action_data["actie_type"],
            confidence=action_data["confidence"],
            raw_output=tuple(action_data["raw_output"]),
        )
        return cls(
            name=data["name"],
            pattern=list(data["pattern"]),
            observation=dict(data["observation"]),
            action=action,
            outcome=data["outcome"],
            created_at=data["created_at"],
            strength=data.get("strength", 1.0),
            access_count=data.get("access_count", 0),
        )


class TissueMemory:
    """Pattern-based memory for an AgentTissue using NeuraxonApplication storage/recall.

    Each experience (observation-action-outcome triplet) is encoded as a trinary
    pattern and stored in a :class:`~neuraxon_agent.vendor.neuraxon2.NeuraxonApplication`.
    Patterns are recalled by similarity (Hamming distance on trinary vectors) and
    can be partially reconstructed by the network through associative completion.

    Forgetting is implemented as gradual strength decay.  Old patterns with low
    strength are automatically pruned when *capacity* is reached.
    """

    def __init__(
        self,
        params: NetworkParameters | None = None,
        capacity: int = 100,
        forgetting_rate: float = 0.001,
        strength_threshold: float = 0.1,
    ) -> None:
        self.params = params or NetworkParameters()
        self.app = NeuraxonApplication(self.params)
        self.encoder = PerceptionEncoder(self.params.num_input_neurons)
        self.capacity = capacity
        self.forgetting_rate = forgetting_rate
        self.strength_threshold = strength_threshold
        self.experiences: dict[str, ExperiencePattern] = {}
        self._step_counter = 0
        self._pattern_counter = 0

    # ----------------------------------------------------------------- core ---

    def store_experience(
        self,
        observation: dict[str, Any],
        action: AgentAction,
        outcome: str,
        steps: int = 20,
    ) -> str:
        """Encode *observation* as a pattern and store the experience.

        Returns the generated experience ID.
        """
        self._step_counter += 1
        self._pattern_counter += 1
        name = f"exp_{self._pattern_counter:06d}"

        pattern = self.encoder.encode(observation)
        self.app.store_pattern(name, pattern, steps=steps)

        # Apply forgetting before storing
        self._decay_strengths()

        exp = ExperiencePattern(
            name=name,
            pattern=pattern,
            observation=dict(observation),
            action=action,
            outcome=outcome,
            created_at=float(self._step_counter),
        )
        self.experiences[name] = exp

        # Prune weakest if over capacity
        self._prune_if_needed()

        return name

    def recall_similar(
        self,
        observation: dict[str, Any],
        top_k: int = 1,
        steps: int = 20,
        mask_fraction: float = 0.3,
    ) -> list[ExperiencePattern]:
        """Recall the *top_k* experiences most similar to *observation*.

        Similarity is measured by Hamming distance on the encoded trinary
        patterns.  Accessing a pattern boosts its strength (rehearsal effect).
        The network performs associative completion by presenting a masked
        version of the closest pattern.
        """
        if not self.experiences:
            return []

        query = self.encoder.encode(observation)

        # Rank by similarity (higher is better)
        scored: list[tuple[float, str]] = []
        for name, exp in self.experiences.items():
            sim = self._pattern_similarity(query, exp.pattern) * exp.strength
            scored.append((sim, name))

        scored.sort(reverse=True)
        top_names = [name for _, name in scored[:top_k]]

        results: list[ExperiencePattern] = []
        for name in top_names:
            exp = self.experiences[name]
            # Rehearsal boost
            exp.access_count += 1
            exp.strength = min(1.0, exp.strength + 0.05)
            # Associative completion via network
            self.app.recall_pattern(name, steps=steps, mask_fraction=mask_fraction)
            results.append(exp)

        return results

    # ----------------------------------------------------------- forgetting ---

    def _decay_strengths(self) -> None:
        """Age all patterns by one step."""
        for exp in self.experiences.values():
            exp.strength *= 1.0 - self.forgetting_rate
            exp.strength = max(0.0, exp.strength)

    def _prune_if_needed(self) -> None:
        """Remove weakest patterns when over capacity."""
        while len(self.experiences) > self.capacity:
            weakest_name = min(
                self.experiences,
                key=lambda n: self.experiences[n].strength,
            )
            del self.experiences[weakest_name]
            # Also remove from app patterns dict if present
            self.app.patterns.pop(weakest_name, None)

    def forget_weak(self) -> int:
        """Explicitly remove patterns below *strength_threshold*.

        Returns the number of patterns removed.
        """
        to_remove = [
            name for name, exp in self.experiences.items()
            if exp.strength < self.strength_threshold
        ]
        for name in to_remove:
            del self.experiences[name]
            self.app.patterns.pop(name, None)
        return len(to_remove)

    # ---------------------------------------------------------- internals ---

    @staticmethod
    def _pattern_similarity(a: list[int], b: list[int]) -> float:
        """Compute normalised similarity between two trinary patterns.

        Returns a value in ``[0.0, 1.0]`` where 1.0 means identical.
        """
        n = max(len(a), len(b))
        if n == 0:
            return 0.0
        matches = 0
        for i in range(n):
            av = a[i] if i < len(a) else 0
            bv = b[i] if i < len(b) else 0
            if av == bv:
                matches += 1
        return matches / n

    # ----------------------------------------------------------- state mgmt ---

    def save(self, path: str) -> None:
        """Serialize memory state (patterns + metadata) to JSON."""
        data = {
            "params": {
                "num_input_neurons": self.params.num_input_neurons,
                "num_hidden_neurons": self.params.num_hidden_neurons,
                "num_output_neurons": self.params.num_output_neurons,
            },
            "capacity": self.capacity,
            "forgetting_rate": self.forgetting_rate,
            "strength_threshold": self.strength_threshold,
            "step_counter": self._step_counter,
            "pattern_counter": self._pattern_counter,
            "experiences": [exp.to_dict() for exp in self.experiences.values()],
            "patterns": {
                name: pattern for name, pattern in self.app.patterns.items()
                if name in self.experiences
            },
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str) -> TissueMemory:
        """Deserialize memory state from JSON."""
        data = json.loads(Path(path).read_text())
        params_data = data.get("params", {})
        params = NetworkParameters(
            num_input_neurons=params_data.get("num_input_neurons", 5),
            num_hidden_neurons=params_data.get("num_hidden_neurons", 20),
            num_output_neurons=params_data.get("num_output_neurons", 5),
        )
        instance = cls(
            params=params,
            capacity=data.get("capacity", 100),
            forgetting_rate=data.get("forgetting_rate", 0.001),
            strength_threshold=data.get("strength_threshold", 0.1),
        )
        instance._step_counter = data.get("step_counter", 0)
        instance._pattern_counter = data.get("pattern_counter", 0)
        instance.experiences = {
            exp_data["name"]: ExperiencePattern.from_dict(exp_data)
            for exp_data in data.get("experiences", [])
        }
        instance.app.patterns = {
            name: list(pattern) for name, pattern in data.get("patterns", {}).items()
        }
        return instance

    # --------------------------------------------------------------- introspection ---

    def __len__(self) -> int:
        return len(self.experiences)

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics about the memory contents."""
        if not self.experiences:
            return {"count": 0, "mean_strength": 0.0, "oldest_step": 0}
        strengths = [e.strength for e in self.experiences.values()]
        return {
            "count": len(self.experiences),
            "mean_strength": round(sum(strengths) / len(strengths), 4),
            "min_strength": round(min(strengths), 4),
            "max_strength": round(max(strengths), 4),
            "oldest_step": int(min(e.created_at for e in self.experiences.values())),
            "newest_step": int(max(e.created_at for e in self.experiences.values())),
        }
