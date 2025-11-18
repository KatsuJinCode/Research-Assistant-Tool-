"""Tests for AI provider interfaces."""

import pytest
from pydantic import ValidationError

from research_assistant_ai.interface import (
    AIInterface,
    AIMessage,
    AIResponse,
    MessageRole,
)


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_message_roles(self):
        """Test message role values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"


class TestAIMessage:
    """Tests for AIMessage model."""

    def test_create_message(self):
        """Test creating an AI message."""
        msg = AIMessage(role=MessageRole.USER, content="Hello")

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_message_with_enum_value(self):
        """Test creating message with enum value."""
        msg = AIMessage(role="user", content="Hello")

        assert msg.role == MessageRole.USER

    def test_invalid_role(self):
        """Test that invalid role raises error."""
        with pytest.raises(ValidationError):
            AIMessage(role="invalid_role", content="Hello")

    def test_message_serialization(self):
        """Test message serialization."""
        msg = AIMessage(role=MessageRole.USER, content="Hello")

        data = msg.model_dump()
        assert data["role"] == "user"
        assert data["content"] == "Hello"


class TestAIResponse:
    """Tests for AIResponse model."""

    def test_create_response(self):
        """Test creating an AI response."""
        response = AIResponse(
            content="Hello, how can I help?",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
        )

        assert response.content == "Hello, how can I help?"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 15
        assert response.finish_reason == "stop"

    def test_response_without_usage(self):
        """Test creating response without usage stats."""
        response = AIResponse(content="Hello", model="gpt-4")

        assert response.content == "Hello"
        assert response.usage is None
        assert response.finish_reason is None

    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = AIResponse(
            content="Hello",
            model="gpt-4",
            metadata={"response_id": "123", "created": 1234567890},
        )

        assert response.metadata["response_id"] == "123"
        assert response.metadata["created"] == 1234567890

    def test_response_defaults(self):
        """Test response default values."""
        response = AIResponse(content="Hello", model="gpt-4")

        assert response.metadata == {}


class TestAIInterface:
    """Tests for AIInterface ABC."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that AIInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIInterface()

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {
            "generate",
            "generate_streaming",
            "count_tokens",
            "get_model_info",
        }

        assert set(AIInterface.__abstractmethods__) == abstract_methods
