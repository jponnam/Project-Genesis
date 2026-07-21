"""Domain layer: core models, value objects, and domain events.

This layer contains pure domain concepts with no I/O, no framework
coupling, and no dependency on engine or systems. All other layers
may depend on domain; domain depends on nothing inside Civitas Lab.
"""

from __future__ import annotations

from civitas.domain.agent import Agent, AgentIdentity
from civitas.domain.attributes import (
    AgentStatus,
    Belief,
    Beliefs,
    Goal,
    GoalSet,
    Health,
    Inventory,
    Knowledge,
    Memory,
    MemoryRecord,
    Needs,
    Personality,
    Relationship,
    RelationshipMap,
    ResourceStack,
    Skill,
    Skills,
)
from civitas.domain.config import CANONICAL_SEED, SimulationConfig
from civitas.domain.ids import AgentId, LocationId
from civitas.domain.time import Tick

__all__ = [
    "CANONICAL_SEED",
    "Agent",
    "AgentId",
    "AgentIdentity",
    "AgentStatus",
    "Belief",
    "Beliefs",
    "Goal",
    "GoalSet",
    "Health",
    "Inventory",
    "Knowledge",
    "LocationId",
    "Memory",
    "MemoryRecord",
    "Needs",
    "Personality",
    "Relationship",
    "RelationshipMap",
    "ResourceStack",
    "SimulationConfig",
    "Skill",
    "Skills",
    "Tick",
]
