# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-28
**Fase:** 5 (SA-first uitvoering op open pilots + MLflow matrix pilot + claim-gate + OpenML drift mini-run opgeleverd)

- [klaar] Executorstrategie tijdelijk omgezet naar **SA-first** voor open fase-5 queue-items (OTel/MLflow/claim-gate/OpenML drift) om ACP-stallgedrag te vermijden.
- [klaar] `neuraxon-phase5-otel-pilot-2026-02-27` is afgerond met trace-id correlatie in `run_matrix.py` + `poc_wrapper.py`.
- [klaar] MLflow minimale vertical slice opgeleverd: parent + 3 child runs lokaal in file-store, vaste tags en artifacts per run (`scripts/smoke_mlflow_slice.sh`, `scripts/run_mlflow_smoke.py`)
- [klaar] Reproduceerbare smoke-output aanwezig onder `benchmarks/results/mlflow/smoke/` (incl. `outputs/latest_smoke_run.json` + run artifacts)
- [klaar] `scripts/run_matrix.py` ondersteunt optionele lokale MLflow-tracking voor volledige matrix-runs: parent-run per executie + child-run per `(use_case, variant, seed)` met metrics + artifacts + vaste tags (`protocol_version`, `claim_eval_version`, `git_commit`), inclusief CLI-compatibiliteit voor `--enable-mlflow` en `--mlflow-track`.
- [klaar] Matrix-demo met reproduceerbaar bewijs geverifieerd onder `benchmarks/results/mlflow/pilot_2026-02-28/` (manifest + matrix CSV + parent/child samenvatting), verslag: `docs/MLFLOW_MATRIX_PILOT_001.md`.
- [klaar] Qubic ecosystem deep-dive + triage opgeleverd: `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md`
- [klaar] Fase-4 besluitdocument opgeleverd: `docs/GO_NO_GO.md`
- [klaar] Beslissing: **R&D only** (geen productiepilot in huidige staat)
- [klaar] Next-step investering + stop-criteria vastgelegd in `docs/GO_NO_GO.md`
- [klaar] Claim-evaluatie tegen protocol-drempels geüpdatet: `docs/CLAIM_EVAL_002.md`
  - dual-weight plasticity: **FAIL**
  - SOC: **INCONCLUSIVE**
  - UPOW: **INCONCLUSIVE**
- [klaar] Publieke Neuraxon-signalen (Qubic all-hands/blog, LinkedIn, openPR, HF activity) toegevoegd als contextbron in `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md`; claimstatus blijft ongewijzigd.
- [klaar] AGI-contextsamenvatting toegevoegd in `docs/AGI_CONTEXT_2026-02-27.md` (state-of-the-art vs hype, governance/risico, implicaties voor claim-discipline).
- [klaar] Shadow sidecar ontwerp toegevoegd als veilige read-only pilot (`docs/SHADOW_ORCHESTRATOR_SIDECAR_001.md` + `sidecar/README.md`).
- [klaar] Sidecar fase-1 observer opgeleverd (`sidecar/observer.py`) met read-only task ingest + scorecard + advisory output (`sidecar/out/task-advice-latest.json`), inclusief runbook/evidence in `docs/SIDECAR_PHASE1_OBSERVER_001.md`.
- [klaar] Automatische claim-gate POC toegevoegd (`scripts/claim_gate.py`, `scripts/check_claim_gate.sh`) met machine-readable output op `benchmarks/results/summary/claim_gate.json`.
- [klaar] UPOW-schema uitgebreid: `run_matrix.py` geeft nu `worker_count`, `node_id`, `throughput_steps_sec`, `cost_per_1m_steps` uit en `scripts/validate_matrix_schema.py` checkt kolommen in CI (`.github/workflows/phase2_bootstrap_ci.yml`).
- [klaar] UPOW probe-script toegevoegd: `scripts/run_upow_probe.py` (1/2/4 worker-schaal via één CLI-run). Resultaat nog: geen extra claim-eindstatus, wel schaalbare raw output.
- [klaar] Huidige claim-gate resultaat: **FAIL** (phase1 PASS, claim1 FAIL, claim2 FAIL, claim3 FAIL).
- [klaar] Bounded OpenML kalibratieronde op 3 CC18-taken afgerond met driftsignalen via River ADWIN; reproducible runner + manifest + outputs + compacte protocolmapping toegevoegd (`scripts/run_openml_subset.py`, `benchmarks/manifests/openml_subset_phase5.json`, `benchmarks/results/openml/pilot_2026-02-28/`, `docs/OPENML_DRIFT_MINIRUN_001.md`).

## Aantoonbaar afgerond
- [x] Fase-2 testprotocol vastgelegd: `docs/TEST_PROTOCOL_PHASE1_2.md`
- [x] Dry-run rapport beschikbaar: `docs/DRY_RUN_001.md`
- [x] Raw benchmark-output aanwezig:
  - `benchmarks/results/raw/usecase_a_drift.csv` (25 runs)
  - `benchmarks/results/raw/usecase_b_perturbation.csv` (25 runs)
- [x] Samenvattingsoutput aanwezig: `benchmarks/results/summary/claim_summary.csv` (10 groepen, 50 runs)
- [x] Benchmarkresultaten transparant gerapporteerd: `BENCHMARK_RESULTS.md`
- [x] Machine-readable claim-gate artifact aanwezig: `benchmarks/results/summary/claim_gate.json`
- [x] Runner schrijft nu echte per-run metric-output in raw CSV:
  - `runtime_sec`
  - `steps`
  - `score_main`
  - `drift_recovery_t90` (waar van toepassing)
  - `forgetting_delta` (waarvan toepassing)
- [x] OTel pilot op benchmark + wrapper afgerond: `run_matrix.py` en `poc_wrapper.py` voegen nu `trace_id` toe aan respectievelijk matrix-output en wrapper-metadata; afhankelijk van `OTEL_EXPORTER_OTLP_ENDPOINT` activeert optionele export en fallback naar deterministische hashing wanneer SDK/spans niet actief zijn.

## Expliciet nog niet afgerond (voor volgende iteratie)
- [ ] Volledige protocoldekking voor alle claims (ontbrekende metrics toevoegen zodat 3/3 claims volledig beslisbaar zijn)
- [ ] Claim-gate van FAIL naar PASS brengen door ontbrekende protocolmetrics en UPOW-schaalmetingen toe te voegen
  - **Blokkerende input:** in-run simulatieproducering levert nog geen `stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`; UPOW-proof mist nog multi-node, distributed 1/4-sweep met herhaalbaarheid.
- [ ] UPOW probe-runner implementeren met 1->4 worker-schaalmeting (throughput/success-rate/reproduceerbaarheid/kost)
- [ ] Volledige protocolmetricset in raw output (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`)

## Huidige conclusie
- Pipeline-integriteit voor fase-2 matrix-output is aantoonbaar.
- Claimstatus op basis van `docs/CLAIM_EVAL_002.md`:
  - dual-weight plasticity = **FAIL** (T90-drempel niet gehaald op Use-case A)
  - SOC = **INCONCLUSIVE** (verplichte SOC-metrics ontbreken)
  - UPOW = **INCONCLUSIVE** (distributed schaal-/kostmetrics ontbreken)
- Machine-readable gate op basis van protocol-check (`benchmarks/results/summary/claim_gate.json`) staat op **FAIL**.
- Qubic-ecosysteemanalyse verhoogt operationele zekerheid voor UPOW-testimplementatie, maar levert nog geen nieuwe claim-PASS.
- Daarom blijft de formele beslissing: **R&D only**.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
