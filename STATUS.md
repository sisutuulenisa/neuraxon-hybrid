# STATUS — Neuraxon evaluatie

**Laatste update:** 2026-02-26
**Fase:** 1 (Hardening)

## Nu bezig
- Upstream clone uitgevoerd (`upstream/Neuraxon`).
- v1/v2 script-level smoke runs zijn groen.
- Packaging mismatch lokaal gefixt (`README.md` toegevoegd naast `readme.md`).
- Test-workaround actief: `scripts/run_upstream_tests_no_pytest.py` met 7/7 geslaagde tests.

## Next acties
1. API-compatibiliteit check v1 vs v2 documenteren.
2. Minimaal CI-voorstel opstellen (smoke + test-runner workaround).
3. Daarna fase 2 run-matrix starten volgens `docs/RUN_SHEET_PHASE1_2.md`.

## Blokkades
- Pip-install commando’s zijn in deze runner momenteel allowlist-geblokkeerd.
- Hierdoor is directe `pytest`-install niet beschikbaar (workaround gebruikt).

## Korte statusformat voor updates
- `[bezig]`
- `[klaar]`
- `[volgende]`
- `[ETA]`
