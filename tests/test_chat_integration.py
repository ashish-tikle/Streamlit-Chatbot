"""
Happy-path integration tests for chat completion function
Tests chat flow with mocked LLM responses (no real API calls)
Validates response structure, latency, and cost tracking
Run with: pytest tests/test_chat_integration.py -v
"""

import pytest
from unittest.mock import patch
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestChatHappyPath:
    """Test happy-path chat completion scenarios with mocked LLM"""

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_basic_success(self, mock_completion):
        """Test basic chat completion returns valid response structure"""
        from backend import generate_response

        mock_completion.return_value = {
            "id": "chatcmpl-test",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am a helpful AI assistant. How can I help you today?",
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 25, "completion_tokens": 15, "total_tokens": 40},
        }

        response = generate_response(
            user_message="Hello, who are you?",
            history=[],
            temperature=0.7,
            user_id="test-user-123",
            session_id="test-session-456",
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "AI assistant" in response or "helpful" in response.lower()
        assert mock_completion.call_count == 1

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_with_conversation_history(self, mock_completion):
        """Test chat completion with multi-turn conversation history"""
        from backend import generate_response

        mock_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Python is a high-level programming language known for readability.",
                }
            }],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }

        history = [
            {"role": "user", "content": "What is programming?"},
            {"role": "assistant", "content": "Programming is writing instructions for computers."},
            {"role": "user", "content": "Tell me about Python"},
        ]

        response = generate_response(
            user_message="Tell me about Python",
            history=history,
            temperature=0.5,
        )

        assert isinstance(response, str)
        assert len(response) > 0
        assert "Python" in response

        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs["messages"]

        assert len(messages) >= 4
        assert messages[0]["role"] == "system"
        assert any(msg["content"] == "What is programming?" for msg in messages)

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_latency_budget(self, mock_completion):
        """Test that response completes within generous latency budget"""
        from backend import generate_response

        mock_completion.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Quick response"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

        start = time.time()
        response = generate_response(user_message="Quick test", history=[], temperature=0.3)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Response took {elapsed:.2f}s (expected < 5s)"
        assert isinstance(response, str)
        assert len(response) > 0

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_cost_tracking(self, mock_completion):
        """Test that cost is calculated correctly from token usage"""
        from backend import generate_response, _calculate_cost

        mock_completion.return_value = {
            "choices": [{"message": {"content": "Test response for cost tracking"}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500, "total_tokens": 1500},
        }

        response = generate_response(
            user_message="Test cost calculation",
            history=[],
            temperature=0.5,
        )

        assert isinstance(response, str)

        expected_cost = (1000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        actual_cost = _calculate_cost({"prompt_tokens": 1000, "completion_tokens": 500})

        assert abs(actual_cost - expected_cost) < 0.0001

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_temperature_variations(self, mock_completion):
        """Test that different temperature values are passed correctly"""
        from backend import generate_response

        temperatures = [0.0, 0.5, 0.7, 1.0]

        for temp in temperatures:
            mock_completion.return_value = {
                "choices": [{"message": {"content": f"Response at temp {temp}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }

            response = generate_response(
                user_message=f"Test temperature {temp}",
                history=[],
                temperature=temp,
            )

            call_kwargs = mock_completion.call_args.kwargs
            assert call_kwargs["temperature"] == temp
            assert isinstance(response, str)

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_empty_history(self, mock_completion):
        """Test chat with no prior conversation history"""
        from backend import generate_response

        mock_completion.return_value = {
            "choices": [{"message": {"content": "First message in conversation"}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        }

        response = generate_response(
            user_message="Start new conversation",
            history=[],
            temperature=0.6,
        )

        assert isinstance(response, str)
        assert len(response) > 0

        call_kwargs = mock_completion.call_args.kwargs
        messages = call_kwargs["messages"]

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Start new conversation"


class TestChatTranscriptValidation:
    """Test complete chat transcript structure and flow"""

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_complete_conversation_transcript(self, mock_completion):
        """Test multi-turn conversation maintains proper structure"""
        from backend import generate_response

        conversation_transcript = []

        mock_completion.return_value = {
            "choices": [{
                "message": {"content": "AI stands for Artificial Intelligence."}
            }],
            "usage": {"prompt_tokens": 30, "completion_tokens": 25, "total_tokens": 55},
        }

        turn1_user = "What is AI?"
        turn1_response = generate_response(user_message=turn1_user, history=[], temperature=0.5)

        conversation_transcript.append({"role": "user", "content": turn1_user})
        conversation_transcript.append({"role": "assistant", "content": turn1_response})

        mock_completion.return_value = {
            "choices": [{
                "message": {"content": "Machine Learning is a subset of AI."}
            }],
            "usage": {"prompt_tokens": 60, "completion_tokens": 22, "total_tokens": 82},
        }

        turn2_user = "What about Machine Learning?"
        turn2_response = generate_response(user_message=turn2_user, history=conversation_transcript, temperature=0.5)

        conversation_transcript.append({"role": "user", "content": turn2_user})
        conversation_transcript.append({"role": "assistant", "content": turn2_response})

        assert len(conversation_transcript) == 4

        for i, msg in enumerate(conversation_transcript):
            expected_role = "user" if i % 2 == 0 else "assistant"
            assert msg["role"] == expected_role

        for msg in conversation_transcript:
            assert "content" in msg
            assert isinstance(msg["content"], str)
            assert len(msg["content"]) > 0


class TestErrorHandlingInChat:
    """Test error handling in chat completion flow"""

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_handles_missing_api_key(self, mock_completion):
        """Test graceful error message when API key is missing"""
        from backend import generate_response
        import backend

        original_key = backend.API_KEY
        backend.API_KEY = None

        response = generate_response(user_message="Test missing key", history=[], temperature=0.5)

        assert isinstance(response, str)
        assert "Configuration error" in response or "GEMINI_API_KEY" in response

        backend.API_KEY = original_key

    @patch("backend.completion")
    @patch("backend.langfuse_client", None)
    def test_generate_response_handles_empty_message(self, mock_completion):
        """Test handling of empty user message"""
        from backend import generate_response

        mock_completion.return_value = {
            "choices": [{"message": {"content": "Please provide a message."}}],
            "usage": {"prompt_tokens": 15, "completion_tokens": 8, "total_tokens": 23},
        }

        response = generate_response(user_message="", history=[], temperature=0.5)
        assert isinstance(response, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])