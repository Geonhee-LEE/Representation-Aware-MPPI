# SPDX-License-Identifier: BSD-3-Clause
"""Pins for :mod:`obstacle_instrumentation` — the 물체회피 coverage census.

The module's claim is that STATE's "run the conjunctive record over 물체회피"
is **ill-posed**, and that the honest question in its place is class coverage.
These tests pin both halves: that the two constitutions' clauses really are of
different kinds (so the premise is derived, not asserted), and that the
coverage numbers are re-derivable from the yaml rather than typed.

Tamper tests are included for every derived predicate — D-489's lesson was that
the tamper direction is where a coverage census's real bugs live, because a
predicate that is accidentally always-True reads as *better* coverage.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import class_contract as cc
from eval.mppi_sandbox import obstacle_instrumentation as oi
from eval.mppi_sandbox import tracking_instrumentation as ti


class TestConstitution:
    def test_six_classes_in_north_star_order(self):
        assert oi.NORTH_STAR_CLASSES == (
            "static", "dynamic", "다중", "가까운", "가려진", "의외",
        )

    def test_every_class_is_either_derivable_or_unmeasurable(self):
        """No class may fall through both tables — that is how one goes unasked."""
        covered = set(oi.DERIVATION) | set(oi.UNMEASURABLE_CLASSES)
        assert covered == set(oi.NORTH_STAR_CLASSES)

    def test_derivation_and_unmeasurable_are_disjoint(self):
        assert not (set(oi.DERIVATION) & set(oi.UNMEASURABLE_CLASSES))

    def test_clause_kinds_differ_is_derived_not_asserted(self):
        """The module's whole premise, read off the two clause lists."""
        assert oi.clause_kinds_differ() is True
        assert oi.verdict() == "CLAUSE_KINDS_DIFFER"

    def test_tracking_clauses_all_have_readers_obstacle_classes_none_do(self):
        """The asymmetry `clause_kinds_differ` compresses, spelled out."""
        from eval import path_tracking_metrics

        assert all(ti.reader_for(c) is not None for c in ti.NORTH_STAR_CLAUSES)
        assert all(
            getattr(path_tracking_metrics, c, None) is None
            for c in oi.NORTH_STAR_CLASSES
        )

    def test_premise_goes_false_if_an_obstacle_class_gains_a_metric(self, monkeypatch):
        """Tamper: the premise must be falsifiable by the thing that would falsify it."""
        from eval import path_tracking_metrics

        monkeypatch.setattr(
            path_tracking_metrics, "static", lambda *a, **k: 0.0, raising=False,
        )
        assert oi.clause_kinds_differ() is False
        assert oi.verdict() == "CLAUSE_KINDS_MATCH"


class TestScenePool:
    def test_pool_is_the_contract_s_own_obstacle_pool(self):
        """One population, shared by construction — D-491's lesson."""
        assert oi._scene_pool() == cc.scenes("obstacle")

    def test_pool_is_five_scenes(self):
        assert len(oi._scene_pool()) == 5


class TestMembership:
    def test_no_scene_has_a_static_obstacle(self):
        """The finding: every obstacle in the measured surface moves."""
        assert all(oi.static_obstacles(s) == 0 for s in oi._scene_pool())
        assert oi.scenes_for("static") == ()

    def test_every_scene_has_a_moving_obstacle(self):
        assert all(oi.moving_obstacles(s) > 0 for s in oi._scene_pool())
        assert len(oi.scenes_for("dynamic")) == 5

    def test_multiple_requires_two_movers(self):
        for s in oi.scenes_for("다중"):
            assert oi.moving_obstacles(s) >= 2

    def test_close_scenes_have_an_arm_at_or_under_the_declared_budget(self):
        for s in oi.scenes_for("가까운"):
            budget = oi.declared_clearance_budget(s)
            assert budget is not None
            assert min(oi.measured_clearances(s).values()) <= budget

    def test_non_close_scenes_have_every_arm_above_budget(self):
        """The complement — a coverage census is only honest in both directions.

        This test is the reason `exercises` returns `None` for a scene with no
        declared budget: written as a plain complement it failed, and what it
        had caught was `cafe_freezing_v0` being counted as a *non-close* scene
        when it had never been asked.
        """
        close = set(oi.scenes_for("가까운"))
        unasked = set(oi.unaskable_scenes("가까운"))
        for s in oi._scene_pool():
            if s in close or s in unasked:
                continue
            budget = oi.declared_clearance_budget(s)
            assert budget is not None
            assert min(oi.measured_clearances(s).values()) > budget

    def test_a_scene_with_no_declared_budget_is_unasked_not_answered(self):
        assert oi.unaskable_scenes("가까운") == ("cafe_freezing_v0",)
        assert oi.exercises("가까운", "cafe_freezing_v0") is None
        assert oi.declared_clearance_budget("cafe_freezing_v0") is None

    def test_unasked_scene_is_absent_from_both_close_answers(self):
        """Neither close nor non-close — absence is the encoding."""
        s = "cafe_freezing_v0"
        assert s not in oi.scenes_for("가까운")
        hits, askable = oi.askable_coverage("가까운")
        assert (hits, askable) == (3, 4)
        assert askable < len(oi._scene_pool())

    def test_derivable_classes_other_than_close_are_askable_everywhere(self):
        """The narrowing is specific to 가까운, not a property of the pool."""
        for cls in ("static", "dynamic", "다중"):
            assert oi.unaskable_scenes(cls) == ()

    def test_unmeasurable_classes_return_none_not_false(self):
        """`None` says nothing can answer; `False` would say it was asked."""
        for cls in oi.UNMEASURABLE_CLASSES:
            for s in oi._scene_pool():
                assert oi.exercises(cls, s) is None

    def test_unknown_class_raises(self):
        with pytest.raises(KeyError):
            oi.exercises("nonexistent", oi._scene_pool()[0])

    def test_close_follows_the_scene_s_own_budget(self, monkeypatch):
        """Tamper: drop every budget to 0 and no scene may still read close."""
        monkeypatch.setattr(oi, "declared_clearance_budget", lambda s: 0.0)
        assert oi.scenes_for("가까운") == ()
        assert oi.unaskable_scenes("가까운") == ()

    def test_close_is_not_vacuously_true(self, monkeypatch):
        """Tamper the other way: a huge budget makes every scene close."""
        monkeypatch.setattr(oi, "declared_clearance_budget", lambda s: 1e6)
        assert len(oi.scenes_for("가까운")) == len(oi._scene_pool())

    def test_dynamic_follows_the_schedule_not_the_count(self, monkeypatch):
        """Tamper: strip schedules and `dynamic` must empty while `static` fills."""
        real = oi._obstacles

        def frozen(scene):
            obs = real(scene)
            for o in obs:
                o.schedule = o.schedule[:0]
            return obs

        monkeypatch.setattr(oi, "_obstacles", frozen)
        assert oi.scenes_for("dynamic") == ()
        assert oi.scenes_for("다중") == ()
        assert len(oi.scenes_for("static")) == 5


class TestCoverage:
    def test_covered_uncovered_unmeasurable_partition_the_classes(self):
        parts = (
            set(oi.covered_classes())
            | set(oi.uncovered_classes())
            | set(oi.unmeasurable_classes())
        )
        assert parts == set(oi.NORTH_STAR_CLASSES)

    def test_the_three_buckets_are_pairwise_disjoint(self):
        a, b, c = (
            set(oi.covered_classes()),
            set(oi.uncovered_classes()),
            set(oi.unmeasurable_classes()),
        )
        assert not (a & b) and not (b & c) and not (a & c)

    def test_static_is_uncovered_not_unmeasurable(self):
        """It is derivable and simply has no scene — an authoring gap, not a build."""
        assert oi.uncovered_classes() == ("static",)

    def test_occluded_and_surprise_are_unmeasurable(self):
        assert oi.unmeasurable_classes() == ("가려진", "의외")

    def test_coverage_is_three_of_six(self):
        assert oi.coverage() == (3, 6)

    def test_line_coverage_reads_the_shipped_line_not_a_retyped_one(self):
        line, covered, total = oi.line_class_coverage()
        assert line == cc.contract_line("obstacle")[0] == "cbf_mppi"
        assert (covered, total) == (3, 6)

    def test_the_line_sweeps_every_scene_but_only_half_the_classes(self):
        """The headline, stated as the two numbers side by side."""
        assert cc.CENSUS["obstacle_total_order"] == "yes"
        assert len(oi._scene_pool()) == 5
        assert oi.coverage()[0] < len(oi.NORTH_STAR_CLASSES)

    def test_gap_shapes_differ_between_the_two_classes(self):
        """The planning consequence: a build on one side, a purchase on the other."""
        obstacle, tracking = oi.gap_shapes()
        assert obstacle == "unmeasurable"
        assert tracking == "unbought"
        assert obstacle != tracking

    def test_tracking_gap_shape_tracks_its_own_module(self):
        """Not retyped — it follows `tracking_instrumentation`'s live population."""
        assert ti.unbought_clauses() == ("heading error",)
        assert oi.gap_shapes()[1] == "unbought"


class TestCensus:
    def test_pinned_census_matches_live(self):
        assert oi.drift() == ()

    def test_census_keys_match_the_pin(self):
        assert set(oi.census()) == set(oi.CENSUS)

    def test_drift_fires_when_the_pin_is_wrong(self, monkeypatch):
        monkeypatch.setitem(oi.CENSUS, "line_class_coverage", "cbf_mppi 6/6")
        assert any("line_class_coverage" in d for d in oi.drift())

    def test_format_table_names_every_class(self):
        table = oi.format_table()
        for c in oi.NORTH_STAR_CLASSES:
            assert c in table

    def test_format_table_prices_the_unmeasurable_classes(self):
        """The artefact each needs must be visible in the table, not just the code."""
        table = oi.format_table()
        for need in oi.UNMEASURABLE_CLASSES.values():
            assert need in table


class TestLineSpanVsPoolSpan:
    """The headline's population: what the line *leads*, not what the pool *has*.

    `line_class_coverage` originally sourced its fraction from `coverage()` —
    the whole pool — and read correctly only because `cbf_mppi`'s order over
    the pool is total. These tests pin the distinction *and* the coincidence,
    so the day the coincidence ends the census says so instead of inflating
    (D-493).
    """

    def test_line_leads_every_pool_scene_today(self):
        """The coincidence's cause, stated as its own fact."""
        line, _ = cc.contract_line("obstacle")
        assert line == "cbf_mppi"
        assert oi.scenes_led_by(line) == oi._scene_pool()

    def test_line_classes_are_the_classes_of_the_led_scenes(self):
        assert oi.line_classes() == ("dynamic", "다중", "가까운")

    def test_headline_counts_line_classes_not_pool_classes(self):
        line, covered, total = oi.line_class_coverage()
        assert (line, covered, total) == ("cbf_mppi", 3, 6)
        assert covered == len(oi.line_classes())

    def test_span_coincidence_holds_today(self):
        assert oi.line_span_is_pool_span() is True

    def test_scenes_led_by_a_losing_arm_is_empty(self):
        """`scenes_led_by` must be able to return nothing, or it pins nothing."""
        assert oi.scenes_led_by("no_such_arm") == ()

    def _stage_unled_static_scene(self, monkeypatch):
        """Add a static scene to the pool that the line does *not* lead.

        This is exactly STATE's next planned action (author a static scene) in
        the direction that breaks the coincidence.
        """
        fake = "cafe_static_probe_v0"
        pool = oi._scene_pool() + (fake,)
        cols = dict(cc.columns("obstacle"))
        cols[fake] = {"cbf_mppi": 0.10, "social_mppi": 0.90}
        monkeypatch.setattr(oi, "_scene_pool", lambda: pool)
        monkeypatch.setattr(
            cc, "columns",
            lambda cls, gated=True: cols if cls == "obstacle" else {},
        )
        real_exercises = oi.exercises
        monkeypatch.setattr(
            oi, "exercises",
            lambda c, s: (c == "static") if s == fake else real_exercises(c, s),
        )
        return fake

    def test_tamper_unled_static_scene_breaks_the_coincidence(self, monkeypatch):
        self._stage_unled_static_scene(monkeypatch)
        assert oi.line_span_is_pool_span() is False

    def test_tamper_unled_static_scene_does_not_inflate_the_headline(self, monkeypatch):
        """The whole point: the pool gains a class, the line does not."""
        self._stage_unled_static_scene(monkeypatch)
        assert "static" in oi.covered_classes()
        assert "static" not in oi.line_classes()
        _, covered, _ = oi.line_class_coverage()
        assert covered == 3, "line span must not follow the pool"
        assert len(oi.covered_classes()) == 4

    def test_tamper_line_leading_static_scene_does_move_the_headline(self, monkeypatch):
        """The honest direction still works — coverage the line *earns* counts."""
        fake = "cafe_static_probe_v0"
        pool = oi._scene_pool() + (fake,)
        cols = dict(cc.columns("obstacle"))
        cols[fake] = {"cbf_mppi": 0.90, "social_mppi": 0.10}
        monkeypatch.setattr(oi, "_scene_pool", lambda: pool)
        monkeypatch.setattr(
            cc, "columns",
            lambda cls, gated=True: cols if cls == "obstacle" else {},
        )
        real_exercises = oi.exercises
        monkeypatch.setattr(
            oi, "exercises",
            lambda c, s: (c == "static") if s == fake else real_exercises(c, s),
        )
        assert "static" in oi.line_classes()
        _, covered, _ = oi.line_class_coverage()
        assert covered == 4
        assert oi.line_span_is_pool_span() is True

    def test_census_ships_both_the_span_and_the_coincidence(self):
        c = oi.census()
        assert c["line_classes"] == "dynamic,다중,가까운"
        assert c["line_span_is_pool_span"] == "true"
