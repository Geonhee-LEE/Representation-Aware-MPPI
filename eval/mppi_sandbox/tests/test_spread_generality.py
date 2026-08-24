# SPDX-License-Identifier: BSD-3-Clause
"""Pins for :mod:`eval.mppi_sandbox.spread_generality` (D-365).

The findings are a *refutation*: arm spread explains cross-track vacuity
(D-363) and does **not** explain clearance vacuity. These pins hold the
refutation's two load-bearing comparisons — the clearance spread floor, and the
vacuous-wider-than-grading pair — so a later harvest that moves either one
fails here rather than silently restoring the generalisation.
"""

from __future__ import annotations

from eval.mppi_sandbox import (
    excursion_tracking,
    scene_census,
    spread_generality,
    threshold_vacuity,
)


def test_census_matches_the_measured_join() -> None:
    assert spread_generality.measure() == spread_generality.CENSUS


def test_main_reports_no_drift() -> None:
    assert spread_generality.main() == 0


def test_clearance_has_no_narrow_spread_scene() -> None:
    """Finding #1: no clearance scene reaches the cross-track vacuous band."""
    assert spread_generality.spread_floor() == spread_generality.CLEARANCE_SPREAD_FLOOR
    # The cross-track column's vacuous cells spread at most 0.0730 (D-363).
    cross_track_vacuous_max = excursion_tracking.SPREAD_SEPARATES[1]
    assert spread_generality.CLEARANCE_SPREAD_FLOOR > cross_track_vacuous_max


def test_spread_is_necessary_but_not_sufficient() -> None:
    """Finding #2: the vacuous scene spreads wider than a grading one."""
    vac_scene, vac_spread, grading_scene, grading_spread = (
        spread_generality.SPREAD_NOT_SUFFICIENT
    )
    assert vac_spread > grading_spread
    assert spread_generality.CENSUS[vac_scene][2] == vac_spread
    assert spread_generality.CENSUS[vac_scene][4] == "VACUOUS_FAIL"
    # The comparator is the narrowest *excited* cross-track scene (D-363).
    assert excursion_tracking.CENSUS[grading_scene][3] == grading_spread


def test_the_vacuous_clearance_scene_is_a_placement_failure() -> None:
    """Finding #3: the bar sits above the whole attained range, not inside it."""
    for scene in spread_generality.REPAIRABLE_BY_PLACEMENT:
        lo, hi, spread, _cte, verdict = spread_generality.CENSUS[scene]
        assert verdict == "VACUOUS_FAIL"
        assert round(hi - lo, 4) == spread
        # A width failure would be a narrow spread; this one is not narrow.
        assert spread > excursion_tracking.SPREAD_SEPARATES[1]


def test_vacuous_set_agrees_with_the_clearance_census() -> None:
    got = spread_generality.vacuous()
    assert got == spread_generality.REPAIRABLE_BY_PLACEMENT
    for scene in got:
        assert threshold_vacuity.CENSUS[scene] == "VACUOUS_FAIL"


def test_both_channels_silent_scene_is_excited_on_cross_track() -> None:
    """Finding #4: dispersion on both channels, grading on neither."""
    for scene in spread_generality.BOTH_CHANNELS_SILENT:
        assert scene in spread_generality.vacuous()
        # Excited on cross-track means forced excursion > 0 (D-363).
        assert scene in excursion_tracking.excited()
        # ...yet it declares no cte_max key at all (D-362).
        assert scene not in excursion_tracking.CURVATURE_SETS_THE_FLOOR[0]


def test_excluded_scenes_are_dropped_by_one_of_two_named_mechanisms() -> None:
    """The dropped scenes are dropped by a property, not by a label (D-330).

    `measure` filters on the operands themselves rather than on a verdict
    allow-list. This pins that the exclusions partition into exactly the two
    mechanisms `measure` implements, with nothing excused out on a third.

    Until the 9th scene there was one mechanism — no attained range at all —
    and this test asserted it as *the* rule (D-459). `cafe_obstacle_contested_v0`
    landed with a measured clearance column and no cross-track column, so a
    proposition that was true of every scene on disk started failing on a join
    that was behaving correctly. Same shape as D-458's excite finding: a
    one-mechanism claim survives only until a scene arrives that splits it.
    """
    excluded = set(threshold_vacuity.CENSUS) - set(spread_generality.CENSUS)

    # (a) no attained clearance range at all — nothing to join on either side.
    no_range = {"cafe_freezing_v0", "cafe_straight_v0", "city_curved_v0", "city_figure8_v0"}
    # (b) clearance harvested, cross-track owed — half a join (D-458(2)).
    half_harvested = set(scene_census.UNHARVESTED_SCENES) & set(threshold_vacuity.CENSUS)

    assert excluded == no_range | half_harvested
    assert no_range & half_harvested == set(), "a scene cannot be dropped by both"

    for scene in no_range:
        col = scene_census.SCENE_SEED0.get(scene, {})
        assert [v for v in col.values() if v is not None] == [], scene

    for scene in half_harvested:
        # The distinguishing property: this one *does* carry clearances. It is
        # excluded for the missing operand, not for an empty column.
        col = scene_census.SCENE_SEED0.get(scene, {})
        assert [v for v in col.values() if v is not None] != [], scene
        assert scene not in excursion_tracking.measure(), scene
