# SIDECAR_PHASE1_OBSERVER_001

**Datum:** 2026-02-28  
**Status:** opgeleverd (read-only)

## Scope
Afgerond roadmap-item:
- Fase 5: **"Sidecar fase-1 observer implementeren (task ingest + scorecard + advisory output, zonder auto-acties)."**

Niet gedaan (bewust buiten scope):
- geen auto-kill/restart/merge
- geen writes naar code/worktrees buiten sidecar output artifacts

## Implementatie
Toegevoegd:
- `sidecar/observer.py`
- `sidecar/examples/active_tasks_sample.json`
- `sidecar/examples/history_events_sample.json`
- update `sidecar/README.md`

Observer levert:
1. **Task ingest**
   - leest active task state (lijst of object met `tasks`)
   - leest optionele history events (lijst of object met `events`)
2. **Scorecard**
   - progress score (0-100)
   - reliability score (0-100)
   - evidence score (0-100)
3. **Advisory output**
   - `continue` / `steer` / `fallback-to-sa` / `needs-human`
   - confidence + reasonregels per taak

## Runbook
```bash
python3 sidecar/observer.py \
  --active-tasks sidecar/examples/active_tasks_sample.json \
  --events sidecar/examples/history_events_sample.json \
  --write-timestamped
```

## Bewijs
- output pad: `sidecar/out/task-advice-latest.json`
- timestamped output: `sidecar/out/task-advice-<timestamp>.json`

## Trade-off
- Scoringregels zijn bewust rule-based en transparant (geen model dependency), zodat resultaten reproduceerbaar en reviewbaar blijven.
- Nadeel: beperkte nuance bij incomplete/rommelige event-data; dit wordt expliciet als `steer` of `needs-human` gerapporteerd i.p.v. auto-acties.
