"""High-level wrapper around the rpi-rgb-led-matrix driver.

This module isolates all direct interactions with the ``rgbmatrix`` library so
other project components (animations, conductor, web API) never import that
low-level dependency directly.  Doing so improves testability: when the
``rgbmatrix`` module is unavailable (e.g. during CI on non-Raspberry Pi
workstations) the :class:`MatrixController` seamlessly enters *simulation* mode
where frame operations are no-ops but retain the same public interface.
"""

from __future__ import annotations

from types import SimpleNamespace
import logging
import time

from .hardware_config import HardwareConfig

logger = logging.getLogger(__name__)

try:
    # The official Henner Zeller library. Import guarded so that development
    # on non-Pi hosts does not raise ImportError.
    from rgbmatrix import RGBMatrix  # type: ignore
    from rgbmatrix import RGBMatrixOptions  # type: ignore

    _HARDWARE_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover – CI runners lack the module
    logger.warning(
        "rgbmatrix module not found – running MatrixController in "
        "simulation mode"
    )
    _HARDWARE_AVAILABLE = False

    # Lightweight stub objects that match the API shape used below. They let us
    # exercise application logic and unit tests without real hardware.
    class _SimCanvas(SimpleNamespace):
        def Clear(self) -> None:  # noqa: D401 – simple stub verb
            """Pretend to clear the panel."""

    class _SimMatrix(SimpleNamespace):
        width: int = 64
        height: int = 64

        def CreateFrameCanvas(self) -> _SimCanvas:  # noqa: D401 – simple stub verb
            return _SimCanvas()

        def SwapOnVSync(self, _canvas: _SimCanvas) -> _SimCanvas:  # noqa: D401
            # Swap is instantaneous in simulation; just return same canvas.
            return _canvas

        def Clear(self) -> None:  # noqa: D401 – simple stub verb
            """No-op clear."""


class MatrixController:
    """Facade providing safe, typed access to the HUB75 LED matrix.

    Parameters
    ----------
    hw_cfg
        Hardware configuration dataclass describing the target panel.
    target_fps
        Desired frame-rate limit.  Used only for simulation throttling – the
        underlying *rgbmatrix* driver refreshes as fast as possible in hardware
        mode.
    """

    def __init__(self, hw_cfg: HardwareConfig, target_fps: int | float = 30):
        self.hw_cfg: HardwareConfig = hw_cfg
        self._target_fps: float = float(target_fps)
        self._frame_period: float = 1.0 / self._target_fps if self._target_fps else 0

        if _HARDWARE_AVAILABLE:
            self._matrix = self._create_matrix()
            self._canvas = self._matrix.CreateFrameCanvas()
            logger.info(
                "Initialised RGBMatrix: %sx%s",
                hw_cfg.cols,
                hw_cfg.rows,
            )
        else:
            self._matrix = _SimMatrix(width=hw_cfg.cols, height=hw_cfg.rows)
            self._canvas = self._matrix.CreateFrameCanvas()
            logger.info(
                "Initialised *simulated* RGBMatrix: %sx%s",  # noqa: E501
                hw_cfg.cols,
                hw_cfg.rows,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def width(self) -> int:  # noqa: D401 – simple accessor verb
        """Return matrix width in pixels."""
        return self.hw_cfg.cols

    @property
    def height(self) -> int:  # noqa: D401 – simple accessor verb
        """Return matrix height in pixels."""
        return self.hw_cfg.rows

    def create_frame(self):
        """Allocate a fresh off-screen canvas ready for drawing."""
        return self._matrix.CreateFrameCanvas()

    def swap(self, frame) -> None:
        """Block until the provided frame is shown (with VSync).

        In simulation mode the call sleeps long enough to emulate the requested
        frame-rate so the rest of the application experiences realistic timing.
        """
        self._canvas = self._matrix.SwapOnVSync(frame)
        if not _HARDWARE_AVAILABLE and self._frame_period:
            time.sleep(self._frame_period)

    def clear(self) -> None:
        """Clear the display immediately."""
        self._matrix.Clear()

    # ------------------------------------------------------------------
    # Cleanup helpers
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Release hardware resources (if any) and blank the panel."""
        try:
            self.clear()
        finally:
            logger.info("MatrixController cleaned up")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_matrix(self):  # noqa: D401 – internal helper verb
        if not _HARDWARE_AVAILABLE:  # pragma: no cover – guarded earlier
            raise RuntimeError("_create_matrix called without rgbmatrix present")

        opts = RGBMatrixOptions()
        opts.rows = self.hw_cfg.rows
        opts.cols = self.hw_cfg.cols
        opts.chain_length = self.hw_cfg.chain_length
        opts.parallel = self.hw_cfg.parallel
        opts.hardware_mapping = self.hw_cfg.hardware_mapping
        opts.pwm_bits = self.hw_cfg.pwm_bits
        opts.pwm_lsb_nanoseconds = self.hw_cfg.pwm_lsb_nanoseconds
        opts.gpio_slowdown = self.hw_cfg.gpio_slowdown
        if self.hw_cfg.limit_refresh:
            # Attribute present only on recent builds.  Guard with attr check.
            # pyright: ignore [reportGeneralTypeIssues] – attribute optional
            opts.limit_refresh_rate_hz = (
                self.hw_cfg.limit_refresh  # type: ignore[attr-defined]
            )
        # Advanced options – applied only when non-default to avoid obscure
        # driver-side issues.
        if self.hw_cfg.scan_mode:
            opts.scan_mode = self.hw_cfg.scan_mode
        if self.hw_cfg.row_address_type:
            opts.row_address_type = self.hw_cfg.row_address_type
        if self.hw_cfg.multiplexing:
            opts.multiplexing = self.hw_cfg.multiplexing

        return RGBMatrix(options=opts) 