"""Simulation engine: deterministic tick-loop orchestration.

The engine wires domain/events, clock, world factory, and systems into a
single reproducible run. It contains no action-scoring or need-decay
formulas — those remain in their respective systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from civitas.domain import SimulationCompleted, TickCompleted, TickStarted
from civitas.engine.clock import SimulationClock
from civitas.engine.event_bus import EventBus
from civitas.engine.world_factory import WorldFactory
from civitas.systems import ActionExecutor, NeedsSystem, UtilityPolicy

if TYPE_CHECKING:
    from civitas.domain import DomainEvent, SimulationConfig, World


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Outcome of a completed simulation run.

    Attributes:
        config: Configuration used for the run.
        world: Final world state after the last tick.
        ticks_executed: Number of ticks advanced (equals ``config.ticks``).
        events: Append-only event history in publish order.
    """

    config: SimulationConfig
    world: World
    ticks_executed: int
    events: tuple[DomainEvent, ...]


class SimulationEngine:
    """Run a full deterministic simulation from a ``SimulationConfig``.

    Per-tick pipeline (fixed order):

    1. Advance clock / set ``world.tick``
    2. Publish ``TickStarted``
    3. ``NeedsSystem.apply_decay``
    4. ``UtilityPolicy.select_all``
    5. ``ActionExecutor.execute_all``
    6. Publish ``TickCompleted``
    """

    def __init__(
        self,
        *,
        world_factory: WorldFactory | None = None,
        needs_system: NeedsSystem | None = None,
        policy: UtilityPolicy | None = None,
        executor: ActionExecutor | None = None,
    ) -> None:
        self._world_factory = (
            world_factory if world_factory is not None else WorldFactory()
        )
        self._needs_system = needs_system if needs_system is not None else NeedsSystem()
        self._policy = policy if policy is not None else UtilityPolicy()
        self._executor = executor if executor is not None else ActionExecutor()

    def run(
        self,
        config: SimulationConfig,
        bus: EventBus | None = None,
    ) -> SimulationResult:
        """Execute ``config.ticks`` ticks and return the final result.

        If ``bus`` is omitted, a fresh ``EventBus`` is created for the run.
        """
        event_bus = bus if bus is not None else EventBus()
        clock = SimulationClock.from_config(config)
        world = self._world_factory.create(config, bus=event_bus)

        for tick in clock.run():
            world = world.with_tick(tick)
            event_bus.publish(TickStarted(tick=tick))
            world = self._needs_system.apply_decay(world, bus=event_bus)
            choices = self._policy.select_all(world, bus=event_bus)
            world = self._executor.execute_all(world, choices, bus=event_bus)
            event_bus.publish(TickCompleted(tick=tick))

        event_bus.publish(
            SimulationCompleted(
                tick=world.tick,
                ticks_executed=clock.duration,
            )
        )
        return SimulationResult(
            config=config,
            world=world,
            ticks_executed=clock.duration,
            events=event_bus.history,
        )
