"""
Build Optimal Claim Hierarchy - Rigorous Mathematical Approach

This script performs sophisticated claim space analysis using:
1. Semantic embeddings (sentence-transformers/SBERT) for true semantic similarity
2. Information-theoretic redundancy detection
3. Subsumption analysis (detecting when one claim fully contains another)
4. Hierarchical structure discovery based on specificity
5. Optimal spanning set computation (minimal non-redundant representation)

This is NOT simple clustering - this finds the mathematically optimal
representation of the claim space with zero duplication and maximum coverage.
"""

import sys
from pathlib import Path
from typing import List, Dict
from research_agent.neo4j_database import Neo4jDatabase
from research_agent.claim_analysis import ClaimSpaceOptimizer, RelationType


def fetch_claims_from_neo4j(db: Neo4jDatabase) -> List[Dict]:
    """Fetch all claims from Neo4j database."""
    print("\n--- Fetching Claims from Neo4j ---\n")

    claims = db.find_nodes('Claim')

    print(f"Found {len(claims)} claims in database")

    return claims


def analyze_claim_space(claims: List[Dict]) -> Dict:
    """
    Perform rigorous claim space analysis.

    Returns optimization results.
    """
    print("\n" + "=" * 80)
    print("RIGOROUS CLAIM SPACE OPTIMIZATION".center(80))
    print("=" * 80)

    # Initialize optimizer
    optimizer = ClaimSpaceOptimizer()

    # Add all claims to analysis
    print(f"\nAdding {len(claims)} claims to optimizer...")
    for claim in claims:
        optimizer.add_claim(
            claim_id=claim['id'],
            text=claim.get('text', '')
        )

    # Run optimization
    results = optimizer.optimize()

    return results


def clear_existing_hierarchy(db: Neo4jDatabase):
    """Remove existing SuperClaim nodes and hierarchy relationships."""
    print("\n--- Clearing Existing Hierarchy ---\n")

    query = """
    // Delete existing SuperClaims and their relationships
    MATCH (sc:SuperClaim)
    DETACH DELETE sc
    """

    with db.driver.session(database=db.database) as session:
        session.run(query)

    # Also clear SIMILAR_TO relationships (we'll rebuild them properly)
    query = """
    MATCH ()-[r:SIMILAR_TO]-()
    DELETE r
    """

    with db.driver.session(database=db.database) as session:
        session.run(query)

    print("Cleared existing hierarchy")


def build_neo4j_hierarchy(db: Neo4jDatabase, results: Dict):
    """
    Build optimized hierarchy in Neo4j based on analysis results.

    Args:
        db: Neo4j database connection
        results: Optimization results from ClaimSpaceOptimizer
    """
    print("\n--- Building Optimized Hierarchy in Neo4j ---\n")

    optimal_claims = results['optimal_claims']
    redundant_claims = results['redundant_claims']
    hierarchy = results['hierarchy']
    claim_nodes = results['claim_nodes']
    relationships = results['relationships']

    print(f"Optimal claims: {len(optimal_claims)}")
    print(f"Redundant claims: {len(redundant_claims)}")
    print(f"Hierarchy edges: {len(hierarchy)}")

    # Step 1: Mark redundant claims in database
    print("\nStep 1: Marking redundant claims...")
    for claim_id in redundant_claims:
        node = claim_nodes[claim_id]

        query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.is_redundant = true,
            c.subsumed_by = $subsumed_by,
            c.information_content = $info_content
        """

        with db.driver.session(database=db.database) as session:
            session.run(
                query,
                claim_id=claim_id,
                subsumed_by=node.subsumed_by,
                info_content=node.information_content
            )

    print(f"Marked {len(redundant_claims)} claims as redundant")

    # Step 2: Update optimal claims with analysis metrics
    print("\nStep 2: Updating optimal claims with metrics...")
    for claim_id in optimal_claims:
        node = claim_nodes[claim_id]

        query = """
        MATCH (c:Claim {id: $claim_id})
        SET c.is_redundant = false,
            c.specificity_score = $specificity,
            c.information_content = $info_content,
            c.is_optimal = true
        """

        with db.driver.session(database=db.database) as session:
            session.run(
                query,
                claim_id=claim_id,
                specificity=node.specificity_score,
                info_content=node.information_content
            )

    print(f"Updated {len(optimal_claims)} optimal claims")

    # Step 3: Create hierarchical PARENT_OF relationships
    print("\nStep 3: Creating hierarchical relationships...")
    parent_of_count = 0

    for parent_id, child_ids in hierarchy.items():
        for child_id in child_ids:
            # Get relationship type
            rel_key = (parent_id, child_id)
            rel_type = relationships.get(rel_key, RelationType.INDEPENDENT)

            # Create PARENT_OF relationship
            query = """
            MATCH (parent:Claim {id: $parent_id})
            MATCH (child:Claim {id: $child_id})
            CREATE (parent)-[r:PARENT_OF {
                relationship_type: $rel_type,
                specificity_delta: child.specificity_score - parent.specificity_score
            }]->(child)
            """

            with db.driver.session(database=db.database) as session:
                session.run(
                    query,
                    parent_id=parent_id,
                    child_id=child_id,
                    rel_type=rel_type.value
                )

            parent_of_count += 1

    print(f"Created {parent_of_count} PARENT_OF relationships")

    # Step 4: Create semantic relationship edges
    print("\nStep 4: Creating semantic relationships...")

    rel_counts = {
        RelationType.SUPPORTS: 0,
        RelationType.REFINES: 0,
        RelationType.OVERLAPS: 0
    }

    for (claim1_id, claim2_id), rel_type in relationships.items():
        # Skip redundant claims
        if claim1_id in redundant_claims or claim2_id in redundant_claims:
            continue

        # Only create relationships for optimal claims
        if claim1_id not in optimal_claims or claim2_id not in optimal_claims:
            continue

        # Create appropriate relationship type
        if rel_type == RelationType.SUPPORTS:
            db.create_relationship(
                claim1_id,
                claim2_id,
                'SUPPORTS',
                {'confidence': 0.7}
            )
            rel_counts[RelationType.SUPPORTS] += 1

        elif rel_type == RelationType.REFINES:
            # Already handled as PARENT_OF
            rel_counts[RelationType.REFINES] += 1

        elif rel_type == RelationType.OVERLAPS:
            db.create_relationship(
                claim1_id,
                claim2_id,
                'OVERLAPS',
                {'overlap_score': 0.5}
            )
            rel_counts[RelationType.OVERLAPS] += 1

    print(f"\nRelationship counts:")
    for rel_type, count in rel_counts.items():
        print(f"  {rel_type.value}: {count}")


def print_optimization_summary(results: Dict):
    """Print detailed optimization summary."""
    print("\n" + "=" * 80)
    print("OPTIMIZATION SUMMARY".center(80))
    print("=" * 80 + "\n")

    stats = results['statistics']

    print("Claim Space Coverage:")
    print(f"  Total claims analyzed: {stats['total_claims']}")
    print(f"  Optimal representation: {stats['optimal_claims']} claims")
    print(f"  Redundant claims: {stats['redundant_claims']}")
    print(f"  Space reduction: {(1 - stats['reduction_ratio']) * 100:.1f}%")

    print(f"\nHierarchical Structure:")
    print(f"  Hierarchy depth: {stats['hierarchy_depth']} levels")

    print(f"\nSemantic Analysis:")
    print(f"  Average specificity: {stats['avg_specificity']:.3f}")
    print(f"  Average information content: {stats['avg_information_content']:.3f}")

    print(f"\nRelationship Distribution:")
    for rel_type, count in stats['relationship_distribution'].items():
        print(f"  {rel_type}: {count}")

    print("\n" + "=" * 80)


def print_visualization_guide():
    """Print Neo4j visualization instructions."""
    print("\n" + "=" * 80)
    print("NEO4J VISUALIZATION".center(80))
    print("=" * 80 + "\n")

    print("Open Neo4j Browser: http://localhost:7474\n")

    print("Query 1: See Optimal Claim Set (non-redundant)")
    print("-" * 80)
    print("""
MATCH (c:Claim)
WHERE c.is_optimal = true
RETURN c.text as Claim,
       c.specificity_score as Specificity,
       c.information_content as UniquenessScore
ORDER BY c.information_content DESC
LIMIT 20
""")

    print("\nQuery 2: See Hierarchical Tree Structure")
    print("-" * 80)
    print("""
MATCH (parent:Claim)-[r:PARENT_OF]->(child:Claim)
WHERE parent.is_optimal = true AND child.is_optimal = true
RETURN parent, r, child
""")

    print("\nQuery 3: See Redundant Claims and What They're Subsumed By")
    print("-" * 80)
    print("""
MATCH (redundant:Claim)
WHERE redundant.is_redundant = true
MATCH (parent:Claim {id: redundant.subsumed_by})
RETURN redundant.text as RedundantClaim,
       parent.text as SubsumedBy
LIMIT 10
""")

    print("\nQuery 4: Find Root Claims (Most General)")
    print("-" * 80)
    print("""
MATCH (c:Claim)
WHERE c.is_optimal = true
  AND NOT ()-[:PARENT_OF]->(c)
RETURN c.text as RootClaim,
       c.specificity_score as Specificity
ORDER BY c.specificity_score ASC
""")

    print("\nQuery 5: Find Leaf Claims (Most Specific)")
    print("-" * 80)
    print("""
MATCH (c:Claim)
WHERE c.is_optimal = true
  AND NOT (c)-[:PARENT_OF]->()
RETURN c.text as LeafClaim,
       c.specificity_score as Specificity
ORDER BY c.specificity_score DESC
""")

    print("\n" + "=" * 80)


def main():
    """Run optimal hierarchy builder."""
    print("=" * 80)
    print("OPTIMAL CLAIM HIERARCHY BUILDER".center(80))
    print("=" * 80)

    # Connect to Neo4j
    db = Neo4jDatabase()

    try:
        # Fetch claims
        claims = fetch_claims_from_neo4j(db)

        if not claims:
            print("ERROR: No claims found in database")
            print("Run test_end_to_end_verbose.py first to populate claims")
            return

        # Clear existing hierarchy
        clear_existing_hierarchy(db)

        # Analyze claim space
        results = analyze_claim_space(claims)

        # Build optimized hierarchy in Neo4j
        build_neo4j_hierarchy(db, results)

        # Print summary
        print_optimization_summary(results)

        # Print visualization guide
        print_visualization_guide()

    finally:
        db.close()


if __name__ == "__main__":
    main()
