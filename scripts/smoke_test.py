"""Smoke test for Neuraxon v2.0 vendor integration."""
from __future__ import annotations

import sys

def test_vendor_import() -> bool:
    """Test that vendor module imports work."""
    try:
        from neuraxon_agent.vendor import NeuraxonNetwork, NetworkParameters
        print("PASS: Vendor imports work")
        return True
    except Exception as e:
        print(f"FAIL: Vendor imports failed: {e}")
        return False

def test_neuraxon2_basic() -> bool:
    """Test basic Neuraxon v2.0 instantiation."""
    try:
        from neuraxon_agent.vendor.neuraxon2 import NetworkParameters, NeuraxonNetwork
        params = NetworkParameters()
        network = NeuraxonNetwork(params)
        total = len(network.all_neurons)
        print(f"PASS: NeuraxonNetwork created with {total} neurons (input={len(network.input_neurons)}, hidden={len(network.hidden_neurons)}, output={len(network.output_neurons)})")
        return True
    except Exception as e:
        print(f"FAIL: NeuraxonNetwork instantiation failed: {e}")
        return False

def test_agent_imports() -> bool:
    """Test that all agent module stubs import."""
    try:
        from neuraxon_agent import Tissue, Perception, Action, Modulation, Memory, Evolution
        print("PASS: All agent module stubs import")
        return True
    except Exception as e:
        print(f"FAIL: Agent imports failed: {e}")
        return False

def main() -> int:
    results = [
        test_vendor_import(),
        test_neuraxon2_basic(),
        test_agent_imports(),
    ]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
