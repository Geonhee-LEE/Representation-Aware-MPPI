# SPDX-License-Identifier: BSD-3-Clause
"""`class_contract`: can P5 name one arm per north-star class?

Same two-kind split as `test_baseline_domination`, and for the same reason:

* **Relationship tests** run against the live censuses and pin *structure* —
  that the obstacle class's line is a total order and not merely a singleton
  frontier, that the tracking class has no line, that a plurality record
  shrinks when the inert-block scenes are removed. These survive a re-measure
  that moves the numbers.
* **Tamper tests** feed synthetic columns to the algebra so the pieces that the
  live data exercises only one way (a class with no line, a line that dies when
  its inadmissible cell is cut) are graded on cases the tree does not contain.

Pinning the *integers* is left to `CENSUS`/`drift`, which the CLI grades. A test
asserting `plurality() == ("essps_mppi", 6, 7)` would go red on any re-measure,
which is how a check gets muted (D-044).
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import class_contract as cc


# ---------------------------------------------------------------- structure


def test_census_matches_the_derived_reading():
    """The pinned census is what the module derives. This is the CLI's rc."""
    assert cc.drift() == ()


def test_both_north_star_classes_are_covered():
    """A contract that omits half the north star is not a contract."""
    assert set(cc.classes()) == {"obstacle", "tracking"}


def test_obstacle_line_is_a_total_order_not_just_a_singleton_frontier():
    """The contract needs the stronger claim, so the test asserts the stronger one.

    A singleton frontier says *nothing dominates this arm*; a total order says
    *this arm beats everything*. Only the second licenses "use this arm for
    this class", and asserting the first would pass on a class where the
    favourite ties its way to the front.
    """
    arm, reason = cc.contract_line("obstacle")
    assert arm is not None
    assert reason == "TOTAL_ORDER"
    assert cc.total_order_winner("obstacle") == arm
    assert cc.frontier_in_class("obstacle") == (arm,)


def test_obstacle_line_wins_every_scene_of_its_class_outright():
    """The total order restated as the count it rests on, so a partial sweep shows."""
    arm, _ = cc.contract_line("obstacle")
    assert cc.outright_wins("obstacle")[arm] == len(cc.scenes("obstacle"))


def test_tracking_class_has_no_line():
    """D-486's shape, one level down: the class trades off rather than resolving."""
    arm, reason = cc.contract_line("tracking")
    assert arm is None
    assert reason in {"NO_FRONTIER_SINGLETON", "NO_TOTAL_ORDER"}
    assert len(cc.frontier_in_class("tracking")) > 1


def test_the_contract_is_partial():
    """Exactly the finding: one class resolves, the other does not.

    Pinned as an inequality on both sides rather than "1 of 2" so it survives a
    third class being censused, and still fails if either class flips.
    """
    lines = [c for c in cc.classes() if cc.contract_line(c)[0]]
    assert 0 < len(lines) < len(cc.classes())


def test_duplicate_classes_are_axis_dependent():
    """Finding #3 — the joint collapse is not reusable per class.

    The obstacle class holds strictly fewer distinct arms than the tracking
    class, because a pair that separates only on cross-track is one arm inside
    a class that never reads cross-track.
    """
    from eval.mppi_sandbox import baseline_domination as bd

    assert cc.distinct_arms("obstacle") < cc.distinct_arms("tracking")
    assert len(cc.duplicates_in_class("obstacle")) > len(bd.duplicates())


def test_inert_block_scenes_partition_the_class_scenes():
    """Ranking and inert-block scenes are complements — no scene is lost or double-counted."""
    for cls in cc.classes():
        rank, inert = set(cc.ranking_scenes(cls)), set(cc.inert_block_scenes(cls))
        assert rank | inert == set(cc.scenes(cls))
        assert rank & inert == set()


def test_inert_block_scenes_resolve_below_the_ranking_bar():
    """The name has to be earned by the measurement, not by the label."""
    for cls in cc.classes():
        for scene in cc.inert_block_scenes(cls):
            assert cc.resolution(cls, scene) < cc.RANKING_RESOLUTION
        for scene in cc.ranking_scenes(cls):
            assert cc.resolution(cls, scene) >= cc.RANKING_RESOLUTION


def test_tracking_plurality_shrinks_on_the_ranking_scenes():
    """Finding #2's load-bearing half: the 6/7 is inflated by inert blocks.

    Pinned as a *relationship* — the denominator strictly shrinks and the win
    rate does not improve — so it holds under a re-measure that changes which
    scenes are inert.
    """
    _, all_won, all_of = cc.plurality("tracking")
    _, rank_won, rank_of = cc.plurality("tracking", cc.ranking_scenes("tracking"))
    assert rank_of < all_of
    assert rank_won / rank_of <= all_won / all_of


def test_obstacle_line_does_not_depend_on_an_inadmissible_cell():
    """Finding #4 — checked, not hoped.

    The class contains `reportable_surface().empty`'s single member, so the
    line is drafted partly on numbers taken at a temperature the calibration
    table does not admit. It survives their removal.
    """
    arm, _ = cc.contract_line("obstacle")
    assert cc.inadmissible_scenes("obstacle", arm)      # the cell is really there
    assert cc.line_survives_inadmissible("obstacle") is True


def test_no_line_means_no_survival_verdict():
    """A class without a line has nothing to test for survival — `None`, not `False`."""
    assert cc.line_survives_inadmissible("tracking") is None


def test_class_scenes_come_from_the_coverage_partition():
    """Derived, not typed (D-047): each class's scenes are its axis's coverage."""
    from eval.mppi_sandbox import baseline_domination as bd

    cov = bd.coverage()
    assert cc.scenes("obstacle") == cov["clearance"]
    assert cc.scenes("tracking") == cov["cte"]


def test_class_scenes_are_not_restricted_to_the_joint_surface():
    """A class is entitled to every scene its own axis records.

    Restricting to the joint intersection would silently drop three tracking
    scenes for the sake of a column that class never reads.
    """
    from eval.mppi_sandbox import baseline_domination as bd

    assert len(cc.scenes("tracking")) > len(bd.coverage()["joint"])


def test_cli_is_clean():
    assert cc.main() == 0


# ------------------------------------------------------------------- tamper


@pytest.fixture
def synthetic(monkeypatch):
    """Swap the live columns/arms for a hand-built class of three arms.

    `cut` installs synthetic non-arrival cells, so the arrival-gate algebra is
    graded on shapes the tree holds only one instance of (finding #5's live
    population is a single cell).
    """

    def install(cols, arms=("a", "b", "c"), cut=()):
        cut = frozenset(cut)

        def columns(cls, gated=False):
            if not gated:
                return cols
            return {s: {a: v for a, v in col.items() if (a, s) not in cut}
                    for s, col in cols.items()}

        monkeypatch.setattr(cc, "scenes", lambda cls: tuple(cols))
        monkeypatch.setattr(cc, "columns", columns)
        monkeypatch.setattr(cc, "unfinished_cells", lambda cls: cut)
        monkeypatch.setattr(cc, "arrival_censused_scenes", lambda cls: tuple(cols))
        monkeypatch.setattr("eval.mppi_sandbox.baseline_domination.arms", lambda: arms)

    return install


def test_strict_sweep_is_a_total_order(synthetic):
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 5.0, "b": 4.0, "c": 0.0}})
    assert cc.total_order_winner("obstacle") == "a"


def test_a_tie_on_one_scene_breaks_the_total_order(synthetic):
    """Sharing the maximum is not winning it — the arm did not beat the field."""
    synthetic({"s1": {"a": 3.0, "b": 3.0, "c": 2.0},
               "s2": {"a": 5.0, "b": 4.0, "c": 0.0}})
    assert cc.total_order_winner("obstacle") is None
    assert cc.outright_wins("obstacle")["a"] == 1


def test_one_lost_scene_breaks_the_total_order(synthetic):
    """The tracking class's live shape: a favourite that a single scene refutes."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 1.0, "b": 4.0, "c": 0.0}})
    assert cc.total_order_winner("obstacle") is None
    assert cc.plurality("obstacle")[1] == 1


def test_restricting_the_pool_can_restore_a_total_order(synthetic):
    """This is the mechanism `line_survives_inadmissible` runs on."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 1.0, "b": 4.0, "c": 0.0}})
    assert cc.total_order_winner("obstacle", ("s1",)) == "a"


def test_resolution_counts_distinct_values_not_arms(synthetic):
    """A column separating one arm from a tied block resolves 2, not 3."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 1.0},
               "s2": {"a": 3.0, "b": 2.0, "c": 1.0}})
    assert cc.resolution("obstacle", "s1") == 2
    assert cc.resolution("obstacle", "s2") == 3
    assert cc.inert_block_scenes("obstacle") == ("s1",)
    assert cc.ranking_scenes("obstacle") == ("s2",)


def test_a_fully_tied_column_crowns_nobody(synthetic):
    """Resolution 1: every arm identical, so no outright win is available."""
    synthetic({"s1": {"a": 1.0, "b": 1.0, "c": 1.0}})
    assert cc.resolution("obstacle", "s1") == 1
    assert set(cc.outright_wins("obstacle").values()) == {0}
    assert cc.total_order_winner("obstacle") is None


def test_empty_pool_has_no_winner(synthetic):
    """A vacuous sweep must not be reported as a total order over zero scenes."""
    synthetic({})
    assert cc.total_order_winner("obstacle") is None


# ------------------------------------------------- arrival gate (finding #5/#6)


def test_the_gate_reads_its_population_from_the_arrival_census():
    """D-047: a cell's arrival status is its own property, never typed here.

    Asserted as set equality against `axis_purchase` restricted to the class's
    scenes, so adding a scene to either census moves this module without an
    edit — and a hand-typed copy diverging from the source goes red.
    """
    from eval.mppi_sandbox.axis_purchase import unfinished

    for cls in cc.classes():
        mine = set(cc.scenes(cls))
        assert cc.unfinished_cells(cls) == {
            (a, s) for a, s in unfinished() if s in mine
        }


def test_a_gated_cell_is_absent_not_ranked_last():
    """The encoding is the finding: a non-arrival is not a competitor that lost."""
    for cls in cc.classes():
        plain, gated = cc.columns(cls), cc.columns(cls, gated=True)
        for arm, scene in cc.unfinished_cells(cls):
            assert arm in plain[scene]
            assert arm not in gated[scene]


def test_tracking_record_does_not_survive_the_arrival_gate():
    """Finding #5 — the bottleneck's question, answered in the negative.

    Pinned as a strict inequality on both parts of the fraction rather than
    `2/3`, so it survives a re-measure that moves the integers but still fails
    if the gate ever becomes a no-op for this class.
    """
    _, raw_won, raw_of = cc.plurality("tracking", cc.ranking_scenes("tracking"))
    _, won, of = cc.arrival_gated("tracking")
    assert cc.unfinished_cells("tracking")
    assert won < raw_won, "the gate must cost the plurality arm a win"
    assert of < raw_of, "and the scene must leave its denominator, not count as a loss"


def test_the_forfeited_win_transfers_rather_than_vanishing():
    """A gated scene still has a winner — the arm behind the absent one.

    Guards the failure where gating silently drops the whole column instead of
    the cell, which would understate every other arm's record.
    """
    tally = dict(cc.gated_tally("tracking"))
    assert len(tally) > 1, "a 2-1-1 tally is the finding; a 2-0-0 would be a dropped column"
    assert sum(tally.values()) == len(cc.ranking_scenes("tracking", gated=True))


def test_obstacle_line_survives_the_arrival_gate():
    """Checked because it is the direction the cycle did not expect to move."""
    arm, _ = cc.contract_line("obstacle")
    assert arm is not None
    assert cc.line_survives_arrival("obstacle") is True


def test_gating_does_not_demote_any_ranking_scene():
    """Finding #5's third bullet: the denominator moves for arrival, nothing else.

    Removing an arm can only lower resolution, so without this the record could
    shrink twice for one cause and be reported as if the gate had done it all.
    """
    for cls in cc.classes():
        assert cc.gate_preserves_resolution(cls) is True


def test_gate_coverage_is_derived_and_the_two_classes_disagree():
    """Finding #6 — total coverage is a coincidence, and it already fails once.

    Tracking's ranking scenes are exactly the joint surface, so its gate is
    total; the obstacle class owns a scene outside it and is not. Pinning the
    *disagreement* is what stops a future cycle quoting one fraction for both.
    """
    for cls in cc.classes():
        seen, total = cc.arrival_gate_coverage(cls)
        assert 0 <= seen <= total == len(cc.ranking_scenes(cls))
    assert cc.arrival_gate_coverage("tracking")[0] == cc.arrival_gate_coverage("tracking")[1]
    seen, total = cc.arrival_gate_coverage("obstacle")
    assert seen < total, "the obstacle gate is partial — say so rather than implying total"


def test_an_ungated_class_reads_identically(synthetic):
    """No unfinished cells ⇒ gating is the identity, not a silent re-derivation."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 5.0, "b": 4.0, "c": 0.0}})
    assert cc.columns("obstacle", gated=True) == cc.columns("obstacle")
    assert cc.arrival_gated("obstacle") == ("a", 2, 2)
    assert cc.line_survives_arrival("obstacle") is True


def test_gating_the_winning_cell_moves_both_halves_of_the_fraction(synthetic):
    """The live shape, hand-built: the leader forfeits the scene it never finished."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 5.0, "b": 4.0, "c": 0.0}},
              cut=[("a", "s1")])
    assert cc.arrival_gated("obstacle") == ("a", 1, 1)
    assert dict(cc.gated_tally("obstacle")) == {"a": 1, "c": 1}


def test_gating_can_destroy_a_total_order(synthetic):
    """The contract line is not immune — it survives live, and must be able to fail.

    Without this, `line_survives_arrival` returning `True` on the tree would be
    untestable: a function that cannot say no is not a check.
    """
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 2.0},
               "s2": {"a": 5.0, "b": 4.0, "c": 0.0}},
              cut=[("a", "s2")])
    assert cc.total_order_winner("obstacle") == "a"
    assert cc.line_survives_arrival("obstacle") is False


def test_gating_that_flattens_a_column_is_caught(synthetic):
    """Resolution loss is reported, not absorbed into the record."""
    synthetic({"s1": {"a": 3.0, "b": 1.0, "c": 1.0},
               "s2": {"a": 3.0, "b": 2.0, "c": 1.0}},
              cut=[("b", "s2")])
    assert cc.resolution("obstacle", "s2") == 3
    assert cc.resolution("obstacle", "s2", gated=True) == 2
    assert cc.gate_preserves_resolution("obstacle") is False
