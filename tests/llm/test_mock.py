"""Unit tests for language-model adapters."""

from __future__ import annotations

from civitas.llm import (
    LanguageModelRequest,
    NullLanguageModel,
    SeededMockLanguageModel,
)


def test_seeded_mock_is_deterministic() -> None:
    """Identical seed+prompt pairs always produce the same mock text."""
    model = SeededMockLanguageModel()
    request = LanguageModelRequest(prompt="reflect on camp life", seed=42)
    first = model.complete(request)
    second = model.complete(request)
    assert first == second
    assert first.text.startswith("mock:")
    assert first.model_name == "seeded-mock"


def test_seeded_mock_changes_with_seed_or_prompt() -> None:
    """Different seeds or prompts diverge."""
    model = SeededMockLanguageModel()
    left = model.complete(LanguageModelRequest(prompt="a", seed=1))
    right = model.complete(LanguageModelRequest(prompt="a", seed=2))
    other = model.complete(LanguageModelRequest(prompt="b", seed=1))
    assert left.text != right.text
    assert left.text != other.text


def test_null_language_model_returns_placeholder() -> None:
    """Null adapter returns a fixed offline placeholder."""
    response = NullLanguageModel().complete(
        LanguageModelRequest(prompt="anything", seed=0)
    )
    assert response.text == "null"
    assert response.model_name == "null"
