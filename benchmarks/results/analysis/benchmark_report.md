# Neuraxon Agent Benchmark Report

## 1. Samenvatting

Na de semantic tissue policy is de mock benchmark volledig opgelost voor de bestaande scenario-set. De tissue gebruikt nu de gestructureerde observatiesemantiek uit de benchmark in plaats van uitsluitend de willekeurige low-level netwerkoutput. Daardoor worden complete tool calls, ontbrekende parameters, retryable failures, ambiguous prompts, non-retryable recovery en success streaks verschillend behandeld.

Resultaat: `neuraxon_tissue` haalt nu 700/700 correcte runs = 100.00% accuracy. Dat is significant beter dan zowel random (15.71%) als always-execute (28.57%).

Een extra holdout/noisy generalization smoke benchmark haalt nog altijd 140/140 correcte runs = 100.00%; alle 140 finale observaties zijn direct oplosbaar door de expliciete semantic policy bridge (`semantic_policy_coverage=100%`). Dat bevestigt je vermoeden: 100% is hier vooral oracle-/feature-coverage, niet bewijs voor emergente Neuraxon-dynamiek.

Daarom is de NIA-geïnspireerde temporal dynamics probe uitgebreid van 6 smoke cases naar 108 gegenereerde scenario's: 6 actie-archetypes × 3 dataset-seeds × 3 sequentielengtes × 2 varianten. De finale actie-oracle zit verborgen in een generieke `temporal_decision_probe`; counterfactual pairs delen exact dezelfde finale observatie maar vereisen andere acties door de voorafgaande observaties, en noise/perturbation-varianten veranderen irrelevante velden zonder de latente temporele staat te wijzigen. Op die probe haalt `neuraxon_tissue` nu 108/108 = 100.00% via de expliciete temporal context adapter, maar de sequence-majority oracle baseline haalt ook 108/108.

Issue #70 voegt daarom een strengere anti-oracle temporal benchmark toe: 48 scenario's met task-family train/test split, identieke finale probes, gemaskeerde schema-/field-namen, counterfactual pairs met dezelfde aggregate sequence statistics en irrelevante perturbatievelden. Daarop haalt sequence-majority 0/48 = 0.00% in plaats van 100%, terwijl `temporal_context_adapter` en de full `semantic_bridge` mode 48/48 = 100.00% halen. Raw-network-only haalt 7/48 = 14.58%, waardoor de output expliciet adapter-success van raw-network-success scheidt.

Belangrijke nuance: dit bewijst nog geen algemene Neuraxon-intelligentie. Dit bewijst dat de runtime nu een werkende semantische beslisbrug heeft voor de huidige mock-scenario's. De biologische/trinary tissue blijft daarmee instrumenteerbaar, maar de bruikbare policy komt in deze slice uit expliciete observatiesemantiek.

### Proven / not proven summary

Proven:

- semantic bridge performance: 700/700 correcte runs (100.00%) op de huidige mock benchmark.
- explicit temporal context adapter performance: 108/108 correcte runs (100.00%) op de temporal dynamics probe met identieke finale observaties, plus 48/48 (100.00%) op de anti-oracle masked temporal probe.
- simple baseline performance: random haalt 22/140 (15.71%) en always-execute haalt 40/140 (28.57%) op de mock benchmark; op de oudere temporal probe haalt sequence-majority nog 100.00%, maar op de anti-oracle split zakt sequence-majority naar 0/48 (0.00%).
- criticality/dynamics instrumentation evidence: `dynamics_metrics.csv` bevat 11.000 per-step samples en `criticality_summary.csv` classificeert de tissue-run als `near_useful_dynamic_regime` met neutral-state occupancy 0.757844, transition entropy 0.332013 en modulation action-change rate 0.000000.

Not proven:

- raw Neuraxon network generalization: policy-ablation `raw_network` haalt 110/700 (15.71%) op de mock benchmark en 7/48 (14.58%) op de anti-oracle temporal benchmark, dus geen claim dat de ruwe continuous-time/trinary dynamics zelfstandig een nuttige policy boven eenvoudige baselines leren.
- learned policy uit feedback: modulation verandert interne state, maar deze regeneratie toont geen post-feedback behavioral action changes.
- memory persistence of visual perception value: beide blijven buiten scope tot raw/adapter separation sterker bewijs levert.

## 2. Benchmarkopzet

- Scenario dataset: `benchmarks/scenarios/mock_agent_scenarios.json`
- Aantal scenario's: 140
- Scenario types: 7
- Seeds voor tissue: 5
- Tissue runs: 140 × 5 = 700
- Baselines: random en always-execute, elk 140 runs
- Metrics: accuracy, confidence, per-scenario breakdown, learning curve, simple two-proportion z-tests
- Holdout/noisy smoke benchmark: 140 deterministische varianten, 1 seed, originele scenario-type labels vervangen door `holdout_<expected_action>`; 100% semantic-policy coverage, dus niet als echte generalisatieclaim behandelen
- Temporal dynamics benchmark: 108 NIA-geïnspireerde scenario's (6 actie-archetypes × 3 dataset-seeds × 3 sequentielengtes × counterfactual/noise-perturbation varianten), 1 tissue seed; finale observatie bevat geen actie-oracle en counterfactual pairs kunnen exact dezelfde finale probe met verschillende verwachte acties hebben
- Anti-oracle temporal benchmark: 48 scenario's met task-family train/test split (24 train, 24 test), identieke finale probes, gemaskeerde schema-/field-namen, counterfactual pairs met dezelfde aggregate sequence statistics, perturbation/noise fields, en aparte scores voor full tissue runtime, raw-network-only, semantic-policy-only, temporal-context-adapter, random, always-execute, last-observation-only en sequence-majority.

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

Beslissing: `pass_temporal_context_bridge_evidence`. De semantic policy bridge blijft boven always-execute op deze deterministische holdout/noisy set, maar 100% coverage betekent dat deze score vooral bewijst dat de handgemaakte observatiefeatures goed afgedekt zijn. De temporal probe hieronder is daarom de relevante state-carry-over check.

### NIA temporal dynamics probe

Qubic's NIA-artikelen leggen de lat anders: Vol. 1 benadrukt continue tijd en state carry-over, Vol. 2 trinary neutral/subthreshold buffering, Vol. 3 neuromodulatie en plasticity windows, Vol. 5 astrocytic/eligibility-gated plasticity, en Vol. 7 emergentie rond edge-of-chaos-dynamiek. Een one-shot finale observatie met expliciete semantische velden test dat niet.

Daarom is de temporal dynamics benchmark nu uitgebreid. De finale observatie is overal dezelfde generieke `temporal_decision_probe`; de relevante signalen zitten alleen in de voorafgaande observaties. De dataset bevat 108 scenario's met meerdere dataset-seeds, sequentielengtes, counterfactual pairs en noise/perturbation-varianten. Resultaat:

| Agent | Runs | Correct | Accuracy |
|---|---:|---:|---:|
| Neuraxon tissue | 108 | 108 | 100.00% |
| Random baseline | 108 | 19 | 17.59% |
| Always-execute baseline | 108 | 18 | 16.67% |
| Last-observation-only baseline | 108 | 0 | 0.00% |
| Semantic-policy-only baseline | 108 | 0 | 0.00% |
| Sequence-majority oracle baseline | 108 | 108 | 100.00% |

Interpretatie: last-observation-only en semantic-policy-only falen volledig omdat de finale probe geen semantische actievelden bevat. De sequence-majority baseline bewijst dat de verwachte actie wel degelijk uit de voorafgaande sequentie afleidbaar is. `neuraxon_tissue` haalt nu dezelfde perfecte score via `temporal_context_bridge`: een expliciete temporal context adapter in AgentTissue die compacte prior-observation evidence samenvat voordat de identieke finale probe wordt beslist. Dat behoudt de scheiding tussen semantic-policy success en temporale state carry-over, en is beter dan last-observation-only/always-execute, maar het is nog expliciete adapterlogica; raw Neuraxon network dynamics blijven apart gerapporteerd via policy-ablation.

### Anti-oracle temporal generalization probe (#70)

De nieuwe anti-oracle variant maakt de vorige temporal probe strenger op precies de failure mode uit issue #70: semantic labels, duidelijke field names en sequence-majority heuristieken mogen de benchmark niet triviaal oplossen. De scenario's gebruiken een task-family train/test split, maskeren schema-/field-namen (`x*`/`z*` i.p.v. `signal`, `risk`, `missing_count`, enz.), delen dezelfde finale probe (`{"z0": 0, "z1": "probe", "z2": 1}`), en bevatten counterfactual pairs waarvan aggregate sequence statistics overeenkomen terwijl de juiste actie verschilt.

| Agent / mode | Runs | Correct | Accuracy |
|---|---:|---:|---:|
| Full tissue runtime (`semantic_bridge`) | 48 | 48 | 100.00% |
| Temporal-context-adapter mode | 48 | 48 | 100.00% |
| Raw-network-only mode | 48 | 7 | 14.58% |
| Semantic-policy-only mode | 48 | 7 | 14.58% |
| Random baseline | 48 | 5 | 10.42% |
| Always-execute baseline | 48 | 8 | 16.67% |
| Last-observation-only baseline | 48 | 0 | 0.00% |
| Sequence-majority baseline | 48 | 0 | 0.00% |

Interpretatie: de anti-oracle benchmark voldoet aan de strengere acceptatie voor deze fase: de sequence-majority baseline bereikt niet langer triviaal 100%, counterfactuals vereisen prior state, output is deterministisch voor vaste seeds, en de metrics scheiden adapter-success van raw-network-success. De 100% score is nog altijd adaptergedreven (`temporal_context_bridge`), niet raw Neuraxon learning.

### Policy-ablation benchmark

Issue #52 voegt de expliciete ablation toe die semantic-bridge performance scheidt van raw-network performance. Dezelfde 140 scenario's × 5 seeds zijn in drie modes gedraaid:

| Mode | Runs | Correct | Accuracy | Interpretatie |
|---|---:|---:|---:|---|
| semantic-bridge enabled | 700 | 700 | 100.00% | Handgeschreven semantische brug lost policy-covered observations op. |
| raw-network only | 700 | 110 | 15.71% | Low-level decoderpad zonder semantic policy; dit is de ruwe Neuraxon-bijdrage in deze slice. |
| semantic-bridge coverage audit | 700 | 700 | 100.00% | Auditmodus die zichtbaar houdt dat policy-covered observations niet als Neuraxon-generalisatie mogen tellen. |

Conclusie: raw-network performance blijft apart gerapporteerd en ligt onder always-execute op de huidige mock benchmark. Er wordt daarom geen claim van Neuraxon generalization gemaakt uit policy-covered observations; de 100% score is een semantic-bridge resultaat.

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

### Criticality en neuromodulator dynamics

Issue #54 voegt per-step dynamics instrumentation toe aan de tissue benchmark zonder vendored upstream Neuraxon-code te wijzigen. Elk raw benchmarkresultaat bevat nu `dynamics_samples` met activity, energy, trinary state distribution, neutral-state occupancy en neuromodulator levels per gesimuleerde stap. Daarnaast bevat elk resultaat `criticality_metrics` met activity variance, transition entropy, neutral-state occupancy, branching/activity propagation ratio en gemiddelde energy.

De analyse schrijft twee nieuwe artefacten onder `benchmarks/results/analysis/`: `dynamics_metrics.csv` voor per-step inspectie en `criticality_summary.csv` voor run-level interpretatie. De summary classificeert de dynamiek expliciet als `dead`, `saturated`, `random_like` of `near_useful_dynamic_regime`, zodat het rapport kan antwoorden of een run dead/saturated/random-like is of near useful dynamic regime lijkt. Modulation wordt apart vastgelegd via neuromodulator deltas en `modulation_action_change_rate`: in deze slice verandert modulatie vooral observable state; een behavioral effect is pas aangetoond wanneer latere decisions na feedback veranderen.

| Metric | Interpretatie |
|---|---|
| Activity variance | Lage variantie wijst op dead/saturated regime; gematigde variantie wijst op bruikbare dynamiek. |
| Transition entropy | Meet hoeveel trinary states over stappen wisselen; extreem laag is frozen/dead, extreem hoog met instabiele propagation is random-like. |
| Neutral-state occupancy | Houdt bij of het trinary netwerk vooral neutraal/subthreshold buffert of volledig actief/saturated is. |
| Branching ratio | Eenvoudige activity-propagation proxy: actieve neuronen in stap t+1 tegenover stap t. |
| Modulation action-change rate | Geeft aan of neuromodulator feedback later observable decisions wijzigt of alleen interne state. |

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
- Geen bewijs dat de vendor Neuraxon dynamics zelfstandig een nuttige policy leren; de anti-oracle split maakt dat expliciet met raw-network-only 14.58% versus temporal-context-adapter 100.00%.

## 8. Verdict

Status: GO voor de semantische adapter en de expliciete temporal context adapter; NO-GO voor raw Neuraxon-generalisatieclaims.

De vorige NO-GO blocker (niet beter dan random/always-execute) is opgelost voor de huidige mock benchmark. De temporal blocker is voor deze bounded slice sterker opgelost: identieke finale probes kunnen verschillend worden beslist op basis van voorafgaande observaties, de anti-oracle split verslaat sequence-majority/last-observation-only, en de rapportage scheidt full tissue, raw-network, semantic-policy-only en temporal-context-adapter modes. De nuance blijft scherp: perfecte anti-oracle temporal scores komen uit expliciete adapterlogica (`temporal_context_bridge`) en niet uit aangetoonde raw continuous-time/neuromodulated learning. Memory persistence en visual perception blijven buiten scope tot raw/adapter-separation verdere nuttige beslissingen blijft aantonen.

## 9. Artefacten

- Raw tissue benchmark: `benchmarks/results/neuraxon_tissue_raw.json`
- Summary CSV: `benchmarks/results/analysis/benchmark_summary.csv`
- Scenario breakdown CSV: `benchmarks/results/analysis/scenario_type_breakdown.csv`
- Statistical tests CSV: `benchmarks/results/analysis/statistical_tests.csv`
- Dynamics metrics CSV: `benchmarks/results/analysis/dynamics_metrics.csv`
- Criticality summary CSV: `benchmarks/results/analysis/criticality_summary.csv`
- Diagnostic traces: `benchmarks/results/diagnostics/action_mapping_traces.json`
- Diagnostic report: `benchmarks/results/diagnostics/action_mapping_diagnostic_report.md`
- Holdout/noisy generalization: `benchmarks/results/holdout_noisy_generalization.json`
- Policy-ablation benchmark: `benchmarks/results/policy_ablation.json`
- Plots:
  - `benchmarks/results/analysis/plots/accuracy_by_agent.png`
  - `benchmarks/results/analysis/plots/confidence_distribution.png`
  - `benchmarks/results/analysis/plots/neuromodulator_trends.png`
  - `benchmarks/results/analysis/plots/learning_curve.png`
  - `benchmarks/results/analysis/plots/activity_energy_trends.png`
