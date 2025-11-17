"""
Command-line interface for Research Verification Agent System.
"""

import asyncio
import logging
import sys
from pathlib import Path
from uuid import UUID
import click

from research_agent.config import load_config, get_config
from research_agent.database import init_database, close_database, get_database
from research_agent.utils.ai_client import AIClient
from research_agent.document_processing.pdf_extractor import PDFExtractor
from research_agent.document_processing.claim_extractor import ClaimExtractor
from research_agent.normalization.normalizer import ClaimNormalizer
from research_agent.investigation.orchestrator import InvestigationOrchestrator
from research_agent.investigation.work_scheduler import WorkScheduler
from research_agent.reporting.report_generator import ReportGenerator


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', default=None, help='Path to config file')
@click.pass_context
def cli(ctx, config):
    """Research Verification Agent System CLI."""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option('--title', required=True, help='Document title')
@click.pass_context
def ingest(ctx, pdf_path, title):
    """Ingest a PDF research paper."""
    asyncio.run(_ingest(ctx.obj['config_path'], pdf_path, title))


async def _ingest(config_path, pdf_path, title):
    """Async ingest implementation."""
    # Load config and init
    config = load_config(config_path)
    db = await init_database(config.database.connection_string)
    ai_client = AIClient(
        config.default_provider,
        config.ai_providers[config.default_provider].api_key,
        config.ai_providers[config.default_provider].model,
        config.ai_providers[config.default_provider].temperature
    )

    try:
        click.echo(f"📄 Ingesting: {pdf_path}")

        # Extract PDF
        extractor = PDFExtractor()
        result = extractor.extract(Path(pdf_path))

        click.echo(f"[OK] Extracted {result['page_count']} pages, {result['total_chars']} characters")

        # Save document
        doc_id = await db.fetchval(
            """
            INSERT INTO documents (title, source_type, file_path, full_text, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            title,
            'pdf',
            pdf_path,
            result['full_text'],
            result['metadata']
        )

        click.echo(f"[OK] Document saved: {doc_id}")

        # Extract claims
        claim_extractor = ClaimExtractor(ai_client)
        claims = await claim_extractor.extract_claims(result['full_text'])

        click.echo(f"[OK] Extracted {len(claims)} claims")

        # Save claims
        for claim in claims:
            claim_id = await db.fetchval(
                """
                INSERT INTO claims (source_document_id, original_text, status)
                VALUES ($1, $2, 'extracted')
                RETURNING id
                """,
                doc_id,
                claim['text']
            )

            # Schedule investigations
            scheduler = WorkScheduler(db)
            await scheduler.schedule_initial_investigations(claim_id)

        click.echo(f"[OK] Saved {len(claims)} claims and scheduled investigations")

    finally:
        await close_database()


@cli.command()
@click.argument('claim_id', type=click.UUID)
@click.pass_context
def normalize(ctx, claim_id):
    """Normalize a claim."""
    asyncio.run(_normalize(ctx.obj['config_path'], claim_id))


async def _normalize(config_path, claim_id):
    """Async normalize implementation."""
    config = load_config(config_path)
    db = await init_database(config.database.connection_string)
    ai_client = AIClient(
        config.default_provider,
        config.ai_providers[config.default_provider].api_key,
        config.ai_providers[config.default_provider].model
    )

    try:
        # Get claim
        claim = await db.get_claim(claim_id)
        if not claim:
            click.echo(f"Error: Claim {claim_id} not found", err=True)
            return

        click.echo(f"Original: {claim['original_text']}")

        # Normalize
        normalizer = ClaimNormalizer(ai_client)
        result = await normalizer.normalize(claim['original_text'])

        # Display result
        click.echo(f"\nNormalized: {result['normalized_text']}")
        click.echo(f"Qualifiers preserved: {'[OK]' if result['qualifiers_preserved'] else '[X]'}")
        click.echo(f"Confidence: {result['confidence']:.2f}")

        if result['needs_human_review']:
            click.echo("\n[WARNING]  Needs human review")

        # Save to validation table
        await db.execute(
            """
            INSERT INTO normalization_validations (
                claim_id, original_text, proposed_normalized, confidence
            ) VALUES ($1, $2, $3, $4)
            """,
            claim_id,
            claim['original_text'],
            result['normalized_text'],
            result['confidence']
        )

    finally:
        await close_database()


@cli.command()
@click.pass_context
def start_agents(ctx):
    """Start agent pool (runs indefinitely)."""
    asyncio.run(_start_agents(ctx.obj['config_path']))


async def _start_agents(config_path):
    """Start agents."""
    config = load_config(config_path)
    db = await init_database(config.database.connection_string)
    ai_client = AIClient(
        config.default_provider,
        config.ai_providers[config.default_provider].api_key,
        config.ai_providers[config.default_provider].model
    )

    click.echo("[->] Starting Research Verification Agent System")
    click.echo("Press Ctrl+C to stop")

    orchestrator = InvestigationOrchestrator(config, db, ai_client)

    try:
        await orchestrator.start_agent_pool()
    except KeyboardInterrupt:
        click.echo("\n\nShutting down...")
        await orchestrator.stop()
    finally:
        await close_database()


@cli.command()
@click.argument('claim_id', type=click.UUID)
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def report(ctx, claim_id, output):
    """Generate report for a claim."""
    asyncio.run(_report(ctx.obj['config_path'], claim_id, output))


async def _report(config_path, claim_id, output):
    """Generate report."""
    config = load_config(config_path)
    db = await init_database(config.database.connection_string)

    try:
        generator = ReportGenerator(db)
        report_text = await generator.generate_claim_report(claim_id)

        if output:
            Path(output).write_text(report_text)
            click.echo(f"[OK] Report saved to: {output}")
        else:
            click.echo(report_text)

    finally:
        await close_database()


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status."""
    asyncio.run(_status(ctx.obj['config_path']))


async def _status(config_path):
    """Show status."""
    config = load_config(config_path)
    db = await init_database(config.database.connection_string)

    try:
        scheduler = WorkScheduler(db)
        queue_status = await scheduler.get_queue_status()

        click.echo("📊 System Status")
        click.echo("")
        click.echo("Work Queue:")
        click.echo(f"  Queued: {queue_status['total_queued']}")
        click.echo(f"  In Progress: {queue_status['in_progress']}")
        click.echo(f"  Completed: {queue_status['completed']}")
        click.echo(f"  Failed: {queue_status['failed']}")

        if queue_status['by_framework']:
            click.echo("\nBy Framework:")
            for framework, count in queue_status['by_framework'].items():
                click.echo(f"  {framework}: {count}")

    finally:
        await close_database()


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == '__main__':
    main()
