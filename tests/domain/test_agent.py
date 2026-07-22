"""Unit tests for the Agent aggregate."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    Agent,
    AgentId,
    AgentIdentity,
    AgentStatus,
    Health,
    LocationId,
    Needs,
    Personality,
    Tick,
)


def test_agent_create_defaults() -> None:
    """Agent.create builds a living agent with baseline attributes."""
    agent = Agent.create(agent_id=1, name="Ada", location_id=0, money=10)
    assert agent.agent_id == AgentId(value=1)
    assert agent.name == "Ada"
    assert agent.location_id == LocationId(value=0)
    assert agent.money == 10
    assert agent.status == AgentStatus.ALIVE
    assert agent.is_alive()
    assert agent.parent_id is None
    assert agent.needs.food == 1.0
    assert agent.personality.openness == 0.5
    assert agent.inventory.stacks == ()
    assert agent.memory.records == ()


def test_agent_create_accepts_parent_id() -> None:
    """Born agents may record a parent id on identity."""
    agent = Agent.create(agent_id=2, name="Bea", parent_id=1)
    assert agent.parent_id == AgentId(value=1)
    assert agent.identity.parent_id == AgentId(value=1)


def test_agent_is_frozen() -> None:
    """Agents cannot be mutated in place."""
    agent = Agent.create(agent_id=2, name="Bob")
    with pytest.raises(ValidationError):
        agent.money = 99  # type: ignore[misc]


def test_agent_is_alive_requires_vitality() -> None:
    """Zero vitality means the agent cannot act even if marked alive."""
    agent = Agent.create(agent_id=3, name="Cara")
    weak = agent.model_copy(update={"health": Health(vitality=0.0)})
    assert weak.status == AgentStatus.ALIVE
    assert not weak.is_alive()


def test_dead_agent_requires_zero_vitality() -> None:
    """DEAD status is inconsistent with positive vitality."""
    with pytest.raises(ValidationError, match=r"vitality 0\.0"):
        Agent(
            identity=AgentIdentity(
                agent_id=AgentId(value=4),
                name="Dana",
                birth_tick=Tick(value=0),
            ),
            location_id=LocationId(value=0),
            status=AgentStatus.DEAD,
            health=Health(vitality=0.5),
        )


def test_dead_agent_with_zero_vitality_is_valid() -> None:
    """A properly marked dead agent validates and is not alive."""
    agent = Agent(
        identity=AgentIdentity(agent_id=AgentId(value=5), name="Eve"),
        location_id=LocationId(value=1),
        status=AgentStatus.DEAD,
        health=Health(vitality=0.0),
    )
    assert not agent.is_alive()


def test_agent_accepts_custom_personality_and_needs() -> None:
    """create() forwards optional personality and needs."""
    personality = Personality(extraversion=0.9, agreeableness=0.1)
    needs = Needs(food=0.2, water=0.3, energy=0.4, social=0.5, safety=0.6)
    agent = Agent.create(
        agent_id=6,
        name="Finn",
        personality=personality,
        needs=needs,
        birth_tick=3,
    )
    assert agent.personality.extraversion == 0.9
    assert agent.needs.most_urgent() == "food"
    assert agent.identity.birth_tick == Tick(value=3)


def test_identical_agents_compare_equal() -> None:
    """Value equality holds for identically constructed agents."""
    left = Agent.create(agent_id=7, name="Gus", money=5)
    right = Agent.create(agent_id=7, name="Gus", money=5)
    assert left == right
