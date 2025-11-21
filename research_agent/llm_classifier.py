"""
LLM Evidence Classifier - Stage 2 Evidence Auto-Linking
=======================================================

Uses LLM to classify the relationship between claims and evidence:
- SUPPORTS: Evidence supports the claim
- CONTRADICTS: Evidence contradicts the claim
- IRRELEVANT: Evidence is topically similar but doesn't support or contradict

Based on: EVIDENCE_AUTO_LINKING_STRATEGY.md Stage 2

This stage operates on candidate pairs from Stage 1 (semantic similarity > 0.7)
and provides higher-quality classification with reasoning.
"""

import logging
import json
from typing import Dict, List, Literal, Optional
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)

RelationshipType = Literal["SUPPORTS", "CONTRADICTS", "IRRELEVANT"]


class EvidenceClassifier:
    """
    Classifies claim-evidence relationships using LLM.
    """

    def __init__(self, provider: str = "anthropic", model: str = None):
        """
        Initialize classifier.

        Args:
            provider: "anthropic" or "openai"
            model: Model name (default: claude-3-5-sonnet-20241022 or gpt-4o-mini)
        """
        self.provider = provider.lower()

        if self.provider == "anthropic":
            self.client = Anthropic()
            self.model = model or "claude-3-5-sonnet-20241022"
        elif self.provider == "openai":
            self.client = OpenAI()
            self.model = model or "gpt-4o-mini"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        logger.info(f"[LLMClassifier] Initialized with {self.provider} - {self.model}")

    def classify_relationship(
        self,
        claim_text: str,
        evidence_text: str
    ) -> Dict:
        """
        Classify the relationship between a claim and evidence.

        Args:
            claim_text: The claim text
            evidence_text: The evidence text

        Returns:
            {
                'relationship': 'SUPPORTS' | 'CONTRADICTS' | 'IRRELEVANT',
                'confidence': 0.0-1.0,
                'reasoning': 'Brief explanation'
            }
        """
        try:
            prompt = self._build_classification_prompt(claim_text, evidence_text)

            if self.provider == "anthropic":
                result = self._classify_with_anthropic(prompt)
            else:
                result = self._classify_with_openai(prompt)

            logger.info(f"[LLMClassifier] Classified as {result['relationship']} (confidence: {result['confidence']})")
            return result

        except Exception as e:
            logger.error(f"[LLMClassifier] Error classifying relationship: {e}")
            return {
                'relationship': 'IRRELEVANT',
                'confidence': 0.0,
                'reasoning': f'Classification failed: {str(e)}',
                'error': True
            }

    def _build_classification_prompt(self, claim_text: str, evidence_text: str) -> str:
        """Build the classification prompt."""
        return f"""You are an evidence classifier for a research analysis system.

Analyze the relationship between this claim and evidence:

CLAIM:
{claim_text}

EVIDENCE:
{evidence_text}

Determine if the evidence:
1. SUPPORTS the claim (provides evidence in favor)
2. CONTRADICTS the claim (provides evidence against)
3. Is IRRELEVANT to the claim (topically related but doesn't support or contradict)

Consider:
- Does the evidence directly address the claim's core assertion?
- Is the evidence strong enough to meaningfully support or contradict?
- Are there important qualifiers or conditions that affect the relationship?

Respond with ONLY a valid JSON object (no markdown, no explanation before or after):
{{
  "relationship": "SUPPORTS" | "CONTRADICTS" | "IRRELEVANT",
  "confidence": 0.85,
  "reasoning": "Brief explanation (1-2 sentences)"
}}"""

    def _classify_with_anthropic(self, prompt: str) -> Dict:
        """Classify using Claude."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0.3,  # Lower temperature for consistent classification
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Extract JSON from code block
                lines = response_text.split('\n')
                json_lines = []
                in_code = False
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code or (not line.startswith('```')):
                        json_lines.append(line)
                response_text = '\n'.join(json_lines).strip()

            result = json.loads(response_text)

            # Validate response
            if 'relationship' not in result or result['relationship'] not in ['SUPPORTS', 'CONTRADICTS', 'IRRELEVANT']:
                raise ValueError(f"Invalid relationship: {result.get('relationship')}")

            if 'confidence' not in result:
                result['confidence'] = 0.5

            if 'reasoning' not in result:
                result['reasoning'] = 'No reasoning provided'

            return result

        except json.JSONDecodeError as e:
            logger.error(f"[LLMClassifier] Failed to parse JSON: {response_text}")
            raise ValueError(f"Invalid JSON response: {e}")

    def _classify_with_openai(self, prompt: str) -> Dict:
        """Classify using OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an evidence classifier. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}  # Force JSON response
            )

            response_text = response.choices[0].message.content.strip()
            result = json.loads(response_text)

            # Validate response
            if 'relationship' not in result or result['relationship'] not in ['SUPPORTS', 'CONTRADICTS', 'IRRELEVANT']:
                raise ValueError(f"Invalid relationship: {result.get('relationship')}")

            if 'confidence' not in result:
                result['confidence'] = 0.5

            if 'reasoning' not in result:
                result['reasoning'] = 'No reasoning provided'

            return result

        except json.JSONDecodeError as e:
            logger.error(f"[LLMClassifier] Failed to parse JSON: {response_text}")
            raise ValueError(f"Invalid JSON response: {e}")

    def batch_classify(
        self,
        claim_evidence_pairs: List[tuple[str, str, str]]
    ) -> List[Dict]:
        """
        Classify multiple claim-evidence pairs.

        Args:
            claim_evidence_pairs: List of (claim_id, claim_text, evidence_id, evidence_text) tuples

        Returns:
            List of classification results with IDs
        """
        results = []

        for claim_id, claim_text, evidence_id, evidence_text in claim_evidence_pairs:
            classification = self.classify_relationship(claim_text, evidence_text)
            classification['claim_id'] = claim_id
            classification['evidence_id'] = evidence_id
            results.append(classification)

        return results


class AutoLinkingPipeline:
    """
    Combines Stage 1 (semantic similarity) and Stage 2 (LLM classification)
    to automatically link evidence to claims.
    """

    def __init__(self, db, similarity_engine, classifier: EvidenceClassifier):
        """
        Initialize auto-linking pipeline.

        Args:
            db: GraphDatabase instance
            similarity_engine: SemanticSimilarityEngine instance
            classifier: EvidenceClassifier instance
        """
        self.db = db
        self.engine = similarity_engine
        self.classifier = classifier
        logger.info("[AutoLinking] Pipeline initialized")

    def auto_link_for_claim(
        self,
        claim_id: str,
        semantic_threshold: float = 0.7,
        llm_confidence_threshold: float = 0.7,
        auto_approve: bool = False
    ) -> Dict:
        """
        Auto-link evidence to a specific claim using 2-stage pipeline.

        Args:
            claim_id: Claim to find evidence for
            semantic_threshold: Stage 1 similarity threshold
            llm_confidence_threshold: Stage 2 confidence threshold
            auto_approve: If True, create links immediately. If False, create pending links.

        Returns:
            {
                'claim_id': str,
                'candidates_found': int,
                'supports': int,
                'contradicts': int,
                'irrelevant': int,
                'links_created': int,
                'links_pending': int
            }
        """
        logger.info(f"[AutoLinking] Processing claim {claim_id}")

        # Get claim details
        claim_query = """
        MATCH (c:Claim {id: $claim_id})
        RETURN c.text as text, c.embedding as embedding
        """
        claim_result = self.db.execute_query(claim_query, {'claim_id': claim_id})

        if not claim_result or not claim_result[0]['embedding']:
            logger.warning(f"[AutoLinking] Claim {claim_id} not found or has no embedding")
            return {'error': 'Claim not found or no embedding'}

        claim_text = claim_result[0]['text']
        claim_embedding = self.engine.list_to_embedding(claim_result[0]['embedding'])

        # Stage 1: Find semantically similar evidence
        evidence_query = """
        MATCH (e:Evidence)
        WHERE e.embedding IS NOT NULL
        RETURN e.id as id, e.text as text, e.embedding as embedding
        """
        all_evidence = self.db.execute_query(evidence_query)

        if not all_evidence:
            logger.info("[AutoLinking] No evidence nodes with embeddings found")
            return {'candidates_found': 0, 'links_created': 0}

        # Calculate similarities
        candidates = []
        for evidence in all_evidence:
            ev_embedding = self.engine.list_to_embedding(evidence['embedding'])
            similarity = self.engine.calculate_similarity(claim_embedding, ev_embedding)

            if similarity >= semantic_threshold:
                candidates.append({
                    'evidence_id': evidence['id'],
                    'evidence_text': evidence['text'],
                    'similarity': similarity
                })

        logger.info(f"[AutoLinking] Stage 1: Found {len(candidates)} candidates above {semantic_threshold}")

        if not candidates:
            return {'candidates_found': 0, 'links_created': 0}

        # Stage 2: LLM classification
        supports = 0
        contradicts = 0
        irrelevant = 0
        links_created = 0
        links_pending = 0

        for candidate in candidates:
            classification = self.classifier.classify_relationship(
                claim_text,
                candidate['evidence_text']
            )

            relationship = classification['relationship']
            confidence = classification['confidence']
            reasoning = classification['reasoning']

            # Count by type
            if relationship == 'SUPPORTS':
                supports += 1
            elif relationship == 'CONTRADICTS':
                contradicts += 1
            else:
                irrelevant += 1

            # Only create links for SUPPORTS or CONTRADICTS with sufficient confidence
            if relationship in ['SUPPORTS', 'CONTRADICTS'] and confidence >= llm_confidence_threshold:
                link_strength = (candidate['similarity'] * 0.3) + (confidence * 0.7)  # Combined score

                if auto_approve:
                    # Create relationship immediately
                    rel_type = 'SUPPORTED_BY' if relationship == 'SUPPORTS' else 'CONTRADICTED_BY'

                    link_query = f"""
                    MATCH (c:Claim {{id: $claim_id}})
                    MATCH (e:Evidence {{id: $evidence_id}})
                    MERGE (c)-[r:{rel_type} {{
                        auto_linked: true,
                        semantic_similarity: $similarity,
                        llm_confidence: $llm_confidence,
                        llm_relationship: $relationship,
                        link_strength: $link_strength,
                        reasoning: $reasoning,
                        created_at: datetime()
                    }}]->(e)
                    RETURN r
                    """

                    result = self.db.execute_query(link_query, {
                        'claim_id': claim_id,
                        'evidence_id': candidate['evidence_id'],
                        'similarity': candidate['similarity'],
                        'llm_confidence': confidence,
                        'relationship': relationship,
                        'link_strength': link_strength,
                        'reasoning': reasoning
                    })

                    if result:
                        links_created += 1
                        logger.info(f"[AutoLinking] Created {rel_type} link (strength: {link_strength:.2f})")

                else:
                    # Create pending link for review
                    import hashlib
                    link_id = f"link_{hashlib.sha256(f'{claim_id}_{candidate['evidence_id']}'.encode()).hexdigest()[:16]}"

                    pending_query = """
                    CREATE (p:PendingLink {
                        id: $link_id,
                        claim_id: $claim_id,
                        evidence_id: $evidence_id,
                        relationship: $relationship,
                        semantic_similarity: $similarity,
                        llm_confidence: $llm_confidence,
                        link_strength: $link_strength,
                        reasoning: $reasoning,
                        status: 'pending_review',
                        created_at: datetime()
                    })
                    RETURN p.id as id
                    """

                    result = self.db.execute_query(pending_query, {
                        'link_id': link_id,
                        'claim_id': claim_id,
                        'evidence_id': candidate['evidence_id'],
                        'relationship': relationship,
                        'similarity': candidate['similarity'],
                        'llm_confidence': confidence,
                        'link_strength': link_strength,
                        'reasoning': reasoning
                    })

                    if result:
                        links_pending += 1

        return {
            'claim_id': claim_id,
            'candidates_found': len(candidates),
            'supports': supports,
            'contradicts': contradicts,
            'irrelevant': irrelevant,
            'links_created': links_created,
            'links_pending': links_pending
        }


# Global instance
_classifier = None


def get_classifier(provider: str = "anthropic") -> EvidenceClassifier:
    """Get or create global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = EvidenceClassifier(provider=provider)
    return _classifier
