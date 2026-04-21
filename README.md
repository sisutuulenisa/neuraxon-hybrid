# Neuraxon Agent

Agent integration layer for the Neuraxon upstream library. This package provides a modular substrate for building adaptive agents around the core Neuraxon tissue model.

## Project goal

Neuraxon Agent wraps the upstream Neuraxon codebase in a clean, testable Python package focused on:

- **Tissue** — structural connective substrate
- **Perception** — sensory input processing
- **Action** — motor output and effector control
- **Modulation** — dynamic parameter adjustment
- **Memory** — episodic experience storage
- **Evolution** — adaptive learning hooks

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
│   └── evolution.py
├── tests/                  # Test suite
├── examples/               # Usage examples
├── upstream/Neuraxon/      # Upstream source (submodule)
├── scripts/                # Utility scripts
├── pyproject.toml
└── README.md
```

## License

MIT
