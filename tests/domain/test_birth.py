"""Unit tests for domain birth helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Health,
    Location,
    Needs,
    Personality,
    SimulationConfig,
    Tick,
    World,
    agent_age_ticks,
    apply_birth,
    can_birth,
    inherit_personality,
)


def _world(
    *agents: Agent,
    tick: int = 10,
    locations: tuple[Location, ...] | None = None,
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        tick=Tick(value=tick),
        locations=locations if locations is not None else (CAMP_LOCATION,),
        agents=agents,
    )


def test_agent_age_ticks() -> None:
    """Age is current tick minus birth tick."""
    agent = Agent.create(agent_id=0, name="A", birth_tick=3)
    assert agent_age_ticks(agent, 10) == 7


def test_inherit_personality_blends_toward_neutral() -> None:
    """Regression 0.5 moves traits halfway to 0.5."""
    parent = Personality(openness=1.0, neuroticism=0.0)
    child = inherit_personality(parent, regression=0.5)
    assert child.openness == pytest.approx(0.75)
    assert child.neuroticism == pytest.approx(0.25)
    assert child.extraversion == pytest.approx(0.5)


def test_inherit_personality_rejects_out_of_range_regression() -> None:
    """Regression outside [0, 1] is rejected."""
    with pytest.raises(ValueError, match="personality regression"):
        inherit_personality(Personality(), regression=1.5)


def test_can_birth_requires_age_needs_and_capacity() -> None:
    """Young, hungry, dead, or capacity-blocked parents cannot birth."""
    parent = Agent.create(
        agent_id=0,
        name="A",
        birth_tick=0,
        needs=Needs(food=0.9, water=0.9, energy=0.9),
    )
    world = _world(parent, tick=10)
    assert can_birth(world, parent) is True

    young = _world(parent, tick=5)
    assert can_birth(young, parent) is False

    hungry = parent.model_copy(update={"needs": Needs(food=0.1, water=0.9, energy=0.9)})
    assert can_birth(_world(hungry, tick=10), hungry) is False

    dead = parent.model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_birth(_world(dead, tick=10), dead) is False

    tiny = Location.create(0, "Tiny", 0, 0, capacity=1)
    assert can_birth(_world(parent, tick=10, locations=(tiny,)), parent) is False


def test_can_birth_respects_max_population() -> None:
    """A full population ceiling blocks birth."""
    parent = Agent.create(
        agent_id=0,
        name="A",
        birth_tick=0,
        needs=Needs(food=0.9, water=0.9, energy=0.9),
    )
    world = _world(parent, tick=10)
    assert can_birth(world, parent, max_population=1) is False
    assert can_birth(world, parent, max_population=2) is True


def test_apply_birth_spawns_child_and_costs_parent_energy() -> None:
    """Successful birth appends a child and deducts parent energy."""
    parent = Agent.create(
        agent_id=0,
        name="A",
        birth_tick=0,
        personality=Personality(openness=1.0),
        needs=Needs(food=0.9, water=0.9, energy=0.9),
    )
    world = _world(parent, tick=12)
    result = apply_birth(world, parent, parent_energy_cost=0.1)
    assert result is not None
    updated, child = result
    assert updated.population_size == 2
    assert child.agent_id.value == 1
    assert child.name == "Agent-1"
    assert child.identity.birth_tick.value == 12
    assert child.location_id == parent.location_id
    assert child.personality.openness == pytest.approx(0.75)
    assert updated.agent_by_id(0) is not None
    assert updated.agent_by_id(0).needs.energy == pytest.approx(0.8)


def test_apply_birth_returns_none_when_illegal() -> None:
    """Illegal births leave the world unchanged via None."""
    parent = Agent.create(agent_id=0, name="A", birth_tick=0)
    world = _world(parent, tick=1)
    assert apply_birth(world, parent, min_parent_age_ticks=10) is None
