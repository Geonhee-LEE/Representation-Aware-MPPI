# SPDX-License-Identifier: BSD-3-Clause
"""PredictedGeometryCritic — PGIF anisotropic pedestrian cost (2608.08323 port).

The tests that carry the argument, rather than the shape:

- `test_cv_prediction_ignores_the_schedule` is the anti-confound one. The source
  paper predicts its orbital pedestrians with the simulator's own kinematics, so
  its prediction error is identically zero and its numbers are an upper bound.
  This pins that the port does not inherit that: the critic extrapolates
  constant-velocity from `t0` and is *wrong* through a waypoint corner, by
  construction.
- `test_ahead_costs_more_than_behind` and `test_ahead_lobe_grows_with_speed` are
  the anisotropy — the entire content of the borrow is three constants, and
  without these two it is an isotropic disc with extra arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from ..critics import PredictedGeometryCritic
from ..critics.predicted_geometry import (SIGMA_PAR_BASE, SIGMA_PAR_BEHIND,
                                          SIGMA_PAR_PER_SPEED, SIGMA_PERP)
from ..obstacles import CircleObstacle


def _walker(vx: float = 1.0, x0: float = 0.0, y0: float = 0.0, span: float = 10.0):
    """Pedestrian walking +x at `vx` m/s from (x0, y0) — one straight leg."""
    return CircleObstacle(
        x=x0, y=y0,
        schedule=np.array([[0.0, x0, y0], [span, x0 + vx * span, y0]]),
    )


def _one_point(xy) -> np.ndarray:
    """A single rollout of a single horizon step at world point `xy`."""
    return np.asarray([xy], dtype=float)


def _cost_at(critic, obstacles, xy, t0=0.0, dt=0.1) -> float:
    return float(critic.cost(obstacles, _one_point(xy), K=1, t0=t0, dt=dt)[0])


# --------------------------------------------------------------- no-op contract

def test_zero_weight_is_an_exact_noop():
    """w_ped = 0.0 must reproduce the baseline bit-for-bit (ablation invariant)."""
    critic = PredictedGeometryCritic()          # default weight
    assert critic.w_ped == 0.0
    out = critic.cost([_walker()], np.zeros((8, 2)), K=2, t0=0.0, dt=0.1)
    assert np.array_equal(out, np.zeros(2))


def test_cost_is_nonnegative_and_shaped_per_rollout():
    critic = PredictedGeometryCritic(w_ped=10.0)
    xy = np.random.default_rng(0).uniform(-3, 3, size=(6 * 4, 2))
    out = critic.cost([_walker()], xy, K=6, t0=0.0, dt=0.1)
    assert out.shape == (6,)
    assert np.all(out >= 0.0)


def test_empty_obstacle_set_is_free():
    critic = PredictedGeometryCritic(w_ped=10.0)
    assert np.array_equal(critic.cost([], np.zeros((4, 2)), K=2, t0=0.0, dt=0.1),
                          np.zeros(2))


# ------------------------------------------------- standalone / no double-count

def test_static_obstacles_are_not_charged():
    """A wall is not a pedestrian.

    An obstacle with an empty schedule is already priced by the baseline
    obstacle term; charging it here too would break the standalone contract
    that P5 ablation attribution rests on.
    """
    wall = CircleObstacle(x=0.0, y=0.0)          # no schedule => static
    critic = PredictedGeometryCritic(w_ped=100.0)
    assert _cost_at(critic, [wall], (0.0, 0.0)) == 0.0


def test_a_pedestrian_at_rest_is_isotropic():
    """Speed below eps leaves the heading undefined, so the field degenerates to
    a `sigma_perp` disc rather than to an arbitrary direction."""
    still = CircleObstacle(
        x=0.0, y=0.0,
        schedule=np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]),   # scripted, static
    )
    critic = PredictedGeometryCritic(w_ped=1.0)
    r = 0.7
    ahead = _cost_at(critic, [still], (r, 0.0))
    behind = _cost_at(critic, [still], (-r, 0.0))
    lateral = _cost_at(critic, [still], (0.0, r))
    assert ahead == pytest.approx(behind)
    assert ahead == pytest.approx(lateral)
    assert ahead == pytest.approx(np.exp(-0.5 * (r / SIGMA_PERP) ** 2))


# ----------------------------------------------------------------- anisotropy

def test_ahead_costs_more_than_behind():
    """Cutting in front is charged far more than passing behind — the whole
    point of the borrow. Both probes sit the same distance from the pedestrian."""
    ped = _walker(vx=1.0)
    critic = PredictedGeometryCritic(w_ped=1.0)
    # evaluate at t0 with dt=0 so the pedestrian has not moved: pure geometry
    d = 1.0
    ahead = _cost_at(critic, [ped], (d, 0.0), t0=0.0, dt=0.0)
    behind = _cost_at(critic, [ped], (-d, 0.0), t0=0.0, dt=0.0)
    assert ahead > behind
    assert ahead == pytest.approx(
        np.exp(-0.5 * (d / (SIGMA_PAR_BASE + SIGMA_PAR_PER_SPEED * 1.0)) ** 2))
    assert behind == pytest.approx(np.exp(-0.5 * (d / SIGMA_PAR_BEHIND) ** 2))


def test_ahead_lobe_grows_with_speed():
    """sigma_par = 1.2 + 0.5*s ahead: the same point costs more at higher speed,
    because a moving person's danger zone is a cone, not a disc."""
    critic = PredictedGeometryCritic(w_ped=1.0)
    slow = _cost_at(critic, [_walker(vx=0.5)], (1.5, 0.0), t0=0.0, dt=0.0)
    fast = _cost_at(critic, [_walker(vx=2.0)], (1.5, 0.0), t0=0.0, dt=0.0)
    assert fast > slow


def test_behind_lobe_is_speed_independent():
    """Only the ahead lobe scales — sigma_par behind is a flat 0.5 m."""
    critic = PredictedGeometryCritic(w_ped=1.0)
    slow = _cost_at(critic, [_walker(vx=0.5)], (-0.4, 0.0), t0=0.0, dt=0.0)
    fast = _cost_at(critic, [_walker(vx=2.0)], (-0.4, 0.0), t0=0.0, dt=0.0)
    assert slow == pytest.approx(fast)


def test_lateral_extent_is_the_narrowest_axis():
    """sigma_perp = 0.6 < sigma_par ahead (>= 1.2), so a point abeam is cheaper
    than the same offset directly in front."""
    critic = PredictedGeometryCritic(w_ped=1.0)
    ped = _walker(vx=1.0)
    d = 1.0
    front = _cost_at(critic, [ped], (d, 0.0), t0=0.0, dt=0.0)
    abeam = _cost_at(critic, [ped], (0.0, d), t0=0.0, dt=0.0)
    assert front > abeam


# ------------------------------------------------- CV prediction, not the oracle

def test_cost_follows_the_predicted_position_not_the_current_one():
    """The field is placed where the pedestrian is *going*, over the horizon."""
    ped = _walker(vx=1.0)                       # at origin, walking +x at 1 m/s
    critic = PredictedGeometryCritic(w_ped=1.0)
    # one rollout, one horizon step at t0 + dt*1 = 1.0s => predicted at (1, 0)
    on_prediction = _cost_at(critic, [ped], (1.0, 0.0), t0=0.0, dt=1.0)
    on_current = _cost_at(critic, [ped], (0.0, 0.0), t0=0.0, dt=1.0)
    assert on_prediction > on_current


def test_cv_prediction_ignores_the_schedule():
    """The planner must not be handed the simulator's own motion model.

    This pedestrian walks +x for 2 s and then turns hard +y. A critic reading
    `position(t0 + h*dt)` would place its field at the true post-corner pose; a
    constant-velocity extrapolation from t0 continues straight through. The
    port is required to be the second one, and therefore to be *wrong* here —
    that wrongness is the whole reason the arm is gradeable against a real
    tracker's error rather than against an oracle's zero.
    """
    corner = CircleObstacle(x=0.0, y=0.0, schedule=np.array([
        [0.0, 0.0, 0.0],
        [2.0, 2.0, 0.0],       # +x leg
        [4.0, 2.0, 2.0],       # turns +y
    ]))
    critic = PredictedGeometryCritic(w_ped=1.0)

    truth = np.asarray(corner.position(4.0))            # (2, 2) — after the turn
    cv = np.asarray(corner.position(0.0)) + np.asarray(corner.velocity(0.0)) * 4.0
    assert not np.allclose(truth, cv), "test scene must actually corner"

    # a probe sitting on the true future pose must NOT be the more expensive one
    at_truth = _cost_at(critic, [corner], tuple(truth), t0=0.0, dt=4.0)
    at_cv = _cost_at(critic, [corner], tuple(cv), t0=0.0, dt=4.0)
    assert at_cv > at_truth


# ------------------------------------------------------------------ superposition

def test_multiple_pedestrians_superpose():
    critic = PredictedGeometryCritic(w_ped=1.0)
    a, b = _walker(vx=1.0, y0=0.0), _walker(vx=1.0, y0=1.0)
    probe = (0.3, 0.5)
    both = _cost_at(critic, [a, b], probe, t0=0.0, dt=0.0)
    solo = (_cost_at(critic, [a], probe, t0=0.0, dt=0.0)
            + _cost_at(critic, [b], probe, t0=0.0, dt=0.0))
    assert both == pytest.approx(solo)


def test_cost_accumulates_over_the_horizon():
    """cost_k sums the field over horizon steps, so a longer horizon in the same
    field is strictly more expensive."""
    critic = PredictedGeometryCritic(w_ped=1.0)
    ped = _walker(vx=1.0)
    one = critic.cost([ped], np.zeros((1, 2)), K=1, t0=0.0, dt=0.0)[0]
    four = critic.cost([ped], np.zeros((4, 2)), K=1, t0=0.0, dt=0.0)[0]
    assert four == pytest.approx(4.0 * one)


def test_weight_scales_linearly():
    critic1 = PredictedGeometryCritic(w_ped=1.0)
    critic7 = PredictedGeometryCritic(w_ped=7.0)
    ped, probe = _walker(vx=1.0), (0.5, 0.2)
    assert (_cost_at(critic7, [ped], probe)
            == pytest.approx(7.0 * _cost_at(critic1, [ped], probe)))
