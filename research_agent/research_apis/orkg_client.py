"""
ORKG (Open Research Knowledge Graph) API Client

Free access to structured research knowledge.
API: https://orkg.org/data
Docs: https://orkg.readthedocs.io/
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ORKGClient:
    """
    Client for the Open Research Knowledge Graph (ORKG) API.

    ORKG provides structured research papers, comparisons, and knowledge graphs.
    Free to use, no API key required for basic access.

    API Documentation: https://orkg.readthedocs.io/
    """

    def __init__(self):
        """Initialize ORKG client."""
        try:
            import orkg
            self.orkg = orkg
            self.api = orkg.ORKG()
            self._available = True
            logger.info("ORKG client initialized successfully")
        except ImportError:
            self._available = False
            logger.warning("ORKG package not installed. Install with: pip install orkg")

    def is_available(self) -> bool:
        """Check if ORKG package is available."""
        return self._available

    def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search ORKG for research papers.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of paper dictionaries with metadata

        Example:
            >>> client = ORKGClient()
            >>> papers = client.search("machine learning", max_results=5)
            >>> for paper in papers:
            ...     print(paper['title'])
        """
        if not self._available:
            raise RuntimeError("ORKG package not installed. Install with: pip install orkg")

        try:
            # Search for papers
            results = self.api.papers.search(query=query, size=max_results)

            papers = []
            for paper in results.content:
                papers.append({
                    'id': paper.id,
                    'title': paper.title,
                    'doi': paper.doi if hasattr(paper, 'doi') else None,
                    'publication_year': paper.publication_info.published_year if hasattr(paper, 'publication_info') else None,
                    'authors': self._extract_authors(paper),
                    'url': f"https://orkg.org/paper/{paper.id}",
                    'source': 'ORKG',
                    'abstract': paper.research_fields[0].label if hasattr(paper, 'research_fields') and paper.research_fields else None,
                    'research_fields': [field.label for field in paper.research_fields] if hasattr(paper, 'research_fields') else [],
                })

            logger.info(f"ORKG search found {len(papers)} papers for query: {query}")
            return papers

        except Exception as e:
            logger.error(f"ORKG search failed: {e}")
            return []

    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific paper.

        Args:
            paper_id: ORKG paper ID

        Returns:
            Paper dictionary with metadata, or None if not found

        Example:
            >>> client = ORKGClient()
            >>> paper = client.get_paper("R123456")
            >>> print(paper['title'])
        """
        if not self._available:
            raise RuntimeError("ORKG package not installed. Install with: pip install orkg")

        try:
            paper = self.api.papers.by_id(id=paper_id)

            return {
                'id': paper.id,
                'title': paper.title,
                'doi': paper.doi if hasattr(paper, 'doi') else None,
                'publication_year': paper.publication_info.published_year if hasattr(paper, 'publication_info') else None,
                'authors': self._extract_authors(paper),
                'url': f"https://orkg.org/paper/{paper.id}",
                'source': 'ORKG',
                'research_fields': [field.label for field in paper.research_fields] if hasattr(paper, 'research_fields') else [],
                'contributions': self._extract_contributions(paper),
            }

        except Exception as e:
            logger.error(f"ORKG get_paper failed for {paper_id}: {e}")
            return None

    def get_comparisons(self, topic: str, max_results: int = 5) -> List[Dict]:
        """
        Get research comparisons for a topic.

        ORKG specializes in structured comparisons of research papers.

        Args:
            topic: Research topic to search for
            max_results: Maximum number of comparisons to return

        Returns:
            List of comparison dictionaries

        Example:
            >>> client = ORKGClient()
            >>> comparisons = client.get_comparisons("deep learning", max_results=3)
            >>> for comp in comparisons:
            ...     print(comp['title'])
        """
        if not self._available:
            raise RuntimeError("ORKG package not installed. Install with: pip install orkg")

        try:
            results = self.api.comparisons.search(query=topic, size=max_results)

            comparisons = []
            for comp in results.content:
                comparisons.append({
                    'id': comp.id,
                    'title': comp.title,
                    'url': f"https://orkg.org/comparison/{comp.id}",
                    'description': comp.description if hasattr(comp, 'description') else None,
                    'num_papers': len(comp.contributions) if hasattr(comp, 'contributions') else 0,
                    'research_fields': [field.label for field in comp.research_fields] if hasattr(comp, 'research_fields') else [],
                    'source': 'ORKG Comparison',
                })

            logger.info(f"ORKG found {len(comparisons)} comparisons for: {topic}")
            return comparisons

        except Exception as e:
            logger.error(f"ORKG comparison search failed: {e}")
            return []

    def _extract_authors(self, paper) -> List[str]:
        """Extract author names from paper object."""
        try:
            if hasattr(paper, 'authors') and paper.authors:
                return [author.name for author in paper.authors]
            return []
        except Exception:
            return []

    def _extract_contributions(self, paper) -> List[Dict]:
        """Extract research contributions from paper."""
        try:
            if hasattr(paper, 'contributions') and paper.contributions:
                return [{
                    'id': contrib.id,
                    'name': contrib.label if hasattr(contrib, 'label') else None,
                } for contrib in paper.contributions]
            return []
        except Exception:
            return []

    def format_citation(self, paper: Dict) -> str:
        """
        Format paper as APA-style citation.

        Args:
            paper: Paper dictionary from search() or get_paper()

        Returns:
            APA-formatted citation string

        Example:
            >>> citation = client.format_citation(paper)
            >>> print(citation)
            Smith, J. et al. (2024). Title of paper. ORKG. https://orkg.org/paper/R123
        """
        authors = paper.get('authors', [])
        if not authors:
            author_str = "Unknown"
        elif len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        else:
            author_str = f"{authors[0]} et al."

        year = paper.get('publication_year', 'n.d.')
        title = paper.get('title', 'Untitled')
        url = paper.get('url', '')

        return f"{author_str} ({year}). {title}. ORKG. {url}"


# Example usage
if __name__ == "__main__":
    client = ORKGClient()

    if client.is_available():
        # Search for papers
        print("Searching ORKG for 'mental illness'...")
        papers = client.search("mental illness", max_results=3)

        for i, paper in enumerate(papers, 1):
            print(f"\nPaper {i}:")
            print(f"  Title: {paper['title']}")
            print(f"  Authors: {', '.join(paper.get('authors', ['Unknown']))}")
            print(f"  Year: {paper.get('publication_year', 'N/A')}")
            print(f"  URL: {paper['url']}")
            print(f"  Citation: {client.format_citation(paper)}")

        # Search for comparisons
        print("\n" + "="*80)
        print("Searching for research comparisons...")
        comparisons = client.get_comparisons("deep learning", max_results=2)

        for i, comp in enumerate(comparisons, 1):
            print(f"\nComparison {i}:")
            print(f"  Title: {comp['title']}")
            print(f"  Papers: {comp['num_papers']}")
            print(f"  URL: {comp['url']}")
    else:
        print("ORKG package not installed.")
        print("Install with: pip install orkg")
