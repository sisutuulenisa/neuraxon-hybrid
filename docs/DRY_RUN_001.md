# DRY_RUN_001 — fase-2 matrix tooling

**Datum:** 2026-02-26  
**Branch:** `feat/neuraxon-phase2-dryrun-2026-02-26`

## Doel
Valideren dat de fase-2 matrix pipeline end-to-end werkt:
1. manifest -> raw run CSV
2. meerdere raw CSV's -> claim summary CSV

## Uitgevoerde commands
```bash
python3 scripts/run_matrix.py \
  --manifest benchmarks/manifests/usecase_a_drift.json \
  --out benchmarks/results/raw/usecase_a_drift.csv \
  --ts-utc 2026-02-26T00:00:00Z

python3 scripts/run_matrix.py \
  --manifest benchmarks/manifests/usecase_b_perturbation.json \
  --out benchmarks/results/raw/usecase_b_perturbation.csv \
  --ts-utc 2026-02-26T00:00:00Z

python3 scripts/summarize_claims.py \
  --in benchmarks/results/raw/usecase_a_drift.csv \
  --in benchmarks/results/raw/usecase_b_perturbation.csv \
  --out benchmarks/results/summary/claim_summary.csv
```

## Korte interpretatie
- Pipeline werkt technisch: alle vereiste outputbestanden zijn aangemaakt zonder fouten.
- Dekking is aanwezig voor 2 use-cases x 5 varianten x 5 seeds = 50 run-rijen totaal.
- `claim_summary.csv` toont 10 groepen (per use-case + variant), elk met `total=5`, `ok=5`, `error=0`.

## Beperkingen / caveats
- Dit is een **stubbed dry-run**: `scripts/run_matrix.py` markeert elke rij momenteel hardcoded als `status=ok`.
- De raw CSV bevat nog geen echte benchmarkmetrics (zoals `score_main`, `runtime_sec`, `forgetting_delta`).
- De uitkomst bewijst dus pipeline-integriteit, niet modelkwaliteit of claim-validatie.
- Voor reproduceerbaarheid is een vaste timestamp gebruikt (`--ts-utc 2026-02-26T00:00:00Z`).

## Volgende stap
Koppel `run_matrix.py` aan echte uitvoering/metriccollectie zodat dezelfde matrix direct bruikbare claim-evidence produceert.
