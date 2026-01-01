# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""JSONL logger with timestamps for session actions."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Log schema version for forward compatibility
LOG_SCHEMA_VERSION = "1.0.0"

# Known actions and their expected fields (for documentation)
LOG_SCHEMA = {
    "version": LOG_SCHEMA_VERSION,
    "description": "Club Maquis session log - JSONL format with UTC timestamps",
    "fields": {
        "timestamp": "ISO 8601 UTC timestamp (e.g., 2025-01-01T12:30:00.123456+00:00)",
        "action": "Action identifier (see known_actions)",
    },
    "known_actions": {
        "log_schema": "First entry in log file, documents the log format",
        "session_created": "Session directory was created. Fields: path",
        "launchpad_check": "Checked for Launchpad USB connection. Fields: status (connected|not_found|timeout|error), error?",
        "app_launched": "Application was launched. Fields: app, url?",
        "app_launch_failed": "Application failed to launch. Fields: app, error, url?",
        "setup_complete": "Recording setup completed successfully",
        "shutdown_started": "Session shutdown initiated",
        "shutdown_complete": "Session shutdown completed",
        "process_started": "Pipeline processing started",
        "process_complete": "Pipeline processing completed",
    },
}


class JSONLLogger:
    """Logs actions to a JSONL file with UTC timestamps.

    Each log entry is a JSON object on its own line with format:
    {"timestamp": "2025-01-01T12:30:00.123456+00:00", "action": "...", ...}

    The first entry in each log file is a schema entry documenting the format.
    """

    def __init__(self, log_path: Path, write_schema: bool = True) -> None:
        """Initialize logger with path to log file.

        Args:
            log_path: Path to the JSONL log file (will be created if needed).
            write_schema: If True and log file is new, write schema as first entry.
        """
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Write schema entry if this is a new log file
        if write_schema and not self.log_path.exists():
            self._write_schema()

    def _write_entry(self, entry: dict[str, Any], mode: str = "a") -> None:
        """Write an entry to the log file with error handling.

        Args:
            entry: The log entry dict to write.
            mode: File open mode ('w' for write, 'a' for append).

        Raises:
            OSError: If writing fails (disk full, permission denied, etc.).
        """
        try:
            with self.log_path.open(mode, encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as e:
            # Print to stderr as fallback since we can't log
            print(f"ERROR: Failed to write log entry to {self.log_path}: {e}", file=sys.stderr)
            raise

    def _write_schema(self) -> None:
        """Write the log schema as the first entry."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "log_schema",
            "schema": LOG_SCHEMA,
        }
        self._write_entry(entry, mode="w")

    def log(self, action: str, **kwargs: Any) -> dict[str, Any]:
        """Log an action with timestamp.

        Args:
            action: Name of the action being logged.
            **kwargs: Additional key-value pairs to include in the log entry.

        Returns:
            The complete log entry dict that was written.

        Raises:
            OSError: If writing fails (disk full, permission denied, etc.).
        """
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            **kwargs,
        }
        self._write_entry(entry)
        return entry
