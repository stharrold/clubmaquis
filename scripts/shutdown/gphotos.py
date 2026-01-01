# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Google Photos upload via gphotos-uploader-cli.

Provides functions to upload session files to Google Photos.
Requires gphotos-uploader-cli to be installed and configured.

See: https://github.com/gphotos-uploader-cli/gphotos-uploader-cli
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from scripts.shutdown.utils import OperationResult

# File extensions to upload (video and image files)
UPLOAD_EXTENSIONS = {".mov", ".mp4", ".m4v", ".jpg", ".jpeg", ".png", ".heic"}


def is_cli_available() -> bool:
    """Check if gphotos-uploader-cli is installed and available.

    Returns:
        True if the CLI tool is available, False otherwise.
    """
    return shutil.which("gphotos-uploader-cli") is not None


def find_uploadable_files(session_dir: Path) -> list[Path]:
    """Find files in the session directory that can be uploaded.

    Args:
        session_dir: Path to the session directory.

    Returns:
        List of paths to uploadable files (videos and images).
    """
    session_dir = Path(session_dir)
    if not session_dir.exists():
        return []

    files = []
    for file_path in session_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in UPLOAD_EXTENSIONS:
            files.append(file_path)

    return sorted(files)


def upload_session(
    session_dir: Path,
    album_name: str | None = None,
) -> OperationResult:
    """Upload session files to Google Photos.

    Args:
        session_dir: Path to the session directory containing files to upload.
        album_name: Optional album name. Defaults to session directory name.

    Returns:
        OperationResult with success status and lists of uploaded/failed files.
    """
    if not is_cli_available():
        return OperationResult(
            success=False,
            message="gphotos-uploader-cli is not installed. Install with: brew install gphotos-uploader-cli (macOS only)",
            details={"files_processed": [], "files_failed": []},
        )

    session_dir = Path(session_dir)
    if not session_dir.exists():
        return OperationResult(
            success=False,
            message=f"Session directory does not exist: {session_dir}",
            details={"files_processed": [], "files_failed": []},
        )

    files_to_upload = find_uploadable_files(session_dir)
    if not files_to_upload:
        return OperationResult(
            success=True,
            message="No uploadable files found in session directory",
            details={"files_processed": [], "files_failed": []},
        )

    # Default album name is the session directory name (YYYYMMDDTHHMMSSZ)
    if album_name is None:
        album_name = f"ClubMaquis_{session_dir.name}"

    uploaded: list[Path] = []
    failed: list[Path] = []
    errors: list[str] = []

    for file_path in files_to_upload:
        # Upload each file individually to track success/failure
        try:
            result = subprocess.run(
                [
                    "gphotos-uploader-cli",
                    "push",
                    str(file_path),
                    "--album",
                    album_name,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                uploaded.append(file_path)
            else:
                failed.append(file_path)
                errors.append(f"{file_path.name}: {result.stderr.strip()}")
        except subprocess.SubprocessError as e:
            failed.append(file_path)
            errors.append(f"{file_path.name}: {e}")

    if failed:
        return OperationResult(
            success=False,
            message=f"Uploaded {len(uploaded)} file(s), {len(failed)} failed",
            details={
                "files_processed": uploaded,
                "files_failed": failed,
                "album": album_name,
                "errors": errors,
            },
        )

    return OperationResult(
        success=True,
        message=f"Successfully uploaded {len(uploaded)} file(s) to album '{album_name}'",
        details={
            "files_processed": uploaded,
            "files_failed": [],
            "album": album_name,
        },
    )
