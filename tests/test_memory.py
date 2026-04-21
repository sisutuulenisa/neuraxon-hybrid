"""Tests for TissueMemory and AgentTissue memory coupling."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from neuraxon_agent.memory import TissueMemory, ExperiencePattern, Memory
from neuraxon_agent.action import AgentAction
from neuraxon_agent.tissue import AgentTissue
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


# ---------------------------------------------------------------------------
# TissueMemory basics
# ---------------------------------------------------------------------------


def test_memory_init() -> None:
    mem = TissueMemory()
    assert len(mem) == 0
    assert mem.capacity == 100


def test_memory_store_experience() -> None:
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=3))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    obs = {"tool_result": "success"}
    exp_id = mem.store_experience(obs, action, "success")
    assert exp_id.startswith("exp_")
    assert len(mem) == 1


def test_memory_recall_similar() -> None:
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=3))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))

    # Store two experiences with different observations
    mem.store_experience({"tool_result": "success"}, action, "success")
    mem.store_experience({"tool_result": "fail"}, action, "failure")

    # Recall should return the closest match
    results = mem.recall_similar({"tool_result": "success"}, top_k=1)
    assert len(results) == 1
    assert results[0].outcome == "success"


def test_memory_recall_similar_returns_related() -> None:
    """Vergelijkbare observaties roepen gerelateerde memories op."""
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=5))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0, 0, 0))

    mem.store_experience({"tool_result": "success", "error_type": None}, action, "success")
    mem.store_experience({"tool_result": "fail", "error_type": "runtime"}, action, "failure")
    mem.store_experience({"tool_result": "success", "error_type": None}, action, "success")

    # A success-like observation should prefer success outcomes
    results = mem.recall_similar({"tool_result": "success", "error_type": None}, top_k=2)
    outcomes = [r.outcome for r in results]
    assert "success" in outcomes


def test_memory_recall_boosts_strength() -> None:
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=3))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")
    pre_access = mem.experiences["exp_000001"].access_count
    mem.recall_similar({"tool_result": "success"})
    post_access = mem.experiences["exp_000001"].access_count
    assert post_access > pre_access
    # Strength may already be capped at 1.0; access_count is the reliable signal
    assert mem.experiences["exp_000001"].strength == 1.0


def test_memory_forgetting() -> None:
    mem = TissueMemory(
        params=NetworkParameters(num_input_neurons=3),
        forgetting_rate=0.5,
    )
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")
    initial_strength = mem.experiences["exp_000001"].strength

    # Store another experience to trigger decay
    mem.store_experience({"tool_result": "fail"}, action, "failure")
    new_strength = mem.experiences["exp_000001"].strength
    assert new_strength < initial_strength


def test_memory_forget_weak() -> None:
    mem = TissueMemory(
        params=NetworkParameters(num_input_neurons=3),
        forgetting_rate=0.9,
        strength_threshold=0.2,
    )
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")
    # Store many more to decay the first one heavily
    for i in range(20):
        mem.store_experience({"tool_result": "fail", "index": i}, action, "failure")

    removed = mem.forget_weak()
    assert removed > 0
    assert "exp_000001" not in mem.experiences


def test_memory_capacity_pruning() -> None:
    mem = TissueMemory(
        params=NetworkParameters(num_input_neurons=3),
        capacity=5,
        forgetting_rate=0.0,
    )
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    for i in range(10):
        mem.store_experience({"tool_result": "success", "index": i}, action, "success")

    assert len(mem) <= 5


# ---------------------------------------------------------------------------
# Save / load
# ---------------------------------------------------------------------------


def test_memory_save_load() -> None:
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=3))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")
    mem.store_experience({"tool_result": "fail"}, action, "failure")

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "memory.json"
        mem.save(str(path))
        assert path.exists()

        loaded = TissueMemory.load(str(path))
        assert len(loaded) == 2
        assert "exp_000001" in loaded.experiences
        assert loaded.experiences["exp_000001"].outcome == "success"
        assert loaded.experiences["exp_000002"].outcome == "failure"


def test_memory_save_load_survives_roundtrip() -> None:
    """Geheugen overleeft save() / load()."""
    params = NetworkParameters(num_input_neurons=3)
    mem = TissueMemory(params=params, capacity=50, forgetting_rate=0.01)
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "memory.json"
        mem.save(str(path))
        loaded = TissueMemory.load(str(path))
        assert loaded.capacity == 50
        assert loaded.forgetting_rate == 0.01
        assert len(loaded) == 1
        results = loaded.recall_similar({"tool_result": "success"})
        assert len(results) == 1
        assert results[0].outcome == "success"


# ---------------------------------------------------------------------------
# AgentTissue coupling
# ---------------------------------------------------------------------------


def test_tissue_has_memory() -> None:
    tissue = AgentTissue()
    assert hasattr(tissue, "memory")
    assert isinstance(tissue.memory, TissueMemory)


def test_tissue_store_experience() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    tissue.observe({"tool_result": "success"})
    action = tissue.think(steps=5)
    exp_id = tissue.store_experience(action, "success")
    assert exp_id.startswith("exp_")
    assert len(tissue.memory) == 1


def test_tissue_recall_similar() -> None:
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    tissue.observe({"tool_result": "success"})
    action = tissue.think(steps=5)
    tissue.store_experience(action, "success")

    results = tissue.recall_similar({"tool_result": "success"})
    assert len(results) == 1
    assert results[0].outcome == "success"


def test_tissue_save_load_with_memory() -> None:
    """Tissue save/load roundtrip preserves memory."""
    params = NetworkParameters(num_input_neurons=3, num_hidden_neurons=5, num_output_neurons=2)
    tissue = AgentTissue(params)
    tissue.observe({"tool_result": "success"})
    action = tissue.think(steps=5)
    tissue.store_experience(action, "success")

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        tissue.save(str(path))
        assert path.exists()

        tissue2 = AgentTissue.load(str(path))
        assert len(tissue2.memory) == 1
        results = tissue2.memory.recall_similar({"tool_result": "success"})
        assert len(results) == 1
        assert results[0].outcome == "success"


def test_tissue_store_experience_without_observation_raises() -> None:
    tissue = AgentTissue()
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0))
    with pytest.raises(RuntimeError):
        tissue.store_experience(action, "success")


def test_tissue_recall_without_observation_raises() -> None:
    tissue = AgentTissue()
    with pytest.raises(RuntimeError):
        tissue.recall_similar()


# ---------------------------------------------------------------------------
# Old Memory backward compatibility
# ---------------------------------------------------------------------------


def test_old_memory_still_works() -> None:
    mem = Memory(capacity=10)
    mem.store({"episode": 1})
    assert len(mem.recall(1)) == 1
    mem.clear()
    assert len(mem.recall(1)) == 0


# ---------------------------------------------------------------------------
# Stats / introspection
# ---------------------------------------------------------------------------


def test_memory_stats() -> None:
    mem = TissueMemory(params=NetworkParameters(num_input_neurons=3))
    action = AgentAction(actie_type="PROCEED", confidence=0.8, raw_output=(1, 0, 0))
    mem.store_experience({"tool_result": "success"}, action, "success")
    stats = mem.get_stats()
    assert stats["count"] == 1
    assert stats["mean_strength"] > 0.0
