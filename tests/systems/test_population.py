"""Unit tests for the PopulationSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    PopulationObserved,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import PopulationConfig, PopulationSystem


def test_observe_emits_population_observed_without_mutating_world() -> None:
    """observe publishes one census event and leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=4))
    bus = EventBus()
    updated = PopulationSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, PopulationObserved)]
    assert len(events) == 1
    assert events[0].initial_count == 4
    assert events[0].total == 4
    assert events[0].alive == 4
    assert events[0].dead == 0
    assert events[0].location_counts[0] == (0, 4)


def test_observe_can_suppress_events() -> None:
    """PopulationConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    PopulationSystem(PopulationConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_census_matches_domain_helper() -> None:
    """System.census delegates to the domain census helper."""
    world = WorldFactory().create(SimulationConfig(seed=7, agent_count=3))
    system = PopulationSystem()
    assert system.census(world) == system.census(world)
    assert system.census(world).total == 3
