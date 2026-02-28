# MLFLOW_MATRIX_PILOT_001 - volledige matrix parent/child tracking

**Datum:** 2026-02-28  
**Doel:** aantonen dat `scripts/run_matrix.py` lokaal een MLflow parent-run + child-runs per `(use_case, variant, seed)` logt met vaste tags en artifacts.

## Wat is geïmplementeerd

`run_matrix.py` ondersteunt optionele lokale MLflow-tracking via:

- `--enable-mlflow` (primair)
- `--mlflow-track` (compat-alias)
- `--mlflow-tracking-dir`
- `--mlflow-output-dir`
- `--mlflow-experiment-name`
- `--mlflow-run-name`
- `--protocol-version`
- `--claim-eval-version`
- `--git-commit`

Gedrag bij MLflow aan:
- 1 parent-run per matrix-executie
- nested child-run per matrix-rij `(use_case, variant, seed)`
- key metrics per child (`runtime_sec`, `steps`, `score_main`, `drift_recovery_t90`, `forgetting_delta` waar beschikbaar)
- artifacts:
  - parent: input manifest, output CSV, `parent_summary.json`, `parent_summary.txt`
  - child: per-rij JSON artifact
- vaste tags op parent + child:
  - `protocol_version`
  - `claim_eval_version`
  - `git_commit`

## Reproduceerbare demonstratierun

Command:

```bash
./scripts/run_matrix_mlflow.sh \
  --manifest benchmarks/results/mlflow/pilot_2026-02-28/manifest_small.json \
  --out benchmarks/results/mlflow/pilot_2026-02-28/matrix_runs.csv \
  --ts-utc 2026-02-28T00:00:00Z \
  --mlflow-tracking-dir benchmarks/results/mlflow/pilot_2026-02-28/mlruns \
  --mlflow-output-dir benchmarks/results/mlflow/pilot_2026-02-28/outputs \
  --mlflow-experiment-name phase5_matrix_tracking_pilot \
  --mlflow-run-name phase5_matrix_pilot_small \
  --protocol-version phase5.frontier.v1 \
  --claim-eval-version CLAIM_EVAL_002
```

Resultaat:
- rows: `8 ok / 0 error`
- parent run id: `bf2dbafbd4b94c85b1d1fb2a443e7642`
- child runs: 8 stuks (zie `parent_summary.json`)

Bewijs-output:
- `benchmarks/results/mlflow/pilot_2026-02-28/manifest_small.json`
- `benchmarks/results/mlflow/pilot_2026-02-28/matrix_runs.csv`
- `benchmarks/results/mlflow/pilot_2026-02-28/outputs/latest_matrix_run.json`
- `benchmarks/results/mlflow/pilot_2026-02-28/outputs/matrix_20260227T233125Z/parent_summary.json`
- `benchmarks/results/mlflow/pilot_2026-02-28/outputs/matrix_20260227T233125Z/child_*.json`

## Setup-notitie

- Geen externe infra nodig; tracking gebruikt lokale file-store (`mlruns` map).
- `scripts/run_matrix_mlflow.sh` houdt setup lichtgewicht met project-local `.venv-mlflow-smoke` + `mlflow-skinny==2.20.1`.
- `mlruns/` staat bewust in `.gitignore`; reproduceerbare bewijslijn in git zit in manifest + CSV + outputs-samenvattingen.
