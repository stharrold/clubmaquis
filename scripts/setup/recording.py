# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""
Club Maquis Recording Setup Script.

Creates a timestamped session directory, launches all required applications
for a cat DJ recording session, and logs all actions.

Usage:
    uv run python -m scripts.setup.recording
    uv run python -m scripts.setup.recording --cat-tv-url "https://youtube.com/..."
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.logger import JSONLLogger
from scripts.setup.launchers import check_launchpad, launch_chrome_to_url, launch_quicktime

# Base directory for all Club Maquis session data (Google Drive)
# Can be overridden via CLUB_MAQUIS_DATA_DIR environment variable
_DEFAULT_DATA_DIR = (
    Path.home()
    / "Library"
    / "CloudStorage"
    / "GoogleDrive-samuel.harrold@gmail.com"
    / "My Drive"
    / "My_Drive"
    / "ClubMaquis"
)
BASE_DATA_DIR = Path(os.environ.get("CLUB_MAQUIS_DATA_DIR", str(_DEFAULT_DATA_DIR)))

# Default cat TV video URL
DEFAULT_CAT_TV_URL = "https://www.youtube.com/watch?v=2WHuRziGaFg"

# Delay between app launches to allow each app to initialize
QUICKTIME_STARTUP_DELAY_SEC = 1

# Banner width for consistent formatting
BANNER_WIDTH = 58


def get_session_timestamp() -> str:
    """Get current UTC timestamp in session ID format.

    Returns:
        Timestamp string in YYYYMMDDTHHMMSSZ format.
    """
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def create_session_directory(session_id: str) -> Path:
    """Create a new timestamped session directory.

    Args:
        session_id: Session timestamp in YYYYMMDDTHHMMSSZ format.

    Returns:
        Path to the created session directory.
    """
    session_dir = BASE_DATA_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_log_filename(session_id: str) -> str:
    """Get the log filename for a session.

    Args:
        session_id: Session timestamp in YYYYMMDDTHHMMSSZ format.

    Returns:
        Log filename in YYYYMMDDTHHMMSSZ_log.jsonl format.
    """
    return f"{session_id}_log.jsonl"


def display_reminders(session_dir: Path) -> None:
    """Display manual steps required after setup.

    Args:
        session_dir: Path to session directory for file naming guidance.
    """
    border_width = BANNER_WIDTH + 2  # Account for '+' characters on each side
    date_prefix = datetime.now(UTC).strftime("%Y%m%d")
    print()
    print("=" * border_width)
    print("  MANUAL STEPS REQUIRED")
    print("=" * border_width)
    print()
    print("  QuickTime Player:")
    print("    1. File > New Movie Recording (webcam + audio)")
    print("    2. Click Record")
    print()
    print("  iPhone:")
    print("    3. Start camera recording")
    print()
    print("  Sync:")
    print("    4. CLAP loudly for sync point")
    print()
    print("  Then let Nerys DJ!")
    print()
    print("-" * border_width)
    print("  FILE NAMING (when saving):")
    print(f"    {date_prefix}_webcam.mov")
    print(f"    {date_prefix}_iphone.mov")
    print()
    print(f"  SAVE TO: {session_dir}")
    print("=" * border_width)


def main() -> int:
    """Main entry point for recording setup.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Set up Club Maquis recording session",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python -m scripts.setup.recording
    uv run python -m scripts.setup.recording --cat-tv-url "https://youtube.com/watch?v=..."
        """,
    )
    parser.add_argument(
        "--cat-tv-url",
        type=str,
        default=DEFAULT_CAT_TV_URL,
        help=f"YouTube URL for cat entertainment (default: {DEFAULT_CAT_TV_URL})",
    )
    args = parser.parse_args()

    # Print banner
    print()
    print(f"+{'=' * BANNER_WIDTH}+")
    print(f"|{'CLUB MAQUIS SETUP':^{BANNER_WIDTH}}|")
    print(f"|{'DJ Nerys drops beats.':^{BANNER_WIDTH}}|")
    print(f"|{'Shelter pets get treats.':^{BANNER_WIDTH}}|")
    print(f"+{'=' * BANNER_WIDTH}+")
    print()

    # Create session directory with timestamped ID
    session_id = get_session_timestamp()
    session_dir = create_session_directory(session_id)
    print(f"Session directory: {session_dir}")

    # Initialize logger with timestamped filename
    log_filename = get_log_filename(session_id)
    log_path = session_dir / log_filename
    logger = JSONLLogger(log_path)
    logger.log("session_created", session_id=session_id, session_dir=str(session_dir), log_file=str(log_path))
    print(f"Log file: {log_path}")
    print()

    # Track failures for exit code
    failures = 0

    # Pre-flight check: Launchpad (warning only, not critical)
    print("Checking Launchpad connection...")
    if check_launchpad(logger):
        print("  [OK] Launchpad Mini MK3 connected")
    else:
        print("  [!!] Launchpad not detected - check USB connection")
    print()

    # Launch applications
    print("Launching applications...")

    print("  Starting QuickTime Player...")
    if launch_quicktime(logger):
        print("  [OK] QuickTime launched")
    else:
        print("  [!!] Failed to launch QuickTime")
        failures += 1
    time.sleep(QUICKTIME_STARTUP_DELAY_SEC)

    print("  Opening cat TV in Chrome...")
    if launch_chrome_to_url(args.cat_tv_url, logger):
        print("  [OK] Chrome opened to cat TV")
    else:
        print("  [!!] Failed to open Chrome")
        failures += 1

    # Log setup complete
    logger.log("setup_complete", failures=failures, session_dir=str(session_dir))

    # Display manual steps
    display_reminders(session_dir)

    print(f"Session: {session_dir}")
    print(f"Log: {log_path}")
    if failures > 0:
        print(f"[!!] {failures} application(s) failed to launch")
    print()

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
