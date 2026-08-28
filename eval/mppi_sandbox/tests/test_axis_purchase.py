# SPDX-License-Identifier: BSD-3-Clause
"""`axis_purchase`: the two uncensused north-star axes, bought at seed 0.

Same split as `test_baseline_domination`:

* **Structure tests** run against the live census and pin *relationships* — that
  the contract line never leads the time column, that the duplicate pairs
  reproduce, that a non-arrival is kept out of the ranking. These survive a
  re-measure that moves the numbers.
* **Tamper tests** feed synthetic tables to the ranking helpers so the algebra
  is graded on cases the live data does not contain.

The integers are pinned by `CENSUS`/`drift`, which is what the CLI grades. A
test asserting a specific float would go red on any re-take, which is how a
check gets muted (D-044).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import axis_purchase as ap
from eval.mppi_sandbox import baseline_domination as bd


# ---------------------------------------------------------------- structure


def test_census_matches_the_derived_reading():
    """The pinned census is what the module derives. This is the CLI's rc."""
    assert ap.drift() == ()


def test_axes_are_exactly_the_uncensused_ones():
    """This module exists to buy `UNCENSUSED_AXES`; the two must agree.

    Tied by test rather than by one importing the other, so a cycle that
    censuses a third axis has to come here and decide, instead of silently
    widening a constant this module's findings were not measured over.
    """
    assert ap.AXES == bd.UNCENSUSED_AXES


def test_scene_set_is_the_joint_surface():
    """Cells must line up with the clearance/cte columns to be joinable."""
    assert set(ap.scenes()) == set(bd.coverage()["joint"])


def test_arms_match_the_reportable_surface():
    """Same eight arms `baseline_domination` quotes the calibration table over."""
    assert set(ap.arms()) == set(bd.arms())


def test_no_censused_scene_has_unusable_arrival():
    """The joint surface must not contain a closed-loop scene.

    `city_figure8_v0` arrives at `t = 0.0` for any controller (D-252). If a
    widening cycle pulls such a scene onto this surface, every time cell on it
    becomes meaningless — go red here rather than publish the column.
    """
    assert set(ap.scenes()).isdisjoint(ap.ARRIVAL_UNUSABLE_SCENES)


# ------------------------------------------------------------- finding #1


def test_the_obstacle_line_is_never_the_fastest_arm():
    """Finding #1: `cbf_mppi` buys clearance and pays in time, on every scene."""
    assert ap.line_is_ever_fastest() is False


def test_the_price_table_covers_every_censused_scene():
    """A partial table would understate the price by omitting its worst cell."""
    assert set(ap.price_of_the_line()) == set(ap.scenes())


def test_the_line_the_findings_describe_is_still_the_contract_line():
    """The prose names `cbf_mppi`; `class_contract` is the authority.

    If the contract moves, this goes red — the findings above were measured
    about a specific arm and must not silently re-point at a different one.
    """
    from eval.mppi_sandbox.class_contract import contract_line

    arm, _ = contract_line("obstacle")
    assert arm == ap.DOCUMENTED_LINE


def test_the_line_is_strictly_slower_than_the_best_on_every_scene():
    """Stronger than "never fastest": there is a real gap in every cell."""
    for scene, (line, best, _, _) in ap.price_of_the_line().items():
        assert line > best, scene


# ------------------------------------------------------------- finding #2


def test_a_non_arrival_is_excluded_from_the_time_column():
    """Never-arrived is off the scale, not the bottom of it."""
    for arm, scene in ap.unfinished():
        assert arm not in ap.time_column(scene)
        assert ap.rank_of(scene, arm) is None


def test_unfinished_cells_still_carry_a_cross_track_number():
    """Finding #2: the tracking record is computed over a run that never arrived.

    This is the defect the finding reports, so the test asserts it is *present*
    — a later cycle that drops these cells from the tracking record should come
    here and update the finding, not find a silently-passing test.
    """
    from eval.mppi_sandbox.cte_vacuity import CTE_SEED0

    assert ap.unfinished(), "finding #2 has no population"
    for arm, scene in ap.unfinished():
        assert arm in CTE_SEED0.get(scene, {}), (arm, scene)


def test_the_unfinished_arm_is_the_tracking_plurality_candidate():
    """Why finding #2 bites: it lands on the arm the tracking record favours."""
    from eval.mppi_sandbox.class_contract import plurality

    candidate, _, _ = plurality("tracking")
    assert candidate in {arm for arm, _ in ap.unfinished()}


# ------------------------------------------------------------- finding #3


def test_duplicate_pairs_reproduce_on_the_new_axes():
    """The inert-channel signature on a third and fourth disjoint column set."""
    assert ap.duplicate_pairs() == (
        ("frozen_risk_mppi", "risk_mppi"),
        ("geometric_mppi", "stock_mppi"),
    )


def test_distinct_arm_count_collapses_the_duplicates():
    assert ap.distinct_arms() == len(ap.arms()) - len(ap.duplicate_pairs())


def test_every_column_is_populated_for_every_arm():
    """Smoothness has no missing cells — only time can be absent."""
    for scene in ap.scenes():
        for key in ("jerk_lat", "jerk_lon", "accel_var"):
            col = ap.smoothness_column(scene, key)
            assert set(col) == set(ap.arms()), (scene, key)


def test_widening_price_matches_the_sibling_census_convention():
    """Same surface, same arithmetic as `baseline_domination`'s two axes."""
    assert ap.WIDENING_UNBOUGHT == bd.WIDENING_UNBOUGHT


# ---------------------------------------------------------------- tamper


@pytest.fixture
def synthetic(monkeypatch):
    """Install a 2-scene / 3-arm table and return it."""
    table = {
        "s1": {"a": (1.0, 0.0, 0.0, 0.0), "b": (2.0, 0.0, 0.0, 0.0),
               "c": (3.0, 0.0, 0.0, 0.0)},
        "s2": {"a": (5.0, 0.0, 0.0, 0.0), "b": (None, 0.0, 0.0, 0.0),
               "c": (4.0, 0.0, 0.0, 0.0)},
    }
    monkeypatch.setattr(ap, "AXIS_SEED0", table)
    return table


def test_rank_orders_fastest_first(synthetic):
    assert ap.rank_of("s1", "a") == (1, 3)
    assert ap.rank_of("s1", "c") == (3, 3)


def test_rank_field_shrinks_when_an_arm_does_not_arrive(synthetic):
    """The field is the arrivals, so a non-arrival shrinks the denominator."""
    assert ap.rank_of("s2", "c") == (1, 2)
    assert ap.rank_of("s2", "b") is None


def test_ties_do_not_share_a_rank(synthetic):
    """Two arms on the same time get consecutive ranks, deterministically.

    The order is by `(time, name)`, so a re-take that leaves a tie in place
    produces the same table twice rather than a coin flip.
    """
    synthetic["s1"]["b"] = (1.0, 0.0, 0.0, 0.0)
    assert ap.rank_of("s1", "a") == (1, 3)
    assert ap.rank_of("s1", "b") == (2, 3)


def test_unfinished_finds_every_none_cell(synthetic):
    assert ap.unfinished() == (("b", "s2"),)


def test_duplicate_pairs_needs_agreement_on_every_scene(synthetic):
    """An arm pair that matches on one scene but not the other is not a dupe."""
    synthetic["s1"]["b"] = synthetic["s1"]["a"]
    assert ap.duplicate_pairs() == ()
    synthetic["s2"]["b"] = synthetic["s2"]["a"]
    assert ap.duplicate_pairs() == (("a", "b"),)


def test_worst_scene_is_by_rank_fraction_not_raw_rank(synthetic, monkeypatch):
    """A 2/2 must outrank a 3/8 — the field sizes differ across scenes."""
    monkeypatch.setattr(ap, "price_of_the_line",
                        lambda: {"small": (9.0, 1.0, 2, 2),
                                 "big": (9.0, 1.0, 3, 8)})
    assert ap.worst_scene_for_line() == ("small", 2, 2)
