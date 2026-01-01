# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""Shutdown script for Club Maquis recording sessions.

This module provides utilities to gracefully stop all recording sources,
save files to the session directory, and upload to Google Photos.

Usage:
    uv run python scripts/shutdown/main.py <YYYYMMDDTHHMMSSZ>

Modules:
    main: CLI entry point and orchestration
    quicktime: QuickTime Player control via AppleScript
    ableton: Ableton Live file management and control
    gphotos: Google Photos upload via gphotos-uploader-cli
    utils: Shared utilities (AppleScript helpers, result types)
"""

