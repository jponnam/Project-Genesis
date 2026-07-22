"""Unit tests for the LawSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    Law,
    LawKind,
    LawsObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import LawConfig, LawSystem


def test_observe_emits_laws_observed_without_mutating_world() -> None:
    """observe publishes one law census and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = LawSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, LawsObserved)]
    assert len(events) == 1
    assert events[0].law_count == 1
    assert events[0].active_count == 1
    assert events[0].active_tax_schedule_count == 1


def test_observe_can_suppress_events() -> None:
    """LawConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=1),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    LawSystem(LawConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_system_wrappers_enact_and_repeal() -> None:
    """System wrappers apply legal statute mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = LawSystem()
    enacted = system.enact(
        world,
        Law.create(0, 0, "Poll", LawKind.TAX_SCHEDULE, flat_amount=2),
    )
    assert enacted.law_by_id(0) is not None
    repealed = system.repeal(enacted, 0)
    assert repealed.law_by_id(0).active is False  # type: ignore[union-attr]
