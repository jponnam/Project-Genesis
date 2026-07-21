"""Unit tests for the EnergySystem."""

from __future__ import annotations

import pytest

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    NeedDecayed,
    Needs,
    SimulationConfig,
    World,
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
