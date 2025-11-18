"""Abstract AI interface for research agents."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class AIInterface(ABC):
    """Abstract interface for AI operations required by research agents.

    This interface defines all AI operations that agents need to perform.
    Concrete implementations can use OpenAI, Anthropic, local models, or any other provider.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: str = "text",
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            response_format: Format of response ("text" or "json")

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate structured output matching a JSON schema.

        Args:
            prompt: The input prompt
            schema: JSON schema for the response
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Dictionary matching the schema
        """
        pass

    @abstractmethod
    async def generate_batch(
        self,
        prompts: List[str],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> List[str]:
        """Generate text for multiple prompts in batch.

        Args:
            prompts: List of input prompts
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate per prompt

        Returns:
            List of generated texts
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current AI model.

        Returns:
            Dictionary with model name, version, capabilities, etc.
        """
        pass
