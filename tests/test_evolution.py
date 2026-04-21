"""Tests for AgentEvolution."""
from __future__ import annotations

import tempfile
from pathlib import Path

from neuraxon_agent.evolution import AgentEvolution, EvolutionConfig
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def test_evolution_init() -> None:
    evo = AgentEvolution()
    assert evo.hybrid is not None
    assert len(evo.hybrid.population) > 0


def test_evolution_custom_scenarios() -> None:
    scenarios = [
        {"observation": {"type": "prompt"}, "expected_action": "respond"},
        {"observation": {"type": "tool_result", "status": "error"}, "expected_action": "retry"},
    ]
    config = EvolutionConfig(task_scenarios=scenarios, seasons=2, episodes_per_season=3, seed=42)
    evo = AgentEvolution(config=config)
    summary = evo.evolve()
    assert "initial_fitness" in summary
    assert "final_fitness" in summary
    assert summary["seasons"] == 2


def test_evolution_fitness_improves_or_stable() -> None:
    config = EvolutionConfig(seasons=2, episodes_per_season=2, seed=42)
    evo = AgentEvolution(config=config)
    summary = evo.evolve()
    assert summary["final_fitness"] >= summary["initial_fitness"] - 0.01


def test_evolution_reproducible() -> None:
    config = EvolutionConfig(seasons=2, episodes_per_season=2, seed=123)
    evo1 = AgentEvolution(config=config)
    evo1.evolve()
    weights1 = evo1.best_agent_weights()

    evo2 = AgentEvolution(config=config)
    evo2.evolve()
    weights2 = evo2.best_agent_weights()

    assert weights1 == weights2


def test_evolution_save_load() -> None:
    config = EvolutionConfig(seasons=1, episodes_per_season=1, seed=42)
    evo = AgentEvolution(config=config)
    evo.evolve()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "evo.json"
        evo.save(str(path))
        assert path.exists()
        evo2 = AgentEvolution.load(str(path))
        assert len(evo2.history) == len(evo.history)


def test_evolution_history() -> None:
    config = EvolutionConfig(seasons=1, episodes_per_season=1)
    evo = AgentEvolution(config=config)
    assert len(evo.history) == 0
    evo.evolve()
    assert len(evo.history) == 1
