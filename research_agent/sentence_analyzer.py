"""
Sentence-by-Sentence Document Analyzer

Processes documents incrementally, analyzing each sentence to:
1. Identify if it's a claim, evidence, or supporting text
2. Extract the core assertion
3. Find similar existing claims in the knowledge graph
4. Merge or add, preserving provenance
5. Build hierarchical claim-evidence structure

This ensures:
- Every sentence is analyzed and represented
- No unnecessary duplication
- Novel information is added
- Similar claims are merged intelligently
- Source provenance is maintained
"""

from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
from research_agent.normalization.qualifier_extractor import QualifierExtractor


class SentenceAnalyzer:
    """
    Analyzes sentences to build incremental knowledge graph.

    Each sentence is classified as:
    - CLAIM: Makes a factual assertion
    - EVIDENCE: Provides support for a claim
    - CONTEXT: Background information
    - QUALIFIER: Modifies an existing claim
    - TRANSITION: Organizational text
    """

    def __init__(self, graph_db):
        """
        Initialize sentence analyzer.

        Args:
            graph_db: Graph database instance (NetworkX or Neo4j)
        """
        self.graph = graph_db
        self.qualifier_extractor = QualifierExtractor()

    def analyze_sentence(self, sentence: str, document_id: str,
                        sentence_index: int) -> Dict[str, Any]:
        """
        Analyze a single sentence.

        Args:
            sentence: The sentence text
            document_id: ID of containing document
            sentence_index: Position in document (0-indexed)

        Returns:
            Analysis dict with:
                - type: CLAIM, EVIDENCE, CONTEXT, etc.
                - claim_text: Extracted claim (if applicable)
                - qualifiers: List of qualifiers
                - supports_claim_id: ID of claim this supports (if evidence)
                - confidence: 0.0-1.0
        """
        # I (Claude) would analyze this sentence
        # For now, heuristic-based classification

        analysis = {
            'sentence': sentence,
            'sentence_index': sentence_index,
            'document_id': document_id,
            'type': 'UNKNOWN',
            'claim_text': None,
            'qualifiers': [],
            'confidence': 0.0
        }

        # Check for evidence indicators
        evidence_indicators = [
            'studies show', 'research indicates', 'according to',
            'data suggests', 'evidence demonstrates', 'for example',
            'specifically', 'in fact', 'indeed'
        ]

        lower_sentence = sentence.lower()

        # Classify sentence
        if any(indicator in lower_sentence for indicator in evidence_indicators):
            analysis['type'] = 'EVIDENCE'
            analysis['confidence'] = 0.8
        elif self._is_claim_sentence(sentence):
            analysis['type'] = 'CLAIM'
            analysis['claim_text'] = sentence
            analysis['qualifiers'] = self.qualifier_extractor.extract(sentence)
            analysis['confidence'] = 0.85
        elif self._is_transition(sentence):
            analysis['type'] = 'TRANSITION'
            analysis['confidence'] = 0.9
        else:
            analysis['type'] = 'CONTEXT'
            analysis['confidence'] = 0.7

        return analysis

    def _is_claim_sentence(self, sentence: str) -> bool:
        """
        Determine if sentence makes a claim.

        Heuristics:
        - Contains subject-verb-object structure
        - Makes an assertion (not a question)
        - Not purely descriptive
        """
        # Simple heuristic
        sentence = sentence.strip()

        # Not a question
        if sentence.endswith('?'):
            return False

        # Has assertion verbs
        assertion_verbs = ['is', 'are', 'was', 'were', 'can', 'may', 'must',
                          'should', 'will', 'exists', 'appears', 'seems']

        lower_sentence = sentence.lower()
        has_assertion = any(verb in lower_sentence.split() for verb in assertion_verbs)

        # Reasonable length (not just a fragment)
        word_count = len(sentence.split())
        if word_count < 5:
            return False

        return has_assertion

    def _is_transition(self, sentence: str) -> bool:
        """Check if sentence is transitional/organizational."""
        transition_starts = [
            'however', 'moreover', 'furthermore', 'in addition',
            'first', 'second', 'third', 'finally', 'in conclusion',
            'therefore', 'thus', 'hence'
        ]

        lower_sentence = sentence.lower().strip()
        return any(lower_sentence.startswith(t) for t in transition_starts)

    def process_document_incrementally(self, document_id: str, text: str,
                                      chunk_size: int = 10) -> Dict[str, Any]:
        """
        Process document sentence-by-sentence, building knowledge graph incrementally.

        Args:
            document_id: Document ID
            text: Full document text
            chunk_size: Process this many sentences before checking for duplicates

        Returns:
            Summary of processing:
                - sentences_analyzed: int
                - claims_found: int
                - claims_merged: int
                - novel_claims_added: int
                - evidence_linked: int
        """
        # Split into sentences (simple split for now)
        sentences = self._split_sentences(text)

        stats = {
            'sentences_analyzed': 0,
            'claims_found': 0,
            'claims_merged': 0,
            'novel_claims_added': 0,
            'evidence_linked': 0,
            'transitions': 0,
            'context': 0
        }

        current_claim_id = None  # Track current claim being discussed

        for i, sentence in enumerate(sentences):
            # Analyze sentence
            analysis = self.analyze_sentence(sentence, document_id, i)
            stats['sentences_analyzed'] += 1

            # Create sentence node
            sentence_id = self.graph.create_node('Sentence', {
                'text': sentence,
                'index': i,
                'type': analysis['type'],
                'confidence': analysis['confidence']
            })

            # Link sentence to document
            self.graph.create_relationship(document_id, sentence_id, 'CONTAINS')

            # Handle based on type
            if analysis['type'] == 'CLAIM':
                stats['claims_found'] += 1

                # Check if similar claim exists
                existing_similar = self._find_similar_existing_claim(
                    analysis['claim_text']
                )

                if existing_similar:
                    # Merge with existing
                    stats['claims_merged'] += 1
                    current_claim_id = self._merge_claim_variant(
                        existing_similar['id'],
                        analysis['claim_text'],
                        sentence_id,
                        document_id
                    )
                else:
                    # Novel claim - add to graph
                    stats['novel_claims_added'] += 1
                    current_claim_id = self._add_novel_claim(
                        analysis['claim_text'],
                        analysis['qualifiers'],
                        sentence_id,
                        document_id
                    )

            elif analysis['type'] == 'EVIDENCE' and current_claim_id:
                # Link evidence to current claim
                stats['evidence_linked'] += 1
                self._link_evidence_to_claim(
                    sentence_id,
                    current_claim_id,
                    sentence
                )

            elif analysis['type'] == 'TRANSITION':
                stats['transitions'] += 1
                # Transitions might signal new claim context
                # Could reset current_claim_id here

            else:  # CONTEXT
                stats['context'] += 1
                if current_claim_id:
                    # Link context to current claim
                    self.graph.create_relationship(
                        sentence_id,
                        current_claim_id,
                        'PROVIDES_CONTEXT'
                    )

        return stats

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Simple implementation - could use NLTK or spaCy for better results.
        """
        import re

        # Simple sentence splitter
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _find_similar_existing_claim(self, claim_text: str,
                                    threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """
        Find existing similar claims in the graph.

        Args:
            claim_text: New claim text
            threshold: Similarity threshold

        Returns:
            Existing claim dict or None
        """
        # Get all existing claims
        existing_claims = self.graph.find_nodes('Claim')

        # I (Claude) would compute semantic similarity
        # For now, use simple word overlap
        for existing in existing_claims:
            similarity = self._compute_similarity(
                claim_text,
                existing.get('text', '')
            )

            if similarity >= threshold:
                return existing

        return None

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts.

        Simple Jaccard similarity for now.
        In production, would use embeddings.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _merge_claim_variant(self, existing_claim_id: str, variant_text: str,
                            sentence_id: str, document_id: str) -> str:
        """
        Merge a new variant of an existing claim.

        Creates a ClaimVariant node and links it.
        """
        variant_id = self.graph.create_node('ClaimVariant', {
            'text': variant_text,
            'source_document_id': document_id,
            'source_sentence_id': sentence_id
        })

        # Link variant to main claim
        self.graph.create_relationship(
            variant_id,
            existing_claim_id,
            'VARIANT_OF'
        )

        # Link sentence to variant
        self.graph.create_relationship(
            sentence_id,
            variant_id,
            'EXPRESSES'
        )

        return existing_claim_id

    def _add_novel_claim(self, claim_text: str, qualifiers: List[Dict],
                        sentence_id: str, document_id: str) -> str:
        """
        Add a novel claim to the graph.
        """
        claim_id = self.graph.create_node('Claim', {
            'text': claim_text,
            'source_document_id': document_id,
            'has_qualifiers': len(qualifiers) > 0,
            'qualifier_count': len(qualifiers)
        })

        # Link sentence to claim
        self.graph.create_relationship(
            sentence_id,
            claim_id,
            'EXPRESSES'
        )

        # Add qualifiers
        for qual in qualifiers:
            qual_id = self.graph.create_node('Qualifier', {
                'text': qual['text'],
                'type': qual['type'],
                'impact': qual['impact']
            })
            self.graph.create_relationship(
                claim_id,
                qual_id,
                'HAS_QUALIFIER'
            )

        return claim_id

    def _link_evidence_to_claim(self, sentence_id: str, claim_id: str,
                                evidence_text: str):
        """
        Link an evidence sentence to a claim.
        """
        evidence_id = self.graph.create_node('Evidence', {
            'text': evidence_text,
            'sentence_id': sentence_id
        })

        # Link evidence to claim
        self.graph.create_relationship(
            evidence_id,
            claim_id,
            'SUPPORTS',
            {'strength': 0.8}  # Would be computed by Claude
        )

        # Link sentence to evidence
        self.graph.create_relationship(
            sentence_id,
            evidence_id,
            'CONTAINS_EVIDENCE'
        )

    def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get summary of how document was processed.

        Returns:
            - Total sentences
            - Novel claims added
            - Claims merged with existing
            - Evidence pieces linked
            - Claim hierarchy
        """
        # Query graph for document analysis
        sentences = self.graph.get_relationships(document_id, 'CONTAINS')

        claims = []
        evidence = []

        for sentence_id, _ in sentences:
            sentence_rels = self.graph.get_relationships(sentence_id, direction='out')

            for target_id, rel_data in sentence_rels:
                target = self.graph.get_node(target_id)
                if not target:
                    continue

                label = target.get('label', '')

                if 'Claim' in label:
                    claims.append(target)
                elif 'Evidence' in label:
                    evidence.append(target)

        return {
            'document_id': document_id,
            'total_sentences': len(sentences),
            'novel_claims': len([c for c in claims if c.get('source_document_id') == document_id]),
            'evidence_linked': len(evidence),
            'claim_ids': [c['id'] for c in claims]
        }
