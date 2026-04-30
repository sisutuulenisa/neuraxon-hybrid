"""Restart-oriented checkpoint persistence evaluation tests."""

from __future__ import annotations

import json
from pathlib import Path

from neuraxon_agent.action_contract import normalize_benchmark_action
from neuraxon_agent.checkpoint_persistence_evaluation import (
    DEFAULT_CHECKPOINT_PERSISTENCE_MARKDOWN_PATH,
    DEFAULT_CHECKPOINT_PERSISTENCE_PATH,
    RestartPersistenceEpisode,
    generate_restart_persistence_episodes,
    run_checkpoint_persistence_evaluation,
)
from neuraxon_agent.persistence import CHECKPOINT_SCHEMA_VERSION, PersistenceLoadError
from neuraxon_agent.tissue import AgentTissue


def test_agent_tissue_checkpoint_restores_temporal_context_after_restart(tmp_path: Path) -> None:
    checkpoint = tmp_path / "state.json"
    final_probe = {
        "intent": "temporal_decision_probe",
        "probe": "choose_action_from_prior_dynamics",
    }
    tissue = AgentTissue()
    tissue.observe({"signal": "parameters_complete", "missing_count": 0, "risk": "low"})
    tissue.think(steps=1)

    tissue.save(str(checkpoint))
    loaded = AgentTissue.load(str(checkpoint))
    loaded.observe(final_probe)
    action = loaded.think(steps=1)

    assert normalize_benchmark_action(action.actie_type) == "execute"
    assert loaded.last_action_source == "temporal_context_bridge"


def test_agent_tissue_load_rejects_incompatible_schema_version(tmp_path: Path) -> None:
    checkpoint = tmp_path / "state.json"
    tissue = AgentTissue()
    tissue.save(str(checkpoint))
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    payload["_checkpoint_schema_version"] = CHECKPOINT_SCHEMA_VERSION + 100
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")

    try:
        AgentTissue.load(str(checkpoint))
    except PersistenceLoadError as exc:
        assert "Unsupported checkpoint schema version" in str(exc)
    else:  # pragma: no cover - failure path assertion
        raise AssertionError("incompatible schema version should fail loudly")


def test_restart_persistence_evaluation_compares_persisted_cold_and_bad_checkpoints(
    tmp_path: Path,
) -> None:
    report = run_checkpoint_persistence_evaluation(
        output_path=tmp_path / "persistence_value.json",
        markdown_path=tmp_path / "persistence_value.md",
        workspace_dir=tmp_path / "workspace",
    )

    assert report.episode_count == len(generate_restart_persistence_episodes())
    assert set(report.mode_metrics) == {
        "persisted_checkpoint",
        "cold_start",
        "missing_checkpoint",
        "corrupt_checkpoint",
        "incompatible_checkpoint",
    }
    assert report.mode_metrics["persisted_checkpoint"].success_count == report.episode_count
    assert report.mode_metrics["cold_start"].success_count < report.mode_metrics[
        "persisted_checkpoint"
    ].success_count
    assert report.mode_metrics["missing_checkpoint"].failure_modes["missing_checkpoint"] == 1
    assert report.mode_metrics["corrupt_checkpoint"].failure_modes["corrupt_checkpoint"] == 1
    assert report.mode_metrics["incompatible_checkpoint"].failure_modes[
        "incompatible_checkpoint"
    ] == 1
    assert report.persisted_beats_cold_start is True
    assert "Persisted checkpoint mode beat cold-start" in report.verdict

    output = tmp_path / "persistence_value.json"
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode_metrics"]["persisted_checkpoint"]["success_rate"] == 1.0
    assert payload["mode_metrics"]["cold_start"]["success_rate"] < 1.0

    markdown = (tmp_path / "persistence_value.md").read_text(encoding="utf-8")
    assert "# Checkpoint Persistence Decision-Value Evaluation" in markdown
    assert "missing checkpoint" in markdown.lower()
    assert "corrupt checkpoint" in markdown.lower()
    assert "schema" in markdown.lower()
    assert "measured decision value" in markdown.lower()


def test_restart_persistence_episodes_are_deterministic() -> None:
    first = run_checkpoint_persistence_evaluation(
        output_path=None,
        markdown_path=None,
        episodes=[
            RestartPersistenceEpisode(
                name="complete_then_probe",
                episode_a=[{"signal": "parameters_complete", "missing_count": 0, "risk": "low"}],
                episode_b=[
                    {
                        "intent": "temporal_decision_probe",
                        "probe": "choose_action_from_prior_dynamics",
                    }
                ],
                expected_action="execute",
                seed=7,
            )
        ]
    )
    second = run_checkpoint_persistence_evaluation(
        output_path=None,
        markdown_path=None,
        episodes=[
            RestartPersistenceEpisode(
                name="complete_then_probe",
                episode_a=[{"signal": "parameters_complete", "missing_count": 0, "risk": "low"}],
                episode_b=[
                    {
                        "intent": "temporal_decision_probe",
                        "probe": "choose_action_from_prior_dynamics",
                    }
                ],
                expected_action="execute",
                seed=7,
            )
        ]
    )

    assert first.to_dict() == second.to_dict()


def test_default_persistence_report_paths_are_tracked_benchmark_artifacts() -> None:
    assert DEFAULT_CHECKPOINT_PERSISTENCE_PATH.as_posix().endswith(
        "benchmarks/results/checkpoint_persistence_value.json"
    )
    assert DEFAULT_CHECKPOINT_PERSISTENCE_MARKDOWN_PATH.as_posix().endswith(
        "benchmarks/results/checkpoint_persistence_value.md"
    )
