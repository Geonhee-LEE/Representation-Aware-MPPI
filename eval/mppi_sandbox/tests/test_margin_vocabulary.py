# SPDX-License-Identifier: BSD-3-Clause
"""The declared margin vocabulary meets `cafe_freezing_v0`'s window in one point."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import declaration_gap, margin_vocabulary, threshold_vacuity
from eval.mppi_sandbox.clearance_census import SEED_ENSEMBLE
from eval.mppi_sandbox.margin_vocabulary import (
    CEILING,
    FLOOR,
    FORCED,
    INTERIOR,
)


def test_vocabulary_is_derived_from_the_scenarios_not_typed():
    """The membership must come off disk — D-413's lesson, applied up front."""
    derived = margin_vocabulary.vocabulary()
    declared = threshold_vacuity.declared_thresholds()
    assert set(derived) == {round(float(m), 4) for m in declared.values()}
    # every declaring scene appears exactly once, under its own value
    flat = [s for scenes in derived.values() for s in scenes]
    assert sorted(flat) == sorted(declared)


def test_target_scene_declares_nothing_so_cannot_be_its_own_precedent():
    assert margin_vocabulary.SCENE not in threshold_vacuity.declared_thresholds()
    for scenes in margin_vocabulary.vocabulary().values():
        assert margin_vocabulary.SCENE not in scenes


def test_vocabulary_matches_the_pin():
    assert margin_vocabulary.vocabulary() == margin_vocabulary.PRECEDENT


def test_grades_match_the_pin():
    assert margin_vocabulary.graded_vocabulary() == margin_vocabulary.GRADES


def test_030_is_a_floor_every_cell_clears():
    """The FLOOR grade is the claim that the bar tests nothing — check it."""
    assert margin_vocabulary.grade(0.30) == FLOOR
    cells = [v for row in SEED_ENSEMBLE.values() for v in row]
    assert all(v > 0.30 for v in cells), "0.30 must be vacuous on this scene"
    assert declaration_gap.straddling_arms(0.30) == ()


def test_040_is_interior_and_actually_cuts_the_population():
    assert margin_vocabulary.grade(0.40) == INTERIOR
    cells = [v for row in SEED_ENSEMBLE.values() for v in row]
    assert 0 < sum(v < 0.40 for v in cells) < len(cells), "must cut, not sweep"
    assert declaration_gap.straddling_arms(0.40) != ()


def test_interiority_is_strict_at_both_endpoints():
    """A bar on an endpoint does not cut the seed that attains it."""
    lo, hi = declaration_gap.common_window()
    assert margin_vocabulary.grade(lo) == FLOOR
    assert margin_vocabulary.grade(hi) == CEILING
    assert margin_vocabulary.grade((lo + hi) / 2) == INTERIOR


def test_ceiling_grade_is_reachable_even_though_the_vocabulary_omits_it():
    """CEILING is a named outcome, not a dead branch."""
    _, hi = declaration_gap.common_window()
    assert margin_vocabulary.grade(hi + 0.1) == CEILING
    assert CEILING not in margin_vocabulary.graded_vocabulary().values()


def test_verdict_is_forced_by_exactly_one_interior_value():
    assert margin_vocabulary.interior_values() == (0.40,)
    assert margin_vocabulary.verdict() == FORCED == margin_vocabulary.VERDICT


@pytest.mark.parametrize(
    "extra, expected",
    [
        ({}, margin_vocabulary.FORCED),
        ({"scene_x": 0.50}, margin_vocabulary.AMBIGUOUS),  # a 2nd interior value
        ({"scene_x": 0.10}, margin_vocabulary.FORCED),  # another floor changes nothing
    ],
)
def test_verdict_responds_to_a_new_declaration(monkeypatch, extra, expected):
    """A fifth scene declaring a value must move the verdict, not be absorbed."""
    base = dict(threshold_vacuity.declared_thresholds())
    base.update(extra)
    monkeypatch.setattr(threshold_vacuity, "declared_thresholds", lambda: base)
    assert margin_vocabulary.verdict() == expected


def test_no_precedent_is_reachable_when_every_declared_value_is_vacuous(monkeypatch):
    monkeypatch.setattr(
        threshold_vacuity, "declared_thresholds", lambda: {"scene_x": 0.10}
    )
    assert margin_vocabulary.verdict() == margin_vocabulary.NO_PRECEDENT


def test_drift_is_empty_and_cli_is_green():
    assert margin_vocabulary.drift() == ()
    assert margin_vocabulary.main() == 0


def test_drift_convicts_when_a_pin_disagrees(monkeypatch):
    monkeypatch.setattr(margin_vocabulary, "VERDICT", "SOMETHING_ELSE")
    assert margin_vocabulary.drift() != ()
    assert margin_vocabulary.main() == 1
