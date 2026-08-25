# SPDX-License-Identifier: BSD-3-Clause
"""Q-148's two arms are separate channels, not two sides of one term."""

import numpy as np
import pytest

from eval.mppi_sandbox import channel_support as cs
from eval.mppi_sandbox import rollout_cloud as rc
from eval.mppi_sandbox import ratio_pick as rp


# --- the live-set primitive -------------------------------------------------

def test_live_mask_is_empty_on_a_flat_arm():
    mask, dev = cs.live_mask(np.full(10, 3.0))
    assert not mask.any()
    assert dev.max() == 0.0


def test_live_mask_is_deviation_from_min_not_from_zero():
    # An arm offset well away from zero is still flat everywhere but one point.
    cost = np.full(8, 5.0)
    cost[3] = 6.0
    mask, _ = cs.live_mask(cost)
    assert mask.sum() == 1 and mask[3]


def test_live_mask_is_scale_invariant():
    cost = np.array([0.0, 1.0, 0.0, 2.0])
    a, _ = cs.live_mask(cost)
    b, _ = cs.live_mask(cost * 1e4)
    assert np.array_equal(a, b)


# --- the geometry is the scene's, not the instrument's default --------------

def test_scene_radius_matches_the_radius_the_ab_runs_at():
    # D-261 picked the ratio at the scene's radius; if these two ever disagree
    # this module is measuring a different experiment than the one it argues on.
    assert cs.SCENE_RADIUS == rp.SCENE_RADIUS


def test_the_support_is_the_planner_cloud_not_the_grid():
    repel, _, _ = cs.arm_fields(cs.SCENE_RADIUS, seed=0)
    _, bev, _ = rc.scene(cs.SCENE_RADIUS)
    assert len(repel) == rc.matched_k(cs.SCENE_RADIUS, 13)
    # and it is genuinely the rollout cloud: the grid set at matched K differs.
    assert not np.array_equal(
        rc.rollout_points(bev, rc.matched_k(cs.SCENE_RADIUS, 13), 0),
        rc.grid_points(bev, 13))


# --- the measurement --------------------------------------------------------

@pytest.mark.parametrize("radius,n_repel,n_attract,n_both,n_union", [
    (0.3, 8, 271, 2, 277),
    (0.5, 6, 293, 0, 299),
    (1.0, 2, 314, 2, 314),
])
def test_live_set_counts_are_pinned(radius, n_repel, n_attract, n_both, n_union):
    r = cs.read(radius, seed=0)
    assert (r.n_repel_live, r.n_attract_live) == (n_repel, n_attract)
    assert (r.n_both_live, r.n_union_live) == (n_both, n_union)


@pytest.mark.parametrize("radius", [0.3, 0.5, 1.0])
def test_every_posed_radius_reads_channel_separated(radius):
    r = cs.read(radius, seed=0)
    assert r.verdict == cs.CHANNEL_SEPARATED
    assert r.jaccard <= cs.SEPARATED_MAX_JACCARD


def test_overlap_at_the_scene_radius_is_two_points_of_two_hundred_seventy_seven():
    r = cs.read(cs.SCENE_RADIUS, seed=0)
    assert r.n_both_live == 2
    assert r.jaccard == pytest.approx(2 / 277, rel=1e-9)


def test_the_repel_arm_lives_on_a_fiftieth_of_the_planner_support():
    # 8 of 316 at the scene radius: the mean the root's numerator is taken over
    # has a sample size of eight, which is the seed-spread mechanism D-257/D-258
    # measured without naming.
    r = cs.read(cs.SCENE_RADIUS, seed=0)
    assert r.k == 316
    assert r.n_repel_live == 8
    assert r.repel_live_fraction < 0.03


@pytest.mark.parametrize("radius", [0.3, 0.5, 1.0])
def test_the_repel_live_set_is_exactly_the_classify_exposed_partition(radius):
    # This is the load-bearing half: the root's numerator and denominator are
    # means over complementary point sets, so it cannot be a pointwise contest.
    r = cs.read(radius, seed=0)
    assert r.repel_live_is_exposed
    assert r.n_repel_live == r.n_exposed


def test_the_small_overlap_does_not_carry_the_attract_arms_force():
    # A count-based Jaccard could hide a two-point overlap that carries all the
    # mass. It does not: the shared points are ~0.1% of the attract arm's total.
    r = cs.read(cs.SCENE_RADIUS, seed=0)
    assert r.attract_mass_on_overlap < 0.01


# --- the predicates ---------------------------------------------------------

def test_survey_reads_separate_channels_and_a_between_region_rate():
    surveyed = cs.survey()
    assert cs.arms_are_separate_channels(surveyed)
    assert cs.root_is_a_between_region_rate(surveyed)


def test_an_empty_survey_is_not_a_vacuous_pass():
    assert not cs.arms_are_separate_channels({})
    assert not cs.root_is_a_between_region_rate({})


def test_unposed_cells_do_not_vote_either_way():
    posed = cs.read(cs.SCENE_RADIUS, seed=0)
    unposed = cs.SupportReading(
        radius=9.0, k=0, n_repel_live=0, n_attract_live=0, n_both_live=0,
        n_union_live=0, n_exposed=0, repel_mass_on_overlap=0.0,
        attract_mass_on_overlap=0.0, repel_live_is_exposed=False,
        verdict=cs.UNPOSED)
    assert cs.arms_are_separate_channels({0.3: posed, 9.0: unposed})
    # ...but a survey of nothing but UNPOSED cells still fails.
    assert not cs.arms_are_separate_channels({9.0: unposed})


def test_a_contended_reading_would_fail_the_predicate():
    # The predicate is falsifiable: a fabricated overlapping cell flips it.
    contended = cs.SupportReading(
        radius=0.3, k=316, n_repel_live=200, n_attract_live=200,
        n_both_live=180, n_union_live=220, n_exposed=200,
        repel_mass_on_overlap=0.9, attract_mass_on_overlap=0.9,
        repel_live_is_exposed=True, verdict=cs.POINTWISE_CONTENDED)
    assert contended.jaccard >= cs.CONTENDED_MIN_JACCARD
    assert not cs.arms_are_separate_channels({0.3: contended})


# --- the seed band: what survives, and what does not ------------------------

def test_the_per_seed_verdict_is_threshold_fragile_seven_of_eight():
    # Pinned as measured, not as wanted: seed 3 reads PARTIAL at jaccard
    # 0.0565, just over the 0.05 constant. Retuning the threshold to reach 8/8
    # would be choosing the constant to fit the finding.
    band = cs.seed_band(cs.SCENE_RADIUS)
    assert (band.n_separated, band.n_seeds) == (7, 8)
    assert band.jaccard_hi == pytest.approx(0.0565, abs=5e-4)
    assert band.jaccard_hi > cs.SEPARATED_MAX_JACCARD


def test_what_survives_every_seed_is_the_exposed_partition_identity():
    band = cs.seed_band(cs.SCENE_RADIUS)
    assert band.exposed_match_all
    assert band.jaccard_hi <= cs.SEED_ROBUST_MAX_JACCARD
    assert cs.separation_survives_seeds(band)


def test_the_repel_live_count_itself_swings_five_fold_across_seeds():
    # 8 .. 42 of 316. The root's numerator is a mean whose sample size is not
    # merely small but seed-dependent — the band-width mechanism, stated.
    band = cs.seed_band(cs.SCENE_RADIUS)
    assert (band.n_repel_lo, band.n_repel_hi) == (8, 42)
    assert band.repel_count_spread > 5.0


def test_separation_survives_seeds_is_falsifiable():
    overlapping = cs.SeedBand(
        radius=0.3, jaccard_lo=0.4, jaccard_hi=0.6, n_repel_lo=100,
        n_repel_hi=110, n_separated=0, n_seeds=8, exposed_match_all=True)
    assert not cs.separation_survives_seeds(overlapping)
    misaligned = cs.SeedBand(
        radius=0.3, jaccard_lo=0.001, jaccard_hi=0.01, n_repel_lo=8,
        n_repel_hi=42, n_separated=8, n_seeds=8, exposed_match_all=False)
    assert not cs.separation_survives_seeds(misaligned)
