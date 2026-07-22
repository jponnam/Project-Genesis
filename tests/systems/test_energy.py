"""Unit tests for the EnergySystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    BATHHOUSE_REST_RESTORE_BONUS,
    CAMP_FIRE,
    CAMP_FIRE_HEARTH,
    CAMP_LOCATION,
    DEFAULT_REST_RESTORE,
    FIRE_HEARTH_REST_BONUS,
    HOSPITAL_REST_RESTORE_BONUS,
    INFIRMARY_REST_RESTORE_BONUS,
    TEMPLE_REST_RESTORE_BONUS,
    Agent,
    City,
    CityKind,
    Government,
    Infrastructure,
    InfrastructureKind,
    Institution,
    InstitutionKind,
    NeedDecayed,
    Needs,
    SimulationConfig,
    World,
    default_world_map,
)
from civitas.engine import EventBus
from civitas.systems import EnergyConfig, EnergySystem


def _world_tired(energy: float = 0.5) -> World:
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=1.0, energy=energy, social=1.0, safety=1.0),
    )
    return World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        agents=(agent,),
    )


def test_rest_emits_energy_need_event() -> None:
    """Successful rest publishes energy NeedDecayed and restores energy."""
    world = _world_tired(0.5)
    bus = EventBus()
    updated = EnergySystem().rest(world, 0, bus=bus)
    assert updated.agents[0].needs.energy == pytest.approx(0.70)
    assert any(
        isinstance(event, NeedDecayed) and event.need == "energy"
        for event in bus.history
    )


def test_rest_when_full_is_noop() -> None:
    """Resting at full energy leaves the world unchanged."""
    world = _world_tired(1.0)
    bus = EventBus()
    system = EnergySystem()
    assert system.can_rest(world, 0) is False
    assert system.rest(world, 0, bus=bus) == world
    assert bus.history == ()


def test_energy_config_controls_restore() -> None:
    """EnergyConfig.restore is applied."""
    world = _world_tired(0.5)
    updated = EnergySystem(EnergyConfig(restore=0.4)).rest(world, 0)
    assert updated.agents[0].needs.energy == pytest.approx(0.9)


def test_missing_agent_raises() -> None:
    """rest raises when the agent id is absent."""
    world = _world_tired()
    with pytest.raises(ValueError, match="not found"):
        EnergySystem().rest(world, 9)


def test_rest_applies_temple_and_fire_hearth_bonuses() -> None:
    """EnergySystem.rest passes the agent so temple seat bonus stacks with fire."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=1.0, energy=0.5, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Temple", InstitutionKind.TEMPLE),
        ),
        technologies=(CAMP_FIRE,),
        innovations=(CAMP_FIRE_HEARTH,),
        agents=(agent,),
    )
    updated = EnergySystem().rest(world, 0)
    assert updated.agents[0].needs.energy == pytest.approx(
        0.5 + DEFAULT_REST_RESTORE + FIRE_HEARTH_REST_BONUS + TEMPLE_REST_RESTORE_BONUS
    )


def test_rest_applies_hospital_bonus() -> None:
    """EnergySystem.rest includes the hospital seat bonus."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=1.0, energy=0.5, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        institutions=(
            Institution.create(0, 0, 0, "Camp Hospital", InstitutionKind.HOSPITAL),
        ),
        agents=(agent,),
    )
    updated = EnergySystem().rest(world, 0)
    assert updated.agents[0].needs.energy == pytest.approx(
        0.5 + DEFAULT_REST_RESTORE + HOSPITAL_REST_RESTORE_BONUS
    )


def test_rest_applies_infirmary_bonus() -> None:
    """EnergySystem.rest includes the infirmary city seat bonus."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        location_id=1,
        needs=Needs(food=1.0, water=1.0, energy=0.5, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=default_world_map()[:2],
        governments=(Government.create(0, "Camp", 0, (0, 1)),),
        cities=(
            City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),
            City.create(1, 0, 1, "Camp Infirmary", CityKind.INFIRMARY),
        ),
        agents=(agent,),
    )
    updated = EnergySystem().rest(world, 0)
    assert updated.agents[0].needs.energy == pytest.approx(
        0.5 + DEFAULT_REST_RESTORE + INFIRMARY_REST_RESTORE_BONUS
    )


def test_rest_applies_bathhouse_bonus() -> None:
    """EnergySystem.rest includes the bathhouse infrastructure seat bonus."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=1.0, energy=0.5, social=1.0, safety=1.0),
    )
    world = World(
        config=SimulationConfig(agent_count=1, seed=1),
        locations=(CAMP_LOCATION,),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        cities=(City.create(0, 0, 0, "Camp", CityKind.SETTLEMENT, is_capital=True),),
        infrastructure=(
            Infrastructure.create(
                0, 0, 0, 0, "Camp Bathhouse", InfrastructureKind.BATHHOUSE
            ),
        ),
        agents=(agent,),
    )
    updated = EnergySystem().rest(world, 0)
    assert updated.agents[0].needs.energy == pytest.approx(
        0.5 + DEFAULT_REST_RESTORE + BATHHOUSE_REST_RESTORE_BONUS
    )
