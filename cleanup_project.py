#!/usr/bin/env python3
"""
Project Cleanup Script - Organizes files into proper directories
Run this to clean up the Research Assistant Tool project directory
"""

import os
import shutil
from pathlib import Path

# Project root
ROOT = Path(__file__).parent

# Files to archive (move to archive/)
TO_ARCHIVE = {
    'old-tests': [
        # Already moved via git mv
    ],
    'test-outputs': [
        'ACTUAL_4STAGE_TEST_OUTPUT.txt',
        'comprehensive_test_output.txt',
        'end_to_end_output.txt',
        'ENHANCED_4STAGE_WITH_QUALITY.txt',
        'hierarchy_output.txt',
        'NEW_4STAGE_PIPELINE_OUTPUT.txt',
        'summarization_test_results.txt',
        'test_4stage_output.txt',
        'temp_test.txt',
    ],
    'old-docs': [
        'ACTUAL_4STAGE_TEST_OUTPUT.txt',
        'ARCHITECTURE_REFACTOR.md',
        'AUTO_INSTALL_COMPLETE.md',
        'CLI_AGENT_WORKFLOW.md',
        'CLAUDE_CLI_RESEARCH.md',
        'COLUMN_DETECTION_AND_HIERARCHY_REBUILD_COMPLETE.md',
        'COLUMN_DETECTION_COMPLETE.md',
        'DATABASE_RESEARCH_FINDINGS.md',
        'END_TO_END_TEST_RESULTS.md',
        'EXTRACTION_PIPELINE_TODO.md',
        'FULL_VISION_COMPLETE.md',
        'HANDOFF_TO_CLI.md',
        'IMPLEMENTATION_SUMMARY.md',
        'INSTALLATION_SUMMARY.md',
        'LIVE_UPDATES_IMPLEMENTATION_PLAN.md',
        'LIVE_UPDATES_PROGRESS.md',
        'NEO4J_USAGE_CLARIFICATION.md',
        'NEO4J_VISUALIZATION_GUIDE.md',
        'NEO4J_WINDOWS_INSTALL.md',
        'PIPELINE_DEMONSTRATION.md',
        'PROGRESS_TRACKING_DESIGN.md',
        'PROGRESS_TRACKING_STATUS.md',
        'PROJECT_INIT.md',
        'SEMANTIC_EMBEDDINGS_RESEARCH.md',
        'SEMANTIC_HIERARCHY_SUCCESS.md',
        'SESSION_SUMMARY.md',
        'SYSTEM_DEMO_SUMMARY.md',
        'TEXT_QUALITY_AND_VISUALIZATION_UPDATE.md',
        'UNICODE_FIX_COMPLETE.md',
        'VERIFICATION_COMPLETE.md',
        'WEBSOCKET_FIX_DIAGNOSIS.md',
        'WEBSOCKET_INCIDENT_REPORT.md',
    ],
    'old-scripts': [
        'ai_helper.py',
        'build_claim_hierarchy.py',
        'build_full_research_graph.py',
        'build_optimal_hierarchy.py',
        'change_neo4j_password.ps1',
        'change_password.py',
        'cleanup_duplicate_documents.py',
        'cli_assistant.py',
        'cli_assistant_enhanced.py',
        'debug_column_extraction.py',
        'demo_normalization.py',
        'demo_qualifiers.py',
        'extract_and_cluster_claims.py',
        'fix_neo4j_auth.ps1',
        'fix_unicode.py',
        'migrate_to_neo4j.py',
        'query_graph.py',
        'real_claims_extracted.py',
        'reprocess_with_column_detection.py',
        'reset_neo4j_password.ps1',
        'run_extraction.bat',
        'run_pipeline_test.bat',
        'run_tests.py',
        'set_neo4j_password.ps1',
        'setup_agent.py',
        'setup_cli.py',
        'setup_interactive.py',
        'show_graph.py',
        'simple_test.py',
        'verify_extraction.py',
        'view_hierarchy.py',
    ],
}

# Files to DELETE (junk/temporary)
TO_DELETE = [
    'nul',  # Windows redirect artifact
    'claim_hierarchy_visualization.html',  # Old visualization
    'research_graph_view.html',  # Old visualization
    'szasz_claims_graph.cypher',  # Old export
]

def main():
    print("🧹 Starting project cleanup...")

    # Create archive directories
    for subdir in TO_ARCHIVE.keys():
        archive_dir = ROOT / 'archive' / subdir
        archive_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created archive/{subdir}/")

    # Move files to archive
    moved_count = 0
    for category, files in TO_ARCHIVE.items():
        for filename in files:
            src = ROOT / filename
            if src.exists():
                dst = ROOT / 'archive' / category / filename
                try:
                    shutil.move(str(src), str(dst))
                    print(f"  Archived: {filename} → archive/{category}/")
                    moved_count += 1
                except Exception as e:
                    print(f"  ⚠ Failed to move {filename}: {e}")

    # Delete junk files
    deleted_count = 0
    for filename in TO_DELETE:
        filepath = ROOT / filename
        if filepath.exists():
            try:
                if filepath.is_file():
                    filepath.unlink()
                else:
                    shutil.rmtree(filepath)
                print(f"  Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠ Failed to delete {filename}: {e}")

    print(f"\n✓ Cleanup complete!")
    print(f"  {moved_count} files archived")
    print(f"  {deleted_count} files deleted")
    print(f"\nClean project structure:")
    print(f"  research_agent/    - Core library")
    print(f"  web_ui/            - Web interface")
    print(f"  tests/             - Unit tests")
    print(f"  docs/              - Current documentation (README, QUICKSTART, etc.)")
    print(f"  archive/           - Old files (safe to delete)")

if __name__ == '__main__':
    main()
