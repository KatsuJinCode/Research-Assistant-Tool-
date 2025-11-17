"""
Test Column-Aware Extraction

Compares old (broken) vs new (column-aware) PDF extraction.
"""

from pathlib import Path
from research_agent.document_processing.pdf_extractor import PDFExtractor

pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

print("=" * 80)
print("COMPARING EXTRACTION METHODS".center(80))
print("=" * 80)

# Old method (column-unaware)
print("\n1. OLD METHOD (Column-Unaware):")
print("-" * 80)
old_extractor = PDFExtractor(column_aware=False)
old_result = old_extractor.extract(pdf_path)

print(f"Total chars: {old_result['total_chars']:,}")
print("\nFirst 300 chars:")
print(old_result['full_text'][:300])
print("...")

# New method (column-aware)
print("\n\n2. NEW METHOD (Column-Aware):")
print("-" * 80)
new_extractor = PDFExtractor(column_aware=True)
new_result = new_extractor.extract(pdf_path)

print(f"Total chars: {new_result['total_chars']:,}")

# Show warnings
if new_result.get('warnings'):
    print("\n[WARNINGS]:")
    for warning in new_result['warnings']:
        print(f"  - {warning}")

print("\nFirst 300 chars:")
print(new_result['full_text'][:300])
print("...")

# Show column layout info
print("\n\n3. COLUMN LAYOUT ANALYSIS:")
print("-" * 80)
col_info = new_result.get('column_layout', {})
print(f"Total pages: {col_info.get('total_pages', 0)}")
print(f"Multi-column pages: {len(col_info.get('multi_column_pages', []))}")
print(f"Single-column pages: {len(col_info.get('single_column_pages', []))}")

if col_info.get('multi_column_pages'):
    print("\nMulti-column page details:")
    for page_info in col_info['multi_column_pages'][:3]:
        print(f"  Page {page_info['page']}: {page_info['num_columns']} columns, "
              f"boundary at X={page_info['boundary_x']:.1f}")

if col_info.get('recommendations'):
    print("\n[RECOMMENDATIONS]:")
    for rec in col_info['recommendations']:
        print(f"  - {rec}")

print("\n" + "=" * 80)
print("COMPARISON COMPLETE".center(80))
print("=" * 80)

# Calculate difference
chars_diff = new_result['total_chars'] - old_result['total_chars']
print(f"\nChar count difference: {chars_diff:+,} chars")
print(f"Extraction method: {'Column-aware' if chars_diff > 0 else 'No difference'}")
