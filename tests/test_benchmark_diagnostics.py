"""Tests for diagnosing the Neuraxon tissue benchmark 0% accuracy."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from neuraxon_agent.benchmark import BenchmarkScenario
from neuraxon_agent.benchmark_diagnostics import diagnose_tissue_action_mapping
from neuraxon_agent.scenarios import MOCK_AGENT_ACTIONS


def _diagnostic_scenarios() -> list[BenchmarkScenario]:
    return [
        BenchmarkScenario(
            name="ready-tool",
            scenario_type="simple_tool_call",
            observation_sequence=[{"tool_result": "success", "previous_outcome": "success"}],
            expected_optimal_action="execute",
            expected_actions=("execute",),
            difficulty=1.0,
        ),
        BenchmarkScenario(
            name="missing-parameter",
            scenario_type="missing_params_tool_call",
            observation_sequence=[{"tool_result": "fail", "error_type": "auth"}],
            expected_optimal_action="query",
            expected_actions=("query",),
            difficulty=2.0,
        ),
        BenchmarkScenario(
            name="failed-tool",
            scenario_type="failed_tool_call",
            observation_sequence=[{"tool_result": "fail", "error_type": "runtime"}],
            expected_optimal_action="retry",
            expected_actions=("retry",),
            difficulty=2.0,
        ),
    ]


def test_diagnostics_use_normalized_benchmark_action_contract(tmp_path: Path) -> None:
    diagnostics = diagnose_tissue_action_mapping(
        scenarios=_diagnostic_scenarios(),
        seeds=(0, 1),
        steps_per_observation=1,
        output_dir=tmp_path,
    )

    assert diagnostics.run_count == 6
    assert diagnostics.expected_actions == {"execute", "query", "retry"}
    assert diagnostics.decoder_actions == {"PROCEED", "PAUSE", "RETRY", "ESCALATE", "EXPLORE"}
    assert diagnostics.normalized_decoder_actions >= {"execute", "query", "retry"}
    assert diagnostics.missing_decoder_actions == set()
    assert diagnostics.root_cause != "action_vocabulary_mismatch"


def test_diagnostics_export_trace_json_confusion_csv_and_report(tmp_path: Path) -> None:
    diagnostics = diagnose_tissue_action_mapping(
        scenarios=_diagnostic_scenarios(),
        seeds=(0,),
        steps_per_observation=1,
        output_dir=tmp_path,
    )

    assert diagnostics.output_paths.trace_json == tmp_path / "action_mapping_traces.json"
    assert diagnostics.output_paths.confusion_csv == tmp_path / "action_confusion_matrix.csv"
    assert diagnostics.output_paths.report_md == tmp_path / "action_mapping_diagnostic_report.md"

    trace_payload = json.loads(diagnostics.output_paths.trace_json.read_text())
    first_trace = trace_payload["traces"][0]
    assert first_trace["scenario_name"] == "ready-tool"
    assert first_trace["observation_trace"][0]["observation"] == {
        "tool_result": "success",
        "previous_outcome": "success",
    }
    assert first_trace["observation_trace"][0]["encoded_input"] == [1, 1, 0, 0, 1]
    assert set(first_trace) >= {
        "seed",
        "scenario_name",
        "expected_action",
        "decoded_action",
        "raw_output",
        "confidence",
        "outcome",
    }

    confusion_rows = list(csv.DictReader(diagnostics.output_paths.confusion_csv.open()))
    assert {row["expected_action"] for row in confusion_rows} == {"execute", "query", "retry"}
    assert sum(int(row["count"]) for row in confusion_rows) == 3

    report = diagnostics.output_paths.report_md.read_text()
    assert "# Neuraxon Tissue Action Mapping Diagnostic" in report
    assert "ActionDecoder emits" in report
    assert "normalized benchmark actions" in report
    assert "mock benchmark expects" in report
    assert "memory persistence" in report.lower()
    assert "visual perception" in report.lower()


def test_default_diagnostics_explain_remaining_post_contract_gap(tmp_path: Path) -> None:
    diagnostics = diagnose_tissue_action_mapping(output_dir=tmp_path)

    assert diagnostics.run_count == 700
    assert diagnostics.expected_actions == MOCK_AGENT_ACTIONS
    assert diagnostics.missing_decoder_actions == {"cautious"}
    assert diagnostics.root_cause in {
        "network_never_reaches_expected_actions",
        "partially_working",
    }
    assert diagnostics.output_paths.report_md.exists()
