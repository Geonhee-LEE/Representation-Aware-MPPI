# SPDX-License-Identifier: BSD-3-Clause
"""Pins for `seed_debt` — the discharge of STATE's 256-rollout seed debt."""

from __future__ import annotations

import itertools

import pytest

from eval.mppi_sandbox import (
    clearance_census,
    declaration_gap,
    pairing_precondition,
    scene_transfer,
    seed_debt,
)


def test_baseline_agrees_with_clearance_census():
    """A rename of the baseline arm goes red here, not silently re-scoped."""
    assert seed_debt.BASELINE == clearance_census.BASELINE


def test_the_four_scenes_are_the_ones_state_priced_and_exclude_freezing():
    """The debt discharged is STATE #2's four, not D-366's already-harvested one."""
    assert set(seed_debt.ENSEMBLES) == {
        "cafe_convoy_v0", "cafe_cut_in_v0",
        "cafe_head_on_v0", "cafe_obstacle_crossing_v0",
    }
    assert scene_transfer.FREEZING_SCENE not in seed_debt.ENSEMBLES
    assert seed_debt.SCENE == scene_transfer.HEAD_ON_SCENE


def test_every_ensemble_is_the_full_registry_at_eight_seeds():
    """The debt is only paid if the harvest is a census, not a selection."""
    for scene, ensemble in seed_debt.ENSEMBLES.items():
        assert set(ensemble) == set(clearance_census.SEED_ENSEMBLE), scene
        for arm, row in ensemble.items():
            assert len(row) == clearance_census.SEEDS, (scene, arm)


def test_the_debt_costs_zero_rollouts():
    """Finding's premise: the ensembles are on disk, so the price is zero."""
    assert seed_debt.BUDGETED_ROLLOUTS == 256
    assert seed_debt.ACTUAL_ROLLOUTS == 0


@pytest.mark.parametrize("scene", sorted(seed_debt.ENSEMBLES))
def test_pinned_windows_are_recomputed_not_recalled(scene):
    assert seed_debt.common_window(scene) == seed_debt.WINDOWS[scene]


@pytest.mark.parametrize("scene", sorted(seed_debt.ENSEMBLES))
def test_every_scene_hosts_a_seed_robust_bar(scene):
    """All four windows non-empty — every scene STATE widened is gradeable."""
    assert seed_debt.window_width(scene) > 0.0
    assert seed_debt.verdict(scene) == seed_debt.SURVIVES


def test_window_is_the_intersection_of_the_per_seed_ranges():
    """Derived, so an ensemble re-take moves the window rather than the prose."""
    scene = seed_debt.SCENE
    spread = seed_debt.per_seed_spread(scene)
    lo, hi = seed_debt.common_window(scene)
    assert lo == max(row[0] for row in spread.values())
    assert hi == min(row[1] for row in spread.values())
    for seed, (seed_lo, seed_hi, _) in spread.items():
        assert seed_lo <= lo and hi <= seed_hi, seed


def test_a_window_value_cuts_the_population_on_every_seed():
    """The property the repair needs, checked per seed rather than inferred."""
    lo, hi = seed_debt.WINDOW
    bar = (lo + hi) / 2.0
    ensemble = seed_debt.ENSEMBLES[seed_debt.SCENE]
    for seed in range(clearance_census.SEEDS):
        col = [row[seed] for row in ensemble.values()]
        assert any(v > bar for v in col) and any(v < bar for v in col), seed


def test_per_seed_spread_agrees_with_declaration_gap_on_its_shared_statistic():
    """Same arithmetic, scene as a parameter — pinned equal on freezing's shape."""
    theirs = declaration_gap.per_seed_spread()
    mine = seed_debt.per_seed_spread(seed_debt.SCENE)
    assert set(theirs) == set(mine)
    for seed, (lo, hi, spread) in mine.items():
        assert round(hi - lo, 4) == spread, seed


def test_finding_1_the_interval_survives_but_narrows_and_the_ceiling_collapses():
    lo, hi = seed_debt.WINDOW
    seed0_lo, seed0_hi, seed0_spread = seed_debt.SEED0_RANGE
    assert seed_debt.narrowing() == 1.96
    assert seed_debt.window_width(seed_debt.SCENE) < seed0_spread
    # The ceiling moves far more than the floor — that is the whole finding.
    assert seed0_hi - hi > lo - seed0_lo
    assert round(seed0_hi - hi, 4) == 0.0959


def test_finding_1_seed_0_is_not_the_widest_seed_and_that_is_not_the_mechanism():
    """Written expecting seed 0 to be the widest; it is third of eight.

    So D-365's overstatement is **not** "it read the luckiest seed" — seeds 3
    and 6 are wider (`0.2126`, `0.2121` vs `0.1964`). The mechanism is that
    *any* single seed overstates an intersection, because a per-seed range is a
    superset of the intersection by construction. Kept as a pin because the
    plausible-and-wrong version of finding #1 is the one a reader will reach
    for, and `test_finding_1_one_seed_binds_the_ceiling` names the real cause.
    """
    spread = seed_debt.per_seed_spread(seed_debt.SCENE)
    assert spread[0] == seed_debt.SEED0_RANGE
    widths = sorted((row[2] for row in spread.values()), reverse=True)
    assert widths.index(spread[0][2]) == 2
    assert spread[0][2] < max(widths)


def test_finding_1_one_seed_binds_the_ceiling():
    """`cbf_mppi` on seed 4 is what a seed-robust bar has to clear."""
    _lo, hi = seed_debt.WINDOW
    ensemble = seed_debt.ENSEMBLES[seed_debt.SCENE]
    binding = [
        seed for seed in range(clearance_census.SEEDS)
        if max(row[seed] for row in ensemble.values()) == hi
    ]
    assert binding == [4]
    assert ensemble["cbf_mppi"][4] == hi


def test_finding_2_freezing_window_pinned_equal_to_declaration_gap():
    """A re-take there goes red here instead of quietly restating 4.35x."""
    assert declaration_gap.window_width() == seed_debt.FREEZING_WINDOW_WIDTH


def test_finding_2_ratio_is_derived_and_exceeds_states_2_2x():
    ratio = round(
        seed_debt.FREEZING_WINDOW_WIDTH / seed_debt.window_width(seed_debt.SCENE), 2
    )
    assert ratio == seed_debt.WINDOW_RATIO
    # STATE's 2.2x is freezing against head_on's *seed-0* spread.
    assert round(
        seed_debt.FREEZING_WINDOW_WIDTH / seed_debt.SEED0_RANGE[2], 1
    ) == 2.2
    assert seed_debt.WINDOW_RATIO > 2.2


def test_finding_3_sign_tally_is_recomputed_and_the_majority_flips():
    assert seed_debt.signs(seed_debt.SCENE) == seed_debt.HEAD_ON_SIGNS
    neg, total = seed_debt.HEAD_ON_SIGNS
    assert neg * 2 > total          # majority negative on head_on
    f_neg, f_total = seed_debt.FREEZING_SIGNS
    assert f_neg * 2 < f_total      # minority negative on freezing
    assert total == f_total         # same population width, so the counts compare


def test_finding_3_freezing_tally_agrees_with_pairing_precondition():
    """D-367's number is read from its module, not retyped from its prose."""
    rows = [
        pairing_precondition.pearson(
            clearance_census.SEED_ENSEMBLE[a], clearance_census.SEED_ENSEMBLE[b]
        )
        for a, b in itertools.combinations(sorted(clearance_census.SEED_ENSEMBLE), 2)
        if not seed_debt.is_degenerate(a, b)
    ]
    assert (sum(1 for r in rows if r < 0.0), len(rows)) == seed_debt.FREEZING_SIGNS


def test_finding_3_range_straddles_zero_on_both_scenes():
    """The property that kills the rider as a policy, on the second scene too."""
    assert seed_debt.rho_range(seed_debt.SCENE) == seed_debt.RHO_RANGE
    assert seed_debt.straddles_zero(seed_debt.SCENE)
    lo, hi = seed_debt.RHO_RANGE
    assert lo < 0.0 < hi


def test_finding_3_the_baseline_column_is_worse_than_the_branch_wide_tally():
    assert seed_debt.baseline_signs(seed_debt.SCENE) == seed_debt.HEAD_ON_BASELINE_HURT
    hurt, total = seed_debt.HEAD_ON_BASELINE_HURT
    assert hurt * 2 > total
    # Worse than D-367's, and on the comparison the deficit is claimed in.
    assert hurt > seed_debt.FREEZING_BASELINE_HURT[0]
    assert total == seed_debt.FREEZING_BASELINE_HURT[1]


def test_finding_3_worst_baseline_pair_is_social_mppi_and_pairing_inflates_it():
    rows = seed_debt.baseline_hurt(seed_debt.SCENE)
    rho, arm, ratio = rows[0]
    assert arm == "social_mppi"
    assert (rho, ratio) == (-0.5614, 1.2496)
    assert ratio > pairing_precondition.NEUTRAL_SD_RATIO


def test_sd_ratio_agrees_with_pairing_preconditions_own_reading():
    """Two modules, one formula — pinned on a shared rho rather than by eye."""
    for rho in (-0.5614, -0.2988, 0.0, 0.3389, 0.7218):
        reading = pairing_precondition.PairReading("a", "b", rho)
        assert seed_debt.sd_ratio(rho) == round(reading.sd_ratio, 4)


def test_sd_ratio_crosses_neutral_exactly_at_zero_correlation():
    assert seed_debt.sd_ratio(0.0) == pairing_precondition.NEUTRAL_SD_RATIO
    # 4 dp is the resolution: `+-0.0001` in rho rounds back onto 1.0, so the
    # crossing is pinned at the smallest rho the returned precision can express.
    assert seed_debt.sd_ratio(-0.001) > pairing_precondition.NEUTRAL_SD_RATIO
    assert seed_debt.sd_ratio(0.001) < pairing_precondition.NEUTRAL_SD_RATIO
    assert seed_debt.sd_ratio(-0.0001) == pairing_precondition.NEUTRAL_SD_RATIO


@pytest.mark.parametrize("scene", sorted(seed_debt.ENSEMBLES))
def test_correlations_cover_every_pair_and_are_sorted(scene):
    ensemble = seed_debt.ENSEMBLES[scene]
    rows = seed_debt.correlations(scene)
    n = len(ensemble)
    assert len(rows) == n * (n - 1) // 2
    assert list(rows) == sorted(rows)
    assert len(seed_debt.non_degenerate(scene)) == len(rows) - len(
        pairing_precondition.DEGENERATE
    )


def test_the_inert_channel_signature_reproduces_on_a_second_scene():
    """Perfect seed correlation is derived from the measurement, not recalled."""
    derived = seed_debt.degenerate_pairs(seed_debt.SCENE)
    assert derived == pairing_precondition.DEGENERATE
    assert len(derived) == 2


def test_the_inert_pairs_are_bit_identical_which_is_why_rho_is_one():
    ensemble = seed_debt.ENSEMBLES[seed_debt.SCENE]
    for arm_a, arm_b in pairing_precondition.DEGENERATE:
        assert ensemble[arm_a] == ensemble[arm_b]


def test_scope_no_cross_track_ensemble_is_claimed():
    """The `cte_rms_max` half of the grading surface stays unpaid (scope bullet)."""
    doc = seed_debt.__doc__ or ""
    assert "Clearance only." in doc
    assert "cross-track" in doc
    for ensemble in seed_debt.ENSEMBLES.values():
        for row in ensemble.values():
            assert all(v >= 0.0 for v in row)   # clearances, not signed CTE


def test_report_names_all_three_findings_and_the_zero_price():
    out = seed_debt.format_report()
    for token in ("finding #1", "finding #2", "finding #3", "256", "SURVIVES"):
        assert token in out
    assert str(seed_debt.WINDOW_RATIO) in out
