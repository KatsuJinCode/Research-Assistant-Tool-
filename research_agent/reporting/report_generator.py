"""
Report generation for claims and investigations.

Generates markdown reports with confidence scores and evidence.
"""

import logging
from typing import Dict, Any, List
from uuid import UUID
from research_agent.database import Database
from research_agent.utils.confidence import ConfidenceCalculator


logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate investigation reports."""

    def __init__(self, db: Database):
        """
        Initialize report generator.

        Args:
            db: Database instance
        """
        self.db = db
        self.confidence_calc = ConfidenceCalculator(db)

    async def generate_claim_report(self, claim_id: UUID) -> str:
        """
        Generate markdown report for a claim.

        Args:
            claim_id: Claim ID

        Returns:
            Markdown report string
        """
        # Load claim data
        claim = await self.db.get_claim(claim_id)
        if not claim:
            return f"Error: Claim {claim_id} not found"

        # Load qualifiers
        qualifiers = await self.db.get_claim_qualifiers(claim_id)

        # Load findings
        findings = await self.db.get_findings_for_claim(claim_id)

        # Get confidence breakdown
        confidence = await self.confidence_calc.get_claim_confidence_breakdown(claim_id)

        # Group findings by type
        support = [f for f in findings if f['finding_type'] == 'support']
        challenge = [f for f in findings if f['finding_type'] == 'challenge']
        neutral = [
            f for f in findings
            if f['finding_type'] in ['neutral', 'clarification']
        ]

        # Generate report
        report = self._build_report(claim, qualifiers, support, challenge, neutral, confidence)

        return report

    def _build_report(
        self,
        claim: Dict[str, Any],
        qualifiers: List[Dict[str, Any]],
        support: List[Dict[str, Any]],
        challenge: List[Dict[str, Any]],
        neutral: List[Dict[str, Any]],
        confidence: Dict[str, Any]
    ) -> str:
        """Build markdown report."""
        report = []

        # Header
        report.append("# Investigation Report")
        report.append("")

        # Claim section
        report.append("## Claim")
        report.append("")
        report.append(f"**Original**: {claim['original_text']}")
        report.append("")

        if claim['normalized_text']:
            report.append(f"**Normalized**: {claim['normalized_text']}")
            report.append("")

        # Qualifiers
        if qualifiers:
            qualifier_texts = [q['qualifier_text'] for q in qualifiers]
            report.append(f"**Qualifiers**: {', '.join(qualifier_texts)}")
            report.append("")

        report.append("---")
        report.append("")

        # Overall assessment
        report.append("## Overall Assessment")
        report.append("")
        report.append(
            f"**Confidence**: {confidence['overall_confidence']:.2f} "
            f"({confidence['overall_label']})"
        )
        report.append("")
        report.append(confidence['overall_stars'])
        report.append("")

        report.append("### Breakdown")
        report.append("")
        report.append(
            f"- Support: {confidence['support_stars']} "
            f"({confidence['support_confidence']:.2f}) "
            f"- {confidence['support_count']} findings"
        )
        report.append(
            f"- Challenge: {confidence['challenge_stars']} "
            f"({confidence['challenge_confidence']:.2f}) "
            f"- {confidence['challenge_count']} findings"
        )

        if confidence['needs_more_investigation']:
            report.append("")
            report.append("[WARNING]  **Recommendation**: Low confidence - additional investigation recommended")

        report.append("")
        report.append("---")
        report.append("")

        # Supporting evidence
        if support:
            report.append(f"## Supporting Evidence ({len(support)} findings)")
            report.append("")
            for i, finding in enumerate(support, 1):
                report.extend(await self._format_finding(finding, i))

        # Challenging evidence
        if challenge:
            report.append(f"## Challenging Evidence ({len(challenge)} findings)")
            report.append("")
            for i, finding in enumerate(challenge, 1):
                report.extend(await self._format_finding(finding, i))

        # Analysis/Clarification
        if neutral:
            report.append(f"## Analysis & Clarification ({len(neutral)} findings)")
            report.append("")
            for i, finding in enumerate(neutral, 1):
                report.extend(await self._format_finding(finding, i))

        return "\n".join(report)

    async def _format_finding(
        self,
        finding: Dict[str, Any],
        number: int
    ) -> List[str]:
        """Format a single finding."""
        lines = []

        # Finding header
        confidence_stars = self.confidence_calc.get_confidence_stars(
            finding.get('confidence', 0.5)
        )
        lines.append(
            f"### Finding {number} - {finding['agent_framework']} "
            f"({confidence_stars})"
        )
        lines.append("")

        # Summary
        lines.append(f"**Summary**: {finding['summary']}")
        lines.append("")

        # Evidence
        evidence_list = await self.db.get_evidence_for_finding(finding['id'])
        if evidence_list:
            lines.append("**Evidence**:")
            lines.append("")
            for evidence in evidence_list:
                lines.append(f"- {evidence['citation_apa']}")

                if evidence.get('relevant_quote'):
                    quote = evidence['relevant_quote']
                    if len(quote) > 200:
                        quote = quote[:200] + "..."
                    lines.append(f"  > \"{quote}\"")

                relevance = evidence.get('relevance_score', 0)
                credibility = evidence.get('credibility_score', 0)
                lines.append(
                    f"  *Relevance: {relevance:.2f}, Credibility: {credibility:.2f}*"
                )
                lines.append("")

        lines.append("")
        return lines

    async def generate_summary_report(self, document_id: UUID) -> str:
        """
        Generate summary report for all claims in a document.

        Args:
            document_id: Document ID

        Returns:
            Markdown report
        """
        # Get document
        document = await self.db.get_document(document_id)
        if not document:
            return f"Error: Document {document_id} not found"

        # Get all claims for document
        claims = await self.db.fetch(
            "SELECT * FROM claims WHERE source_document_id = $1 ORDER BY created_at",
            document_id
        )

        report = []
        report.append(f"# Summary Report: {document['title']}")
        report.append("")
        report.append(f"**Total Claims**: {len(claims)}")
        report.append("")
        report.append("---")
        report.append("")

        for i, claim in enumerate(claims, 1):
            report.append(f"## Claim {i}")
            report.append("")
            report.append(claim['original_text'])
            report.append("")

            # Get confidence
            confidence = await self.confidence_calc.get_claim_confidence_breakdown(
                claim['id']
            )
            report.append(
                f"**Confidence**: {confidence['overall_confidence']:.2f} "
                f"{confidence['overall_stars']}"
            )
            report.append("")

            # Get finding counts
            report.append(
                f"- Support: {confidence['support_count']}, "
                f"Challenge: {confidence['challenge_count']}, "
                f"Analysis: {confidence['neutral_count']}"
            )
            report.append("")
            report.append("---")
            report.append("")

        return "\n".join(report)
