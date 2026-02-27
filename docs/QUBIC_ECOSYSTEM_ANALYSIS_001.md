# QUBIC_ECOSYSTEM_ANALYSIS_001

**Datum:** 2026-02-27  
**Project:** neuraxon-hybrid  
**Scope:** Qubic GitHub-org deep-dive met focus op Neuraxon-claims, architectuur, tooling en operationele haalbaarheid.

---

## 0) Afbakening (coverage + exclusions)

### Coverage (wel gedaan)
1. **Org-brede inventaris** van repositories in `github.com/qubic` (actief + archived), incl. update-activiteit, stars, open issues, releases/tags.
2. **Diepte-analyse op Tier-1 kandidaten**:
   - `core`, `core-lite`, `Qiner`, `outsourced-computing`, `oracle-machine`, `docs`, `integration`, `qubic-http`, `qubic-cli`, `qubic-dev-kit`, `qct`.
3. **Documentatie/specificaties**:
   - `core/doc/protocol.md`, `core/doc/custom_mining.md`
   - Qubic docs-site bron (`docs/docs/learn/upow.md`, `learn/aigarth.md`, `overview/whitepaper.md`, `developers/oracles.md`, `overview/consensus.md`)
   - `outsourced-computing` docs/PoC
   - `qct/iterations/iteration-log.md`
4. **Koppeling naar intern evaluatiekader**:
   - `docs/CLAIM_MATRIX.md`
   - `docs/TEST_PROTOCOL_PHASE1_2.md`
   - `docs/CLAIM_EVAL_002.md`
   - `BENCHMARK_RESULTS.md`

### Exclusions (expliciet niet volledig)
- Geen volledige inhoudelijke review van **alle** PR-discussies/changelog-notes per release (te breed voor 67 repos).
- Geen end-to-end execution test op live Qubic-netwerk in deze stap (dit document is ecosystem-analyse, geen runtime-validatie).
- Geen bewijs dat Qubic-artefacten Neuraxon-claims automatisch bewijzen; alleen evidence dat Qubic technisch artefacten heeft die **kúnnen** worden gebruikt voor validatie.

---

## 1) Qubic asset-inventaris (Neuraxon-relevante snapshot)

## 1.1 Org-snapshot
- **Totaal repos:** 67
- **Actief:** 64
- **Archived:** 3 (`dapps-explorer`, `go-node-fetcher`, `quottery-frontend`)
- **Repos met Discussions:** 0 (op basis van GraphQL snapshot)

Release/activiteit-signalen:
- `core`: **155 releases**, laatste tag `v1.280.0`, open issues `85`
- `core-lite`: **11 releases**, laatste tag `E202.1-engine`
- `qubic-http`: **7 releases**, laatste tag `v0.9.1`
- `qubic-cli`: **3 releases**, laatste tag `v2026-02-11`
- `roadmap`: geen releases, wel **72 open issues** (roadmap lijkt issue-gedreven)

## 1.2 Tier-1 (direct Neuraxon/claim-relevant)

| Repo | Why Tier 1 | Open issues | Releases | Latest tag | Last push |
|---|---|---:|---:|---|---|
| `core` | Main node implementation; protocol/custom mining/oracle execution path | 85 | 155 | v1.280.0 | 2026-02-25 |
| `core-lite` | Lean node runtime + deployment path for operators | 0 | 11 | E202.1-engine | 2026-02-25 |
| `Qiner` | Reference AI miner with published ANN-based algorithms | 0 | 0 | - | 2026-01-22 |
| `outsourced-computing` | Design + PoC docs for custom mining/oracle compute offload | 0 | 0 | - | 2025-10-30 |
| `oracle-machine` | Running middleware for off-chain oracle bridge | 1 | 0 | - | 2026-02-11 |
| `docs` | UPoW/Aigarth/consensus documentation and whitepaper status | 2 | 0 | - | 2026-02-24 |
| `integration` | Network/API/RPC/operator integration docs | 23 | 0 | - | 2026-02-24 |
| `qubic-http` | HTTP API wrapper around node access | 3 | 7 | v0.9.1 | 2026-02-25 |
| `qubic-cli` | Operator and integration CLI | 2 | 3 | v2026-02-11 | 2026-02-20 |
| `qubic-dev-kit` | Developer tooling and local test environment | 0 | 0 | - | 2025-04-05 |
| `qct` | Iteration logs linking roadmap items to issues/PRs for mining/oracles | 1 | 0 | - | 2026-02-24 |

### Tier-1 kernbevindingen (evidence-based)
1. **UPoW/AI-mining is niet alleen marketingtekst; er is code + protocoloppervlak**
   - `core` bevat custom mining flow (`core/doc/custom_mining.md`) en protocoltypes voor oracle verkeer (`core/doc/protocol.md`).
   - `core/src/public_settings.h` bevat concrete mining-configs incl. `HYPERIDENTITY_*`, `ADDITION_*`, `NEURON_VALUE_LIMIT=1`.
   - `Qiner/README.md` documenteert ANN-mining algoritmes (hyperidentity + addition), met trit-representatie en scoring.
2. **Oracle-pad is functioneel uitgewerkt (brug naar externe compute/data)**
   - `oracle-machine/README.md` beschrijft query/reply protocol, cache, interface clients, deploy/run pad.
   - `outsourced-computing/oracle-machines/*` documenteert OM-architectuur en request lifecycle.
3. **Outsourced compute is aanwezig als ontwerp + PoC, maar nog geen hard benchmarkbewijs**
   - `outsourced-computing/README.md` + `monero-poc/README.md` tonen task/solution/validator flow.
   - Dit is nuttig voor opzet van onze UPOW-tests, maar bewijst niet automatisch schaal/KPI’s uit ons protocol.
4. **Roadmap/uitvoering is traceerbaar via issues/iteration logs**
   - `qct/iterations/iteration-log.md` linkt meerdere mining/oracle milestones aan concrete PRs/issues (core, oracle-machine, qubic-cli, qlogging).

## 1.3 Tier-2 (ondersteunend infra/tooling)
Ondersteunende repos voor operationele haalbaarheid (SDK’s, node connectors, archivers, streams, libraries, governance repos):
- Voorbeelden: `go-node-connector`, `go-qubic`, `go-qubic-nodes`, `go-archiver*`, `go-data-publisher`, `network-guardians`, `qubic-aggregation`, `qubic-stats-service`, `Qubic.NET*`, `ts-library*`, `qlogging`, `core-docker`, `proposal`, `roadmap`, etc.
- Relevantie voor Neuraxon: vooral **enablement** (observability, ingest, connectoren, operator tooling), niet direct claim-bewijs.

## 1.4 Tier-3 (laag signaal / niet-prioritair voor Neuraxon)
Voornamelijk frontends/apps/community-assets met lage directe bijdrage aan Neuraxon-claimvalidatie:
- `.github`, `dapps-explorer`, `explorer-frontend`, `grants`, `proposals-frontend`, `qubic-hackathon`, `qubic-mm-snap`, `qx-frontend`, `react-ui`, `voting-frontend`, `wallet*`, `wiki`, etc.

> Volledige repo-indeling (alle 67) staat onderaan in **Appendix A**.

---

## 2) Relevance triage (samenvatting)

- **Tier 1 (11 repos):** direct bruikbaar voor UPOW/AI-mining architectuur, oracle-brug en operationele integratiepad.
- **Tier 2 (41 repos):** noodzakelijke randinfrastructuur voor productie-achtige tests en observability.
- **Tier 3 (15 repos):** laag signaal voor huidige Neuraxon-claimtoetsing.

Pragmatisch: voor onze volgende iteratie moeten we vooral op **Tier 1 + selecte Tier 2** inzetten.

---

## 3) Koppeling aan intern evaluatiekader

## 3.1 Mapping naar `docs/CLAIM_MATRIX.md`

### Claim: Useful Proof of Work levert schaalbare compute voor Neuraxon-simulaties
- **Wat wordt sterker:**
  - Er is aantoonbaar Qubic-ecosysteemmateriaal (code/docs/tooling) dat een UPOW-achtig pad technisch ondersteunt.
  - Niet alleen high-level claims; er zijn concrete componenten (`core`, `Qiner`, `oracle-machine`, `outsourced-computing`, `qubic-http`, `qubic-cli`).
- **Wat blijft onbewezen:**
  - Onze protocoldrempels (`eff`, success-rate, inter-node drift, kost/1M steps) zijn nog niet gemeten in onze setup.
- **Status:** blijft **INCONCLUSIVE** (consistent met `docs/CLAIM_EVAL_002.md`).

### Claims rond trinaire states / adaptiviteit / SOC / dual-weight
- Qubic bevat ANN/trit-gerelateerde mechanismen (m.n. `Qiner` + `core` custom mining).
- Maar dit is **geen direct bewijs** voor Neuraxon-claims over `w_fast/w_slow`, homeostasis, small-world, neuromodulatie, SOC-passcriteria.
- **Status voor deze claims:** ongewijzigd (onbevestigd / inconclusive / fail waar reeds vastgesteld).

## 3.2 Mapping naar `docs/TEST_PROTOCOL_PHASE1_2.md`
Qubic-analyse levert vooral input voor Claim-test 3 (UPOW):
- Candidate stack voor implementatie van 1→4 worker test:
  - node/core pad (`core` / evt. `core-lite`)
  - interface/adapter (`qubic-http`, `qubic-cli`)
  - oracle/external compute brug (`oracle-machine`, `outsourced-computing`)
- Ontbrekende metingen blijven exact dezelfde als in protocol:
  - `throughput_steps_sec`, worker-schaal-efficiëntie
  - distributed success-rate
  - inter-node afwijking
  - kost per 1M steps

## 3.3 Mapping naar gaps uit `docs/CLAIM_EVAL_002.md` en `BENCHMARK_RESULTS.md`
- Deze analyse **vult geen metric-gap** op (nog geen nieuwe benchmarkruns).
- Wel verkleint ze de **implementatie-onzekerheid**: we hebben nu een concreter technisch pad en componentkeuze om de ontbrekende UPOW-metrics te gaan meten.

---

## 4) Impact op evidence-score

Ik splits hier tussen **ecosysteem-evidence** en **onze experimentele claim-evidence**.

| Domein | Voor | Na | Toelichting |
|---|---:|---:|---|
| UPOW ecosysteem-haalbaarheid (bestaan van implementeerbare bouwstenen) | 2/5 | 3/5 | Door concrete code/docs/tooling in Tier 1, niet enkel narratief. |
| UPOW claim-bewijs in onze setup (protocol PASS/FAIL) | 1/5 | 1/5 | Geen nieuwe metingen; nog steeds INCONCLUSIVE. |
| Neuraxon-specifieke claims buiten UPOW (dual-weight, SOC, etc.) | ongewijzigd | ongewijzigd | Qubic-data is hier hoogstens indirect/contextueel. |

**Netto:** betere operationele zekerheid over *hoe* we UPOW kunnen testen, maar geen nieuwe claim-PASS.

---

## 5) Welke claims worden sterker / zwakker / blijven onbewezen?

## Sterker
1. **"Er bestaat een technisch Qubic-pad voor useful compute / AI-mining integratie"**  
   Sterker door combinatie van `core` + `Qiner` + `oracle-machine` + `outsourced-computing` + integratietooling.

## Zwakker (of strenger geïnterpreteerd)
1. **Narratief dat whitepaper-level claims al finale specificatie zijn**  
   `docs/docs/overview/whitepaper.md` zegt expliciet dat de whitepaper pas na voltooiing komt; huidige referentie is vooral code/documentatie-in-evolutie.

## Blijven onbewezen
1. **UPOW-schaalclaim in ónze Neuraxon setup** (efficiency/success-rate/repro/kost)  
2. **Neuraxon dual-weight/SOC/homeostasis/small-world/meta claims** door Qubic alleen.

---

## 6) Top 5 vervolgacties (effort/impact)

| # | Actie | Effort | Impact | Waarom nu |
|---|---|---|---|---|
| 1 | Bouw `scripts/qubic_upow_probe.py` die 1/2/4 worker-runs orchestreert via `qubic-http`/`qubic-cli` en per run `throughput_steps_sec`, success, node-id logt | M | Hoog | Directe input voor protocol claim 3 drempels |
| 2 | Voeg verplichte UPOW-velden toe aan raw benchmark schema (`worker_count`, `node_id`, `throughput_steps_sec`, `cost_per_1m_steps`) + validator in CI | S-M | Hoog | Sluit huidige INCONCLUSIVE-gap hard af |
| 3 | Maak minimale OM-adapter PoC (query/reply pad) als fault-tolerance testcase (timeouts/retries) | M | Midden-Hoog | Meet distributed robustheid i.p.v. alleen lokale runs |
| 4 | Definieer reproducibility harness: zelfde job op >=2 nodes, afwijkingsrapport (`inter_node_delta_pct`) | M | Hoog | Nodig voor protocol-eis `<=10%` afwijking |
| 5 | Formaliseer claim-gate in `summarize_claims.py`: automatische PASS/FAIL voor claim 3 incl. drempelreden | S | Hoog | Voorkomt narratieve interpretatie, versnelt besluitvorming |

---

## 7) Bronnenlijst (klikbare links)

### Org/repo metadata
- <https://github.com/qubic>
- GraphQL snapshot (lokaal): `data/qubic_org_repos_graphql_2026-02-27.json`
- Repo inventory (lokaal): `data/qubic_repo_inventory_2026-02-27.tsv`

### Tier-1 kernrepos
- <https://github.com/qubic/core>
- <https://github.com/qubic/core-lite>
- <https://github.com/qubic/Qiner>
- <https://github.com/qubic/outsourced-computing>
- <https://github.com/qubic/oracle-machine>
- <https://github.com/qubic/docs>
- <https://github.com/qubic/integration>
- <https://github.com/qubic/qubic-http>
- <https://github.com/qubic/qubic-cli>
- <https://github.com/qubic/qubic-dev-kit>
- <https://github.com/qubic/qct>

### Spec/docs/whitepaper pages gebruikt in analyse
- <https://github.com/qubic/core/blob/main/doc/protocol.md>
- <https://github.com/qubic/core/blob/main/doc/custom_mining.md>
- <https://github.com/qubic/Qiner/blob/main/README.md>
- <https://github.com/qubic/outsourced-computing/blob/main/README.md>
- <https://github.com/qubic/outsourced-computing/blob/main/monero-poc/README.md>
- <https://github.com/qubic/outsourced-computing/tree/main/oracle-machines>
- <https://github.com/qubic/oracle-machine/blob/main/README.md>
- <https://github.com/qubic/docs/blob/main/docs/learn/upow.md>
- <https://github.com/qubic/docs/blob/main/docs/learn/aigarth.md>
- <https://github.com/qubic/docs/blob/main/docs/overview/whitepaper.md>
- <https://github.com/qubic/docs/blob/main/docs/developers/oracles.md>
- <https://github.com/qubic/docs/blob/main/docs/overview/consensus.md>
- <https://github.com/qubic/qct/blob/main/iterations/iteration-log.md>

### Interne Neuraxon-kaderbronnen
- `docs/CLAIM_MATRIX.md`
- `docs/TEST_PROTOCOL_PHASE1_2.md`
- `docs/CLAIM_EVAL_002.md`
- `BENCHMARK_RESULTS.md`

### Aanvullende publieke signalen (ingest 2026-02-27)
- <https://qubic.org/blog-detail/qubic-all-hands-recap-february-19-2026>
- <https://www.linkedin.com/posts/qubicnetwork_neuraxon-activity-7403826652805455873-_5mc>
- <https://www.openpr.com/news/4397966/beyond-binary-qubic-s-neuraxon-2-0-introduces-a-trinary>
- <https://huggingface.co/DavidVivancos/activity/posts>

**Interpretatie van deze extra bronnen:**
- Ze versterken vooral het publieke narratief en de operationele signalen (recente HF-activiteit/running spaces).
- Ze leveren geen onafhankelijke benchmarkresultaten of protocolmetriek die onze claimstatus wijzigt.
- Daarom blijft de formele claim-impact ongewijzigd: dual-weight **FAIL**, SOC **INCONCLUSIVE**, UPOW **INCONCLUSIVE**.

---

## Appendix A — Volledige repo-triage (alle 67)

| Repo | Tier | Archived | Stars | Last push |
|---|---|---:|---:|---|
| `.github` | Tier 3 | no | 0 | 2025-12-09 |
| `Qiner` | Tier 1 | no | 16 | 2026-01-22 |
| `Qubic.NET` | Tier 2 | no | 5 | 2026-02-26 |
| `Qubic.NET.Toolkit` | Tier 2 | no | 0 | 2026-02-22 |
| `Qubic.NET.Wallet` | Tier 2 | no | 1 | 2026-02-26 |
| `Qubic.NET.Wallet.Mobile` | Tier 2 | no | 0 | 2026-02-26 |
| `archive-query-service` | Tier 2 | no | 0 | 2026-02-26 |
| `archiver-db-migrator` | Tier 2 | no | 0 | 2025-12-09 |
| `core` | Tier 1 | no | 162 | 2026-02-25 |
| `core-bob` | Tier 2 | no | 4 | 2026-02-27 |
| `core-docker` | Tier 2 | no | 1 | 2025-04-10 |
| `core-lite` | Tier 1 | no | 0 | 2026-02-25 |
| `dapps-explorer` | Tier 3 | yes | 0 | 2026-02-12 |
| `docs` | Tier 1 | no | 8 | 2026-02-24 |
| `explorer-frontend` | Tier 3 | no | 12 | 2026-02-27 |
| `go-archiver` | Tier 2 | no | 2 | 2025-12-01 |
| `go-archiver-v2` | Tier 2 | no | 0 | 2026-01-21 |
| `go-data-publisher` | Tier 2 | no | 0 | 2026-02-25 |
| `go-events` | Tier 2 | no | 0 | 2026-02-12 |
| `go-events-consumer` | Tier 2 | no | 0 | 2025-04-24 |
| `go-events-publisher` | Tier 2 | no | 0 | 2025-04-30 |
| `go-log-data-publisher` | Tier 2 | no | 0 | 2026-02-26 |
| `go-node-connector` | Tier 2 | no | 4 | 2026-02-23 |
| `go-node-fetcher` | Tier 2 | yes | 1 | 2024-09-17 |
| `go-qubic` | Tier 2 | no | 1 | 2026-02-11 |
| `go-qubic-nodes` | Tier 2 | no | 3 | 2025-10-21 |
| `go-schnorrq` | Tier 2 | no | 1 | 2024-10-11 |
| `go-transactions-consumer` | Tier 2 | no | 0 | 2025-04-28 |
| `go-transfers` | Tier 2 | no | 0 | 2025-10-22 |
| `grants` | Tier 3 | no | 2 | 2024-12-24 |
| `integration` | Tier 1 | no | 4 | 2026-02-24 |
| `java-archiver-proto` | Tier 2 | no | 0 | 2024-09-13 |
| `kafka-streams-services` | Tier 2 | no | 0 | 2026-02-25 |
| `license` | Tier 2 | no | 0 | 2023-10-22 |
| `live-websocket` | Tier 2 | no | 0 | 2024-10-08 |
| `network-guardians` | Tier 2 | no | 6 | 2026-02-21 |
| `oracle-machine` | Tier 1 | no | 3 | 2026-02-11 |
| `org.qubic.proposal` | Tier 2 | no | 0 | 2024-10-30 |
| `outsourced-computing` | Tier 1 | no | 5 | 2025-10-30 |
| `proposal` | Tier 2 | no | 11 | 2026-02-27 |
| `proposals-frontend` | Tier 3 | no | 0 | 2025-09-10 |
| `qct` | Tier 1 | no | 1 | 2026-02-24 |
| `qlogging` | Tier 2 | no | 0 | 2026-02-11 |
| `qubic-aggregation` | Tier 2 | no | 0 | 2026-02-25 |
| `qubic-cli` | Tier 1 | no | 47 | 2026-02-20 |
| `qubic-csharp` | Tier 2 | no | 2 | 2026-02-01 |
| `qubic-dev-kit` | Tier 1 | no | 9 | 2025-04-05 |
| `qubic-hackathon` | Tier 3 | no | 11 | 2025-08-01 |
| `qubic-http` | Tier 1 | no | 3 | 2026-02-25 |
| `qubic-mm-snap` | Tier 3 | no | 3 | 2025-02-12 |
| `qubic-stats-service` | Tier 2 | no | 1 | 2026-01-26 |
| `qubic-transfer-watcher` | Tier 2 | no | 1 | 2026-02-19 |
| `quottery-frontend` | Tier 3 | yes | 2 | 2025-12-13 |
| `qx-frontend` | Tier 3 | no | 0 | 2025-11-03 |
| `qx-service` | Tier 2 | no | 0 | 2026-02-17 |
| `react-ui` | Tier 3 | no | 0 | 2025-02-12 |
| `roadmap` | Tier 2 | no | 0 | 2025-01-24 |
| `static` | Tier 2 | no | 2 | 2026-02-25 |
| `ts-library` | Tier 2 | no | 10 | 2025-04-30 |
| `ts-library-wrapper` | Tier 2 | no | 0 | 2025-11-12 |
| `ts-types` | Tier 2 | no | 0 | 2024-07-08 |
| `ts-vault-library` | Tier 2 | no | 0 | 2024-07-11 |
| `voting-frontend` | Tier 3 | no | 1 | 2026-02-07 |
| `wallet` | Tier 3 | no | 9 | 2026-02-24 |
| `wallet-app` | Tier 3 | no | 8 | 2026-02-27 |
| `wallet-app-dapp` | Tier 3 | no | 0 | 2025-11-25 |
| `wiki` | Tier 3 | no | 0 | 2025-01-16 |
