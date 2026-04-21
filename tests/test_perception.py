"""Unit tests for the PerceptionEncoder class."""

from __future__ import annotations

import pytest

from neuraxon_agent.perception import Perception, PerceptionEncoder


class TestPerception:
    """Smoke tests for the legacy Perception stub."""

    def test_observe_returns_dict(self) -> None:
        p = Perception()
        obs = p.observe({"input": 42})
        assert isinstance(obs, dict)
        assert obs["source"] == "raw"
        assert obs["data"] == {"input": 42}

    def test_last_returns_most_recent(self) -> None:
        p = Perception()
        p.observe("first")
        p.observe("second")
        assert p.last() == {"source": "raw", "data": "second", "timestamp": None}

    def test_last_empty(self) -> None:
        p = Perception()
        assert p.last() is None


class TestPerceptionEncoderInit:
    def test_default_num_input_neurons(self) -> None:
        enc = PerceptionEncoder()
        assert enc.num_input_neurons == 5

    def test_custom_num_input_neurons(self) -> None:
        enc = PerceptionEncoder(num_input_neurons=10)
        assert enc.num_input_neurons == 10

    def test_invalid_num_input_neurons_raises(self) -> None:
        with pytest.raises(ValueError, match="num_input_neurons must be positive"):
            PerceptionEncoder(num_input_neurons=0)
        with pytest.raises(ValueError, match="num_input_neurons must be positive"):
            PerceptionEncoder(num_input_neurons=-3)

    def test_custom_thresholds(self) -> None:
        enc = PerceptionEncoder(thresholds={"cpu_percent": (10.0, 90.0)})
        assert enc.thresholds["cpu_percent"] == (10.0, 90.0)
        # Other defaults remain intact
        assert "memory_percent" in enc.thresholds


class TestPerceptionEncoderToolResult:
    def test_success(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"tool_result": "success"})[0] == 1

    def test_fail(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"tool_result": "fail"})[0] == -1

    def test_timeout(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"tool_result": "timeout"})[0] == 0

    def test_missing(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({})[0] == 0

    def test_case_insensitive(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"tool_result": "SUCCESS"})[0] == 1
        assert enc.encode({"tool_result": "Fail"})[0] == -1


class TestPerceptionEncoderErrorType:
    def test_syntax(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"error_type": "syntax"})[1] == -1

    def test_runtime(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"error_type": "runtime"})[1] == -1

    def test_network(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"error_type": "network"})[1] == 0

    def test_auth(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"error_type": "auth"})[1] == 0

    def test_no_error_positive(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({})[1] == 1


class TestPerceptionEncoderSessionHealth:
    def test_duration_low(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"duration_seconds": 10.0})
        assert result[2] == -1

    def test_duration_mid(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"duration_seconds": 120.0})
        assert result[2] == 0

    def test_duration_high(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"duration_seconds": 400.0})
        assert result[2] == 1

    def test_turn_count_low(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"turn_count": 2.0})
        assert result[2] == -1

    def test_turn_count_high(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"turn_count": 25.0})
        assert result[2] == 1

    def test_token_count_high(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({"token_count": 2500.0})
        assert result[2] == 1

    def test_aggregate_majority(self) -> None:
        enc = PerceptionEncoder()
        # Two low, one high -> majority is low -> -1
        result = enc.encode(
            {
                "duration_seconds": 10.0,
                "turn_count": 2.0,
                "token_count": 2500.0,
            }
        )
        assert result[2] == -1

    def test_missing_session_data(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({})[2] == 0


class TestPerceptionEncoderEnvironmentHealth:
    def test_cpu_low(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"cpu_percent": 10.0})[3] == -1

    def test_cpu_mid(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"cpu_percent": 50.0})[3] == 0

    def test_cpu_high(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"cpu_percent": 80.0})[3] == 1

    def test_memory_high(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"memory_percent": 90.0})[3] == 1

    def test_disk_high(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"disk_percent": 90.0})[3] == 1

    def test_missing_environment_data(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({})[3] == 0


class TestPerceptionEncoderPreviousOutcome:
    def test_success(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"previous_outcome": "success"})[4] == 1

    def test_fail(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"previous_outcome": "fail"})[4] == -1

    def test_none(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({"previous_outcome": "none"})[4] == 0

    def test_missing(self) -> None:
        enc = PerceptionEncoder()
        assert enc.encode({})[4] == 0


class TestPerceptionEncoderOutputShape:
    def test_default_length(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode({})
        assert len(result) == 5

    def test_custom_length(self) -> None:
        enc = PerceptionEncoder(num_input_neurons=3)
        result = enc.encode({"tool_result": "success"})
        assert len(result) == 3

    def test_padding(self) -> None:
        enc = PerceptionEncoder(num_input_neurons=10)
        result = enc.encode({})
        assert len(result) == 10
        assert result[5:] == [0, 0, 0, 0, 0]

    def test_truncation(self) -> None:
        enc = PerceptionEncoder(num_input_neurons=2)
        result = enc.encode({"tool_result": "success"})
        assert len(result) == 2


class TestPerceptionEncoderTrinaryValues:
    def test_only_trinary_values(self) -> None:
        enc = PerceptionEncoder()
        obs = {
            "tool_result": "success",
            "error_type": "syntax",
            "duration_seconds": 400.0,
            "cpu_percent": 80.0,
            "previous_outcome": "fail",
        }
        result = enc.encode(obs)
        for val in result:
            assert val in (-1, 0, 1)

    def test_different_observations_different_patterns(self) -> None:
        enc = PerceptionEncoder()
        r1 = enc.encode({"tool_result": "success"})
        enc.reset()
        r2 = enc.encode({"tool_result": "fail"})
        assert r1 != r2


class TestPerceptionEncoderSequential:
    def test_first_call_no_history(self) -> None:
        enc = PerceptionEncoder()
        result = enc.encode_sequential({"tool_result": "success"})
        assert result == [1, 1, 0, 0, 0]

    def test_trend_detection(self) -> None:
        enc = PerceptionEncoder()
        enc.encode_sequential({"tool_result": "fail"})  # [-1, ...]
        result = enc.encode_sequential({"tool_result": "success"})  # trend up
        assert result[0] == 1  # increased from -1 to 1

    def test_stable(self) -> None:
        enc = PerceptionEncoder()
        enc.encode_sequential({"tool_result": "success"})
        result = enc.encode_sequential({"tool_result": "success"})
        assert result[0] == 0  # stable at 1

    def test_reset_clears_history(self) -> None:
        enc = PerceptionEncoder()
        enc.encode({"tool_result": "fail"})
        enc.reset()
        result = enc.encode_sequential({"tool_result": "success"})
        # After reset, no previous history, so falls back to raw encoding
        assert result[0] == 1

    def test_history_tracking(self) -> None:
        enc = PerceptionEncoder()
        enc.encode({"a": 1})
        enc.encode({"b": 2})
        hist = enc.get_history()
        assert len(hist) == 2
        assert all(len(row) == 5 for row in hist)


class TestPerceptionEncoderHelpers:
    def test_threshold_encode(self) -> None:
        assert PerceptionEncoder._threshold_encode(10.0, 20.0, 80.0) == -1
        assert PerceptionEncoder._threshold_encode(50.0, 20.0, 80.0) == 0
        assert PerceptionEncoder._threshold_encode(90.0, 20.0, 80.0) == 1

    def test_aggregate_signals_majority(self) -> None:
        assert PerceptionEncoder._aggregate_signals([1, 1, -1]) == 1
        assert PerceptionEncoder._aggregate_signals([-1, -1, 1]) == -1

    def test_aggregate_signals_tie(self) -> None:
        assert PerceptionEncoder._aggregate_signals([1, -1]) == 0
        assert PerceptionEncoder._aggregate_signals([1, 0, -1]) == 0

    def test_aggregate_signals_unanimous(self) -> None:
        assert PerceptionEncoder._aggregate_signals([0, 0, 0]) == 0


class TestPerceptionEncoderWithNetwork:
    """Verify encoder output can be fed into a live NeuraxonNetwork."""

    def test_encode_fits_network_input(self) -> None:
        from neuraxon_agent.vendor import NetworkParameters, NeuraxonNetwork

        params = NetworkParameters(num_input_neurons=5)
        network = NeuraxonNetwork(params)
        enc = PerceptionEncoder(num_input_neurons=5)

        obs = {
            "tool_result": "success",
            "error_type": "runtime",
            "duration_seconds": 120.0,
            "cpu_percent": 50.0,
            "previous_outcome": "fail",
        }
        pattern = enc.encode(obs)
        assert len(pattern) == len(network.input_neurons)
        network.set_input_states(pattern)
        states = [n.trinary_state for n in network.input_neurons]
        assert states == pattern
