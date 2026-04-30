# Neuraxon Tissue Action Mapping Diagnostic

## Verdict
- Root cause classification: `network_never_reaches_expected_actions`.
- Runs inspected: 700.
- Successful runs under current benchmark scoring: 110.

## Core Finding
- The mock benchmark expects: `assertive, cautious, execute, explore, query, retry`.
- ActionDecoder emits: `ESCALATE, EXPLORE, PAUSE, PROCEED, RETRY`.
- ActionDecoder normalized benchmark actions: `assertive, execute, explore, query, retry`.
- The traced tissue runs observed after normalization: `assertive, execute, query, retry`.
- Expected actions missing from decoder vocabulary: `cautious`.
- Expected actions not observed in traced runs: `cautious, explore`.

Benchmark scoring now uses the normalized benchmark action contract, so the previous pure string-vocabulary mismatch is no longer the main failure mode. Any remaining misses are now evidence about which normalized actions the tissue actually reaches, before learning, memory, or visual perception enter the picture.

## Non-goals for the next fix
- Do not implement memory persistence yet; persistence would only store decisions from a mismatched action contract.
- Do not add visual perception yet; the action contract must be fixed on simple mock scenarios first.

## Recommended follow-up
1. Re-run the full benchmark and compare normalized Neuraxon accuracy against random and always-execute baselines.
2. Diagnose remaining decision-quality gaps separately from scoring compatibility.
3. Only revisit memory persistence or visual perception after the simple mock-scenario action policy beats baseline behavior.

## Artefacts
- Trace JSON: `benchmarks/results/diagnostics/action_mapping_traces.json`
- Confusion CSV: `benchmarks/results/diagnostics/action_confusion_matrix.csv`
