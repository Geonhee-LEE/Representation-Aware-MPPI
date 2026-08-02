# SPDX-License-Identifier: BSD-3-Clause
"""Contract tests for `eval.mppi_sandbox.ab` — the seed × scene × speed harness.

These assert the *guard* behaviour, not any P3 finding: that the completion
guard actually rejects a non-finishing arm, that a `v_max` handicap actually
binds on realized speed, that pairing refuses mismatched seed sets, and that
`seed_sweep` reproduces what the hand-rolled loops computed. If a future cycle
weakens one of these, the three nuisance controls stop controlling anything
while still looking present at the call site.
"""

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario


def _scen(**kw):
    return _straight_scenario(obstacles=[CircleObstacle(0.0, -1.5)], **kw)


class TestCompletionGuard:
    def test_finishing_run_passes_the_guard(self):
        scen = _scen(expected_duration=15.0)
        run = ab.run_arm(scen, "stock_mppi", seed=0)
        assert run.reached_goal
        ab.assert_all_reached([run], "stock")   # must not raise

    def test_truncated_trajectory_fails_the_guard(self):
        """The failure the guard exists for: a run that stopped short still
        reports a clearance, and that clearance is the one a freeze buys."""
        scen = _scen(expected_duration=15.0)
        ctrl = make_controller("stock_mppi", scen, seed=0,
                               robot_radius=ROBOT_RADIUS)
        traj = simulate(scen, ctrl)
        stalled = traj[:len(traj) // 3]          # give up a third of the way
        assert ab.reached_goal(traj, scen)
        assert not ab.reached_goal(stalled, scen)

    def test_assert_all_reached_names_the_offending_seeds(self):
        good = ab.ArmRun(3, np.zeros((2, 6)), 0.5, True, 0.3)
        bad = ab.ArmRun(7, np.zeros((2, 6)), 0.5, False, 0.3)
        with pytest.raises(AssertionError, match=r"\[7\]"):
            ab.assert_all_reached([good, bad], "blind")


class TestSpeedHandicap:
    def test_v_max_binds_on_realized_speed(self):
        """A handicap that does not move realized speed is not a control."""
        scen = _scen(expected_duration=15.0)
        free = ab.run_arm(scen, "stock_mppi", seed=0)
        slow = ab.run_arm(scen, "stock_mppi", seed=0, v_max=0.20)
        assert slow.mean_speed < free.mean_speed, (slow.mean_speed,
                                                   free.mean_speed)
        assert slow.mean_speed <= 0.20 + 1e-9

    def test_mean_speed_reads_the_velocity_column(self):
        traj = np.zeros((4, 6))
        traj[:, ab.COL_V] = [0.4, -0.2, 0.6, 0.0]     # |v| mean = 0.3
        assert ab.mean_speed(traj) == pytest.approx(0.3)


class TestSeedSweepAndPairing:
    def test_sweep_is_seed_ordered_and_matches_per_seed_runs(self):
        scen = _scen(expected_duration=12.0)
        seeds = [2, 0, 1]                      # deliberately unsorted
        sweep = ab.seed_sweep(scen, "stock_mppi", seeds)
        assert [r.seed for r in sweep] == seeds
        solo = ab.run_arm(scen, "stock_mppi", seed=1)
        assert sweep[2].clearance == pytest.approx(solo.clearance, abs=0.0)

    def test_paired_delta_refuses_mismatched_seed_sets(self):
        a = [ab.ArmRun(s, np.zeros((2, 6)), 0.1, True, 0.3) for s in (0, 1)]
        b = [ab.ArmRun(s, np.zeros((2, 6)), 0.1, True, 0.3) for s in (0, 2)]
        with pytest.raises(ValueError, match="different seeds"):
            ab.paired_delta(a, b)

    def test_sign_counts_separates_tied_from_favoured(self):
        deltas = np.array([0.05, -0.05, 0.0, 1e-9, -0.2])
        assert ab.sign_counts(deltas) == (1, 2, 2)


class TestSummarize:
    def test_collision_is_negative_clearance_and_rate_is_over_n(self):
        runs = [ab.ArmRun(0, np.zeros((2, 6)), -0.02, True, 0.3),
                ab.ArmRun(1, np.zeros((2, 6)), 0.10, True, 0.3),
                ab.ArmRun(2, np.zeros((2, 6)), 0.30, True, 0.3),
                ab.ArmRun(3, np.zeros((2, 6)), 0.50, True, 0.3)]
        st = ab.summarize(runs)
        assert (st.n, st.collisions) == (4, 1)
        assert st.collision_rate == pytest.approx(0.25)
        assert st.median_clearance == pytest.approx(0.20)
        assert st.min_clearance == pytest.approx(-0.02)
        assert st.all_reached and runs[0].collided and not runs[1].collided

    def test_all_reached_is_false_if_any_seed_stopped_short(self):
        runs = [ab.ArmRun(0, np.zeros((2, 6)), 0.1, True, 0.3),
                ab.ArmRun(1, np.zeros((2, 6)), 0.1, False, 0.3)]
        assert not ab.summarize(runs).all_reached


class TestClearanceScoringScope:
    def test_default_scores_every_obstacle_subset_scores_one(self):
        """The `obstacles=` override is load-bearing: on a multi-obstacle
        scene, 'clearance to the hazard' and 'clearance to the nearest of
        anything' are different numbers, and a claim must say which it means."""
        near = CircleObstacle(0.35, -1.0, radius=0.3)
        far = CircleObstacle(0.0, -3.0, radius=0.3)
        scen = _straight_scenario(obstacles=[near, far], expected_duration=15.0)
        both = ab.run_arm(scen, "stock_mppi", seed=0)
        far_only = ab.run_arm(scen, "stock_mppi", seed=0, obstacles=[far])
        assert both.clearance <= far_only.clearance
        np.testing.assert_array_equal(both.traj, far_only.traj)
