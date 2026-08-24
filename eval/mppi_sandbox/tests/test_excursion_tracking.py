# SPDX-License-Identifier: BSD-3-Clause
"""D-363: attained cross-track vs forced excursion — level, spread, residual."""

from __future__ import annotations

from eval.mppi_sandbox import (
    cte_peak_vacuity,
    excursion_tracking as et,
    obstacle_reach,
    path_curvature,
    scene_census as sc,
)


def test_census_matches_the_live_join():
    assert et.drift() == ()


def test_the_join_covers_every_harvested_scene():
    assert set(et.measure()) == set(cte_peak_vacuity.CTE_MAX_SEED0)
    # `obstacle_reach.CENSUS` is a static-yaml census, so a new scene joins it
    # for free; this join is keyed on *measured* columns and cannot follow
    # without rollouts. The gap is the pinned debt and nothing else — widening
    # `UNHARVESTED_SCENES` to pass this is forbidden (D-458(2)); buying the
    # column shrinks it.
    assert set(obstacle_reach.CENSUS) - set(et.measure()) == set(sc.UNHARVESTED_SCENES)


def test_forced_is_imported_not_recomputed():
    for scene, row in et.measure().items():
        assert row[0] == round(obstacle_reach.CENSUS[scene][1], 4), scene


def test_hi_is_never_below_lo():
    for scene, (_, hi, lo, spread) in et.measure().items():
        assert hi >= lo, scene
        assert abs((hi - lo) - spread) < 1e-9, scene


def test_the_partition_is_four_and_four():
    assert len(et.excited()) == 4
    assert len(et.unexcited()) == 4
    assert set(et.excited()) & set(et.unexcited()) == set()


def test_finding_1_forced_does_not_predict_the_level():
    """The `hi/forced` ratio spans >4x, so `forced` is not a scale factor."""
    rows = et.measure()
    ratios = [rows[s][1] / rows[s][0] for s in et.excited()]
    assert max(ratios) / min(ratios) > 4.0
    assert 0.40 < min(ratios) < 0.41
    assert 2.02 < max(ratios) < 2.03


def test_finding_1_convoy_is_the_scene_the_lower_bound_fails_on():
    assert et.under_forced() == et.UNDER_FORCED == ("cafe_convoy_v0",)
    forced, hi, _, _ = et.measure()["cafe_convoy_v0"]
    assert hi < forced
    assert forced / hi > 2.4


def test_finding_2_every_excited_scene_outspreads_every_unexcited_one():
    """n=16 ordered pairs, exhaustive over the 4x4 partition.

    Registered in `loop_reach.READING` — an empty filter on either side would
    make this vacuously true, which is exactly the reading it exists to deny.
    """
    rows = et.measure()
    pairs = 0
    for e in et.excited():
        for u in et.unexcited():
            assert rows[e][3] > rows[u][3], (e, u)
            pairs += 1
    assert pairs == 16


def test_finding_2_the_gap_is_pinned_and_has_no_overlap():
    lo_exc, hi_unexc = et.spread_gap()
    assert (lo_exc, hi_unexc) == et.SPREAD_SEPARATES
    assert lo_exc > hi_unexc
    assert lo_exc / hi_unexc > 1.9


def test_finding_3_obstacle_free_is_not_the_same_set_as_unexcited():
    """`cafe_freezing_v0` forces zero excursion while still having obstacles."""
    assert set(et.obstacle_free()) < set(et.unexcited())
    assert set(et.unexcited()) - set(et.obstacle_free()) == {"cafe_freezing_v0"}
    assert obstacle_reach.CENSUS["cafe_freezing_v0"][0] != float("inf")


def test_finding_3_level_is_monotone_in_curvature_with_nothing_to_avoid():
    floor = et.curvature_floor()
    assert floor == et.CURVATURE_SETS_THE_FLOOR
    ratios = [r for _, r, _ in floor]
    levels = [h for _, _, h in floor]
    assert ratios == sorted(ratios)
    assert levels == sorted(levels)
    assert max(levels) / min(levels) > 20.0


def test_finding_3_curved_attains_without_any_obstacle():
    """0.4583 m of peak cross-track bought purely by tracking lag."""
    forced, hi, _, _ = et.measure()["city_curved_v0"]
    assert forced == 0.0
    assert hi > 0.45
    assert hi / et.measure()["cafe_obstacle_crossing_v0"][0] > 0.9
    assert path_curvature.CENSUS["city_curved_v0"][2] == 0.733


def test_high_level_low_spread_names_the_trap():
    assert et.high_level_low_spread() == et.HIGH_LEVEL_LOW_SPREAD
    assert et.high_level_low_spread() == ("city_curved_v0",)
    rows = et.measure()
    assert rows["city_curved_v0"][1] > rows["cafe_convoy_v0"][1]
    assert rows["city_curved_v0"][3] < rows["cafe_convoy_v0"][3]


def test_the_scenes_state_proposes_barring_are_both_excited():
    for scene in ("cafe_cut_in_v0", "cafe_head_on_v0"):
        assert scene in et.excited(), scene
        assert scene in obstacle_reach.UNBARRED_EXCITED, scene


def test_seed_scope_is_declared():
    assert "seed0" in et.SEED_SCOPE
