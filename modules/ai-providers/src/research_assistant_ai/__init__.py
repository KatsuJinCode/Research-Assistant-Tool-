"""Research Assistant AI - AI provider abstractions.

This module provides AI provider interfaces and implementations
for OpenAI and Anthropic models.
"""

from .interface import AIInterface, AIMessage, AIResponse, MessageRole
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider

__version__ = "0.1.0"

__all__ = [
    # Interfaces
    "AIInterface",
    "AIMessage",
    "AIResponse",
    "MessageRole",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
]
