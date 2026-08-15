"""`lam = 1.2`'s non-monotone rise is seed 0's, not the sampler's (D-288)."""

import pytest

from eval.mppi_sandbox.calibrated_ladder import (
    MEASURED_LAM12_RISE,
    RISE_SAMPLER_SHAPE,
    RISE_SEED_ARTEFACT,
    RISE_UNATTRIBUTED,
    Point,
    rise_attribution,
)


def test_rise_is_attributed_to_seed_zero():
    got = rise_attribution()
    assert got["verdict"] == RISE_SEED_ARTEFACT
    assert got["rise_seeds"] == (0,)
    assert got["fall_seeds"] == (1, 2)


def test_every_seed_is_walked_at_both_rungs():
    """D-019: a 3-seed rung may not be read against a 1-seed one."""
    got = rise_attribution()
    assert got["n_seeds"] == 3
    for seed, per in got["per_seed_ess"].items():
        assert set(per) == {8.0, 12.0}, seed


def test_the_loose_rung_is_the_left_hand_one():
    """The argument: the outlier is seed 0's `w = 8`, not anybody's `w = 12`."""
    got = rise_attribution()
    assert got["looser_rung"] == 8.0
    assert got["spread"][8.0] > got["spread"][12.0]
    assert got["spread"][8.0] == pytest.approx(3.7029, abs=1e-3)
    assert got["spread"][12.0] == pytest.approx(1.5915, abs=1e-3)


def test_the_two_falling_seeds_fall_by_the_same_factor():
    """Near-identical decay is why this reads as noise rather than shape."""
    per = rise_attribution()["per_seed_ess"]
    ratios = [per[s][12.0] / per[s][8.0] for s in (1, 2)]
    assert ratios[0] == pytest.approx(ratios[1], abs=0.03)
    assert all(r < 1.0 for r in ratios)


def test_withholding_is_re_founded_not_lifted():
    """The added seeds make `CROSSING_NON_MONOTONE` better-founded, not removable."""
    got = rise_attribution()
    assert got["reinstates_trend"] is False
    assert got["withholding_still_correct"] is True
    # D-019's conjunction is unmet at *both* rungs — seed 1 alone is in band.
    assert got["conjunction_met"] == {8.0: False, 12.0: False}
    assert got["in_band_seeds"][8.0] == (1,)
    assert got["in_band_seeds"][12.0] == ()


def test_scope_is_not_widened():
    got = rise_attribution()
    assert got["scene"] == "cafe_freezing_v0"
    assert got["transfers_to_ab_scene"] is False


@pytest.mark.parametrize("built,expected", [
    (((8.0, 1.0, 0), (12.0, 2.0, 0), (8.0, 1.0, 1), (12.0, 2.0, 1)),
     RISE_SAMPLER_SHAPE),
    (((8.0, 2.0, 0), (12.0, 1.0, 0), (8.0, 2.0, 1), (12.0, 1.0, 1)),
     RISE_SEED_ARTEFACT),
    (((8.0, 1.0, 0), (12.0, 2.0, 0)), RISE_UNATTRIBUTED),
    (((8.0, 1.0, 0), (12.0, 2.0, 0), (8.0, 2.0, 1), (12.0, 1.0, 1)),
     RISE_UNATTRIBUTED),
])
def test_verdict_vocabulary_is_reachable(built, expected):
    """Each verdict is earned by some ladder — no vocabulary that never fires."""
    rows = tuple(
        Point(lam=1.2, weight=w, median_ess=e, n_samples=256,
              ratio=None, reached_goal=True, seed=s)
        for w, e, s in built
    )
    assert rise_attribution(rows)["verdict"] == expected


def test_measured_table_carries_both_rungs_for_each_seed():
    seen = {}
    for p in MEASURED_LAM12_RISE:
        seen.setdefault(p.seed, set()).add(p.weight)
    assert seen == {0: {8.0, 12.0}, 1: {8.0, 12.0}, 2: {8.0, 12.0}}
