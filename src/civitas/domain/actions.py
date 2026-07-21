"""Action catalog and selection value objects.

Action kinds are domain concepts shared by the utility policy (selection)
and action executor (effects). Systems must not own this catalog.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.ids import AgentId, LocationId


class ActionKind(StrEnum):
    """Phase 2 action catalog."""

    EAT = "eat"
    DRINK = "drink"
    REST = "rest"
    SOCIALIZE = "socialize"
    SEEK_SAFETY = "seek_safety"
    MOVE = "move"
    IDLE = "idle"


# Stable iteration order for deterministic tie-breaking and execution.
ACTION_CATALOG: tuple[ActionKind, ...] = (
    ActionKind.EAT,
    ActionKind.DRINK,
    ActionKind.REST,
    ActionKind.SOCIALIZE,
    ActionKind.SEEK_SAFETY,
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

    @model_validator(mode="after")
    def move_target_consistency(self) -> Self:
        """MOVE requires a destination; other actions forbid one."""
        if self.action is ActionKind.MOVE:
            if self.target_location_id is None:
                msg = "MOVE requires target_location_id"
                raise ValueError(msg)
        elif self.target_location_id is not None:
            msg = "target_location_id is only valid for MOVE"
            raise ValueError(msg)
        return self
