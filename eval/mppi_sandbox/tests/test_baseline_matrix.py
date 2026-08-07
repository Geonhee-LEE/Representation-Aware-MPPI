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
    LAM_UNCALIBRATED,
    NO_ADMISSIBLE_LAM,
    NO_OBSTACLES,
    NOT_REACHED,
    OK,
    UNRUN,
    Cell,
    Matrix,
    _status,
    default_scenarios,
    lam_for_cell,
    pick_lam,
    run_cell,
    run_matrix,
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


# --------------------------------------------------- per-cell temperature

def test_pick_lam_is_the_log_space_middle_not_an_endpoint():
    """A cell reported at a window endpoint is one rung from inadmissible.

    The tie-break on an even-length window (upper of the two central rungs) is
    a convention, not a claim — pinned so a change to it reads as a diff
    instead of as numbers quietly moving.
    """
    assert pick_lam([0.2, 0.4, 0.8]) == 0.4
    assert pick_lam([0.2, 0.4]) == 0.4          # tie-break: upper
    assert pick_lam([0.8, 0.2, 0.4]) == 0.4     # input order must not matter


def test_pick_lam_refuses_an_empty_window():
    """No representative rung exists, so there is no value to return.

    Returning a default here is precisely how an unreportable cell would
    acquire a temperature and re-enter the headline.
    """
    with pytest.raises(ValueError):
        pick_lam([])


def test_table_answers_the_cell_before_any_sweep_is_paid_for():
    W = {("s.yaml", "stock_mppi"): {"admissible": (0.2, 0.4)},
         ("s.yaml", "risk_mppi"): {"admissible": ()}}
    assert lam_for_cell("s.yaml", "stock_mppi", W) == (0.4, None)
    assert lam_for_cell("s.yaml", "risk_mppi", W) == (None, NO_ADMISSIBLE_LAM)
    assert lam_for_cell("s.yaml", "cbf_mppi", W) == (None, LAM_UNCALIBRATED)


def test_unrun_cells_count_on_neither_axis():
    """A cell that never executed is not a tracking result either.

    `tracking_reportable` used to be `status != NOT_REACHED`, which would have
    made both new table verdicts tracking-reportable by default — a cell with
    `n_seeds=0` contributing to `success_rate`'s denominator. This is the
    property that stops a new status from defaulting into a denominator.
    """
    for status in (NO_ADMISSIBLE_LAM, LAM_UNCALIBRATED):
        c = Cell(controller="stock_mppi", scenario="s", status=status,
                 n_seeds=0, successes=0)
        assert not c.tracking_reportable
        assert not c.avoidance_reportable
    assert UNRUN == {NOT_REACHED, NO_ADMISSIBLE_LAM, LAM_UNCALIBRATED}


def test_unrun_cells_are_named_in_the_headline_not_dropped():
    """They stay in `avoidance_total` — the denominator is the whole grid."""
    m = Matrix(cells=(_cell(OK),
                      Cell(controller="c", scenario="s",
                           status=NO_ADMISSIBLE_LAM, n_seeds=0, successes=0)))
    h = m.headline()
    assert (h.avoidance_cells, h.avoidance_total) == (1, 2)
    assert (h.tracking_cells, h.tracking_total) == (1, 2)
    assert NO_ADMISSIBLE_LAM in {why for _, why in h.excluded}


def test_calibrated_lam_moves_the_sampler_into_band_live():
    """The cycle's whole claim, on the cheapest obstacle-bearing scene.

    At the shipped default the sampler is a greedy argmin, so `cafe_head_on`
    grades `ESS_OUT_OF_BAND` and its avoidance number describes the
    temperature. At the cell's admissible rung the same scene grades `OK`.
    Without this the calibration could be wired up and inert.
    """
    default = run_cell(HEAD_ON, "stock_mppi", range(2))
    assert default.status == ESS_OUT_OF_BAND
    assert default.lam is None

    calibrated = run_cell(HEAD_ON, "stock_mppi", range(2), lam=0.4)
    assert calibrated.status == OK
    assert calibrated.lam == 0.4
    assert calibrated.stats.median_ess > default.stats.median_ess


def test_uncalibrated_flag_reproduces_the_shipped_default_matrix():
    """`calibrated=False` is D-118's matrix — no cell names a temperature."""
    m = run_matrix([STRAIGHT], ["stock_mppi"], range(1), calibrated=False)
    assert [c.lam for c in m.cells] == [None]
