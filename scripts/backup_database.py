"""
Database Backup Script

Backs up Neo4j database to local storage and optionally to S3.
Can be run manually or via cron/GitHub Actions.

Usage:
    python scripts/backup_database.py
    python scripts/backup_database.py --upload-s3
    python scripts/backup_database.py --restore backups/backup_20251123.dump
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import gzip
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.logging_config import setup_logging

logger = setup_logging("backup_script", log_level="INFO")


class DatabaseBackup:
    """Database backup manager"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")

        if not self.neo4j_password:
            logger.warning("NEO4J_PASSWORD not set, using default password")
            self.neo4j_password = "password"

    def create_backup(self) -> Path:
        """
        Create a backup of the Neo4j database.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"neo4j_backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.dump"

        logger.info(f"Creating backup: {backup_path}")

        try:
            # Use Neo4j admin dump command
            # Note: This requires neo4j-admin to be in PATH
            subprocess.run(
                [
                    "neo4j-admin",
                    "database",
                    "dump",
                    "neo4j",
                    f"--to={backup_path}"
                ],
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"Backup created successfully: {backup_path}")

            # Compress backup
            compressed_path = self.compress_backup(backup_path)

            return compressed_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during backup: {str(e)}")
            raise

    def compress_backup(self, backup_path: Path) -> Path:
        """
        Compress backup file with gzip.

        Args:
            backup_path: Path to backup file

        Returns:
            Path to compressed backup
        """
        compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")

        logger.info(f"Compressing backup: {compressed_path}")

        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove uncompressed backup
        backup_path.unlink()

        size_mb = compressed_path.stat().st_size / (1024 * 1024)
        logger.info(f"Backup compressed successfully: {size_mb:.2f} MB")

        return compressed_path

    def upload_to_s3(self, backup_path: Path):
        """
        Upload backup to S3.

        Args:
            backup_path: Path to backup file
        """
        bucket = os.getenv("S3_BUCKET")
        if not bucket:
            logger.warning("S3_BUCKET not set, skipping S3 upload")
            return

        try:
            import boto3

            s3_client = boto3.client('s3')
            s3_key = f"backups/{backup_path.name}"

            logger.info(f"Uploading to S3: s3://{bucket}/{s3_key}")

            s3_client.upload_file(
                str(backup_path),
                bucket,
                s3_key
            )

            logger.info("Upload to S3 successful")

        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise

    def restore_backup(self, backup_path: Path):
        """
        Restore database from backup.

        Args:
            backup_path: Path to backup file
        """
        logger.info(f"Restoring backup: {backup_path}")

        # Decompress if needed
        if backup_path.suffix == ".gz":
            logger.info("Decompressing backup...")
            decompressed_path = backup_path.with_suffix('')

            with gzip.open(backup_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            backup_path = decompressed_path

        try:
            # Use Neo4j admin load command
            subprocess.run(
                [
                    "neo4j-admin",
                    "database",
                    "load",
                    "neo4j",
                    f"--from={backup_path}",
                    "--force"
                ],
                check=True,
                capture_output=True,
                text=True
            )

            logger.info("Restore completed successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during restore: {str(e)}")
            raise

    def cleanup_old_backups(self, keep_days: int = 30):
        """
        Remove backups older than keep_days.

        Args:
            keep_days: Number of days to keep backups
        """
        logger.info(f"Cleaning up backups older than {keep_days} days")

        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        removed_count = 0

        for backup_file in self.backup_dir.glob("neo4j_backup_*.dump.gz"):
            if backup_file.stat().st_mtime < cutoff_time:
                logger.info(f"Removing old backup: {backup_file}")
                backup_file.unlink()
                removed_count += 1

        logger.info(f"Removed {removed_count} old backups")


def main():
    """Main backup script"""
    parser = argparse.ArgumentParser(description="Database backup utility")
    parser.add_argument(
        "--restore",
        type=str,
        help="Restore from backup file"
    )
    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload backup to S3"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup old backups"
    )
    parser.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Days to keep backups (default: 30)"
    )

    args = parser.parse_args()

    backup_manager = DatabaseBackup()

    try:
        if args.restore:
            # Restore from backup
            backup_path = Path(args.restore)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                sys.exit(1)

            backup_manager.restore_backup(backup_path)

        else:
            # Create backup
            backup_path = backup_manager.create_backup()

            # Upload to S3 if requested
            if args.upload_s3:
                backup_manager.upload_to_s3(backup_path)

            # Cleanup old backups if requested
            if args.cleanup:
                backup_manager.cleanup_old_backups(args.keep_days)

        logger.info("Backup operation completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Backup operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
