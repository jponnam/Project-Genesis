"""Unit tests for the MovementSystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    BRIDGE_MOVE_ENERGY_DISCOUNT,
    BUILDING_CODES_MOVE_ENERGY_DISCOUNT,
    CAMP_LOCATION,
    DEFAULT_MOVE_ENERGY_COST,
    PASSAGE_MOVE_ENERGY_DISCOUNT,
    Agent,
    AgentMoved,
    AgentStatus,
    City,
    CityKind,
    Government,
    Health,
    Infrastructure,
    InfrastructureKind,
    Law,
    LawKind,
    Location,
    LocationKind,
    NeedDecayed,
    Needs,
    SimulationConfig,
    World,
    default_world_map,
)
from civitas.engine import EventBus
from civitas.systems import MovementConfig, MovementSystem


def _world_with_neighbor(*, capacity: int = 8) -> World:
    plain = Location.create(
        1, "Plain", 1, 0, kind=LocationKind.PLAIN, capacity=capacity
    )
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )


def test_move_to_emits_agent_moved_and_energy_decay() -> None:
    """Successful move publishes AgentMoved and energy NeedDecayed."""
    world = _world_with_neighbor()
    bus = EventBus()
    updated = MovementSystem().move_to(world, 0, 1, bus=bus)
    assert updated.agents[0].location_id.value == 1
    assert updated.agents[0].needs.energy == pytest.approx(0.95)
    moved = [event for event in bus.history if isinstance(event, AgentMoved)]
    assert len(moved) == 1
    assert moved[0].from_location_id.value == 0
    assert moved[0].to_location_id.value == 1
    assert any(
        isinstance(event, NeedDecayed) and event.need == "energy"
        for event in bus.history
    )


def test_move_to_uses_building_codes_discount() -> None:
    """MOVE spends the effective energy cost for building-code subjects."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    agent = Agent.create(
        agent_id=0,
        name="A",
        location_id=0,
        needs=Needs(food=1.0, water=1.0, energy=0.04, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Building Codes", LawKind.BUILDING_CODES),),
        agents=(agent,),
    )
    expected_cost = DEFAULT_MOVE_ENERGY_COST - BUILDING_CODES_MOVE_ENERGY_DISCOUNT
    system = MovementSystem()
    assert system.can_move(world, 0, 1) is True
    updated = system.move_to(world, 0, 1)
    assert updated.agents[0].location_id.value == 1
    assert updated.agents[0].needs.energy == pytest.approx(0.04 - expected_cost)


def test_move_to_uses_passage_discount() -> None:
    """MOVE spends the effective energy cost for passage subjects."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    agent = Agent.create(
        agent_id=0,
        name="A",
        location_id=0,
        needs=Needs(food=1.0, water=1.0, energy=0.04, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        laws=(Law.create(0, 0, "Camp Passage", LawKind.PASSAGE),),
        agents=(agent,),
    )
    expected_cost = DEFAULT_MOVE_ENERGY_COST - PASSAGE_MOVE_ENERGY_DISCOUNT
    system = MovementSystem()
    assert system.can_move(world, 0, 1) is True
    updated = system.move_to(world, 0, 1)
    assert updated.agents[0].location_id.value == 1
    assert updated.agents[0].needs.energy == pytest.approx(0.04 - expected_cost)


def test_move_to_uses_bridge_discount() -> None:
    """MOVE spends the effective energy cost at an active bridge seat."""
    plain = Location.create(1, "Plain", 1, 0, kind=LocationKind.PLAIN)
    agent = Agent.create(
        agent_id=0,
        name="A",
        location_id=0,
        needs=Needs(food=1.0, water=1.0, energy=0.04, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION, plain),
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(0, 0, 0, 0, "Camp Bridge", InfrastructureKind.BRIDGE),
        ),
        agents=(agent,),
    )
    expected_cost = DEFAULT_MOVE_ENERGY_COST - BRIDGE_MOVE_ENERGY_DISCOUNT
    system = MovementSystem()
    assert system.can_move(world, 0, 1) is True
    updated = system.move_to(world, 0, 1)
    assert updated.agents[0].location_id.value == 1
    assert updated.agents[0].needs.energy == pytest.approx(0.04 - expected_cost)


def test_move_to_illegal_destination_is_noop() -> None:
    """Non-adjacent destinations leave the world unchanged."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    bus = EventBus()
    updated = MovementSystem().move_to(world, 0, 8, bus=bus)
    assert updated == world
    assert bus.history == ()


def test_move_to_respects_capacity() -> None:
    """A full destination cannot be entered."""
    plain = Location.create(1, "Plain", 1, 0, capacity=1)
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        locations=(CAMP_LOCATION, plain),
        agents=(
            Agent.create(agent_id=0, name="A", location_id=1),
            Agent.create(agent_id=1, name="B", location_id=0),
        ),
    )
    assert MovementSystem().can_move(world, 1, 1) is False
    updated = MovementSystem().move_to(world, 1, 1)
    assert updated.agents[1].location_id.value == 0


def test_move_requires_energy() -> None:
    """Agents below the energy cost cannot move."""
    world = _world_with_neighbor()
    tired = world.with_agent(
        world.agents[0].model_copy(
            update={
                "needs": Needs(food=1.0, water=1.0, energy=0.01, social=1.0, safety=1.0)
            }
        )
    )
    system = MovementSystem(MovementConfig(energy_cost=0.05))
    assert system.can_move(tired, 0, 1) is False
    assert system.move_to(tired, 0, 1) == tired


def test_dead_agent_cannot_move() -> None:
    """Dead agents are rejected by can_move and move_to."""
    world = _world_with_neighbor()
    dead = world.with_agent(
        world.agents[0].model_copy(
            update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
        )
    )
    system = MovementSystem()
    assert system.can_move(dead, 0, 1) is False
    assert system.move_to(dead, 0, 1) == dead


def test_neighbors_are_stable() -> None:
    """neighbors returns ascending-id orthogonal cells."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map(),
        agents=(Agent.create(agent_id=0, name="A", location_id=0),),
    )
    ids = [loc.location_id.value for loc in MovementSystem().neighbors(world, 0)]
    assert ids == [1, 3]


def test_missing_agent_raises() -> None:
    """move_to raises when the agent id is absent."""
    world = _world_with_neighbor()
    with pytest.raises(ValueError, match="not found"):
        MovementSystem().move_to(world, 9, 1)
