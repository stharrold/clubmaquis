# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Club Maquis
"""Application launchers for Club Maquis recording sessions."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.common.logger import JSONLLogger


def check_launchpad(logger: JSONLLogger) -> bool:
    """Check if Novation Launchpad is connected via USB.

    Args:
        logger: Logger instance for recording the check result.

    Returns:
        True if Launchpad is detected, False otherwise.
    """
    try:
        result = subprocess.run(
            ["system_profiler", "SPUSBDataType"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        connected = "Launchpad" in result.stdout
        logger.log("launchpad_check", status="connected" if connected else "not_found")
        return connected
    except subprocess.TimeoutExpired:
        logger.log("launchpad_check", status="timeout")
        return False
    except (subprocess.SubprocessError, OSError) as e:
        logger.log("launchpad_check", status="error", error=str(e))
        return False


def _launch_app(app_name: str, logger: JSONLLogger, url: str | None = None) -> bool:
    """Launch a macOS application, optionally with a URL.

    Args:
        app_name: Name of the application to launch.
        logger: Logger instance for recording the launch.
        url: Optional URL to open with the application.

    Returns:
        True if launch command succeeded, False otherwise.
    """
    try:
        cmd = ["open", "-a", app_name]
        if url:
            cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or f"Exit code {result.returncode}"
            log_kwargs = {"app": app_name, "error": error_msg}
            if url:
                log_kwargs["url"] = url
            logger.log("app_launch_failed", **log_kwargs)
            return False

        log_kwargs = {"app": app_name}
        if url:
            log_kwargs["url"] = url
        logger.log("app_launched", **log_kwargs)
        return True

    except subprocess.TimeoutExpired:
        log_kwargs = {"app": app_name, "error": "Launch timed out"}
        if url:
            log_kwargs["url"] = url
        logger.log("app_launch_failed", **log_kwargs)
        return False
    except (subprocess.SubprocessError, OSError) as e:
        log_kwargs = {"app": app_name, "error": str(e)}
        if url:
            log_kwargs["url"] = url
        logger.log("app_launch_failed", **log_kwargs)
        return False


def launch_ableton(logger: JSONLLogger) -> bool:
    """Launch Ableton Live 12 Suite.

    Args:
        logger: Logger instance for recording the launch.

    Returns:
        True if launch command succeeded, False otherwise.
    """
    return _launch_app("Ableton Live 12 Suite", logger)


def launch_quicktime(logger: JSONLLogger) -> bool:
    """Launch QuickTime Player.

    Args:
        logger: Logger instance for recording the launch.

    Returns:
        True if launch command succeeded, False otherwise.
    """
    return _launch_app("QuickTime Player", logger)


def launch_chrome_to_url(url: str, logger: JSONLLogger) -> bool:
    """Launch Google Chrome to a specific URL.

    Args:
        url: The URL to open in Chrome.
        logger: Logger instance for recording the launch.

    Returns:
        True if launch command succeeded, False otherwise.
    """
    return _launch_app("Google Chrome", logger, url=url)
