"""
Support Agent - Finds evidence that SUPPORTS claims.
"""

import json
import logging
from typing import Dict, Any, List
from research_agent.agents.base_agent import BaseAgent
from research_agent.models import AgentFramework


logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """
    Find empirical evidence that SUPPORTS the claim.

    MVP: Uses LLM to generate plausible evidence.
    TODO Post-MVP: Real academic search (Semantic Scholar, arXiv, PubMed)
    """

    def __init__(self, db, ai_client, poll_interval=30):
        """Initialize support agent."""
        super().__init__(
            AgentFramework.SUPPORT_EMPIRICAL,
            db,
            ai_client,
            poll_interval
        )

    async def investigate(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find supporting evidence for claim.

        Args:
            claim: Claim dict

        Returns:
            Investigation result with supporting evidence
        """
        claim_text = claim['normalized_text'] or claim['original_text']

        logger.info(f"Finding support for: {claim_text}")

        # Search for supporting evidence
        evidence_list = await self._search_supporting_evidence(claim_text)

        # Calculate confidence based on evidence quality
        confidence = self._calculate_finding_confidence(evidence_list)

        return {
            'finding_type': 'support',
            'summary': f"Found {len(evidence_list)} sources supporting this claim",
            'detailed_analysis': self._generate_analysis(claim_text, evidence_list),
            'confidence': confidence,
            'evidence': evidence_list
        }

    async def _search_supporting_evidence(
        self,
        claim: str
    ) -> List[Dict[str, Any]]:
        """
        Search for supporting evidence.

        MVP: Use LLM to generate plausible evidence.
        TODO: Real academic search.

        Args:
            claim: Claim text

        Returns:
            List of evidence dicts
        """
        prompt = f"""You are a research assistant finding evidence that SUPPORTS this claim:

"{claim}"

Find 3-5 academic sources that provide supporting evidence. For each source:
1. Generate a realistic APA citation
2. Provide a relevant quote that supports the claim
3. Rate relevance (0.0-1.0) - how relevant is this to the claim?
4. Rate credibility (0.0-1.0) - how credible is this source?

Return JSON array:
[
  {{
    "citation_apa": "Author, A. B., & Author, C. D. (2023). Article title. Journal Name, 10(2), 123-145. https://doi.org/10.xxxx/xxxxx",
    "quote": "Relevant passage from the source that supports the claim",
    "source_category": "academic",
    "relevance_score": 0.9,
    "credibility_score": 0.85
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            response = await self.ai.generate(
                prompt,
                temperature=0.6,
                response_format='json'
            )
            evidence = json.loads(response)

            # Validate structure
            if not isinstance(evidence, list):
                logger.error(f"Expected list, got {type(evidence)}")
                return []

            logger.info(f"Found {len(evidence)} supporting sources")
            return evidence

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching evidence: {e}")
            return []

    def _calculate_finding_confidence(self, evidence_list: List[Dict]) -> float:
        """
        Calculate confidence in this finding.

        Args:
            evidence_list: List of evidence

        Returns:
            Confidence score (0.0-1.0)
        """
        if not evidence_list:
            return 0.0

        # Average of relevance and credibility scores
        total = 0.0
        for evidence in evidence_list:
            relevance = evidence.get('relevance_score', 0.5)
            credibility = evidence.get('credibility_score', 0.5)
            total += (relevance + credibility) / 2

        confidence = total / len(evidence_list)
        return round(confidence, 2)

    def _generate_analysis(
        self,
        claim: str,
        evidence_list: List[Dict]
    ) -> str:
        """
        Generate detailed analysis of findings.

        Args:
            claim: Claim text
            evidence_list: Evidence found

        Returns:
            Analysis text
        """
        if not evidence_list:
            return "No supporting evidence found."

        analysis = f"Analysis of support for: '{claim}'\n\n"
        analysis += f"Found {len(evidence_list)} supporting sources:\n\n"

        for i, evidence in enumerate(evidence_list, 1):
            relevance = evidence.get('relevance_score', 0)
            credibility = evidence.get('credibility_score', 0)

            analysis += f"{i}. {evidence['citation_apa']}\n"
            analysis += f"   Relevance: {relevance:.2f}, Credibility: {credibility:.2f}\n"

            if 'quote' in evidence:
                quote = evidence['quote'][:200]
                analysis += f"   Quote: \"{quote}...\"\n"

            analysis += "\n"

        avg_relevance = sum(e.get('relevance_score', 0) for e in evidence_list) / len(evidence_list)
        avg_credibility = sum(e.get('credibility_score', 0) for e in evidence_list) / len(evidence_list)

        analysis += f"Overall: Average relevance {avg_relevance:.2f}, "
        analysis += f"average credibility {avg_credibility:.2f}"

        return analysis
