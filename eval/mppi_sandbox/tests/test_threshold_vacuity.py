# SPDX-License-Identifier: BSD-3-Clause
"""Pins for :mod:`eval.mppi_sandbox.threshold_vacuity` (STATE #1 / D-357)."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import threshold_vacuity as tv
from eval.mppi_sandbox.scene_census import SCENE_OBSTACLES


def test_census_matches_the_scenarios_on_disk():
    """The whole point: a scene changing verdict fails here, not in a later grep."""
    assert tv.drift() == ()


def test_every_shipped_scene_is_graded():
    assert {v.scene for v in tv.sweep()} == set(SCENE_OBSTACLES)
    assert set(tv.CENSUS) == set(SCENE_OBSTACLES)


def test_head_on_threshold_cannot_be_passed_by_any_arm():
    """Finding #1 — vacuity in the *failing* direction, 8/8 arms below `0.40`."""
    v = tv.grade_scene("cafe_head_on_v0")
    assert v.grade == "VACUOUS_FAIL"
    assert v.declared == 0.40
    assert v.hi == pytest.approx(0.2003)
    col = tv.attained("cafe_head_on_v0")
    assert sum(c >= v.declared for c in col.values()) == 0
    assert len(col) == 8


def test_convoy_vacuity_is_population_scoped_not_scene_scoped():
    """Finding #2 — D-356's verdict is about its arm pair, not about the scene."""
    scene, arms, pair_grade = tv.HEADLINE_PAIR
    col = tv.attained(scene)
    assert tv.grade_scene(scene, {a: col[a] for a in arms}).grade == pair_grade
    assert tv.grade_scene(scene).grade == "DISCRIMINATING"
    # the arm that discriminates is the one the headline pair excluded
    assert col["essps_mppi"] < tv.declared_thresholds()[scene]


def test_freezing_declares_no_clearance_threshold_despite_obstacles():
    """Finding #3 — `acceptance_coverage` cannot see a key nobody declared."""
    assert SCENE_OBSTACLES["cafe_freezing_v0"] == 2
    assert "cafe_freezing_v0" not in tv.declared_thresholds()
    assert tv.grade_scene("cafe_freezing_v0").grade == "UNDECLARED"


def test_obstacle_free_scenes_are_undefined_not_vacuous():
    """`+inf` clearance is not a passing grade — the question is not posed."""
    for scene, n in SCENE_OBSTACLES.items():
        if n == 0:
            assert tv.attained(scene) == {}
            assert tv.grade_scene(scene).grade == "UNMEASURABLE"


def test_widening_compares_the_same_arms():
    """The instrument must not commit the error it reports (finding #2)."""
    for scene, (narrow, wide) in tv.widened().items():
        assert narrow == wide, f"{scene} moved on seeds alone: {narrow} -> {wide}"


def test_unswept_keys_are_derived_not_typed():
    """D-047: the blind spot is a measured constant, not a docstring sentence."""
    assert tv.UNSWEPT_KEYS == tv.undeclared_key_gap()
    assert tv.SWEPT_KEY not in tv.UNSWEPT_KEYS


def test_grade_boundaries_are_closed_on_the_passing_side():
    """`declared <= lo` is vacuous-pass: the checker uses `clearance >= v`."""
    col = {"a": 0.30, "b": 0.50}
    assert tv.grade_scene("cafe_convoy_v0", col).grade == "VACUOUS_PASS"
    assert tv.grade_scene("cafe_cut_in_v0", {"a": 0.20, "b": 0.29}).grade \
        == "VACUOUS_FAIL"
