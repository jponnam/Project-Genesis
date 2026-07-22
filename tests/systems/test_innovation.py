"""Unit tests for the InnovationSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    CAMP_POTTERY,
    CAMP_POTTERY_CRAFT,
    Agent,
    InnovationActivated,
    InnovationsObserved,
    SimulationConfig,
    World,
    default_innovations,
    default_technologies,
    discover_technology,
)
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import InnovationConfig, InnovationSystem


def test_observe_emits_without_mutating_world() -> None:
    """observe publishes one innovation census and leaves world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    bus = EventBus()
    updated = InnovationSystem().observe(world, bus=bus)
    assert updated == world
    events = [event for event in bus.history if isinstance(event, InnovationsObserved)]
    assert len(events) == 1
    assert events[0].innovation_count == 22
    assert events[0].active_count == 1
    assert events[0].active_fire_hearth_count == 1
    assert events[0].active_pottery_craft_count == 0
    assert events[0].active_irrigation_canal_count == 0
    assert events[0].active_forge_count == 0
    assert events[0].active_scribe_count == 0
    assert events[0].active_abacus_count == 0
    assert events[0].active_star_chart_count == 0
    assert events[0].active_dialectic_count == 0
    assert events[0].active_syllogism_count == 0
    assert events[0].active_oration_count == 0
    assert events[0].active_remedy_count == 0
    assert events[0].active_dissection_count == 0
    assert events[0].active_asepsis_count == 0
    assert events[0].active_pulley_count == 0
    assert events[0].active_blueprint_count == 0
    assert events[0].active_plumb_line_count == 0
    assert events[0].active_compass_count == 0
    assert events[0].active_map_count == 0
    assert events[0].active_sail_count == 0
    assert events[0].active_plow_count == 0
    assert events[0].active_fallow_count == 0
    assert events[0].active_coppice_count == 0


def test_observe_can_suppress_events() -> None:
    """InnovationConfig.emit_events=False skips publishing."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        innovations=default_innovations(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    bus = EventBus()
    InnovationSystem(InnovationConfig(emit_events=False)).observe(world, bus=bus)
    assert bus.history == ()


def test_apply_innovations_emits_activation() -> None:
    """apply_innovations activates pottery craft after discovery."""
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        innovations=default_innovations(),
        agents=(Agent.create(agent_id=0, name="A"),),
    )
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    bus = EventBus()
    updated = InnovationSystem().apply_innovations(discovered, bus=bus)
    craft = updated.innovation_by_id(CAMP_POTTERY_CRAFT.innovation_id)
    assert craft is not None
    assert craft.active is True
    activated = [
        event for event in bus.history if isinstance(event, InnovationActivated)
    ]
    assert len(activated) == 1
    assert activated[0].name == "Camp Pottery Craft"
    assert activated[0].kind == "pottery_craft"


def test_apply_innovations_can_be_disabled() -> None:
    """InnovationConfig.enabled=False leaves the world unchanged."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=2))
    discovered = discover_technology(world, CAMP_POTTERY.technology_id)
    assert discovered is not None
    bus = EventBus()
    updated = InnovationSystem(InnovationConfig(enabled=False)).apply_innovations(
        discovered, bus=bus
    )
    assert updated == discovered
    assert bus.history == ()


def test_engine_activates_pottery_craft_by_tick_ten() -> None:
    """Default research+innovation activates pottery craft on tick 10."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=10, agent_count=3))
    craft = result.world.innovation_by_id(1)
    assert craft is not None
    assert craft.active is True
    assert result.world.technologies[1].discovered is True
    activated = [
        event for event in result.events if isinstance(event, InnovationActivated)
    ]
    assert len(activated) == 1
    assert activated[0].tick.value == 10
