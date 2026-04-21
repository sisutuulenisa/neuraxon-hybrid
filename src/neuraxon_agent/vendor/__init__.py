"""Vendor shim for Neuraxon v2.0 upstream dependency.

Bundles neuraxon2.py directly so no external dependencies or submodules are needed.
"""
from __future__ import annotations

from .neuraxon2 import NeuraxonNetwork, NetworkParameters

__all__ = ["NeuraxonNetwork", "NetworkParameters"]
