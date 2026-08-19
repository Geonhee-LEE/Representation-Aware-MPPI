# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the A-A null calibration (Islam et al. 1708.04133, method only)."""

from __future__ import annotations

import math
import statistics

import pytest

from eval.mppi_sandbox import aa_calibration as aa
from eval.mppi_sandbox import clearance_census, excursion_seed_width


def test_no_drift_from_pins():
    assert aa.drift() == ()


def test_cli_exits_clean():
    assert aa.main([]) == 0


# --- the null construction itself -------------------------------------------


def test_split_count_is_the_whole_null_distribution():
    """C(8,4)/2 = 35 — enumerated, not sampled, so there is no sampling error."""
    assert aa.SPLITS == 35
    for scene in aa.calibrated_scenes():
        for row in aa._ensemble(scene).values():
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
    for scene in aa.calibrated_scenes():
        assert aa.p95_floor(scene) <= aa.max_floor(scene)


# --- finding #1: the calibration separates the two columns -------------------


def test_clearance_column_clears_its_null_on_both_readings():
    scene = clearance_census.PEAK_SCENE
    assert aa.clears_floor(scene) is True
    assert aa.clears_floor(scene, strict=True) is True
    assert aa.headroom(scene) > 6.0


@pytest.mark.parametrize("scene", ["cafe_convoy_v0", "city_curved_v0"])
def test_cross_track_column_clears_its_null_on_neither_reading(scene):
    assert aa.clears_floor(scene) is False
    assert aa.clears_floor(scene, strict=True) is False
    assert aa.headroom(scene) < 1.0


def test_the_excited_scene_is_the_thinner_margin_of_the_two_cte_scenes():
    """D-363 picked convoy because its arms differ most; relative to its own
    noise that advantage is worth 0.96x against curved's 0.35x — real, and not
    enough to cross the floor."""
    assert aa.headroom("cafe_convoy_v0") > aa.headroom("city_curved_v0")
    assert aa.headroom("cafe_convoy_v0") < 1.0


def test_floor_verdict_pins_match_the_live_readings():
    for scene, (gap, p95, mx) in aa.FLOOR_VERDICT.items():
        assert aa.real_gap(scene) == gap
        assert aa.p95_floor(scene) == p95
        assert aa.max_floor(scene) == mx


# --- finding #2: D-370's refuting endpoints are themselves below the floor ---


def test_both_robust_separation_endpoints_sit_below_their_scene_floor():
    assert aa.below_floor_endpoints() == aa.BOTH_BELOW_FLOOR
    assert len(aa.BOTH_BELOW_FLOOR) == 2


def test_endpoints_are_checked_against_the_scene_they_were_measured_on():
    """Not a pooled floor: each endpoint comes from a different scene, and the
    two floors differ by more than the gap D-370 reported between them."""
    exc, unexc = excursion_seed_width.ENDPOINTS
    scenes = [scene for _, scene, _ in aa.BOTH_BELOW_FLOOR]
    assert scenes == [exc, unexc]
    assert aa.max_floor(exc) != aa.max_floor(unexc)


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


# --- finding #3: per-scene, and it does not transfer -------------------------


def test_calibration_covers_three_scenes_and_disclaims_the_rest():
    assert len(aa.calibrated_scenes()) == 3
    assert set(aa.calibrated_scenes()).isdisjoint(aa.UNCALIBRATED)


def test_uncalibrated_scenes_carry_no_floor():
    for scene in aa.UNCALIBRATED:
        with pytest.raises(KeyError):
            aa.max_floor(scene)


def test_the_per_scene_answer_differs_by_more_than_4x():
    """Islam et al.'s Half-Cheetah-vs-Hopper shape, reproduced here."""
    convoy = aa.max_floor("cafe_convoy_v0") / aa.real_gap("cafe_convoy_v0")
    curved = aa.max_floor("city_curved_v0") / aa.real_gap("city_curved_v0")
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
    for scene in aa.calibrated_scenes():
        for arm, row in aa._ensemble(scene).items():
            gaps = aa.null_gaps(row)
            rms = math.sqrt(sum(g * g for g in gaps) / len(gaps))
            expected = 2 * statistics.pstdev(row) / math.sqrt(len(row) - 1)
            assert rms == pytest.approx(expected, rel=1e-12), f"{scene}/{arm}"


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
    assert aa._ensemble("cafe_convoy_v0") is excursion_seed_width.SEED_ENSEMBLE["cafe_convoy_v0"]
    assert aa._ensemble(clearance_census.PEAK_SCENE) is clearance_census.SEED_ENSEMBLE
