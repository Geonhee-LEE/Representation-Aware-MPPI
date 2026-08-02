# SPDX-License-Identifier: BSD-3-Clause
"""STATE #1 — calibrate a `lam` window for an arm that actually carries `w_voo`.

D-021 established that every window in `lam_windows.yaml` was measured with the
epistemic channel **off**, so no clearance number from a `w_voo` arm was a
controller comparison. D-027 shipped the term; D-028 said which denominator its
weight must be priced against. This file runs the missing measurement and the
answer has three parts, only one of which was anticipated.

## 1. At a scale-matched weight the window does not move

`cafe_obstacle_crossing_v0` / `risk_mppi`, the factor-2 ladder (0.05 → 6.4, a
128× span), 8 seeds per rung, `ab.LamProbe.admissible` (every seed in the ESS
band **and** reached):

| arm | `w_voo` | admissible window |
|---|---|---|
| baseline (control, re-measured) | 0 | **[1.6, 3.2]** |
| scale-matched, fixed | 5.43 | **[1.6, 3.2]** |
| scale-matched, ratio held per rung | 3.41–7.17 | **[1.6, 3.2]** |
| naive (D-027's inherited weight) | 200 | **[]** — empty at every rung |

The baseline row reproduces the recorded `lam_windows.yaml` cell exactly, which
is what licenses reading the other three: the control was re-measured this
cycle rather than quoted (D-028's rule, after D-027 nearly shipped a table
mixing two temperatures).

So STATE #1's premise — that a `w_voo` arm needs its own window before any
comparison is legal — is **answered in the negative for the weights worth
shipping**. The recorded windows transfer, and the A/B is unblocked without a
per-arm recalibration.

## 2. The naive weight is not a temperature *shift*, it is a temperature *kill*

D-027 called `w_voo = 200` "a disguised temperature change", which implies a
window that has moved somewhere else. It has not. The arm is out of band at
**every rung of a 128× ladder** — median ESS 1.00 at six of eight rungs and
1.80 at the top — so it is not calibratable in Q-035's sense at all. Until now
the repo had seen an empty window only on a *defective scene*
(`cafe_cut_in_v0`, which never completes). This is an empty window induced by a
**weight**, on a scene that is healthy on the same ladder in the next column.
Raising `lam` does not buy it back.

## 3. Where the boundary is

Sweeping the weight at the two admissible rungs, in units of the ratio
`weight_units.TermSpread.ratio` (`lam = 1.6` reference):

| `w_voo` | ratio | `lam = 1.6` | `lam = 3.2` |
|---|---|---|---|
| 5.43 | 0.13 | 8/8 | 8/8 |
| 10.7 | 0.25 | 8/8 | 8/8 |
| 21.5 | 0.50 | 1/8 | 8/8 |
| 43.0 | 1.00 | 0/8 | 1/8 |
| 86.0 | 2.00 | 0/8 | 0/8 |
| 200 | 4.66 | 0/8 | 0/8 |

The full window survives to **ratio ≈ 0.25**, costs half its rungs at 0.5, and
is gone by 1.0. Ratio 1 is where the term spans as much of the per-sample cost
range as everything else combined — the line `TermSpread.ratio`'s docstring
already named as the danger condition — so the measurement confirms that guess
and locates the *practical* ceiling a factor of four below it.

## 4. The prescription is a fixed point, and it happens not to matter here

`scale_match`'s module docstring records the mechanism: `per_unit` is
near-invariant in `lam` (1.12× over 128×) while `rest` falls 2.26×, so the
scale-matched weight itself swings **2.11×** along the ladder. That makes
"scale-match, then calibrate" circular in principle. In practice, on this
scene, holding the ratio fixed per rung produced the **same window** as holding
the weight fixed — an honest negative, recorded so the next reader does not pay
for the per-rung protocol expecting it to buy something.
"""

from __future__ import annotations

import pytest

from ..scale_match import (DAMAGE_TOLERANCE, ExchangeRate, check_undamaged,
                           exchange_rate, format_ladder, scale_matched_ladder,
                           verify_ratio, weight_for_ratio)
from ..scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"

#: The two rungs of the recorded window. Every narrow re-measurement below runs
#: at one of these, so a failure is a statement about the shipped window rather
#: than about a temperature nobody uses.
LAM_LO, LAM_HI = 1.6, 3.2

#: The `lam` extremes of `calibrate_lam.DEFAULT_LADDER` — used for the
#: invariance claims, where the whole point is the 128× span.
LAM_COLD, LAM_HOT = 0.05, 6.4

#: D-027's inherited weight. Kept as a named constant because three separate
#: assertions are about *this* number rather than about large weights generally.
W_NAIVE = 200.0

_CACHE: dict = {}


def _crossing():
    if "sc" not in _CACHE:
        _CACHE["sc"] = load_scenario(CROSSING)
    return _CACHE["sc"]


def _rate(lam: float, **kw) -> ExchangeRate:
    """Cached — each call is two closed-loop runs (~12 s)."""
    key = (lam, tuple(sorted(kw.items())))
    if key not in _CACHE:
        _CACHE[key] = exchange_rate(_crossing(), "w_voo", lam=lam, **kw)
    return _CACHE[key]


class TestTheRateIsPricedAgainstTheArmItIsAddedTo:
    """D-028's rule, enforced rather than documented."""

    def test_the_unit_probe_does_not_steer_the_arm(self):
        """The precondition for calling `rest` a *baseline* at all."""
        rate = _rate(LAM_LO)
        assert rate.is_undamaged
        assert rate.damage == pytest.approx(1.0, abs=0.15)

    def test_the_naive_weight_derails_and_the_rate_is_refused(self):
        """D-028's inversion, as a guard instead of a warning.

        At `w_voo = 200` the run stops completing, so `rest` is measuring the
        wreckage the weight itself caused. Reporting the ratio anyway is what
        made the self-referential number understate by 4.2×.
        """
        rate = _rate(LAM_LO, probe_weight=W_NAIVE)
        assert not rate.is_undamaged
        assert rate.damage > DAMAGE_TOLERANCE
        with pytest.raises(ValueError, match="already damaged"):
            check_undamaged(rate)

    def test_the_damaged_rate_may_be_studied_on_request(self):
        """The guard is a default, not a prohibition — D-028's own table was
        built by deliberately measuring both denominators. Asserted against the
        cached damaged rate rather than a fresh `require_undamaged=False` call,
        which would buy a second derailed run to learn the same thing."""
        assert _rate(LAM_LO, probe_weight=W_NAIVE).weight_for_ratio(0.1) > 0.0

    def test_a_non_additive_knob_has_no_scale_matched_weight(self):
        """`k_margin_per_sigma` is in metres (D-028) — a category error, and it
        must fail before spending a run to find out."""
        with pytest.raises(ValueError, match="not an additive cost"):
            exchange_rate(_crossing(), "k_margin_per_sigma", lam=LAM_LO)

    def test_an_unknown_term_raises(self):
        with pytest.raises(KeyError):
            exchange_rate(_crossing(), "w_nonexistent", lam=LAM_LO)


class TestTheNumeratorIsTheTermAndTheDenominatorIsTheTemperature:
    """The fixed point, pinned at the ladder's two extremes."""

    def test_the_exchange_rate_is_nearly_lam_invariant(self):
        """`per_unit` is a constant of the critic, not of the temperature —
        measured 2.34–2.62 over the full ladder."""
        cold, hot = _rate(LAM_COLD).per_unit, _rate(LAM_HOT).per_unit
        assert max(cold, hot) / min(cold, hot) < 1.20

    def test_the_baseline_landscape_shrinks_as_the_softmax_warms(self):
        """`rest` falls 2.26× over the ladder. This is the half that moves."""
        cold, hot = _rate(LAM_COLD).rest, _rate(LAM_HOT).rest
        assert cold / hot > 1.8

    def test_the_scale_matched_weight_therefore_depends_on_lam(self):
        """Which is what makes "scale-match, then calibrate" circular: the
        weight you would pick differs 2.1× depending on the temperature you
        have not calibrated yet."""
        cold = _rate(LAM_COLD).weight_for_ratio(0.1)
        hot = _rate(LAM_HOT).weight_for_ratio(0.1)
        assert cold / hot > 1.6

    def test_a_term_with_no_spread_has_no_scale_matched_weight(self):
        """The D-021 condition, stated as a refusal. `ShadowCostCritic` is
        identically zero on this scene, so no weight gives it a ratio — which
        is why six cycles of `w_epist` tuning could not have worked."""
        dead = ExchangeRate(term="w_epist", lam=LAM_LO, probe_weight=1.0,
                            per_unit=0.0, rest=100.0, n_steps=100,
                            baseline_n_steps=100)
        with pytest.raises(ValueError, match="identically-zero"):
            dead.weight_for_ratio(0.1)


class TestThePrescriptionLandsWhereItSaysItWill:
    """`weight_for_ratio` extrapolates from a unit probe along an algebra that
    is exact on a fixed batch and only approximate in closed loop (D-028). The
    question this closes is how approximate."""

    def test_the_prescribed_weight_achieves_the_requested_ratio(self):
        """Within 1.25× at the ratios that matter. Measured over
        target = 0.1 / 0.25 / 0.5 at both admissible rungs: 1.005–1.221×, with
        the worst case at the *smallest* target. One target is committed —
        each is four closed-loop runs and the six agreed within 8% of the
        trend."""
        target = 0.25
        w = weight_for_ratio(_crossing(), "w_voo", ratio=target, lam=LAM_HI)
        got = verify_ratio(_crossing(), "w_voo", w, lam=LAM_HI)
        assert got == pytest.approx(target, rel=0.25)

    def test_the_extrapolation_degrades_only_where_the_weight_is_unusable(self):
        """D-028 measured the closed-loop rate moving 2.1× between w = 1 and
        w = 200. That is real, but 200 is four ratio-units past the point where
        the window is already empty — so the extrapolation is trustworthy over
        exactly the range a shippable weight lives in."""
        rate = _rate(LAM_LO)
        assert rate.weight_for_ratio(1.0) < W_NAIVE / 3


class TestTheLadderProtocol:

    def test_holding_the_ratio_fixed_gives_a_different_weight_per_rung(self):
        """The per-rung protocol's whole content. If these came out equal the
        fixed point would be a fiction."""
        ladder = scale_matched_ladder(_crossing(), "w_voo", ratio=0.1,
                                      lams=(LAM_COLD, LAM_HOT))
        assert len(set(ladder.values())) == 2
        assert ladder[LAM_COLD] / ladder[LAM_HOT] > 1.6

    def test_the_ladder_renders(self):
        out = format_ladder({LAM_LO: 4.296, LAM_HI: 3.405}, rates=[_rate(LAM_LO)])
        assert "| 1.6 |" in out and "**4.296**" in out
        assert "| 3.2 |" in out and "—" in out       # missing rate degrades


class TestTheWindowUnderAScaleMatchedWeight:
    """Narrow re-measurement of the wide table in this file's docstring.

    The full 4-arm × 8-rung × 8-seed sweep is ~13 min and lives in the cycle
    report; what is committed is the one cell whose failure would falsify the
    headline — a scale-matched arm holding the recorded window's lower rung.
    """

    def test_a_scale_matched_arm_still_weights_in_band_at_the_recorded_rung(self):
        from .. import ab
        w = weight_for_ratio(_crossing(), "w_voo", ratio=0.1, lam=LAM_LO)
        probe = ab.lam_ladder(_crossing(), "risk_mppi", [LAM_LO],
                              seeds=range(4), w_voo=w)[0]
        assert probe.all_reached
        assert probe.n_in_band == probe.n

    def test_the_naive_weight_is_out_of_band_at_the_same_rung(self):
        """The contrast that makes the previous test mean something: same
        scene, same rung — only the weight's scale differs.

        Two seeds, not four: every one of these runs derails to the 1000-step
        cap (~35 s each), and the wide sweep read **0 of 8** in band at all
        eight rungs, so this is spot-checking a unanimous result rather than
        estimating a rate.
        """
        from .. import ab
        probe = ab.lam_ladder(_crossing(), "risk_mppi", [LAM_LO],
                              seeds=range(2), w_voo=W_NAIVE)[0]
        assert probe.n_in_band == 0
