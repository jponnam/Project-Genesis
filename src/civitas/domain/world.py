"""World aggregate: the complete simulation state at a tick.

The world is immutable. Systems and the engine produce new ``World``
instances via ``model_copy`` / helpers rather than mutating in place.

``config.agent_count`` is the *initial* population created by the world
factory. Runtime roster size is ``len(agents)`` and may diverge once
birth and death are introduced.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from civitas.domain.agent import Agent
from civitas.domain.cities import City, CityKind
from civitas.domain.config import SimulationConfig
from civitas.domain.governments import Government
from civitas.domain.ids import (
    AgentId,
    CityId,
    ElectionId,
    GovernmentId,
    InfrastructureId,
    InnovationId,
    InstitutionId,
    LawId,
    LocationId,
    MarketId,
    TechnologyId,
)
from civitas.domain.infrastructure import Infrastructure
from civitas.domain.innovation import Innovation
from civitas.domain.institutions import Institution
from civitas.domain.laws import Law, LawKind
from civitas.domain.location import Location
from civitas.domain.market import Market
from civitas.domain.research import ResearchProgress
from civitas.domain.technology import Technology
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt
from civitas.domain.voting import Election


class World(BaseModel):
    """Deterministic snapshot of a civilization simulation.

    Attributes:
        config: Configuration used to construct this world.
        tick: Current discrete time (``0`` at construction).
        locations: Places on the map, ordered by ascending ``location_id``.
        markets: Market venues, ordered by ascending ``market_id``.
        governments: Polities, ordered by ascending ``government_id``.
        laws: Statutes, ordered by ascending ``law_id``.
        elections: Archived elections, ordered by ascending ``election_id``.
        institutions: Civic organizations, ordered by ascending ``institution_id``.
        cities: Settlements, ordered by ascending ``city_id``.
        infrastructure: Built capacity, ordered by ascending ``infrastructure_id``.
        technologies: Society tech catalog, ordered by ascending ``technology_id``.
        research_progress: Open research rows, ordered by ascending technology_id.
        innovations: Society adoptions, ordered by ascending ``innovation_id``.
        agents: Agents ordered by ascending ``agent_id``.
        treasury: Global public money balance for collections without a government.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    config: SimulationConfig
    tick: Tick = Field(default_factory=Tick)
    locations: tuple[Location, ...] = ()
    markets: tuple[Market, ...] = ()
    governments: tuple[Government, ...] = ()
    laws: tuple[Law, ...] = ()
    elections: tuple[Election, ...] = ()
    institutions: tuple[Institution, ...] = ()
    cities: tuple[City, ...] = ()
    infrastructure: tuple[Infrastructure, ...] = ()
    technologies: tuple[Technology, ...] = ()
    research_progress: tuple[ResearchProgress, ...] = ()
    innovations: tuple[Innovation, ...] = ()
    agents: tuple[Agent, ...] = ()
    treasury: NonNegativeInt = 0

    @model_validator(mode="after")
    def world_must_be_consistent(self) -> Self:
        """Enforce aggregate integrity across world collections."""
        agent_ids = [agent.agent_id.value for agent in self.agents]
        if len(agent_ids) != len(set(agent_ids)):
            msg = "agent ids must be unique"
            raise ValueError(msg)
        if agent_ids != sorted(agent_ids):
            msg = "agents must be ordered by ascending agent_id"
            raise ValueError(msg)

        location_ids = [location.location_id.value for location in self.locations]
        if len(location_ids) != len(set(location_ids)):
            msg = "location ids must be unique"
            raise ValueError(msg)
        if location_ids != sorted(location_ids):
            msg = "locations must be ordered by ascending location_id"
            raise ValueError(msg)

        known = set(location_ids)
        if not known:
            msg = "world must contain at least one location"
            raise ValueError(msg)

        for agent in self.agents:
            if agent.location_id.value not in known:
                msg = (
                    f"agent {agent.agent_id.value} references unknown "
                    f"location {agent.location_id.value}"
                )
                raise ValueError(msg)

        coord_keys = {(loc.coordinates.x, loc.coordinates.y) for loc in self.locations}
        if len(coord_keys) != len(self.locations):
            msg = "location coordinates must be unique"
            raise ValueError(msg)

        market_ids = [market.market_id.value for market in self.markets]
        if len(market_ids) != len(set(market_ids)):
            msg = "market ids must be unique"
            raise ValueError(msg)
        if market_ids != sorted(market_ids):
            msg = "markets must be ordered by ascending market_id"
            raise ValueError(msg)

        market_locations = [market.location_id.value for market in self.markets]
        if len(market_locations) != len(set(market_locations)):
            msg = "at most one market is allowed per location"
            raise ValueError(msg)
        for market in self.markets:
            if market.location_id.value not in known:
                msg = (
                    f"market {market.market_id.value} references unknown "
                    f"location {market.location_id.value}"
                )
                raise ValueError(msg)

        government_ids = [
            government.government_id.value for government in self.governments
        ]
        if len(government_ids) != len(set(government_ids)):
            msg = "government ids must be unique"
            raise ValueError(msg)
        if government_ids != sorted(government_ids):
            msg = "governments must be ordered by ascending government_id"
            raise ValueError(msg)

        claimed: set[int] = set()
        for government in self.governments:
            for location in government.jurisdiction:
                if location.value not in known:
                    msg = (
                        f"government {government.government_id.value} references "
                        f"unknown location {location.value}"
                    )
                    raise ValueError(msg)
                if location.value in claimed:
                    msg = "government jurisdictions must be disjoint"
                    raise ValueError(msg)
                claimed.add(location.value)
            if government.leader_id is not None:
                leader = self.agent_by_id(government.leader_id)
                if leader is None:
                    msg = (
                        f"government {government.government_id.value} references "
                        f"unknown leader {government.leader_id.value}"
                    )
                    raise ValueError(msg)

        known_governments = set(government_ids)
        law_ids = [law.law_id.value for law in self.laws]
        if len(law_ids) != len(set(law_ids)):
            msg = "law ids must be unique"
            raise ValueError(msg)
        if law_ids != sorted(law_ids):
            msg = "laws must be ordered by ascending law_id"
            raise ValueError(msg)

        active_tax_govs: set[int] = set()
        active_market_fee_govs: set[int] = set()
        for law in self.laws:
            if law.government_id.value not in known_governments:
                msg = (
                    f"law {law.law_id.value} references unknown "
                    f"government {law.government_id.value}"
                )
                raise ValueError(msg)
            if law.active and law.kind == LawKind.TAX_SCHEDULE:
                gov_value = law.government_id.value
                if gov_value in active_tax_govs:
                    msg = "at most one active TAX_SCHEDULE law per government"
                    raise ValueError(msg)
                active_tax_govs.add(gov_value)
            if law.active and law.kind == LawKind.MARKET_FEE:
                gov_value = law.government_id.value
                if gov_value in active_market_fee_govs:
                    msg = "at most one active MARKET_FEE law per government"
                    raise ValueError(msg)
                active_market_fee_govs.add(gov_value)

        election_ids = [election.election_id.value for election in self.elections]
        if len(election_ids) != len(set(election_ids)):
            msg = "election ids must be unique"
            raise ValueError(msg)
        if election_ids != sorted(election_ids):
            msg = "elections must be ordered by ascending election_id"
            raise ValueError(msg)
        known_agents = set(agent_ids)
        for election in self.elections:
            if election.government_id.value not in known_governments:
                msg = (
                    f"election {election.election_id.value} references unknown "
                    f"government {election.government_id.value}"
                )
                raise ValueError(msg)
            for agent_ref in (*election.franchise, *election.candidates):
                if agent_ref.value not in known_agents:
                    msg = (
                        f"election {election.election_id.value} references "
                        f"unknown agent {agent_ref.value}"
                    )
                    raise ValueError(msg)
            if (
                election.winner_id is not None
                and election.winner_id.value not in known_agents
            ):
                msg = (
                    f"election {election.election_id.value} references unknown "
                    f"winner {election.winner_id.value}"
                )
                raise ValueError(msg)

        institution_ids = [
            institution.institution_id.value for institution in self.institutions
        ]
        if len(institution_ids) != len(set(institution_ids)):
            msg = "institution ids must be unique"
            raise ValueError(msg)
        if institution_ids != sorted(institution_ids):
            msg = "institutions must be ordered by ascending institution_id"
            raise ValueError(msg)

        gov_by_id = {
            government.government_id.value: government
            for government in self.governments
        }
        active_kind_govs: set[tuple[int, str]] = set()
        for institution in self.institutions:
            gov_value = institution.government_id.value
            if gov_value not in gov_by_id:
                msg = (
                    f"institution {institution.institution_id.value} references "
                    f"unknown government {gov_value}"
                )
                raise ValueError(msg)
            government = gov_by_id[gov_value]
            if institution.location_id.value not in known:
                msg = (
                    f"institution {institution.institution_id.value} references "
                    f"unknown location {institution.location_id.value}"
                )
                raise ValueError(msg)
            jurisdiction = {location.value for location in government.jurisdiction}
            if institution.location_id.value not in jurisdiction:
                msg = (
                    f"institution {institution.institution_id.value} seat must lie "
                    f"inside government jurisdiction"
                )
                raise ValueError(msg)
            if (
                institution.officer_id is not None
                and institution.officer_id.value not in known_agents
            ):
                msg = (
                    f"institution {institution.institution_id.value} references "
                    f"unknown officer {institution.officer_id.value}"
                )
                raise ValueError(msg)
            if institution.active:
                key = (institution.government_id.value, institution.kind.value)
                if key in active_kind_govs:
                    msg = "at most one active institution of each kind per government"
                    raise ValueError(msg)
                active_kind_govs.add(key)

        city_ids = [city.city_id.value for city in self.cities]
        if len(city_ids) != len(set(city_ids)):
            msg = "city ids must be unique"
            raise ValueError(msg)
        if city_ids != sorted(city_ids):
            msg = "cities must be ordered by ascending city_id"
            raise ValueError(msg)

        city_locations: set[int] = set()
        active_capitals: set[int] = set()
        for city in self.cities:
            gov_value = city.government_id.value
            if gov_value not in gov_by_id:
                msg = (
                    f"city {city.city_id.value} references unknown "
                    f"government {gov_value}"
                )
                raise ValueError(msg)
            government = gov_by_id[gov_value]
            if city.location_id.value not in known:
                msg = (
                    f"city {city.city_id.value} references unknown "
                    f"location {city.location_id.value}"
                )
                raise ValueError(msg)
            if city.location_id.value in city_locations:
                msg = "at most one city is allowed per location"
                raise ValueError(msg)
            city_locations.add(city.location_id.value)
            jurisdiction = {location.value for location in government.jurisdiction}
            if city.location_id.value not in jurisdiction:
                msg = (
                    f"city {city.city_id.value} seat must lie "
                    f"inside government jurisdiction"
                )
                raise ValueError(msg)
            if city.is_capital and city.kind is CityKind.OUTPOST:
                msg = "outpost cities cannot be capitals"
                raise ValueError(msg)
            if city.active and city.is_capital:
                if gov_value in active_capitals:
                    msg = "at most one active capital city per government"
                    raise ValueError(msg)
                active_capitals.add(gov_value)

        infra_ids = [item.infrastructure_id.value for item in self.infrastructure]
        if len(infra_ids) != len(set(infra_ids)):
            msg = "infrastructure ids must be unique"
            raise ValueError(msg)
        if infra_ids != sorted(infra_ids):
            msg = "infrastructure must be ordered by ascending infrastructure_id"
            raise ValueError(msg)

        city_by_value = {city.city_id.value: city for city in self.cities}
        active_kind_locations: set[tuple[int, str]] = set()
        for item in self.infrastructure:
            gov_value = item.government_id.value
            if gov_value not in gov_by_id:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} references "
                    f"unknown government {gov_value}"
                )
                raise ValueError(msg)
            government = gov_by_id[gov_value]
            if item.location_id.value not in known:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} references "
                    f"unknown location {item.location_id.value}"
                )
                raise ValueError(msg)
            city_value = item.city_id.value
            if city_value not in city_by_value:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} references "
                    f"unknown city {city_value}"
                )
                raise ValueError(msg)
            city = city_by_value[city_value]
            if city.government_id != item.government_id:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} government "
                    f"must match city government"
                )
                raise ValueError(msg)
            if city.location_id != item.location_id:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} location "
                    f"must match city seat"
                )
                raise ValueError(msg)
            jurisdiction = {location.value for location in government.jurisdiction}
            if item.location_id.value not in jurisdiction:
                msg = (
                    f"infrastructure {item.infrastructure_id.value} seat must lie "
                    f"inside government jurisdiction"
                )
                raise ValueError(msg)
            if item.active:
                key = (item.location_id.value, item.kind.value)
                if key in active_kind_locations:
                    msg = "at most one active infrastructure of each kind per location"
                    raise ValueError(msg)
                active_kind_locations.add(key)

        technology_ids = [tech.technology_id.value for tech in self.technologies]
        if len(technology_ids) != len(set(technology_ids)):
            msg = "technology ids must be unique"
            raise ValueError(msg)
        if technology_ids != sorted(technology_ids):
            msg = "technologies must be ordered by ascending technology_id"
            raise ValueError(msg)
        tech_kinds = [tech.kind.value for tech in self.technologies]
        if len(tech_kinds) != len(set(tech_kinds)):
            msg = "technology kinds must be unique"
            raise ValueError(msg)
        tech_by_value = {tech.technology_id.value: tech for tech in self.technologies}
        for tech in self.technologies:
            for prerequisite_id in tech.prerequisite_ids:
                if prerequisite_id.value == tech.technology_id.value:
                    msg = f"technology {tech.technology_id.value} cannot require itself"
                    raise ValueError(msg)
                if prerequisite_id.value not in tech_by_value:
                    msg = (
                        f"technology {tech.technology_id.value} references "
                        f"unknown prerequisite {prerequisite_id.value}"
                    )
                    raise ValueError(msg)

        research_ids = [row.technology_id.value for row in self.research_progress]
        if len(research_ids) != len(set(research_ids)):
            msg = "research progress technology ids must be unique"
            raise ValueError(msg)
        if research_ids != sorted(research_ids):
            msg = "research_progress must be ordered by ascending technology_id"
            raise ValueError(msg)
        for row in self.research_progress:
            tech_value = row.technology_id.value
            if tech_value not in tech_by_value:
                msg = f"research progress references unknown technology {tech_value}"
                raise ValueError(msg)
            tech = tech_by_value[tech_value]
            if tech.discovered:
                msg = (
                    f"research progress not allowed for discovered technology "
                    f"{row.technology_id.value}"
                )
                raise ValueError(msg)
            if row.points > row.threshold:
                msg = "research points must be <= threshold"
                raise ValueError(msg)

        innovation_ids = [
            innovation.innovation_id.value for innovation in self.innovations
        ]
        if len(innovation_ids) != len(set(innovation_ids)):
            msg = "innovation ids must be unique"
            raise ValueError(msg)
        if innovation_ids != sorted(innovation_ids):
            msg = "innovations must be ordered by ascending innovation_id"
            raise ValueError(msg)
        innovation_kinds = [innovation.kind.value for innovation in self.innovations]
        if len(innovation_kinds) != len(set(innovation_kinds)):
            msg = "innovation kinds must be unique"
            raise ValueError(msg)
        innovation_tech_ids = [
            innovation.technology_id.value for innovation in self.innovations
        ]
        if len(innovation_tech_ids) != len(set(innovation_tech_ids)):
            msg = "innovation technology ids must be unique"
            raise ValueError(msg)
        for innovation in self.innovations:
            tech_value = innovation.technology_id.value
            if tech_value not in tech_by_value:
                msg = (
                    f"innovation {innovation.innovation_id.value} references "
                    f"unknown technology {tech_value}"
                )
                raise ValueError(msg)
            tech = tech_by_value[tech_value]
            if innovation.active and not tech.discovered:
                msg = (
                    f"active innovation {innovation.innovation_id.value} requires "
                    f"discovered technology {tech_value}"
                )
                raise ValueError(msg)

        return self

    @property
    def population_size(self) -> int:
        """Return the current roster size."""
        return len(self.agents)

    def agent_by_id(self, agent_id: AgentId | int) -> Agent | None:
        """Return the agent with ``agent_id``, or ``None`` if absent."""
        target = agent_id if isinstance(agent_id, AgentId) else AgentId(value=agent_id)
        for agent in self.agents:
            if agent.agent_id == target:
                return agent
        return None

    def location_by_id(self, location_id: LocationId | int) -> Location | None:
        """Return the location with ``location_id``, or ``None`` if absent."""
        target = (
            location_id
            if isinstance(location_id, LocationId)
            else LocationId(value=location_id)
        )
        for location in self.locations:
            if location.location_id == target:
                return location
        return None

    def market_by_id(self, market_id: MarketId | int) -> Market | None:
        """Return the market with ``market_id``, or ``None`` if absent."""
        target = (
            market_id if isinstance(market_id, MarketId) else MarketId(value=market_id)
        )
        for market in self.markets:
            if market.market_id == target:
                return market
        return None

    def government_by_id(
        self,
        government_id: GovernmentId | int,
    ) -> Government | None:
        """Return the government with ``government_id``, or ``None`` if absent."""
        target = (
            government_id
            if isinstance(government_id, GovernmentId)
            else GovernmentId(value=government_id)
        )
        for government in self.governments:
            if government.government_id == target:
                return government
        return None

    def law_by_id(self, law_id: LawId | int) -> Law | None:
        """Return the law with ``law_id``, or ``None`` if absent."""
        target = law_id if isinstance(law_id, LawId) else LawId(value=law_id)
        for law in self.laws:
            if law.law_id == target:
                return law
        return None

    def election_by_id(self, election_id: ElectionId | int) -> Election | None:
        """Return the election with ``election_id``, or ``None`` if absent."""
        target = (
            election_id
            if isinstance(election_id, ElectionId)
            else ElectionId(value=election_id)
        )
        for election in self.elections:
            if election.election_id == target:
                return election
        return None

    def institution_by_id(
        self,
        institution_id: InstitutionId | int,
    ) -> Institution | None:
        """Return the institution with ``institution_id``, or ``None`` if absent."""
        target = (
            institution_id
            if isinstance(institution_id, InstitutionId)
            else InstitutionId(value=institution_id)
        )
        for institution in self.institutions:
            if institution.institution_id == target:
                return institution
        return None

    def city_by_id(self, city_id: CityId | int) -> City | None:
        """Return the city with ``city_id``, or ``None`` if absent."""
        target = city_id if isinstance(city_id, CityId) else CityId(value=city_id)
        for city in self.cities:
            if city.city_id == target:
                return city
        return None

    def infrastructure_by_id(
        self,
        infrastructure_id: InfrastructureId | int,
    ) -> Infrastructure | None:
        """Return the infrastructure with ``infrastructure_id``, or ``None``."""
        target = (
            infrastructure_id
            if isinstance(infrastructure_id, InfrastructureId)
            else InfrastructureId(value=infrastructure_id)
        )
        for item in self.infrastructure:
            if item.infrastructure_id == target:
                return item
        return None

    def technology_by_id(
        self,
        technology_id: TechnologyId | int,
    ) -> Technology | None:
        """Return the technology with ``technology_id``, or ``None`` if absent."""
        target = (
            technology_id
            if isinstance(technology_id, TechnologyId)
            else TechnologyId(value=technology_id)
        )
        for technology in self.technologies:
            if technology.technology_id == target:
                return technology
        return None

    def agents_at(self, location_id: LocationId | int) -> tuple[Agent, ...]:
        """Return agents occupying ``location_id`` in stable id order."""
        target = (
            location_id
            if isinstance(location_id, LocationId)
            else LocationId(value=location_id)
        )
        return tuple(agent for agent in self.agents if agent.location_id == target)

    def alive_agents(self) -> tuple[Agent, ...]:
        """Return living agents in stable id order."""
        return tuple(agent for agent in self.agents if agent.is_alive())

    def with_tick(self, tick: Tick) -> World:
        """Return a copy of this world at ``tick``."""
        return self.model_copy(update={"tick": tick})

    def with_agent(self, agent: Agent) -> World:
        """Return a copy replacing the agent that shares ``agent.agent_id``.

        Raises:
            ValueError: If no agent with that id exists.
        """
        updated: list[Agent] = []
        found = False
        for existing in self.agents:
            if existing.agent_id == agent.agent_id:
                updated.append(agent)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"agent id {agent.agent_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"agents": tuple(updated)})

    def with_agents(self, agents: tuple[Agent, ...]) -> World:
        """Return a copy with a replaced agent roster.

        The roster must remain uniquely id-sorted; validation enforces this.
        """
        return World(
            config=self.config,
            tick=self.tick,
            locations=self.locations,
            markets=self.markets,
            governments=self.governments,
            laws=self.laws,
            elections=self.elections,
            institutions=self.institutions,
            cities=self.cities,
            infrastructure=self.infrastructure,
            technologies=self.technologies,
            research_progress=self.research_progress,
            innovations=self.innovations,
            agents=agents,
            treasury=self.treasury,
        )

    def with_treasury(self, balance: int) -> World:
        """Return a copy with ``treasury`` set to ``balance``.

        Raises:
            ValueError: If ``balance`` is negative.
        """
        if balance < 0:
            msg = f"treasury balance must be >= 0, got {balance}"
            raise ValueError(msg)
        return self.model_copy(update={"treasury": balance})

    def with_location(self, location: Location) -> World:
        """Return a copy replacing the location that shares ``location_id``.

        Raises:
            ValueError: If no location with that id exists.
        """
        updated: list[Location] = []
        found = False
        for existing in self.locations:
            if existing.location_id == location.location_id:
                updated.append(location)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"location id {location.location_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"locations": tuple(updated)})

    def with_market(self, market: Market) -> World:
        """Return a copy replacing the market that shares ``market_id``.

        Raises:
            ValueError: If no market with that id exists.
        """
        updated: list[Market] = []
        found = False
        for existing in self.markets:
            if existing.market_id == market.market_id:
                updated.append(market)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"market id {market.market_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"markets": tuple(updated)})

    def with_government(self, government: Government) -> World:
        """Return a copy replacing the government that shares ``government_id``.

        Raises:
            ValueError: If no government with that id exists.
        """
        updated: list[Government] = []
        found = False
        for existing in self.governments:
            if existing.government_id == government.government_id:
                updated.append(government)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"government id {government.government_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"governments": tuple(updated)})

    def with_law(self, law: Law) -> World:
        """Return a copy replacing the law that shares ``law_id``.

        Raises:
            ValueError: If no law with that id exists.
        """
        updated: list[Law] = []
        found = False
        for existing in self.laws:
            if existing.law_id == law.law_id:
                updated.append(law)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"law id {law.law_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"laws": tuple(updated)})

    def with_election(self, election: Election) -> World:
        """Return a copy replacing or inserting ``election`` by ``election_id``.

        New elections are inserted so the archive remains ascending by id.
        """
        updated: list[Election] = []
        found = False
        for existing in self.elections:
            if existing.election_id == election.election_id:
                updated.append(election)
                found = True
            else:
                updated.append(existing)
        if not found:
            updated.append(election)
            updated.sort(key=lambda item: item.election_id.value)
        return self.model_copy(update={"elections": tuple(updated)})

    def with_institution(self, institution: Institution) -> World:
        """Return a copy replacing the institution that shares ``institution_id``.

        Raises:
            ValueError: If no institution with that id exists.
        """
        updated: list[Institution] = []
        found = False
        for existing in self.institutions:
            if existing.institution_id == institution.institution_id:
                updated.append(institution)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = (
                f"institution id {institution.institution_id.value} not found in world"
            )
            raise ValueError(msg)
        return self.model_copy(update={"institutions": tuple(updated)})

    def with_city(self, city: City) -> World:
        """Return a copy replacing the city that shares ``city_id``.

        Raises:
            ValueError: If no city with that id exists.
        """
        updated: list[City] = []
        found = False
        for existing in self.cities:
            if existing.city_id == city.city_id:
                updated.append(city)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"city id {city.city_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"cities": tuple(updated)})

    def with_infrastructure(self, item: Infrastructure) -> World:
        """Return a copy replacing the infrastructure that shares its id.

        Raises:
            ValueError: If no infrastructure with that id exists.
        """
        updated: list[Infrastructure] = []
        found = False
        for existing in self.infrastructure:
            if existing.infrastructure_id == item.infrastructure_id:
                updated.append(item)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"infrastructure id {item.infrastructure_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"infrastructure": tuple(updated)})

    def with_technology(self, technology: Technology) -> World:
        """Return a copy replacing the technology that shares ``technology_id``.

        Raises:
            ValueError: If no technology with that id exists.
        """
        updated: list[Technology] = []
        found = False
        for existing in self.technologies:
            if existing.technology_id == technology.technology_id:
                updated.append(technology)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"technology id {technology.technology_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"technologies": tuple(updated)})

    def with_research_progress(self, progress: ResearchProgress) -> World:
        """Return a copy replacing or inserting ``progress`` by technology_id."""
        updated: list[ResearchProgress] = []
        found = False
        for existing in self.research_progress:
            if existing.technology_id == progress.technology_id:
                updated.append(progress)
                found = True
            else:
                updated.append(existing)
        if not found:
            updated.append(progress)
            updated.sort(key=lambda item: item.technology_id.value)
        return self.model_copy(update={"research_progress": tuple(updated)})

    def innovation_by_id(
        self,
        innovation_id: InnovationId | int,
    ) -> Innovation | None:
        """Return the innovation with ``innovation_id``, or ``None`` if absent."""
        target = (
            innovation_id
            if isinstance(innovation_id, InnovationId)
            else InnovationId(value=innovation_id)
        )
        for innovation in self.innovations:
            if innovation.innovation_id == target:
                return innovation
        return None

    def with_innovation(self, innovation: Innovation) -> World:
        """Return a copy replacing the innovation that shares ``innovation_id``.

        Raises:
            ValueError: If no innovation with that id exists.
        """
        updated: list[Innovation] = []
        found = False
        for existing in self.innovations:
            if existing.innovation_id == innovation.innovation_id:
                updated.append(innovation)
                found = True
            else:
                updated.append(existing)
        if not found:
            msg = f"innovation id {innovation.innovation_id.value} not found in world"
            raise ValueError(msg)
        return self.model_copy(update={"innovations": tuple(updated)})
