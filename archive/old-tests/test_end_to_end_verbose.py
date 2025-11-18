"""
Comprehensive End-to-End Test for Research Verification Agent System

This script demonstrates ALL working capabilities of the system:
1. PDF text extraction
2. Sentence segmentation
3. Qualifier extraction and analysis
4. Neo4j knowledge graph construction
5. Related research discovery via arXiv
6. Complete pipeline visualization

Shows ALL intermediate steps and outputs.
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import all working modules
from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.normalization.qualifier_extractor import QualifierExtractor
from research_agent.neo4j_database import Neo4jDatabase
from research_agent.research_apis.arxiv_client import ArxivClient


class EndToEndPipeline:
    """Complete end-to-end research verification pipeline with verbose output."""

    def __init__(self):
        """Initialize all components."""
        self.pdf_extractor = PDFExtractor()
        self.qualifier_extractor = QualifierExtractor()
        self.arxiv_client = ArxivClient()
        self.db = None

    def print_section(self, title: str, char: str = "="):
        """Print a section header."""
        print(f"\n{char * 80}")
        print(f"{title.center(80)}")
        print(f"{char * 80}\n")

    def print_subsection(self, title: str):
        """Print a subsection header."""
        print(f"\n--- {title} ---\n")

    def extract_sentences(self, text: str) -> List[str]:
        """
        Simple sentence extraction using regex.

        Args:
            text: Full text to segment

        Returns:
            List of sentences
        """
        # Clean up text
        text = re.sub(r'\s+', ' ', text)

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        # Filter out very short or empty sentences
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        return sentences

    def extract_key_claims(self, sentences: List[str], min_length: int = 50) -> List[str]:
        """
        Extract key claims from sentences.

        Focus on sentences that:
        - Are substantive (longer than min_length)
        - Contain verbs indicating claims (is, are, can, may, etc.)
        - Are not questions

        Args:
            sentences: List of sentences
            min_length: Minimum sentence length

        Returns:
            List of key claim sentences
        """
        claims = []

        for sentence in sentences:
            # Skip questions
            if sentence.strip().endswith('?'):
                continue

            # Skip very short sentences
            if len(sentence) < min_length:
                continue

            # Look for claim indicators
            claim_indicators = [
                r'\bis\b', r'\bare\b', r'\bcan\b', r'\bmay\b',
                r'\bmight\b', r'\bwill\b', r'\bshould\b', r'\bmust\b',
                r'\bsuggests?\b', r'\bindicates?\b', r'\bshows?\b',
                r'\bdemonstrates?\b', r'\bproves?\b'
            ]

            if any(re.search(pattern, sentence, re.I) for pattern in claim_indicators):
                claims.append(sentence)

        return claims

    def run_pipeline(self, pdf_path: Path):
        """
        Run complete end-to-end pipeline.

        Args:
            pdf_path: Path to PDF file
        """
        self.print_section("RESEARCH VERIFICATION AGENT - END-TO-END DEMONSTRATION")

        print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"PDF File: {pdf_path}")
        print(f"File exists: {pdf_path.exists()}")

        # ========================================================================
        # STEP 1: PDF EXTRACTION
        # ========================================================================
        self.print_section("STEP 1: PDF TEXT EXTRACTION", "=")

        print("Extracting text from PDF using pdfplumber...")
        extraction_result = self.pdf_extractor.extract(pdf_path)

        print(f"\nExtraction Results:")
        print(f"  - Pages: {extraction_result['page_count']}")
        print(f"  - Total characters: {extraction_result['total_chars']:,}")
        print(f"  - Average chars per page: {extraction_result['avg_chars_per_page']:,}")

        if extraction_result['metadata'].get('title'):
            print(f"  - Title: {extraction_result['metadata']['title']}")
        if extraction_result['metadata'].get('author'):
            print(f"  - Author: {extraction_result['metadata']['author']}")

        full_text = extraction_result['full_text']

        self.print_subsection("First 500 Characters of Extracted Text")
        print(full_text[:500])
        print("...")

        # ========================================================================
        # STEP 2: SENTENCE SEGMENTATION
        # ========================================================================
        self.print_section("STEP 2: SENTENCE SEGMENTATION", "=")

        print("Splitting text into sentences...")
        sentences = self.extract_sentences(full_text)

        print(f"\nSegmentation Results:")
        print(f"  - Total sentences: {len(sentences)}")

        self.print_subsection("Sample Sentences (first 10)")
        for i, sentence in enumerate(sentences[:10], 1):
            print(f"{i}. {sentence[:100]}{'...' if len(sentence) > 100 else ''}")

        # ========================================================================
        # STEP 3: CLAIM EXTRACTION
        # ========================================================================
        self.print_section("STEP 3: KEY CLAIM EXTRACTION", "=")

        print("Extracting key claims from sentences...")
        claims = self.extract_key_claims(sentences)

        print(f"\nClaim Extraction Results:")
        print(f"  - Total claims found: {len(claims)}")
        print(f"  - Percentage of sentences: {len(claims)/len(sentences)*100:.1f}%")

        self.print_subsection("Extracted Claims (first 10)")
        for i, claim in enumerate(claims[:10], 1):
            print(f"\n{i}. {claim}")

        # ========================================================================
        # STEP 4: QUALIFIER EXTRACTION
        # ========================================================================
        self.print_section("STEP 4: QUALIFIER EXTRACTION & ANALYSIS", "=")

        print("Analyzing qualifiers in each claim...")

        claim_analyses = []
        for claim in claims[:20]:  # Analyze first 20 claims in detail
            qualifiers = self.qualifier_extractor.extract(claim)
            strength = self.qualifier_extractor.analyze_claim_strength(claim)

            claim_analyses.append({
                'claim': claim,
                'qualifiers': qualifiers,
                'strength': strength
            })

        print(f"\nQualifier Analysis Results:")
        print(f"  - Claims analyzed: {len(claim_analyses)}")

        # Count qualifier types
        qualifier_type_counts = {}
        for analysis in claim_analyses:
            for q in analysis['qualifiers']:
                qtype = q['type']
                qualifier_type_counts[qtype] = qualifier_type_counts.get(qtype, 0) + 1

        print(f"\n  Qualifier Type Distribution:")
        for qtype, count in sorted(qualifier_type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {qtype}: {count}")

        # Show detailed analysis for first 5 claims
        self.print_subsection("Detailed Qualifier Analysis (first 5 claims)")
        for i, analysis in enumerate(claim_analyses[:5], 1):
            print(f"\nClaim {i}:")
            print(f"  Text: {analysis['claim'][:150]}...")
            print(f"  Strength: {analysis['strength']['strength'].upper()}")
            print(f"  Total qualifiers: {analysis['strength']['total_qualifiers']}")

            if analysis['qualifiers']:
                print(f"  Qualifiers found:")
                for q in analysis['qualifiers']:
                    print(f"    - {q['type'].upper()}: '{q['text']}' -> {q['impact']}")
            else:
                print(f"  No qualifiers found")

        # ========================================================================
        # STEP 5: NEO4J KNOWLEDGE GRAPH CONSTRUCTION
        # ========================================================================
        self.print_section("STEP 5: NEO4J KNOWLEDGE GRAPH CONSTRUCTION", "=")

        print("Connecting to Neo4j database...")
        try:
            self.db = Neo4jDatabase()
            print("  Connection successful!")

            # Get initial stats
            initial_stats = self.db.stats()
            print(f"\nInitial Database State:")
            print(f"  - Total nodes: {initial_stats['total_nodes']}")
            print(f"  - Total relationships: {initial_stats['total_relationships']}")

            # Create document node
            self.print_subsection("Creating Document Node")
            doc_id = self.db.create_node('Document', {
                'title': extraction_result['metadata'].get('title', 'Unknown'),
                'author': extraction_result['metadata'].get('author', 'Unknown'),
                'page_count': extraction_result['page_count'],
                'source_file': str(pdf_path.name),
                'processed_at': datetime.utcnow().isoformat()
            })
            print(f"  Document node created: {doc_id}")

            # Create claim nodes
            self.print_subsection("Creating Claim Nodes")
            print(f"Creating {len(claim_analyses)} claim nodes...")

            claim_ids = []
            for i, analysis in enumerate(claim_analyses, 1):
                claim_id = self.db.create_node('Claim', {
                    'text': analysis['claim'],
                    'strength': analysis['strength']['strength'],
                    'qualifier_count': analysis['strength']['total_qualifiers'],
                    'has_temporal': analysis['strength']['has_temporal_constraint'],
                    'has_percentage': analysis['strength']['has_percentage'],
                    'sequence_number': i
                })
                claim_ids.append(claim_id)

                # Link claim to document
                self.db.create_relationship(doc_id, claim_id, 'CONTAINS_CLAIM', {
                    'position': i
                })

                # Create qualifier nodes
                for q in analysis['qualifiers']:
                    qualifier_id = self.db.create_node('Qualifier', {
                        'type': q['type'],
                        'text': q['text'],
                        'impact': q['impact']
                    })

                    # Link qualifier to claim
                    self.db.create_relationship(claim_id, qualifier_id, 'HAS_QUALIFIER')

                if i % 5 == 0:
                    print(f"  Created {i}/{len(claim_analyses)} claims...")

            print(f"  All {len(claim_analyses)} claims created!")

            # Get final stats
            final_stats = self.db.stats()
            print(f"\nFinal Database State:")
            print(f"  - Total nodes: {final_stats['total_nodes']}")
            print(f"  - Total relationships: {final_stats['total_relationships']}")
            print(f"\n  Nodes by type:")
            for label, count in final_stats['node_labels'].items():
                print(f"    - {label}: {count}")
            print(f"\n  Relationships by type:")
            for rel_type, count in final_stats['relationship_types'].items():
                print(f"    - {rel_type}: {count}")

        except Exception as e:
            print(f"  ERROR connecting to Neo4j: {e}")
            print(f"  Skipping graph construction step...")

        # ========================================================================
        # STEP 6: RELATED RESEARCH DISCOVERY
        # ========================================================================
        self.print_section("STEP 6: RELATED RESEARCH DISCOVERY (arXiv)", "=")

        # Extract key terms from document for search
        doc_title = extraction_result['metadata'].get('title', '')

        # If no title, use first claim
        if not doc_title or doc_title == 'Unknown':
            search_query = claims[0][:100] if claims else "mental illness psychiatry"
        else:
            search_query = doc_title

        print(f"Searching arXiv for related papers...")
        print(f"Search query: {search_query}")

        try:
            related_papers = self.arxiv_client.search(search_query, max_results=5)

            print(f"\nSearch Results: {len(related_papers)} papers found")

            self.print_subsection("Related Papers from arXiv")
            for i, paper in enumerate(related_papers, 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   Authors: {', '.join(paper['authors'][:3])}")
                print(f"   Published: {paper.get('published', 'Unknown')}")
                print(f"   arXiv ID: {paper['id']}")
                print(f"   Categories: {', '.join(paper.get('categories', [])[:3])}")
                print(f"   Abstract: {paper['abstract'][:200]}...")

                # Add to Neo4j if connected
                if self.db:
                    paper_id = self.db.create_node('RelatedPaper', {
                        'title': paper['title'],
                        'authors': ', '.join(paper['authors']),
                        'arxiv_id': paper['id'],
                        'published': paper.get('published', ''),
                        'url': paper['url'],
                        'source': 'arXiv'
                    })

                    # Link to document
                    self.db.create_relationship(doc_id, paper_id, 'RELATED_TO', {
                        'search_query': search_query,
                        'relevance_rank': i
                    })

            if self.db:
                print(f"\n  Added {len(related_papers)} related papers to knowledge graph")

        except Exception as e:
            print(f"  ERROR searching arXiv: {e}")
            print(f"  Continuing without related papers...")

        # ========================================================================
        # STEP 7: FINAL SUMMARY
        # ========================================================================
        self.print_section("STEP 7: PIPELINE SUMMARY", "=")

        print("Processing Complete!")
        print(f"\nPipeline Results:")
        print(f"  PDF Extraction:")
        print(f"    - Pages processed: {extraction_result['page_count']}")
        print(f"    - Characters extracted: {extraction_result['total_chars']:,}")
        print(f"\n  Text Analysis:")
        print(f"    - Sentences found: {len(sentences)}")
        print(f"    - Key claims extracted: {len(claims)}")
        print(f"    - Claims analyzed: {len(claim_analyses)}")
        print(f"\n  Qualifier Analysis:")
        print(f"    - Total qualifiers found: {sum(qualifier_type_counts.values())}")
        print(f"    - Qualifier types: {len(qualifier_type_counts)}")
        print(f"    - Most common type: {max(qualifier_type_counts.items(), key=lambda x: x[1])[0] if qualifier_type_counts else 'N/A'}")

        if self.db:
            print(f"\n  Knowledge Graph:")
            print(f"    - Total nodes: {final_stats['total_nodes']}")
            print(f"    - Total relationships: {final_stats['total_relationships']}")
            print(f"    - Document nodes: {final_stats['node_labels'].get('Document', 0)}")
            print(f"    - Claim nodes: {final_stats['node_labels'].get('Claim', 0)}")
            print(f"    - Qualifier nodes: {final_stats['node_labels'].get('Qualifier', 0)}")
            print(f"    - Related paper nodes: {final_stats['node_labels'].get('RelatedPaper', 0)}")

        print(f"\n  Related Research:")
        print(f"    - arXiv papers found: {len(related_papers) if 'related_papers' in locals() else 0}")

        print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # ========================================================================
        # CLEANUP
        # ========================================================================
        if self.db:
            self.db.close()
            print("\nDatabase connection closed.")

        print("\n" + "=" * 80)
        print("END-TO-END TEST COMPLETE".center(80))
        print("=" * 80)


def main():
    """Run the end-to-end pipeline test."""
    # Use the short Szasz paper
    pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        print(f"Current directory: {Path.cwd()}")
        sys.exit(1)

    # Run pipeline
    pipeline = EndToEndPipeline()
    pipeline.run_pipeline(pdf_path)


if __name__ == "__main__":
    main()
