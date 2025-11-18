#!/usr/bin/env python3
"""
Simple PDF text extraction test using PyPDF2.
"""

import sys
from pathlib import Path
import PyPDF2


def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyPDF2."""
    print("=" * 80)
    print("PDF TEXT EXTRACTION TEST")
    print("=" * 80)
    print()

    print(f"📄 Opening: {Path(pdf_path).name}")
    print()

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        num_pages = len(reader.pages)
        print(f"[OK] Total pages: {num_pages}")
        print()

        # Extract metadata
        metadata = reader.metadata
        if metadata:
            print("[DOC] Metadata:")
            if metadata.title:
                print(f"  Title: {metadata.title}")
            if metadata.author:
                print(f"  Author: {metadata.author}")
            if metadata.subject:
                print(f"  Subject: {metadata.subject}")
            print()

        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            full_text += text + "\n\n"

        print(f"[OK] Total characters extracted: {len(full_text):,}")
        print()

        # Show first 1000 characters
        print("📖 Preview (first 1000 characters):")
        print("-" * 80)
        print(full_text[:1000])
        print("...")
        print("-" * 80)
        print()

        # Show last 500 characters
        print("📖 End preview (last 500 characters):")
        print("-" * 80)
        print("...")
        print(full_text[-500:])
        print("-" * 80)
        print()

        print("=" * 80)
        print("[OK] EXTRACTION COMPLETE")
        print("=" * 80)

        return full_text


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python simple_test.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    extract_pdf_text(pdf_path)
