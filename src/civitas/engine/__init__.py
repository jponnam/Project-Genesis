"""Engine layer: deterministic simulation orchestration.

Owns the simulation clock, seeded RNG, world lifecycle, and the tick
loop that advances agent state. The engine emits and consumes domain
events but contains no domain-specific policy logic.
"""

from __future__ import annotations

from civitas.engine.clock import ClockError, SimulationClock
from civitas.engine.event_bus import EventBus

__all__ = [
    "ClockError",
    "EventBus",
    "SimulationClock",
]
