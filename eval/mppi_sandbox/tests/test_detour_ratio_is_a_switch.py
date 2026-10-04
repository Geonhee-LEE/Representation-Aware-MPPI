"""D-513: `progress_detour_ratio` is a switch on every shipped scene but one.

Sweep of `w_progress=10` + knee+shape band 0.30, seeds 0-15, each yaml's
acceptance, measured 2026-10-04 10:00:

    scene            r0               r1.2            r1.5            r2 / r3
    city_figure8_v1  16/16 cte .020   16/16 cte .048  16/16 cte .144  0/16 (shortcut)
    city_curved_v0   16/16 cte .030   16/16 cte .145  16/16 cte .145  16/16 cte .145
    crossing         16/16 T 17.8     2/16  T 9.2     2/16  T 9.2     2/16  T 9.2
    head_on          0/16  T 42.1     0/16  T 9.6     0/16  T 9.6     0/16  T 9.6

The reason is geometry, not tuning. The gate opens when the remaining path is
<= ratio x the straight-line goal distance. At t=0 that ratio is the path's
own length / chord, and on every shipped scene except figure8_v1 it is
<= 1.13. So any ratio >= 1.13 turns the attractor on from the first step,
and the r1.2..r3 columns are identical. On figure8_v1 (9.38) the ratio only
decides how early the gate opens on the closing lobe, and cte rises with it.

So curved's cte gain (0.145 -> 0.030) is also the attractor being off, like
crossing's 16/16 (D-512). No ratio keeps those gains and also fixes head_on.

Cost: no rollouts.
"""
import numpy as np
import pytest

from eval.mppi_sandbox.critics import ArclengthProgressCritic
from eval.mppi_sandbox.scenario import load_scenario

SHIPPED_DETOUR = {
    "cafe_head_on_v0": 1.0,
    "cafe_obstacle_crossing_v0": 1.0,
    "cafe_straight_v0": 1.0,
    "city_curved_v0": 1.129,
    "variants/city_figure8_v1": 9.381,
}


def _path(name):
    return load_scenario(f"eval/scenarios/{name}.yaml").waypoints[:, :2]


def _detour(path):
    length = np.linalg.norm(np.diff(path, axis=0), axis=1).sum()
    return length / np.linalg.norm(path[-1] - path[0])


@pytest.mark.parametrize("name,ratio", sorted(SHIPPED_DETOUR.items()))
def test_path_detour_ratio(name, ratio):
    assert _detour(_path(name)) == pytest.approx(ratio, abs=1e-3)


@pytest.mark.parametrize("name", [n for n, r in SHIPPED_DETOUR.items() if r < 1.2])
def test_ratio_1_2_opens_the_gate_at_t0(name):
    path = _path(name)
    off = ArclengthProgressCritic(path, 10.0)
    on = ArclengthProgressCritic(path, 10.0, detour_ratio=1.2)
    off.update(path[0])
    on.update(path[0])
    # gate closed at t0 only where the path is longer than goal_gate (3 m)
    assert on.goal_gate() == 1.0
    assert off.goal_gate() == (1.0 if on.length <= off.goal_gate_m else 0.0)


def test_figure8_v1_gate_stays_closed_at_t0_up_to_ratio_9():
    path = _path("variants/city_figure8_v1")
    for r in (1.2, 1.5, 2.0, 3.0, 9.0):
        c = ArclengthProgressCritic(path, 10.0, detour_ratio=r)
        c.update(path[0])
        assert c.goal_gate() == 0.0
