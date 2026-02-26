Project: neuraxon-hybrid — Self-seed fase 2 echte benchmarkmetingen

Doel:
Vervang stub-status in de matrixflow door echte, reproduceerbare metric-output per run.

Taken:
1) Update de runner (en waar nodig ondersteunende scripts) zodat elke run minstens deze velden schrijft:
- runtime_sec
- steps
- score_main
- drift_recovery_t90 (indien van toepassing)
- forgetting_delta (indien van toepassing)

2) Zorg dat output backward-compatible blijft:
- bestaande velden (`run_id`, `ts_utc`, `use_case`, `variant`, `seed`, `status`, `error_msg`) blijven bestaan.

3) Draai een eerste echte meting voor beide use-cases en werk CSV outputs bij.

4) Update BENCHMARK_RESULTS.md + STATUS.md:
- duidelijk welke metrics nu echt zijn
- welke nog ontbreken

5) Update ROADMAP.md checkboxes alleen op basis van aantoonbaar resultaat.

6) Commit + push branch.

Regels:
- Geen overclaims.
- Houd scripts simpel en reproduceerbaar.
- Geen merge naar main.
