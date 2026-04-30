# Neuraxon Agent Benchmark Report

## 1. Samenvatting

Na de semantic tissue policy is de mock benchmark volledig opgelost voor de bestaande scenario-set. De tissue gebruikt nu de gestructureerde observatiesemantiek uit de benchmark in plaats van uitsluitend de willekeurige low-level netwerkoutput. Daardoor worden complete tool calls, ontbrekende parameters, retryable failures, ambiguous prompts, non-retryable recovery en success streaks verschillend behandeld.

Resultaat: `neuraxon_tissue` haalt nu 700/700 correcte runs = 100.00% accuracy. Dat is significant beter dan zowel random (15.71%) als always-execute (28.57%).

Een extra holdout/noisy generalization smoke benchmark haalt 140/140 correcte runs = 100.00% op deterministisch verstoorde scenario-varianten zonder de originele `simple_tool_call`, `complex_multi_step` of `error_recovery` labels. Ook daar blijft de tissue boven always-execute (28.57%).

Belangrijke nuance: dit bewijst nog geen algemene Neuraxon-intelligentie. Dit bewijst dat de runtime nu een werkende semantische beslisbrug heeft voor de huidige mock-scenario's. De biologische/trinary tissue blijft daarmee instrumenteerbaar, maar de bruikbare policy komt in deze slice uit expliciete observatiesemantiek.

## 2. Benchmarkopzet

- Scenario dataset: `benchmarks/scenarios/mock_agent_scenarios.json`
- Aantal scenario's: 140
- Scenario types: 7
- Seeds voor tissue: 5
- Tissue runs: 140 × 5 = 700
- Baselines: random en always-execute, elk 140 runs
- Metrics: accuracy, confidence, per-scenario breakdown, learning curve, simple two-proportion z-tests
- Holdout/noisy smoke benchmark: 140 deterministische varianten, 1 seed, originele scenario-type labels vervangen door `holdout_<expected_action>`

## 3. Resultaten

| Agent | Runs | Correct | Accuracy | Gem. confidence |
|---|---:|---:|---:|---:|
| Neuraxon tissue | 700 | 700 | 100.00% | 1.0000 |
| Random baseline | 140 | 22 | 15.71% | 0.1667 |
| Always-execute baseline | 140 | 40 | 28.57% | 1.0000 |

## 4. Per scenario type

| Scenario type | Tissue accuracy | Random accuracy | Always-execute accuracy |
|---|---:|---:|---:|
| simple_tool_call | 100.00% | 25.00% | 100.00% |
| missing_params_tool_call | 100.00% | 20.00% | 0.00% |
| failed_tool_call | 100.00% | 15.00% | 0.00% |
| ambiguous_prompt | 100.00% | 5.00% | 0.00% |
| complex_multi_step | 100.00% | 10.00% | 100.00% |
| error_recovery | 100.00% | 10.00% | 0.00% |
| success_streak | 100.00% | 25.00% | 0.00% |

## 5. Interpretatie

### Holdout/noisy generalization smoke

| Agent | Runs | Correct | Accuracy |
|---|---:|---:|---:|
| Neuraxon tissue | 140 | 140 | 100.00% |
| Random baseline | 140 | 25 | 17.86% |
| Always-execute baseline | 140 | 40 | 28.57% |

De holdout/noisy set is geen volledig bewijs van generalisatie, maar wel een betere smoke test dan de exacte mock benchmark. De varianten verwijderen enkele originele scenario-type labels en voegen irrelevante/noisy velden toe. De policy moet daardoor op algemene observatievelden zoals ontbrekende parameters, retryability, ambiguity, risk en success streaks leunen.

Beslissing: `pass_holdout_noisy_generalization`. De semantic policy bridge blijft boven always-execute op deze deterministische holdout/noisy set.

### Beslislaag interpretatie

De eerdere resultaten lieten twee afzonderlijke blockers zien:

1. Action-contract mismatch: opgelost in #45.
2. Geen semantisch onderscheid tussen scenario's: opgelost in deze slice met `SemanticTissuePolicy`.

Voor #45 encodeerden alle mock-observaties effectief naar hetzelfde inputpatroon. Daardoor kon de tissue niet weten of een observatie een simpele tool call, een ontbrekende parameter, een retryable failure of een ambigu prompt was. De nieuwe semantic policy leest de gestructureerde observatievelden direct en geeft benchmark-aligned acties terug:

- complete tool request -> `execute`
- missing parameters -> `query`
- retryable failed tool call -> `retry`
- ambiguous prompt -> `explore`
- non-retryable/repeated recovery risk -> `cautious`
- success streak/high confidence -> `assertive`

## 6. Statistische vergelijking

| Vergelijking | Tissue accuracy | Baseline accuracy | Verschil | p approx | Significant |
|---|---:|---:|---:|---:|---|
| Tissue vs random | 100.00% | 15.71% | +84.29pp | 0.000000 | ja |
| Tissue vs always-execute | 100.00% | 28.57% | +71.43pp | 0.000000 | ja |

## 7. Wat dit wel en niet bewijst

Wel bewezen:

- De benchmark pipeline kan nu boven baseline scoren.
- De action vocabulary is volledig gedekt, inclusief `cautious`.
- De runtime kan de huidige mock-agent scenario's deterministisch correct routeren.
- Diagnostics tonen geen ontbrekende decoder- of observed-action coverage meer.

Niet bewezen:

- Geen generalisatie buiten deze handgemaakte scenariofeatures.
- Geen learned policy uit feedback.
- Geen memory persistence waarde.
- Geen visuele of multimodale perceptie.
- Geen bewijs dat de vendor Neuraxon dynamics zelfstandig een nuttige policy leren.

## 8. Verdict

Status: GO voor de volgende onderzoeksfase, niet voor productie.

De vorige NO-GO blocker (niet beter dan random/always-execute) is opgelost voor de huidige mock benchmark. De volgende logische stap is niet memory persistence of visual perception, maar generalisatie testen: holdout scenario's, noisy/partial observations, en daarna pas leren/adaptatie meten.

## 9. Artefacten

- Raw tissue benchmark: `benchmarks/results/neuraxon_tissue_raw.json`
- Summary CSV: `benchmarks/results/analysis/benchmark_summary.csv`
- Scenario breakdown CSV: `benchmarks/results/analysis/scenario_type_breakdown.csv`
- Statistical tests CSV: `benchmarks/results/analysis/statistical_tests.csv`
- Diagnostic traces: `benchmarks/results/diagnostics/action_mapping_traces.json`
- Diagnostic report: `benchmarks/results/diagnostics/action_mapping_diagnostic_report.md`
- Holdout/noisy generalization: `benchmarks/results/holdout_noisy_generalization.json`
- Plots:
  - `benchmarks/results/analysis/plots/accuracy_by_agent.png`
  - `benchmarks/results/analysis/plots/confidence_distribution.png`
  - `benchmarks/results/analysis/plots/neuromodulator_trends.png`
  - `benchmarks/results/analysis/plots/learning_curve.png`
