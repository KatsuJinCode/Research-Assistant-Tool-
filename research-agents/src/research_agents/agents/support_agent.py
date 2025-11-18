"""
Support Agent - Finds evidence that SUPPORTS claims.
"""

import json
import logging
from typing import List
from datetime import datetime

from .base_agent import BaseAgent
from ..interfaces import (
    DatabaseInterface,
    AIInterface,
    Claim,
    Finding,
    Evidence,
    InvestigationFramework,
    AgentConfig,
)


logger = logging.getLogger(__name__)


class SupportAgent(BaseAgent):
    """
    Find empirical evidence that SUPPORTS the claim.

    MVP: Uses LLM to generate plausible evidence.
    TODO Post-MVP: Real academic search (Semantic Scholar, arXiv, PubMed)
    """

    def __init__(
        self,
        db: DatabaseInterface,
        ai: AIInterface,
        config: AgentConfig = None,
    ):
        """Initialize support agent."""
        if config is None:
            config = AgentConfig(agent_type="support")

        super().__init__(
            InvestigationFramework.SUPPORT,
            db,
            ai,
            config,
        )

    async def investigate(self, claim: Claim) -> Finding:
        """
        Find supporting evidence for claim.

        Args:
            claim: Claim to investigate

        Returns:
            Finding with supporting evidence
        """
        logger.info(f"Finding support for: {claim.text}")

        # Search for supporting evidence
        evidence_list = await self._search_supporting_evidence(claim.text)

        # Calculate confidence based on evidence quality
        confidence_impact = self._calculate_confidence_impact(evidence_list)

        # Generate summary
        summary = f"Found {len(evidence_list)} sources supporting this claim"

        # Generate detailed analysis
        reasoning = self._generate_analysis(claim.text, evidence_list)

        return Finding(
            investigation_id=None,  # Will be set by base agent
            summary=summary,
            confidence_impact=confidence_impact,
            evidence_list=evidence_list,
            reasoning=reasoning,
            created_at=datetime.utcnow(),
        )

    async def _search_supporting_evidence(
        self,
        claim_text: str
    ) -> List[Evidence]:
        """
        Search for supporting evidence.

        MVP: Use LLM to generate plausible evidence.
        TODO: Real academic search.

        Args:
            claim_text: Claim text

        Returns:
            List of Evidence objects
        """
        prompt = f"""You are a research assistant finding evidence that SUPPORTS this claim:

"{claim_text}"

Find 3-5 academic sources that provide supporting evidence. For each source:
1. Generate a realistic APA citation
2. Provide a relevant quote that supports the claim
3. Rate relevance (0.0-1.0) - how relevant is this to the claim?
4. Rate credibility (0.0-1.0) - how credible is this source?

Return JSON array:
[
  {{
    "source": "Author, A. B., & Author, C. D. (2023). Article title. Journal Name, 10(2), 123-145. https://doi.org/10.xxxx/xxxxx",
    "quote": "Relevant passage from the source that supports the claim",
    "relevance_score": 0.9,
    "publication_year": 2023
  }}
]

Return ONLY the JSON array, no other text."""

        try:
            response = await self.ai.generate(
                prompt,
                temperature=0.6,
                response_format='json'
            )
            evidence_data = json.loads(response)

            # Validate structure
            if not isinstance(evidence_data, list):
                logger.error(f"Expected list, got {type(evidence_data)}")
                return []

            # Convert to Evidence objects
            evidence_list = []
            for item in evidence_data:
                evidence = Evidence(
                    source=item.get('source', 'Unknown source'),
                    quote=item.get('quote', ''),
                    relevance_score=float(item.get('relevance_score', 0.5)),
                    supports_claim=True,  # Support agent finds supporting evidence
                    publication_year=item.get('publication_year'),
                    created_at=datetime.utcnow(),
                )
                evidence_list.append(evidence)

            logger.info(f"Found {len(evidence_list)} supporting sources")
            return evidence_list

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching evidence: {e}")
            return []

    def _calculate_confidence_impact(self, evidence_list: List[Evidence]) -> float:
        """
        Calculate confidence impact of this finding.

        Args:
            evidence_list: List of evidence

        Returns:
            Confidence impact score (-1.0 to 1.0)
        """
        if not evidence_list:
            return 0.0

        # Average relevance score, scaled to impact
        total_relevance = sum(e.relevance_score for e in evidence_list)
        avg_relevance = total_relevance / len(evidence_list)

        # Positive impact since this is supporting evidence
        # Scale: 0.0-0.3 for weak support, 0.3-0.7 for moderate, 0.7-1.0 for strong
        impact = avg_relevance * 0.5  # Cap at 0.5 to allow for multiple investigations

        return round(impact, 2)

    def _generate_analysis(
        self,
        claim: str,
        evidence_list: List[Evidence]
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
            analysis += f"{i}. {evidence.source}\n"
            analysis += f"   Relevance: {evidence.relevance_score:.2f}\n"

            if evidence.quote:
                quote = evidence.quote[:200]
                analysis += f"   Quote: \"{quote}...\"\n"

            analysis += "\n"

        avg_relevance = sum(e.relevance_score for e in evidence_list) / len(evidence_list)
        analysis += f"Overall: Average relevance {avg_relevance:.2f}"

        return analysis
