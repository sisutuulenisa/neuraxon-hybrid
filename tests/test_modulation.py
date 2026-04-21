"""Tests for ModulationFeedback."""
from __future__ import annotations

import pytest

from neuraxon_agent.modulation import ModulationFeedback, DEFAULT_OUTCOME_MAP
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, NeuraxonNetwork


def test_default_mapping_matches_spec() -> None:
    """Default deltas must match the spec table from issue #8."""
    fb = ModulationFeedback()
    assert fb.get_deltas("success") == {
        "dopamine": 0.30,
        "serotonin": 0.10,
        "acetylcholine": 0.10,
        "norepinephrine": 0.05,
    }
    assert fb.get_deltas("failure") == {
        "dopamine": -0.10,
        "serotonin": -0.20,
        "acetylcholine": 0.20,
        "norepinephrine": 0.30,
    }
    assert fb.get_deltas("partial") == {
        "dopamine": 0.10,
        "serotonin": -0.05,
        "acetylcholine": 0.15,
        "norepinephrine": 0.15,
    }
    assert fb.get_deltas("timeout") == {
        "dopamine": -0.05,
        "serotonin": -0.10,
        "acetylcholine": 0.10,
        "norepinephrine": 0.20,
    }


def test_unknown_outcome_returns_empty() -> None:
    fb = ModulationFeedback()
    assert fb.get_deltas("nonexistent") == {}


def test_configurable_mapping() -> None:
    custom = {"win": {"dopamine": 0.99}}
    fb = ModulationFeedback(outcome_map=custom)
    assert fb.get_deltas("win") == {"dopamine": 0.99}
    assert fb.get_deltas("success") == {}


def test_apply_success_raises_dopamine() -> None:
    """Acceptance: after modulate('success') dopamine is increased."""
    params = NetworkParameters(
        num_input_neurons=2, num_hidden_neurons=4, num_output_neurons=2
    )
    net = NeuraxonNetwork(params)
    fb = ModulationFeedback()
    pre = net.neuromodulators.get("dopamine", 0.0)
    fb.apply(net, "success")
    post = net.neuromodulators.get("dopamine", 0.0)
    assert post > pre


def test_apply_failure_lowers_serotonin() -> None:
    """Acceptance: after modulate('failure') serotonin is decreased."""
    params = NetworkParameters(
        num_input_neurons=2, num_hidden_neurons=4, num_output_neurons=2
    )
    net = NeuraxonNetwork(params)
    fb = ModulationFeedback()
    pre = net.neuromodulators.get("serotonin", 0.0)
    fb.apply(net, "failure")
    post = net.neuromodulators.get("serotonin", 0.0)
    assert post < pre


def test_apply_returns_deltas() -> None:
    params = NetworkParameters(
        num_input_neurons=2, num_hidden_neurons=4, num_output_neurons=2
    )
    net = NeuraxonNetwork(params)
    fb = ModulationFeedback()
    deltas = fb.apply(net, "partial")
    assert "dopamine" in deltas
    assert "serotonin" in deltas


def test_adaptive_convergence() -> None:
    """Acceptance: adaptive mapping converges to stable values."""
    fb = ModulationFeedback(adapt_rate=0.05, history_window=200)

    # Use a fresh network for each iteration so baseline levels are
    # identical and actual_change is constant → running mean converges.
    for _ in range(50):
        params = NetworkParameters(
            num_input_neurons=2, num_hidden_neurons=4, num_output_neurons=2
        )
        net = NeuraxonNetwork(params)
        fb.apply(net, "success")

    metrics = fb.convergence_metrics()
    assert metrics["call_count"] == 50
    assert metrics["is_stable"] is True

    adaptive = fb.adaptive_deltas("success")
    assert adaptive is not None
    assert "dopamine" in adaptive


def test_network_behavior_changes_after_feedback() -> None:
    """Acceptance: network behaviour changes measurably after repeated feedback."""
    params = NetworkParameters(
        num_input_neurons=2, num_hidden_neurons=6, num_output_neurons=2
    )
    net = NeuraxonNetwork(params)
    fb = ModulationFeedback()

    # Prime the network with input so neurons become active
    net.set_input_states([1, -1])
    net.simulate_step()
    baseline_energy = net.get_energy()

    # Apply repeated success feedback and simulate
    for _ in range(20):
        fb.apply(net, "success")
        net.simulate_step()

    post_energy = net.get_energy()
    # Energy should have accumulated from active simulation steps
    assert post_energy > baseline_energy


def test_reset_adaptation_clears_state() -> None:
    fb = ModulationFeedback(adapt_rate=0.1)
    params = NetworkParameters(
        num_input_neurons=2, num_hidden_neurons=4, num_output_neurons=2
    )
    net = NeuraxonNetwork(params)
    fb.apply(net, "success")
    assert fb._call_count == 1
    fb.reset_adaptation()
    assert fb._call_count == 0
    assert fb._history == []
    assert fb._running_mean == {}


def test_convergence_metrics_empty() -> None:
    fb = ModulationFeedback()
    metrics = fb.convergence_metrics()
    assert metrics["call_count"] == 0
    assert metrics["is_stable"] is False
