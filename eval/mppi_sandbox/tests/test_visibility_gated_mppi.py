# SPDX-License-Identifier: BSD-3-Clause
"""visibility_gated_mppi (vg_mppi) contract + north-star tests.

Four claim classes:

1. Line-of-sight occlusion gate — a disc hidden behind a nearer disc is not in
   the observed set; it reveals once the robot moves off the shadowing ray.
2. Sensing-range gate — a disc whose nearest surface is beyond sensing_range is
   not observed; within range it is.
3. Ablation invariance — with sensing_range=inf and no obstacle occluding
   another, vg_mppi reproduces stock_mppi byte-for-byte (so any behaviour delta
   is attributable to the gate, not the plumbing).
4. North-star effect — on cafe_blind_approach_v0, the oracle (stock_mppi) never
   collides while the gated controller collides on a fraction of seeds and keeps
   a strictly smaller mean clearance: occlusion finally *moves a collision
   outcome*, the STATE 2026-07-13 bottleneck.
"""

import numpy as np

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.visibility_gated_mppi import VisibilityGatedMPPI
from eval.mppi_sandbox.obstacles import CircleObstacle, min_clearance
from eval.mppi_sandbox.run import ROBOT_RADIUS, run_scenario, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

BLIND_YAML = "eval/scenarios/cafe_blind_approach_v0.yaml"


class TestLineOfSightGate:
    def test_hazard_behind_nearer_disc_is_occluded_then_revealed(self):
        # near occluder on the x=0 line, hazard directly behind it
        occ = CircleObstacle(0.0, -2.5, radius=0.3)
        haz = CircleObstacle(0.0, -4.3, radius=0.3)
        scen = _straight_scenario(obstacles=[occ, haz])
        vg = make_controller("vg_mppi", scen, seed=0, robot_radius=ROBOT_RADIUS)

        # from the start pose the hazard sits in the occluder's shadow
        seen_start = vg.observed_obstacles(np.array([0.0, 0.0]), 0.0)
        assert occ in seen_start and haz not in seen_start

        # step off the shadowing ray → hazard reveals (occluder still seen)
        seen_side = vg.observed_obstacles(np.array([0.8, -3.0]), 0.0)
        assert haz in seen_side

    def test_disc_never_occludes_itself(self):
        ob = CircleObstacle(0.0, -3.0, radius=0.5)
        scen = _straight_scenario(obstacles=[ob])
        vg = make_controller("vg_mppi", scen, seed=0, robot_radius=ROBOT_RADIUS)
        assert vg.observed_obstacles(np.array([0.0, 0.0]), 0.0) == [ob]


class TestSensingRangeGate:
    def test_beyond_range_unobserved_within_range_observed(self):
        ob = CircleObstacle(0.0, -4.0, radius=0.4)   # nearest surface at 3.6 m
        scen = _straight_scenario(obstacles=[ob])
        vg = make_controller("vg_mppi", scen, seed=0, robot_radius=ROBOT_RADIUS,
                             sensing_range=1.0)
        assert vg.observed_obstacles(np.array([0.0, 0.0]), 0.0) == []      # 3.6 > 1.0
        assert vg.observed_obstacles(np.array([0.0, -3.2]), 0.0) == [ob]   # 0.4 < 1.0


class TestAblationInvariance:
    def test_inf_range_single_obstacle_reproduces_stock_byte_for_byte(self):
        ob = CircleObstacle(0.3, -2.0, radius=0.3)
        scen = _straight_scenario(obstacles=[ob], expected_duration=12.0)
        stock = make_controller("stock_mppi", scen, seed=5)
        vg = make_controller("vg_mppi", scen, seed=5)   # sensing_range=inf default
        np.testing.assert_array_equal(simulate(scen, stock), simulate(scen, vg))

    def test_default_sensing_range_is_infinite(self):
        scen = _straight_scenario(obstacles=[CircleObstacle(0.0, -2.0)])
        vg = make_controller("vg_mppi", scen, seed=0)
        assert vg.sensing_range == float("inf")
        assert isinstance(vg, VisibilityGatedMPPI)


class TestOcclusionMovesCollisionOutcome:
    """The Q-017 unblock: a visibility-gated baseline hits a hazard the oracle
    routes around. Aggregate over seeds — the effect is a raised collision
    *rate*, not a single deterministic crash (MPPI is stochastic per seed)."""

    def test_gated_collides_where_oracle_never_does(self):
        scen = load_scenario(BLIND_YAML)
        haz = scen.obstacles[0]
        seeds = range(8)
        stock_clr = [
            min_clearance(
                simulate(scen, make_controller("stock_mppi", scen, seed=s,
                                                robot_radius=ROBOT_RADIUS)),
                [haz], ROBOT_RADIUS)
            for s in seeds
        ]
        vg_clr = [
            min_clearance(
                simulate(scen, make_controller("vg_mppi", scen, seed=s,
                                                robot_radius=ROBOT_RADIUS,
                                                sensing_range=1.0)),
                [haz], ROBOT_RADIUS)
            for s in seeds
        ]
        # oracle sees the hazard from the start → never collides
        assert all(c >= 0.0 for c in stock_clr), stock_clr
        # blind controller collides on ≥1 seed and is worse in the mean
        assert sum(c < 0.0 for c in vg_clr) >= 1, vg_clr
        assert np.mean(vg_clr) < np.mean(stock_clr)

    def test_run_scenario_reports_gated_collision(self):
        # seed 4 deterministically collides for the gated controller and clears
        # for the oracle — exercises the run_scenario JSON/acceptance path.
        oracle = run_scenario(BLIND_YAML, controller="stock_mppi", seed=4)
        blind = run_scenario(BLIND_YAML, controller="vg_mppi", seed=4,
                             sensing_range=1.0)
        assert oracle["collision"] is False
        assert blind["collision"] is True
        # acceptance encodes the finding: oracle passes, blind fails on clearance
        assert oracle["acceptance"]["min_distance_to_obstacle"] is True
        assert blind["acceptance"]["min_distance_to_obstacle"] is False
