"""
Automated Fact-Checking Module.

Verifies factual claims automatically using external sources and AI analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from .base_nlp import BaseNLPProcessor

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Types of claims for fact-checking."""
    FACTUAL = "factual"  # Verifiable factual claim
    OPINION = "opinion"  # Opinion or subjective claim
    PREDICTION = "prediction"  # Future prediction
    DEFINITION = "definition"  # Definition claim
    MIXED = "mixed"  # Mix of factual and opinion


class TruthRating(Enum):
    """Truth rating scale."""
    TRUE = "true"  # Claim is true
    MOSTLY_TRUE = "mostly_true"  # Claim is mostly true
    HALF_TRUE = "half_true"  # Claim is half true
    MOSTLY_FALSE = "mostly_false"  # Claim is mostly false
    FALSE = "false"  # Claim is false
    UNVERIFIABLE = "unverifiable"  # Cannot be verified
    NEEDS_CONTEXT = "needs_context"  # True but needs context


@dataclass
class FactCheckSource:
    """External source used for fact-checking."""
    source_name: str
    source_url: Optional[str]
    relevant_text: str
    credibility_score: float  # 0-100


@dataclass
class FactCheckResult:
    """Result of fact-checking analysis."""
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    is_checkable: bool
    truth_rating: TruthRating
    confidence: float  # 0-100
    sources: List[FactCheckSource]
    verification_summary: str
    context_needed: Optional[str] = None
    checked_at: Optional[str] = None


class FactChecker(BaseNLPProcessor):
    """
    Automated fact-checker for claims.

    Classifies claims as factual/opinion and verifies factual claims
    against external sources.
    """

    def __init__(self, **kwargs):
        """Initialize fact checker."""
        super().__init__(**kwargs)

    async def classify_claim_type(
        self,
        claim_text: str
    ) -> Tuple[ClaimType, bool, float]:
        """
        Classify claim as factual, opinion, prediction, etc.

        Args:
            claim_text: Claim text to classify

        Returns:
            Tuple of (claim_type, is_checkable, confidence)
        """
        prompt = f"""Classify this claim:

"{claim_text}"

Determine:
1. Type: factual (verifiable fact), opinion (subjective), prediction (future claim), definition, or mixed
2. Is it checkable? (Can it be verified against evidence?)
3. Confidence in classification (0-100)

Consider whether the claim makes verifiable assertions about the world."""

        schema = {
            "claim_type": "string - factual, opinion, prediction, definition, or mixed",
            "is_checkable": "boolean - true if can be fact-checked",
            "confidence": "number - 0-100",
            "explanation": "string - brief explanation"
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.2)

            # Parse claim type
            type_str = result.get('claim_type', 'mixed').lower()
            claim_type = ClaimType.MIXED
            for ct in ClaimType:
                if ct.value == type_str:
                    claim_type = ct
                    break

            return (
                claim_type,
                result.get('is_checkable', False),
                float(result.get('confidence', 0.0))
            )

        except Exception as e:
            logger.error(f"Claim classification failed: {e}")
            return (ClaimType.MIXED, False, 0.0)

    async def search_verification_sources(
        self,
        claim_text: str
    ) -> List[FactCheckSource]:
        """
        Search for sources to verify the claim.

        This is a simplified version. In production, this would:
        - Query Wikipedia API
        - Query fact-checking databases
        - Query academic sources
        - Use web search APIs

        Args:
            claim_text: Claim to verify

        Returns:
            List of fact-check sources
        """
        # Extract key terms from claim
        keywords = self.extract_keywords(claim_text, top_n=5)

        # Use AI to generate hypothetical verification sources
        # In production, this would make actual API calls
        prompt = f"""For the claim: "{claim_text}"

What are the most reliable sources to verify this claim?

List 3-5 potential sources with:
1. Source name (e.g., "Wikipedia", "PubMed", "Official statistics")
2. What information from that source would be relevant
3. Credibility score (0-100)

Focus on authoritative, verifiable sources."""

        schema = {
            "sources": [
                {
                    "source_name": "string - name of source",
                    "source_url": "string - URL or description",
                    "relevant_text": "string - what information is relevant",
                    "credibility_score": "number - 0-100"
                }
            ]
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.3)

            sources = []
            for src_data in result.get('sources', []):
                sources.append(FactCheckSource(
                    source_name=src_data.get('source_name', 'Unknown'),
                    source_url=src_data.get('source_url', None),
                    relevant_text=src_data.get('relevant_text', ''),
                    credibility_score=float(src_data.get('credibility_score', 0.0))
                ))

            return sources

        except Exception as e:
            logger.error(f"Source search failed: {e}")
            return []

    async def verify_claim(
        self,
        claim_text: str,
        sources: List[FactCheckSource]
    ) -> Tuple[TruthRating, str, str, float]:
        """
        Verify claim against sources.

        Args:
            claim_text: Claim to verify
            sources: List of verification sources

        Returns:
            Tuple of (truth_rating, summary, context, confidence)
        """
        # Compile source information
        source_info = "\n\n".join([
            f"Source: {src.source_name}\n{src.relevant_text}"
            for src in sources
        ])

        prompt = f"""Verify this claim against the provided sources:

Claim: "{claim_text}"

Sources:
{source_info}

Determine:
1. Truth rating: true, mostly_true, half_true, mostly_false, false, unverifiable, or needs_context
2. Verification summary explaining the rating
3. Any important context needed
4. Confidence in rating (0-100)

Be precise and cite specific information from sources."""

        schema = {
            "truth_rating": "string - true, mostly_true, half_true, mostly_false, false, unverifiable, or needs_context",
            "verification_summary": "string - explanation of the rating",
            "context_needed": "string - important context or null",
            "confidence": "number - 0-100"
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.2)

            # Parse truth rating
            rating_str = result.get('truth_rating', 'unverifiable').lower()
            truth_rating = TruthRating.UNVERIFIABLE
            for tr in TruthRating:
                if tr.value == rating_str:
                    truth_rating = tr
                    break

            return (
                truth_rating,
                result.get('verification_summary', ''),
                result.get('context_needed', None),
                float(result.get('confidence', 0.0))
            )

        except Exception as e:
            logger.error(f"Claim verification failed: {e}")
            return (
                TruthRating.UNVERIFIABLE,
                f"Verification failed: {str(e)}",
                None,
                0.0
            )

    async def fact_check_claim(
        self,
        claim: Dict[str, Any]
    ) -> FactCheckResult:
        """
        Perform complete fact-check on a claim.

        Args:
            claim: Claim dict with 'id' and 'text'

        Returns:
            FactCheckResult
        """
        claim_id = claim.get('id', 'unknown')
        claim_text = claim.get('text', claim.get('original_text', ''))

        logger.info(f"Fact-checking claim: {claim_text[:100]}...")

        # Step 1: Classify claim type
        claim_type, is_checkable, type_confidence = await self.classify_claim_type(claim_text)

        if not is_checkable:
            logger.info(f"Claim is not checkable (type: {claim_type.value})")
            return FactCheckResult(
                claim_id=claim_id,
                claim_text=claim_text,
                claim_type=claim_type,
                is_checkable=False,
                truth_rating=TruthRating.UNVERIFIABLE,
                confidence=type_confidence,
                sources=[],
                verification_summary=f"Claim is {claim_type.value} and not fact-checkable.",
                checked_at=datetime.utcnow().isoformat()
            )

        # Step 2: Search for verification sources
        sources = await self.search_verification_sources(claim_text)

        if not sources:
            logger.warning("No verification sources found")
            return FactCheckResult(
                claim_id=claim_id,
                claim_text=claim_text,
                claim_type=claim_type,
                is_checkable=True,
                truth_rating=TruthRating.UNVERIFIABLE,
                confidence=0.0,
                sources=[],
                verification_summary="No verification sources available.",
                checked_at=datetime.utcnow().isoformat()
            )

        # Step 3: Verify claim against sources
        truth_rating, summary, context, confidence = await self.verify_claim(
            claim_text, sources
        )

        result = FactCheckResult(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            is_checkable=True,
            truth_rating=truth_rating,
            confidence=confidence,
            sources=sources,
            verification_summary=summary,
            context_needed=context,
            checked_at=datetime.utcnow().isoformat()
        )

        logger.info(
            f"Fact-check complete: {truth_rating.value} "
            f"(confidence: {confidence:.1f}%)"
        )

        return result

    async def fact_check_claims_batch(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[FactCheckResult]:
        """
        Fact-check multiple claims.

        Args:
            claims: List of claim dicts

        Returns:
            List of fact-check results
        """
        results = []

        for claim in claims:
            result = await self.fact_check_claim(claim)
            results.append(result)

        return results

    def add_fact_check_to_graph(
        self,
        graph_db,
        fact_check_results: List[FactCheckResult]
    ) -> int:
        """
        Add fact-check results to graph.

        Args:
            graph_db: GraphDatabase instance
            fact_check_results: List of fact-check results

        Returns:
            Number of nodes updated
        """
        count = 0

        for result in fact_check_results:
            # Update claim node with fact-check info
            claim_node = graph_db.get_node(result.claim_id)

            if claim_node:
                claim_node['fact_checked'] = True
                claim_node['claim_type'] = result.claim_type.value
                claim_node['truth_rating'] = result.truth_rating.value
                claim_node['fact_check_confidence'] = result.confidence
                claim_node['verification_summary'] = result.verification_summary
                claim_node['checked_at'] = result.checked_at
                count += 1

            # Create FactCheck node
            fact_check_id = graph_db.create_node('FactCheck', {
                'claim_id': result.claim_id,
                'truth_rating': result.truth_rating.value,
                'confidence': result.confidence,
                'summary': result.verification_summary,
                'context_needed': result.context_needed,
                'checked_at': result.checked_at
            })

            # Link to claim
            graph_db.create_relationship(
                from_node=result.claim_id,
                to_node=fact_check_id,
                rel_type='HAS_FACT_CHECK',
                properties={}
            )

            # Create source nodes and links
            for source in result.sources:
                source_id = graph_db.create_node('FactCheckSource', {
                    'name': source.source_name,
                    'url': source.source_url,
                    'relevant_text': source.relevant_text,
                    'credibility_score': source.credibility_score
                })

                graph_db.create_relationship(
                    from_node=fact_check_id,
                    to_node=source_id,
                    rel_type='USES_SOURCE',
                    properties={}
                )

        logger.info(f"Added fact-check info to {count} claim nodes")
        return count

    def get_fact_check_badge(
        self,
        truth_rating: TruthRating
    ) -> Dict[str, str]:
        """
        Get UI badge info for truth rating.

        Args:
            truth_rating: Truth rating

        Returns:
            Dict with 'label', 'color', 'icon'
        """
        badges = {
            TruthRating.TRUE: {
                'label': 'TRUE',
                'color': 'green',
                'icon': 'check-circle'
            },
            TruthRating.MOSTLY_TRUE: {
                'label': 'MOSTLY TRUE',
                'color': 'light-green',
                'icon': 'check'
            },
            TruthRating.HALF_TRUE: {
                'label': 'HALF TRUE',
                'color': 'yellow',
                'icon': 'info'
            },
            TruthRating.MOSTLY_FALSE: {
                'label': 'MOSTLY FALSE',
                'color': 'orange',
                'icon': 'alert'
            },
            TruthRating.FALSE: {
                'label': 'FALSE',
                'color': 'red',
                'icon': 'x-circle'
            },
            TruthRating.UNVERIFIABLE: {
                'label': 'UNVERIFIABLE',
                'color': 'gray',
                'icon': 'question'
            },
            TruthRating.NEEDS_CONTEXT: {
                'label': 'NEEDS CONTEXT',
                'color': 'blue',
                'icon': 'message-circle'
            }
        }

        return badges.get(truth_rating, badges[TruthRating.UNVERIFIABLE])
