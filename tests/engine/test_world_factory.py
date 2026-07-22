"""Unit tests for deterministic WorldFactory."""

from __future__ import annotations

from civitas.domain import (
    CAMP_COUNCIL,
    CAMP_GOVERNMENT,
    CAMP_LOCATION,
    CAMP_MARKET,
    CAMP_POLL_TAX_LAW,
    CANONICAL_SEED,
    AgentSpawned,
    GovernmentCreated,
    InstitutionCreated,
    LawCreated,
    LocationCreated,
    MarketCreated,
    SimulationConfig,
    SimulationStarted,
    default_governments,
    default_institutions,
    default_laws,
    default_markets,
    default_world_map,
)
from civitas.engine import EventBus, WorldFactory
from civitas.engine.world_factory import ORIGIN_LOCATION_ID


def test_seed_forty_two_produces_identical_worlds() -> None:
    """Canonical seed 42 must always generate identical worlds."""
    config = SimulationConfig(seed=CANONICAL_SEED, agent_count=10, ticks=100)
    factory = WorldFactory()
    first = factory.create(config)
    second = factory.create(config)
    assert first == second
    assert first.config.seed == 42
    assert len(first.agents) == 10


def test_research_default_world_is_reproducible() -> None:
    """research_default() worlds compare equal across factory calls."""
    factory = WorldFactory()
    config = SimulationConfig.research_default()
    assert factory.create(config) == factory.create(config)


def test_different_seeds_produce_different_worlds() -> None:
    """Changing only the seed must change sampled agent attributes."""
    factory = WorldFactory()
    left = factory.create(SimulationConfig(seed=1, agent_count=5))
    right = factory.create(SimulationConfig(seed=2, agent_count=5))
    assert left != right
    assert left.agents[0].personality != right.agents[0].personality


def test_agents_have_stable_ids_names_and_origin_location() -> None:
    """Factory assigns contiguous ids, deterministic names, origin location."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=3))
    assert [agent.agent_id.value for agent in world.agents] == [0, 1, 2]
    assert [agent.name for agent in world.agents] == [
        "Agent-0",
        "Agent-1",
        "Agent-2",
    ]
    assert all(agent.location_id.value == ORIGIN_LOCATION_ID for agent in world.agents)
    assert world.tick.value == 0
    assert world.locations == default_world_map()
    assert world.locations[0] == CAMP_LOCATION
    assert world.markets == default_markets()
    assert world.markets[0] == CAMP_MARKET
    assert world.governments == default_governments()
    assert world.governments[0] == CAMP_GOVERNMENT
    assert world.laws == default_laws()
    assert world.laws[0] == CAMP_POLL_TAX_LAW
    assert world.elections == ()
    assert world.institutions == default_institutions()
    assert world.institutions[0] == CAMP_COUNCIL
    assert world.treasury == 0
    assert world.agents_at(0) == world.agents


def test_agent_traits_depend_only_on_seed_and_id() -> None:
    """Per-agent streams keep agent 0 stable when population grows."""
    factory = WorldFactory()
    small = factory.create(SimulationConfig(seed=42, agent_count=2))
    large = factory.create(SimulationConfig(seed=42, agent_count=8))
    assert small.agents[0] == large.agents[0]
    assert small.agents[1] == large.agents[1]


def test_starting_money_within_configured_bounds() -> None:
    """Starting money is sampled inside the inclusive factory range."""
    world = WorldFactory().create(SimulationConfig(seed=42, agent_count=20))
    monies = [agent.money for agent in world.agents]
    assert all(0 <= money <= 20 for money in monies)
    assert len(set(monies)) > 1


def test_create_publishes_started_locations_markets_govs_laws_insts_spawned() -> None:
    """Bus receives Started, locations, markets, govs, laws, institutions, spawns."""
    bus = EventBus()
    config = SimulationConfig(seed=42, agent_count=2, ticks=5, run_name="w")
    world = WorldFactory().create(config, bus=bus)
    assert isinstance(bus.history[0], SimulationStarted)
    assert bus.history[0].seed == 42
    assert bus.history[0].agent_count == 2
    created = [event for event in bus.history if isinstance(event, LocationCreated)]
    assert len(created) == 9
    assert created[0].name == "Camp"
    markets = [event for event in bus.history if isinstance(event, MarketCreated)]
    assert len(markets) == 1
    assert markets[0].name == "Camp Market"
    governments = [
        event for event in bus.history if isinstance(event, GovernmentCreated)
    ]
    assert len(governments) == 1
    assert governments[0].name == "Camp Authority"
    assert len(governments[0].jurisdiction) == 9
    laws = [event for event in bus.history if isinstance(event, LawCreated)]
    assert len(laws) == 1
    assert laws[0].name == "Camp Poll Tax"
    assert laws[0].flat_amount == 1
    institutions = [
        event for event in bus.history if isinstance(event, InstitutionCreated)
    ]
    assert len(institutions) == 1
    assert institutions[0].name == "Camp Council"
    assert institutions[0].kind == "council"
    spawned = [event for event in bus.history if isinstance(event, AgentSpawned)]
    assert len(spawned) == 2
    assert spawned[0].name == world.agents[0].name
    assert spawned[1].agent_id.value == 1
    # Markets → governments → laws → institutions after locations, before spawns.
    first_market = next(
        index
        for index, event in enumerate(bus.history)
        if isinstance(event, MarketCreated)
    )
    first_government = next(
        index
        for index, event in enumerate(bus.history)
        if isinstance(event, GovernmentCreated)
    )
    first_law = next(
        index
        for index, event in enumerate(bus.history)
        if isinstance(event, LawCreated)
    )
    first_institution = next(
        index
        for index, event in enumerate(bus.history)
        if isinstance(event, InstitutionCreated)
    )
    first_spawn = next(
        index
        for index, event in enumerate(bus.history)
        if isinstance(event, AgentSpawned)
    )
    assert created[-1].sequence < markets[0].sequence < governments[0].sequence
    assert governments[0].sequence < laws[0].sequence < institutions[0].sequence
    assert institutions[0].sequence < spawned[0].sequence
    assert first_market < first_government < first_law < first_institution < first_spawn


def test_map_is_independent_of_seed() -> None:
    """Geography is fixed; only agent attributes vary with seed."""
    factory = WorldFactory()
    left = factory.create(SimulationConfig(seed=1, agent_count=3))
    right = factory.create(SimulationConfig(seed=2, agent_count=3))
    assert left.locations == right.locations
    assert left.markets == right.markets
    assert left.governments == right.governments
    assert left.laws == right.laws
    assert left.institutions == right.institutions
    assert left.agents[0].personality != right.agents[0].personality
