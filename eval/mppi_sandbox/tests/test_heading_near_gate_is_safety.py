# SPDX-License-Identifier: BSD-3-Clause
"""D-505: `w_heading_near` must never ship without `heading_near_v_gate`.

On `cafe_cut_in_v0` the pedestrian parks inside the goal ball, so the
reference path runs through it. An ungated heading price pushes fast rollouts
to align with that path, i.e. straight into the pedestrian. Measured
2026-09-27 (knee+shape band, w_heading_near=64, n=32): ungated collides on
12/32 seeds (min clearance -0.23 to -0.58 m); gated at 0.45 m/s fails the
0.30 m band on 1/32, the same count as the w=0 baseline (the parked-phase
creep mode, not the price).

Pinned on the first three colliding seeds of 0-7 (measured 2026-09-27 20:00):

    seed   ungated clr   gated(0.45) clr
    0      -0.56 m       0.30 m
    3      -0.50 m       0.30 m
    5      -0.46 m       0.30 m

Cost: 6 integrations.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import heading_error_phase as h
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

CUT_IN = "eval/scenarios/cafe_cut_in_v0.yaml"
#: D-501's weight and the speed gate D-503 pins under it.
W_HIGH, V_GATE = 64.0, 0.45
#: Seeds on which the ungated arm collides (D-505).
SEEDS = (0, 3, 5)


@pytest.fixture(scope="module")
def clearance():
    """{v_gate: [min clearance per seed]} at W_HIGH on cut_in."""
    scenario = load_scenario(CUT_IN)
    out = {}
    for vg in (0.0, V_GATE):
        p = MPPIParams(collision_margin=h.AVOIDANCE_BAND,
                       obs_barrier_band=h.AVOIDANCE_BAND,
                       w_heading_near=W_HIGH, heading_near_v_gate=vg)
        out[vg] = [ab.run_arm(scenario, "stock_mppi", s, params=p).clearance
                   for s in SEEDS]
    return out


def test_ungated_heading_price_collides_on_cut_in(clearance):
    assert all(c < 0.0 for c in clearance[0.0])


def test_speed_gate_keeps_the_avoidance_band(clearance):
    assert all(c >= h.AVOIDANCE_BAND - 1e-3 for c in clearance[V_GATE])
