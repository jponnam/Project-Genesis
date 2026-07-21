"""Systems layer: decoupled behavioral subsystems.

Each system implements one concern (needs, movement, economy, etc.)
and communicates exclusively through domain events. Systems must not
import or call each other directly.
"""

from __future__ import annotations

from civitas.systems.needs import NEED_NAMES, NeedsConfig, NeedsSystem, clamp_unit

__all__ = [
    "NEED_NAMES",
    "NeedsConfig",
    "NeedsSystem",
    "clamp_unit",
]
