# sidecar/

Read-only shadow orchestrator pilot voor Neuraxon.

## Doel
Een extra POV geven op ACP/SA task-health zonder de execution-flow te beïnvloeden.

## Fase 1 regels
- read-only ingest
- scorecard + advies
- geen auto-acties

## Verwachte outputs
- `sidecar/out/task-advice-<timestamp>.json`
- `sidecar/out/task-advice-latest.json`

## Referentie
- `docs/SHADOW_ORCHESTRATOR_SIDECAR_001.md`
