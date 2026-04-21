"""Tissue layer — NeuraxonNetwork wrapper for agent runtime."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, NeuraxonNetwork
from neuraxon_agent.perception import PerceptionEncoder
from neuraxon_agent.action import ActionDecoder, AgentAction


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

    def __init__(self, params: NetworkParameters | None = None) -> None:
        self.params = params or NetworkParameters()
        self.network = NeuraxonNetwork(self.params)
        self.encoder = PerceptionEncoder(self.params.num_input_neurons)
        self.decoder = ActionDecoder(self.params.num_output_neurons)
        self._last_observation: dict[str, Any] | None = None

    def observe(self, observation: dict[str, Any]) -> None:
        """Encode an observation and feed it to the network input neurons."""
        self._last_observation = observation
        encoded = self.encoder.encode(observation)
        self.network.set_input_states(encoded)

    def think(self, steps: int = 10) -> AgentAction:
        """Run the network for N steps and decode the output into an action."""
        for _ in range(steps):
            self.network.simulate_step()
        output_states = self.network.get_output_states()
        return self.decoder.decode(output_states)

    def modulate(self, outcome: str) -> None:
        """Apply neuromodulator feedback based on outcome."""
        if outcome == "success":
            reward = {"dopamine": 1.0, "serotonin": 0.5}
        elif outcome == "failure":
            reward = {"dopamine": -1.0, "serotonin": -0.5}
        elif outcome == "partial":
            reward = {"dopamine": 0.3, "serotonin": 0.0}
        else:
            reward = {}
        self.network.modulate(reward)

    def save(self, path: str) -> None:
        """Serialize network state to JSON."""
        data = self.network.to_dict()
        data["_params"] = {
            "num_input_neurons": self.params.num_input_neurons,
            "num_hidden_neurons": self.params.num_hidden_neurons,
            "num_output_neurons": self.params.num_output_neurons,
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str) -> AgentTissue:
        """Deserialize network state from JSON."""
        data = json.loads(Path(path).read_text())
        params_data = data.pop("_params", {})
        params = NetworkParameters(
            num_input_neurons=params_data.get("num_input_neurons", 5),
            num_hidden_neurons=params_data.get("num_hidden_neurons", 20),
            num_output_neurons=params_data.get("num_output_neurons", 5),
        )
        instance = cls(params)
        # TODO: restore full network state from dict when upstream supports from_dict
        return instance

    @property
    def state(self) -> TissueState:
        """Return current observable tissue state."""
        nm = self.network.neuromodulators
        return TissueState(
            energy=self.network.get_energy(),
            activity=sum(abs(s) for s in self.network.get_all_states()) / max(len(self.network.all_neurons), 1),
            step_count=self.network.step_count,
            dopamine=nm.get("dopamine", 0.0),
            serotonin=nm.get("serotonin", 0.0),
            acetylcholine=nm.get("acetylcholine", 0.0),
            norepinephrine=nm.get("norepinephrine", 0.0),
            num_neurons=len(self.network.all_neurons),
            num_synapses=len(self.network.synapses),
        )
