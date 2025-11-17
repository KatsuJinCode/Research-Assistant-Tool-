"""
Investigation Agent Base Class

Base class for all investigation agents that research claims.
Agents use research APIs and Claude's analysis to find evidence.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from research_agent.research_apis import ArxivClient, CoreClient, OpenAlexClient


class InvestigationAgent:
    """
    Base class for investigation agents.

    Agents research claims by:
    1. Searching research databases (arXiv, CORE, OpenAlex)
    2. Analyzing results (Claude does this)
    3. Extracting relevant evidence
    4. Assessing credibility
    5. Storing findings in graph database
    """

    def __init__(self, graph_db, agent_type: str):
        """
        Initialize investigation agent.

        Args:
            graph_db: Graph database instance
            agent_type: Type of agent (support, challenge, analysis)
        """
        self.graph = graph_db
        self.agent_type = agent_type

        # Initialize research API clients
        self.arxiv = ArxivClient()
        self.core = CoreClient()
        self.openalex = OpenAlexClient()

    def investigate(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Investigate a claim.

        This is the main method that subclasses implement.

        Args:
            claim: Claim dictionary with 'id', 'text', etc.

        Returns:
            Investigation result dict
        """
        raise NotImplementedError("Subclasses must implement investigate()")

    def search_research_databases(self, query: str,
                                  max_results_per_db: int = 5) -> List[Dict[str, Any]]:
        """
        Search all research databases for papers related to query.

        Args:
            query: Search query
            max_results_per_db: Max results from each database

        Returns:
            Combined list of papers from all databases
        """
        all_papers = []

        # Search arXiv
        try:
            arxiv_results = self.arxiv.search(query, max_results=max_results_per_db)
            all_papers.extend(arxiv_results)
        except Exception as e:
            print(f"⚠ arXiv search failed: {e}")

        # Search CORE
        try:
            core_results = self.core.search(query, limit=max_results_per_db)
            all_papers.extend(core_results)
        except Exception as e:
            print(f"⚠ CORE search failed: {e}")

        # Search OpenAlex
        try:
            openalex_results = self.openalex.search(query, max_results=max_results_per_db)
            all_papers.extend(openalex_results)
        except Exception as e:
            print(f"⚠ OpenAlex search failed: {e}")

        return all_papers

    def extract_evidence_from_paper(self, paper: Dict[str, Any],
                                   claim_text: str) -> Optional[Dict[str, Any]]:
        """
        Extract evidence from a paper that relates to the claim.

        I (Claude) would analyze the paper's abstract/content to find
        relevant evidence.

        Args:
            paper: Paper metadata dict
            claim_text: The claim being investigated

        Returns:
            Evidence dict or None if not relevant
        """
        # I (Claude) analyze the abstract
        abstract = paper.get('abstract', '')

        if not abstract:
            return None

        # Simple relevance check (in production, I'd do semantic analysis)
        claim_words = set(claim_text.lower().split())
        abstract_words = set(abstract.lower().split())
        overlap = claim_words & abstract_words

        relevance_score = len(overlap) / len(claim_words) if claim_words else 0

        if relevance_score < 0.2:  # Not relevant enough
            return None

        # Extract evidence
        evidence = {
            'text': abstract[:500],  # First 500 chars
            'source_title': paper.get('title', 'Unknown'),
            'source_authors': paper.get('authors', []),
            'source_year': paper.get('year') or paper.get('published', '')[:4],
            'source_url': paper.get('url') or paper.get('pdf_url'),
            'source_doi': paper.get('doi'),
            'source_database': paper.get('source', 'Unknown'),
            'relevance_score': relevance_score,
            'citation': self._format_citation(paper)
        }

        return evidence

    def _format_citation(self, paper: Dict[str, Any]) -> str:
        """Format paper citation in APA style."""
        source = paper.get('source', '').lower()

        if 'arxiv' in source:
            return self.arxiv.format_citation(paper)
        elif 'core' in source:
            return self.core.format_citation(paper)
        elif 'openalex' in source:
            return self.openalex.format_citation(paper)
        else:
            # Generic format
            authors = paper.get('authors', [])
            author_str = ', '.join(authors[:3]) if authors else "Unknown"
            if len(authors) > 3:
                author_str += ", et al."

            title = paper.get('title', 'Untitled')
            year = paper.get('year', 'n.d.')

            return f"{author_str} ({year}). {title}."

    def assess_evidence_credibility(self, evidence: Dict[str, Any]) -> float:
        """
        Assess credibility of evidence.

        Factors:
        - Source database reputation
        - Publication year (recent = higher)
        - Citation count (if available)
        - Relevance score

        Args:
            evidence: Evidence dict

        Returns:
            Credibility score 0.0-1.0
        """
        score = 0.5  # Base score

        # Database credibility
        database = evidence.get('source_database', '').lower()
        if 'arxiv' in database:
            score += 0.15  # Preprints (good but not peer-reviewed)
        elif 'core' in database:
            score += 0.20  # Open access (peer-reviewed)
        elif 'openalex' in database:
            score += 0.15  # Mixed sources

        # Recency (prefer last 5 years)
        year = evidence.get('source_year')
        if year:
            try:
                year_int = int(str(year)[:4])
                current_year = datetime.now().year
                age = current_year - year_int

                if age <= 5:
                    score += 0.15
                elif age <= 10:
                    score += 0.10
            except:
                pass

        # Relevance
        relevance = evidence.get('relevance_score', 0)
        score += relevance * 0.20

        # Cap at 1.0
        return min(score, 1.0)

    def store_investigation(self, claim_id: str, findings: List[Dict[str, Any]],
                          summary: str, confidence: float) -> str:
        """
        Store investigation results in graph database.

        Args:
            claim_id: ID of claim investigated
            findings: List of evidence dicts
            summary: Text summary of findings
            confidence: Overall confidence in findings

        Returns:
            investigation_id: ID of created investigation node
        """
        investigation_id = self.graph.create_node('Investigation', {
            'agent_type': self.agent_type,
            'summary': summary,
            'confidence': confidence,
            'evidence_count': len(findings),
            'status': 'completed'
        })

        # Link to claim
        self.graph.create_relationship(
            investigation_id,
            claim_id,
            'INVESTIGATES'
        )

        # Store each piece of evidence
        for finding in findings:
            evidence_id = self.graph.create_node('Evidence', {
                'text': finding.get('text', ''),
                'citation': finding.get('citation', ''),
                'credibility': self.assess_evidence_credibility(finding),
                'relevance_score': finding.get('relevance_score', 0),
                'source_database': finding.get('source_database', ''),
                'source_url': finding.get('source_url')
            })

            # Link evidence to investigation
            self.graph.create_relationship(
                investigation_id,
                evidence_id,
                'FOUND'
            )

            # Create source node
            source_id = self.graph.create_node('Source', {
                'title': finding.get('source_title', ''),
                'authors': finding.get('source_authors', []),
                'year': finding.get('source_year', ''),
                'url': finding.get('source_url', ''),
                'doi': finding.get('source_doi')
            })

            # Link evidence to source
            self.graph.create_relationship(
                evidence_id,
                source_id,
                'REFERENCES'
            )

        return investigation_id
