# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-26
**Fase:** 2 (Dry Run 001 uitgevoerd)

## Bootstrap fase 2 — afgerond
- [x] API-compat document: `docs/API_COMPAT_V1_V2.md`
- [x] Minimale CI workflow: `.github/workflows/phase2_bootstrap_ci.yml`
- [x] Run-matrix generator: `scripts/run_matrix.py`
- [x] Claims samenvatting: `scripts/summarize_claims.py`
- [x] Smoke + fallback tests lokaal groen

## Dry Run 001 — outputs geproduceerd
- [x] Manifesten aangemaakt:
  - `benchmarks/manifests/usecase_a_drift.json`
  - `benchmarks/manifests/usecase_b_perturbation.json`
- [x] Raw run-matrix CSV's gegenereerd (elk 25 rijen):
  - `benchmarks/results/raw/usecase_a_drift.csv`
  - `benchmarks/results/raw/usecase_b_perturbation.csv`
- [x] Claims summary gegenereerd:
  - `benchmarks/results/summary/claim_summary.csv` (10 groepen, 50 rijen)
- [x] Deterministische timestamp-optie toegevoegd aan runner: `scripts/run_matrix.py --ts-utc ...`

## Open / volgende acties
1. Stub-executie vervangen door echte runner met metrics (`steps`, `runtime_sec`, `score_main`, etc.).
2. `BENCHMARK_RESULTS.md` opstellen met echte metricvergelijking per claim.
3. v2-specifieke regressietests toevoegen (upstream tests dekken nu vooral v1).

## Blokkades
- Runner heeft pip/install beperkingen; workflow en lokale checks gebruiken daarom bewust geen externe pytest-install.
- Huidige matrix-runner markeert runs nog als stub (`status=ok`), dus nog geen prestatiebewijs.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
