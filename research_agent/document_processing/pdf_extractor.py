"""
PDF text extraction using pdfplumber with column detection.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any
import pdfplumber
from .column_detector import ColumnDetector


logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text and metadata from PDF files with column-awareness."""

    def __init__(self, column_aware: bool = True):
        """
        Initialize PDF extractor.

        Args:
            column_aware: If True, detects and handles multi-column layouts
        """
        self.column_aware = column_aware
        self.column_detector = ColumnDetector() if column_aware else None

    def extract(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with:
                - full_text: Complete text content
                - pages: List of page dicts with text
                - page_count: Number of pages
                - metadata: PDF metadata
                - warnings: List of warnings (e.g., multi-column detection)
                - column_layout: Info about column detection

        Raises:
            FileNotFoundError: If PDF file not found
            ValueError: If PDF cannot be processed
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        warnings = []
        column_info = {}

        try:
            # First, analyze for column layout if enabled
            if self.column_aware:
                column_analysis = self.column_detector.analyze_pdf(str(pdf_path))
                column_info = column_analysis
                warnings.extend(column_analysis.get('warnings', []))

            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                full_text = ""

                for i, page in enumerate(pdf.pages):
                    # Use column-aware extraction if enabled
                    if self.column_aware:
                        page_text = self.column_detector.extract_text_in_reading_order(page)
                    else:
                        page_text = page.extract_text() or ""

                    pages.append({
                        'page_number': i + 1,
                        'text': page_text,
                        'char_count': len(page_text)
                    })
                    full_text += page_text + "\n\n"

                # Extract PDF metadata
                metadata = {
                    'author': pdf.metadata.get('Author'),
                    'title': pdf.metadata.get('Title'),
                    'subject': pdf.metadata.get('Subject'),
                    'creator': pdf.metadata.get('Creator'),
                    'producer': pdf.metadata.get('Producer'),
                    'creation_date': pdf.metadata.get('CreationDate'),
                }

                result = {
                    'full_text': full_text.strip(),
                    'pages': pages,
                    'page_count': len(pages),
                    'metadata': metadata,
                    'total_chars': len(full_text),
                    'avg_chars_per_page': len(full_text) // len(pages) if pages else 0,
                    'warnings': warnings,
                    'column_layout': column_info
                }

                logger.info(
                    f"Extracted {result['page_count']} pages, "
                    f"{result['total_chars']} characters from {pdf_path.name}"
                )

                return result

        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to extract PDF: {e}")

    def extract_text_only(self, pdf_path: Path) -> str:
        """
        Extract only text content (no metadata).

        Args:
            pdf_path: Path to PDF file

        Returns:
            Full text content
        """
        result = self.extract(pdf_path)
        return result['full_text']

    def extract_page(self, pdf_path: Path, page_number: int) -> str:
        """
        Extract text from a specific page.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Page text

        Raises:
            ValueError: If page number invalid
        """
        with pdfplumber.open(pdf_path) as pdf:
            if page_number < 1 or page_number > len(pdf.pages):
                raise ValueError(
                    f"Page {page_number} out of range (1-{len(pdf.pages)})"
                )

            page = pdf.pages[page_number - 1]
            return page.extract_text() or ""

    def count_pages(self, pdf_path: Path) -> int:
        """
        Count pages in PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages
        """
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
