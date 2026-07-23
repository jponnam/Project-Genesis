"""Read-only HTTP API adapters for local simulation runs.

Import ``civitas.api.app:app`` (or ``create_app``) to obtain the FastAPI
application. This package is an outer adapter: it depends on storage and
analytics, never the reverse.
"""

from __future__ import annotations

from typing import Any

__all__ = ["app", "create_app"]


def __getattr__(name: str) -> Any:
    """Lazily export the FastAPI app objects."""
    if name in {"app", "create_app"}:
        from civitas.api.app import app as fastapi_app
        from civitas.api.app import create_app as factory

        mapping = {"app": fastapi_app, "create_app": factory}
        return mapping[name]
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
