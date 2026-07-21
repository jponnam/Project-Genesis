"""Systems layer: decoupled behavioral subsystems.

Each system implements one concern (needs, movement, economy, etc.)
and communicates exclusively through domain events. Systems must not
import or call each other directly.
"""

from __future__ import annotations

from civitas.systems.actions import ActionConfig, ActionExecutor
from civitas.systems.movement import MovementConfig, MovementSystem
from civitas.systems.needs import NEED_NAMES, NeedsConfig, NeedsSystem
from civitas.systems.policy import PolicyConfig, UtilityPolicy

__all__ = [
    "NEED_NAMES",
    "ActionConfig",
    "ActionExecutor",
    "MovementConfig",
    "MovementSystem",
    "NeedsConfig",
    "NeedsSystem",
    "PolicyConfig",
    "UtilityPolicy",
]
