# SPDX-License-Identifier: BSD-3-Clause
"""D-506: on `cafe_head_on_v0` the heading residual is the sidestep itself,
and the speed-gated `w_heading_near` price makes it worse, not better.

D-499 localized the knee+shape heading residual to obstacle proximity on
`cafe_obstacle_crossing_v0`. Measured 2026-09-29 on head_on (knee+shape band,
n=16): the same holds, more strongly. Baseline rho(clearance, |heading err|)
is negative on 16/16 (-0.37 to -0.81), every peak sits at clearance
0.44-1.38 m, and steps within 1.5 m of the pedestrian (~18% of the run) carry
53-73% of the squared error. With those steps zeroed, heading rms is
0.22-0.29 on 16/16, i.e. under the borrowed 0.30 ceiling. head_on's own yaml
declares no heading limit and says "may sidestep".

The D-503 arm (w_heading_near=64, v_gate 0.45) raises heading rms on 15/16
seeds (median 0.42 -> 0.54). Seeds 3 and 5 blow up (0.43 -> 0.91, 0.43 -> 1.03)
with 98% of the error near the pedestrian.

    seed   w0 rms   w0 far-only rms   w64+gate rms   w64 near share
    3      0.428    0.292             0.907          0.98
    5      0.433    0.227             1.027          0.98

Cost: 4 integrations.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import heading_error_phase as h
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario
from eval.path_tracking_metrics import heading_error

HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"
W_HIGH, V_GATE = 64.0, 0.45
SEEDS = (3, 5)


def _stats(traj, scenario):
    he = np.abs(heading_error(traj, scenario.waypoints))
    clr = h.per_timestep_clearance(traj, scenario.obstacles, h.ROBOT_RADIUS)
    near = clr < h.NEAR_OBSTACLE_CLEARANCE
    return {
        "rms": float(np.sqrt(np.mean(he ** 2))),
        "far_rms": float(np.sqrt(np.mean(np.where(near, 0.0, he) ** 2))),
        "near_share": float((he[near] ** 2).sum() / (he ** 2).sum()),
        "rho": h.heading_clearance_correlation(
            traj, scenario.waypoints, scenario.obstacles),
    }


@pytest.fixture(scope="module")
def arms():
    """{w: [stats per seed]} for the baseline and the D-503 gated arm."""
    scenario = load_scenario(HEAD_ON)
    out = {}
    for w, vg in ((0.0, 0.0), (W_HIGH, V_GATE)):
        p = MPPIParams(collision_margin=h.AVOIDANCE_BAND,
                       obs_barrier_band=h.AVOIDANCE_BAND,
                       w_heading_near=w, heading_near_v_gate=vg)
        out[w] = [_stats(ab.run_arm(scenario, "stock_mppi", s, params=p).traj,
                         scenario) for s in SEEDS]
    return out


def test_baseline_residual_is_near_the_pedestrian(arms):
    for s in arms[0.0]:
        assert s["rms"] > h.HEADING_ERR_RMS_MAX
        assert s["rho"] < 0.0
        assert s["far_rms"] < h.HEADING_ERR_RMS_MAX


def test_gated_heading_price_worsens_head_on(arms):
    for base, gated in zip(arms[0.0], arms[W_HIGH]):
        assert gated["rms"] > 1.5 * base["rms"]
        assert gated["near_share"] > 0.9
