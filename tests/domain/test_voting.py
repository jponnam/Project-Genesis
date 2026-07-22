"""Unit tests for election models, helpers, and leader appointment."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    AgentStatus,
    Election,
    ElectionStatus,
    Government,
    Health,
    SimulationConfig,
    World,
    census_elections,
    choose_candidate,
    conduct_election,
    default_elections,
    election_by_id,
    elections_for,
    next_election_id,
    set_relationship,
    tally_ballots,
    winner_from_tallies,
)
from civitas.domain.ids import AgentId
from civitas.domain.voting import Ballot, VoteTally


def _world(
    *agents: Agent,
    governments: tuple[Government, ...] = (Government.create(0, "Camp", 0, (0,)),),
    elections: tuple[Election, ...] = (),
) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        governments=governments,
        elections=elections,
        agents=agents,
    )


def test_default_elections_empty() -> None:
    """Bootstrap archive has no elections."""
    assert default_elections() == ()


def test_choose_candidate_tie_breaks_to_smaller_id() -> None:
    """Equal standing picks the smaller candidate id."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    candidates = (
        AgentId(value=0),
        AgentId(value=1),
        AgentId(value=2),
    )
    assert choose_candidate(world, 2, candidates) == AgentId(value=0)


def test_choose_candidate_prefers_higher_standing() -> None:
    """Highest standing_bps wins even when id is larger."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
        Agent.create(agent_id=2, name="C"),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    candidates = (AgentId(value=0), AgentId(value=1))
    assert choose_candidate(world, 0, candidates) == AgentId(value=1)


def test_tally_and_winner_plurality_with_tie_break() -> None:
    """Plurality tallies include zeros; ties prefer smaller candidate id."""
    ballots = (
        Ballot(voter_id=AgentId(value=0), candidate_id=AgentId(value=1)),
        Ballot(voter_id=AgentId(value=1), candidate_id=AgentId(value=0)),
        Ballot(voter_id=AgentId(value=2), candidate_id=AgentId(value=0)),
    )
    candidates = (AgentId(value=0), AgentId(value=1), AgentId(value=2))
    tallies = tally_ballots(ballots, candidates)
    assert tallies == (
        VoteTally(candidate_id=AgentId(value=0), votes=2),
        VoteTally(candidate_id=AgentId(value=1), votes=1),
        VoteTally(candidate_id=AgentId(value=2), votes=0),
    )
    assert winner_from_tallies(tallies) == AgentId(value=0)

    tied = (
        VoteTally(candidate_id=AgentId(value=0), votes=1),
        VoteTally(candidate_id=AgentId(value=1), votes=1),
    )
    assert winner_from_tallies(tied) == AgentId(value=0)
    assert winner_from_tallies(()) is None


def test_conduct_election_sets_leader_and_archives() -> None:
    """Conduct archives a closed election and appoints the standing winner."""
    world = _world(
        Agent.create(agent_id=0, name="A"),
        Agent.create(agent_id=1, name="B"),
    )
    world = set_relationship(world, 0, 1, affinity=1.0, trust=1.0)
    assert world is not None
    assert world.governments[0].leader_id is None

    updated = conduct_election(world, 0)
    assert updated is not None
    assert len(updated.elections) == 1
    election = updated.elections[0]
    assert election.status is ElectionStatus.CLOSED
    assert election.election_id.value == 0
    assert election.winner_id == AgentId(value=1)
    assert len(election.franchise) == 2
    assert len(election.ballots) == 2
    assert all(ballot.candidate_id == AgentId(value=1) for ballot in election.ballots)
    assert updated.governments[0].leader_id == AgentId(value=1)
    assert election_by_id(updated, 0) == election
    assert elections_for(updated, 0) == (election,)
    assert next_election_id(updated).value == 1


def test_conduct_election_empty_franchise_clears_leader() -> None:
    """No living subjects yields an empty closed election and vacant seat."""
    world = _world(Agent.create(agent_id=0, name="A"))
    world = conduct_election(world, 0)
    assert world is not None
    assert world.governments[0].leader_id == AgentId(value=0)

    dead = world.agents[0].model_copy(
        update={"status": AgentStatus.DEAD, "health": Health(vitality=0.0)}
    )
    world = world.with_agent(dead)
    updated = conduct_election(world, 0)
    assert updated is not None
    election = updated.elections[-1]
    assert election.franchise == ()
    assert election.winner_id is None
    assert updated.governments[0].leader_id is None


def test_conduct_unknown_government_returns_none() -> None:
    """Unknown government ids do not mutate the world."""
    world = _world(Agent.create(agent_id=0, name="A"))
    assert conduct_election(world, 99) is None


def test_census_elections_counts() -> None:
    """Census aggregates archive stats without mutation."""
    world = _world(Agent.create(agent_id=0, name="A"))
    world = conduct_election(world, 0)
    assert world is not None
    snap = census_elections(world)
    assert snap.election_count == 1
    assert snap.closed_count == 1
    assert snap.open_count == 0
    assert snap.governments_with_elections == 1
    assert census_elections(world) == snap


def test_election_rejects_unsorted_franchise() -> None:
    """Franchise must be ascending by agent id."""
    with pytest.raises(ValidationError):
        Election.create(
            0,
            0,
            0,
            ElectionStatus.CLOSED,
            franchise=(1, 0),
            candidates=(0, 1),
            ballots=((0, 0), (1, 0)),
            tallies=((0, 2), (1, 0)),
            winner_id=0,
        )


def test_world_rejects_unknown_election_government() -> None:
    """Elections must reference an existing government."""
    with pytest.raises(ValidationError):
        World(
            config=SimulationConfig(agent_count=1, seed=1),
            locations=(CAMP_LOCATION,),
            governments=(Government.create(0, "Camp", 0, (0,)),),
            elections=(
                Election.create(
                    0,
                    1,
                    0,
                    ElectionStatus.CLOSED,
                    franchise=(),
                    candidates=(),
                ),
            ),
            agents=(Agent.create(agent_id=0, name="A"),),
        )
