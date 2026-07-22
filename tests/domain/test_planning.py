"""Unit tests for planning helpers."""

from __future__ import annotations

from civitas.domain import (
    CAMP_LOCATION,
    Agent,
    Belief,
    Beliefs,
    Needs,
    SimulationConfig,
    World,
    apply_planning,
    census_plans,
    default_innovations,
    default_research_progress,
    default_technologies,
    plan_goal_for_agent,
)


def _world(*agents: Agent) -> World:
    return World(
        config=SimulationConfig(agent_count=max(len(agents), 1), seed=1),
        locations=(CAMP_LOCATION,),
        technologies=default_technologies(),
        research_progress=default_research_progress(),
        innovations=default_innovations(),
        agents=agents,
    )


def test_plan_goal_uses_priority_belief() -> None:
    """Priority beliefs become satisfy-need goals with matching confidence."""
    agent = Agent.create(
        agent_id=0,
        name="A",
        needs=Needs(food=0.9, water=0.1, energy=0.9),
    )
    agent = agent.model_copy(
        update={
            "beliefs": Beliefs(
                entries=(Belief(proposition="priority:water", confidence=0.8),)
            )
        }
    )
    goal = plan_goal_for_agent(agent)
    assert goal.kind == "satisfy_water"
    assert goal.target == "water"
    assert goal.priority == 0.8


def test_apply_planning_sets_single_goal() -> None:
    """Planning replaces the goal set with one satisfy-need goal."""
    world = _world(
        Agent.create(
            agent_id=0,
            name="A",
            needs=Needs(food=0.2, water=0.5, energy=0.5),
        )
    )
    world, updates = apply_planning(world)
    assert len(updates) == 1
    assert updates[0].goal_kind == "satisfy_food"
    assert world.agents[0].goals.goals[0].kind == "satisfy_food"
    snap = census_plans(world)
    assert snap.agents_with_plans == 1
    assert snap.satisfy_food_count == 1
