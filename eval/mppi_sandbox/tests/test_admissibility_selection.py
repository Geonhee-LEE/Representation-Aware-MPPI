# SPDX-License-Identifier: BSD-3-Clause
"""Q-124's screen: does `ess_band` admissibility select the residual share?

The tests that matter here are the ones pinning that a *perfect* coupling on a
tiny population returns no finding. That is the whole reason the module exists
rather than a one-line concordance call.
"""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox import admissibility_selection as asel
from eval.mppi_sandbox.admissibility_selection import (
    ADMISSIBLE_SEPARATED, ADMISSIBLE_SPANS_REFUSED, ALPHA, LICENCE_SPLIT,
    NO_COMPARABLE_PAIRS, SCREEN_UNDERPOWERED, SELECTION_INDEPENDENT,
    SELECTION_SUSPECTED, Point, Screen, ladder_rungs, licence_split,
    walked_nulls)


def _pt(share: float, admissible: bool, w=None) -> Point:
    return Point(f"p{share}", admissible, share, 32, w)


# ---------------------------------------------------------------- statistic


def test_coupling_is_directional_admissible_low_is_one():
    """Admissible ⇒ lower share is the accusation, so it scores 1.0."""
    s = Screen("t", (_pt(0.1, True), _pt(0.9, False)))
    assert s.coupling == 1.0


def test_coupling_reversed_is_zero_not_one():
    """The opposite ordering is *not* coupling. D-171's statistic was
    unsigned; this one must not be, or a filter that disfavoured the
    representation would read as the same defect."""
    s = Screen("t", (_pt(0.9, True), _pt(0.1, False)))
    assert s.coupling == 0.0


def test_ties_on_either_axis_are_dropped_not_counted():
    same_label = Screen("t", (_pt(0.1, True), _pt(0.9, True)))
    assert same_label.coupling is None
    assert same_label.verdict == NO_COMPARABLE_PAIRS

    same_share = Screen("t", (_pt(0.5, True), _pt(0.5, False)))
    assert same_share.coupling is None


def test_half_is_independence():
    s = Screen("t", (_pt(0.1, True), _pt(0.5, False),
                     _pt(0.9, True), _pt(0.3, False)))
    assert s.coupling == 0.5


# ------------------------------------------------------------------- power


def test_perfect_coupling_on_a_tiny_population_returns_no_finding():
    """The guard the module is built around.

    One admissible against two refused couples perfectly and still cannot
    clear ALPHA, because only three labellings exist. If this ever returns
    SELECTION_SUSPECTED the screen has started reporting luck as evidence.
    """
    s = Screen("t", (_pt(0.1, True), _pt(0.5, False), _pt(0.9, False)))
    assert s.coupling == 1.0
    assert s.verdict == SCREEN_UNDERPOWERED
    assert s.p_value == pytest.approx(1 / 3)


def test_min_achievable_p_ignores_the_observed_shares():
    """Power is a property of the label split alone — the reason it can be
    consulted before the data and cannot be gamed by them."""
    a = Screen("t", (_pt(0.1, True), _pt(0.5, False), _pt(0.9, False)))
    b = Screen("t", (_pt(0.9, True), _pt(0.5, False), _pt(0.1, False)))
    assert a.min_achievable_p == b.min_achievable_p
    assert a.coupling != b.coupling


def test_min_achievable_p_is_one_over_the_labelling_count():
    for n, k in ((3, 1), (6, 4), (7, 3)):
        pts = tuple(_pt(0.1 * i, i < k) for i in range(n))
        assert Screen("t", pts).min_achievable_p == pytest.approx(
            1 / math.comb(n, k))


def test_a_powered_population_can_return_a_finding():
    """Complements the guard: the screen is not merely always-underpowered.
    Seven points, 3 admissible ⇒ 35 labellings ⇒ best-case p = 1/35."""
    pts = tuple(_pt(0.1 * i, i < 3) for i in range(7))
    s = Screen("t", pts)
    assert s.powered
    assert s.coupling == 1.0
    assert s.verdict == SELECTION_SUSPECTED


def test_a_powered_population_with_no_coupling_reads_independent():
    pts = (_pt(0.1, True), _pt(0.2, False), _pt(0.3, True), _pt(0.4, False),
           _pt(0.5, True), _pt(0.6, False), _pt(0.7, False))
    s = Screen("t", pts)
    assert s.powered
    assert s.verdict == SELECTION_INDEPENDENT


def test_points_needed_is_zero_when_powered_and_positive_otherwise():
    powered = Screen("t", tuple(_pt(0.1 * i, i < 3) for i in range(7)))
    assert powered.points_needed == 0

    thin = Screen("t", (_pt(0.1, True), _pt(0.5, False), _pt(0.9, False)))
    assert thin.points_needed > 0


def test_points_needed_actually_suffices():
    """The number is a promise; check it can be kept. Adding that many points
    must admit at least one labelling that clears ALPHA."""
    for s in (walked_nulls(), ladder_rungs()):
        j = s.points_needed
        assert j > 0
        n, k = s.n + j, s.n_admissible
        assert any(math.comb(n, k + extra) >= 1 / ALPHA
                   for extra in range(j + 1))
        # ...and one fewer would not have.
        n_short = s.n + j - 1
        assert not any(math.comb(n_short, k + extra) >= 1 / ALPHA
                       for extra in range(j))


# -------------------------------------------------------------------- span


def test_span_reading_separated_and_spanning():
    sep = Screen("t", (_pt(0.1, True), _pt(0.2, True), _pt(0.9, False)))
    assert sep.span_reading == ADMISSIBLE_SEPARATED

    spans = Screen("t", (_pt(0.1, True), _pt(0.9, True), _pt(0.5, False)))
    assert spans.span_reading == ADMISSIBLE_SPANS_REFUSED


def test_span_reading_survives_low_power():
    """The span is an observation about the set, not a reference-distribution
    claim, so it is readable on exactly the populations the p-value is not."""
    s = Screen("t", (_pt(0.1, True), _pt(0.9, True), _pt(0.5, False)))
    assert not s.powered
    assert s.span_reading == ADMISSIBLE_SPANS_REFUSED


# ------------------------------------------------------- measured readings


def test_walked_nulls_is_the_three_recorded_nulls():
    s = walked_nulls()
    assert s.n == 3
    assert s.n_admissible == 1
    assert all(p.n_seeds == 32 for p in s.points)


def test_walked_null_shares_match_the_modules_that_own_them():
    """The screen recomputes `residual_share`; pin it against the two classes
    whose published numbers it must reproduce, or the table is a third
    independent calculation of the headline."""
    from eval.mppi_sandbox.geometric_null import attribution
    from eval.mppi_sandbox.structural_null import convoy_w75_frozen

    by_label = {p.label: p.residual_share for p in walked_nulls().points}
    assert by_label["geom w_geom=2.5"] == pytest.approx(
        attribution().residual_share)
    assert by_label["frozen prediction"] == pytest.approx(
        convoy_w75_frozen().residual_share)


def test_walked_population_couples_perfectly_and_is_still_refused():
    """The measured headline: the worrying pattern is real *and* worthless."""
    s = walked_nulls()
    assert s.coupling == 1.0
    assert s.span_reading == ADMISSIBLE_SEPARATED
    assert s.verdict == SCREEN_UNDERPOWERED
    assert s.points_needed == 3


def test_ladder_is_underpowered_by_exactly_one_rung():
    s = ladder_rungs()
    assert s.n == 6 and s.n_admissible == 4
    assert s.min_achievable_p == pytest.approx(1 / 15)
    assert not s.powered
    assert s.points_needed == 1


def test_ladder_admissible_set_spans_the_refused_ones():
    """The one non-underpowered piece of evidence, and it points away from
    selection: the filter admits both the lowest and the highest share."""
    s = ladder_rungs()
    assert s.span_reading == ADMISSIBLE_SPANS_REFUSED
    lo, hi = s.admissible_span
    assert lo < 0.35 and hi > 1.0
    for p in s.points:
        if not p.admissible:
            assert lo <= p.residual_share <= hi


def test_an_admissible_rung_is_maximally_unflattering():
    """`w_geom = 20` is admitted at a share ≥ 1 — the null reproducing the
    whole mechanism gain. A filter selecting for the representation could not
    have let this through."""
    worst = max(ladder_rungs().points, key=lambda p: p.residual_share)
    assert worst.admissible
    assert worst.residual_share >= 1.0


def test_the_two_populations_split_on_w_geom_5():
    """D-163's permissive licence, a fourth sighting — and the reason the two
    screens disagree. Joined numerically: a text join on the formatted labels
    reads `5` against `5.0` and silently drops this rung."""
    verdict, split = licence_split()
    assert verdict == LICENCE_SPLIT
    assert split == (5.0,)


def test_no_overlap_is_not_reported_as_agreement(monkeypatch):
    """An empty join must not read as consensus.

    `guard_reflexivity` pulled `licence_split` into the `&`-shaped registry and
    that is what surfaced this: "nothing disagreed" and "nothing was compared"
    are opposite states, and returning LICENCE_AGREED for the second is D-107's
    shape inside the screen written to catch a selected denominator.
    """
    monkeypatch.setattr(
        asel, "ladder_rungs",
        lambda: Screen("empty", (_pt(0.5, True, 999.0),)))
    verdict, split = licence_split()
    assert verdict == asel.LICENCE_NO_OVERLAP
    assert split == ()


def test_the_split_rung_is_permissive_at_the_smaller_ensemble():
    """Direction matters: all-seeds admissibility is monotone non-increasing
    in seed count, so the 16-seed read must be the permissive one."""
    strict = {p.w_geom: p.admissible for p in walked_nulls().points}
    loose = {p.w_geom: p.admissible for p in ladder_rungs().points}
    assert loose[5.0] is True and strict[5.0] is False


def test_frozen_null_has_no_coefficient_and_never_joins():
    """It has no `w_geom` by construction (that is the structural null's whole
    claim), so it must not be matched against a ladder rung."""
    frozen = [p for p in walked_nulls().points
              if p.label == "frozen prediction"]
    assert len(frozen) == 1 and frozen[0].w_geom is None
    assert None not in {p.w_geom for p in ladder_rungs().points}


def test_frozen_admissibility_is_taken_from_the_rung_not_restated():
    from eval.mppi_sandbox.structural_null import convoy_w75_frozen
    frozen = next(p for p in walked_nulls().points
                  if p.label == "frozen prediction")
    assert frozen.admissible == convoy_w75_frozen().admissible


def test_ladder_shares_are_paired_on_the_truncated_arms():
    """Each ladder share must compare 16 null seeds against the arms' first 16
    — the same truncation `NullRung._ladder_arms` performs. A share computed
    against the 32-seed arms would silently compare different seed sets."""
    from eval.mppi_sandbox.geometric_null import CONVOY_W75_CLEARANCE_LADDER
    from eval.mppi_sandbox.scene_transplant import CONVOY_W75_CLEARANCES

    stock = CONVOY_W75_CLEARANCES["stock_mppi"][:16]
    risk = CONVOY_W75_CLEARANCES["risk_mppi"][:16]
    by_w = {p.w_geom: p.residual_share for p in ladder_rungs().points}
    for w, clearances in CONVOY_W75_CLEARANCE_LADDER.items():
        assert len(clearances) == 16
        assert by_w[w] == pytest.approx(
            asel._share(stock, risk, clearances))


def test_both_recorded_populations_are_underpowered():
    """The cycle's actual answer to Q-124, pinned so a later reader cannot
    quote either screen as having settled it."""
    assert walked_nulls().verdict == SCREEN_UNDERPOWERED
    assert ladder_rungs().verdict == SCREEN_UNDERPOWERED


def test_zero_gain_denominator_is_refused_not_silently_inf():
    with pytest.raises(ZeroDivisionError):
        asel._share((1.0, 2.0), (1.0, 2.0), (0.5, 0.5))
