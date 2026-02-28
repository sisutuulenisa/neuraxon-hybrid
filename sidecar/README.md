# sidecar/

Read-only shadow orchestrator pilot voor Neuraxon.

## Doel
Een extra POV geven op ACP/SA task-health zonder de execution-flow te beïnvloeden.

## Fase 1 regels
- read-only ingest
- scorecard + advies
- geen auto-acties

## Observer (fase 1)
Script: `sidecar/observer.py`

### Input
- `--active-tasks <pad>`: JSON lijst met taken of object met `tasks`
- `--events <pad>` (optioneel): JSON lijst met events of object met `events`

Ondersteunde taskvelden (best effort):
- id: `taskId` / `task_id` / `id`
- status: `status` / `state`
- tijdstempel: `updatedAt` / `updated_at` / `lastUpdate`
- retries: `retry_count` / `retries`
- evidence: `artifacts`, `artifact_count`, `has_test_output`, `reproducible`

### Output
- `sidecar/out/task-advice-latest.json`
- optioneel timestamped met `--write-timestamped`: `sidecar/out/task-advice-<timestamp>.json`

Output bevat per taak:
- scorecard (`progress`, `reliability`, `evidence`)
- advies (`continue`, `steer`, `fallback-to-sa`, `needs-human`)
- compacte redenen en snapshot-metadata

### Voorbeeldrun
```bash
python3 sidecar/observer.py \
  --active-tasks sidecar/examples/active_tasks_sample.json \
  --events sidecar/examples/history_events_sample.json \
  --write-timestamped
```

## Referentie
- `docs/SHADOW_ORCHESTRATOR_SIDECAR_001.md`
