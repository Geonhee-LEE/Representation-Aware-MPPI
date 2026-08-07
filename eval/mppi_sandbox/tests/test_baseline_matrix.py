# SPDX-License-Identifier: BSD-3-Clause
"""P5 baseline matrix: the admissibility ladder and the two-axis headline.

Scene choice is load-bearing: every test here runs on `cafe_straight` (0.29 s
per seed) or `cafe_head_on` (0.44 s), never on `city_*` (14.4 s). The ladder
and the headline are pure functions of `SweepStats`, so the *grading* logic is
tested on synthetic cells and only the two integration tests pay for a sim.
"""

from __future__ import annotations

import math

import pytest

from eval.mppi_sandbox.ab import SweepStats
from eval.mppi_sandbox.baseline_matrix import (
    ESS_OUT_OF_BAND,
    ESS_UNKNOWN,
    NO_OBSTACLES,
    NOT_REACHED,
    OK,
    Cell,
    Matrix,
    _status,
    default_scenarios,
    run_cell,
)

STRAIGHT = "eval/scenarios/cafe_straight_v0.yaml"
HEAD_ON = "eval/scenarios/cafe_head_on_v0.yaml"


def _stats(*, all_reached=True, ess_in_band=True, collisions=0,
           min_clearance=0.5, n=2) -> SweepStats:
    return SweepStats(
        n=n, collisions=collisions,
        collision_rate=collisions / n, mean_clearance=min_clearance,
        median_clearance=min_clearance, min_clearance=min_clearance,
        mean_speed=0.4, all_reached=all_reached,
        median_ess=20.0, n_samples=256, ess_in_band=ess_in_band,
    )


def _cell(status, *, successes=2, n_seeds=2, stats=None) -> Cell:
    return Cell(controller="stock_mppi", scenario="s", status=status,
                n_seeds=n_seeds, successes=successes,
                stats=stats if stats is not None else _stats())


# ------------------------------------------------------------------ the ladder

def test_unfinished_cell_is_not_graded_on_its_ess():
    """`NOT_REACHED` outranks every ESS verdict.

    A run that never reached the goal has an ESS, but it is an ESS of a
    trajectory that gave up — grading it would let a freeze be reported as a
    sampler problem rather than as the completion failure it is.
    """
    assert _status(_stats(all_reached=False, ess_in_band=False),
                   measurable=True) == NOT_REACHED
    assert _status(_stats(all_reached=False, ess_in_band=None),
                   measurable=True) == NOT_REACHED


def test_obstacle_free_scene_is_not_an_avoidance_result():
    assert _status(_stats(), measurable=False) == NO_OBSTACLES


def test_unknown_ess_is_not_compliant():
    """`None` must not collapse to False-y "in band" — unknown is its own rung."""
    assert _status(_stats(ess_in_band=None), measurable=True) == ESS_UNKNOWN
    assert _status(_stats(ess_in_band=False), measurable=True) == ESS_OUT_OF_BAND
    assert _status(_stats(ess_in_band=True), measurable=True) == OK


# --------------------------------------------------------------- the two axes

def test_axes_are_independent_not_a_single_grade():
    """The pair (tracking, avoidance) takes three of its four combinations.

    This is the property that makes two axes worth the cost. If avoidance
    always implied tracking *and vice versa* the flags would be one flag.
    """
    seen = {(c.tracking_reportable, c.avoidance_reportable)
            for c in (_cell(OK), _cell(NO_OBSTACLES), _cell(NOT_REACHED))}
    assert seen == {(True, True), (True, False), (False, False)}


def test_empty_avoidance_population_is_nan_not_a_clean_sweep():
    """Zero reportable avoidance cells must not read as zero collisions.

    D-107's empty-population-reads-as-clean, in the place it would do the most
    damage: a headline that says `collision_rate 0.0000` over nothing at all.
    """
    m = Matrix(cells=(_cell(NO_OBSTACLES), _cell(NO_OBSTACLES)))
    h = m.headline()
    assert h.avoidance_cells == 0
    assert math.isnan(h.collision_rate)
    assert math.isnan(h.min_clearance)


def test_excluded_cells_are_named_not_counted():
    """No silent caps: every non-reportable cell appears with its reason."""
    m = Matrix(cells=(_cell(OK), _cell(NOT_REACHED), _cell(NO_OBSTACLES)))
    h = m.headline()
    assert h.avoidance_cells == 1 and h.avoidance_total == 3
    assert len(h.excluded) == 2, "one entry per excluded cell, never a tally"
    assert sorted(why for _, why in h.excluded) == sorted((NOT_REACHED,
                                                           NO_OBSTACLES))


def test_success_rate_is_scoped_to_the_tracking_population():
    """A `NOT_REACHED` cell leaves the denominator, it does not score zero.

    Scoring it 0/8 would blend "the controller failed" into "this cell has no
    verdict", which is the conflation the ladder exists to prevent.
    """
    m = Matrix(cells=(_cell(OK, successes=2, n_seeds=2),
                      _cell(NOT_REACHED, successes=0, n_seeds=2)))
    assert m.headline().success_rate == 1.0
    assert m.headline().tracking_cells == 1


# ------------------------------------------------------------- integration

def test_scene_set_excludes_the_calibration_table():
    names = {p.name for p in default_scenarios()}
    assert "lam_windows.yaml" not in names
    assert "cafe_straight_v0.yaml" in names


def test_obstacle_free_scene_grades_no_obstacles_live():
    cell = run_cell(STRAIGHT, "stock_mppi", range(2))
    assert cell.status == NO_OBSTACLES
    assert cell.tracking_reportable and not cell.avoidance_reportable


def test_success_counts_the_joint_event():
    """`successes` must require goal *and* no collision, not either alone."""
    cell = run_cell(HEAD_ON, "stock_mppi", range(2))
    assert 0 <= cell.successes <= cell.n_seeds
    assert cell.stats is not None
    if cell.stats.all_reached and cell.stats.collisions == 0:
        assert cell.successes == cell.n_seeds
    if cell.stats.collisions == cell.n_seeds:
        assert cell.successes == 0
