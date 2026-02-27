# MLFLOW_SMOKE_001 - minimale parent/child tracking slice

**Datum:** 2026-02-27
**Doel:** kleine, verifieerbare MLflow end-to-end slice die lokaal draait (zonder externe infra).

## 1-command smoke runner

```bash
./scripts/smoke_mlflow_slice.sh --matrix-csv benchmarks/results/raw/usecase_a_drift.csv
```

Wat dit doet:
- Maakt/lanceert lokale tracking file-store onder `benchmarks/results/mlflow/smoke/mlruns/`
- Start **1 parent run** + **3 child runs** (vaste kleine set)
- Zet vaste tags op parent + children:
  - `protocol_version`
  - `claim_eval_version`
  - `git_commit`
- Logt basismetrics en per run minimaal 1 artifact
- Optionele matrix-integratiehaak: `--matrix-csv ...` wordt als parent artifact opgeslagen onder `matrix_hook/`

## Outputlocaties

- Tracking store (MLflow files):
  - `benchmarks/results/mlflow/smoke/mlruns/`
- Reproduceerbare output-samenvatting:
  - `benchmarks/results/mlflow/smoke/outputs/latest_smoke_run.json`
- Per run smoke-output map (timestamped):
  - `benchmarks/results/mlflow/smoke/outputs/smoke_<UTCSTAMP>/`

## Voorbeeldresultaat (deze run)

- Parent run id: `1c5fc00f2c3f453481624f64152c7c38`
- Child run ids:
  - `c45c28b1ebe346b9a448053f15093261`
  - `bbee55a0ab45432c8bab74ec3e82e97d`
  - `6342b5bb64a04a0eab6d2a8063574a40`
- Gemiddelde child metrics:
  - `avg_child_score_main = 0.83`
  - `avg_child_runtime_sec = 0.70`
- Parent artifact voorbeelden:
  - `artifacts/smoke/parent_summary.json`
  - `artifacts/smoke/parent_summary.txt`
  - `artifacts/matrix_hook/usecase_a_drift.csv` (wanneer `--matrix-csv` is gezet)

## Notitie

Deze slice is bewust klein en checkpoint-vriendelijk. Volgende stap (optioneel) is opschalen naar een child-run per matrix-combinatie vanuit `scripts/run_matrix.py`.
