"""OpenAI provider implementation."""

from typing import List, Optional, Dict, Any, Iterator
import openai
from openai import OpenAI

from ..interface import AIInterface, AIMessage, AIResponse, MessageRole


class OpenAIProvider(AIInterface):
    """OpenAI API provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (e.g., gpt-4, gpt-3.5-turbo)
            temperature: Default sampling temperature (0.0-2.0)
            max_tokens: Default maximum tokens
            **kwargs: Additional OpenAI client parameters
        """
        self.api_key = api_key
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens
        self.client = OpenAI(api_key=api_key, **kwargs)

    def generate(
        self,
        messages: List[AIMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate a response from OpenAI.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens (overrides default)
            **kwargs: Additional OpenAI completion parameters

        Returns:
            AIResponse with generated content
        """
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role if isinstance(msg.role, str) else msg.role.value, "content": msg.content}
            for msg in messages
        ]

        # Use provided values or defaults
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens if max_tokens is not None else self.default_max_tokens

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temp,
            max_tokens=max_tok,
            **kwargs,
        )

        # Extract response
        choice = response.choices[0]
        content = choice.message.content

        # Build usage stats
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return AIResponse(
            content=content,
            model=response.model,
            usage=usage,
            finish_reason=choice.finish_reason,
            metadata={
                "response_id": response.id,
                "created": response.created,
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
        Generate a streaming response from OpenAI.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides default)
            max_tokens: Maximum tokens (overrides default)
            **kwargs: Additional OpenAI completion parameters

        Yields:
            Chunks of generated content
        """
        # Convert messages to OpenAI format
        openai_messages = [
            {"role": msg.role if isinstance(msg.role, str) else msg.role.value, "content": msg.content}
            for msg in messages
        ]

        # Use provided values or defaults
        temp = temperature if temperature is not None else self.default_temperature
        max_tok = max_tokens if max_tokens is not None else self.default_max_tokens

        # Call OpenAI API with streaming
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temp,
            max_tokens=max_tok,
            stream=True,
            **kwargs,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        try:
            import tiktoken

            # Get encoding for model
            if "gpt-4" in self.model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in self.model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Fallback to cl100k_base (used by gpt-4 and gpt-3.5-turbo)
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))
        except ImportError:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": "openai",
            "model": self.model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "supports_streaming": True,
            "supports_system_messages": True,
        }
