"""Systems layer: decoupled behavioral subsystems.

Each system implements one concern (needs, movement, economy, etc.)
and communicates exclusively through domain events. Systems must not
import or call each other directly.
"""

from __future__ import annotations

from civitas.systems.actions import ActionConfig, ActionExecutor
from civitas.systems.birth import BirthConfig, BirthSystem
from civitas.systems.death import DeathConfig, DeathSystem
from civitas.systems.economy import EconomyConfig, EconomySystem
from civitas.systems.energy import EnergyConfig, EnergySystem
from civitas.systems.food import FoodConfig, FoodSystem
from civitas.systems.gathering import GatheringConfig, GatheringSystem
from civitas.systems.market import MarketConfig, MarketSystem
from civitas.systems.movement import MovementConfig, MovementSystem
from civitas.systems.needs import NEED_NAMES, NeedsConfig, NeedsSystem
from civitas.systems.policy import PolicyConfig, UtilityPolicy
from civitas.systems.population import PopulationConfig, PopulationSystem
from civitas.systems.trading import TradingConfig, TradingSystem
from civitas.systems.water import WaterConfig, WaterSystem

__all__ = [
    "NEED_NAMES",
    "ActionConfig",
    "ActionExecutor",
    "BirthConfig",
    "BirthSystem",
    "DeathConfig",
    "DeathSystem",
    "EconomyConfig",
    "EconomySystem",
    "EnergyConfig",
    "EnergySystem",
    "FoodConfig",
    "FoodSystem",
    "GatheringConfig",
    "GatheringSystem",
    "MarketConfig",
    "MarketSystem",
    "MovementConfig",
    "MovementSystem",
    "NeedsConfig",
    "NeedsSystem",
    "PolicyConfig",
    "PopulationConfig",
    "PopulationSystem",
    "TradingConfig",
    "TradingSystem",
    "UtilityPolicy",
    "WaterConfig",
    "WaterSystem",
]
