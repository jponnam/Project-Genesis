"""Network system: observe-only social-graph censuses.

Derives degree, reciprocity, density, and weakly connected components from
living directed bonds after relationship observation. Does not mutate agents
or relationships. Emits ``NetworksObserved``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from civitas.domain import NetworksObserved, census_networks

if TYPE_CHECKING:
    from civitas.domain import NetworkCensus, World
    from civitas.engine.event_bus import EventBus


class NetworkConfig(BaseModel):
    """Parameters controlling social-network observation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    emit_events: bool = True


class NetworkSystem:
    """Emit deterministic social-network censuses without mutating the world."""

    def __init__(self, config: NetworkConfig | None = None) -> None:
        self._config = config if config is not None else NetworkConfig()

    @property
    def config(self) -> NetworkConfig:
        """Return the immutable network configuration."""
        return self._config

    def census(self, world: World) -> NetworkCensus:
        """Return a social-network census for ``world``."""
        return census_networks(world)

    def observe(
        self,
        world: World,
        bus: EventBus | None = None,
    ) -> World:
        """Observe the social network and optionally emit ``NetworksObserved``.

        The world is never modified.
        """
        snap = census_networks(world)
        if bus is not None and self._config.emit_events:
            tie = snap.strongest_tie
            bus.publish(
                NetworksObserved(
                    tick=snap.tick,
                    living_agent_count=snap.living_agent_count,
                    directed_edge_count=snap.directed_edge_count,
                    undirected_edge_count=snap.undirected_edge_count,
                    reciprocal_pair_count=snap.reciprocal_pair_count,
                    reciprocity_rate=snap.reciprocity_rate,
                    reciprocity_bps=snap.reciprocity_bps,
                    mean_degree=snap.mean_degree,
                    max_degree=snap.max_degree,
                    max_degree_agent_id=snap.max_degree_agent_id,
                    isolated_count=snap.isolated_count,
                    component_count=snap.component_count,
                    largest_component_size=snap.largest_component_size,
                    mean_component_size=snap.mean_component_size,
                    density=snap.density,
                    density_bps=snap.density_bps,
                    strongest_from_id=None if tie is None else tie.from_id,
                    strongest_to_id=None if tie is None else tie.to_id,
                    strongest_strength=None if tie is None else tie.strength,
                )
            )
        return world
