"""Composable agent attribute value objects.

Each model is immutable and independently validated. The ``Agent``
aggregate composes these parts; systems will later update them by
producing new aggregate instances from domain events.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from civitas.domain.ids import AgentId
from civitas.domain.time import Tick
from civitas.domain.types import (
    AffinityScore,
    NonEmptyStr,
    NonNegativeInt,
    PositiveInt,
    UnitInterval,
)

_FROZEN = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class AgentStatus(StrEnum):
    """Lifecycle status of an agent."""

    ALIVE = "alive"
    DEAD = "dead"


class Personality(BaseModel):
    """Big Five personality traits on the unit interval.

    Traits feed the utility policy (later milestone). Defaults are
    neutral (0.5) so an unspecified personality is well-defined.
    """

    model_config = _FROZEN

    openness: UnitInterval = 0.5
    conscientiousness: UnitInterval = 0.5
    extraversion: UnitInterval = 0.5
    agreeableness: UnitInterval = 0.5
    neuroticism: UnitInterval = 0.5


class Needs(BaseModel):
    """Homeostatic needs on the unit interval.

    ``1.0`` means fully satisfied; ``0.0`` means critically deprived.
    The needs system decays and restores these values each tick.
    """

    model_config = _FROZEN

    food: UnitInterval = 1.0
    water: UnitInterval = 1.0
    energy: UnitInterval = 1.0
    social: UnitInterval = 1.0
    safety: UnitInterval = 1.0

    def as_mapping(self) -> dict[str, float]:
        """Return need name → satisfaction for policy scoring."""
        return {
            "food": self.food,
            "water": self.water,
            "energy": self.energy,
            "social": self.social,
            "safety": self.safety,
        }

    def most_urgent(self) -> str:
        """Return the need with lowest satisfaction (ties: stable name order)."""
        items = self.as_mapping()
        return min(items, key=lambda name: (items[name], name))


class Health(BaseModel):
    """Physical vitality on the unit interval (``0.0`` = no vitality)."""

    model_config = _FROZEN

    vitality: UnitInterval = 1.0


class ResourceStack(BaseModel):
    """A single resource type and non-negative quantity."""

    model_config = _FROZEN

    resource: NonEmptyStr
    quantity: NonNegativeInt = 0


class Inventory(BaseModel):
    """Immutable resource stockpile for an agent."""

    model_config = _FROZEN

    stacks: tuple[ResourceStack, ...] = ()

    @model_validator(mode="after")
    def resources_must_be_unique(self) -> Self:
        """Reject inventories that list the same resource more than once."""
        names = [stack.resource for stack in self.stacks]
        if len(names) != len(set(names)):
            msg = "inventory resources must be unique"
            raise ValueError(msg)
        return self

    def quantity(self, resource: str) -> int:
        """Return on-hand quantity for ``resource`` (0 if absent)."""
        for stack in self.stacks:
            if stack.resource == resource:
                return stack.quantity
        return 0

    def add(self, resource: str, amount: int) -> Inventory:
        """Return a new inventory with ``amount`` added to ``resource``.

        Args:
            resource: Non-empty resource name.
            amount: Positive quantity to add.

        Raises:
            ValueError: If ``amount`` is not positive.
        """
        if amount <= 0:
            msg = f"add amount must be positive, got {amount}"
            raise ValueError(msg)
        current = self.quantity(resource)
        return self._with_quantity(resource, current + amount)

    def remove(self, resource: str, amount: int) -> Inventory:
        """Return a new inventory with ``amount`` removed from ``resource``.

        Raises:
            ValueError: If ``amount`` is not positive or stock is insufficient.
        """
        if amount <= 0:
            msg = f"remove amount must be positive, got {amount}"
            raise ValueError(msg)
        current = self.quantity(resource)
        if current < amount:
            msg = f"insufficient {resource}: have {current}, need {amount}"
            raise ValueError(msg)
        return self._with_quantity(resource, current - amount)

    def _with_quantity(self, resource: str, quantity: int) -> Inventory:
        updated: list[ResourceStack] = []
        found = False
        for stack in self.stacks:
            if stack.resource == resource:
                found = True
                if quantity > 0:
                    updated.append(ResourceStack(resource=resource, quantity=quantity))
            else:
                updated.append(stack)
        if not found and quantity > 0:
            updated.append(ResourceStack(resource=resource, quantity=quantity))
        updated.sort(key=lambda stack: stack.resource)
        return Inventory(stacks=tuple(updated))


class Goal(BaseModel):
    """A single prioritized objective pursued by an agent."""

    model_config = _FROZEN

    kind: NonEmptyStr
    priority: UnitInterval = 0.5
    target: str | None = None


class GoalSet(BaseModel):
    """Ordered collection of goals; priority selects among them."""

    model_config = _FROZEN

    goals: tuple[Goal, ...] = ()

    def highest_priority(self) -> Goal | None:
        """Return the highest-priority goal (ties: earliest in tuple)."""
        if not self.goals:
            return None
        best = self.goals[0]
        for goal in self.goals[1:]:
            if goal.priority > best.priority:
                best = goal
        return best


class Belief(BaseModel):
    """A proposition with a confidence score on the unit interval."""

    model_config = _FROZEN

    proposition: NonEmptyStr
    confidence: UnitInterval = 0.5


class Beliefs(BaseModel):
    """Immutable set of beliefs held by an agent."""

    model_config = _FROZEN

    entries: tuple[Belief, ...] = ()

    @model_validator(mode="after")
    def propositions_must_be_unique(self) -> Self:
        """Reject duplicate propositions."""
        props = [belief.proposition for belief in self.entries]
        if len(props) != len(set(props)):
            msg = "belief propositions must be unique"
            raise ValueError(msg)
        return self

    def confidence_in(self, proposition: str) -> float | None:
        """Return confidence for ``proposition``, or ``None`` if unknown."""
        for belief in self.entries:
            if belief.proposition == proposition:
                return belief.confidence
        return None


class Relationship(BaseModel):
    """Directed social bond toward another agent."""

    model_config = _FROZEN

    other_id: AgentId
    affinity: AffinityScore = 0.0
    trust: UnitInterval = 0.5


class RelationshipMap(BaseModel):
    """Immutable collection of directed relationships."""

    model_config = _FROZEN

    bonds: tuple[Relationship, ...] = ()

    @model_validator(mode="after")
    def others_must_be_unique(self) -> Self:
        """Reject multiple bonds to the same agent."""
        ids = [bond.other_id for bond in self.bonds]
        if len(ids) != len(set(ids)):
            msg = "relationship targets must be unique"
            raise ValueError(msg)
        return self

    def toward(self, other_id: AgentId) -> Relationship | None:
        """Return the bond toward ``other_id``, if any."""
        for bond in self.bonds:
            if bond.other_id == other_id:
                return bond
        return None


class Skill(BaseModel):
    """A named skill and proficiency on the unit interval."""

    model_config = _FROZEN

    name: NonEmptyStr
    level: UnitInterval = 0.0


class Skills(BaseModel):
    """Immutable skill profile."""

    model_config = _FROZEN

    entries: tuple[Skill, ...] = ()

    @model_validator(mode="after")
    def skill_names_must_be_unique(self) -> Self:
        """Reject duplicate skill names."""
        names = [skill.name for skill in self.entries]
        if len(names) != len(set(names)):
            msg = "skill names must be unique"
            raise ValueError(msg)
        return self

    def level(self, name: str) -> float:
        """Return proficiency for ``name`` (0.0 if absent)."""
        for skill in self.entries:
            if skill.name == name:
                return skill.level
        return 0.0


class Knowledge(BaseModel):
    """Immutable set of known facts (opaque strings for Phase 1)."""

    model_config = _FROZEN

    facts: frozenset[str] = Field(default_factory=frozenset)

    @field_validator("facts")
    @classmethod
    def facts_must_be_nonempty_strings(cls, value: frozenset[str]) -> frozenset[str]:
        """Reject blank facts."""
        for fact in value:
            if not fact.strip():
                msg = "knowledge facts must be non-blank"
                raise ValueError(msg)
        return value

    def knows(self, fact: str) -> bool:
        """Return whether ``fact`` is known."""
        return fact in self.facts


class MemoryRecord(BaseModel):
    """A single episodic memory entry anchored to a tick."""

    model_config = _FROZEN

    tick: Tick
    kind: NonEmptyStr
    content: NonEmptyStr


class Memory(BaseModel):
    """Bounded episodic memory with FIFO eviction."""

    model_config = _FROZEN

    records: tuple[MemoryRecord, ...] = ()
    capacity: PositiveInt = 100

    @model_validator(mode="after")
    def records_must_fit_capacity(self) -> Self:
        """Reject memories that already exceed capacity."""
        if len(self.records) > self.capacity:
            msg = (
                f"memory has {len(self.records)} records "
                f"but capacity is {self.capacity}"
            )
            raise ValueError(msg)
        return self

    def remember(self, record: MemoryRecord) -> Memory:
        """Append ``record``, evicting oldest entries if over capacity."""
        merged = [*self.records, record]
        if len(merged) > self.capacity:
            merged = merged[-self.capacity :]
        return Memory(records=tuple(merged), capacity=self.capacity)
