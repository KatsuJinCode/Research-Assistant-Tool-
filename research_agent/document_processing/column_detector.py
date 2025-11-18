"""
Column Layout Detector

Detects multi-column layouts in PDFs and extracts text in proper reading order.
"""

import statistics
from typing import List, Dict, Tuple, Optional
import pdfplumber


class ColumnDetector:
    """Detects and handles multi-column PDF layouts."""

    def __init__(self, column_threshold: float = 0.4):
        """
        Initialize column detector.

        Args:
            column_threshold: Minimum ratio of chars in each column to detect multi-column
                             (0.4 = at least 40% of chars must be in each half)
        """
        self.column_threshold = column_threshold

    def detect_columns(self, page) -> Tuple[bool, int, Optional[float]]:
        """
        Detect if a PDF page has multiple columns.

        Args:
            page: pdfplumber page object

        Returns:
            (is_multi_column, num_columns, column_boundary_x)
        """
        chars = page.chars
        if not chars:
            return False, 1, None

        # Get x-coordinates of all characters
        x_positions = [c['x0'] for c in chars]

        page_width = page.width
        midpoint = page_width / 2

        # Count chars in left and right halves
        left_chars = sum(1 for x in x_positions if x < midpoint)
        right_chars = sum(1 for x in x_positions if x >= midpoint)

        total_chars = len(x_positions)

        left_ratio = left_chars / total_chars if total_chars > 0 else 0
        right_ratio = right_chars / total_chars if total_chars > 0 else 0

        # If both sides have significant text, it's multi-column
        is_multi_column = (
            left_ratio >= self.column_threshold and
            right_ratio >= self.column_threshold
        )

        if is_multi_column:
            # Find the actual boundary (gap between columns)
            # Sort x-positions and look for largest gap near middle
            sorted_x = sorted(set(x_positions))

            # Look for gaps in the middle 50% of page
            quarter = page_width / 4
            middle_region = [x for x in sorted_x if quarter < x < 3 * quarter]

            if middle_region:
                # Find largest gap
                gaps = []
                for i in range(len(middle_region) - 1):
                    gap_start = middle_region[i]
                    gap_end = middle_region[i + 1]
                    gap_size = gap_end - gap_start
                    gaps.append((gap_size, (gap_start + gap_end) / 2))

                if gaps:
                    # Use the largest gap as column boundary
                    largest_gap = max(gaps, key=lambda x: x[0])
                    boundary = largest_gap[1]
                    return True, 2, boundary

            return True, 2, midpoint

        return False, 1, None

    def extract_column_text(self, page, column_boundary: float) -> Tuple[str, str]:
        """
        Extract text from left and right columns separately.

        Args:
            page: pdfplumber page object
            column_boundary: X-coordinate separating columns

        Returns:
            (left_column_text, right_column_text)
        """
        # Extract text from left column (x < boundary)
        left_bbox = (0, 0, column_boundary, page.height)
        left_crop = page.crop(left_bbox)
        left_text = left_crop.extract_text() or ""

        # Extract text from right column (x >= boundary)
        right_bbox = (column_boundary, 0, page.width, page.height)
        right_crop = page.crop(right_bbox)
        right_text = right_crop.extract_text() or ""

        return left_text, right_text

    def extract_text_in_reading_order(self, page) -> str:
        """
        Extract text in proper reading order (handles multi-column).

        Args:
            page: pdfplumber page object

        Returns:
            Text in reading order
        """
        is_multi_column, num_columns, boundary = self.detect_columns(page)

        if not is_multi_column:
            # Single column - normal extraction
            return page.extract_text() or ""

        # Multi-column - extract each column and combine
        left_text, right_text = self.extract_column_text(page, boundary)

        # Combine: left column first, then right column
        return left_text + "\n\n" + right_text

    def analyze_pdf(self, pdf_path: str) -> Dict:
        """
        Analyze entire PDF for column layout.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Analysis results including warnings
        """
        results = {
            'total_pages': 0,
            'multi_column_pages': [],
            'single_column_pages': [],
            'warnings': [],
            'recommendations': []
        }

        with pdfplumber.open(pdf_path) as pdf:
            results['total_pages'] = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                is_multi, num_cols, boundary = self.detect_columns(page)

                if is_multi:
                    results['multi_column_pages'].append({
                        'page': i + 1,
                        'num_columns': num_cols,
                        'boundary_x': boundary
                    })
                else:
                    results['single_column_pages'].append(i + 1)

        # Generate warnings
        if results['multi_column_pages']:
            num_multi = len(results['multi_column_pages'])
            results['warnings'].append(
                f"MULTI-COLUMN LAYOUT DETECTED on {num_multi}/{results['total_pages']} pages"
            )
            results['warnings'].append(
                "Standard PDF extraction will produce NONSENSE text (reading across columns)"
            )

            results['recommendations'].append(
                "Use ColumnDetector.extract_text_in_reading_order() for proper extraction"
            )
            results['recommendations'].append(
                "Or use PDFExtractor with column_aware=True parameter"
            )

        return results


def quick_check(pdf_path: str) -> bool:
    """
    Quick check if PDF has multi-column layout.

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if multi-column detected
    """
    detector = ColumnDetector()

    with pdfplumber.open(pdf_path) as pdf:
        # Check first page
        if pdf.pages:
            is_multi, _, _ = detector.detect_columns(pdf.pages[0])
            return is_multi

    return False
