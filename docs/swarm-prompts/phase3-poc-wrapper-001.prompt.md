Project: Neuraxon-hybrid (fase 3 POC wrapper)

Doel:
Maak een mini integratie-POC die laat zien hoe we Neuraxon als component kunnen aanroepen via JSON in/out.

Taken:
1) Voeg een eenvoudige wrapper toe:
- scripts/poc_wrapper.py
- CLI: --input <json> --out <json>
- Leest simpele input payload (bijv. use_case, variant, seed, params)
- Schrijft deterministische output-structuur met status, metadata en placeholder/result-veld

2) Voeg een voorbeeldflow toe:
- data/poc_input_example.json
- data/poc_output_example.json (gegenereerd)

3) Documenteer integratie:
- docs/POC_INTEGRATION_001.md
- Include: JSON contract, foutpaden, observability hooks (wat loggen), volgende stap naar echte adapter.

4) Update STATUS.md met korte POC-statusregel.

5) Commit + push op deze branch.

Constraints:
- Simpel en duidelijk.
- Geen extra zware dependencies.
- Geen merge naar main.
