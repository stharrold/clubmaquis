# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Launchpad Mini MK3 light patterns for attracting cats.

This module controls the Launchpad's LED grid to display moving patterns
that are enticing to cats. Cats are attracted to movement, so we use
chase patterns with bright, warm colors (reds, oranges, yellows).

Based on Novation Launchpad Mini MK3 Programmer's Reference Manual.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

try:
    import mido
except ImportError:
    mido = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from scripts.common.logger import JSONLLogger

# Launchpad Mini MK3 MIDI port name pattern
LAUNCHPAD_PORT_PATTERN = "Launchpad Mini MK3"

# SysEx header for Launchpad Mini MK3 (manufacturer ID + device ID)
SYSEX_HEADER = [0x00, 0x20, 0x29, 0x02, 0x0D]

# Programmer mode layout value
PROGRAMMER_MODE = 0x7F

# Pad note numbers for the 8x8 grid (bottom-left is 11, top-right is 88)
# Row 1 (bottom): 11-18, Row 2: 21-28, ... Row 8 (top): 81-88
PAD_GRID = [
    [81, 82, 83, 84, 85, 86, 87, 88],  # Top row
    [71, 72, 73, 74, 75, 76, 77, 78],
    [61, 62, 63, 64, 65, 66, 67, 68],
    [51, 52, 53, 54, 55, 56, 57, 58],
    [41, 42, 43, 44, 45, 46, 47, 48],
    [31, 32, 33, 34, 35, 36, 37, 38],
    [21, 22, 23, 24, 25, 26, 27, 28],
    [11, 12, 13, 14, 15, 16, 17, 18],  # Bottom row
]

# Warm color palette indices from the Launchpad color palette
# These are high-contrast, attention-grabbing colors
WARM_COLORS = [
    5,   # Red
    6,   # Red-orange
    9,   # Orange
    10,  # Orange-yellow
    13,  # Yellow
    12,  # Amber
    72,  # Bright orange
    84,  # Bright red
]

# Animation speed (seconds between frames)
CHASE_SPEED = 0.08


class LaunchpadLights:
    """Controls Launchpad Mini MK3 LED patterns for cat attraction.

    Uses MIDI to communicate with the Launchpad, switching to Programmer
    mode for full LED control. Runs chase patterns with warm colors to
    attract cat attention through movement.
    """

    def __init__(self, logger: JSONLLogger | None = None) -> None:
        """Initialize the Launchpad lights controller.

        Args:
            logger: Optional logger for recording actions.
        """
        self.logger = logger
        self._outport: mido.ports.BaseOutput | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def _log(self, action: str, **kwargs) -> None:
        """Log an action if logger is available."""
        if self.logger:
            self.logger.log(action, **kwargs)

    def connect(self) -> bool:
        """Connect to the Launchpad Mini MK3.

        Returns:
            True if connection successful, False otherwise.
        """
        if mido is None:
            self._log("launchpad_lights", status="error", error="mido library not installed")
            return False

        try:
            # Find Launchpad MIDI output port (use MIDI port, not DAW port)
            output_names = mido.get_output_names()
            launchpad_port = None
            for name in output_names:
                if LAUNCHPAD_PORT_PATTERN in name and "MIDI" in name:
                    launchpad_port = name
                    break

            if not launchpad_port:
                self._log("launchpad_lights", status="not_found", available_ports=output_names)
                return False

            self._outport = mido.open_output(launchpad_port)
            self._log("launchpad_lights", status="connected", port=launchpad_port)
            return True

        except (OSError, ValueError, RuntimeError) as e:
            self._log("launchpad_lights", status="error", error=str(e))
            return False

    def disconnect(self) -> None:
        """Disconnect from the Launchpad and reset to default state."""
        self.stop()
        if self._outport:
            try:
                self._exit_programmer_mode()
                self._clear_all_leds()
                self._outport.close()
            except (OSError, ValueError):
                pass
            self._outport = None

    def _send_sysex(self, data: list[int]) -> None:
        """Send a SysEx message to the Launchpad.

        Args:
            data: SysEx data bytes (without F0 header or F7 terminator).
        """
        if self._outport:
            msg = mido.Message("sysex", data=SYSEX_HEADER + data)
            self._outport.send(msg)

    def _send_note_on(self, note: int, velocity: int, channel: int = 0) -> None:
        """Send a Note On message to control an LED.

        Args:
            note: Pad note number (11-88 for grid, 91-98 for top row).
            velocity: Color index from palette (0-127).
            channel: MIDI channel (0=static, 1=flash, 2=pulse).
        """
        if self._outport:
            msg = mido.Message("note_on", note=note, velocity=velocity, channel=channel)
            self._outport.send(msg)

    def _enter_programmer_mode(self) -> None:
        """Switch Launchpad to Programmer mode for full LED control."""
        # SysEx: Set layout to Programmer mode (0x7F)
        self._send_sysex([0x00, PROGRAMMER_MODE])

    def _exit_programmer_mode(self) -> None:
        """Switch Launchpad back to default mode."""
        # SysEx: Set layout to Session mode (0x00)
        self._send_sysex([0x00, 0x00])

    def _clear_all_leds(self) -> None:
        """Turn off all LEDs on the grid."""
        for row in PAD_GRID:
            for note in row:
                self._send_note_on(note, 0)
        # Also clear top row buttons (91-98)
        for note in range(91, 99):
            self._send_note_on(note, 0)

    def _set_led(self, note: int, color: int, pulse: bool = False) -> None:
        """Set an LED to a specific color.

        Args:
            note: Pad note number.
            color: Color index from palette (0-127, 0 = off).
            pulse: If True, LED will pulse; otherwise static.
        """
        channel = 2 if pulse else 0  # Channel 2 = pulsing, Channel 0 = static
        self._send_note_on(note, color, channel)

    def _run_chase_pattern(self) -> None:
        """Run a chase pattern across the grid.

        Creates a snake-like pattern that moves across all pads,
        using warm colors that shift as the chase progresses.
        """
        self._enter_programmer_mode()
        self._clear_all_leds()

        # Create a list of all pads in snake order (alternating direction per row)
        snake_order = []
        for i, row in enumerate(PAD_GRID):
            if i % 2 == 0:
                snake_order.extend(row)
            else:
                snake_order.extend(reversed(row))

        trail_length = 8  # Number of pads lit at once (creates trail effect)
        color_index = 0

        while self._running:
            for head_pos in range(len(snake_order) + trail_length):
                if not self._running:
                    break

                # Clear previous frame
                self._clear_all_leds()

                # Draw trail behind the head
                for trail_offset in range(trail_length):
                    pos = head_pos - trail_offset
                    if 0 <= pos < len(snake_order):
                        # Fade colors as trail gets further from head
                        color_idx = (color_index + trail_offset) % len(WARM_COLORS)
                        # Use pulsing for head, static for trail
                        pulse = trail_offset == 0
                        self._set_led(snake_order[pos], WARM_COLORS[color_idx], pulse)

                time.sleep(CHASE_SPEED)

            # Cycle through colors for next loop
            color_index = (color_index + 1) % len(WARM_COLORS)

        self._clear_all_leds()
        self._exit_programmer_mode()

    def start(self) -> bool:
        """Start the light pattern animation.

        Returns:
            True if started successfully, False otherwise.
        """
        if not self._outport:
            if not self.connect():
                return False

        if self._running:
            return True

        self._running = True
        self._thread = threading.Thread(target=self._run_chase_pattern, daemon=True)
        self._thread.start()
        self._log("launchpad_lights", status="started", pattern="chase")
        return True

    def stop(self) -> None:
        """Stop the light pattern animation."""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._log("launchpad_lights", status="stopped")


def start_cat_lights(logger: JSONLLogger | None = None) -> LaunchpadLights | None:
    """Start cat-enticing light pattern on Launchpad.

    Convenience function that creates a LaunchpadLights instance,
    connects to the Launchpad, and starts the animation.

    Args:
        logger: Optional logger for recording actions.

    Returns:
        LaunchpadLights instance if successful, None otherwise.
    """
    lights = LaunchpadLights(logger)
    if lights.start():
        return lights
    return None


def stop_cat_lights(lights: LaunchpadLights | None) -> None:
    """Stop cat-enticing light pattern.

    Args:
        lights: LaunchpadLights instance to stop (can be None).
    """
    if lights:
        lights.disconnect()
