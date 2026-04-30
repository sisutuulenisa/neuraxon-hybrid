"""End-to-end smoke test for neuraxon-agent."""
from __future__ import annotations

import tempfile
from pathlib import Path

from neuraxon_agent import ActionDecoder, AgentEvolution
from neuraxon_agent.action_contract import normalize_benchmark_action
from neuraxon_agent.persistence import load_state, save_state
from neuraxon_agent.streaming import StreamingLoop
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def test_full_agent_loop() -> None:
    """Run a complete observe-think-act-modulate cycle."""
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)

    # Observe
    tissue.observe({"type": "prompt", "content": "hello"})

    # Think
    action = tissue.think(steps=5)
    assert action.actie_type in ActionDecoder.get_all_defined_actions()
    assert normalize_benchmark_action(action.actie_type) in (
        "execute",
        "query",
        "retry",
        "assertive",
        "explore",
        "cautious",
    )

    # Modulate
    tissue.modulate("success")
    assert tissue.state.dopamine > 0

    # Memory
    tissue.memory.store_experience(
        {"type": "prompt", "content": "hello"},
        action,
        "success"
    )
    recalled = tissue.memory.recall_similar({"type": "prompt"})
    assert len(recalled) > 0


def test_streaming_loop() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    loop = StreamingLoop(tissue)
    events = loop.run([
        {"type": "prompt", "content": "a"},
        {"type": "prompt", "content": "b"},
    ], steps_per_obs=3)
    assert len(events) == 2
    assert events[0].step == 0
    assert events[1].step == 1


def test_persistence_roundtrip() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    tissue.observe({"type": "prompt"})
    tissue.think(steps=3)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(tissue, str(path))
        assert path.exists()
        tissue2 = load_state(str(path))
        assert tissue2.state.num_neurons == tissue.state.num_neurons


def test_evolution_integration() -> None:
    config = {"seasons": 1, "episodes_per_season": 1, "seed": 42}
    evo = AgentEvolution(config=config)
    summary = evo.evolve()
    assert summary["final_fitness"] >= summary["initial_fitness"] - 0.01
