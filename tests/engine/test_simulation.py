"""Unit tests for the SimulationEngine."""

from __future__ import annotations

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentMoved,
    AgentSpawned,
    LocationCreated,
    MarketCreated,
    MarketObserved,
    NeedDecayed,
    PopulationObserved,
    PriceObserved,
    RelationshipsObserved,
    ResourceConsumed,
    ResourceGathered,
    SimulationCompleted,
    SimulationConfig,
    SimulationStarted,
    TaxCollected,
    TickCompleted,
    TickStarted,
    WealthObserved,
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
    assert types.count(AgentSpawned.__name__) == 2
    assert types[1] == LocationCreated.__name__
    assert types[10] == MarketCreated.__name__
    assert types[11] == AgentSpawned.__name__
    assert types.count(TickStarted.__name__) == 2
    assert types.count(TickCompleted.__name__) == 2
    assert types[-1] == SimulationCompleted.__name__
    assert isinstance(result.events[-1], SimulationCompleted)
    assert result.events[-1].ticks_executed == 2
    assert result.world.tick.value == 2
    assert len(result.world.locations) == 9
    assert len(result.world.markets) == 1


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
    assert result.world.treasury == len(taxes)
    assert wealth_total(result.world) + result.world.treasury == initial_money
    # No taxes at tick 0 observe; first levy is on tick 1.
    assert taxes[0].tick.value == 1


def test_wealth_observed_reports_treasury_after_enabled_taxes() -> None:
    """Post-levy WealthObserved society_total matches agents plus treasury."""
    engine = SimulationEngine(
        tax_system=TaxSystem(TaxConfig(enabled=True, flat_amount=1, rate_bps=0)),
        birth_system=BirthSystem(BirthConfig(enabled=False)),
    )
    result = engine.run(SimulationConfig(seed=11, ticks=2, agent_count=3))
    observed = [event for event in result.events if isinstance(event, WealthObserved)]
    final = observed[-1]
    assert final.treasury == result.world.treasury
    assert final.society_total == wealth_total(result.world) + result.world.treasury
    assert final.treasury == final.society_total - final.total


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
