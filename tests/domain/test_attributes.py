"""Unit tests for agent attribute value objects."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    AgentId,
    Belief,
    Beliefs,
    Goal,
    GoalSet,
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
    Tick,
)


def test_personality_defaults_are_neutral() -> None:
    """Unspecified personality traits default to 0.5."""
    personality = Personality()
    assert personality.openness == 0.5
    assert personality.neuroticism == 0.5


def test_personality_rejects_out_of_range() -> None:
    """Trait values outside [0, 1] are invalid."""
    with pytest.raises(ValidationError):
        Personality(openness=1.5)


def test_needs_most_urgent_is_lowest_satisfaction() -> None:
    """most_urgent selects the lowest need; ties break by name."""
    needs = Needs(food=0.2, water=0.1, energy=0.4, social=0.8, safety=0.9)
    assert needs.most_urgent() == "water"
    tied = Needs(food=0.1, water=0.1, energy=1.0, social=1.0, safety=1.0)
    assert tied.most_urgent() == "food"


def test_inventory_add_and_remove_are_immutable() -> None:
    """Inventory updates return new instances and preserve stocks."""
    empty = Inventory()
    with_food = empty.add("food", 3)
    assert empty.quantity("food") == 0
    assert with_food.quantity("food") == 3
    reduced = with_food.remove("food", 1)
    assert reduced.quantity("food") == 2
    assert with_food.quantity("food") == 3


def test_inventory_remove_insufficient_raises() -> None:
    """Removing more than available is an error."""
    inv = Inventory(stacks=(ResourceStack(resource="water", quantity=1),))
    with pytest.raises(ValueError, match="insufficient water"):
        inv.remove("water", 2)


def test_inventory_rejects_duplicate_resources() -> None:
    """Duplicate resource stacks are invalid."""
    with pytest.raises(ValidationError):
        Inventory(
            stacks=(
                ResourceStack(resource="food", quantity=1),
                ResourceStack(resource="food", quantity=2),
            )
        )


def test_goal_set_highest_priority_prefers_earlier_on_ties() -> None:
    """Highest priority wins; earliest goal wins ties."""
    goals = GoalSet(
        goals=(
            Goal(kind="eat", priority=0.5),
            Goal(kind="drink", priority=0.9),
            Goal(kind="rest", priority=0.9),
        )
    )
    best = goals.highest_priority()
    assert best is not None
    assert best.kind == "drink"
    assert GoalSet().highest_priority() is None


def test_beliefs_confidence_lookup() -> None:
    """Belief confidence is retrievable by proposition."""
    beliefs = Beliefs(entries=(Belief(proposition="water_nearby", confidence=0.8),))
    assert beliefs.confidence_in("water_nearby") == 0.8
    assert beliefs.confidence_in("unknown") is None


def test_relationship_map_toward_lookup() -> None:
    """Relationships are keyed by the other agent's id."""
    other = AgentId(value=7)
    rel_map = RelationshipMap(
        bonds=(Relationship(other_id=other, affinity=0.25, trust=0.6),)
    )
    bond = rel_map.toward(other)
    assert bond is not None
    assert bond.trust == 0.6
    assert rel_map.toward(AgentId(value=1)) is None


def test_skills_level_defaults_to_zero() -> None:
    """Missing skills report level 0.0."""
    skills = Skills(entries=(Skill(name="farming", level=0.4),))
    assert skills.level("farming") == 0.4
    assert skills.level("mining") == 0.0


def test_knowledge_knows_and_rejects_blank_facts() -> None:
    """Knowledge membership works; blank facts are rejected."""
    knowledge = Knowledge(facts=frozenset({"fire", "wheel"}))
    assert knowledge.knows("fire")
    assert not knowledge.knows("agriculture")
    with pytest.raises(ValidationError):
        Knowledge(facts=frozenset({"  "}))


def test_memory_remember_evicts_fifo() -> None:
    """Memory truncates oldest records when over capacity."""
    memory = Memory(capacity=2)
    first = MemoryRecord(tick=Tick(value=1), kind="saw", content="tree")
    second = MemoryRecord(tick=Tick(value=2), kind="saw", content="river")
    third = MemoryRecord(tick=Tick(value=3), kind="saw", content="fire")
    filled = memory.remember(first).remember(second).remember(third)
    assert len(filled.records) == 2
    assert filled.records[0] == second
    assert filled.records[1] == third
