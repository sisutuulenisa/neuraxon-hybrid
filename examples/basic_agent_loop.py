"""Basic agent loop example for neuraxon_agent."""

from neuraxon_agent import Action, Evolution, Memory, Modulation, Perception, Tissue


def main() -> None:
    tissue = Tissue(config={"debug": True})
    perception = Perception()
    action = Action()
    modulation = Modulation()
    memory = Memory(capacity=100)
    evolution = Evolution()

    tissue.bind(perception, "perception")
    tissue.bind(action, "action")
    tissue.bind(modulation, "modulation")
    tissue.bind(memory, "memory")
    tissue.bind(evolution, "evolution")

    for step in range(3):
        obs = perception.observe({"step": step, "value": step * 0.1})
        decision = {"type": "move", "params": obs}
        result = action.act(decision)
        memory.store({"step": step, "observation": obs, "result": result})
        modulation.adjust({"error": result["decision"]["params"]["data"]["value"] - 0.5})
        evolution.evaluate({"reward": float(step)})
        print(f"Step {step}: obs={obs}, action={result}, gen={evolution.generation}")
        evolution.step()

    print("Recalled episodes:", memory.recall(3))


if __name__ == "__main__":
    main()
