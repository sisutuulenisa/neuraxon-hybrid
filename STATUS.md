# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-26
**Fase:** 4 (besluit vastgelegd, fase-2 metrics uitgebreid)

- [klaar] Fase-4 besluitdocument opgeleverd: `docs/GO_NO_GO.md`
- [klaar] Beslissing: **R&D only** (geen productiepilot in huidige staat)
- [klaar] Next-step investering + stop-criteria vastgelegd in `docs/GO_NO_GO.md`

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
- [ ] Claim PASS/FAIL evaluatie tegen drempels uit `docs/TEST_PROTOCOL_PHASE1_2.md`
- [ ] UPOW-schaalmetingen (1->4 workers, throughput/success-rate/reproduceerbaarheid/kost)
- [ ] Volledige protocolmetricset in raw output (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`, throughput/kost)

## Huidige conclusie
- Pipeline-integriteit voor fase-2 matrix-output is aantoonbaar.
- De matrixflow bevat nu echte run-level metrics (geen stub-status-only output meer).
- Claim-validatie blijft **INCONCLUSIVE** totdat alle protocolmetrics en PASS/FAIL-evaluatie aanwezig zijn.
- Daarom is de formele beslissing nu: **R&D only**.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
