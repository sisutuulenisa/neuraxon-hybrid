# RESEARCH_FRONTIER_001 - Externe evaluatie- en integratiekansen (bounded)

**Datum:** 2026-02-26  
**Context in deze repo (huidige stand):**
- `scripts/run_matrix.py` logt nu run-level basisvelden + beperkte metrics (`runtime_sec`, `steps`, `score_main`, `drift_recovery_t90`, `forgetting_delta`).
- `scripts/summarize_claims.py` aggregeert nu alleen `total/ok/error`.
- `docs/CLAIM_EVAL_002.md` toont dat claim 1 = FAIL en claim 2/3 = INCONCLUSIVE door ontbrekende protocolmetrics.

Doel van deze frontier-notitie: pragmatische kansen die direct de evidence-gap verkleinen zonder scope-creep buiten dit repo.

## 1) Kans: End-to-end observability via OpenTelemetry (OTLP)

**Waarom nu relevant**
- Jullie hebben al meerdere scripts/artefacten, maar nog geen uniforme trace-keten over benchmark-run -> claim-eval -> wrapper.
- OpenTelemetry beschrijft 3 kernsignalen (traces, metrics, logs) plus context-koppeling, wat precies de ontbrekende auditability voor regressies/claimdiscussies oplost.

**Impact:** Hoog  
**Implementatiekost:** Laag-Middel (1-2 dagen pilot)  
**Risico:** Laag-Middel  
- Risico op metric-cardinality en extra overhead als alle seed-level details als labels worden meegestuurd.
- Mitigatie: begin met beperkte attributenset (`use_case`, `variant`, `seed`, `status`, `claim_id`) en sampling.

**Voorstel 1-2 volgende experimentele taken**
1. Voeg OTel-instrumentatie toe aan `scripts/run_matrix.py` en `scripts/poc_wrapper.py` (trace/span + minimale counters + error-events), met OTLP-endpoint via env var.
2. Draai 1 matrix-run met lokale collector en verifieer dat iedere `run_id` correleert met een trace-id in outputmetadata.

## 2) Kans: Strakke experiment tracking en artifact lineage met MLflow

**Waarom nu relevant**
- Jullie zitten nog in CSV-gebaseerde rapportage; vergelijkingen over iteraties worden daardoor snel fragiel.
- MLflow Tracking ondersteunt run logging van params/metrics/artifacts; dit sluit direct aan op jullie matrix-setup.

**Impact:** Hoog  
**Implementatiekost:** Middel (2-3 dagen)  
**Risico:** Middel  
- Extra operationele laag (tracking backend/artifact store), plus discipline nodig in run-taxonomie.
- Mitigatie: start lokaal (`mlruns`), migreer pas later naar server als de taxonomie stabiel is.

**Voorstel 1-2 volgende experimentele taken**
1. Maak een parent-run per matrix-executie en child-runs per `(use_case, variant, seed)`; log raw CSV en samenvattingen als artifacts.
2. Definieer vaste MLflow-tags (`protocol_version`, `claim_eval_version`, `git_commit`) en maak 1 vergelijkingsquery voor "beste baseline vs neuraxon_full".

## 3) Kans: Geautomatiseerde claim-gates met MLflow evaluatie/validatie API

**Waarom nu relevant**
- De huidige claimbeslissing gebeurt document-first; automatische drempelbewaking ontbreekt nog.
- MLflow heeft een evaluation + validation pad (`mlflow.models.evaluate` en `mlflow.validate_evaluation_results`) waarmee thresholds hard afgedwongen kunnen worden.

**Impact:** Middel-Hoog  
**Implementatiekost:** Middel (1-2 dagen bovenop kans 2)  
**Risico:** Middel  
- Risico dat protocolmetrics niet 1-op-1 passen op standaard evaluators.
- Mitigatie: custom metrics gebruiken voor `T90`, `F`, `SV`, `R95`, `eff` en alleen gate op metrics die echt aanwezig zijn.

**Voorstel 1-2 volgende experimentele taken**
1. Bouw een `scripts/claim_gate.py` dat threshold-validatie uitvoert en een machine-readable PASS/FAIL JSON schrijft.
2. Veranker de gate in een lokale CI-stap: fail de run wanneer een claimdrempel expliciet wordt gemist.

## 4) Kans: Externe benchmarkkalibratie met OpenML suites + driftchecks (Evidently/River)

**Waarom nu relevant**
- Huidige evidence komt uit synthetische use-cases; dat verhoogt het risico op benchmark-overfit.
- OpenML benchmark suites bieden gestandaardiseerde tasks/splits en API-toegang.
- Evidently en River versnellen driftdiagnostiek (data/prediction drift + online concept-drift detectie zoals ADWIN) om protocolgaten concreet te vullen.

**Impact:** Middel-Hoog  
**Implementatiekost:** Middel-Hoog (3-5 dagen voor mini-pilot)  
**Risico:** Middel  
- Hogere compute- en data-prep-kost; drempelinstellingen voor driftdetectors kunnen foutpositieven geven.
- Mitigatie: start klein (3 OpenML-taken), fixeer seeds/budgets, en rapporteer detector-parameters expliciet.

**Voorstel 1-2 volgende experimentele taken**
1. Voeg `scripts/run_openml_subset.py` toe (3 OpenML-CC18 classificatietaken) met dezelfde varianten en budgetpolitiek als fase 2.
2. Voeg per taak een drift-rapport toe (`evidently` report + ADWIN events) en map dit naar protocolvelden (`collapse_rate`, `recovery_steps` proxy, stabiliteitssignalen).

## Aanbevolen volgorde (bounded uitvoering)
1. Kans 1 (OTel pilot)
2. Kans 2 + 3 samen (MLflow tracking + claim gate)
3. Kans 4 als beperkte kalibratieronde (3 taken, geen brede suite)

## Bronnen (officiele docs/public)
- OpenTelemetry Signals: https://opentelemetry.io/docs/concepts/signals/
- OpenTelemetry OTLP spec: https://opentelemetry.io/docs/specs/otlp/
- MLflow Tracking: https://mlflow.org/docs/latest/ml/tracking/
- MLflow Model Evaluation: https://mlflow.org/docs/latest/ml/evaluation/
- Evidently Data/ML checks quickstart: https://docs.evidentlyai.com/quickstart_ml
- River ADWIN drift detector: https://riverml.xyz/dev/api/drift/ADWIN/
- OpenML benchmark suites: https://docs.openml.org/benchmark/
- W&B experiment tracking (referentie-optie): https://docs.wandb.ai/models/track
