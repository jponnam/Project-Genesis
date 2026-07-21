"""CLI layer: researcher-facing command-line interface.

Exposes simulation controls via Typer. The CLI is a thin adapter over
engine and storage; it contains no domain or policy logic.
"""

from __future__ import annotations
