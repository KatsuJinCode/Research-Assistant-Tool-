"""Tests for OpenAI provider."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from research_assistant_ai import OpenAIProvider, AIMessage, MessageRole


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_initialization(self, mock_openai_class, openai_config):
        """Test initializing OpenAI provider."""
        provider = OpenAIProvider(**openai_config)

        assert provider.api_key == "sk-test-key-1234567890"
        assert provider.model == "gpt-4"
        assert provider.default_temperature == 0.7
        assert provider.default_max_tokens == 4000
        mock_openai_class.assert_called_once()

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_generate(self, mock_openai_class, openai_config, sample_messages, mock_openai_response):
        """Test generating a response."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(**openai_config)
        response = provider.generate(sample_messages)

        assert response.content == "Python is a high-level programming language."
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 30
        assert response.finish_reason == "stop"

        # Verify API was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 4000

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_generate_with_overrides(self, mock_openai_class, openai_config, sample_messages, mock_openai_response):
        """Test generating with parameter overrides."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(**openai_config)
        response = provider.generate(
            sample_messages,
            temperature=0.9,
            max_tokens=2000,
        )

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.9
        assert call_args.kwargs["max_tokens"] == 2000

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_generate_streaming(self, mock_openai_class, openai_config, sample_messages):
        """Test streaming generation."""
        # Mock streaming response
        chunk1 = Mock()
        chunk1.choices = [Mock()]
        chunk1.choices[0].delta.content = "Python "

        chunk2 = Mock()
        chunk2.choices = [Mock()]
        chunk2.choices[0].delta.content = "is great"

        chunk3 = Mock()
        chunk3.choices = [Mock()]
        chunk3.choices[0].delta.content = None  # End of stream

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = iter([chunk1, chunk2, chunk3])
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(**openai_config)
        chunks = list(provider.generate_streaming(sample_messages))

        assert chunks == ["Python ", "is great"]

        # Verify streaming was enabled
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["stream"] is True

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_count_tokens_with_tiktoken(self, mock_openai_class, openai_config):
        """Test token counting with tiktoken."""
        provider = OpenAIProvider(**openai_config)

        try:
            import tiktoken
            # If tiktoken is available, test actual counting
            count = provider.count_tokens("Hello world")
            assert count > 0
            assert isinstance(count, int)
        except ImportError:
            # If tiktoken not available, test fallback
            count = provider.count_tokens("Hello world")
            # Fallback: 11 characters / 4 ≈ 2-3 tokens
            assert count >= 2

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_count_tokens_fallback(self, mock_openai_class, openai_config):
        """Test token counting fallback when tiktoken unavailable."""
        provider = OpenAIProvider(**openai_config)

        with patch.dict("sys.modules", {"tiktoken": None}):
            count = provider.count_tokens("This is a test")
            # 14 characters / 4 = 3.5 ≈ 3 tokens
            assert count == 3

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_get_model_info(self, mock_openai_class, openai_config):
        """Test getting model information."""
        provider = OpenAIProvider(**openai_config)
        info = provider.get_model_info()

        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4"
        assert info["default_temperature"] == 0.7
        assert info["default_max_tokens"] == 4000
        assert info["supports_streaming"] is True
        assert info["supports_system_messages"] is True

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_message_conversion(self, mock_openai_class, openai_config, mock_openai_response):
        """Test that messages are correctly converted to OpenAI format."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(**openai_config)

        messages = [
            AIMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            AIMessage(role=MessageRole.USER, content="Hi"),
            AIMessage(role=MessageRole.ASSISTANT, content="Hello!"),
            AIMessage(role=MessageRole.USER, content="How are you?"),
        ]

        provider.generate(messages)

        call_args = mock_client.chat.completions.create.call_args
        openai_messages = call_args.kwargs["messages"]

        assert len(openai_messages) == 4
        assert openai_messages[0] == {"role": "system", "content": "You are helpful"}
        assert openai_messages[1] == {"role": "user", "content": "Hi"}
        assert openai_messages[2] == {"role": "assistant", "content": "Hello!"}
        assert openai_messages[3] == {"role": "user", "content": "How are you?"}

    @patch("research_assistant_ai.providers.openai_provider.OpenAI")
    def test_response_metadata(self, mock_openai_class, openai_config, sample_messages, mock_openai_response):
        """Test that response includes metadata."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(**openai_config)
        response = provider.generate(sample_messages)

        assert "response_id" in response.metadata
        assert response.metadata["response_id"] == "chatcmpl-123"
        assert "created" in response.metadata
        assert response.metadata["created"] == 1234567890
