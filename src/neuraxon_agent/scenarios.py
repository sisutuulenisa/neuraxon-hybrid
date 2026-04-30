"""Built-in benchmark scenario loading utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neuraxon_agent.benchmark import BenchmarkScenario

MOCK_AGENT_ACTIONS = {
    "execute",
    "query",
    "retry",
    "explore",
    "cautious",
    "assertive",
}

DEFAULT_MOCK_SCENARIO_PATH = (
    Path(__file__).resolve().parents[2] / "benchmarks" / "scenarios" / "mock_agent_scenarios.json"
)


def load_mock_agent_scenarios(path: str | Path | None = None) -> list[BenchmarkScenario]:
    """Load mock agent benchmark scenarios from JSON.

    The JSON file may contain either a top-level list or an object with a
    ``scenarios`` list. Each scenario must provide:

    - ``name``
    - ``scenario_type``
    - ``input_sequence``
    - ``expected_actions``
    - ``difficulty``
    """
    scenario_path = Path(path) if path is not None else DEFAULT_MOCK_SCENARIO_PATH
    payload = json.loads(scenario_path.read_text())
    raw_scenarios = payload.get("scenarios", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_scenarios, list):
        raise ValueError("scenario JSON must be a list or an object with a scenarios list")

    return [_scenario_from_dict(raw) for raw in raw_scenarios]


def _scenario_from_dict(raw: dict[str, Any]) -> BenchmarkScenario:
    """Convert one raw JSON scenario into a BenchmarkScenario."""
    expected_actions = tuple(str(action) for action in raw["expected_actions"])
    if not expected_actions:
        raise ValueError(f"scenario {raw.get('name', '<unnamed>')} has no expected_actions")

    unknown_actions = set(expected_actions) - MOCK_AGENT_ACTIONS
    if unknown_actions:
        raise ValueError(
            f"scenario {raw.get('name', '<unnamed>')} contains unknown actions: "
            f"{sorted(unknown_actions)}"
        )

    return BenchmarkScenario(
        name=str(raw["name"]),
        observation_sequence=list(raw["input_sequence"]),
        expected_optimal_action=expected_actions[-1],
        difficulty=float(raw["difficulty"]),
        scenario_type=str(raw["scenario_type"]),
        expected_actions=expected_actions,
    )
