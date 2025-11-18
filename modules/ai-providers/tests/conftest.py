"""Shared test fixtures for ai-providers tests."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_messages():
    """Sample AI messages."""
    from research_assistant_ai import AIMessage, MessageRole

    return [
        AIMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        AIMessage(role=MessageRole.USER, content="What is Python?"),
    ]


@pytest.fixture
def openai_config():
    """OpenAI configuration."""
    return {
        "api_key": "sk-test-key-1234567890",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4000,
    }


@pytest.fixture
def anthropic_config():
    """Anthropic configuration."""
    return {
        "api_key": "sk-ant-test-key-1234567890",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.5,
        "max_tokens": 8000,
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    response = Mock()
    response.id = "chatcmpl-123"
    response.model = "gpt-4"
    response.created = 1234567890

    choice = Mock()
    choice.message.content = "Python is a high-level programming language."
    choice.finish_reason = "stop"
    response.choices = [choice]

    usage = Mock()
    usage.prompt_tokens = 20
    usage.completion_tokens = 10
    usage.total_tokens = 30
    response.usage = usage

    return response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    response = Mock()
    response.id = "msg_123"
    response.model = "claude-3-5-sonnet-20241022"
    response.type = "message"
    response.stop_reason = "end_turn"

    content_block = Mock()
    content_block.text = "Python is a high-level programming language."
    response.content = [content_block]

    usage = Mock()
    usage.input_tokens = 20
    usage.output_tokens = 10
    response.usage = usage

    return response
