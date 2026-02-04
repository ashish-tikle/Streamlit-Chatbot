"""
Tests for monitoring features
Run with: pytest tests/test_monitoring.py -v
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend import (
    _calculate_cost,
    _log_metrics,
    log_feedback,
    generate_response,
)


class TestCostCalculation:
    """Test cost calculation for different token usage patterns."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation with typical usage."""
        usage = {"prompt_tokens": 100, "completion_tokens": 50}

        # Gemini Flash pricing: $0.075 per 1M input, $0.30 per 1M output
        expected_cost = (100 / 1_000_000) * 0.075 + (50 / 1_000_000) * 0.30

        actual_cost = _calculate_cost(usage)
        assert abs(actual_cost - expected_cost) < 0.0000001

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        usage = {"prompt_tokens": 0, "completion_tokens": 0}

        assert _calculate_cost(usage) == 0.0

    def test_calculate_cost_large_numbers(self):
        """Test cost calculation with large token counts."""
        usage = {
            "prompt_tokens": 1_000_000,  # 1M tokens
            "completion_tokens": 500_000,  # 500K tokens
        }

        expected_cost = 1.0 * 0.075 + 0.5 * 0.30
        actual_cost = _calculate_cost(usage)

        assert abs(actual_cost - expected_cost) < 0.01

    def test_calculate_cost_missing_fields(self):
        """Test cost calculation with missing fields (should default to 0)."""
        usage = {}

        assert _calculate_cost(usage) == 0.0

    def test_calculate_cost_only_prompt_tokens(self):
        """Test cost calculation with only prompt tokens."""
        usage = {"prompt_tokens": 1000}

        expected_cost = (1000 / 1_000_000) * 0.075
        actual_cost = _calculate_cost(usage)

        assert abs(actual_cost - expected_cost) < 0.0000001


class TestMetricsLogging:
    """Test metrics logging functionality."""

    @patch("backend.METRICS_FILE", Path("test_metrics.jsonl"))
    def test_log_metrics_success(self):
        """Test successful metrics logging."""
        metrics = {
            "request_id": "test-123",
            "timestamp": datetime.utcnow().isoformat(),
            "cost_usd": 0.00015,
            "duration_seconds": 1.5,
            "success": True,
        }

        with patch("builtins.open", mock_open()) as mock_file:
            _log_metrics(metrics)

            mock_file.assert_called_once()
            handle = mock_file()

            # Check that json.dump was called with our metrics
            written_data = "".join(
                [call.args[0] for call in handle.write.call_args_list]
            )
            assert "test-123" in written_data
            assert "0.00015" in written_data

    @patch("backend.METRICS_FILE", Path("test_metrics.jsonl"))
    @patch("backend.logger")
    def test_log_metrics_handles_errors(self, mock_logger):
        """Test that logging errors are handled gracefully."""
        metrics = {"test": "data"}

        with patch("builtins.open", side_effect=IOError("Disk full")):
            _log_metrics(metrics)

            # Should log error but not raise exception
            mock_logger.error.assert_called_once()


class TestFeedbackLogging:
    """Test user feedback logging."""

    @patch("backend.FEEDBACK_FILE", Path("test_feedback.jsonl"))
    def test_log_feedback_positive(self):
        """Test logging positive feedback."""
        with patch("builtins.open", mock_open()) as mock_file:
            log_feedback("req-123", 5, "positive", "Great response!")

            mock_file.assert_called_once()
            handle = mock_file()

            written_data = "".join(
                [call.args[0] for call in handle.write.call_args_list]
            )
            assert "req-123" in written_data
            assert "positive" in written_data
            assert "Great response!" in written_data

    @patch("backend.FEEDBACK_FILE", Path("test_feedback.jsonl"))
    def test_log_feedback_negative(self):
        """Test logging negative feedback."""
        with patch("builtins.open", mock_open()) as mock_file:
            log_feedback("req-456", 2, "negative", "")

            mock_file.assert_called_once()
            handle = mock_file()

            written_data = "".join(
                [call.args[0] for call in handle.write.call_args_list]
            )
            assert "req-456" in written_data
            assert "negative" in written_data

    @patch("backend.FEEDBACK_FILE", Path("test_feedback.jsonl"))
    @patch("backend.logger")
    def test_log_feedback_handles_errors(self, mock_logger):
        """Test that feedback logging errors are handled."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            log_feedback("req-789", 0, "positive")

            mock_logger.error.assert_called_once()


class TestRetryLogic:
    """Test retry logic and error handling."""

    @patch("backend.completion")
    @patch("backend._log_metrics")
    def test_generate_response_success(self, mock_log, mock_completion):
        """Test successful response generation."""
        mock_completion.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }

        response = generate_response("Test message", [], 0.5)

        assert response == "Test response"
        mock_completion.assert_called_once()
        mock_log.assert_called_once()

        # Verify metrics logged correctly
        logged_metrics = mock_log.call_args[0][0]
        assert logged_metrics["success"] is True
        assert logged_metrics["total_tokens"] == 70
        assert logged_metrics["cost_usd"] > 0

    @patch("backend._call_llm_with_retry")
    @patch("backend._log_metrics")
    def test_generate_response_rate_limit_error(self, mock_log, mock_retry):
        """Test handling of rate limit errors."""
        from litellm.exceptions import RateLimitError

        mock_retry.side_effect = RateLimitError("Rate limit exceeded")

        response = generate_response("Test", [], 0.5)

        assert "Rate limit exceeded" in response
        assert "⚠️" in response

        # Verify error metrics logged
        logged_metrics = mock_log.call_args[0][0]
        assert logged_metrics["success"] is False
        assert logged_metrics["error_type"] == "RateLimitError"

    @patch("backend._call_llm_with_retry")
    @patch("backend._log_metrics")
    def test_generate_response_auth_error(self, mock_log, mock_retry):
        """Test handling of authentication errors."""
        from litellm.exceptions import AuthenticationError

        mock_retry.side_effect = AuthenticationError("Invalid API key")

        response = generate_response("Test", [], 0.5)

        assert "Authentication error" in response

        logged_metrics = mock_log.call_args[0][0]
        assert logged_metrics["success"] is False
        assert logged_metrics["error_type"] == "AuthenticationError"

    @patch("backend._call_llm_with_retry")
    @patch("backend._log_metrics")
    def test_generate_response_timeout_error(self, mock_log, mock_retry):
        """Test handling of timeout errors."""
        from litellm.exceptions import Timeout

        mock_retry.side_effect = Timeout("Request timed out")

        response = generate_response("Test", [], 0.5)

        assert "timed out" in response.lower()

        logged_metrics = mock_log.call_args[0][0]
        assert logged_metrics["success"] is False
        assert "Timeout" in logged_metrics["error_type"]


class TestConfigValidation:
    """Test configuration validation."""

    @patch("backend.API_KEY", "sk-valid-key")
    @patch("backend.API_BASE", "https://api.example.com")
    @patch("backend.MODEL_NAME", "openai/gpt-4")
    def test_valid_configuration(self):
        """Test that valid configuration passes validation."""
        from backend import _validate_env

        problems = _validate_env()
        assert len(problems) == 0

    @patch("backend.API_KEY", "invalid-key")
    def test_invalid_api_key_format(self):
        """Test detection of invalid API key format."""
        from backend import _validate_env

        problems = _validate_env()
        assert any("sk-" in p for p in problems)

    @patch("backend.API_KEY", None)
    def test_missing_api_key(self):
        """Test detection of missing API key."""
        from backend import _validate_env

        problems = _validate_env()
        assert any("API_KEY" in p for p in problems)

    @patch("backend.MODEL_NAME", "invalid-model-without-provider")
    def test_model_without_provider_prefix(self):
        """Test detection of model name without provider prefix."""
        from backend import _validate_env

        problems = _validate_env()
        assert any("provider" in p.lower() for p in problems)


class TestAlertingSystem:
    """Test alerting system functionality."""

    def test_metrics_analyzer_error_rate(self):
        """Test error rate calculation."""
        from monitoring.alerts import MetricsAnalyzer

        # Mock metrics data
        test_metrics = [
            {"success": True, "timestamp": datetime.utcnow().isoformat()},
            {"success": True, "timestamp": datetime.utcnow().isoformat()},
            {"success": False, "timestamp": datetime.utcnow().isoformat()},
            {"success": False, "timestamp": datetime.utcnow().isoformat()},
            {"success": True, "timestamp": datetime.utcnow().isoformat()},
        ]

        analyzer = MetricsAnalyzer()
        analyzer.metrics = test_metrics

        error_rate = analyzer.calculate_error_rate()
        assert error_rate is not None
        assert abs(error_rate - 40.0) < 0.1  # 2/5 = 40%

    def test_metrics_analyzer_p95_latency(self):
        """Test p95 latency calculation."""
        from monitoring.alerts import MetricsAnalyzer

        # Create test data with known p95
        test_metrics = [
            {
                "success": True,
                "duration_seconds": i * 0.1,
                "timestamp": datetime.utcnow().isoformat(),
            }
            for i in range(1, 101)  # 0.1s to 10s
        ]

        analyzer = MetricsAnalyzer()
        analyzer.metrics = test_metrics

        p95 = analyzer.calculate_p95_latency()
        assert p95 is not None
        assert 9.0 <= p95 <= 10.0  # p95 should be around 9.5s

    def test_alert_cooldown(self):
        """Test alert cooldown mechanism."""
        from monitoring.alerts import AlertSender

        sender = AlertSender()

        # First alert should be allowed
        assert sender.can_send_alert("test_alert") is True

        # Mark alert as sent
        from monitoring.alerts import last_alert_times

        last_alert_times["test_alert"] = datetime.utcnow()

        # Second immediate alert should be blocked
        assert sender.can_send_alert("test_alert") is False


class TestDashboard:
    """Test dashboard functionality."""

    def test_load_metrics_from_jsonl(self):
        """Test loading and parsing metrics from JSONL file."""
        from monitoring.dashboard import load_metrics

        test_data = [
            {"request_id": "1", "timestamp": "2026-02-04T10:00:00", "cost_usd": 0.001},
            {"request_id": "2", "timestamp": "2026-02-04T11:00:00", "cost_usd": 0.002},
        ]

        json_content = "\n".join([json.dumps(d) for d in test_data])

        with patch("monitoring.dashboard.METRICS_FILE", Path("test.jsonl")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=json_content)):
                    df = load_metrics()

                    assert len(df) == 2
                    assert "request_id" in df.columns
                    assert "cost_usd" in df.columns

    def test_calculate_percentile(self):
        """Test percentile calculation."""
        from monitoring.dashboard import calculate_percentile
        import pandas as pd

        data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        p50 = calculate_percentile(data, 50)
        assert 5 <= p50 <= 6  # Median should be around 5.5

        p95 = calculate_percentile(data, 95)
        assert 9 <= p95 <= 10  # p95 should be around 9.5


# Integration test (runs only if environment is properly configured)
@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"), reason="Integration test requires GEMINI_API_KEY"
)
def test_full_request_flow():
    """Integration test: full request flow with real API (if configured)."""
    response = generate_response("Say 'test' only", [], 0.0)

    # Should get a response (not an error message)
    assert response is not None
    assert len(response) > 0
    assert not response.startswith("⚠️")  # No error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
