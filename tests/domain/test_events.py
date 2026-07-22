"""Unit tests for domain event models and serialization."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    ActionCompleted,
    ActionSelected,
    AgentBorn,
    AgentDied,
    AgentId,
    AgentMoved,
    AgentReflected,
    AgentSpawned,
    CitiesObserved,
    CityCreated,
    CityId,
    CognitionObserved,
    DomainEvent,
    EffectsObserved,
    ElectionId,
    ElectionResolved,
    ElectionsObserved,
    FamiliesObserved,
    GovernmentCreated,
    GovernmentId,
    GovernmentsObserved,
    InfrastructureBuilt,
    InfrastructureCommissioned,
    InfrastructureCreated,
    InfrastructureId,
    InfrastructuresObserved,
    InnovationActivated,
    InnovationCreated,
    InnovationId,
    InnovationsObserved,
    InstitutionCreated,
    InstitutionFunded,
    InstitutionId,
    InstitutionsObserved,
    KnowledgeLearned,
    KnowledgeObserved,
    LawCreated,
    LawId,
    LawsObserved,
    ListingFilled,
    ListingId,
    ListingPosted,
    LocationId,
    MarketCreated,
    MarketFeeCollected,
    MarketId,
    MarketObserved,
    MemoryRecorded,
    MemoryRetrieved,
    MoneyTransferred,
    NeedDecayed,
    NetworksObserved,
    PlansObserved,
    PlanUpdated,
    PopulationObserved,
    PriceObserved,
    RelationshipsObserved,
    RelationshipUpdated,
    ReputationObserved,
    ResearchObserved,
    ResearchProgressed,
    ResourceConsumed,
    ResourceGathered,
    ResourceProduced,
    ResourceTraded,
    RetrievalObserved,
    SimulationCompleted,
    SimulationStarted,
    TaxCollected,
    TechnologiesObserved,
    TechnologyCreated,
    TechnologyDiscovered,
    TechnologyId,
    Tick,
    TickCompleted,
    TickStarted,
    WealthObserved,
    event_from_record,
)
from civitas.domain.events import CONCRETE_EVENT_TYPES, EVENT_TYPE_REGISTRY


def test_domain_event_exposes_event_type_name() -> None:
    """event_type matches the concrete class name."""
    event = TickStarted(tick=Tick(value=1))
    assert event.event_type == "TickStarted"
    assert isinstance(event, DomainEvent)


def test_events_are_frozen() -> None:
    """Domain events cannot be mutated in place."""
    event = TickCompleted(sequence=0, tick=Tick(value=2))
    with pytest.raises(ValidationError):
        event.sequence = 9  # type: ignore[misc]


def test_to_record_includes_event_type_and_round_trips() -> None:
    """Serialization includes event_type and deserializes losslessly."""
    original = ActionSelected(
        sequence=3,
        tick=Tick(value=4),
        agent_id=AgentId(value=1),
        action="eat",
        utility=0.75,
    )
    record = original.to_record()
    assert record["event_type"] == "ActionSelected"
    assert record["action"] == "eat"
    restored = event_from_record(record)
    assert restored == original
    assert isinstance(restored, ActionSelected)


def test_event_from_record_rejects_unknown_type() -> None:
    """Unknown event_type values are hard errors."""
    with pytest.raises(ValueError, match="unknown event_type"):
        event_from_record(
            {
                "event_type": "NotARealEvent",
                "sequence": 0,
                "tick": {"value": 0},
            }
        )


def test_event_from_record_requires_event_type() -> None:
    """Records without event_type are rejected."""
    with pytest.raises(ValueError, match="missing required key"):
        event_from_record({"sequence": 0, "tick": {"value": 0}})


def test_all_concrete_events_are_registered() -> None:
    """Every concrete event type is present in the registry."""
    assert len(CONCRETE_EVENT_TYPES) == len(EVENT_TYPE_REGISTRY)
    for event_cls in CONCRETE_EVENT_TYPES:
        assert EVENT_TYPE_REGISTRY[event_cls.__name__] is event_cls


def test_phase1_events_validate_payloads() -> None:
    """Representative Phase 1 events accept well-formed payloads."""
    tick = Tick(value=1)
    started = SimulationStarted(
        tick=Tick(value=0),
        seed=42,
        ticks=100,
        agent_count=10,
        run_name="default",
    )
    spawned = AgentSpawned(
        tick=tick,
        agent_id=AgentId(value=0),
        name="Ada",
        location_id=LocationId(value=0),
    )
    completed = ActionCompleted(
        tick=tick,
        agent_id=AgentId(value=0),
        action="rest",
        success=True,
    )
    consumed = ResourceConsumed(
        tick=tick,
        agent_id=AgentId(value=0),
        resource="food",
        amount=1,
    )
    decayed = NeedDecayed(
        tick=tick,
        agent_id=AgentId(value=0),
        need="food",
        previous=1.0,
        current=0.9,
    )
    finished = SimulationCompleted(tick=Tick(value=100), ticks_executed=100)
    assert started.run_name == "default"
    assert spawned.name == "Ada"
    assert completed.success is True
    assert consumed.amount == 1
    assert decayed.current == 0.9
    assert finished.ticks_executed == 100


def test_nested_ids_round_trip_through_record() -> None:
    """Nested AgentId/LocationId survive JSON record round-trips."""
    event = AgentSpawned(
        sequence=5,
        tick=Tick(value=0),
        agent_id=AgentId(value=9),
        name="Bea",
        location_id=LocationId(value=2),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentSpawned)
    assert restored.agent_id == AgentId(value=9)
    assert restored.location_id == LocationId(value=2)


def test_agent_moved_round_trips() -> None:
    """AgentMoved serializes nested location ids losslessly."""
    event = AgentMoved(
        sequence=2,
        tick=Tick(value=3),
        agent_id=AgentId(value=1),
        from_location_id=LocationId(value=0),
        to_location_id=LocationId(value=1),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentMoved)
    assert restored.from_location_id == LocationId(value=0)
    assert restored.to_location_id == LocationId(value=1)


def test_action_selected_optional_target_location() -> None:
    """ActionSelected accepts an optional MOVE destination."""
    event = ActionSelected(
        tick=Tick(value=1),
        agent_id=AgentId(value=0),
        action="move",
        utility=0.5,
        target_location_id=LocationId(value=3),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ActionSelected)
    assert restored.target_location_id == LocationId(value=3)


def test_resource_gathered_round_trips() -> None:
    """ResourceGathered serializes agent/location ids losslessly."""
    event = ResourceGathered(
        sequence=4,
        tick=Tick(value=2),
        agent_id=AgentId(value=1),
        location_id=LocationId(value=2),
        resource="wood",
        amount=1,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceGathered)
    assert restored.resource == "wood"
    assert restored.location_id == LocationId(value=2)


def test_action_selected_optional_target_resource() -> None:
    """ActionSelected accepts an optional GATHER resource."""
    event = ActionSelected(
        tick=Tick(value=1),
        agent_id=AgentId(value=0),
        action="gather",
        utility=0.4,
        target_resource="water",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ActionSelected)
    assert restored.target_resource == "water"


def test_population_observed_round_trips() -> None:
    """PopulationObserved serializes census fields losslessly."""
    event = PopulationObserved(
        sequence=7,
        tick=Tick(value=3),
        initial_count=10,
        total=10,
        alive=9,
        dead=1,
        location_counts=((0, 6), (1, 4)),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, PopulationObserved)
    assert restored.alive == 9
    assert restored.location_counts == ((0, 6), (1, 4))


def test_agent_born_round_trips() -> None:
    """AgentBorn serializes parent/child identity losslessly."""
    event = AgentBorn(
        sequence=4,
        tick=Tick(value=8),
        agent_id=AgentId(value=3),
        parent_id=AgentId(value=1),
        location_id=LocationId(value=0),
        name="Agent-3",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentBorn)
    assert restored.agent_id == AgentId(value=3)
    assert restored.parent_id == AgentId(value=1)
    assert restored.name == "Agent-3"


def test_agent_died_round_trips() -> None:
    """AgentDied serializes cause and identity losslessly."""
    event = AgentDied(
        sequence=5,
        tick=Tick(value=9),
        agent_id=AgentId(value=2),
        location_id=LocationId(value=0),
        cause="starvation",
        name="Agent-2",
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, AgentDied)
    assert restored.cause == "starvation"
    assert restored.agent_id == AgentId(value=2)


def test_money_transferred_round_trips() -> None:
    """MoneyTransferred serializes payer/payee/amount losslessly."""
    event = MoneyTransferred(
        sequence=6,
        tick=Tick(value=2),
        from_agent_id=AgentId(value=0),
        to_agent_id=AgentId(value=1),
        amount=4,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, MoneyTransferred)
    assert restored.amount == 4
    assert restored.from_agent_id == AgentId(value=0)


def test_resource_traded_round_trips() -> None:
    """ResourceTraded serializes trade terms losslessly."""
    event = ResourceTraded(
        sequence=7,
        tick=Tick(value=4),
        buyer_id=AgentId(value=0),
        seller_id=AgentId(value=2),
        resource="food",
        quantity=1,
        price=3,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceTraded)
    assert restored.resource == "food"
    assert restored.price == 3
    assert restored.seller_id == AgentId(value=2)


def test_resource_produced_round_trips() -> None:
    """ResourceProduced serializes recipe outputs losslessly."""
    event = ResourceProduced(
        sequence=8,
        tick=Tick(value=5),
        agent_id=AgentId(value=1),
        recipe_id="tools",
        outputs=(("tools", 1),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ResourceProduced)
    assert restored.recipe_id == "tools"
    assert restored.outputs == (("tools", 1),)
    assert restored.agent_id == AgentId(value=1)


def test_tax_collected_round_trips() -> None:
    """TaxCollected serializes levy amounts losslessly."""
    event = TaxCollected(
        sequence=9,
        tick=Tick(value=6),
        agent_id=AgentId(value=2),
        amount=3,
        treasury_after=11,
        government_id=GovernmentId(value=0),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, TaxCollected)
    assert restored.amount == 3
    assert restored.treasury_after == 11
    assert restored.agent_id == AgentId(value=2)
    assert restored.government_id == GovernmentId(value=0)


def test_market_created_and_listing_events_round_trip() -> None:
    """Market venue and listing events serialize losslessly."""
    created = MarketCreated(
        sequence=1,
        tick=Tick(value=0),
        market_id=MarketId(value=0),
        location_id=LocationId(value=0),
        name="Camp Market",
    )
    assert isinstance(event_from_record(created.to_record()), MarketCreated)

    posted = ListingPosted(
        sequence=2,
        tick=Tick(value=1),
        market_id=MarketId(value=0),
        listing_id=ListingId(value=0),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=2,
        unit_price=1,
    )
    restored_posted = event_from_record(posted.to_record())
    assert isinstance(restored_posted, ListingPosted)
    assert restored_posted.quantity == 2

    filled = ListingFilled(
        sequence=3,
        tick=Tick(value=2),
        market_id=MarketId(value=0),
        listing_id=ListingId(value=0),
        buyer_id=AgentId(value=2),
        seller_id=AgentId(value=1),
        resource="food",
        quantity=1,
        unit_price=1,
        total_price=1,
    )
    restored_filled = event_from_record(filled.to_record())
    assert isinstance(restored_filled, ListingFilled)
    assert restored_filled.total_price == 1

    fee = MarketFeeCollected(
        sequence=4,
        tick=Tick(value=2),
        market_id=MarketId(value=0),
        listing_id=ListingId(value=0),
        buyer_id=AgentId(value=2),
        amount=1,
        treasury_after=3,
        government_id=GovernmentId(value=0),
    )
    restored_fee = event_from_record(fee.to_record())
    assert isinstance(restored_fee, MarketFeeCollected)
    assert restored_fee.amount == 1
    assert restored_fee.treasury_after == 3
    assert restored_fee.government_id == GovernmentId(value=0)


def test_market_observed_round_trips() -> None:
    """MarketObserved serializes open-book census fields losslessly."""
    event = MarketObserved(
        sequence=9,
        tick=Tick(value=3),
        market_count=1,
        listing_count=2,
        total_units=5,
        market_listings=((0, 2),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, MarketObserved)
    assert restored.total_units == 5
    assert restored.market_listings == ((0, 2),)


def test_price_observed_round_trips() -> None:
    """PriceObserved serializes quote tuples losslessly."""
    event = PriceObserved(
        sequence=10,
        tick=Tick(value=4),
        quote_count=1,
        quotes=((0, "food", 3, 2, None, 1, 2, 3),),
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, PriceObserved)
    assert restored.quote_count == 1
    assert restored.quotes[0][1] == "food"
    assert restored.quotes[0][2] == 3
    assert restored.quotes[0][4] is None


def test_wealth_observed_round_trips() -> None:
    """WealthObserved serializes census fields losslessly."""
    event = WealthObserved(
        sequence=8,
        tick=Tick(value=3),
        total=20,
        alive_total=15,
        dead_total=5,
        alive_count=3,
        mean_alive=5.0,
        min_alive=1,
        max_alive=9,
        treasury=4,
        government_treasury=2,
        institution_budget=1,
        society_total=27,
        treasury_share_bps=2592,
        median_alive=5,
        gini_bps=2000,
        top1_share_bps=6000,
        top10_share_bps=6000,
        zero_count=0,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, WealthObserved)
    assert restored.alive_total == 15
    assert restored.min_alive == 1
    assert restored.max_alive == 9
    assert restored.treasury == 4
    assert restored.government_treasury == 2
    assert restored.institution_budget == 1
    assert restored.society_total == 27
    assert restored.gini_bps == 2000
    assert restored.median_alive == 5


def test_relationship_updated_round_trips() -> None:
    """RelationshipUpdated serializes bond fields losslessly."""
    event = RelationshipUpdated(
        sequence=10,
        tick=Tick(value=4),
        from_agent_id=AgentId(value=0),
        to_agent_id=AgentId(value=2),
        affinity=0.35,
        trust=0.7,
        created=True,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, RelationshipUpdated)
    assert restored.affinity == 0.35
    assert restored.trust == 0.7
    assert restored.created is True
    assert restored.to_agent_id == AgentId(value=2)


def test_relationships_observed_round_trips() -> None:
    """RelationshipsObserved serializes census fields losslessly."""
    event = RelationshipsObserved(
        sequence=11,
        tick=Tick(value=5),
        bond_count=2,
        agents_with_bonds=1,
        living_bond_count=2,
        mean_affinity=0.25,
        min_affinity=-0.1,
        max_affinity=0.6,
        mean_trust=0.55,
        min_trust=0.4,
        max_trust=0.7,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, RelationshipsObserved)
    assert restored.bond_count == 2
    assert restored.living_bond_count == 2
    assert restored.min_affinity == -0.1
    assert restored.max_affinity == 0.6
    assert restored.mean_trust == 0.55
    assert restored.min_trust == 0.4
    assert restored.max_trust == 0.7


def test_reputation_observed_round_trips() -> None:
    """ReputationObserved serializes standing census fields losslessly."""
    event = ReputationObserved(
        sequence=12,
        tick=Tick(value=6),
        living_agent_count=3,
        mean_standing=0.375,
        median_standing_bps=3750,
        gini_standing_bps=2000,
        top_standing_share_bps=5000,
        agents_with_inbound_bonds=2,
        top_agent_id=AgentId(value=0),
        top_standing=0.75,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, ReputationObserved)
    assert restored.living_agent_count == 3
    assert restored.mean_standing == 0.375
    assert restored.median_standing_bps == 3750
    assert restored.gini_standing_bps == 2000
    assert restored.top_standing_share_bps == 5000
    assert restored.agents_with_inbound_bonds == 2
    assert restored.top_agent_id == AgentId(value=0)
    assert restored.top_standing == 0.75


def test_families_observed_round_trips() -> None:
    """FamiliesObserved serializes kinship census fields losslessly."""
    event = FamiliesObserved(
        sequence=13,
        tick=Tick(value=7),
        living_agent_count=5,
        founder_count=2,
        parented_count=3,
        orphan_count=1,
        living_with_living_parent=2,
        lineage_count=2,
        mean_lineage_size=2.5,
        max_lineage_size=3,
        max_generation_depth=2,
        parents_with_living_children=1,
        mean_living_children=2.0,
        max_living_children=2,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, FamiliesObserved)
    assert restored.founder_count == 2
    assert restored.parented_count == 3
    assert restored.orphan_count == 1
    assert restored.lineage_count == 2
    assert restored.mean_lineage_size == 2.5
    assert restored.max_generation_depth == 2
    assert restored.max_living_children == 2


def test_networks_observed_round_trips() -> None:
    """NetworksObserved serializes graph census fields losslessly."""
    event = NetworksObserved(
        sequence=14,
        tick=Tick(value=8),
        living_agent_count=4,
        directed_edge_count=3,
        undirected_edge_count=2,
        reciprocal_pair_count=1,
        reciprocity_rate=0.5,
        reciprocity_bps=5000,
        mean_degree=1.0,
        max_degree=2,
        max_degree_agent_id=AgentId(value=1),
        isolated_count=1,
        component_count=2,
        largest_component_size=3,
        mean_component_size=2.0,
        density=0.333333,
        density_bps=3333,
        strongest_from_id=AgentId(value=0),
        strongest_to_id=AgentId(value=1),
        strongest_strength=0.75,
    )
    restored = event_from_record(event.to_record())
    assert isinstance(restored, NetworksObserved)
    assert restored.directed_edge_count == 3
    assert restored.reciprocity_bps == 5000
    assert restored.max_degree_agent_id == AgentId(value=1)
    assert restored.component_count == 2
    assert restored.density_bps == 3333
    assert restored.strongest_from_id == AgentId(value=0)
    assert restored.strongest_strength == 0.75


def test_government_created_and_observed_round_trips() -> None:
    """Government create/observe events serialize losslessly."""
    created = GovernmentCreated(
        sequence=15,
        tick=Tick(value=0),
        government_id=GovernmentId(value=0),
        name="Camp Authority",
        seat_location_id=LocationId(value=0),
        jurisdiction=(0, 1, 2),
        leader_id=None,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, GovernmentCreated)
    assert restored_created.name == "Camp Authority"
    assert restored_created.jurisdiction == (0, 1, 2)

    observed = GovernmentsObserved(
        sequence=16,
        tick=Tick(value=9),
        government_count=1,
        covered_location_count=9,
        uncovered_location_count=0,
        total_treasury=4,
        led_count=0,
        vacant_leader_count=1,
        living_subject_count=5,
        mean_subjects=5.0,
        max_subjects=5,
        max_subjects_government_id=GovernmentId(value=0),
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, GovernmentsObserved)
    assert restored.covered_location_count == 9
    assert restored.total_treasury == 4
    assert restored.max_subjects_government_id == GovernmentId(value=0)


def test_law_created_and_observed_round_trips() -> None:
    """Law create/observe events serialize losslessly."""
    created = LawCreated(
        sequence=17,
        tick=Tick(value=0),
        law_id=LawId(value=0),
        government_id=GovernmentId(value=0),
        name="Camp Poll Tax",
        kind="tax_schedule",
        active=True,
        flat_amount=1,
        rate_bps=0,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, LawCreated)
    assert restored_created.name == "Camp Poll Tax"
    assert restored_created.kind == "tax_schedule"
    assert restored_created.flat_amount == 1

    observed = LawsObserved(
        sequence=18,
        tick=Tick(value=3),
        law_count=2,
        active_count=1,
        inactive_count=1,
        governments_with_active_laws=1,
        active_tax_schedule_count=1,
        active_market_fee_count=0,
        active_curriculum_count=0,
        active_calendar_count=0,
        active_ethics_count=0,
        active_assembly_count=0,
        active_sanitation_count=0,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, LawsObserved)
    assert restored.law_count == 2
    assert restored.active_count == 1
    assert restored.active_tax_schedule_count == 1
    assert restored.active_market_fee_count == 0
    assert restored.active_curriculum_count == 0
    assert restored.active_calendar_count == 0
    assert restored.active_ethics_count == 0
    assert restored.active_assembly_count == 0
    assert restored.active_sanitation_count == 0


def test_election_resolved_and_observed_round_trips() -> None:
    """Election resolve/observe events serialize losslessly."""
    resolved = ElectionResolved(
        sequence=19,
        tick=Tick(value=4),
        election_id=ElectionId(value=0),
        government_id=GovernmentId(value=0),
        winner_id=AgentId(value=1),
        franchise_count=3,
        ballot_count=3,
    )
    restored_resolved = event_from_record(resolved.to_record())
    assert isinstance(restored_resolved, ElectionResolved)
    assert restored_resolved.winner_id == AgentId(value=1)
    assert restored_resolved.franchise_count == 3

    observed = ElectionsObserved(
        sequence=20,
        tick=Tick(value=4),
        election_count=1,
        closed_count=1,
        open_count=0,
        governments_with_elections=1,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, ElectionsObserved)
    assert restored.election_count == 1
    assert restored.closed_count == 1


def test_institution_created_and_observed_round_trips() -> None:
    """Institution create/observe events serialize losslessly."""
    created = InstitutionCreated(
        sequence=21,
        tick=Tick(value=0),
        institution_id=InstitutionId(value=0),
        government_id=GovernmentId(value=0),
        location_id=LocationId(value=0),
        name="Camp Council",
        kind="council",
        active=True,
        officer_id=None,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, InstitutionCreated)
    assert restored_created.name == "Camp Council"
    assert restored_created.kind == "council"

    observed = InstitutionsObserved(
        sequence=22,
        tick=Tick(value=5),
        institution_count=1,
        active_count=1,
        inactive_count=0,
        governments_with_institutions=1,
        staffed_count=0,
        vacant_officer_count=1,
        active_council_count=1,
        active_guild_count=1,
        active_archive_count=1,
        active_bureaucracy_count=1,
        active_academy_count=1,
        active_temple_count=1,
        active_school_count=1,
        active_lyceum_count=1,
        active_hospital_count=1,
        total_budget=3,
        funded_count=1,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, InstitutionsObserved)
    assert restored.institution_count == 1
    assert restored.active_council_count == 1
    assert restored.active_guild_count == 1
    assert restored.active_archive_count == 1
    assert restored.active_bureaucracy_count == 1
    assert restored.active_academy_count == 1
    assert restored.active_temple_count == 1
    assert restored.active_school_count == 1
    assert restored.active_lyceum_count == 1
    assert restored.active_hospital_count == 1
    assert restored.total_budget == 3
    assert restored.funded_count == 1

    funded = InstitutionFunded(
        sequence=23,
        tick=Tick(value=2),
        institution_id=InstitutionId(value=0),
        government_id=GovernmentId(value=0),
        amount=3,
        budget_after=3,
        treasury_after=7,
    )
    restored_funded = event_from_record(funded.to_record())
    assert isinstance(restored_funded, InstitutionFunded)
    assert restored_funded.amount == 3
    assert restored_funded.budget_after == 3
    assert restored_funded.treasury_after == 7


def test_city_created_and_observed_round_trips() -> None:
    """City create/observe events serialize losslessly."""
    created = CityCreated(
        sequence=23,
        tick=Tick(value=0),
        city_id=CityId(value=0),
        government_id=GovernmentId(value=0),
        location_id=LocationId(value=0),
        name="Camp City",
        kind="settlement",
        active=True,
        is_capital=True,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, CityCreated)
    assert restored_created.name == "Camp City"
    assert restored_created.is_capital is True

    observed = CitiesObserved(
        sequence=24,
        tick=Tick(value=6),
        city_count=2,
        active_count=2,
        inactive_count=0,
        governments_with_cities=1,
        capital_count=1,
        total_residents=4,
        mean_residents=2.0,
        max_residents=3,
        max_residents_city_id=CityId(value=0),
        active_settlement_count=1,
        active_outpost_count=1,
        active_library_count=1,
        active_forum_count=1,
        active_sanctuary_count=1,
        active_agora_count=1,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, CitiesObserved)
    assert restored.city_count == 2
    assert restored.total_residents == 4
    assert restored.active_outpost_count == 1
    assert restored.active_library_count == 1
    assert restored.active_forum_count == 1
    assert restored.active_sanctuary_count == 1
    assert restored.active_agora_count == 1

    legacy = CitiesObserved(
        sequence=25,
        tick=Tick(value=6),
        city_count=1,
        active_count=1,
        inactive_count=0,
        governments_with_cities=1,
        capital_count=1,
        total_residents=4,
        mean_residents=4.0,
        max_residents=4,
        max_residents_city_id=CityId(value=0),
        active_settlement_count=1,
    )
    assert legacy.active_outpost_count == 0
    assert legacy.active_library_count == 0
    assert legacy.active_forum_count == 0
    assert legacy.active_sanctuary_count == 0
    assert legacy.active_agora_count == 0


def test_infrastructure_created_and_observed_round_trips() -> None:
    """Infrastructure create/observe events serialize losslessly."""
    created = InfrastructureCreated(
        sequence=25,
        tick=Tick(value=0),
        infrastructure_id=InfrastructureId(value=0),
        government_id=GovernmentId(value=0),
        city_id=CityId(value=0),
        location_id=LocationId(value=0),
        name="Camp Well",
        kind="well",
        active=True,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, InfrastructureCreated)
    assert restored_created.name == "Camp Well"
    assert restored_created.kind == "well"

    observed = InfrastructuresObserved(
        sequence=26,
        tick=Tick(value=7),
        infrastructure_count=1,
        active_count=1,
        inactive_count=0,
        governments_with_infrastructure=1,
        cities_with_infrastructure=1,
        active_well_count=1,
        active_storehouse_count=1,
        active_road_count=1,
        active_scriptorium_count=1,
        active_stoa_count=1,
        active_observatory_count=1,
        active_shrine_count=1,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, InfrastructuresObserved)
    assert restored.active_well_count == 1
    assert restored.active_storehouse_count == 1
    assert restored.active_road_count == 1
    assert restored.active_scriptorium_count == 1
    assert restored.active_stoa_count == 1
    assert restored.active_observatory_count == 1
    assert restored.active_shrine_count == 1

    funded = InfrastructureBuilt(
        sequence=27,
        tick=Tick(value=3),
        infrastructure_id=InfrastructureId(value=1),
        government_id=GovernmentId(value=0),
        city_id=CityId(value=0),
        location_id=LocationId(value=0),
        name="Paid Well",
        kind="well",
        cost=5,
        treasury_after=3,
    )
    restored_built = event_from_record(funded.to_record())
    assert isinstance(restored_built, InfrastructureBuilt)
    assert restored_built.cost == 5
    assert restored_built.treasury_after == 3

    commissioned = InfrastructureCommissioned(
        sequence=28,
        tick=Tick(value=4),
        infrastructure_id=InfrastructureId(value=2),
        government_id=GovernmentId(value=0),
        institution_id=InstitutionId(value=0),
        city_id=CityId(value=0),
        location_id=LocationId(value=0),
        name="Council Well",
        kind="well",
        cost=5,
        budget_after=2,
    )
    restored_commissioned = event_from_record(commissioned.to_record())
    assert isinstance(restored_commissioned, InfrastructureCommissioned)
    assert restored_commissioned.cost == 5
    assert restored_commissioned.budget_after == 2
    assert restored_commissioned.institution_id.value == 0


def test_technology_created_and_observed_round_trips() -> None:
    """Technology create/observe events serialize losslessly."""
    created = TechnologyCreated(
        sequence=27,
        tick=Tick(value=0),
        technology_id=TechnologyId(value=0),
        name="Camp Fire",
        kind="fire",
        discovered=True,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, TechnologyCreated)
    assert restored_created.discovered is True

    observed = TechnologiesObserved(
        sequence=28,
        tick=Tick(value=8),
        technology_count=11,
        discovered_count=1,
        undiscovered_count=10,
        discovered_fire_count=1,
        discovered_pottery_count=0,
        discovered_irrigation_count=0,
        discovered_metallurgy_count=0,
        discovered_writing_count=0,
        discovered_mathematics_count=0,
        discovered_astronomy_count=0,
        discovered_philosophy_count=0,
        discovered_logic_count=0,
        discovered_rhetoric_count=0,
        discovered_medicine_count=0,
        locked_count=9,
        researchable_count=1,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, TechnologiesObserved)
    assert restored.discovered_fire_count == 1
    assert restored.discovered_irrigation_count == 0
    assert restored.discovered_metallurgy_count == 0
    assert restored.discovered_writing_count == 0
    assert restored.discovered_mathematics_count == 0
    assert restored.discovered_astronomy_count == 0
    assert restored.discovered_philosophy_count == 0
    assert restored.discovered_logic_count == 0
    assert restored.discovered_rhetoric_count == 0
    assert restored.discovered_medicine_count == 0
    assert restored.researchable_count == 1


def test_research_events_round_trip() -> None:
    """Research progress/discovery/observe events serialize losslessly."""
    progressed = ResearchProgressed(
        sequence=29,
        tick=Tick(value=3),
        technology_id=TechnologyId(value=1),
        points_after=3,
        threshold=10,
        delta=1,
    )
    restored_progressed = event_from_record(progressed.to_record())
    assert isinstance(restored_progressed, ResearchProgressed)
    assert restored_progressed.points_after == 3

    discovered = TechnologyDiscovered(
        sequence=30,
        tick=Tick(value=10),
        technology_id=TechnologyId(value=1),
        name="Camp Pottery",
        kind="pottery",
    )
    restored_discovered = event_from_record(discovered.to_record())
    assert isinstance(restored_discovered, TechnologyDiscovered)
    assert restored_discovered.kind == "pottery"

    observed = ResearchObserved(
        sequence=31,
        tick=Tick(value=4),
        progress_count=1,
        total_points=4,
        total_threshold=10,
        total_remaining=6,
        completion_bps=4_000,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, ResearchObserved)
    assert restored_observed.completion_bps == 4_000


def test_innovation_events_round_trip() -> None:
    """Innovation create/activate/observe events serialize losslessly."""
    created = InnovationCreated(
        sequence=32,
        tick=Tick(value=0),
        innovation_id=InnovationId(value=0),
        technology_id=TechnologyId(value=0),
        name="Camp Fire Hearth",
        kind="fire_hearth",
        active=True,
    )
    restored_created = event_from_record(created.to_record())
    assert isinstance(restored_created, InnovationCreated)
    assert restored_created.active is True

    activated = InnovationActivated(
        sequence=33,
        tick=Tick(value=10),
        innovation_id=InnovationId(value=1),
        technology_id=TechnologyId(value=1),
        name="Camp Pottery Craft",
        kind="pottery_craft",
    )
    restored_activated = event_from_record(activated.to_record())
    assert isinstance(restored_activated, InnovationActivated)
    assert restored_activated.kind == "pottery_craft"

    observed = InnovationsObserved(
        sequence=34,
        tick=Tick(value=8),
        innovation_count=11,
        active_count=1,
        inactive_count=10,
        active_fire_hearth_count=1,
        active_pottery_craft_count=0,
        active_irrigation_canal_count=0,
        active_forge_count=0,
        active_scribe_count=0,
        active_abacus_count=0,
        active_star_chart_count=0,
        active_dialectic_count=0,
        active_syllogism_count=0,
        active_oration_count=0,
        active_remedy_count=0,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, InnovationsObserved)
    assert restored_observed.active_fire_hearth_count == 1
    assert restored_observed.active_irrigation_canal_count == 0
    assert restored_observed.active_forge_count == 0
    assert restored_observed.active_scribe_count == 0
    assert restored_observed.active_abacus_count == 0
    assert restored_observed.active_star_chart_count == 0
    assert restored_observed.active_dialectic_count == 0
    assert restored_observed.active_syllogism_count == 0
    assert restored_observed.active_oration_count == 0
    assert restored_observed.active_remedy_count == 0


def test_knowledge_events_round_trip() -> None:
    """Knowledge learn/observe events serialize losslessly."""
    learned = KnowledgeLearned(
        sequence=35,
        tick=Tick(value=10),
        agent_id=AgentId(value=0),
        fact="pottery",
        source="bootstrap",
        teacher_id=None,
    )
    restored_learned = event_from_record(learned.to_record())
    assert isinstance(restored_learned, KnowledgeLearned)
    assert restored_learned.fact == "pottery"
    assert restored_learned.teacher_id is None

    peer = KnowledgeLearned(
        sequence=36,
        tick=Tick(value=10),
        agent_id=AgentId(value=1),
        fact="pottery",
        source="peer",
        teacher_id=AgentId(value=0),
    )
    restored_peer = event_from_record(peer.to_record())
    assert isinstance(restored_peer, KnowledgeLearned)
    assert restored_peer.teacher_id is not None
    assert restored_peer.teacher_id.value == 0

    observed = KnowledgeObserved(
        sequence=37,
        tick=Tick(value=4),
        living_count=3,
        discovered_technology_count=1,
        fire_knower_count=3,
        pottery_knower_count=0,
        irrigation_knower_count=0,
        metallurgy_knower_count=0,
        writing_knower_count=0,
        mathematics_knower_count=0,
        astronomy_knower_count=0,
        philosophy_knower_count=0,
        logic_knower_count=0,
        rhetoric_knower_count=0,
        medicine_knower_count=0,
        total_fact_instances=3,
        coverage_bps=10_000,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, KnowledgeObserved)
    assert restored_observed.irrigation_knower_count == 0
    assert restored_observed.metallurgy_knower_count == 0
    assert restored_observed.writing_knower_count == 0
    assert restored_observed.mathematics_knower_count == 0
    assert restored_observed.astronomy_knower_count == 0
    assert restored_observed.philosophy_knower_count == 0
    assert restored_observed.logic_knower_count == 0
    assert restored_observed.rhetoric_knower_count == 0
    assert restored_observed.medicine_knower_count == 0
    assert restored_observed.coverage_bps == 10_000


def test_cognition_events_round_trip() -> None:
    """Memory recorded / cognition observe events serialize losslessly."""
    recorded = MemoryRecorded(
        sequence=38,
        tick=Tick(value=2),
        agent_id=AgentId(value=0),
        kind="episode",
        content="loc=0|food=1.000|water=1.000|energy=1.000|facts=fire",
    )
    restored_recorded = event_from_record(recorded.to_record())
    assert isinstance(restored_recorded, MemoryRecorded)
    assert restored_recorded.kind == "episode"

    observed = CognitionObserved(
        sequence=39,
        tick=Tick(value=2),
        living_count=3,
        total_records=6,
        agents_with_memory=3,
        episode_records=3,
        reflection_records=3,
        belief_count=3,
        mean_records_bps=20_000,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, CognitionObserved)
    assert restored_observed.reflection_records == 3

    reflected = AgentReflected(
        sequence=40,
        tick=Tick(value=2),
        agent_id=AgentId(value=0),
        proposition="priority:food",
        confidence=0.75,
        model_name="seeded-mock",
    )
    restored_reflected = event_from_record(reflected.to_record())
    assert isinstance(restored_reflected, AgentReflected)
    assert restored_reflected.proposition == "priority:food"


def test_planning_events_round_trip() -> None:
    """Plan update/observe events serialize losslessly."""
    updated = PlanUpdated(
        sequence=41,
        tick=Tick(value=3),
        agent_id=AgentId(value=1),
        goal_kind="satisfy_food",
        priority=0.8,
        target="food",
    )
    restored_updated = event_from_record(updated.to_record())
    assert isinstance(restored_updated, PlanUpdated)
    assert restored_updated.target == "food"

    observed = PlansObserved(
        sequence=42,
        tick=Tick(value=3),
        living_count=3,
        agents_with_plans=3,
        satisfy_food_count=2,
        satisfy_water_count=1,
        satisfy_energy_count=0,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, PlansObserved)
    assert restored_observed.satisfy_food_count == 2


def test_retrieval_events_round_trip() -> None:
    """Memory retrieved / retrieval observe events serialize losslessly."""
    retrieved = MemoryRetrieved(
        sequence=43,
        tick=Tick(value=4),
        agent_id=AgentId(value=2),
        query="water",
        retrieved_count=2,
        summary="episode@3|reflection@4",
    )
    restored_retrieved = event_from_record(retrieved.to_record())
    assert isinstance(restored_retrieved, MemoryRetrieved)
    assert restored_retrieved.query == "water"
    assert restored_retrieved.summary == "episode@3|reflection@4"

    observed = RetrievalObserved(
        sequence=44,
        tick=Tick(value=4),
        living_count=3,
        agents_with_context=3,
        total_retrieved=6,
        mean_retrieved_bps=20_000,
    )
    restored_observed = event_from_record(observed.to_record())
    assert isinstance(restored_observed, RetrievalObserved)
    assert restored_observed.total_retrieved == 6


def test_effects_events_round_trip() -> None:
    """Effects observe events serialize losslessly."""
    observed = EffectsObserved(
        sequence=45,
        tick=Tick(value=5),
        living_count=4,
        fire_hearth_active=1,
        pottery_craft_active=0,
        rest_restore_bps=2500,
        water_gather_amount=1,
        active_well_count=1,
        drink_restore_bps=3500,
        active_storehouse_count=1,
        food_gather_amount=2,
        active_road_count=1,
        move_energy_cost_bps=300,
        active_guild_count=1,
        produce_energy_cost_bps=800,
    )
    restored = event_from_record(observed.to_record())
    assert isinstance(restored, EffectsObserved)
    assert restored.rest_restore_bps == 2500
    assert restored.fire_hearth_active == 1
    assert restored.active_well_count == 1
    assert restored.drink_restore_bps == 3500
    assert restored.active_storehouse_count == 1
    assert restored.food_gather_amount == 2
    assert restored.active_road_count == 1
    assert restored.move_energy_cost_bps == 300
    assert restored.active_guild_count == 1
    assert restored.produce_energy_cost_bps == 800
