"""Unit tests for typed domain identifiers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import AgentId, LocationId


def test_agent_id_rejects_negative() -> None:
    """Agent ids must be non-negative."""
    with pytest.raises(ValidationError):
        AgentId(value=-1)


def test_location_id_ordering_and_int() -> None:
    """Location ids support ordering and int conversion."""
    assert LocationId(value=1) < LocationId(value=2)
    assert int(LocationId(value=9)) == 9
    assert str(AgentId(value=3)) == "3"


def test_ids_are_frozen_and_hashable() -> None:
    """Ids are immutable and usable in sets."""
    agent = AgentId(value=1)
    with pytest.raises(ValidationError):
        agent.value = 2  # type: ignore[misc]
    assert {AgentId(value=1), AgentId(value=1)} == {AgentId(value=1)}
