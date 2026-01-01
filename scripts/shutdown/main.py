# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Shutdown script for Club Maquis recording sessions.

Usage:
    uv run python scripts/shutdown/main.py <YYYYMMDDTHHMMSSZ>

This script:
1. Prompts user to save QuickTime recordings to session directory
2. Prompts user to AirDrop iPhone video to session directory
3. Waits for user confirmation
4. Logs all files in session directory with absolute paths

Note: User manually names files as YYYYMMDD_<filename>.<ext>
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.clubmaquis.session_logger import ActionStatus, ActionType, SessionLogger  # noqa: E402

# Base directory for all Club Maquis sessions (Google Drive)
# Use CLUBMAQUIS_DATA_DIR env var if set, otherwise default to GDrive
_DEFAULT_DATA_DIR = (
    Path.home()
    / "Library"
    / "CloudStorage"
    / "GoogleDrive-samuel.harrold@gmail.com"
    / "My Drive"
    / "My_Drive"
    / "ClubMaquis"
)
BASE_DATA_DIR = Path(os.environ.get("CLUBMAQUIS_DATA_DIR", str(_DEFAULT_DATA_DIR)))

# Pattern to match session ID format
SESSION_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")

# Script version for logging
SCRIPT_VERSION = "2.0.0"

# Banner width for consistent formatting
BANNER_WIDTH = 60


def validate_session_id(session_id: str) -> bool:
    """Validate session ID matches YYYYMMDDTHHMMSSZ format."""
    return bool(SESSION_ID_PATTERN.match(session_id))


def get_session_dir(session_id: str) -> Path:
    """Get the session directory path.

    Args:
        session_id: Session timestamp in YYYYMMDDTHHMMSSZ format.

    Returns:
        Path to the session directory within BASE_DATA_DIR.

    Raises:
        ValueError: If the constructed path escapes BASE_DATA_DIR (path injection).
    """
    session_dir = (BASE_DATA_DIR / session_id).resolve()
    base_resolved = BASE_DATA_DIR.resolve()
    # Validate path stays within BASE_DATA_DIR (prevents path injection)
    if not session_dir.is_relative_to(base_resolved):
        raise ValueError(f"Invalid session directory: {session_dir}")
    return session_dir


def get_log_filename(session_id: str) -> str:
    """Get the log filename for a session.

    Args:
        session_id: Session timestamp in YYYYMMDDTHHMMSSZ format.

    Returns:
        Log filename in YYYYMMDDTHHMMSSZ_log.jsonl format.
    """
    return f"{session_id}_log.jsonl"


def find_session_files(session_dir: Path) -> list[Path]:
    """Find all files in the session directory.

    Args:
        session_dir: Path to session directory.

    Returns:
        List of absolute paths to files in the session directory.
    """
    if not session_dir.exists():
        return []
    return sorted([f.resolve() for f in session_dir.iterdir() if f.is_file()])


def stop_launchpad_lights(session_dir: Path) -> tuple[bool, int | None]:
    """Stop the Launchpad lights background process.

    Args:
        session_dir: Path to session directory containing lights.pid.

    Returns:
        Tuple of (success, pid) - pid is None if no PID file found.
    """
    import subprocess

    pid_file = session_dir / "lights.pid"
    stopped_pid = None

    # Try PID file first
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            stopped_pid = pid
        except (ValueError, ProcessLookupError):
            pass  # PID invalid or process already gone
        except PermissionError:
            return False, None
        finally:
            if pid_file.exists():
                pid_file.unlink()

    # Also search for process by command pattern (handles Google Drive sync delay)
    try:
        result = subprocess.run(
            ["pgrep", "-f", "scripts.setup.run_lights"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        pid = int(line)
                        os.kill(pid, signal.SIGTERM)
                        if stopped_pid is None:
                            stopped_pid = pid
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass
    except (subprocess.SubprocessError, OSError):
        pass  # pgrep failed, continue with whatever we have

    return True, stopped_pid


def display_save_prompts(session_dir: Path, session_id: str) -> None:
    """Display prompts for user to save files.

    Args:
        session_dir: Path to session directory.
        session_id: Session timestamp for file naming guidance.
    """
    date_prefix = session_id[:8]  # YYYYMMDD from YYYYMMDDTHHMMSSZ

    print()
    print("=" * BANNER_WIDTH)
    print("  SAVE FILES TO SESSION DIRECTORY")
    print("=" * BANNER_WIDTH)
    print()
    print(f"  Session: {session_dir}")
    print()
    print("-" * BANNER_WIDTH)
    print("  1. QUICKTIME RECORDINGS")
    print("-" * BANNER_WIDTH)
    print("     In QuickTime: File > Save")
    print(f"     Save to: {session_dir}")
    print(f"     Name as: {date_prefix}_webcam.mov")
    print()
    print("-" * BANNER_WIDTH)
    print("  2. IPHONE VIDEO")
    print("-" * BANNER_WIDTH)
    print("     AirDrop video to this Mac")
    print(f"     Move to: {session_dir}")
    print(f"     Name as: {date_prefix}_iphone.mov")
    print()
    print("=" * BANNER_WIDTH)


def run_shutdown(session_id: str) -> int:
    """Execute the shutdown sequence.

    Args:
        session_id: Session timestamp in YYYYMMDDTHHMMSSZ format.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    session_dir = get_session_dir(session_id)

    # Validate session directory exists (should be created by setup script)
    if not session_dir.exists():
        print(f"ERROR: Session directory does not exist: {session_dir}")
        print("The setup script should create this directory before shutdown.")
        return 1

    # Initialize logger with timestamped filename
    log_filename = get_log_filename(session_id)
    logger = SessionLogger(session_dir, log_filename)

    # Log session shutdown start with full context
    logger.log_start(
        ActionType.SESSION_END,
        "Starting shutdown sequence",
        details={
            "session_id": session_id,
            "session_dir": str(session_dir.resolve()),
            "base_data_dir": str(BASE_DATA_DIR.resolve()),
            "log_file": str((session_dir / log_filename).resolve()),
            "script_version": SCRIPT_VERSION,
        },
    )

    # Print banner
    print()
    print(f"+{'=' * BANNER_WIDTH}+")
    print(f"|{'CLUB MAQUIS SHUTDOWN':^{BANNER_WIDTH}}|")
    print(f"+{'=' * BANNER_WIDTH}+")

    # Stop Launchpad lights first
    print()
    print("Stopping Launchpad lights...")
    lights_stopped, lights_pid = stop_launchpad_lights(session_dir)
    if lights_pid:
        print(f"  [OK] Lights stopped (PID: {lights_pid})")
        logger.log(
            ActionType.LAUNCHPAD_LIGHTS,
            ActionStatus.SUCCESS,
            "Stopped Launchpad lights",
            details={"pid": lights_pid},
        )
    elif lights_stopped:
        print("  [--] No lights process found (already stopped or not started)")
    else:
        print("  [!!] Failed to stop lights process")
        logger.log(
            ActionType.LAUNCHPAD_LIGHTS,
            ActionStatus.FAILED,
            "Failed to stop Launchpad lights",
        )

    # Display save prompts
    display_save_prompts(session_dir, session_id)

    # Log that user was prompted
    logger.log(
        ActionType.USER_PROMPT,
        ActionStatus.SUCCESS,
        "Displayed file save instructions to user",
        details={
            "session_dir": str(session_dir.resolve()),
            "expected_files": [
                f"{session_id[:8]}_webcam.mov",
                f"{session_id[:8]}_iphone.mov",
            ],
        },
    )

    # Wait for user confirmation
    print()
    try:
        input("  Press ENTER when files are saved to continue...")
    except KeyboardInterrupt:
        print("\n\nShutdown cancelled by user.")
        logger.log(
            ActionType.USER_CONFIRM,
            ActionStatus.FAILED,
            "User cancelled shutdown",
            details={"reason": "KeyboardInterrupt"},
        )
        return 1

    logger.log(
        ActionType.USER_CONFIRM,
        ActionStatus.SUCCESS,
        "User confirmed files are saved",
    )

    # Scan session directory for files
    print()
    print("-" * BANNER_WIDTH)
    print("  SCANNING SESSION DIRECTORY")
    print("-" * BANNER_WIDTH)

    session_files = find_session_files(session_dir)
    media_extensions = {".mov", ".mp4", ".m4v", ".jpg", ".jpeg", ".png", ".heic"}
    media_files = [f for f in session_files if f.suffix.lower() in media_extensions]
    log_files = [f for f in session_files if f.suffix.lower() == ".jsonl"]

    print()
    print(f"  Found {len(media_files)} media file(s):")
    for f in media_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"    - {f.name} ({size_mb:.1f} MB)")

    print()
    print(f"  Found {len(log_files)} log file(s):")
    for f in log_files:
        print(f"    - {f.name}")

    # Log session end with absolute paths
    logger.log(
        ActionType.SESSION_END,
        ActionStatus.SUCCESS,
        "Shutdown sequence complete",
        details={
            "session_id": session_id,
            "session_dir": str(session_dir.resolve()),
            "media_files": [str(f) for f in media_files],
            "log_files": [str(f) for f in log_files],
            "total_files": len(session_files),
        },
    )

    print()
    print("=" * BANNER_WIDTH)
    print("  SHUTDOWN COMPLETE")
    print("=" * BANNER_WIDTH)
    print()
    print(f"  Session: {session_dir}")
    print(f"  Log: {session_dir / log_filename}")
    print()

    return 0


def main() -> int:
    """Main entry point for the shutdown script."""
    parser = argparse.ArgumentParser(
        description="Shutdown Club Maquis recording session",
        epilog="Example: uv run python scripts/shutdown/main.py 20251231T120000Z",
    )
    parser.add_argument(
        "session_id",
        help="Session timestamp in YYYYMMDDTHHMMSSZ format",
    )

    args = parser.parse_args()

    if not validate_session_id(args.session_id):
        print(f"ERROR: Invalid session ID format: {args.session_id}")
        print("Expected format: YYYYMMDDTHHMMSSZ (e.g., 20251231T120000Z)")
        return 1

    return run_shutdown(args.session_id)


if __name__ == "__main__":
    sys.exit(main())
