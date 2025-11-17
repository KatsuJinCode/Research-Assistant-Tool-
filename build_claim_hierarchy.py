"""
Build Claim Hierarchy and Similarity Relationships

This script analyzes existing claims in Neo4j and builds:
1. SIMILAR_TO relationships between related claims
2. SUPPORTS/CONTRADICTS relationships for evidence
3. SuperClaim nodes grouping similar claims
4. Hierarchical tree structure for visualization

Run this after extracting claims to enable hierarchical visualization.
"""

import re
from typing import List, Dict, Tuple
from collections import defaultdict
from research_agent.neo4j_database import Neo4jDatabase


class ClaimHierarchyBuilder:
    """Build hierarchical relationships between claims."""

    def __init__(self):
        self.db = Neo4jDatabase()

    def close(self):
        """Close database connection."""
        self.db.close()

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings.

        Uses simple word overlap approach.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize text
        def normalize(text):
            # Convert to lowercase
            text = text.lower()
            # Remove punctuation
            text = re.sub(r'[^\w\s]', ' ', text)
            # Split into words
            words = set(text.split())
            # Remove very common words
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                        'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was',
                        'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did'}
            words = words - stopwords
            return words

        words1 = normalize(text1)
        words2 = normalize(text2)

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def find_similar_claims(self, min_similarity: float = 0.3) -> List[Tuple[str, str, float]]:
        """
        Find pairs of similar claims.

        Args:
            min_similarity: Minimum similarity threshold

        Returns:
            List of (claim_id1, claim_id2, similarity_score) tuples
        """
        print(f"\n--- Finding Similar Claims (threshold: {min_similarity}) ---\n")

        # Get all claims
        claims = self.db.find_nodes('Claim')
        print(f"Analyzing {len(claims)} claims...")

        similar_pairs = []

        # Compare each pair
        for i, claim1 in enumerate(claims):
            for j, claim2 in enumerate(claims):
                if i >= j:  # Skip self-comparison and duplicates
                    continue

                similarity = self.calculate_text_similarity(
                    claim1.get('text', ''),
                    claim2.get('text', '')
                )

                if similarity >= min_similarity:
                    similar_pairs.append((
                        claim1['id'],
                        claim2['id'],
                        similarity
                    ))

        print(f"Found {len(similar_pairs)} similar claim pairs")
        return similar_pairs

    def create_similarity_relationships(self, similar_pairs: List[Tuple[str, str, float]]):
        """
        Create SIMILAR_TO relationships in graph.

        Args:
            similar_pairs: List of (claim_id1, claim_id2, similarity) tuples
        """
        print(f"\n--- Creating SIMILAR_TO Relationships ---\n")

        for claim1_id, claim2_id, score in similar_pairs:
            # Create bidirectional SIMILAR_TO relationship
            self.db.create_relationship(
                claim1_id,
                claim2_id,
                'SIMILAR_TO',
                {'score': score}
            )

        print(f"Created {len(similar_pairs)} SIMILAR_TO relationships")

    def find_claim_clusters(self, min_similarity: float = 0.5) -> List[List[str]]:
        """
        Find clusters of related claims using graph traversal.

        Args:
            min_similarity: Minimum similarity to consider claims in same cluster

        Returns:
            List of claim ID lists (each list is a cluster)
        """
        print(f"\n--- Finding Claim Clusters (threshold: {min_similarity}) ---\n")

        # Get all claims
        claims = self.db.find_nodes('Claim')
        claim_ids = {c['id'] for c in claims}

        clusters = []
        visited = set()

        for claim_id in claim_ids:
            if claim_id in visited:
                continue

            # Get cluster for this claim
            cluster = self.db.find_claim_cluster(claim_id, min_similarity)

            if len(cluster) > 1:  # Only keep clusters with multiple claims
                clusters.append(cluster)
                visited.update(cluster)

        print(f"Found {len(clusters)} claim clusters")
        for i, cluster in enumerate(clusters, 1):
            print(f"  Cluster {i}: {len(cluster)} claims")

        return clusters

    def create_super_claims(self, clusters: List[List[str]]) -> List[str]:
        """
        Create SuperClaim nodes from clusters.

        Args:
            clusters: List of claim ID lists

        Returns:
            List of created SuperClaim IDs
        """
        print(f"\n--- Creating SuperClaims ---\n")

        super_claim_ids = []

        for i, cluster in enumerate(clusters, 1):
            # Get claim texts
            claims = [self.db.get_node(claim_id) for claim_id in cluster]
            claim_texts = [c.get('text', '') for c in claims if c]

            if not claim_texts:
                continue

            # Create normalized text (use shortest claim as representative)
            normalized_text = min(claim_texts, key=len)

            # Calculate average confidence
            confidences = [c.get('confidence', 1.0) for c in claims if c]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0

            # Create super claim
            super_claim_id = self.db.create_super_claim(
                cluster,
                normalized_text,
                avg_confidence
            )

            super_claim_ids.append(super_claim_id)

            print(f"SuperClaim {i}: Merged {len(cluster)} claims")
            print(f"  Text: {normalized_text[:100]}...")

        print(f"\nCreated {len(super_claim_ids)} SuperClaims")
        return super_claim_ids

    def create_support_relationships(self, min_similarity: float = 0.4):
        """
        Create SUPPORTS relationships between claims and SuperClaims.

        Args:
            min_similarity: Minimum similarity for support relationship
        """
        print(f"\n--- Creating SUPPORTS Relationships ---\n")

        # Get all SuperClaims
        super_claims = self.db.find_nodes('SuperClaim')

        # Get all independent claims (not merged into SuperClaims)
        query = """
        MATCH (c:Claim)
        WHERE NOT (c)-[:MERGED_INTO]->(:SuperClaim)
        RETURN c
        """

        with self.db.driver.session(database=self.db.database) as session:
            result = session.run(query)
            independent_claims = [dict(record['c']) for record in result]

        print(f"Found {len(independent_claims)} independent claims")
        print(f"Found {len(super_claims)} super claims")

        supports_count = 0

        # Check if independent claims support any SuperClaims
        for claim in independent_claims:
            for super_claim in super_claims:
                similarity = self.calculate_text_similarity(
                    claim.get('text', ''),
                    super_claim.get('text', '')
                )

                if similarity >= min_similarity:
                    # Create SUPPORTS relationship
                    self.db.create_relationship(
                        claim['id'],
                        super_claim['id'],
                        'SUPPORTS',
                        {'strength': similarity}
                    )
                    supports_count += 1

        print(f"Created {supports_count} SUPPORTS relationships")

    def print_hierarchy_summary(self):
        """Print summary of hierarchical structure."""
        print("\n" + "=" * 80)
        print("HIERARCHICAL STRUCTURE SUMMARY".center(80))
        print("=" * 80 + "\n")

        stats = self.db.stats()

        print("Graph Statistics:")
        print(f"  Total nodes: {stats['total_nodes']}")
        print(f"  Total relationships: {stats['total_relationships']}")
        print("\nNode types:")
        for label, count in stats['node_labels'].items():
            print(f"  {label}: {count}")
        print("\nRelationship types:")
        for rel_type, count in stats['relationship_types'].items():
            print(f"  {rel_type}: {count}")

        # Show sample SuperClaim hierarchy
        super_claims = self.db.find_nodes('SuperClaim')
        if super_claims:
            print(f"\n--- Sample SuperClaim Hierarchy ---\n")
            sc = super_claims[0]
            print(f"SuperClaim: {sc.get('text', '')[:150]}...")
            print(f"  Member count: {sc.get('member_count', 0)}")
            print(f"  Confidence: {sc.get('confidence', 0.0):.2f}")

            # Get merged claims
            query = """
            MATCH (c:Claim)-[r:MERGED_INTO]->(sc:SuperClaim {id: $sc_id})
            RETURN c.text as text, r.verbatim as verbatim
            LIMIT 5
            """
            with self.db.driver.session(database=self.db.database) as session:
                result = session.run(query, sc_id=sc['id'])
                print(f"\n  Merged claims:")
                for i, record in enumerate(result, 1):
                    print(f"    {i}. {record['text'][:100]}...")

    def run(self, similarity_threshold: float = 0.3, cluster_threshold: float = 0.5):
        """
        Run complete hierarchy building process.

        Args:
            similarity_threshold: Minimum similarity to create SIMILAR_TO relationship
            cluster_threshold: Minimum similarity to group into clusters
        """
        print("=" * 80)
        print("BUILDING CLAIM HIERARCHY".center(80))
        print("=" * 80)

        # Step 1: Find similar claims
        similar_pairs = self.find_similar_claims(similarity_threshold)

        if not similar_pairs:
            print("\nNo similar claims found. Try lowering the similarity threshold.")
            return

        # Step 2: Create similarity relationships
        self.create_similarity_relationships(similar_pairs)

        # Step 3: Find clusters
        clusters = self.find_claim_clusters(cluster_threshold)

        if not clusters:
            print("\nNo claim clusters found. Try lowering the cluster threshold.")
            return

        # Step 4: Create SuperClaims
        super_claim_ids = self.create_super_claims(clusters)

        # Step 5: Create support relationships
        self.create_support_relationships(min_similarity=0.4)

        # Step 6: Print summary
        self.print_hierarchy_summary()

        print("\n" + "=" * 80)
        print("HIERARCHY BUILDING COMPLETE".center(80))
        print("=" * 80)
        print("\nYou can now visualize the hierarchy in Neo4j Browser:")
        print("  1. Open http://localhost:7474")
        print("  2. Run this query to see the full hierarchy:")
        print("\n     MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)")
        print("     OPTIONAL MATCH (c)-[s:SIMILAR_TO]-(c2:Claim)")
        print("     OPTIONAL MATCH (c)-[m:MERGED_INTO]->(sc:SuperClaim)")
        print("     OPTIONAL MATCH (c)-[sup:SUPPORTS]->(sc2:SuperClaim)")
        print("     RETURN d, c, s, c2, m, sc, sup, sc2")
        print("\n  3. Or see just SuperClaims and their members:")
        print("\n     MATCH (sc:SuperClaim)<-[m:MERGED_INTO]-(c:Claim)")
        print("     RETURN sc, m, c")


def main():
    """Run the hierarchy builder."""
    builder = ClaimHierarchyBuilder()

    try:
        # Run with default thresholds
        # Lower thresholds = more grouping, higher thresholds = stricter grouping
        builder.run(
            similarity_threshold=0.3,  # Find claims with 30%+ word overlap
            cluster_threshold=0.5      # Group claims with 50%+ similarity
        )
    finally:
        builder.close()


if __name__ == "__main__":
    main()
