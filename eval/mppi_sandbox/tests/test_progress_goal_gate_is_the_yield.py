"""D-512: on obstacle scenes, `w_progress`'s effect comes from its goal gate.

Cross-scene check of `w_progress=10` (knee+shape band 0.30, seeds 0-15,
each scene's yaml acceptance), measured 2026-10-03 20:00:

    scene        band (w=0)          band + w10           + detour_ratio 1.5
    crossing     6/16  T 9.7 s       16/16  T 17.8 s      2/16  T 9.2 s
    head_on      0/16  T 9.9 s       0/16   T 42.1 s      0/16  T 9.6 s
    convoy / freezing / contested / straight / curved: 16/16 in all arms
    city_figure8_v1                  (D-511: 4/4)         16/16  T 23.1 s

The D-511 gate turns the goal attractor off until <= 3 m of path remains. On
both 4-5 m cafe scenes that is the whole encounter. Without the pull, crossing
yields behind the crosser (+8 s, the heading fails go away), and head_on backs
up behind its start and parks behind the stopped pedestrian (seed 0 reaches
y=+1.4 and loses 25 s). `detour_ratio` reopens the gate wherever the remaining
path is <= ratio x straight-line goal distance. That restores both cafe scenes
to baseline, so the crossing gain does not come from the progress reward.

Cost: 3 integrations.
"""
import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.critics import ArclengthProgressCritic
from eval.mppi_sandbox.scenario import load_scenario

FIG8 = "eval/scenarios/variants/city_figure8_v1.yaml"
HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"
BAND = 0.30


def test_detour_ratio_is_inert_at_default():
    assert ArclengthProgressCritic(np.zeros((2, 2)), 1.0).detour_ratio == 0.0


def test_detour_ratio_opens_the_gate_on_a_straight_path():
    path = np.array([[0.0, 0.0], [0.0, -4.0]])
    c = ArclengthProgressCritic(path, w_progress=1.0, detour_ratio=1.5)
    c.update(np.array([0.0, -0.4]))
    assert c.goal_gate() == 1.0
    assert ArclengthProgressCritic(path, w_progress=1.0).goal_gate() == 0.0


def test_detour_ratio_keeps_the_figure8_gate_closed_near_the_start():
    path = load_scenario(FIG8).waypoints[:, :2]
    c = ArclengthProgressCritic(path, w_progress=1.0, detour_ratio=1.5)
    c.update(path[0])
    assert c.goal_gate() == 0.0           # 16.3 m of path vs 1.74 m straight


@pytest.fixture(scope="module")
def head_on_ttg():
    sc = load_scenario(HEAD_ON)
    p = MPPIParams(collision_margin=BAND, obs_barrier_band=BAND)
    out = {}
    for key, kw in (("w0", {}),
                    ("w10", {"w_progress": 10.0}),
                    ("w10_r15", {"w_progress": 10.0,
                                 "progress_detour_ratio": 1.5})):
        r = ab.run_arm(sc, "stock_mppi", 0, params=p, **kw)
        out[key] = (r.traj, sc.goal)
    return out


def _ttg(traj, goal, tol=0.2):
    d = np.hypot(traj[:, 1] - goal[0], traj[:, 2] - goal[1])
    hit = np.flatnonzero(d <= tol)
    return float(traj[hit[0], 0]) if hit.size else float("inf")


def test_gate_makes_head_on_retreat_and_ratio_removes_it(head_on_ttg):
    t0 = _ttg(*head_on_ttg["w0"])
    t10 = _ttg(*head_on_ttg["w10"])
    t15 = _ttg(*head_on_ttg["w10_r15"])
    assert t10 > t0 + 15.0                                  # 25 s lost
    assert head_on_ttg["w10"][0][:, 2].max() > 1.0          # behind its start
    assert abs(t15 - t0) < 2.0
