"""Systems layer: decoupled behavioral subsystems.

Each system implements one concern (needs, movement, economy, etc.)
and communicates exclusively through domain events. Systems must not
import or call each other directly.
"""

from __future__ import annotations

from civitas.systems.actions import ActionConfig, ActionExecutor
from civitas.systems.birth import BirthConfig, BirthSystem
from civitas.systems.cities import CityConfig, CitySystem
from civitas.systems.death import DeathConfig, DeathSystem
from civitas.systems.economy import EconomyConfig, EconomySystem
from civitas.systems.energy import EnergyConfig, EnergySystem
from civitas.systems.families import FamilyConfig, FamilySystem
from civitas.systems.food import FoodConfig, FoodSystem
from civitas.systems.gathering import GatheringConfig, GatheringSystem
from civitas.systems.governments import GovernmentConfig, GovernmentSystem
from civitas.systems.institutions import InstitutionConfig, InstitutionSystem
from civitas.systems.laws import LawConfig, LawSystem
from civitas.systems.market import MarketConfig, MarketSystem
from civitas.systems.movement import MovementConfig, MovementSystem
from civitas.systems.needs import NEED_NAMES, NeedsConfig, NeedsSystem
from civitas.systems.networks import NetworkConfig, NetworkSystem
from civitas.systems.policy import PolicyConfig, UtilityPolicy
from civitas.systems.population import PopulationConfig, PopulationSystem
from civitas.systems.prices import PriceConfig, PriceSystem
from civitas.systems.production import ProductionConfig, ProductionSystem
from civitas.systems.relationships import RelationshipConfig, RelationshipSystem
from civitas.systems.reputation import ReputationConfig, ReputationSystem
from civitas.systems.taxes import TaxConfig, TaxSystem
from civitas.systems.trading import TradingConfig, TradingSystem
from civitas.systems.voting import VoteConfig, VoteSystem
from civitas.systems.water import WaterConfig, WaterSystem

__all__ = [
    "NEED_NAMES",
    "ActionConfig",
    "ActionExecutor",
    "BirthConfig",
    "BirthSystem",
    "CityConfig",
    "CitySystem",
    "DeathConfig",
    "DeathSystem",
    "EconomyConfig",
    "EconomySystem",
    "EnergyConfig",
    "EnergySystem",
    "FamilyConfig",
    "FamilySystem",
    "FoodConfig",
    "FoodSystem",
    "GatheringConfig",
    "GatheringSystem",
    "GovernmentConfig",
    "GovernmentSystem",
    "InstitutionConfig",
    "InstitutionSystem",
    "LawConfig",
    "LawSystem",
    "MarketConfig",
    "MarketSystem",
    "MovementConfig",
    "MovementSystem",
    "NeedsConfig",
    "NeedsSystem",
    "NetworkConfig",
    "NetworkSystem",
    "PolicyConfig",
    "PopulationConfig",
    "PopulationSystem",
    "PriceConfig",
    "PriceSystem",
    "ProductionConfig",
    "ProductionSystem",
    "RelationshipConfig",
    "RelationshipSystem",
    "ReputationConfig",
    "ReputationSystem",
    "TaxConfig",
    "TaxSystem",
    "TradingConfig",
    "TradingSystem",
    "UtilityPolicy",
    "VoteConfig",
    "VoteSystem",
    "WaterConfig",
    "WaterSystem",
]
