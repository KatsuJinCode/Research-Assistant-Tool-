"""
Example usage of all NLP features.

Demonstrates:
1. Contradiction detection
2. Argument mining
3. Stance detection
4. Fact-checking
5. Entity extraction
"""

import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.nlp import (
    ContradictionDetector,
    ArgumentMiner,
    StanceDetector,
    FactChecker,
    EntityExtractor
)
from research_agent.graph_database import GraphDatabase


# Sample data
CLAIMS = [
    {
        "id": "claim_1",
        "text": "Artificial intelligence will revolutionize healthcare by 2030.",
        "original_text": "Artificial intelligence will revolutionize healthcare by 2030."
    },
    {
        "id": "claim_2",
        "text": "AI in healthcare poses significant risks to patient privacy.",
        "original_text": "AI in healthcare poses significant risks to patient privacy."
    },
    {
        "id": "claim_3",
        "text": "Machine learning models can diagnose diseases more accurately than human doctors.",
        "original_text": "Machine learning models can diagnose diseases more accurately than human doctors."
    }
]

DOCUMENT = {
    "id": "doc_1",
    "title": "The Future of AI in Healthcare",
    "content": """
    Artificial intelligence is transforming healthcare at an unprecedented pace.
    Dr. Sarah Johnson from MIT Medical School argues that AI-powered diagnostic
    tools have already achieved 95% accuracy in detecting certain cancers, surpassing
    the average human radiologist's 88% accuracy rate. Therefore, we can expect
    AI to become an essential tool in medical diagnosis.

    However, critics raise concerns about data privacy. Because AI systems require
    vast amounts of patient data for training, there is an inherent risk of data
    breaches. The HIPAA regulations in the United States may not be sufficient
    to protect patient information in the age of AI. Consequently, stronger
    privacy protections are needed.

    Research from Stanford University, published in Nature Medicine in 2023,
    demonstrated that deep learning algorithms could predict patient outcomes
    with 92% accuracy. This study involved collaboration between Stanford,
    Google Health, and Massachusetts General Hospital.
    """
}


async def example_contradiction_detection():
    """Example: Detect contradictions between claims."""
    print("\n" + "="*70)
    print("1. CONTRADICTION DETECTION")
    print("="*70)

    detector = ContradictionDetector()

    # Check for contradictions between claims
    result = await detector.detect_contradiction(
        claim1=CLAIMS[0],
        claim2=CLAIMS[1]
    )

    print(f"\nClaim 1: {CLAIMS[0]['text']}")
    print(f"Claim 2: {CLAIMS[1]['text']}")
    print(f"\nContradiction: {result.is_contradiction}")
    print(f"Type: {result.contradiction_type.value}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Explanation: {result.explanation}")
    print(f"Keywords: {', '.join(result.keywords)}")


async def example_argument_mining():
    """Example: Extract argument structures."""
    print("\n" + "="*70)
    print("2. ARGUMENT MINING")
    print("="*70)

    miner = ArgumentMiner()

    # Extract arguments from document
    arguments = await miner.extract_argument_structure(
        text=DOCUMENT['content'],
        doc_id=DOCUMENT['id']
    )

    print(f"\nFound {len(arguments)} arguments:\n")

    for i, arg in enumerate(arguments, 1):
        print(f"Argument {i}:")
        print(f"  Scheme: {arg.scheme.value}")
        print(f"  Confidence: {arg.confidence:.1f}%")
        print(f"  Premises ({len(arg.premises)}):")
        for j, prem in enumerate(arg.premises, 1):
            print(f"    {j}. {prem.text}")
        print(f"  Conclusion: {arg.conclusion.text}")
        print(f"  Indicators: {', '.join(arg.indicators)}")
        print()


async def example_stance_detection():
    """Example: Detect author stance toward claims."""
    print("\n" + "="*70)
    print("3. STANCE DETECTION")
    print("="*70)

    detector = StanceDetector()

    # Detect stance for each claim
    for claim in CLAIMS:
        result = await detector.detect_stance(
            claim=claim,
            document=DOCUMENT
        )

        print(f"\nClaim: {claim['text'][:70]}...")
        print(f"Stance: {result.stance.value.upper()}")
        print(f"Confidence: {result.confidence:.1f}%")
        print(f"Explanation: {result.explanation}")
        if result.supporting_quotes:
            print(f"Supporting quotes:")
            for quote in result.supporting_quotes[:2]:
                print(f"  - \"{quote}\"")


async def example_fact_checking():
    """Example: Automated fact-checking."""
    print("\n" + "="*70)
    print("4. FACT-CHECKING")
    print("="*70)

    checker = FactChecker()

    # Fact-check a claim
    result = await checker.fact_check_claim(CLAIMS[2])

    print(f"\nClaim: {result.claim_text}")
    print(f"Type: {result.claim_type.value}")
    print(f"Checkable: {result.is_checkable}")
    print(f"Truth Rating: {result.truth_rating.value.upper()}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"\nVerification Summary:")
    print(f"  {result.verification_summary}")

    if result.sources:
        print(f"\nSources ({len(result.sources)}):")
        for i, src in enumerate(result.sources, 1):
            print(f"  {i}. {src.source_name}")
            print(f"     Credibility: {src.credibility_score:.1f}%")
            print(f"     Info: {src.relevant_text[:100]}...")

    badge = checker.get_fact_check_badge(result.truth_rating)
    print(f"\nUI Badge: {badge['label']} ({badge['color']}, {badge['icon']})")


async def example_entity_extraction():
    """Example: Extract entities and relations."""
    print("\n" + "="*70)
    print("5. ENTITY AND RELATION EXTRACTION")
    print("="*70)

    extractor = EntityExtractor()

    # Extract entities and relations
    result = await extractor.extract_entities_and_relations(
        text=DOCUMENT['content'],
        doc_id=DOCUMENT['id']
    )

    print(f"\nExtracted {len(result.entities)} entities:")
    for entity in result.entities:
        print(f"  - {entity.text} ({entity.entity_type.value}, "
              f"confidence: {entity.confidence:.1f}%)")

    print(f"\nExtracted {len(result.relations)} relations:")
    for relation in result.relations:
        from_entity = next((e for e in result.entities if e.id == relation.from_entity_id), None)
        to_entity = next((e for e in result.entities if e.id == relation.to_entity_id), None)

        if from_entity and to_entity:
            print(f"  - {from_entity.text} --[{relation.relation_type.value}]--> {to_entity.text}")
            print(f"    Evidence: {relation.evidence_text[:80]}...")
            print(f"    Confidence: {relation.confidence:.1f}%")


async def example_complete_analysis():
    """Example: Complete NLP analysis of a document."""
    print("\n" + "="*70)
    print("6. COMPLETE NLP ANALYSIS")
    print("="*70)

    graph_db = GraphDatabase()

    # Create document node
    doc_node_id = graph_db.create_node('Document', DOCUMENT)

    # Create claim nodes
    for claim in CLAIMS:
        claim_node_id = graph_db.create_node('Claim', claim)
        graph_db.create_relationship(
            from_node=doc_node_id,
            to_node=claim_node_id,
            rel_type='CONTAINS',
            properties={}
        )

    print(f"\nRunning complete NLP analysis on document: {DOCUMENT['title']}")

    # 1. Extract entities
    entity_extractor = EntityExtractor()
    entity_result = await entity_extractor.extract_entities_and_relations(
        text=DOCUMENT['content'],
        doc_id=DOCUMENT['id']
    )
    entity_stats = entity_extractor.create_entity_graph(graph_db, entity_result)
    print(f"  ✓ Entity extraction: {entity_stats['entities']} entities, "
          f"{entity_stats['relations']} relations")

    # 2. Mine arguments
    argument_miner = ArgumentMiner()
    arguments = await argument_miner.extract_argument_structure(
        text=DOCUMENT['content'],
        doc_id=DOCUMENT['id']
    )
    arg_relations = await argument_miner.detect_argument_relations(arguments)
    arg_stats = await argument_miner.create_argument_graph(
        graph_db, arguments, arg_relations
    )
    print(f"  ✓ Argument mining: {arg_stats['arguments']} arguments, "
          f"{arg_stats['relations']} relations")

    # 3. Detect contradictions
    contradiction_detector = ContradictionDetector()
    contradictions = await contradiction_detector.detect_contradictions_batch(
        claims=CLAIMS,
        min_confidence=60.0
    )
    contr_count = await contradiction_detector.create_contradiction_relationships(
        graph_db, contradictions
    )
    print(f"  ✓ Contradiction detection: {len(contradictions)} contradictions found")

    # 4. Detect stances
    stance_detector = StanceDetector()
    stance_results = await stance_detector.detect_stances_batch(
        claim=CLAIMS[0],
        documents=[DOCUMENT]
    )
    stance_detector.add_stance_to_graph(graph_db, stance_results)
    print(f"  ✓ Stance detection: analyzed {len(stance_results)} stances")

    # 5. Fact-check claims
    fact_checker = FactChecker()
    fact_results = await fact_checker.fact_check_claims_batch(claims=CLAIMS)
    fact_checker.add_fact_check_to_graph(graph_db, fact_results)
    print(f"  ✓ Fact-checking: verified {len(fact_results)} claims")

    # Print graph statistics
    stats = graph_db.stats()
    print(f"\nGraph Statistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total relationships: {stats['total_relationships']}")
    print(f"  Node types: {stats['node_labels']}")
    print(f"  Relationship types: {stats['relationship_types']}")


async def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("ADVANCED NLP CAPABILITIES - EXAMPLES")
    print("="*70)

    await example_contradiction_detection()
    await example_argument_mining()
    await example_stance_detection()
    await example_fact_checking()
    await example_entity_extraction()
    await example_complete_analysis()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
