"""Compatibility shim for legacy scripts that import `config_enhanced`.

Modern code uses `core.config.ConfigManager`.  This module re-exports a
`Config` class with the same basic interface so older animation and test
scripts continue to run without modification.
"""

from core.config import ConfigManager


class Config(ConfigManager):
    """Thin subclass so `isinstance(obj, Config)` checks still pass."""

    # Legacy attribute expected by some scripts
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 