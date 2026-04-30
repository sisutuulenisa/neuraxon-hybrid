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

## Roadmap gate

Current phase: benchmark the decision layer before expanding input/state complexity.
The current benchmark report shows useful semantic routing and an explicit
`temporal_context_bridge`, but raw Neuraxon dynamics have not yet demonstrated a
learned policy that generalizes meaningfully above baselines. The near-term
blockers and prerequisite evidence are tracked in:

- #51 — expanded temporal benchmark beyond the original smoke probe.
- #52 — policy-ablation separating semantic-bridge behavior from raw-network behavior.
- #53 — temporal state carry-over into action decisions.
- #54 — criticality and neuromodulator dynamics instrumentation.
- #55 — this roadmap gate and documentation/linking pass.

Minimum evidence before deferred work resumes:

- Memory persistence remains deferred until temporal benchmark performance is
  meaningfully above baselines and the useful behavior survives raw/adapter
  separation, so persisted state would preserve real decision value rather than
  semantic routing artifacts.
- Visual perception remains deferred until the base decision layer generalizes
  beyond hand-authored semantic routing. Additional screenshots, DOM grids, or
  multi-sphere visual inputs should not be added before the core policy can make
  useful non-visual decisions under temporal/stateful evaluation.
