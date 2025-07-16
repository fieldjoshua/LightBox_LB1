from __future__ import annotations

"""Hardware configuration dataclass for HUB75 LED matrices.

This module exposes :class:`HardwareConfig`, a dataclass that groups together
all parameters required by the ``rgbmatrix.RGBMatrix`` driver from Henner
Zeller's *rpi-rgb-led-matrix* project.

The class may be instantiated directly, or via
:meth:`HardwareConfig.from_config`, which consumes the project's
:class:`~core.config.ConfigManager` so that the JSON settings file remains the
single source-of-truth.

Default values target a single 64 × 64 panel plugged into an Adafruit RGB
Matrix HAT running on a Raspberry Pi 3B+.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, TYPE_CHECKING

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HardwareConfig:
    """Strongly-typed container for HUB75 driver options."""

    # Matrix geometry
    rows: int = 64
    cols: int = 64
    chain_length: int = 1  # number of panels chained horizontally
    parallel: int = 1      # parallel chains (rare on Pi 3B+)

    # PWM / timing parameters
    pwm_bits: int = 11
    pwm_lsb_nanoseconds: int = 130
    gpio_slowdown: int = 4
    limit_refresh: int = 120  # Limit to 120Hz for stability
    pwm_dither_bits: int = 0  # Dithering to improve color smoothness

    # Advanced signalling parameters
    hardware_pwm: str = "auto"  # "auto", "on", "off"
    scan_mode: int = 0
    row_address_type: int = 0
    multiplexing: int = 0

    # Misc
    cpu_isolation: bool = True  # Use isolated CPU core for display
    show_refresh_rate: bool = False  # Show refresh rate for debugging
    disable_hardware_pulsing: bool = False  # Should be False if hardware PWM is connected
    # Preset recognised by the rgbmatrix C++ driver. Most users should leave
    # the default (Adafruit HAT/Bonnet) unless their panel uses a custom GPIO
    # mapping.
    hardware_mapping: str = "adafruit-hat"

    if TYPE_CHECKING:
        # Forward reference for type checkers / linters
        from core.config import ConfigManager

    @classmethod
    def from_config(
        cls,
        cfg_mgr: "ConfigManager | Dict[str, Any]",  # noqa: F821 – forward ref
    ) -> "HardwareConfig":
        """Create a :class:`HardwareConfig` from the project configuration.

        Parameters
        ----------
        cfg_mgr
            Either an instance of :class:`~core.config.ConfigManager` or the
            dictionary it returns via ``get("hub75")``.
        """
        if hasattr(cfg_mgr, "get"):
            # Assume ConfigManager-like
            hub_cfg: Dict[str, Any] = cfg_mgr.get(  # type: ignore[arg-type]
                "hub75",
                {},
            )
        else:
            hub_cfg = cfg_mgr  # already the mapping we want

        logger.debug(
            "Building HardwareConfig from mapping: %s", hub_cfg
        )
        return cls(
            rows=int(hub_cfg.get("rows", cls.rows)),
            cols=int(hub_cfg.get("cols", cls.cols)),
            chain_length=int(hub_cfg.get("chain_length", cls.chain_length)),
            parallel=int(hub_cfg.get("parallel", cls.parallel)),
            pwm_bits=int(hub_cfg.get("pwm_bits", cls.pwm_bits)),
            pwm_lsb_nanoseconds=int(
                hub_cfg.get("pwm_lsb_nanoseconds", cls.pwm_lsb_nanoseconds)
            ),
            gpio_slowdown=int(hub_cfg.get("gpio_slowdown", cls.gpio_slowdown)),
            limit_refresh=int(hub_cfg.get("limit_refresh", cls.limit_refresh)),
            pwm_dither_bits=int(hub_cfg.get("pwm_dither_bits", cls.pwm_dither_bits)),
            hardware_pwm=str(hub_cfg.get("hardware_pwm", cls.hardware_pwm)),
            scan_mode=int(hub_cfg.get("scan_mode", cls.scan_mode)),
            row_address_type=int(
                hub_cfg.get("row_address_type", cls.row_address_type)
            ),
            multiplexing=int(hub_cfg.get("multiplexing", cls.multiplexing)),
            cpu_isolation=bool(
                hub_cfg.get("cpu_isolation", cls.cpu_isolation)
            ),
            show_refresh_rate=bool(
                hub_cfg.get("show_refresh_rate", cls.show_refresh_rate)
            ),
            disable_hardware_pulsing=bool(
                hub_cfg.get("disable_hardware_pulsing", cls.disable_hardware_pulsing)
            ),
            hardware_mapping=str(
                hub_cfg.get("hardware_mapping", cls.hardware_mapping)
            ),
        )

    # ---------------------------------------------------------------------
    # Convenience helpers
    # ---------------------------------------------------------------------

    @property
    def resolution(self) -> tuple[int, int]:
        """Return ``(cols, rows)`` for quick access."""
        return self.cols, self.rows 