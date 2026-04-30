"""Benchmark result analysis, CSV exports, and PNG visualizations."""

from __future__ import annotations

import csv
import json
import math
import struct
import zlib
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, stdev
from typing import Iterable

from neuraxon_agent.baselines import run_baseline_benchmarks
from neuraxon_agent.benchmark import BenchmarkResult, BenchmarkScenario
from neuraxon_agent.scenarios import load_mock_agent_scenarios
from neuraxon_agent.tissue_benchmark import DEFAULT_TISSUE_BENCHMARK_PATH

DEFAULT_BENCHMARK_ANALYSIS_DIR = Path("benchmarks/results/analysis")
PLOT_NAMES = (
    "accuracy_by_agent",
    "confidence_distribution",
    "neuromodulator_trends",
    "learning_curve",
)


@dataclass(frozen=True)
class BenchmarkRun:
    """Normalized raw benchmark run for any benchmarked agent."""

    agent_name: str
    scenario_name: str
    scenario_type: str
    expected_optimal_action: str
    difficulty: float
    action: str
    confidence: float
    outcome: str
    elapsed_seconds: float
    seed: int | None = None
    neuromodulator_levels: dict[str, float] | None = None


@dataclass(frozen=True)
class AgentSummary:
    """Aggregate metrics for one benchmarked agent."""

    agent_name: str
    run_count: int
    success_count: int
    accuracy: float
    confidence_mean: float
    confidence_stddev: float
    elapsed_seconds_mean: float
    recovery_time_mean: float | None
    learning_curve_start_accuracy: float
    learning_curve_end_accuracy: float


@dataclass(frozen=True)
class ScenarioTypeSummary:
    """Aggregate metrics for one agent/scenario-type pair."""

    agent_name: str
    scenario_type: str
    run_count: int
    success_count: int
    accuracy: float
    confidence_mean: float


@dataclass(frozen=True)
class StatisticalComparison:
    """Approximate Welch-style comparison against a baseline agent."""

    metric: str
    treatment_agent: str
    baseline_agent: str
    treatment_mean: float
    baseline_mean: float
    mean_difference: float
    statistic: float
    p_value_approx: float
    significant_at_0_05: bool


@dataclass(frozen=True)
class BenchmarkAnalysisOutputPaths:
    """Files written by benchmark analysis."""

    summary_csv: Path
    scenario_type_csv: Path
    statistical_tests_csv: Path
    plots: dict[str, Path]


@dataclass(frozen=True)
class BenchmarkAnalysis:
    """Complete benchmark analysis result and written artifact paths."""

    runs: list[BenchmarkRun]
    agent_summaries: list[AgentSummary]
    scenario_type_summaries: list[ScenarioTypeSummary]
    statistical_comparisons: list[StatisticalComparison]
    output_paths: BenchmarkAnalysisOutputPaths


def analyze_benchmark_results(
    tissue_raw_path: str | Path = DEFAULT_TISSUE_BENCHMARK_PATH,
    *,
    output_dir: str | Path = DEFAULT_BENCHMARK_ANALYSIS_DIR,
    scenarios: list[BenchmarkScenario] | None = None,
) -> BenchmarkAnalysis:
    """Load benchmark data, run baselines, and export CSV + PNG analysis artifacts."""
    scenario_list = scenarios if scenarios is not None else load_mock_agent_scenarios()
    scenario_type_by_name = {scenario.name: scenario.scenario_type for scenario in scenario_list}
    raw_runs = _load_tissue_runs(Path(tissue_raw_path))
    baseline_runs = _run_baseline_runs(scenario_list, scenario_type_by_name)
    runs = raw_runs + baseline_runs

    agent_summaries = _summarize_agents(runs, scenario_list)
    scenario_type_summaries = _summarize_scenario_types(runs)
    statistical_comparisons = _compare_against_baselines(runs, "neuraxon_tissue")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    plots_dir = output_path / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    summary_csv = output_path / "benchmark_summary.csv"
    scenario_type_csv = output_path / "scenario_type_breakdown.csv"
    statistical_tests_csv = output_path / "statistical_tests.csv"
    _write_agent_summary_csv(summary_csv, agent_summaries)
    _write_scenario_type_csv(scenario_type_csv, scenario_type_summaries)
    _write_statistical_tests_csv(statistical_tests_csv, statistical_comparisons)

    plot_paths = {
        "accuracy_by_agent": plots_dir / "accuracy_by_agent.png",
        "confidence_distribution": plots_dir / "confidence_distribution.png",
        "neuromodulator_trends": plots_dir / "neuromodulator_trends.png",
        "learning_curve": plots_dir / "learning_curve.png",
    }
    _plot_accuracy_by_agent(plot_paths["accuracy_by_agent"], agent_summaries)
    _plot_confidence_distribution(plot_paths["confidence_distribution"], runs)
    _plot_neuromodulator_trends(plot_paths["neuromodulator_trends"], runs)
    _plot_learning_curve(plot_paths["learning_curve"], runs, scenario_list)

    return BenchmarkAnalysis(
        runs=runs,
        agent_summaries=agent_summaries,
        scenario_type_summaries=scenario_type_summaries,
        statistical_comparisons=statistical_comparisons,
        output_paths=BenchmarkAnalysisOutputPaths(
            summary_csv=summary_csv,
            scenario_type_csv=scenario_type_csv,
            statistical_tests_csv=statistical_tests_csv,
            plots=plot_paths,
        ),
    )


def _load_tissue_runs(path: Path) -> list[BenchmarkRun]:
    payload = json.loads(path.read_text())
    agent_name = str(payload["agent_name"])
    return [
        BenchmarkRun(
            agent_name=agent_name,
            seed=int(result["seed"]),
            scenario_name=str(result["scenario_name"]),
            scenario_type=str(result["scenario_type"]),
            expected_optimal_action=str(result["expected_optimal_action"]),
            difficulty=float(result["difficulty"]),
            action=str(result["action"]),
            confidence=float(result["confidence"]),
            outcome=str(result["outcome"]),
            elapsed_seconds=float(result["elapsed_seconds"]),
            neuromodulator_levels={
                key: float(value)
                for key, value in dict(result.get("neuromodulator_levels", {})).items()
            },
        )
        for result in payload["results"]
    ]


def _run_baseline_runs(
    scenarios: list[BenchmarkScenario],
    scenario_type_by_name: dict[str, str],
) -> list[BenchmarkRun]:
    reports = run_baseline_benchmarks(scenarios, random_seed=0)
    runs: list[BenchmarkRun] = []
    for agent_name, report in reports.items():
        for result in report.results:
            runs.append(_baseline_result_to_run(agent_name, result, scenario_type_by_name))
    return runs


def _baseline_result_to_run(
    agent_name: str,
    result: BenchmarkResult,
    scenario_type_by_name: dict[str, str],
) -> BenchmarkRun:
    return BenchmarkRun(
        agent_name=agent_name,
        scenario_name=result.scenario_name,
        scenario_type=scenario_type_by_name.get(result.scenario_name, "unknown"),
        expected_optimal_action=result.expected_optimal_action,
        difficulty=result.difficulty,
        action=result.action,
        confidence=result.confidence,
        outcome=result.outcome,
        elapsed_seconds=result.elapsed_seconds,
        seed=None,
        neuromodulator_levels=result.neuromodulator_levels,
    )


def _summarize_agents(
    runs: list[BenchmarkRun],
    scenarios: list[BenchmarkScenario],
) -> list[AgentSummary]:
    return [
        _summarize_one_agent(agent_name, agent_runs, scenarios)
        for agent_name, agent_runs in _group_by_agent(runs).items()
    ]


def _summarize_one_agent(
    agent_name: str,
    runs: list[BenchmarkRun],
    scenarios: list[BenchmarkScenario],
) -> AgentSummary:
    success_count = sum(_is_success(run) for run in runs)
    confidences = [run.confidence for run in runs]
    elapsed = [run.elapsed_seconds for run in runs]
    learning = _learning_curve_by_scenario_index(runs, scenarios)
    return AgentSummary(
        agent_name=agent_name,
        run_count=len(runs),
        success_count=success_count,
        accuracy=_safe_ratio(success_count, len(runs)),
        confidence_mean=_safe_mean(confidences),
        confidence_stddev=_safe_stddev(confidences),
        elapsed_seconds_mean=_safe_mean(elapsed),
        recovery_time_mean=_mean_recovery_time(runs, scenarios),
        learning_curve_start_accuracy=learning[0] if learning else 0.0,
        learning_curve_end_accuracy=learning[-1] if learning else 0.0,
    )


def _summarize_scenario_types(runs: list[BenchmarkRun]) -> list[ScenarioTypeSummary]:
    grouped: dict[tuple[str, str], list[BenchmarkRun]] = defaultdict(list)
    for run in runs:
        grouped[(run.agent_name, run.scenario_type)].append(run)
    return [
        ScenarioTypeSummary(
            agent_name=agent_name,
            scenario_type=scenario_type,
            run_count=len(group_runs),
            success_count=sum(_is_success(run) for run in group_runs),
            accuracy=_safe_ratio(sum(_is_success(run) for run in group_runs), len(group_runs)),
            confidence_mean=_safe_mean([run.confidence for run in group_runs]),
        )
        for (agent_name, scenario_type), group_runs in sorted(grouped.items())
    ]


def _compare_against_baselines(
    runs: list[BenchmarkRun],
    treatment_agent: str,
) -> list[StatisticalComparison]:
    grouped = _group_by_agent(runs)
    treatment = [_is_success(run) for run in grouped.get(treatment_agent, [])]
    comparisons: list[StatisticalComparison] = []
    for baseline_agent, baseline_runs in grouped.items():
        if baseline_agent == treatment_agent:
            continue
        baseline = [_is_success(run) for run in baseline_runs]
        statistic, p_value = _welch_binary_test(treatment, baseline)
        treatment_mean = _safe_mean(treatment)
        baseline_mean = _safe_mean(baseline)
        comparisons.append(
            StatisticalComparison(
                metric="accuracy",
                treatment_agent=treatment_agent,
                baseline_agent=baseline_agent,
                treatment_mean=treatment_mean,
                baseline_mean=baseline_mean,
                mean_difference=treatment_mean - baseline_mean,
                statistic=statistic,
                p_value_approx=p_value,
                significant_at_0_05=p_value < 0.05,
            )
        )
    return comparisons


def _write_agent_summary_csv(path: Path, summaries: list[AgentSummary]) -> None:
    fieldnames = [
        "agent_name",
        "run_count",
        "success_count",
        "accuracy",
        "confidence_mean",
        "confidence_stddev",
        "elapsed_seconds_mean",
        "recovery_time_mean",
        "learning_curve_start_accuracy",
        "learning_curve_end_accuracy",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(_format_dataclass_row(summary))


def _write_scenario_type_csv(path: Path, summaries: list[ScenarioTypeSummary]) -> None:
    fieldnames = [
        "agent_name",
        "scenario_type",
        "run_count",
        "success_count",
        "accuracy",
        "confidence_mean",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(_format_dataclass_row(summary))


def _write_statistical_tests_csv(path: Path, comparisons: list[StatisticalComparison]) -> None:
    fieldnames = [
        "metric",
        "treatment_agent",
        "baseline_agent",
        "treatment_mean",
        "baseline_mean",
        "mean_difference",
        "statistic",
        "p_value_approx",
        "significant_at_0_05",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for comparison in comparisons:
            writer.writerow(_format_dataclass_row(comparison))


def _format_dataclass_row(item: object) -> dict[str, str]:
    return {field: _format_csv_value(value) for field, value in item.__dict__.items()}


def _format_csv_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _group_by_agent(runs: Iterable[BenchmarkRun]) -> dict[str, list[BenchmarkRun]]:
    grouped: dict[str, list[BenchmarkRun]] = defaultdict(list)
    for run in runs:
        grouped[run.agent_name].append(run)
    return dict(grouped)


def _learning_curve_by_scenario_index(
    runs: list[BenchmarkRun],
    scenarios: list[BenchmarkScenario],
) -> list[float]:
    index_by_name = {scenario.name: index for index, scenario in enumerate(scenarios)}
    grouped: dict[int, list[int]] = defaultdict(list)
    for run in runs:
        if run.scenario_name in index_by_name:
            grouped[index_by_name[run.scenario_name]].append(_is_success(run))
    return [_safe_mean(grouped[index]) for index in sorted(grouped)]


def _mean_recovery_time(
    runs: list[BenchmarkRun],
    scenarios: list[BenchmarkScenario],
) -> float | None:
    index_by_name = {scenario.name: index for index, scenario in enumerate(scenarios)}
    grouped: dict[int | None, list[BenchmarkRun]] = defaultdict(list)
    for run in runs:
        grouped[run.seed].append(run)
    recovery_lengths: list[int] = []
    for group_runs in grouped.values():
        ordered = sorted(group_runs, key=lambda run: index_by_name.get(run.scenario_name, 10**9))
        failures_since_last_success = 0
        recovering = False
        for run in ordered:
            if _is_success(run):
                if recovering:
                    recovery_lengths.append(failures_since_last_success)
                failures_since_last_success = 0
                recovering = False
            else:
                failures_since_last_success += 1
                recovering = True
    if not recovery_lengths:
        return None
    return _safe_mean(recovery_lengths)


def _welch_binary_test(first: list[int], second: list[int]) -> tuple[float, float]:
    if not first or not second:
        return 0.0, 1.0
    mean_first = _safe_mean(first)
    mean_second = _safe_mean(second)
    var_first = _sample_variance(first)
    var_second = _sample_variance(second)
    standard_error = math.sqrt(var_first / len(first) + var_second / len(second))
    if standard_error == 0:
        return 0.0, 1.0 if mean_first == mean_second else 0.0
    statistic = (mean_first - mean_second) / standard_error
    p_value = math.erfc(abs(statistic) / math.sqrt(2.0))
    return statistic, max(0.0, min(1.0, p_value))


def _sample_variance(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _safe_mean(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _safe_mean(values: Iterable[float | int]) -> float:
    items = list(values)
    return float(fmean(items)) if items else 0.0


def _safe_stddev(values: Iterable[float]) -> float:
    items = list(values)
    return float(stdev(items)) if len(items) > 1 else 0.0


def _safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _is_success(run: BenchmarkRun) -> int:
    return 1 if run.outcome == "success" else 0


def _plot_accuracy_by_agent(path: Path, summaries: list[AgentSummary]) -> None:
    labels = [summary.agent_name for summary in summaries]
    values = [summary.accuracy for summary in summaries]
    _draw_bar_chart(path, labels, values, title="Accuracy per agent")


def _plot_confidence_distribution(path: Path, runs: list[BenchmarkRun]) -> None:
    bins = [0 for _ in range(10)]
    for run in runs:
        index = min(9, max(0, int(run.confidence * 10)))
        bins[index] += 1
    labels = [f"{index / 10:.1f}" for index in range(10)]
    _draw_bar_chart(path, labels, bins, title="Confidence distribution")


def _plot_neuromodulator_trends(path: Path, runs: list[BenchmarkRun]) -> None:
    tissue_runs = [run for run in runs if run.agent_name == "neuraxon_tissue"]
    series = []
    for modulator in ("dopamine", "serotonin", "acetylcholine", "norepinephrine"):
        values = [(run.neuromodulator_levels or {}).get(modulator, 0.0) for run in tissue_runs]
        series.append(values)
    _draw_line_chart(path, series, title="Neuromodulator trends")


def _plot_learning_curve(
    path: Path,
    runs: list[BenchmarkRun],
    scenarios: list[BenchmarkScenario],
) -> None:
    grouped = _group_by_agent(runs)
    series = [
        _learning_curve_by_scenario_index(agent_runs, scenarios) for agent_runs in grouped.values()
    ]
    _draw_line_chart(path, series, title="Learning curve")


def _draw_bar_chart(
    path: Path,
    labels: list[str],
    values: Sequence[float | int],
    *,
    title: str,
) -> None:
    width, height = 900, 520
    image = _new_image(width, height)
    _draw_axes(image, width, height)
    max_value = max([float(value) for value in values] + [1.0])
    plot_left, plot_top, plot_right, plot_bottom = 80, 60, width - 30, height - 80
    bar_slot = max(1, (plot_right - plot_left) // max(1, len(values)))
    for index, value in enumerate(values):
        x1 = plot_left + index * bar_slot + 8
        x2 = plot_left + (index + 1) * bar_slot - 8
        bar_height = int((float(value) / max_value) * (plot_bottom - plot_top))
        y1 = plot_bottom - bar_height
        _fill_rect(image, x1, y1, x2, plot_bottom, _palette(index))
        _draw_text_hint(image, x1, plot_bottom + 8, labels[index][:8])
    _draw_text_hint(image, 20, 20, title)
    _write_png(path, image)


def _draw_line_chart(path: Path, series: list[list[float]], *, title: str) -> None:
    width, height = 900, 520
    image = _new_image(width, height)
    _draw_axes(image, width, height)
    all_values = [value for line in series for value in line]
    max_value = max(all_values + [1.0])
    min_value = min(all_values + [0.0])
    if max_value == min_value:
        max_value += 1.0
    plot_left, plot_top, plot_right, plot_bottom = 80, 60, width - 30, height - 80
    for index, line in enumerate(series):
        if not line:
            continue
        points = []
        for point_index, value in enumerate(line):
            x = plot_left + int(point_index * (plot_right - plot_left) / max(1, len(line) - 1))
            normalized = (value - min_value) / (max_value - min_value)
            y = plot_bottom - int(normalized * (plot_bottom - plot_top))
            points.append((x, y))
        _draw_polyline(image, points, _palette(index))
    _draw_text_hint(image, 20, 20, title)
    _write_png(path, image)


def _new_image(width: int, height: int) -> list[list[tuple[int, int, int]]]:
    return [[(255, 255, 255) for _ in range(width)] for _ in range(height)]


def _draw_axes(image: list[list[tuple[int, int, int]]], width: int, height: int) -> None:
    plot_left, plot_top, _plot_right, plot_bottom = 80, 60, width - 30, height - 80
    _draw_line(image, plot_left, plot_top, plot_left, plot_bottom, (30, 30, 30))
    _draw_line(image, plot_left, plot_bottom, width - 30, plot_bottom, (30, 30, 30))


def _fill_rect(
    image: list[list[tuple[int, int, int]]],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int],
) -> None:
    height = len(image)
    width = len(image[0])
    for y in range(max(0, y1), min(height, y2)):
        row = image[y]
        for x in range(max(0, x1), min(width, x2)):
            row[x] = color


def _draw_polyline(
    image: list[list[tuple[int, int, int]]],
    points: list[tuple[int, int]],
    color: tuple[int, int, int],
) -> None:
    for first, second in zip(points, points[1:]):
        _draw_line(image, first[0], first[1], second[0], second[1], color)
    for x, y in points:
        _fill_rect(image, x - 2, y - 2, x + 3, y + 3, color)


def _draw_line(
    image: list[list[tuple[int, int, int]]],
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int],
) -> None:
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    error = dx + dy
    x, y = x1, y1
    while True:
        if 0 <= y < len(image) and 0 <= x < len(image[0]):
            image[y][x] = color
        if x == x2 and y == y2:
            break
        e2 = 2 * error
        if e2 >= dy:
            error += dy
            x += sx
        if e2 <= dx:
            error += dx
            y += sy


def _draw_text_hint(image: list[list[tuple[int, int, int]]], x: int, y: int, text: str) -> None:
    # Minimal label hint: encode each character as tiny deterministic tick marks.
    for char_index, char in enumerate(text):
        code = ord(char)
        base_x = x + char_index * 6
        for bit in range(5):
            if code & (1 << bit):
                _fill_rect(image, base_x, y + bit * 3, base_x + 4, y + bit * 3 + 2, (20, 20, 20))


def _palette(index: int) -> tuple[int, int, int]:
    colors = (
        (31, 119, 180),
        (255, 127, 14),
        (44, 160, 44),
        (214, 39, 40),
        (148, 103, 189),
        (140, 86, 75),
    )
    return colors[index % len(colors)]


def _write_png(path: Path, image: list[list[tuple[int, int, int]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height = len(image)
    width = len(image[0]) if height else 0
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in image)
    payload = bytearray()
    payload.extend(b"\x89PNG\r\n\x1a\n")
    payload.extend(_png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
    payload.extend(_png_chunk(b"IDAT", zlib.compress(raw, level=9)))
    payload.extend(_png_chunk(b"IEND", b""))
    path.write_bytes(bytes(payload))


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)
