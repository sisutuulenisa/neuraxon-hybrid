# OPENML_DRIFT_MINIRUN_001 — Bounded externe kalibratie (3 taken)

**Datum:** 2026-02-28  
**Doel:** beperkte externe kalibratie op 3 OpenML-taken met expliciete driftsignalen en compacte protocolmapping.

## Scope en reproduceerbaarheid

- Runner: `scripts/run_openml_subset.py`
- Manifest: `benchmarks/manifests/openml_subset_phase5.json`
- Output: `benchmarks/results/openml/pilot_2026-02-28/`
- Suite: `OpenML-CC18`
- Taakselectie (expliciet, vast): `11` (balance-scale), `37` (diabetes), `43` (spambase)
- Variants: `neuraxon_full_proxy`, `baseline_classic`
- Budget (bounded):
  - `max_samples_per_task=2500`
  - `warm_start_samples=120`
  - `accuracy_window=128`
  - `recovery_hold_steps=32`
- Driftinjectie (deterministisch D1→D2→D1):
  - label-permutatie in segment `[start_frac=0.50, end_frac=0.75]`
- Drift detector: **River ADWIN**
  - `delta=0.002`, `clock=32`, `max_buckets=5`, `min_window_length=5`, `grace_period=10`

## Compacte resultaten

Bronbestand: `benchmarks/results/openml/pilot_2026-02-28/openml_runs.csv`

| task_id | dataset | variant | acc_pre | acc_drift | acc_recovery | collapse_rate_proxy | recovery95_steps_proxy | adwin_event_count |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 11 | balance-scale | neuraxon_full_proxy | 0.6493 | 0.3970 | 0.5174 | 0.6731 | 243 | 2 |
| 11 | balance-scale | baseline_classic | 0.9136 | 0.9091 | 0.9125 | 0.0000 | 0 | 0 |
| 37 | diabetes | neuraxon_full_proxy | 0.4880 | 0.5391 | 0.5768 | 0.2396 | 0 | 2 |
| 37 | diabetes | baseline_classic | 0.9651 | 0.9548 | 0.9322 | 0.0000 | 0 | 0 |
| 43 | spambase | neuraxon_full_proxy | 0.4287 | 0.6009 | 0.5031 | 0.2928 | 52 | 11 |
| 43 | spambase | baseline_classic | 0.9622 | 0.9338 | 0.9767 | 0.0496 | 0 | 1 |

## Protocolmapping (proxy)

| Protocolveld (`docs/TEST_PROTOCOL_PHASE1_2.md`) | Proxy in mini-run | Betekenis | Opmerking |
|---|---|---|---|
| `collapse-rate` | `collapse_rate_proxy` | fractie rolling-accuracy in driftsegment onder `0.8 * pre_drift_accuracy` | geschikt als snelle collapse-indicatie |
| `R95` / `recovery95_steps` | `recovery95_steps_proxy` | stappen vanaf drift-start tot rolling-accuracy >= 95% van pre-drift voor 32 opeenvolgende punten | proxy, niet identiek aan originele perturbatie-definitie |
| `SV` (`stability_var`) | `stability_var_proxy` | variantie van rolling-accuracy in recoverysegment | bruikbaar voor relatieve stabiliteitsvergelijking |
| `sigma` (branching ratio) | n.v.t. | niet direct observeerbaar in deze setup | ADWIN-eventcount enkel kwalitatief driftsignaal |

## Korte interpretatie

- Dit levert **externe kalibratie-evidence** buiten de synthetische use-cases, met strikte scope (3 taken).
- ADWIN-events reageren op shifts in de online errorstroom; parameters zijn expliciet gelogd per run.
- De protocolmapping vult vooral `collapse/recovery/stability`-proxies in; `sigma` blijft open en vereist aparte dynamica-instrumentatie.
- Dit rapport is **niet** bedoeld als finale claim-gate, maar als bounded frontier-evidence voor fase 5.

## Re-run command

```bash
./scripts/run_openml_subset.py \
  --manifest benchmarks/manifests/openml_subset_phase5.json \
  --out-dir benchmarks/results/openml/pilot_2026-02-28
```
