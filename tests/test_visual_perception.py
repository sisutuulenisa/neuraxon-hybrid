"""Tests for the visual perception pipeline."""

from __future__ import annotations

from neuraxon_agent.visual import DOMElement, DOMSpatialEncoder, ScreenshotInput, TrinaryGridEncoder


class TestScreenshotInput:
    def test_from_pixels_normalizes_rgb_rows(self) -> None:
        screenshot = ScreenshotInput.from_pixels(
            [
                [(0, 0, 0), (255, 255, 255)],
                [(255, 0, 0), (0, 0, 255)],
            ]
        )

        assert screenshot.width == 2
        assert screenshot.height == 2
        assert screenshot.pixels == (
            ((0, 0, 0), (255, 255, 255)),
            ((255, 0, 0), (0, 0, 255)),
        )

    def test_from_pixels_rejects_ragged_rows(self) -> None:
        try:
            ScreenshotInput.from_pixels([[(0, 0, 0)], [(255, 255, 255), (0, 0, 0)]])
        except ValueError as exc:
            assert "same width" in str(exc)
        else:  # pragma: no cover - keeps assertion message useful
            raise AssertionError("ragged pixel rows should be rejected")


class TestTrinaryGridEncoder:
    def test_downsamples_brightness_into_trinary_grid(self) -> None:
        screenshot = ScreenshotInput.from_pixels(
            [
                [(0, 0, 0), (20, 20, 20), (240, 240, 240), (255, 255, 255)],
                [(0, 0, 0), (20, 20, 20), (240, 240, 240), (255, 255, 255)],
                [(110, 110, 110), (120, 120, 120), (130, 130, 130), (140, 140, 140)],
                [(110, 110, 110), (120, 120, 120), (130, 130, 130), (140, 140, 140)],
            ]
        )

        grid = TrinaryGridEncoder(width=2, height=2).encode_screenshot(screenshot)

        assert grid == ((-1, 1), (0, 0))

    def test_flatten_returns_network_ready_vector(self) -> None:
        grid = ((-1, 1), (0, 1))

        assert TrinaryGridEncoder.flatten(grid) == [-1, 1, 0, 1]


class TestDOMSpatialEncoder:
    def test_encodes_element_coverage_as_trinary_grid(self) -> None:
        encoder = DOMSpatialEncoder(
            viewport_width=100,
            viewport_height=100,
            grid_width=4,
            grid_height=4,
        )
        elements = [DOMElement(x=0, y=0, width=50, height=50, role="hero", importance=1)]

        grid = encoder.encode(elements)

        assert grid == (
            (1, 1, -1, -1),
            (1, 1, -1, -1),
            (-1, -1, -1, -1),
            (-1, -1, -1, -1),
        )

    def test_overlapping_elements_use_highest_absolute_importance(self) -> None:
        encoder = DOMSpatialEncoder(
            viewport_width=100,
            viewport_height=100,
            grid_width=2,
            grid_height=2,
        )
        elements = [
            DOMElement(x=0, y=0, width=100, height=100, role="background", importance=0),
            DOMElement(x=0, y=0, width=50, height=50, role="error", importance=-1),
        ]

        grid = encoder.encode(elements)

        assert grid == ((-1, 0), (0, 0))
