"""Unit tests for deterministic WorldFactory."""

from __future__ import annotations

from civitas.domain import (
    CAMP_CITY,
    CAMP_COUNCIL,
    CAMP_FIRE,
    CAMP_GOVERNMENT,
    CAMP_IRRIGATION,
    CAMP_LOCATION,
    CAMP_MARKET,
    CAMP_POLL_TAX_LAW,
    CAMP_POTTERY,
    CAMP_WELL,
    CANONICAL_SEED,
    AgentSpawned,
    CityCreated,
    InfrastructureCreated,
    SimulationConfig,
    SimulationStarted,
    default_cities,
    default_governments,
    default_infrastructure,
    default_institutions,
    default_laws,
    default_markets,
    default_technologies,
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
    assert world.cities == default_cities()
    assert world.cities[0] == CAMP_CITY
    assert world.infrastructure == default_infrastructure()
    assert world.infrastructure[0] == CAMP_WELL
    assert world.technologies == default_technologies()
    assert world.technologies[0] == CAMP_FIRE
    assert world.technologies[1] == CAMP_POTTERY
    assert world.technologies[2] == CAMP_IRRIGATION
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


def test_create_publishes_started_through_infrastructure_then_spawned() -> None:
    """Bus receives Started through infrastructure events, then spawns."""
    bus = EventBus()
    config = SimulationConfig(seed=42, agent_count=2, ticks=5, run_name="w")
    world = WorldFactory().create(config, bus=bus)
    assert isinstance(bus.history[0], SimulationStarted)
    cities = [event for event in bus.history if isinstance(event, CityCreated)]
    assert len(cities) == 1
    assert cities[0].name == "Camp City"
    infra = [event for event in bus.history if isinstance(event, InfrastructureCreated)]
    assert len(infra) == 1
    assert infra[0].name == "Camp Well"
    assert infra[0].kind == "well"
    spawned = [event for event in bus.history if isinstance(event, AgentSpawned)]
    assert len(spawned) == 2
    assert cities[0].sequence < infra[0].sequence < spawned[0].sequence
    assert world.infrastructure[0].name == "Camp Well"


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
    assert left.cities == right.cities
    assert left.infrastructure == right.infrastructure
    assert left.technologies == right.technologies
    assert left.agents[0].personality != right.agents[0].personality
