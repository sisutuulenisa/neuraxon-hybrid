"""Visual perception pipeline for spatial UI/UX observations.

The visual package keeps the core project dependency-free. Screenshot file
loading uses Pillow only when callers opt into the ``visual`` extra; tests and
agent integrations can use ``ScreenshotInput.from_pixels`` with plain Python
RGB buffers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence, cast

RGBPixel = tuple[int, int, int]
PixelRows = tuple[tuple[RGBPixel, ...], ...]
TrinaryGrid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ScreenshotInput:
    """Normalized RGB screenshot buffer.

    Pixels are stored as immutable ``height x width`` RGB tuples so the object
    is deterministic and serializable without requiring numpy in core runtime.
    """

    width: int
    height: int
    pixels: PixelRows

    @classmethod
    def from_pixels(cls, pixels: Sequence[Sequence[Sequence[int]]]) -> "ScreenshotInput":
        """Create a screenshot from a rectangular RGB pixel buffer."""
        if not pixels:
            raise ValueError("pixels must contain at least one row")

        normalized_rows: list[tuple[RGBPixel, ...]] = []
        expected_width: int | None = None
        for row in pixels:
            if not row:
                raise ValueError("pixel rows must not be empty")
            normalized_row = tuple(cls._normalize_pixel(pixel) for pixel in row)
            if expected_width is None:
                expected_width = len(normalized_row)
            elif len(normalized_row) != expected_width:
                raise ValueError("all pixel rows must have the same width")
            normalized_rows.append(normalized_row)

        assert expected_width is not None
        return cls(width=expected_width, height=len(normalized_rows), pixels=tuple(normalized_rows))

    @classmethod
    def from_file(cls, path: str | Path) -> "ScreenshotInput":
        """Load a PNG/JPG screenshot via Pillow when the visual extra is installed."""
        try:
            from PIL import Image  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "ScreenshotInput.from_file requires Pillow; install neuraxon-agent[visual]"
            ) from exc

        with Image.open(path) as image:  # pragma: no cover - covered when Pillow installed
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            flat_pixels = list(rgb_image.getdata())

        rows = [flat_pixels[y * width : (y + 1) * width] for y in range(height)]
        return cls.from_pixels(rows)

    @staticmethod
    def _normalize_pixel(pixel: Sequence[int]) -> RGBPixel:
        if len(pixel) < 3:
            raise ValueError("RGB pixels must contain at least three channels")
        channels = tuple(int(channel) for channel in pixel[:3])
        if any(channel < 0 or channel > 255 for channel in channels):
            raise ValueError("RGB channel values must be between 0 and 255")
        return cast(RGBPixel, channels)


class TrinaryGridEncoder:
    """Downsample visual buffers into fixed-size {-1, 0, +1} grids."""

    def __init__(
        self,
        width: int = 32,
        height: int = 32,
        dark_threshold: float = 85.0,
        light_threshold: float = 170.0,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("grid width and height must be positive")
        if dark_threshold >= light_threshold:
            raise ValueError("dark_threshold must be lower than light_threshold")
        self.width = width
        self.height = height
        self.dark_threshold = dark_threshold
        self.light_threshold = light_threshold

    def encode_screenshot(self, screenshot: ScreenshotInput) -> TrinaryGrid:
        """Encode average cell brightness as dark=-1, mid=0, light=+1."""
        rows: list[tuple[int, ...]] = []
        for grid_y in range(self.height):
            encoded_row: list[int] = []
            y0, y1 = _cell_bounds(grid_y, self.height, screenshot.height)
            for grid_x in range(self.width):
                x0, x1 = _cell_bounds(grid_x, self.width, screenshot.width)
                brightness = _average_brightness(screenshot.pixels, x0, x1, y0, y1)
                encoded_row.append(self._encode_scalar(brightness))
            rows.append(tuple(encoded_row))
        return tuple(rows)

    def _encode_scalar(self, value: float) -> int:
        if value < self.dark_threshold:
            return -1
        if value > self.light_threshold:
            return 1
        return 0

    @staticmethod
    def flatten(grid: Iterable[Iterable[int]]) -> list[int]:
        """Flatten a trinary grid into a Neuraxon input vector."""
        return [int(value) for row in grid for value in row]


@dataclass(frozen=True)
class DOMElement:
    """Spatial DOM element bounds in viewport coordinates."""

    x: float
    y: float
    width: float
    height: float
    role: str = "element"
    importance: int = 1

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("DOMElement width and height must be non-negative")
        if self.importance not in (-1, 0, 1):
            raise ValueError("DOMElement importance must be -1, 0, or 1")


class DOMSpatialEncoder:
    """Encode DOM element coverage into a deterministic trinary layout grid."""

    def __init__(
        self,
        viewport_width: float,
        viewport_height: float,
        grid_width: int = 32,
        grid_height: int = 32,
    ) -> None:
        if viewport_width <= 0 or viewport_height <= 0:
            raise ValueError("viewport dimensions must be positive")
        if grid_width <= 0 or grid_height <= 0:
            raise ValueError("grid dimensions must be positive")
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.grid_width = grid_width
        self.grid_height = grid_height

    def encode(self, elements: Sequence[DOMElement]) -> TrinaryGrid:
        scores: list[list[int | None]] = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        for element in elements:
            if element.width == 0 or element.height == 0:
                continue
            for grid_y in range(self.grid_height):
                cell_y0, cell_y1 = _float_cell_bounds(
                    grid_y, self.grid_height, self.viewport_height
                )
                for grid_x in range(self.grid_width):
                    cell_x0, cell_x1 = _float_cell_bounds(
                        grid_x, self.grid_width, self.viewport_width
                    )
                    current = scores[grid_y][grid_x]
                    if _rects_overlap(
                        cell_x0,
                        cell_y0,
                        cell_x1,
                        cell_y1,
                        element.x,
                        element.y,
                        element.x + element.width,
                        element.y + element.height,
                    ) and (current is None or abs(element.importance) >= abs(current)):
                        scores[grid_y][grid_x] = element.importance
        return tuple(tuple(-1 if value is None else value for value in row) for row in scores)


def _cell_bounds(index: int, cells: int, source_size: int) -> tuple[int, int]:
    start = (index * source_size) // cells
    end = ((index + 1) * source_size) // cells
    if end <= start:
        end = min(source_size, start + 1)
    return start, end


def _float_cell_bounds(index: int, cells: int, source_size: float) -> tuple[float, float]:
    start = (index * source_size) / cells
    end = ((index + 1) * source_size) / cells
    return start, end


def _average_brightness(pixels: PixelRows, x0: int, x1: int, y0: int, y1: int) -> float:
    total = 0.0
    count = 0
    for row in pixels[y0:y1]:
        for red, green, blue in row[x0:x1]:
            total += (red + green + blue) / 3.0
            count += 1
    if count == 0:
        return 0.0
    return total / count


def _rects_overlap(
    ax0: float,
    ay0: float,
    ax1: float,
    ay1: float,
    bx0: float,
    by0: float,
    bx1: float,
    by1: float,
) -> bool:
    return ax0 < bx1 and ax1 > bx0 and ay0 < by1 and ay1 > by0


__all__ = [
    "DOMElement",
    "DOMSpatialEncoder",
    "RGBPixel",
    "ScreenshotInput",
    "TrinaryGrid",
    "TrinaryGridEncoder",
]
