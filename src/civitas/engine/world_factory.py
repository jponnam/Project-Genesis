"""Deterministic world construction from ``SimulationConfig``.

Identical configs (especially seed ``42``) must always produce identical
worlds. Agent attribute sampling uses per-agent child RNG streams so an
agent's traits depend only on ``(seed, agent_id)``, not on population size.

The location map is a fixed canonical layout (no RNG) so geography stays
stable across seeds while agent traits still vary with the seed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from civitas.domain import (
    Agent,
    AgentSpawned,
    CityCreated,
    GovernmentCreated,
    InfrastructureCreated,
    InnovationCreated,
    InstitutionCreated,
    LawCreated,
    LocationCreated,
    LocationId,
    MarketCreated,
    Personality,
    SimulationStarted,
    TechnologyCreated,
    Tick,
    World,
    default_cities,
    default_elections,
    default_governments,
    default_infrastructure,
    default_innovations,
    default_institutions,
    default_laws,
    default_markets,
    default_research_progress,
    default_technologies,
)
from civitas.domain.ids import AgentId
from civitas.domain.location import CAMP_LOCATION, default_world_map
from civitas.engine.rng import SeededRNG

if TYPE_CHECKING:
    from civitas.domain import SimulationConfig
    from civitas.engine.event_bus import EventBus

# All agents spawn at the camp; MOVE may relocate them on later ticks.
ORIGIN_LOCATION_ID: int = CAMP_LOCATION.location_id.value

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
        2. Build the canonical location map; optionally publish
           ``LocationCreated`` for each location in id order.
        3. Build canonical markets; optionally publish ``MarketCreated``.
        4. Build canonical governments; optionally publish
           ``GovernmentCreated``.
        5. Build canonical laws; optionally publish ``LawCreated``.
        6. Build canonical institutions; optionally publish
           ``InstitutionCreated``.
        7. Build canonical cities; optionally publish ``CityCreated``.
        8. Build canonical infrastructure; optionally publish
           ``InfrastructureCreated``.
        9. Build canonical technologies; optionally publish
           ``TechnologyCreated``.
        10. Build canonical research progress rows (no create event).
        11. Build canonical innovations; optionally publish
           ``InnovationCreated``.
        12. For each ``agent_id`` in ``0 .. agent_count-1``, spawn a child
           RNG stream and sample personality + starting money at camp.
        13. Optionally publish ``AgentSpawned`` for each agent in id order.
        """
        root_rng = SeededRNG.from_config(config)
        locations = default_world_map()
        markets = default_markets()
        governments = default_governments()
        laws = default_laws()
        elections = default_elections()
        institutions = default_institutions()
        cities = default_cities()
        infrastructure = default_infrastructure()
        technologies = default_technologies()
        research_progress = default_research_progress()
        innovations = default_innovations()
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
            for location in locations:
                bus.publish(
                    LocationCreated(
                        tick=Tick(value=0),
                        location_id=location.location_id,
                        name=location.name,
                        x=location.coordinates.x,
                        y=location.coordinates.y,
                        kind=location.kind.value,
                    )
                )
            for market in markets:
                bus.publish(
                    MarketCreated(
                        tick=Tick(value=0),
                        market_id=market.market_id,
                        location_id=market.location_id,
                        name=market.name,
                    )
                )
            for government in governments:
                bus.publish(
                    GovernmentCreated(
                        tick=Tick(value=0),
                        government_id=government.government_id,
                        name=government.name,
                        seat_location_id=government.seat_location_id,
                        jurisdiction=tuple(
                            location.value for location in government.jurisdiction
                        ),
                        leader_id=government.leader_id,
                    )
                )
            for law in laws:
                bus.publish(
                    LawCreated(
                        tick=Tick(value=0),
                        law_id=law.law_id,
                        government_id=law.government_id,
                        name=law.name,
                        kind=law.kind.value,
                        active=law.active,
                        flat_amount=law.flat_amount,
                        rate_bps=law.rate_bps,
                    )
                )
            for institution in institutions:
                bus.publish(
                    InstitutionCreated(
                        tick=Tick(value=0),
                        institution_id=institution.institution_id,
                        government_id=institution.government_id,
                        location_id=institution.location_id,
                        name=institution.name,
                        kind=institution.kind.value,
                        active=institution.active,
                        officer_id=institution.officer_id,
                    )
                )
            for city in cities:
                bus.publish(
                    CityCreated(
                        tick=Tick(value=0),
                        city_id=city.city_id,
                        government_id=city.government_id,
                        location_id=city.location_id,
                        name=city.name,
                        kind=city.kind.value,
                        active=city.active,
                        is_capital=city.is_capital,
                    )
                )
            for item in infrastructure:
                bus.publish(
                    InfrastructureCreated(
                        tick=Tick(value=0),
                        infrastructure_id=item.infrastructure_id,
                        government_id=item.government_id,
                        city_id=item.city_id,
                        location_id=item.location_id,
                        name=item.name,
                        kind=item.kind.value,
                        active=item.active,
                    )
                )
            for technology in technologies:
                bus.publish(
                    TechnologyCreated(
                        tick=Tick(value=0),
                        technology_id=technology.technology_id,
                        name=technology.name,
                        kind=technology.kind.value,
                        discovered=technology.discovered,
                    )
                )
            for innovation in innovations:
                bus.publish(
                    InnovationCreated(
                        tick=Tick(value=0),
                        innovation_id=innovation.innovation_id,
                        technology_id=innovation.technology_id,
                        name=innovation.name,
                        kind=innovation.kind.value,
                        active=innovation.active,
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
            locations=locations,
            markets=markets,
            governments=governments,
            laws=laws,
            elections=elections,
            institutions=institutions,
            cities=cities,
            infrastructure=infrastructure,
            technologies=technologies,
            research_progress=research_progress,
            innovations=innovations,
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
