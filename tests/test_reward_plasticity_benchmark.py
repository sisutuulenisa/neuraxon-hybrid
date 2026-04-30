"""Tests for reward-driven behavioral plasticity benchmarks."""

from __future__ import annotations

from neuraxon_agent.reward_plasticity_benchmark import (
    generate_reward_plasticity_episodes,
    run_reward_plasticity_benchmark,
)
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters

SMALL_PARAMS = NetworkParameters(
    num_input_neurons=3,
    num_hidden_neurons=5,
    num_output_neurons=2,
)


def test_reward_plasticity_episode_generation_is_seeded_and_hides_final_answer() -> None:
    first = generate_reward_plasticity_episodes(seed=7, episode_count=6)
    second = generate_reward_plasticity_episodes(seed=7, episode_count=6)
    other = generate_reward_plasticity_episodes(seed=8, episode_count=6)

    assert first == second
    assert first != other
    assert len(first) == 6
    assert {episode.expected_action for episode in first} >= {"execute", "query"}
    for episode in first:
        assert episode.training_observation["feedback_cue"] == episode.feedback_cue
        assert "expected_action" not in episode.final_observation
        assert "expected_actions" not in episode.final_observation
        assert "scenario_type" not in episode.final_observation
        assert episode.final_observation["feedback_cue"] == episode.feedback_cue


def test_reward_plasticity_benchmark_reports_before_after_metrics_and_verdict() -> None:
    report = run_reward_plasticity_benchmark(
        seed=11,
        episode_count=8,
        steps_per_observation=1,
        params=SMALL_PARAMS,
    )

    expected_modes = {
        "cold_tissue",
        "feedback_trained_tissue",
        "raw_network_only",
        "semantic_bridge",
        "persisted_checkpoint",
        "random",
        "always_execute",
    }
    assert set(report.modes) == expected_modes
    assert report.episode_count == 8
    assert report.verdict in {
        "behavioral_plasticity_observed",
        "internal_state_changed_without_behavioral_improvement",
        "no_plasticity_observed",
    }
    assert "adapter-only" in report.claim_boundary
    assert "broad Qubic/Neuraxon intelligence" in report.claim_boundary

    for mode, metrics in report.modes.items():
        assert 0.0 <= metrics.before_accuracy <= 1.0, mode
        assert 0.0 <= metrics.after_accuracy <= 1.0, mode
        assert 0.0 <= metrics.decision_change_rate <= 1.0, mode
        assert len(metrics.before_actions) == report.episode_count
        assert len(metrics.after_actions) == report.episode_count
        assert len(metrics.feedback_events) in {0, report.episode_count}
        if mode != "cold_tissue":
            assert len(metrics.feedback_events) == report.episode_count


def test_reward_plasticity_benchmark_records_feedback_application() -> None:
    report = run_reward_plasticity_benchmark(
        seed=3,
        episode_count=6,
        steps_per_observation=1,
        params=SMALL_PARAMS,
    )

    trained = report.modes["feedback_trained_tissue"]
    assert trained.training_feedback_count == 6
    assert {event.outcome for event in trained.feedback_events} <= {"success", "failure"}
    assert any(event.neuromodulator_delta for event in trained.feedback_events)
    assert trained.internal_state_changed in {False, True}


def test_reward_plasticity_report_exports_json_and_markdown(tmp_path) -> None:
    json_path = tmp_path / "reward-plasticity.json"
    markdown_path = tmp_path / "reward-plasticity.md"

    report = run_reward_plasticity_benchmark(
        seed=5,
        episode_count=4,
        steps_per_observation=1,
        params=SMALL_PARAMS,
        output_path=json_path,
        markdown_path=markdown_path,
    )

    assert json_path.exists()
    assert markdown_path.exists()
    assert report.to_dict()["verdict"] in markdown_path.read_text(encoding="utf-8")
    assert "No broad Qubic/Neuraxon intelligence claim" in markdown_path.read_text(
        encoding="utf-8"
    )
