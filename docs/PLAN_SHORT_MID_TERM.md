# Plan — korte en middellange termijn (Neuraxon-hybrid)

## Korte termijn (0-72u)

### Doel
Fase 1 volledig dichtzetten en Fase 2 meetbaar starten.

### Acties
1. **Hardening afronden**
   - upstream clone + env setup
   - import smoke (v1/v2)
   - pytest/smoke logs
   - packaging/entrypoint issues expliciet loggen
2. **Run-matrix operationeel maken**
   - manifests A/B finaliseren
   - `scripts/run_matrix.py` + `scripts/summarize_claims.py` neerzetten
   - 1 dry-run per use-case
3. **Eerste volledige benchmarkbatch**
   - 5 seeds × alle varianten × 2 use-cases
   - raw + summary CSV genereren
4. **Claim-evaluatie v1**
   - PASS/FAIL invullen voor:
     - dual-weight plasticity
     - self-organized criticality
     - UPOW schaalclaim

### Verwachte output
- `logs/phase1_pytest.log`
- `benchmarks/results/raw/usecase_*.csv`
- `benchmarks/results/summary/claim_summary.csv`
- korte statusupdate met `[bezig]/[klaar]/[volgende]/[ETA]`

---

## Middellange termijn (3-14 dagen)

### Doel
Van losse testresultaten naar een beslisbaar Go/No-Go advies.

### Acties
1. **Fase 2 verdiepen**
   - gevoeligheidsanalyse op `meta`
   - extra ablations waar nodig
   - confidence intervals over seeds
2. **Fase 3 Integratie-POC**
   - JSON in/out wrapper
   - plugin-adapter koppeling naar een minimale workflow
   - observability hooks (status/events/failures)
3. **Fase 4 Besluitdocumenten**
   - scorecard (impact/risico/effort)
   - GO / R&D only / NO-GO onderbouwing
   - concreet investeringsvoorstel (wat wel/niet bouwen)

### Beslispunten
- **Als 3/3 claims PASS:** beperkte productie-POC met guardrails
- **Als 1-2 claims PASS:** R&D-only vervolg met gerichte iteraties
- **Als 0/3 claims PASS:** stop op productieroute, enkel onderzoeksnotitie afsluiten

---

## Risico’s die ik actief wil managen
- claim-inflatie zonder reproduceerbare evidence
- teveel protocol, te weinig effectieve runs
- baseline-keuze die vergelijking oneerlijk maakt

## Werkstijl
- klein, hard meetbaar, iteratief
- alles in artifacts (CSV/log/report), geen losse aannames
