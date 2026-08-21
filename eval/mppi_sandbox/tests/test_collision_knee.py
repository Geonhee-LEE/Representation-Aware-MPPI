# SPDX-License-Identifier: BSD-3-Clause
"""D-410: where `w_collision` fires, and what moving it costs.

D-409 located the `pass=0/5` defect as a **knee-placement mismatch**: the hard
term fired at `clear < 0.0` while `min_distance_to_obstacle` asks for 0.30 m,
leaving the entire graded band priced only by the soft barrier. `w_collision`'s
threshold was a literal `0.0` in two places, so no weight could reach it.

`MPPIParams.collision_margin` makes the threshold a parameter. It ships at
**0.0**, which is byte-identical to every run recorded before it existed —
the same ablation invariant `w_freeze` and `gap_gate_strength` ship under, and
the reason the blast radius of *shipping* the knob is exactly zero.

The tests below pin three separate things, in increasing cost:

1. the default is 0.0 (free);
2. the knee's effect on `_cost` is exactly `w_collision`, no more and no less
   (free — synthetic rollouts, no integration);
3. the knee is where the robot actually ends up (~0.4 s/seed on
   `cafe_obstacle_crossing_v0`).

(3) is the one that earns the parameter. The clearance the run achieves tracks
the knee it was priced against **1:1** — which is why the sole failing check
flips, and also why the cost lands on tracking error instead.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, StockMPPI
from eval.mppi_sandbox.run import run_scenario
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: The threshold `cafe_obstacle_crossing_v0` grades `min_distance_to_obstacle`
#: against. Named here so the test reads against the scene, not a magic number.
GATE = 0.30


# ------------------------------------------------------ the shipped default

def test_shipped_knee_is_zero():
    """The knob ships inert — D-027's ablation invariant is not broken by it."""
    assert MPPIParams().collision_margin == 0.0


def test_scene_still_grades_against_the_threshold_the_knee_targets():
    """If the scene's gate moves, the 0.30 in these tests stops meaning it."""
    acc = load_scenario(CROSSING).acceptance
    assert acc["min_distance_to_obstacle"] == pytest.approx(GATE)


# ------------------------------------------ the knee's price is w_collision

def _straight_rollouts(ctrl: StockMPPI, clearances: np.ndarray) -> np.ndarray:
    """(K,H,6) rollouts held at a fixed surface-to-surface clearance each.

    Each rollout parks at a constant offset from the (single, static) obstacle
    centre, so its clearance is exactly the value asked for and the hard term's
    `.any(axis=1)` reduces to a scalar predicate per rollout.
    """
    ob = ctrl.obstacles[0]
    centre = ob.position(np.zeros(1))[0]
    H = ctrl.p.horizon
    traj = np.zeros((len(clearances), H, 6))
    radius = clearances + ob.radius + ctrl.robot_radius
    traj[..., 0] = centre[0]
    traj[..., 1] = centre[1] + radius[:, None]
    return traj


def _cost_at(margin: float, clearances: np.ndarray) -> np.ndarray:
    scenario = load_scenario(CROSSING)
    ctrl = StockMPPI(scenario, seed=0, robot_radius=0.3,
                     params=MPPIParams(collision_margin=margin))
    return ctrl._cost(_straight_rollouts(ctrl, clearances), 0.0)


def test_moving_the_knee_charges_exactly_w_collision_inside_the_band():
    """The only term that moves is the hard one, and it moves by its weight.

    This is the arithmetic form of "no weight could have reached it": the soft
    barrier, the path term and the terminal term are identical on both sides,
    so the whole difference is `w_collision` on the rollouts the new knee now
    condemns — and exactly zero on the ones it does not.
    """
    # Two inside the band the gate grades, two clear of it.
    clearances = np.array([0.05, 0.20, 0.35, 0.60])
    delta = _cost_at(GATE, clearances) - _cost_at(0.0, clearances)
    w = MPPIParams().w_collision
    assert delta == pytest.approx([w, w, 0.0, 0.0])


def test_knee_at_zero_condemns_only_interpenetration():
    """The shipped knee prices the cliff edge and nothing above it."""
    clearances = np.array([-0.05, 0.0001, 0.29])
    delta = _cost_at(0.0, clearances) - _cost_at(-1.0, clearances)
    w = MPPIParams().w_collision
    assert delta == pytest.approx([w, 0.0, 0.0])


# -------------------------------------------- the knee is where it ends up

@pytest.mark.parametrize("margin", [0.0, GATE])
def test_achieved_clearance_tracks_the_knee(margin):
    """D-410's measured claim: the run parks on whatever knee it was priced at.

    At the shipped knee the robot finishes ~0.01 m from the surface — on the
    cliff edge, because that is the only boundary it was charged against. Move
    the knee to the graded threshold and the same planner, same seed, same
    weights parks just past 0.30 instead. That is the mechanism behind
    `pass=0/5`, stated as a prediction the sim has to satisfy.
    """
    r = run_scenario(CROSSING, controller="stock_mppi", seed=0,
                     params=MPPIParams(collision_margin=margin))
    achieved = r["min_obstacle_clearance"]
    assert achieved == pytest.approx(margin, abs=0.05)
    assert r["acceptance"]["min_distance_to_obstacle"] is (margin >= GATE)


def test_buying_the_clearance_check_is_not_free():
    """The trade D-410 records: clearance is paid for in tracking error.

    Guarding the direction only. The magnitude moved 0.124 -> 0.094 on seed 0
    and 0.122 -> 0.323 on seed 1 when this was measured, so a tight pin here
    would be pinning the seed, not the effect. What is stable across seeds is
    that the detour is real: the run takes materially longer to reach the goal.
    """
    kw = dict(controller="stock_mppi", seed=0)
    near = run_scenario(CROSSING, params=MPPIParams(collision_margin=0.0), **kw)
    far = run_scenario(CROSSING, params=MPPIParams(collision_margin=GATE), **kw)
    assert far["metrics"]["time_to_goal"] > near["metrics"]["time_to_goal"]
