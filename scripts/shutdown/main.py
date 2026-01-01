# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""Shutdown script for Club Maquis recording sessions.

Usage:
    uv run python scripts/shutdown/main.py <YYYYMMDDTHHMMSSZ>

This script:
1. Stops QuickTime recordings (webcam + screen)
2. Waits for recordings to save to Desktop
3. Moves recordings from Desktop to session directory
4. Copies Ableton project files to session directory
5. Closes Ableton Live
6. Uploads session files to Google Photos
7. Logs all actions to log.jsonl

Note: Chrome MCP tab should be closed by Claude before running this script.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.shutdown import ableton, gphotos, quicktime  # noqa: E402
from scripts.shutdown.utils import wait_for_files_stable  # noqa: E402
from src.clubmaquis.session_logger import ActionStatus, ActionType, SessionLogger  # noqa: E402

# Base directory for all Club Maquis sessions
BASE_DATA_DIR = Path("/Users/stharrold/Documents/Data/ClubMaquis")

# Desktop path for QuickTime recordings
DESKTOP_PATH = Path.home() / "Desktop"

# Pattern to match session ID format
SESSION_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z$")

# QuickTime recording patterns on Desktop
QUICKTIME_PATTERNS = {
    "screen": "Screen Recording*.mov",
    "webcam": "Untitled*.mov",
}

# Time to wait for QuickTime files to save (seconds)
QUICKTIME_SAVE_TIMEOUT = 30.0
QUICKTIME_STABILITY_TIME = 2.0


def validate_session_id(session_id: str) -> bool:
    """Validate session ID matches YYYYMMDDTHHMMSSZ format."""
    return bool(SESSION_ID_PATTERN.match(session_id))


def get_session_dir(session_id: str) -> Path:
    """Get the session directory path."""
    return BASE_DATA_DIR / session_id


def find_quicktime_files() -> dict[str, list[Path]]:
    """Find all QuickTime recording files on Desktop.

    Returns:
        Dict with 'webcam' and 'screen' keys, values are lists of Paths.
    """
    files: dict[str, list[Path]] = {"webcam": [], "screen": []}

    for file_type, pattern in QUICKTIME_PATTERNS.items():
        matching_files = list(DESKTOP_PATH.glob(pattern))
        files[file_type] = sorted(matching_files)

    return files


def wait_for_quicktime_files(logger: SessionLogger) -> dict[str, list[Path]]:
    """Wait for QuickTime files to appear and stabilize on Desktop.

    Args:
        logger: Session logger for recording progress.

    Returns:
        Dict with file types and their paths.
    """
    logger.log(
        ActionType.QUICKTIME_SAVE,
        ActionStatus.STARTED,
        "Waiting for QuickTime recordings to save",
        details={
            "timeout_seconds": QUICKTIME_SAVE_TIMEOUT,
            "stability_seconds": QUICKTIME_STABILITY_TIME,
            "patterns": QUICKTIME_PATTERNS,
        },
    )

    # Wait for files to appear and stabilize
    time.sleep(2)  # Initial delay for QuickTime to start saving

    result_files: dict[str, list[Path]] = {"webcam": [], "screen": []}

    for file_type, pattern in QUICKTIME_PATTERNS.items():
        stable_files = wait_for_files_stable(
            DESKTOP_PATH,
            pattern,
            timeout_seconds=QUICKTIME_SAVE_TIMEOUT,
            stability_seconds=QUICKTIME_STABILITY_TIME,
        )
        result_files[file_type] = stable_files

    return result_files


def move_quicktime_files(
    session_dir: Path,
    session_id: str,
    qt_files: dict[str, list[Path]],
    logger: SessionLogger,
) -> list[Path]:
    """Move QuickTime recording files from Desktop to session directory.

    Args:
        session_dir: Destination session directory.
        session_id: Session timestamp for file naming.
        qt_files: Dict of file type to list of paths.
        logger: Session logger for recording actions.

    Returns:
        List of destination paths for moved files.
    """
    moved_files = []

    for file_type, source_paths in qt_files.items():
        if not source_paths:
            logger.log_skipped(
                ActionType.FILE_MOVE,
                f"No {file_type} recording found on Desktop",
                details={
                    "file_type": file_type,
                    "source_location": str(DESKTOP_PATH),
                    "pattern": QUICKTIME_PATTERNS[file_type],
                },
            )
            continue

        # Handle multiple files of the same type
        for idx, source_path in enumerate(source_paths, start=1):
            # Rename to: YYYYMMDDTHHMMSSZ_quicktime_<type>.mov
            # or YYYYMMDDTHHMMSSZ_quicktime_<type>_<n>.mov for multiples
            if len(source_paths) == 1:
                new_name = f"{session_id}_quicktime_{file_type}.mov"
            else:
                new_name = f"{session_id}_quicktime_{file_type}_{idx}.mov"

            dest_path = session_dir / new_name

            # Check if destination already exists
            if dest_path.exists():
                logger.log_failed(
                    ActionType.FILE_MOVE,
                    f"Destination already exists: {new_name}",
                    details={
                        "source": str(source_path),
                        "destination": str(dest_path),
                        "skipped": True,
                    },
                )
                continue

            logger.log_start(
                ActionType.FILE_MOVE,
                f"Moving {file_type} recording",
                details={
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "original_name": source_path.name,
                    "new_name": new_name,
                },
            )

            try:
                shutil.move(str(source_path), str(dest_path))
                moved_files.append(dest_path)
                logger.log_success(
                    ActionType.FILE_MOVE,
                    f"Moved {file_type} recording",
                    details={
                        "source": str(source_path),
                        "destination": str(dest_path),
                        "file_size_bytes": dest_path.stat().st_size,
                    },
                )
            except OSError as e:
                logger.log_failed(
                    ActionType.FILE_MOVE,
                    f"Failed to move {file_type} recording: {e}",
                    details={
                        "source": str(source_path),
                        "destination": str(dest_path),
                        "error": str(e),
                    },
                )

    return moved_files


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

    # Initialize logger
    logger = SessionLogger(session_dir)

    # Log session start with full context
    logger.log_start(
        ActionType.SESSION_END,
        "Starting shutdown sequence",
        details={
            "session_id": session_id,
            "session_dir": str(session_dir),
            "base_data_dir": str(BASE_DATA_DIR),
            "desktop_path": str(DESKTOP_PATH),
            "ableton_user_library": str(ableton.DEFAULT_USER_LIBRARY),
            "quicktime_patterns": QUICKTIME_PATTERNS,
            "quicktime_save_timeout": QUICKTIME_SAVE_TIMEOUT,
            "script_version": "1.1.0",
        },
    )

    errors_occurred = False

    # Step 1: Stop QuickTime recordings
    logger.log_start(
        ActionType.QUICKTIME_STOP,
        "Stopping QuickTime recordings",
        details={"expected_types": list(QUICKTIME_PATTERNS.keys())},
    )

    qt_result = quicktime.stop_all_recordings()

    if qt_result.success:
        logger.log_success(
            ActionType.QUICKTIME_STOP,
            qt_result.message,
            details={"documents_stopped": qt_result.details.get("documents_stopped", 0)},
        )
    else:
        logger.log_failed(
            ActionType.QUICKTIME_STOP,
            qt_result.message,
            details={"error": qt_result.message},
        )
        errors_occurred = True

    # Step 2: Wait for QuickTime files to save to Desktop
    qt_files = wait_for_quicktime_files(logger)

    total_files = sum(len(files) for files in qt_files.values())
    if total_files > 0:
        logger.log_success(
            ActionType.QUICKTIME_SAVE,
            f"Found {total_files} QuickTime recording(s)",
            details={
                "screen_recordings": len(qt_files["screen"]),
                "webcam_recordings": len(qt_files["webcam"]),
                "files": {k: [str(f) for f in v] for k, v in qt_files.items()},
            },
        )
    else:
        logger.log_skipped(
            ActionType.QUICKTIME_SAVE,
            "No QuickTime recordings found on Desktop",
        )

    # Step 3: Move QuickTime files from Desktop to session directory
    moved_files = move_quicktime_files(session_dir, session_id, qt_files, logger)

    if moved_files:
        logger.log_success(
            ActionType.QUICKTIME_SAVE,
            f"Saved {len(moved_files)} QuickTime recording(s) to session",
            details={"files": [str(f) for f in moved_files]},
        )

    # Step 4: Quit QuickTime Player
    qt_quit_result = quicktime.quit_player()
    if not qt_quit_result.success:
        logger.log_failed(
            ActionType.QUICKTIME_STOP,
            f"Failed to quit QuickTime: {qt_quit_result.message}",
        )

    # Step 5: Copy Ableton project files
    logger.log_start(
        ActionType.ABLETON_CLOSE,
        "Copying Ableton project files",
        details={
            "source": str(ableton.DEFAULT_USER_LIBRARY),
            "destination": str(session_dir),
            "extensions": list(ableton.ABLETON_EXTENSIONS.keys()),
            "max_age_hours": 12,
        },
    )

    ableton_result = ableton.copy_project_files(session_dir, session_id)

    if ableton_result.success:
        logger.log_success(
            ActionType.ABLETON_CLOSE,
            ableton_result.message,
            details={"files_copied": [str(f) for f in ableton_result.files_processed]},
        )
    else:
        logger.log_failed(
            ActionType.ABLETON_CLOSE,
            ableton_result.message,
            details={
                "files_copied": [str(f) for f in ableton_result.files_processed],
                "files_failed": [str(f) for f in ableton_result.files_failed],
                "errors": ableton_result.details.get("errors", []),
            },
        )
        errors_occurred = True

    # Step 6: Close Ableton Live
    logger.log_start(
        ActionType.ABLETON_CLOSE,
        "Closing Ableton Live",
        details={"save_on_close": False},
    )

    close_result = ableton.close_app()

    if close_result.success:
        logger.log_success(ActionType.ABLETON_CLOSE, close_result.message)
    else:
        logger.log_failed(
            ActionType.ABLETON_CLOSE,
            close_result.message,
            details={"error": close_result.message},
        )
        errors_occurred = True

    # Step 7: Upload to Google Photos
    logger.log_start(
        ActionType.GPHOTOS_UPLOAD,
        "Uploading session files to Google Photos",
        details={
            "session_dir": str(session_dir),
            "account": "samuel.harrold@gmail.com",
            "upload_extensions": list(gphotos.UPLOAD_EXTENSIONS),
        },
    )

    upload_result = gphotos.upload_session(session_dir)

    if upload_result.success:
        logger.log_success(
            ActionType.GPHOTOS_UPLOAD,
            upload_result.message,
            details={
                "files_uploaded": [str(f) for f in upload_result.files_processed],
                "album": upload_result.details.get("album"),
            },
        )
    else:
        logger.log_failed(
            ActionType.GPHOTOS_UPLOAD,
            upload_result.message,
            details={
                "files_uploaded": [str(f) for f in upload_result.files_processed],
                "files_failed": [str(f) for f in upload_result.files_failed],
                "errors": upload_result.details.get("errors", []),
            },
        )
        errors_occurred = True

    # Log session end
    final_status = ActionStatus.SUCCESS if not errors_occurred else ActionStatus.FAILED
    logger.log(
        ActionType.SESSION_END,
        final_status,
        "Shutdown sequence complete" if not errors_occurred else "Shutdown completed with errors",
        details={
            "session_id": session_id,
            "session_dir": str(session_dir),
            "errors_occurred": errors_occurred,
            "files_in_session": [f.name for f in session_dir.iterdir() if f.is_file()],
        },
    )

    return 0 if not errors_occurred else 1


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
