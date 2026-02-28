# CLAIM_EVAL_002 — Fase-2 claim-evaluatie tegen protocol-drempels

**Datum:** 2026-02-26  
**Bronnen (evidence-only):**
- `BENCHMARK_RESULTS.md`
- `docs/TEST_PROTOCOL_PHASE1_2.md`
- `benchmarks/results/raw/usecase_a_drift.csv`
- `benchmarks/results/raw/usecase_b_perturbation.csv`
- `benchmarks/results/summary/claim_summary.csv`
- `benchmarks/results/summary/claim_gate.json` (machine-readable gate artifact, gegenereerd via `./scripts/check_claim_gate.sh`; huidige gate-status: **FAIL**)

## 1) Resultaat per claim

| Claim | Status | Kernreden |
|---|---|---|
| Dual-weight plasticity (`w_fast + w_slow`) | **FAIL** | Use-case A faalt protocoldrempel voor `T90` (en ook `F`), wat volgens protocol direct FAIL triggert. |
| Self-organized criticality (SOC) | **INCONCLUSIVE** | Vereiste metrics (`sigma`, collapse-rate, `R95`) ontbreken volledig in de huidige outputs. |
| Useful Proof of Work (UPOW) compute-schaal | **INCONCLUSIVE** | Geen 1->4 worker-schaalmeting, geen throughput-efficiency, geen inter-node reproducerbaarheid, geen kost/1M steps. |

## 2) Claim 1 — Dual-weight plasticity (`w_fast + w_slow`)

**Protocolreferentie:** `docs/TEST_PROTOCOL_PHASE1_2.md` sectie 2.  
**Protocolregels (PASS):**
- `T90_full <= 0.80 * min(T90_fastOnly, T90_slowOnly, T90_bestBaseline)`
- `F_full <= 0.85 * min(F_fastOnly, F_slowOnly, F_bestBaseline)`
- `SV_full <= 0.90 * min(SV_fastOnly, SV_slowOnly, SV_bestBaseline)`
- Geldig op beide use-cases.

### Gebruikte metrics en drempelcheck

**Use-case A (`usecase_a_drift`)**
- Beschikbaar: `drift_recovery_t90` (25/25), `forgetting_delta` (25/25)
- Ontbrekend: `stability_var` / `SV` (0/25)

`T90` (seedgemiddelden per variant):
- `T90_full = 36.00`
- `T90_wfast_only = 13.60`
- `T90_wslow_only = 54.80`
- `T90_bestBaseline = 17.80` (beste van baselines)
- Drempel: `0.80 * min(13.60, 54.80, 17.80) = 10.88`
- Uitkomst: `36.00 <= 10.88` is **FALSE** -> **FAIL-conditie geraakt**

`F` (seedgemiddelden per variant, volgens protocolformule):
- `F_full = 0.000345`
- `F_wfast_only = -0.000174`
- `F_wslow_only = -0.000560`
- `F_bestBaseline = -0.000053`
- Drempel: `0.85 * min(-0.000174, -0.000560, -0.000053) = -0.000476`
- Uitkomst: `0.000345 <= -0.000476` is **FALSE** -> **FAIL-conditie geraakt**

**Use-case B (`usecase_b_perturbation`)**
- `drift_recovery_t90`: 0/25 gevuld
- `forgetting_delta`: 0/25 gevuld
- `SV`: 0/25 gevuld
- Daardoor geen volledige 2-use-case dekking mogelijk.

### Besluit claim 1
**FAIL.**  
Rationale: protocol zegt FAIL zodra een vereiste voorwaarde op een use-case niet wordt gehaald; de `T90`-voorwaarde faalt al op Use-case A.

## 3) Claim 2 — Self-organized criticality (SOC)

**Protocolreferentie:** `docs/TEST_PROTOCOL_PHASE1_2.md` sectie 3.  
**Vereiste metrics/drempels:**
- mediane `sigma` in `[0.90, 1.10]`
- collapse-rate `<= 5%`
- `R95 <= 500` steps

**Beschikbaarheid in huidige data:**
- `sigma`/`sigma_branching`: niet aanwezig
- `collapse_flag` of equivalent: niet aanwezig
- `recovery95_steps`/`R95`: niet aanwezig

### Besluit claim 2
**INCONCLUSIVE.**  
Rationale: geen van de drie verplichte SOC-metrics is meetbaar in de huidige CSV-output.

## 4) Claim 3 — Useful Proof of Work (UPOW) compute-schaal

**Protocolreferentie:** `docs/TEST_PROTOCOL_PHASE1_2.md` sectie 4.  
**Vereiste metrics/drempels:**
- `eff >= 0.65` (1->4 workers)
- success-rate `>= 95%` (distributed jobs)
- inter-node score-afwijking `<= 10%`
- kost/1M steps `<= 1.25x` lokale baseline

**Beschikbaarheid in huidige data:**
- `claim_summary.csv` bevat alleen `total/ok/error`, geen worker-schaalinfo
- raw CSV bevat geen worker-count, geen throughput, geen node-id, geen kostenveld

### Besluit claim 3
**INCONCLUSIVE.**  
Rationale: protocol vereist distributed schaal- en kostmetingen die nu niet gelogd zijn.

## 5) Onzekerheden en ontbrekende data

- `forgetting_delta` bevat negatieve waarden; protocol definieert `F` als prestatieverlies, maar normalisatie/sign-conventie is niet expliciet vastgelegd.
- Voor dual-weight ontbreekt `SV` volledig en ontbreken alle dual-weight metrics op Use-case B.
- Voor SOC ontbreken `sigma_branching`, `collapse_flag`, `recovery95_steps`.
- Voor UPOW ontbreken distributed 1->4 worker-runs plus `throughput_steps_sec`, inter-node afwijking en `cost_per_1m_steps`.
- Huidige status (`50 ok / 0 error`) bewijst run-stabiliteit, niet claim-PASS voor SOC/UPOW.
