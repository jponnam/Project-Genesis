"""Simulation engine: deterministic tick-loop orchestration.

The engine wires domain/events, clock, world factory, and systems into a
single reproducible run. It contains no action-scoring or need-decay
formulas — those remain in their respective systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from civitas.domain import SimulationCompleted, TickCompleted, TickStarted
from civitas.engine.clock import SimulationClock
from civitas.engine.event_bus import EventBus
from civitas.engine.world_factory import WorldFactory
from civitas.systems import (
    ActionExecutor,
    BirthSystem,
    CitySystem,
    DeathSystem,
    EconomySystem,
    FamilySystem,
    GovernmentSystem,
    InfrastructureSystem,
    InstitutionSystem,
    LawSystem,
    MarketSystem,
    NeedsSystem,
    NetworkSystem,
    PopulationSystem,
    PriceSystem,
    RelationshipSystem,
    ReputationSystem,
    TaxSystem,
    UtilityPolicy,
    VoteSystem,
)

if TYPE_CHECKING:
    from civitas.domain import DomainEvent, SimulationConfig, World


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Outcome of a completed simulation run.

    Attributes:
        config: Configuration used for the run.
        world: Final world state after the last tick.
        ticks_executed: Number of ticks advanced (equals ``config.ticks``).
        events: Append-only event history in publish order.
    """

    config: SimulationConfig
    world: World
    ticks_executed: int
    events: tuple[DomainEvent, ...]


class SimulationEngine:
    """Run a full deterministic simulation from a ``SimulationConfig``.

    Per-tick pipeline (fixed order):

    1. Advance clock / set ``world.tick``
    2. Publish ``TickStarted``
    3. ``NeedsSystem.apply_decay``
    4. ``UtilityPolicy.select_all``
    5. ``ActionExecutor.execute_all``
    6. ``DeathSystem.apply_deaths``
    7. ``BirthSystem.apply_births``
    8. ``TaxSystem.apply_taxes``
    9. Publish ``TickCompleted``
    10. ``PopulationSystem.observe``
    11. ``EconomySystem.observe``
    12. ``MarketSystem.observe``
    13. ``PriceSystem.observe``
    14. ``RelationshipSystem.observe``
    15. ``ReputationSystem.observe``
    16. ``FamilySystem.observe``
    17. ``NetworkSystem.observe``
    18. ``GovernmentSystem.observe``
    19. ``LawSystem.observe``
    20. ``VoteSystem.observe``
    21. ``InstitutionSystem.observe``
    22. ``CitySystem.observe``
    23. ``InfrastructureSystem.observe``

    Initial population, wealth, market, price, relationship, reputation,
    family, network, government, law, election, institution, city, and
    infrastructure censuses are also observed at tick 0 immediately after
    world creation. Death runs after actions (recovery chance) and before
    birth so newly dead parents cannot reproduce. Birth and death both
    complete before taxes so the levy sees the settled roster. Taxes
    complete before ``TickCompleted`` so wealth censuses reflect post-levy
    balances. Taxes are disabled by default; when enabled, active
    ``TAX_SCHEDULE`` laws override levy parameters. Relationship
    observation is wired each tick; SOCIALIZE may mutate bonds during
    action execution. Reputation observation follows relationships so
    standings reflect the latest bonds. Family observation follows
    reputation and reads birth ``parent_id`` lineage without mutating
    agents. Network observation follows families and measures the living
    bond graph. Government observation follows networks and reports polity
    coverage, treasuries, and subjects without mutating agents. Law
    observation follows governments and reports statute activity. Election
    observation follows laws and reports the archived vote history;
    elections are not auto-conducted each tick. Institution observation
    follows elections and reports civic organizations without mutating
    agents. City observation follows institutions and reports settlement
    residency without mutating agents. Infrastructure observation follows
    cities and reports built capacity without mutating agents.
    """

    def __init__(
        self,
        *,
        world_factory: WorldFactory | None = None,
        needs_system: NeedsSystem | None = None,
        policy: UtilityPolicy | None = None,
        executor: ActionExecutor | None = None,
        death_system: DeathSystem | None = None,
        birth_system: BirthSystem | None = None,
        tax_system: TaxSystem | None = None,
        population_system: PopulationSystem | None = None,
        economy_system: EconomySystem | None = None,
        market_system: MarketSystem | None = None,
        price_system: PriceSystem | None = None,
        relationship_system: RelationshipSystem | None = None,
        reputation_system: ReputationSystem | None = None,
        family_system: FamilySystem | None = None,
        network_system: NetworkSystem | None = None,
        government_system: GovernmentSystem | None = None,
        law_system: LawSystem | None = None,
        vote_system: VoteSystem | None = None,
        institution_system: InstitutionSystem | None = None,
        city_system: CitySystem | None = None,
        infrastructure_system: InfrastructureSystem | None = None,
    ) -> None:
        self._world_factory = (
            world_factory if world_factory is not None else WorldFactory()
        )
        self._needs_system = needs_system if needs_system is not None else NeedsSystem()
        self._policy = policy if policy is not None else UtilityPolicy()
        self._executor = executor if executor is not None else ActionExecutor()
        self._death_system = death_system if death_system is not None else DeathSystem()
        self._birth_system = birth_system if birth_system is not None else BirthSystem()
        self._tax_system = tax_system if tax_system is not None else TaxSystem()
        self._population_system = (
            population_system if population_system is not None else PopulationSystem()
        )
        self._economy_system = (
            economy_system if economy_system is not None else EconomySystem()
        )
        self._market_system = (
            market_system if market_system is not None else MarketSystem()
        )
        self._price_system = price_system if price_system is not None else PriceSystem()
        self._relationship_system = (
            relationship_system
            if relationship_system is not None
            else RelationshipSystem()
        )
        self._reputation_system = (
            reputation_system if reputation_system is not None else ReputationSystem()
        )
        self._family_system = (
            family_system if family_system is not None else FamilySystem()
        )
        self._network_system = (
            network_system if network_system is not None else NetworkSystem()
        )
        self._government_system = (
            government_system if government_system is not None else GovernmentSystem()
        )
        self._law_system = law_system if law_system is not None else LawSystem()
        self._vote_system = vote_system if vote_system is not None else VoteSystem()
        self._institution_system = (
            institution_system
            if institution_system is not None
            else InstitutionSystem()
        )
        self._city_system = city_system if city_system is not None else CitySystem()
        self._infrastructure_system = (
            infrastructure_system
            if infrastructure_system is not None
            else InfrastructureSystem()
        )

    def run(
        self,
        config: SimulationConfig,
        bus: EventBus | None = None,
    ) -> SimulationResult:
        """Execute ``config.ticks`` ticks and return the final result.

        If ``bus`` is omitted, a fresh ``EventBus`` is created for the run.
        """
        event_bus = bus if bus is not None else EventBus()
        clock = SimulationClock.from_config(config)
        world = self._world_factory.create(config, bus=event_bus)
        world = self._population_system.observe(world, bus=event_bus)
        world = self._economy_system.observe(world, bus=event_bus)
        world = self._market_system.observe(world, bus=event_bus)
        world = self._price_system.observe(world, bus=event_bus)
        world = self._relationship_system.observe(world, bus=event_bus)
        world = self._reputation_system.observe(world, bus=event_bus)
        world = self._family_system.observe(world, bus=event_bus)
        world = self._network_system.observe(world, bus=event_bus)
        world = self._government_system.observe(world, bus=event_bus)
        world = self._law_system.observe(world, bus=event_bus)
        world = self._vote_system.observe(world, bus=event_bus)
        world = self._institution_system.observe(world, bus=event_bus)
        world = self._city_system.observe(world, bus=event_bus)
        world = self._infrastructure_system.observe(world, bus=event_bus)

        for tick in clock.run():
            world = world.with_tick(tick)
            event_bus.publish(TickStarted(tick=tick))
            world = self._needs_system.apply_decay(world, bus=event_bus)
            choices = self._policy.select_all(world, bus=event_bus)
            world = self._executor.execute_all(world, choices, bus=event_bus)
            world = self._death_system.apply_deaths(world, bus=event_bus)
            world = self._birth_system.apply_births(world, bus=event_bus)
            world = self._tax_system.apply_taxes(world, bus=event_bus)
            event_bus.publish(TickCompleted(tick=tick))
            world = self._population_system.observe(world, bus=event_bus)
            world = self._economy_system.observe(world, bus=event_bus)
            world = self._market_system.observe(world, bus=event_bus)
            world = self._price_system.observe(world, bus=event_bus)
            world = self._relationship_system.observe(world, bus=event_bus)
            world = self._reputation_system.observe(world, bus=event_bus)
            world = self._family_system.observe(world, bus=event_bus)
            world = self._network_system.observe(world, bus=event_bus)
            world = self._government_system.observe(world, bus=event_bus)
            world = self._law_system.observe(world, bus=event_bus)
            world = self._vote_system.observe(world, bus=event_bus)
            world = self._institution_system.observe(world, bus=event_bus)
            world = self._city_system.observe(world, bus=event_bus)
            world = self._infrastructure_system.observe(world, bus=event_bus)

        event_bus.publish(
            SimulationCompleted(
                tick=world.tick,
                ticks_executed=clock.duration,
            )
        )
        return SimulationResult(
            config=config,
            world=world,
            ticks_executed=clock.duration,
            events=event_bus.history,
        )
