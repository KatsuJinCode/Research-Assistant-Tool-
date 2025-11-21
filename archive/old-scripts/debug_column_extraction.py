"""
Debug Column Extraction

Compare first 1500 chars to see the actual reading order difference.
"""

from pathlib import Path
from research_agent.document_processing.pdf_extractor import PDFExtractor

pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

print("=" * 80)
print("COLUMN EXTRACTION DEBUG".center(80))
print("=" * 80)

# Old method
print("\n1. OLD METHOD (Column-Unaware) - First 1500 chars:")
print("-" * 80)
old_extractor = PDFExtractor(column_aware=False)
old_result = old_extractor.extract(pdf_path)
print(old_result['full_text'][:1500])

# New method
print("\n\n2. NEW METHOD (Column-Aware) - First 1500 chars:")
print("-" * 80)
new_extractor = PDFExtractor(column_aware=True)
new_result = new_extractor.extract(pdf_path)
print(new_result['full_text'][:1500])

print("\n\n" + "=" * 80)
print("ANALYSIS".center(80))
print("=" * 80)

print("\nOLD: Look for text jumping between columns (nonsense)")
print("NEW: Look for proper reading order (left column, then right column)")
