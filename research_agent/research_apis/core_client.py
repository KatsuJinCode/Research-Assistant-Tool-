"""
CORE API Client

Access to world's largest collection of open access research papers.
API documentation: https://core.ac.uk/documentation/api
API v3 documentation: https://api.core.ac.uk/docs/v3

Free tier: 10,000 requests/month (no API key needed for basic search)
"""

import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional


class CoreClient:
    """
    Client for CORE API (COnnecting REpositories).

    CORE aggregates open access research papers from repositories worldwide,
    providing the largest collection of open access scientific papers.

    API Key: Optional for basic use, recommended for higher limits
    Get key at: https://core.ac.uk/services/api#form
    """

    BASE_URL = 'https://api.core.ac.uk/v3'

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CORE client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key
        self.session_user_agent = 'Research-Verification-Agent/1.0'

    def search(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search CORE for papers.

        Args:
            query: Search query
            limit: Maximum number of results (max 100)
            offset: Starting index for pagination

        Returns:
            List of paper dictionaries

        Query syntax:
            - Simple: "machine learning"
            - Title: "title:(neural networks)"
            - Author: "author:(einstein)"
            - Year: "year:2023"
            - Boolean: "quantum AND computing"
            - Wildcard: "comput*"
        """
        endpoint = f"{self.BASE_URL}/search/works"

        params = {
            'q': query,
            'limit': min(limit, 100),
            'offset': offset
        }

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read())
                return self._parse_core_response(data)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("[WARNING] Rate limit exceeded. Consider getting a free API key from https://core.ac.uk/services/api")
                return []
            raise

    def get_by_id(self, core_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by CORE ID.

        Args:
            core_id: CORE work ID

        Returns:
            Paper metadata or None
        """
        endpoint = f"{self.BASE_URL}/works/{core_id}"

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        request = urllib.request.Request(endpoint, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read())
                return self._parse_single_work(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def search_recent(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for recent papers (sorted by publication date).

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of recent papers
        """
        # CORE API v3 doesn't have built-in sorting in free tier
        # We'll filter results by recent years
        recent_query = f"{query} AND year:>=2023"
        return self.search(recent_query, limit=limit)

    def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Search for paper by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper metadata or None
        """
        # Clean DOI
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')

        results = self.search(f'doi:"{doi}"', limit=1)
        return results[0] if results else None

    def _parse_core_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse CORE API response into standardized format."""
        if 'results' not in data:
            return []

        papers = []
        for item in data['results']:
            paper = self._parse_single_work(item)
            if paper:
                papers.append(paper)

        return papers

    def _parse_single_work(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single CORE work item."""
        if not item:
            return None

        paper = {
            'source': 'CORE',
            'id': item.get('id'),
            'title': item.get('title', '').strip(),
            'abstract': item.get('abstract', '').strip() if item.get('abstract') else item.get('description', '').strip(),
            'authors': [],
            'year': item.get('yearPublished'),
            'doi': item.get('doi'),
            'url': item.get('downloadUrl') or item.get('sourceFulltextUrls', [None])[0],
            'pdf_url': item.get('downloadUrl'),
            'publisher': item.get('publisher'),
            'journal': item.get('journal'),
            'language': item.get('language', {}).get('name') if isinstance(item.get('language'), dict) else None,
            'open_access': True  # CORE only indexes OA papers
        }

        # Parse authors
        if 'authors' in item and isinstance(item['authors'], list):
            paper['authors'] = [
                author.get('name', '') if isinstance(author, dict) else str(author)
                for author in item['authors']
            ]

        # External IDs
        if 'identifiers' in item:
            paper['identifiers'] = item['identifiers']

        return paper

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
        elif authors:
            author_str = ', '.join(authors)
        else:
            author_str = "Unknown Author"

        title = paper.get('title', 'Untitled')
        year = paper.get('year', 'n.d.')

        citation = f"{author_str} ({year}). {title}."

        if paper.get('journal'):
            citation += f" {paper['journal']}."

        if paper.get('doi'):
            citation += f" https://doi.org/{paper['doi']}"
        elif paper.get('url'):
            citation += f" {paper['url']}"

        citation += " [Open Access via CORE]"

        return citation
