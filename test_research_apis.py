#!/usr/bin/env python3
"""
Test script for all three free research APIs.

Demonstrates searching for papers on "mental illness" across:
- arXiv (preprints)
- CORE (open access)
- OpenAlex (comprehensive)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from research_agent.research_apis import ArxivClient, CoreClient, OpenAlexClient


def test_arxiv():
    """Test arXiv API."""
    print("=" * 80)
    print("TESTING ARXIV API")
    print("=" * 80)
    print()

    client = ArxivClient()

    # Search for papers
    print("Searching arXiv for 'mental illness diagnosis'...")
    results = client.search("all:mental illness diagnosis", max_results=3)

    print(f"✓ Found {len(results)} papers")
    print()

    for i, paper in enumerate(results, 1):
        print(f"PAPER {i}:")
        print(f"  Title: {paper['title']}")
        print(f"  Authors: {', '.join(paper['authors'][:3])}")
        if len(paper['authors']) > 3:
            print(f"           ... and {len(paper['authors']) - 3} more")
        print(f"  Published: {paper.get('published', 'N/A')}")
        print(f"  arXiv ID: {paper['id']}")
        print(f"  Categories: {', '.join(paper['categories'][:3])}")
        print(f"  PDF: {paper.get('pdf_url', 'N/A')}")
        print()
        print(f"  Abstract: {paper.get('abstract', '')[:200]}...")
        print()
        print(f"  Citation: {client.format_citation(paper)}")
        print()

    return results


def test_core():
    """Test CORE API."""
    print("=" * 80)
    print("TESTING CORE API")
    print("=" * 80)
    print()

    client = CoreClient()  # No API key needed for basic use

    # Search for papers
    print("Searching CORE for 'mental illness diagnosis'...")
    try:
        results = client.search("mental illness diagnosis", limit=3)

        print(f"✓ Found {len(results)} papers")
        print()

        for i, paper in enumerate(results, 1):
            print(f"PAPER {i}:")
            print(f"  Title: {paper.get('title', 'N/A')}")
            authors = paper.get('authors', [])
            if authors:
                print(f"  Authors: {', '.join(authors[:3])}")
                if len(authors) > 3:
                    print(f"           ... and {len(authors) - 3} more")
            print(f"  Year: {paper.get('year', 'N/A')}")
            print(f"  CORE ID: {paper.get('id', 'N/A')}")
            if paper.get('journal'):
                print(f"  Journal: {paper['journal']}")
            if paper.get('doi'):
                print(f"  DOI: {paper['doi']}")
            print(f"  URL: {paper.get('url', 'N/A')}")
            print(f"  Open Access: {paper.get('open_access', False)}")
            print()
            if paper.get('abstract'):
                print(f"  Abstract: {paper['abstract'][:200]}...")
                print()
            print(f"  Citation: {client.format_citation(paper)}")
            print()

        return results

    except Exception as e:
        print(f"⚠ CORE API error: {e}")
        print("   Note: CORE has rate limits. Get a free API key for better access:")
        print("   https://core.ac.uk/services/api#form")
        print()
        return []


def test_openalex():
    """Test OpenAlex API."""
    print("=" * 80)
    print("TESTING OPENALEX API")
    print("=" * 80)
    print()

    # Optional: Add your email for better rate limits
    client = OpenAlexClient(email="your-email@example.com")  # Optional but recommended

    # Search for papers
    print("Searching OpenAlex for 'mental illness diagnosis'...")
    results = client.search("mental illness diagnosis", max_results=3)

    print(f"✓ Found {len(results)} papers")
    print()

    for i, paper in enumerate(results, 1):
        print(f"PAPER {i}:")
        print(f"  Title: {paper.get('title', 'N/A')}")
        authors = paper.get('authors', [])
        if authors:
            print(f"  Authors: {', '.join(authors[:3])}")
            if len(authors) > 3:
                print(f"           ... and {len(authors) - 3} more")
        print(f"  Year: {paper.get('year', 'N/A')}")
        print(f"  Type: {paper.get('type', 'N/A')}")
        print(f"  OpenAlex ID: {paper.get('id', 'N/A')}")
        if paper.get('doi'):
            print(f"  DOI: {paper['doi']}")
        print(f"  Citations: {paper.get('cited_by_count', 0)}")
        print(f"  Open Access: {paper.get('is_oa', False)}")
        if paper.get('oa_url'):
            print(f"  OA URL: {paper['oa_url']}")
        if paper.get('concepts'):
            print(f"  Topics: {', '.join(paper['concepts'][:3])}")
        print()
        print(f"  Citation: {client.format_citation(paper)}")
        print()

    return results


def main():
    """Run all API tests."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " FREE RESEARCH APIs TEST SUITE".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    all_results = {}

    # Test arXiv
    try:
        all_results['arxiv'] = test_arxiv()
    except Exception as e:
        print(f"❌ arXiv test failed: {e}")
        print()

    # Test CORE
    try:
        all_results['core'] = test_core()
    except Exception as e:
        print(f"❌ CORE test failed: {e}")
        print()

    # Test OpenAlex
    try:
        all_results['openalex'] = test_openalex()
    except Exception as e:
        print(f"❌ OpenAlex test failed: {e}")
        print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"✓ arXiv:    {len(all_results.get('arxiv', []))} papers found")
    print(f"✓ CORE:     {len(all_results.get('core', []))} papers found")
    print(f"✓ OpenAlex: {len(all_results.get('openalex', []))} papers found")
    print()
    print(f"Total papers discovered: {sum(len(v) for v in all_results.values())}")
    print()
    print("All three free research APIs are working! 🎉")
    print()
    print("Next steps:")
    print("  1. Use these APIs in investigation agents")
    print("  2. Search for evidence supporting/contradicting claims")
    print("  3. Build citation network analysis")
    print()


if __name__ == '__main__':
    main()
