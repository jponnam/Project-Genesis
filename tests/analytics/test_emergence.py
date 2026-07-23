"""Tests for rule-based emergence detection."""

from __future__ import annotations

from civitas.analytics.emergence import (
    detect_coordinated_group_behavior,
    detect_emergence,
    detect_persistent_inequality,
    detect_sustained_specialization,
    detect_technology_diffusion,
)
from civitas.domain import (
    ActionSelected,
    AgentId,
    KnowledgeLearned,
    SimulationConfig,
    TechnologyDiscovered,
    TechnologyId,
    Tick,
    WealthObserved,
)
from civitas.engine import SimulationEngine


def _wealth(sequence: int, tick: int, gini: int, top1: int = 6000) -> WealthObserved:
    return WealthObserved(
        sequence=sequence,
        tick=Tick(value=tick),
        total=100,
        alive_total=100,
        dead_total=0,
        alive_count=4,
        mean_alive=25.0,
        gini_bps=gini,
        top1_share_bps=top1,
    )


def _action(
    sequence: int,
    tick: int,
    agent: int,
    action: str,
) -> ActionSelected:
    return ActionSelected(
        sequence=sequence,
        tick=Tick(value=tick),
        agent_id=AgentId(value=agent),
        action=action,
        utility=0.4,
    )


def test_persistent_inequality_requires_sustained_high_gini() -> None:
    """Inequality fires only when multiple high-gini censuses persist."""
    low = (_wealth(0, 0, 1000), _wealth(1, 1, 1100), _wealth(2, 2, 1200))
    assert detect_persistent_inequality(low) is None
    high = (
        _wealth(0, 0, 4500),
        _wealth(1, 1, 4800),
        _wealth(2, 2, 5100),
        _wealth(3, 3, 5300),
    )
    finding = detect_persistent_inequality(high)
    assert finding is not None
    assert finding.pattern == "persistent_inequality"
    assert finding.strength > 0
    assert finding.tick_start == 0
    assert finding.tick_end == 3
    assert "gini" in finding.explanation.lower()


def test_sustained_specialization_detects_dominant_action() -> None:
    """An agent dominated by one action is flagged as specialized."""
    events = tuple(_action(index, index, 0, "gather") for index in range(8))
    finding = detect_sustained_specialization(events)
    assert finding is not None
    assert finding.pattern == "sustained_specialization"
    assert "agent:0" in finding.entities
    assert finding.metrics_used["dominance_share"] >= 0.7


def test_coordinated_group_behavior_needs_repeated_ticks() -> None:
    """Coordination requires multiple ticks with shared actions."""
    events = (
        _action(0, 1, 0, "rest"),
        _action(1, 1, 1, "rest"),
        _action(2, 2, 0, "rest"),
        _action(3, 2, 1, "rest"),
        _action(4, 3, 0, "move"),
        _action(5, 3, 1, "gather"),
    )
    finding = detect_coordinated_group_behavior(events)
    assert finding is not None
    assert finding.pattern == "coordinated_group_behavior"
    assert finding.metrics_used["coordinated_tick_count"] >= 2


def test_technology_diffusion_needs_multiple_learners() -> None:
    """Diffusion requires a discovery plus two distinct learners of a fact."""
    events = (
        TechnologyDiscovered(
            sequence=0,
            tick=Tick(value=1),
            technology_id=TechnologyId(value=1),
            name="Camp Pottery",
            kind="pottery",
        ),
        KnowledgeLearned(
            sequence=1,
            tick=Tick(value=2),
            agent_id=AgentId(value=0),
            fact="pottery",
            source="discover",
        ),
        KnowledgeLearned(
            sequence=2,
            tick=Tick(value=3),
            agent_id=AgentId(value=1),
            fact="pottery",
            source="teach",
            teacher_id=AgentId(value=0),
        ),
    )
    finding = detect_technology_diffusion(events)
    assert finding is not None
    assert finding.pattern == "technology_diffusion"
    assert set(finding.entities) == {"agent:0", "agent:1"}


def test_detect_emergence_is_deterministic_and_ordered() -> None:
    """Full detector returns stable ordering for the same event stream."""
    actions = tuple(_action(3 + index, index, 0, "move") for index in range(8))
    events = (
        _wealth(0, 0, 4500),
        _wealth(1, 1, 4600),
        _wealth(2, 2, 4700),
        *actions,
    )
    first = detect_emergence(events)
    second = detect_emergence(events)
    assert first.to_dict() == second.to_dict()
    assert first.rules_evaluated
    patterns = [finding.pattern for finding in first.findings]
    assert patterns == sorted(
        patterns,
        key=lambda pattern: (
            -next(f.strength for f in first.findings if f.pattern == pattern),
            pattern,
        ),
    )
    assert "persistent_inequality" in patterns
    assert "sustained_specialization" in patterns


def test_live_run_emergence_report_is_structured() -> None:
    """Engine runs produce a well-formed emergence report (findings optional)."""
    result = SimulationEngine().run(
        SimulationConfig(seed=42, ticks=8, agent_count=4, run_name="emerge")
    )
    report = detect_emergence(result.events, path="memory")
    assert report.path == "memory"
    assert len(report.rules_evaluated) == 10
    for finding in report.findings:
        assert 0.0 <= finding.strength <= 1.0
        assert 0.0 <= finding.confidence <= 1.0
        assert finding.explanation
        assert finding.evidence
