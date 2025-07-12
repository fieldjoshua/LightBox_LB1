"""MatrixDriver adapter bridging :class:`core.matrix_controller.MatrixController`.

This adapter lets legacy code that expects the original ``MatrixDriver``
interface work with the new high-level controller without refactoring.
"""

# flake8: noqa: E501  # allow a few intentional long lines for readability

from __future__ import annotations

import logging
from typing import List, Tuple, Union

from core.hardware_config import HardwareConfig
from core.matrix_controller import MatrixController
from .matrix_driver import MatrixDriver

logger = logging.getLogger(__name__)


class HUB75ControllerDriver(MatrixDriver):
    """Bridge between old MatrixDriver API and new MatrixController."""

    def __init__(self, config):
        super().__init__(config)
        self.hw_cfg = HardwareConfig.from_config(config)
        self.width = self.hw_cfg.cols
        self.height = self.hw_cfg.rows
        self.num_pixels = self.width * self.height
        self._brightness = config.get("brightness", 1.0)

        fps = config.get("target_fps", 30)
        self.controller = MatrixController(self.hw_cfg, fps)

    # ------------------------------------------------------------------
    # MatrixDriver interface implementation
    # ------------------------------------------------------------------

    def initialize(self) -> bool:  # noqa: D401 – imperative verb OK
        """Hardware is already initialised in MatrixController constructor."""
        return True

    def _apply_brightness(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        if self._brightness >= 0.999:
            return rgb
        r, g, b = rgb
        scale = self._brightness
        return int(r * scale), int(g * scale), int(b * scale)

    def update(
        self,
        frame_buffer: Union[List[Tuple[int, int, int]], bytearray],
    ) -> None:
        """Copy an RGB frame buffer to the hardware canvas."""
        canvas = self.controller.create_frame()

        if isinstance(frame_buffer, bytearray):
            # Convert byte-stream (RGBRGB...) into pixel tuples on the fly.
            buf_len = len(frame_buffer)
            for idx in range(0, buf_len, 3):
                pixel_index = idx // 3
                if pixel_index >= self.num_pixels:
                    break
                x = pixel_index % self.width
                y = pixel_index // self.width
                r = frame_buffer[idx]
                g = frame_buffer[idx + 1]
                b = frame_buffer[idx + 2]
                r, g, b = self._apply_brightness((r, g, b))
                canvas.SetPixel(x, y, r, g, b)  # type: ignore[attr-defined]
        else:
            for pixel_index, (r, g, b) in enumerate(frame_buffer):
                if pixel_index >= self.num_pixels:
                    break
                x = pixel_index % self.width
                y = pixel_index // self.width
                r, g, b = self._apply_brightness((r, g, b))
                canvas.SetPixel(x, y, r, g, b)  # type: ignore[attr-defined]

        self.controller.swap(canvas)

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        canvas = self.controller.create_frame()
        r, g, b = self._apply_brightness((r, g, b))
        canvas.SetPixel(x, y, r, g, b)  # type: ignore[attr-defined]
        self.controller.swap(canvas)

    def fill(self, r: int, g: int, b: int) -> None:
        canvas = self.controller.create_frame()
        r, g, b = self._apply_brightness((r, g, b))
        for y in range(self.height):
            for x in range(self.width):
                canvas.SetPixel(x, y, r, g, b)  # type: ignore[attr-defined]
        self.controller.swap(canvas)

    def clear(self) -> None:
        self.controller.clear()

    def show(self) -> None:  # No-op; swap is done in update
        pass

    def set_brightness(self, brightness: float) -> None:
        self._brightness = max(0.0, min(1.0, brightness))

    def cleanup(self) -> None:
        self.controller.cleanup() 