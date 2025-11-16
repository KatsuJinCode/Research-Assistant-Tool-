"""
AI Client wrapper for OpenAI and Anthropic APIs.
Provides unified interface for both providers.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

# Import based on availability
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """AI Provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class AIClient:
    """
    Unified AI client for OpenAI and Anthropic.

    Provides consistent interface regardless of backend provider.
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        temperature: float = 0.5,
        max_tokens: int = 4000
    ):
        """
        Initialize AI client.

        Args:
            provider: 'openai' or 'anthropic'
            api_key: API key for the provider
            model: Model name
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.provider = AIProvider(provider)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize provider client
        if self.provider == AIProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = openai.OpenAI(api_key=api_key)

        elif self.provider == AIProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=api_key)

        logger.info(f"Initialized {self.provider.value} client with model {self.model}")

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: 'json' for JSON response, None for text
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        try:
            if self.provider == AIProvider.OPENAI:
                return await self._generate_openai(
                    prompt, temp, max_tok, response_format, system_prompt
                )
            elif self.provider == AIProvider.ANTHROPIC:
                return await self._generate_anthropic(
                    prompt, temp, max_tok, response_format, system_prompt
                )
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            raise

    async def _generate_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[str],
        system_prompt: Optional[str]
    ) -> str:
        """Generate using OpenAI API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format == 'json':
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def _generate_anthropic(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: Optional[str],
        system_prompt: Optional[str]
    ) -> str:
        """Generate using Anthropic API."""
        if response_format == 'json':
            # Add JSON instruction to prompt
            prompt += "\n\nRespond with valid JSON only."

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate structured output matching a schema.

        Args:
            prompt: Input prompt
            schema: JSON schema for response
            temperature: Sampling temperature

        Returns:
            Parsed JSON response
        """
        # Add schema to prompt
        schema_prompt = f"""{prompt}

Return JSON matching this schema:
```json
{json.dumps(schema, indent=2)}
```"""

        response = await self.generate(
            schema_prompt,
            temperature=temperature,
            response_format='json'
        )

        # Parse and validate
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {response}")
            raise ValueError(f"AI returned invalid JSON: {e}")

    async def batch_generate(
        self,
        prompts: List[str],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> List[str]:
        """
        Generate multiple completions.

        Args:
            prompts: List of prompts
            temperature: Sampling temperature
            max_tokens: Max tokens per response

        Returns:
            List of generated texts
        """
        # For MVP, process sequentially
        # TODO: Add parallel processing with rate limiting
        results = []
        for prompt in prompts:
            result = await self.generate(prompt, temperature, max_tokens)
            results.append(result)
        return results

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4

    async def check_equivalence(
        self,
        text1: str,
        text2: str
    ) -> Dict[str, Any]:
        """
        Check if two texts are semantically equivalent.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Dict with 'equivalent' (bool) and 'confidence' (float)
        """
        prompt = f"""Are these two texts semantically equivalent (same meaning)?

Text 1: "{text1}"
Text 2: "{text2}"

Respond with JSON:
{{
  "equivalent": true/false,
  "confidence": 0.0-1.0,
  "explanation": "brief explanation"
}}"""

        response = await self.generate(prompt, temperature=0.0, response_format='json')
        return json.loads(response)


def create_ai_client(config_provider) -> AIClient:
    """
    Factory function to create AI client from config.

    Args:
        config_provider: AIProviderConfig instance

    Returns:
        AIClient instance
    """
    return AIClient(
        provider=config_provider.api_key,  # This will be fixed in config
        api_key=config_provider.api_key,
        model=config_provider.model,
        temperature=config_provider.temperature,
        max_tokens=config_provider.max_tokens
    )
