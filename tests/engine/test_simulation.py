"""Unit tests for the SimulationEngine."""

from __future__ import annotations

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentMoved,
    AgentSpawned,
    CitiesObserved,
    CityCreated,
    CognitionObserved,
    EffectsObserved,
    ElectionsObserved,
    FamiliesObserved,
    GovernmentCreated,
    GovernmentsObserved,
    InfrastructureCreated,
    InfrastructuresObserved,
    InnovationActivated,
    InnovationCreated,
    InnovationsObserved,
    InstitutionCreated,
    InstitutionsObserved,
    KnowledgeObserved,
    LawCreated,
    LawsObserved,
    LocationCreated,
    MarketCreated,
    MarketObserved,
    NeedDecayed,
    NetworksObserved,
    PlansObserved,
    PopulationObserved,
    PriceObserved,
    RelationshipsObserved,
    ReputationObserved,
    ResearchObserved,
    ResearchProgressed,
    ResourceConsumed,
    ResourceGathered,
    RetrievalObserved,
    SimulationCompleted,
    SimulationConfig,
    SimulationStarted,
    TaxCollected,
    TechnologiesObserved,
    TechnologyCreated,
    TechnologyDiscovered,
    TickCompleted,
    TickStarted,
    WealthObserved,
    society_money_total,
    wealth_total,
)
from civitas.engine import EventBus, SimulationEngine, WorldFactory
from civitas.systems import (
    BirthConfig,
    BirthSystem,
    DeathConfig,
    DeathSystem,
    TaxConfig,
    TaxSystem,
)


def test_seed_forty_two_runs_are_identical() -> None:
    """Canonical seed 42 must produce identical worlds and event streams."""
    config = SimulationConfig(seed=42, ticks=5, agent_count=4, run_name="r")
    engine = SimulationEngine()
    first = engine.run(config)
    second = engine.run(config)
    assert first.world == second.world
    assert first.ticks_executed == second.ticks_executed == 5
    assert [event.event_type for event in first.events] == [
        event.event_type for event in second.events
    ]
    assert first.events == second.events


def test_research_default_run_is_reproducible() -> None:
    """research_default() simulations compare equal across engine runs."""
    engine = SimulationEngine()
    config = SimulationConfig.research_default()
    # Use fewer ticks for speed while still exercising the full pipeline.
    config = config.model_copy(update={"ticks": 3})
    assert engine.run(config) == engine.run(config)


def test_different_seeds_diverge() -> None:
    """Different seeds must not produce identical final worlds."""
    engine = SimulationEngine()
    left = engine.run(SimulationConfig(seed=1, ticks=3, agent_count=5))
    right = engine.run(SimulationConfig(seed=2, ticks=3, agent_count=5))
    assert left.world != right.world


def test_run_emits_lifecycle_and_tick_events() -> None:
    """A run emits started/spawn/tick/completed events in a valid envelope."""
    config = SimulationConfig(seed=42, ticks=2, agent_count=2)
    result = SimulationEngine().run(config)
    types = [event.event_type for event in result.events]

    assert types[0] == SimulationStarted.__name__
    assert types.count(LocationCreated.__name__) == 9
    assert types.count(MarketCreated.__name__) == 1
    assert types.count(GovernmentCreated.__name__) == 1
    assert types.count(LawCreated.__name__) == 1
    assert types.count(InstitutionCreated.__name__) == 1
    assert types.count(CityCreated.__name__) == 1
    assert types.count(InfrastructureCreated.__name__) == 1
    assert types.count(TechnologyCreated.__name__) == 5
    assert types.count(InnovationCreated.__name__) == 5
    assert types.count(AgentSpawned.__name__) == 2
    assert types[1] == LocationCreated.__name__
    assert types[10] == MarketCreated.__name__
    assert types[11] == GovernmentCreated.__name__
    assert types[12] == LawCreated.__name__
    assert types[13] == InstitutionCreated.__name__
    assert types[14] == CityCreated.__name__
    assert types[15] == InfrastructureCreated.__name__
    assert types[16] == TechnologyCreated.__name__
    assert types[21] == InnovationCreated.__name__
    assert types[26] == AgentSpawned.__name__
    assert types.count(TickStarted.__name__) == 2
    assert types.count(TickCompleted.__name__) == 2
    assert types[-1] == SimulationCompleted.__name__
    assert isinstance(result.events[-1], SimulationCompleted)
    assert result.events[-1].ticks_executed == 2
    assert result.world.tick.value == 2
    assert len(result.world.locations) == 9
    assert len(result.world.markets) == 1
    assert len(result.world.governments) == 1
    assert len(result.world.laws) == 1
    assert result.world.elections == ()
    assert len(result.world.institutions) == 1
    assert len(result.world.cities) == 1
    assert len(result.world.infrastructure) == 1
    assert len(result.world.technologies) == 5
    assert len(result.world.research_progress) == 4
    assert len(result.world.innovations) == 5


def test_each_tick_selects_and_executes_actions() -> None:
    """Living agents receive ActionSelected and ActionCompleted each tick."""
    config = SimulationConfig(seed=42, ticks=2, agent_count=3)
    result = SimulationEngine().run(config)
    selected = [e for e in result.events if isinstance(e, ActionSelected)]
    completed = [e for e in result.events if isinstance(e, ActionCompleted)]
    assert len(selected) == 2 * 3
    assert len(completed) == 2 * 3
    assert all(event.success for event in completed)


def test_needs_decay_events_occur() -> None:
    """Need decay runs every tick and emits NeedDecayed events."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=1, agent_count=1))
    decayed = [event for event in result.events if isinstance(event, NeedDecayed)]
    # Five needs decay each tick; MOVE may add an extra energy NeedDecayed.
    assert {event.need for event in decayed} == {
        "food",
        "water",
        "energy",
        "social",
        "safety",
    }
    assert len(decayed) >= 5


def test_agents_can_move_during_engine_run() -> None:
    """Open agents may leave Camp via MOVE within a short seeded run."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=5, agent_count=8))
    moved = [event for event in result.events if isinstance(event, AgentMoved)]
    assert moved
    assert any(agent.location_id.value != 0 for agent in result.world.agents)


def test_agents_can_gather_during_engine_run() -> None:
    """Seeded runs eventually gather resources from biome deposits."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=30, agent_count=10))
    gathered = [event for event in result.events if isinstance(event, ResourceGathered)]
    assert gathered
    assert any(agent.inventory.stacks for agent in result.world.agents)


def test_agents_can_eat_gathered_food_during_engine_run() -> None:
    """After gathering food, hungry agents consume it via EAT."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=50, agent_count=12))
    eaten = [
        event
        for event in result.events
        if isinstance(event, ResourceConsumed) and event.resource == "food"
    ]
    assert eaten
    assert any(
        isinstance(event, ResourceGathered) and event.resource == "food"
        for event in result.events
    )


def test_agents_can_drink_gathered_water_during_engine_run() -> None:
    """After gathering water, thirsty agents consume it via DRINK."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=50, agent_count=12))
    drunk = [
        event
        for event in result.events
        if isinstance(event, ResourceConsumed) and event.resource == "water"
    ]
    assert drunk
    assert any(
        isinstance(event, ResourceGathered) and event.resource == "water"
        for event in result.events
    )


def test_agents_can_rest_during_engine_run() -> None:
    """Seeded runs include successful REST actions as energy decays."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=40, agent_count=10))
    rested = [
        event
        for event in result.events
        if isinstance(event, ActionCompleted)
        and event.action == "rest"
        and event.success
    ]
    assert rested


def test_run_accepts_external_event_bus() -> None:
    """Caller-supplied buses receive the full event history."""
    bus = EventBus()
    result = SimulationEngine().run(
        SimulationConfig(seed=7, ticks=1, agent_count=1),
        bus=bus,
    )
    assert result.events == bus.history
    assert bus.next_sequence == len(bus.history)


def test_final_world_population_preserved_on_short_runs() -> None:
    """Short runs stay fully alive with default birth age and death thresholds."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=4, agent_count=6))
    assert result.world.population_size == 6
    assert len(result.world.alive_agents()) == 6
    assert not any(isinstance(event, AgentBorn) for event in result.events)
    assert not any(isinstance(event, AgentDied) for event in result.events)


def test_population_observed_each_tick_including_start() -> None:
    """Engine emits an initial census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=5))
    observed = [
        event for event in result.events if isinstance(event, PopulationObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.total == 5 and event.alive == 5 for event in observed)


def test_engine_births_grow_population_and_census() -> None:
    """Births after actions grow the roster before the end-of-tick census."""
    engine = SimulationEngine(
        birth_system=BirthSystem(
            BirthConfig(
                min_parent_age_ticks=0,
                min_food=0.0,
                min_water=0.0,
                min_energy=0.0,
                parent_energy_cost=0.0,
                max_births_per_tick=1,
            )
        )
    )
    result = engine.run(SimulationConfig(seed=42, ticks=3, agent_count=2))
    born = [event for event in result.events if isinstance(event, AgentBorn)]
    assert len(born) == 3
    assert result.world.population_size == 5
    observed = [
        event for event in result.events if isinstance(event, PopulationObserved)
    ]
    assert observed[0].total == 2
    assert observed[-1].total == 5


def test_engine_deaths_reduce_alive_and_update_census() -> None:
    """Deaths after actions mark agents dead before the end-of-tick census."""
    engine = SimulationEngine(
        death_system=DeathSystem(DeathConfig(max_age_ticks=1)),
        birth_system=BirthSystem(BirthConfig(enabled=False)),
    )
    result = engine.run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    died = [event for event in result.events if isinstance(event, AgentDied)]
    assert len(died) == 3
    assert all(event.cause == "old_age" for event in died)
    assert result.world.population_size == 3
    assert result.world.alive_agents() == ()
    observed = [
        event for event in result.events if isinstance(event, PopulationObserved)
    ]
    assert observed[0].alive == 3
    assert observed[-1].alive == 0
    assert observed[-1].dead == 3


def test_wealth_observed_each_tick_including_start() -> None:
    """Engine emits an initial wealth census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=5))
    observed = [event for event in result.events if isinstance(event, WealthObserved)]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.alive_count == 5 for event in observed)
    assert observed[0].total == sum(agent.money for agent in result.world.agents)


def test_market_observed_each_tick_including_start() -> None:
    """Engine emits an initial market census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    observed = [event for event in result.events if isinstance(event, MarketObserved)]
    assert len(observed) == 3  # tick 0 + ticks 1..2
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 2
    assert all(event.market_count == 1 for event in observed)
    assert result.world.markets[0].name == "Camp Market"


def test_price_observed_each_tick_including_start() -> None:
    """Engine emits an initial price census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=2, agent_count=3))
    observed = [event for event in result.events if isinstance(event, PriceObserved)]
    assert len(observed) == 3  # tick 0 + ticks 1..2
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 2
    assert all(event.quote_count == 0 for event in observed)


def test_default_engine_does_not_collect_taxes() -> None:
    """Taxes stay disabled unless an enabled TaxSystem is injected."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    assert result.world.treasury == 0
    assert sum(government.treasury for government in result.world.governments) == 0
    assert not any(isinstance(event, TaxCollected) for event in result.events)


def test_enabled_taxes_collect_after_births_each_tick() -> None:
    """Injected TaxSystem levies once per tick after the roster settles."""
    config = SimulationConfig(seed=7, ticks=2, agent_count=3)
    initial_money = wealth_total(WorldFactory().create(config))
    engine = SimulationEngine(
        tax_system=TaxSystem(TaxConfig(enabled=True, flat_amount=1, rate_bps=0)),
        birth_system=BirthSystem(BirthConfig(enabled=False)),
    )
    result = engine.run(config)
    taxes = [event for event in result.events if isinstance(event, TaxCollected)]
    assert len(taxes) >= 1
    tax_total = sum(event.amount for event in taxes)
    assert result.world.treasury == 0
    assert (
        sum(government.treasury for government in result.world.governments) == tax_total
    )
    assert society_money_total(result.world) == initial_money
    assert all(event.government_id is not None for event in taxes)
    # No taxes at tick 0 observe; first levy is on tick 1.
    assert taxes[0].tick.value == 1


def test_wealth_observed_reports_treasury_after_enabled_taxes() -> None:
    """Post-levy WealthObserved society_total matches all money holders."""
    engine = SimulationEngine(
        tax_system=TaxSystem(TaxConfig(enabled=True, flat_amount=1, rate_bps=0)),
        birth_system=BirthSystem(BirthConfig(enabled=False)),
    )
    result = engine.run(SimulationConfig(seed=11, ticks=2, agent_count=3))
    observed = [event for event in result.events if isinstance(event, WealthObserved)]
    final = observed[-1]
    assert final.treasury == result.world.treasury
    assert final.government_treasury == sum(
        government.treasury for government in result.world.governments
    )
    assert final.institution_budget == sum(
        institution.budget for institution in result.world.institutions
    )
    assert final.society_total == society_money_total(result.world)
    assert (
        final.treasury + final.government_treasury + final.institution_budget
        == final.society_total - final.total
    )


def test_relationships_observed_each_tick_including_start() -> None:
    """Engine emits an initial relationship census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, RelationshipsObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.bond_count == 0 for event in observed)


def test_reputation_observed_each_tick_including_start() -> None:
    """Engine emits an initial reputation census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, ReputationObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.living_agent_count == 4 for event in observed)
    # Reputation follows relationships in the observe chain.
    rel_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, RelationshipsObserved)
    ]
    rep_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ReputationObserved)
    ]
    assert all(rep > rel for rel, rep in zip(rel_indexes, rep_indexes, strict=True))


def test_families_observed_each_tick_including_start() -> None:
    """Engine emits an initial family census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, FamiliesObserved)]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.founder_count == event.living_agent_count for event in observed)
    # Families follow reputation in the observe chain.
    rep_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ReputationObserved)
    ]
    fam_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, FamiliesObserved)
    ]
    assert all(fam > rep for rep, fam in zip(rep_indexes, fam_indexes, strict=True))


def test_networks_observed_each_tick_including_start() -> None:
    """Engine emits an initial network census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, NetworksObserved)]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.component_count == event.living_agent_count for event in observed)
    # Networks follow families in the observe chain.
    fam_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, FamiliesObserved)
    ]
    net_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, NetworksObserved)
    ]
    assert all(net > fam for fam, net in zip(fam_indexes, net_indexes, strict=True))


def test_governments_observed_each_tick_including_start() -> None:
    """Engine emits an initial government census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, GovernmentsObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.government_count == 1 for event in observed)
    assert all(event.covered_location_count == 9 for event in observed)
    # Governments follow networks in the observe chain.
    net_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, NetworksObserved)
    ]
    gov_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, GovernmentsObserved)
    ]
    assert all(gov > net for net, gov in zip(net_indexes, gov_indexes, strict=True))


def test_laws_observed_each_tick_including_start() -> None:
    """Engine emits an initial law census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, LawsObserved)]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.law_count == 1 for event in observed)
    assert all(event.active_tax_schedule_count == 1 for event in observed)
    assert all(event.active_market_fee_count == 0 for event in observed)
    # Laws follow governments in the observe chain.
    gov_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, GovernmentsObserved)
    ]
    law_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, LawsObserved)
    ]
    assert all(law > gov for gov, law in zip(gov_indexes, law_indexes, strict=True))


def test_elections_observed_each_tick_including_start() -> None:
    """Engine emits an initial election census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, ElectionsObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.election_count == 0 for event in observed)
    # Elections follow laws in the observe chain.
    law_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, LawsObserved)
    ]
    vote_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ElectionsObserved)
    ]
    assert all(vote > law for law, vote in zip(law_indexes, vote_indexes, strict=True))


def test_institutions_observed_each_tick_including_start() -> None:
    """Engine emits an initial institution census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, InstitutionsObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.institution_count == 1 for event in observed)
    assert all(event.active_council_count == 1 for event in observed)
    # Institutions follow elections in the observe chain.
    vote_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ElectionsObserved)
    ]
    inst_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InstitutionsObserved)
    ]
    assert all(
        inst > vote for vote, inst in zip(vote_indexes, inst_indexes, strict=True)
    )


def test_cities_observed_each_tick_including_start() -> None:
    """Engine emits an initial city census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, CitiesObserved)]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.city_count == 1 for event in observed)
    assert all(event.capital_count == 1 for event in observed)
    # Cities follow institutions in the observe chain.
    inst_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InstitutionsObserved)
    ]
    city_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, CitiesObserved)
    ]
    assert all(
        city > inst for inst, city in zip(inst_indexes, city_indexes, strict=True)
    )


def test_infrastructure_observed_each_tick_including_start() -> None:
    """Engine emits an initial infrastructure census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, InfrastructuresObserved)
    ]
    assert len(observed) == 4  # tick 0 + ticks 1..3
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.infrastructure_count == 1 for event in observed)
    assert all(event.active_well_count == 1 for event in observed)
    city_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, CitiesObserved)
    ]
    infra_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InfrastructuresObserved)
    ]
    assert all(
        infra > city for city, infra in zip(city_indexes, infra_indexes, strict=True)
    )


def test_technologies_observed_each_tick_including_start() -> None:
    """Engine emits an initial technology census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, TechnologiesObserved)
    ]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.technology_count == 5 for event in observed)
    assert all(event.discovered_fire_count == 1 for event in observed)
    assert all(event.discovered_irrigation_count == 0 for event in observed)
    assert all(event.discovered_metallurgy_count == 0 for event in observed)
    assert all(event.discovered_writing_count == 0 for event in observed)
    infra_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InfrastructuresObserved)
    ]
    tech_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, TechnologiesObserved)
    ]
    assert all(
        tech > infra for infra, tech in zip(infra_indexes, tech_indexes, strict=True)
    )


def test_research_observed_each_tick_including_start() -> None:
    """Engine emits an initial research census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, ResearchObserved)]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[0].total_points == 0
    assert observed[-1].tick.value == 3
    assert observed[-1].total_points == 3
    assert all(event.progress_count == 4 for event in observed)
    tech_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, TechnologiesObserved)
    ]
    research_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ResearchObserved)
    ]
    assert all(
        research > tech
        for tech, research in zip(tech_indexes, research_indexes, strict=True)
    )
    progressed = [
        event for event in result.events if isinstance(event, ResearchProgressed)
    ]
    assert len(progressed) == 3
    assert not any(isinstance(event, TechnologyDiscovered) for event in result.events)


def test_innovations_observed_each_tick_including_start() -> None:
    """Engine emits an initial innovation census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, InnovationsObserved)
    ]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.innovation_count == 5 for event in observed)
    assert all(event.active_fire_hearth_count == 1 for event in observed)
    assert all(event.active_pottery_craft_count == 0 for event in observed)
    assert all(event.active_irrigation_canal_count == 0 for event in observed)
    assert all(event.active_forge_count == 0 for event in observed)
    assert all(event.active_scribe_count == 0 for event in observed)
    research_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, ResearchObserved)
    ]
    innovation_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InnovationsObserved)
    ]
    assert all(
        innovation > research
        for research, innovation in zip(
            research_indexes, innovation_indexes, strict=True
        )
    )
    assert not any(isinstance(event, InnovationActivated) for event in result.events)


def test_knowledge_observed_each_tick_including_start() -> None:
    """Engine emits an initial knowledge census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, KnowledgeObserved)
    ]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[-1].tick.value == 3
    assert all(event.fire_knower_count == 4 for event in observed)
    assert all(event.pottery_knower_count == 0 for event in observed)
    assert all(event.irrigation_knower_count == 0 for event in observed)
    assert all(event.metallurgy_knower_count == 0 for event in observed)
    assert all(event.writing_knower_count == 0 for event in observed)
    innovation_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InnovationsObserved)
    ]
    knowledge_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, KnowledgeObserved)
    ]
    assert all(
        knowledge > innovation
        for innovation, knowledge in zip(
            innovation_indexes, knowledge_indexes, strict=True
        )
    )


def test_cognition_observed_each_tick_including_start() -> None:
    """Engine emits an initial cognition census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, CognitionObserved)
    ]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[0].total_records == 0
    assert observed[-1].tick.value == 3
    assert observed[-1].total_records == 24
    assert observed[-1].reflection_records == 12
    assert observed[-1].belief_count >= 4
    knowledge_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, KnowledgeObserved)
    ]
    cognition_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, CognitionObserved)
    ]
    assert all(
        cognition > knowledge
        for knowledge, cognition in zip(
            knowledge_indexes, cognition_indexes, strict=True
        )
    )


def test_plans_observed_each_tick_including_start() -> None:
    """Engine emits an initial plan census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, PlansObserved)]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[0].agents_with_plans == 0
    assert observed[-1].tick.value == 3
    assert observed[-1].agents_with_plans == 4
    cognition_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, CognitionObserved)
    ]
    plan_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, PlansObserved)
    ]
    assert all(
        plan > cognition
        for cognition, plan in zip(cognition_indexes, plan_indexes, strict=True)
    )


def test_retrieval_observed_each_tick_including_start() -> None:
    """Engine emits an initial retrieval census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [
        event for event in result.events if isinstance(event, RetrievalObserved)
    ]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[0].agents_with_context == 0
    assert observed[-1].tick.value == 3
    assert observed[-1].agents_with_context == 4
    assert observed[-1].total_retrieved == 12
    plan_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, PlansObserved)
    ]
    retrieval_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, RetrievalObserved)
    ]
    assert all(
        retrieval > plan
        for plan, retrieval in zip(plan_indexes, retrieval_indexes, strict=True)
    )


def test_effects_observed_each_tick_including_start() -> None:
    """Engine emits an initial effects census plus one per executed tick."""
    result = SimulationEngine().run(SimulationConfig(seed=42, ticks=3, agent_count=4))
    observed = [event for event in result.events if isinstance(event, EffectsObserved)]
    assert len(observed) == 4
    assert observed[0].tick.value == 0
    assert observed[0].fire_hearth_active == 1
    assert observed[0].rest_restore_bps == 2500
    assert observed[0].active_well_count == 1
    assert observed[0].drink_restore_bps == 3500
    assert observed[-1].tick.value == 3
    innovation_indexes = [
        i
        for i, event in enumerate(result.events)
        if isinstance(event, InnovationsObserved)
    ]
    effects_indexes = [
        i for i, event in enumerate(result.events) if isinstance(event, EffectsObserved)
    ]
    assert all(
        effects > innovation
        for innovation, effects in zip(innovation_indexes, effects_indexes, strict=True)
    )
