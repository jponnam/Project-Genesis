"""Domain layer: core models, value objects, and domain events.

This layer contains pure domain concepts with no I/O, no framework
coupling, and no dependency on engine or systems. All other layers
may depend on domain; domain depends on nothing inside Civitas Lab.
"""

from __future__ import annotations

from civitas.domain.actions import (
    ACTION_CATALOG,
    ACTION_NEED_TARGET,
    ACTION_RESOURCE,
    ActionChoice,
    ActionKind,
)
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
from civitas.domain.events import (
    ActionCompleted,
    ActionSelected,
    AgentSpawned,
    DomainEvent,
    NeedDecayed,
    ResourceConsumed,
    SimulationCompleted,
    SimulationStarted,
    TickCompleted,
    TickStarted,
    event_from_record,
)
from civitas.domain.ids import AgentId, LocationId
from civitas.domain.numeric import clamp_unit
from civitas.domain.time import Tick
from civitas.domain.world import World

__all__ = [
    "ACTION_CATALOG",
    "ACTION_NEED_TARGET",
    "ACTION_RESOURCE",
    "CANONICAL_SEED",
    "ActionChoice",
    "ActionCompleted",
    "ActionKind",
    "ActionSelected",
    "Agent",
    "AgentId",
    "AgentIdentity",
    "AgentSpawned",
    "AgentStatus",
    "Belief",
    "Beliefs",
    "DomainEvent",
    "Goal",
    "GoalSet",
    "Health",
    "Inventory",
    "Knowledge",
    "LocationId",
    "Memory",
    "MemoryRecord",
    "NeedDecayed",
    "Needs",
    "Personality",
    "Relationship",
    "RelationshipMap",
    "ResourceConsumed",
    "ResourceStack",
    "SimulationCompleted",
    "SimulationConfig",
    "SimulationStarted",
    "Skill",
    "Skills",
    "Tick",
    "TickCompleted",
    "TickStarted",
    "World",
    "clamp_unit",
    "event_from_record",
]
