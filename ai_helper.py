#!/usr/bin/env python3
"""
AI Helper for Research Assistant
Provides AI-powered features like summarization and Q&A.
"""

import os
from typing import List, Dict, Optional


class AIHelper:
    """AI helper for document analysis."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI helper."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.has_api = bool(self.api_key)

        if self.has_api:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("Warning: openai package not installed. AI features disabled.")
                self.has_api = False

    def summarize(self, text: str, max_length: int = 200) -> str:
        """Summarize a document."""
        if not self.has_api:
            return self._simple_summarize(text, max_length)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research assistant that creates concise, informative summaries."},
                    {"role": "user", "content": f"Summarize the following text in about {max_length} words:\n\n{text}"}
                ],
                max_tokens=max_length * 2,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI summarization failed: {e}")
            return self._simple_summarize(text, max_length)

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
            return "AI features require OpenAI API key. Set OPENAI_API_KEY environment variable."

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant. Answer questions based on the provided context. If the answer is not in the context, say so."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"

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

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research assistant that extracts key points from documents."},
                    {"role": "user", "content": f"Extract the {num_points} most important key points from this text:\n\n{text}"}
                ],
                max_tokens=500,
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
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
            print(f"Key point extraction failed: {e}")
            return []

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

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a research assistant that suggests relevant tags for documents."},
                    {"role": "user", "content": f"Suggest {max_tags} relevant tags for this document. Return only the tags, separated by commas:\n\n{text[:1000]}"}
                ],
                max_tokens=100,
                temperature=0.3
            )
            tags_str = response.choices[0].message.content.strip()
            tags = [tag.strip() for tag in tags_str.split(',')]
            return tags[:max_tags]
        except Exception as e:
            print(f"Tag suggestion failed: {e}")
            return []


if __name__ == "__main__":
    # Test the AI helper
    ai = AIHelper()

    if ai.has_api:
        print("AI features enabled!")
    else:
        print("AI features disabled (no API key)")

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
