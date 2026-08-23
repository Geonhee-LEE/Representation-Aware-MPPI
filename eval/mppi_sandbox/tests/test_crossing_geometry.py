# SPDX-License-Identifier: BSD-3-Clause
"""Q-190 crossing geometry: unit-level contracts, no integrations.

Same split as `test_avoidance_budget.py` — the 16-integration `measure_arm` is
exercised by the cycle that takes the reading; these tests pin the *scoring*,
where a silent error would move the verdict without moving the runtime.

The one measured fact pinned here is Reading A, because it needs no sim at all:
`cafe_obstacle_crossing_v0`'s five actors run exactly perpendicular to the
reference path, so Q-190 option (a) ("the scene never crosses") is refuted by
the yaml itself and no future cycle should have to re-derive that.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import crossing_geometry as cg
from eval.mppi_sandbox.scenario import load_scenario


class _Ob:
    """Circle on a straight constant-velocity course; matches the `ab` protocol."""

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 radius: float = 0.3) -> None:
        self._xy = np.array([x, y], dtype=float)
        self._v = np.array([vx, vy], dtype=float)
        self.radius = radius

    def position(self, t) -> np.ndarray:
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        return self._xy[None, :] + t_arr[:, None] * self._v[None, :]

    def velocity(self, t: float, eps: float = 0.05) -> np.ndarray:
        return self._v.copy()


def _traj(xs, ys, yaws, vs, dt: float = 0.1) -> np.ndarray:
    """(T, 6) log in `ab`'s column order `[t, x, y, yaw, v, omega]`."""
    out = np.zeros((len(xs), 6))
    out[:, 0] = np.arange(len(xs)) * dt
    out[:, 1], out[:, 2], out[:, 3], out[:, 4] = xs, ys, yaws, vs
    return out


#: Reference path runs along +x through the origin, so `t_hat = (1, 0)`.
STRAIGHT = np.array([[0.0, 0.0, 0.0], [5.0, 0.0, 0.0]])


# --------------------------------------------------------------------------
# Reading A — the scene, from the yaml alone
# --------------------------------------------------------------------------

def test_the_crossing_scene_actually_crosses():
    """Q-190 (a), refuted by the yaml: all five courses are perpendicular.

    Pinned as a measured fact rather than left in prose because it is the half
    of Q-190 that costs nothing, and because every null lateral-avoidance
    result on this scene is a statement about the controller only while this
    holds. If someone re-parameterises the actors along the path, this test is
    how the branch's four null sweeps get re-read as scene artefacts.
    """
    courses = cg.actor_courses(load_scenario(cg.SCENE))
    assert len(courses) == 5
    assert cg.course_verdict(courses).startswith("CROSSING")
    for c in courses:
        assert c.course_tangent_frac == pytest.approx(0.0, abs=1e-9)
        assert c.speed == pytest.approx(0.75, abs=1e-6)


def test_static_obstacles_have_no_course_and_are_skipped():
    """A body that never moves has no crossing angle to report.

    Reporting it as 0.0 would drag the population toward "crosses the path"
    for an obstacle that cannot cross anything.
    """
    scene = load_scenario(cg.SCENE)
    for ob in scene.obstacles:
        ob.schedule = np.empty((0, 3))
    assert cg.actor_courses(scene) == ()
    assert cg.course_verdict(()).startswith("NO_ACTOR")


def test_a_course_along_the_path_is_called_a_scene_defect():
    """The verdict's other branch, so `CROSSING` is a reading and not a constant."""
    scene = load_scenario(cg.SCENE)
    for ob in scene.obstacles:
        # Same axis as the reference path (which descends -y), not across it.
        ob.schedule = np.array([[0.0, 0.0, 0.0], [8.0, 0.0, -6.0]])
    verdict = cg.course_verdict(cg.actor_courses(scene))
    assert verdict.startswith("SCENE_DEFECT")


# --------------------------------------------------------------------------
# Reading B — the (CPA) identity
# --------------------------------------------------------------------------

def test_cpa_identity_is_exact_on_a_constructed_closest_approach():
    """On the geometry the identity is stated about, prediction == measurement.

    Robot on the path at the origin heading +x at 1 m/s; hazard directly
    abeam at (0, 2) moving +x at 1 m/s as well, so the range is stationary and
    the separation is exactly orthogonal to a zero relative velocity... which
    is degenerate. Give the hazard 2 m/s instead: `v_rel = (1, 0)`, the
    separation `(0, 2)` is orthogonal to it, so this instant *is* a closest
    approach and the identity must return `|v_rel x t_hat| / |v_rel| = 0`.
    """
    traj = _traj([0.0], [0.0], [0.0], [1.0])
    row = cg.score_one_run_cpa(traj, STRAIGHT, [_Ob(0.0, 2.0, 2.0, 0.0)],
                               0.1, seed=0)
    assert row.cpa_orthogonality == pytest.approx(0.0, abs=1e-9)
    assert row.predicted == pytest.approx(0.0, abs=1e-9)
    assert row.measured_from_robot == pytest.approx(0.0, abs=1e-9)


def test_prediction_uses_velocities_only_and_ignores_where_the_bodies_are():
    """The identity's whole content: move the hazard, keep the velocities.

    `predicted` must not move. This is what makes the residual a statement
    about the *instant* rather than about the separation, and it is the
    property that lets Reading B generalise off this scene.
    """
    traj = _traj([0.0], [0.0], [0.0], [1.0])
    near = cg.score_one_run_cpa(traj, STRAIGHT, [_Ob(0.5, 1.0, 0.0, 3.0)],
                                0.1, seed=0)
    far = cg.score_one_run_cpa(traj, STRAIGHT, [_Ob(-2.0, 4.0, 0.0, 3.0)],
                               0.1, seed=0)
    assert near.predicted == pytest.approx(far.predicted)
    assert near.predicted == pytest.approx(3.0 / np.hypot(1.0, 3.0))


def test_the_foot_origin_and_robot_origin_bearings_differ_by_the_excursion():
    """D-446's `bearing_tangent_frac` is read from the foot, (CPA) from the robot.

    This is the correction Q-190 turns up: the two origins are separated by the
    excursion, so on a scene where the robot has left the path they are not the
    same number and must not be quoted for each other. On the reference path
    they coincide — pinned here in both directions so the gap is understood as
    the excursion's doing and not as an error in either reading.
    """
    hazard = [_Ob(3.0, 0.5, 0.0, 2.0)]
    on_path = cg.score_one_run_cpa(_traj([0.0], [0.0], [0.0], [1.0]),
                                   STRAIGHT, hazard, 0.1, seed=0)
    assert on_path.measured == pytest.approx(on_path.measured_from_robot)

    off_path = cg.score_one_run_cpa(_traj([0.0], [-0.6], [0.0], [1.0]),
                                    STRAIGHT, hazard, 0.1, seed=0)
    assert off_path.measured != pytest.approx(off_path.measured_from_robot)
    # The foot is the robot's projection, so its bearing to a hazard ahead is
    # the more path-aligned of the two whenever the excursion is path-normal.
    assert off_path.measured > off_path.measured_from_robot


def test_no_hazard_is_an_error_not_a_nan():
    """Same refusal `avoidance_budget` makes: an undefined reading is not a value."""
    with pytest.raises(ValueError):
        cg.score_one_run_cpa(_traj([0.0], [0.0], [0.0], [1.0]),
                             STRAIGHT, [], 0.1, seed=0)


# --------------------------------------------------------------------------
# The verdict ladder
# --------------------------------------------------------------------------

def _row(**kw) -> cg.SeedCPA:
    base = dict(seed=0, index=0, t_s=0.0, measured=0.95,
                measured_from_robot=0.74, predicted=0.75, robot_speed=0.75,
                hazard_speed=0.75, rel_speed=1.06, cpa_orthogonality=0.05)
    base.update(kw)
    return cg.SeedCPA(**base)


def test_the_verdict_is_taken_against_the_robot_origin_bearing():
    """The band tests `measured_from_robot - predicted`, not the foot number.

    Stated as a test because it is the single place the frame correction could
    silently regress: a row whose foot-origin bearing is far from the
    prediction but whose robot-origin bearing is on it is KINEMATIC, and the
    opposite pairing is not.
    """
    on_identity = (_row(measured=0.99, measured_from_robot=0.75, predicted=0.75),)
    assert cg.explains(on_identity, 0.05).startswith("KINEMATIC")
    off_identity = (_row(measured=0.75, measured_from_robot=0.40, predicted=0.75),)
    assert cg.explains(off_identity, 0.05).startswith("UNEXPLAINED")


def test_seeds_without_a_defined_prediction_do_not_vote():
    """A vanished relative velocity has no identity to test, either way."""
    rows = (_row(predicted=float("nan")),)
    assert cg.explains(rows, 0.10).startswith("NO_PREDICTION")


def test_the_band_ladder_is_swept_not_fixed():
    """D-445's discipline: a verdict that moves with its own constant is not one."""
    rows = (_row(measured_from_robot=0.75, predicted=0.75),
            _row(seed=1, measured_from_robot=0.60, predicted=0.75))
    calls = cg.explains_over_bands(rows)
    assert set(calls) == set(cg.BANDS)
    assert calls[0.05].startswith("PARTIAL")
    assert calls[0.20].startswith("KINEMATIC")


def test_residuals_of_an_empty_population_are_nan_not_an_exception():
    """Same contract `avoidance_budget.shares` makes."""
    out = cg.residuals(())
    assert all(np.isnan(v) for v in out.values())
