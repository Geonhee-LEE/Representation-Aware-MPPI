# SPDX-License-Identifier: BSD-3-Clause
"""`baseline_domination`: is any single arm non-dominated on the north star?

Two kinds of test here, deliberately separated:

* **Relationship tests** run against the live censuses and pin *structure* —
  that the frontier is the whole distinct registry, that the two single-axis
  frontiers are disjoint, that duplicates are collapsed. These survive a
  re-measurement that moves the numbers.
* **Tamper tests** feed synthetic columns to :func:`dominates` /
  :func:`frontier` so the domination algebra is graded on cases the live data
  does not contain (a strict dominator, an exact tie, a missing column).

Pinning the *integers* is left to `CENSUS`/`drift`, which is what the CLI
grades. A test that asserted `frontier() == (8 specific names)` would go red on
any re-measure, which is how a check gets muted (D-044).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import baseline_domination as bd


# ---------------------------------------------------------------- structure


def test_census_matches_the_derived_reading():
    """The pinned census is what the module derives. This is the CLI's rc."""
    assert bd.drift() == ()


def test_joint_frontier_is_the_entire_registry():
    """The P5 finding: no arm dominates any other on the joint surface.

    This is STATE's second branch — "if none is, that is itself the P5 finding
    and the report needs a per-class contract rather than a single baseline".
    """
    assert set(bd.frontier()) == set(bd.arms())


def test_no_single_baseline_is_available():
    """Restated as the decision it blocks: the frontier is not a singleton."""
    assert len(bd.distinct_frontier()) > 1


def test_the_two_single_axis_frontiers_are_disjoint():
    """Each axis alone nominates a baseline, and they nominate different ones.

    This is why the joint read is the one that counts: a P5 report quoting
    either axis in isolation would name a winner the other axis refutes.
    """
    clear = set(bd.frontier(("clear",)))
    cte = set(bd.frontier(("cte",)))
    assert clear and cte
    assert clear.isdisjoint(cte)


def test_clearance_alone_has_a_sole_winner():
    """`cbf_mppi` dominates every other arm on clearance — a total order."""
    assert bd.frontier(("clear",)) == ("cbf_mppi",)


def test_duplicate_class_is_collapsed_out_of_the_frontier():
    """A duplicate pair is non-dominated by construction; only one may count."""
    dups = bd.duplicates()
    assert dups, "expected the geometric/stock duplicate class"
    dropped = {arm for group in dups for arm in group[1:]}
    assert dropped
    assert set(bd.distinct_frontier()).isdisjoint(dropped)
    assert len(bd.distinct_frontier()) == len(bd.frontier()) - len(dropped)


def test_geometric_arm_duplicates_the_baseline():
    """The inert-channel signature, reproduced on a column set disjoint from
    the one `clearance_census` pinned it on."""
    assert any({"geometric_mppi", "stock_mppi"} <= set(g) for g in bd.duplicates())


# ---------------------------------------------------------------- coverage


def test_joint_surface_is_the_intersection_of_the_two_axes():
    cov = bd.coverage()
    assert set(cov["joint"]) == set(cov["clearance"]) & set(cov["cte"])


def test_neither_axis_covers_the_whole_completable_surface():
    """The scope caveat, derived. Both gaps are real and have distinct causes."""
    cov = bd.coverage()
    comp = set(bd.completable())
    assert set(cov["clearance"]) < comp
    assert set(cov["cte"]) < comp
    assert 0 < len(cov["joint"]) < len(comp)


def test_columns_are_restricted_to_scenes_carrying_every_axis():
    """A domination test must never grade a missing column as a loss."""
    scenes = {s for s, _axis in bd.columns()}
    assert scenes == set(bd.coverage()["joint"])
    for col in bd.columns().values():
        assert set(col) == set(bd.arms())


def test_cte_column_is_sign_normalised_to_higher_is_better():
    """A ceiling bar and a floor bar must not be compared with the same sign."""
    from eval.mppi_sandbox.cte_vacuity import CTE_SEED0

    scene = bd.coverage()["joint"][0]
    col = bd._cte_column(scene)
    for arm, raw in CTE_SEED0[scene].items():
        assert col[arm] == pytest.approx(-raw)
    # lower raw cte ⇒ higher normalised score
    best_raw = min(CTE_SEED0[scene], key=lambda a: CTE_SEED0[scene][a])
    assert col[best_raw] == max(col.values())


def test_uncensused_axes_are_named_rather_than_silent():
    """Two of the north star's clauses have no census; the frontier is a
    lower bound on the true tradeoff width because of it."""
    assert bd.UNCENSUSED_AXES
    assert bd.WIDENING_UNBOUGHT > 0


# ------------------------------------------------- the inadmissible cell


def test_inadmissible_joint_cell_is_derived_not_asserted_away():
    """The one empty window in the reportable 64 lands on the joint surface,
    and it belongs to the clearance winner."""
    cells = bd.inadmissible_joint_cells()
    assert cells == (("cafe_obstacle_crossing_v0", "cbf_mppi"),)


def test_frontier_survives_dropping_the_inadmissible_scene():
    """The module docstring claims dropping it does not change finding #1.

    That claim is load-bearing — it is what licenses reporting the frontier at
    all despite one cell being calibration-inadmissible — so it is measured
    here rather than assumed.
    """
    (scene, _arm), = bd.inadmissible_joint_cells()
    cols = {k: v for k, v in bd.columns().items() if k[0] != scene}
    assert cols, "dropping the scene must leave a non-empty surface"
    survivors = [
        a for a in bd.arms()
        if not any(bd.dominates(a, b, cols) for b in bd.arms() if b != a)
    ]
    assert set(survivors) == set(bd.arms())


# ------------------------------------------------------------ domination algebra


def _cols(**per_axis):
    return {("s", axis): col for axis, col in per_axis.items()}


def test_strict_dominator_is_detected():
    cols = _cols(clear={"a": 1.0, "b": 2.0}, cte={"a": 1.0, "b": 2.0})
    assert bd.dominates("a", "b", cols)
    assert not bd.dominates("b", "a", cols)


def test_weak_dominator_needs_one_strict_win():
    """Equal everywhere is not domination — that is the duplicate case."""
    cols = _cols(clear={"a": 1.0, "b": 1.0}, cte={"a": 2.0, "b": 2.0})
    assert not bd.dominates("a", "b", cols)
    assert not bd.dominates("b", "a", cols)

    cols = _cols(clear={"a": 1.0, "b": 1.0}, cte={"a": 2.0, "b": 3.0})
    assert bd.dominates("a", "b", cols)


def test_a_genuine_tradeoff_is_not_domination():
    cols = _cols(clear={"a": 1.0, "b": 5.0}, cte={"a": 5.0, "b": 1.0})
    assert not bd.dominates("a", "b", cols)
    assert not bd.dominates("b", "a", cols)


def test_absent_arm_yields_no_domination():
    """No shared column ⇒ no verdict, rather than a vacuous `all()` True."""
    cols = _cols(clear={"a": 1.0})
    assert not bd.dominates("a", "b", cols)
    assert not bd.dominates("b", "a", cols)


def test_main_returns_zero_when_the_census_holds():
    assert bd.main() == 0


def test_main_reports_drift(monkeypatch):
    monkeypatch.setitem(bd.CENSUS, "joint_scenes", "999")
    assert bd.drift()
    assert bd.main() == 1
