# SPDX-License-Identifier: BSD-3-Clause
"""En-route clearance screen — the answer to Q-108.

D-120 measured `unsafe_rate` against each scene's own declared margin and
`cafe_head_on_v0` and `cafe_obstacle_crossing_v0` came back **8/8 on both
controllers**. The identical verdict hid two opposite causes, and separating
them is what these tests pin: head-on is a scene whose margin cannot be held
on the reference path at all, crossing is a scene whose margin is attainable
without ever leaving it.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.feasibility import (
    DEFAULT_ROBOT_RADIUS,
    declared_corridor,
    declared_margin,
    goal_ball_clearance,
    path_clearance,
    required_corridor,
)
from eval.mppi_sandbox.obstacles import DEFAULT_RADIUS, CircleObstacle
from eval.mppi_sandbox.scenario import Scenario, load_scenario

SCENARIOS = "eval/scenarios"

#: Surface-to-surface offset between two circle centres at zero clearance.
CONTACT = DEFAULT_RADIUS + DEFAULT_ROBOT_RADIUS


def _scene(name):
    return load_scenario(f"{SCENARIOS}/{name}.yaml")


# --------------------------------------------------------------------------
# The corridor reader
# --------------------------------------------------------------------------

def test_declared_corridor_reads_cte_max_only():
    """`cte_max` is the corridor; `cte_rms_max` is deliberately not read.

    An rms bound constrains the whole run and a corridor constrains every
    instant. Folding one into the other would let this screen retire a scene
    whose controller passes by making a brief excursion — the exact direction
    the screen is forbidden to err in.
    """
    assert declared_corridor(_scene("cafe_obstacle_crossing_v0")) == 1.0

    head_on = _scene("cafe_head_on_v0")
    assert declared_corridor(head_on) is None
    assert head_on.acceptance["cte_rms_max"] == 0.30, (
        "the scene does declare a lateral *rms* bound; the point of the None "
        "above is that the reader refuses to promote it to a corridor"
    )


def test_most_shipped_scenes_declare_no_corridor():
    """The absent case is the common one, so it must not be filled in."""
    names = ["cafe_convoy_v0", "cafe_cut_in_v0", "cafe_freezing_v0",
             "cafe_head_on_v0", "cafe_obstacle_crossing_v0"]
    absent = [n for n in names if declared_corridor(_scene(n)) is None]
    assert len(absent) == 4 and "cafe_obstacle_crossing_v0" not in absent


# --------------------------------------------------------------------------
# Q-108: two scenes, one verdict, opposite causes
# --------------------------------------------------------------------------

def test_head_on_margin_is_unattainable_on_the_reference_path():
    """The pedestrian sweeps every station, so the margin is all lateral.

    `ped_head_on` walks y = -5.5 -> +0.5 while the robot must traverse
    y = 0 -> -4, a strict subset. No schedule avoids an instant of zero
    longitudinal separation, so the whole margin has to come out of the
    lateral budget and the on-path bound is an interpenetration.
    """
    s = _scene("cafe_head_on_v0")
    on_path = path_clearance(s, corridor_half_width=0.0)

    assert on_path.best_clearance < 0.0
    assert not on_path.meets_acceptance
    assert not on_path.is_reachable


def test_head_on_required_corridor_is_the_margin_plus_both_radii():
    """Closed form, because the encounter is exactly head-on.

    At the sweep instant the separation is purely lateral, so holding margin m
    needs |e| = m + r_obs + r_robot. Recovering that identity from the DP is
    the check that the search is finding the true optimum and not a lucky
    grid cell.
    """
    s = _scene("cafe_head_on_v0")
    expected = declared_margin(s) + CONTACT
    assert required_corridor(s) == pytest.approx(expected, abs=0.02)


def test_crossing_margin_is_attainable_without_leaving_the_path():
    """The five crossing pedestrians open gaps in *time*, not in space.

    Same 8/8 unsafe verdict as head-on in D-120 and the opposite cause: a
    corridor of zero suffices, so every unsafe seed here is the controller
    failing to use timing that provably exists.
    """
    s = _scene("cafe_obstacle_crossing_v0")
    on_path = path_clearance(s, corridor_half_width=0.0)

    assert on_path.meets_acceptance
    assert on_path.best_clearance >= declared_margin(s)
    assert required_corridor(s) == 0.0


def test_the_two_d120_failures_have_opposite_causes():
    """The contrast itself, stated once — this is Q-108's answer.

    Both scenes were 8/8 unsafe on both controllers. If the screen graded them
    alike it would carry no information about which of them is a controller
    target, which is the whole question D-120 left open.
    """
    head_on = required_corridor(_scene("cafe_head_on_v0"))
    crossing = required_corridor(_scene("cafe_obstacle_crossing_v0"))

    assert crossing == 0.0 < head_on


# --------------------------------------------------------------------------
# Soundness of the search
# --------------------------------------------------------------------------

def test_clearance_is_monotone_in_corridor_width():
    """Bisection in `required_corridor` depends on this.

    A narrower corridor's schedules stay admissible in a wider one, so extra
    lateral room can never lower the bound.
    """
    s = _scene("cafe_head_on_v0")
    widths = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
    got = [path_clearance(s, corridor_half_width=w).best_clearance
           for w in widths]
    assert got == sorted(got)


def test_grid_resolution_errs_optimistic_never_pessimistic():
    """The discretisation floor must sit on the safe side of the exact value.

    On-path head-on the exact worst instant is contact, clearance `-CONTACT`.
    The time grid can miss that instant by half a step, so the bound reads
    slightly *higher*. Reading lower would mean the screen could retire a
    scene for a reason that is only sampling.
    """
    on_path = path_clearance(_scene("cafe_head_on_v0"), corridor_half_width=0.0)
    assert -CONTACT <= on_path.best_clearance < -CONTACT + 0.1


def test_obstacle_parked_on_the_path_forces_a_corridor():
    """Positive control: a static hazard the schedule cannot outwait."""
    s = Scenario(
        name="parked", start=np.array([0.0, 0.0, 0.0]),
        goal=np.array([4.0, 0.0, 0.0]),
        waypoints=np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0]]),
        target_speed=0.5, expected_duration=10.0,
        obstacles=[CircleObstacle(x=2.0, y=0.0)],
        acceptance={"min_distance_to_obstacle": 0.2},
    )
    assert path_clearance(s, corridor_half_width=0.0).best_clearance < 0.0
    assert required_corridor(s) == pytest.approx(0.2 + CONTACT, abs=0.02)


def test_empty_scene_screens_vacuous_rather_than_clean():
    """Negative control: nothing to hit is `inf`, not a passing number.

    D-107's empty-population-reads-as-clean is the failure mode; `inf` is
    honest here because the screen is an upper bound and there genuinely is
    no upper bound when the world is empty.
    """
    s = _scene("cafe_straight_v0")
    assert not s.obstacles
    assert path_clearance(s, corridor_half_width=0.0).best_clearance == np.inf


def test_no_corridor_declared_means_the_default_screen_says_nothing():
    """Defaulting to the declared `cte_max` makes head-on vacuous on purpose.

    The useful question needs a width the yaml does not supply, which is why
    `required_corridor` exists rather than a bare pass/fail on the default.
    """
    default = path_clearance(_scene("cafe_head_on_v0"))
    assert default.best_clearance == np.inf and default.meets_acceptance


def test_cut_in_is_refused_by_both_screens():
    """Cross-check against the screen that already retired it (Q-037).

    `cafe_cut_in_v0` parks a pedestrian 0.4 m from the goal ball's best point,
    so `goal_ball_clearance` proves it uncompletable. An independent en-route
    bound disagreeing with that would mean one of the two is wrong.
    """
    s = _scene("cafe_cut_in_v0")
    assert not goal_ball_clearance(s).is_reachable
    assert not path_clearance(s, corridor_half_width=0.0).is_reachable
