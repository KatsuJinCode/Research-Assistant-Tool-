"""
DOCX file extractor
"""
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class DOCXExtractor:
    """Extract text from Microsoft Word (.docx) files"""

    def extract(self, file_path: Path) -> Dict:
        """
        Extract text from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            Dict with 'text', 'metadata', and 'quality_score'
        """
        try:
            # Import python-docx (install with: pip install python-docx)
            try:
                from docx import Document
            except ImportError:
                raise ImportError("python-docx package not installed. Install with: pip install python-docx")

            # Load the document
            doc = Document(file_path)

            # Extract text from paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:  # Skip empty paragraphs
                    paragraphs.append(text)

            # Combine all paragraphs
            text = '\n\n'.join(paragraphs)

            # Extract metadata
            char_count = len(text)
            word_count = len(text.split())
            paragraph_count = len(paragraphs)

            # Quality score - DOCX files are generally high quality
            quality_score = 1.0
            if char_count < 100:
                quality_score = 0.5  # Very short documents

            metadata = {
                'file_type': 'docx',
                'char_count': char_count,
                'word_count': word_count,
                'paragraph_count': paragraph_count
            }

            # Try to extract document properties
            try:
                core_props = doc.core_properties
                if core_props.title:
                    metadata['title'] = core_props.title
                if core_props.author:
                    metadata['author'] = core_props.author
                if core_props.created:
                    metadata['created'] = str(core_props.created)
            except:
                pass  # Properties might not be available

            logger.info(f"Extracted {word_count} words from {file_path.name}")

            return {
                'text': text,
                'metadata': metadata,
                'quality_score': quality_score
            }

        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise
