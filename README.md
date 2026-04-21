# neuraxon-agent

Intelligence Tissue for CLI AI Agents, powered by [Neuraxon](https://github.com/DavidVivancos/Neuraxon) v2.0.

## Wat is dit?

`neuraxon-agent` is een agent-integratielaag rond Neuraxon v2.0 — een bio-geinspireerd neuraal netwerk met trinaire toestanden, continue tijd, en 4 neuromodulatoren. Dit project maakt het mogelijk om Neuraxon als "intelligentie weefsel" te gebruiken voor CLI AI agents zoals Hermes.

## Architectuur

```
AgentTissue (wrapper)
  ├── PerceptionEncoder    → zet observaties om naar trinaire input
  ├── NeuraxonNetwork      → het bio-neurale netwerk
  ├── ActionDecoder        → zet output om naar agent acties
  ├── ModulationFeedback   → dopamine/serotonine feedback loop
  ├── TissueMemory         → pattern storage en recall
  ├── AgentEvolution       → Aigarth evolutionaire training
  └── StreamingLoop        → real-time simulatie loop
```

## Snel starten

```bash
# Installeren
pip install -e ".[dev]"

# CLI gebruiken
neuraxon-agent think -i observation.json -o action.json
neuraxon-agent modulate -i outcome.json -o result.json
neuraxon-agent evolve -g 5 -o summary.json

# Python API
from neuraxon_agent import AgentTissue

tissue = AgentTissue()
tissue.observe({"type": "prompt", "content": "hello"})
action = tissue.think(steps=10)
print(action.actie_type, action.confidence)
tissue.modulate("success")
```

## Projectstructuur

| Module | Functie |
|--------|---------|
| `perception.py` | Observaties → trinaire input encoding |
| `action.py` | Trinaire output → agent acties |
| `tissue.py` | NeuraxonNetwork wrapper |
| `modulation.py` | Neuromodulator feedback loop |
| `memory.py` | Pattern storage en recall |
| `evolution.py` | Aigarth evolutionaire training |
| `streaming.py` | Real-time simulatie loop |
| `cli.py` | JSON CLI interface |
| `vendor/` | Neuraxon v2.0 upstream code |

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

## Status

Dit project is in actieve ontwikkeling. Zie de [GitHub issues](https://github.com/sisutuulenisa/neuraxon-hybrid/issues) voor de roadmap.
