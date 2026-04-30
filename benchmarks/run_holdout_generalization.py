#!/usr/bin/env python
"""Run the holdout/noisy generalization benchmark."""

from __future__ import annotations

from neuraxon_agent.holdout_generalization import (
    DEFAULT_HOLDOUT_GENERALIZATION_PATH,
    run_holdout_generalization_benchmark,
)

if __name__ == "__main__":
    report = run_holdout_generalization_benchmark(
        output_path=DEFAULT_HOLDOUT_GENERALIZATION_PATH,
    )
    print(report.to_json())
