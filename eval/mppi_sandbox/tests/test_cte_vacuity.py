# SPDX-License-Identifier: BSD-3-Clause
"""The 경로추종 column of the acceptance matrix, and whether it can fail."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import cte_vacuity as cv
from eval.mppi_sandbox import threshold_vacuity as tv


def test_census_matches_the_scenarios_on_disk():
    assert cv.drift() == ()


def test_every_shipped_scene_is_graded():
    assert set(cv.CENSUS) == set(cv.CTE_SEED0)
    assert set(cv.CENSUS) == set(cv.declared_thresholds())


def test_majority_of_scenes_cannot_fail_their_cross_track_bar():
    """Finding #1 — five of eight, not one."""
    vacuous = [v.scene for v in cv.sweep() if v.grade == "VACUOUS_PASS"]
    assert len(vacuous) == 5
    for scene in vacuous:
        declared = cv.declared_thresholds()[scene]
        worst = max(cv.CTE_SEED0[scene].values())
        assert worst <= declared, f"{scene} worst arm {worst} exceeds {declared}"
        assert cv.failing_arms(scene) == ()


def test_straight_declares_a_bar_twenty_times_the_worst_arm():
    """The most extreme cell, quoted in the docstring — kept honest here."""
    worst = max(cv.CTE_SEED0["cafe_straight_v0"].values())
    assert cv.declared_thresholds()["cafe_straight_v0"] == pytest.approx(0.20)
    assert worst == pytest.approx(0.0088, abs=5e-5)
    assert 0.20 / worst > 20


def test_vacuity_direction_is_inverted_relative_to_clearance():
    """Finding #2 — a ceiling and a floor put vacuity on opposite sides.

    The same numeric relation (`declared` above the attained range) is
    `VACUOUS_PASS` here and `VACUOUS_FAIL` in the clearance module. This is the
    asymmetry a shared generic helper would have hidden.
    """
    above = {"a": 0.1, "b": 0.2}      # declared sits above the whole range
    below = {"a": 5.0, "b": 6.0}      # declared sits below the whole range
    scene = "cafe_straight_v0"        # declares 0.20 for cte, no clearance key
    assert cv.grade_scene(scene, above).grade == "VACUOUS_PASS"
    assert cv.grade_scene(scene, below).grade == "VACUOUS_FAIL"

    # ...and the clearance module reads the mirror image on its own key.
    head_on = "cafe_head_on_v0"       # declares 0.40 clearance
    assert tv.grade_scene(head_on, {"a": 0.1, "b": 0.2}).grade == "VACUOUS_FAIL"
    assert tv.grade_scene(head_on, {"a": 5.0, "b": 6.0}).grade == "VACUOUS_PASS"


def test_no_scene_is_vacuous_fail_on_cross_track():
    """The dangerous direction here is the *passing* one; record that none of
    the eight fails closed, so finding #2's claim is about a real population."""
    assert [v.scene for v in cv.sweep() if v.grade == "VACUOUS_FAIL"] == []


def test_the_clearance_winner_is_the_cross_track_loser():
    """Finding #3 — `cbf_mppi` fails the most scenes on the tracking half."""
    assert cv.tension() == cv.CLEARANCE_TENSION
    assert cv.CLEARANCE_TENSION["cbf_mppi"] == (
        "cafe_head_on_v0", "cafe_obstacle_crossing_v0")
    # It fails strictly more scenes than any other arm.
    counts = {a: len(s) for a, s in cv.tension().items()}
    assert counts["cbf_mppi"] == max(counts.values())
    assert sorted(counts, key=lambda a: -counts[a])[0] == "cbf_mppi"


def test_grade_boundaries_are_closed_on_the_non_discriminating_side():
    """`declared == hi` cannot fail (<= is the acceptance test), so it is
    vacuous, not discriminating — the boundary that decides four of the five."""
    scene = "cafe_straight_v0"
    declared = cv.declared_thresholds()[scene]
    assert cv.grade_scene(scene, {"a": declared, "b": 0.0}).grade == "VACUOUS_PASS"
    # One arm a hair over the bar, one under: the bar now separates them.
    assert cv.grade_scene(
        scene, {"a": declared + 1e-9, "b": 0.0}).grade == "DISCRIMINATING"
    # ...whereas a population entirely over the bar is the other vacuity, not
    # discrimination — `lo == hi` collapses the range and nothing can pass.
    assert cv.grade_scene(scene, {"a": declared + 1e-9}).grade == "VACUOUS_FAIL"


def test_seed_zero_range_can_only_over_report_vacuity():
    """Widening the population can only move a scene toward DISCRIMINATING.

    Stated as a property because it is what licenses shipping a seed-0 reading
    without the 448 rollouts :data:`WIDENING_UNBOUGHT` prices.
    """
    for v in cv.sweep():
        if v.grade != "VACUOUS_PASS":
            continue
        widened = dict(cv.CTE_SEED0[v.scene])
        widened["hypothetical_seed"] = v.declared + 0.01
        assert cv.grade_scene(v.scene, widened).grade == "DISCRIMINATING"


def test_unswept_keys_are_derived_not_typed():
    from eval.mppi_sandbox import cte_peak_vacuity as cpv

    assert cv.unswept_key_gap() == cv.UNSWEPT_KEYS
    assert cv.SWEPT_KEY not in cv.UNSWEPT_KEYS
    assert tv.SWEPT_KEY not in cv.UNSWEPT_KEYS
    # Two modules have since closed two of the sibling's declared gaps: this
    # one's `cte_rms_max` and `cte_peak_vacuity`'s `cte_max` (STATE #1c).
    assert set(tv.UNSWEPT_KEYS) - set(cv.UNSWEPT_KEYS) == {
        cv.SWEPT_KEY, cpv.SWEPT_KEY}


def test_cte_max_gap_is_closed_and_bought_nothing():
    """The column this module named as cheapest-next has been swept.

    D-358 left `cte_max` in :data:`cte_vacuity.UNSWEPT_KEYS` as the cheapest
    remaining column. It has been taken, and the result was a negative — the
    peak bar grades the same partition — so the gap closes without any vacuous
    cell moving. Both halves are pinned: the key is gone from the census, and
    this module's own five vacuous scenes are unchanged.
    """
    from eval.mppi_sandbox import cte_peak_vacuity as cpv

    assert "cte_max" not in cv.UNSWEPT_KEYS
    assert cpv.SWEPT_KEY == "cte_max"
    assert cpv.RMS_BLIND == ()
    assert sum(1 for v in cv.sweep() if v.grade == "VACUOUS_PASS") == 5
    assert cv.WIDENING_UNBOUGHT == 448
