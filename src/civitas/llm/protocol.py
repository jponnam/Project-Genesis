"""Language-model Protocol used by cognition systems."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from civitas.domain.types import NonEmptyStr, NonNegativeInt


class LanguageModelRequest(BaseModel):
    """Immutable prompt request for a language model adapter."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    prompt: NonEmptyStr
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
