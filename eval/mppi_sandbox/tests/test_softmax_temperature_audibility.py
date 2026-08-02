# SPDX-License-Identifier: BSD-3-Clause
"""Q-017 / Q-024: the shadow term's inertness is a *temperature* artifact.

The 2026-08-02 11:00 cycle measured `w_epist` as bit-inert on an off-centre
hazard and attributed it to **homotopy indifference** — a centred obstacle
leaves pass-left and pass-right cost-tied, so a knife-edge softmax is tippable
by any large additive term, while an off-centre hazard decides the homotopy
outright and the term cannot bridge the gap. That story is superseded here.
The discriminator is not the geometry's homotopy structure. It is that the
shipped softmax is **degenerate**, and de-generating it makes the same term
audible on the same geometry with no scene change at all.

Measured on `risk_mppi`, K = 256 samples, one circle hazard, `w_risk` and
`k_margin_per_sigma` zeroed so `w_epist` is the only live term:

| lam  | ESS median (offset 0.3) | `w_epist` 200 vs 0 |
|------|-------------------------|--------------------|
| 0.1 (shipped) | **1.01** | bit-identical, 24/24 seeds |
| 0.3  | 1.12  | bit-identical, 24/24 seeds |
| 1.2  | 45.99 | **differs on every seed** |
| 3.0  | 197.2 | differs |

At `lam = 0.1` the effective sample size is **one sample out of 256**. The
update `U += sum_k w_k * noise_k` is then `U += noise[argmin]` — the sandbox
baseline is a greedy argmin picker over 256 draws, not a path-integral
average. An additive cost term is audible to a one-hot softmax only when it
flips the argmin, which is why it registered on exactly the one geometry
where the argmin was contested. Raise `lam` until the ESS enters the
admissible band and the term is heard on the previously inert geometry.

Two things this does **not** rescue, both asserted below:

* **Direction still does not follow.** At `lam = 1.2`, n = 24, paired by
  seed on the `offset = 0.3` scene: 10 farther / 5 closer / 9 tied,
  two-sided sign p = 0.30, median delta-clearance 0.0 m; both arms complete
  every seed and are speed-matched at 0.98x. So Q-017 answer (a) is not
  merely mis-tuned — audible and non-directional is where it lands once the
  sampler can hear it. That is a *stronger* refutation than 11:00's, because
  it is no longer confounded with a sampler that discards the term.
* **A genuinely inert geometry survives.** `offset = 0.6` stays bit-identical
  at `lam = 1.2`. Temperature explains the 0.3 m case, not every case.

Not asserted, deliberately: the high-`lam` end. `lam = 30` drives ESS to ~225
of 256 (near-uniform weights, so `U += mean(noise) ~ 0`) and the term goes
inert again — but **neither arm reaches the goal there**, so by this repo's
own completion doctrine (`ab.assert_all_reached`) those runs are inadmissible
as evidence of anything. The two-sided audibility window is a real-looking
observation with no admissible measurement behind it yet; see Q-034.
"""

import numpy as np
import pytest

from eval.mppi_sandbox import ab
from eval.mppi_sandbox.controllers import make_controller
from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
from eval.mppi_sandbox.obstacles import CircleObstacle
from eval.mppi_sandbox.run import ROBOT_RADIUS, simulate
from eval.mppi_sandbox.tests.test_sandbox import _straight_scenario

SEEDS = tuple(range(3))
W_EPIST_ON = 200.0
LAM_SHIPPED = 0.1
LAM_IN_BAND = 1.2

K = MPPIParams().samples
ESS_BAND = (0.05 * K, 0.5 * K)          # Q-026's proposed admissible band

_ISOLATE_SHADOW = dict(w_risk=0.0, k_margin_per_sigma=0.0)
_CACHE: dict = {}


def _scenario(offset: float):
    return _straight_scenario(obstacles=[CircleObstacle(offset, -1.5)],
                              expected_duration=15.0)


def _arms(offset: float, lam: float):
    """(shadow-on, shadow-off) seed sweeps at one (geometry, temperature).

    Memoized: each entry costs 2 * len(SEEDS) closed-loop sims and several
    assertions below read the same pair.
    """
    key = (offset, lam)
    if key not in _CACHE:
        scen = _scenario(offset)
        _CACHE[key] = tuple(
            ab.seed_sweep(scen, "risk_mppi", SEEDS,
                          params=MPPIParams(lam=lam), w_epist=w,
                          **_ISOLATE_SHADOW)
            for w in (W_EPIST_ON, 0.0))
    return _CACHE[key]


def _seeds_moved(offset: float, lam: float) -> int:
    on, off = _arms(offset, lam)
    return sum(a.traj.shape != b.traj.shape or not np.array_equal(a.traj, b.traj)
               for a, b in zip(on, off))


def _median_ess(offset: float, lam: float) -> float:
    """Median effective sample size of the MPPI softmax over a closed-loop run.

    ESS = 1 / sum(w^2): K when weights are uniform, 1 when one-hot. Computed
    by wrapping `_cost`, so it measures the weights the controller actually
    used rather than a reconstruction.
    """
    key = ("ess", offset, lam)
    if key not in _CACHE:
        scen = _scenario(offset)
        ctrl = make_controller("risk_mppi", scen, seed=0,
                               robot_radius=ROBOT_RADIUS,
                               params=MPPIParams(lam=lam),
                               w_epist=W_EPIST_ON, **_ISOLATE_SHADOW)
        vals: list[float] = []
        inner = ctrl._cost

        def _record(traj, t0):
            cost = inner(traj, t0)
            w = np.exp(-(cost - cost.min()) / lam)
            w /= w.sum()
            vals.append(1.0 / np.square(w).sum())
            return cost

        ctrl._cost = _record
        simulate(scen, ctrl)
        assert vals, "controller never weighted a rollout batch"
        _CACHE[key] = float(np.median(vals))
    return _CACHE[key]


class TestShippedTemperatureCollapsesTheSoftmax:
    """The baseline defect this file exists to pin."""

    def test_shipped_lam_gives_an_effective_sample_size_of_about_one(self):
        """`lam = 0.1` against costs spanning ~1e4 units makes every weight but
        the argmin's underflow. 256 samples are drawn and one is used.

        This is a defect in the *baseline*, not in `risk_mppi` — it applies to
        every controller in the registry, and it is the mechanism behind the
        Q-017 inertness. Kept separate from the Q-032 raw-noise defect: that
        one mis-credits the update, this one collapses the weighting.
        """
        ess = _median_ess(0.3, LAM_SHIPPED)
        assert ess < 2.0, (
            f"median ESS {ess:.2f} of {K} — if this has risen above ~1 the "
            f"softmax is no longer one-hot and the temperature explanation "
            f"for Q-017's inertness needs re-deriving")
        assert ess < ESS_BAND[0], (
            f"median ESS {ess:.2f} now clears the admissible-band floor "
            f"{ESS_BAND[0]:.1f} (Q-026) at the shipped temperature")

    def test_raising_lam_restores_a_usable_effective_sample_size(self):
        """Positive control: the collapse is the temperature's doing and is
        reversible, so the assertion above is not merely measuring a broken
        ESS probe."""
        ess = _median_ess(0.3, LAM_IN_BAND)
        assert ESS_BAND[0] <= ess <= ESS_BAND[1], (
            f"median ESS {ess:.2f} at lam={LAM_IN_BAND} left the admissible "
            f"band {ESS_BAND} — re-pick the in-band temperature before "
            f"reading the audibility assertions below")


class TestInertnessIsATemperatureArtifactNotAGeometryProperty:
    """Supersedes 11:00's homotopy-indifference explanation of Q-017."""

    def test_off_centre_hazard_is_inert_at_the_shipped_temperature(self):
        """Reproduces 11:00's headline at n=3, so the contrast below is
        measured against a live baseline rather than a quoted number."""
        moved = _seeds_moved(0.3, LAM_SHIPPED)
        assert moved == 0, (
            f"{moved}/{len(SEEDS)} seeds moved at lam={LAM_SHIPPED} — the "
            f"off-centre inertness no longer reproduces; this file's premise "
            f"and the 11:00 rescope table both need re-measuring")

    def test_same_geometry_becomes_audible_once_the_softmax_de_concentrates(self):
        """The headline. **No scene change** — same obstacle, same offset,
        same cost weights. Only `lam` moves, and the term that was
        bit-identical on every seed now moves every seed.

        So 'the shadow term cannot bridge a decided homotopy' was the wrong
        model: the term was never being weighed at all.
        """
        moved = _seeds_moved(0.3, LAM_IN_BAND)
        assert moved == len(SEEDS), (
            f"only {moved}/{len(SEEDS)} seeds moved at lam={LAM_IN_BAND} — if "
            f"this drops toward 0 the temperature explanation fails and "
            f"homotopy indifference is back on the table")

    def test_both_arms_still_complete_at_the_raised_temperature(self):
        """Completion guard on the comparison that carries the claim. A
        temperature change is exactly the kind of edit that buys 'a difference'
        by making one arm stop driving — cf. the lam=30 runs, which show a
        difference and reach nothing."""
        on, off = _arms(0.3, LAM_IN_BAND)
        ab.assert_all_reached(on, f"w_epist={W_EPIST_ON} @ lam={LAM_IN_BAND}")
        ab.assert_all_reached(off, f"w_epist=0 @ lam={LAM_IN_BAND}")

    def test_a_farther_offset_stays_inert_even_in_band(self):
        """Bounds the claim. Temperature explains the 0.3 m case; at 0.6 m the
        arms are still bit-identical with the sampler fully able to hear the
        term, so some inertness is genuinely the term's own."""
        on, off = _arms(0.6, LAM_IN_BAND)
        ab.assert_all_reached(on, "offset=0.6 w_epist=200")
        moved = _seeds_moved(0.6, LAM_IN_BAND)
        assert moved == 0, (
            f"{moved}/{len(SEEDS)} seeds moved at offset=0.6, lam="
            f"{LAM_IN_BAND} — the 'genuinely inert geometry' bound no longer "
            f"holds and Q-017 (a) deserves a re-measurement at n=24")


class TestAudibilityDoesNotBuyDirection:
    """Making the term heard does not make it steer — the Q-017 (a) verdict."""

    def test_no_clearance_direction_sweeps_at_the_in_band_temperature(self):
        """At n=24 this scene measured 10 farther / 5 closer / 9 tied,
        p = 0.30. Asserted here at n=3 only as 'neither side sweeps', which is
        all n=3 can carry — the n=24 number lives in the docstring and the
        journal, deliberately not in a CI assertion (Q-030: an assertion whose
        power comes from a seed count CI will not pay for is a liability).
        """
        on, off = _arms(0.3, LAM_IN_BAND)
        farther, closer, _ = ab.sign_counts(ab.paired_delta(on, off), 1e-6)
        assert max(farther, closer) < len(SEEDS), (
            f"{farther} farther / {closer} closer — one direction now sweeps "
            f"n={len(SEEDS)}; re-run the n=24 paired sweep before treating "
            f"Q-017 (a) as refuted")

    def test_arms_are_speed_matched_so_any_delta_is_not_a_speed_effect(self):
        """0.98x at n=24. Raising `lam` changes how decisively the sampler
        commits, which is a plausible route to a speed difference — so this
        control is not inherited from the lam=0.1 comparison and is re-checked
        at the temperature actually used."""
        on, off = (ab.summarize(s) for s in _arms(0.3, LAM_IN_BAND))
        ratio = on.mean_speed / off.mean_speed
        assert 0.9 <= ratio <= 1.1, (
            f"arms diverged in realized speed ({on.mean_speed:.4f} vs "
            f"{off.mean_speed:.4f} m/s, {ratio:.3f}x) — the audibility claim "
            f"is now speed-confounded and needs a v_max handicap")


class TestAdmissibleTemperatureIsSceneDependent:
    """Q-025, answered from the measurement side."""

    @pytest.mark.parametrize("offset,in_band", [(0.3, True), (0.0, False)])
    def test_one_lam_cannot_put_two_geometries_in_band_together(self, offset,
                                                                in_band):
        """`lam = 1.2` lands the off-centre scene at ESS ~46 (in band) and the
        centred scene at ESS ~5 (still one-hot). Moving one obstacle 0.3 m
        changes the cost scale enough to change which temperatures are
        admissible at all.

        Consequence for the ablation protocol: a fixed-`lam` A/B across scenes
        is not a controlled comparison — it silently varies how much of the
        sample budget each scene actually uses. `lam` has to be either
        cost-normalized or reported per scene alongside the ESS (Q-024/Q-025).
        """
        ess = _median_ess(offset, LAM_IN_BAND)
        actually_in_band = ESS_BAND[0] <= ess <= ESS_BAND[1]
        assert actually_in_band is in_band, (
            f"offset={offset} at lam={LAM_IN_BAND}: median ESS {ess:.2f}, "
            f"band {ESS_BAND}, expected in_band={in_band} — the "
            f"scene-dependence of the admissible temperature has changed")
