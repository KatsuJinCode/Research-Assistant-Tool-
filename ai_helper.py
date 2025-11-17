#!/usr/bin/env python3
"""
AI Helper for Research Assistant
Supports both OpenAI (ChatGPT) and Anthropic (Claude) models.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path


class AIHelper:
    """AI helper for document analysis with multi-provider support."""

    def __init__(self, config_file: str = ".research_config"):
        """Initialize AI helper with configuration."""
        self.config = self._load_config(config_file)
        self.provider = self.config.get('provider', 'openai')
        self.has_api = False
        self.client = None
        self.model = None

        # Initialize the configured provider
        if self.provider == 'openai':
            self._init_openai()
        elif self.provider == 'anthropic':
            self._init_anthropic()
        else:
            print(f"[WARNING] Unknown provider: {self.provider}")

    def _load_config(self, config_file: str) -> Dict[str, str]:
        """Load configuration from file."""
        config = {}
        config_path = Path(config_file)

        if config_path.exists():
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        # Remove quotes
                        value = value.strip('"').strip("'")
                        config[key] = value

            # Determine provider
            default_provider = config.get('DEFAULT_PROVIDER', 'openai')
            config['provider'] = default_provider

        return config

    def _init_openai(self):
        """Initialize OpenAI client."""
        api_key = self.config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')

        if not api_key:
            return

        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = self.config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
            self.has_api = True
            self.provider = 'openai'
        except ImportError:
            print("[WARNING] openai package not installed. Run: pip install openai")
        except Exception as e:
            print(f"[WARNING] OpenAI initialization failed: {e}")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        api_key = self.config.get('ANTHROPIC_API_KEY') or os.getenv('ANTHROPIC_API_KEY')

        if not api_key:
            return

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = self.config.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
            self.has_api = True
            self.provider = 'anthropic'
        except ImportError:
            print("[WARNING] anthropic package not installed. Run: pip install anthropic")
        except Exception as e:
            print(f"[WARNING] Anthropic initialization failed: {e}")

    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize a document."""
        if not self.has_api:
            return self._simple_summarize(text, max_length)

        prompt = f"Summarize the following text in about {max_length} words:\n\n{text}"

        try:
            if self.provider == 'openai':
                return self._openai_summarize(prompt, max_length)
            elif self.provider == 'anthropic':
                return self._anthropic_summarize(prompt, max_length)
        except Exception as e:
            print(f"[WARNING] AI summarization failed: {e}")
            return self._simple_summarize(text, max_length)

    def _openai_summarize(self, prompt: str, max_length: int) -> str:
        """Summarize using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a research assistant that creates concise, informative summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_length * 2,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()

    def _anthropic_summarize(self, prompt: str, max_length: int) -> str:
        """Summarize using Anthropic."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_length * 2,
            temperature=0.5,
            system="You are a research assistant that creates concise, informative summaries.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.strip()

    def _simple_summarize(self, text: str, max_length: int) -> str:
        """Simple non-AI summarization - just take first N words."""
        words = text.split()
        if len(words) <= max_length:
            return text

        # Take first and last parts
        first_part = " ".join(words[:max_length // 2])
        last_part = " ".join(words[-(max_length // 2):])
        return f"{first_part}\n\n[...]\n\n{last_part}"

    def answer_question(self, question: str, context: str) -> str:
        """Answer a question based on document context."""
        if not self.has_api:
            return "AI features require API key. Run: ./setup.sh"

        try:
            if self.provider == 'openai':
                return self._openai_answer(question, context)
            elif self.provider == 'anthropic':
                return self._anthropic_answer(question, context)
        except Exception as e:
            return f"Error: {e}"

    def _openai_answer(self, question: str, context: str) -> str:
        """Answer using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant. Answer questions based on the provided context. If the answer is not in the context, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def _anthropic_answer(self, question: str, context: str) -> str:
        """Answer using Anthropic."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.3,
            system="You are a helpful research assistant. Answer questions based on the provided context. If the answer is not in the context, say so.",
            messages=[
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
        )
        return message.content[0].text.strip()

    def extract_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """Extract key points from text."""
        if not self.has_api:
            # Simple extraction - first sentence of each paragraph
            paragraphs = text.split('\n\n')
            points = []
            for para in paragraphs[:num_points]:
                sentences = para.split('. ')
                if sentences:
                    points.append(sentences[0].strip() + '.')
            return points

        prompt = f"Extract the {num_points} most important key points from this text:\n\n{text}"

        try:
            if self.provider == 'openai':
                content = self._openai_extract(prompt)
            elif self.provider == 'anthropic':
                content = self._anthropic_extract(prompt)

            # Parse numbered list
            points = []
            for line in content.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering
                    point = line.lstrip('0123456789.-• ').strip()
                    if point:
                        points.append(point)
            return points
        except Exception as e:
            print(f"[WARNING] Key point extraction failed: {e}")
            return []

    def _openai_extract(self, prompt: str) -> str:
        """Extract using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a research assistant that extracts key points from documents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def _anthropic_extract(self, prompt: str) -> str:
        """Extract using Anthropic."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.3,
            system="You are a research assistant that extracts key points from documents.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.strip()

    def suggest_tags(self, text: str, max_tags: int = 5) -> List[str]:
        """Suggest tags for a document."""
        if not self.has_api:
            # Simple tag extraction - look for common words
            from collections import Counter
            import re

            # Remove common words
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            words = [w for w in words if w not in common_words]

            # Count and return most common
            counter = Counter(words)
            return [word for word, _ in counter.most_common(max_tags)]

        prompt = f"Suggest {max_tags} relevant tags for this document. Return only the tags, separated by commas:\n\n{text[:1000]}"

        try:
            if self.provider == 'openai':
                tags_str = self._openai_tags(prompt)
            elif self.provider == 'anthropic':
                tags_str = self._anthropic_tags(prompt)

            tags = [tag.strip() for tag in tags_str.split(',')]
            return tags[:max_tags]
        except Exception as e:
            print(f"[WARNING] Tag suggestion failed: {e}")
            return []

    def _openai_tags(self, prompt: str) -> str:
        """Generate tags using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a research assistant that suggests relevant tags for documents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def _anthropic_tags(self, prompt: str) -> str:
        """Generate tags using Anthropic."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            temperature=0.3,
            system="You are a research assistant that suggests relevant tags for documents.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text.strip()

    def get_provider_info(self) -> str:
        """Get information about the current provider."""
        if not self.has_api:
            return "No AI provider configured"
        return f"{self.provider.title()} - {self.model}"


if __name__ == "__main__":
    # Test the AI helper
    ai = AIHelper()

    if ai.has_api:
        print(f"[OK] AI features enabled: {ai.get_provider_info()}")
    else:
        print("[WARNING] AI features disabled (no API key)")
        print("Run: ./setup.sh")

    test_text = """
    Artificial intelligence (AI) is transforming the field of research and development.
    Machine learning algorithms can now process vast amounts of data and identify patterns
    that would be impossible for humans to detect manually. This has applications in
    medicine, climate science, and many other fields. However, there are also concerns
    about bias in AI systems and the need for transparency and accountability.
    """

    print("\nTest Summarization:")
    summary = ai.summarize(test_text)
    print(summary)

    print("\nTest Tags:")
    tags = ai.suggest_tags(test_text)
    print(tags)
