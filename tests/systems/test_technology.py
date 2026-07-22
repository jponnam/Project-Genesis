"""Unit tests for the TechSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    SimulationConfig,
    TechnologiesObserved,
    Technology,
    TechnologyKind,
    World,
)
from civitas.engine import EventBus, WorldFactory
from civitas.systems import TechConfig, TechSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one technology census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = TechSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, TechnologiesObserved)]
    assert len(events) == 1
    assert events[0].technology_count == 21
    assert events[0].discovered_count == 1
    assert events[0].discovered_fire_count == 1
    assert events[0].discovered_pottery_count == 0
    assert events[0].discovered_irrigation_count == 0
    assert events[0].discovered_metallurgy_count == 0
    assert events[0].discovered_writing_count == 0
    assert events[0].discovered_mathematics_count == 0
    assert events[0].discovered_astronomy_count == 0
    assert events[0].discovered_philosophy_count == 0
    assert events[0].discovered_logic_count == 0
    assert events[0].discovered_rhetoric_count == 0
    assert events[0].discovered_medicine_count == 0
    assert events[0].discovered_anatomy_count == 0
    assert events[0].discovered_hygiene_count == 0
    assert events[0].discovered_engineering_count == 0
    assert events[0].discovered_architecture_count == 0
    assert events[0].discovered_surveying_count == 0
    assert events[0].discovered_navigation_count == 0
    assert events[0].discovered_cartography_count == 0
    assert events[0].discovered_seafaring_count == 0
    assert events[0].discovered_agriculture_count == 0
    assert events[0].discovered_crop_rotation_count == 0
    assert events[0].locked_count == 19
    assert events[0].researchable_count == 1


def test_observe_can_suppress_events() -> None:
    """TechConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=(
            Technology.create(0, "Fire", TechnologyKind.FIRE, discovered=True),
        ),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    TechSystem(TechConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_system_wrappers_create_and_discover() -> None:
    """System wrappers apply legal technology mutations."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    system = TechSystem()
    created = system.create(
        world,
        Technology.create(0, "Pottery", TechnologyKind.POTTERY),
    )
    assert created.technology_by_id(0) is not None
    discovered = system.discover(created, 0)
    assert discovered.technologies[0].discovered is True
