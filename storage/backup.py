"""
MNEMOS 2.0 - Automatic SQLite backups to local dir and optional Google Drive.
No secrets in code; Drive mount path from env or default.
"""
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import BACKUP_DIR, DB_PATH, DRIVE_BACKUP_FOLDER_NAME
from storage.db import ensure_data_dir

logger = logging.getLogger(__name__)


def backup_to_local() -> Optional[Path]:
    """Copy DB to BACKUP_DIR with timestamp. Returns path or None."""
    if not DB_PATH.exists():
        logger.warning("No DB file to backup: %s", DB_PATH)
        return None
    ensure_data_dir()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"mnemos_{ts}.db"
    try:
        shutil.copy2(DB_PATH, dest)
        logger.info("Backup created: %s", dest)
        return dest
    except Exception as e:
        logger.error("Backup failed: %s", e)
        return None


def backup_to_drive(drive_mount_path: Optional[Path] = None) -> Optional[Path]:
    """
    Copy DB to Google Drive folder. On Colab use /content/drive/MyDrive/...
    drive_mount_path: e.g. Path("/content/drive/MyDrive"). Pass from Colab after mount.
    """
    if drive_mount_path is None:
        drive_mount_path = Path("/content/drive/MyDrive")
    if not drive_mount_path.exists():
        logger.warning("Drive not mounted at %s; skip Drive backup", drive_mount_path)
        return None
    if not DB_PATH.exists():
        return None
    folder = drive_mount_path / DRIVE_BACKUP_FOLDER_NAME
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = folder / f"mnemos_{ts}.db"
    try:
        shutil.copy2(DB_PATH, dest)
        logger.info("Drive backup created: %s", dest)
        return dest
    except Exception as e:
        logger.error("Drive backup failed: %s", e)
        return None


def run_backups(drive_mount_path: Optional[Path] = None) -> None:
    """Run local backup and optionally Drive backup."""
    backup_to_local()
    backup_to_drive(drive_mount_path)
