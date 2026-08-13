# SPDX-License-Identifier: BSD-3-Clause
"""`time_to_goal` — first-arrival time, and the acceptance key it un-blocks.

`cafe_freezing_v0` has declared `time_to_goal_max: 12.0` since the scene landed
and nothing graded it: D-241's census pinned it as needing *first-arrival time*,
because the only wall-clock the harness produced was `duration_s`, the whole sim.
The gap was not cosmetic — stock_mppi seed 0 runs 13.1 s and arrives at 7.4 s, so
grading the declared 12.0 s limit against `duration_s` would have failed a run
that reached the goal in well under the limit.

These tests pin the distinction that motivated the metric (arrival ≠ duration),
the agreement that keeps it from drifting away from `goal_reached`, and the
direction the acceptance rule must take when no arrival happens at all.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import acceptance_coverage as ac
from eval.mppi_sandbox.run import check_acceptance
from eval.path_tracking_metrics import Goal, goal_reached, summary, time_to_goal

GOAL = Goal(1.0, 0.0, 0.0)


def _traj(rows):
    """rows = [(t, x, y, yaw), ...] -> the (T, 4) array the metrics read."""
    return np.asarray(rows, dtype=float)


def test_returns_first_arrival_not_last():
    """The defining property: the *first* qualifying timestep, not any later one."""
    traj = _traj([
        (0.0, 0.0, 0.0, 0.0),
        (1.0, 0.9, 0.0, 0.0),      # 0.1 m away -> inside a 0.2 m tolerance
        (2.0, 1.0, 0.0, 0.0),      # dead on, but arrival already happened at t=1
        (3.0, 1.0, 0.0, 0.0),
    ])
    assert time_to_goal(traj, GOAL) == pytest.approx(1.0)


def test_arrival_is_not_the_sim_duration():
    """The regression that motivated the metric (D-241's 13.1 s vs 12.0 s note).

    A run that arrives and keeps simulating has `duration_s` strictly greater
    than its arrival time. Grading a `time_to_goal_max` against the former is
    what made the key un-gradeable; this pins the two apart.
    """
    traj = _traj([(0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.0),
                  (2.0, 1.0, 0.0, 0.0), (9.0, 1.0, 0.0, 0.0)])
    duration_s = float(traj[-1, 0])
    assert time_to_goal(traj, GOAL) == pytest.approx(1.0)
    assert duration_s == pytest.approx(9.0)
    assert time_to_goal(traj, GOAL) < duration_s


def test_never_reached_is_none():
    traj = _traj([(0.0, 0.0, 0.0, 0.0), (1.0, 0.4, 0.0, 0.0),
                  (2.0, 0.5, 0.0, 0.0)])
    assert time_to_goal(traj, GOAL) is None


def test_yaw_tolerance_binds_too():
    """Inside the xy tolerance but pointing the wrong way is not an arrival."""
    traj = _traj([(0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 3.0)])
    assert time_to_goal(traj, GOAL) is None
    assert time_to_goal(traj, GOAL, yaw_tol=3.2) == pytest.approx(1.0)


@pytest.mark.parametrize("rows", [
    [(0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 0.0)],           # arrives
    [(0.0, 0.0, 0.0, 0.0), (1.0, 0.4, 0.0, 0.0)],           # never arrives
    [(0.0, 1.0, 0.0, 0.0), (1.0, 5.0, 0.0, 0.0)],           # starts arrived
    [(0.0, 0.0, 0.0, 0.0), (1.0, 1.0, 0.0, 3.0)],           # xy yes, yaw no
])
def test_agrees_with_goal_reached(rows):
    """`goal_reached` and `time_to_goal` share one predicate — pinned, not restated.

    D-241 tied two constants together with a test rather than letting a second
    statement of the same rule drift. Same pattern: these two functions must
    never disagree about whether the goal was reached.
    """
    traj = _traj(rows)
    assert goal_reached(traj, GOAL) == (time_to_goal(traj, GOAL) is not None)


def test_summary_carries_it():
    traj = _traj([(0.0, 0.0, 0.0, 0.0), (1.0, 0.5, 0.0, 0.0),
                  (2.0, 1.0, 0.0, 0.0)])
    path = np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
    out = summary(traj, path, goal=GOAL)
    assert out["time_to_goal"] == pytest.approx(2.0)
    assert out["goal_reached"] == 1


# --- the acceptance rule ------------------------------------------------------

BASE = {
    "cte_rms": 0.1, "cte_max": 0.2, "heading_err_rms": 0.05,
    "completion_final": 1.0, "goal_reached": 1, "freeze_duration": 0.5,
    "jerk_lat": 2.9, "time_to_goal": 7.4,
}


def test_rule_is_graded_not_skipped():
    """The key `cafe_freezing_v0` declares is now scored, so the census loses it."""
    assert ac.grades("time_to_goal_max")
    assert "time_to_goal_max" not in ac.UNGRADED_CENSUS.get("cafe_freezing_v0", [])


@pytest.mark.parametrize("ttg,limit,expected", [
    (7.4, 12.0, True),
    (12.0, 12.0, True),       # boundary is inclusive, as every other `_max` rule
    (13.1, 12.0, False),
])
def test_rule_compares_against_the_limit(ttg, limit, expected):
    metrics = dict(BASE, time_to_goal=ttg)
    assert check_acceptance({"time_to_goal_max": limit}, metrics, 1.0) == {
        "time_to_goal_max": expected}


def test_never_arrived_fails_rather_than_skips():
    """Direction matters: no arrival is the *worst* time, not an absent one.

    If `None` fell through to `"skipped"` the scene would silently stop asking
    exactly when the robot froze hard enough never to finish — the D-241 defect,
    reintroduced at the one input that most needs to fail.
    """
    metrics = dict(BASE, time_to_goal=None, goal_reached=0)
    verdict = check_acceptance({"time_to_goal_max": 12.0}, metrics, 1.0)
    assert verdict["time_to_goal_max"] is False
