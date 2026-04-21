"""State persistence helpers for neuraxon-agent."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def save_state(tissue: AgentTissue, path: str) -> None:
    """Save tissue state plus metadata to a JSON file."""
    data = {
        "version": 1,
        "params": {
            "num_input_neurons": tissue.params.num_input_neurons,
            "num_hidden_neurons": tissue.params.num_hidden_neurons,
            "num_output_neurons": tissue.params.num_output_neurons,
        },
        "network": tissue.network.to_dict(),
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_state(path: str) -> AgentTissue:
    """Load tissue state from a JSON file."""
    data = json.loads(Path(path).read_text())
    p = data.get("params", {})
    params = NetworkParameters(
        num_input_neurons=p.get("num_input_neurons", 5),
        num_hidden_neurons=p.get("num_hidden_neurons", 20),
        num_output_neurons=p.get("num_output_neurons", 5),
    )
    tissue = AgentTissue(params)
    # Network state restoration is limited by upstream API
    return tissue
