"""
arXiv API Client

Free access to preprints in physics, mathematics, computer science, and more.
API documentation: https://info.arxiv.org/help/api/
Python client: pip install arxiv
"""

import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from datetime import datetime


class ArxivClient:
    """
    Client for arXiv API.

    arXiv is a free distribution service and open-access archive for scholarly
    articles in physics, mathematics, computer science, quantitative biology,
    quantitative finance, statistics, electrical engineering and systems science.

    No API key required!
    """

    BASE_URL = 'http://export.arxiv.org/api/query'

    def __init__(self):
        """Initialize arXiv client."""
        self.session_user_agent = 'Research-Verification-Agent/1.0'

    def search(self, query: str, max_results: int = 10,
               start: int = 0, sort_by: str = 'relevance') -> List[Dict[str, Any]]:
        """
        Search arXiv for papers.

        Args:
            query: Search query (e.g., "quantum computing", "all:electron")
            max_results: Maximum number of results to return
            start: Starting index for pagination
            sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate')

        Returns:
            List of paper dictionaries with metadata

        Query examples:
            - "quantum computing" - Search all fields
            - "ti:neural networks" - Search title
            - "au:einstein" - Search author
            - "abs:machine learning" - Search abstract
            - "cat:cs.AI" - Category (AI)
        """
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': sort_by,
            'sortOrder': 'descending'
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(url)
        request.add_header('User-Agent', self.session_user_agent)

        with urllib.request.urlopen(request) as response:
            xml_data = response.read()

        return self._parse_arxiv_response(xml_data)

    def get_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2103.14030" or "arxiv:2103.14030")

        Returns:
            Paper metadata dictionary or None if not found
        """
        # Clean ID
        arxiv_id = arxiv_id.replace('arxiv:', '').replace('arXiv:', '')

        params = {
            'id_list': arxiv_id
        }

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        request = urllib.request.Request(url)
        request.add_header('User-Agent', self.session_user_agent)

        with urllib.request.urlopen(request) as response:
            xml_data = response.read()

        results = self._parse_arxiv_response(xml_data)
        return results[0] if results else None

    def search_by_category(self, category: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search by arXiv category.

        Args:
            category: arXiv category code (e.g., "cs.AI", "physics.gen-ph")
            max_results: Maximum results

        Returns:
            List of papers

        Popular categories:
            - cs.AI: Artificial Intelligence
            - cs.LG: Machine Learning
            - q-bio.NC: Neurons and Cognition
            - physics.med-ph: Medical Physics
            - stat.ML: Machine Learning (Statistics)
        """
        return self.search(f"cat:{category}", max_results=max_results)

    def _parse_arxiv_response(self, xml_data: bytes) -> List[Dict[str, Any]]:
        """Parse arXiv XML response into list of paper dictionaries."""
        namespace = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }

        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall('atom:entry', namespace):
            # Extract basic metadata
            paper = {}

            # ID and URL
            id_elem = entry.find('atom:id', namespace)
            if id_elem is not None:
                paper['id'] = id_elem.text.split('/')[-1]  # Extract ID from URL
                paper['url'] = id_elem.text

            # Title
            title_elem = entry.find('atom:title', namespace)
            if title_elem is not None:
                paper['title'] = ' '.join(title_elem.text.split())

            # Abstract
            summary_elem = entry.find('atom:summary', namespace)
            if summary_elem is not None:
                paper['abstract'] = ' '.join(summary_elem.text.split())

            # Authors
            authors = []
            for author in entry.findall('atom:author', namespace):
                name_elem = author.find('atom:name', namespace)
                if name_elem is not None:
                    authors.append(name_elem.text)
            paper['authors'] = authors

            # Published date
            published_elem = entry.find('atom:published', namespace)
            if published_elem is not None:
                paper['published'] = published_elem.text[:10]  # YYYY-MM-DD

            # Updated date
            updated_elem = entry.find('atom:updated', namespace)
            if updated_elem is not None:
                paper['updated'] = updated_elem.text[:10]

            # Categories
            categories = []
            for category in entry.findall('atom:category', namespace):
                term = category.get('term')
                if term:
                    categories.append(term)
            paper['categories'] = categories

            # PDF link
            for link in entry.findall('atom:link', namespace):
                if link.get('title') == 'pdf':
                    paper['pdf_url'] = link.get('href')

            # DOI (if available)
            doi_elem = entry.find('arxiv:doi', namespace)
            if doi_elem is not None:
                paper['doi'] = doi_elem.text

            # Journal reference (if available)
            journal_elem = entry.find('arxiv:journal_ref', namespace)
            if journal_elem is not None:
                paper['journal_ref'] = journal_elem.text

            paper['source'] = 'arXiv'
            papers.append(paper)

        return papers

    def format_citation(self, paper: Dict[str, Any]) -> str:
        """
        Format paper as APA citation.

        Args:
            paper: Paper metadata dictionary

        Returns:
            APA-formatted citation string
        """
        authors = paper.get('authors', [])
        if len(authors) > 3:
            author_str = f"{authors[0]}, et al."
        else:
            author_str = ', '.join(authors)

        title = paper.get('title', 'Untitled')
        year = paper.get('published', '')[:4] if paper.get('published') else 'n.d.'
        arxiv_id = paper.get('id', '')

        citation = f"{author_str} ({year}). {title}. arXiv:{arxiv_id}"

        if paper.get('journal_ref'):
            citation += f" [Published in: {paper['journal_ref']}]"

        if paper.get('doi'):
            citation += f" https://doi.org/{paper['doi']}"

        return citation
