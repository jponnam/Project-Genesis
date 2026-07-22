"""Elections: franchise ballots by social standing, archived results, leaders.

Phase 5 Milestone 3. Franchise and candidates are living subjects of the
government (``living_subjects``). Each living subject casts one ballot for the
candidate with highest society-wide ``standing_of`` / ``standing_bps`` (ties →
smaller agent id). Empty franchise leaves the seat vacant. Elections are
archived on ``World.elections``; they are not auto-run each tick — call
``conduct_election`` (or ``VoteSystem.conduct``) when an election should fire.
Institutions are a separate Phase 5 aggregate.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from civitas.domain.governments import government_by_id, living_subjects, set_leader
from civitas.domain.ids import AgentId, ElectionId, GovernmentId
from civitas.domain.reputation import standing_of
from civitas.domain.time import Tick
from civitas.domain.types import NonNegativeInt

if TYPE_CHECKING:
    from civitas.domain.world import World


class ElectionStatus(StrEnum):
    """Lifecycle of a stored election record."""

    OPEN = "open"
    CLOSED = "closed"


class Ballot(BaseModel):
    """One voter's choice of candidate."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    voter_id: AgentId
    candidate_id: AgentId


class VoteTally(BaseModel):
    """Votes received by one candidate in an election."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    candidate_id: AgentId
    votes: NonNegativeInt = 0


class Election(BaseModel):
    """A completed (or open) election for a government seat."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    election_id: ElectionId
    government_id: GovernmentId
    tick: Tick
    status: ElectionStatus
    franchise: tuple[AgentId, ...] = ()
    candidates: tuple[AgentId, ...] = ()
    ballots: tuple[Ballot, ...] = ()
    tallies: tuple[VoteTally, ...] = ()
    winner_id: AgentId | None = None

    @model_validator(mode="after")
    def election_must_be_consistent(self) -> Self:
        """Reject inconsistent franchise, ballots, tallies, or winners."""
        franchise_values = [agent.value for agent in self.franchise]
        if len(franchise_values) != len(set(franchise_values)):
            msg = "duplicate franchise agent ids"
            raise ValueError(msg)
        if franchise_values != sorted(franchise_values):
            msg = "franchise must be ordered by ascending agent_id"
            raise ValueError(msg)

        candidate_values = [agent.value for agent in self.candidates]
        if len(candidate_values) != len(set(candidate_values)):
            msg = "duplicate candidate agent ids"
            raise ValueError(msg)
        if candidate_values != sorted(candidate_values):
            msg = "candidates must be ordered by ascending agent_id"
            raise ValueError(msg)

        franchise_set = set(franchise_values)
        candidate_set = set(candidate_values)
        if not candidate_set.issubset(franchise_set):
            msg = "candidates must be a subset of franchise"
            raise ValueError(msg)

        voters_seen: set[int] = set()
        for ballot in self.ballots:
            voter_value = ballot.voter_id.value
            if voter_value in voters_seen:
                msg = f"duplicate ballot for voter {voter_value}"
                raise ValueError(msg)
            voters_seen.add(voter_value)
            if voter_value not in franchise_set:
                msg = f"voter {voter_value} not in franchise"
                raise ValueError(msg)
            if ballot.candidate_id.value not in candidate_set:
                msg = f"candidate {ballot.candidate_id.value} not among candidates"
                raise ValueError(msg)

        if self.status is ElectionStatus.CLOSED and voters_seen != franchise_set:
            msg = "closed election ballots must cover the franchise"
            raise ValueError(msg)

        tally_values = [tally.candidate_id.value for tally in self.tallies]
        if len(tally_values) != len(set(tally_values)):
            msg = "duplicate tallies for the same candidate"
            raise ValueError(msg)
        if tally_values != sorted(tally_values):
            msg = "tallies must be ordered by ascending candidate_id"
            raise ValueError(msg)
        for tally in self.tallies:
            if tally.candidate_id.value not in candidate_set:
                msg = f"tally for non-candidate {tally.candidate_id.value}"
                raise ValueError(msg)

        if self.winner_id is not None and self.winner_id.value not in candidate_set:
            msg = "winner_id must be among candidates when set"
            raise ValueError(msg)

        if self.status is ElectionStatus.CLOSED and self.candidates:
            expected_votes = sum(tally.votes for tally in self.tallies)
            if expected_votes != len(self.ballots):
                msg = "tally vote sum must equal ballot count"
                raise ValueError(msg)
        return self

    @classmethod
    def create(
        cls,
        election_id: int,
        government_id: int,
        tick: int,
        status: ElectionStatus | str,
        *,
        franchise: tuple[int, ...] = (),
        candidates: tuple[int, ...] = (),
        ballots: tuple[tuple[int, int], ...] = (),
        tallies: tuple[tuple[int, int], ...] = (),
        winner_id: int | None = None,
    ) -> Election:
        """Construct a validated election from primitive fields."""
        return cls(
            election_id=ElectionId(value=election_id),
            government_id=GovernmentId(value=government_id),
            tick=Tick(value=tick),
            status=ElectionStatus(status),
            franchise=tuple(AgentId(value=value) for value in franchise),
            candidates=tuple(AgentId(value=value) for value in candidates),
            ballots=tuple(
                Ballot(
                    voter_id=AgentId(value=voter),
                    candidate_id=AgentId(value=candidate),
                )
                for voter, candidate in ballots
            ),
            tallies=tuple(
                VoteTally(
                    candidate_id=AgentId(value=candidate),
                    votes=votes,
                )
                for candidate, votes in tallies
            ),
            winner_id=None if winner_id is None else AgentId(value=winner_id),
        )


class ElectionCensus(BaseModel):
    """Observe-only snapshot of archived elections (no mutation)."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    tick: Tick
    election_count: NonNegativeInt
    closed_count: NonNegativeInt
    open_count: NonNegativeInt
    governments_with_elections: NonNegativeInt


def default_elections() -> tuple[Election, ...]:
    """Bootstrap: no elections until one is conducted."""
    return ()


def election_by_id(world: World, election_id: ElectionId | int) -> Election | None:
    """Return the election with ``election_id``, or ``None``."""
    target = (
        election_id
        if isinstance(election_id, ElectionId)
        else ElectionId(value=election_id)
    )
    for election in world.elections:
        if election.election_id == target:
            return election
    return None


def elections_for(
    world: World,
    government_id: GovernmentId | int,
) -> tuple[Election, ...]:
    """Return elections for ``government_id`` in ascending election id order."""
    target = (
        government_id
        if isinstance(government_id, GovernmentId)
        else GovernmentId(value=government_id)
    )
    return tuple(e for e in world.elections if e.government_id == target)


def next_election_id(world: World) -> ElectionId:
    """Allocate the next unused ``ElectionId`` (max existing + 1, or 0)."""
    if not world.elections:
        return ElectionId(value=0)
    highest = max(election.election_id.value for election in world.elections)
    return ElectionId(value=highest + 1)


def _standing_bps(world: World, agent_id: AgentId) -> int:
    row = standing_of(world, agent_id)
    return 0 if row is None else row.standing_bps


def choose_candidate(
    world: World,
    voter_id: AgentId | int,
    candidates: tuple[AgentId, ...],
) -> AgentId:
    """Pick the standing-argmax candidate (ties → smaller agent id).

    Requires a non-empty ``candidates`` tuple. Uses society-wide reputation
    ``standing_bps``; agents with no inbound bonds score 0. ``voter_id`` is
    accepted for a stable ballot API (each subject still casts one vote).
    """
    del voter_id  # standing is society-wide; franchise still ensures one ballot each
    if not candidates:
        msg = "candidates must be non-empty"
        raise ValueError(msg)
    best = candidates[0]
    best_bps = _standing_bps(world, best)
    for candidate_id in candidates[1:]:
        bps = _standing_bps(world, candidate_id)
        if bps > best_bps or (bps == best_bps and candidate_id.value < best.value):
            best = candidate_id
            best_bps = bps
    return best


def tally_ballots(
    ballots: tuple[Ballot, ...],
    candidates: tuple[AgentId, ...],
) -> tuple[VoteTally, ...]:
    """Count votes per candidate; include zero-vote candidates; order by id."""
    counts = {candidate.value: 0 for candidate in candidates}
    for ballot in ballots:
        counts[ballot.candidate_id.value] = counts[ballot.candidate_id.value] + 1
    ordered = sorted(counts.items(), key=lambda item: item[0])
    return tuple(
        VoteTally(candidate_id=AgentId(value=candidate), votes=votes)
        for candidate, votes in ordered
    )


def winner_from_tallies(tallies: tuple[VoteTally, ...]) -> AgentId | None:
    """Plurality winner; ties → smaller agent id. Empty tallies ⇒ ``None``."""
    if not tallies:
        return None
    best = tallies[0]
    for tally in tallies[1:]:
        if tally.votes > best.votes or (
            tally.votes == best.votes
            and tally.candidate_id.value < best.candidate_id.value
        ):
            best = tally
    return best.candidate_id


def conduct_election(world: World, government_id: GovernmentId | int) -> World | None:
    """Run one closed election for ``government_id`` and apply the winner as leader.

    Franchise and candidates are living subject ids. Ballots use
    ``choose_candidate``. Archives a ``CLOSED`` ``Election``, then
    ``set_leader`` to the winner (or ``None`` if the franchise is empty).

    Returns ``None`` when ``government_id`` is unknown.
    """
    government = government_by_id(world, government_id)
    if government is None:
        return None

    subjects = living_subjects(world, government.government_id)
    franchise = tuple(agent.agent_id for agent in subjects)
    candidates = franchise
    ballots = tuple(
        Ballot(
            voter_id=voter_id,
            candidate_id=choose_candidate(world, voter_id, candidates),
        )
        for voter_id in franchise
    )
    tallies = tally_ballots(ballots, candidates)
    winner_id = winner_from_tallies(tallies)

    election = Election(
        election_id=next_election_id(world),
        government_id=government.government_id,
        tick=world.tick,
        status=ElectionStatus.CLOSED,
        franchise=franchise,
        candidates=candidates,
        ballots=ballots,
        tallies=tallies,
        winner_id=winner_id,
    )
    world = world.with_election(election)
    updated = set_leader(world, government.government_id, winner_id)
    return world if updated is None else updated


def census_elections(world: World) -> ElectionCensus:
    """Aggregate election archive stats (read-only)."""
    closed = sum(
        1 for election in world.elections if election.status is ElectionStatus.CLOSED
    )
    open_count = sum(
        1 for election in world.elections if election.status is ElectionStatus.OPEN
    )
    gov_ids = {election.government_id.value for election in world.elections}
    return ElectionCensus(
        tick=world.tick,
        election_count=len(world.elections),
        closed_count=closed,
        open_count=open_count,
        governments_with_elections=len(gov_ids),
    )
