# Neuraxon Tissue Action Mapping Diagnostic

## Verdict
- Root cause classification: `action_vocabulary_mismatch`.
- Runs inspected: 700.
- Successful runs under current benchmark scoring: 0.

## Core Finding
- The mock benchmark expects: `assertive, cautious, execute, explore, query, retry`.
- ActionDecoder emits: `ESCALATE, PAUSE, PROCEED, RETRY`.
- The traced tissue runs observed: `ESCALATE, PAUSE, PROCEED, RETRY`.
- Expected actions missing from decoder vocabulary: `assertive, cautious, execute, explore, query, retry`.
- Expected actions not observed in traced runs: `assertive, cautious, execute, explore, query, retry`.

The 0% benchmark accuracy is therefore explained before learning, memory, or visual perception enter the picture: the benchmark scenarios use a lowercase task-policy vocabulary while the current ActionDecoder emits uppercase control-policy labels. No current decoder output can equal the expected mock benchmark actions, so equality scoring must always fail.

## Non-goals for the next fix
- Do not implement memory persistence yet; persistence would only store decisions from a mismatched action contract.
- Do not add visual perception yet; the action contract must be fixed on simple mock scenarios first.

## Recommended follow-up
1. Decide whether benchmark actions should map onto the existing decoder vocabulary or whether the decoder should emit the benchmark vocabulary.
2. Add an explicit action-contract adapter and tests for all expected benchmark actions.
3. Re-run the benchmark after the contract is aligned, then diagnose actual network decision quality separately from scoring compatibility.

## Artefacts
- Trace JSON: `benchmarks/results/diagnostics/action_mapping_traces.json`
- Confusion CSV: `benchmarks/results/diagnostics/action_confusion_matrix.csv`
