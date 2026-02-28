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
  - Parse't protocol-drempels uit `docs/TEST_PROTOCOL_PHASE1_2.md`.
  - Neemt optioneel metadata uit `docs/CLAIM_EVAL_002.md`.
  - Schrijft machine-readable output naar `benchmarks/results/summary/claim_gate.json`.
- `./scripts/check_claim_gate.sh`
  - Lokale gate-check met strikte non-zero exit bij gate-FAIL.

Gebruik:

```bash
python3 scripts/claim_gate.py --out benchmarks/results/summary/claim_gate.json
./scripts/check_claim_gate.sh
```

## Beperkingen

- De gate kan alleen claims valideren op metrics die effectief in raw CSV aanwezig zijn.
- Ontbrekende protocolvelden (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`, `worker_count`, `throughput_steps_sec`, `node_id`, `cost_per_1m_steps`) leiden momenteel tot gate-FAIL.
- Dit is een lokale POC-checkflow; er is nog geen CI-koppeling.
