# SPDX-License-Identifier: BSD-3-Clause
"""The denominator of every cross-scene avoidance claim.

2026-08-02 17:00 shipped a goal-ball occupancy screen to explain one
uncompletable scene, and the screen incidentally found a larger defect: **four
of the eight shipped scenes carried no sandbox obstacles at all**, including
`cafe_obstacle_crossing_v0`, whose hazards lived only in the Gazebo world file
(`cafe3_jazzy.sdf.xacro`, 5 baked `<actor>`s) that the NumPy sandbox never
loads. So "obstacle avoidance across the scenario matrix" was a claim about
half the matrix, and nothing in the suite said so.

Two failure modes, and they are not the same
--------------------------------------------
1. **Silent absence** — a scene has no obstacles and declares no obstacle
   checks. Nothing is wrong per run; the damage is to any *aggregate* that
   counts it, which reads a clean sheet as evidence of avoidance. Pinned below
   as a census, so the avoidance-capable subset can never drift unremarked.
2. **Vacuous assertion** — a scene declares `collision: 0` or
   `min_distance_to_obstacle` while carrying nothing to hit. Then the harness
   reports those checks *satisfied* on every run forever. This is the mirror
   image of Q-037: that defect made a scene impossible to pass, this one makes
   it impossible to fail, which is worse, because it inflates the numbers
   instead of depressing them.

`cafe_obstacle_crossing_v0` was mode 1; giving it actors is what this cycle
did, and mode 2 is the guard that stops the fix from being undone by a later
edit that deletes the obstacles but leaves the acceptance block.
"""

from __future__ import annotations

import glob

import pytest

from eval.mppi_sandbox.feasibility import (
    OBSTACLE_DEPENDENT_ACCEPTANCE,
    declared_obstacle_checks,
    goal_ball_clearance,
    is_avoidance_measurable,
    vacuous_acceptance_checks,
)
from eval.mppi_sandbox.scenario import load_scenario

SCENARIOS = sorted(
    p for p in glob.glob("eval/scenarios/*.yaml") if "lam_windows" not in p
)

#: Scenes that carry sandbox obstacles, i.e. that can contribute an avoidance
#: number at all. Strict equality on purpose: adding a scene without obstacles,
#: or silently dropping a scene's obstacle block, must fail here rather than
#: quietly shrink the denominator of an aggregate somebody else reports.
AVOIDANCE_CAPABLE = {
    "cafe-convoy-v0",
    "cafe-cut-in-v0",
    "cafe-freezing-v0",
    "cafe-head-on-v0",
    "cafe-obstacle-crossing-v0",
}

#: Of those, the ones a controller can actually finish — `cafe-cut-in-v0`'s
#: goal ball is provably occupied (Q-037, `test_scenario_feasibility.py`), so
#: it cannot contribute a completed-run avoidance number however good the
#: controller is. This, not `AVOIDANCE_CAPABLE`, is the honest denominator.
AVOIDANCE_REPORTABLE = AVOIDANCE_CAPABLE - {"cafe-cut-in-v0"}


def _scenarios():
    return [load_scenario(p) for p in SCENARIOS]


def test_no_scene_declares_an_obstacle_check_it_cannot_fail():
    """Failure mode 2 — the guard that must never have an exception.

    Not pinned as a known-bad set: unlike the census below, there is no
    legitimate reason for a scene to assert `collision: 0` with nothing in the
    world. If this ever fails, either restore the obstacles or drop the check.
    """
    offenders = {
        s.name: vacuous_acceptance_checks(s)
        for s in _scenarios() if vacuous_acceptance_checks(s)
    }

    assert offenders == {}, (
        f"scenes assert obstacle-dependent checks with no obstacles: {offenders} "
        f"— these pass vacuously on every run"
    )


def test_avoidance_capable_scene_set_is_pinned():
    """Failure mode 1 — the census, as a strict set equality."""
    measurable = {s.name for s in _scenarios() if is_avoidance_measurable(s)}

    assert measurable == AVOIDANCE_CAPABLE


def test_obstacle_crossing_carries_the_actors_its_name_promises():
    """The specific regression this cycle fixed.

    Before 2026-08-02 18:00 this scene ran to `min_obstacle_clearance = +inf`:
    the only scene in the matrix named after an obstacle had none.
    """
    scenario = load_scenario("eval/scenarios/cafe_obstacle_crossing_v0.yaml")

    assert len(scenario.obstacles) == 5, "one per cafe3 baked actor"
    assert is_avoidance_measurable(scenario)
    # It declares both obstacle-dependent checks, so both are now live.
    assert declared_obstacle_checks(scenario) == OBSTACLE_DEPENDENT_ACCEPTANCE


def test_obstacle_crossing_actors_clear_the_goal_ball():
    """Compose with 17:00's screen: do not fix mode 1 by creating a Q-037.

    The whole point of the goal-ball precondition is that new hazards get
    screened before they cost anybody a calibration ladder. These actors sweep
    the band and walk out of it, so the goal stays reachable by a wide margin.
    """
    verdict = goal_ball_clearance(
        load_scenario("eval/scenarios/cafe_obstacle_crossing_v0.yaml"))

    assert verdict.is_reachable
    assert verdict.meets_acceptance
    # Not marginal — nearest parked actor is ~3 m from the goal.
    assert verdict.best_clearance > 2.0


def test_reportable_denominator_is_smaller_than_the_matrix():
    """The number any cross-scene avoidance aggregate is entitled to use.

    Stated as a test so that a future aggregate cannot quietly divide by 8.
    """
    reportable = {
        s.name for s in _scenarios()
        if is_avoidance_measurable(s) and goal_ball_clearance(s).is_reachable
    }

    assert reportable == AVOIDANCE_REPORTABLE
    assert len(reportable) == 4
    assert len(SCENARIOS) == 8
