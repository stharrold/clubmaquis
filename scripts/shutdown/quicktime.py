# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""QuickTime Player control via AppleScript.

Provides functions to stop recordings and manage QuickTime Player.
"""

from __future__ import annotations

from scripts.shutdown.utils import OperationResult, is_app_running, quit_app, run_applescript

# QuickTime Player process name
PROCESS_NAME = "QuickTime Player"


def is_running() -> bool:
    """Check if QuickTime Player is running."""
    return is_app_running(PROCESS_NAME)


def stop_all_recordings() -> OperationResult:
    """Stop all active QuickTime recordings.

    This stops recording on all open documents. QuickTime auto-saves
    recordings to Desktop when stopped.

    Returns:
        OperationResult with success status and count of documents stopped.
    """
    if not is_running():
        return OperationResult(
            success=False,
            message="QuickTime Player is not running",
            details={"documents_stopped": 0},
        )

    # AppleScript to stop all recordings
    script = '''
    tell application "QuickTime Player"
        set docCount to count of documents
        if docCount = 0 then
            return "0"
        end if

        set stoppedCount to 0
        repeat with doc in documents
            try
                stop doc
                set stoppedCount to stoppedCount + 1
            end try
        end repeat

        return stoppedCount as string
    end tell
    '''

    success, stdout, stderr = run_applescript(script)

    if not success:
        return OperationResult(
            success=False,
            message=f"AppleScript error: {stderr}",
            details={"documents_stopped": 0, "stderr": stderr},
        )

    try:
        stopped_count = int(stdout)
    except ValueError:
        stopped_count = 0

    if stopped_count == 0:
        return OperationResult(
            success=True,
            message="No active recordings found",
            details={"documents_stopped": 0},
        )

    return OperationResult(
        success=True,
        message=f"Stopped {stopped_count} recording(s)",
        details={"documents_stopped": stopped_count},
    )


def quit_player() -> OperationResult:
    """Quit QuickTime Player application."""
    return quit_app(PROCESS_NAME)
