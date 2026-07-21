"""Unit tests for deterministic WorldFactory."""

from __future__ import annotations

from civitas.domain import (
    CANONICAL_SEED,
    AgentSpawned,
    SimulationConfig,
    SimulationStarted,
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


def test_create_publishes_started_and_spawned_events() -> None:
    """Optional EventBus receives SimulationStarted then AgentSpawned events."""
    bus = EventBus()
    config = SimulationConfig(seed=42, agent_count=2, ticks=5, run_name="w")
    world = WorldFactory().create(config, bus=bus)
    assert isinstance(bus.history[0], SimulationStarted)
    assert bus.history[0].seed == 42
    assert bus.history[0].agent_count == 2
    spawned = [event for event in bus.history if isinstance(event, AgentSpawned)]
    assert len(spawned) == 2
    assert spawned[0].name == world.agents[0].name
    assert spawned[1].agent_id.value == 1
