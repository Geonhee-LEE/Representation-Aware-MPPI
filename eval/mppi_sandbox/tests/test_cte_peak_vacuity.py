# SPDX-License-Identifier: BSD-3-Clause
"""The `cte_max` (peak) vacuity sweep — STATE #1c, the column D-358 left unswept.

The load-bearing assertion here is a **negative**: :data:`RMS_BLIND` is empty.
D-358's five vacuous cross-track cells had an obvious cheap repair — *maybe the
RMS statistic is washing out the excursion, so read the peak instead* — and
these tests pin that the repair does not work. If a future change makes the peak
bar grade a scene the RMS bar could not, `test_peak_buys_no_new_graded_cell`
goes red, which is the honest signal that finding #1 has been overturned.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import cte_peak_vacuity as cpv
from eval.mppi_sandbox import cte_vacuity as cv


def test_no_drift_from_census():
    """Every pinned grade, tension row, and the RMS-blind set still derive."""
    assert cpv.drift() == ()


def test_module_cli_is_green():
    assert cpv.main() == 0


def test_sweep_covers_the_same_scenes_as_the_rms_column():
    """Both columns read the same 64 rollouts, so they must span the same scenes.

    A scene present in one and absent from the other would mean the two sweeps
    are describing different populations, which is exactly the error D-357
    finding #2 caught its own instrument committing.
    """
    assert sorted(cpv.CTE_MAX_SEED0) == sorted(cv.CTE_SEED0)
    for scene, col in cpv.CTE_MAX_SEED0.items():
        assert sorted(col) == sorted(cv.CTE_SEED0[scene]), scene


def test_peak_is_never_below_rms_on_the_same_trajectory():
    """`max |cte| >= rms |cte|` identically — a floor on the harvested numbers.

    This is the one relation between the two columns that holds by arithmetic
    rather than by measurement, so violating it means a harvest read the wrong
    metric key, not that a controller changed.
    """
    for scene, col in cpv.CTE_MAX_SEED0.items():
        for arm, peak in col.items():
            assert peak >= cv.CTE_SEED0[scene][arm] - 1e-9, f"{scene}/{arm}"


def test_peak_buys_no_new_graded_cell():
    """**Finding #1.** No scene is vacuous on RMS and discriminating on peak.

    The whole point of buying this column was to find out whether the D-358
    vacuity is a property of the *statistic* or of the *scenes*. It is the
    scenes: swapping RMS for peak moves nothing.
    """
    assert cpv.rms_blind() == ()
    assert cpv.RMS_BLIND == ()


def test_the_two_columns_agree_scene_by_scene_where_both_declare():
    """Same partition, not merely the same count of vacuous cells."""
    both = [s for s in cpv.CTE_MAX_SEED0
            if cpv.declared_thresholds().get(s) is not None
            and cv.declared_thresholds().get(s) is not None]
    assert both, "no scene declares both bars — the comparison would be vacuous"
    for scene in both:
        assert cpv.grade_scene(scene).grade == cv.grade_scene(scene).grade, scene


def test_obstacle_crossing_is_the_only_discriminating_scene():
    """And `cbf_mppi` is the only arm over the line, by `0.0272 m`."""
    graded = {v.scene: v.grade for v in cpv.sweep()}
    assert [s for s, g in graded.items() if g == "DISCRIMINATING"] == \
        ["cafe_obstacle_crossing_v0"]
    assert cpv.failing_arms("cafe_obstacle_crossing_v0") == ("cbf_mppi",)


def test_four_scenes_declare_no_peak_bar_at_all():
    """D-357 finding #3's shape again: an undeclared key cannot be vacuous."""
    undeclared = tuple(v.scene for v in cpv.sweep() if v.grade == "UNDECLARED")
    assert undeclared == ("cafe_convoy_v0", "cafe_cut_in_v0",
                          "cafe_freezing_v0", "cafe_head_on_v0")
    # The branch's headline scenes are both in there — the column is silent
    # exactly where D-352/D-353 took their numbers.
    assert "cafe_convoy_v0" in undeclared


def test_headroom_orders_curved_below_straight_on_both_statistics():
    """**Finding #2.** Curvature ordering, and it must hold on *both* columns.

    A single column showing this ordering could be a coincidence of three
    numbers; the same monotone ordering on two different statistics of the same
    trajectories is the corroboration the feed's Nav2 #5925 mechanism predicts.
    """
    peak = cpv.headroom()
    assert list(peak) == ["city_curved_v0", "city_figure8_v0", "cafe_straight_v0"]

    rms = {}
    for v in cv.sweep():
        if v.grade == "VACUOUS_PASS" and v.declared is not None and v.hi:
            rms[v.scene] = v.declared / v.hi
    for scene in peak:
        assert scene in rms, f"{scene} vacuous on peak but not on RMS"
    assert rms["city_curved_v0"] < rms["city_figure8_v0"]
    assert rms["city_curved_v0"] < rms["cafe_straight_v0"]


def test_curvature_gap_is_named_not_silently_left_open():
    """Finding #2 is corroboration, not a test — the module must say so."""
    assert "curvature radius" in cpv.CURVATURE_UNMEASURED
    assert "horizon" in cpv.CURVATURE_UNMEASURED


def test_declared_thresholds_are_derived_from_disk_not_restated():
    """D-047: a hand-typed copy of a registry that later grows is the defect."""
    declared = cpv.declared_thresholds()
    assert declared["cafe_straight_v0"] == pytest.approx(0.5)
    assert declared["city_curved_v0"] == pytest.approx(1.0)
    assert "cafe_convoy_v0" not in declared


def test_grade_scene_accepts_an_injected_population():
    """The ceiling comparison, exercised on both sides without new rollouts."""
    assert cpv.grade_scene("cafe_straight_v0", {"a": 9.0}).grade == "VACUOUS_FAIL"
    assert cpv.grade_scene("cafe_straight_v0", {"a": 0.01}).grade == "VACUOUS_PASS"
    assert cpv.grade_scene("cafe_straight_v0",
                           {"a": 0.01, "b": 9.0}).grade == "DISCRIMINATING"
    assert cpv.grade_scene("cafe_straight_v0", {}).grade == "UNMEASURABLE"


def test_widening_cost_matches_the_rms_columns():
    """Both sweeps decline the same 8x8x7 purchase; the constants must agree."""
    assert cpv.WIDENING_UNBOUGHT == cv.WIDENING_UNBOUGHT == 8 * 8 * 7
