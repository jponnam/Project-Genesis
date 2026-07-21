"""Death helpers for retiring critically deprived or aged agents.

Death is system-driven. Domain helpers decide the cause and produce the
updated agent so the death system and tests share one legality contract.
Dead agents remain on the world roster with ``status=DEAD`` and
``vitality=0.0``; they are not removed.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from civitas.domain.attributes import AgentStatus, Health

if TYPE_CHECKING:
    from civitas.domain.agent import Agent

DEFAULT_FOOD_THRESHOLD: float = 0.0
DEFAULT_WATER_THRESHOLD: float = 0.0
DEFAULT_ENERGY_THRESHOLD: float = 0.0


class DeathCause(StrEnum):
    """Deterministic reason an agent transitions to dead."""

    STARVATION = "starvation"
    DEHYDRATION = "dehydration"
    EXHAUSTION = "exhaustion"
    OLD_AGE = "old_age"


def death_cause(
    agent: Agent,
    current_tick: int,
    *,
    food_threshold: float = DEFAULT_FOOD_THRESHOLD,
    water_threshold: float = DEFAULT_WATER_THRESHOLD,
    energy_threshold: float = DEFAULT_ENERGY_THRESHOLD,
    max_age_ticks: int | None = None,
) -> DeathCause | None:
    """Return why ``agent`` should die now, or ``None`` if they should live.

    Cause priority when multiple conditions match: starvation, dehydration,
    exhaustion, then old age. Already-dead agents never receive a cause.
    """
    if food_threshold < 0.0 or water_threshold < 0.0 or energy_threshold < 0.0:
        msg = "death need thresholds must be >= 0"
        raise ValueError(msg)
    if max_age_ticks is not None and max_age_ticks < 0:
        msg = f"max_age_ticks must be >= 0 when set, got {max_age_ticks}"
        raise ValueError(msg)

    if not agent.is_alive():
        return None
    if agent.needs.food <= food_threshold:
        return DeathCause.STARVATION
    if agent.needs.water <= water_threshold:
        return DeathCause.DEHYDRATION
    if agent.needs.energy <= energy_threshold:
        return DeathCause.EXHAUSTION
    age = current_tick - agent.identity.birth_tick.value
    if max_age_ticks is not None and age >= max_age_ticks:
        return DeathCause.OLD_AGE
    return None


def should_die(
    agent: Agent,
    current_tick: int,
    *,
    food_threshold: float = DEFAULT_FOOD_THRESHOLD,
    water_threshold: float = DEFAULT_WATER_THRESHOLD,
    energy_threshold: float = DEFAULT_ENERGY_THRESHOLD,
    max_age_ticks: int | None = None,
) -> bool:
    """Return True when ``agent`` meets at least one death condition."""
    return (
        death_cause(
            agent,
            current_tick,
            food_threshold=food_threshold,
            water_threshold=water_threshold,
            energy_threshold=energy_threshold,
            max_age_ticks=max_age_ticks,
        )
        is not None
    )


def apply_death(agent: Agent) -> Agent | None:
    """Return ``agent`` marked dead with zero vitality, or ``None`` if already dead.

    Inventory and location are preserved; only lifecycle fields change.
    """
    if not agent.is_alive():
        return None
    return agent.model_copy(
        update={
            "status": AgentStatus.DEAD,
            "health": Health(vitality=0.0),
        }
    )
