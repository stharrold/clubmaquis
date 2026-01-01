# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""JSONL session logger for recording actions with timestamps."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ActionStatus(str, Enum):
    """Status of an action."""

    STARTED = "started"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionType(str, Enum):
    """Types of actions that can be logged."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    QUICKTIME_STOP = "quicktime_stop"
    QUICKTIME_SAVE = "quicktime_save"
    ABLETON_CLOSE = "ableton_close"
    CHROME_CLOSE = "chrome_close"
    FILE_MOVE = "file_move"
    GPHOTOS_UPLOAD = "gphotos_upload"
    FILE_DELETE = "file_delete"
    ERROR = "error"


class SessionLogger:
    """Logger that writes actions to a JSONL file with timestamps."""

    def __init__(self, session_dir: Path) -> None:
        """Initialize the logger.

        Args:
            session_dir: Directory for the session (e.g., /Users/.../ClubMaquis/YYYYMMDDTHHMMSSZ/)
        """
        self.session_dir = Path(session_dir)
        self.log_file = self.session_dir / "log.jsonl"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        """Ensure the session directory exists."""
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def log(
        self,
        action: ActionType,
        status: ActionStatus,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log an action to the JSONL file.

        Args:
            action: Type of action being logged.
            status: Status of the action.
            message: Optional human-readable message.
            details: Optional additional details.

        Returns:
            The log entry that was written.
        """
        entry = {
            "timestamp": self._get_timestamp(),
            "action": action.value,
            "status": status.value,
        }

        if message:
            entry["message"] = message

        if details:
            entry["details"] = details

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def log_start(self, action: ActionType, message: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Log the start of an action."""
        return self.log(action, ActionStatus.STARTED, message, details)

    def log_success(self, action: ActionType, message: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Log successful completion of an action."""
        return self.log(action, ActionStatus.SUCCESS, message, details)

    def log_failed(self, action: ActionType, message: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Log a failed action."""
        return self.log(action, ActionStatus.FAILED, message, details)

    def log_skipped(self, action: ActionType, message: str | None = None, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Log a skipped action."""
        return self.log(action, ActionStatus.SKIPPED, message, details)

    def log_error(self, error: Exception, context: str | None = None) -> dict[str, Any]:
        """Log an error with full exception details."""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        if context:
            details["context"] = context

        return self.log(ActionType.ERROR, ActionStatus.FAILED, str(error), details)
