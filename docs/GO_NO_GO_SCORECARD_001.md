# GO_NO_GO_SCORECARD_001 - Fase 4 besluitscorecard

**Datum:** 2026-02-26  
**Status:** concept voor besluitvorming  
**Besluitscope:** geschiktheid voor productiepilot vs. R&D-only

## Gebruikte bronnen
- `benchmarks/results/summary/claim_summary.csv` (meest recente benchmarksamenvatting; `BENCHMARK_RESULTS.md` ontbreekt nog)
- `docs/CLAIM_EVAL_001.md`
- `docs/POC_INTEGRATION_001.md`
- `STATUS.md`

## Scoremodel
Schaal 1-5:
- `impact`: 1 = lage verwachte waarde, 5 = hoge verwachte waarde
- `risico`: 1 = laag risico, 5 = hoog risico
- `effort`: 1 = lage extra inspanning, 5 = hoge extra inspanning
- `bewijssterkte`: 1 = zeer zwak bewijs, 5 = sterk reproduceerbaar bewijs

## Scorecard
| Dimensie | Score | Korte motivatie |
|---|---:|---|
| Impact | 3/5 | Er is potentiële productwaarde (adaptatie/perturbatie-use-cases zijn afgebakend), maar geen meetbaar voordeel t.o.v. baselines aangetoond. |
| Risico | 4/5 | Hoog beslisrisico: claimstatus is 3x INCONCLUSIVE en huidige runner is stubbed (`status=ok` zonder inhoudelijke metrics). |
| Effort | 4/5 | Extra werk is substantieel voor pilotniveau: echte metriclogging, protocol-drempelchecks, UPOW 1->4 worker meetpad en v2-regressietests ontbreken. |
| Bewijssterkte | 1/5 | Beschikbaar bewijs toont alleen pipeline-integriteit (50/50 runs technisch ok), niet modelprestatie, schaalgedrag of operationele robuustheid. |

## Onzekerheden en blockers
1. Geen definitief benchmarkrapport met echte metrics (`BENCHMARK_RESULTS.md` nog niet opgeleverd).
2. Dry-run data is niet inhoudelijk valide voor claims door stub-executie.
3. UPOW-claims niet toetsbaar: geen distributed metingen (throughput/success-rate/reproduceerbaarheid/kost).
4. Integratie-POC gebruikt placeholder-verwerking; geen bewijs van echte adapterkwaliteit of runtime-gedrag.
5. Beperkingen rond install/pip en ontbrekende v2-specifieke regressietests verhogen operationeel risico.

## Voorgesteld beslissingstype
**R&D only**

Onderbouwing:
- `GO pilot` is nu niet verdedigbaar wegens onvoldoende bewijssterkte en hoog beslisrisico.
- `NO-GO` is prematuur omdat de infrastructuur bruikbaar is en vervolgevaluatie technisch haalbaar is.
- `R&D only` past bij de huidige staat: eerst claims falsifieerbaar maken met echte benchmark- en schaaldata, daarna herbeoordelen.

## Exit-criteria voor herbesluit (naar GO pilot)
1. `BENCHMARK_RESULTS.md` met niet-stub metrics en reproduceerbare commands.
2. Minstens 1 relevante use-case met aantoonbare meerwaarde vs. baseline onder gelijk budget.
3. UPOW-metingen 1 vs 4 workers met expliciete efficiëntie/success-rate/reproduceerbaarheid/kost.
4. Basis regressietests (incl. v2-specifieke paden) groen in CI.
