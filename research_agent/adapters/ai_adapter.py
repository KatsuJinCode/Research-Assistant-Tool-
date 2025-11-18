"""
AI adapter for research-agents module.

Implements the AIInterface using the existing AIClient.
"""

import logging
from typing import Optional, Dict, Any, List

from research_agent.utils.ai_client import AIClient

# Import from the standalone research-agents module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../research-agents/src'))

from research_agents import AIInterface


logger = logging.getLogger(__name__)


class AIAdapter(AIInterface):
    """
    Adapter that implements AIInterface using the existing AIClient.

    This allows the research-agents module to work with the existing AI infrastructure
    (OpenAI, Anthropic, etc.).
    """

    def __init__(self, ai_client: AIClient):
        """
        Initialize adapter.

        Args:
            ai_client: Existing AIClient instance
        """
        self.ai_client = ai_client

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        response_format: str = "text",
    ) -> str:
        """Generate text from a prompt."""
        return await self.ai_client.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Generate structured output matching a JSON schema."""
        # Use the existing generate method with json format
        response = await self.ai_client.generate(
            prompt=prompt,
            temperature=temperature,
            response_format="json",
        )

        # Parse and return as dict
        import json
        return json.loads(response)

    async def generate_batch(
        self,
        prompts: List[str],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> List[str]:
        """Generate text for multiple prompts in batch."""
        # Current AIClient doesn't support batch, so do sequentially
        results = []
        for prompt in prompts:
            result = await self.ai_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            results.append(result)
        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current AI model."""
        return {
            "provider": getattr(self.ai_client, "provider", "unknown"),
            "model": getattr(self.ai_client, "model", "unknown"),
            "capabilities": ["text_generation", "json_output"],
        }
