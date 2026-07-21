"""World resource deposits and gathering helpers.

Resource stocks live on locations. Gathering transfers stock into an
agent inventory. Systems must not call each other to answer deposit
queries — they use these domain helpers instead.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from civitas.domain.attributes import ResourceStack
from civitas.domain.location import LocationKind

if TYPE_CHECKING:
    from civitas.domain.agent import Agent
    from civitas.domain.location import Location
    from civitas.domain.world import World


class ResourceKind(StrEnum):
    """Canonical gatherable resource types for Phase 2."""

    FOOD = "food"
    WATER = "water"
    WOOD = "wood"
    STONE = "stone"


# Which homeostatic need each resource primarily supports (materials: none).
RESOURCE_NEED: dict[str, str | None] = {
    ResourceKind.FOOD.value: "food",
    ResourceKind.WATER.value: "water",
    ResourceKind.WOOD.value: None,
    ResourceKind.STONE.value: None,
}

# Deterministic initial stock by resource kind (no RNG).
DEFAULT_INITIAL_STOCK: dict[ResourceKind, int] = {
    ResourceKind.FOOD: 24,
    ResourceKind.WATER: 32,
    ResourceKind.WOOD: 16,
    ResourceKind.STONE: 16,
}

# Fixed deposit catalog per biome / site kind.
LOCATION_RESOURCE_KINDS: dict[LocationKind, tuple[ResourceKind, ...]] = {
    LocationKind.CAMP: (),
    LocationKind.PLAIN: (ResourceKind.FOOD,),
    LocationKind.FOREST: (ResourceKind.FOOD, ResourceKind.WOOD),
    LocationKind.RIVER: (ResourceKind.WATER,),
    LocationKind.HILL: (ResourceKind.STONE,),
}

DEFAULT_GATHER_AMOUNT: int = 1


def deposits_for_kind(kind: LocationKind) -> tuple[ResourceStack, ...]:
    """Return the canonical initial deposits for a location ``kind``."""
    stacks = [
        ResourceStack(
            resource=resource.value,
            quantity=DEFAULT_INITIAL_STOCK[resource],
        )
        for resource in LOCATION_RESOURCE_KINDS[kind]
    ]
    stacks.sort(key=lambda stack: stack.resource)
    return tuple(stacks)


def location_stock(location: Location, resource: str) -> int:
    """Return remaining ``resource`` stock at ``location`` (0 if absent)."""
    for stack in location.deposits:
        if stack.resource == resource:
            return stack.quantity
    return 0


def gatherable_resources(location: Location) -> tuple[str, ...]:
    """Return resource names with positive stock, sorted ascending."""
    return tuple(stack.resource for stack in location.deposits if stack.quantity > 0)


def with_deposit_quantity(
    location: Location,
    resource: str,
    quantity: int,
) -> Location:
    """Return ``location`` with ``resource`` stock set to ``quantity``.

    Raises:
        ValueError: If ``quantity`` is negative.
    """
    if quantity < 0:
        msg = f"deposit quantity must be >= 0, got {quantity}"
        raise ValueError(msg)
    updated: list[ResourceStack] = []
    found = False
    for stack in location.deposits:
        if stack.resource == resource:
            found = True
            if quantity > 0:
                updated.append(ResourceStack(resource=resource, quantity=quantity))
        else:
            updated.append(stack)
    if not found and quantity > 0:
        updated.append(ResourceStack(resource=resource, quantity=quantity))
    updated.sort(key=lambda stack: stack.resource)
    return location.model_copy(update={"deposits": tuple(updated)})


def apply_gather(
    world: World,
    agent: Agent,
    resource: str,
    *,
    amount: int = DEFAULT_GATHER_AMOUNT,
) -> World | None:
    """Gather ``amount`` of ``resource`` from the agent's current location.

    On success, depletes the location deposit and adds to the agent
    inventory. Returns ``None`` when the gather is illegal (dead agent,
    unknown location, insufficient stock, or non-positive amount).
    """
    if amount <= 0:
        return None
    if not agent.is_alive():
        return None
    location = world.location_by_id(agent.location_id)
    if location is None:
        return None
    stock = location_stock(location, resource)
    if stock < amount:
        return None

    new_location = with_deposit_quantity(location, resource, stock - amount)
    new_inventory = agent.inventory.add(resource, amount)
    new_agent = agent.model_copy(update={"inventory": new_inventory})
    return world.with_location(new_location).with_agent(new_agent)
