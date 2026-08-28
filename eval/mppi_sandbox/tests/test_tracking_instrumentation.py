# SPDX-License-Identifier: BSD-3-Clause
"""Pins for :mod:`tracking_instrumentation` — the 경로추종 instrumentation decision.

The tamper tests matter more than the census pins here. The module's whole value
is that it separates two effects (more clauses vs fewer scenes) and gates
non-arrivals across *all* clause columns; both are the kind of thing that reads
correct and computes wrong, so each is checked by breaking it on purpose.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import tracking_instrumentation as ti


class TestClauseInventory:
    def test_four_north_star_clauses(self):
        assert len(ti.NORTH_STAR_CLAUSES) == 4

    def test_every_clause_has_a_reader_entry(self):
        assert set(ti.CLAUSE_READER) == set(ti.NORTH_STAR_CLAUSES)

    def test_every_clause_reader_resolves(self):
        """Finding #1: no clause is unmeasurable — each has a live callable."""
        for clause in ti.NORTH_STAR_CLAUSES:
            assert callable(ti.reader_for(clause)), clause

    def test_three_clauses_censused(self):
        assert len(ti.censused_clauses()) == 3

    def test_heading_error_is_the_unbought_clause(self):
        assert ti.unbought_clauses() == ("heading error",)

    def test_nothing_is_unmeasurable(self):
        assert ti.unmeasurable_clauses() == ()

    def test_unbought_and_unmeasurable_are_disjoint(self):
        """The two call for different actions and must never merge."""
        assert not set(ti.unbought_clauses()) & set(ti.unmeasurable_clauses())

    def test_censused_clauses_derived_not_typed(self):
        """Emptying a census must move the inventory, not leave prose stale."""
        from eval.mppi_sandbox import axis_purchase

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(axis_purchase, "AXIS_SEED0", {})
            assert ti.censused_clauses() == ("cross-track error",)
            assert set(ti.unbought_clauses()) == {
                "heading error", "smoothness", "time-to-goal",
            }

    def test_a_missing_reader_reads_as_unmeasurable(self):
        from eval import path_tracking_metrics

        with pytest.MonkeyPatch.context() as mp:
            mp.delattr(path_tracking_metrics, "heading_error")
            assert ti.reader_for("heading error") is None
            assert ti.unmeasurable_clauses() == ("heading error",)
            assert ti.verdict() == "CLAUSE_UNMEASURABLE"

    def test_heading_price_matches_the_bought_axes(self):
        """Finding #1: the gap is priced in D-488's own units, not left silent."""
        from eval.mppi_sandbox.axis_purchase import MEASURED_ROLLOUTS

        assert ti.HEADING_UNBOUGHT_ROLLOUTS == MEASURED_ROLLOUTS


class TestPopulationCost:
    def test_widening_costs_scenes(self):
        """Finding #2: three clauses are stateable on fewer scenes than one."""
        one = ti.population(("cross-track error",))
        wide = ti.population(ti.censused_clauses())
        assert len(one) == 7
        assert len(wide) == 4
        assert set(wide) < set(one)

    def test_lost_scenes_are_exactly_the_inert_blocks(self):
        """The three scenes widening drops are the ones that cannot rank anyway."""
        from eval.mppi_sandbox.class_contract import inert_block_scenes

        lost = set(ti.population(("cross-track error",))) - set(
            ti.population(ti.censused_clauses())
        )
        assert lost == set(inert_block_scenes("tracking"))

    def test_common_population_is_the_widened_one(self):
        assert set(ti.common_population()) == set(
            ti.population(ti.censused_clauses())
        )

    def test_columns_keep_only_scenes_with_every_clause(self):
        cols = ti.clause_columns()
        scenes = {s for s, _ in cols}
        for scene in scenes:
            for clause in ti.censused_clauses():
                assert (scene, clause) in cols


class TestArrivalGate:
    def test_non_arrival_is_cut_from_every_clause(self):
        """Finding #3: the gate is not limited to the column that noticed."""
        cols = ti.clause_columns()
        for clause in ti.censused_clauses():
            col = cols[("cafe_obstacle_crossing_v0", clause)]
            assert "essps_mppi" not in col, clause

    def test_the_gate_removes_exactly_one_cell(self):
        assert ti.non_arrivals("cafe_obstacle_crossing_v0") == frozenset(
            {"essps_mppi"}
        )
        assert ti.non_arrivals("cafe_convoy_v0") == frozenset()

    def test_ungated_cross_track_cell_exists(self):
        """The cell the gate cuts is present and finite — that is why it misleads."""
        from eval.mppi_sandbox.cte_vacuity import CTE_SEED0

        assert "essps_mppi" in CTE_SEED0["cafe_obstacle_crossing_v0"]

    def test_gate_is_derived_from_the_arrival_census(self):
        from eval.mppi_sandbox import axis_purchase

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(axis_purchase, "unfinished", lambda: ())
            cols = ti.clause_columns()
            assert "essps_mppi" in cols[
                ("cafe_obstacle_crossing_v0", "cross-track error")
            ]

    def test_arrival_coverage_is_total_on_this_population(self):
        assert ti.arrival_coverage() == (4, 4)

    def test_coverage_falls_when_the_census_narrows(self):
        """Coverage is a coincidence of the scene sets, so it must be derived."""
        from eval.mppi_sandbox import axis_purchase

        trimmed = {
            k: v for k, v in axis_purchase.AXIS_SEED0.items()
            if k != "cafe_convoy_v0"
        }
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(axis_purchase, "AXIS_SEED0", trimmed)
            censused, total = ti.arrival_coverage()
            assert censused == total == 3


class TestFrontier:
    def test_single_clause_frontier_matches_the_shipped_contract(self):
        """D-487's tracking frontier, re-derived through this module's columns."""
        assert len(ti.frontier_under(("cross-track error",))) == 3

    def test_widened_frontier_is_the_whole_registry(self):
        assert len(ti.frontier_under(ti.censused_clauses())) == 8

    def test_distinct_frontier_collapses_the_duplicate_pair(self):
        """Finding #5: the raw 8 is inflated by one bit-identical pair."""
        assert ti.duplicate_groups(ti.censused_clauses()) == (
            ("geometric_mppi", "stock_mppi"),
        )
        assert len(ti.distinct_frontier_under(ti.censused_clauses())) == 7

    def test_duplicate_structure_is_clause_relative(self):
        """One pair here vs two on clearance — so it cannot be inherited."""
        from eval.mppi_sandbox.class_contract import duplicates_in_class

        assert len(duplicates_in_class("obstacle")) == 2
        assert len(ti.duplicate_groups(ti.censused_clauses())) == 1

    def test_widening_is_monotone(self):
        assert ti.widening_is_monotone() is True

    def test_monotonicity_is_checked_not_assumed(self):
        """An asymmetric gate would break the implication; nothing else would say so."""
        real = ti.frontier_under

        dropped = real(("cross-track error",), ti.common_population())[0]

        def broken(clause_set=None, pool=None):
            got = real(clause_set, pool)
            if clause_set is not None and len(clause_set) > 1:
                return tuple(a for a in got if a != dropped)
            return got

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(ti, "frontier_under", broken)
            assert ti.widening_is_monotone() is False
            assert ti.verdict() == "WIDENING_NOT_MONOTONE"

    def test_no_line_under_the_widened_instrumentation(self):
        """Finding #4: widening cannot rescue the tracking contract line."""
        assert ti.line_under() is None

    def test_line_under_finds_a_planted_total_order(self):
        """The `None` above is a reading, not a function that always returns None."""
        planted = {
            ("s1", "cross-track error"): {"a": 2.0, "b": 1.0},
            ("s1", "smoothness"): {"a": 2.0, "b": 1.0},
        }
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(ti, "clause_columns", lambda **kw: planted)
            assert ti.line_under() == "a"

    def test_one_losing_column_denies_the_line(self):
        """동시 만족 — an arm must win every clause of every scene."""
        planted = {
            ("s1", "cross-track error"): {"a": 2.0, "b": 1.0},
            ("s1", "smoothness"): {"a": 1.0, "b": 2.0},
        }
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(ti, "clause_columns", lambda **kw: planted)
            assert ti.line_under() is None


class TestSignNormalisation:
    @pytest.mark.parametrize("clause", ["cross-track error", "smoothness", "time-to-goal"])
    def test_all_censused_clauses_are_negated_ceilings(self, clause):
        """Every column is lower-is-better on disk, so every one must be negated."""
        col = ti._raw_column(clause, "cafe_convoy_v0")
        assert col
        assert all(v < 0 for v in col.values()), clause

    def test_cross_track_matches_the_joint_surface_column(self):
        from eval.mppi_sandbox.baseline_domination import _cte_column

        mine = ti._raw_column("cross-track error", "cafe_convoy_v0")
        assert mine == _cte_column("cafe_convoy_v0")

    def test_smoothness_key_is_pinned(self):
        from eval.mppi_sandbox.axis_purchase import smoothness_column

        assert ti.SMOOTHNESS_KEY == "jerk_lat"
        raw = smoothness_column("cafe_convoy_v0", ti.SMOOTHNESS_KEY)
        assert ti._raw_column("smoothness", "cafe_convoy_v0") == {
            a: -v for a, v in raw.items()
        }


class TestCensus:
    def test_no_drift(self):
        assert ti.drift() == ()

    def test_verdict(self):
        assert ti.verdict() == "WIDEN_TO_CENSUSED"

    def test_census_keys_match_the_pin(self):
        assert set(ti.census()) == set(ti.CENSUS)

    def test_drift_reports_a_moved_key(self):
        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(ti.CENSUS, "verdict", "WIDEN_TO_ALL")
            assert len(ti.drift()) == 1

    def test_table_names_every_clause(self):
        table = ti.format_table()
        for clause in ti.NORTH_STAR_CLAUSES:
            assert clause in table
        assert "unbought" in table

    def test_class_axis_is_not_repointed_here(self):
        """Scope: this module decides, `class_contract` still states the contract."""
        from eval.mppi_sandbox.class_contract import CLASS_AXIS

        assert CLASS_AXIS["tracking"] == "cte"


class TestWidenedRecord:
    """D-491 — the record claim D-490 priced but left to a follow-up cycle."""

    def test_no_arm_wins_any_scene_on_all_three_clauses(self):
        """The headline: widening does not move the record, it empties it."""
        assert ti.tally_under() == ()
        arm, won, of = ti.record_under()
        assert (arm, won) == ("", 0)
        assert of == 4

    def test_no_winner_is_not_named_alphabetically(self):
        """`max` over an all-zero tally would credit an arm that did nothing."""
        arm, _, _ = ti.record_under()
        assert arm not in ti.arms_in(ti.clause_columns())
        assert arm == ""

    def test_same_pool_one_clause_reproduces_the_shipped_record(self):
        """The two fractions differ by clause set alone, not by population.

        Held fixed the way `common_population` holds it for the frontier: if
        this ever stops reproducing `class_contract`'s shipped 2/3, the widened
        record's contrast is confounded and must not be quoted.
        """
        from eval.mppi_sandbox.class_contract import CENSUS

        arm, won, of = ti.record_under(
            ("cross-track error",), ti.population(ti.censused_clauses())
        )
        assert f"{arm} {won}/{of}" == CENSUS["tracking_gated_record"]

    def test_record_pools_coincide_by_two_unrelated_filters(self):
        """Ranking-resolution and census-coverage select the same four scenes."""
        from eval.mppi_sandbox.class_contract import ranking_scenes

        assert ti.record_pools_equal()
        assert set(ranking_scenes("tracking")) == set(
            ti.population(ti.censused_clauses())
        )

    def test_conjunction_is_stricter_than_per_clause_win(self):
        """An arm leading on one clause is not thereby a scene winner.

        The bar `outright_wins_under` applies. `essps_mppi` leads cross-track on
        scenes it wins nothing on here — that gap is the whole finding, so it is
        asserted rather than left to the aggregate count.
        """
        wide = ti.outright_wins_under()
        narrow = ti.outright_wins_under(("cross-track error",))
        assert narrow["essps_mppi"] > 0
        assert wide["essps_mppi"] == 0
        assert all(wide[a] <= narrow.get(a, 0) for a in wide)

    def test_eligible_scenes_drop_the_non_arrival(self):
        """D-489's gate on three columns at once."""
        elig = ti.eligible_scenes_under("essps_mppi")
        assert "cafe_obstacle_crossing_v0" not in elig
        assert len(elig) == 3

    def test_tamper_a_single_dominant_arm_produces_a_record(self, monkeypatch):
        """Drive the opposite verdict: the empty tally must be data, not shape."""
        cols = ti.clause_columns()
        rigged = {
            k: {a: (99.0 if a == "risk_mppi" else v) for a, v in c.items()}
            for k, c in cols.items()
        }
        monkeypatch.setattr(ti, "clause_columns", lambda **kw: rigged)
        arm, won, _ = ti.record_under()
        assert arm == "risk_mppi"
        assert won == 4

    def test_census_labels_both_records_with_their_clause_sets(self):
        """Unlabelled, 2/3 vs 0/4 reads as a contradiction."""
        from eval.mppi_sandbox import class_contract as cc

        got = cc.census()
        assert got["tracking_gated_record_clauses"] == "cross-track error"
        assert got["tracking_widened_record_clauses"] == (
            "cross-track error+smoothness+time-to-goal"
        )
        assert got["tracking_widened_record"] != got["tracking_gated_record"]

    def test_class_contract_cites_rather_than_recomputes(self):
        """One claim, one module — the failure D-490 declined to create."""
        from eval.mppi_sandbox import class_contract as cc

        assert cc.census()["tracking_widened_record"] == ti.census()["record_widened"]

    def test_class_axis_is_still_not_re_pointed(self):
        """D-487/D-489's shipped keys must not move under this cycle."""
        from eval.mppi_sandbox import class_contract as cc

        assert cc.CLASS_AXIS["tracking"] == "cte"
        assert cc.CENSUS["tracking_gated_record"] == "essps_mppi 2/3"
        assert cc.drift() == ()
