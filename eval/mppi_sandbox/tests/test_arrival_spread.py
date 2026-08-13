# SPDX-License-Identifier: BSD-3-Clause
"""Arithmetic over fixture arrival readings — no simulation in this file.

The measured walk lives in the journal / D-NNN. What is pinned here is the
*reasoning*: that censoring outranks the interval, that a difference over the
seeds which arrived is refused rather than reported, and that the tie band is
tied to `SIM_DT` instead of typed.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox.arrival_spread import (
    ARRIVAL_CENSORED,
    ARMS,
    BASE_ARM,
    D247_LAM,
    EPS_ARRIVAL_S,
    LAMS,
    NOT_SEPARATED,
    PAIRED_LAM,
    SEEDS,
    SEPARATED_FASTER,
    SEPARATED_SLOWER,
    ArmArrivals,
    ArrivalComparison,
    StallSplit,
    compare,
    separation_survives,
    spans_overlap,
)
from eval.mppi_sandbox.run import SIM_DT


def arm(name: str, arrivals, *, lam: float = PAIRED_LAM) -> ArmArrivals:
    return ArmArrivals(arm=name, lam=lam,
                       seeds=tuple(range(len(arrivals))),
                       arrivals=tuple(arrivals))


# --- constants -------------------------------------------------------------

def test_tie_band_is_half_a_sim_step_and_derived_from_it():
    """Not typed: a `SIM_DT` change must move the band with it."""
    assert EPS_ARRIVAL_S == SIM_DT / 2.0
    # Only exact ties fit: one full step is outside the band.
    assert SIM_DT > EPS_ARRIVAL_S


def test_protocol_constants_are_the_two_named_conditions():
    assert SEEDS == tuple(range(12)), "D-235's protocol is n=12"
    assert LAMS == (D247_LAM, PAIRED_LAM), \
        "both temperatures, reproduction column first"
    assert D247_LAM != PAIRED_LAM, \
        "the two columns exist because widening moves n and lam together"
    assert BASE_ARM == ARMS[0] == "stock_mppi"


# --- ArmArrivals -----------------------------------------------------------

def test_unequal_seed_and_arrival_lengths_are_rejected():
    with pytest.raises(ValueError, match="paired by seed index"):
        ArmArrivals(arm="a", lam=0.8, seeds=(0, 1), arrivals=(1.0,))


def test_empty_reading_is_rejected():
    with pytest.raises(ValueError, match="at least one seed"):
        ArmArrivals(arm="a", lam=0.8, seeds=(), arrivals=())


def test_arrival_counts_and_completeness():
    a = arm("a", [1.0, None, 3.0])
    assert (a.n, a.n_arrived) == (3, 2)
    assert not a.complete
    assert arm("b", [1.0, 2.0]).complete


def test_span_reads_over_survivors_and_refuses_when_none_arrived():
    assert arm("a", [3.0, None, 1.0]).span == (1.0, 3.0)
    with pytest.raises(ValueError, match="no seed arrived"):
        arm("a", [None, None]).span


# --- spans_overlap (D-247's weak reading) ----------------------------------

def test_spans_overlap_both_directions():
    stock = arm("stock_mppi", [7.4, 7.8, 7.4])
    social = arm("social_mppi", [9.0, 8.8, 8.9])
    assert not spans_overlap(stock, social), "D-247's n=3 non-overlap"
    assert not spans_overlap(social, stock), "symmetric"
    assert spans_overlap(stock, arm("x", [7.6, 12.0]))


def test_spans_of_different_survivor_sets_are_not_comparable():
    with pytest.raises(ValueError, match="not comparable"):
        spans_overlap(arm("a", [1.0, None]), arm("b", [2.0, 3.0]))


# --- ArrivalComparison pairing contract ------------------------------------

def test_comparison_rejects_mismatched_seed_ensembles():
    base = ArmArrivals(arm="a", lam=0.8, seeds=(0, 1), arrivals=(1.0, 2.0))
    other = ArmArrivals(arm="b", lam=0.8, seeds=(0, 5), arrivals=(1.0, 2.0))
    with pytest.raises(ValueError, match="paired by seed index"):
        ArrivalComparison(base=base, arm=other)


def test_comparison_rejects_two_temperatures():
    with pytest.raises(ValueError, match="compares nothing"):
        ArrivalComparison(base=arm("a", [1.0], lam=0.1),
                          arm=arm("b", [2.0], lam=0.8))


# --- the censoring guard ---------------------------------------------------

def test_censoring_is_a_disjunction_over_both_arms():
    full = [1.0, 2.0, 3.0]
    assert not ArrivalComparison(base=arm("a", full),
                                 arm=arm("b", full)).censored
    assert ArrivalComparison(base=arm("a", full),
                             arm=arm("b", [1.0, None, 3.0])).censored, \
        "the arm lost a seed"
    assert ArrivalComparison(base=arm("a", [1.0, None, 3.0]),
                             arm=arm("b", full)).censored, \
        "a lost base seed removes a *pair*, so base completeness is required too"


def test_diffs_refuse_rather_than_returning_the_arrived_subset():
    """The subset is a well-formed list of floats that means nothing."""
    c = ArrivalComparison(base=arm("a", [1.0, 2.0]),
                          arm=arm("b", [5.0, None]))
    with pytest.raises(ValueError, match="biased fast"):
        _ = c.diffs
    for prop in ("mean_step", "sign_p"):
        with pytest.raises(ValueError):
            getattr(c, prop)
    with pytest.raises(ValueError):
        c.ci()


def test_censoring_outranks_an_interval_that_would_have_separated():
    """The trap: the frozen seed *leaves* the average instead of lengthening it.

    On the seeds that arrived, this arm reads unambiguously faster than base —
    a clean `SEPARATED_FASTER` had the `None` been dropped. It froze on the
    other eight, which is the opposite conclusion.
    """
    base = arm("stock", [9.0] * 12)
    frozen = arm("social", [1.0, 1.0, 1.0, 1.0] + [None] * 8)
    c = ArrivalComparison(base=base, arm=frozen)
    assert c.verdict == ARRIVAL_CENSORED
    # The dropped-None reading, computed here to show what is being refused.
    survivors = ArrivalComparison(base=arm("stock", [9.0] * 4),
                                  arm=arm("social", [1.0] * 4))
    assert survivors.verdict == SEPARATED_FASTER


# --- separation readings ---------------------------------------------------

def test_separated_slower_when_the_paired_ci_excludes_zero_above():
    c = ArrivalComparison(base=arm("stock", [7.4, 7.8, 7.4, 7.6]),
                          arm=arm("social", [9.0, 8.8, 8.9, 9.1]))
    assert c.verdict == SEPARATED_SLOWER
    assert c.mean_step == pytest.approx(1.4, abs=0.2)
    lo, hi = c.ci()
    assert lo > 0.0 and hi > lo


def test_separated_faster_is_the_mirror():
    c = ArrivalComparison(base=arm("stock", [9.0, 8.8, 8.9, 9.1]),
                          arm=arm("fast", [7.4, 7.8, 7.4, 7.6]))
    assert c.verdict == SEPARATED_FASTER
    assert c.mean_step < 0.0


def test_not_separated_when_the_ci_straddles_zero():
    c = ArrivalComparison(base=arm("stock", [7.0, 8.0, 7.0, 8.0]),
                          arm=arm("other", [8.0, 7.0, 8.0, 7.0]))
    assert c.verdict == NOT_SEPARATED


def test_identical_arms_tie_and_report_no_sign_evidence():
    same = [7.4, 7.8, 9.0, 8.8]
    c = ArrivalComparison(base=arm("a", same), arm=arm("b", same))
    assert c.verdict == NOT_SEPARATED
    assert c.sign_p == 1.0
    assert c.diffs == (0.0, 0.0, 0.0, 0.0)


def test_sign_test_ties_only_on_exact_equality_at_this_quantisation():
    """One full step apart is a sign, not a tie — the band is half a step."""
    c = ArrivalComparison(base=arm("a", [7.0, 7.0, 7.0, 7.0, 7.0, 7.0]),
                          arm=arm("b", [7.1] * 6))
    assert c.sign_p < 0.05


def test_ci_is_reproducible():
    c = ArrivalComparison(base=arm("a", [7.4, 7.8, 7.4, 7.6]),
                          arm=arm("b", [9.0, 8.8, 8.9, 9.1]))
    assert c.ci(seed=0) == c.ci(seed=0)


# --- compare / separation_survives ----------------------------------------

def test_compare_denominates_every_other_arm_against_the_base():
    readings = [arm("stock_mppi", [7.4, 7.8]),
                arm("social_mppi", [9.0, 8.8]),
                arm("risk_mppi", [9.0, 9.1])]
    cs = compare(readings)
    assert [c.arm.arm for c in cs] == ["social_mppi", "risk_mppi"]
    assert all(c.base.arm == "stock_mppi" for c in cs)


def test_compare_refuses_when_the_base_arm_is_absent():
    with pytest.raises(ValueError, match="nothing to denominate against"):
        compare([arm("social_mppi", [9.0])])


def test_separation_survives_is_a_conjunction():
    base = arm("stock_mppi", [7.4, 7.8, 7.4, 7.6])
    separated = arm("social_mppi", [9.0, 8.8, 8.9, 9.1])
    overlapping = arm("risk_mppi", [7.5, 7.7, 7.5, 7.6])
    assert separation_survives([base, separated])
    assert not separation_survives([base, separated, overlapping]), \
        "one unresolved pair and the ranking is not licensed"


def test_one_censored_pair_sinks_the_conjunction():
    base = arm("stock_mppi", [7.4, 7.8, 7.4, 7.6])
    separated = arm("social_mppi", [9.0, 8.8, 8.9, 9.1])
    censored = arm("risk_mppi", [9.0, None, 9.1, 9.0])
    assert not separation_survives([base, separated, censored])


def test_separation_survives_is_false_with_no_comparisons():
    """A single arm has no ranking to survive — vacuous truth is not the answer."""
    assert not separation_survives([arm("stock_mppi", [7.4, 7.8])])


# --- StallSplit ------------------------------------------------------------

def split(before: float, whole: float, *, arrival=10.0) -> StallSplit:
    return StallSplit(arm="social_mppi", seed=0, lam=PAIRED_LAM,
                      arrival=arrival, before=before, whole=whole,
                      duration=93.1)


def test_post_arrival_share_is_the_contamination_reading():
    # The measured case: 81.90 s whole, ~2 s of it before arrival.
    assert split(2.0, 81.9).post_arrival_share == pytest.approx(0.9756, abs=1e-3)
    # A genuinely pre-arrival freeze leaves nothing for the post half.
    assert split(4.0, 4.0).post_arrival_share == 0.0


def test_post_arrival_share_of_a_never_stalled_run_is_zero_not_undefined():
    assert split(0.0, 0.0).post_arrival_share == 0.0


def test_exceeds_grades_the_pre_arrival_stall_not_the_whole_run():
    """The predicate D-244/D-245/D-246 should have been using on this scene."""
    s = split(2.0, 81.9)
    assert s.whole > 2.0, "the whole-run reading breaches the declared limit"
    assert not s.exceeds(2.0), "the pre-arrival reading does not"
    assert split(3.0, 81.9).exceeds(2.0), "a real pre-arrival freeze still fires"


def test_a_run_that_never_arrived_has_no_post_arrival_phase():
    """`before == whole` by construction, so the share cannot read as clean."""
    s = StallSplit(arm="a", seed=0, lam=PAIRED_LAM, arrival=None,
                   before=40.0, whole=40.0, duration=90.0)
    assert s.post_arrival_share == 0.0
    assert s.exceeds(2.0)
