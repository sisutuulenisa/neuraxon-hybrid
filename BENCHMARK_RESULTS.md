# BENCHMARK_RESULTS — Fase 2 (stand per 2026-02-26)

## 1) Scope en brondata

Dit rapport gebruikt uitsluitend:
- `benchmarks/results/raw/usecase_a_drift.csv`
- `benchmarks/results/raw/usecase_b_perturbation.csv`
- `benchmarks/results/summary/claim_summary.csv`
- `docs/TEST_PROTOCOL_PHASE1_2.md`

Runset:
- use-cases: `usecase_a_drift`, `usecase_b_perturbation`
- varianten: `neuraxon_full`, `neuraxon_wfast_only`, `neuraxon_wslow_only`, `baseline_classic`, `baseline_gru_small`
- seeds: `1..5` per use-case/variant
- timestamp in raw output: `2026-02-26T23:35:00Z`
- totaal: `50` runs (`50 ok`, `0 error`)

Uitgevoerde commands:
```bash
python3 scripts/run_matrix.py --manifest benchmarks/manifests/usecase_a_drift.json --out benchmarks/results/raw/usecase_a_drift.csv --ts-utc 2026-02-26T23:35:00Z
python3 scripts/run_matrix.py --manifest benchmarks/manifests/usecase_b_perturbation.json --out benchmarks/results/raw/usecase_b_perturbation.csv --ts-utc 2026-02-26T23:35:00Z
python3 scripts/summarize_claims.py --in benchmarks/results/raw/usecase_a_drift.csv --in benchmarks/results/raw/usecase_b_perturbation.csv --out benchmarks/results/summary/claim_summary.csv
```

## 2) Wat nu echt gemeten is

De runner schrijft nu per run:
- backward-compatible velden: `run_id`, `ts_utc`, `use_case`, `variant`, `seed`, `status`, `error_msg`
- nieuwe metricvelden: `runtime_sec`, `steps`, `score_main`, `drift_recovery_t90`, `forgetting_delta`

Belangrijk:
- Dit zijn **echte berekende metrics uit de run-harness** (niet meer hardcoded `status=ok` zonder meting).
- `drift_recovery_t90` en `forgetting_delta` worden alleen gevuld wanneer toepasselijk (`usecase_a_drift`), en blijven leeg voor `usecase_b_perturbation`.

## 3) Eerste echte meting (gemiddelden per groep)

| use_case | variant | runs_ok | runtime_sec (mean) | steps (mean) | score_main (mean) | drift_recovery_t90 (mean) | forgetting_delta (mean) |
|---|---|---:|---:|---:|---:|---:|---:|
| usecase_a_drift | baseline_classic | 5/5 | 63.4820 | 20000.0 | 0.986508 | 18.80 | 0.000508 |
| usecase_a_drift | baseline_gru_small | 5/5 | 95.0980 | 20000.0 | 0.991917 | 17.80 | -0.000053 |
| usecase_a_drift | neuraxon_full | 5/5 | 83.2420 | 20000.0 | 0.993076 | 36.00 | 0.000345 |
| usecase_a_drift | neuraxon_wfast_only | 5/5 | 75.3380 | 20000.0 | 0.991560 | 13.60 | -0.000174 |
| usecase_a_drift | neuraxon_wslow_only | 5/5 | 91.1460 | 20000.0 | 0.991819 | 54.80 | -0.000560 |
| usecase_b_perturbation | baseline_classic | 5/5 | 74.8638 | 20000.0 | 0.962426 | n.v.t. | n.v.t. |
| usecase_b_perturbation | baseline_gru_small | 5/5 | 112.1706 | 20000.0 | 0.982622 | n.v.t. | n.v.t. |
| usecase_b_perturbation | neuraxon_full | 5/5 | 98.1806 | 20000.0 | 0.981335 | n.v.t. | n.v.t. |
| usecase_b_perturbation | neuraxon_wfast_only | 5/5 | 88.8538 | 20000.0 | 0.985725 | n.v.t. | n.v.t. |
| usecase_b_perturbation | neuraxon_wslow_only | 5/5 | 107.5073 | 20000.0 | 0.963848 | n.v.t. | n.v.t. |

## 4) Nog ontbrekend voor protocol-claimbewijs

Nog niet in output:
- taakafhankelijke externe metrics zoals `accuracy/F1` op echte datasets
- stabiliteitsset uit protocol (`stability_var`, `sigma_branching`, `collapse_flag`, `recovery95_steps`)
- schaal/kost (`throughput_steps_sec`, `cost_per_1m_steps`, UPOW worker-schaal 1->4)

Wel beschikbaar:
- formele machine-readable PASS/FAIL gate-evaluatie via `scripts/claim_gate.py`
- artifact: `benchmarks/results/summary/claim_gate.json` (huidige status: **FAIL**)

## 5) Conclusie

Fase-2 matrixflow bevat nu aantoonbaar **run-level metric-output** (geen stub-status-only output meer).  
Machine-readable claim-gate evaluatie is toegevoegd, maar de gate blijft **FAIL** door ontbrekende SOC/UPOW-metrics en omdat dual-weight op huidige data de protocoldrempel niet haalt.
