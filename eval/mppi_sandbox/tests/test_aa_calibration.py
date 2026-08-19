# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the A-A null calibration (Islam et al. 1708.04133, method only)."""

from __future__ import annotations

import math
import statistics

import pytest

from eval.mppi_sandbox import aa_calibration as aa
from eval.mppi_sandbox import clearance_census, excursion_seed_width, scene_transfer


def test_no_drift_from_pins():
    assert aa.drift() == ()


def test_cli_exits_clean():
    assert aa.main([]) == 0


# --- the null construction itself -------------------------------------------


def test_split_count_is_the_whole_null_distribution():
    """C(8,4)/2 = 35 — enumerated, not sampled, so there is no sampling error."""
    assert aa.SPLITS == 35
    for column, scene in aa.CALIBRATED:
        for row in aa._ensemble(column, scene).values():
            assert len(aa.null_gaps(row)) == aa.SPLITS


def test_constant_row_has_identically_zero_null():
    """An arm with no seed variation manufactures no gap. Sanity floor."""
    assert set(aa.null_gaps((0.5,) * aa.SEEDS)) == {0.0}


def test_null_gaps_are_sorted_and_non_negative():
    gaps = aa.null_gaps(excursion_seed_width.SEED_ENSEMBLE["cafe_convoy_v0"]["risk_mppi"])
    assert list(gaps) == sorted(gaps)
    assert gaps[0] >= 0.0


def test_null_gap_is_invariant_to_complementing_a_split():
    """|mean(A)-mean(B)| is symmetric, so dedup by 'seed 0 in A' loses nothing."""
    row = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    gaps = aa.null_gaps(row)
    # widest split of a monotone row is the bottom half against the top half
    assert gaps[-1] == pytest.approx(0.4, abs=1e-12)


def test_shifting_a_row_by_a_constant_leaves_the_null_unchanged():
    """The floor is a dispersion statistic, not a level one."""
    row = excursion_seed_width.SEED_ENSEMBLE["city_curved_v0"]["cbf_mppi"]
    shifted = tuple(v + 10.0 for v in row)
    assert aa.null_gaps(shifted) == pytest.approx(aa.null_gaps(row), abs=1e-9)


def test_quantile_uses_ceiling_rank_without_interpolation():
    values = tuple(float(i) for i in range(35))
    assert aa._quantile(values, 0.95) == 33.0
    assert aa._quantile(values, 1.0) == 34.0


def test_p95_floor_never_exceeds_max_floor():
    for column, scene in aa.CALIBRATED:
        assert aa.p95_floor(column, scene) <= aa.max_floor(column, scene)


# --- D-372 finding #1: the divide is by column, not by scene ----------------


def test_column_verdict_is_derived_and_not_typed():
    """The pinned table must equal the one computed from `CALIBRATED`."""
    for column, pinned in aa.COLUMN_VERDICT.items():
        assert aa.column_verdict(column) == pinned


def test_clearance_clears_its_null_on_every_scene_it_is_calibrated_on():
    """5 of 5, on the adversarial reading too — this is the graded column."""
    rows, p95, mx = aa.COLUMN_VERDICT["clearance"]
    assert (rows, p95, mx) == (5, 5, 5)
    for column, scene in aa.CALIBRATED:
        if column == "clearance":
            assert aa.clears_floor(column, scene, strict=True) is True
            assert aa.headroom(column, scene) > 2.0


def test_cross_track_clears_its_null_on_no_scene():
    """0 of 2, by neither reading — unchanged from D-371."""
    assert aa.COLUMN_VERDICT["cte_max"] == (2, 0, 0)
    for column, scene in aa.CALIBRATED:
        if column == "cte_max":
            assert aa.clears_floor(column, scene) is False
            assert aa.headroom(column, scene) < 1.0


def test_the_two_columns_do_not_overlap_in_headroom():
    """The worst clearance row still clears by more than 2x the best cte row.

    This is the statement D-371 could not make from one row per column, and it
    is what demotes the scene axis: the columns separate as populations.
    """
    clearance = [aa.headroom(c, s) for c, s in aa.CALIBRATED if c == "clearance"]
    cte = [aa.headroom(c, s) for c, s in aa.CALIBRATED if c == "cte_max"]
    assert min(clearance) > 1.0 > max(cte)
    assert min(clearance) / max(cte) > 2.0


# --- D-372 finding #2: convoy is the controlled comparison -------------------


def test_convoy_is_the_only_scene_carrying_both_columns():
    assert aa.both_column_scenes() == ("cafe_convoy_v0",)


def test_the_same_scene_lands_on_opposite_sides_in_its_two_columns():
    """Scene, arms, operating point and seed set fixed; only the column varies.

    So the unreadability of the cross-track column cannot be a property of the
    scene — this scene's clearance signal is 5.14x its own noise.
    """
    assert aa.clears_floor("clearance", "cafe_convoy_v0", strict=True) is True
    assert aa.clears_floor("cte_max", "cafe_convoy_v0") is False
    assert aa.CONVOY_SPLIT == (
        ("clearance", 0.2704, 0.0526, 5.14),
        ("cte_max", 0.0633, 0.0659, 0.96),
    )


def test_convoy_split_rows_are_the_live_readings():
    for column, gap, p95, head in aa.CONVOY_SPLIT:
        assert aa.real_gap(column, "cafe_convoy_v0") == gap
        assert aa.p95_floor(column, "cafe_convoy_v0") == p95
        assert aa.headroom(column, "cafe_convoy_v0") == head


def test_ensemble_dispatches_on_column_before_scene():
    """Regression for the collision D-371's scene-keyed lookup would have hit."""
    assert aa._ensemble("clearance", "cafe_convoy_v0") is not aa._ensemble(
        "cte_max", "cafe_convoy_v0"
    )
    assert aa._ensemble("cte_max", "cafe_convoy_v0") is excursion_seed_width.SEED_ENSEMBLE[
        "cafe_convoy_v0"
    ]
    with pytest.raises(KeyError):
        aa._ensemble("no_such_column", "cafe_convoy_v0")


# --- D-372 finding #3: the head-on declaration is licensed -------------------


def test_head_on_clears_its_floor_and_discharges_the_hold():
    """`STATE.md` held user-blocked #2 one cycle because the scene had no floor.

    It has one now and it clears on both readings, so the bar interval D-368
    measured separates arms the harness can distinguish.
    """
    scene, gap, floor, head, clears = aa.HEAD_ON_DECLARATION
    assert scene == scene_transfer.HEAD_ON_SCENE
    assert aa.real_gap("clearance", scene) == gap
    assert aa.p95_floor("clearance", scene) == floor
    assert aa.headroom("clearance", scene) == head
    assert aa.clears_floor("clearance", scene, strict=True) is clears is True


def test_the_head_on_bar_interval_is_narrower_than_its_own_real_gap():
    """D-368's interval is (0.0043, 0.1044); the arms it cuts differ by 0.1781.

    The failure mode D-371 found on the `cte_max` bar is a bar wider than the
    signal it cuts. This one is not that.
    """
    width = round(0.1044 - 0.0043, 4)
    assert width < aa.real_gap("clearance", scene_transfer.HEAD_ON_SCENE)
    assert width > aa.p95_floor("clearance", scene_transfer.HEAD_ON_SCENE)


def test_the_two_clearance_sources_agree_on_the_shared_scene():
    """`clearance_census` and `scene_transfer` both hold `cafe_freezing_v0`.

    D-371 read it through the first and D-372 reads every clearance row through
    the second, so the calibration is only continuous if the two agree.
    """
    peak = clearance_census.PEAK_SCENE
    assert scene_transfer._COLUMNS[peak] == clearance_census.SEED_ENSEMBLE
    assert aa.FLOOR_VERDICT[("clearance", peak)] == (0.4606, 0.0733, 0.0800)


# --- finding #2 (D-371): D-370's refuting endpoints are below the floor ------


def test_both_robust_separation_endpoints_sit_below_their_scene_floor():
    assert aa.below_floor_endpoints() == aa.BOTH_BELOW_FLOOR
    assert len(aa.BOTH_BELOW_FLOOR) == 2


def test_endpoints_are_checked_against_the_scene_they_were_measured_on():
    """Not a pooled floor: each endpoint comes from a different scene, and the
    two floors differ by more than the gap D-370 reported between them."""
    exc, unexc = excursion_seed_width.ENDPOINTS
    scenes = [scene for _, scene, _ in aa.BOTH_BELOW_FLOOR]
    assert scenes == [exc, unexc]
    assert aa.max_floor("cte_max", exc) != aa.max_floor("cte_max", unexc)


def test_the_endpoint_values_are_d370s_and_not_a_local_copy():
    """Guards the finding against `ROBUST_SEPARATION` drifting away underneath."""
    lo, hi = excursion_seed_width.ROBUST_SEPARATION
    assert [v for v, _, _ in aa.BOTH_BELOW_FLOOR] == [lo, hi]


def test_d370s_inversion_gap_is_smaller_than_either_floor():
    """0.0730 - 0.0612 = 0.0118 against floors of 0.0673 and 0.0760 — the
    inversion is several times finer than the resolution that produced it."""
    lo, hi = excursion_seed_width.ROBUST_SEPARATION
    inversion = round(hi - lo, 4)
    assert inversion == 0.0118
    for _, scene, floor in aa.BOTH_BELOW_FLOOR:
        assert inversion < floor


# --- scope: what carries a floor and what does not ---------------------------


def test_calibration_covers_six_scenes_and_disclaims_the_rest():
    assert len(aa.calibrated_scenes()) == 6
    assert set(aa.calibrated_scenes()).isdisjoint(aa.UNCALIBRATED)


def test_the_uncalibrated_set_shrank_to_scenes_with_no_ensemble_at_all():
    """D-371 listed six; three of them had ensembles already on disk.

    What is left carries no seed ensemble in either harvest, so calibrating it
    would cost rollouts rather than arithmetic.
    """
    assert len(aa.UNCALIBRATED) == 3
    for scene in aa.UNCALIBRATED:
        assert scene not in scene_transfer._COLUMNS
        assert scene not in excursion_seed_width.SEED_ENSEMBLE


def test_uncalibrated_scenes_carry_no_floor():
    for scene in aa.UNCALIBRATED:
        with pytest.raises(KeyError):
            aa.max_floor("clearance", scene)


def test_every_clearance_ensemble_on_disk_is_calibrated():
    """The gap D-372 closed: the registry and the calibration are now equal.

    A new scene column added to `scene_transfer` re-opens this rather than
    leaving a stale count, which is the same shape as that module's own
    `test_the_column_registry_matches_measured_scenes`.
    """
    calibrated = {s for c, s in aa.CALIBRATED if c == "clearance"}
    assert calibrated == set(scene_transfer._COLUMNS)


def test_the_per_scene_answer_differs_by_more_than_4x_within_the_cte_column():
    """Islam et al.'s Half-Cheetah-vs-Hopper shape, reproduced here.

    Still true within a column — D-372 does not delete the per-scene spread, it
    shows the column axis dominates it.
    """
    convoy = aa.max_floor("cte_max", "cafe_convoy_v0") / aa.real_gap("cte_max", "cafe_convoy_v0")
    curved = aa.max_floor("cte_max", "city_curved_v0") / aa.real_gap("cte_max", "city_curved_v0")
    assert convoy == pytest.approx(1.06, abs=0.01)
    assert curved == pytest.approx(4.66, abs=0.01)


# --- finding #4: the re-priced debt -----------------------------------------


def test_resolution_debt_is_an_alternative_to_the_standing_debt_not_an_addition():
    """512 for 32 seeds on the binding pair, against 384 for six more scenes at
    eight — comparable price, and only one of them lowers the floor."""
    assert aa.RESOLUTION_DEBT == 8 * 32 * 2
    assert aa.RESOLUTION_DEBT > excursion_seed_width.REMAINING_DEBT
    assert aa.RESOLUTION_DEBT < 2 * excursion_seed_width.REMAINING_DEBT


def test_null_rms_matches_the_exact_permutation_identity():
    """`rms|mean(A)-mean(B)| == 2*sigma_pop/sqrt(n-1)` exactly, for every arm.

    This is the identity finding #4's scaling rests on, and it is exact rather
    than asymptotic because the split is a permutation of a fixed finite set,
    not a resample. Verifying it here is what makes the 8->32 projection a
    calculation instead of an extrapolation.
    """
    for column, scene in aa.CALIBRATED:
        for arm, row in aa._ensemble(column, scene).items():
            gaps = aa.null_gaps(row)
            rms = math.sqrt(sum(g * g for g in gaps) / len(gaps))
            expected = 2 * statistics.pstdev(row) / math.sqrt(len(row) - 1)
            assert rms == pytest.approx(expected, rel=1e-12), f"{column}/{scene}/{arm}"


def test_quadrupling_seeds_shrinks_the_floor_by_more_than_two():
    """8 -> 32 seeds shrinks the rms floor by sqrt(31/7) = 2.10x at fixed
    dispersion, so finding #4's 'halves' is the conservative statement."""
    shrink = math.sqrt((32 - 1) / (aa.SEEDS - 1))
    assert shrink == pytest.approx(2.104, abs=0.001)
    assert shrink > 2.0


# --- borrowed-method scope --------------------------------------------------


def test_verdict_is_symmetric_and_names_both_decisions():
    assert "D-363" in aa.VERDICT and "D-370" in aa.VERDICT
    assert "undecidable" in aa.VERDICT


def test_module_spends_no_rollouts():
    """Every input is an ensemble another cycle already paid for."""
    assert aa._ensemble("cte_max", "cafe_convoy_v0") is excursion_seed_width.SEED_ENSEMBLE[
        "cafe_convoy_v0"
    ]
    for scene in scene_transfer._COLUMNS:
        assert aa._ensemble("clearance", scene) is scene_transfer._COLUMNS[scene]
