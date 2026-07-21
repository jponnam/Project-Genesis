"""Civitas Lab: deterministic multi-agent civilization research platform.

Civitas Lab is an open-source AI research platform for studying emergent
intelligence, autonomous agents, economics, governance, cooperation,
conflict, institutions, and civilization formation.

Architecture follows Domain-Driven Design with clean layered boundaries:

* ``domain`` — immutable core models, value objects, and domain events
* ``engine`` — deterministic simulation clock, RNG, and orchestration
* ``systems`` — decoupled behavioral systems communicating via events
* ``storage`` — durable event persistence and replay (JSONL)
* ``analytics`` — offline analysis of simulation traces
* ``cli`` — researcher-facing command-line interface
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
