"""Unit tests for the TaxSystem."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Government,
    Law,
    LawKind,
    SimulationConfig,
    TaxCollected,
    World,
    wealth_total,
)
from civitas.engine import EventBus
from civitas.systems import TaxConfig, TaxSystem


def _world(
    *agents: Agent,
    treasury: int = 0,
    governments: tuple[Government, ...] = (),
    laws: tuple[Law, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        laws=laws,
        agents=agents,
        treasury=treasury,
    )


def test_tax_system_emits_tax_collected_in_id_order() -> None:
    """Enabled levies emit one TaxCollected per payer with rising treasury."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=3),
        Agent.create(agent_id=1, name="B", money=2),
    )
    bus = EventBus()
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=1))
    updated = system.apply_taxes(world, bus=bus)
    assert updated.treasury == 2
    assert wealth_total(updated) == wealth_total(world) - 2
    events = [event for event in bus.history if isinstance(event, TaxCollected)]
    assert len(events) == 2
    assert events[0].agent_id.value == 0
    assert events[0].amount == 1
    assert events[0].treasury_after == 1
    assert events[0].government_id is None
    assert events[1].agent_id.value == 1
    assert events[1].treasury_after == 2
    assert events[1].government_id is None


def test_tax_system_disabled_is_noop() -> None:
    """Default disabled config leaves world and bus unchanged."""
    world = _world(Agent.create(agent_id=0, name="A", money=5))
    bus = EventBus()
    updated = TaxSystem().apply_taxes(world, bus=bus)
    assert updated == world
    assert bus.history == ()


def test_tax_system_can_suppress_events() -> None:
    """emit_events=False still collects money without publishing."""
    world = _world(Agent.create(agent_id=0, name="A", money=4))
    bus = EventBus()
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=1, emit_events=False))
    updated = system.apply_taxes(world, bus=bus)
    assert updated.treasury == 1
    assert bus.history == ()


def test_tax_system_accumulates_across_calls() -> None:
    """Repeated levies grow the treasury."""
    world = _world(Agent.create(agent_id=0, name="A", money=5))
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=2, rate_bps=0))
    world = system.apply_taxes(world)
    world = system.apply_taxes(world)
    assert world.treasury == 4
    agent = world.agent_by_id(0)
    assert agent is not None
    assert agent.money == 1


def test_tax_system_redirects_governed_collections() -> None:
    """Governed payers credit their government treasury."""
    government = Government.create(0, "Camp", 0, (0,))
    world = _world(
        Agent.create(agent_id=0, name="A", money=4),
        treasury=7,
        governments=(government,),
    )
    bus = EventBus()
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=1))
    updated = system.apply_taxes(world, bus=bus)
    assert updated.treasury == 7
    assert updated.government_by_id(0).treasury == 1  # type: ignore[union-attr]
    events = [event for event in bus.history if isinstance(event, TaxCollected)]
    assert len(events) == 1
    assert events[0].treasury_after == 1
    assert events[0].government_id == government.government_id


def test_tax_system_tax_due_uses_config() -> None:
    """tax_due mirrors collectable amounts under the active config."""
    world = _world(Agent.create(agent_id=0, name="A", money=100))
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=1, rate_bps=100))
    assert system.tax_due(world, 0) == 2
    assert system.tax_due(world, 9) == 0


def test_tax_system_uses_active_tax_schedule_law() -> None:
    """Active TAX_SCHEDULE overrides TaxConfig flat amount for subjects."""
    world = _world(
        Agent.create(agent_id=0, name="A", money=5),
        governments=(Government.create(0, "Camp", 0, (0,)),),
        laws=(Law.create(0, 0, "Heavy", LawKind.TAX_SCHEDULE, flat_amount=2),),
    )
    system = TaxSystem(TaxConfig(enabled=True, flat_amount=1))
    assert system.tax_due(world, 0) == 2
    updated = system.apply_taxes(world)
    assert updated.treasury == 0
    assert updated.government_by_id(0).treasury == 2  # type: ignore[union-attr]
    assert updated.agent_by_id(0).money == 3  # type: ignore[union-attr]
