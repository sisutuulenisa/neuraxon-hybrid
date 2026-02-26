# Neuraxon-hybrid — Testprotocol v1 (Fase 1/2)

Doel: de 3 nieuw toegevoegde claims objectief testen met harde metrics en pass/fail-drempels:
1) dual-weight plasticity (`w_fast` + `w_slow`),
2) self-organized criticality,
3) Useful Proof of Work (UPOW) compute-schaal.

---

## 0) Scope en vaste settings

### Testcases (Fase 2)
- **Use-case A (drift):** non-stationaire sequence/control taak met 2 distributieshifts (D1→D2→D1).
- **Use-case B (perturbatie):** dynamische grid/agent-omgeving met stochastische verstoringen (noise spikes + topology changes).

### Baselines
- **Klassiek:** MLP of lineaire baseline (afhankelijk van taakinput).
- **Klein recurrent:** GRU/LSTM small.
- **Neuraxon varianten:**
  - full (`w_fast + w_slow`)
  - `w_fast`-only
  - `w_slow`-only

### Run-policy
- 5 seeds per configuratie.
- Zelfde compute-budget per run (gelijke wall-clock limiet + max steps).
- Alle runs loggen naar `benchmarks/results/<datum>/` met config-hash.

---

## 1) Fase 1 — Hardening gate (moet eerst groen)

### 1.1 Reproduceerbaarheid
- **Metric:** hash van config + dependency lockfile + seed.
- **Pass:** 10/10 smoke-runs starten en eindigen zonder crash op 1 machine.
- **Fail:** <10 succesvolle runs of niet-deterministische config-resolutie.

### 1.2 Basis-stabiliteit
- **Metric:** crash-rate, NaN-rate, timeouts.
- **Pass:**
  - crash-rate = 0%
  - NaN-rate = 0%
  - timeout-rate ≤ 5%
- **Fail:** één van bovenstaande niet gehaald.

### 1.3 Logging & auditability
- **Metric:** aanwezigheid van verplichte velden (`seed`, `model_variant`, `steps`, `score`, `runtime_sec`).
- **Pass:** 100% runs bevatten alle verplichte velden.
- **Fail:** ontbrekende velden in eender welke run.

---

## 2) Claim-test 1 — Dual-weight plasticity

**Claim:** combinatie `w_fast + w_slow` levert sneller aanpassen + minder forgetting dan ablations/baselines.

### Metingen
1. **Adaptatiesnelheid (T90):** steps tot 90% van pre-drift performance na shift.
2. **Forgetting (F):** prestatieverlies op oude distributie na re-adaptatie.
3. **Stabiliteit (SV):** variantie van score in laatste 20% van run.

### Pass/fail
- **PASS** als full-model op **beide use-cases** voldoet aan:
  - `T90_full <= 0.80 * min(T90_fastOnly, T90_slowOnly, T90_bestBaseline)`
  - `F_full <= 0.85 * min(F_fastOnly, F_slowOnly, F_bestBaseline)`
  - `SV_full <= 0.90 * min(SV_fastOnly, SV_slowOnly, SV_bestBaseline)`
- **FAIL** zodra één van bovenstaande voorwaarden op een use-case niet gehaald wordt.

---

## 3) Claim-test 2 — Self-organized criticality

**Claim:** systeem blijft in een bruikbaar kritische regime (niet chaotisch, niet dood), inclusief herstel na perturbatie.

### Metingen
1. **Branching ratio (`sigma`)** tijdens actieve fase.
2. **Collapse-rate:** % runs met divergerende of stille dynamiek.
3. **Recovery steps (R95):** steps tot 95% van pre-perturbatie score.

### Pass/fail
- **PASS** als op Use-case B:
  - mediane `sigma` in band **[0.90, 1.10]**
  - collapse-rate **<= 5%**
  - `R95 <= 500` steps na perturbatie-event
- **FAIL** zodra één drempel niet gehaald wordt.

---

## 4) Claim-test 3 — Useful Proof of Work compute-schaal

**Claim:** UPOW-pad levert schaalbare, reproduceerbare compute voor Neuraxon-simulaties.

### Metingen
1. **Throughput scaling efficiency** van 1→4 workers.
   - `eff = throughput_4 / (4 * throughput_1)`
2. **Job success-rate** op distributed runs.
3. **Reproduceerbaarheid tussen nodes:** relatieve afwijking op kernmetric (score).
4. **Kost-efficiëntie:** kost per 1M sim-steps.

### Pass/fail
- **PASS** als:
  - `eff >= 0.65`
  - success-rate `>= 95%`
  - inter-node score-afwijking `<= 10%`
  - kost per 1M steps `<= 1.25x` lokale baseline-kost
- **FAIL** zodra één drempel niet gehaald wordt.

---

## 5) Rapportageformat (Fase 2 output)

Per claim 1 blok:
- `[claim]`
- `[resultaat] PASS/FAIL`
- `[metrics]` (numerieke waarden + gemiddelde over 5 seeds)
- `[vergelijking]` t.o.v. beste baseline
- `[besluit]` keep / iterate / drop

---

## 6) Beslisimpact op projectstatus

- **3/3 claims PASS:** kandidaat voor “R&D+” en beperkte productie-POC.
- **1-2 claims PASS:** “R&D only”, focus op gerichte iteraties.
- **0/3 claims PASS:** voorlopig NO-GO voor verdere productierichting.
