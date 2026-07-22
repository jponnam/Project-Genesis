"""Language-model adapters for optional agent cognition.

Phase 7 introduces a Protocol-based port so cognition can stay
deterministic by default. Live provider SDKs are not wired in Milestone 1.
"""

from __future__ import annotations

from civitas.llm.mock import SeededMockLanguageModel
from civitas.llm.null import NullLanguageModel
from civitas.llm.protocol import (
    LanguageModel,
    LanguageModelRequest,
    LanguageModelResponse,
)

__all__ = [
    "LanguageModel",
    "LanguageModelRequest",
    "LanguageModelResponse",
    "NullLanguageModel",
    "SeededMockLanguageModel",
]
