"""Tests for AgentTissue."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from neuraxon_agent.tissue import AgentTissue, TissueState
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def test_tissue_init() -> None:
    tissue = AgentTissue()
    assert tissue.state.num_neurons > 0
    assert tissue.state.num_synapses > 0


def test_tissue_observe() -> None:
    tissue = AgentTissue()
    tissue.observe({"type": "tool_result", "status": "success", "value": 42})
    assert tissue._last_observation is not None


def test_tissue_think() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    tissue.observe({"type": "prompt", "content": "hello"})
    action = tissue.think(steps=5)
    defined_actions = {"PROCEED", "PAUSE", "RETRY", "ESCALATE", "EXPLORE"}
    assert action.actie_type in defined_actions
    assert 0.0 <= action.confidence <= 1.0


def test_tissue_can_disable_semantic_policy_and_use_raw_decoder_path() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params, semantic_policy_enabled=False)
    tissue.observe(
        {
            "scenario_type": "simple_tool_call",
            "intent": "call_tool",
            "parameters": {"target": "resource", "mode": "read"},
            "missing_parameters": [],
        }
    )

    action = tissue.think(steps=1)

    assert action == tissue.decoder.last()
    assert tissue.last_action_source == "raw_network"


def test_tissue_modulate_success() -> None:
    tissue = AgentTissue()
    pre = tissue.state.dopamine
    deltas = tissue.modulate("success")
    post = tissue.state.dopamine
    assert post > pre
    assert "dopamine" in deltas


def test_tissue_modulate_failure() -> None:
    tissue = AgentTissue()
    pre = tissue.state.serotonin
    deltas = tissue.modulate("failure")
    post = tissue.state.serotonin
    assert post < pre
    assert "dopamine" in deltas


def test_tissue_save_load() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        tissue.save(str(path))
        assert path.exists()
        data = json.loads(path.read_text())
        assert "_params" in data
        tissue2 = AgentTissue.load(str(path))
        assert tissue2.state.num_neurons == tissue.state.num_neurons


def test_tissue_state_returns_tissue_state() -> None:
    tissue = AgentTissue()
    state = tissue.state
    assert isinstance(state, TissueState)
    assert hasattr(state, "energy")
    assert hasattr(state, "dopamine")


def test_tissue_feedback_property() -> None:
    tissue = AgentTissue()
    fb = tissue.feedback
    assert fb is not None
    assert fb.get_deltas("success")["dopamine"] == 0.30
