# SPDX-License-Identifier: BSD-3-Clause
"""cbf_mppi contract tests (issue #65 S1, cbfkit safety-filter architecture).

The safety filter's promise is a *floor*, not performance: with the default
margin the head-on clearance must stay near the margin instead of the stock
graze (0.005 m), and the filter must be exactly transparent when inactive.
"""

import numpy as np
import pytest

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.cbf_mppi import solve_qp_2d
from eval.mppi_sandbox.run import run_scenario, simulate
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

HEAD_ON_YAML = "eval/scenarios/cafe_head_on_v0.yaml"


class TestQPSolver:
    def test_feasible_nominal_is_returned_unchanged(self):
        u = solve_qp_2d(np.array([0.4, 0.1]),
                        np.array([[1.0, 0.0]]), np.array([0.0]))
        np.testing.assert_allclose(u, [0.4, 0.1])

    def test_single_active_constraint_projects(self):
        # v >= 0.5 active for nominal v = 0.4
        u = solve_qp_2d(np.array([0.4, 0.1]),
                        np.array([[1.0, 0.0]]), np.array([0.5]))
        np.testing.assert_allclose(u, [0.5, 0.1])

    def test_pair_intersection(self):
        # v >= 0.5 and omega >= 0.2 both active
        u = solve_qp_2d(np.array([0.0, 0.0]),
                        np.array([[1.0, 0.0], [0.0, 1.0]]),
                        np.array([0.5, 0.2]))
        np.testing.assert_allclose(u, [0.5, 0.2])

    def test_infeasible_returns_min_violation_not_crash(self):
        # v >= 1 and v <= 0 (i.e., -v >= 0): empty set
        u = solve_qp_2d(np.array([0.5, 0.0]),
                        np.array([[1.0, 0.0], [-1.0, 0.0]]),
                        np.array([1.0, 0.0]))
        assert u is not None and np.isfinite(u).all()


class TestFilterTransparency:
    def test_no_obstacles_passes_nominal_through_exactly(self):
        scenario = _straight_scenario()
        stock = make_controller("stock_mppi", scenario, seed=3)
        cbf = make_controller("cbf_mppi", scenario, seed=3)
        np.testing.assert_array_equal(simulate(scenario, stock),
                                      simulate(scenario, cbf))


class TestSafetyFloor:
    def test_head_on_clearance_respects_margin_floor(self):
        """Default margin 0.25 must hold clearance near the floor — an
        order of magnitude above the stock graze (0.005), with the small
        residual gap coming from time discretization."""
        r = run_scenario(HEAD_ON_YAML, controller="cbf_mppi", seed=0)
        assert r["collision"] is False
        assert r["metrics"]["goal_reached"] == 1
        assert r["min_obstacle_clearance"] > 0.15, r["min_obstacle_clearance"]

    def test_risk_nominal_composes_with_filter(self):
        r = run_scenario(HEAD_ON_YAML, controller="cbf_mppi", seed=0,
                         nominal="risk_mppi")
        assert r["collision"] is False
        assert r["min_obstacle_clearance"] > 0.15

    def test_unknown_nominal_raises(self):
        scenario = _straight_scenario()
        with pytest.raises(KeyError):
            make_controller("cbf_mppi", scenario, nominal="no_such")
