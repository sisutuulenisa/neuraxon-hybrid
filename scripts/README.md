# Scripts

Lokale helper scripts voor reproduceerbaarheid:
- setup
- smoke-tests
- benchmark-runs
- MLflow smoke slice: `./scripts/smoke_mlflow_slice.sh`
- OpenML drift mini-run (bounded):
  - manifest: `benchmarks/manifests/openml_subset_phase5.json`
  - run: `./scripts/run_openml_subset.py --manifest benchmarks/manifests/openml_subset_phase5.json --out-dir benchmarks/results/openml/pilot_2026-02-28`
