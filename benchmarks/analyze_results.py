"""Generate benchmark CSV summaries and PNG plots.

Run from the repository root:

    uv run python benchmarks/analyze_results.py
"""

from __future__ import annotations

from neuraxon_agent.benchmark_analysis import analyze_benchmark_results

if __name__ == "__main__":
    analysis = analyze_benchmark_results()
    print(f"summary_csv={analysis.output_paths.summary_csv}")
    print(f"scenario_type_csv={analysis.output_paths.scenario_type_csv}")
    print(f"statistical_tests_csv={analysis.output_paths.statistical_tests_csv}")
    for name, path in analysis.output_paths.plots.items():
        print(f"plot_{name}={path}")
