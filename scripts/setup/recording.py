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
from scripts.setup.launchers import check_launchpad, launch_ableton, launch_chrome_to_url, launch_quicktime

# Base directory for all Club Maquis session data
# Can be overridden via CLUB_MAQUIS_DATA_DIR environment variable
_DEFAULT_DATA_DIR = Path.home() / "Documents" / "Data" / "ClubMaquis"
BASE_DATA_DIR = Path(os.environ.get("CLUB_MAQUIS_DATA_DIR", str(_DEFAULT_DATA_DIR)))

# Default cat TV video URL
DEFAULT_CAT_TV_URL = "https://www.youtube.com/watch?v=2WHuRziGaFg"

# Delay between app launches to allow each app to initialize
ABLETON_STARTUP_DELAY_SEC = 2
QUICKTIME_STARTUP_DELAY_SEC = 1

# Banner width for consistent formatting
BANNER_WIDTH = 58


def create_session_directory() -> Path:
    """Create a new timestamped session directory.

    Returns:
        Path to the created session directory.
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    session_dir = BASE_DATA_DIR / timestamp
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def display_reminders() -> None:
    """Display manual steps required after setup."""
    border_width = BANNER_WIDTH + 2  # Account for '+' characters on each side
    print()
    print("=" * border_width)
    print("  MANUAL STEPS REQUIRED")
    print("=" * border_width)
    print()
    print("  QuickTime Player:")
    print("    1. File > New Movie Recording (webcam + audio)")
    print("    2. File > New Screen Recording (Ableton window)")
    print("    3. Click Record on both")
    print()
    print("  iPhone:")
    print("    4. Start camera recording")
    print()
    print("  Sync:")
    print("    5. CLAP loudly for sync point")
    print()
    print("  Then let Nerys DJ!")
    print()
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

    # Create session directory
    session_dir = create_session_directory()
    print(f"Session directory: {session_dir}")

    # Initialize logger
    log_path = session_dir / "log.jsonl"
    logger = JSONLLogger(log_path)
    logger.log("session_created", path=str(session_dir))
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

    # Launch applications with delays between each
    print("Launching applications...")

    print("  Starting Ableton Live 12 Suite...")
    if launch_ableton(logger):
        print("  [OK] Ableton launched")
    else:
        print("  [!!] Failed to launch Ableton")
        failures += 1
    time.sleep(ABLETON_STARTUP_DELAY_SEC)

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
    logger.log("setup_complete", failures=failures)

    # Display manual steps
    display_reminders()

    print(f"Session: {session_dir}")
    print(f"Log: {log_path}")
    if failures > 0:
        print(f"[!!] {failures} application(s) failed to launch")
    print()

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
