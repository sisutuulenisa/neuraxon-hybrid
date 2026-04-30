# Neuraxon Agent Benchmark Report

## 1. Samenvatting

Na de semantic tissue policy is de mock benchmark volledig opgelost voor de bestaande scenario-set. De tissue gebruikt nu de gestructureerde observatiesemantiek uit de benchmark in plaats van uitsluitend de willekeurige low-level netwerkoutput. Daardoor worden complete tool calls, ontbrekende parameters, retryable failures, ambiguous prompts, non-retryable recovery en success streaks verschillend behandeld.

Resultaat: `neuraxon_tissue` haalt nu 700/700 correcte runs = 100.00% accuracy. Dat is significant beter dan zowel random (15.71%) als always-execute (28.57%).

Een extra holdout/noisy generalization smoke benchmark haalt nog altijd 140/140 correcte runs = 100.00%, maar dat resultaat is nu expliciet gedegradeerd van “pass” naar `needs_temporal_dynamics_evidence`: alle 140 finale observaties zijn direct oplosbaar door de expliciete semantic policy bridge (`semantic_policy_coverage=100%`). Dat bevestigt je vermoeden: 100% is hier vooral oracle-/feature-coverage, niet bewijs voor emergente Neuraxon-dynamiek.

Daarom is er nu een NIA-geïnspireerde temporal dynamics probe toegevoegd. Die verbergt de finale actie-oracle in een generieke `temporal_decision_probe`; de relevante signalen zitten alleen in eerdere observaties. Op die strengere probe haalt `neuraxon_tissue` 1/6 = 16.67%, gelijk aan always-execute en onder random (33.33% op deze kleine set). Dit is het juiste kritische signaal: de huidige slice bewijst een nuttige semantische adapter, maar nog geen continue-tijd/stateful/neuromodulated generalisatie.

Belangrijke nuance: dit bewijst nog geen algemene Neuraxon-intelligentie. Dit bewijst dat de runtime nu een werkende semantische beslisbrug heeft voor de huidige mock-scenario's. De biologische/trinary tissue blijft daarmee instrumenteerbaar, maar de bruikbare policy komt in deze slice uit expliciete observatiesemantiek.

## 2. Benchmarkopzet

- Scenario dataset: `benchmarks/scenarios/mock_agent_scenarios.json`
- Aantal scenario's: 140
- Scenario types: 7
- Seeds voor tissue: 5
- Tissue runs: 140 × 5 = 700
- Baselines: random en always-execute, elk 140 runs
- Metrics: accuracy, confidence, per-scenario breakdown, learning curve, simple two-proportion z-tests
- Holdout/noisy smoke benchmark: 140 deterministische varianten, 1 seed, originele scenario-type labels vervangen door `holdout_<expected_action>`; 100% semantic-policy coverage, dus niet als echte generalisatieclaim behandelen
- Temporal dynamics probe: 6 NIA-geïnspireerde scenario's, 1 seed, finale observatie bevat geen actie-oracle; meet of eerdere observaties/state carry-over de beslissing dragen

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

De holdout/noisy set is geen volledig bewijs van generalisatie. De varianten verwijderen enkele originele scenario-type labels en voegen irrelevante/noisy velden toe, maar de finale observaties blijven allemaal direct oplosbaar via algemene observatievelden zoals ontbrekende parameters, retryability, ambiguity, risk en success streaks.

Semantic-policy coverage audit:

| Maat | Waarde |
|---|---:|
| Finale observaties | 140 |
| Direct oplosbaar door semantic policy | 140 |
| Coverage | 100.00% |

Beslissing: `needs_temporal_dynamics_evidence`. De semantic policy bridge blijft boven always-execute op deze deterministische holdout/noisy set, maar 100% coverage betekent dat deze score vooral bewijst dat de handgemaakte observatiefeatures goed afgedekt zijn.

### NIA temporal dynamics probe

Qubic's NIA-artikelen leggen de lat anders: Vol. 1 benadrukt continue tijd en state carry-over, Vol. 2 trinary neutral/subthreshold buffering, Vol. 3 neuromodulatie en plasticity windows, Vol. 5 astrocytic/eligibility-gated plasticity, en Vol. 7 emergentie rond edge-of-chaos-dynamiek. Een one-shot finale observatie met expliciete semantische velden test dat niet.

Daarom is er nu een kleine temporal dynamics probe toegevoegd. De finale observatie is overal dezelfde generieke `temporal_decision_probe`; de relevante signalen zitten alleen in de voorafgaande observaties. Resultaat:

| Agent | Runs | Correct | Accuracy |
|---|---:|---:|---:|
| Neuraxon tissue | 6 | 1 | 16.67% |
| Random baseline | 6 | 2 | 33.33% |
| Always-execute baseline | 6 | 1 | 16.67% |

Interpretatie: de huidige runtime draagt nog onvoldoende taakrelevante temporele dynamiek door tot een finale probe zonder expliciete action oracle. Dat is geen regressie; het is een eerlijkere onderzoeksmeting die voorkomt dat de semantic bridge als Neuraxon-generalisatie wordt verkocht.

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

Status: GO voor de semantische adapter, NO-GO voor Neuraxon-generalisatieclaims.

De vorige NO-GO blocker (niet beter dan random/always-execute) is opgelost voor de huidige mock benchmark. De nieuwe blocker is scherper: perfecte scores op exact/holdout-noisy zijn verdacht wanneer 100% van de finale observaties direct door een handgeschreven policy oplosbaar is. De volgende logische stap is daarom niet memory persistence of visual perception, maar een grotere temporal/criticality benchmark waarin beslissingen afhangen van state carry-over, neuromodulatorniveaus, eligibility/plasticity gates en perturbaties rond de edge of chaos.

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
