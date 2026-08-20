# SPDX-License-Identifier: BSD-3-Clause
"""The TVaR re-expression of the cross-track column, and what it does not buy."""

from __future__ import annotations

from eval.mppi_sandbox import aa_calibration, excursion_seed_width, tail_mean


def test_the_census_is_internally_consistent():
    assert tail_mean.drift() == ()


def test_the_two_columns_rest_on_the_same_arms():
    """The whole comparison is 'same rollouts, different observable'.

    If the arm populations differ the reading silently becomes a comparison of
    two *cells*, which is the D-374 defect (two sides of a ratio derived from
    different floors) transposed onto the numerator.
    """
    assert set(tail_mean.TVAR_ENSEMBLE) == set(
        excursion_seed_width.SEED_ENSEMBLE[tail_mean.SCENE])
    assert all(len(r) == tail_mean.SEEDS for r in tail_mean.TVAR_ENSEMBLE.values())


def test_finding_1_tvar_clears_the_floor_that_cte_max_misses():
    """The headline: an ungradeable cell becomes graded by changing observable.

    Both halves are asserted. A test that only pinned TVaR's `2.64x` would pass
    just as well in a world where `cte_max` also cleared — and in that world the
    fork would be untouched, because nothing would have been rescued.
    """
    assert tail_mean.baseline_ratio() == 0.96
    assert tail_mean.ratio() == 2.64
    assert tail_mean.clears_floor() is True
    assert tail_mean.rescued() is True


def test_finding_1_survives_the_adversarial_floor():
    """D-372/D-374 grade on `max_floor`; a p95-only rescue would be weaker.

    `cte_max` fails both readings (`0.94x`), so the rescue is not an artifact of
    which floor was chosen.
    """
    assert tail_mean.ratio(strict=True) == 2.49
    assert tail_mean.clears_floor(strict=True) is True
    assert tail_mean.baseline_ratio(strict=True) == 0.94


def test_finding_2_the_floor_falls_while_the_gap_rises():
    """A rescue that only widened the numerator would look like a rescaling.

    Pinned as a direction, not a magnitude: the gap must grow *and* the floor
    must shrink, which is the estimator-class prediction and the reason the
    ratio moves by more than either factor alone.
    """
    assert tail_mean.real_gap() > aa_calibration.real_gap("cte_max", tail_mean.SCENE)
    assert tail_mean.p95_floor() < aa_calibration.p95_floor("cte_max", tail_mean.SCENE)


def test_finding_3_the_arms_split_into_two_clusters_with_nothing_between():
    """The gap the maximum blurred, stated as a partition rather than a spread."""
    means = sorted(sum(r) / len(r) for r in tail_mean.TVAR_ENSEMBLE.values())
    jumps = [(b - a, i) for i, (a, b) in enumerate(zip(means, means[1:]))]
    widest, at = max(jumps)
    low, high = means[: at + 1], means[at + 1:]
    assert len(low) == 4 and len(high) == 4
    assert widest > tail_mean.p95_floor()
    # the between-cluster ratio, and neither cluster's internal width nears the floor
    assert round(sum(high) / 4 / (sum(low) / 4), 1) == 3.0
    assert (low[-1] - low[0]) < tail_mean.p95_floor()
    assert (high[-1] - high[0]) < tail_mean.p95_floor()


def test_finding_4_the_claim_survives_the_g5_threshold_window():
    """A claim alive at exactly one threshold is shopped; this one is not."""
    assert sorted(tail_mean.THRESHOLD_STABILITY) == [0.88, 0.90, 0.92]
    assert all(r > 1.0 for _g, _f, r in tail_mean.THRESHOLD_STABILITY.values())
    assert tail_mean.threshold_shopped() == ()


def test_finding_4_the_ratio_decays_monotonically_toward_the_maximum():
    """The mechanism, as a trend rather than a point.

    Gap down, floor up, ratio down as `q` rises — and `cte_max` is the `q -> 1`
    endpoint of that same curve at `0.96x`. If the rescue were an artifact of
    `q=0.90` the ordering would not be monotone in all three columns at once.
    """
    qs = sorted(tail_mean.THRESHOLD_STABILITY)
    gaps = [tail_mean.THRESHOLD_STABILITY[q][0] for q in qs]
    floors = [tail_mean.THRESHOLD_STABILITY[q][1] for q in qs]
    ratios = [tail_mean.THRESHOLD_STABILITY[q][2] for q in qs]
    assert gaps == sorted(gaps, reverse=True)
    assert floors == sorted(floors)
    assert ratios == sorted(ratios, reverse=True)
    # the curve is heading for the value the maximum actually measures
    assert ratios[-1] > tail_mean.baseline_ratio()


def test_the_q_that_is_pinned_is_the_one_that_was_measured():
    """`Q` must appear in the window it claims to be the centre of."""
    assert tail_mean.Q in tail_mean.THRESHOLD_STABILITY
    assert tail_mean.THRESHOLD_STABILITY[tail_mean.Q][2] == tail_mean.ratio()
    assert tail_mean.THRESHOLD_STABILITY[tail_mean.Q][0] == tail_mean.real_gap()
    assert tail_mean.THRESHOLD_STABILITY[tail_mean.Q][1] == tail_mean.p95_floor()


def test_the_floor_machinery_is_shared_not_reimplemented():
    """The floor is re-derived through `aa_calibration`, never copied.

    So a change to the A-A definition moves both columns together rather than
    leaving this module quoting a floor the rest of the branch has retired.
    """
    for row in tail_mean.TVAR_ENSEMBLE.values():
        gaps = aa_calibration.null_gaps(row)
        assert gaps == tuple(sorted(gaps))
        assert gaps[-1] >= aa_calibration._quantile(gaps, 0.95)
    assert tail_mean.max_floor() >= tail_mean.p95_floor()


def test_baseline_ratio_is_read_from_aa_calibration_not_restated():
    expected = round(
        aa_calibration.real_gap("cte_max", tail_mean.SCENE)
        / aa_calibration.p95_floor("cte_max", tail_mean.SCENE), 2)
    assert tail_mean.baseline_ratio() == expected


def test_ratio_and_clears_floor_cannot_disagree():
    assert tail_mean.clears_floor() == (tail_mean.ratio() > 1.0)
    assert tail_mean.clears_floor(strict=True) == (tail_mean.ratio(True) > 1.0)


def test_the_census_prints_both_columns_and_the_rescue_verdict():
    text = tail_mean.format_census()
    assert "cte_max" in text and "TVaR_0.9" in text
    assert "RESCUED: True" in text
    assert "2.64x" in text and "0.96x" in text


def test_the_claim_form_names_the_observable_not_the_worst_case():
    """The prose failure mode this module is most exposed to.

    `cte_max` and `TVaR_0.9` answer different questions, and a later cycle
    quoting `2.64x` as evidence about *worst-case* excursion would be citing a
    number nobody measured.
    """
    assert "worst-decile" in tail_mean.CLAIM_FORM
    assert "TVaR" in tail_mean.CLAIM_FORM and tail_mean.SCENE in tail_mean.CLAIM_FORM
    assert "worst-case" not in tail_mean.CLAIM_FORM


def test_the_second_endpoint_is_untestable_not_refuted():
    """The distinction the whole second harvest exists to preserve.

    A cell whose arms do not separate cannot refute anything. Collapsing
    `UNTESTABLE` into `REFUTED` would record `city_curved_v0` as evidence
    *against* finding #1 when it is evidence about the scene.
    """
    assert tail_mean.excited(tail_mean.TVAR_ENSEMBLE_SECOND) is False
    assert tail_mean.second_verdict().startswith("UNTESTABLE")
    assert "REFUTED" not in tail_mean.second_verdict()


def test_the_degeneracy_is_the_scenes_property_not_this_observables():
    """Same seven-way tie in the pinned `cte_max` column on the same scene.

    If only the TVaR column were degenerate the finding would be about the
    estimator. It is present in data pinned before this module existed, so it
    is about `city_curved_v0`.
    """
    pinned = excursion_seed_width.SEED_ENSEMBLE[tail_mean.SECOND_SCENE]
    assert len(set(pinned.values())) == len(set(tail_mean.TVAR_ENSEMBLE_SECOND.values()))
    assert tail_mean.distinct_arms(tail_mean.TVAR_ENSEMBLE_SECOND) == 2


def test_the_excited_endpoint_is_excited():
    """The precondition is a real filter, not one that rejects every cell."""
    assert tail_mean.distinct_arms() == 6
    assert tail_mean.excited() is True


def test_a_column_level_claim_needs_a_second_excited_endpoint():
    """D-371's exact error, guarded rather than remembered.

    This assertion read `is False` from D-383 until the third endpoint was
    harvested. What licenses it now is *not* that the requirement was relaxed —
    it is that a second excited scene was bought and it cleared. The degenerate
    endpoint still licenses nothing, which is what the second half pins.
    """
    assert tail_mean.column_licensed() is True
    assert tail_mean.clears_floor() is True
    assert tail_mean.excited(tail_mean.TVAR_ENSEMBLE_THIRD) is True
    assert tail_mean.third_clears_floor() is True
    # The degenerate scene contributes nothing either way.
    assert tail_mean.excited(tail_mean.TVAR_ENSEMBLE_SECOND) is False


def test_the_third_endpoint_clears_on_both_floors():
    """The measurement itself: 64 rollouts, 6/8 arms, clears p95 and adversarial."""
    assert tail_mean.distinct_arms(tail_mean.TVAR_ENSEMBLE_THIRD) == 6
    assert tail_mean.third_ratio() == 3.88
    assert tail_mean.third_ratio(strict=True) == 3.32
    assert tail_mean.third_clears_floor(strict=True) is True
    assert tail_mean.third_verdict().startswith("CONFIRMED")


def test_the_third_endpoint_is_paired_and_the_contrast_does_not_replicate():
    """The half the previous cycle did not buy, bought — and it came back negative.

    `cafe_head_on_v0` was picked by the clearance ordering, not by where a
    `cte_max` ensemble sat, so its pairing had to be paid for (64 rollouts).
    Paid, the second scene grades `cte_max` at `3.12x` — finding #1's
    *cte_max-misses-its-floor* half does not reproduce, so the contrast is a
    property of `cafe_convoy_v0` and not of the column.
    """
    assert tail_mean.third_paired() is True
    assert "UNPAIRED" not in tail_mean.third_verdict()
    assert tail_mean.THIRD_SCENE not in tail_mean.free_screen_gap()
    assert tail_mean.THIRD_SCENE in tail_mean.both_columns_scenes()

    assert tail_mean.third_baseline_ratio() == 3.12
    assert tail_mean.third_baseline_ratio(strict=True) == 2.73
    assert tail_mean.contrast_replicates() is False
    assert "DOES NOT replicate" in tail_mean.third_verdict()


def test_what_survives_the_failed_replication_is_dominance_not_contrast():
    """The weaker claim the two comparable cells actually support.

    TVaR's ratio exceeds `cte_max`'s on both scenes that can be compared. That
    is a *noise-reduction* statement and it is consistent with both cells: it
    only becomes decisive where the effect is marginal against seed noise, which
    is convoy and not head-on.
    """
    assert tail_mean.dominance_holds() is True
    assert set(tail_mean.COMPARABLE_CELLS) == {tail_mean.SCENE, tail_mean.THIRD_SCENE}
    for tv, base in tail_mean.COMPARABLE_CELLS.values():
        assert tv > base
    # Exactly one of the two cells has cte_max below its floor — that is the
    # whole of the contrast's evidence, and it is a population of one.
    assert sum(1 for _tv, b in tail_mean.COMPARABLE_CELLS.values() if b <= 1.0) == 1


def test_the_degenerate_scene_is_not_admitted_as_a_counter_example():
    """`city_curved_v0` disagrees with dominance and must still be excluded.

    Its `cte_max` reads `0.35x` against TVaR's `0.07x` — the opposite ordering.
    Admitting it would refute `dominance_holds()` on the strength of a cell with
    two distinct arm rows, which is the `UNTESTABLE`/`REFUTED` collapse D-385
    ruled out. The exclusion is by `excited()`, not by which way it points.
    """
    assert tail_mean.second_baseline_ratio() > tail_mean.second_ratio()
    assert not tail_mean.excited(tail_mean.TVAR_ENSEMBLE_SECOND)
    assert tail_mean.SECOND_SCENE not in tail_mean.COMPARABLE_CELLS


def test_the_column_claim_form_keeps_the_contrast_caveat():
    """Prose drift is the failure mode, same as `CLAIM_FORM`."""
    form = tail_mean.COLUMN_CLAIM_FORM
    assert "cafe_convoy_v0 only" in form
    assert tail_mean.THIRD_SCENE in form
    # It must not claim the contrast on both scenes.
    assert "cte_max" in form and "gradeable as TVaR_0.9" in form


def test_the_second_endpoints_floors_are_well_formed_despite_the_degeneracy():
    """Why `MIN_DISTINCT_ARMS` gates instead of the ratio.

    Every floor statistic returns a clean number on the degenerate cell — that
    is the trap. The reading is only untrustworthy for a reason no ratio shows.
    """
    assert tail_mean.second_ratio() == 0.07
    assert tail_mean.second_ratio(strict=True) == 0.06
    assert tail_mean.second_baseline_ratio() == 0.35
    assert tail_mean.second_ratio() < 1.0


def test_the_second_g5_window_fails_at_every_threshold():
    """Not threshold-shopped in either direction — no signal anywhere in it."""
    assert sorted(tail_mean.THRESHOLD_STABILITY_SECOND) == [0.88, 0.90, 0.92]
    assert all(r < 1.0 for _g, _f, r in tail_mean.THRESHOLD_STABILITY_SECOND.values())
    assert tail_mean.THRESHOLD_STABILITY_SECOND[tail_mean.Q][2] == tail_mean.second_ratio()


def test_the_census_reports_the_untestable_verdict():
    """The degenerate endpoint stays visible after a third one licensed the column.

    The licensing line flipped to `True` when `THIRD_SCENE` was harvested; the
    `UNTESTABLE` reading beside it must not be tidied away by that, or the
    census stops distinguishing "measured and flat" from "never looked at".
    """
    text = tail_mean.format_census()
    assert "COLUMN-LEVEL CLAIM LICENSED: True" in text
    assert "UNTESTABLE" in text and tail_mean.SECOND_SCENE in text
    assert tail_mean.THIRD_SCENE in text
    # The licensing line and the failed replication must print together, or the
    # census reads as if a second endpoint confirmed finding #1 outright.
    assert "CONTRAST REPLICATES: False" in text
    assert "DOMINANCE HOLDS: True" in text


def test_the_free_screen_state_asked_for_is_empty_on_the_column_it_asked_about():
    """The correction: `cte_max` is pinned only where it was already harvested.

    STATE's next-action #1 priced a screen of "the six unharvested scenarios" at
    zero rollouts, on the true premise that `distinct_arms` is free wherever an
    ensemble is pinned. The conjunction is empty — the six are unharvested in
    exactly the column the screen needed — so the free step does not exist and
    the cost is `REMAINING_DEBT`, unchanged.
    """
    gap = tail_mean.free_screen_gap()
    # 6 when D-386 measured it; 5 since one of the six was bought outright.
    assert len(gap) == 5
    assert tail_mean.SCENE not in gap and tail_mean.SECOND_SCENE not in gap
    assert not any(("cte_max", scene) in tail_mean.screen() for scene in gap)


def test_the_clearance_column_is_excited_everywhere_it_is_pinned():
    """STATE's next-action #2, answered at zero rollouts.

    D-385's blind spot does not repeat one column over: all five pinned
    clearance cells separate their arms well above `MIN_DISTINCT_ARMS`.
    """
    cells = {cell: n for cell, n in tail_mean.screen().items()
             if cell[0] == "clearance"}
    assert len(cells) == 5
    assert all(n >= tail_mean.MIN_DISTINCT_ARMS for n in cells.values())
    assert not [c for c in tail_mean.degenerate_cells() if c[0] == "clearance"]


def test_the_only_degenerate_pinned_cell_is_the_one_d385_found():
    """The screen and `second_verdict()` must not be able to disagree."""
    assert tail_mean.degenerate_cells() == (("cte_max", tail_mean.SECOND_SCENE),)
    assert tail_mean.second_verdict().startswith("UNTESTABLE")


def test_cross_column_excitation_cannot_contain_its_own_falsifier():
    """Why five excited clearance cells stay an ordering hint after a second case.

    The population grew from one to two when `cafe_head_on_v0` was harvested,
    and the second case agrees with the first. That does **not** upgrade the
    inference, and the reason is structural rather than about sample size: a
    scene enters this set only once its cross-track column has been *bought*,
    so the falsifying shape — clearance excited, cross-track degenerate — is
    unobservable here by construction. `city_curved_v0` is the one scene that
    could have supplied it and it is absent from the clearance harvest.
    """
    both = tail_mean.both_columns_scenes()
    assert both == (tail_mean.SCENE, tail_mean.THIRD_SCENE)
    for scene in both:
        assert tail_mean.screen()[("clearance", scene)] >= tail_mean.MIN_DISTINCT_ARMS
        assert tail_mean.screen()[("cte_max", scene)] >= tail_mean.MIN_DISTINCT_ARMS
    # The degenerate cross-track cell is outside the set, so the agreement is
    # over a population selected on the very property being predicted.
    assert tail_mean.SECOND_SCENE not in both
    assert "does not license" in tail_mean.SCREEN_VERDICT


def test_the_screen_prints_and_stays_internally_consistent():
    text = tail_mean.format_census()
    assert "excitation screen" in text and "DEGENERATE" in text
    assert tail_mean.drift() == ()
