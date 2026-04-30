# Neuraxon Agent Benchmark Report

## 1. Samenvatting

Na de action-contract adapter is de pure vocabulary-mismatch uit PR #43 opgelost: `ActionDecoder`-labels zoals `PROCEED` en `PAUSE` worden nu genormaliseerd naar benchmark-acties zoals `execute` en `query`.

De Neuraxon tissue haalt daardoor niet langer 0.00%, maar 15.71% accuracy over 700 runs. Dat is exact gelijk aan de deterministic random baseline (15.71%) en nog steeds duidelijk lager dan always-execute (28.57%).

Go/No-Go: NO-GO voor gebruik als autonome beslislaag. De score bewijst dat de vorige 0%-meting grotendeels een scoring/contract-bug was, maar de tissue toont nog geen nuttige beslissingen boven baselinegedrag.

## 2. Methodologie

De benchmark vergelijkt drie agentvarianten op dezelfde set mock agent scenarios:

- `neuraxon_tissue`: de huidige AgentTissue-integratie met Neuraxon v2.0, gescoord via de genormaliseerde action-contract adapter.
- `random`: baseline die willekeurig uit de beschikbare agentacties kiest.
- `always_execute`: baseline die consequent de `execute`-actie kiest.

De scenario-set simuleert agent-observaties zoals eenvoudige tool calls, ontbrekende parameters, gefaalde tool calls, ambiguë prompts, complexe multi-step taken, error recovery en success streaks. Per run wordt gemeten of de gekozen genormaliseerde actie overeenkomt met de verwachte optimale actie. De analyse rapporteert daarnaast confidence, recovery time, learning-curve start/eindwaarden, scenario-type breakdowns en approximate significance checks.

Gebruikte analyse-artefacten:

- `benchmark_summary.csv`
- `scenario_type_breakdown.csv`
- `statistical_tests.csv`
- `plots/accuracy_by_agent.png`
- `plots/confidence_distribution.png`
- `plots/neuromodulator_trends.png`
- `plots/learning_curve.png`
- `../diagnostics/action_mapping_diagnostic_report.md`
- `../diagnostics/action_mapping_traces.json`
- `../diagnostics/action_confusion_matrix.csv`

## 3. Resultaten

### Vergelijkingstabel

| Agent | Runs | Successes | Accuracy | Gemiddelde confidence | Recovery time mean | Learning start | Learning end |
|---|---:|---:|---:|---:|---:|---:|---:|
| Neuraxon tissue | 700 | 110 | 15.71% | 0.509429 | 7.389610 | 40.00% | 40.00% |
| Random baseline | 140 | 22 | 15.71% | 0.166667 | 6.222222 | 0.00% | 0.00% |
| Always-execute baseline | 140 | 40 | 28.57% | 1.000000 | 60.000000 | 100.00% | 0.00% |

### Accuracy by agent

![Accuracy by agent](plots/accuracy_by_agent.png)

### Confidence distribution

![Confidence distribution](plots/confidence_distribution.png)

### Neuromodulator trends

![Neuromodulator trends](plots/neuromodulator_trends.png)

### Learning curve

![Learning curve](plots/learning_curve.png)

### Scenario-type breakdown

| Agent | Scenario type | Runs | Successes | Accuracy | Confidence mean |
|---|---|---:|---:|---:|---:|
| Always-execute | ambiguous_prompt | 20 | 0 | 0.00% | 1.000000 |
| Always-execute | complex_multi_step | 20 | 20 | 100.00% | 1.000000 |
| Always-execute | error_recovery | 20 | 0 | 0.00% | 1.000000 |
| Always-execute | failed_tool_call | 20 | 0 | 0.00% | 1.000000 |
| Always-execute | missing_params_tool_call | 20 | 0 | 0.00% | 1.000000 |
| Always-execute | simple_tool_call | 20 | 20 | 100.00% | 1.000000 |
| Always-execute | success_streak | 20 | 0 | 0.00% | 1.000000 |
| Neuraxon tissue | ambiguous_prompt | 100 | 0 | 0.00% | 0.492000 |
| Neuraxon tissue | complex_multi_step | 100 | 22 | 22.00% | 0.520000 |
| Neuraxon tissue | error_recovery | 100 | 0 | 0.00% | 0.502000 |
| Neuraxon tissue | failed_tool_call | 100 | 19 | 19.00% | 0.520000 |
| Neuraxon tissue | missing_params_tool_call | 100 | 40 | 40.00% | 0.506000 |
| Neuraxon tissue | simple_tool_call | 100 | 16 | 16.00% | 0.542000 |
| Neuraxon tissue | success_streak | 100 | 13 | 13.00% | 0.484000 |
| Random baseline | ambiguous_prompt | 20 | 1 | 5.00% | 0.166667 |
| Random baseline | complex_multi_step | 20 | 2 | 10.00% | 0.166667 |
| Random baseline | error_recovery | 20 | 2 | 10.00% | 0.166667 |
| Random baseline | failed_tool_call | 20 | 3 | 15.00% | 0.166667 |
| Random baseline | missing_params_tool_call | 20 | 4 | 20.00% | 0.166667 |
| Random baseline | simple_tool_call | 20 | 5 | 25.00% | 0.166667 |
| Random baseline | success_streak | 20 | 5 | 25.00% | 0.166667 |

### Statistical checks

| Metric | Treatment | Baseline | Treatment mean | Baseline mean | Difference | Statistic | Approx. p-value | Significant at 0.05 |
|---|---|---|---:|---:|---:|---:|---:|---|
| Accuracy | Neuraxon tissue | Random | 0.157143 | 0.157143 | 0.000000 | 0.000000 | 1.000000 | false |
| Accuracy | Neuraxon tissue | Always-execute | 0.157143 | 0.285714 | -0.128571 | -3.157853 | 0.001589 | true |

## 4. Analyse

De action-contract adapter verandert de diagnose substantieel: de vorige 0.00% was geen betrouwbare maat voor tissue-intelligentie, want de scorer vergeleek twee verschillende actievocabulaires. Na normalisatie is de accuracy 15.71%.

Dat is vooruitgang, maar nog geen bewijs van nuttige beslissingen. Neuraxon tissue is statistisch niet beter dan random (`p=1.000000`) en blijft significant slechter dan always-execute (`p≈0.001589`). De huidige score kan dus nog volledig baseline-achtig gedrag zijn.

De scenario-type breakdown laat zien dat de tissue sommige genormaliseerde acties bereikt (`execute`, `query`, `retry`, `assertive`), maar `cautious` blijft onbereikbaar in het huidige decoder-contract en `explore` wordt in de traced benchmark runs niet geobserveerd. De nieuwe diagnostics classificeren de resterende hoofdoorzaak als `network_never_reaches_expected_actions`, niet langer als globale `action_vocabulary_mismatch`.

De confidence is lager dan in het oude 0%-rapport maar nog steeds niet bewezen gekalibreerd: gemiddeld 0.509429 bij random-equivalente accuracy. Confidence mag daarom nog niet als operationeel beslissingssignaal worden gebruikt.

## 5. Limitaties

- De benchmark gebruikt mock agent scenarios. Dat maakt de test reproduceerbaar en veilig, maar het blijft een vereenvoudiging van echte agent-interactie.
- De adapter is een scoring-normalisatie, geen training of echte policy-verbetering.
- De mapping `ESCALATE -> assertive` en het ontbreken van `cautious` zijn architecturale keuzes die later scherper gevalideerd moeten worden.
- De baselines zijn bewust eenvoudig. Equal-to-random is nog steeds onvoldoende voor een agentbeslisser.
- De approximate p-values zijn bedoeld als pragmatische regressie-/triage-indicator, niet als definitief wetenschappelijk bewijs.
- De benchmark meet vooral discrete actiecorrectheid. Andere eigenschappen zoals interpretability, robustness, lange-termijn adaptatie of multimodale perceptie zijn niet bewezen door deze meting.

## 6. Aanbevelingen voor v0.2.0

1. Behandel de action-contract adapter als noodzakelijke regressielaag.
   - Bewaak dat decoded runtime labels altijd expliciet naar benchmarklabels worden genormaliseerd.
   - Laat regression tests falen als `execute`, `query`, `retry`, `explore` of `assertive` opnieuw onbereikbaar worden.

2. Los de resterende action coverage gap op.
   - Beslis of `cautious` een echte decoder-output moet worden of uit de benchmark-vocabulaire moet verdwijnen.
   - Onderzoek waarom `explore` wel in de decoder/adapter bestaat maar niet in de 700 traced runs voorkomt.

3. Verbeter de policy vóór extra features.
   - Kies één scenario-slice, bijvoorbeeld `missing_params_tool_call`, en verbeter gericht totdat Neuraxon daar betrouwbaar beter dan random scoort.
   - Gebruik daarna pas de volledige scenario-set als regressiebenchmark.

4. Kalibreer confidence tegen correctheid.
   - Confidence mag niet hoog blijven bij baseline-achtig of fout gedrag.
   - Voeg tests toe die confidence/accuracy-correlatie bewaken.

5. Stel memory persistence uit.
   - Memory persistence uitstellen blijft voorlopig de juiste keuze; het is niet de juiste volgende investering.
   - Zolang de tissue geen nuttige beslissingen boven random/always-execute produceert, is het opslaan van memory/state weinig relevant en kan het zelfs fout gedrag duurzamer maken; eerst moet de basisbeslisser werken.
   - Pak persistence pas opnieuw op wanneer Neuraxon aantoonbaar nuttige beslissingen maakt in een kleine, stabiele benchmark-slice.

6. Houd visual/multimodal research los van de kernbeslisser.
   - Visual Perception Layer-onderzoek blijft interessant, maar mag de basisvraag niet maskeren: kan de huidige tissue een eenvoudige agentactie beter kiezen dan baseline?

## Go/No-Go beslissing

NO-GO: de huidige Neuraxon tissue is nog niet productie-waardig als beslislaag voor CLI agents.

Minimale voorwaarden voor een latere Go:

- Accuracy > random baseline op de volledige benchmark.
- Accuracy > always-execute baseline op de volledige benchmark of op een expliciet afgebakende scenario-subset.
- `cautious`/`explore` coverage is verklaard en bewust ontworpen.
- Confidence correleert positief met correctheid.
- Learning curve toont verbetering binnen of tussen runs.
- Regressietests voorkomen terugval naar action-contract mismatch of 0.00% accuracy.

Tot die voorwaarden gehaald zijn, moet de tissue worden behandeld als experimenteel onderzoekscomponent, niet als operationele agent policy.
