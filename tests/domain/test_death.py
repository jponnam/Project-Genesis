"""Unit tests for domain death helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    Agent,
    AgentStatus,
    DeathCause,
    Health,
    Needs,
    apply_death,
    death_cause,
    should_die,
)


def test_death_cause_priority_and_thresholds() -> None:
    """Starvation wins over other concurrent causes; healthy agents live."""
    healthy = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.5, water=0.5, energy=0.5),
    )
    assert death_cause(healthy, current_tick=10) is None
    assert should_die(healthy, current_tick=10) is False

    starving = healthy.model_copy(
        update={"needs": Needs(food=0.0, water=0.0, energy=0.0)}
    )
    assert death_cause(starving, current_tick=10) == DeathCause.STARVATION

    thirsty = healthy.model_copy(
        update={"needs": Needs(food=0.5, water=0.0, energy=0.0)}
    )
    assert death_cause(thirsty, current_tick=10) == DeathCause.DEHYDRATION

    tired = healthy.model_copy(update={"needs": Needs(food=0.5, water=0.5, energy=0.0)})
    assert death_cause(tired, current_tick=10) == DeathCause.EXHAUSTION


def test_death_cause_old_age() -> None:
    """Optional max age kills living agents that reach the limit."""
    agent = Agent.create(agent_id=0, name="A", birth_tick=0)
    assert death_cause(agent, current_tick=9, max_age_ticks=10) is None
    assert death_cause(agent, current_tick=10, max_age_ticks=10) == DeathCause.OLD_AGE


def test_death_cause_skips_already_dead() -> None:
    """Already-dead agents never receive a new cause."""
    dead = Agent.create(agent_id=0, name="A").model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert death_cause(dead, current_tick=100, max_age_ticks=1) is None
    assert apply_death(dead) is None


def test_apply_death_marks_status_and_vitality() -> None:
    """apply_death flips lifecycle fields and preserves identity/location."""
    agent = Agent.create(agent_id=3, name="A", location_id=0, money=12)
    dead = apply_death(agent)
    assert dead is not None
    assert dead.status == AgentStatus.DEAD
    assert dead.health.vitality == 0.0
    assert dead.is_alive() is False
    assert dead.agent_id == agent.agent_id
    assert dead.location_id == agent.location_id
    assert dead.money == 12


def test_death_cause_rejects_negative_thresholds() -> None:
    """Negative need thresholds are rejected."""
    agent = Agent.create(agent_id=0, name="A")
    with pytest.raises(ValueError, match="thresholds"):
        death_cause(agent, current_tick=1, food_threshold=-0.1)
