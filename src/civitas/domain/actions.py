"""Action catalog and selection value objects.

Action kinds are domain concepts shared by the utility policy (selection)
and action executor (effects). Systems must not own this catalog.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from civitas.domain.ids import AgentId


class ActionKind(StrEnum):
    """Phase 1 action catalog."""

    EAT = "eat"
    DRINK = "drink"
    REST = "rest"
    SOCIALIZE = "socialize"
    SEEK_SAFETY = "seek_safety"
    IDLE = "idle"


# Stable iteration order for deterministic tie-breaking and execution.
ACTION_CATALOG: tuple[ActionKind, ...] = (
    ActionKind.EAT,
    ActionKind.DRINK,
    ActionKind.REST,
    ActionKind.SOCIALIZE,
    ActionKind.SEEK_SAFETY,
    ActionKind.IDLE,
)

# Which need each restorative action targets.
ACTION_NEED_TARGET: dict[ActionKind, str | None] = {
    ActionKind.EAT: "food",
    ActionKind.DRINK: "water",
    ActionKind.REST: "energy",
    ActionKind.SOCIALIZE: "social",
    ActionKind.SEEK_SAFETY: "safety",
    ActionKind.IDLE: None,
}

# Inventory resource consumed opportunistically when present.
ACTION_RESOURCE: dict[ActionKind, str | None] = {
    ActionKind.EAT: "food",
    ActionKind.DRINK: "water",
    ActionKind.REST: None,
    ActionKind.SOCIALIZE: None,
    ActionKind.SEEK_SAFETY: None,
    ActionKind.IDLE: None,
}


class ActionChoice(BaseModel):
    """Result of selecting one action for one agent."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    agent_id: AgentId
    action: ActionKind
    utility: float
