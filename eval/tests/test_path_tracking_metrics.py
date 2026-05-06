# SPDX-License-Identifier: BSD-3-Clause
"""Sanity tests for eval.path_tracking_metrics.

Synthetic trajectories with closed-form ground truth; no ROS dependency.
Run: python -m pytest eval/tests/  (or python -m unittest)
"""

import math
import unittest

import numpy as np

from eval.path_tracking_metrics import (
    Goal,
    completion_percent,
    cross_track_error,
    goal_reached,
    heading_error,
    smoothness,
    summary,
    time_deviation,
)


def _straight_path(length=10.0, n=11):
    xs = np.linspace(0, length, n)
    return np.stack([xs, np.zeros(n), np.zeros(n)], axis=1)


def _on_path_traj(length=10.0, n=11, speed=1.0):
    xs = np.linspace(0, length, n)
    ts = xs / speed
    return np.stack(
        [ts, xs, np.zeros(n), np.zeros(n),
         np.full(n, speed), np.zeros(n)],
        axis=1,
    )


class CrossTrackErrorTest(unittest.TestCase):
    def test_zero_on_path(self):
        path = _straight_path()
        traj = _on_path_traj()
        np.testing.assert_allclose(cross_track_error(traj, path), 0.0, atol=1e-9)

    def test_constant_offset(self):
        path = _straight_path()
        traj = _on_path_traj()
        traj[:, 2] = 0.5  # offset y by +0.5 (left of path direction = positive)
        np.testing.assert_allclose(cross_track_error(traj, path), 0.5, atol=1e-9)

    def test_negative_offset(self):
        path = _straight_path()
        traj = _on_path_traj()
        traj[:, 2] = -0.3
        np.testing.assert_allclose(cross_track_error(traj, path), -0.3, atol=1e-9)


class HeadingErrorTest(unittest.TestCase):
    def test_aligned(self):
        path = _straight_path()
        traj = _on_path_traj()
        np.testing.assert_allclose(heading_error(traj, path), 0.0, atol=1e-9)

    def test_quarter_turn(self):
        path = _straight_path()
        traj = _on_path_traj()
        traj[:, 3] = math.pi / 2
        np.testing.assert_allclose(heading_error(traj, path), math.pi / 2, atol=1e-9)

    def test_wrap_to_pi(self):
        path = _straight_path()
        traj = _on_path_traj()
        traj[:, 3] = math.pi - 0.1  # near +pi
        # path tangent is 0; heading error should stay close to +pi-0.1
        # (not wrap to negative side)
        e = heading_error(traj, path)
        self.assertTrue(np.all(np.abs(e - (math.pi - 0.1)) < 1e-9))


class CompletionPercentTest(unittest.TestCase):
    def test_endpoints(self):
        path = _straight_path(length=10.0)
        traj = _on_path_traj(length=10.0)
        cp = completion_percent(traj, path)
        self.assertAlmostEqual(cp[0], 0.0, places=9)
        self.assertAlmostEqual(cp[-1], 1.0, places=9)

    def test_clamped_when_overshooting(self):
        path = _straight_path(length=10.0)
        traj = _on_path_traj(length=10.0)
        traj[-1, 1] = 15.0  # past end
        cp = completion_percent(traj, path)
        self.assertAlmostEqual(cp[-1], 1.0, places=9)


class TimeDeviationTest(unittest.TestCase):
    def test_on_schedule(self):
        path = _straight_path(length=10.0)
        traj = _on_path_traj(length=10.0, speed=1.0)
        td = time_deviation(traj, path, target_speed=1.0)
        np.testing.assert_allclose(td, 0.0, atol=1e-9)

    def test_behind_schedule(self):
        path = _straight_path(length=10.0)
        traj = _on_path_traj(length=10.0, speed=0.5)  # half target
        td = time_deviation(traj, path, target_speed=1.0)
        # at completion 1.0, expected_t = 10.0/1.0 = 10.0;
        # actual_t = 10.0/0.5 = 20.0 → deviation = +10.0
        self.assertAlmostEqual(td[-1], 10.0, places=6)

    def test_invalid_speed(self):
        with self.assertRaises(ValueError):
            time_deviation(_on_path_traj(), _straight_path(), target_speed=0.0)


class SmoothnessTest(unittest.TestCase):
    def test_constant_velocity(self):
        traj = _on_path_traj()
        sm = smoothness(traj)
        # constant v, zero omega → zero jerk
        self.assertAlmostEqual(sm["jerk_lon"], 0.0, places=6)
        self.assertAlmostEqual(sm["jerk_lat"], 0.0, places=6)

    def test_short_traj_returns_zero(self):
        traj = np.zeros((2, 6))
        sm = smoothness(traj)
        self.assertEqual(sm, {"jerk_lat": 0.0, "jerk_lon": 0.0, "accel_var": 0.0})


class GoalReachedTest(unittest.TestCase):
    def test_reaches_within_tolerance(self):
        traj = _on_path_traj(length=10.0)
        self.assertTrue(goal_reached(traj, Goal(10.0, 0.0, 0.0)))

    def test_misses_xy(self):
        traj = _on_path_traj(length=10.0)
        self.assertFalse(goal_reached(traj, Goal(10.0, 5.0, 0.0)))

    def test_misses_yaw(self):
        traj = _on_path_traj(length=10.0)
        self.assertFalse(goal_reached(traj, Goal(10.0, 0.0, math.pi), yaw_tol=0.1))


class SummaryTest(unittest.TestCase):
    def test_perfect_run(self):
        path = _straight_path(length=10.0)
        traj = _on_path_traj(length=10.0)
        s = summary(traj, path, target_speed=1.0)
        self.assertAlmostEqual(s["cte_rms"], 0.0, places=9)
        self.assertAlmostEqual(s["heading_err_rms"], 0.0, places=9)
        self.assertAlmostEqual(s["completion_final"], 1.0, places=9)
        self.assertAlmostEqual(s["time_deviation_final"], 0.0, places=6)
        self.assertEqual(s["goal_reached"], 1)


if __name__ == "__main__":
    unittest.main()
