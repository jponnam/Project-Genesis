"""Engine layer: deterministic simulation orchestration.

Owns the simulation clock, seeded RNG, world lifecycle, and the tick
loop that advances agent state. The engine emits and consumes domain
events but contains no domain-specific policy logic.
"""

from __future__ import annotations

from civitas.engine.clock import ClockError, SimulationClock
from civitas.engine.event_bus import EventBus
from civitas.engine.rng import SeededRNG, mix_seed
from civitas.engine.simulation import SimulationEngine, SimulationResult
from civitas.engine.world_factory import WorldFactory

__all__ = [
    "ClockError",
    "EventBus",
    "SeededRNG",
    "SimulationClock",
    "SimulationEngine",
    "SimulationResult",
    "WorldFactory",
    "mix_seed",
]
