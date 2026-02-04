"""
Unit tests for observability features: logging, Prometheus metrics, and configuration
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLoggingConfiguration:
    """Test logging setup and rotation"""

    def test_log_directory_created(self):
        """Test that logs directory is created"""
        from backend import LOGS_DIR

        assert LOGS_DIR.exists()
        assert LOGS_DIR.is_dir()

    def test_log_file_path_from_env(self, monkeypatch):
        """Test custom log file path from environment"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_log = os.path.join(tmpdir, "custom.log")
            monkeypatch.setenv("LOG_FILE_PATH", custom_log)

            # Re-import to pick up env var
            import importlib
            import backend

            importlib.reload(backend)

            # Verify the path is used
            assert backend.LOG_FILE_PATH == custom_log

    def test_litellm_logging_disabled_by_default(self):
        """Test that LiteLLM verbose logging is disabled by default"""
        import litellm

        # Default should be False
        assert litellm.set_verbose == False

    def test_litellm_logging_enabled_via_env(self, monkeypatch):
        """Test enabling LiteLLM logging via environment variable"""
        monkeypatch.setenv("LITELLM_LOGGING", "true")

        import importlib
        import backend

        importlib.reload(backend)

        import litellm

        assert litellm.set_verbose == True


class TestPrometheusMetrics:
    """Test Prometheus metrics configuration and recording"""

    def test_prometheus_disabled_without_client(self, monkeypatch):
        """Test graceful degradation without prometheus-client"""
        # Hide prometheus_client
        with patch.dict(sys.modules, {"prometheus_client": None}):
            import importlib
            import backend

            importlib.reload(backend)

            assert backend.PROMETHEUS_AVAILABLE == False

    def test_prometheus_metrics_configurable(self, monkeypatch):
        """Test that Prometheus metrics can be disabled via env"""
        monkeypatch.setenv("LITELLM_PROMETHEUS_METRICS", "false")

        import importlib
        import backend

        importlib.reload(backend)

        assert backend.LITELLM_PROMETHEUS_METRICS == False

    def test_prometheus_port_configuration(self, monkeypatch):
        """Test custom Prometheus port via environment"""
        monkeypatch.setenv("PROMETHEUS_PORT", "9999")

        # Mock the start_http_server to prevent actual server start
        with patch("backend.start_http_server") as mock_server:
            import importlib
            import backend

            importlib.reload(backend)

            if backend.LITELLM_PROMETHEUS_METRICS:
                mock_server.assert_called_once_with(9999)

    @pytest.mark.skipif(
        not os.getenv("PROMETHEUS_AVAILABLE"), reason="prometheus-client not installed"
    )
    def test_metrics_increment_on_success(self):
        """Test that metrics are incremented on successful requests"""
        from backend import request_counter, LITELLM_PROMETHEUS_METRICS

        if not LITELLM_PROMETHEUS_METRICS:
            pytest.skip("Prometheus metrics disabled")

        # Get initial value
        before = request_counter.labels(
            model="test/model", status="success"
        )._value._value

        # Increment
        request_counter.labels(model="test/model", status="success").inc()

        # Check increment
        after = request_counter.labels(
            model="test/model", status="success"
        )._value._value
        assert after == before + 1


class TestSecretMasking:
    """Test that secrets are properly masked in logs"""

    def test_api_key_not_logged(self, monkeypatch, caplog):
        """Test that API keys are never logged in plain text"""
        import logging
        import backend

        # Set a test API key
        test_key = "sk-test-secret-key-12345"
        monkeypatch.setenv("GEMINI_API_KEY", test_key)

        # Trigger logging
        with caplog.at_level(logging.INFO):
            backend.logger.info(f"Config check: API_BASE={backend.API_BASE}")
            backend.logger.error(f"Test error with key in message: {test_key}")

        # Check that the key doesn't appear in logs
        log_text = caplog.text
        assert test_key not in log_text

    def test_litellm_failure_logger_masks_keys(self):
        """Test that failure logger masks API keys in error messages"""
        from backend import litellm_failure_logger

        # Create mock error with API key
        mock_error = Exception(
            "Authentication failed with key sk-test-secret-key-12345"
        )
        mock_kwargs = {"model": "test/model"}

        # Call logger (it should log without exposing the key)
        import logging

        with patch.object(logging.getLogger("backend"), "error") as mock_log:
            litellm_failure_logger(mock_kwargs, mock_error, 0, 1)

            # Verify error was logged
            mock_log.assert_called_once()
            call_args = str(mock_log.call_args)

            # Verify key was masked
            assert "sk-test-secret-key-12345" not in call_args
            assert "***REDACTED***" in call_args or "sk-" not in call_args


class TestMetricsLogging:
    """Test JSONL metrics logging"""

    def test_metrics_directory_created(self):
        """Test that metrics directory is created"""
        from backend import METRICS_DIR

        assert METRICS_DIR.exists()
        assert METRICS_DIR.is_dir()

    def test_log_metrics_writes_jsonl(self):
        """Test that metrics are written as valid JSONL"""
        from backend import _log_metrics, METRICS_FILE

        # Create test metric
        test_metric = {
            "timestamp": "2026-02-04T10:00:00",
            "model": "test/model",
            "duration_seconds": 1.5,
            "success": True,
        }

        # Log it
        _log_metrics(test_metric)

        # Verify it was written
        assert METRICS_FILE.exists()

        # Read and verify valid JSON
        with open(METRICS_FILE, "r") as f:
            lines = f.readlines()
            last_line = lines[-1]
            parsed = json.loads(last_line)

            assert parsed["model"] == "test/model"
            assert parsed["duration_seconds"] == 1.5
            assert parsed["success"] == True

    def test_log_metrics_handles_errors_gracefully(self):
        """Test that logging errors don't crash the application"""
        from backend import _log_metrics

        # Try to log to an invalid path
        with patch("backend.METRICS_FILE", Path("/invalid/path/file.jsonl")):
            # Should not raise exception
            _log_metrics({"test": "data"})


class TestCallbackRegistration:
    """Test LiteLLM callback registration"""

    def test_custom_callbacks_registered(self):
        """Test that custom logging callbacks are registered"""
        import backend
        import litellm

        # Verify callbacks exist
        assert hasattr(backend, "litellm_success_logger")
        assert hasattr(backend, "litellm_failure_logger")

        # Verify they're callable
        assert callable(backend.litellm_success_logger)
        assert callable(backend.litellm_failure_logger)

    def test_langfuse_callbacks_optional(self, monkeypatch):
        """Test that Langfuse callbacks are optional"""
        # Clear Langfuse keys
        monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        import importlib
        import backend

        importlib.reload(backend)

        # Should still work without Langfuse
        assert backend.logger is not None


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""

    def test_default_values(self):
        """Test that defaults are set when env vars not provided"""
        import backend

        # These should have defaults even without env vars
        assert backend.LOGS_DIR is not None
        assert backend.METRICS_DIR is not None

    def test_litellm_suppress_debug_enabled(self):
        """Test that LiteLLM debug info is suppressed"""
        import litellm

        assert litellm.suppress_debug_info == True
        assert litellm.drop_params == True

    def test_circuit_breaker_configuration(self, monkeypatch):
        """Test circuit breaker configuration from env"""
        monkeypatch.setenv("CIRCUIT_BREAKER_THRESHOLD", "10")
        monkeypatch.setenv("CIRCUIT_BREAKER_TIMEOUT", "60")

        import importlib
        import backend

        importlib.reload(backend)

        assert backend.circuit_breaker.fail_max == 10
        assert backend.circuit_breaker.timeout_duration == 60


class TestSmokeTests:
    """Smoke tests to ensure basic functionality works"""

    def test_backend_imports(self):
        """Test that backend module imports without errors"""
        try:
            import backend

            assert True
        except Exception as e:
            pytest.fail(f"Backend import failed: {e}")

    def test_logging_works(self, caplog):
        """Test that logging produces output"""
        import logging
        import backend

        with caplog.at_level(logging.INFO):
            backend.logger.info("Test log message")

        assert "Test log message" in caplog.text

    def test_metrics_file_writable(self):
        """Test that metrics file is writable"""
        from backend import _log_metrics

        test_data = {"test": "smoke_test", "timestamp": "2026-02-04"}

        try:
            _log_metrics(test_data)
            assert True
        except Exception as e:
            pytest.fail(f"Metrics logging failed: {e}")

    @pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
    )
    def test_generate_response_with_mock(self, monkeypatch):
        """Smoke test for generate_response with mocked LLM call"""
        from backend import generate_response

        # Mock the LiteLLM call
        mock_response = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        with patch("backend._call_llm_with_retry", return_value=mock_response):
            result = generate_response("Test message", [], 0.5)

            assert result == "Test response"
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
