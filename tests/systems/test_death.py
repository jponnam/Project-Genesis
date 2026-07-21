"""Unit tests for the DeathSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentDied,
    AgentStatus,
    Needs,
    SimulationConfig,
    Tick,
    World,
)
from civitas.engine import EventBus
from civitas.systems import DeathConfig, DeathSystem


def _world(*agents: Agent, tick: int = 5) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        tick=Tick(value=tick),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_apply_deaths_emits_agent_died_and_marks_dead() -> None:
    """Eligible agents die in id order and emit AgentDied."""
    living = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.0, water=0.5, energy=0.5),
    )
    safe = Agent.create(
        agent_id=1,
        name="B",
        needs=Needs(food=0.5, water=0.5, energy=0.5),
    )
    bus = EventBus()
    updated = DeathSystem().apply_deaths(_world(living, safe), bus=bus)
    assert updated.agent_by_id(0) is not None
    assert updated.agent_by_id(0).status == AgentStatus.DEAD
    assert updated.agent_by_id(1) is not None
    assert updated.agent_by_id(1).is_alive()
    events = [event for event in bus.history if isinstance(event, AgentDied)]
    assert len(events) == 1
    assert events[0].agent_id.value == 0
    assert events[0].cause == "starvation"
    assert events[0].name == "A"


def test_apply_deaths_can_be_disabled() -> None:
    """DeathConfig.enabled=False skips all deaths."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.0, water=0.0, energy=0.0),
    )
    world = _world(agent)
    bus = EventBus()
    updated = DeathSystem(DeathConfig(enabled=False)).apply_deaths(world, bus=bus)
    assert updated == world
    assert bus.history == ()


def test_apply_deaths_old_age() -> None:
    """Configured max age kills agents that reach the limit."""
    agent = Agent.create(agent_id=0, name="A", birth_tick=0)
    bus = EventBus()
    updated = DeathSystem(DeathConfig(max_age_ticks=5)).apply_deaths(
        _world(agent, tick=5),
        bus=bus,
    )
    assert updated.alive_agents() == ()
    events = [event for event in bus.history if isinstance(event, AgentDied)]
    assert events[0].cause == "old_age"


def test_should_die_delegates_to_domain_rules() -> None:
    """System.should_die mirrors domain eligibility for an agent id."""
    world = _world(
        Agent.create(
            agent_id=0,
            name="A",
            needs=Needs(food=0.0, water=1.0, energy=1.0),
        )
    )
    system = DeathSystem()
    assert system.should_die(world, 0) is True
    assert system.should_die(world, 99) is False
