"""
Base NLP processor with AI client integration.

Provides common functionality for all NLP modules.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add research_agent to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from research_agent.utils.ai_client import AIClient, AIProvider
from research_agent.config import load_config

logger = logging.getLogger(__name__)


class BaseNLPProcessor:
    """
    Base class for NLP processors.

    Provides AI client integration and common utilities.
    """

    def __init__(self, ai_client: Optional[AIClient] = None):
        """
        Initialize NLP processor.

        Args:
            ai_client: Optional AI client. If not provided, creates from config.
        """
        if ai_client is None:
            # Load from config
            try:
                config = load_config()
                default_provider = config.default_provider
                provider_config = config.ai_providers.get(default_provider)

                if not provider_config:
                    raise ValueError(f"No configuration for provider: {default_provider}")

                self.ai_client = AIClient(
                    provider=default_provider,
                    api_key=provider_config.api_key,
                    model=provider_config.model,
                    temperature=provider_config.temperature,
                    max_tokens=provider_config.max_tokens
                )
                logger.info(f"Initialized AI client with provider: {default_provider}")
            except Exception as e:
                logger.error(f"Failed to initialize AI client from config: {e}")
                raise
        else:
            self.ai_client = ai_client

    async def analyze_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Analyze text with structured output.

        Args:
            prompt: Analysis prompt
            schema: Expected JSON schema
            temperature: Sampling temperature

        Returns:
            Parsed JSON response
        """
        try:
            return await self.ai_client.generate_with_schema(
                prompt=prompt,
                schema=schema,
                temperature=temperature
            )
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise

    async def analyze_text(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Analyze text with free-form output.

        Args:
            prompt: Analysis prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text
        """
        try:
            return await self.ai_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"AI text analysis failed: {e}")
            raise

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (character-based).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0-1.0)
        """
        # Simple character-level similarity
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract top keywords from text (simple word frequency).

        Args:
            text: Input text
            top_n: Number of keywords to extract

        Returns:
            List of keywords
        """
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how'
        }

        words = text.lower().split()
        word_freq = {}

        for word in words:
            # Clean word
            word = ''.join(c for c in word if c.isalnum())
            if word and word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]

    def chunk_text(self, text: str, max_chunk_size: int = 2000) -> List[str]:
        """
        Split text into chunks for processing.

        Args:
            text: Input text
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        # Split by sentences (simple approach)
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
