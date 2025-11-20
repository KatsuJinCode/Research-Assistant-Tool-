"""
Plain text file extractor
"""
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class TXTExtractor:
    """Extract text from plain text files"""

    def extract(self, file_path: Path) -> Dict:
        """
        Extract text from a TXT file.

        Args:
            file_path: Path to the text file

        Returns:
            Dict with 'text', 'metadata', and 'quality_score'
        """
        try:
            # Read the file with UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()

            # Basic quality metrics
            char_count = len(text)
            word_count = len(text.split())
            line_count = len(text.splitlines())

            # Quality score based on content
            quality_score = 1.0  # Text files are already clean
            if char_count < 100:
                quality_score = 0.5  # Very short files might be incomplete

            metadata = {
                'file_type': 'txt',
                'char_count': char_count,
                'word_count': word_count,
                'line_count': line_count
            }

            logger.info(f"Extracted {word_count} words from {file_path.name}")

            return {
                'text': text,
                'metadata': metadata,
                'quality_score': quality_score
            }

        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
