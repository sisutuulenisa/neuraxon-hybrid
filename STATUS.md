# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-27
**Fase:** 5 (Qubic ecosystem-analyse + MLflow minimale smoke-slice opgeleverd)

- [klaar] MLflow minimale vertical slice opgeleverd: parent + 3 child runs lokaal in file-store, vaste tags en artifacts per run (`scripts/smoke_mlflow_slice.sh`, `scripts/run_mlflow_smoke.py`)
- [klaar] Reproduceerbare smoke-output aanwezig onder `benchmarks/results/mlflow/smoke/` (incl. `outputs/latest_smoke_run.json` + run artifacts)
- [klaar] Qubic ecosystem deep-dive + triage opgeleverd: `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md`
- [klaar] Fase-4 besluitdocument opgeleverd: `docs/GO_NO_GO.md`
- [klaar] Beslissing: **R&D only** (geen productiepilot in huidige staat)
- [klaar] Next-step investering + stop-criteria vastgelegd in `docs/GO_NO_GO.md`
- [klaar] Claim-evaluatie tegen protocol-drempels geüpdatet: `docs/CLAIM_EVAL_002.md`
  - dual-weight plasticity: **FAIL**
  - SOC: **INCONCLUSIVE**
  - UPOW: **INCONCLUSIVE**

## Aantoonbaar afgerond
- [x] Fase-2 testprotocol vastgelegd: `docs/TEST_PROTOCOL_PHASE1_2.md`
- [x] Dry-run rapport beschikbaar: `docs/DRY_RUN_001.md`
- [x] Raw benchmark-output aanwezig:
  - `benchmarks/results/raw/usecase_a_drift.csv` (25 runs)
  - `benchmarks/results/raw/usecase_b_perturbation.csv` (25 runs)
- [x] Samenvattingsoutput aanwezig: `benchmarks/results/summary/claim_summary.csv` (10 groepen, 50 runs)
- [x] Benchmarkresultaten transparant gerapporteerd: `BENCHMARK_RESULTS.md`
- [x] Runner schrijft nu echte per-run metric-output in raw CSV:
  - `runtime_sec`
  - `steps`
  - `score_main`
  - `drift_recovery_t90` (waar van toepassing)
  - `forgetting_delta` (waar van toepassing)

## Expliciet nog niet afgerond (voor volgende iteratie)
- [ ] Volledige protocoldekking voor alle claims (ontbrekende metrics toevoegen zodat 3/3 claims volledig beslisbaar zijn)
- [ ] MLflow-koppeling opschalen van smoke naar volledige matrix (`scripts/run_matrix.py` => child-run per `(use_case, variant, seed)`)
- [ ] UPOW probe-runner implementeren met 1->4 worker-schaalmeting (throughput/success-rate/reproduceerbaarheid/kost)
- [ ] Raw output uitbreiden met UPOW velden (`worker_count`, `node_id`, `throughput_steps_sec`, `cost_per_1m_steps`)
- [ ] Volledige protocolmetricset in raw output (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`, throughput/kost)

## Huidige conclusie
- Pipeline-integriteit voor fase-2 matrix-output is aantoonbaar.
- Claimstatus op basis van `docs/CLAIM_EVAL_002.md`:
  - dual-weight plasticity = **FAIL** (T90-drempel niet gehaald op Use-case A)
  - SOC = **INCONCLUSIVE** (verplichte SOC-metrics ontbreken)
  - UPOW = **INCONCLUSIVE** (distributed schaal-/kostmetrics ontbreken)
- Qubic-ecosysteemanalyse verhoogt operationele zekerheid voor UPOW-testimplementatie, maar levert nog geen nieuwe claim-PASS.
- Daarom blijft de formele beslissing: **R&D only**.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
