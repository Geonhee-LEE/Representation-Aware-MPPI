# SPDX-License-Identifier: BSD-3-Clause
"""D-427: barrier **shape** as a knob, after D-426 closed barrier **position**.

D-426 priced `collision_margin` across 2 scenes × 2 knees × 5 seeds and found
it trades the two halves of the north star **1:1**: moving the hard knee to the
0.30 m gate flips `min_distance_to_obstacle` green on 10/10 seeds and puts
`cte_max` / `cte_rms_max` / `heading_err_rms_max` in its place on 4/5. Net pass
moved 0/5 → 1/5. Translation cannot buy both halves.

The mechanism is not the hard term but the **soft** one. `exp(-clear / 0.3)` is
positive at every clearance — `e^-1 = 0.37` at the gate itself, and it never
reaches zero — so the cost goes on rewarding retreat long after the check is
satisfied. Clearance is therefore bought with distance from the path.

`MPPIParams.obs_barrier_band` gives the barrier **compact support** instead: a
quadratic hinge, steep inside `[0, band]` and exactly zero above it. It ships
at **0.0**, the legacy exponential, which is byte-identical to every run
recorded before it existed — the same ablation invariant `w_freeze`,
`gap_gate_strength` and `collision_margin` ship under.

The tests below pin, in increasing cost:

1. the default is inert, and inert means *the legacy expression*, not merely
   "some barrier" (free);
2. the shape properties that make it a shape change — compact support,
   steepness inside the band, agreement with the legacy form at `clear = 0`
   (free);
3. that the knob reaches `_cost` through **both** branches of the obstacle
   term, the gated one included (free — synthetic rollouts, no integration).

(3) exists because the gated branch is a separate code path that has silently
diverged before: it is the one D-243 and the gap-gate work kept re-deriving.
A knob wired into only one branch would pass every test above it.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams, StockMPPI
from eval.mppi_sandbox.scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: The clearance `cafe_obstacle_crossing_v0` grades against. The band is only
#: interesting because it can be set to exactly this — see D-426.
GATE = 0.30


def _ctrl(**kw) -> StockMPPI:
    return StockMPPI(load_scenario(CROSSING), seed=0, params=MPPIParams(**kw))


# ------------------------------------------------------ the shipped default

def test_shipped_band_is_zero():
    """The knob ships inert — D-027's ablation invariant survives it."""
    assert MPPIParams().obs_barrier_band == 0.0


def test_inert_means_the_legacy_exponential_exactly():
    """`band = 0` must reproduce the expression, not just "a barrier".

    Pinned against the literal `exp(-clear / obs_soft_scale)` rather than
    against a recorded array, so the test still fails if the default branch is
    re-derived into something that merely *resembles* it.
    """
    ctrl = _ctrl()
    clear = np.linspace(-0.4, 2.0, 97)
    assert ctrl._soft_barrier(clear) == pytest.approx(
        np.exp(-clear / ctrl.p.obs_soft_scale))


# ------------------------------------------------------- the shape it buys

def test_band_has_compact_support():
    """Exactly zero above the band — this is the whole point.

    The legacy form is positive here, and that positivity is what D-426
    measured as the price of clearance.
    """
    ctrl = _ctrl(obs_barrier_band=GATE)
    outside = np.array([GATE, GATE + 1e-9, 0.5, 1.0, 5.0])
    assert np.all(ctrl._soft_barrier(outside) == 0.0)
    # …and the legacy barrier is *not* zero there, so the two genuinely differ.
    assert np.all(_ctrl()._soft_barrier(outside) > 0.0)


def test_band_is_positive_and_decreasing_inside():
    """Steep inside `[0, band]`: strictly positive, strictly decreasing."""
    ctrl = _ctrl(obs_barrier_band=GATE)
    inside = np.linspace(0.0, GATE, 25, endpoint=False)
    vals = ctrl._soft_barrier(inside)
    assert np.all(vals > 0.0)
    assert np.all(np.diff(vals) < 0.0)


def test_penetration_still_costs_more_than_contact():
    """`clear < 0` is inside the obstacle and must not be cheaper than 0."""
    ctrl = _ctrl(obs_barrier_band=GATE)
    assert ctrl._soft_barrier(np.array([-0.2]))[0] > ctrl._soft_barrier(
        np.array([0.0]))[0]


def test_both_forms_agree_at_contact():
    """`w_obs_soft` keeps its calibrated meaning across the switch.

    Both forms return 1.0 at `clear = 0`, so flipping the band does not
    silently rescale the weight every prior sweep was tuned against.
    """
    at_contact = np.array([0.0])
    assert _ctrl()._soft_barrier(at_contact)[0] == pytest.approx(1.0)
    assert _ctrl(obs_barrier_band=GATE)._soft_barrier(
        at_contact)[0] == pytest.approx(1.0)


# --------------------------------------- the knob reaches _cost, both paths

def _traj_at(clear: float, ctrl: StockMPPI) -> np.ndarray:
    """(1,H,6) rollout parked at a fixed surface-to-surface clearance.

    Placed on the far side of the obstacle along +x so the geometry is exact:
    centre distance = radii sum + margin + `clear`.
    """
    ob = ctrl.obstacles[0]
    pos = ob.position(np.zeros(1))[0]
    r = ob.radius + ctrl.robot_radius + clear
    H = ctrl.p.horizon
    traj = np.zeros((1, H, 6))
    traj[..., 0] = pos[0] + r
    traj[..., 1] = pos[1]
    return traj


@pytest.mark.parametrize("gap_gate_strength", [0.0, 1.0])
def test_band_changes_cost_through_both_obstacle_branches(gap_gate_strength):
    """The gated branch is a second code path — the knob must reach it too."""
    kw = dict(seed=0, gap_gate_strength=gap_gate_strength)
    scen = load_scenario(CROSSING)
    legacy = StockMPPI(scen, params=MPPIParams(), **kw)
    shaped = StockMPPI(scen, params=MPPIParams(obs_barrier_band=GATE), **kw)

    # Far outside the band: the shaped barrier prices this at zero, the legacy
    # one does not, so the costs must differ.
    far = _traj_at(1.0, legacy)
    assert legacy._cost(far, 0.0)[0] != pytest.approx(
        shaped._cost(far, 0.0)[0])


def _min_clearance(ctrl: StockMPPI, traj: np.ndarray) -> float:
    """Smallest surface-to-surface clearance over the horizon, all obstacles.

    `_traj_at` parks against obstacle 0 at `t = 0`, but this scene's obstacle
    *moves* — so the clearance a rollout actually sees over `H` steps is not
    the offset it was placed at. Deriving it here rather than assuming it is
    what keeps the next test's precondition honest.
    """
    times = ctrl.p.dt * np.arange(1, ctrl.p.horizon + 1)
    return min(
        float((np.linalg.norm(traj[..., :2] - ob.position(times)[None], axis=2)
               - ob.radius - ctrl.robot_radius).min())
        for ob in ctrl.obstacles)


def _traj_just_outside(ctrl: StockMPPI) -> np.ndarray:
    """(1,H,6) rollout parked in `(GATE, 1.2]` clearance of every obstacle.

    Two constraints pull against each other, so the offset is searched rather
    than guessed. It must clear *all* obstacles for the whole horizon — the
    scene has more than one and they move, so +1.0 m from obstacle 0 at t=0
    is not outside the band and +6.0 m is 0.07 m from a different obstacle.
    But it must also stay *near*: at 100 m `exp(-clear / 0.3)` underflows to
    zero, so the legacy barrier would vanish too and the far-field test below
    would pass without discriminating between the two shapes.
    """
    for off in np.arange(0.35, 3.0, 0.05):
        traj = _traj_at(float(off), ctrl)
        if GATE < _min_clearance(ctrl, traj) <= 1.2:
            return traj
    raise AssertionError("no offset clears every obstacle inside (GATE, 1.2]")


def test_far_field_soft_cost_is_exactly_zero_under_the_band():
    """The far-field term vanishes — isolated from path/goal/effort costs.

    Compares two shaped controllers differing only in `w_obs_soft`: if the
    barrier really has compact support, the weight cannot matter out here.
    Path / speed / effort / terminal costs are identical between the two, so
    any difference would have to come from the barrier.
    """
    scen = load_scenario(CROSSING)
    a = StockMPPI(scen, seed=0,
                  params=MPPIParams(obs_barrier_band=GATE, w_obs_soft=10.0))
    b = StockMPPI(scen, seed=0,
                  params=MPPIParams(obs_barrier_band=GATE, w_obs_soft=1.0e6))
    far = _traj_just_outside(a)
    assert _min_clearance(a, far) > GATE          # precondition, not a hope
    assert a._cost(far, 0.0)[0] == pytest.approx(b._cost(far, 0.0)[0])


def test_legacy_barrier_has_no_such_far_field():
    """The contrast that makes the previous test a *shape* result.

    Same geometry, same weights, band off: `w_obs_soft` still moves the cost,
    because `exp(-clear / scale)` never reaches zero. This is the term D-426
    measured as the price of clearance.
    """
    scen = load_scenario(CROSSING)
    a = StockMPPI(scen, seed=0, params=MPPIParams(w_obs_soft=10.0))
    b = StockMPPI(scen, seed=0, params=MPPIParams(w_obs_soft=1.0e6))
    far = _traj_just_outside(a)
    assert _min_clearance(a, far) > GATE
    assert a._cost(far, 0.0)[0] != pytest.approx(b._cost(far, 0.0)[0])
