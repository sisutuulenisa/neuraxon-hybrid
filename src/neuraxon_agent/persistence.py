"""State persistence helpers for neuraxon-agent."""
from __future__ import annotations

import json
import os
from pathlib import Path

from neuraxon_agent.action import AgentAction
from neuraxon_agent.tissue import CHECKPOINT_SCHEMA_VERSION, AgentTissue, PersistenceLoadError
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, load_network

DEFAULT_AUTO_SAVE_TRIGGERS = frozenset({"modulate", "store_experience", "shutdown"})

__all__ = [
    "CHECKPOINT_SCHEMA_VERSION",
    "DEFAULT_AUTO_SAVE_TRIGGERS",
    "PersistentAgentTissue",
    "PersistenceLoadError",
    "load_state",
    "save_state",
]


def save_state(tissue: AgentTissue, path: str) -> None:
    """Save tissue state plus metadata to a JSON file."""
    tissue.save(path)


def load_state(path: str) -> AgentTissue:
    """Load tissue state from a JSON file."""
    data = json.loads(Path(path).read_text())
    if "network" not in data:
        return AgentTissue.load(path)

    p = data.get("params", {})
    params = NetworkParameters(
        num_input_neurons=p.get("num_input_neurons", 5),
        num_hidden_neurons=p.get("num_hidden_neurons", 20),
        num_output_neurons=p.get("num_output_neurons", 5),
    )
    tissue = AgentTissue(params)
    tmp = Path(path).with_suffix(Path(path).suffix + ".network.tmp")
    try:
        tmp.write_text(json.dumps(data["network"]), encoding="utf-8")
        tissue.network = load_network(str(tmp))
    finally:
        tmp.unlink(missing_ok=True)
    return tissue


class PersistentAgentTissue(AgentTissue):
    """AgentTissue with automatic, rotating checkpoint persistence."""

    def __init__(
        self,
        params: NetworkParameters | None = None,
        *,
        save_dir: str | Path = "~/.neuraxon",
        auto_save: bool = True,
        auto_save_triggers: set[str] | None = None,
        keep_last: int = 5,
    ) -> None:
        super().__init__(params)
        self.save_dir = Path(save_dir).expanduser()
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save
        self.auto_save_triggers = set(auto_save_triggers or DEFAULT_AUTO_SAVE_TRIGGERS)
        self.keep_last = max(1, keep_last)
        self._checkpoint_counter = self._discover_checkpoint_counter()

    def think(self, steps: int = 10) -> AgentAction:
        """Run inference and optionally checkpoint after thinking."""
        action = super().think(steps)
        self._maybe_checkpoint("think")
        return action

    def modulate(self, outcome: str) -> dict[str, float]:
        """Apply feedback and optionally checkpoint the learned state."""
        result = super().modulate(outcome)
        self._maybe_checkpoint("modulate")
        return result

    def store_experience(self, action: AgentAction, outcome: str) -> str:
        """Store an experience and optionally checkpoint the updated memory."""
        experience_id = super().store_experience(action, outcome)
        self._maybe_checkpoint("store_experience")
        return experience_id

    def shutdown(self) -> None:
        """Persist an explicit shutdown checkpoint when configured."""
        self._maybe_checkpoint("shutdown")

    def load_latest(self) -> bool:
        """Load the most recent checkpoint into this instance."""
        latest = self._latest_checkpoint()
        if latest is None:
            return False

        loaded = AgentTissue.load(str(latest))
        self.params = loaded.params
        self.network = loaded.network
        self.encoder = loaded.encoder
        self.decoder = loaded.decoder
        self.semantic_policy_enabled = loaded.semantic_policy_enabled
        self.semantic_policy = loaded.semantic_policy
        self.last_action_source = loaded.last_action_source
        self.last_raw_decoder_action = loaded.last_raw_decoder_action
        self._last_observation = loaded._last_observation
        self._temporal_context = loaded._temporal_context
        self._feedback = loaded.feedback
        self.memory = loaded.memory
        self._checkpoint_counter = self._discover_checkpoint_counter()
        return True

    def _maybe_checkpoint(self, trigger: str) -> Path | None:
        if not self.auto_save or trigger not in self.auto_save_triggers:
            return None
        return self._checkpoint()

    def _checkpoint(self) -> Path:
        self._checkpoint_counter += 1
        tmp = self.save_dir / f"checkpoint_{self._checkpoint_counter:06d}.json.tmp"
        final = self.save_dir / f"checkpoint_{self._checkpoint_counter:06d}.json"
        self.save(str(tmp))
        os.replace(tmp, final)
        self._rotate_checkpoints()
        return final

    def _rotate_checkpoints(self) -> None:
        checkpoints = self._checkpoint_files()
        for stale in checkpoints[:-self.keep_last]:
            memory_path = self._memory_path_for_checkpoint(stale)
            stale.unlink(missing_ok=True)
            memory_path.unlink(missing_ok=True)

    def _latest_checkpoint(self) -> Path | None:
        checkpoints = self._checkpoint_files()
        return checkpoints[-1] if checkpoints else None

    def _checkpoint_files(self) -> list[Path]:
        return sorted(
            path for path in self.save_dir.glob("checkpoint_*.json")
            if path.stem.rsplit("_", 1)[-1].isdigit()
        )

    def _discover_checkpoint_counter(self) -> int:
        latest = self._latest_checkpoint()
        if latest is None:
            return 0
        try:
            return int(latest.stem.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            return 0

    @staticmethod
    def _memory_path_for_checkpoint(checkpoint: Path) -> Path:
        return Path(str(checkpoint) + ".memory.json")
