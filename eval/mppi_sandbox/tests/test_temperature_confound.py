# SPDX-License-Identifier: BSD-3-Clause
"""Q-107's decomposition: controller delta vs temperature delta.

The arithmetic is pinned exhaustively and costs no sims. The *plumbing* is
pinned once against the real sandbox on the cheapest obstacle scene, because a
decomposition that never touches a run is a spreadsheet.
"""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import temperature_confound as tc
from eval.mppi_sandbox.ab import ab_temperature
from eval.mppi_sandbox.baseline_matrix import pick_lam

#: The scene path (`measure` loads it) and the calibration table's key for the
#: same scene (`ab_temperature` is keyed by basename, deliberately — it is a
#: precondition checked before any path is opened).
CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
CROSSING_KEY = "cafe_obstacle_crossing_v0.yaml"


def _pts(**vals) -> list[tc.ArmPoint]:
    """`_pts(a_08=..., b_32=...)` → points, all in band unless overridden."""
    out = []
    for key, v in vals.items():
        arm, lam = key.split("_")
        out.append(tc.ArmPoint(controller=arm, lam=float(lam) / 10.0,
                               value=float(v)))
    return out


# --------------------------------------------------------------------------
# The identity. Everything else in this file rests on it holding exactly.
# --------------------------------------------------------------------------

def test_reported_equals_matched_plus_temperature_exactly():
    d = tc.decompose(_pts(a_08=1.0, a_32=1.5, b_08=2.0, b_32=3.0),
                     "a", "b", 0.8, 3.2)
    assert d.reported == pytest.approx(2.0)
    assert len(d.matched) == 2
    for m in d.matched:
        assert m.delta + m.temperature == pytest.approx(d.reported, abs=1e-15)


def test_identity_holds_for_random_values():
    # The decomposition is arithmetic, so it must hold for values that were
    # not chosen to make it hold.
    vals = [(0.3, -2.7, 11.0, 0.0), (-5.0, -5.0, -5.0, 4.9), (1e6, 1.0, 2.0, 3.0)]
    for aa, ab, ba, bb in vals:
        d = tc.decompose(_pts(a_08=aa, a_32=ab, b_08=ba, b_32=bb),
                         "a", "b", 0.8, 3.2)
        for m in d.matched:
            assert m.delta + m.temperature == pytest.approx(d.reported, rel=1e-12)


def test_one_matched_rung_per_distinct_lam():
    # A published pair that already shares a temperature has exactly one
    # matched comparison — itself — not the same one listed twice.
    d = tc.decompose(_pts(a_08=1.0, b_08=2.0), "a", "b", 0.8, 0.8)
    assert len(d.matched) == 1
    assert d.matched[0].delta == pytest.approx(d.reported)
    assert d.matched[0].temperature == pytest.approx(0.0)
    assert d.verdict == tc.ROBUST
    assert d.lam_gap == pytest.approx(1.0)


# --------------------------------------------------------------------------
# The verdict ladder, one test per rung, both directions where it matters.
# --------------------------------------------------------------------------

def test_sign_flip_when_a_matched_delta_inverts():
    # b beats a as published (+1.0); at the shared rung 0.8, a beats b.
    d = tc.decompose(_pts(a_08=1.0, a_32=1.5, b_08=0.5, b_32=2.0),
                     "a", "b", 0.8, 3.2)
    assert d.reported == pytest.approx(1.0)
    assert [m.delta for m in d.matched] == pytest.approx([0.5, -0.5])
    assert d.verdict == tc.SIGN_FLIP
    assert not d.reportable_as_controller_delta


def test_sign_flip_is_symmetric_in_direction():
    # The mirror image: published delta negative, matched positive.
    d = tc.decompose(_pts(a_08=-1.0, a_32=-1.5, b_08=-0.5, b_32=-2.0),
                     "a", "b", 0.8, 3.2)
    assert d.reported == pytest.approx(-1.0)
    assert [m.delta for m in d.matched] == pytest.approx([-0.5, 0.5])
    assert d.verdict == tc.SIGN_FLIP


def test_masked_when_published_delta_is_zero_and_matched_is_not():
    # The `unsafe_rate` case: the headline reports no difference at all while
    # a temperature-matched comparison finds one. A zero delta is not evidence
    # of no delta.
    d = tc.decompose(_pts(a_08=1.0, a_32=1.0, b_08=0.5, b_32=1.0),
                     "a", "b", 0.8, 3.2)
    assert d.reported == pytest.approx(0.0)
    assert d.verdict == tc.MASKED
    assert math.isinf(d.max_confound_share)


def test_zero_reported_and_zero_matched_is_robust_not_masked():
    # Negative control for MASKED: nothing anywhere is not a hidden finding.
    d = tc.decompose(_pts(a_08=1.0, a_32=1.0, b_08=1.0, b_32=1.0),
                     "a", "b", 0.8, 3.2)
    assert d.verdict == tc.ROBUST
    assert d.max_confound_share == pytest.approx(0.0)


def test_temperature_dominated_at_and_above_the_share_threshold():
    # reported = +1.0, matched@3.2 = +0.4 ⇒ temperature = 0.6 ⇒ share 0.6.
    d = tc.decompose(_pts(a_08=1.0, a_32=1.6, b_08=1.4, b_32=2.0),
                     "a", "b", 0.8, 3.2)
    assert d.verdict == tc.TEMPERATURE_DOMINATED
    assert d.max_confound_share == pytest.approx(0.6)


def test_robust_when_every_matched_delta_agrees_and_temperature_is_small():
    d = tc.decompose(_pts(a_08=1.0, a_32=1.1, b_08=2.0, b_32=2.0),
                     "a", "b", 0.8, 3.2)
    assert d.verdict == tc.ROBUST
    assert d.reportable_as_controller_delta
    assert d.max_confound_share < tc.DOMINANCE_SHARE


def test_dominance_threshold_is_inclusive():
    # Exactly at the threshold counts as dominated — the boundary is a claim,
    # so it is pinned rather than left to whichever comparison got typed.
    matched = [tc.MatchedDelta(lam=3.2, delta=0.5, temperature=0.5,
                               out_of_band=False)]
    assert tc.classify(1.0, matched) == tc.TEMPERATURE_DOMINATED
    matched = [tc.MatchedDelta(lam=3.2, delta=0.51, temperature=0.49,
                               out_of_band=False)]
    assert tc.classify(1.0, matched) == tc.ROBUST


def test_no_matched_rung_is_unmeasurable_not_robust():
    # Only the published diagonal available ⇒ nothing to compare against.
    # This must not read as "no confound found".
    d = tc.decompose(_pts(a_08=1.0, b_32=2.0), "a", "b", 0.8, 3.2)
    assert d.matched == ()
    assert d.verdict == tc.UNMEASURABLE
    assert not d.reportable_as_controller_delta


def test_tolerance_does_not_let_float_noise_counterfeit_a_flip():
    d = tc.decompose(_pts(a_08=1.0, a_32=1.0 + 1e-15, b_08=2.0, b_32=2.0),
                     "a", "b", 0.8, 3.2)
    assert d.verdict == tc.ROBUST


def test_a_run_that_did_not_reach_is_dropped_not_differenced():
    pts = [tc.ArmPoint("a", 0.8, 1.0), tc.ArmPoint("b", 3.2, 2.0),
           tc.ArmPoint("a", 3.2, 99.0, all_reached=False),
           tc.ArmPoint("b", 0.8, 99.0, all_reached=False)]
    d = tc.decompose(pts, "a", "b", 0.8, 3.2)
    assert d.matched == ()
    assert d.verdict == tc.UNMEASURABLE


def test_missing_published_pair_raises_rather_than_reporting_zero():
    with pytest.raises(ValueError, match="no reported delta"):
        tc.decompose(_pts(a_32=1.0, b_08=2.0), "a", "b", 0.8, 3.2)


# --------------------------------------------------------------------------
# The out-of-band flag: the reason option (b) of Q-107 is not available.
# --------------------------------------------------------------------------

def test_out_of_band_is_flagged_per_matched_rung():
    pts = [tc.ArmPoint("a", 0.8, 1.0, ess_in_band=True),
           tc.ArmPoint("b", 3.2, 2.0, ess_in_band=True),
           tc.ArmPoint("a", 3.2, 1.2, ess_in_band=False),   # out of its window
           tc.ArmPoint("b", 0.8, 1.9, ess_in_band=False)]   # out of its window
    d = tc.decompose(pts, "a", "b", 0.8, 3.2)
    assert [m.out_of_band for m in d.matched] == [True, True]


def test_unknown_band_is_not_recorded_as_in_band():
    # `ess_in_band=None` means the sweep could not say. Treating that as
    # "in band" would let an unmeasured arm launder a matched comparison.
    pts = [tc.ArmPoint("a", 0.8, 1.0, ess_in_band=True),
           tc.ArmPoint("b", 3.2, 2.0, ess_in_band=True),
           tc.ArmPoint("a", 3.2, 1.2, ess_in_band=None),
           tc.ArmPoint("b", 0.8, 1.9, ess_in_band=None)]
    d = tc.decompose(pts, "a", "b", 0.8, 3.2)
    assert [m.out_of_band for m in d.matched] == [False, False]


def test_crossing_admits_no_in_band_matched_comparison():
    """The structural claim behind Q-107's answer, read from the table.

    On a `per_arm` scene the windows are disjoint by definition, so no single
    rung is admissible for both arms — every temperature-matched comparison
    must run one arm out of band. This is table-only: zero sims.
    """
    t = ab_temperature(CROSSING_KEY, ["stock_mppi", "risk_mppi"])
    assert t.verdict == "per_arm"
    assert t.shared == ()
    for lam in set(t.per_arm["stock_mppi"]) | set(t.per_arm["risk_mppi"]):
        in_band = [lam in t.per_arm[arm] for arm in t.arms]
        assert not all(in_band), (
            f"lam={lam} admissible for both arms contradicts verdict=per_arm")


def test_the_tree_holds_two_disagreeing_rung_choices_on_this_scene():
    """`pick_lam` and `lam_for` are both shipped and they differ here.

    Not a bug in either — they optimise different things (own-window middle vs
    minimum log-gap to the other arm). Pinned because the measured confound
    share tracks the gap, so which reader the matrix consults is a 2x
    difference in the impurity it carries.
    """
    t = ab_temperature(CROSSING_KEY, ["stock_mppi", "risk_mppi"])
    matrix_rungs = {arm: pick_lam(t.per_arm[arm]) for arm in t.arms}
    ab_rungs = {arm: t.lam_for(arm) for arm in t.arms}
    assert matrix_rungs == {"stock_mppi": 0.8, "risk_mppi": 3.2}
    assert ab_rungs == {"stock_mppi": 0.8, "risk_mppi": 1.6}
    matrix_gap = max(matrix_rungs.values()) / min(matrix_rungs.values())
    assert matrix_gap == pytest.approx(4.0)
    assert t.lam_gap == pytest.approx(2.0)


# --------------------------------------------------------------------------
# Plumbing: one real sweep, smallest that proves `measure` reaches the sim.
# --------------------------------------------------------------------------

def test_measure_wires_to_the_sandbox_and_returns_the_identity():
    out = tc.measure(CROSSING, ["stock_mppi", "risk_mppi"], [0.8, 3.2],
                     seeds=range(2), metrics=("mean_clearance",))
    assert out["margin"] == pytest.approx(0.30)
    assert len(out["grid"]) == 4
    assert all(c["all_reached"] for c in out["grid"])
    (dec,) = out["decompositions"]
    assert dec["lam_gap"] == pytest.approx(4.0)
    assert dec["verdict"] in {tc.ROBUST, tc.SIGN_FLIP, tc.MASKED,
                              tc.TEMPERATURE_DOMINATED}
    for m in dec["matched"]:
        assert m["delta"] + m["temperature"] == pytest.approx(dec["reported"])
        # Disjoint windows ⇒ every matched rung buys its match with an
        # out-of-band arm. If this ever goes False the scene was recalibrated.
        assert m["out_of_band"]
