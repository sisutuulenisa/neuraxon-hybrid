# BENCHMARK_RESULTS — Fase 2 (stand per 2026-02-26)

## 1) Scope en brondata

Dit rapport beschrijft alleen de benchmarkdata die aantoonbaar aanwezig is in:
- `benchmarks/results/raw/usecase_a_drift.csv`
- `benchmarks/results/raw/usecase_b_perturbation.csv`
- `benchmarks/results/summary/claim_summary.csv`
- `docs/DRY_RUN_001.md`
- `docs/TEST_PROTOCOL_PHASE1_2.md`

Use-cases en varianten komen uit de manifesten:
- Use-case A: `usecase_a_drift` (D1->D2->D1 drift)
- Use-case B: `usecase_b_perturbation` (dynamische perturbaties/noise spikes)
- Varianten: `neuraxon_full`, `neuraxon_wfast_only`, `neuraxon_wslow_only`, `baseline_classic`, `baseline_gru_small`
- Seeds: `1..5` per use-case/variant
- Run timestamp in beide raw CSV's: `2026-02-26T00:00:00Z`

Belangrijk: deze runs zijn gegenereerd via de huidige matrix-runner die per run `status=ok` schrijft (stub-executie), zonder modelprestatiemetrics.

## 2) Werkelijk beschikbare metrics

Beschikbare velden in raw output:
- `run_id`, `ts_utc`, `use_case`, `variant`, `seed`, `status`, `error_msg`

Beschikbare geaggregeerde metrics:
- `total` (aantal runs)
- `ok` (aantal status=ok)
- `error` (aantal niet-ok)
- afgeleid: `ok_rate = ok / total`
- seed-dekking (aanwezigheid van seeds 1..5)

Niet aanwezig in huidige output:
- `steps`, `runtime_sec`, `score_main`, `accuracy/F1`, `forgetting_delta`, `T90`, `SV`, `sigma`, `collapse_rate`, `R95`, UPOW-throughput/kost.

## 3) Resultaten per use-case/variant

| use_case | variant | total_runs | ok_runs | error_runs | ok_rate | seed_dekking | metingstype |
|---|---:|---:|---:|---:|---:|---|---|
| usecase_a_drift | baseline_classic | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_a_drift | baseline_gru_small | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_a_drift | neuraxon_full | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_a_drift | neuraxon_wfast_only | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_a_drift | neuraxon_wslow_only | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_b_perturbation | baseline_classic | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_b_perturbation | baseline_gru_small | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_b_perturbation | neuraxon_full | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_b_perturbation | neuraxon_wfast_only | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |
| usecase_b_perturbation | neuraxon_wslow_only | 5 | 5 | 0 | 1.00 | 1,2,3,4,5 | Echte pipeline-uitvoer (runregistratie), geen performance-meting |

## 4) Echte meting vs placeholder/stub

Wat is echt gemeten:
- De matrix-combinaties (use-case x variant x seed) zijn daadwerkelijk opgebouwd en weggeschreven.
- De runstatus-samenvatting (`ok/error`) is daadwerkelijk berekend uit de raw CSV's.

Wat placeholder/stub is:
- De run-uitkomst zelf is niet gebaseerd op echte modeluitvoering of metriccollectie; de runner zet nu alle runs op `status=ok`.
- Er is geen kwantitatief benchmarkbewijs voor de 3 claims uit `docs/TEST_PROTOCOL_PHASE1_2.md`.

## 5) Conclusie en ontbrekend bewijs

Fase 2 heeft op dit moment aantoonbaar **pipeline-evidence** (datapad werkt, matrix volledig, samenvatting reproduceerbaar), maar nog geen **claim-evidence** op modelkwaliteit/stabiliteit/schaal.

Voor definitief bewijs ontbreken minimaal:
1. Echte run-executie per matrixrij i.p.v. stub-status.
2. Opslag van task- en claimmetrics in raw output (`runtime_sec`, `score_main`, drift/forgetting, criticality, UPOW-schaal).
3. Aggregatie en PASS/FAIL-evaluatie tegen de drempels in `docs/TEST_PROTOCOL_PHASE1_2.md`.

Zonder deze drie punten blijven claimresultaten formeel: **INCONCLUSIVE**.
