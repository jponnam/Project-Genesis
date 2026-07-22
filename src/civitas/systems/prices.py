"""Price system: observe market price quotes each tick.

Owns price observation as a first-class tick concern that emits
``PriceObserved``. Quote math lives in domain helpers so other layers can
query prices without calling this system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import PriceObserved, census_prices

if TYPE_CHECKING:
    from civitas.domain import PriceCensus, World
    from civitas.engine.event_bus import EventBus


class PriceConfig(BaseModel):
    """Parameters controlling price observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class PriceSystem:
    """Compute and emit deterministic market price censuses."""

    def __init__(self, config: PriceConfig | None = None) -> None:
        self._config = config if config is not None else PriceConfig()

    @property
    def config(self) -> PriceConfig:
        """Return the immutable price configuration."""
        return self._config

    def census(self, world: World) -> PriceCensus:
        """Return a price census for ``world``."""
        return census_prices(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe prices and optionally emit ``PriceObserved``.

        The world is never modified.
        """
        snap = census_prices(world)
        if bus is not None and self._config.emit_events:
            bus.publish(
                PriceObserved(
                    tick=snap.tick,
                    quote_count=snap.quote_count,
                    quotes=tuple(
                        (
                            quote.market_id.value,
                            quote.resource,
                            quote.best_ask,
                            quote.ask_quantity,
                            quote.last_trade,
                            quote.listing_count,
                            quote.total_units,
                            quote.suggested_unit_price,
                        )
                        for quote in snap.quotes
                    ),
                )
            )
        return world
