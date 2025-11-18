"""
Analysis Agent - Analyzes and clarifies key terms and definitions.
"""

import json
import logging
from typing import Dict, Any, List
from research_agent.agents.base_agent import BaseAgent
from research_agent.models import AgentFramework


logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analyze and clarify key terms, definitions, and scope.

    Helps understand what a claim actually means before verification.
    """

    def __init__(self, db, ai_client, poll_interval=30):
        """Initialize analysis agent."""
        super().__init__(
            AgentFramework.ANALYSIS_DEFINITIONAL,
            db,
            ai_client,
            poll_interval
        )

    async def investigate(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze claim definitions and scope.

        Args:
            claim: Claim dict

        Returns:
            Investigation result with clarifications
        """
        claim_text = claim['normalized_text'] or claim['original_text']

        logger.info(f"Analyzing: {claim_text}")

        # Perform definitional analysis
        analysis_result = await self._analyze_definitions(claim_text)

        # Generate evidence items for key definitions
        evidence_list = self._create_definition_evidence(analysis_result)

        return {
            'finding_type': 'clarification',
            'summary': analysis_result.get('summary', 'Definitional analysis completed'),
            'detailed_analysis': analysis_result.get('detailed_analysis', ''),
            'confidence': 0.8,  # Definitions are generally reliable
            'evidence': evidence_list
        }

    async def _analyze_definitions(self, claim: str) -> Dict[str, Any]:
        """
        Analyze key terms and definitions in claim.

        Args:
            claim: Claim text

        Returns:
            Analysis dict
        """
        prompt = f"""Analyze the key terms and definitions in this claim:

"{claim}"

Identify:
1. Key terms that need definition
2. Ambiguous terms that could be interpreted multiple ways
3. Scope and boundaries of the claim
4. Implicit assumptions in the claim

Return JSON:
{{
  "key_terms": [
    {{
      "term": "term name",
      "definition": "clear definition",
      "importance": "why this matters for the claim",
      "ambiguity_level": "high/medium/low"
    }}
  ],
  "scope_analysis": "What is the scope and what are the boundaries?",
  "assumptions": ["assumption 1", "assumption 2"],
  "summary": "Brief summary of definitional analysis"
}}

Return ONLY the JSON, no other text."""

        try:
            response = await self.ai.generate(
                prompt,
                temperature=0.3,
                response_format='json'
            )
            analysis = json.loads(response)

            # Generate detailed analysis text
            detailed = self._format_analysis(analysis)
            analysis['detailed_analysis'] = detailed

            logger.info(f"Analyzed {len(analysis.get('key_terms', []))} key terms")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from AI: {e}")
            return {
                'summary': 'Analysis failed',
                'detailed_analysis': f'Error: {e}',
                'key_terms': []
            }
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return {
                'summary': 'Analysis error',
                'detailed_analysis': f'Error: {e}',
                'key_terms': []
            }

    def _create_definition_evidence(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create evidence items from definitions.

        Args:
            analysis: Analysis result

        Returns:
            List of evidence dicts
        """
        evidence_list = []

        for term_data in analysis.get('key_terms', []):
            # Create evidence entry for each key term definition
            evidence_list.append({
                'citation_apa': f"Definitional Analysis: {term_data['term']}",
                'quote': f"{term_data['term']}: {term_data['definition']}",
                'source_category': 'academic',
                'relevance_score': 0.9,
                'credibility_score': 0.8
            })

        return evidence_list

    def _format_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Format analysis as readable text.

        Args:
            analysis: Analysis dict

        Returns:
            Formatted analysis text
        """
        text = "Definitional Analysis\n\n"

        # Key terms
        if 'key_terms' in analysis and analysis['key_terms']:
            text += "Key Terms:\n"
            for term_data in analysis['key_terms']:
                text += f"\n- {term_data['term']} (Ambiguity: {term_data.get('ambiguity_level', 'unknown')})\n"
                text += f"  Definition: {term_data['definition']}\n"
                text += f"  Importance: {term_data.get('importance', 'N/A')}\n"

        # Scope
        if 'scope_analysis' in analysis:
            text += f"\nScope Analysis:\n{analysis['scope_analysis']}\n"

        # Assumptions
        if 'assumptions' in analysis and analysis['assumptions']:
            text += "\nImplicit Assumptions:\n"
            for i, assumption in enumerate(analysis['assumptions'], 1):
                text += f"{i}. {assumption}\n"

        return text
