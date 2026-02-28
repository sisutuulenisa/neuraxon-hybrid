# Scripts

Lokale helper scripts voor reproduceerbaarheid:
- setup
- smoke-tests
- benchmark-runs
- MLflow smoke slice: `./scripts/smoke_mlflow_slice.sh`
- MLflow matrix tracking (opt-in): `run_matrix.py --enable-mlflow ...`
- MLflow matrix tracking wrapper: `./scripts/run_matrix_mlflow.sh --manifest ... --out ...`

## Claim-gate POC

- `./scripts/claim_gate.py`
  - Leest alle raw benchmark-CSV's onder `benchmarks/results/raw/`.
  - Steunt nu ook `worker_count`, `node_id`, `throughput_steps_sec` en `cost_per_1m_steps` in de inputschema.
  - Parse't protocol-drempels uit `docs/TEST_PROTOCOL_PHASE1_2.md`.
  - Neemt optioneel metadata uit `docs/CLAIM_EVAL_002.md`.
  - Schrijft machine-readable output naar `benchmarks/results/summary/claim_gate.json`.
- `./scripts/check_claim_gate.sh`
  - Lokale gate-check met strikte non-zero exit bij gate-FAIL.
- `./scripts/run_upow_probe.py`
  - UPOW-probe met vaste worker-schaal (`--worker-counts 1,2,4`, default).
  - Schrijft zowel een gecombineerde probe-CSV als een samenvattings-CSV met `success_rate` + `node_variance`.

Gebruik:

```bash
python3 scripts/claim_gate.py --out benchmarks/results/summary/claim_gate.json
./scripts/check_claim_gate.sh
```

Voor UPOW-schaalmeting:

```bash
python3 scripts/run_upow_probe.py \
  --manifest benchmarks/manifests/usecase_a_drift.json \
  --out benchmarks/results/upow/run_upow_probe.csv
```

## Beperkingen

- De gate kan alleen claims valideren op metrics die effectief in raw CSV aanwezig zijn.
- Ontbrekende protocolvelden (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`) leiden momenteel tot gate-FAIL.
- UPOW-schaalvelden (`worker_count`, `throughput_steps_sec`, `node_id`, `cost_per_1m_steps`) zijn nu in de matrix output opgenomen via `run_matrix.py`.
- Dit is een lokale POC-checkflow; CI-koppeling is toegevoegd via `scripts/validate_matrix_schema.py`.

- Quick check:
  - `python3 scripts/validate_matrix_schema.py`

## OpenML drift mini-run (bounded)

- manifest: `benchmarks/manifests/openml_subset_phase5.json`
- runner: `./scripts/run_openml_subset.py --manifest benchmarks/manifests/openml_subset_phase5.json --out-dir benchmarks/results/openml/pilot_2026-02-28`
