# DASHBOARD_DATA_FLOW

## Doel
Uitleg van hoe de dashboarddata voor phase-2 dry-run wordt opgebouwd en ververst.

## Databronnen
- `benchmarks/results/raw/*.csv`
  - Gegenereerd door `scripts/run_matrix.py` vanuit fase-2 manifesten.
- `benchmarks/results/summary/claim_summary.csv`
  - Gegenereerd door `scripts/summarize_claims.py` op basis van meerdere raw CSV's.
- `dashboard/data/claim_summary.json`
  - Gegenereerd door `scripts/export_summary_json.py` als frontend-vriendelijke mirror.
- Overige dashboardbronnen:
  - `STATUS.md`
  - `ROADMAP.md`
  - `logs/smoke_summary.json`
  - `logs/upstream_tests_no_pytest.json`

## Refresh-stappen
1. Run matrix opnieuw voor de gewenste manifesten.
```bash
python3 scripts/run_matrix.py --manifest benchmarks/manifests/usecase_a_drift.json --out benchmarks/results/raw/usecase_a_drift.csv
python3 scripts/run_matrix.py --manifest benchmarks/manifests/usecase_b_perturbation.json --out benchmarks/results/raw/usecase_b_perturbation.csv
```
2. Bouw de geaggregeerde claims CSV.
```bash
python3 scripts/summarize_claims.py \
  --in benchmarks/results/raw/usecase_a_drift.csv \
  --in benchmarks/results/raw/usecase_b_perturbation.csv \
  --out benchmarks/results/summary/claim_summary.csv
```
3. Exporteer CSV naar dashboard JSON.
```bash
python3 scripts/export_summary_json.py
```
4. Start of refresh de dashboardserver.
```bash
python3 scripts/serve_dashboard.py --host 0.0.0.0 --port 8787
```
Open daarna `http://<host>:8787/dashboard/`.

## Caveats
- `dashboard/index.html` leest alleen de JSON mirror voor claim summary, niet direct de CSV.
- De huidige dry-run is stubbed: `status=ok` in de matrix is nog geen prestatiebewijs.
- `generated_at_utc` in de JSON is export-tijd, niet de oorspronkelijke runtijd van individuele benchmark-rijen.
- Als `claim_summary.csv` ontbreekt of verouderd is, toont het dashboard dus ook verouderde of ontbrekende claim-data.
