"""Tests for automatic tissue persistence."""

from __future__ import annotations

from pathlib import Path

from neuraxon_agent import AgentTissue, PersistentAgentTissue
from neuraxon_agent.persistence import load_state, save_state
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def small_params() -> NetworkParameters:
    return NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)


def test_agent_tissue_load_restores_network_runtime_state(tmp_path: Path) -> None:
    tissue = AgentTissue(small_params(), semantic_policy_enabled=False)
    tissue.observe({"tool_result": "success"})
    tissue.think(steps=3)
    tissue.modulate("success")
    before_state = tissue.state
    path = tmp_path / "state.json"

    tissue.save(str(path))
    loaded = AgentTissue.load(str(path))

    assert loaded.state.step_count == before_state.step_count
    assert loaded.state.energy == before_state.energy
    assert loaded.state.dopamine == before_state.dopamine
    assert loaded.network.get_output_states() == tissue.network.get_output_states()


def test_save_state_load_state_preserves_network_and_memory(tmp_path: Path) -> None:
    tissue = AgentTissue(small_params(), semantic_policy_enabled=False)
    tissue.observe({"tool_result": "success"})
    action = tissue.think(steps=3)
    tissue.store_experience(action, "success")
    path = tmp_path / "state.json"

    save_state(tissue, str(path))
    loaded = load_state(str(path))

    assert loaded.state.step_count == tissue.state.step_count
    assert len(loaded.memory) == 1
    assert loaded.recall_similar({"tool_result": "success"})[0].outcome == "success"


def test_persistent_tissue_checkpoints_after_configured_trigger(tmp_path: Path) -> None:
    tissue = PersistentAgentTissue(
        small_params(),
        save_dir=tmp_path,
        auto_save=True,
        auto_save_triggers={"modulate"},
    )
    tissue.observe({"tool_result": "success"})
    tissue.think(steps=1)

    assert list(tmp_path.glob("checkpoint_*.json")) == []
    tissue.modulate("success")

    checkpoints = sorted(
        path for path in tmp_path.glob("checkpoint_*.json")
        if path.stem.rsplit("_", 1)[-1].isdigit()
    )
    assert [p.name for p in checkpoints] == ["checkpoint_000001.json"]
    assert not list(tmp_path.glob("*.tmp"))


def test_persistent_tissue_checkpoint_rotation_keeps_latest(tmp_path: Path) -> None:
    tissue = PersistentAgentTissue(
        small_params(),
        save_dir=tmp_path,
        auto_save=True,
        auto_save_triggers={"modulate"},
        keep_last=2,
    )
    tissue.observe({"tool_result": "success"})
    tissue.think(steps=1)

    for _ in range(4):
        tissue.modulate("success")

    checkpoints = sorted(
        path for path in tmp_path.glob("checkpoint_*.json")
        if path.stem.rsplit("_", 1)[-1].isdigit()
    )
    assert [p.name for p in checkpoints] == [
        "checkpoint_000003.json",
        "checkpoint_000004.json",
    ]
    assert not (tmp_path / "checkpoint_000001.json.memory.json").exists()


def test_persistent_tissue_load_latest_restores_most_recent_checkpoint(tmp_path: Path) -> None:
    tissue = PersistentAgentTissue(
        small_params(),
        save_dir=tmp_path,
        auto_save=True,
        auto_save_triggers={"modulate", "store_experience"},
    )
    tissue.observe({"tool_result": "success"})
    action = tissue.think(steps=2)
    tissue.store_experience(action, "success")
    tissue.modulate("success")

    rehydrated = PersistentAgentTissue(small_params(), save_dir=tmp_path, auto_save=False)
    assert rehydrated.load_latest() is True

    assert rehydrated.state.step_count == tissue.state.step_count
    assert rehydrated.state.dopamine == tissue.state.dopamine
    assert len(rehydrated.memory) == 1


def test_persistent_tissue_shutdown_checkpoint_is_explicit(tmp_path: Path) -> None:
    tissue = PersistentAgentTissue(
        small_params(),
        save_dir=tmp_path,
        auto_save=True,
        auto_save_triggers={"shutdown"},
    )
    tissue.observe({"tool_result": "success"})
    tissue.think(steps=1)

    tissue.shutdown()

    assert (tmp_path / "checkpoint_000001.json").exists()
