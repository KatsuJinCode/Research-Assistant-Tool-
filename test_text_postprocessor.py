"""
Test Text Post-Processor

Tests the drop cap fix and quality scoring on the Szasz paper.
"""

from pathlib import Path
from research_agent.document_processing.pdf_extractor import PDFExtractor

pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

print("=" * 80)
print("TEXT POST-PROCESSOR TEST".center(80))
print("=" * 80)

# Extract WITH post-processing
print("\n1. EXTRACTION WITH POST-PROCESSING:")
print("-" * 80)
extractor = PDFExtractor(column_aware=True, postprocess=True)
result = extractor.extract(pdf_path)

print(f"Quality Score: {result.get('quality_score', 'N/A'):.2f}" if result.get('quality_score') else "Quality Score: N/A")
print(f"Text Changed: {result.get('text_changed', False)}")

if result.get('warnings'):
    print(f"\nWarnings ({len(result['warnings'])}):")
    for warning in result['warnings']:
        print(f"  - {warning}")

if result.get('postprocess_result'):
    pp = result['postprocess_result']
    if pp['fixes_applied']:
        print(f"\nFixes Applied:")
        for fix in pp['fixes_applied']:
            print(f"  - {fix}")

    if pp['quality_analysis']['issues']:
        print(f"\nQuality Issues:")
        for issue in pp['quality_analysis']['issues']:
            print(f"  - {issue}")

print(f"\n[FIRST 500 CHARS - AFTER POST-PROCESSING]:")
print(result['full_text'][:500])
print("...")

# Extract WITHOUT post-processing for comparison
print("\n\n2. EXTRACTION WITHOUT POST-PROCESSING (for comparison):")
print("-" * 80)
extractor_no_pp = PDFExtractor(column_aware=True, postprocess=False)
result_no_pp = extractor_no_pp.extract(pdf_path)

print(f"\n[FIRST 500 CHARS - BEFORE POST-PROCESSING]:")
print(result_no_pp['full_text'][:500])
print("...")

# Compare
print("\n\n3. COMPARISON:")
print("-" * 80)

if result['text_changed']:
    print("[SUCCESS] Text was modified by post-processor!")
    print("\nLook for 'My aim' vs 'Y aim' in the comparison above.")
else:
    print("[INFO] No changes made by post-processor")

print("\n" + "=" * 80)
print("TEST COMPLETE".center(80))
print("=" * 80)
