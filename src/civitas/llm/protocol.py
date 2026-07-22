"""Language-model Protocol used by cognition systems."""

from __future__ import annotations

from typing import Annotated, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.types import NonEmptyStr, NonNegativeInt

# Reflection prompts embed episode content plus need metadata; tech-tree
# fact lists can push past the shared NonEmptyStr 128-char bound and the
# earlier 384-char prompt ceiling once cabinetry and later techs join.
PromptStr = Annotated[str, Field(min_length=1, max_length=512)]


class LanguageModelRequest(BaseModel):
    """Immutable prompt request for a language model adapter."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    prompt: PromptStr
    seed: NonNegativeInt = 0


class LanguageModelResponse(BaseModel):
    """Immutable completion response from a language model adapter."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    text: NonEmptyStr
    model_name: NonEmptyStr


@runtime_checkable
class LanguageModel(Protocol):
    """Port for optional language-model completions."""

    def complete(self, request: LanguageModelRequest) -> LanguageModelResponse:
        """Return a completion for ``request``."""
        ...
