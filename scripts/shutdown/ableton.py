# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Ableton Live control and file management.

Provides functions to copy project files and close the application.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.shutdown.utils import OperationResult, is_app_running, run_applescript

# Ableton process and app names
PROCESS_NAME = "Live"
APP_NAME_SUITE = "Ableton Live 12 Suite"
APP_NAME_FALLBACK = "Live"

# Default Ableton User Library location (uses Path.home() for portability)
DEFAULT_USER_LIBRARY = Path.home() / "Music" / "Ableton" / "User Library"

# File extensions to copy (relevant for Magenta and reproducing setup)
ABLETON_EXTENSIONS = {
    ".als": "project",      # Ableton Live Set (project file)
    ".alc": "clip",         # Ableton Live Clip
    ".mid": "midi",         # MIDI files
    ".adg": "devicegroup",  # Device Group
}


def is_running() -> bool:
    """Check if Ableton Live is running."""
    return is_app_running(PROCESS_NAME)


def find_session_files(
    user_library: Path = DEFAULT_USER_LIBRARY,
    max_age_hours: int = 12,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Find Ableton files modified within the specified time window.

    Args:
        user_library: Path to Ableton User Library.
        max_age_hours: Maximum age of files to consider (in hours).

    Returns:
        Tuple of (found_files, failed_files) where failed_files contains
        (path, error_message) tuples.
    """
    if not user_library.exists():
        return [], []

    cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
    files_found = []
    files_failed = []

    for ext in ABLETON_EXTENSIONS:
        for file_path in user_library.rglob(f"*{ext}"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)
                if mtime >= cutoff_time:
                    files_found.append(file_path)
            except OSError as e:
                files_failed.append((file_path, str(e)))
                continue

    return sorted(files_found, key=lambda p: p.stat().st_mtime, reverse=True), files_failed


def copy_project_files(
    session_dir: Path,
    session_id: str,
    user_library: Path = DEFAULT_USER_LIBRARY,
    max_age_hours: int = 12,
) -> OperationResult:
    """Copy recent Ableton files to the session directory.

    Files are renamed to: YYYYMMDDTHHMMSSZ_ableton_<file-type>.<ext>

    Continues copying even if individual files fail, collecting all errors.

    Args:
        session_dir: Destination directory for the session.
        session_id: Session timestamp (YYYYMMDDTHHMMSSZ format).
        user_library: Path to Ableton User Library.
        max_age_hours: Maximum age of files to consider (in hours).

    Returns:
        OperationResult with success status and lists of copied/failed files.
    """
    files, scan_errors = find_session_files(user_library, max_age_hours)

    if not files and not scan_errors:
        return OperationResult(
            success=True,
            message="No recent Ableton files found to copy",
            details={"files_processed": [], "files_failed": []},
        )

    session_dir = Path(session_dir)
    if not session_dir.exists():
        return OperationResult(
            success=False,
            message=f"Session directory does not exist: {session_dir}",
            details={"files_processed": [], "files_failed": []},
        )

    copied_files: list[Path] = []
    failed_files: list[Path] = []
    errors: list[str] = []

    # Track file counts per type for unique naming
    type_counts: dict[str, int] = {}

    for source_file in files:
        ext = source_file.suffix.lower()
        file_type = ABLETON_EXTENSIONS.get(ext, "unknown")

        # Generate unique filename with counter if multiple files of same type
        type_counts[file_type] = type_counts.get(file_type, 0) + 1
        count = type_counts[file_type]

        if count == 1:
            new_name = f"{session_id}_ableton_{file_type}{ext}"
        else:
            new_name = f"{session_id}_ableton_{file_type}_{count}{ext}"

        dest_path = session_dir / new_name

        # Check if destination already exists
        if dest_path.exists():
            errors.append(f"Destination already exists: {dest_path.name}")
            failed_files.append(source_file)
            continue

        try:
            shutil.copy2(source_file, dest_path)
            copied_files.append(dest_path)
        except OSError as e:
            errors.append(f"Failed to copy {source_file.name}: {e}")
            failed_files.append(source_file)
            # Continue with remaining files instead of returning early

    # Add scan errors to the error list
    for path, error in scan_errors:
        errors.append(f"Failed to scan {path.name}: {error}")

    if failed_files or scan_errors:
        return OperationResult(
            success=False,
            message=f"Copied {len(copied_files)} file(s), {len(failed_files)} failed",
            details={
                "files_processed": copied_files,
                "files_failed": failed_files,
                "errors": errors,
            },
        )

    return OperationResult(
        success=True,
        message=f"Copied {len(copied_files)} file(s)",
        details={"files_processed": copied_files, "files_failed": []},
    )


def close_app() -> OperationResult:
    """Close Ableton Live application.

    Note: This does NOT save the project. Ensure files are copied before calling.

    Returns:
        OperationResult with success status.
    """
    if not is_running():
        return OperationResult(
            success=True,
            message="Ableton Live is not running",
        )

    # Try Suite version first, then fallback
    script_suite = f'''
    tell application "{APP_NAME_SUITE}"
        quit saving no
    end tell
    '''

    success, _, stderr = run_applescript(script_suite)

    if success:
        return OperationResult(
            success=True,
            message="Ableton Live closed successfully",
        )

    # Try generic app name as fallback
    script_fallback = f'''
    tell application "{APP_NAME_FALLBACK}"
        quit saving no
    end tell
    '''

    success, _, stderr = run_applescript(script_fallback)

    if success:
        return OperationResult(
            success=True,
            message="Ableton Live closed successfully",
        )

    return OperationResult(
        success=False,
        message=f"Failed to quit Ableton: {stderr}",
        details={"stderr": stderr},
    )
