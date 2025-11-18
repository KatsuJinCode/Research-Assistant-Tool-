"""Tests for Anthropic provider."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from research_assistant_ai import AnthropicProvider, AIMessage, MessageRole


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_initialization(self, mock_anthropic_class, anthropic_config):
        """Test initializing Anthropic provider."""
        provider = AnthropicProvider(**anthropic_config)

        assert provider.api_key == "sk-ant-test-key-1234567890"
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.default_temperature == 0.5
        assert provider.default_max_tokens == 8000
        mock_anthropic_class.assert_called_once()

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_generate(self, mock_anthropic_class, anthropic_config, sample_messages, mock_anthropic_response):
        """Test generating a response."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)
        response = provider.generate(sample_messages)

        assert response.content == "Python is a high-level programming language."
        assert response.model == "claude-3-5-sonnet-20241022"
        assert response.usage["total_tokens"] == 30
        assert response.finish_reason == "end_turn"

        # Verify API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert call_args.kwargs["temperature"] == 0.5
        assert call_args.kwargs["max_tokens"] == 8000

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_generate_with_system_message(self, mock_anthropic_class, anthropic_config, mock_anthropic_response):
        """Test that system messages are handled correctly."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)

        messages = [
            AIMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            AIMessage(role=MessageRole.USER, content="What is Python?"),
        ]

        provider.generate(messages)

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["system"] == "You are a helpful assistant."
        # System message should not be in messages list
        assert len(call_args.kwargs["messages"]) == 1
        assert call_args.kwargs["messages"][0]["role"] == "user"

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_generate_without_system_message(self, mock_anthropic_class, anthropic_config, mock_anthropic_response):
        """Test generating without system message."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)

        messages = [
            AIMessage(role=MessageRole.USER, content="What is Python?"),
        ]

        provider.generate(messages)

        call_args = mock_client.messages.create.call_args
        # No system parameter should be passed
        assert "system" not in call_args.kwargs

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_generate_with_overrides(self, mock_anthropic_class, anthropic_config, sample_messages, mock_anthropic_response):
        """Test generating with parameter overrides."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)
        response = provider.generate(
            sample_messages,
            temperature=0.8,
            max_tokens=4000,
        )

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["temperature"] == 0.8
        assert call_args.kwargs["max_tokens"] == 4000

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_generate_streaming(self, mock_anthropic_class, anthropic_config, sample_messages):
        """Test streaming generation."""
        # Mock streaming response
        mock_stream = Mock()
        mock_stream.text_stream = iter(["Python ", "is ", "great"])
        mock_stream.__enter__ = Mock(return_value=mock_stream)
        mock_stream.__exit__ = Mock(return_value=False)

        mock_client = Mock()
        mock_client.messages.stream.return_value = mock_stream
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)
        chunks = list(provider.generate_streaming(sample_messages))

        assert chunks == ["Python ", "is ", "great"]

        # Verify streaming was called
        mock_client.messages.stream.assert_called_once()

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_count_tokens(self, mock_anthropic_class, anthropic_config):
        """Test token counting (approximate)."""
        provider = AnthropicProvider(**anthropic_config)

        # Test with known text
        count = provider.count_tokens("Hello world")
        # 11 characters / 3.5 ≈ 3 tokens
        assert count == 3

        # Test with longer text
        count = provider.count_tokens("This is a longer sentence with more words.")
        assert count > 0
        assert isinstance(count, int)

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_get_model_info(self, mock_anthropic_class, anthropic_config):
        """Test getting model information."""
        provider = AnthropicProvider(**anthropic_config)
        info = provider.get_model_info()

        assert info["provider"] == "anthropic"
        assert info["model"] == "claude-3-5-sonnet-20241022"
        assert info["default_temperature"] == 0.5
        assert info["default_max_tokens"] == 8000
        assert info["supports_streaming"] is True
        assert info["supports_system_messages"] is True

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_message_conversion(self, mock_anthropic_class, anthropic_config, mock_anthropic_response):
        """Test that messages are correctly converted to Anthropic format."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)

        messages = [
            AIMessage(role=MessageRole.SYSTEM, content="You are helpful"),
            AIMessage(role=MessageRole.USER, content="Hi"),
            AIMessage(role=MessageRole.ASSISTANT, content="Hello!"),
            AIMessage(role=MessageRole.USER, content="How are you?"),
        ]

        provider.generate(messages)

        call_args = mock_client.messages.create.call_args
        anthropic_messages = call_args.kwargs["messages"]

        # System message should be separate
        assert call_args.kwargs["system"] == "You are helpful"

        # Only non-system messages in messages list
        assert len(anthropic_messages) == 3
        assert anthropic_messages[0] == {"role": "user", "content": "Hi"}
        assert anthropic_messages[1] == {"role": "assistant", "content": "Hello!"}
        assert anthropic_messages[2] == {"role": "user", "content": "How are you?"}

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_response_metadata(self, mock_anthropic_class, anthropic_config, sample_messages, mock_anthropic_response):
        """Test that response includes metadata."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)
        response = provider.generate(sample_messages)

        assert "response_id" in response.metadata
        assert response.metadata["response_id"] == "msg_123"
        assert "type" in response.metadata
        assert response.metadata["type"] == "message"

    @patch("research_assistant_ai.providers.anthropic_provider.Anthropic")
    def test_multiple_content_blocks(self, mock_anthropic_class, anthropic_config, sample_messages):
        """Test handling multiple content blocks in response."""
        # Mock response with multiple content blocks
        response = Mock()
        response.id = "msg_123"
        response.model = "claude-3-5-sonnet-20241022"
        response.type = "message"
        response.stop_reason = "end_turn"

        block1 = Mock()
        block1.text = "First part. "
        block2 = Mock()
        block2.text = "Second part."
        response.content = [block1, block2]

        usage = Mock()
        usage.input_tokens = 10
        usage.output_tokens = 5
        response.usage = usage

        mock_client = Mock()
        mock_client.messages.create.return_value = response
        mock_anthropic_class.return_value = mock_client

        provider = AnthropicProvider(**anthropic_config)
        result = provider.generate(sample_messages)

        assert result.content == "First part. Second part."
