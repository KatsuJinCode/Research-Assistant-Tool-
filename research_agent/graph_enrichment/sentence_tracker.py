"""
Sentence-Level Tracking System

Tracks exact locations where claims appear in source documents.
Enables "click claim -> see exact source location" functionality.
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class SentenceTracker:
    """Track sentences and their locations in documents."""

    def __init__(self):
        """Initialize sentence tracker."""
        pass

    def extract_sentences_with_location(
        self,
        text: str,
        document_id: str,
        source_file: str
    ) -> List[Dict[str, Any]]:
        """
        Extract sentences with precise location tracking.

        Args:
            text: Full document text
            document_id: Document UUID
            source_file: Source file path

        Returns:
            List of sentence dicts with location info
        """
        sentences = []

        # Split into pages (assuming "\n\n" separates pages from PDFExtractor)
        pages = text.split('\n\n')

        for page_num, page_text in enumerate(pages, 1):
            # Split page into lines
            lines = page_text.split('\n')

            current_sentence = ""
            sentence_start_line = 0

            for line_num, line in enumerate(lines, 1):
                # Add line to current sentence
                if current_sentence:
                    current_sentence += " " + line.strip()
                else:
                    current_sentence = line.strip()
                    sentence_start_line = line_num

                # Check if sentence ends
                if self._is_sentence_end(current_sentence):
                    # Extract complete sentences
                    complete_sentences = self._split_into_sentences(current_sentence)

                    for sent_text in complete_sentences:
                        if len(sent_text.strip()) > 20:  # Skip very short sentences
                            sentence = {
                                'id': str(uuid4()),
                                'text': sent_text.strip(),
                                'document_id': document_id,
                                'source_file': source_file,
                                'page': page_num,
                                'start_line': sentence_start_line,
                                'end_line': line_num,
                                'char_count': len(sent_text.strip())
                            }
                            sentences.append(sentence)

                    current_sentence = ""

            # Handle any remaining sentence at end of page
            if current_sentence.strip() and len(current_sentence.strip()) > 20:
                sentence = {
                    'id': str(uuid4()),
                    'text': current_sentence.strip(),
                    'document_id': document_id,
                    'source_file': source_file,
                    'page': page_num,
                    'start_line': sentence_start_line,
                    'end_line': len(lines),
                    'char_count': len(current_sentence.strip())
                }
                sentences.append(sentence)

        logger.info(f"Extracted {len(sentences)} sentences from {len(pages)} pages")
        return sentences

    def _is_sentence_end(self, text: str) -> bool:
        """Check if text ends with sentence terminator."""
        return bool(re.search(r'[.!?][\s"\']*$', text))

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into individual sentences."""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def find_claim_in_sentences(
        self,
        claim_text: str,
        sentences: List[Dict[str, Any]],
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Find which sentences contain or match a claim.

        Args:
            claim_text: The claim to search for
            sentences: List of sentence dicts
            similarity_threshold: Minimum similarity to consider a match

        Returns:
            List of matching sentences with match info
        """
        matches = []
        claim_clean = self._normalize_text(claim_text)

        for sentence in sentences:
            sentence_clean = self._normalize_text(sentence['text'])

            # Check for exact substring match
            if claim_clean in sentence_clean:
                matches.append({
                    **sentence,
                    'match_type': 'exact_substring',
                    'similarity': 1.0
                })
                continue

            # Check for partial match (claim contains sentence or vice versa)
            if sentence_clean in claim_clean:
                matches.append({
                    **sentence,
                    'match_type': 'sentence_in_claim',
                    'similarity': len(sentence_clean) / len(claim_clean)
                })
                continue

            # Check word overlap
            similarity = self._calculate_word_similarity(claim_clean, sentence_clean)
            if similarity >= similarity_threshold:
                matches.append({
                    **sentence,
                    'match_type': 'high_similarity',
                    'similarity': similarity
                })

        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        logger.info(f"Found {len(matches)} sentence matches for claim")
        return matches

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove punctuation for comparison
        text = re.sub(r'[^\w\s]', '', text)
        # Lowercase
        return text.lower().strip()

    def _calculate_word_similarity(self, text1: str, text2: str) -> float:
        """Calculate word-level similarity (Jaccard)."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def create_sentence_nodes_in_neo4j(
        self,
        sentences: List[Dict[str, Any]],
        db
    ) -> List[str]:
        """
        Create Sentence nodes in Neo4j.

        Args:
            sentences: List of sentence dicts
            db: Neo4jDatabase instance

        Returns:
            List of created sentence IDs
        """
        created_ids = []

        for sentence in sentences:
            # Create Sentence node
            node_id = db.create_node('Sentence', {
                'id': sentence['id'],
                'text': sentence['text'],
                'page': sentence['page'],
                'start_line': sentence['start_line'],
                'end_line': sentence['end_line'],
                'char_count': sentence['char_count'],
                'source_file': sentence['source_file']
            })

            # Link to Document
            db.create_relationship(
                sentence['id'],
                sentence['document_id'],
                'IN_DOCUMENT',
                {'page': sentence['page']}
            )

            created_ids.append(node_id)

        logger.info(f"Created {len(created_ids)} Sentence nodes in Neo4j")
        return created_ids

    def link_claims_to_sentences(
        self,
        claims: List[Dict[str, Any]],
        sentences: List[Dict[str, Any]],
        db
    ) -> int:
        """
        Link Claim nodes to Sentence nodes based on text matching.

        Args:
            claims: List of claim dicts
            sentences: List of sentence dicts
            db: Neo4jDatabase instance

        Returns:
            Number of relationships created
        """
        relationships_created = 0

        for claim in claims:
            # Find matching sentences
            matches = self.find_claim_in_sentences(
                claim['text'],
                sentences,
                similarity_threshold=0.7
            )

            # Create relationships
            for match in matches:
                db.create_relationship(
                    claim['id'],
                    match['id'],
                    'EXTRACTED_FROM',
                    {
                        'match_type': match['match_type'],
                        'similarity': match['similarity'],
                        'page': match['page'],
                        'line_start': match['start_line'],
                        'line_end': match['end_line']
                    }
                )
                relationships_created += 1

        logger.info(f"Created {relationships_created} EXTRACTED_FROM relationships")
        return relationships_created
