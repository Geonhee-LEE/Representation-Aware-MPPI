# SPDX-License-Identifier: BSD-3-Clause
"""D-500: a near-obstacle-gated heading price is a directional hint, not a fix.

D-499 localized the knee+shape arm's `heading_err_rms_max` residual on
`cafe_obstacle_crossing_v0` to near-obstacle timesteps (peak error at
0.32-1.05 m clearance, rho < 0 on all 16 seeds). `MPPIParams.w_heading_near`
prices heading error only inside `heading_near_band` (1.05 m, the top of that
window), leaving the open path as unpriced as the `w_heading = 0` baseline.

Measured 2026-09-24 20:00 on the same 16 paired seeds as D-430/D-433:

    w_heading_near   heading fails   clearance fails
    0  (baseline)    10/16           0/16
    8                11/16           0/16
    32                7/16           0/16

At 32 the per-seed heading RMS improves on 12 seeds and worsens on 4 (sign
test p ~ 0.08); McNemar on the pass/fail flip is 6 vs 3 (p ~ 0.51). Clearance
is untouched. So unlike `w_omega` (D-433: 9 improve / 7 worsen) the gated
price moves the *distribution*, not only which seeds straddle 0.30 — but the
non-monotone point at 8 and n=16 mean the pass count is not established.
Pinned here as a measurement, not as a new default: the knob stays inert.

Cost: 32 integrations (~28 s), computed once in a module fixture.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import heading_error_phase as h
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

#: Gated weight measured to move the distribution; 8 was the non-monotone point.
W_NEAR = 32.0


def _rms(runs, scenario):
    return np.array([
        float(np.sqrt(np.mean(h.heading_error(r.traj, scenario.waypoints) ** 2)))
        for r in runs
    ])


def _min_clearance(runs, scenario):
    return np.array([
        float(h.per_timestep_clearance(r.traj, scenario.obstacles, h.ROBOT_RADIUS).min())
        for r in runs
    ])


@pytest.fixture(scope="module")
def arms():
    scenario = load_scenario(h.CROSSING)
    out = {}
    for w in (0.0, W_NEAR):
        p = MPPIParams(collision_margin=h.AVOIDANCE_BAND,
                       obs_barrier_band=h.AVOIDANCE_BAND, w_heading_near=w)
        runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(h.SEEDS), params=p)
        out[w] = (_rms(runs, scenario), _min_clearance(runs, scenario))
    return out


def test_knob_defaults_inert():
    assert MPPIParams().w_heading_near == 0.0


def test_baseline_reproduces_d430(arms):
    rms, clr = arms[0.0]
    assert int((rms > h.HEADING_ERR_RMS_MAX).sum()) == 10
    assert int((clr < h.AVOIDANCE_BAND - 1e-9).sum()) == 0


def test_gated_price_cuts_heading_failures_without_touching_clearance(arms):
    rms0, _ = arms[0.0]
    rms1, clr1 = arms[W_NEAR]
    assert int((rms1 > h.HEADING_ERR_RMS_MAX).sum()) == 7
    assert int((clr1 < h.AVOIDANCE_BAND - 1e-9).sum()) == 0
    delta = rms1 - rms0
    assert int((delta < 0).sum()) == 12 and int((delta > 0).sum()) == 4


def test_the_flip_is_not_yet_established(arms):
    """McNemar exact on the pass/fail flip — 6 fixed vs 3 broken, p > 0.05."""
    from math import comb
    f0 = arms[0.0][0] > h.HEADING_ERR_RMS_MAX
    f1 = arms[W_NEAR][0] > h.HEADING_ERR_RMS_MAX
    fixed, broken = int((f0 & ~f1).sum()), int((~f0 & f1).sum())
    assert (fixed, broken) == (6, 3)
    n, k = fixed + broken, min(fixed, broken)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    assert p > 0.05
