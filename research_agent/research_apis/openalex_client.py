"""
OpenAlex API Client

Comprehensive database of scholarly papers, authors, institutions, and more.
API documentation: https://docs.openalex.org/
Python client: pyalex

Free, no API key required!
Rate limit: 100,000 requests/day per user
"""

import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional


class OpenAlexClient:
    """
    Client for OpenAlex API.

    OpenAlex is a free, open catalog of scholarly papers, authors, institutions,
    and more. It indexes ~250M works with comprehensive metadata and citation data.

    No API key required!
    Polite pool: Add email to get better rate limits (recommended)
    """

    BASE_URL = 'https://api.openalex.org'

    def __init__(self, email: Optional[str] = None):
        """
        Initialize OpenAlex client.

        Args:
            email: Your email for "polite pool" (better rate limits)
                  Not required but recommended
        """
        self.email = email
        self.session_user_agent = 'Research-Verification-Agent/1.0'

    def search(self, query: str, max_results: int = 10,
               filter_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search OpenAlex for papers (works).

        Args:
            query: Search query
            max_results: Maximum number of results
            filter_params: Optional filters (e.g., {'from_publication_year': 2020})

        Returns:
            List of paper dictionaries

        Filter examples:
            - {'from_publication_year': 2020} - Papers from 2020 onwards
            - {'type': 'journal-article'} - Only journal articles
            - {'is_oa': True} - Only open access
            - {'has_fulltext': True} - Only papers with full text
        """
        endpoint = f"{self.BASE_URL}/works"

        params = {
            'search': query,
            'per_page': min(max_results, 200)  # Max 200 per page
        }

        # Add email for polite pool
        if self.email:
            params['mailto'] = self.email

        # Add filters
        if filter_params:
            filter_parts = []
            for key, value in filter_params.items():
                if isinstance(value, bool):
                    filter_parts.append(f"{key}:{str(value).lower()}")
                else:
                    filter_parts.append(f"{key}:{value}")

            if filter_parts:
                params['filter'] = ','.join(filter_parts)

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._parse_works_response(data)

    def get_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper metadata or None
        """
        # Clean and encode DOI
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        doi_encoded = urllib.parse.quote(doi, safe='')

        endpoint = f"{self.BASE_URL}/works/https://doi.org/{doi_encoded}"

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        request = urllib.request.Request(endpoint, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read())
                return self._parse_single_work(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def get_by_openalex_id(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """
        Get paper by OpenAlex ID.

        Args:
            openalex_id: OpenAlex work ID (e.g., "W2741809807")

        Returns:
            Paper metadata or None
        """
        # Clean ID
        if not openalex_id.startswith('W'):
            openalex_id = f"W{openalex_id}"

        endpoint = f"{self.BASE_URL}/works/{openalex_id}"

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        request = urllib.request.Request(endpoint, headers=headers)

        try:
            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read())
                return self._parse_single_work(data)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def search_recent_oa(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for recent open access papers.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of recent OA papers
        """
        import datetime
        current_year = datetime.datetime.now().year

        filters = {
            'is_oa': True,
            'from_publication_year': current_year - 2  # Last 2 years
        }

        return self.search(query, max_results=max_results, filter_params=filters)

    def search_highly_cited(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for highly cited papers on a topic.

        Args:
            query: Search query
            max_results: Maximum results

        Returns:
            List of highly cited papers (sorted by citation count)
        """
        endpoint = f"{self.BASE_URL}/works"

        params = {
            'search': query,
            'per_page': min(max_results, 200),
            'sort': 'cited_by_count:desc'  # Sort by citations
        }

        if self.email:
            params['mailto'] = self.email

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        headers = {
            'User-Agent': self.session_user_agent,
            'Accept': 'application/json'
        }

        request = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())

        return self._parse_works_response(data)

    def _parse_works_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse OpenAlex works response."""
        if 'results' not in data:
            return []

        papers = []
        for item in data['results']:
            paper = self._parse_single_work(item)
            if paper:
                papers.append(paper)

        return papers

    def _parse_single_work(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a single OpenAlex work."""
        if not item:
            return None

        paper = {
            'source': 'OpenAlex',
            'id': item.get('id', '').split('/')[-1],  # Extract ID from URL
            'openalex_id': item.get('id'),
            'title': item.get('title', '').strip(),
            'doi': item.get('doi', '').replace('https://doi.org/', '') if item.get('doi') else None,
            'year': item.get('publication_year'),
            'type': item.get('type'),
            'cited_by_count': item.get('cited_by_count', 0),
            'is_oa': item.get('open_access', {}).get('is_oa', False),
            'oa_url': item.get('open_access', {}).get('oa_url'),
            'pdf_url': None,
            'url': item.get('doi') or item.get('id'),
            'authors': []
        }

        # Abstract (inverted index format)
        if 'abstract_inverted_index' in item and item['abstract_inverted_index']:
            paper['has_abstract'] = True
            # Note: Reconstructing abstract from inverted index is complex
            # For now, just mark that it exists
        else:
            paper['has_abstract'] = False

        # Parse authors
        if 'authorships' in item:
            for authorship in item['authorships']:
                author = authorship.get('author', {})
                author_name = author.get('display_name', '')
                if author_name:
                    paper['authors'].append(author_name)

        # Best OA location (for PDF)
        best_oa = item.get('best_oa_location')
        if best_oa:
            paper['oa_url'] = best_oa.get('landing_page_url') or best_oa.get('pdf_url')
            paper['pdf_url'] = best_oa.get('pdf_url')

        # Publication venue
        primary_location = item.get('primary_location')
        if primary_location:
            source = primary_location.get('source')
            if source:
                paper['journal'] = source.get('display_name')
                paper['publisher'] = source.get('host_organization_name')

        # Concepts (topics)
        if 'concepts' in item:
            paper['concepts'] = [
                c.get('display_name') for c in item['concepts'][:5]  # Top 5
            ]

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
        if len(authors) > 7:
            # APA: List first 6, then "...", then last
            author_str = ', '.join(authors[:6]) + ', ... ' + authors[-1]
        elif len(authors) > 3:
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

        # Add citation count if significant
        if paper.get('cited_by_count', 0) > 10:
            citation += f" [Cited by {paper['cited_by_count']}]"

        if paper.get('is_oa'):
            citation += " [Open Access]"

        return citation
