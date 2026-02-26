# GO_NO_GO - Fase 4 finale beslissing

**Datum:** 2026-02-26  
**Status:** definitief fase-4 besluit  
**Besluit:** **R&D only**

## Besluit in 1 alinea
Neuraxon gaat **niet** door naar productiepilot in de huidige staat. Het project blijft wel actief als **gerichte R&D-investering** voor een korte, meetbare iteratie met harde stop-criteria. Reden: de huidige evidence toont pipeline- en wrapper-werkbaarheid, maar nog geen inhoudelijke prestatie-, schaal- of robuustheidswinst.

## Traceerbare onderbouwing (evidence -> conclusie)
1. **Bewijssterkte te laag voor GO**
   - `docs/GO_NO_GO_SCORECARD_001.md`: impact 3/5, risico 4/5, effort 4/5, bewijssterkte 1/5.
   - `docs/CLAIM_EVAL_001.md`: alle drie kernclaims staan op **INCONCLUSIVE**.
   - `benchmarks/results/summary/claim_summary.csv`: alleen `ok/error`-tellingen (50 runs technisch OK), geen inhoudelijke metrics.
2. **Productiegeschiktheid nog niet aangetoond**
   - `docs/POC_INTEGRATION_001.md`: integratie is expliciet een placeholder-wrapper; echte adapter-call ontbreekt.
   - `BENCHMARK_RESULTS.md` ontbreekt nog, waardoor geen definitieve benchmarkvergelijking beschikbaar is.
3. **NO-GO nu nog te vroeg**
   - Infrastructuur is bruikbaar en reproduceerbaar op dry-run niveau (matrix + claim-samenvatting + POC contract), dus een korte, afgebakende bewijsronde is rationeel.

## Randvoorwaarden voor de volgende iteratie
1. Scope blijft **R&D-only**: geen productiegebruik, geen externe SLA-commitments.
2. Alle vergelijkingen draaien op **gelijke compute-budgetten** en vaste seeds.
3. Resultaten moeten reproduceerbaar zijn via gedocumenteerde commands en artefacten.
4. Elke claim krijgt expliciete PASS/FAIL-checks op protocol-drempels, geen narratieve interpretatie.

## Concrete next-step investering (tijd/budget/scope)
- **Tijd:** 10 werkdagen (2 weken), start direct na dit besluit.
- **Budget:** EUR 12.000 tot EUR 18.000 (engineering + review + compute).
- **Scope (verplicht):**
  1. Stub-executie vervangen door echte metriclogging in `scripts/run_matrix.py`.
  2. `scripts/summarize_claims.py` uitbreiden met claim-aggregaties + automatische drempelchecks.
  3. Volledige rerun van bestaande matrix (2 use-cases x 5 varianten x 5 seeds).
  4. UPOW meetpad uitvoeren op 1 vs 4 workers (throughput, success-rate, reproduceerbaarheid, kost).
  5. v2-specifieke regressietests toevoegen aan minimale CI.
  6. Rapportage opleveren: `BENCHMARK_RESULTS.md` + `docs/CLAIM_EVAL_002.md`.

## Stop-criteria voor volgende iteratie
Stop de investering en escalatie naar extra fase alleen als minimaal een van onderstaande situaties optreedt:

1. **Execution stop (dag 3):** echte metrics zijn nog steeds niet beschikbaar in raw outputs.
2. **Evidence stop (einde iteratie):** geen enkele use-case toont aantoonbare meerwaarde t.o.v. beste baseline onder gelijk budget.
3. **Schaal stop:** 4-worker run haalt <95% success-rate of duidelijk onvoldoende efficiëntie t.o.v. 1 worker.
4. **Reproduceerbaarheid stop:** resultaten zijn niet stabiel over seeds/reruns of niet herhaalbaar via gedocumenteerde workflow.
5. **Kwaliteitsstop:** regressietests (incl. v2-pad) blijven structureel rood.

## Exit naar mogelijk GO-pilot na iteratie
Alleen heroverwegen richting GO wanneer:
1. `BENCHMARK_RESULTS.md` complete, niet-stub metricvergelijkingen bevat.
2. Minstens 1 relevante use-case overtuigend beter presteert dan baseline onder gelijke constraints.
3. UPOW-schaalpad operationeel en reproduceerbaar is aangetoond.
4. CI-regressies groen en operationele risico's beheersbaar zijn.
