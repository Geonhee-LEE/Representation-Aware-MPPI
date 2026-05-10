# SPDX-License-Identifier: BSD-3-Clause
"""Smoke tests for the include_run_metrics launch flag on
jackal_outdoor_sim.launch.py.

Mirrors test_launch_include_run_metrics.py (cafe variant, lands via the
jackal_cafe.launch.py PR). Lives in a separate file so the cafe + outdoor
PRs can land in any order without a merge conflict on the test file. Both
files share the same offline contract: walk the LaunchDescription, do
not spawn nodes, skip cleanly when `launch` is unimportable.
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
    "jackal_outdoor_sim.launch.py")


def _load_launch_module():
    spec = importlib.util.spec_from_file_location(
        "jackal_outdoor_sim_launch", LAUNCH_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _declared_args(ld):
    from launch.actions import DeclareLaunchArgument
    return {
        a.name: a for a in ld.entities if isinstance(a, DeclareLaunchArgument)
    }


class OutdoorLaunchIncludeRunMetricsTests(unittest.TestCase):
    """Verify the include_run_metrics integration contract on the outdoor
    (city / cafe-via-outdoor) launch."""

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
        tokens = self.args["run_metrics_pythonpath"].default_value
        self.assertTrue(all(t.text == "" for t in tokens))

    def test_legacy_args_still_present(self):
        for name in ("namespace", "headless", "use_rviz", "world",
                     "pedestrians", "params_file", "slam",
                     "x", "y", "z", "yaw"):
            self.assertIn(name, self.args, f"legacy arg {name} regressed")


if __name__ == "__main__":
    unittest.main()
