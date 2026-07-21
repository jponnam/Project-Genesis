"""Systems layer: decoupled behavioral subsystems.

Each system implements one concern (needs, movement, economy, etc.)
and communicates exclusively through domain events. Systems must not
import or call each other directly.
"""

from __future__ import annotations

from civitas.systems.actions import ActionConfig, ActionExecutor
from civitas.systems.food import FoodConfig, FoodSystem
from civitas.systems.gathering import GatheringConfig, GatheringSystem
from civitas.systems.movement import MovementConfig, MovementSystem
from civitas.systems.needs import NEED_NAMES, NeedsConfig, NeedsSystem
from civitas.systems.policy import PolicyConfig, UtilityPolicy
from civitas.systems.water import WaterConfig, WaterSystem

__all__ = [
    "NEED_NAMES",
    "ActionConfig",
    "ActionExecutor",
    "FoodConfig",
    "FoodSystem",
    "GatheringConfig",
    "GatheringSystem",
    "MovementConfig",
    "MovementSystem",
    "NeedsConfig",
    "NeedsSystem",
    "PolicyConfig",
    "UtilityPolicy",
    "WaterConfig",
    "WaterSystem",
]
