"""Action catalog and selection value objects.

Action kinds are domain concepts shared by the utility policy (selection)
and action executor (effects). Systems must not own this catalog.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.ids import AgentId, LocationId
from civitas.domain.types import NonEmptyStr


class ActionKind(StrEnum):
    """Phase 2 action catalog."""

    EAT = "eat"
    DRINK = "drink"
    REST = "rest"
    SOCIALIZE = "socialize"
    SEEK_SAFETY = "seek_safety"
    GATHER = "gather"
    MOVE = "move"
    IDLE = "idle"


# Stable iteration order for deterministic tie-breaking and execution.
ACTION_CATALOG: tuple[ActionKind, ...] = (
    ActionKind.EAT,
    ActionKind.DRINK,
    ActionKind.REST,
    ActionKind.SOCIALIZE,
    ActionKind.SEEK_SAFETY,
    ActionKind.GATHER,
    ActionKind.MOVE,
    ActionKind.IDLE,
)

# Which need each restorative action targets.
ACTION_NEED_TARGET: dict[ActionKind, str | None] = {
    ActionKind.EAT: "food",
    ActionKind.DRINK: "water",
    ActionKind.REST: "energy",
    ActionKind.SOCIALIZE: "social",
    ActionKind.SEEK_SAFETY: "safety",
    ActionKind.GATHER: None,
    ActionKind.MOVE: None,
    ActionKind.IDLE: None,
}

# Inventory resource consumed opportunistically when present.
ACTION_RESOURCE: dict[ActionKind, str | None] = {
    ActionKind.EAT: "food",
    ActionKind.DRINK: "water",
    ActionKind.REST: None,
    ActionKind.SOCIALIZE: None,
    ActionKind.SEEK_SAFETY: None,
    ActionKind.GATHER: None,
    ActionKind.MOVE: None,
    ActionKind.IDLE: None,
}


class ActionChoice(BaseModel):
    """Result of selecting one action for one agent."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    agent_id: AgentId
    action: ActionKind
    utility: float
    target_location_id: LocationId | None = None
    target_resource: NonEmptyStr | None = None

    @model_validator(mode="after")
    def target_field_consistency(self) -> Self:
        """MOVE needs a destination; GATHER needs a resource; others forbid both."""
        if self.action is ActionKind.MOVE:
            if self.target_location_id is None:
                msg = "MOVE requires target_location_id"
                raise ValueError(msg)
            if self.target_resource is not None:
                msg = "MOVE forbids target_resource"
                raise ValueError(msg)
        elif self.action is ActionKind.GATHER:
            if self.target_resource is None:
                msg = "GATHER requires target_resource"
                raise ValueError(msg)
            if self.target_location_id is not None:
                msg = "GATHER forbids target_location_id"
                raise ValueError(msg)
        else:
            if self.target_location_id is not None:
                msg = "target_location_id is only valid for MOVE"
                raise ValueError(msg)
            if self.target_resource is not None:
                msg = "target_resource is only valid for GATHER"
                raise ValueError(msg)
        return self
