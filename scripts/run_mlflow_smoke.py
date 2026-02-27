#!/usr/bin/env python3
"""Minimal local MLflow parent/child smoke slice for Phase 5.

This intentionally keeps scope tiny:
- one parent run
- a fixed set of child runs
- local file-store tracking only
- lightweight artifacts and summary outputs
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, List

try:
    import mlflow
except ImportError as exc:  # pragma: no cover - clear operator guidance
    raise SystemExit(
        "mlflow module not found. Install dependency first (recommended: mlflow-skinny) "
        "or use scripts/smoke_mlflow_slice.sh"
    ) from exc


FIXED_CHILDREN: List[Dict[str, Any]] = [
    {"child_key": "slice_a", "use_case": "usecase_a_drift", "variant": "neuraxon_full", "seed": "11"},
    {"child_key": "slice_b", "use_case": "usecase_a_drift", "variant": "baseline_classic", "seed": "17"},
    {"child_key": "slice_c", "use_case": "usecase_b_perturbation", "variant": "neuraxon_wfast_only", "seed": "29"},
]


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit = proc.stdout.strip()
        return commit or "unknown"
    except Exception:
        return "unknown"


def _child_metrics(index: int) -> Dict[str, float]:
    # Deterministic pseudo-metrics to prove tracking plumbing.
    return {
        "runtime_sec": round(0.42 + index * 0.14, 4),
        "steps": float(1200 + index * 400),
        "score_main": round(0.67 + index * 0.08, 6),
        "drift_recovery_t90": float(180 + index * 25),
    }


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny local MLflow parent/child smoke slice")
    parser.add_argument(
        "--tracking-dir",
        default="benchmarks/results/mlflow/smoke/mlruns",
        help="Directory used as MLflow file-store root",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmarks/results/mlflow/smoke/outputs",
        help="Directory for reproducible smoke output summaries",
    )
    parser.add_argument(
        "--experiment-name",
        default="phase5_mlflow_smoke",
        help="MLflow experiment name",
    )
    parser.add_argument("--protocol-version", default="phase5.frontier.v1")
    parser.add_argument("--claim-eval-version", default="CLAIM_EVAL_002")
    parser.add_argument(
        "--git-commit",
        default=None,
        help="Optional override for git_commit tag (default: auto-detect)",
    )
    parser.add_argument(
        "--matrix-csv",
        default=None,
        help="Optional integration hook: attach existing matrix CSV to parent run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    tracking_dir = Path(args.tracking_dir).resolve()
    output_root = Path(args.output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_output_dir = output_root / f"smoke_{stamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)

    git_commit = args.git_commit or _git_commit(repo_root)

    common_tags = {
        "protocol_version": args.protocol_version,
        "claim_eval_version": args.claim_eval_version,
        "git_commit": git_commit,
    }

    mlflow.set_tracking_uri(tracking_dir.as_uri())
    mlflow.set_experiment(args.experiment_name)

    child_results: List[Dict[str, Any]] = []

    with mlflow.start_run(run_name=f"phase5_mlflow_smoke_parent_{stamp}") as parent_run:
        mlflow.set_tags({**common_tags, "run_role": "parent", "slice": "minimal_vertical_smoke"})
        mlflow.log_param("child_count", len(FIXED_CHILDREN))
        mlflow.log_param("tracking_dir", str(tracking_dir))
        mlflow.log_param("output_dir", str(run_output_dir))

        matrix_csv_attached = None
        if args.matrix_csv:
            matrix_csv_path = Path(args.matrix_csv).resolve()
            if matrix_csv_path.exists():
                mlflow.log_artifact(str(matrix_csv_path), artifact_path="matrix_hook")
                matrix_csv_attached = str(matrix_csv_path)
            else:
                matrix_csv_attached = f"missing:{matrix_csv_path}"

        for index, child_cfg in enumerate(FIXED_CHILDREN, start=1):
            metrics = _child_metrics(index)
            child_source_summary = {
                "ts_utc": _now_utc_iso(),
                "index": index,
                "child": child_cfg,
                "metrics": metrics,
                "note": "minimal deterministic smoke child",
            }
            child_source_path = run_output_dir / f"child_{index}_summary.json"
            _write_json(child_source_path, child_source_summary)

            with mlflow.start_run(run_name=f"child_{index}_{child_cfg['child_key']}", nested=True) as child_run:
                mlflow.set_tags(
                    {
                        **common_tags,
                        "run_role": "child",
                        "child_key": child_cfg["child_key"],
                        "use_case": child_cfg["use_case"],
                        "variant": child_cfg["variant"],
                    }
                )
                mlflow.log_params(
                    {
                        "seed": child_cfg["seed"],
                        "child_index": index,
                    }
                )
                mlflow.log_metrics(metrics)
                mlflow.log_artifact(str(child_source_path), artifact_path="smoke")

                child_results.append(
                    {
                        "index": index,
                        "run_id": child_run.info.run_id,
                        "artifact_uri": child_run.info.artifact_uri,
                        "child_key": child_cfg["child_key"],
                        "metrics": metrics,
                        "source_artifact": str(child_source_path),
                    }
                )

        avg_score = fmean(result["metrics"]["score_main"] for result in child_results)
        avg_runtime = fmean(result["metrics"]["runtime_sec"] for result in child_results)
        mlflow.log_metric("avg_child_score_main", avg_score)
        mlflow.log_metric("avg_child_runtime_sec", avg_runtime)

        parent_summary = {
            "ts_utc": _now_utc_iso(),
            "experiment_name": args.experiment_name,
            "tracking_dir": str(tracking_dir),
            "run_output_dir": str(run_output_dir),
            "parent_run_id": parent_run.info.run_id,
            "parent_artifact_uri": parent_run.info.artifact_uri,
            "tags": common_tags,
            "children": child_results,
            "aggregate": {
                "avg_child_score_main": round(avg_score, 6),
                "avg_child_runtime_sec": round(avg_runtime, 6),
            },
            "matrix_hook_csv": matrix_csv_attached,
        }

        parent_summary_path = run_output_dir / "parent_summary.json"
        parent_summary_txt = run_output_dir / "parent_summary.txt"
        _write_json(parent_summary_path, parent_summary)
        parent_summary_txt.write_text(
            "\n".join(
                [
                    "Phase 5 MLflow smoke summary",
                    f"parent_run_id={parent_run.info.run_id}",
                    f"tracking_dir={tracking_dir}",
                    f"run_output_dir={run_output_dir}",
                    f"avg_child_score_main={avg_score:.6f}",
                    f"avg_child_runtime_sec={avg_runtime:.6f}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        mlflow.log_artifact(str(parent_summary_path), artifact_path="smoke")
        mlflow.log_artifact(str(parent_summary_txt), artifact_path="smoke")

    latest_path = output_root / "latest_smoke_run.json"
    latest_payload = {
        "ts_utc": _now_utc_iso(),
        "tracking_dir": str(tracking_dir),
        "output_dir": str(run_output_dir),
        "parent_summary": str(parent_summary_path),
    }
    _write_json(latest_path, latest_payload)

    print("MLflow smoke slice complete")
    print(f"tracking_dir={tracking_dir}")
    print(f"output_dir={run_output_dir}")
    print(f"latest={latest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
