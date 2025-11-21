"""
Reprocess Szasz Paper with Column-Aware Extraction

This script:
1. Clears existing claims from the database
2. Re-extracts the Szasz paper using column-aware extraction
3. Re-builds the claim hierarchy with proper text
4. Generates updated visualization
"""

import sys
from pathlib import Path
from datetime import datetime

from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.neo4j_database import Neo4jDatabase


def print_section(title: str, char: str = "="):
    """Print a section header."""
    print(f"\n{char * 80}")
    print(f"{title.center(80)}")
    print(f"{char * 80}\n")


def main():
    """Reprocess the Szasz paper with column-aware extraction."""

    print_section("REPROCESSING WITH COLUMN-AWARE EXTRACTION")

    pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

    if not pdf_path.exists():
        print(f"[ERROR] PDF file not found: {pdf_path}")
        sys.exit(1)

    # ========================================================================
    # STEP 1: Clear existing claims
    # ========================================================================
    print_section("STEP 1: CLEARING OLD CLAIMS", "-")

    print("Connecting to Neo4j...")
    db = Neo4jDatabase()

    # Get initial stats
    initial_stats = db.stats()
    print(f"\nInitial Database State:")
    print(f"  - Total nodes: {initial_stats['total_nodes']}")
    print(f"  - Documents: {initial_stats['node_labels'].get('Document', 0)}")
    print(f"  - Claims: {initial_stats['node_labels'].get('Claim', 0)}")
    print(f"  - Qualifiers: {initial_stats['node_labels'].get('Qualifier', 0)}")

    print("\nClearing all Document, Claim, and Qualifier nodes...")

    # Delete all documents and their claims
    query = """
    MATCH (d:Document)
    OPTIONAL MATCH (d)-[:CONTAINS_CLAIM]->(c:Claim)
    OPTIONAL MATCH (c)-[:HAS_QUALIFIER]->(q:Qualifier)
    OPTIONAL MATCH (c)-[r:PARENT_OF|SUPPORTS|OVERLAPS]-()
    DETACH DELETE d, c, q
    """
    with db.driver.session(database=db.database) as session:
        session.run(query)

    # Get stats after clearing
    cleared_stats = db.stats()
    print(f"\nDatabase State After Clearing:")
    print(f"  - Total nodes: {cleared_stats['total_nodes']}")
    print(f"  - Documents: {cleared_stats['node_labels'].get('Document', 0)}")
    print(f"  - Claims: {cleared_stats['node_labels'].get('Claim', 0)}")
    print(f"  - Qualifiers: {cleared_stats['node_labels'].get('Qualifier', 0)}")

    # ========================================================================
    # STEP 2: Extract with column awareness
    # ========================================================================
    print_section("STEP 2: EXTRACTING WITH COLUMN DETECTION", "-")

    print("Creating column-aware PDF extractor...")
    extractor = PDFExtractor(column_aware=True)

    print(f"Extracting: {pdf_path.name}")
    result = extractor.extract(pdf_path)

    print(f"\nExtraction Results:")
    print(f"  - Pages: {result['page_count']}")
    print(f"  - Total chars: {result['total_chars']:,}")
    print(f"  - Avg chars/page: {result['avg_chars_per_page']:,}")

    # Show warnings
    if result.get('warnings'):
        print(f"\n[WARNINGS]:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    # Show column layout
    if result.get('column_layout'):
        col_info = result['column_layout']
        print(f"\n[COLUMN LAYOUT]:")
        print(f"  - Total pages: {col_info.get('total_pages', 0)}")
        print(f"  - Multi-column pages: {len(col_info.get('multi_column_pages', []))}")
        print(f"  - Single-column pages: {len(col_info.get('single_column_pages', []))}")

        if col_info.get('recommendations'):
            print(f"\n  Recommendations:")
            for rec in col_info['recommendations']:
                print(f"    - {rec}")

    print(f"\n[TEXT SAMPLE - First 500 chars]:")
    print(result['full_text'][:500])
    print("...")

    # ========================================================================
    # STEP 3: Show comparison
    # ========================================================================
    print_section("STEP 3: COMPARISON", "-")

    print("Extracting with OLD method (column-unaware) for comparison...")
    old_extractor = PDFExtractor(column_aware=False)
    old_result = old_extractor.extract(pdf_path)

    print(f"\nOLD METHOD (Column-Unaware):")
    print(f"  Total chars: {old_result['total_chars']:,}")
    print(f"\n  First 500 chars:")
    print(old_result['full_text'][:500])
    print("...")

    print(f"\nNEW METHOD (Column-Aware):")
    print(f"  Total chars: {result['total_chars']:,}")
    print(f"\n  First 500 chars:")
    print(result['full_text'][:500])
    print("...")

    chars_diff = result['total_chars'] - old_result['total_chars']
    print(f"\n[COMPARISON]:")
    print(f"  Char count difference: {chars_diff:+,} chars")
    print(f"  Method: {'Column-aware extraction produces better text' if chars_diff != 0 else 'Same'}")

    # ========================================================================
    # CLEANUP
    # ========================================================================
    db.close()
    print("\nDatabase connection closed.")

    print_section("REPROCESSING COMPLETE")

    print("[NEXT STEPS]:")
    print("  1. Run: python test_end_to_end_verbose.py")
    print("     (This will create claims from the properly extracted text)")
    print("")
    print("  2. Run: python build_optimal_hierarchy.py")
    print("     (This will build the hierarchical structure)")
    print("")
    print("  3. Run: python view_hierarchy.py")
    print("     (This will show the visualization)")


if __name__ == "__main__":
    main()
