"""Unit tests for the ActionDecoder and AgentAction classes."""

from __future__ import annotations

import pytest

from neuraxon_agent.action import TRINARY_STATES, ActionDecoder, AgentAction


class TestAgentAction:
    def test_creation(self) -> None:
        action = AgentAction(actie_type="PROCEED", confidence=1.0, raw_output=(1,))
        assert action.actie_type == "PROCEED"
        assert action.confidence == 1.0
        assert action.raw_output == (1,)

    def test_immutability(self) -> None:
        action = AgentAction(actie_type="PAUSE", confidence=0.5, raw_output=(0,))
        with pytest.raises(AttributeError):
            action.actie_type = "RETRY"  # type: ignore[misc]


class TestActionDecoderInit:
    def test_default_num_output_neurons(self) -> None:
        dec = ActionDecoder()
        assert dec.num_output_neurons == 1

    def test_custom_num_output_neurons(self) -> None:
        dec = ActionDecoder(num_output_neurons=3)
        assert dec.num_output_neurons == 3

    def test_invalid_num_output_neurons_raises(self) -> None:
        with pytest.raises(ValueError, match="num_output_neurons must be >= 1"):
            ActionDecoder(num_output_neurons=0)
        with pytest.raises(ValueError, match="num_output_neurons must be >= 1"):
            ActionDecoder(num_output_neurons=-1)


class TestActionDecoderBasis:
    """Tests for the single-neuron (basis) decoder."""

    def test_proceed(self) -> None:
        dec = ActionDecoder(num_output_neurons=1)
        result = dec.decode([1])
        assert result.actie_type == ActionDecoder.PROCEED
        assert result.confidence == 1.0
        assert result.raw_output == (1,)

    def test_pause(self) -> None:
        dec = ActionDecoder(num_output_neurons=1)
        result = dec.decode([0])
        assert result.actie_type == ActionDecoder.PAUSE
        assert result.confidence == 1.0
        assert result.raw_output == (0,)

    def test_retry(self) -> None:
        dec = ActionDecoder(num_output_neurons=1)
        result = dec.decode([-1])
        assert result.actie_type == ActionDecoder.RETRY
        assert result.confidence == 1.0
        assert result.raw_output == (-1,)


class TestActionDecoderMulti:
    """Tests for the multi-neuron decoder."""

    def test_escalate_exact(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([1, 1])
        assert result.actie_type == ActionDecoder.ESCALATE
        assert result.confidence == 1.0
        assert result.raw_output == (1, 1)

    def test_explore_exact(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([0, 1])
        assert result.actie_type == ActionDecoder.EXPLORE
        assert result.confidence == 1.0
        assert result.raw_output == (0, 1)

    def test_fallback_sum_proceed(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([1, 0])
        assert result.actie_type == ActionDecoder.PROCEED
        # One of two neurons agrees with positive direction
        assert result.confidence == 0.5

    def test_fallback_sum_pause(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([0, 0])
        assert result.actie_type == ActionDecoder.PAUSE
        assert result.confidence == 1.0  # both neutral

    def test_fallback_sum_retry(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([-1, 0])
        assert result.actie_type == ActionDecoder.RETRY
        assert result.confidence == 0.5

    def test_fallback_sum_escalate(self) -> None:
        # Three neurons, sum = 2 -> ESCALATE fallback
        dec = ActionDecoder(num_output_neurons=3)
        result = dec.decode([1, 1, 0])
        assert result.actie_type == ActionDecoder.ESCALATE
        assert result.confidence == pytest.approx(0.6667)

    def test_all_combinations_defined(self) -> None:
        """Every possible 2-neuron trinary combination must decode without error."""
        dec = ActionDecoder(num_output_neurons=2)
        defined_actions = set(ActionDecoder.get_all_defined_actions())
        for a in TRINARY_STATES:
            for b in TRINARY_STATES:
                result = dec.decode([a, b])
                assert result.actie_type in defined_actions

    def test_all_combinations_defined_3_neurons(self) -> None:
        """Every possible 3-neuron trinary combination must decode without error."""
        dec = ActionDecoder(num_output_neurons=3)
        defined_actions = set(ActionDecoder.get_all_defined_actions())
        for a in TRINARY_STATES:
            for b in TRINARY_STATES:
                for c in TRINARY_STATES:
                    result = dec.decode([a, b, c])
                    assert result.actie_type in defined_actions


class TestActionDecoderPaddingTruncation:
    def test_pad_to_num_output_neurons(self) -> None:
        dec = ActionDecoder(num_output_neurons=3)
        result = dec.decode([1])
        assert result.raw_output == (1, 0, 0)

    def test_truncate_to_num_output_neurons(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        result = dec.decode([1, -1, 0, 1])
        assert result.raw_output == (1, -1)


class TestActionDecoderValidation:
    def test_empty_list_raises(self) -> None:
        dec = ActionDecoder()
        with pytest.raises(ValueError, match="output_states must not be empty"):
            dec.decode([])

    def test_invalid_state_raises(self) -> None:
        dec = ActionDecoder()
        with pytest.raises(ValueError, match="Invalid trinary state"):
            dec.decode([2])

    def test_invalid_state_negative_large(self) -> None:
        dec = ActionDecoder()
        with pytest.raises(ValueError, match="Invalid trinary state"):
            dec.decode([-2])


class TestActionDecoderDeterminism:
    def test_same_input_same_output(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        r1 = dec.decode([1, -1])
        dec.reset()
        r2 = dec.decode([1, -1])
        assert r1 == r2

    def test_multiple_calls_independent(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        results = [dec.decode([0, 1]) for _ in range(5)]
        assert all(r == results[0] for r in results)


class TestActionDecoderHistory:
    def test_last_empty(self) -> None:
        dec = ActionDecoder()
        assert dec.last() is None

    def test_last_returns_most_recent(self) -> None:
        dec = ActionDecoder()
        dec.decode([1])
        dec.decode([-1])
        last = dec.last()
        assert last is not None
        assert last.actie_type == ActionDecoder.RETRY

    def test_get_history(self) -> None:
        dec = ActionDecoder()
        dec.decode([1])
        dec.decode([0])
        hist = dec.get_history()
        assert len(hist) == 2
        assert hist[0].actie_type == ActionDecoder.PROCEED
        assert hist[1].actie_type == ActionDecoder.PAUSE

    def test_reset_clears_history(self) -> None:
        dec = ActionDecoder()
        dec.decode([1])
        dec.reset()
        assert dec.last() is None
        assert dec.get_history() == []


class TestActionDecoderMappings:
    def test_basis_mapping_keys(self) -> None:
        mapping = ActionDecoder.get_basis_mapping()
        assert set(mapping.keys()) == {-1, 0, 1}

    def test_multi_mapping_contains_defined_patterns(self) -> None:
        mapping = ActionDecoder.get_multi_mapping()
        assert (1, 1) in mapping
        assert (0, 1) in mapping

    def test_all_defined_actions(self) -> None:
        actions = ActionDecoder.get_all_defined_actions()
        assert actions == [
            "PROCEED",
            "PAUSE",
            "RETRY",
            "ESCALATE",
            "EXPLORE",
            "CAUTIOUS",
        ]


class TestActionDecoderConfidence:
    def test_exact_match_confidence_is_one(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        assert dec.decode([1, 1]).confidence == 1.0
        assert dec.decode([0, 1]).confidence == 1.0

    def test_fallback_confidence_range(self) -> None:
        dec = ActionDecoder(num_output_neurons=2)
        for a in TRINARY_STATES:
            for b in TRINARY_STATES:
                pattern = (a, b)
                if pattern in ActionDecoder.get_multi_mapping():
                    continue
                result = dec.decode([a, b])
                assert 0.0 <= result.confidence <= 1.0
