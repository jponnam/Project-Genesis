"""Unit tests for domain energy helpers."""

from __future__ import annotations

import pytest

from civitas.domain import (
    Agent,
    AgentStatus,
    Health,
    Needs,
    apply_rest,
    can_rest,
    spend_energy,
)


def _tired(energy: float = 0.4) -> Agent:
    return Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=1.0, water=1.0, energy=energy, social=1.0, safety=1.0),
    )


def test_can_rest_requires_energy_below_full() -> None:
    """Fully rested agents cannot usefully rest."""
    assert can_rest(_tired(1.0)) is False
    assert can_rest(_tired(0.9)) is True


def test_apply_rest_restores_energy() -> None:
    """Resting raises energy satisfaction by the restore amount."""
    updated = apply_rest(_tired(0.4), restore=0.20)
    assert updated is not None
    assert updated.needs.energy == pytest.approx(0.60)


def test_apply_rest_rejects_full_energy_and_dead() -> None:
    """Rest fails when energy is full or the agent is dead."""
    assert apply_rest(_tired(1.0)) is None
    dead = _tired(0.2).model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    assert can_rest(dead) is False
    assert apply_rest(dead) is None


def test_apply_rest_clamps_at_one() -> None:
    """Energy restoration cannot exceed 1.0."""
    updated = apply_rest(_tired(0.9), restore=0.5)
    assert updated is not None
    assert updated.needs.energy == 1.0


def test_spend_energy_deducts_and_rejects_insufficient() -> None:
    """spend_energy deducts when affordable and rejects otherwise."""
    spent = spend_energy(_tired(0.5), 0.05)
    assert spent is not None
    assert spent.needs.energy == pytest.approx(0.45)
    assert spend_energy(_tired(0.01), 0.05) is None
    assert spend_energy(_tired(0.5), 0.0) == _tired(0.5)
