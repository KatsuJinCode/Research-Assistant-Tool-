"""
Build Full Research Graph

Demonstrates the complete vision:
1. Sentence-level tracking
2. Source attribution
3. Evidence integration
4. Agent tracking
5. Citation network

Creates a rich, navigable research graph in Neo4j.
"""

from pathlib import Path
from research_agent.neo4j_database import Neo4jDatabase
from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.graph_enrichment import (
    SentenceTracker,
    EvidenceManager,
    AgentTracker,
    CitationNetwork
)


def print_section(title: str, char: str = "="):
    """Print section header."""
    print(f"\n{char * 80}")
    print(f"{title.center(80)}")
    print(f"{char * 80}\n")


def main():
    """Build the full research graph."""

    print_section("BUILDING FULL RESEARCH GRAPH")

    pdf_path = Path("sample papers/SHORT-The-Myth-of-Mental-Illness.pdf")

    # Initialize components
    db = Neo4jDatabase()
    pdf_extractor = PDFExtractor(column_aware=True, postprocess=True)
    sentence_tracker = SentenceTracker()
    evidence_manager = EvidenceManager()
    agent_tracker = AgentTracker()
    citation_network = CitationNetwork()

    # ========================================================================
    # STEP 1: Extract Document with Quality Checking
    # ========================================================================
    print_section("STEP 1: DOCUMENT EXTRACTION", "-")

    print(f"Extracting: {pdf_path.name}")
    extraction_result = pdf_extractor.extract(pdf_path)

    print(f"  Pages: {extraction_result['page_count']}")
    print(f"  Chars: {extraction_result['total_chars']:,}")
    print(f"  Quality Score: {extraction_result.get('quality_score', 'N/A'):.2f}" if extraction_result.get('quality_score') else "  Quality Score: N/A")

    if extraction_result.get('warnings'):
        print(f"\n  Warnings ({len(extraction_result['warnings'])}):")
        for warning in extraction_result['warnings'][:5]:
            print(f"    - {warning}")

    # ========================================================================
    # STEP 2: Sentence-Level Tracking
    # ========================================================================
    print_section("STEP 2: SENTENCE-LEVEL TRACKING", "-")

    # Get document from database
    docs = db.find_nodes('Document')
    if not docs:
        print("[ERROR] No documents in database. Run test_end_to_end_verbose.py first.")
        return

    document_id = docs[0]['id']
    print(f"Document ID: {document_id}")

    # Extract sentences with locations
    print("\nExtracting sentences with location tracking...")
    sentences = sentence_tracker.extract_sentences_with_location(
        extraction_result['full_text'],
        document_id,
        str(pdf_path)
    )

    print(f"  Sentences extracted: {len(sentences)}")
    print(f"\n  Sample sentences:")
    for i, sent in enumerate(sentences[:3], 1):
        print(f"    {i}. Page {sent['page']}, Lines {sent['start_line']}-{sent['end_line']}")
        print(f"       {sent['text'][:100]}...")

    # Create Sentence nodes in Neo4j
    print("\nCreating Sentence nodes in Neo4j...")
    sentence_ids = sentence_tracker.create_sentence_nodes_in_neo4j(sentences, db)
    print(f"  Created {len(sentence_ids)} Sentence nodes")

    # Link Claims to Sentences
    print("\nLinking Claims to Sentences...")
    claims = db.find_nodes('Claim', {'is_optimal': True})
    links_created = sentence_tracker.link_claims_to_sentences(claims, sentences, db)
    print(f"  Created {links_created} EXTRACTED_FROM relationships")

    # ========================================================================
    # STEP 3: Evidence Integration
    # ========================================================================
    print_section("STEP 3: EVIDENCE INTEGRATION", "-")

    print("Creating sample evidence entries...")

    # Evidence 1: Supporting
    evidence1 = evidence_manager.create_evidence(
        title="Rethinking Mental Illness: A Critical Analysis",
        source_type="research_paper",
        url="https://example.com/paper1",
        authors=["Smith, J.", "Jones, M."],
        publication_date="2023-05-15",
        abstract="This study examines the conceptual foundations of mental illness...",
        doi="10.1234/example.001"
    )

    evidence1_id = evidence_manager.create_evidence_node_in_neo4j(evidence1, db)
    print(f"  Created evidence: {evidence1['title']}")

    # Link to a claim (supporting)
    if claims:
        evidence_manager.link_evidence_to_claim(
            evidence1_id,
            claims[0]['id'],
            'SUPPORTS',
            strength=0.85,
            notes="Strongly supports the conceptual argument",
            db=db
        )
        print(f"  Linked evidence to claim (SUPPORTS, strength: 0.85)")

    # Evidence 2: Contradicting
    evidence2 = evidence_manager.create_evidence(
        title="Biological Basis of Mental Disorders",
        source_type="research_paper",
        url="https://example.com/paper2",
        authors=["Brown, A."],
        publication_date="2022-11-20",
        abstract="Evidence for neurological basis of mental illness...",
        doi="10.1234/example.002"
    )

    evidence2_id = evidence_manager.create_evidence_node_in_neo4j(evidence2, db)
    print(f"  Created evidence: {evidence2['title']}")

    if len(claims) > 1:
        evidence_manager.link_evidence_to_claim(
            evidence2_id,
            claims[1]['id'],
            'CONTRADICTS',
            strength=0.65,
            notes="Presents opposing view based on neuroscience",
            db=db
        )
        print(f"  Linked evidence to claim (CONTRADICTS, strength: 0.65)")

    # ========================================================================
    # STEP 4: Agent Tracking
    # ========================================================================
    print_section("STEP 4: AGENT TRACKING", "-")

    print("Creating Agent nodes...")

    # Create agents
    agent1_id = agent_tracker.create_agent_node_in_neo4j(
        agent_name="ResearchAgent-Alpha",
        agent_type="research",
        capabilities=["literature_search", "claim_validation"],
        db=db
    )
    print(f"  Created agent: ResearchAgent-Alpha")

    agent2_id = agent_tracker.create_agent_node_in_neo4j(
        agent_name="SynthesisAgent-Beta",
        agent_type="synthesis",
        capabilities=["evidence_synthesis", "contradiction_resolution"],
        db=db
    )
    print(f"  Created agent: SynthesisAgent-Beta")

    # Create research results
    print("\nCreating research results...")

    if len(claims) >= 2:
        result1 = agent_tracker.create_research_result(
            agent_name="ResearchAgent-Alpha",
            claim_id=claims[0]['id'],
            findings="Found 5 supporting papers and 2 contradicting studies",
            status="completed",
            confidence=0.82,
            sources_found=[evidence1['id'], evidence2['id']]
        )

        result1_id = agent_tracker.create_research_result_node_in_neo4j(result1, db)
        print(f"  Created research result: {result1['findings'][:50]}...")

        # Link result to evidence
        agent_tracker.link_result_to_evidence(result1_id, evidence1_id, db)
        agent_tracker.link_result_to_evidence(result1_id, evidence2_id, db)
        print(f"  Linked research result to {len(result1['sources_found'])} evidence items")

    # ========================================================================
    # STEP 5: Citation Network
    # ========================================================================
    print_section("STEP 5: CITATION NETWORK", "-")

    print("Building citation network...")

    if len(claims) >= 3:
        # Create citation relationships
        citation_network.create_citation(
            claims[0]['id'],
            claims[1]['id'],
            'supports',
            context="This claim provides foundational support",
            db=db
        )
        print(f"  Created citation: Claim 1 -> Claim 2 (supports)")

        citation_network.create_citation(
            claims[1]['id'],
            claims[2]['id'],
            'extends',
            context="Further develops the argument",
            db=db
        )
        print(f"  Created citation: Claim 2 -> Claim 3 (extends)")

        # Create document citations
        citation_network.create_document_citation(
            claims[0]['id'],
            document_id,
            page=1,
            line_number=15,
            quote="Mental illness is not literally a 'thing'",
            db=db
        )
        print(f"  Created document citation: Claim 1 cited on page 1, line 15")

    # ========================================================================
    # STEP 6: Graph Statistics
    # ========================================================================
    print_section("STEP 6: GRAPH STATISTICS", "-")

    stats = db.stats()

    print(f"Total Nodes: {stats['total_nodes']}")
    print(f"Total Relationships: {stats['total_relationships']}")
    print(f"\nNode Types:")
    for label, count in sorted(stats['node_labels'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count}")

    print(f"\nRelationship Types:")
    for rel_type, count in sorted(stats['relationship_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")

    # Research stats
    print("\nResearch Activity:")
    research_stats = agent_tracker.get_research_stats(db)
    print(f"  Total research results: {research_stats['total_research_results']}")
    print(f"  Active agents: {research_stats['active_agents']}")
    print(f"  Completed: {research_stats['completed']}")
    print(f"  In progress: {research_stats['in_progress']}")

    # ========================================================================
    # STEP 7: Navigation Queries
    # ========================================================================
    print_section("STEP 7: NAVIGATION QUERIES", "-")

    print("Sample Neo4j queries for graph navigation:\n")

    print("1. See Full Research Graph:")
    print("-" * 80)
    print("""
MATCH (c:Claim)
WHERE c.is_optimal = true
OPTIONAL MATCH (c)-[r1:EXTRACTED_FROM]->(s:Sentence)
OPTIONAL MATCH (c)-[r2:SUPPORTS|CONTRADICTS]-(e:Evidence)
OPTIONAL MATCH (c)<-[r3:INVESTIGATES]-(res:ResearchResult)
OPTIONAL MATCH (c)-[r4:CITES]-(other:Claim)
RETURN c, r1, s, r2, e, r3, res, r4, other
LIMIT 100
    """.strip())

    print("\n2. Click Claim -> See Exact Source Locations:")
    print("-" * 80)
    print("""
MATCH (c:Claim {text: "Your claim text here"})
MATCH (c)-[:EXTRACTED_FROM]->(s:Sentence)
MATCH (s)-[:IN_DOCUMENT]->(d:Document)
RETURN c.text as Claim,
       s.text as Sentence,
       s.page as Page,
       s.start_line as StartLine,
       s.end_line as EndLine,
       d.title as Document
    """.strip())

    print("\n3. See Agent Research History for a Claim:")
    print("-" * 80)
    print("""
MATCH (c:Claim)-[:INVESTIGATES]-(res:ResearchResult)
MATCH (res)-[:PERFORMED_BY]->(a:Agent)
OPTIONAL MATCH (res)-[:FOUND_EVIDENCE]->(e:Evidence)
RETURN a.name as Agent,
       res.findings as Findings,
       res.confidence as Confidence,
       collect(e.title) as EvidenceFound
ORDER BY res.started_at DESC
    """.strip())

    print("\n4. See Evidence Balance for a Claim:")
    print("-" * 80)
    print("""
MATCH (c:Claim {text: "Your claim text"})
OPTIONAL MATCH (e_support:Evidence)-[:SUPPORTS]->(c)
OPTIONAL MATCH (e_contra:Evidence)-[:CONTRADICTS]->(c)
RETURN c.text as Claim,
       count(DISTINCT e_support) as Supporting,
       count(DISTINCT e_contra) as Contradicting
    """.strip())

    print("\n5. Navigate Citation Network:")
    print("-" * 80)
    print("""
MATCH path = (c1:Claim)-[:CITES*1..3]->(c2:Claim)
RETURN path
LIMIT 50
    """.strip())

    # ========================================================================
    # COMPLETE
    # ========================================================================
    print_section("BUILD COMPLETE")

    print("[SUCCESS] Full research graph built!")
    print(f"\nOpen Neo4j Browser: http://localhost:7474")
    print(f"Login: neo4j / research123")
    print(f"\nPaste any of the queries above to navigate the graph.")
    print(f"\nYou now have:")
    print(f"  - Sentence-level tracking (click claim -> see exact location)")
    print(f"  - Evidence integration (supporting/contradicting papers)")
    print(f"  - Agent tracking (see which agent researched what)")
    print(f"  - Citation network (how claims reference each other)")
    print(f"  - Rich, navigable research graph!")

    db.close()


if __name__ == "__main__":
    main()
