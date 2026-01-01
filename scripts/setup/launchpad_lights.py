# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Launchpad Mini MK3 light patterns for attracting cats.

This module controls the Launchpad's LED grid to display moving patterns
that are enticing to cats. Cats are attracted to movement, so we use
chase patterns with bright, warm colors (reds, oranges, yellows).

Based on Novation Launchpad Mini MK3 Programmer's Reference Manual.
"""

from __future__ import annotations

import random
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

# Snake colors: gradient from bright white head to bright red tail (length=5)
# Based on Launchpad Mini MK3 palette (page 11 of Programmer's Reference):
#   Row 0 (0-7): off, grays, white, pinks
#   Row 1 (8-15): reds(5-7), oranges(8-11), yellows(12-15)
#   Bright colors: 5=red, 9=orange, 13=yellow
WARM_COLORS = [
    3,   # Bright white (head)
    13,  # Bright yellow
    9,   # Bright orange
    6,   # Red-orange (medium red)
    5,   # Bright red (tail)
]

# Animation speed (seconds between frames)
CHASE_SPEED = 0.08

# How long each pattern runs before switching (seconds)
PATTERN_DURATION = 8

# All bright colors for variety (from palette page 11)
ALL_COLORS = [
    5,   # Bright red
    9,   # Bright orange
    13,  # Bright yellow
    17,  # Bright lime-green
    21,  # Bright green
    25,  # Bright green-cyan
    29,  # Bright cyan-green
    33,  # Bright teal
    37,  # Bright cyan
    41,  # Bright blue-cyan
    45,  # Bright blue
    49,  # Bright purple
    53,  # Bright magenta
    57,  # Bright pink
]

# Cool colors for the dot (prey) - bright colors from palette (page 11)
# Using the brightest version of each cool hue
COOL_COLORS = [
    37,  # Bright cyan
    41,  # Bright blue-cyan
    45,  # Bright blue
    49,  # Bright purple
    53,  # Bright magenta
    33,  # Bright teal
    29,  # Bright cyan-green
    25,  # Bright green-cyan
    21,  # Bright green
]

# Snake movement directions (up, down, left, right only)
SNAKE_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Dot movement directions (all 8 directions)
DOT_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

# Forbidden dot positions (3 cells in each corner)
DOT_FORBIDDEN = {
    (0, 0), (0, 1), (1, 0),  # TL corner
    (0, 7), (0, 6), (1, 7),  # TR corner
    (7, 0), (6, 0), (7, 1),  # BL corner
    (7, 7), (7, 6), (6, 7),  # BR corner
}


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

    def _pattern_snake(self, duration: float) -> None:
        """Snake chase pattern - lights chase in a snake across the grid."""
        snake_order = []
        for i, row in enumerate(PAD_GRID):
            if i % 2 == 0:
                snake_order.extend(row)
            else:
                snake_order.extend(reversed(row))

        trail_length = 8
        color_index = 0
        end_time = time.time() + duration

        while self._running and time.time() < end_time:
            for head_pos in range(len(snake_order) + trail_length):
                if not self._running or time.time() >= end_time:
                    break
                self._clear_all_leds()
                for trail_offset in range(trail_length):
                    pos = head_pos - trail_offset
                    if 0 <= pos < len(snake_order):
                        color_idx = (color_index + trail_offset) % len(WARM_COLORS)
                        pulse = trail_offset == 0
                        self._set_led(snake_order[pos], WARM_COLORS[color_idx], pulse)
                time.sleep(CHASE_SPEED)
            color_index = (color_index + 1) % len(WARM_COLORS)

    def _pattern_sparkle(self, duration: float) -> None:
        """Random sparkle pattern - random pads flash like fireflies."""
        end_time = time.time() + duration
        active_pads: dict[int, float] = {}  # note -> expire_time

        while self._running and time.time() < end_time:
            now = time.time()
            # Remove expired pads
            expired = [n for n, exp in active_pads.items() if now >= exp]
            for note in expired:
                self._set_led(note, 0)
                del active_pads[note]

            # Add new random pads
            if len(active_pads) < 12 and random.random() > 0.3:
                row = random.choice(PAD_GRID)
                note = random.choice(row)
                if note not in active_pads:
                    color = random.choice(ALL_COLORS)
                    pulse = random.random() > 0.5
                    self._set_led(note, color, pulse)
                    active_pads[note] = now + random.uniform(0.2, 0.8)

            time.sleep(0.05)

        # Clear remaining
        for note in active_pads:
            self._set_led(note, 0)

    def _pattern_rain(self, duration: float) -> None:
        """Rain pattern - drops fall from top to bottom."""
        end_time = time.time() + duration
        drops: list[tuple[int, int, int]] = []  # (col, row, color)

        while self._running and time.time() < end_time:
            self._clear_all_leds()

            # Move drops down
            new_drops = []
            for col, row, color in drops:
                new_row = row + 1
                if new_row < 8:
                    new_drops.append((col, new_row, color))
                    self._set_led(PAD_GRID[new_row][col], color)
            drops = new_drops

            # Add new drops at top
            if random.random() > 0.5:
                col = random.randint(0, 7)
                color = random.choice(WARM_COLORS)
                drops.append((col, 0, color))
                self._set_led(PAD_GRID[0][col], color, pulse=True)

            time.sleep(0.12)

    def _pattern_spiral(self, duration: float) -> None:
        """Spiral pattern - lights spiral from outside to center."""
        # Create spiral order
        spiral = []
        top, bottom, left, right = 0, 7, 0, 7
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                spiral.append(PAD_GRID[top][c])
            top += 1
            for r in range(top, bottom + 1):
                spiral.append(PAD_GRID[r][right])
            right -= 1
            if top <= bottom:
                for c in range(right, left - 1, -1):
                    spiral.append(PAD_GRID[bottom][c])
                bottom -= 1
            if left <= right:
                for r in range(bottom, top - 1, -1):
                    spiral.append(PAD_GRID[r][left])
                left += 1

        trail_length = 10
        color_index = 0
        end_time = time.time() + duration

        while self._running and time.time() < end_time:
            for head_pos in range(len(spiral) + trail_length):
                if not self._running or time.time() >= end_time:
                    break
                self._clear_all_leds()
                for trail_offset in range(trail_length):
                    pos = head_pos - trail_offset
                    if 0 <= pos < len(spiral):
                        color_idx = (color_index + trail_offset) % len(ALL_COLORS)
                        self._set_led(spiral[pos], ALL_COLORS[color_idx], trail_offset == 0)
                time.sleep(CHASE_SPEED)
            color_index = (color_index + 2) % len(ALL_COLORS)

    def _pattern_wave(self, duration: float) -> None:
        """Wave pattern - horizontal waves sweep across."""
        end_time = time.time() + duration
        wave_pos = 0
        color_index = 0

        while self._running and time.time() < end_time:
            self._clear_all_leds()
            # Light up columns based on wave position
            for offset in range(3):
                col = (wave_pos - offset) % 8
                for row in range(8):
                    color = WARM_COLORS[(color_index + offset) % len(WARM_COLORS)]
                    self._set_led(PAD_GRID[row][col], color, offset == 0)

            wave_pos = (wave_pos + 1) % 8
            if wave_pos == 0:
                color_index = (color_index + 1) % len(WARM_COLORS)
            time.sleep(0.1)

    def _pattern_diagonal(self, duration: float) -> None:
        """Diagonal chase pattern - lights move diagonally."""
        diagonals = []
        for d in range(15):  # 15 diagonals in 8x8 grid
            diag = []
            for r in range(8):
                c = d - r
                if 0 <= c < 8:
                    diag.append(PAD_GRID[r][c])
            if diag:
                diagonals.append(diag)

        end_time = time.time() + duration
        color_index = 0

        while self._running and time.time() < end_time:
            for i, diag in enumerate(diagonals):
                if not self._running or time.time() >= end_time:
                    break
                self._clear_all_leds()
                color = ALL_COLORS[(color_index + i) % len(ALL_COLORS)]
                for note in diag:
                    self._set_led(note, color, True)
                # Also show trailing diagonals
                for trail in range(1, 3):
                    if i - trail >= 0:
                        trail_color = WARM_COLORS[(color_index + i - trail) % len(WARM_COLORS)]
                        for note in diagonals[i - trail]:
                            self._set_led(note, trail_color)
                time.sleep(0.08)
            color_index = (color_index + 1) % len(ALL_COLORS)

    def _pattern_expand(self, duration: float) -> None:
        """Expanding rings from center."""
        end_time = time.time() + duration
        color_index = 0

        while self._running and time.time() < end_time:
            for radius in range(6):
                if not self._running or time.time() >= end_time:
                    break
                self._clear_all_leds()
                color = ALL_COLORS[color_index % len(ALL_COLORS)]

                # Draw ring at current radius
                for r in range(8):
                    for c in range(8):
                        dist = max(abs(r - 3.5), abs(c - 3.5))
                        if radius <= dist < radius + 1:
                            self._set_led(PAD_GRID[r][c], color, True)
                        elif radius - 1 <= dist < radius:
                            self._set_led(PAD_GRID[r][c], WARM_COLORS[color_index % len(WARM_COLORS)])

                time.sleep(0.15)
            color_index = (color_index + 1) % len(ALL_COLORS)

    def _pattern_hunt(self, duration: float) -> None:
        """Snake hunts dot pattern - Nerys's favorite!

        A warm-colored snake chases a cool-colored dot.
        - Snake moves up/down/left/right only
        - Dot moves in 8 directions (including diagonals)
        - Dot moves half as fast, away from snake
        - Board wraps around (torus topology)
        - When snake catches dot, new dot spawns
        - Snake length is fixed (doesn't grow)
        """
        end_time = time.time() + duration
        snake_length = 5
        snake_speed = 0.135  # seconds per move
        dot_speed = 0.15     # seconds per move (~10s avg chase)

        # Initialize snake in center, moving right
        snake: list[tuple[int, int]] = [(3, 3 - i) for i in range(snake_length)]
        snake_dir = (0, 1)  # moving right

        # Spawn dot away from snake
        dot = self._spawn_dot_away_from(snake)
        dot_color_idx = 0

        last_snake_move = time.time()
        last_dot_move = time.time()

        while self._running and time.time() < end_time:
            now = time.time()

            # Move snake
            if now - last_snake_move >= snake_speed:
                # Choose direction toward dot
                snake_dir = self._choose_snake_direction(snake[0], dot, snake_dir, snake)
                # Move head (NO wrapping - stay on square)
                new_r = snake[0][0] + snake_dir[0]
                new_c = snake[0][1] + snake_dir[1]
                # Clamp to grid bounds
                new_r = max(0, min(7, new_r))
                new_c = max(0, min(7, new_c))
                new_head = (new_r, new_c)
                # Only move if not hitting own body
                if new_head not in snake[1:]:
                    snake = [new_head] + snake[:-1]
                last_snake_move = now

                # Check if caught dot
                if snake[0] == dot:
                    dot = self._spawn_dot_away_from(snake)
                    # Ensure new color is different from current
                    old_color_idx = dot_color_idx
                    while dot_color_idx == old_color_idx:
                        dot_color_idx = random.randint(0, len(COOL_COLORS) - 1)

            # Move dot (half as often)
            if now - last_dot_move >= dot_speed:
                dot = self._move_dot_away(dot, snake[0])
                last_dot_move = now

            # Draw
            self._clear_all_leds()

            # Draw snake with warm color gradient
            for i, (r, c) in enumerate(snake):
                color = WARM_COLORS[i % len(WARM_COLORS)]
                pulse = i == 0  # Head pulses
                self._set_led(PAD_GRID[r][c], color, pulse)

            # Draw dot with cool color (pulsing)
            dr, dc = dot
            self._set_led(PAD_GRID[dr][dc], COOL_COLORS[dot_color_idx], pulse=True)

            time.sleep(0.03)

    def _spawn_dot_away_from(self, snake: list[tuple[int, int]]) -> tuple[int, int]:
        """Spawn dot at random position not occupied by snake or forbidden."""
        snake_set = set(snake)
        while True:
            r, c = random.randint(0, 7), random.randint(0, 7)
            if (r, c) not in snake_set and (r, c) not in DOT_FORBIDDEN:
                # Prefer positions far from snake head
                head = snake[0]
                dist = abs(r - head[0]) + abs(c - head[1])
                if dist >= 3 or random.random() > 0.5:
                    return (r, c)

    def _choose_snake_direction(
        self, head: tuple[int, int], dot: tuple[int, int], current_dir: tuple[int, int],
        snake_body: list[tuple[int, int]]
    ) -> tuple[int, int]:
        """Choose snake direction toward dot (square geometry, no wrapping)."""
        hr, hc = head
        dr, dc = dot

        # Calculate direct distances on square (no wrapping)
        row_diff = dr - hr
        col_diff = dc - hc

        # Build list of valid directions (not blocked by wall or body)
        valid_dirs = []
        for d in SNAKE_DIRS:
            new_r = hr + d[0]
            new_c = hc + d[1]
            # Check bounds (snake stays on square)
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                # Check not hitting own body
                if (new_r, new_c) not in snake_body[1:]:
                    valid_dirs.append(d)

        if not valid_dirs:
            return current_dir  # Stuck

        # Score each valid direction by how much it reduces distance to dot
        def score_dir(d: tuple[int, int]) -> int:
            # Higher score = better (reduces distance more)
            score = 0
            if row_diff > 0 and d[0] > 0:
                score += abs(row_diff)  # Moving down toward dot below
            elif row_diff < 0 and d[0] < 0:
                score += abs(row_diff)  # Moving up toward dot above
            if col_diff > 0 and d[1] > 0:
                score += abs(col_diff)  # Moving right toward dot right
            elif col_diff < 0 and d[1] < 0:
                score += abs(col_diff)  # Moving left toward dot left
            return score

        # Sort by score descending
        scored = [(score_dir(d), d) for d in valid_dirs]
        scored.sort(key=lambda x: -x[0])

        # Pick best direction, with slight randomness
        if len(scored) > 1 and scored[0][0] == scored[1][0] and random.random() > 0.5:
            return scored[1][1]
        return scored[0][1]

    def _figure8_wrap(self, r: int, c: int) -> tuple[int, int]:
        """Wrap coordinates on figure-8 topology.

        Twisted figure-8: top↔left, bottom↔right (preserves corners).
        - (0,0) TL → (0,0) TL (stays)
        - (0,7) TR → (7,0) BL (swaps)
        - (7,7) BR → (7,7) BR (stays)
        - (7,0) BL → (0,7) TR (swaps)
        """
        # Clamp for edge position
        c_clamped = max(0, min(7, c))
        r_clamped = max(0, min(7, r))

        # Handle row overflow/underflow first
        if r < 0:
            # Off top → left edge, column becomes row
            return (c_clamped, 0)
        elif r > 7:
            # Off bottom → right edge, column becomes row
            return (c_clamped, 7)

        # Handle column overflow/underflow
        if c < 0:
            # Off left → top edge, row becomes column
            return (0, r_clamped)
        elif c > 7:
            # Off right → bottom edge, row becomes column
            return (7, r_clamped)

        return (r, c)

    def _move_dot_away(self, dot: tuple[int, int], snake_head: tuple[int, int]) -> tuple[int, int]:
        """Move dot away from snake head (bounded square, no wrapping)."""
        dr, dc = dot
        hr, hc = snake_head

        def square_distance(r1: int, c1: int, r2: int, c2: int) -> int:
            """Calculate Manhattan distance on square (no wrapping)."""
            return abs(r1 - r2) + abs(c1 - c2)

        current_dist = square_distance(dr, dc, hr, hc)

        # Score each direction, clamping to grid bounds (no wrapping)
        scored_dirs = []
        for d in DOT_DIRS:
            new_r = max(0, min(7, dr + d[0]))
            new_c = max(0, min(7, dc + d[1]))
            # Skip if didn't actually move (hit wall)
            if (new_r, new_c) == (dr, dc):
                continue
            # Skip forbidden positions
            if (new_r, new_c) in DOT_FORBIDDEN:
                continue
            new_dist = square_distance(new_r, new_c, hr, hc)
            # Prefer directions that increase distance from snake
            scored_dirs.append((new_dist - current_dist, d))

        # If all directions blocked, stay in place
        if not scored_dirs:
            return dot

        # Sort by distance increase (descending)
        scored_dirs.sort(key=lambda x: -x[0])

        # Pick from best directions with some randomness
        best_score = scored_dirs[0][0]
        best_dirs = [d for score, d in scored_dirs if score == best_score]
        direction = random.choice(best_dirs)

        new_r = max(0, min(7, dr + direction[0]))
        new_c = max(0, min(7, dc + direction[1]))
        return (new_r, new_c)

    def _run_hunt_loop(self) -> None:
        """Run the hunt pattern continuously (default mode)."""
        self._enter_programmer_mode()
        self._clear_all_leds()

        while self._running:
            # Run hunt pattern in long segments
            self._pattern_hunt(60.0)  # 1 minute per cycle
            self._clear_all_leds()

        self._clear_all_leds()
        self._exit_programmer_mode()

    def _run_random_patterns(self) -> None:
        """Run random patterns, cycling every few seconds."""
        self._enter_programmer_mode()
        self._clear_all_leds()

        patterns = [
            self._pattern_snake,
            self._pattern_sparkle,
            self._pattern_rain,
            self._pattern_spiral,
            self._pattern_wave,
            self._pattern_diagonal,
            self._pattern_expand,
            self._pattern_hunt,
        ]

        while self._running:
            pattern = random.choice(patterns)
            pattern(PATTERN_DURATION)
            self._clear_all_leds()

        self._clear_all_leds()
        self._exit_programmer_mode()

    def start(self, pattern: str = "hunt") -> bool:
        """Start the light pattern animation.

        Args:
            pattern: Pattern mode - "hunt" (default) or "random".

        Returns:
            True if started successfully, False otherwise.
        """
        if not self._outport:
            if not self.connect():
                return False

        if self._running:
            return True

        self._running = True
        if pattern == "random":
            self._thread = threading.Thread(target=self._run_random_patterns, daemon=True)
        else:
            self._thread = threading.Thread(target=self._run_hunt_loop, daemon=True)
        self._thread.start()
        self._log("launchpad_lights", status="started", pattern=pattern)
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


def start_cat_lights(
    logger: JSONLLogger | None = None, pattern: str = "hunt"
) -> LaunchpadLights | None:
    """Start cat-enticing light pattern on Launchpad.

    Convenience function that creates a LaunchpadLights instance,
    connects to the Launchpad, and starts the animation.

    Args:
        logger: Optional logger for recording actions.
        pattern: Pattern mode - "hunt" (default) or "random".

    Returns:
        LaunchpadLights instance if successful, None otherwise.
    """
    lights = LaunchpadLights(logger)
    if lights.start(pattern=pattern):
        return lights
    return None


def stop_cat_lights(lights: LaunchpadLights | None) -> None:
    """Stop cat-enticing light pattern.

    Args:
        lights: LaunchpadLights instance to stop (can be None).
    """
    if lights:
        lights.disconnect()
