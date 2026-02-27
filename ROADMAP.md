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
- [ ] UPOW probe-script bouwen voor 1/2/4 worker-schaalmeting (throughput, success-rate, node-variance, kost/1M steps).
- [ ] Benchmarkschema uitbreiden met verplichte UPOW velden (`worker_count`, `node_id`, `throughput_steps_sec`, `cost_per_1m_steps`) + validatie in CI.
- [ ] OTel pilot op benchmark + wrapper (`run_matrix.py`, `poc_wrapper.py`) met trace-id correlatie in output.
- [ ] MLflow tracking pilot (parent/child-runs, artifacts, vaste tags voor protocol/commit).
- [ ] Automatische claim-gate POC (machine-readable PASS/FAIL op protocol-drempels).
- [ ] Externe kalibratie-mini-run op 3 OpenML taken + driftrapport (Evidently/ADWIN).

**Deliverable:** `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md` + `docs/RESEARCH_FRONTIER_001.md` + eerste pilot-output onder `benchmarks/results/`

---

## Beslisregels
- **GO (productiepilot):** stabiele run + duidelijke winst + acceptabele onderhoudslast.
- **R&D only:** interessante signalen, maar te weinig robuustheid/bewijs.
- **NO-GO:** geen meetbare meerwaarde of te hoge operationele kost.

## Eigenaarschap
- Owner: Sisu
- Reviewer: Seppe
