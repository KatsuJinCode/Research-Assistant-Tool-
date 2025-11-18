#!/usr/bin/env python3
"""
CLI Research Assistant Tool
A simplified version that runs in the command line environment.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import hashlib


class SimpleResearchAssistant:
    """CLI-based research assistant."""

    def __init__(self, data_dir: str = "./data"):
        """Initialize the research assistant."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.db_path = self.data_dir / "research.db"
        self.docs_dir = self.data_dir / "documents"
        self.docs_dir.mkdir(exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                file_path TEXT,
                content TEXT,
                content_hash TEXT UNIQUE,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # Notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                content TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_project(self, name: str, description: str = "") -> int:
        """Create a new research project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description)
        )
        project_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return project_id

    def list_projects(self) -> List[Dict]:
        """List all projects."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, p.description, p.created_at,
                   COUNT(d.id) as doc_count
            FROM projects p
            LEFT JOIN documents d ON p.id = d.project_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """)

        projects = []
        for row in cursor.fetchall():
            projects.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "doc_count": row[4]
            })

        conn.close()
        return projects

    def add_document(self, project_id: int, title: str, content: str,
                    metadata: Optional[Dict] = None) -> int:
        """Add a document to a project."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if document already exists
        cursor.execute(
            "SELECT id FROM documents WHERE content_hash = ?",
            (content_hash,)
        )
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing[0]

        # Insert new document
        cursor.execute(
            """INSERT INTO documents
               (project_id, title, content, content_hash, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, title, content, content_hash,
             json.dumps(metadata or {}))
        )
        doc_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return doc_id

    def add_document_from_file(self, project_id: int, file_path: str) -> int:
        """Add a document from a file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        if file_path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_path.suffix.lower() == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # For other formats, we'd need proper parsers
            # For now, try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")

        metadata = {
            "source_file": str(file_path),
            "file_type": file_path.suffix,
            "file_size": file_path.stat().st_size
        }

        return self.add_document(
            project_id,
            file_path.stem,
            content,
            metadata
        )

    def search_documents(self, query: str, project_id: Optional[int] = None) -> List[Dict]:
        """Search documents by content."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if project_id:
            cursor.execute(
                """SELECT id, title, content, created_at
                   FROM documents
                   WHERE project_id = ? AND content LIKE ?
                   ORDER BY created_at DESC""",
                (project_id, f"%{query}%")
            )
        else:
            cursor.execute(
                """SELECT id, title, content, created_at
                   FROM documents
                   WHERE content LIKE ?
                   ORDER BY created_at DESC""",
                (f"%{query}%",)
            )

        results = []
        for row in cursor.fetchall():
            # Find snippet around the query
            content = row[2]
            query_lower = query.lower()
            content_lower = content.lower()

            idx = content_lower.find(query_lower)
            if idx >= 0:
                start = max(0, idx - 100)
                end = min(len(content), idx + len(query) + 100)
                snippet = "..." + content[start:end] + "..."
            else:
                snippet = content[:200] + "..."

            results.append({
                "id": row[0],
                "title": row[1],
                "snippet": snippet,
                "created_at": row[3]
            })

        conn.close()
        return results

    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get a document by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, project_id, title, content, metadata, created_at
               FROM documents WHERE id = ?""",
            (doc_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "project_id": row[1],
            "title": row[2],
            "content": row[3],
            "metadata": json.loads(row[4]) if row[4] else {},
            "created_at": row[5]
        }

    def add_note(self, document_id: int, content: str, tags: List[str] = None) -> int:
        """Add a note to a document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO notes (document_id, content, tags) VALUES (?, ?, ?)",
            (document_id, content, json.dumps(tags or []))
        )
        note_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return note_id

    def get_project_summary(self, project_id: int) -> Dict:
        """Get summary of a project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get project info
        cursor.execute(
            "SELECT name, description, created_at FROM projects WHERE id = ?",
            (project_id,)
        )
        project = cursor.fetchone()

        if not project:
            conn.close()
            return None

        # Get document count
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE project_id = ?",
            (project_id,)
        )
        doc_count = cursor.fetchone()[0]

        # Get recent documents
        cursor.execute(
            """SELECT title, created_at FROM documents
               WHERE project_id = ?
               ORDER BY created_at DESC LIMIT 5""",
            (project_id,)
        )
        recent_docs = cursor.fetchall()

        conn.close()

        return {
            "name": project[0],
            "description": project[1],
            "created_at": project[2],
            "document_count": doc_count,
            "recent_documents": [{"title": d[0], "created_at": d[1]} for d in recent_docs]
        }


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="CLI Research Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create project
    create_parser = subparsers.add_parser("create-project", help="Create a new project")
    create_parser.add_argument("name", help="Project name")
    create_parser.add_argument("--description", help="Project description", default="")

    # List projects
    subparsers.add_parser("list-projects", help="List all projects")

    # Add document
    add_parser = subparsers.add_parser("add-document", help="Add a document")
    add_parser.add_argument("project_id", type=int, help="Project ID")
    add_parser.add_argument("file_path", help="Path to document file")

    # Search
    search_parser = subparsers.add_parser("search", help="Search documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--project", type=int, help="Limit to project ID")

    # View document
    view_parser = subparsers.add_parser("view", help="View a document")
    view_parser.add_argument("doc_id", type=int, help="Document ID")

    # Project summary
    summary_parser = subparsers.add_parser("summary", help="Get project summary")
    summary_parser.add_argument("project_id", type=int, help="Project ID")

    args = parser.parse_args()

    assistant = SimpleResearchAssistant()

    if args.command == "create-project":
        project_id = assistant.create_project(args.name, args.description)
        print(f"Created project '{args.name}' with ID: {project_id}")

    elif args.command == "list-projects":
        projects = assistant.list_projects()
        if not projects:
            print("No projects found.")
        else:
            print("\nProjects:")
            print("-" * 80)
            for p in projects:
                print(f"ID: {p['id']} | {p['name']} | Docs: {p['doc_count']}")
                if p['description']:
                    print(f"  Description: {p['description']}")
                print()

    elif args.command == "add-document":
        doc_id = assistant.add_document_from_file(args.project_id, args.file_path)
        print(f"Added document with ID: {doc_id}")

    elif args.command == "search":
        results = assistant.search_documents(args.query, args.project)
        if not results:
            print("No results found.")
        else:
            print(f"\nFound {len(results)} result(s):")
            print("-" * 80)
            for r in results:
                print(f"ID: {r['id']} | {r['title']}")
                print(f"Snippet: {r['snippet']}\n")

    elif args.command == "view":
        doc = assistant.get_document(args.doc_id)
        if not doc:
            print("Document not found.")
        else:
            print(f"\nTitle: {doc['title']}")
            print(f"Created: {doc['created_at']}")
            print("-" * 80)
            print(doc['content'])

    elif args.command == "summary":
        summary = assistant.get_project_summary(args.project_id)
        if not summary:
            print("Project not found.")
        else:
            print(f"\nProject: {summary['name']}")
            print(f"Description: {summary['description']}")
            print(f"Created: {summary['created_at']}")
            print(f"Documents: {summary['document_count']}")
            if summary['recent_documents']:
                print("\nRecent documents:")
                for doc in summary['recent_documents']:
                    print(f"  - {doc['title']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
