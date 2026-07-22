"""Unit tests for the ProductionSystem and PRODUCE action integration."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    ActionKind,
    Agent,
    Inventory,
    NeedDecayed,
    Needs,
    Personality,
    ResourceProduced,
    ResourceStack,
    SimulationConfig,
    World,
)
from civitas.engine import EventBus
from civitas.systems import ProductionSystem, UtilityPolicy


def _crafter(
    agent_id: int = 0,
    *,
    food: int = 0,
    water: int = 0,
    wood: int = 0,
    stone: int = 0,
    energy: float = 1.0,
    rations: int = 0,
) -> Agent:
    stacks = [
        ResourceStack(resource=name, quantity=qty)
        for name, qty in (
            ("food", food),
            ("rations", rations),
            ("stone", stone),
            ("water", water),
            ("wood", wood),
        )
        if qty > 0
    ]
    stacks.sort(key=lambda stack: stack.resource)
    return Agent.create(agent_id=agent_id, name=f"A-{agent_id}").model_copy(
        update={
            "inventory": Inventory(stacks=tuple(stacks)),
            "needs": Needs(
                food=1.0,
                water=1.0,
                energy=energy,
                social=1.0,
                safety=1.0,
            ),
        }
    )


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=len(agents), seed=1),
        locations=(CAMP_LOCATION,),
        agents=agents,
    )


def test_production_system_emits_resource_produced() -> None:
    """ProductionSystem.produce mutates inventory and emits ResourceProduced."""
    world = _world(_crafter(food=2, water=1, energy=0.5))
    bus = EventBus()
    updated = ProductionSystem().produce(world, 0, "rations", bus=bus)
    agent = updated.agent_by_id(0)
    assert agent is not None
    assert agent.inventory.quantity("rations") == 1
    assert agent.inventory.quantity("food") == 0
    assert agent.needs.energy == 0.45
    produced = [event for event in bus.history if isinstance(event, ResourceProduced)]
    assert len(produced) == 1
    assert produced[0].recipe_id == "rations"
    assert produced[0].outputs == (("rations", 1),)
    assert any(isinstance(event, NeedDecayed) for event in bus.history)


def test_production_system_illegal_craft_is_noop() -> None:
    """Illegal crafts leave the world and event bus unchanged."""
    world = _world(_crafter(food=1, water=1))
    bus = EventBus()
    updated = ProductionSystem().produce(world, 0, "rations", bus=bus)
    assert updated == world
    assert bus.history == ()


def test_policy_selects_produce_when_recipe_is_craftable() -> None:
    """Craft-ready agents on a camp-only map select PRODUCE for tools."""
    agent = _crafter(stone=1, wood=2, energy=1.0).model_copy(
        update={
            "personality": Personality(
                conscientiousness=1.0,
                agreeableness=0.0,
                openness=0.0,
                extraversion=0.0,
                neuroticism=0.0,
            ),
        }
    )
    world = _world(agent)
    choice = UtilityPolicy().select(agent, world=world)
    assert choice.action is ActionKind.PRODUCE
    assert choice.target_resource == "tools"
