# ROADMAP.md — Neuraxon Hybrid (swarm-canoniek)

## Doel
Objectief beslissen of Neuraxon bruikbaar is als productie-bouwsteen of enkel als R&D-engine, op basis van reproduceerbaar bewijs.

Project root: `/home/sisu/.openclaw/workspace/local/projects/neuraxon-hybrid`

swarm_queue_paused: true

---

## Swarm contract (kort)
- Top-down prioriteit: eerste open `- [ ]` item is hoogste prioriteit.
- Research/spec/evaluatie: `subagent`.
- Gerichte code-implementatie: `acp`.
- Worktrees onder `<repo>/.worktrees/`.
- Runtime/queue state buiten repo (`local/runtime/agent-swarm/`).

---

## Priority queue (open werk)

### P0 — Claim evidence afronden
- [ ] [executor:acp][model:codex][reasoning:high] Implementeer instrumentatie-first ontbrekende protocolmetrics in `run_matrix.py` (incl. verplichte SOC/UPOW velden) zodat claim-gate volledig beslisbaar wordt.
- [ ] [executor:subagent][model:spark][reasoning:medium] Draai claim-gate opnieuw op geüpdatete outputs en publiceer machine-readable PASS/FAIL met korte oorzaak-analyse in `docs/CLAIM_GATE_STATUS.md`.

### P1 — Externe validatie en rapportage
- [ ] [executor:subagent][model:spark][reasoning:medium] Voltooi OpenML drift mini-run rapportage (3 taken) met compacte conclusies + beperkingen.
- [ ] [executor:subagent][model:spark][reasoning:medium] Refresh `BENCHMARK_RESULTS.md` en `docs/CLAIM_EVAL_002.md` met nieuwe evidence en expliciete go/no-go impact.

### P2 — Beslissing en vervolg
- [ ] [executor:subagent][model:spark][reasoning:medium] Schrijf weeksamenvatting met beslispunten, risico’s en aanbevolen volgende iteratie.
- [ ] [executor:subagent][model:spark][reasoning:low] Groom vervolgbacklog (bounded) op basis van claim-gate resultaat.

---

## Reeds afgerond (samengevat)
- Fase 0 t/m 4 afgerond (intake, hardening, benchmark-setup, POC-integratie, eerste go/no-go kader).
- Grote delen van fase 5 afgerond: Qubic deep-dive, sidecar observer, OTel pilot, MLflow pilot + matrix-koppeling, claim-gate POC, OpenML mini-run basis.
- Nog open: volledige protocolmetricdekking en finale claim-beslisbaarheid.

---

## Referenties
- `BENCHMARK_RESULTS.md`
- `docs/CLAIM_EVAL_002.md`
- `docs/GO_NO_GO.md`
- `docs/QUBIC_ECOSYSTEM_ANALYSIS_001.md`
- `docs/OPENML_DRIFT_MINIRUN_001.md`

Dit bestand is de operationele waarheid voor swarm queue-seeding in dit project.
