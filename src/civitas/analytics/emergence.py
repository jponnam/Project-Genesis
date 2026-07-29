"""Rule-based emergence detectors over event streams and metrics.

Detection is deterministic and threshold-driven. Findings are not
LLM-generated narratives: each pattern has an explicit rule, score
formula, and evidence bundle. Patterns that lack required inputs are
simply omitted (never fabricated).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from itertools import pairwise
from pathlib import Path
from typing import Any

from civitas.analytics.engine import compute_metrics
from civitas.analytics.types import MetricsReport
from civitas.domain import (
    ActionSelected,
    CityCreated,
    DomainEvent,
    InstitutionCreated,
    KnowledgeLearned,
    NetworksObserved,
    PopulationObserved,
    ResourceGathered,
    ResourceProduced,
    ResourceTraded,
    TechnologyCreated,
    TechnologyDiscovered,
    WealthObserved,
)
from civitas.storage.replay import load_events


@dataclass(frozen=True, slots=True)
class EmergenceFinding:
    """One reproducible emergence pattern detection."""

    pattern: str
    strength: float
    confidence: float
    explanation: str
    evidence: tuple[str, ...]
    tick_start: int
    tick_end: int
    entities: tuple[str, ...]
    metrics_used: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EmergenceReport:
    """Ordered emergence findings for one run."""

    path: str | None
    findings: tuple[EmergenceFinding, ...]
    rules_evaluated: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable mapping."""
        return {
            "path": self.path,
            "findings": [finding.to_dict() for finding in self.findings],
            "rules_evaluated": list(self.rules_evaluated),
        }


def _tick(event: DomainEvent) -> int:
    return int(event.tick.value)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def detect_persistent_inequality(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """High wealth Gini across multiple consecutive censuses."""
    observations = [e for e in events if isinstance(e, WealthObserved)]
    if len(observations) < 3:
        return None
    threshold = 4000
    high = [e for e in observations if int(e.gini_bps) >= threshold]
    if len(high) < 3:
        return None
    # Require persistence: last 3 observations all high, or >=70% of series.
    last_three = observations[-3:]
    persistent_tail = all(int(e.gini_bps) >= threshold for e in last_three)
    fraction = len(high) / len(observations)
    if not persistent_tail and fraction < 0.7:
        return None
    mean_gini = sum(int(e.gini_bps) for e in high) / len(high)
    strength = _clamp01((mean_gini - threshold) / 6000 + 0.5)
    confidence = _clamp01(0.55 + 0.15 * len(high))
    return EmergenceFinding(
        pattern="persistent_inequality",
        strength=strength,
        confidence=confidence,
        explanation=(
            f"Wealth Gini remained at or above {threshold} bps across "
            f"{len(high)}/{len(observations)} WealthObserved censuses."
        ),
        evidence=tuple(
            f"t{_tick(e)}: gini_bps={e.gini_bps}, top1_share_bps={e.top1_share_bps}"
            for e in high[:8]
        ),
        tick_start=_tick(high[0]),
        tick_end=_tick(high[-1]),
        entities=(),
        metrics_used={
            "gini_threshold_bps": threshold,
            "mean_high_gini_bps": mean_gini,
            "high_observation_fraction": fraction,
        },
    )


def detect_sustained_specialization(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """An agent repeats one action for the majority of a long action streak."""
    actions = [e for e in events if isinstance(e, ActionSelected)]
    if len(actions) < 8:
        return None
    by_agent: dict[int, list[ActionSelected]] = defaultdict(list)
    for event in actions:
        by_agent[int(event.agent_id.value)].append(event)
    best: EmergenceFinding | None = None
    for agent_id, sequence in by_agent.items():
        if len(sequence) < 6:
            continue
        counts = Counter(str(event.action) for event in sequence)
        dominant_action, dominant_count = counts.most_common(1)[0]
        share = dominant_count / len(sequence)
        if share < 0.7:
            continue
        strength = _clamp01((share - 0.7) / 0.3)
        confidence = _clamp01(0.5 + len(sequence) / 40)
        finding = EmergenceFinding(
            pattern="sustained_specialization",
            strength=strength,
            confidence=confidence,
            explanation=(
                f"Agent {agent_id} chose '{dominant_action}' for "
                f"{dominant_count}/{len(sequence)} actions "
                f"({share:.0%} dominance)."
            ),
            evidence=(
                f"agent={agent_id}",
                f"dominant_action={dominant_action}",
                f"action_counts={dict(sorted(counts.items()))}",
            ),
            tick_start=_tick(sequence[0]),
            tick_end=_tick(sequence[-1]),
            entities=(f"agent:{agent_id}",),
            metrics_used={
                "dominance_share": share,
                "action_count": len(sequence),
            },
        )
        if best is None or finding.strength > best.strength:
            best = finding
    return best


def detect_coordinated_group_behavior(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Multiple agents select the same action on the same tick repeatedly."""
    actions = [e for e in events if isinstance(e, ActionSelected)]
    if len(actions) < 6:
        return None
    by_tick: dict[int, list[ActionSelected]] = defaultdict(list)
    for event in actions:
        by_tick[_tick(event)].append(event)
    coordinated_ticks: list[tuple[int, str, int]] = []
    for tick, selected in sorted(by_tick.items()):
        if len(selected) < 2:
            continue
        counts = Counter(str(event.action) for event in selected)
        action, count = counts.most_common(1)[0]
        if count >= 2 and count / len(selected) >= 0.75:
            coordinated_ticks.append((tick, action, count))
    if len(coordinated_ticks) < 2:
        return None
    # Prefer a repeated action across coordinated ticks.
    action_counts = Counter(action for _, action, _ in coordinated_ticks)
    top_action, top_count = action_counts.most_common(1)[0]
    strength = _clamp01(len(coordinated_ticks) / 10)
    confidence = _clamp01(0.45 + 0.1 * top_count)
    agents = sorted(
        {
            int(event.agent_id.value)
            for event in actions
            if str(event.action) == top_action
        }
    )
    return EmergenceFinding(
        pattern="coordinated_group_behavior",
        strength=strength,
        confidence=confidence,
        explanation=(
            f"On {len(coordinated_ticks)} ticks, >=75% of acting agents "
            f"chose the same action; most common coordinated action "
            f"was '{top_action}'."
        ),
        evidence=tuple(
            f"t{tick}: action={action}, agents={count}"
            for tick, action, count in coordinated_ticks[:8]
        ),
        tick_start=coordinated_ticks[0][0],
        tick_end=coordinated_ticks[-1][0],
        entities=tuple(f"agent:{agent_id}" for agent_id in agents[:12]),
        metrics_used={
            "coordinated_tick_count": len(coordinated_ticks),
            "top_action": top_action,
        },
    )


def detect_institutional_clustering(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Multiple institutions share the same seat location."""
    created = [e for e in events if isinstance(e, InstitutionCreated)]
    if len(created) < 2:
        return None
    by_location: dict[int, list[InstitutionCreated]] = defaultdict(list)
    for event in created:
        by_location[int(event.location_id.value)].append(event)
    cluster = max(by_location.values(), key=len)
    if len(cluster) < 2:
        return None
    location_id = int(cluster[0].location_id.value)
    strength = _clamp01(len(cluster) / 5)
    return EmergenceFinding(
        pattern="institutional_clustering",
        strength=strength,
        confidence=0.8,
        explanation=(
            f"{len(cluster)} institutions were created at location {location_id}."
        ),
        evidence=tuple(f"{event.kind}:{event.name}" for event in cluster),
        tick_start=min(_tick(event) for event in cluster),
        tick_end=max(_tick(event) for event in cluster),
        entities=(
            f"location:{location_id}",
            *(f"institution:{event.kind}" for event in cluster),
        ),
        metrics_used={"institutions_at_location": len(cluster)},
    )


def detect_market_concentration(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Trade participation concentrated in few agents, or high top1 wealth."""
    trades = [e for e in events if isinstance(e, ResourceTraded)]
    wealth = [e for e in events if isinstance(e, WealthObserved)]
    findings_strength = 0.0
    evidence: list[str] = []
    metrics: dict[str, Any] = {}
    entities: list[str] = []
    tick_start = 0
    tick_end = 0
    if len(trades) >= 3:
        participants: Counter[int] = Counter()
        for event in trades:
            participants[int(event.buyer_id.value)] += 1
            participants[int(event.seller_id.value)] += 1
        total = sum(participants.values())
        top_agent, top_count = participants.most_common(1)[0]
        share = top_count / total
        if share >= 0.5:
            findings_strength = max(findings_strength, share)
            evidence.append(
                f"top_trader agent={top_agent} participation_share={share:.2f}"
            )
            metrics["top_trader_share"] = share
            entities.append(f"agent:{top_agent}")
            tick_start = _tick(trades[0])
            tick_end = _tick(trades[-1])
    if wealth:
        last = wealth[-1]
        if int(last.top1_share_bps) >= 5000 and int(last.alive_count) >= 2:
            share = int(last.top1_share_bps) / 10_000
            findings_strength = max(findings_strength, share)
            evidence.append(f"t{_tick(last)}: top1_share_bps={last.top1_share_bps}")
            metrics["top1_share_bps"] = int(last.top1_share_bps)
            tick_end = max(tick_end, _tick(last))
            tick_start = tick_start or _tick(last)
    if findings_strength < 0.5:
        return None
    return EmergenceFinding(
        pattern="market_concentration",
        strength=_clamp01(findings_strength),
        confidence=0.7 if trades else 0.6,
        explanation=(
            "Market/wealth concentration exceeded thresholds "
            "(top trader share >= 0.5 and/or top1 wealth share >= 5000 bps)."
        ),
        evidence=tuple(evidence),
        tick_start=tick_start,
        tick_end=tick_end,
        entities=tuple(entities),
        metrics_used=metrics,
    )


def detect_technology_diffusion(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """A discovered technology/fact is learned by multiple agents."""
    discoveries = [e for e in events if isinstance(e, TechnologyDiscovered)]
    learnings = [e for e in events if isinstance(e, KnowledgeLearned)]
    if not discoveries or len(learnings) < 2:
        return None
    by_fact: dict[str, list[KnowledgeLearned]] = defaultdict(list)
    for event in learnings:
        by_fact[str(event.fact)].append(event)
    fact, learners = max(by_fact.items(), key=lambda item: len(item[1]))
    unique_agents = {int(event.agent_id.value) for event in learners}
    if len(unique_agents) < 2:
        return None
    strength = _clamp01(len(unique_agents) / 6)
    return EmergenceFinding(
        pattern="technology_diffusion",
        strength=strength,
        confidence=_clamp01(0.5 + 0.1 * len(unique_agents)),
        explanation=(
            f"Fact '{fact}' was learned by {len(unique_agents)} distinct agents "
            f"after technology discovery events were present."
        ),
        evidence=tuple(
            f"t{_tick(event)}: agent={event.agent_id.value} fact={event.fact}"
            for event in learners[:10]
        ),
        tick_start=_tick(learners[0]),
        tick_end=_tick(learners[-1]),
        entities=tuple(f"agent:{agent_id}" for agent_id in sorted(unique_agents)),
        metrics_used={
            "fact": fact,
            "learner_count": len(unique_agents),
            "discoveries": len(discoveries),
        },
    )


def detect_urban_concentration(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Population concentrates in one location in the final census."""
    observations = [e for e in events if isinstance(e, PopulationObserved)]
    if not observations:
        return None
    last = observations[-1]
    if int(last.alive) < 3 or not last.location_counts:
        return None
    top_location, top_count = max(last.location_counts, key=lambda item: item[1])
    share = top_count / int(last.alive)
    if share < 0.6:
        return None
    cities = [e for e in events if isinstance(e, CityCreated)]
    return EmergenceFinding(
        pattern="urban_concentration",
        strength=_clamp01((share - 0.6) / 0.4),
        confidence=0.75,
        explanation=(
            f"Final population census placed {top_count}/{last.alive} living "
            f"agents ({share:.0%}) at location {top_location}."
        ),
        evidence=(
            f"location_counts={list(last.location_counts)}",
            f"cities={[f'{c.kind}:{c.name}' for c in cities]}",
        ),
        tick_start=_tick(last),
        tick_end=_tick(last),
        entities=(f"location:{top_location}",),
        metrics_used={"top_location_share": share, "alive": int(last.alive)},
    )


def detect_stable_social_communities(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Network component structure stays stable with non-trivial density."""
    observations = [e for e in events if isinstance(e, NetworksObserved)]
    if len(observations) < 3:
        return None
    components = [int(event.component_count) for event in observations]
    densities = [int(event.density_bps) for event in observations]
    if max(densities) <= 0:
        return None
    # Stability: component_count range small relative to mean.
    mean_components = sum(components) / len(components)
    spread = max(components) - min(components)
    if mean_components <= 0:
        return None
    if spread > max(1, mean_components * 0.25):
        return None
    mean_density = sum(densities) / len(densities)
    if mean_density < 500:
        return None
    return EmergenceFinding(
        pattern="stable_social_communities",
        strength=_clamp01(mean_density / 5000),
        confidence=_clamp01(0.5 + len(observations) / 20),
        explanation=(
            f"NetworksObserved component_count stayed within spread={spread} "
            f"across {len(observations)} censuses while mean density_bps="
            f"{mean_density:.0f}."
        ),
        evidence=tuple(
            f"t{_tick(e)}: components={e.component_count}, "
            f"density_bps={e.density_bps}, reciprocity_bps={e.reciprocity_bps}"
            for e in observations[:8]
        ),
        tick_start=_tick(observations[0]),
        tick_end=_tick(observations[-1]),
        entities=(),
        metrics_used={
            "component_spread": spread,
            "mean_density_bps": mean_density,
        },
    )


def detect_rapid_systemic_transition(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Large tick-to-tick jumps in wealth totals or living population."""
    wealth = [e for e in events if isinstance(e, WealthObserved)]
    population = [e for e in events if isinstance(e, PopulationObserved)]
    jumps: list[tuple[str, int, int, float]] = []
    for wealth_prev, wealth_curr in pairwise(wealth):
        prev_total = max(int(wealth_prev.alive_total), 1)
        wealth_delta = (
            abs(int(wealth_curr.alive_total) - int(wealth_prev.alive_total))
            / prev_total
        )
        if wealth_delta >= 0.35:
            jumps.append(
                (
                    "wealth_alive_total",
                    _tick(wealth_prev),
                    _tick(wealth_curr),
                    wealth_delta,
                )
            )
    for pop_prev, pop_curr in pairwise(population):
        prev_alive = max(int(pop_prev.alive), 1)
        pop_delta = abs(int(pop_curr.alive) - int(pop_prev.alive)) / prev_alive
        if pop_delta >= 0.35:
            jumps.append(
                (
                    "population_alive",
                    _tick(pop_prev),
                    _tick(pop_curr),
                    pop_delta,
                )
            )
    if not jumps:
        return None
    metric_name, start, end, max_delta = max(jumps, key=lambda item: item[3])
    return EmergenceFinding(
        pattern="rapid_systemic_transition",
        strength=_clamp01(max_delta),
        confidence=0.65,
        explanation=(
            f"Detected a rapid transition in {metric_name} with relative "
            f"change {max_delta:.0%} between ticks {start} and {end}."
        ),
        evidence=tuple(
            f"{name}: t{left}->t{right} delta={change:.2f}"
            for name, left, right, change in jumps[:8]
        ),
        tick_start=start,
        tick_end=end,
        entities=(),
        metrics_used={"max_relative_delta": max_delta, "metric": metric_name},
    )


def detect_resource_collapse(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Consumption/death pressure without offsetting gathers, or mass death."""
    gathers = sum(int(e.amount) for e in events if isinstance(e, ResourceGathered))
    # ResourceConsumed amount
    consumed = 0
    for event in events:
        if event.event_type == "ResourceConsumed":
            consumed += int(event.model_dump(mode="json")["amount"])
    deaths = [e for e in events if e.event_type == "AgentDied"]
    population = [e for e in events if isinstance(e, PopulationObserved)]
    evidence: list[str] = []
    strength = 0.0
    tick_start = 0
    tick_end = 0
    if population:
        first, last = population[0], population[-1]
        if int(first.alive) >= 3 and int(last.alive) <= int(first.alive) * 0.5:
            strength = max(
                strength,
                1.0 - (int(last.alive) / max(int(first.alive), 1)),
            )
            evidence.append(
                f"population alive {first.alive}-> {last.alive} "
                f"(t{_tick(first)}->t{_tick(last)})"
            )
            tick_start, tick_end = _tick(first), _tick(last)
    if len(deaths) >= 3:
        strength = max(strength, min(1.0, len(deaths) / 10))
        evidence.append(f"agent_deaths={len(deaths)}")
        tick_start = tick_start or _tick(deaths[0])
        tick_end = max(tick_end, _tick(deaths[-1]))
    if consumed > 0 and gathers == 0 and len(events) > 20:
        strength = max(strength, 0.55)
        evidence.append(f"consumed={consumed} with gathers=0")
    if strength < 0.5:
        return None
    return EmergenceFinding(
        pattern="resource_collapse",
        strength=_clamp01(strength),
        confidence=0.6,
        explanation=(
            "Resource/population collapse signals exceeded thresholds "
            "(sharp alive decline, multiple deaths, or consumption without gathers)."
        ),
        evidence=tuple(evidence),
        tick_start=tick_start,
        tick_end=tick_end,
        entities=(),
        metrics_used={
            "gathers": gathers,
            "consumed": consumed,
            "deaths": len(deaths),
        },
    )


def detect_mid_tree_activation(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Multiple non-fire technologies are active/discovered in the run."""
    discovered: dict[str, tuple[int, str]] = {}
    for event in events:
        if (isinstance(event, TechnologyCreated) and event.discovered) or isinstance(
            event, TechnologyDiscovered
        ):
            discovered[str(event.kind)] = (_tick(event), str(event.name))
    discovered.pop("fire", None)
    if len(discovered) < 2:
        return None
    ordered = sorted(discovered.items(), key=lambda item: (item[1][0], item[0]))
    ticks = [value[0] for _kind, value in ordered]
    kinds = [kind for kind, _value in ordered]
    return EmergenceFinding(
        pattern="mid_tree_activation",
        strength=_clamp01(0.45 + len(kinds) / 10),
        confidence=_clamp01(0.65 + len(kinds) / 20),
        explanation=(
            f"{len(kinds)} non-fire technologies were active or discovered: "
            f"{', '.join(kinds)}."
        ),
        evidence=tuple(
            f"t{tick}: {kind} ({name})" for kind, (tick, name) in ordered[:10]
        ),
        tick_start=min(ticks),
        tick_end=max(ticks),
        entities=tuple(f"technology:{kind}" for kind in kinds),
        metrics_used={"non_fire_technology_count": len(kinds)},
    )


def detect_civic_densification(
    events: tuple[DomainEvent, ...],
) -> EmergenceFinding | None:
    """Several active institutions and cities coexist in the event record."""
    institutions = [
        event
        for event in events
        if isinstance(event, InstitutionCreated) and event.active
    ]
    cities = [
        event for event in events if isinstance(event, CityCreated) and event.active
    ]
    if len(institutions) < 3 or len(cities) < 2:
        return None
    all_events: list[DomainEvent] = [*institutions, *cities]
    entities = tuple(
        [f"institution:{event.kind}" for event in institutions]
        + [f"city:{event.kind}" for event in cities]
    )
    return EmergenceFinding(
        pattern="civic_densification",
        strength=_clamp01(0.45 + (len(institutions) + len(cities)) / 16),
        confidence=0.9,
        explanation=(
            f"{len(institutions)} active institutions and {len(cities)} active "
            "cities coexist, exceeding the civic-density threshold."
        ),
        evidence=tuple(
            [f"institution={event.kind}:{event.name}" for event in institutions]
            + [f"city={event.kind}:{event.name}" for event in cities]
        ),
        tick_start=min(_tick(event) for event in all_events),
        tick_end=max(_tick(event) for event in all_events),
        entities=entities,
        metrics_used={
            "active_institution_count": len(institutions),
            "active_city_count": len(cities),
        },
    )


def detect_craft_stock_specialization(
    events: tuple[DomainEvent, ...],
    metrics: MetricsReport,
) -> EmergenceFinding | None:
    """Production plus concentrated resource stocks indicates craft specialization."""
    inequality = metrics.by_name().get("resource_inequality")
    holdings = metrics.by_name().get("final_resource_holdings")
    produced = [event for event in events if isinstance(event, ResourceProduced)]
    if (
        inequality is None
        or inequality.status != "ok"
        or holdings is None
        or holdings.status != "ok"
        or len(produced) < 2
    ):
        return None
    gini = int(inequality.value)
    resources = dict(holdings.value)
    if gini < 2500 or not resources:
        return None
    recipes = Counter(str(event.recipe_id) for event in produced)
    return EmergenceFinding(
        pattern="craft_stock_specialization",
        strength=_clamp01(0.45 + (gini - 2500) / 7500),
        confidence=_clamp01(0.6 + len(produced) / 20),
        explanation=(
            f"Craft production occurred {len(produced)} times while final "
            f"resource-stock inequality reached {gini} bps."
        ),
        evidence=(
            f"production_events={len(produced)}",
            f"recipes={dict(sorted(recipes.items()))}",
            f"final_holdings={resources}",
            f"resource_gini_bps={gini}",
        ),
        tick_start=_tick(produced[0]),
        tick_end=_tick(produced[-1]),
        entities=tuple(f"recipe:{recipe}" for recipe in sorted(recipes)),
        metrics_used={
            "resource_inequality": gini,
            "final_resource_holdings": resources,
            "production_event_count": len(produced),
        },
    )


RuleFn = Callable[[tuple[DomainEvent, ...]], EmergenceFinding | None]

RULES: tuple[RuleFn, ...] = (
    detect_persistent_inequality,
    detect_sustained_specialization,
    detect_coordinated_group_behavior,
    detect_institutional_clustering,
    detect_market_concentration,
    detect_technology_diffusion,
    detect_urban_concentration,
    detect_stable_social_communities,
    detect_rapid_systemic_transition,
    detect_resource_collapse,
    detect_mid_tree_activation,
    detect_civic_densification,
)

MetricRuleFn = Callable[
    [tuple[DomainEvent, ...], MetricsReport],
    EmergenceFinding | None,
]

METRIC_RULES: tuple[MetricRuleFn, ...] = (detect_craft_stock_specialization,)


def detect_emergence(
    events: tuple[DomainEvent, ...] | list[DomainEvent],
    *,
    path: str | None = None,
    metrics: MetricsReport | None = None,
) -> EmergenceReport:
    """Evaluate all emergence rules and return deterministic findings.

    Event rules and metric-composed rules remain explicit and auditable.
    """
    ordered = tuple(events)
    metric_report = metrics or compute_metrics(ordered, path=path)
    findings: list[EmergenceFinding] = []
    rule_names: list[str] = []
    for rule in RULES:
        rule_names.append(rule.__name__.removeprefix("detect_"))
        finding = rule(ordered)
        if finding is not None:
            findings.append(finding)
    for metric_rule in METRIC_RULES:
        rule_names.append(metric_rule.__name__.removeprefix("detect_"))
        finding = metric_rule(ordered, metric_report)
        if finding is not None:
            findings.append(finding)
    findings.sort(key=lambda item: (-item.strength, item.pattern, item.tick_start))
    return EmergenceReport(
        path=path,
        findings=tuple(findings),
        rules_evaluated=tuple(rule_names),
    )


def analyze_emergence(path: Path | str) -> EmergenceReport:
    """Load JSONL and run emergence detection."""
    resolved = Path(path)
    events = load_events(resolved)
    # Metrics computed for side-channel completeness / future composition.
    report = compute_metrics(events, path=str(resolved))
    return detect_emergence(events, path=str(resolved), metrics=report)
