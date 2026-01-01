# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Club Maquis
"""Tests for Launchpad lights module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.setup.launchpad_lights import (
    CHASE_SPEED,
    LAUNCHPAD_PORT_PATTERN,
    PAD_GRID,
    PROGRAMMER_MODE,
    SYSEX_HEADER,
    WARM_COLORS,
    LaunchpadLights,
    start_cat_lights,
    stop_cat_lights,
)


class TestLaunchpadLightsConstants:
    """Test module constants are correctly defined."""

    def test_sysex_header_format(self):
        """SysEx header matches Launchpad Mini MK3 spec."""
        # Header should be: 00 20 29 02 0D (Novation manufacturer ID + device)
        assert SYSEX_HEADER == [0x00, 0x20, 0x29, 0x02, 0x0D]

    def test_programmer_mode_value(self):
        """Programmer mode should be 0x7F per spec."""
        assert PROGRAMMER_MODE == 0x7F

    def test_pad_grid_dimensions(self):
        """Pad grid should be 8x8."""
        assert len(PAD_GRID) == 8
        for row in PAD_GRID:
            assert len(row) == 8

    def test_pad_grid_note_range(self):
        """Pad notes should be in valid range (11-88)."""
        for row in PAD_GRID:
            for note in row:
                assert 11 <= note <= 88

    def test_warm_colors_not_empty(self):
        """Warm colors palette should have colors defined."""
        assert len(WARM_COLORS) > 0

    def test_warm_colors_in_valid_range(self):
        """Color indices should be in valid palette range (0-127)."""
        for color in WARM_COLORS:
            assert 0 <= color <= 127

    def test_chase_speed_positive(self):
        """Chase speed should be a positive value."""
        assert CHASE_SPEED > 0


class TestLaunchpadLightsNoDevice:
    """Test LaunchpadLights behavior when no device is connected."""

    def test_connect_without_mido(self):
        """Connect should fail gracefully if mido is not available."""
        with patch("scripts.setup.launchpad_lights.mido", None):
            lights = LaunchpadLights()
            assert lights.connect() is False

    def test_connect_no_launchpad_found(self):
        """Connect should fail if no Launchpad port exists."""
        mock_mido = MagicMock()
        mock_mido.get_output_names.return_value = ["Other MIDI Device"]

        with patch("scripts.setup.launchpad_lights.mido", mock_mido):
            lights = LaunchpadLights()
            assert lights.connect() is False

    def test_start_without_connection(self):
        """Start should fail if connect fails."""
        mock_mido = MagicMock()
        mock_mido.get_output_names.return_value = []

        with patch("scripts.setup.launchpad_lights.mido", mock_mido):
            lights = LaunchpadLights()
            assert lights.start() is False


class TestLaunchpadLightsWithMock:
    """Test LaunchpadLights with mocked MIDI port."""

    @pytest.fixture
    def mock_mido(self):
        """Create a mock mido module."""
        mock = MagicMock()
        mock.get_output_names.return_value = [f"{LAUNCHPAD_PORT_PATTERN} LPMiniMK3 MIDI"]
        mock.Message = MagicMock()
        return mock

    def test_connect_success(self, mock_mido):
        """Connect should succeed when Launchpad is found."""
        with patch("scripts.setup.launchpad_lights.mido", mock_mido):
            lights = LaunchpadLights()
            assert lights.connect() is True
            mock_mido.open_output.assert_called_once()

    def test_disconnect_closes_port(self, mock_mido):
        """Disconnect should close the MIDI port."""
        mock_port = MagicMock()
        mock_mido.open_output.return_value = mock_port

        with patch("scripts.setup.launchpad_lights.mido", mock_mido):
            lights = LaunchpadLights()
            lights.connect()
            lights.disconnect()
            mock_port.close.assert_called_once()


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_start_cat_lights_returns_none_on_failure(self):
        """start_cat_lights should return None if connection fails."""
        with patch("scripts.setup.launchpad_lights.mido", None):
            result = start_cat_lights()
            assert result is None

    def test_stop_cat_lights_handles_none(self):
        """stop_cat_lights should handle None input gracefully."""
        # Should not raise
        stop_cat_lights(None)

    def test_stop_cat_lights_calls_disconnect(self):
        """stop_cat_lights should call disconnect on the lights object."""
        mock_lights = MagicMock()
        stop_cat_lights(mock_lights)
        mock_lights.disconnect.assert_called_once()
