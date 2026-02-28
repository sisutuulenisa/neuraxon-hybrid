# OTel Pilot 001 — Trace-id correlatie in benchmark en wrapper

## Doel
Toevoegen en verifiëren van optionele OpenTelemetry-ondersteuning met trace-id terugkoppeling in
- matrix-run output CSV (`run_matrix.py`)
- wrapper output metadata (`poc_wrapper.py`)

## Scope
- Geen nieuwe claims of scoringwijzigingen.
- Geen extra dependency-installaties (traces exporteren blijft optioneel).

## Implementatie (voltooid)
- `scripts/run_matrix.py`
  - voegt optionele `OTEL_EXPORTER_OTLP_ENDPOINT`-activering toe via `_otel_configure()`
  - logt per matrixrij een `trace_id`
  - voegt `trace_id` toe aan CSV (veld in `BASE_FIELDS`)
  - voegt per child MLflow run `trace_id` toe als parameter
- `scripts/poc_wrapper.py`
  - voegt optionele OTEL-configuratie toe via `_otel_configure()`
  - omhult request verwerking met `poc_wrapper_run` span
  - voegt `trace_id` toe aan `metadata.trace_id`
  - bewaart OTEL-indicator in `metadata.telemetry.otlp_endpoint`

## Korte validatie
Uitvoeren op lokaal niveau (zonder OTLP runtime):

```bash
python3 scripts/run_matrix.py --manifest /tmp/otel_pilot_manifest.json --out /tmp/otel_matrix_output.csv
python3 scripts/poc_wrapper.py --input /tmp/poc_input.json --out /tmp/poc_output.json
```

Verenigbare velden:
- `run_matrix.csv`: `trace_id` kolom aanwezig in header.
- `poc_output.json`: `metadata.trace_id` aanwezig.

## Externe afhankelijkheden
Als `OTEL_EXPORTER_OTLP_ENDPOINT` gezet is, wordt automatisch geprobeert
op te zetten met een OTLP-exporter (`opentelemetry`-SDK + OTLP-exporter). Als deps ontbreken,
logt het script een waarschuwing en draait verder met lokale UUID-fallback.
