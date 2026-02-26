# API compatibility: Neuraxon v1 (`neuraxon.py`) vs v2 (`neuraxon2.py`)

Status snapshot: 2026-02-26 (bron: `upstream/Neuraxon` in deze workspace).

## 1) Publiek API-contract (high level)

| Onderdeel | v1 (`neuraxon.py`) | v2 (`neuraxon2.py`) | Compatibiliteit |
|---|---|---|---|
| Kernklassen | `NetworkParameters`, `Neuraxon`, `Synapse`, `NeuraxonNetwork` | Zelfde kernnamen + extra subsystemen (`NeuromodulatorSystem`, `OscillatorBank`, `MSTHState`, `NeuraxonApplication`, `NeuraxonAigarthHybrid`) | Deels compatibel (v2 is superset qua concepten, niet 1-op-1 qua gedrag) |
| Netwerk API | `simulate_step`, `set_input_states`, `get_output_states`, `modulate`, `to_dict` | Zelfde + `get_all_states`, `get_energy` | Bestaande v1-calls blijven grotendeels mogelijk |
| Save/load API | `save_network`, `load_network` | Zelfde functienamen | Bestandsformaat niet volledig symmetrisch |
| Testdekking upstream | `tests/test_neuraxon.py` target v1 module | Geen aparte v2 testfile in upstream | Integratierisico voor v2 hoger |

## 2) Concreet contractverschil

### 2.1 `NetworkParameters` is niet schema-compatibel
- v1 gebruikt o.a. `connection_probability`.
- v2 vervangt netwerkopbouw met small-world settings (`ws_k`, `ws_beta`) en veel extra parameters (DSN/CTSN/AGMP/MSTH, etc.).
- Gevolg: code die v1-parameterdict blind doorgeeft aan v2 kan op `TypeError` stuklopen (onbekende keys), en omgekeerd.

### 2.2 `Synapse` constructor is breaking voor directe aanroepen
- v1: `Synapse(pre_id, post_id, params)`.
- v2: `Synapse(pre_id, post_id, branch_id, params)`.
- Gevolg: integraties die direct `Synapse(...)` instantieren moeten worden aangepast.

### 2.3 Neuromodulatie semantiek verschilt
- v1: simpele globale dict met decay naar baseline; `modulate(name, level)` zet direct waarde (clamp 0..1).
- v2: intern tonic/phasic model + receptoractivatie + crosstalk; `modulate` zet tonic-level, totale effectieve waarde ontstaat dynamisch.
- Gevolg: dezelfde `modulate` call geeft niet hetzelfde dynamische effect.

### 2.4 Simulatiegedrag voor inputneuronen verschilt
- v1: alle actieve neuronen worden in `simulate_step` via `update(...)` verwerkt.
- v2: inputneuronen worden expliciet niet door de ODE geüpdatet (set state blijft vast tenzij externe input).
- Gevolg: input-driven scenario’s kunnen ander tijdgedrag en andere outputpatronen geven.

### 2.5 Serialisatie is slechts deels compatibel
- v2 JSON bevat extra velden (`version`, `neuromodulator_system`, `oscillators`, `energy_usage`, extra neuron/synapse state).
- v1 loader verwacht v1-parameterschema; v2-save inlezen met v1 is risicovol/niet gegarandeerd.
- v2 loader vult defaults voor missende velden; v1-save inlezen in v2 is kansrijker.

## 3) Gedragsverschillen relevant voor integratie

1. Topologie: v1 gebruikt probabilistische verbindingen, v2 small-world opbouw met dendritische branches.
2. Complexiteit: v2 bevat meerdere regel-lussen (MSTH/DSN/CTSN/AGMP/Chrono), daardoor meer state en hogere variantie.
3. Observability: v2 biedt extra inspectie (`get_all_states`, `get_energy`) en rijker model-state in JSON.
4. Reproduceerbaarheid: beide versies gebruiken `random`; zonder expliciete seed-control zijn runs niet deterministisch.

## 4) Integratierisico's

1. `HIGH`: parameter- en constructor mismatch (runtime breaks bij directe API-aanroepen).
2. `MEDIUM`: outputgedrag verandert ondanks gelijkluidende methode-namen (`simulate_step`, `modulate`).
3. `MEDIUM`: serialisatie niet veilig round-trip v2 -> v1.
4. `MEDIUM`: upstream tests dekken vooral v1; v2 regressies kunnen onopgemerkt blijven.

## 5) Migratierichtlijn (wanneer v1 of v2 gebruiken)

Gebruik **v1** wanneer:
- je een stabiele, eenvoudige baseline nodig hebt;
- je wilt aansluiten op bestaande upstream testverwachtingen;
- je integratie minimaal moet zijn en gedrag voorspelbaar moet blijven.

Gebruik **v2** wanneer:
- je expliciet geavanceerde dynamiek nodig hebt (homeostase/chrono/astrocyte/energy);
- je bereid bent extra validatie en tuning te doen;
- je v2 als R&D-engine inzet en niet als drop-in vervanger van v1 behandelt.

Aanpak voor migratie v1 -> v2:
1. Zet een dunne adapterlaag voor een stabiel intern contract (`set_input_states`, `simulate_step`, `get_output_states`, `modulate`).
2. Migreer parameterbeheer via expliciete mapping i.p.v. blind `**kwargs` hergebruik.
3. Scheid model-artifacts per versie (geen v2-save terugladen met v1).
4. Vergelijk v1 vs v2 op dezelfde seed/use-case met run-matrix voordat je v2 als default kiest.
