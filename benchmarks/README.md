# Benchmarks

Hier komen:
- use-case definities
- baselineconfigs
- meetprotocol
- resultaten + reproducerende commands

## Huidige outputstructuur (fase 5)

- `benchmarks/manifests/`
  - matrix input manifests
- `benchmarks/results/raw/`
  - run-level CSV output per use-case (deterministische matrix-runs)
- `benchmarks/results/summary/`
  - geaggregeerde claim-samenvattingen
- `benchmarks/results/mlflow/`
  - `smoke/` = minimale vertical slice (parent + 3 child)
  - `matrix/` = volledige matrix tracking
    - `outputs/latest_matrix_run.json` (pointer naar laatste run)
    - `outputs/matrix_<UTCSTAMP>/parent_summary.json`
    - `outputs/matrix_<UTCSTAMP>/child_*.json`
    - `mlruns/` lokale MLflow file-store (niet nodig voor git-commit)
- `benchmarks/results/openml/`
  - mini-openml drift pilot output (`pilot_2026-02-28/`)

## OpenML drift mini-run (fase 5, bounded)

- Manifest: `benchmarks/manifests/openml_subset_phase5.json`
- Runner: `scripts/run_openml_subset.py`
- Output map (pilot): `benchmarks/results/openml/pilot_2026-02-28/`