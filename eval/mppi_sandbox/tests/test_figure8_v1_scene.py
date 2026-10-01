"""city_figure8_v1: the D-509 rewrite, and why it still measures nothing alone.

D-509 found city_figure8_v0 unmeasurable: one circle driven twice, start ==
goal, so no arm leaves the start. v1 (in `variants/`, so the 8-scene census
pins are not migrated — same placement claim as city_crossing_v0) fixes all
three yaml facts, pinned below:

1. Two lobes: waypoints sit on both sides of the crossing x = -25.
2. The final waypoint lies on a segment traversed once, so completion there
   clears STOP_COMPLETION and the stop rule is reachable.
3. goal != start.

and pins the reading taken on it (D-510): fixing the yaml is necessary but
not sufficient. A figure-8 must come back near where it began, so the goal is
1.74 m from the start against 16.3 m of path. Every registered controller
prices `dist_goal` and, at the shipped `w_freeze = 0`, nothing prices
progress, so stock MPPI shortcuts straight to the goal: it travels < 3 m and
never drives either lobe. Measured 2026-10-01 on all 8 arms x 4 seeds (all 8
arms are bit-identical here — no obstacles): heading rms 2.20-2.53, 0/32 pass.
`w_freeze = 1e4` is the first rung that drives the loop (arrives at 52-59 s,
heading rms 1.04-1.16 on seeds 0-1); still not a pass. Reported, not pinned.
"""
import numpy as np

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.run import ROBOT_RADIUS, STOP_COMPLETION, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.path_tracking_metrics import completion_percent

SCENE = "eval/scenarios/variants/city_figure8_v1.yaml"
CROSS_X = -25.0


def _path_length(xy):
    return float(np.linalg.norm(np.diff(xy, axis=0), axis=1).sum())


def test_waypoints_trace_two_lobes():
    wp = load_scenario(SCENE).waypoints
    assert (wp[:, 0] < CROSS_X - 2.0).any() and (wp[:, 0] > CROSS_X + 2.0).any()
    # The right lobe is driven once (not the v0 one-circle-twice shape).
    assert not np.allclose(wp[: len(wp) // 2, :2], wp[len(wp) // 2: 2 * (len(wp) // 2), :2])


def test_stop_rule_is_reachable_at_the_final_waypoint():
    wp = load_scenario(SCENE).waypoints
    final = np.array([[0.0, *wp[-1, :2], 0.0, 0.0, 0.0]])
    assert completion_percent(final, wp)[-1] >= STOP_COMPLETION


def test_goal_is_not_start_and_is_the_final_waypoint():
    sc = load_scenario(SCENE)
    assert np.linalg.norm(sc.goal[:2] - sc.start[:2]) > 1.0
    np.testing.assert_allclose(sc.goal[:2], sc.waypoints[-1, :2], atol=1e-3)
    np.testing.assert_allclose(sc.start[:2], sc.waypoints[0, :2], atol=1e-3)


def test_stock_mppi_shortcuts_to_the_goal_instead_of_driving_the_loop():
    sc = load_scenario(SCENE)
    assert _path_length(sc.waypoints[:, :2]) > 15.0          # 16.3 m
    ctrl = make_controller("stock_mppi", sc, seed=0, robot_radius=ROBOT_RADIUS)
    tr = simulate(sc, ctrl)
    assert _path_length(tr[:, 1:3]) < 3.0                     # measured 1.97 m
    assert tr[:, 1].max() < CROSS_X                           # never reaches the right lobe
