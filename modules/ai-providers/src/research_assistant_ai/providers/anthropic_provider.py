"""Anthropic provider implementation."""

from typing import List, Optional, Dict, Any, Iterator
import anthropic
from anthropic import Anthropic

from ..interface import AIInterface, AIMessage, AIResponse, MessageRole


class AnthropicProvider(AIInterface):
    """Anthropic API provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.5,
        max_tokens: int = 8000,
        **kwargs,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (e.g., claude-3-5-sonnet-20241022, claude-3-opus-20240229)
            temperature: Default sampling temperature (0.0-1.0)
            max_tokens: Default maximum tokens
            **kwargs: Additional Anthropic client parameters
        """
        self.api_key = api_key
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key, **kwargs)

    def generate(
        self,
        messages: List[AIMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate a response from Anthropic.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens (overrides default)
            **kwargs: Additional Anthropic message parameters

        Returns:
            AIResponse with generated content
        """
        # Extract system message if present
        system_message = None
        conversation_messages = []

        for msg in messages:
            role_str = msg.role if isinstance(msg.role, str) else msg.role.value
            if role_str == "system" or msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                conversation_messages.append(
                    {"role": role_str, "content": msg.content}
                )

        # Use provided values or defaults
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens if max_tokens is not None else self.default_max_tokens

        # Call Anthropic API
        create_kwargs = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs,
        }

        if system_message:
            create_kwargs["system"] = system_message

        response = self.client.messages.create(**create_kwargs)

        # Extract response content
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        # Build usage stats
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            }

        return AIResponse(
            content=content,
            model=response.model,
            usage=usage,
            finish_reason=response.stop_reason,
            metadata={
                "response_id": response.id,
                "type": response.type,
            },
        )

    def generate_streaming(
        self,
        messages: List[AIMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        Generate a streaming response from Anthropic.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens (overrides default)
            **kwargs: Additional Anthropic message parameters

        Yields:
            Chunks of generated content
        """
        # Extract system message if present
        system_message = None
        conversation_messages = []

        for msg in messages:
            role_str = msg.role if isinstance(msg.role, str) else msg.role.value
            if role_str == "system" or msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                conversation_messages.append(
                    {"role": role_str, "content": msg.content}
                )

        # Use provided values or defaults
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens if max_tokens is not None else self.default_max_tokens

        # Call Anthropic API with streaming
        create_kwargs = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs,
        }

        if system_message:
            create_kwargs["system"] = system_message

        with self.client.messages.stream(**create_kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Note: Anthropic uses different tokenization than OpenAI.
        This provides a rough estimate.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens (approximate)
        """
        # Anthropic doesn't provide a public tokenizer
        # Use rough estimate: 1 token ≈ 3.5 characters for Claude
        return int(len(text) / 3.5)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": "anthropic",
            "model": self.model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "supports_streaming": True,
            "supports_system_messages": True,
        }
