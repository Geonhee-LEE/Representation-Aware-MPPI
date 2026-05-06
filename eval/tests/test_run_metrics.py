# SPDX-License-Identifier: BSD-3-Clause
"""Pure-Python tests for eval.run_metrics — yaw conversion, msg→ndarray
conversion, and the JSON writer. The ROS2 wrapper itself is exercised only
in sim.
"""

from __future__ import annotations

import json
import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np

from eval.run_metrics import (
    RunMetricsConfig,
    _odom_row_from_pose_twist,
    _path_rows_from_poses,
    _quat_to_yaw,
    write_summary_json,
)

try:
    import eval.path_tracking_metrics  # noqa: F401
    HAS_PATH_TRACKING = True
except ModuleNotFoundError:
    # path_tracking_metrics lives on PR #4. Until it merges to main, the
    # JSON-write test below skips. Pure-Python helper tests (yaw, msg
    # conversion, short-input guards) still run.
    HAS_PATH_TRACKING = False


def _quat_from_yaw(yaw: float):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class TestQuatToYaw(unittest.TestCase):

    def test_identity_quaternion_is_zero_yaw(self):
        self.assertAlmostEqual(_quat_to_yaw(0.0, 0.0, 0.0, 1.0), 0.0, places=12)

    def test_quarter_turn_z_is_pi_over_2(self):
        qx, qy, qz, qw = _quat_from_yaw(math.pi / 2)
        self.assertAlmostEqual(_quat_to_yaw(qx, qy, qz, qw),
                               math.pi / 2, places=10)

    def test_negative_yaw_recovered(self):
        for yaw in (-2.0, -1.0, -0.3, 0.3, 1.0, 2.0):
            qx, qy, qz, qw = _quat_from_yaw(yaw)
            self.assertAlmostEqual(_quat_to_yaw(qx, qy, qz, qw),
                                   yaw, places=10)


class TestOdomRow(unittest.TestCase):

    def test_row_layout_matches_traj_contract(self):
        # Contract: [t, x, y, yaw, v, omega]. yaw=π/4, v=0.5, ω=0.1.
        row = _odom_row_from_pose_twist(
            stamp_sec=12.5,
            pos_x=1.0,
            pos_y=2.0,
            quat=_quat_from_yaw(math.pi / 4),
            lin_x=0.5,
            ang_z=0.1,
        )
        self.assertEqual(len(row), 6)
        self.assertAlmostEqual(row[0], 12.5)
        self.assertAlmostEqual(row[1], 1.0)
        self.assertAlmostEqual(row[2], 2.0)
        self.assertAlmostEqual(row[3], math.pi / 4, places=10)
        self.assertAlmostEqual(row[4], 0.5)
        self.assertAlmostEqual(row[5], 0.1)


class TestPathRowsFromPoses(unittest.TestCase):

    def _pose(self, x, y, yaw):
        qx, qy, qz, qw = _quat_from_yaw(yaw)
        return SimpleNamespace(
            position=SimpleNamespace(x=x, y=y),
            orientation=SimpleNamespace(x=qx, y=qy, z=qz, w=qw),
        )

    def test_empty_input_returns_zero_shaped(self):
        arr = _path_rows_from_poses([])
        self.assertEqual(arr.shape, (0, 3))

    def test_xy_yaw_extracted_in_order(self):
        poses = [self._pose(0.0, 0.0, 0.0),
                 self._pose(1.0, 0.0, 0.0),
                 self._pose(2.0, 1.0, math.pi / 4)]
        arr = _path_rows_from_poses(poses)
        self.assertEqual(arr.shape, (3, 3))
        np.testing.assert_allclose(arr[0], [0.0, 0.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(arr[1], [1.0, 0.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(arr[2], [2.0, 1.0, math.pi / 4], atol=1e-10)


class TestWriteSummaryJson(unittest.TestCase):

    def test_returns_none_when_traj_too_short(self):
        with TemporaryDirectory() as d:
            cfg = RunMetricsConfig(run_id="t", output_dir=Path(d))
            path = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
            self.assertIsNone(write_summary_json([[0.0] * 6], path, cfg))

    def test_returns_none_when_path_too_short(self):
        with TemporaryDirectory() as d:
            cfg = RunMetricsConfig(run_id="t", output_dir=Path(d))
            traj = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [0.1, 0.1, 0.0, 0.0, 0.0, 0.0]]
            self.assertIsNone(write_summary_json(
                traj, np.zeros((1, 3), dtype=float), cfg))

    @unittest.skipUnless(HAS_PATH_TRACKING,
                         "eval.path_tracking_metrics not on main yet (PR #4)")
    def test_writes_json_with_expected_shape(self):
        # Synthetic straight-line drive along +x at 0.5 m/s, on path
        # (0,0)→(1,0). Expected: cte≈0, completion→1, goal_reached=1.
        with TemporaryDirectory() as d:
            cfg = RunMetricsConfig(
                run_id="syn-line", output_dir=Path(d), target_speed=0.5)
            ts = np.linspace(0.0, 2.0, 21)
            xs = ts * 0.5
            traj = [[float(t), float(x), 0.0, 0.0, 0.5, 0.0]
                    for t, x in zip(ts, xs)]
            path = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)

            out = write_summary_json(traj, path, cfg)
            self.assertIsNotNone(out)
            self.assertTrue(out.exists())

            payload = json.loads(out.read_text())
            self.assertEqual(payload["run_id"], "syn-line")
            self.assertEqual(payload["n_traj"], 21)
            self.assertEqual(payload["n_path"], 2)
            self.assertAlmostEqual(payload["target_speed"], 0.5)

            metrics = payload["metrics"]
            for key in ("cte_rms", "cte_max", "heading_err_rms",
                        "heading_err_max", "completion_final",
                        "time_deviation_final", "jerk_lat", "jerk_lon",
                        "accel_var", "goal_reached"):
                self.assertIn(key, metrics)

            self.assertLess(metrics["cte_rms"], 1e-9)
            self.assertGreaterEqual(metrics["completion_final"], 0.99)
            self.assertEqual(metrics["goal_reached"], 1)


if __name__ == "__main__":
    unittest.main()
