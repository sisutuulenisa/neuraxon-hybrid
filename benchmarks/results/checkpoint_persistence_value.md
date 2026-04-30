# Checkpoint Persistence Decision-Value Evaluation

## Summary
Persisted checkpoint mode beat cold-start on seeded restart scenarios; the measured decision value comes from checkpointed runtime temporal context, not from a standalone raw-network generalization claim.

## Mode comparison

| Mode | Runs | Successes | Success rate | Failure modes |
| --- | ---: | ---: | ---: | --- |
| persisted_checkpoint | 5 | 5 | 100.00% | none |
| cold_start | 5 | 0 | 0.00% | none |
| missing_checkpoint | 1 | 0 | 0.00% | missing_checkpoint=1 |
| corrupt_checkpoint | 1 | 0 | 0.00% | corrupt_checkpoint=1 |
| incompatible_checkpoint | 1 | 0 | 0.00% | incompatible_checkpoint=1 |

## Interpretation
Persisted checkpoints have measured decision value here only when restart restores the bounded runtime temporal context established during episode A. Cold-start sees the same episode B probes without that prior context and therefore cannot reliably choose the seeded action.

Missing checkpoint, corrupt checkpoint, and incompatible schema baselines are explicit failure modes rather than silent cold-start successes.

This remains conservative about raw Neuraxon generalization: the positive result is restart continuity for checkpointed adapter/runtime state, not proof that the raw network alone learned a durable policy.
