"""Tissue layer — NeuraxonNetwork wrapper for agent runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neuraxon_agent.action import ActionDecoder, AgentAction
from neuraxon_agent.memory import TissueMemory
from neuraxon_agent.modulation import ModulationFeedback
from neuraxon_agent.perception import PerceptionEncoder
from neuraxon_agent.semantic_policy import SemanticTissuePolicy
from neuraxon_agent.temporal_context import TemporalContextBuffer
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, NeuraxonNetwork, load_network

CHECKPOINT_SCHEMA_VERSION = 1


class PersistenceLoadError(ValueError):
    """Raised when a tissue checkpoint cannot be safely restored."""


@dataclass
class TissueState:
    """Observable state of the agent tissue."""

    energy: float
    activity: float
    step_count: int
    dopamine: float
    serotonin: float
    acetylcholine: float
    norepinephrine: float
    num_neurons: int
    num_synapses: int


class AgentTissue:
    """Wraps NeuraxonNetwork for agent runtime: perception, thinking, action, modulation."""

    def __init__(
        self,
        params: NetworkParameters | None = None,
        semantic_policy: SemanticTissuePolicy | None = None,
        semantic_policy_enabled: bool = True,
        temporal_context_enabled: bool = True,
    ) -> None:
        self.params = params or NetworkParameters()
        self.network = NeuraxonNetwork(self.params)
        self.encoder = PerceptionEncoder(self.params.num_input_neurons)
        self.decoder = ActionDecoder(self.params.num_output_neurons)
        self.semantic_policy_enabled = semantic_policy_enabled
        self.temporal_context_enabled = temporal_context_enabled
        self.semantic_policy = semantic_policy or SemanticTissuePolicy()
        self.last_action_source: str | None = None
        self.last_raw_decoder_action: AgentAction | None = None
        self._last_observation: dict[str, Any] | None = None
        self._temporal_context = TemporalContextBuffer()
        self._feedback = ModulationFeedback()
        self.memory = TissueMemory(self.params)

    def observe(self, observation: dict[str, Any]) -> None:
        """Encode an observation and feed it to the network input neurons."""
        self._last_observation = observation
        self._temporal_context.observe(observation)
        encoded = self.encoder.encode(observation)
        self.network.set_input_states(encoded)

    def think(self, steps: int = 10) -> AgentAction:
        """Run the network for N steps and decode the output into an action."""
        for _ in range(steps):
            self.network.simulate_step()
        output_states = self.network.get_output_states()
        raw_action = self.decoder.decode(output_states)
        self.last_raw_decoder_action = raw_action
        if self._last_observation is not None:
            if self.temporal_context_enabled:
                temporal_action = self._temporal_context.decide(self._last_observation)
                if temporal_action is not None:
                    self.last_action_source = "temporal_context_bridge"
                    return temporal_action
            if self.semantic_policy_enabled:
                semantic_action = self.semantic_policy.decide(self._last_observation)
                if semantic_action is not None:
                    self.last_action_source = "semantic_bridge"
                    return semantic_action
        self.last_action_source = "raw_network"
        return raw_action

    def modulate(self, outcome: str) -> dict[str, float]:
        """Apply neuromodulator feedback based on outcome.

        Uses :class:`ModulationFeedback` to translate *outcome* into
        neuromodulator deltas and applies them to the underlying network.

        Returns the deltas that were applied.
        """
        return self._feedback.apply(self.network, outcome)

    @property
    def feedback(self) -> ModulationFeedback:
        """Return the :class:`ModulationFeedback` instance used by this tissue."""
        return self._feedback

    def store_experience(self, action: AgentAction, outcome: str) -> str:
        """Store the current observation + *action* + *outcome* in tissue memory.

        Returns the experience ID.
        """
        if self._last_observation is None:
            raise RuntimeError("No observation to store; call observe() first.")
        return self.memory.store_experience(self._last_observation, action, outcome)

    def recall_similar(
        self, observation: dict[str, Any] | None = None, top_k: int = 1
    ) -> list[Any]:
        """Recall experiences similar to *observation* (or the last observation)."""
        obs = observation if observation is not None else self._last_observation
        if obs is None:
            raise RuntimeError("No observation to recall against; call observe() first.")
        return self.memory.recall_similar(obs, top_k=top_k)

    def save(self, path: str) -> None:
        """Serialize tissue and memory state to JSON."""
        data = self.network.to_dict()
        data["_checkpoint_schema_version"] = CHECKPOINT_SCHEMA_VERSION
        data["_params"] = {
            "num_input_neurons": self.params.num_input_neurons,
            "num_hidden_neurons": self.params.num_hidden_neurons,
            "num_output_neurons": self.params.num_output_neurons,
        }
        data["_runtime_context"] = {
            "last_observation": self._last_observation,
            "temporal_context": self._temporal_context.to_dict(),
            "semantic_policy_enabled": self.semantic_policy_enabled,
            "temporal_context_enabled": self.temporal_context_enabled,
            "last_action_source": self.last_action_source,
        }
        # Save memory alongside network
        memory_path = str(Path(path).with_suffix("")) + ".memory.json"
        self.memory.save(memory_path)
        data["_memory_path"] = memory_path
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str) -> AgentTissue:
        """Deserialize tissue and memory state from JSON."""
        try:
            data = json.loads(Path(path).read_text())
        except json.JSONDecodeError as exc:
            raise PersistenceLoadError(f"Corrupt checkpoint JSON: {path}") from exc
        schema_version = data.get("_checkpoint_schema_version", 0)
        if schema_version > CHECKPOINT_SCHEMA_VERSION:
            raise PersistenceLoadError(
                "Unsupported checkpoint schema version "
                f"{schema_version}; max supported is {CHECKPOINT_SCHEMA_VERSION}"
            )
        params_data = data.pop("_params", {})
        params = NetworkParameters(
            num_input_neurons=params_data.get("num_input_neurons", 5),
            num_hidden_neurons=params_data.get("num_hidden_neurons", 20),
            num_output_neurons=params_data.get("num_output_neurons", 5),
        )
        instance = cls(params)
        try:
            instance.network = load_network(path)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise PersistenceLoadError(f"Invalid checkpoint payload: {path}") from exc
        # Restore memory if saved alongside
        memory_path = data.pop("_memory_path", None)
        if memory_path and Path(memory_path).exists():
            instance.memory = TissueMemory.load(memory_path)
        runtime_context = data.pop("_runtime_context", {})
        if isinstance(runtime_context, dict):
            last_observation = runtime_context.get("last_observation")
            if isinstance(last_observation, dict):
                instance._last_observation = last_observation
            temporal_context = runtime_context.get("temporal_context")
            if isinstance(temporal_context, dict):
                instance._temporal_context = TemporalContextBuffer.from_dict(temporal_context)
            instance.semantic_policy_enabled = bool(
                runtime_context.get("semantic_policy_enabled", instance.semantic_policy_enabled)
            )
            instance.temporal_context_enabled = bool(
                runtime_context.get("temporal_context_enabled", instance.temporal_context_enabled)
            )
            last_action_source = runtime_context.get("last_action_source")
            if isinstance(last_action_source, str):
                instance.last_action_source = last_action_source
        return instance

    @property
    def state(self) -> TissueState:
        """Return current observable tissue state."""
        nm = self.network.neuromodulators
        all_states_dict = self.network.get_all_states()
        flat_states: list[int] = []
        for group in all_states_dict.values():
            flat_states.extend(group)
        activity = sum(abs(s) for s in flat_states) / max(len(flat_states), 1)
        return TissueState(
            energy=self.network.get_energy(),
            activity=activity,
            step_count=self.network.step_count,
            dopamine=nm.get("dopamine", 0.0),
            serotonin=nm.get("serotonin", 0.0),
            acetylcholine=nm.get("acetylcholine", 0.0),
            norepinephrine=nm.get("norepinephrine", 0.0),
            num_neurons=len(self.network.all_neurons),
            num_synapses=len(self.network.synapses),
        )
