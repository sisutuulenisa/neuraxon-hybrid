# POC_INTEGRATION_001 - JSON wrapper integratie (fase 3)

**Datum:** 2026-02-26  
**Scope:** Mini-POC om Neuraxon als component aan te roepen via JSON in/out.

## Doel
Een simpele, deterministische wrapperflow valideren:
1. lees input JSON payload
2. voer placeholder-processing uit
3. schrijf output JSON met vaste structuur voor orchestration

## Wrapper CLI
```bash
python3 scripts/poc_wrapper.py \
  --input data/poc_input_example.json \
  --out data/poc_output_example.json
```

## JSON contract

### Input (vereist)
```json
{
  "use_case": "classification_baseline",
  "variant": "v1",
  "seed": 42,
  "params": {
    "max_steps": 5,
    "temperature": 0.0
  }
}
```

Regels:
- root moet een object zijn
- `use_case`: non-empty string
- `variant`: non-empty string
- `seed`: int of string (default = `0` indien afwezig)
- `params`: object (default = `{}` indien afwezig of `null`)

### Output (succes)
```json
{
  "status": "ok",
  "metadata": {
    "deterministic": true,
    "request_fingerprint": "e8c0edf510b56f72",
    "schema_version": "neuraxon.poc-wrapper.v1",
    "wrapper_version": "0.1.0"
  },
  "result": {
    "mode": "placeholder",
    "params_echo": {
      "max_steps": 5,
      "note": "phase3-poc",
      "temperature": 0.0
    },
    "placeholder_score": 941,
    "seed": "42",
    "use_case": "classification_baseline",
    "variant": "v1"
  }
}
```

Notities:
- output is deterministisch voor dezelfde genormaliseerde input
- `placeholder_score` is afgeleid van een SHA-256 fingerprint van de input

## Foutpaden
Wrapper retourneert exit code `1` en probeert een fout-JSON naar `--out` te schrijven:

```json
{
  "status": "error",
  "metadata": {
    "deterministic": true,
    "schema_version": "neuraxon.poc-wrapper.v1",
    "wrapper_version": "0.1.0"
  },
  "error": {
    "code": "contract_validation_error",
    "message": "Field 'variant' must be a non-empty string"
  }
}
```

Mogelijke error-codes:
- `input_not_found`
- `input_read_error`
- `input_invalid_json`
- `contract_validation_error`
- `output_write_error`

## Observability hooks (wat loggen)
Voor volgende iteratie naar productie-adapter:
- `request_id` of `request_fingerprint`
- input context: `use_case`, `variant`, `seed`
- `status` (`ok`/`error`) en `error.code`
- wrapper-versie (`wrapper_version`) en schema-versie (`schema_version`)
- duur van call (`duration_ms`)
- (optioneel) adapter downstream metrics: retries, timeouts, upstream status code

Minimale log-events:
- `poc_wrapper.start`
- `poc_wrapper.success`
- `poc_wrapper.error`

## Volgende stap naar echte adapter
1. Vervang `result.mode=placeholder` door echte Neuraxon adapter-aanroep.
2. Voeg runtime-metrics toe (`duration_ms`, `model_runtime_sec`, resource usage).
3. Maak contractversie expliciet uitbreidbaar (`schema_version` + backwards-compat policy).
4. Integreer met bestaande benchmark pipeline voor automatische claim-evidence.
