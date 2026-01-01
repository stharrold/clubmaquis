# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Shared utilities for shutdown scripts.

Provides common AppleScript operations and result types.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OperationResult:
    """Generic result for shutdown operations."""

    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def files_processed(self) -> list[Path]:
        """Get list of processed files from details."""
        return self.details.get("files_processed", [])

    @property
    def files_failed(self) -> list[Path]:
        """Get list of failed files from details."""
        return self.details.get("files_failed", [])


def is_app_running(process_name: str) -> bool:
    """Check if a macOS application is running.

    Args:
        process_name: Name of the process to check (e.g., "QuickTime Player", "Live").

    Returns:
        True if the application is running, False otherwise.
    """
    script = f'''
    tell application "System Events"
        return (name of processes) contains "{process_name}"
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip().lower() == "true"
    except subprocess.SubprocessError:
        return False


def quit_app(
    app_name: str,
    process_name: str | None = None,
    wait_for_termination: bool = True,
    termination_timeout: float = 10.0,
) -> OperationResult:
    """Quit a macOS application via AppleScript.

    By default, this function waits for the application to fully terminate
    after sending the quit command. Set wait_for_termination=False to return
    immediately after sending the quit command.

    Args:
        app_name: Application name for AppleScript (e.g., "QuickTime Player").
        process_name: Process name for is_running check (defaults to app_name).
        wait_for_termination: If True, wait for app to terminate (default: True).
        termination_timeout: Max seconds to wait for termination (default: 10s).

    Returns:
        OperationResult indicating success/failure. If wait_for_termination=True,
        success means the app has fully terminated. Otherwise, success means
        the quit command was sent successfully.
    """
    process_name = process_name or app_name

    if not is_app_running(process_name):
        return OperationResult(
            success=True,
            message=f"{app_name} is not running",
        )

    script = f'''
    tell application "{app_name}"
        quit
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return OperationResult(
                success=False,
                message=f"Failed to quit {app_name}: {result.stderr.strip()}",
                details={"stderr": result.stderr.strip()},
            )

        # Optionally wait for app to fully terminate
        if wait_for_termination:
            poll_interval = 0.5
            elapsed = 0.0
            while elapsed < termination_timeout:
                if not is_app_running(process_name):
                    return OperationResult(
                        success=True,
                        message=f"{app_name} quit and terminated successfully",
                        details={"termination_time_seconds": elapsed},
                    )
                time.sleep(poll_interval)
                elapsed += poll_interval

            # Timeout - app still running
            return OperationResult(
                success=False,
                message=f"{app_name} quit command sent but app did not terminate within {termination_timeout}s",
                details={"timeout_seconds": termination_timeout},
            )

        return OperationResult(
            success=True,
            message=f"{app_name} quit command sent",
        )
    except subprocess.SubprocessError as e:
        return OperationResult(
            success=False,
            message=f"Subprocess error quitting {app_name}: {e}",
            details={"error": str(e)},
        )


def run_applescript(script: str) -> tuple[bool, str, str]:
    """Run an AppleScript and return results.

    Args:
        script: AppleScript code to execute.

    Returns:
        Tuple of (success, stdout, stderr).
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.returncode == 0, result.stdout.strip(), result.stderr.strip())
    except subprocess.SubprocessError as e:
        return (False, "", str(e))


def wait_for_file(
    file_path: Path,
    timeout_seconds: float = 10.0,
    poll_interval: float = 0.5,
) -> bool:
    """Wait for a file to appear on disk.

    Args:
        file_path: Path to the file to wait for.
        timeout_seconds: Maximum time to wait.
        poll_interval: Time between checks.

    Returns:
        True if file appeared, False if timeout.
    """
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if file_path.exists():
            return True
        time.sleep(poll_interval)
    return False


def wait_for_files_stable(
    directory: Path,
    pattern: str,
    timeout_seconds: float = 10.0,
    stability_seconds: float = 1.0,
) -> list[Path]:
    """Wait for files matching pattern to appear and stabilize (stop growing).

    Args:
        directory: Directory to search in.
        pattern: Glob pattern for files.
        timeout_seconds: Maximum time to wait.
        stability_seconds: Time file size must be stable.

    Returns:
        List of stable files found.
    """
    start_time = time.time()
    last_sizes: dict[Path, int] = {}
    stable_since: dict[Path, float] = {}

    while time.time() - start_time < timeout_seconds:
        current_files = list(directory.glob(pattern))

        for file_path in current_files:
            try:
                current_size = file_path.stat().st_size
            except OSError:
                continue

            if file_path not in last_sizes or last_sizes[file_path] != current_size:
                last_sizes[file_path] = current_size
                stable_since[file_path] = time.time()

        # Check if all found files are stable
        stable_files = [
            f for f in current_files
            if f in stable_since and time.time() - stable_since[f] >= stability_seconds
        ]

        if stable_files:
            return stable_files

        time.sleep(0.5)

    return []
