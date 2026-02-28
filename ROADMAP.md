# Neuraxon evaluatie-roadmap


## Doel
Objectief bepalen of Neuraxon (v1/v2) voor ons nuttig is als **R&D-engine** of zelfs als productiebouwsteen.

## Succescriteria (go/no-go)
- **Technisch:** reproduceerbaar runbaar, basis-tests groen, geen kritieke stabiliteitsissues.
- **Performance:** op minstens 1 relevante use-case aantoonbare meerwaarde vs simpele baseline.
- **Operationeel:** beheersbare complexiteit, heldere onderhoudslast, duidelijke licentiegrenzen.

---

## Fase 0 — Intake & risicokaart (afgerond)
- [x] Repo-scan (structuur, code-opzet, activiteit)
- [x] Eerste risicoanalyse (claims vs bewijs, test/CI maturity, packaging)
- [x] Eerste haalbaarheidsadvies (R&D-ja, productie-niet-zonder-validatie)

## Fase 1 — Hardening & reproduceerbaarheid (dag 1)
- [x] Lokale sandbox opzetten + vaste run-instructies (v1 en v2)
- [x] Smoke test script voor v1/v2
- [x] Packaging/entrypoint issues documenteren en quick fixes voorstellen
- [x] Minimaal testplan opstellen (wat móet altijd groen zijn)

**Deliverable:** `HARDENING_REPORT.md`

## Fase 2 — Benchmark shootout (dag 1-2)
- [x] 2 concrete use-cases vastleggen
  - Use-case A: continue time-series adaptatie
  - Use-case B: dynamisch patroonherkenning met concept drift
- [x] Baselines kiezen (eenvoudig en eerlijk)
  - Baseline 1: klassiek model (bv. logistic/GBM)
  - Baseline 2: klein recurrent model (RNN/GRU)
- [x] Meetprotocol + metrics vastzetten
  - kwaliteit: accuracy/F1 (of taakrelevant)
  - adaptatie: tijd tot herstel na drift
  - kosten: CPU-tijd/geheugen
- [x] Eerste dry-run matrix tooling uitvoeren en samenvatten (`docs/DRY_RUN_001.md`, `benchmarks/results/summary/claim_summary.csv`)
- [x] Transparante rapportage op basis van huidige outputs (`BENCHMARK_RESULTS.md`)
- [x] Echte benchmarkmeting met task/claim-metrics per run (geen stub-status)
- [x] Expliciete claim-evaluatie tegen protocol-drempels (`docs/CLAIM_EVAL_002.md`)
  - dual-weight plasticity: FAIL
  - SOC: INCONCLUSIVE
  - UPOW: INCONCLUSIVE
- [ ] Volledige protocolmetricdekking zodat 3/3 claims volledig beslisbaar zijn (nu nog ontbrekende metrics)

**Deliverable (huidige stand):** `BENCHMARK_RESULTS.md` + `docs/CLAIM_EVAL_002.md`

## Fase 3 — Integratie-POC (dag 3)
- [x] Mini-wrapper maken (JSON in/out)
- [x] Eén simpele workflow koppeling voorzien (proof-of-use)
- [x] Failure modes + observability noteren

**Deliverable:** `POC_INTEGRATION_001.md`

## Fase 4 — Besluit (dag 3)
- [x] Scorecard invullen (impact, risico, effort)
- [x] Go / No-Go / Keep-for-R&D advies (`docs/GO_NO_GO.md`)
- [x] Volgende investering bepalen (tijd/budget/scope + stop-criteria in `docs/GO_NO_GO.md`)

**Deliverable:** `GO_NO_GO.md`

## Fase 5 — Frontier vervolg (dag 4-5, bounded)
- [x] Qubic ecosystem deep-dive + triage afgerond (`docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md`).
- [x] AGI-context toegevoegd als kalibratiekader voor bewijsdiscipline (`docs/AGI_CONTEXT_2026-02-27.md`).
- [x] Shadow sidecar concept vastgelegd (read-only pilot) in `docs/SHADOW_ORCHESTRATOR_SIDECAR_001.md` + `sidecar/README.md`.
- [x] Sidecar fase-1 observer implementeren (task ingest + scorecard + advisory output, zonder auto-acties) via `sidecar/observer.py` + runbook in `docs/SIDECAR_PHASE1_OBSERVER_001.md`.
- [x] UPOW probe-script gebouwd voor 1/2/4 worker-schaalmeting (`1,2,4`) via `scripts/run_upow_probe.py`.
- [x] Benchmarkschema uitbreiden met verplichte UPOW velden (`worker_count`, `node_id`, `throughput_steps_sec`, `cost_per_1m_steps`) + validatie in CI.
- [x] OTel pilot op benchmark + wrapper (`run_matrix.py`, `poc_wrapper.py`) met trace-id correlatie in output.
- [x] MLflow tracking pilot (minimale vertical slice): parent-run + 3 child-runs in lokale file-store, vaste tags (`protocol_version`, `claim_eval_version`, `git_commit`) en artifacts per run (`scripts/smoke_mlflow_slice.sh`, output onder `benchmarks/results/mlflow/smoke/`).
- [x] MLflow tracking uitgebreid naar volledige matrix-koppeling (parent per matrix-executie + child-run per `(use_case, variant, seed)` vanuit `scripts/run_matrix.py`, incl. artifacts + vaste tags).
- [x] Kleine reproduceerbare matrix-demonstratierun vastgelegd (`benchmarks/results/mlflow/pilot_2026-02-28/manifest_small.json`, output onder `benchmarks/results/mlflow/pilot_2026-02-28/`, verslag in `docs/MLFLOW_MATRIX_PILOT_001.md`).
- [x] Automatische claim-gate POC (machine-readable PASS/FAIL op protocol-drempels) via `scripts/claim_gate.py` + `scripts/check_claim_gate.sh`; huidige gate-resultaat: **FAIL** (`benchmarks/results/summary/claim_gate.json`).
- [ ] Claim-gate van FAIL naar PASS brengen door ontbrekende protocolmetrics en UPOW-schaalmetingen toe te voegen
- [x] Externe kalibratie-mini-run op 3 OpenML taken + driftrapport (River ADWIN) opgeleverd (`scripts/run_openml_subset.py`, `benchmarks/manifests/openml_subset_phase5.json`, `benchmarks/results/openml/pilot_2026-02-28/`, `docs/OPENML_DRIFT_MINIRUN_001.md`).

### Beslissingstabel — Sidecar fase-1
| Keuze | Opties | Beslissing | Waarom |
|---|---|---|---|
| Inputcontract | Strikt schema vs best-effort aliasing | **Best-effort aliasing** (`taskId`/`task_id`/`id`, `events`/`history`) | Past op bestaande runtime dumps zonder migratieblokkade. |
| Scoringmethode | ML-model vs regelgebaseerd | **Regelgebaseerd** | Transparant, reproduceerbaar en reviewbaar voor fase-1 pilot. |
| Output | Alleen latest vs latest + timestamped | **Latest standaard**, timestamped opt-in (`--write-timestamped`) | Houdt output clean, maar laat audit-trail toe wanneer nodig. |

**Deliverable:** `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md` + `docs/RESEARCH_FRONTIER_001.md` + eerste pilot-output onder `benchmarks/results/`

---

## Beslisregels
- **GO (productiepilot):** stabiele run + duidelijke winst + acceptabele onderhoudslast.
- **R&D only:** interessante signalen, maar te weinig robuustheid/bewijs.
- **NO-GO:** geen meetbare meerwaarde of te hoge operationele kost.

## Weekplan (2026-03-02 t/m 2026-03-08)

**Uitvoeringsmodus:** SA-first (subagents) voor alle open fase-5 taken, met bounded checkpoints.

1. **Maandag**
   - OTel pilot afronden (trace + correlatie in output)
   - Claim-gate POC starten (machine-readable PASS/FAIL)

2. **Dinsdag**
   - Claim-gate afronden + docs update
   - OpenML drift mini-run (3 taken) opstarten

3. **Woensdag**
   - OpenML drift mini-run afronden + compacte rapportage
   - Protocolmapping updaten in benchmark outputs

4. **Donderdag**
   - Cross-check claimstatus met nieuwe evidence
   - `BENCHMARK_RESULTS.md` + `docs/CLAIM_EVAL_002.md` refresh

5. **Vrijdag**
   - Weeksamenvatting + bijgestelde R&D aanbeveling
   - Backlog grooming voor volgende iteratie

### Week-exit criteria
- [x] OTel pilot aantoonbaar af (code + bewijsartefacts)
- [ ] Claim-gate POC geeft machine-readable PASS/FAIL
- [ ] OpenML drift mini-run (3 taken) gerapporteerd
- [ ] Claim-evaluatie en benchmarkrapport geüpdatet met nieuwe evidence
- [ ] Heldere weeksamenvatting + beslispunten voor Seppe

## Eigenaarschap
- Owner: Sisu
- Reviewer: Seppe
