# SPDX-License-Identifier: BSD-3-Clause
"""STATE #1 — the alternate-perspective cost construction (2404.07781 borrow).

D-021 finding #2 left the epistemic channel with **no working consumption
path**: `ShadowCostCritic` prices σ *at the rollout point*, and on
`cafe_obstacle_crossing_v0` at the shipped `H = 30` the rollout cloud never
touches a σ > 0 cell, so the per-sample spread is exactly 0.00 at all 92 steps
and `w_epist = 200` is byte-identical to `w_epist = 0` on 4/4 seeds. Finding #4
pinned why the obvious repair does not work: the distance scalar ("live iff max
reach ≥ distance to the nearest unseen cell") holds on 28 of those 92 zero-
spread steps, because the rollouts reach far *along* the path while the shadows
sit *lateral to and behind* the actors. **Direction has to enter the statement.**

This cycle changes the *construction* rather than the weight, following
2404.07781's thesis that per-occlusion costs "may appear to be in opposition"
and should be replaced by one aggregate map whose cell value is the information
gained by visiting that cell:

    V(q)   = fraction of currently-shadowed cells visible from q       ∈ [0, 1]
    cost_k = w_voo · Σ_h (1 − V(x_kh))

## 1. The primary gate passes — the term speaks, and the old one still does not

Measured side by side on the same scene, same shipped horizon, same isolation
(`w_risk = 0`, `k = 0`), one run each:

| term                        | live steps | max spread | mean spread |
|-----------------------------|-----------|-----------|-------------|
| `ShadowCostCritic` w=200    | **0 / 92** | **0.00**  | 0.00        |
| `ObservationValueCritic` w=200 | **115 / 115** | 1060 | 539     |

The shadow row is D-021 reproduced as this cycle's control, not quoted. The
value-of-observation row is the **first non-inert epistemic consumption path in
the repo** — every weight tested changes the executed trajectory, where the
shadow cost changes none of them.

## 2. What did *not* replicate — and it is the n = 4 result

At n = 4 seeds a scale-matched arm read **+60 % mean clearance** (0.0455 →
0.0728) with ESS in band, which is exactly the kind of number this project has
been burned by before. At **n = 8**, paired per-seed:

| lam | arm         | Δclearance sign counts | mean Δ  |
|-----|-------------|------------------------|---------|
| 1.6 | `w_voo=3.23`| +4 / −4 / =0           | −0.0084 |
| 1.6 | `w_voo=6.46`| +5 / −3 / =0           | +0.0123 |
| 3.2 | `w_voo=3.23`| +5 / −3 / =0           | +0.0073 |
| 3.2 | `w_voo=6.46`| +5 / −3 / =0           | −0.0053 |

A coin flip in all four cells, in both directions. **The clearance improvement
is withdrawn** — D-019's "the verdict is a (scene, n_seeds) property" recurring
verbatim. What this cycle establishes is that the term is *audible*, not that
it is *good*. Those are different claims and only the first is measured.

## 3. The mechanism that does survive: weight units are baseline-spread units

The naive sweep picks `w_voo = 200` because that is what `w_epist` was set to.
Measured against the baseline cost it is absurd: the median per-step total-cost
spread on this scene is **79.09**, the value term contributes **2.45 per unit
weight**, so `w_voo = 200` is **6.19× the entire baseline cost spread**. The
consequence is not "a strong preference for information" but a **temperature
change in disguise** — median ESS collapses 77.9 → 1.00 (argmin-over-draws,
`lam` no longer doing anything) and the arm *collides*: min clearance −0.436,
2/4 reaching goal. Scale-matched weights (10 % / 20 % of the baseline spread →
`w_voo` ≈ 3.2 / 6.5) keep ESS inside the D-017 band.

So: **a new critic's weight sweep must be conducted in units of the baseline
cost spread.** `w_epist = 200` looked safe for six cycles only because it was
multiplying exactly zero.

## 4. Direction-dependence — the feed's open question, answered for *this*
construction rather than for the paper

The RA-L PDF fetch was unavailable in this session, so whether 2404.07781's own
cell value is bearing-dependent stays **unsettled**. For the construction built
here the answer is definite and is pinned below: the stored value is a scalar
per location, but it is computed by the same robot→cell ray test the producer
uses, so it inherits the occluder geometry. On a one-disc scene there exist two
cells at the **same** distance from the nearest shadow cell whose values are
**0.0 and 1.0** — a maximal counterexample to distance-predicts-value, which is
D-021 finding #4 stated positively.

Cost: ~2.75× the control-step wall clock of the shadow term (2.2 s vs 0.8 s per
run of this scene). No repo default moved — `w_voo` defaults to 0.0.
"""

from __future__ import annotations

import numpy as np

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.critics import (ObservationValueCritic,
                                       observation_value_map)
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.representations import GTBevProducer, RiskChannel
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.scenario import load_scenario

import pytest

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SHIPPED_HORIZON = MPPIParams().horizon      # 30 — read, not hard-coded
#: Isolate the epistemic terms from the DYNAMIC-channel risk cost and the
#: margin critic, exactly as `test_epistemic_reach_gate` does, so the two
#: files' spread numbers are directly comparable.
_ISOLATE = dict(w_risk=0.0, k_margin_per_sigma=0.0)
_W_LOUD = 200.0                             # the weight D-021 ablated `w_epist` at

_CACHE: dict = {}


def _crossing():
    if "crossing" not in _CACHE:
        _CACHE["crossing"] = load_scenario(CROSSING)
    return _CACHE["crossing"]


def _trace(term: str, w: float, horizon: int = SHIPPED_HORIZON,
           seed: int = 0) -> dict:
    """Per-control-step trace of one epistemic term. Memoized.

    `term` selects which critic carries the weight; everything else — plant,
    noise, warm start, isolation — is held fixed, so the two traces differ only
    in the *construction* of the epistemic cost.
    """
    key = (term, w, horizon, seed)
    if key in _CACHE:
        return _CACHE[key]

    kw = dict(_ISOLATE)
    kw["w_epist" if term == "shadow" else "w_voo"] = w
    ctrl = make_controller("risk_mppi", _crossing(), seed=seed,
                           robot_radius=ROBOT_RADIUS,
                           params=MPPIParams(horizon=horizon), **kw)
    spreads: list[float] = []
    n_targets: list[int] = []
    inner = ctrl._extra_cost

    def _record(traj, t0):
        cost = inner(traj, t0)
        spreads.append(float(np.ptp(cost)))
        if ctrl._bev is not None:
            n_targets.append(observation_value_map(
                ctrl.producer, ctrl._bev, ctrl._robot_xy, t0)[1])
        return cost

    ctrl._extra_cost = _record
    traj = simulate(_crossing(), ctrl)
    out = dict(spread=np.array(spreads), n_targets=np.array(n_targets),
               traj=traj)
    _CACHE[key] = out
    return out


@pytest.mark.slow
class TestTheTermSpeaks:
    """The primary gate the feed named: per-sample spread ≠ 0 at shipped H."""

    def test_value_of_observation_spread_is_nonzero_at_every_step(self):
        tr = _trace("voo", _W_LOUD)
        spread = tr["spread"]
        assert len(spread) > 50, "run ended early — trace is not representative"
        assert (spread > 0.0).all(), (
            f"the value-of-observation term went silent on "
            f"{(spread == 0.0).sum()} of {len(spread)} steps — the construction "
            f"change is supposed to make silence require *no shadow at all*, "
            f"not merely unreached shadow")
        assert spread.max() > 100.0, (
            f"spread max {spread.max():.3g} — audible but implausibly small "
            f"against the ~79 median baseline cost spread; re-measure before "
            f"trusting the docstring table")

    def test_the_shadow_cost_is_still_exactly_silent_on_the_same_scene(self):
        """The control. D-021 reproduced here rather than cited, because the
        A/B is only meaningful if both arms are measured in this same file at
        this same horizon with this same isolation."""
        spread = _trace("shadow", _W_LOUD)["spread"]
        assert spread.max() == 0.0, (
            f"the shadow cost is no longer identically zero "
            f"(max {spread.max():.3e}) — D-021's premise moved and the "
            f"construction comparison in this file needs re-deriving")

    def test_targets_are_present_at_every_step(self):
        """Silence would be *honest* with zero targets; on this scene there are
        always shadows, so the audibility above is not a lucky rendering."""
        n = _trace("voo", _W_LOUD)["n_targets"]
        assert n.min() > 0, (
            f"{(n == 0).sum()} steps rendered no in-range shadow cells at all — "
            f"the term would be silent for a *stated* reason there, but the "
            f"crossing scene is supposed to be occluded throughout")


class TestAblationInvariant:
    """`w_voo = 0` must be a byte-identical no-op (D-013 / Q-017 contract)."""

    def test_zero_weight_is_byte_identical(self):
        off = _trace("voo", 0.0)["traj"]
        base = _trace("shadow", 0.0)["traj"]
        assert np.array_equal(off, base), (
            "w_voo=0 diverged from the all-off arm — the ablation invariant "
            "every P5 attribution rests on is broken")

    def test_a_live_weight_actually_moves_the_trajectory(self):
        """The other half of the same contract: audible must also mean
        *effective*, or the term is D-021's failure mode one rung up (the
        `offset=0.3` mode from `test_shadow_cost_seed_robustness`, where the
        spread was 197 and the trajectory bit-identical)."""
        off = _trace("voo", 0.0)["traj"]
        on = _trace("voo", _W_LOUD)["traj"]
        assert not (off.shape == on.shape and np.array_equal(off, on)), (
            "w_voo=200 executed the baseline trajectory exactly — the term "
            "prices samples differently and changes nothing, which is the "
            "seed-robustness failure mode, not a working critic")

    def test_cost_is_add_only(self):
        """cost ≥ 0 for every rollout — never a credit against the baseline."""
        assert (_trace("voo", _W_LOUD)["spread"] >= 0.0).all()
        ctrl = make_controller("risk_mppi", _crossing(), seed=0,
                               robot_radius=ROBOT_RADIUS, w_voo=_W_LOUD,
                               **_ISOLATE)
        ctrl.command(np.array([0.0, 0.0, -1.5708, 0.0, 0.0]), 0.0)
        xy = np.random.default_rng(0).uniform(-4, 4, size=(300, 2))
        c = ctrl.observation.cost(ctrl.producer, ctrl._bev, np.zeros(2), 0.0,
                                  xy, K=3)
        assert (c >= 0.0).all(), f"negative rollout cost {c.min()}"


@pytest.mark.slow
class TestWeightIsInBaselineSpreadUnits:
    """§3 — the finding that survives n = 8."""

    def test_the_naive_weight_exceeds_the_whole_baseline_cost_spread(self):
        ctrl = make_controller("risk_mppi", _crossing(), seed=0,
                               robot_radius=ROBOT_RADIUS, w_voo=0.0,
                               params=MPPIParams(lam=1.6), **_ISOLATE)
        probe = ObservationValueCritic(w_voo=1.0)
        base_ptp: list[float] = []
        unit_ptp: list[float] = []
        inner = ctrl._cost

        def _record(traj, t0):
            cost = inner(traj, t0)
            base_ptp.append(float(np.ptp(cost)))
            xy = traj[..., :2].reshape(-1, 2)
            # every weight is zero on this arm, so `command` skips the render —
            # the probe needs the BEV the arm *would* have seen.
            bev = ctrl._bev or ctrl.producer.render(ctrl._robot_xy, t0)
            unit_ptp.append(float(np.ptp(probe.cost(
                ctrl.producer, bev, ctrl._robot_xy, t0, xy,
                traj.shape[0]))))
            return cost

        ctrl._cost = _record
        simulate(_crossing(), ctrl)

        ratio = _W_LOUD * np.median(unit_ptp) / np.median(base_ptp)
        assert ratio > 1.0, (
            f"w_voo={_W_LOUD} is only {ratio:.2f}x the median baseline cost "
            f"spread — the §3 argument that the naive weight is a disguised "
            f"temperature change no longer holds and should be rewritten")

    def test_the_naive_weight_destroys_the_softmax(self):
        """ESS ≈ 1 means the update is argmin-over-draws: `lam` is inert and no
        clearance number measured at this weight is a controller comparison."""
        runs = ab.seed_sweep(_crossing(), "risk_mppi", (0, 1),
                             params=MPPIParams(lam=1.6), w_voo=_W_LOUD,
                             **_ISOLATE)
        assert ab.summarize(runs).median_ess < 2.0

    def test_a_scale_matched_weight_keeps_ess_in_band(self):
        """10 % of the measured baseline spread (79.09 / 2.45 ≈ 3.2)."""
        runs = ab.seed_sweep(_crossing(), "risk_mppi", (0, 1, 2, 3),
                             params=MPPIParams(lam=1.6), w_voo=3.23,
                             **_ISOLATE)
        assert ab.summarize(runs).ess_in_band is True


class TestDirectionNotDistance:
    """§4 — D-021 finding #4 stated positively, on pure geometry (no sim)."""

    @staticmethod
    def _one_disc():
        prod = GTBevProducer([CircleObstacle(x=2.0, y=0.0, radius=0.5)])
        robot = np.zeros(2)
        bev = prod.render(robot, 0.0)
        value, n_targets = observation_value_map(prod, bev, robot, 0.0)
        return prod, bev, robot, value, n_targets

    def test_equal_distance_to_the_nearest_shadow_buys_unequal_value(self):
        prod, bev, robot, value, n_targets = self._one_disc()
        assert n_targets > 0, "the one-disc scene rendered no shadow at all"

        grid = bev.stack[RiskChannel.EPISTEMIC]
        n = grid.shape[0]
        ax = bev.origin[0] + (np.arange(n) + 0.5) * bev.resolution
        ay = bev.origin[1] + (np.arange(n) + 0.5) * bev.resolution
        cx, cy = np.meshgrid(ax, ay)
        cells = np.stack([cx.ravel(), cy.ravel()], axis=1)
        shadow = ((grid > 0.5)
                  & (np.hypot(cx - robot[0], cy - robot[1]) <= prod.r_sense))
        sxy = np.stack([cx[shadow], cy[shadow]], axis=1)
        d_near = np.linalg.norm(cells[:, None] - sxy[None], axis=2).min(axis=1)

        v = value.ravel()
        in_range = np.linalg.norm(cells - robot, axis=1) <= prod.r_sense
        best = 0.0
        for lo in np.arange(0.0, 4.0, 0.125):
            m = in_range & (d_near >= lo) & (d_near < lo + 0.0625)
            if m.sum() >= 2:
                best = max(best, float(v[m].max() - v[m].min()))
        assert best > 0.9, (
            f"largest value gap between two cells equidistant from the nearest "
            f"shadow is only {best:.3f} — the map has become a distance proxy, "
            f"which is precisely the scalar D-021 #4 refuted")

    def test_no_shadow_means_honest_silence_not_a_number(self):
        prod = GTBevProducer([])
        bev = prod.render(np.zeros(2), 0.0)
        value, n_targets = observation_value_map(prod, bev, np.zeros(2), 0.0)
        # An obstacle-free world still has the beyond-range halo, which the map
        # deliberately does *not* credit: only in-range shadow counts.
        assert n_targets == 0
        assert not value.any()
        c = ObservationValueCritic(w_voo=_W_LOUD).cost(
            prod, bev, np.zeros(2), 0.0, np.zeros((60, 2)), K=3)
        assert not c.any(), "silent map still produced a cost"
