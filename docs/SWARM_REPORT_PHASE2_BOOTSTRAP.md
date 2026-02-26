# SWARM Report — Phase 2 Bootstrap

Datum: 2026-02-26
Branch: `feat/neuraxon-phase2-bootstrap-2026-02-26`

## Doel van deze bootstrap
Fase 2 operationeel starten zonder scope creep: alleen minimale, werkende basisartefacts voor compatibiliteit, CI en runregistratie.

## Opgeleverde artefacts
1. `docs/API_COMPAT_V1_V2.md`
   - Vergelijking v1/v2 API-contract
   - Gedragsverschillen
   - Integratierisico's
   - Migratierichtlijn (wanneer v1/v2)

2. `.github/workflows/phase2_bootstrap_ci.yml`
   - Draait `scripts/smoke_v1_v2.py`
   - Draait `scripts/run_upstream_tests_no_pytest.py`
   - Werkt zonder pytest-install assumptie

3. `scripts/run_matrix.py`
   - CLI: `--manifest <json> --out <csv>`
   - Genereert geldige CSV voor alle combinaties van use_case x variant x seed
   - Velden: `run_id, ts_utc, use_case, variant, seed, status, error_msg`

4. `scripts/summarize_claims.py`
   - CLI: meerdere `--in <csv>` + `--out <summary.csv>`
   - Samenvatting per `use_case` + `variant`: `total, ok, error`

5. Statusdocumenten
   - `STATUS.md` bijgewerkt naar fase-2 bootstrapstand
   - `ROADMAP.md` checkboxes bijgewerkt voor feitelijk afgeronde items

## Validatie uitgevoerd
- `python3 scripts/smoke_v1_v2.py` -> groen
- `python3 scripts/run_upstream_tests_no_pytest.py` -> groen (7/7)
- `python3 scripts/run_matrix.py --manifest /tmp/phase2_manifest.json --out /tmp/phase2_runs.csv` -> geldige CSV
- `python3 scripts/summarize_claims.py --in /tmp/phase2_runs.csv --out /tmp/phase2_summary.csv` -> geldige samenvatting

## Open punten
1. Manifest en echte benchmark-runs voor fase 2 zijn nog niet uitgevoerd op projectdata.
2. Upstream tests dekken vooral v1; extra v2-regressietests zijn nog nodig.
3. CI gebruikt een runtime fetch van `upstream/Neuraxon` omdat die map niet in git staat.

## Bewust buiten scope gehouden
- Geen merge naar `main`
- Geen uitbreiding naar grote benchmark/POC-feature set
- Geen secrets of credentials toegevoegd
