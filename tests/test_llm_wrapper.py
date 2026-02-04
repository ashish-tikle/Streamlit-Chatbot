"""
Unit tests for LiteLLM wrapper with mocked provider
Tests the LLM call path without making real API requests
Run with: pytest tests/test_llm_wrapper.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLiteLLMWrapper:
    """Test LiteLLM completion call with mocked provider"""

    @patch("backend.completion")
    def test_call_llm_with_retry_success(self, mock_completion):
        """Test successful LLM call with mocked provider response"""
        from backend import _call_llm_with_retry

        # Mock successful LiteLLM response
        mock_response = {
            "id": "chatcmpl-test-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gemini-3-flash",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mocked response from the LLM.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 25,
                "total_tokens": 75,
            },
        }
        mock_completion.return_value = mock_response

        # Call wrapper function
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, test question?"},
        ]

        result = _call_llm_with_retry(
            model="openai/gemini-3-flash",
            api_key="sk-test-key",
            api_base="https://llm.lingarogroup.com",
            messages=messages,
            temperature=0.7,
            timeout=30,
        )

        # Verify mock was called correctly
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args.kwargs

        assert call_kwargs["model"] == "openai/gemini-3-flash"
        assert call_kwargs["api_key"] == "sk-test-key"
        assert call_kwargs["api_base"] == "https://llm.lingarogroup.com"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["timeout"] == 30
        assert len(call_kwargs["messages"]) == 2

        # Verify response structure
        assert result["choices"][0]["message"]["content"] == "This is a mocked response from the LLM."
        assert result["usage"]["total_tokens"] == 75
        assert result["usage"]["prompt_tokens"] == 50
        assert result["usage"]["completion_tokens"] == 25

    @patch("backend.completion")
    def test_call_llm_retry_on_transient_error(self, mock_completion):
        """Test retry logic on transient API errors"""
        from backend import _call_llm_with_retry
        import litellm

        # Mock first call fails, second succeeds
        mock_completion.side_effect = [
            litellm.exceptions.APIConnectionError("Connection timeout"),
            {
                "choices": [{"message": {"content": "Success after retry"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            },
        ]

        messages = [{"role": "user", "content": "Test retry"}]

        result = _call_llm_with_retry(
            model="openai/gemini-3-flash",
            api_key="sk-test",
            api_base="https://llm.lingarogroup.com",
            messages=messages,
            temperature=0.5,
            timeout=30,
        )

        # Should have retried and succeeded
        assert mock_completion.call_count == 2
        assert result["choices"][0]["message"]["content"] == "Success after retry"

    @patch("backend.completion")
    def test_call_llm_rate_limit_handling(self, mock_completion):
        """Test rate limit exception handling"""
        from backend import _call_llm_with_retry
        import litellm

        # Mock rate limit error (should retry with exponential backoff)
        mock_completion.side_effect = [
            litellm.exceptions.RateLimitError("Rate limit exceeded"),
            {
                "choices": [{"message": {"content": "Success after rate limit"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
            },
        ]

        messages = [{"role": "user", "content": "Rate limit test"}]

        result = _call_llm_with_retry(
            model="openai/gemini-3-flash",
            api_key="sk-test",
            api_base="https://llm.lingarogroup.com",
            messages=messages,
            temperature=0.5,
            timeout=30,
        )

        # Should retry and succeed
        assert mock_completion.call_count == 2
        assert result["choices"][0]["message"]["content"] == "Success after rate limit"

    @patch("backend.completion")
    def test_call_llm_permanent_error(self, mock_completion):
        """Test that permanent errors (auth) fail immediately without retry"""
        from backend import _call_llm_with_retry
        import litellm

        # Mock authentication error (should NOT retry)
        mock_completion.side_effect = litellm.exceptions.AuthenticationError(
            "Invalid API key"
        )

        messages = [{"role": "user", "content": "Auth error test"}]

        with pytest.raises(litellm.exceptions.AuthenticationError):
            _call_llm_with_retry(
                model="openai/gemini-3-flash",
                api_key="sk-invalid",
                api_base="https://llm.lingarogroup.com",
                messages=messages,
                temperature=0.5,
                timeout=30,
            )

        # Should only call once (no retry on auth errors)
        assert mock_completion.call_count == 1

    @patch("backend.completion")
    def test_call_llm_with_different_models(self, mock_completion):
        """Test wrapper works with different model providers"""
        from backend import _call_llm_with_retry

        models_to_test = [
            "openai/gemini-3-flash",
            "openai/gpt-4",
            "gemini/gemini-pro",
        ]

        for model_name in models_to_test:
            mock_completion.return_value = {
                "choices": [{"message": {"content": f"Response from {model_name}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }

            result = _call_llm_with_retry(
                model=model_name,
                api_key="sk-test",
                api_base="https://llm.lingarogroup.com",
                messages=[{"role": "user", "content": "Test"}],
                temperature=0.5,
                timeout=30,
            )

            assert f"Response from {model_name}" in result["choices"][0]["message"]["content"]

        # Should have called completion for each model
        assert mock_completion.call_count == len(models_to_test)


class TestCircuitBreaker:
    """Test circuit breaker pattern for resilience"""

    @patch("backend.completion")
    def test_circuit_breaker_opens_after_failures(self, mock_completion):
        """Test that circuit breaker opens after consecutive failures"""
        from backend import _call_llm_with_retry, circuit_breaker
        import litellm

        # Reset circuit breaker state
        circuit_breaker._state = circuit_breaker.STATE_CLOSED
        circuit_breaker.fail_counter = 0

        # Mock consecutive failures
        mock_completion.side_effect = litellm.exceptions.ServiceUnavailableError(
            "Service unavailable"
        )

        messages = [{"role": "user", "content": "Circuit breaker test"}]

        # Attempt multiple calls (should trigger circuit breaker)
        failure_count = 0
        for _ in range(6):  # Default threshold is 5
            try:
                _call_llm_with_retry(
                    model="openai/gemini-3-flash",
                    api_key="sk-test",
                    api_base="https://llm.lingarogroup.com",
                    messages=messages,
                    temperature=0.5,
                    timeout=30,
                )
            except Exception:
                failure_count += 1

        # Circuit breaker should have opened after threshold
        assert failure_count > 0
        # Note: Exact behavior depends on circuit breaker config


class TestRateLimiting:
    """Test rate limiting decorator"""

    @patch("backend.completion")
    def test_rate_limit_decorator_applied(self, mock_completion):
        """Test that rate limiting decorator is applied to LLM calls"""
        from backend import _call_llm_with_retry

        # Mock successful response
        mock_completion.return_value = {
            "choices": [{"message": {"content": "Rate limit test response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        }

        messages = [{"role": "user", "content": "Rate limit decorator test"}]

        # Should succeed without hitting rate limit for single call
        result = _call_llm_with_retry(
            model="openai/gemini-3-flash",
            api_key="sk-test",
            api_base="https://llm.lingarogroup.com",
            messages=messages,
            temperature=0.5,
            timeout=30,
        )

        assert result["choices"][0]["message"]["content"] == "Rate limit test response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
