"""No-op language model adapter."""

from __future__ import annotations

from civitas.llm.protocol import LanguageModelRequest, LanguageModelResponse


class NullLanguageModel:
    """Adapter that returns a fixed placeholder without side effects."""

    def complete(self, request: LanguageModelRequest) -> LanguageModelResponse:
        """Return a deterministic placeholder completion."""
        _ = request
        return LanguageModelResponse(text="null", model_name="null")
