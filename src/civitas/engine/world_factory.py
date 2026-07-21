"""Deterministic world construction from ``SimulationConfig``.

Identical configs (especially seed ``42``) must always produce identical
worlds. Agent attribute sampling uses per-agent child RNG streams so an
agent's traits depend only on ``(seed, agent_id)``, not on population size.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain import (
    Agent,
    AgentSpawned,
    LocationId,
    Personality,
    SimulationStarted,
    Tick,
    World,
)
from civitas.domain.ids import AgentId
from civitas.engine.rng import SeededRNG

if TYPE_CHECKING:
    from civitas.domain import SimulationConfig
    from civitas.engine.event_bus import EventBus

# Phase 1 places every agent at a single origin location.
ORIGIN_LOCATION_ID: int = 0

# Inclusive starting money range sampled per agent.
STARTING_MONEY_MIN: int = 0
STARTING_MONEY_MAX: int = 20


class WorldFactory:
    """Build reproducible initial worlds for a simulation run."""

    def create(
        self,
        config: SimulationConfig,
        bus: EventBus | None = None,
    ) -> World:
        """Create a world from ``config``, optionally publishing spawn events.

        Construction order is fixed:

        1. Optionally publish ``SimulationStarted`` at tick 0.
        2. For each ``agent_id`` in ``0 .. agent_count-1``, spawn a child
           RNG stream and sample personality + starting money.
        3. Optionally publish ``AgentSpawned`` for each agent in id order.
        """
        root_rng = SeededRNG.from_config(config)
        agents: list[Agent] = []

        if bus is not None:
            bus.publish(
                SimulationStarted(
                    tick=Tick(value=0),
                    seed=config.seed,
                    ticks=config.ticks,
                    agent_count=config.agent_count,
                    run_name=config.run_name,
                )
            )

        for agent_id in range(config.agent_count):
            agent = self._build_agent(root_rng=root_rng, agent_id=agent_id)
            agents.append(agent)
            if bus is not None:
                bus.publish(
                    AgentSpawned(
                        tick=Tick(value=0),
                        agent_id=AgentId(value=agent_id),
                        name=agent.name,
                        location_id=LocationId(value=ORIGIN_LOCATION_ID),
                    )
                )

        return World(
            config=config,
            tick=Tick(value=0),
            agents=tuple(agents),
        )

    def _build_agent(self, root_rng: SeededRNG, agent_id: int) -> Agent:
        """Sample one agent from a child stream keyed by ``agent_id``."""
        rng = root_rng.spawn(agent_id)
        personality = Personality(
            openness=rng.uniform(0.0, 1.0),
            conscientiousness=rng.uniform(0.0, 1.0),
            extraversion=rng.uniform(0.0, 1.0),
            agreeableness=rng.uniform(0.0, 1.0),
            neuroticism=rng.uniform(0.0, 1.0),
        )
        money = rng.randint(STARTING_MONEY_MIN, STARTING_MONEY_MAX)
        return Agent.create(
            agent_id=agent_id,
            name=f"Agent-{agent_id}",
            location_id=ORIGIN_LOCATION_ID,
            money=money,
            birth_tick=0,
            personality=personality,
        )
