# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Standalone Launchpad lights runner for background execution.

This script runs the Launchpad light pattern continuously until killed.
It's designed to be spawned as a background process by the setup script
and killed by the shutdown script.

Usage:
    python scripts/setup/run_lights.py [--pattern hunt|random]
"""

from __future__ import annotations

import argparse
import random
import signal
import sys

from scripts.setup.launchpad_lights import PATTERN_DURATION, LaunchpadLights


def main() -> int:
    """Run Launchpad lights continuously until killed."""
    parser = argparse.ArgumentParser(description="Run Launchpad lights continuously")
    parser.add_argument(
        "--pattern",
        choices=["hunt", "random"],
        default="hunt",
        help="Light pattern to run (default: hunt)",
    )
    args = parser.parse_args()

    lights = LaunchpadLights()

    def shutdown_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        lights.disconnect()
        sys.exit(0)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    if not lights.connect():
        print("Failed to connect to Launchpad", file=sys.stderr)
        return 1

    print(f"Connected! {args.pattern.capitalize()} pattern running...")

    # Start the pattern (this blocks in the current thread)
    lights.running = True
    lights.enter_programmer_mode()
    lights.clear_all_leds()

    try:
        if args.pattern == "random":
            while lights.running:
                patterns = [
                    lights.pattern_snake,
                    lights.pattern_sparkle,
                    lights.pattern_rain,
                    lights.pattern_spiral,
                    lights.pattern_wave,
                    lights.pattern_diagonal,
                    lights.pattern_expand,
                    lights.pattern_hunt,
                ]
                pattern = random.choice(patterns)
                pattern(PATTERN_DURATION)
                lights.clear_all_leds()
        else:
            # Hunt pattern runs continuously
            while lights.running:
                lights.pattern_hunt(60.0)
                lights.clear_all_leds()
    except KeyboardInterrupt:
        pass  # User requested shutdown via Ctrl+C; cleanup handled in finally block
    finally:
        lights.clear_all_leds()
        lights.exit_programmer_mode()
        lights.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(main())
