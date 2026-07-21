"""Agent aggregate root for Civitas Lab.

An ``Agent`` composes identity and attribute value objects. Systems never
mutate an agent in place; they replace fields via ``model_copy`` when
applying domain events (event system arrives in a later milestone).
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.attributes import (
    AgentStatus,
    Beliefs,
    GoalSet,
    Health,
    Inventory,
    Knowledge,
    Memory,
    Needs,
    Personality,
    RelationshipMap,
    Skills,
)
from civitas.domain.ids import AgentId, LocationId
from civitas.domain.time import Tick
from civitas.domain.types import NonEmptyStr, NonNegativeInt


class AgentIdentity(BaseModel):
    """Stable identity attributes for an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    agent_id: AgentId
    name: NonEmptyStr
    birth_tick: Tick = Field(default_factory=Tick)


class Agent(BaseModel):
    """Autonomous agent aggregate used throughout the simulation.

    Attributes mirror the Phase 1 research contract: identity, personality,
    inventory, needs, goals, beliefs, relationships, location, money,
    skills, knowledge, memory, health, and status.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    identity: AgentIdentity
    personality: Personality = Field(default_factory=Personality)
    inventory: Inventory = Field(default_factory=Inventory)
    needs: Needs = Field(default_factory=Needs)
    goals: GoalSet = Field(default_factory=GoalSet)
    beliefs: Beliefs = Field(default_factory=Beliefs)
    relationships: RelationshipMap = Field(default_factory=RelationshipMap)
    location_id: LocationId
    money: NonNegativeInt = 0
    skills: Skills = Field(default_factory=Skills)
    knowledge: Knowledge = Field(default_factory=Knowledge)
    memory: Memory = Field(default_factory=Memory)
    health: Health = Field(default_factory=Health)
    status: AgentStatus = AgentStatus.ALIVE

    @model_validator(mode="after")
    def dead_agents_have_zero_vitality(self) -> Self:
        """Enforce consistency between status and vitality."""
        if self.status == AgentStatus.DEAD and self.health.vitality != 0.0:
            msg = "dead agents must have vitality 0.0"
            raise ValueError(msg)
        return self

    @property
    def agent_id(self) -> AgentId:
        """Shorthand for ``identity.agent_id``."""
        return self.identity.agent_id

    @property
    def name(self) -> str:
        """Shorthand for ``identity.name``."""
        return self.identity.name

    def is_alive(self) -> bool:
        """Return True when the agent can act in the simulation."""
        return self.status == AgentStatus.ALIVE and self.health.vitality > 0.0

    @classmethod
    def create(
        cls,
        agent_id: int,
        name: str,
        location_id: int = 0,
        *,
        money: int = 0,
        birth_tick: int = 0,
        personality: Personality | None = None,
        needs: Needs | None = None,
    ) -> Agent:
        """Construct a living agent with validated identifiers.

        Optional personality/needs default to neutral/satisfied baselines
        suitable for seeded world construction.
        """
        return cls(
            identity=AgentIdentity(
                agent_id=AgentId(value=agent_id),
                name=name,
                birth_tick=Tick(value=birth_tick),
            ),
            location_id=LocationId(value=location_id),
            money=money,
            personality=personality if personality is not None else Personality(),
            needs=needs if needs is not None else Needs(),
        )
