"""Modulation layer — dynamic parameter adjustment and homeostasis.

Provides :class:`ModulationFeedback` to translate agent outcomes
(success, failure, partial, timeout) into neuromodulator deltas
that drive learning in the Neuraxon network.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class Modulation:
    """Adjusts internal parameters to maintain stability and adapt behavior."""

    def __init__(self, params: dict[str, float] | None = None) -> None:
        self.params = params or {"gain": 1.0, "threshold": 0.5}

    def adjust(self, feedback: dict[str, Any]) -> dict[str, float]:
        """Update parameters based on environmental feedback."""
        error = feedback.get("error", 0.0)
        self.params["gain"] += 0.01 * error
        self.params["threshold"] -= 0.005 * error
        return dict(self.params)


#: Default outcome-to-neuromodulator mapping.
#: Values are *deltas* applied to the current tonic level of each modulator.
DEFAULT_OUTCOME_MAP: dict[str, dict[str, float]] = {
    "success": {"dopamine": 0.30, "serotonin": 0.10, "acetylcholine": 0.10, "norepinephrine": 0.05},
    "failure": {"dopamine": -0.10, "serotonin": -0.20, "acetylcholine": 0.20, "norepinephrine": 0.30},
    "partial": {"dopamine": 0.10, "serotonin": -0.05, "acetylcholine": 0.15, "norepinephrine": 0.15},
    "timeout": {"dopamine": -0.05, "serotonin": -0.10, "acetylcholine": 0.10, "norepinephrine": 0.20},
}


@dataclass
class ModulationFeedback:
    """Maps agent outcomes to neuromodulator deltas and learns optimal modulation.

    Parameters
    ----------
    outcome_map:
        Configurable mapping from outcome string to a dict of
        neuromodulator deltas.  Defaults to ``DEFAULT_OUTCOME_MAP``.
    adapt_rate:
        Learning rate for the adaptive mapping update.  Set to ``0.0``
        to disable adaptation.
    history_window:
        Number of recent outcomes to keep for convergence metrics.

    Example
    -------
    >>> feedback = ModulationFeedback()
    >>> feedback.get_deltas("success")
    {'dopamine': 0.3, 'serotonin': 0.1, 'acetylcholine': 0.1, 'norepinephrine': 0.05}
    """

    outcome_map: dict[str, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_OUTCOME_MAP))
    adapt_rate: float = 0.01
    history_window: int = 100

    # internal adaptive state -------------------------------------------------
    _history: list[tuple[str, dict[str, float]]] = field(default_factory=list, repr=False)
    _running_mean: dict[str, dict[str, float]] = field(default_factory=dict, repr=False)
    _call_count: int = field(default=0, repr=False)

    def get_deltas(self, outcome: str) -> dict[str, float]:
        """Return the neuromodulator deltas for *outcome*.

        If the outcome is unknown, returns an empty dict.
        """
        return dict(self.outcome_map.get(outcome, {}))

    def apply(self, network: Any, outcome: str) -> dict[str, float]:
        """Apply neuromodulator deltas to *network* for *outcome*.

        The *network* must expose a ``modulate(neuromodulator: str, level: float)``
        method (as :class:`~neuraxon_agent.vendor.neuraxon2.NeuraxonNetwork` does).

        Returns the deltas that were applied.
        """
        deltas = self.get_deltas(outcome)
        if not deltas:
            return {}

        # Current levels are needed so we can compute *relative* changes
        # for the adaptive learner.
        pre_levels = self._get_flat_levels(network)

        for modulator, delta in deltas.items():
            # Add delta to current tonic level (clamped to [0, 1] by the network)
            current = pre_levels.get(modulator, 0.0)
            new_level = max(0.0, min(1.0, current + delta))
            network.modulate(modulator, new_level)

        post_levels = self._get_flat_levels(network)
        actual_change = {m: post_levels.get(m, 0.0) - pre_levels.get(m, 0.0) for m in deltas}

        self._record(outcome, actual_change)
        return deltas

    def _get_flat_levels(self, network: Any) -> dict[str, float]:
        """Read flat neuromodulator levels from *network*."""
        nm = getattr(network, "neuromodulators", {})
        if callable(nm):
            nm = nm()
        return dict(nm) if nm else {}

    def _record(self, outcome: str, actual_change: dict[str, float]) -> None:
        """Store an outcome observation and update running means."""
        self._history.append((outcome, actual_change))
        if len(self._history) > self.history_window:
            self._history.pop(0)

        self._call_count += 1

        if self.adapt_rate <= 0.0:
            return

        # Exponential moving average per (outcome, modulator)
        if outcome not in self._running_mean:
            self._running_mean[outcome] = {}

        for modulator, change in actual_change.items():
            old = self._running_mean[outcome].get(modulator, change)
            self._running_mean[outcome][modulator] = old + self.adapt_rate * (change - old)

    def adaptive_deltas(self, outcome: str) -> dict[str, float] | None:
        """Return the learned adaptive deltas for *outcome*, if any.

        Returns ``None`` when no adaptive data has been collected yet.
        """
        means = self._running_mean.get(outcome)
        return dict(means) if means else None

    def convergence_metrics(self) -> dict[str, Any]:
        """Return metrics that indicate whether adaptive mapping is stable.

        Returns a dict with keys:

        ``call_count``
            Total number of :meth:`apply` calls.
        ``outcomes``
            Dict mapping each observed outcome to its metrics:
            ``mean_delta``, ``std_delta``, and ``sample_count`` per modulator.
        ``is_stable``
            ``True`` when every modulator's coefficient of variation
            (std / |mean|) is below ``0.5`` and at least 10 samples exist.
        """
        from statistics import mean, stdev

        outcome_samples: dict[str, list[dict[str, float]]] = {}
        for out, change in self._history:
            outcome_samples.setdefault(out, []).append(change)

        outcomes: dict[str, Any] = {}
        all_stable = True

        for out, samples in outcome_samples.items():
            modulators: set[str] = set()
            for s in samples:
                modulators.update(s.keys())

            per_mod: dict[str, Any] = {}
            for mod in sorted(modulators):
                values = [s.get(mod, 0.0) for s in samples]
                m = mean(values)
                per_mod[mod] = {
                    "mean_delta": round(m, 6),
                    "std_delta": round(stdev(values), 6) if len(values) > 1 else 0.0,
                    "sample_count": len(values),
                }
                # Stability heuristic: low relative variance + enough samples
                if len(values) < 10:
                    all_stable = False
                else:
                    abs_mean = abs(m)
                    if abs_mean > 1e-6:
                        cv = per_mod[mod]["std_delta"] / abs_mean
                        if cv > 0.5:
                            all_stable = False
                    else:
                        # mean ~0 → require very small std
                        if per_mod[mod]["std_delta"] > 0.05:
                            all_stable = False

            outcomes[out] = per_mod

        return {
            "call_count": self._call_count,
            "outcomes": outcomes,
            "is_stable": all_stable and self._call_count >= 10,
        }

    def reset_adaptation(self) -> None:
        """Clear adaptive history and running means."""
        self._history.clear()
        self._running_mean.clear()
        self._call_count = 0
