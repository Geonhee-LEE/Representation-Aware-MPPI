# SPDX-License-Identifier: BSD-3-Clause
"""`cafe_freezing_v0`'s absent clearance bar is a declaration gap, not a width failure."""

from __future__ import annotations

from eval.mppi_sandbox import (
    clearance_census,
    declaration_gap,
    spread_generality,
    threshold_vacuity,
)


def test_scene_is_the_undeclared_one() -> None:
    """The module is about the scene `threshold_vacuity` cannot grade at all."""
    assert threshold_vacuity.CENSUS[declaration_gap.SCENE] == "UNDECLARED"


def test_scene_is_the_peak_scene_the_ensemble_was_taken_on() -> None:
    """Findings #2/#3 exist only because the harvest is this scene's ensemble.

    Pinned rather than commented: if `clearance_census` ever re-takes its
    ensemble on a different scene, every seed-wise claim here silently becomes
    about that other scene instead.
    """
    assert clearance_census.PEAK_SCENE == declaration_gap.SCENE
    assert declaration_gap.SEED_ENSEMBLE_SCENES == (declaration_gap.SCENE,)


def test_per_seed_spread_matches_the_pin() -> None:
    assert declaration_gap.per_seed_spread() == declaration_gap.PER_SEED_SPREAD


def test_every_seed_is_covered() -> None:
    """The column is the whole ensemble, not a subset of its seeds."""
    assert sorted(declaration_gap.per_seed_spread()) == list(
        range(clearance_census.SEEDS)
    )


def test_common_window_matches_the_pin_and_is_non_empty() -> None:
    lo, hi = declaration_gap.common_window()
    assert (lo, hi) == declaration_gap.COMMON_WINDOW
    assert lo < hi
    assert declaration_gap.window_width() == 0.4354


def test_verdict_is_a_declaration_gap() -> None:
    assert declaration_gap.verdict() == declaration_gap.DECLARATION_GAP


def test_window_discriminates_on_every_seed() -> None:
    """Finding #3's claim, checked directly rather than via the intersection.

    A bar in the window must leave at least one arm above and one below on
    *each* seed — that is what "discriminates" means, and deriving it from the
    interval arithmetic would be assuming the thing under test.
    """
    mid = sum(declaration_gap.common_window()) / 2
    rows = clearance_census.SEED_ENSEMBLE
    for seed in range(clearance_census.SEEDS):
        col = [vals[seed] for vals in rows.values()]
        assert any(v > mid for v in col), seed
        assert any(v < mid for v in col), seed


def test_spread_is_seed_stable_relative_to_its_own_size() -> None:
    """Finding #2 — the swing is a small fraction of the statistic.

    Reported as a ratio, not thresholded against a tuned constant (D-044): the
    claim is that seed noise does not swamp arm spread on this scene, and the
    number that supports it is the swing over the mean.
    """
    spreads = [row[2] for row in declaration_gap.per_seed_spread().values()]
    swing = max(spreads) - min(spreads)
    assert round(swing, 4) == 0.0599
    assert swing / (sum(spreads) / len(spreads)) < 0.15


def test_narrowest_seed_still_out_spreads_the_graded_population() -> None:
    """Finding #2's second half — the ranking survives the worst seed.

    Without this the seed-stability reading would be compatible with the
    quietest seed dropping into `spread_generality`'s band, which is exactly
    the case where finding #1 would stop holding across the ensemble.
    """
    narrowest = min(row[2] for row in declaration_gap.per_seed_spread().values())
    widest_graded = max(row[2] for row in spread_generality.CENSUS.values())
    assert narrowest > widest_graded


def test_spread_rank_reads_the_other_module_rather_than_restating_it() -> None:
    own, widest, widest_sprd, vacuous, vacuous_sprd = declaration_gap.spread_rank()
    assert (own, widest, widest_sprd, vacuous, vacuous_sprd) == declaration_gap.SPREAD_RANK
    assert spread_generality.CENSUS[widest][2] == widest_sprd
    assert spread_generality.CENSUS[vacuous][2] == vacuous_sprd
    assert vacuous in spread_generality.REPAIRABLE_BY_PLACEMENT
    assert own > widest_sprd > vacuous_sprd


def test_window_is_wider_than_head_ons_whole_attained_range() -> None:
    """The ordering claim: adding a bar here is a cheaper repair than moving one.

    D-365's `cafe_head_on_v0` repair has to land inside a `0.1964 m` seed-0
    range; this one may be drawn from a `0.4354 m` interval verified on eight
    seeds.
    """
    head_on_range = spread_generality.CENSUS["cafe_head_on_v0"][2]
    assert declaration_gap.window_width() > 2 * head_on_range


def test_duplicate_rows_are_named_and_real() -> None:
    """Six distinct arms, eight rows — the reader is counting the wrong number otherwise."""
    for duplicate, original in declaration_gap.DUPLICATE_ROWS:
        assert (
            clearance_census.SEED_ENSEMBLE[duplicate]
            == clearance_census.SEED_ENSEMBLE[original]
        )
    distinct = {vals for vals in clearance_census.SEED_ENSEMBLE.values()}
    assert len(clearance_census.SEED_ENSEMBLE) - len(distinct) == len(
        declaration_gap.DUPLICATE_ROWS
    )


def test_duplicates_cannot_move_the_window() -> None:
    """Scope bullet #2's justification, not just its assertion."""
    deduped = dict(clearance_census.SEED_ENSEMBLE)
    for duplicate, _ in declaration_gap.DUPLICATE_ROWS:
        deduped.pop(duplicate)
    lo = max(
        min(vals[s] for vals in deduped.values()) for s in range(clearance_census.SEEDS)
    )
    hi = min(
        max(vals[s] for vals in deduped.values()) for s in range(clearance_census.SEEDS)
    )
    assert (round(lo, 4), round(hi, 4)) == declaration_gap.COMMON_WINDOW


def test_arm_straddle_is_narrower_than_the_registry_window() -> None:
    """Scope bullet #4 — the two questions are different and must not be conflated."""
    straddle = declaration_gap.arm_straddle()
    assert set(straddle) == set(clearance_census.SEED_ENSEMBLE)
    for lo, hi in straddle.values():
        assert hi - lo < declaration_gap.window_width()


def test_only_the_baseline_pair_straddles_the_window_midpoint() -> None:
    """Recorded because it is the shape of what a mid-window bar would grade.

    `cbf_mppi` clears it on every seed and the five representation arms fail it
    on every seed; only the baseline (and its inert geometric twin) is decided
    seed by seed. A bar placed there grades the registry, not the seeds.
    """
    mid = sum(declaration_gap.common_window()) / 2
    assert declaration_gap.straddling_arms(mid) == ("geometric_mppi", "stock_mppi")


def test_no_value_is_proposed() -> None:
    """The bar's value is scene intent (user-blocked); this module reports an interval.

    Guards the one way this work could overstep D-365's own limit — a module
    that named a number would be doing the threshold-shopping the branch has
    refused four times.
    """
    source = (declaration_gap.__doc__ or "") + "".join(
        str(getattr(declaration_gap, name).__doc__ or "")
        for name in dir(declaration_gap)
        if callable(getattr(declaration_gap, name, None))
    )
    assert "should be set to" not in source
    assert "recommend" not in source.lower()
