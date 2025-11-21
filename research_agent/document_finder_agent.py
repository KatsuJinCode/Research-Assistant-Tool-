"""
Document Finder Agent - Automated Research Document Discovery
=============================================================

This agent searches multiple academic sources and downloads relevant papers
for processing in the research assistant tool.

Supported Sources:
- arXiv: Pre-print scientific papers
- PubMed: Biomedical and life sciences literature
- Scholar Gateway: Google Scholar proxy for broader coverage

Features:
- Multi-source search with unified interface
- Automatic PDF download
- Relevance scoring
- Document metadata extraction
- Background processing with progress updates
- Full transcript logging for monitoring

Usage:
    finder = DocumentFinderAgent(query="vaccine efficacy")
    finder.set_sources(['arxiv', 'pubmed'])
    finder.set_max_results(10)
    results = finder.search_and_download()
"""

import logging
import arxiv
import requests
from typing import List, Dict, Optional, Callable
from datetime import datetime
import os
from pathlib import Path
import time
import traceback

logger = logging.getLogger(__name__)


class DocumentFinderAgent:
    """
    Agent for finding and downloading research documents from multiple sources.
    """

    def __init__(self, query: str, output_dir: str = "./downloaded_papers"):
        """
        Initialize document finder agent.

        Args:
            query: Search query string
            output_dir: Directory to save downloaded documents
        """
        self.query = query
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.enabled_sources = ['arxiv', 'pubmed']  # Default sources
        self.max_results_per_source = 10
        self.min_relevance_score = 0.5

        # Results
        self.search_results = []
        self.downloaded_papers = []
        self.failed_downloads = []

        # Progress callback for real-time updates
        self.progress_callback: Optional[Callable] = None

        # Transcript for logging all activity
        self.transcript = []

        logger.info(f"[DocumentFinder] Initialized with query: {query}")
        self._log_to_transcript("🚀 Document Finder Agent Initialized", {
            'query': query,
            'output_dir': str(self.output_dir)
        })

    def set_sources(self, sources: List[str]):
        """Set which sources to search."""
        valid_sources = ['arxiv', 'pubmed', 'scholar']
        self.enabled_sources = [s for s in sources if s.lower() in valid_sources]
        self._log_to_transcript(f"✓ Enabled sources: {', '.join(self.enabled_sources)}")

    def set_max_results(self, max_results: int):
        """Set maximum results per source."""
        self.max_results_per_source = max_results
        self._log_to_transcript(f"✓ Max results per source: {max_results}")

    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates."""
        self.progress_callback = callback

    def _emit_progress(self, message: str, data: Optional[Dict] = None):
        """Emit progress update via callback."""
        self._log_to_transcript(message, data)
        if self.progress_callback:
            self.progress_callback(message, data)

    def _log_to_transcript(self, message: str, data: Optional[Dict] = None):
        """Log message to transcript for monitoring."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'data': data or {}
        }
        self.transcript.append(entry)
        logger.info(f"[DocumentFinder] {message}")

    def search_and_download(self) -> Dict:
        """
        Main execution method: Search all enabled sources and download papers.

        Returns:
            Dict containing results summary and file paths
        """
        self._emit_progress(f"🔍 Starting search for: \"{self.query}\"")

        try:
            # Search each enabled source
            for source in self.enabled_sources:
                self._emit_progress(f"📚 Searching {source.upper()}...")

                if source == 'arxiv':
                    results = self._search_arxiv()
                elif source == 'pubmed':
                    results = self._search_pubmed()
                elif source == 'scholar':
                    results = self._search_scholar()
                else:
                    continue

                self.search_results.extend(results)
                self._emit_progress(f"✓ Found {len(results)} papers from {source.upper()}")

            # Remove duplicates based on title similarity
            self.search_results = self._deduplicate_results(self.search_results)
            self._emit_progress(f"✓ Total unique papers found: {len(self.search_results)}")

            # Download papers
            self._emit_progress(f"⬇️ Downloading papers...")
            for idx, paper in enumerate(self.search_results):
                self._emit_progress(
                    f"Downloading {idx + 1}/{len(self.search_results)}: {paper['title'][:50]}...",
                    {'progress': (idx + 1) / len(self.search_results)}
                )

                success = self._download_paper(paper)
                if success:
                    self.downloaded_papers.append(paper)
                else:
                    self.failed_downloads.append(paper)

            # Summary
            summary = {
                'query': self.query,
                'total_found': len(self.search_results),
                'downloaded': len(self.downloaded_papers),
                'failed': len(self.failed_downloads),
                'papers': self.downloaded_papers,
                'transcript': self.transcript
            }

            self._emit_progress(
                f"✅ Download complete: {len(self.downloaded_papers)}/{len(self.search_results)} successful",
                summary
            )

            return summary

        except Exception as e:
            error_msg = f"❌ Error during search/download: {str(e)}"
            self._emit_progress(error_msg)
            logger.error(f"[DocumentFinder] {error_msg}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'transcript': self.transcript
            }

    def _search_arxiv(self) -> List[Dict]:
        """
        Search arXiv for papers.

        Returns:
            List of paper metadata dicts
        """
        try:
            search = arxiv.Search(
                query=self.query,
                max_results=self.max_results_per_source,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []
            for paper in search.results():
                results.append({
                    'source': 'arxiv',
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'abstract': paper.summary,
                    'published': paper.published.isoformat() if paper.published else None,
                    'pdf_url': paper.pdf_url,
                    'arxiv_id': paper.entry_id.split('/')[-1],
                    'categories': paper.categories
                })

            return results

        except Exception as e:
            logger.error(f"[DocumentFinder] Error searching arXiv: {e}")
            self._log_to_transcript(f"⚠️ arXiv search failed: {str(e)}")
            return []

    def _search_pubmed(self) -> List[Dict]:
        """
        Search PubMed for papers.

        Returns:
            List of paper metadata dicts
        """
        try:
            # PubMed E-utilities API
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

            # Step 1: Search for IDs
            search_url = f"{base_url}esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': self.query,
                'retmax': self.max_results_per_source,
                'retmode': 'json',
                'sort': 'relevance'
            }

            response = requests.get(search_url, params=search_params, timeout=30)
            response.raise_for_status()
            search_data = response.json()

            if 'esearchresult' not in search_data or 'idlist' not in search_data['esearchresult']:
                return []

            pmids = search_data['esearchresult']['idlist']

            if not pmids:
                return []

            # Step 2: Fetch details for each PMID
            fetch_url = f"{base_url}esummary.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'json'
            }

            response = requests.get(fetch_url, params=fetch_params, timeout=30)
            response.raise_for_status()
            fetch_data = response.json()

            results = []
            if 'result' in fetch_data:
                for pmid in pmids:
                    if pmid in fetch_data['result']:
                        paper_data = fetch_data['result'][pmid]
                        results.append({
                            'source': 'pubmed',
                            'title': paper_data.get('title', ''),
                            'authors': [author.get('name', '') for author in paper_data.get('authors', [])],
                            'abstract': '',  # Need separate API call for abstract
                            'published': paper_data.get('pubdate', ''),
                            'pmid': pmid,
                            'doi': paper_data.get('elocationid', '').replace('doi: ', ''),
                            'pdf_url': None  # PubMed doesn't provide direct PDF links
                        })

            return results

        except Exception as e:
            logger.error(f"[DocumentFinder] Error searching PubMed: {e}")
            self._log_to_transcript(f"⚠️ PubMed search failed: {str(e)}")
            return []

    def _search_scholar(self) -> List[Dict]:
        """
        Search Google Scholar via Scholar Gateway.

        Note: This is a placeholder. Actual implementation would require
        a Scholar Gateway API key or scraping solution.

        Returns:
            List of paper metadata dicts
        """
        self._log_to_transcript("⚠️ Scholar search not yet implemented")
        return []

    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate papers based on title similarity.

        Args:
            results: List of paper dicts

        Returns:
            Deduplicated list
        """
        if not results:
            return []

        unique_papers = []
        seen_titles = set()

        for paper in results:
            # Normalize title for comparison
            title = paper['title'].lower().strip()

            # Simple deduplication: exact title match
            if title not in seen_titles:
                unique_papers.append(paper)
                seen_titles.add(title)

        return unique_papers

    def _download_paper(self, paper: Dict) -> bool:
        """
        Download a single paper's PDF.

        Args:
            paper: Paper metadata dict

        Returns:
            True if successful, False otherwise
        """
        try:
            pdf_url = paper.get('pdf_url')
            if not pdf_url:
                # Try to construct PDF URL from DOI for PubMed papers
                if paper['source'] == 'pubmed' and paper.get('doi'):
                    # Note: This is a placeholder. Real implementation would need
                    # to resolve DOI to actual PDF URL, which often requires
                    # institutional access or Unpaywall API
                    self._log_to_transcript(f"⚠️ No PDF URL for PubMed paper: {paper['title'][:50]}")
                    return False
                else:
                    self._log_to_transcript(f"⚠️ No PDF URL available: {paper['title'][:50]}")
                    return False

            # Generate filename
            source = paper['source']
            paper_id = paper.get('arxiv_id') or paper.get('pmid') or 'unknown'
            filename = f"{source}_{paper_id}.pdf"
            filepath = self.output_dir / filename

            # Download PDF
            response = requests.get(pdf_url, timeout=60, stream=True)
            response.raise_for_status()

            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Add filepath to paper metadata
            paper['local_path'] = str(filepath)
            paper['downloaded_at'] = datetime.now().isoformat()

            self._log_to_transcript(f"✓ Downloaded: {filename}")
            return True

        except Exception as e:
            logger.error(f"[DocumentFinder] Error downloading paper: {e}")
            self._log_to_transcript(f"❌ Download failed for: {paper['title'][:50]} - {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create agent
    agent = DocumentFinderAgent(
        query="machine learning interpretability",
        output_dir="./test_downloads"
    )

    # Configure
    agent.set_sources(['arxiv'])
    agent.set_max_results(5)

    # Run search and download
    results = agent.search_and_download()

    print("\n=== RESULTS ===")
    print(f"Found: {results.get('total_found', 0)} papers")
    print(f"Downloaded: {results.get('downloaded', 0)} papers")
    print(f"Failed: {results.get('failed', 0)} papers")

    print("\n=== TRANSCRIPT ===")
    for entry in results.get('transcript', []):
        print(f"[{entry['timestamp']}] {entry['message']}")
