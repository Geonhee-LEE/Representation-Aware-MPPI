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


#: Seeds the knee ensemble is read over. Eight is what fits the cycle budget
#: (~16 runs, seconds); it is not a power claim — see D-429's honesty note.
KNEE_SEEDS = tuple(range(8))
#: `time_to_goal` separating the two modes D-429 measured. The gap between the
#: modes is ~9 s wide (8.6 vs 17.4), so any cut inside it labels identically.
MODE_SPLIT_TTG = 12.0


def _knee_pair(seed):
    """Both arms of the knee A/B on one seed. ~0.8 s."""
    kw = dict(controller="stock_mppi", seed=seed)
    near = run_scenario(CROSSING, params=MPPIParams(collision_margin=0.0), **kw)
    far = run_scenario(CROSSING, params=MPPIParams(collision_margin=GATE), **kw)
    return near, far


@pytest.fixture(scope="module")
def knee_ensemble():
    """The 8-seed knee A/B, computed once and shared by the tests below."""
    return {s: _knee_pair(s) for s in KNEE_SEEDS}


def test_buying_the_clearance_check_is_not_free(knee_ensemble):
    """The trade D-410 records: clearance is paid for in tracking error.

    Re-pinned off seed 0 (D-429, closing the defect D-426 raised and D-427
    re-confirmed). The old version asserted this on **seed 0 alone**, which
    D-427 had just measured as the single seed that worsens under the shape
    knob — the test was pinned to the one seed its own neighbouring result
    called unrepresentative.

    The re-pin is not a wider tolerance but a wider **population**: the
    direction is asserted on every seed, and it holds on **8 of 8**. That is
    what makes it an effect rather than a seed. Magnitude is still not pinned
    (it ranges 0.3 s to 10.1 s across seeds) — only the sign.
    """
    for seed, (near, far) in sorted(knee_ensemble.items()):
        assert far["metrics"]["time_to_goal"] > near["metrics"]["time_to_goal"], (
            f"seed {seed}: knee did not cost time"
        )


def test_the_knee_splits_the_seeds_into_two_modes(knee_ensemble):
    """D-429: seed 0 is not an outlier, it is a **member of the smaller mode**.

    Under the moved knee the runs land in one of two well-separated outcomes,
    and which one a seed lands in decides the *sign* of its `cte_rms` change:

    - **detour** (`ttg` ~17.5, 3 of 8): goes around wide, and tracking error
      *improves* (0.124 -> 0.094 on seed 0).
    - **squeeze** (`ttg` ~8.2, 5 of 8): stays near the path and pays in
      tracking error (0.112 -> 0.505 on seed 2).

    Both modes clear the gate, so `min_distance_to_obstacle` cannot tell them
    apart — which is why D-426/D-427 read the `cte_rms` spread as seed noise.
    It is not noise: it is a bimodal outcome, and averaging `cte_rms` over a
    seed ensemble averages across two different behaviours. That is the caveat
    the 16-seed ensemble has to carry.
    """
    detour, squeeze = [], []
    for seed, (near, far) in sorted(knee_ensemble.items()):
        bucket = detour if far["metrics"]["time_to_goal"] > MODE_SPLIT_TTG else squeeze
        bucket.append((seed, near["metrics"]["cte_rms"], far["metrics"]["cte_rms"]))

    assert detour and squeeze, "the split is only meaningful if both modes occur"

    # The modes are separated by a wide gap, not a threshold chosen to fit.
    slowest_squeeze = max(f["metrics"]["time_to_goal"]
                          for s, (n, f) in knee_ensemble.items()
                          if f["metrics"]["time_to_goal"] <= MODE_SPLIT_TTG)
    fastest_detour = min(f["metrics"]["time_to_goal"]
                         for s, (n, f) in knee_ensemble.items()
                         if f["metrics"]["time_to_goal"] > MODE_SPLIT_TTG)
    assert fastest_detour - slowest_squeeze > 5.0

    # The sign of the cte_rms change is decided by the mode, both ways.
    for seed, near_cte, far_cte in detour:
        assert far_cte < near_cte, f"seed {seed} detoured but cte_rms worsened"
    for seed, near_cte, far_cte in squeeze:
        assert far_cte > near_cte, f"seed {seed} squeezed but cte_rms improved"


def test_seed_zero_is_in_the_smaller_mode(knee_ensemble):
    """The concrete statement behind the re-pin, kept separately pinnable.

    D-427 recorded "seed 0 is again the outlier". D-429 measures *why*: it is
    one of the three detour-mode seeds. A future cycle that reaches for seed 0
    as a representative single seed is reaching for the minority mode.
    """
    _, far = knee_ensemble[0]
    assert far["metrics"]["time_to_goal"] > MODE_SPLIT_TTG
