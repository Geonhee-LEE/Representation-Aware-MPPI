# SPDX-License-Identifier: BSD-3-Clause
"""risk_mppi + RiskInflationCritic contract tests (D-013 + D-012 consumption).

The load-bearing test is baseline invariance: risk_mppi with every knob at
zero must reproduce stock_mppi byte-for-byte — the D-013 ablation
guarantee that lets P5 attribute any behavior change to the representation.
"""

import numpy as np

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.critics import RiskInflationCritic
from eval.mppi_sandbox.obstacles import CircleObstacle, min_clearance
from eval.mppi_sandbox.representations import GTBevProducer
from eval.mppi_sandbox.run import ROBOT_RADIUS, run_scenario, simulate
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

HEAD_ON_YAML = "eval/scenarios/cafe_head_on_v0.yaml"


class TestBaselineInvariance:
    def test_all_knobs_zero_reproduces_stock_byte_for_byte(self):
        ob = CircleObstacle(0.0, -1.5, schedule=np.array(
            [[0.0, 0.0, -1.5], [4.0, 1.5, -1.5]]))
        scenario = _straight_scenario(obstacles=[ob], expected_duration=15.0)
        stock = make_controller("stock_mppi", scenario, seed=7)
        risk0 = make_controller("risk_mppi", scenario, seed=7,
                                w_risk=0.0, k_margin_per_sigma=0.0)
        np.testing.assert_array_equal(simulate(scenario, stock),
                                      simulate(scenario, risk0))


class TestRiskInflationCritic:
    def test_zero_k_is_noop(self):
        critic = RiskInflationCritic(k_margin_per_sigma=0.0)
        pts = np.zeros((5, 2))
        assert (critic.margin(object(), pts) == 0.0).all()

    def test_tighten_only_and_delta_max_clamp(self):
        ob = CircleObstacle(2.0, 0.0, radius=0.3)
        bev = GTBevProducer([ob]).render(np.array([0.0, 0.0]), 0.0)
        critic = RiskInflationCritic(k_margin_per_sigma=2.0, delta_max=0.4)
        pts = np.array([[3.0, 0.0],    # shadow: sigma=1 -> 2.0 clamped to 0.4
                        [1.0, 1.0]])   # visible: sigma=0 -> 0.0
        m = critic.margin(bev, pts)
        assert m[0] == 0.4
        assert m[1] == 0.0
        assert (m >= 0.0).all()


class TestRepresentationMovesTheNeedle:
    def test_head_on_clearance_improves_over_stock(self):
        """Dynamic-channel consumption (w_risk default) must widen the berth
        vs the stock graze (0.005 m) while keeping goal + cte acceptance."""
        stock = run_scenario(HEAD_ON_YAML, seed=0)
        risk = run_scenario(HEAD_ON_YAML, controller="risk_mppi", seed=0)
        assert risk["metrics"]["goal_reached"] == 1
        assert risk["collision"] is False
        assert (risk["min_obstacle_clearance"]
                > stock["min_obstacle_clearance"] + 0.1), (
            f"risk_mppi {risk['min_obstacle_clearance']:.3f} must beat "
            f"stock {stock['min_obstacle_clearance']:.3f}")
        assert risk["metrics"]["cte_rms"] <= 0.30   # scenario acceptance

    def test_epistemic_margin_widens_berth_in_occlusion_geometry(self):
        """k·σ (D-013) only acts where the robot's corridor is shadowed —
        an on-path static obstacle casts its shadow over the far half of
        the lane, so k > 0 must buy clearance there (w_risk off isolates
        the epistemic effect)."""
        ob = CircleObstacle(0.0, -1.5)
        scenario = _straight_scenario(obstacles=[ob], expected_duration=15.0)
        clearances = {}
        for k in (0.0, 0.4):
            ctrl = make_controller("risk_mppi", scenario, seed=0,
                                   robot_radius=ROBOT_RADIUS,
                                   w_risk=0.0, k_margin_per_sigma=k)
            traj = simulate(scenario, ctrl)
            clearances[k] = min_clearance(traj, [ob], ROBOT_RADIUS)
        assert clearances[0.4] > clearances[0.0] + 0.02, clearances

    def test_registry_exposes_risk_mppi(self):
        scenario = _straight_scenario()
        ctrl = make_controller("risk_mppi", scenario, seed=0)
        assert ctrl.command(np.array([0.0, 0.0, -np.pi / 2, 0.0, 0.0]),
                            0.0).shape == (2,)
