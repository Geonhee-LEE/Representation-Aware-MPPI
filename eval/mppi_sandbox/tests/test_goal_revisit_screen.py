# SPDX-License-Identifier: BSD-3-Clause
"""Q-047: is `city_figure8_v0`'s 0.016 m/s cruise a scene defect or a
controller failure? Measured answer: **neither option as posed** (D-026).

Q-047 offered two readings of the 03:00 cruise scan, with opposite
consequences: a third scene defect in Q-037's class (shrinking the reportable
matrix to 3) or a genuine controller failure on a *self-intersecting* reference
(the first capability finding in nine cycles). The two-directional intervention
below rejects both statements and identifies the actual mechanism, which is a
**controller contract** defect that `city_figure8_v0` merely happens to trip.

The intervention (D-018 discipline: change one thing, both directions)
---------------------------------------------------------------------
Measured 2026-08-03, `stock_mppi`, seeds 0-3, shipped params:

    A0  figure8   as shipped (goal == start)   cruise 0.0164   3/4   240 s
    A1  figure8   goal moved off start          cruise 0.2538   3/4   240 s
    B0  curved    as shipped (goal != start)   cruise 0.7385   4/4  21.3 s
    B1  curved    goal := start, nothing else   cruise  NaN     2/4  100 s

**B1 is the load-bearing cell.** `city_curved_v0` has no self-intersection, no
crossing point, and a healthy 0.739 m/s cruise. Moving *only* its goal onto its
start collapses it to a stall — `cruise_speed` returns NaN, i.e. the run never
leaves the regimes that statistic excludes. So a self-intersecting reference is
**not necessary** to produce the failure, which refutes Q-047's second option.

**A1 refutes the first.** If the scene's waypoints were the defect, repairing
the closure would repair the run. It does not: cruise recovers 15x but the run
still times out at 240 s having covered 13.1 m of a 30.6 m reference. Opening
the goal is necessary and **not sufficient**, so "defective scene" does not
describe it either.

The mechanism, and which half of it is load-bearing
---------------------------------------------------
`StockMPPI` steers by two quantities that are both functions of **Euclidean
distance to goal**, and neither is a function of **remaining arclength**:

    v_ref = min(target, max(gain * d_goal, creep))      # the speed ramp
    cost += w_terminal * d_goal[:, -1] ** 2             # the terminal pull

They agree with arclength only while the path approaches its goal
monotonically. `city_figure8_v0` violates this twice over: `d(start, goal) = 0`,
and the reference returns *exactly* to the goal at arclength fraction 0.5 — the
crossing point **is** the goal. So halfway through the route the loop sees
`d_goal -> 0`.

A 2x2 over the two terms says which one does the damage (figure8-opened and
curved-closed, seeds 0-3; `arclen` is metres actually driven, against a 30.6 m
and 13.6 m reference respectively):

    arm                       cruise   mean_v   arclen   reached
    A1 f8-opened  shipped     0.2538   0.0548    13.11     3/4
    A2 f8-opened  no ramp     0.3405   0.0490    11.78     3/4
    A3 f8-opened  no terminal 0.4525   0.3072    73.23     3/4
    A4 f8-opened  neither     0.4510   0.4507   108.06     0/4
    B1 curved-cl  shipped        NaN   0.0504     5.04     2/4
    B2 curved-cl  no ramp     0.0578   0.0480     4.72     0/4
    B4 curved-cl  neither     0.5252   0.4088    40.92     0/4

**The terminal pull is the binding term; the ramp is nearly inert.** Dropping
the ramp alone moves arclength the *wrong way* on both scenes (13.11 -> 11.78,
5.04 -> 4.72). Dropping `w_terminal` moves it 13.11 -> 73.23. That ordering is
what `w_terminal = 30.0` against `w_speed = 2.0` predicts, and it means the
failure is not "the robot is told to go slowly" but "the robot is told it has
already arrived": at the crossing point the terminal term is at its global
minimum, so every rollout that leaves is penalised. The loop parks on its own
goal with half the path unvisited.

`0/4 reached` in the `neither` arms is the expected other side of the same
coin — with no terminal term nothing asks the robot to stop, so it laps (108 m
of a 30.6 m reference). The fix is not deletion; see Q-048.

Control: **B0'**, the healthy scene with both terms removed, still finishes
4/4 at cruise 0.5674 in 28.05 s. So the removal does not repair scenes by
breaking the screen — it is specifically the goal-revisit geometry that makes
the terminal term pathological.

That is a statement about the controller's contract, not about one yaml file:
**the shipped objective assumes a monotone approach, and any reference that
revisits its goal neighbourhood is outside it.** A figure-8 is the shape that
trips it here; it is not the only such shape.

The completion guard is unsound on the same scenes
--------------------------------------------------
`ab.reached_goal` reads the **last sample only**. When `d(start, goal) <=
goal_xy_tol`, a run that never moves satisfies it. This is why the 03:00 scan
read "3/4 reached" at a 0.016 m/s cruise, and why B1 reports 2/4 while
manifestly not traversing its path — the guard was measuring the start.

What ships
----------
`feasibility.goal_approach` — a static, simulation-free screen for both
conditions, in the module Q-037 created for exactly this move ("generalise the
retirement, not the retiree"). It costs milliseconds and no rollout, and it
separates the matrix cleanly: `city_figure8_v0` is the sole failure on both
predicates and the next-worst scene clears the ramp radius by 1.6x.

What deliberately does **not** ship: any change to `StockMPPI`, `reached_goal`,
or `city_figure8_v0`. Q-032's rule holds (no correctness fix to a shared
baseline mid-queue) and the arclength-driven repair is a controller change with
its own re-baseline cost. The screen states the precondition; the repair is
Q-048, filed.
"""

from __future__ import annotations

import glob

import numpy as np
import pytest

from ..scenario import load_scenario
from .. import feasibility as fz

SCENARIOS = sorted(glob.glob("eval/scenarios/*_v0.yaml"))
FIGURE8 = "eval/scenarios/city_figure8_v0.yaml"
CURVED = "eval/scenarios/city_curved_v0.yaml"
CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"


class TestRampRadius:
    def test_solves_the_throttle_point_per_scene(self):
        """`gain * d = target_speed`, not a shared constant.

        The crossing scene declares 0.3 m/s and every other scene 0.5, so a
        single radius would be wrong on one of them by 1.7x.
        """
        crossing = load_scenario(CROSSING)
        curved = load_scenario(CURVED)

        assert fz.ramp_radius(crossing) == pytest.approx(0.3 / 0.8)
        assert fz.ramp_radius(curved) == pytest.approx(0.75)
        assert fz.ramp_radius(crossing) != fz.ramp_radius(curved)

    def test_scales_with_the_gain(self):
        """A larger gain throttles later, so the ball shrinks."""
        scen = load_scenario(CURVED)
        assert fz.ramp_radius(scen, 1.6) == pytest.approx(
            0.5 * fz.ramp_radius(scen, 0.8))


class TestFigure8IsTheSoleFailure:
    def test_only_figure8_fails_either_predicate(self):
        """The screen's verdict over the shipped 9-scene matrix."""
        verdicts = {p.split("/")[-1]: fz.goal_approach(load_scenario(p))
                    for p in SCENARIOS}
        assert len(verdicts) == 9

        failing = {n for n, g in verdicts.items() if not g.is_traversable}
        assert failing == {"city_figure8_v0.yaml"}

    def test_figure8_fails_both_predicates_not_one(self):
        """Both conditions fire, which is why A1 alone did not repair it."""
        g = fz.goal_approach(load_scenario(FIGURE8))

        assert g.start_goal_distance == 0.0
        assert not g.completion_guard_is_sound      # standing still "reaches"
        assert g.interior_min_distance == 0.0       # and the ramp bites inside
        assert not g.approach_is_monotone

    def test_the_revisit_is_the_crossing_point_not_just_the_start(self):
        """The mid-route revisit is the half of the defect A1 could not fix.

        Waypoint 8 of 17 *is* the goal — so even with the closure opened, the
        loop still throttles to creep at half arclength.
        """
        scen = load_scenario(FIGURE8)
        d = np.linalg.norm(scen.waypoints[:, :2] - scen.goal[:2], axis=1)
        interior_hits = [i for i in range(1, len(d) - 1)
                         if d[i] <= fz.ramp_radius(scen)]

        assert interior_hits == [8]
        assert d[8] == pytest.approx(0.0)

    def test_criterion_is_not_near_its_decision_boundary(self):
        """A screen that only just passes the survivors is not a screen.

        The tightest passing scene sits at 1.6x its ramp radius, so the verdict
        does not turn on the exact value of `goal_slowdown_gain`.
        """
        margins = []
        for p in SCENARIOS:
            g = fz.goal_approach(load_scenario(p))
            if g.approach_is_monotone:
                margins.append(g.interior_min_distance / g.ramp_radius)

        assert len(margins) == 8
        assert min(margins) > 1.5


class TestFinalApproachIsNotCountedAsARevisit:
    def test_monotone_approach_reports_no_interior_hit(self):
        """Every healthy scene ends inside the ramp — that is the point of it.

        The suffix strip is what keeps the intended final slowdown from being
        reported as a defect; without it all 8 scenes would fail.
        """
        for p in SCENARIOS:
            scen = load_scenario(p)
            g = fz.goal_approach(scen)
            final_d = np.linalg.norm(scen.waypoints[-1, :2] - scen.goal[:2])

            assert final_d <= g.ramp_radius, p       # all end in the ramp
            if p != FIGURE8:
                assert g.approach_is_monotone, p     # none are flagged

    def test_a_synthetic_detour_past_the_goal_is_caught(self):
        """Positive control: the screen fires on a non-self-intersecting path.

        A straight run that dips to the goal at mid-arclength and then departs
        again has no crossing and no closure — only a revisit. It must fail,
        which is what makes this a screen for the *mechanism* rather than for
        figure-eights.
        """
        scen = load_scenario(CURVED)
        scen.waypoints = np.array([
            [-28.0, 0.0, 0.0],
            [-22.0, 0.0, 0.0],
            [-16.0, 0.0, 0.0],      # == goal, at mid-arclength
            [-12.0, 4.0, 0.0],
            [-16.0, 0.0, 0.0],
        ], dtype=float)

        g = fz.goal_approach(scen)
        assert g.completion_guard_is_sound          # start is still far away
        assert not g.approach_is_monotone           # but the ramp bites inside
        assert 0.1 < g.interior_min_at_fraction < 0.9   # mid-route, not an end

    def test_whole_path_inside_the_ramp_does_not_crash(self):
        """Degenerate input: a path that never leaves the goal ball.

        The suffix strip consumes every waypoint. Must report the revisit
        rather than index off the end of the array. The start is left where it
        was, so the guard predicate stays sound — the two are separable.
        """
        scen = load_scenario(CURVED)
        scen.waypoints = np.array([[-16.0, 0.0, 0.0],
                                   [-16.1, 0.0, 0.0]], dtype=float)

        g = fz.goal_approach(scen)
        assert not g.approach_is_monotone
        assert g.interior_min_distance == pytest.approx(0.0)
        assert np.isfinite(g.interior_min_at_fraction)


class TestCompletionGuardSoundness:
    def test_guard_is_unsound_exactly_when_start_is_in_the_goal_ball(self):
        """The condition under which `ab.reached_goal` measures the start."""
        for p in SCENARIOS:
            scen = load_scenario(p)
            g = fz.goal_approach(scen)
            standing_still = np.tile(
                [0.0, *scen.start[:2], scen.start[2], 0.0, 0.0], (3, 1))

            from .. import ab
            assert ab.reached_goal(standing_still, scen) == (
                not g.completion_guard_is_sound), p

    def test_soundness_is_independent_of_the_ramp_predicate(self):
        """The two predicates are separable and must not be conflated.

        The synthetic detour above is guard-sound and ramp-unsound; a scene
        can also be the reverse. Reporting one verdict would hide whichever
        half a future scene trips.
        """
        scen = load_scenario(CURVED)
        scen.goal = scen.start.copy()               # closure without a revisit
        scen.waypoints = np.array([[-28.0, 0.0, 0.0],
                                   [-24.0, 3.0, 0.0],
                                   [-28.0, 0.0, 0.0]], dtype=float)

        g = fz.goal_approach(scen)
        assert not g.completion_guard_is_sound
        assert g.interior_min_at_fraction == pytest.approx(0.0)
