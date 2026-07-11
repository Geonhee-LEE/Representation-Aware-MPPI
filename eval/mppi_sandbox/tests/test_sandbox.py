# SPDX-License-Identifier: BSD-3-Clause
"""Sandbox contract tests — the CI gate every controller must pass (D-016).

Covers: straight-path acceptance, determinism, static + head-on dynamic
obstacle avoidance, and JSON schema stability. Pure NumPy, seconds to run:
    python -m pytest eval/mppi_sandbox/tests/
"""

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.obstacles import CircleObstacle, min_clearance
from eval.mppi_sandbox.run import ROBOT_RADIUS, run_scenario, simulate
from eval.mppi_sandbox.scenario import Scenario, load_scenario

STRAIGHT_YAML = "eval/scenarios/cafe_straight_v0.yaml"
HEAD_ON_YAML = "eval/scenarios/cafe_head_on_v0.yaml"


def _straight_scenario(**overrides) -> Scenario:
    """3 m straight drive along -Y (mirrors cafe_straight_v0)."""
    base = dict(
        name="unit-straight",
        start=np.array([0.0, 0.0, -np.pi / 2]),
        goal=np.array([0.0, -3.0, -np.pi / 2]),
        waypoints=np.array([[0.0, -y, -np.pi / 2] for y in (0.0, 1.0, 2.0, 3.0)]),
        target_speed=0.4,
        expected_duration=10.0,
        obstacles=[],
        acceptance={},
    )
    base.update(overrides)
    return Scenario(**base)


class TestStraightTracking:
    def test_cafe_straight_v0_passes_acceptance(self, tmp_path):
        result = run_scenario(STRAIGHT_YAML, seed=0, out_dir=tmp_path)
        assert result["pass"] is True, result["acceptance"]
        assert result["metrics"]["goal_reached"] == 1
        assert result["metrics"]["cte_rms"] <= 0.2
        assert (tmp_path / f"{result['run_id']}.json").exists()

    def test_json_schema_matches_run_metrics_contract(self):
        result = run_scenario(STRAIGHT_YAML, seed=0)
        for key in ("run_id", "started_at", "world", "robot",
                    "target_speed", "metrics"):
            assert key in result  # shared with eval/run_metrics.py schema
        for key in ("backend", "controller", "seed",
                    "min_obstacle_clearance", "collision", "pass"):
            assert key in result  # sandbox extensions
        for key in ("cte_rms", "cte_max", "heading_err_rms", "heading_err_max",
                    "completion_final", "time_deviation_final",
                    "jerk_lat", "jerk_lon", "accel_var", "goal_reached"):
            assert key in result["metrics"]


class TestDeterminism:
    def test_same_seed_identical_trajectory(self):
        scenario = _straight_scenario()
        trajs = []
        for _ in range(2):
            ctrl = make_controller("stock_mppi", scenario, seed=42)
            trajs.append(simulate(scenario, ctrl))
        np.testing.assert_array_equal(trajs[0], trajs[1])

    def test_different_seed_different_rollout_noise(self):
        scenario = _straight_scenario()
        trajs = []
        for seed in (0, 1):
            ctrl = make_controller("stock_mppi", scenario, seed=seed)
            trajs.append(simulate(scenario, ctrl))
        assert trajs[0].shape != trajs[1].shape or \
            not np.array_equal(trajs[0], trajs[1])


class TestObstacleAvoidance:
    def test_static_obstacle_on_path_no_collision(self):
        ob = CircleObstacle(x=0.0, y=-1.5)          # dead center on the path
        scenario = _straight_scenario(obstacles=[ob], expected_duration=15.0)
        ctrl = make_controller("stock_mppi", scenario, seed=0,
                               robot_radius=ROBOT_RADIUS)
        traj = simulate(scenario, ctrl)
        clearance = min_clearance(traj, [ob], ROBOT_RADIUS)
        assert clearance > 0.0, f"collision: clearance={clearance:.3f}"
        dist_goal = np.linalg.norm(traj[-1, 1:3] - scenario.goal[:2])
        assert dist_goal <= 0.3, f"goal missed by {dist_goal:.2f} m"

    def test_head_on_scenario_no_collision(self):
        result = run_scenario(HEAD_ON_YAML, seed=0)
        assert result["collision"] is False
        assert result["metrics"]["goal_reached"] == 1

    def test_unknown_acceptance_keys_are_skipped_not_failed(self):
        result = run_scenario(HEAD_ON_YAML, seed=0)
        assert result["acceptance"]["yield_or_pass_decision_time_max"] == "skipped"


class TestRegistry:
    def test_unknown_controller_raises_with_available_list(self):
        scenario = _straight_scenario()
        with pytest.raises(KeyError, match="stock_mppi"):
            make_controller("no_such_controller", scenario)
