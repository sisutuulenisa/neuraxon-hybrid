# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-26
**Fase:** 4 (finale beslissing vastgelegd)

- [klaar] Fase-4 besluitdocument opgeleverd: `docs/GO_NO_GO.md`
- [klaar] Beslissing: **R&D only** (geen productiepilot in huidige staat)
- [klaar] Next-step investering en stop-criteria vastgelegd voor volgende iteratie

- [klaar] Fase-3 POC wrapper JSON in/out toegevoegd (`scripts/poc_wrapper.py`, `data/poc_input_example.json`, `docs/POC_INTEGRATION_001.md`).

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
- [x] Dashboard-zichtbaarheid toegevoegd voor dry-run outputs:
  - `scripts/export_summary_json.py` (`claim_summary.csv` -> `dashboard/data/claim_summary.json`)
  - `dashboard/index.html` toont claim summary (groepen/runs/tabel)
- [x] Deterministische timestamp-optie toegevoegd aan runner: `scripts/run_matrix.py --ts-utc ...`

## Compacte besluitstatus
1. Claim-evidence blijft **3x INCONCLUSIVE** (`docs/CLAIM_EVAL_001.md`), dus geen GO-pilot.
2. `BENCHMARK_RESULTS.md` ontbreekt nog; huidige summary bevat alleen technische runstatus (`ok/error`), geen prestatiemetrics.
3. Volgende iteratie is expliciet afgebakend op echte metrics, UPOW 1->4 worker-metingen, regressietests en rapportage.

## Open / volgende acties (volgende iteratie)
1. Stub-executie vervangen door echte runner met metrics (`steps`, `runtime_sec`, `score_main`, etc.).
2. `BENCHMARK_RESULTS.md` opleveren met echte metricvergelijking per claim.
3. UPOW-meetpad uitvoeren (1->4 workers) met throughput/success-rate/reproduceerbaarheid/kost.
4. v2-specifieke regressietests toevoegen (upstream tests dekken nu vooral v1).

## Blokkades
- Runner heeft pip/install beperkingen; workflow en lokale checks gebruiken daarom bewust geen externe pytest-install.
- Huidige matrix-runner markeert runs nog als stub (`status=ok`), dus nog geen prestatiebewijs.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
