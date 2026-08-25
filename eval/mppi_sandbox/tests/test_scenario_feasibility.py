# SPDX-License-Identifier: BSD-3-Clause
"""Q-037: `cafe_cut_in_v0` is uncompletable because its goal ball is occupied.

16:00's calibration pass could not distinguish "no temperature works" from
"this arm never finishes" without ~500 closed-loop runs. These tests pin the
static precondition that separates them in milliseconds, and pin that it
agrees with the empirical verdict where both are available.
"""

from __future__ import annotations

import glob

import numpy as np
import pytest

from eval.mppi_sandbox.feasibility import (
    goal_ball_clearance,
    screen_scenarios,
)
from eval.mppi_sandbox.run import ROBOT_RADIUS
from eval.mppi_sandbox.scenario import load_scenario

SCENARIOS = sorted(
    p for p in glob.glob("eval/scenarios/*.yaml") if "lam_windows" not in p
)


def test_robot_radius_matches_run_module():
    """The screen must model the same footprint the simulator uses."""
    from eval.mppi_sandbox import feasibility

    assert feasibility.DEFAULT_ROBOT_RADIUS == ROBOT_RADIUS


def test_cut_in_goal_ball_is_provably_occupied():
    """The headline Q-037 result, with the arithmetic spelled out.

    ped_cut_in parks at (0, -3.8) from t = 5.0 onward; the goal is (0, -4.0)
    with a 0.2 m tolerance. Best point in the ball is 0.4 m from the parked
    centre, against 0.6 m of summed radii.
    """
    verdict = goal_ball_clearance(load_scenario("eval/scenarios/cafe_cut_in_v0.yaml"))

    assert verdict.best_clearance == pytest.approx(-0.2, abs=1e-9)
    assert not verdict.is_reachable
    assert not verdict.meets_acceptance
    assert verdict.blocking_obstacle == 0


def test_cut_in_acceptance_block_is_self_contradictory():
    """`goal_reached: 1` and `collision: 0` cannot both hold in this scene.

    This is the statement that makes it a *scene* defect rather than a
    controller capability gap: the target is not merely hard, it is excluded
    by the scenario's own two hard checks.
    """
    scenario = load_scenario("eval/scenarios/cafe_cut_in_v0.yaml")

    assert scenario.acceptance["goal_reached"] == 1
    assert scenario.acceptance["collision"] == 0
    # Being at the goal implies interpenetration, i.e. collision != 0.
    assert goal_ball_clearance(scenario).best_clearance < 0.0


def test_cut_in_is_the_only_unreachable_shipped_scene():
    """Screen the whole matrix — one failure, and it is not marginal."""
    verdicts = {v.scenario: v for v in screen_scenarios(SCENARIOS)}
    unreachable = sorted(k for k, v in verdicts.items() if not v.is_reachable)

    assert unreachable == ["cafe-cut-in-v0"]

    # The criterion is nowhere near its decision boundary: every other scene
    # with obstacles clears by > 1 m, so this is not a threshold that happens
    # to land between two similar scenes.
    others = [v.best_clearance for k, v in verdicts.items()
              if k != "cafe-cut-in-v0" and np.isfinite(v.best_clearance)]
    assert others and min(others) > 1.0


def test_screen_agrees_with_measured_lam_table():
    """Static screen vs 16:00's empirical `completes_anywhere`.

    The calibration table recorded `cafe_cut_in_v0` as completing at no rung
    for either controller, and every other scene as completing somewhere. The
    static screen must reproduce exactly that partition — if it ever does not,
    one of the two is wrong and the disagreement is the finding.
    """
    import yaml

    cells = yaml.safe_load(open("eval/scenarios/lam_windows.yaml"))["cells"]
    assert cells, "calibration table is empty — the cross-check would be vacuous"

    # A scene is empirically uncompletable only if NO controller finished it
    # anywhere; one controller failing is a controller result, not a scene one.
    by_scene: dict[str, list[bool]] = {}
    for cell in cells:
        stem = cell["scenario"].removesuffix(".yaml")
        by_scene.setdefault(stem, []).append(bool(cell["completes_anywhere"]))
    empirically_never = {s for s, ok in by_scene.items() if not any(ok)}
    assert empirically_never, "ladder recorded no uncompletable scene — expected cut_in"

    statically_never = {
        v.scenario.replace("-", "_") for v in screen_scenarios(SCENARIOS)
        if not v.is_reachable
    }

    assert statically_never == empirically_never, (
        f"static screen flags {statically_never}, "
        f"~500-run ladder flagged {empirically_never}"
    )


def test_screen_is_optimistic_for_obstacle_free_scenes():
    """No obstacles => infinite clearance, never retired by this screen."""
    verdict = goal_ball_clearance(load_scenario("eval/scenarios/cafe_straight_v0.yaml"))

    assert verdict.best_clearance == float("inf")
    assert verdict.is_reachable
    assert verdict.blocking_obstacle is None


def test_earliest_arrival_bound_is_loose_but_positive():
    """The arrival bound must not be so tight that it hides an occupation.

    cafe_cut_in's 4 m path at v_max = 0.8 cannot be done under 5 s, which is
    exactly when the pedestrian parks — so even the optimistic bound puts the
    robot at the goal no earlier than the obstacle.
    """
    verdict = goal_ball_clearance(load_scenario("eval/scenarios/cafe_cut_in_v0.yaml"))

    assert verdict.earliest_arrival_s == pytest.approx(5.0, abs=1e-6)
