# CLAIM_EVAL_001 — voorlopige claim-evaluatie (op basis van Dry Run 001)

**Datum:** 2026-02-26  
**Inputbronnen:**  
- `benchmarks/results/summary/claim_summary.csv`  
- `docs/TEST_PROTOCOL_PHASE1_2.md`  
- `docs/DRY_RUN_001.md`  
- `docs/CLAIM_MATRIX.md`

## Korte context
Deze evaluatie gebruikt uitsluitend Dry Run 001 outputs. Die run valideert dat de matrix-pipeline technisch werkt (manifests -> raw CSV -> summary CSV), maar de executie is nog stubbed: elke run wordt momenteel hardcoded als `status=ok` gezet zonder echte prestatiemetrics.

Gevolg: er is wel operationele evidence dat de testmatrix volledig en foutvrij doorloopt (2 use-cases x 5 varianten x 5 seeds, overal `ok=5`), maar er is nog geen claim-evidence op modelgedrag of compute-schaal conform de pass/fail-drempels in het testprotocol.

## Voorlopige claimstatus

| Claim | Voorlopige status | Evidentiesterkte | Wat ontbreekt voor beslisbaar PASS/FAIL |
|---|---|---|---|
| Dual-weight plasticity (`w_fast` + `w_slow`) | **INCONCLUSIVE** | Laag | Echte `T90`, `F` en `SV` per variant en use-case; vergelijking tegen `w_fast-only`, `w_slow-only` en beste baseline; drempelcheck uit protocol. |
| Self-organized criticality (SOC) | **INCONCLUSIVE** | Laag | Echte `sigma`, collapse-rate en `R95` op Use-case B; event-logging rond perturbaties; drempelcheck uit protocol. |
| Useful Proof of Work (UPOW) compute-schaal | **INCONCLUSIVE** | Zeer laag | Gedistribueerde runs op 1 en 4 workers; throughput-efficiency, success-rate, inter-node afwijking en kost/1M steps. |

## Claimdetail

### 1) Dual-weight plasticity
- **Status:** INCONCLUSIVE
- **Wat is wel aangetoond:** de ablation-matrix is operationeel opgezet met alle relevante varianten (`neuraxon_full`, `neuraxon_wfast_only`, `neuraxon_wslow_only`, plus baselines) en alle seeds zijn zonder technische fout verwerkt in de pipeline.
- **Waarom nog niet beslisbaar:** er zijn geen inhoudelijke adaptatie/forgetting/stabiliteitscores aanwezig in de ruwe of samengevatte outputs, dus de protocolcriteria kunnen niet worden berekend.

### 2) Self-organized criticality (SOC)
- **Status:** INCONCLUSIVE
- **Wat is wel aangetoond:** Use-case B (perturbatie) draait volledig door de pipeline heen voor alle varianten en seeds.
- **Waarom nog niet beslisbaar:** er zijn geen SOC-specifieke observaties (`sigma`, collapse, herstelsteps) gelogd; alleen run-statussen (`ok/error`) zijn beschikbaar.

### 3) Useful Proof of Work (UPOW) compute-schaal
- **Status:** INCONCLUSIVE
- **Wat is wel aangetoond:** er is nu een bruikbaar matrixframework waarop UPOW-metingen later kunnen aansluiten.
- **Waarom nog niet beslisbaar:** Dry Run 001 bevat geen distributed worker-profielen, geen throughputmetingen en geen kosten/reproduceerbaarheidsmeting over nodes.

## Advies voor volgende meetronde (claim-beslisbaar maken)
1. Vervang stub-executie in `scripts/run_matrix.py` door echte run-uitvoering met metriclogging (`steps`, `runtime_sec`, `score_main`, plus claim-specifieke velden zoals `t90_steps`, `forgetting_delta`, `sv_tail_var`, `sigma`, `collapse_flag`, `recovery_steps`).
2. Breid `scripts/summarize_claims.py` uit met aggregaties per claim en automatische protocol-drempelchecks (PASS/FAIL) op seedgemiddelden en spreiding.
3. Draai de bestaande 2 use-cases opnieuw met dezelfde matrix (5 seeds per configuratie) en gelijke compute-budgetten.
4. Voeg voor UPOW een aparte distributed matrix toe (1 vs 4 workers) met verplichte logging van throughput, success-rate, inter-node afwijking en kost.
5. Publiceer na die run `BENCHMARK_RESULTS.md` en een opvolger `CLAIM_EVAL_002.md` met definitieve claimuitspraken.

## Besluit
Op basis van Dry Run 001 zijn de drie fase-2 claims **niet falsifieerbaar noch bevestigd**. Het enige harde resultaat is pipeline-integriteit. Alle drie claims staan daarom voorlopig op **INCONCLUSIVE**.
