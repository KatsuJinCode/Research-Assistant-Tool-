"""
Markdown Export Manager - Git-Friendly Research Snapshots

Exports research data to organized markdown files for version control and portability.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExportManager:
    """Manages markdown exports of research data"""

    def __init__(self, export_root: str = "exports"):
        """
        Initialize export manager

        Args:
            export_root: Root directory for all exports
        """
        self.export_root = Path(export_root)
        self.export_root.mkdir(exist_ok=True)

    def export_project(
        self,
        db,
        project_name: str = "default",
        include_metadata: bool = True
    ) -> Path:
        """
        Export entire project to markdown files

        Args:
            db: Database connection
            project_name: Name of the project
            include_metadata: Include JSON metadata files

        Returns:
            Path to export directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.export_root / project_name / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting export to: {export_dir}")

        # Export documents
        self._export_documents(db, export_dir, include_metadata)

        # Export claims
        self._export_claims(db, export_dir, include_metadata)

        # Export evidence
        self._export_evidence(db, export_dir, include_metadata)

        # Export relationships
        self._export_relationships(db, export_dir)

        # Create index file
        self._create_index(db, export_dir, project_name)

        # Create metadata
        if include_metadata:
            self._create_metadata(db, export_dir, project_name, timestamp)

        logger.info(f"Export completed: {export_dir}")
        return export_dir

    def _export_documents(self, db, export_dir: Path, include_metadata: bool):
        """Export all documents to markdown"""
        docs_dir = export_dir / "documents"
        docs_dir.mkdir(exist_ok=True)

        query = """
        MATCH (d:Document)
        OPTIONAL MATCH (d)-[:HAS_CLAIM]->(c:Claim)
        RETURN d, count(c) as claim_count
        ORDER BY d.created_at DESC
        """

        results = db.execute_query(query)

        for record in results:
            doc = record['d']
            claim_count = record['claim_count']

            doc_id = doc.get('id', 'unknown')
            safe_filename = self._sanitize_filename(doc.get('title', doc_id))

            # Create markdown file
            md_path = docs_dir / f"{safe_filename}.md"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {doc.get('title', 'Untitled Document')}\n\n")
                f.write(f"**ID:** `{doc_id}`  \n")
                f.write(f"**Status:** {doc.get('status', 'unknown')}  \n")
                f.write(f"**Created:** {doc.get('created_at', 'unknown')}  \n")
                f.write(f"**Claims Extracted:** {claim_count}  \n")

                if doc.get('source_url'):
                    f.write(f"**Source:** {doc['source_url']}  \n")

                if doc.get('created_by_agent_id'):
                    f.write(f"**Processed by Agent:** `{doc['created_by_agent_id']}`  \n")

                f.write("\n---\n\n")

                # Add content if available
                if doc.get('content'):
                    f.write("## Content\n\n")
                    f.write(doc['content'])
                    f.write("\n\n")

                # Link to claims
                if claim_count > 0:
                    f.write("## Extracted Claims\n\n")
                    f.write(f"See `claims/` directory for {claim_count} claims extracted from this document.\n\n")

            # Save metadata JSON
            if include_metadata:
                json_path = docs_dir / f"{safe_filename}.meta.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(dict(doc), f, indent=2, default=str)

        logger.info(f"Exported {len(results)} documents")

    def _export_claims(self, db, export_dir: Path, include_metadata: bool):
        """Export all claims to markdown"""
        claims_dir = export_dir / "claims"
        claims_dir.mkdir(exist_ok=True)

        query = """
        MATCH (c:Claim)
        OPTIONAL MATCH (c)<-[:HAS_CLAIM]-(d:Document)
        OPTIONAL MATCH (c)-[r:SUPPORTS|CONTRADICTS]->(other:Claim)
        RETURN c, d.title as doc_title, d.id as doc_id,
               collect({type: type(r), target: other.id, target_text: other.text}) as relationships
        ORDER BY c.created_at DESC
        """

        results = db.execute_query(query)

        for record in results:
            claim = record['c']
            doc_title = record['doc_title']
            doc_id = record['doc_id']
            relationships = record['relationships']

            claim_id = claim.get('id', 'unknown')
            claim_text = claim.get('text', 'No text')
            safe_filename = self._sanitize_filename(claim_text[:50])

            # Create markdown file
            md_path = claims_dir / f"{claim_id}_{safe_filename}.md"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Claim: {claim_id}\n\n")
                f.write(f"> {claim_text}\n\n")
                f.write("---\n\n")

                f.write(f"**ID:** `{claim_id}`  \n")
                f.write(f"**Type:** {claim.get('type', 'unknown')}  \n")
                f.write(f"**Confidence:** {claim.get('confidence', 'unknown')}  \n")
                f.write(f"**Status:** {claim.get('status', 'unknown')}  \n")
                f.write(f"**Created:** {claim.get('created_at', 'unknown')}  \n")

                if doc_title:
                    f.write(f"**Source Document:** [{doc_title}](../documents/{self._sanitize_filename(doc_title)}.md)  \n")

                if claim.get('created_by_agent_id'):
                    f.write(f"**Extracted by Agent:** `{claim['created_by_agent_id']}`  \n")

                f.write("\n")

                # Add relationships
                if relationships and len([r for r in relationships if r.get('type')]) > 0:
                    f.write("## Relationships\n\n")

                    for rel in relationships:
                        if rel.get('type'):
                            rel_type = rel['type']
                            target_id = rel.get('target', 'unknown')
                            target_text = rel.get('target_text', 'Unknown claim')

                            f.write(f"- **{rel_type}** → `{target_id}`: {target_text[:100]}...\n")

                    f.write("\n")

            # Save metadata JSON
            if include_metadata:
                json_path = claims_dir / f"{claim_id}_{safe_filename}.meta.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(dict(claim), f, indent=2, default=str)

        logger.info(f"Exported {len(results)} claims")

    def _export_evidence(self, db, export_dir: Path, include_metadata: bool):
        """Export all evidence nodes to markdown"""
        evidence_dir = export_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)

        query = """
        MATCH (e:Evidence)
        OPTIONAL MATCH (c:Claim)-[:HAS_EVIDENCE]->(e)
        RETURN e, collect({claim_id: c.id, claim_text: c.text}) as supported_claims
        ORDER BY e.created_at DESC
        """

        results = db.execute_query(query)

        for record in results:
            evidence = record['e']
            supported_claims = record['supported_claims']

            ev_id = evidence.get('id', 'unknown')
            ev_text = evidence.get('text', 'No text')
            safe_filename = self._sanitize_filename(ev_text[:50])

            # Create markdown file
            md_path = evidence_dir / f"{ev_id}_{safe_filename}.md"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# Evidence: {ev_id}\n\n")
                f.write(f"> {ev_text}\n\n")
                f.write("---\n\n")

                f.write(f"**ID:** `{ev_id}`  \n")
                f.write(f"**Source:** {evidence.get('source', 'unknown')}  \n")
                f.write(f"**Created:** {evidence.get('created_at', 'unknown')}  \n")

                if evidence.get('created_by_agent_id'):
                    f.write(f"**Found by Agent:** `{evidence['created_by_agent_id']}`  \n")

                f.write("\n")

                # Add supported claims
                if supported_claims and len([c for c in supported_claims if c.get('claim_id')]) > 0:
                    f.write("## Supports Claims\n\n")

                    for claim in supported_claims:
                        if claim.get('claim_id'):
                            claim_id = claim['claim_id']
                            claim_text = claim.get('claim_text', 'Unknown claim')
                            f.write(f"- `{claim_id}`: {claim_text[:100]}...\n")

                    f.write("\n")

            # Save metadata JSON
            if include_metadata:
                json_path = evidence_dir / f"{ev_id}_{safe_filename}.meta.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(dict(evidence), f, indent=2, default=str)

        logger.info(f"Exported {len(results)} evidence nodes")

    def _export_relationships(self, db, export_dir: Path):
        """Export relationship summary"""
        rel_path = export_dir / "relationships.md"

        query = """
        MATCH (c1:Claim)-[r]->(c2:Claim)
        RETURN type(r) as rel_type, count(*) as count
        """

        results = db.execute_query(query)

        with open(rel_path, 'w', encoding='utf-8') as f:
            f.write("# Claim Relationships\n\n")
            f.write("## Summary\n\n")
            f.write("| Relationship Type | Count |\n")
            f.write("|-------------------|-------|\n")

            for record in results:
                rel_type = record['rel_type']
                count = record['count']
                f.write(f"| {rel_type} | {count} |\n")

            f.write("\n")

    def _create_index(self, db, export_dir: Path, project_name: str):
        """Create index markdown file"""
        index_path = export_dir / "README.md"

        # Get stats
        stats_query = """
        MATCH (d:Document) WITH count(d) as doc_count
        MATCH (c:Claim) WITH doc_count, count(c) as claim_count
        MATCH (e:Evidence) WITH doc_count, claim_count, count(e) as ev_count
        RETURN doc_count, claim_count, ev_count
        """

        stats = db.execute_query(stats_query)
        stats_record = stats[0] if stats else {}

        doc_count = stats_record.get('doc_count', 0)
        claim_count = stats_record.get('claim_count', 0)
        ev_count = stats_record.get('ev_count', 0)

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(f"# {project_name} - Research Export\n\n")
            f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Export Directory:** `{export_dir.name}`  \n\n")

            f.write("## Contents\n\n")
            f.write(f"- **Documents:** {doc_count} ([view](documents/))  \n")
            f.write(f"- **Claims:** {claim_count} ([view](claims/))  \n")
            f.write(f"- **Evidence:** {ev_count} ([view](evidence/))  \n")
            f.write(f"- **Relationships:** [view](relationships.md)  \n\n")

            f.write("## Structure\n\n")
            f.write("```\n")
            f.write(f"{export_dir.name}/\n")
            f.write("├── README.md (this file)\n")
            f.write("├── documents/\n")
            f.write("│   ├── *.md (document content)\n")
            f.write("│   └── *.meta.json (metadata)\n")
            f.write("├── claims/\n")
            f.write("│   ├── *.md (claim details)\n")
            f.write("│   └── *.meta.json (metadata)\n")
            f.write("├── evidence/\n")
            f.write("│   ├── *.md (evidence details)\n")
            f.write("│   └── *.meta.json (metadata)\n")
            f.write("├── relationships.md (claim relationships)\n")
            f.write("└── export_metadata.json (export info)\n")
            f.write("```\n\n")

            f.write("## Usage\n\n")
            f.write("This export is git-friendly and can be:\n")
            f.write("- Version controlled with git\n")
            f.write("- Searched with grep/ripgrep\n")
            f.write("- Edited in any text editor\n")
            f.write("- Converted to other formats\n")
            f.write("- Shared as plain text\n\n")

    def _create_metadata(self, db, export_dir: Path, project_name: str, timestamp: str):
        """Create export metadata JSON"""
        meta_path = export_dir / "export_metadata.json"

        metadata = {
            "project_name": project_name,
            "export_timestamp": timestamp,
            "export_datetime": datetime.now().isoformat(),
            "export_version": "1.0",
            "exporter": "Research Assistant Tool"
        }

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use as filename"""
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')

        # Limit length
        text = text[:100]

        # Remove leading/trailing spaces and dots
        text = text.strip('. ')

        return text if text else "untitled"


# Singleton instance
_export_manager = None

def get_export_manager() -> ExportManager:
    """Get singleton export manager instance"""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager
