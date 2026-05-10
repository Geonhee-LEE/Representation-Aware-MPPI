# SPDX-License-Identifier: BSD-3-Clause
"""Smoke tests for the include_run_metrics launch flag on jackal_cafe.launch.py.

Tests load the launch file as a plain Python module and walk its
LaunchDescription. They do NOT spawn any nodes — `launch` package itself
does not need rclpy. This keeps the test runnable in CI without a ROS2
environment, matching the offline-first contract used by
test_run_metrics.py (lazy rclpy import).

If `launch` is not importable (e.g. ROS2 not sourced), the whole module
is skipped via importorskip — the autoresearch CI shell sources jazzy so
this is normally green.
"""
from __future__ import annotations

import importlib.util
import os
import unittest

import pytest

launch = pytest.importorskip("launch")
ament_index_python = pytest.importorskip("ament_index_python")


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LAUNCH_FILE = os.path.join(
    REPO_ROOT, "src", "representation_aware_mppi_bringup", "launch",
    "jackal_cafe.launch.py")


def _load_launch_module():
    spec = importlib.util.spec_from_file_location(
        "jackal_cafe_launch", LAUNCH_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _declared_args(ld):
    from launch.actions import DeclareLaunchArgument
    return {
        a.name: a for a in ld.entities if isinstance(a, DeclareLaunchArgument)
    }


class LaunchIncludeRunMetricsTests(unittest.TestCase):
    """Verify the include_run_metrics integration contract."""

    def setUp(self):
        self.mod = _load_launch_module()
        self.ld = self.mod.generate_launch_description()
        self.args = _declared_args(self.ld)

    def test_include_run_metrics_arg_default_false(self):
        self.assertIn("include_run_metrics", self.args)
        self.assertEqual(
            self.args["include_run_metrics"].default_value[0].text, "false")

    def test_run_id_arg_default(self):
        self.assertIn("run_id", self.args)
        self.assertEqual(
            self.args["run_id"].default_value[0].text, "run-default")

    def test_target_speed_arg_default(self):
        self.assertIn("target_speed", self.args)
        self.assertEqual(
            self.args["target_speed"].default_value[0].text, "0.5")

    def test_output_dir_arg_default(self):
        self.assertIn("run_metrics_output_dir", self.args)
        self.assertEqual(
            self.args["run_metrics_output_dir"].default_value[0].text, "runs")

    def test_pythonpath_arg_default_empty(self):
        self.assertIn("run_metrics_pythonpath", self.args)
        # Empty default == no overrides emit `value=''` token list.
        tokens = self.args["run_metrics_pythonpath"].default_value
        self.assertTrue(all(t.text == "" for t in tokens))

    def test_legacy_args_still_present(self):
        for name in ("namespace", "headless", "use_rviz", "world",
                     "params_file", "slam", "x", "y", "z", "yaw"):
            self.assertIn(name, self.args, f"legacy arg {name} regressed")


if __name__ == "__main__":
    unittest.main()
