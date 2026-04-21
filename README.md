# Neuraxon Agent

Agent integration layer for the Neuraxon upstream library. This package provides a modular substrate for building adaptive agents around the core Neuraxon tissue model.

## Project goal

Neuraxon Agent wraps the upstream Neuraxon codebase in a clean, testable Python package focused on:

- **Tissue** — structural connective substrate
- **Perception** — sensory input processing
- **Action** — motor output and effector control
- **Modulation** — dynamic parameter adjustment and neuromodulator feedback
- **Memory** — episodic experience storage
- **Evolution** — adaptive learning hooks

## Neuromodulator Feedback Loop

Agent outcomes are translated into neuromodulator deltas that shape network
behaviour over time.

| Outcome | Dopamine | Serotonine | Acetylcholine | Norepinephrine |
|---------|----------|------------|---------------|----------------|
| success | +0.30    | +0.10      | +0.10         | +0.05          |
| failure | -0.10    | -0.20      | +0.20         | +0.30          |
| partial | +0.10    | -0.05      | +0.15         | +0.15          |
| timeout | -0.05    | -0.10      | +0.10         | +0.20          |

```python
from neuraxon_agent import AgentTissue

tissue = AgentTissue()
tissue.modulate("success")   # increases dopamine
tissue.modulate("failure")   # decreases serotonin

# Adaptive learning
metrics = tissue.feedback.convergence_metrics()
print(metrics["is_stable"])  # True when deltas stabilise
```

The mapping is fully configurable via `ModulationFeedback`, and an adaptive
layer tracks running means so the network can learn optimal modulation
strengths for its environment.

## Installation

```bash
# Clone with upstream submodule
git clone --recurse-submodules https://github.com/sisutuulenisa/neuraxon-hybrid.git
cd neuraxon-hybrid

# Install in editable mode
pip install -e ".[dev]"
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

## Quick start

```python
from neuraxon_agent import Tissue, Perception, Action, Memory

tissue = Tissue()
perception = Perception()
action = Action()
memory = Memory(capacity=100)

obs = perception.observe({"input": 42})
result = action.act({"type": "respond", "params": obs})
memory.store({"observation": obs, "action": result})
print(memory.recall(1))
```

See `examples/basic_agent_loop.py` for a full loop demonstration.

## Development

```bash
# Lint + format
ruff check src tests examples
ruff format --check src tests examples

# Type check
mypy src

# Run tests
pytest
```

## Project structure

```
neuraxon-hybrid/
├── src/neuraxon_agent/     # Main package
│   ├── __init__.py
│   ├── tissue.py
│   ├── perception.py
│   ├── action.py
│   ├── modulation.py
│   ├── memory.py
│   ├── evolution.py
│   └── vendor/             # Upstream dependency shim
│       ├── __init__.py
│       └── neuraxon2.py    # Fallback vendor copy
├── tests/                  # Test suite
├── examples/               # Usage examples
├── upstream/Neuraxon/      # Upstream source (git submodule)
├── scripts/                # Utility scripts
├── pyproject.toml
└── README.md
```

## Updating the upstream dependency

Neuraxon is tracked as a git submodule under `upstream/Neuraxon`.

**Fetch latest upstream version:**

```bash
# Pull latest upstream changes
cd upstream/Neuraxon
git pull origin main
cd ../..

# Update the bundled fallback copy
cp upstream/Neuraxon/neuraxon2.py src/neuraxon_agent/vendor/neuraxon2.py

# Commit the submodule pointer + fallback copy
git add upstream/Neuraxon src/neuraxon_agent/vendor/neuraxon2.py
git commit -m "vendor: update Neuraxon to latest upstream"
```

**Without submodule (fallback):**
If the submodule is not initialized, the vendor shim automatically falls back
to `src/neuraxon_agent/vendor/neuraxon2.py`. You can also replace that file
manually if needed.

## License

MIT
