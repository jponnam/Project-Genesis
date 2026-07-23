"""Domain events for event-sourced simulation.

Everything important becomes a ``DomainEvent``. Events are immutable,
JSON-serializable, and totally ordered by ``sequence`` within a run.
Systems communicate exclusively through these events.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from civitas.domain.ids import (
    AgentId,
    CityId,
    ElectionId,
    GovernmentId,
    InfrastructureId,
    InnovationId,
    InstitutionId,
    LawId,
    ListingId,
    LocationId,
    MarketId,
    TechnologyId,
)
from civitas.domain.time import Tick
from civitas.domain.types import (
    AffinityScore,
    MemoryContentStr,
    NonEmptyStr,
    NonNegativeInt,
    UnitInterval,
)


class DomainEvent(BaseModel):
    """Base class for all domain events.

    Attributes:
        sequence: Total order index within a run (stamped by the event bus).
        tick: Simulation tick at which the event occurred.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    sequence: NonNegativeInt = Field(
        default=0,
        description="Total order index; assigned by EventBus on publish.",
    )
    tick: Tick = Field(description="Tick at which this event occurred.")

    @property
    def event_type(self) -> str:
        """Stable type name used for serialization and dispatch."""
        return type(self).__name__

    def to_record(self) -> dict[str, Any]:
        """Serialize to a JSON-ready mapping including ``event_type``."""
        payload = self.model_dump(mode="json")
        payload["event_type"] = self.event_type
        return payload


class SimulationStarted(DomainEvent):
    """Emitted once when a simulation run begins."""

    seed: NonNegativeInt
    ticks: NonNegativeInt
    agent_count: NonNegativeInt
    run_name: NonEmptyStr


class SimulationCompleted(DomainEvent):
    """Emitted once when a simulation run finishes."""

    ticks_executed: NonNegativeInt


class TickStarted(DomainEvent):
    """Emitted at the beginning of a tick's agent-update cycle."""


class TickCompleted(DomainEvent):
    """Emitted after all agents have been updated for a tick."""


class LocationCreated(DomainEvent):
    """Emitted when a location is added to the world map."""

    location_id: LocationId
    name: NonEmptyStr
    x: int
    y: int
    kind: NonEmptyStr


class AgentSpawned(DomainEvent):
    """Emitted when an agent is created in the world."""

    agent_id: AgentId
    name: NonEmptyStr
    location_id: LocationId


class AgentMoved(DomainEvent):
    """Emitted when an agent relocates from one location to another."""

    agent_id: AgentId
    from_location_id: LocationId
    to_location_id: LocationId


class ActionSelected(DomainEvent):
    """Emitted when a policy selects an action for an agent."""

    agent_id: AgentId
    action: NonEmptyStr
    utility: float
    target_location_id: LocationId | None = None
    target_resource: NonEmptyStr | None = None
    target_agent_id: AgentId | None = None


class ActionCompleted(DomainEvent):
    """Emitted when an action has been applied to world state."""

    agent_id: AgentId
    action: NonEmptyStr
    success: bool


class ResourceConsumed(DomainEvent):
    """Emitted when an agent consumes a resource from inventory."""

    agent_id: AgentId
    resource: NonEmptyStr
    amount: NonNegativeInt


class ResourceGathered(DomainEvent):
    """Emitted when an agent gathers a resource from a location deposit."""

    agent_id: AgentId
    location_id: LocationId
    resource: NonEmptyStr
    amount: NonNegativeInt


class NeedDecayed(DomainEvent):
    """Emitted when a homeostatic need changes due to decay or recovery."""

    agent_id: AgentId
    need: NonEmptyStr
    previous: UnitInterval
    current: UnitInterval


class PopulationObserved(DomainEvent):
    """Emitted when a population census is taken."""

    initial_count: NonNegativeInt
    total: NonNegativeInt
    alive: NonNegativeInt
    dead: NonNegativeInt
    # (location_id, agent_count) pairs in ascending location_id order.
    location_counts: tuple[tuple[int, int], ...] = ()


class AgentBorn(DomainEvent):
    """Emitted when a living parent produces a new agent."""

    agent_id: AgentId
    parent_id: AgentId
    location_id: LocationId
    name: NonEmptyStr


class AgentDied(DomainEvent):
    """Emitted when a living agent transitions to dead."""

    agent_id: AgentId
    location_id: LocationId
    cause: NonEmptyStr
    name: NonEmptyStr


class MoneyTransferred(DomainEvent):
    """Emitted when money moves from one living agent to another."""

    from_agent_id: AgentId
    to_agent_id: AgentId
    amount: NonNegativeInt


class TaxCollected(DomainEvent):
    """Emitted when an agent pays tax into a public treasury."""

    agent_id: AgentId
    amount: NonNegativeInt
    treasury_after: NonNegativeInt
    government_id: GovernmentId | None = None


class ResourceTraded(DomainEvent):
    """Emitted when a buyer purchases inventory from a seller."""

    buyer_id: AgentId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    price: NonNegativeInt


class ResourceProduced(DomainEvent):
    """Emitted when an agent crafts outputs from a production recipe."""

    agent_id: AgentId
    recipe_id: NonEmptyStr
    # (resource, quantity) pairs in ascending resource name order.
    outputs: tuple[tuple[str, int], ...] = ()


class MarketCreated(DomainEvent):
    """Emitted when a market venue is added to the world."""

    market_id: MarketId
    location_id: LocationId
    name: NonEmptyStr


class GovernmentCreated(DomainEvent):
    """Emitted when a government / polity is added to the world."""

    government_id: GovernmentId
    name: NonEmptyStr
    seat_location_id: LocationId
    # Location ids in ascending order.
    jurisdiction: tuple[int, ...] = ()
    leader_id: AgentId | None = None


class LawCreated(DomainEvent):
    """Emitted when a statute is added to the world."""

    law_id: LawId
    government_id: GovernmentId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = True
    flat_amount: NonNegativeInt = 0
    rate_bps: NonNegativeInt = 0


class InstitutionCreated(DomainEvent):
    """Emitted when an institution is added to the world."""

    institution_id: InstitutionId
    government_id: GovernmentId
    location_id: LocationId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = True
    officer_id: AgentId | None = None


class InstitutionFunded(DomainEvent):
    """Emitted when a government treasury funds an institution budget."""

    institution_id: InstitutionId
    government_id: GovernmentId
    amount: NonNegativeInt
    budget_after: NonNegativeInt
    treasury_after: NonNegativeInt


class CityCreated(DomainEvent):
    """Emitted when a city / settlement is added to the world."""

    city_id: CityId
    government_id: GovernmentId
    location_id: LocationId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = True
    is_capital: bool = False


class InfrastructureCreated(DomainEvent):
    """Emitted when an infrastructure piece is added to the world."""

    infrastructure_id: InfrastructureId
    government_id: GovernmentId
    city_id: CityId
    location_id: LocationId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = True


class InfrastructureBuilt(DomainEvent):
    """Emitted when a government pays to construct infrastructure."""

    infrastructure_id: InfrastructureId
    government_id: GovernmentId
    city_id: CityId
    location_id: LocationId
    name: NonEmptyStr
    kind: NonEmptyStr
    cost: NonNegativeInt
    treasury_after: NonNegativeInt


class InfrastructureCommissioned(DomainEvent):
    """Emitted when an institution budget pays to construct infrastructure."""

    infrastructure_id: InfrastructureId
    government_id: GovernmentId
    institution_id: InstitutionId
    city_id: CityId
    location_id: LocationId
    name: NonEmptyStr
    kind: NonEmptyStr
    cost: NonNegativeInt
    budget_after: NonNegativeInt


class ListingPosted(DomainEvent):
    """Emitted when a seller escrows goods onto a market listing."""

    market_id: MarketId
    listing_id: ListingId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    unit_price: NonNegativeInt


class ListingFilled(DomainEvent):
    """Emitted when a buyer purchases units from a market listing."""

    market_id: MarketId
    listing_id: ListingId
    buyer_id: AgentId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt
    unit_price: NonNegativeInt
    total_price: NonNegativeInt


class MarketFeeCollected(DomainEvent):
    """Emitted when a market fill collects a MARKET_FEE statute charge."""

    market_id: MarketId
    listing_id: ListingId
    buyer_id: AgentId
    amount: NonNegativeInt
    treasury_after: NonNegativeInt
    government_id: GovernmentId | None = None


class ListingCancelled(DomainEvent):
    """Emitted when a seller cancels an open listing and recovers escrow."""

    market_id: MarketId
    listing_id: ListingId
    seller_id: AgentId
    resource: NonEmptyStr
    quantity: NonNegativeInt


class MarketObserved(DomainEvent):
    """Emitted when an open-book market census is taken."""

    market_count: NonNegativeInt
    listing_count: NonNegativeInt
    total_units: NonNegativeInt
    # (market_id, listing_count) pairs in ascending market_id order.
    market_listings: tuple[tuple[int, int], ...] = ()


class PriceObserved(DomainEvent):
    """Emitted when a market price census is taken.

    Each quote tuple is:
    ``(market_id, resource, best_ask, ask_quantity, last_trade,
    listing_count, total_units, suggested_unit_price)`` with ``None``
    allowed for missing best ask / last trade.
    """

    quote_count: NonNegativeInt
    quotes: tuple[
        tuple[int, str, int | None, int, int | None, int, int, int],
        ...,
    ] = ()


class WealthObserved(DomainEvent):
    """Emitted when a wealth census is taken."""

    total: NonNegativeInt
    alive_total: NonNegativeInt
    dead_total: NonNegativeInt
    alive_count: NonNegativeInt
    mean_alive: float
    min_alive: NonNegativeInt | None = None
    max_alive: NonNegativeInt | None = None
    treasury: NonNegativeInt = 0
    government_treasury: NonNegativeInt = 0
    institution_budget: NonNegativeInt = 0
    society_total: NonNegativeInt = 0
    treasury_share_bps: NonNegativeInt = 0
    median_alive: NonNegativeInt | None = None
    gini_bps: NonNegativeInt = 0
    top1_share_bps: NonNegativeInt = 0
    top10_share_bps: NonNegativeInt = 0
    zero_count: NonNegativeInt = 0


class RelationshipUpdated(DomainEvent):
    """Emitted when a directed relationship bond is created or updated."""

    from_agent_id: AgentId
    to_agent_id: AgentId
    affinity: AffinityScore
    trust: UnitInterval
    created: bool = False


class RelationshipsObserved(DomainEvent):
    """Emitted when a relationship census is taken."""

    bond_count: NonNegativeInt
    agents_with_bonds: NonNegativeInt
    living_bond_count: NonNegativeInt
    mean_affinity: float
    min_affinity: AffinityScore | None = None
    max_affinity: AffinityScore | None = None
    mean_trust: float = 0.0
    min_trust: UnitInterval | None = None
    max_trust: UnitInterval | None = None


class ReputationObserved(DomainEvent):
    """Emitted when a public-standing (reputation) census is taken."""

    living_agent_count: NonNegativeInt
    mean_standing: UnitInterval
    median_standing_bps: NonNegativeInt
    gini_standing_bps: NonNegativeInt
    top_standing_share_bps: NonNegativeInt
    agents_with_inbound_bonds: NonNegativeInt
    top_agent_id: AgentId | None = None
    top_standing: UnitInterval | None = None


class FamiliesObserved(DomainEvent):
    """Emitted when a kinship / family-lineage census is taken."""

    living_agent_count: NonNegativeInt
    founder_count: NonNegativeInt
    parented_count: NonNegativeInt
    orphan_count: NonNegativeInt
    living_with_living_parent: NonNegativeInt
    lineage_count: NonNegativeInt
    mean_lineage_size: float
    max_lineage_size: NonNegativeInt
    max_generation_depth: NonNegativeInt
    parents_with_living_children: NonNegativeInt
    mean_living_children: float
    max_living_children: NonNegativeInt


class NetworksObserved(DomainEvent):
    """Emitted when a social-network census is taken."""

    living_agent_count: NonNegativeInt
    directed_edge_count: NonNegativeInt
    undirected_edge_count: NonNegativeInt
    reciprocal_pair_count: NonNegativeInt
    reciprocity_rate: float
    reciprocity_bps: NonNegativeInt
    mean_degree: float
    max_degree: NonNegativeInt
    max_degree_agent_id: AgentId | None = None
    isolated_count: NonNegativeInt
    component_count: NonNegativeInt
    largest_component_size: NonNegativeInt
    mean_component_size: float
    density: float
    density_bps: NonNegativeInt
    strongest_from_id: AgentId | None = None
    strongest_to_id: AgentId | None = None
    strongest_strength: UnitInterval | None = None


class GovernmentsObserved(DomainEvent):
    """Emitted when a government census is taken."""

    government_count: NonNegativeInt
    covered_location_count: NonNegativeInt
    uncovered_location_count: NonNegativeInt
    total_treasury: NonNegativeInt
    led_count: NonNegativeInt
    vacant_leader_count: NonNegativeInt
    living_subject_count: NonNegativeInt
    mean_subjects: float
    max_subjects: NonNegativeInt
    max_subjects_government_id: GovernmentId | None = None


class LawsObserved(DomainEvent):
    """Emitted when a statute census is taken."""

    law_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_active_laws: NonNegativeInt
    active_tax_schedule_count: NonNegativeInt
    active_market_fee_count: NonNegativeInt
    active_curriculum_count: NonNegativeInt
    active_calendar_count: NonNegativeInt
    active_ethics_count: NonNegativeInt
    active_assembly_count: NonNegativeInt
    active_sanitation_count: NonNegativeInt = 0
    active_quarantine_count: NonNegativeInt = 0
    active_building_codes_count: NonNegativeInt = 0
    active_zoning_count: NonNegativeInt = 0
    active_passage_count: NonNegativeInt = 0
    active_customs_count: NonNegativeInt = 0
    active_land_tenure_count: NonNegativeInt = 0
    active_conservation_count: NonNegativeInt = 0
    active_labor_count: NonNegativeInt = 0
    active_sumptuary_count: NonNegativeInt = 0
    active_mineral_rights_count: NonNegativeInt = 0
    active_safety_codes_count: NonNegativeInt = 0
    active_timber_rights_count: NonNegativeInt = 0
    active_forest_management_count: NonNegativeInt = 0
    active_firing_codes_count: NonNegativeInt = 0


class ElectionResolved(DomainEvent):
    """Emitted when an election is conducted and a winner applied."""

    election_id: ElectionId
    government_id: GovernmentId
    winner_id: AgentId | None = None
    franchise_count: NonNegativeInt
    ballot_count: NonNegativeInt


class ElectionsObserved(DomainEvent):
    """Emitted when an election-archive census is taken."""

    election_count: NonNegativeInt
    closed_count: NonNegativeInt
    open_count: NonNegativeInt
    governments_with_elections: NonNegativeInt


class InstitutionsObserved(DomainEvent):
    """Emitted when an institution census is taken."""

    institution_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_institutions: NonNegativeInt
    staffed_count: NonNegativeInt
    vacant_officer_count: NonNegativeInt
    active_council_count: NonNegativeInt
    active_guild_count: NonNegativeInt = 0
    active_archive_count: NonNegativeInt = 0
    active_bureaucracy_count: NonNegativeInt = 0
    active_academy_count: NonNegativeInt = 0
    active_temple_count: NonNegativeInt = 0
    active_school_count: NonNegativeInt = 0
    active_lyceum_count: NonNegativeInt = 0
    active_hospital_count: NonNegativeInt = 0
    active_apothecary_count: NonNegativeInt = 0
    active_collegium_count: NonNegativeInt = 0
    active_workshop_count: NonNegativeInt = 0
    active_mason_count: NonNegativeInt = 0
    active_architect_count: NonNegativeInt = 0
    active_caravan_count: NonNegativeInt = 0
    active_merchant_count: NonNegativeInt = 0
    active_cartographer_count: NonNegativeInt = 0
    active_granary_count: NonNegativeInt = 0
    active_husbandman_count: NonNegativeInt = 0
    active_agronomist_count: NonNegativeInt = 0
    active_weaver_count: NonNegativeInt = 0
    active_dyer_count: NonNegativeInt = 0
    active_tailor_count: NonNegativeInt = 0
    active_miner_count: NonNegativeInt = 0
    active_smelter_count: NonNegativeInt = 0
    active_smith_count: NonNegativeInt = 0
    active_woodcutter_count: NonNegativeInt = 0
    active_joiner_count: NonNegativeInt = 0
    active_carver_count: NonNegativeInt = 0
    active_potter_count: NonNegativeInt = 0
    total_budget: NonNegativeInt = 0
    funded_count: NonNegativeInt = 0


class CitiesObserved(DomainEvent):
    """Emitted when a city census is taken."""

    city_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_cities: NonNegativeInt
    capital_count: NonNegativeInt
    total_residents: NonNegativeInt
    mean_residents: float
    max_residents: NonNegativeInt
    max_residents_city_id: CityId | None = None
    active_settlement_count: NonNegativeInt
    active_outpost_count: NonNegativeInt = 0
    active_library_count: NonNegativeInt = 0
    active_forum_count: NonNegativeInt = 0
    active_sanctuary_count: NonNegativeInt = 0
    active_agora_count: NonNegativeInt = 0
    active_infirmary_count: NonNegativeInt = 0
    active_lazaretto_count: NonNegativeInt = 0
    active_foundry_count: NonNegativeInt = 0
    active_quarry_count: NonNegativeInt = 0
    active_harbor_count: NonNegativeInt = 0
    active_entrepot_count: NonNegativeInt = 0
    active_farmstead_count: NonNegativeInt = 0
    active_pastoral_count: NonNegativeInt = 0
    active_mill_town_count: NonNegativeInt = 0
    active_emporium_count: NonNegativeInt = 0
    active_mining_camp_count: NonNegativeInt = 0
    active_ironworks_count: NonNegativeInt = 0
    active_timber_town_count: NonNegativeInt = 0
    active_guildhall_count: NonNegativeInt = 0


class InfrastructuresObserved(DomainEvent):
    """Emitted when an infrastructure census is taken."""

    infrastructure_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    governments_with_infrastructure: NonNegativeInt
    cities_with_infrastructure: NonNegativeInt
    active_well_count: NonNegativeInt
    active_storehouse_count: NonNegativeInt = 0
    active_road_count: NonNegativeInt = 0
    active_scriptorium_count: NonNegativeInt = 0
    active_stoa_count: NonNegativeInt = 0
    active_observatory_count: NonNegativeInt = 0
    active_shrine_count: NonNegativeInt = 0
    active_clinic_count: NonNegativeInt = 0
    active_bathhouse_count: NonNegativeInt = 0
    active_bridge_count: NonNegativeInt = 0
    active_scaffold_count: NonNegativeInt = 0
    active_waystation_count: NonNegativeInt = 0
    active_beacon_count: NonNegativeInt = 0
    active_ditch_count: NonNegativeInt = 0
    active_terrace_count: NonNegativeInt = 0
    active_fulling_mill_count: NonNegativeInt = 0
    active_warehouse_count: NonNegativeInt = 0
    active_mineshaft_count: NonNegativeInt = 0
    active_forge_works_count: NonNegativeInt = 0
    active_lumber_yard_count: NonNegativeInt = 0
    active_sawpit_count: NonNegativeInt = 0
    active_kiln_yard_count: NonNegativeInt = 0


class TechnologyCreated(DomainEvent):
    """Emitted when a technology catalog entry is added to the world."""

    technology_id: TechnologyId
    name: NonEmptyStr
    kind: NonEmptyStr
    discovered: bool = False


class TechnologiesObserved(DomainEvent):
    """Emitted when a technology census is taken."""

    technology_count: NonNegativeInt
    discovered_count: NonNegativeInt
    undiscovered_count: NonNegativeInt
    discovered_fire_count: NonNegativeInt
    discovered_pottery_count: NonNegativeInt
    discovered_irrigation_count: NonNegativeInt = 0
    discovered_metallurgy_count: NonNegativeInt = 0
    discovered_writing_count: NonNegativeInt = 0
    discovered_mathematics_count: NonNegativeInt = 0
    discovered_astronomy_count: NonNegativeInt = 0
    discovered_philosophy_count: NonNegativeInt = 0
    discovered_logic_count: NonNegativeInt = 0
    discovered_rhetoric_count: NonNegativeInt = 0
    discovered_medicine_count: NonNegativeInt = 0
    discovered_anatomy_count: NonNegativeInt = 0
    discovered_hygiene_count: NonNegativeInt = 0
    discovered_engineering_count: NonNegativeInt = 0
    discovered_architecture_count: NonNegativeInt = 0
    discovered_surveying_count: NonNegativeInt = 0
    discovered_navigation_count: NonNegativeInt = 0
    discovered_cartography_count: NonNegativeInt = 0
    discovered_seafaring_count: NonNegativeInt = 0
    discovered_agriculture_count: NonNegativeInt = 0
    discovered_crop_rotation_count: NonNegativeInt = 0
    discovered_forestry_count: NonNegativeInt = 0
    discovered_textiles_count: NonNegativeInt = 0
    discovered_dyeing_count: NonNegativeInt = 0
    discovered_tanning_count: NonNegativeInt = 0
    discovered_mining_count: NonNegativeInt = 0
    discovered_smithing_count: NonNegativeInt = 0
    discovered_toolmaking_count: NonNegativeInt = 0
    discovered_carpentry_count: NonNegativeInt = 0
    discovered_joinery_count: NonNegativeInt = 0
    discovered_cabinetry_count: NonNegativeInt = 0
    discovered_ceramics_count: NonNegativeInt = 0
    locked_count: NonNegativeInt = 0
    researchable_count: NonNegativeInt = 0


class ResearchProgressed(DomainEvent):
    """Emitted when research points increase for a technology."""

    technology_id: TechnologyId
    points_after: NonNegativeInt
    threshold: NonNegativeInt
    delta: NonNegativeInt


class TechnologyDiscovered(DomainEvent):
    """Emitted when research completes and a technology becomes known."""

    technology_id: TechnologyId
    name: NonEmptyStr
    kind: NonEmptyStr


class ResearchObserved(DomainEvent):
    """Emitted when a research census is taken."""

    progress_count: NonNegativeInt
    total_points: NonNegativeInt
    total_threshold: NonNegativeInt
    total_remaining: NonNegativeInt
    completion_bps: NonNegativeInt


class InnovationCreated(DomainEvent):
    """Emitted when an innovation catalog entry is added to the world."""

    innovation_id: InnovationId
    technology_id: TechnologyId
    name: NonEmptyStr
    kind: NonEmptyStr
    active: bool = False


class InnovationActivated(DomainEvent):
    """Emitted when an innovation becomes active after tech discovery."""

    innovation_id: InnovationId
    technology_id: TechnologyId
    name: NonEmptyStr
    kind: NonEmptyStr


class InnovationsObserved(DomainEvent):
    """Emitted when an innovation census is taken."""

    innovation_count: NonNegativeInt
    active_count: NonNegativeInt
    inactive_count: NonNegativeInt
    active_fire_hearth_count: NonNegativeInt
    active_pottery_craft_count: NonNegativeInt
    active_irrigation_canal_count: NonNegativeInt = 0
    active_forge_count: NonNegativeInt = 0
    active_scribe_count: NonNegativeInt = 0
    active_abacus_count: NonNegativeInt = 0
    active_star_chart_count: NonNegativeInt = 0
    active_dialectic_count: NonNegativeInt = 0
    active_syllogism_count: NonNegativeInt = 0
    active_oration_count: NonNegativeInt = 0
    active_remedy_count: NonNegativeInt = 0
    active_dissection_count: NonNegativeInt = 0
    active_asepsis_count: NonNegativeInt = 0
    active_pulley_count: NonNegativeInt = 0
    active_blueprint_count: NonNegativeInt = 0
    active_plumb_line_count: NonNegativeInt = 0
    active_compass_count: NonNegativeInt = 0
    active_map_count: NonNegativeInt = 0
    active_sail_count: NonNegativeInt = 0
    active_plow_count: NonNegativeInt = 0
    active_fallow_count: NonNegativeInt = 0
    active_coppice_count: NonNegativeInt = 0
    active_loom_count: NonNegativeInt = 0
    active_mordant_count: NonNegativeInt = 0
    active_tannery_count: NonNegativeInt = 0
    active_pickaxe_count: NonNegativeInt = 0
    active_bellows_count: NonNegativeInt = 0
    active_lathe_count: NonNegativeInt = 0
    active_sawmill_count: NonNegativeInt = 0
    active_plane_count: NonNegativeInt = 0
    active_dovetail_count: NonNegativeInt = 0
    active_kiln_count: NonNegativeInt = 0


class KnowledgeLearned(DomainEvent):
    """Emitted when an agent learns a technology fact."""

    agent_id: AgentId
    fact: NonEmptyStr
    source: NonEmptyStr
    teacher_id: AgentId | None = None


class KnowledgeObserved(DomainEvent):
    """Emitted when a knowledge census is taken."""

    living_count: NonNegativeInt
    discovered_technology_count: NonNegativeInt
    fire_knower_count: NonNegativeInt
    pottery_knower_count: NonNegativeInt
    irrigation_knower_count: NonNegativeInt = 0
    metallurgy_knower_count: NonNegativeInt = 0
    writing_knower_count: NonNegativeInt = 0
    mathematics_knower_count: NonNegativeInt = 0
    astronomy_knower_count: NonNegativeInt = 0
    philosophy_knower_count: NonNegativeInt = 0
    logic_knower_count: NonNegativeInt = 0
    rhetoric_knower_count: NonNegativeInt = 0
    medicine_knower_count: NonNegativeInt = 0
    anatomy_knower_count: NonNegativeInt = 0
    hygiene_knower_count: NonNegativeInt = 0
    engineering_knower_count: NonNegativeInt = 0
    architecture_knower_count: NonNegativeInt = 0
    surveying_knower_count: NonNegativeInt = 0
    navigation_knower_count: NonNegativeInt = 0
    cartography_knower_count: NonNegativeInt = 0
    seafaring_knower_count: NonNegativeInt = 0
    agriculture_knower_count: NonNegativeInt = 0
    crop_rotation_knower_count: NonNegativeInt = 0
    forestry_knower_count: NonNegativeInt = 0
    textiles_knower_count: NonNegativeInt = 0
    dyeing_knower_count: NonNegativeInt = 0
    tanning_knower_count: NonNegativeInt = 0
    mining_knower_count: NonNegativeInt = 0
    smithing_knower_count: NonNegativeInt = 0
    toolmaking_knower_count: NonNegativeInt = 0
    carpentry_knower_count: NonNegativeInt = 0
    joinery_knower_count: NonNegativeInt = 0
    cabinetry_knower_count: NonNegativeInt = 0
    ceramics_knower_count: NonNegativeInt = 0
    total_fact_instances: NonNegativeInt
    coverage_bps: NonNegativeInt


class MemoryRecorded(DomainEvent):
    """Emitted when an agent encodes an episodic memory record."""

    agent_id: AgentId
    kind: NonEmptyStr
    content: MemoryContentStr


class CognitionObserved(DomainEvent):
    """Emitted when a cognition / memory census is taken."""

    living_count: NonNegativeInt
    total_records: NonNegativeInt
    agents_with_memory: NonNegativeInt
    episode_records: NonNegativeInt
    reflection_records: NonNegativeInt
    belief_count: NonNegativeInt
    mean_records_bps: NonNegativeInt


class AgentReflected(DomainEvent):
    """Emitted when an agent completes a reflection cycle."""

    agent_id: AgentId
    proposition: NonEmptyStr
    confidence: UnitInterval
    model_name: NonEmptyStr


class PlanUpdated(DomainEvent):
    """Emitted when an agent's planned goal is set."""

    agent_id: AgentId
    goal_kind: NonEmptyStr
    priority: UnitInterval
    target: str | None = None


class PlansObserved(DomainEvent):
    """Emitted when a planning census is taken."""

    living_count: NonNegativeInt
    agents_with_plans: NonNegativeInt
    satisfy_food_count: NonNegativeInt
    satisfy_water_count: NonNegativeInt
    satisfy_energy_count: NonNegativeInt


class MemoryRetrieved(DomainEvent):
    """Emitted when an agent retrieves memories into working memory."""

    agent_id: AgentId
    query: NonEmptyStr
    retrieved_count: NonNegativeInt
    summary: NonEmptyStr


class RetrievalObserved(DomainEvent):
    """Emitted when a memory-retrieval census is taken."""

    living_count: NonNegativeInt
    agents_with_context: NonNegativeInt
    total_retrieved: NonNegativeInt
    mean_retrieved_bps: NonNegativeInt


class EffectsObserved(DomainEvent):
    """Emitted when a society-effects census is taken."""

    living_count: NonNegativeInt
    fire_hearth_active: NonNegativeInt
    pottery_craft_active: NonNegativeInt
    rest_restore_bps: NonNegativeInt
    water_gather_amount: NonNegativeInt
    active_well_count: NonNegativeInt = 0
    drink_restore_bps: NonNegativeInt = 3000
    active_storehouse_count: NonNegativeInt = 0
    food_gather_amount: NonNegativeInt = 1
    active_road_count: NonNegativeInt = 0
    move_energy_cost_bps: NonNegativeInt = 500
    active_guild_count: NonNegativeInt = 0
    produce_energy_cost_bps: NonNegativeInt = 1000


CONCRETE_EVENT_TYPES: tuple[type[DomainEvent], ...] = (
    SimulationStarted,
    SimulationCompleted,
    TickStarted,
    TickCompleted,
    LocationCreated,
    MarketCreated,
    GovernmentCreated,
    LawCreated,
    AgentSpawned,
    AgentMoved,
    AgentBorn,
    AgentDied,
    ActionSelected,
    ActionCompleted,
    ResourceConsumed,
    ResourceGathered,
    ResourceTraded,
    ResourceProduced,
    ListingPosted,
    ListingFilled,
    MarketFeeCollected,
    ListingCancelled,
    NeedDecayed,
    PopulationObserved,
    MoneyTransferred,
    TaxCollected,
    MarketObserved,
    PriceObserved,
    WealthObserved,
    RelationshipUpdated,
    RelationshipsObserved,
    ReputationObserved,
    FamiliesObserved,
    NetworksObserved,
    GovernmentsObserved,
    LawsObserved,
    ElectionResolved,
    ElectionsObserved,
    InstitutionCreated,
    InstitutionFunded,
    InstitutionsObserved,
    CityCreated,
    CitiesObserved,
    InfrastructureCreated,
    InfrastructureBuilt,
    InfrastructureCommissioned,
    InfrastructuresObserved,
    TechnologyCreated,
    TechnologiesObserved,
    ResearchProgressed,
    TechnologyDiscovered,
    ResearchObserved,
    InnovationCreated,
    InnovationActivated,
    InnovationsObserved,
    KnowledgeLearned,
    KnowledgeObserved,
    MemoryRecorded,
    CognitionObserved,
    AgentReflected,
    PlanUpdated,
    PlansObserved,
    MemoryRetrieved,
    RetrievalObserved,
    EffectsObserved,
)

EVENT_TYPE_REGISTRY: dict[str, type[DomainEvent]] = {
    cls.__name__: cls for cls in CONCRETE_EVENT_TYPES
}


def event_from_record(record: dict[str, Any]) -> DomainEvent:
    """Deserialize a JSONL/JSON record into a concrete ``DomainEvent``.

    Raises:
        ValueError: If ``event_type`` is missing or unknown.
        ValidationError: If the payload fails model validation.
    """
    if "event_type" not in record:
        msg = "event record missing required key 'event_type'"
        raise ValueError(msg)
    event_type = record["event_type"]
    if not isinstance(event_type, str):
        msg = f"event_type must be a string, got {type(event_type).__name__}"
        raise ValueError(msg)
    try:
        event_cls = EVENT_TYPE_REGISTRY[event_type]
    except KeyError as exc:
        msg = f"unknown event_type: {event_type}"
        raise ValueError(msg) from exc
    payload = {key: value for key, value in record.items() if key != "event_type"}
    return event_cls.model_validate(payload)
