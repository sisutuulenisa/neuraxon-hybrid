# OpenML drift mini-run report (bounded)

- Generated at: `2026-02-27T23:59:42Z`
- Suite: `OpenML-CC18`
- Task IDs: `11, 37, 43`
- Variants: `neuraxon_full_proxy, baseline_classic`
- Budget: max_samples_per_task=2500, warm_start_samples=120, accuracy_window=128, recovery_hold_steps=32
- Drift setup: mode=deterministic_label_permutation_D1_D2_D1, start_frac=0.5, end_frac=0.75, collapse_threshold_frac=0.8
- ADWIN params: delta=0.002, clock=32, max_buckets=5, min_window_length=5, grace_period=10

## Protocol mapping (proxy) 

| Protocol field | Proxy in this mini-run | Definitie |
|---|---|---|
| `collapse_rate` | `collapse_rate_proxy` | % rolling-accuracy punten tijdens driftfase onder `collapse_threshold_frac * pre_drift_accuracy`. |
| `recovery95_steps` | `recovery95_steps_proxy` | Aantal stappen vanaf drift-start tot rolling accuracy >= 95% van pre-drift voor `recovery_hold_steps` opeenvolgende punten. |
| `stability_var` | `stability_var_proxy` | Variantie van rolling accuracy in recoverysegment (`D2->D1`). |
| `sigma_branching` | n/a (niet direct meetbaar) | Niet geschat in deze bounded setup; ADWIN-eventdichtheid is enkel kwalitatief signaal. |

## Run rows

| task_id | dataset | variant | status | acc_pre | acc_drift | acc_recovery | collapse_rate_proxy | recovery95_steps_proxy | adwin_events |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 11 | balance-scale | neuraxon_full_proxy | ok | 0.6493 | 0.3970 | 0.5174 | 0.6731 | 243 | 2 |
| 11 | balance-scale | baseline_classic | ok | 0.9136 | 0.9091 | 0.9125 | 0.0000 | 0 | 0 |
| 37 | diabetes | neuraxon_full_proxy | ok | 0.4880 | 0.5391 | 0.5768 | 0.2396 | 0 | 2 |
| 37 | diabetes | baseline_classic | ok | 0.9651 | 0.9548 | 0.9322 | 0.0000 | 0 | 0 |
| 43 | spambase | neuraxon_full_proxy | ok | 0.4287 | 0.6009 | 0.5031 | 0.2928 | 52 | 11 |
| 43 | spambase | baseline_classic | ok | 0.9622 | 0.9338 | 0.9767 | 0.0496 | 0 | 1 |

## Compacte interpretatie

- Dit is een **bounded externe kalibratie** (3 taken, beperkte samplebudgetten), geen brede suite-evaluatie.
- ADWIN-events tonen detecteerbare shifts in de online errorstroom, maar zijn geen op zichzelf staand claim-PASS bewijs.
- Proxies vullen protocolgaten richting collapse/recovery-signalen met expliciete detectorinstellingen.
