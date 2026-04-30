"""Holdout/noisy benchmark coverage for the semantic tissue policy."""

from __future__ import annotations

from neuraxon_agent.baselines import run_baseline_benchmarks
from neuraxon_agent.holdout_generalization import (
    generate_anti_oracle_temporal_scenarios,
    generate_holdout_noisy_scenarios,
    generate_temporal_dynamics_scenarios,
    measure_semantic_policy_coverage,
    run_holdout_generalization_benchmark,
)
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue_benchmark import run_neuraxon_tissue_benchmark


def test_holdout_noisy_scenarios_are_deterministic_and_semantically_balanced() -> None:
    base_scenarios = load_mock_agent_scenarios()

    first = generate_holdout_noisy_scenarios(base_scenarios)
    second = generate_holdout_noisy_scenarios(base_scenarios)

    assert first == second
    assert len(first) == len(base_scenarios)
    assert {scenario.expected_optimal_action for scenario in first} == {
        "execute",
        "query",
        "retry",
        "explore",
        "cautious",
        "assertive",
    }
    assert all(scenario.name.startswith("holdout_noisy_") for scenario in first)
    assert all(scenario.scenario_type.startswith("holdout_") for scenario in first)
    assert all("noise_marker" in scenario.observation_sequence[-1] for scenario in first)


def test_holdout_noisy_scenarios_do_not_rely_on_original_scenario_type_labels() -> None:
    scenarios = generate_holdout_noisy_scenarios(load_mock_agent_scenarios())

    observed_types = {
        scenario.observation_sequence[-1].get("scenario_type") for scenario in scenarios
    }

    assert "simple_tool_call" not in observed_types
    assert "complex_multi_step" not in observed_types
    assert "error_recovery" not in observed_types


def test_holdout_noisy_scenarios_are_semantic_policy_covered_not_true_generalization() -> None:
    scenarios = generate_holdout_noisy_scenarios(load_mock_agent_scenarios())

    coverage = measure_semantic_policy_coverage(scenarios)

    assert coverage.scenario_count == 140
    assert coverage.covered_count == 140
    assert coverage.coverage_rate == 1.0
    assert "semantic_policy_oracle" in coverage.warning


def test_temporal_dynamics_scenarios_hide_action_oracles_in_final_probe() -> None:
    scenarios = generate_temporal_dynamics_scenarios()

    final_observations = [scenario.observation_sequence[-1] for scenario in scenarios]

    assert len(scenarios) >= 72
    assert {scenario.expected_optimal_action for scenario in scenarios} == {
        "execute",
        "query",
        "retry",
        "explore",
        "cautious",
        "assertive",
    }
    assert {scenario.scenario_type for scenario in scenarios} >= {
        "temporal_counterfactual",
        "temporal_noise_perturbation",
    }
    assert {len(scenario.observation_sequence) for scenario in scenarios} >= {3, 4, 5}
    assert all(len(scenario.observation_sequence) >= 3 for scenario in scenarios)
    assert all(
        observation.get("intent") == "temporal_decision_probe"
        for observation in final_observations
    )
    assert all("scenario_type" not in observation for observation in final_observations)
    assert all("missing_parameters" not in observation for observation in final_observations)
    assert all("retryable" not in observation for observation in final_observations)
    assert all("known_options" not in observation for observation in final_observations)
    assert all("confidence_signal" not in observation for observation in final_observations)


def test_temporal_dynamics_counterfactuals_require_prior_state() -> None:
    scenarios = generate_temporal_dynamics_scenarios()
    final_probe_groups: dict[tuple[tuple[str, object], ...], set[str]] = {}

    for scenario in scenarios:
        final_probe = tuple(sorted(scenario.observation_sequence[-1].items()))
        final_probe_groups.setdefault(final_probe, set()).add(scenario.expected_optimal_action)

    assert any(len(expected_actions) > 1 for expected_actions in final_probe_groups.values())


def test_temporal_dynamics_summary_uses_temporal_specific_baselines() -> None:
    report = run_holdout_generalization_benchmark(seeds=(0, 1), steps_per_observation=1)
    temporal = report.to_dict()["temporal_dynamics"]

    assert temporal["scenario_count"] >= 72
    assert temporal["seed_count"] == 2
    assert set(temporal["baselines"]) >= {
        "random",
        "always_execute",
        "last_observation_only",
        "sequence_majority",
        "semantic_policy_only",
    }
    assert temporal["baselines"]["semantic_policy_only"]["success_rate"] == 0.0
    assert temporal["neuraxon_tissue"]["run_count"] == temporal["scenario_count"] * 2
    assert "semantic policy bridge result" in report.interpretation
    assert "explicit temporal context adapter" in temporal["interpretation"]
    assert "raw Neuraxon network dynamics" in temporal["interpretation"]


def test_semantic_tissue_beats_always_execute_on_holdout_noisy_benchmark() -> None:
    scenarios = generate_holdout_noisy_scenarios(load_mock_agent_scenarios())

    tissue_report = run_neuraxon_tissue_benchmark(scenarios, seeds=(0,), steps_per_observation=1)
    baseline_reports = run_baseline_benchmarks(scenarios)

    assert tissue_report.success_count > baseline_reports["always_execute"].success_count
    assert tissue_report.success_count == tissue_report.run_count


def test_temporal_dynamics_benchmark_exposes_single_probe_limitation() -> None:
    scenarios = generate_temporal_dynamics_scenarios()

    tissue_report = run_neuraxon_tissue_benchmark(scenarios, seeds=(0,), steps_per_observation=1)

    assert tissue_report.run_count == len(scenarios)
    assert tissue_report.success_count == tissue_report.run_count
    assert {result.action_source for result in tissue_report.results} >= {
        "temporal_context_bridge"
    }


def test_temporal_context_tissue_beats_last_observation_and_always_execute() -> None:
    scenarios = generate_temporal_dynamics_scenarios()

    tissue_report = run_neuraxon_tissue_benchmark(scenarios, seeds=(0,), steps_per_observation=1)
    baseline_reports = run_holdout_generalization_benchmark(
        scenarios=[], seeds=(0,), steps_per_observation=1
    ).temporal_dynamics.baselines

    assert tissue_report.success_count > baseline_reports["last_observation_only"].success_count
    assert tissue_report.success_count > baseline_reports["always_execute"].success_count


def test_holdout_generalization_summary_is_serializable_and_critical() -> None:
    report = run_holdout_generalization_benchmark(seeds=(0,), steps_per_observation=1)

    payload = report.to_dict()

    assert payload["scenario_count"] == 140
    assert payload["neuraxon_tissue"]["success_rate"] == 1.0
    assert payload["semantic_policy_coverage"]["coverage_rate"] == 1.0
    assert payload["temporal_dynamics"]["scenario_count"] >= 6
    assert payload["temporal_dynamics"]["neuraxon_tissue"]["success_rate"] == 1.0
    assert payload["temporal_dynamics"]["neuraxon_tissue"]["success_rate"] > payload[
        "temporal_dynamics"
    ]["baselines"]["last_observation_only"]["success_rate"]
    assert payload["temporal_dynamics"]["neuraxon_tissue"]["success_rate"] > payload[
        "temporal_dynamics"
    ]["baselines"]["always_execute"]["success_rate"]
    assert (
        payload["baselines"]["always_execute"]["success_rate"]
        < payload["neuraxon_tissue"]["success_rate"]
    )
    assert payload["decision"] == "pass_temporal_context_bridge_evidence"
    assert "explicit temporal context adapter" in payload["interpretation"]


def test_anti_oracle_temporal_scenarios_are_split_masked_and_counterfactual() -> None:
    first = generate_anti_oracle_temporal_scenarios(seed=17)
    second = generate_anti_oracle_temporal_scenarios(seed=17)

    assert first == second
    assert {scenario.scenario_type for scenario in first} == {
        "anti_oracle_train",
        "anti_oracle_test",
    }
    assert {scenario.expected_optimal_action for scenario in first} == {
        "execute",
        "query",
        "retry",
        "explore",
        "cautious",
        "assertive",
    }
    assert all(
        scenario.observation_sequence[-1] == {"z0": 0, "z1": "probe", "z2": 1}
        for scenario in first
    )
    assert all(
        "signal" not in observation
        and "risk" not in observation
        and "missing_count" not in observation
        and "expected_action" not in observation
        and "latent_action_hint" not in observation
        for scenario in first
        for observation in scenario.observation_sequence
    )

    pair_groups: dict[tuple[int, str, int], set[str]] = {}
    aggregate_signatures: dict[tuple[tuple[float, ...], ...], set[str]] = {}
    for scenario in first:
        observations = scenario.observation_sequence[:-1]
        pair_id = (observations[0]["z9"], observations[0]["z8"], observations[0]["z7"])
        pair_groups.setdefault(pair_id, set()).add(scenario.expected_optimal_action)
        signature = tuple(
            sorted(
                (
                    round(sum(float(obs[key]) for obs in observations), 3),
                    round(max(float(obs[key]) for obs in observations), 3),
                    round(min(float(obs[key]) for obs in observations), 3),
                )
                for key in ("x0", "x1", "x2")
            )
        )
        aggregate_signatures.setdefault(signature, set()).add(scenario.expected_optimal_action)

    assert any(len(actions) > 1 for actions in pair_groups.values())
    assert any(len(actions) > 1 for actions in aggregate_signatures.values())


def test_anti_oracle_temporal_summary_separates_adapter_and_raw_network() -> None:
    report = run_holdout_generalization_benchmark(seeds=(0,), steps_per_observation=1)
    anti_oracle = report.to_dict()["anti_oracle_temporal"]

    assert anti_oracle["scenario_count"] >= 48
    assert anti_oracle["train_scenario_count"] > 0
    assert anti_oracle["test_scenario_count"] > 0
    assert anti_oracle["baselines"]["sequence_majority"]["success_rate"] < 1.0
    assert set(anti_oracle["tissue_modes"]) >= {
        "semantic_bridge",
        "raw_network",
        "semantic_policy_only",
        "temporal_context_adapter",
    }
    assert anti_oracle["tissue_modes"]["temporal_context_adapter"]["success_rate"] > anti_oracle[
        "tissue_modes"
    ]["raw_network"]["success_rate"]
    assert "task-family train/test split" in anti_oracle["interpretation"]
    assert "sequence-majority" in anti_oracle["interpretation"]
