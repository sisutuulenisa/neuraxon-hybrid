"""Action-contract adapter for benchmark scoring.

The runtime ``ActionDecoder`` currently emits control-policy labels such as
``PROCEED`` and ``PAUSE``. Mock benchmark scenarios use task-policy labels such
as ``execute`` and ``query``. This module makes that contract explicit so
benchmark scores measure tissue behaviour instead of string vocabulary mismatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from neuraxon_agent.action import ActionDecoder

ACTION_DECODER_TO_BENCHMARK_ACTION: dict[str, str] = {
    ActionDecoder.PROCEED: "execute",
    ActionDecoder.PAUSE: "query",
    ActionDecoder.RETRY: "retry",
    ActionDecoder.ESCALATE: "assertive",
    ActionDecoder.EXPLORE: "explore",
    ActionDecoder.CAUTIOUS: "cautious",
}

BENCHMARK_ACTIONS = frozenset(ACTION_DECODER_TO_BENCHMARK_ACTION.values())


@dataclass(frozen=True)
class ActionContractCoverage:
    """Coverage summary for decoder and benchmark action vocabularies."""

    decoder_actions: set[str]
    expected_benchmark_actions: set[str]
    covered_benchmark_actions: set[str]
    unmapped_decoder_actions: set[str]
    unreachable_benchmark_actions: set[str]


def normalize_benchmark_action(action: str) -> str:
    """Normalize a decoded or benchmark action into benchmark vocabulary.

    Existing benchmark-vocabulary actions are returned unchanged. Known
    ``ActionDecoder`` labels are mapped explicitly. Unknown labels are returned
    unchanged so diagnostics can still expose unsupported actions.
    """
    return ACTION_DECODER_TO_BENCHMARK_ACTION.get(action, action)


def benchmark_action_coverage(
    expected_benchmark_actions: Iterable[str],
) -> ActionContractCoverage:
    """Compare current decoder outputs with expected benchmark actions."""
    decoder_actions = set(ActionDecoder.get_all_defined_actions())
    expected = set(expected_benchmark_actions)
    mapped_decoder_actions = set(ACTION_DECODER_TO_BENCHMARK_ACTION)
    covered = {normalize_benchmark_action(action) for action in decoder_actions}
    return ActionContractCoverage(
        decoder_actions=decoder_actions,
        expected_benchmark_actions=expected,
        covered_benchmark_actions=covered & expected,
        unmapped_decoder_actions=decoder_actions - mapped_decoder_actions,
        unreachable_benchmark_actions=expected - covered,
    )
