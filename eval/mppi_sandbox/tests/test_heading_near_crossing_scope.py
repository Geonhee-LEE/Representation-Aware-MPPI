# SPDX-License-Identifier: BSD-3-Clause
"""D-507: scoping `w_heading_near` to obstacles that *cross* the path keeps
the crossing fix and removes the head_on regression.

D-506 found that the D-503 arm (w_heading_near=64, v_gate 0.45) makes head_on
heading worse on 15/16 seeds, because there the pedestrian walks along the path
and the heading residual is the sidestep itself. `heading_near_max_cos` drops an
obstacle from the gate wherever |cos(obstacle heading - path tangent)| exceeds
it. Static obstacles still count.

Measured 2026-09-29 20:00 (knee+shape band, w=64, v_gate 0.45, max_cos 0.5):

    scene      n    arm       heading fails   median rms   clearance fails
    crossing   32   w0        19/32           0.313        0/32
    crossing   32   gated     1/32            0.163        0/32
    crossing   32   scoped    1/32            0.163        0/32  (== gated, per seed)
    head_on    16   gated     16/16           0.544        0/16
    head_on    16   scoped    16/16           0.416        0/16  (== w0, per seed)
    cut_in     32   w0/gated/scoped  clearance fails 1/32 each

head_on still fails heading 16/16 with every arm: its own yaml sets no heading
limit (D-506), so the target there is "no regression", not a pass.

Cost: 4 integrations.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox import heading_error_phase as h
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"
W_HIGH, V_GATE, MAX_COS = 64.0, 0.45, 0.5
SEED = 3


def test_inert_default():
    assert MPPIParams().heading_near_max_cos == 1.0


@pytest.fixture(scope="module")
def trajs():
    out = {}
    for key, path, w, max_cos in (("cross_gated", CROSSING, W_HIGH, 1.0),
                                  ("cross_scoped", CROSSING, W_HIGH, MAX_COS),
                                  ("head_w0", HEAD_ON, 0.0, 1.0),
                                  ("head_scoped", HEAD_ON, W_HIGH, MAX_COS)):
        p = MPPIParams(collision_margin=h.AVOIDANCE_BAND,
                       obs_barrier_band=h.AVOIDANCE_BAND,
                       w_heading_near=w, heading_near_v_gate=V_GATE if w else 0.0,
                       heading_near_max_cos=max_cos)
        out[key] = ab.run_arm(load_scenario(path), "stock_mppi", SEED,
                              params=p).traj
    return out


def test_crossing_pedestrians_stay_priced(trajs):
    # Crossers walk +x across a -y path: cos ~ 0, so the scope is a no-op.
    np.testing.assert_array_equal(trajs["cross_scoped"], trajs["cross_gated"])


def test_head_on_pedestrian_is_unpriced(trajs):
    # The head-on walker is anti-parallel to the path: the price never fires,
    # so the run is the w=0 baseline exactly (D-506 had 0.43 -> 0.91 here).
    np.testing.assert_array_equal(trajs["head_scoped"], trajs["head_w0"])
