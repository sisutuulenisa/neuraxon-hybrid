# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-26
**Fase:** 2 (Bootstrap gestart)

## Bootstrap fase 2 — afgerond
- [x] API-compat document: `docs/API_COMPAT_V1_V2.md`
- [x] Minimale CI workflow: `.github/workflows/phase2_bootstrap_ci.yml`
- [x] Run-matrix generator: `scripts/run_matrix.py`
- [x] Claims samenvatting: `scripts/summarize_claims.py`
- [x] Smoke + fallback tests lokaal groen

## Open / volgende acties
1. Manifest invullen voor echte fase-2 runs (use_cases/variants/seeds) en `scripts/run_matrix.py` uitvoeren.
2. Eerste benchmark-resultaten verzamelen en samenvatten naar `BENCHMARK_RESULTS.md`.
3. v2-specifieke regressietests toevoegen (upstream tests dekken nu vooral v1).

## Blokkades
- Runner heeft pip/install beperkingen; workflow en lokale checks gebruiken daarom bewust geen externe pytest-install.

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
