"""JSON CLI interface for neuraxon-agent, compatible with Hermes tool-calling patterns."""
from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from neuraxon_agent.tissue import AgentTissue, TissueState
from neuraxon_agent.evolution import AgentEvolution, EvolutionConfig
from neuraxon_agent.vendor.neuraxon2 import NetworkParameters


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _save_json(path: str, data: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2))


def _encode_state(tissue: AgentTissue) -> str:
    """Serialize tissue state to base64-encoded JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp = f.name
    try:
        tissue.save(tmp)
        raw = Path(tmp).read_text()
        return base64.b64encode(raw.encode()).decode()
    finally:
        Path(tmp).unlink(missing_ok=True)


def _decode_state(b64: str, params: NetworkParameters | None = None) -> AgentTissue:
    """Deserialize tissue state from base64-encoded JSON."""
    raw = base64.b64decode(b64).decode()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(raw)
        tmp = f.name
    try:
        tissue = AgentTissue.load(tmp)
        return tissue
    finally:
        Path(tmp).unlink(missing_ok=True)


def _tissue_state_to_dict(state: TissueState) -> dict[str, Any]:
    return {
        "energy": state.energy,
        "activity": state.activity,
        "step_count": state.step_count,
        "dopamine": state.dopamine,
        "serotonin": state.serotonin,
        "acetylcholine": state.acetylcholine,
        "norepinephrine": state.norepinephrine,
        "num_neurons": state.num_neurons,
        "num_synapses": state.num_synapses,
    }


def cmd_think(args: argparse.Namespace) -> int:
    try:
        data = _load_json(args.input)
        params = NetworkParameters(**data.get("params", {}))
        tissue = AgentTissue(params)
        if "tissue_state" in data and data["tissue_state"]:
            tissue = _decode_state(data["tissue_state"], params)
        tissue.observe(data.get("observation", {}))
        action = tissue.think(steps=args.steps)
        result = {
            "action": action.actie_type.upper(),
            "confidence": action.confidence,
            "raw_output": action.raw_output,
            "tissue_state": _encode_state(tissue),
            "state": _tissue_state_to_dict(tissue.state),
        }
        _save_json(args.output, result)
        return 0
    except Exception as e:
        _save_json(args.output, {"error": str(e), "action": "ERROR", "confidence": 0.0})
        return 1


def cmd_modulate(args: argparse.Namespace) -> int:
    try:
        data = _load_json(args.input)
        params = NetworkParameters(**data.get("params", {}))
        tissue = AgentTissue(params)
        if "tissue_state" in data and data["tissue_state"]:
            tissue = _decode_state(data["tissue_state"], params)
        tissue.modulate(data.get("outcome", "partial"))
        result = {
            "tissue_state": _encode_state(tissue),
            "state": _tissue_state_to_dict(tissue.state),
        }
        _save_json(args.output, result)
        return 0
    except Exception as e:
        _save_json(args.output, {"error": str(e)})
        return 1


def cmd_evolve(args: argparse.Namespace) -> int:
    try:
        taskset = _load_json(args.taskset) if args.taskset else {}
        config = EvolutionConfig(
            seasons=args.generations,
            episodes_per_season=args.episodes or 10,
            seed=args.seed,
            task_scenarios=taskset.get("scenarios", []),
        )
        evo = AgentEvolution(config=config)
        summary = evo.evolve()
        _save_json(args.output, {"summary": summary})
        return 0
    except Exception as e:
        _save_json(args.output, {"error": str(e)})
        return 1


def cmd_save(args: argparse.Namespace) -> int:
    try:
        data = _load_json(args.input)
        params = NetworkParameters(**data.get("params", {}))
        tissue = AgentTissue(params)
        if "tissue_state" in data and data["tissue_state"]:
            tissue = _decode_state(data["tissue_state"], params)
        tissue.save(args.path)
        return 0
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1


def cmd_load(args: argparse.Namespace) -> int:
    try:
        tissue = AgentTissue.load(args.path)
        result = {
            "tissue_state": _encode_state(tissue),
            "state": _tissue_state_to_dict(tissue.state),
        }
        _save_json(args.output, result)
        return 0
    except Exception as e:
        _save_json(args.output, {"error": str(e)})
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="neuraxon-agent", description="Neuraxon Agent CLI")
    sub = parser.add_subparsers(dest="command")

    p_think = sub.add_parser("think", help="Observe and think")
    p_think.add_argument("--input", "-i", required=True, help="Observation JSON file")
    p_think.add_argument("--output", "-o", required=True, help="Action JSON file")
    p_think.add_argument("--steps", type=int, default=10, help="Simulation steps")
    p_think.set_defaults(func=cmd_think)

    p_mod = sub.add_parser("modulate", help="Apply neuromodulator feedback")
    p_mod.add_argument("--input", "-i", required=True, help="Outcome JSON file")
    p_mod.add_argument("--output", "-o", required=True, help="Result JSON file")
    p_mod.set_defaults(func=cmd_modulate)

    p_evo = sub.add_parser("evolve", help="Evolve agent networks")
    p_evo.add_argument("--taskset", "-t", help="Taskset JSON file")
    p_evo.add_argument("--generations", "-g", type=int, default=5, help="Generations")
    p_evo.add_argument("--episodes", "-e", type=int, default=10, help="Episodes per generation")
    p_evo.add_argument("--seed", type=int, default=None, help="Random seed")
    p_evo.add_argument("--output", "-o", required=True, help="Summary JSON file")
    p_evo.set_defaults(func=cmd_evolve)

    p_save = sub.add_parser("save", help="Save tissue state")
    p_save.add_argument("--input", "-i", required=True, help="State JSON file")
    p_save.add_argument("--path", "-p", required=True, help="Output path")
    p_save.set_defaults(func=cmd_save)

    p_load = sub.add_parser("load", help="Load tissue state")
    p_load.add_argument("--path", "-p", required=True, help="Input path")
    p_load.add_argument("--output", "-o", required=True, help="Result JSON file")
    p_load.set_defaults(func=cmd_load)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
