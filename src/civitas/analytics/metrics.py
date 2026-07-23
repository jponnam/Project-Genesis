"""Deterministic metric implementations over domain event streams.

Each public metric function documents its definition and input
requirements. Degenerate inputs return ``status='empty'`` or
``status='undefined'`` rather than fabricated numbers.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any

from civitas.analytics.types import MetricResult
from civitas.domain import (
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentSpawned,
    CityCreated,
    DomainEvent,
    InstitutionCreated,
    KnowledgeLearned,
    NetworksObserved,
    ResourceTraded,
    SimulationStarted,
    TechnologyDiscovered,
    WealthObserved,
)


def _tick(event: DomainEvent) -> int:
    return int(event.tick.value)


def _shannon_entropy(counts: Counter[str]) -> float:
    """Return Shannon entropy in bits for a categorical count map."""
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy


def _sample_std(values: list[float]) -> float | None:
    """Population sample standard deviation; None if fewer than 2 values."""
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def event_frequency_by_type(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Count events grouped by concrete ``event_type`` name."""
    definition = (
        "Frequency of each DomainEvent.event_type in the run "
        "(absolute counts over the full log)."
    )
    if not events:
        return MetricResult(
            name="event_frequency_by_type",
            definition=definition,
            value={},
            status="empty",
        )
    counts = dict(Counter(event.event_type for event in events).most_common())
    return MetricResult(
        name="event_frequency_by_type",
        definition=definition,
        value=counts,
        details={"distinct_types": len(counts)},
    )


def event_frequency_by_tick(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Count all events per tick value."""
    definition = "Number of persisted events whose tick equals t, for each observed t."
    if not events:
        return MetricResult(
            name="event_frequency_by_tick",
            definition=definition,
            value={},
            status="empty",
        )
    counts = Counter(_tick(event) for event in events)
    series = {str(tick): counts[tick] for tick in sorted(counts)}
    return MetricResult(
        name="event_frequency_by_tick",
        definition=definition,
        value=series,
        details={"ticks_observed": len(series)},
    )


def agent_activity_distribution(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Share of ActionSelected events attributable to each agent id."""
    definition = (
        "Distribution of ActionSelected events by agent_id.value. "
        "Requires ActionSelected events; agents with zero actions are omitted."
    )
    actions = [event for event in events if isinstance(event, ActionSelected)]
    if not actions:
        return MetricResult(
            name="agent_activity_distribution",
            definition=definition,
            value={},
            status="empty",
            details={"action_count": 0},
        )
    counts = Counter(int(event.agent_id.value) for event in actions)
    total = sum(counts.values())
    shares = {str(agent_id): counts[agent_id] / total for agent_id in sorted(counts)}
    return MetricResult(
        name="agent_activity_distribution",
        definition=definition,
        value=shares,
        details={"action_count": total, "counts": dict(sorted(counts.items()))},
    )


def wealth_gini_bps(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Final and series of wealth Gini coefficients from WealthObserved."""
    definition = (
        "Wealth inequality from WealthObserved.gini_bps (basis points, "
        "0=equality, 10000=max inequality as recorded by the domain census). "
        "Primary value is the last observation; details.series lists "
        "(tick, gini_bps)."
    )
    observations = [event for event in events if isinstance(event, WealthObserved)]
    if not observations:
        return MetricResult(
            name="wealth_gini_bps",
            definition=definition,
            value=None,
            status="empty",
        )
    series = [(_tick(event), int(event.gini_bps)) for event in observations]
    return MetricResult(
        name="wealth_gini_bps",
        definition=definition,
        value=series[-1][1],
        details={
            "series": series,
            "observation_count": len(series),
            "final_top1_share_bps": int(observations[-1].top1_share_bps),
        },
    )


def wealth_concentration(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Final top-1 wealth share from WealthObserved."""
    definition = (
        "Concentration of money among living agents using "
        "WealthObserved.top1_share_bps from the last census "
        "(basis points of alive_total held by the richest living agent)."
    )
    observations = [event for event in events if isinstance(event, WealthObserved)]
    if not observations:
        return MetricResult(
            name="wealth_concentration",
            definition=definition,
            value=None,
            status="empty",
        )
    last = observations[-1]
    return MetricResult(
        name="wealth_concentration",
        definition=definition,
        value=int(last.top1_share_bps),
        details={
            "alive_count": int(last.alive_count),
            "alive_total": int(last.alive_total),
            "zero_count": int(last.zero_count),
        },
    )


def institution_formation_rate(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Institutions created per executed tick."""
    definition = (
        "InstitutionCreated count divided by max(1, ticks_executed), "
        "where ticks_executed is inferred from the maximum tick among "
        "events (or SimulationStarted.ticks when the log only has tick 0)."
    )
    created = sum(1 for event in events if isinstance(event, InstitutionCreated))
    if not events:
        return MetricResult(
            name="institution_formation_rate",
            definition=definition,
            value=None,
            status="empty",
        )
    max_tick = max(_tick(event) for event in events)
    ticks_executed = max(max_tick, 1)
    return MetricResult(
        name="institution_formation_rate",
        definition=definition,
        value=created / ticks_executed,
        details={"institutions_created": created, "ticks_executed": ticks_executed},
    )


def city_formation_rate(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Cities created per executed tick."""
    definition = "CityCreated count divided by max(1, max tick observed in the log)."
    created = sum(1 for event in events if isinstance(event, CityCreated))
    if not events:
        return MetricResult(
            name="city_formation_rate",
            definition=definition,
            value=None,
            status="empty",
        )
    ticks_executed = max(max(_tick(event) for event in events), 1)
    return MetricResult(
        name="city_formation_rate",
        definition=definition,
        value=created / ticks_executed,
        details={"cities_created": created, "ticks_executed": ticks_executed},
    )


def technology_adoption_rate(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Technology discoveries and knowledge-learning rate."""
    definition = (
        "Technology adoption proxies: discoveries = TechnologyDiscovered count; "
        "learnings = KnowledgeLearned count; rate = discoveries / "
        "max(1, max tick). This measures recorded discovery/learning events, "
        "not unobserved private knowledge."
    )
    discoveries = [e for e in events if isinstance(e, TechnologyDiscovered)]
    learnings = [e for e in events if isinstance(e, KnowledgeLearned)]
    if not events:
        return MetricResult(
            name="technology_adoption_rate",
            definition=definition,
            value=None,
            status="empty",
        )
    ticks_executed = max(max(_tick(event) for event in events), 1)
    kinds = [event.kind for event in discoveries]
    return MetricResult(
        name="technology_adoption_rate",
        definition=definition,
        value=len(discoveries) / ticks_executed,
        details={
            "discoveries": len(discoveries),
            "knowledge_learned": len(learnings),
            "discovered_kinds": kinds,
            "ticks_executed": ticks_executed,
        },
    )


def trade_activity_rate(events: tuple[DomainEvent, ...]) -> MetricResult:
    """ResourceTraded events per tick and per living-agent proxy."""
    definition = (
        "Trade activity = ResourceTraded count / max(1, max tick). "
        "details.trade_count is the absolute number of peer trades recorded."
    )
    trades = [event for event in events if isinstance(event, ResourceTraded)]
    if not events:
        return MetricResult(
            name="trade_activity_rate",
            definition=definition,
            value=None,
            status="empty",
        )
    ticks_executed = max(max(_tick(event) for event in events), 1)
    return MetricResult(
        name="trade_activity_rate",
        definition=definition,
        value=len(trades) / ticks_executed,
        details={"trade_count": len(trades), "ticks_executed": ticks_executed},
    )


def relationship_network_density(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Final undirected network density from NetworksObserved."""
    definition = (
        "Social-network density from the last NetworksObserved.density_bps "
        "(basis points). Requires at least one NetworksObserved event."
    )
    observations = [event for event in events if isinstance(event, NetworksObserved)]
    if not observations:
        return MetricResult(
            name="relationship_network_density",
            definition=definition,
            value=None,
            status="empty",
        )
    last = observations[-1]
    return MetricResult(
        name="relationship_network_density",
        definition=definition,
        value=int(last.density_bps),
        details={
            "density": float(last.density),
            "undirected_edge_count": int(last.undirected_edge_count),
            "living_agent_count": int(last.living_agent_count),
            "component_count": int(last.component_count),
        },
    )


def birth_and_death_rates(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Birth and death counts normalized by ticks and initial agents."""
    definition = (
        "birth_rate = AgentBorn / max(1, ticks); death_rate = AgentDied / "
        "max(1, ticks). details also report crude rates per initial "
        "SimulationStarted.agent_count when that event exists."
    )
    if not events:
        return MetricResult(
            name="birth_and_death_rates",
            definition=definition,
            value=None,
            status="empty",
        )
    births = sum(1 for event in events if isinstance(event, AgentBorn))
    deaths = sum(1 for event in events if isinstance(event, AgentDied))
    spawned = sum(1 for event in events if isinstance(event, AgentSpawned))
    ticks_executed = max(max(_tick(event) for event in events), 1)
    started = next((e for e in events if isinstance(e, SimulationStarted)), None)
    initial = int(started.agent_count) if started is not None else spawned
    value = {
        "birth_rate_per_tick": births / ticks_executed,
        "death_rate_per_tick": deaths / ticks_executed,
    }
    details: dict[str, Any] = {
        "births": births,
        "deaths": deaths,
        "ticks_executed": ticks_executed,
        "initial_agents": initial,
    }
    if initial > 0:
        details["births_per_initial_agent"] = births / initial
        details["deaths_per_initial_agent"] = deaths / initial
    return MetricResult(
        name="birth_and_death_rates",
        definition=definition,
        value=value,
        details=details,
    )


def action_diversity_entropy(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Shannon entropy of the ActionSelected action categorical distribution."""
    definition = (
        "Shannon entropy (bits) of ActionSelected.action frequencies. "
        "Higher values mean more diverse action mixes. Empty when no actions."
    )
    actions = [event for event in events if isinstance(event, ActionSelected)]
    if not actions:
        return MetricResult(
            name="action_diversity_entropy",
            definition=definition,
            value=None,
            status="empty",
        )
    counts = Counter(str(event.action) for event in actions)
    entropy = _shannon_entropy(counts)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 0.0
    return MetricResult(
        name="action_diversity_entropy",
        definition=definition,
        value=entropy,
        details={
            "action_counts": dict(sorted(counts.items())),
            "max_entropy_bits": max_entropy,
            "normalized_entropy": (None if max_entropy == 0 else entropy / max_entropy),
        },
    )


def wealth_volatility(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Sample stdev of wealth totals and gini across WealthObserved ticks."""
    definition = (
        "Stability vs volatility proxy: sample standard deviation of "
        "WealthObserved.alive_total and gini_bps across censuses. "
        "Undefined when fewer than two WealthObserved events exist."
    )
    observations = [event for event in events if isinstance(event, WealthObserved)]
    if len(observations) < 2:
        return MetricResult(
            name="wealth_volatility",
            definition=definition,
            value=None,
            status="undefined" if observations else "empty",
            details={"observation_count": len(observations)},
        )
    totals = [float(event.alive_total) for event in observations]
    ginis = [float(event.gini_bps) for event in observations]
    return MetricResult(
        name="wealth_volatility",
        definition=definition,
        value={
            "alive_total_stdev": _sample_std(totals),
            "gini_bps_stdev": _sample_std(ginis),
        },
        details={"observation_count": len(observations)},
    )


def repeated_behavior_entropy(events: tuple[DomainEvent, ...]) -> MetricResult:
    """Entropy of adjacent action bigrams per agent (habit/repetition signal)."""
    definition = (
        "Mean Shannon entropy of adjacent ActionSelected action-pairs "
        "(bigrams) within each agent's chronologically ordered actions. "
        "Low entropy indicates repetitive behavior; requires agents with "
        "at least one bigram."
    )
    actions = [event for event in events if isinstance(event, ActionSelected)]
    if not actions:
        return MetricResult(
            name="repeated_behavior_entropy",
            definition=definition,
            value=None,
            status="empty",
        )
    by_agent: dict[int, list[str]] = defaultdict(list)
    for event in sorted(actions, key=lambda item: (item.sequence, _tick(item))):
        by_agent[int(event.agent_id.value)].append(str(event.action))
    entropies: list[float] = []
    for sequence in by_agent.values():
        if len(sequence) < 2:
            continue
        bigrams = Counter(
            f"{sequence[index]}->{sequence[index + 1]}"
            for index in range(len(sequence) - 1)
        )
        entropies.append(_shannon_entropy(bigrams))
    if not entropies:
        return MetricResult(
            name="repeated_behavior_entropy",
            definition=definition,
            value=None,
            status="undefined",
            details={"agents_with_actions": len(by_agent)},
        )
    return MetricResult(
        name="repeated_behavior_entropy",
        definition=definition,
        value=sum(entropies) / len(entropies),
        details={
            "agents_with_bigrams": len(entropies),
            "agents_with_actions": len(by_agent),
        },
    )


MetricFn = Callable[[tuple[DomainEvent, ...]], MetricResult]

ALL_METRICS: tuple[MetricFn, ...] = (
    event_frequency_by_type,
    event_frequency_by_tick,
    agent_activity_distribution,
    wealth_gini_bps,
    wealth_concentration,
    institution_formation_rate,
    city_formation_rate,
    technology_adoption_rate,
    trade_activity_rate,
    relationship_network_density,
    birth_and_death_rates,
    action_diversity_entropy,
    wealth_volatility,
    repeated_behavior_entropy,
)
