"""Unit tests for the NeedsSystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    Agent,
    AgentStatus,
    Health,
    NeedDecayed,
    Needs,
    SimulationConfig,
    World,
    clamp_unit,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import NEED_NAMES, NeedsConfig, NeedsSystem


def _world_with_needs(*needs_list: Needs) -> World:
    agents = tuple(
        Agent.create(agent_id=index, name=f"Agent-{index}", needs=needs)
        for index, needs in enumerate(needs_list)
    )
    config = SimulationConfig(agent_count=len(agents), seed=1, ticks=10)
    return World(config=config, agents=agents)


def test_clamp_unit_bounds_and_rounding() -> None:
    """clamp_unit confines values to [0, 1] with stable rounding."""
    assert clamp_unit(-0.1) == 0.0
    assert clamp_unit(1.2) == 1.0
    assert clamp_unit(0.1234564) == 0.123456


def test_apply_decay_reduces_needs_by_configured_rates() -> None:
    """One decay tick subtracts each configured rate."""
    config = NeedsConfig(
        food=0.02,
        water=0.03,
        energy=0.025,
        social=0.01,
        safety=0.005,
    )
    system = NeedsSystem(config)
    world = _world_with_needs(Needs())
    updated = system.apply_decay(world)
    needs = updated.agents[0].needs
    assert needs.food == pytest.approx(0.98)
    assert needs.water == pytest.approx(0.97)
    assert needs.energy == pytest.approx(0.975)
    assert needs.social == pytest.approx(0.99)
    assert needs.safety == pytest.approx(0.995)


def test_apply_decay_clamps_at_zero() -> None:
    """Needs never fall below 0.0."""
    system = NeedsSystem(
        NeedsConfig(food=0.5, water=0.5, energy=0.5, social=0.5, safety=0.5)
    )
    world = _world_with_needs(
        Needs(food=0.2, water=0.2, energy=0.2, social=0.2, safety=0.2)
    )
    updated = system.apply_decay(world)
    assert updated.agents[0].needs == Needs(
        food=0.0,
        water=0.0,
        energy=0.0,
        social=0.0,
        safety=0.0,
    )


def test_apply_decay_skips_dead_agents() -> None:
    """Dead agents are not decayed."""
    living = Agent.create(agent_id=0, name="A")
    dead = Agent.create(agent_id=1, name="B").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = World(
        config=SimulationConfig(agent_count=2, seed=1),
        agents=(living, dead),
    )
    updated = NeedsSystem().apply_decay(world)
    assert updated.agents[0].needs.food < 1.0
    assert updated.agents[1].needs == Needs()


def test_apply_decay_emits_events_in_deterministic_order() -> None:
    """NeedDecayed events follow agent-id then need-name order."""
    bus = EventBus()
    world = _world_with_needs(Needs(), Needs())
    NeedsSystem().apply_decay(world, bus=bus)
    events = [event for event in bus.history if isinstance(event, NeedDecayed)]
    assert len(events) == 2 * len(NEED_NAMES)
    assert [event.agent_id.value for event in events[:5]] == [0, 0, 0, 0, 0]
    assert [event.need for event in events[:5]] == list(NEED_NAMES)
    assert [event.agent_id.value for event in events[5:10]] == [1, 1, 1, 1, 1]


def test_apply_decay_is_deterministic() -> None:
    """Identical worlds decay identically across runs."""
    system = NeedsSystem()
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=5))
    first = system.apply_decay(world)
    second = system.apply_decay(world)
    assert first == second


def test_satisfy_increases_need_and_emits_event() -> None:
    """satisfy raises a need and publishes NeedDecayed when changed."""
    bus = EventBus()
    world = _world_with_needs(Needs(food=0.4))
    updated = NeedsSystem().satisfy(world, 0, "food", 0.2, bus=bus)
    assert updated.agents[0].needs.food == pytest.approx(0.6)
    assert len(bus.history) == 1
    event = bus.history[0]
    assert isinstance(event, NeedDecayed)
    assert event.previous == 0.4
    assert event.current == pytest.approx(0.6)


def test_satisfy_clamps_at_one() -> None:
    """Satisfaction cannot exceed 1.0."""
    world = _world_with_needs(Needs(water=0.9))
    updated = NeedsSystem().satisfy(world, 0, "water", 0.5)
    assert updated.agents[0].needs.water == 1.0


def test_satisfy_rejects_invalid_inputs() -> None:
    """Unknown needs, non-positive amounts, and missing agents error."""
    system = NeedsSystem()
    world = _world_with_needs(Needs())
    with pytest.raises(ValueError, match="positive"):
        system.satisfy(world, 0, "food", 0.0)
    with pytest.raises(ValueError, match="unknown need"):
        system.satisfy(world, 0, "fame", 0.1)
    with pytest.raises(ValueError, match="not found"):
        system.satisfy(world, 9, "food", 0.1)


def test_needs_config_rate_for() -> None:
    """rate_for returns configured rates and rejects unknowns."""
    config = NeedsConfig(food=0.1)
    assert config.rate_for("food") == 0.1
    with pytest.raises(ValueError, match="unknown need"):
        config.rate_for("fame")
