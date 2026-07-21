"""Birth helpers for spawning agents from living parents.

Birth is system-driven (not a scored action). Domain helpers decide
eligibility and produce the updated world so the birth system and tests
share one legality contract. Systems must not call each other; they call
these helpers and emit ``AgentBorn``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain.agent import Agent
from civitas.domain.attributes import Personality
from civitas.domain.energy import spend_energy
from civitas.domain.geography import can_enter
from civitas.domain.numeric import clamp_unit
from civitas.domain.population import next_agent_id

if TYPE_CHECKING:
    from civitas.domain.world import World

DEFAULT_MIN_FOOD: float = 0.50
DEFAULT_MIN_WATER: float = 0.50
DEFAULT_MIN_ENERGY: float = 0.50
DEFAULT_MIN_PARENT_AGE_TICKS: int = 10
DEFAULT_PARENT_ENERGY_COST: float = 0.10
DEFAULT_PERSONALITY_REGRESSION: float = 0.50


def agent_age_ticks(agent: Agent, current_tick: int) -> int:
    """Return how many ticks have elapsed since ``agent`` was born."""
    return current_tick - agent.identity.birth_tick.value


def inherit_personality(
    parent: Personality,
    *,
    regression: float = DEFAULT_PERSONALITY_REGRESSION,
) -> Personality:
    """Blend parent traits toward the neutral 0.5 baseline.

    ``regression`` of 0.0 copies the parent; 1.0 yields a fully neutral
    personality. Values are clamped to the unit interval.
    """
    if regression < 0.0 or regression > 1.0:
        msg = f"personality regression must be in [0, 1], got {regression}"
        raise ValueError(msg)

    def blend(trait: float) -> float:
        return clamp_unit(trait * (1.0 - regression) + 0.5 * regression)

    return Personality(
        openness=blend(parent.openness),
        conscientiousness=blend(parent.conscientiousness),
        extraversion=blend(parent.extraversion),
        agreeableness=blend(parent.agreeableness),
        neuroticism=blend(parent.neuroticism),
    )


def can_birth(
    world: World,
    parent: Agent,
    *,
    min_food: float = DEFAULT_MIN_FOOD,
    min_water: float = DEFAULT_MIN_WATER,
    min_energy: float = DEFAULT_MIN_ENERGY,
    min_parent_age_ticks: int = DEFAULT_MIN_PARENT_AGE_TICKS,
    max_population: int | None = None,
    parent_energy_cost: float = DEFAULT_PARENT_ENERGY_COST,
) -> bool:
    """Return True when ``parent`` may produce a child in ``world``.

    Requirements: living parent, age threshold, need floors, enough energy
    for the parent cost, free capacity at the parent's location, and an
    optional global population ceiling.
    """
    if min_parent_age_ticks < 0:
        msg = f"min_parent_age_ticks must be >= 0, got {min_parent_age_ticks}"
        raise ValueError(msg)
    if parent_energy_cost < 0.0:
        msg = f"parent_energy_cost must be >= 0, got {parent_energy_cost}"
        raise ValueError(msg)
    if max_population is not None and max_population < 1:
        msg = f"max_population must be >= 1 when set, got {max_population}"
        raise ValueError(msg)

    if not parent.is_alive():
        return False
    if agent_age_ticks(parent, world.tick.value) < min_parent_age_ticks:
        return False
    if parent.needs.food < min_food:
        return False
    if parent.needs.water < min_water:
        return False
    if parent.needs.energy < min_energy:
        return False
    if parent.needs.energy < parent_energy_cost:
        return False
    if max_population is not None and len(world.agents) >= max_population:
        return False
    return can_enter(world, parent.location_id)


def apply_birth(
    world: World,
    parent: Agent,
    *,
    min_food: float = DEFAULT_MIN_FOOD,
    min_water: float = DEFAULT_MIN_WATER,
    min_energy: float = DEFAULT_MIN_ENERGY,
    min_parent_age_ticks: int = DEFAULT_MIN_PARENT_AGE_TICKS,
    max_population: int | None = None,
    parent_energy_cost: float = DEFAULT_PARENT_ENERGY_COST,
    personality_regression: float = DEFAULT_PERSONALITY_REGRESSION,
) -> tuple[World, Agent] | None:
    """Spawn a child from ``parent`` when birth is legal.

    The child receives the next agent id, inherits a regressed personality,
    shares the parent's location, and is born at ``world.tick``. The parent
    pays ``parent_energy_cost``. Returns ``(world, child)`` or ``None``.
    """
    if not can_birth(
        world,
        parent,
        min_food=min_food,
        min_water=min_water,
        min_energy=min_energy,
        min_parent_age_ticks=min_parent_age_ticks,
        max_population=max_population,
        parent_energy_cost=parent_energy_cost,
    ):
        return None

    # Re-fetch so callers can pass a stale snapshot safely.
    current_parent = world.agent_by_id(parent.agent_id)
    if current_parent is None or not current_parent.is_alive():
        return None

    spent = spend_energy(current_parent, parent_energy_cost)
    if spent is None:
        return None

    child_id = next_agent_id(world)
    child = Agent.create(
        agent_id=child_id,
        name=f"Agent-{child_id}",
        location_id=current_parent.location_id.value,
        birth_tick=world.tick.value,
        personality=inherit_personality(
            current_parent.personality,
            regression=personality_regression,
        ),
    )
    # next_agent_id is max+1, so appending preserves ascending id order.
    agents = tuple(
        spent if agent.agent_id == spent.agent_id else agent for agent in world.agents
    ) + (child,)
    return world.with_agents(agents), child
