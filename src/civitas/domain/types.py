"""Shared domain type aliases and validation bounds.

Centralizing annotations prevents duplicated constraint logic across
domain modules and keeps numeric contracts consistent.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(ge=1)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]
AffinityScore = Annotated[float, Field(ge=-1.0, le=1.0)]
NonEmptyStr = Annotated[str, Field(min_length=1, max_length=128)]
MemoryContentStr = Annotated[str, Field(min_length=1, max_length=256)]
