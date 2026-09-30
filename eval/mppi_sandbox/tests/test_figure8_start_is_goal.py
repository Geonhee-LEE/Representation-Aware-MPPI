"""city_figure8_v0's 0/16 is a scene-definition defect, not a controller one.

D-508 left city_figure8 as the one scene no arm passes (heading rms ~2.06 on
every arm). Localized 2026-09-30 20:00 (D-509): the robot never leaves the
start. Three facts about the yaml produce that, and each is pinned here so a
future cycle does not spend a sweep tuning a controller against it.

1. The "figure-8" waypoints trace ONE circle (centre (-25, 0), r 2.5) twice —
   laps 0..8 and 8..16 are the same xy. There is no second lobe.
2. Because the laps overlap, nearest-segment projection aliases lap 2 onto
   lap 1, so `completion_percent` at the final waypoint is 0 and the
   simulator's STOP_COMPLETION rule can never fire (every run times out).
3. start == goal. Every registered controller prices `dist_goal` (speed ramp
   + terminal term) and nothing prices progress, so staying put is optimal:
   all 8 arms stay within 0.80 m of the start over 40 s. The heading residual
   is spin-in-place at the start, not path-tracking error.
"""
import numpy as np

from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.run import ROBOT_RADIUS, STOP_COMPLETION, simulate
from eval.mppi_sandbox.scenario import load_scenario
from eval.path_tracking_metrics import completion_percent

SCENE = "eval/scenarios/city_figure8_v0.yaml"


def test_waypoints_are_one_circle_driven_twice():
    wp = load_scenario(SCENE).waypoints
    assert len(wp) == 17
    np.testing.assert_allclose(wp[0:9, :2], wp[8:17, :2], atol=1e-9)
    r = np.linalg.norm(wp[:, :2] - np.array([-25.0, 0.0]), axis=1)
    np.testing.assert_allclose(r, 2.5, atol=1e-2)


def test_overlap_makes_the_stop_rule_unreachable():
    wp = load_scenario(SCENE).waypoints
    final = np.array([[0.0, *wp[-1, :2], 0.0, 0.0, 0.0]])
    assert completion_percent(final, wp)[-1] < STOP_COMPLETION
    assert completion_percent(final, wp)[-1] == 0.0


def test_start_is_goal_so_stock_mppi_never_leaves():
    sc = load_scenario(SCENE)
    np.testing.assert_allclose(sc.start, sc.goal)
    ctrl = make_controller("stock_mppi", sc, seed=0, robot_radius=ROBOT_RADIUS)
    tr = simulate(sc, ctrl, max_steps=400)
    disp = np.linalg.norm(tr[:, 1:3] - sc.start[:2], axis=1).max()
    assert disp < 1.0            # measured 0.80 m; one lap is 15.7 m
    assert tr[:, 4].mean() < 0.1  # measured 0.046 m/s vs 0.5 target
