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

D-503 (2026-09-26 10:00) adds `heading_near_v_gate`: the gated price applies
only while |v| exceeds the gate. At w_heading_near=64 without it, seed 27
outruns crossing obstacle #1 instead of yielding by spinning in place
(cte_max 0.44 -> 3.93 m, D-502). Measured n=32 (seeds 0-31):

    w    v_gate   heading fails   clearance fails   cte_max   mean T
    0    -        19/32           0/32              1.47 m    18.9 s
    64   0        3/32            0/32              3.93 m    23.2 s
    64   0.30     1/32            0/32              0.99 m    23.7 s
    64   0.35     3/32            0/32              1.14 m    -
    64   0.45     1/32            0/32              0.83 m    24.2 s
    64   0.55     1/32            0/32              0.27 m    24.5 s
    64   0.70     9/32            0/32              0.43 m    24.5 s
    64   1.00     19/32           0/32              1.47 m    18.9 s (= w 0)

This module pins 0.45 (the middle of the 0.30-0.55 plateau) on the paired
16 seeds plus seed 27. The knob stays inert: the cost is ~5 s more time to goal.

Cost: 16+16+17+1 integrations, computed once in a module fixture.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import heading_error_phase as h
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, _polyline_distance
from eval.mppi_sandbox.scenario import load_scenario

#: Gated weight measured to move the distribution; 8 was the non-monotone point.
W_NEAR = 32.0
#: D-501's weight, and the speed gate D-503 pins under it.
W_HIGH, V_GATE = 64.0, 0.45
#: D-502's tail seed: outruns the crosser at W_HIGH without the speed gate.
TAIL_SEED = 27


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


def _cte_max(runs, scenario):
    path = np.asarray(scenario.waypoints)[:, :2]
    return np.array([float(_polyline_distance(r.traj[:, 1:3], path).max()) for r in runs])


@pytest.fixture(scope="module")
def arms():
    """{(w, v_gate): (heading_rms, min_clearance, cte_max)}. Paired arms run
    h.SEEDS + TAIL_SEED (the tail seed last); the ungated W_HIGH arm runs the
    tail seed alone, since it is only the D-502 contrast."""
    scenario = load_scenario(h.CROSSING)
    paired = list(h.SEEDS) + [TAIL_SEED]
    out = {}
    for w, vg, seeds in ((0.0, 0.0, paired), (W_NEAR, 0.0, paired),
                         (W_HIGH, V_GATE, paired), (W_HIGH, 0.0, [TAIL_SEED])):
        p = MPPIParams(collision_margin=h.AVOIDANCE_BAND,
                       obs_barrier_band=h.AVOIDANCE_BAND, w_heading_near=w,
                       heading_near_v_gate=vg)
        runs = ab.seed_sweep(scenario, "stock_mppi", seeds=seeds, params=p)
        out[(w, vg)] = (_rms(runs, scenario), _min_clearance(runs, scenario),
                        _cte_max(runs, scenario))
    return out


def _paired(arms, key):
    rms, clr, cte = arms[key]
    return rms[:len(h.SEEDS)], clr[:len(h.SEEDS)]


def test_knob_defaults_inert():
    assert MPPIParams().w_heading_near == 0.0
    assert MPPIParams().heading_near_v_gate == 0.0


def test_baseline_reproduces_d430(arms):
    rms, clr = _paired(arms, (0.0, 0.0))
    assert int((rms > h.HEADING_ERR_RMS_MAX).sum()) == 10
    assert int((clr < h.AVOIDANCE_BAND - 1e-9).sum()) == 0


def test_gated_price_cuts_heading_failures_without_touching_clearance(arms):
    rms0, _ = _paired(arms, (0.0, 0.0))
    rms1, clr1 = _paired(arms, (W_NEAR, 0.0))
    assert int((rms1 > h.HEADING_ERR_RMS_MAX).sum()) == 7
    assert int((clr1 < h.AVOIDANCE_BAND - 1e-9).sum()) == 0
    delta = rms1 - rms0
    assert int((delta < 0).sum()) == 12 and int((delta > 0).sum()) == 4


def test_the_flip_is_not_yet_established(arms):
    """McNemar exact on the pass/fail flip — 6 fixed vs 3 broken, p > 0.05."""
    from math import comb
    f0 = _paired(arms, (0.0, 0.0))[0] > h.HEADING_ERR_RMS_MAX
    f1 = _paired(arms, (W_NEAR, 0.0))[0] > h.HEADING_ERR_RMS_MAX
    fixed, broken = int((f0 & ~f1).sum()), int((~f0 & f1).sum())
    assert (fixed, broken) == (6, 3)
    n, k = fixed + broken, min(fixed, broken)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    assert p > 0.05


def test_speed_gated_high_weight_establishes_the_flip(arms):
    """D-503: at W_HIGH with the speed gate, 10 fixed vs 1 broken on the paired
    16 seeds (McNemar exact p ~ 0.012), heading fails 10 -> 1, clearance clean."""
    from math import comb
    rms0, _ = _paired(arms, (0.0, 0.0))
    rms1, clr1 = _paired(arms, (W_HIGH, V_GATE))
    f0, f1 = rms0 > h.HEADING_ERR_RMS_MAX, rms1 > h.HEADING_ERR_RMS_MAX
    assert int(f1.sum()) == 1
    assert int((clr1 < h.AVOIDANCE_BAND - 1e-9).sum()) == 0
    fixed, broken = int((f0 & ~f1).sum()), int((~f0 & f1).sum())
    assert (fixed, broken) == (10, 1)
    n = fixed + broken
    p = 2 * sum(comb(n, i) for i in range(broken + 1)) / 2 ** n
    assert p < 0.05


def test_speed_gate_restores_the_tail_seed_yield(arms):
    """D-502's seed 27: 3.93 m cte_max ungated, back under 0.5 m gated (the
    w=0 baseline's own is 0.44 m)."""
    ungated = arms[(W_HIGH, 0.0)][2][-1]
    gated = arms[(W_HIGH, V_GATE)][2][-1]
    base = arms[(0.0, 0.0)][2][-1]
    assert ungated > 3.5
    assert gated < 0.5 and base < 0.5
