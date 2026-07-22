"""Seeded mock language model for deterministic cognition tests."""

from __future__ import annotations

import hashlib

from civitas.llm.protocol import LanguageModelRequest, LanguageModelResponse


class SeededMockLanguageModel:
    """Hash ``(seed, prompt)`` into a stable mock completion string."""

    def complete(self, request: LanguageModelRequest) -> LanguageModelResponse:
        """Return a deterministic mock completion for ``request``."""
        digest = hashlib.sha256(
            f"{request.seed}:{request.prompt}".encode()
        ).hexdigest()[:16]
        return LanguageModelResponse(
            text=f"mock:{digest}",
            model_name="seeded-mock",
        )
