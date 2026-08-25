"""Tests for :mod:`eval.mppi_sandbox.assert_reach`.

The load-bearing one is :class:`TestTheKnownAnswerIsRecovered`.  This module was
written to generalise D-101, and D-101 is the only site whose answer is known
independently — so a scan that cannot recover it is measuring something else.
The first cut could not: it matched CI's printed assertion text by operator
shape, pinned 3 of 14 rows, and missed D-101's own.  That failure is what the
recorded line numbers exist to fix, and this class is what keeps it fixed.
"""

from __future__ import annotations

import ast

import pytest

from eval.mppi_sandbox import assert_reach as ar
from eval.mppi_sandbox import simd_attribution as sa

D101_SITE = (
    "eval/mppi_sandbox/tests/test_exclusion_scope.py"
    "::test_the_exclusion_list_manufactured_exactly_two_candidates"
)


class TestClaimShapes:
    @pytest.mark.parametrize(
        "src,kind",
        [
            ("assert set(a) <= set(b)", ar.SUBSET),
            ("assert a >= b", ar.SUBSET),
            ("assert set(a).issubset(b)", ar.SUBSET),
            ("assert {x.site for x in a} == {'one', 'two'}", ar.SET_EQUALITY),
            ("assert len(a) == 6", ar.CARDINALITY),
            ("assert 0 < len(a) < len(b)", ar.CARDINALITY),
            ("assert a > b", ar.OTHER),
            ("assert isinstance(a, int)", ar.OTHER),
        ],
    )
    def test_shapes_grade_as_documented(self, src: str, kind: str) -> None:
        node = ast.parse(src).body[0]
        assert isinstance(node, ast.Assert)
        assert ar.classify(node.test) == kind

    def test_a_numeric_bound_is_not_a_containment(self) -> None:
        """``ratio <= 1.0`` is an ordinary bound, and grading it :data:`SUBSET`
        would flood the census with rows that were never the defect."""
        node = ast.parse("assert ratio <= 1.0").body[0]
        assert isinstance(node, ast.Assert)
        assert ar.classify(node.test) == ar.OTHER


class TestTheKnownAnswerIsRecovered:
    """The negative control: D-101's line must fall out of the scan."""

    def test_d101s_site_is_pinned(self) -> None:
        assert ar.failing_ordinal(D101_SITE) == 0

    def test_d101s_assertion_is_reported_shielded(self) -> None:
        rows = [s for s in ar.shielded() if s.failure_id == D101_SITE]
        assert len(rows) == 1
        assert "manufactured_candidates" in rows[0].assertion.text
        assert rows[0].assertion.kind == ar.SUBSET

    def test_the_shielded_reading_is_taken_at_the_run_commit(self) -> None:
        """D-043 in a new place.  ``test_exclusion_scope.py`` has been edited
        since the run, so reading it at HEAD would describe a tree that job
        never executed — and the edit was D-101's own repair, which *deleted*
        the shielded statement.  Read at HEAD the finding disappears."""
        assert D101_SITE.split("::")[0] in ar.MOVED_FILES
        at_run = [t for _, _, t, _k in ar._asserts_at_run(D101_SITE)]
        assert any("manufactured_candidates(effect)) <=" in t for t in at_run)


class TestTheCensusIsFullyPinned:
    def test_every_assertion_row_pins(self) -> None:
        """An ``ASSERTION`` row that will not pin is a transcription gap, not a
        fact about the run."""
        unpinnable = [
            f.test_id for f in sa.CI_FAILURES
            if f.attributable and ar.failing_ordinal(f.test_id) is None
        ]
        assert unpinnable == [], f"assertion rows without a recorded line: {unpinnable}"

    def test_the_residue_is_exactly_the_timeouts(self) -> None:
        """The six rows the scan cannot place are the ones with no failing
        statement to be shielded *by* — a property of the failure mode, not a
        deficiency of the matcher."""
        residue = set(ar.unpinned())
        timeouts = {f.test_id for f in sa.CI_FAILURES if f.cause == sa.TIMEOUT}
        assert residue == timeouts

    def test_the_transcription_still_describes_its_tree(self) -> None:
        """Every recorded line still holds the recorded text at the run commit.
        Non-empty means the ordinals below it are fabrications."""
        assert ar.moved() == ()

    def test_the_recorded_keys_are_census_rows(self) -> None:
        """A key that is not in the census pins nothing and is silently inert —
        three of the eight were exactly that when first transcribed, because the
        job log prints ``file.py:NNN`` without the enclosing class."""
        census = {f.test_id for f in sa.CI_FAILURES}
        assert set(ar.FAILED_AT) <= census

    def test_the_position_table_is_derived_not_a_second_transcription(self) -> None:
        """D-104.  ``FAILED_AT`` used to be a hand-kept table in this module.

        The subset check above was the strongest thing sayable about it while it
        was hand-kept — it caught a key that named nothing, but not a census row
        that this table simply never grew an entry for.  That is the direction the
        omission actually ran: the census had all fourteen rows and the position
        table had eight, and nothing anywhere said the eight were the right eight.
        Now the position is a field of the census row, so the two cannot disagree
        and this asserts the *equality* the subset could not.
        """
        assert set(ar.FAILED_AT) == {f.test_id for f in sa.located()}
        for f in sa.located():
            assert ar.FAILED_AT[f.test_id] == (f.lineno, f.statement)

    def test_the_run_commit_is_the_censuss_own(self) -> None:
        """Re-exported, not re-typed: one commit string, one place it is stated."""
        assert ar.RUN_COMMIT == sa.RUN_COMMIT
        assert ar.RUN_ID == sa.RUN_ID


class TestTheShieldedPopulation:
    def test_the_reading_is_two_sites(self) -> None:
        """Pinned, so a change to the census or the corpus announces itself.

        Two is small, and that is a result rather than a disappointment: six of
        the eight failures were their function's *last* assertion, so there was
        nothing behind them to shield.  The hazard is real and rare.
        """
        rows = ar.shielded()
        assert len(rows) == 2
        assert {s.assertion.lineno for s in rows} == {172, 294}

    def test_one_is_a_population_claim_and_one_is_not(self) -> None:
        """The reason nothing filters on :data:`POPULATION_KINDS`.  Filtering to
        the D-100/D-101 shape drops the scalar row, and the scalar row is the
        conclusion of its own test — the statement its docstring calls section
        3's counterexample, never once evaluated."""
        rows = ar.shielded()
        assert sum(s.assertion.is_population_claim for s in rows) == 1
        scalar = [s for s in rows if not s.assertion.is_population_claim]
        assert len(scalar) == 1
        assert "understatement > audited.understatement" in scalar[0].assertion.text

    def test_shielded_assertions_come_after_their_failure(self) -> None:
        for s in ar.shielded():
            assert s.assertion.ordinal > s.failed_at

    def test_census_totals_agree_with_the_rows(self) -> None:
        rows = ar.shielded()
        assert sum(ar.census(rows).values()) == len(rows)


class TestLoopBodyAssertions:
    """STATE #2 — the other under-evaluated population, independent of failure."""

    def test_a_loop_body_assert_is_detected(self, tmp_path) -> None:
        path = tmp_path / "test_probe.py"
        path.write_text(
            "def test_x():\n"
            "    assert 1\n"
            "    for s in sites():\n"
            "        assert set(s.a) <= set(s.b)\n",
            encoding="utf-8",
        )
        rows = ar.sampled((path,))
        assert len(rows) == 1
        assert rows[0].in_loop and rows[0].kind == ar.SUBSET

    def test_a_top_level_assert_is_not_sampled(self, tmp_path) -> None:
        """The control: without it, a detector that returned every assertion
        would pass the test above."""
        path = tmp_path / "test_probe.py"
        path.write_text("def test_x():\n    assert set(a) <= set(b)\n", encoding="utf-8")
        assert ar.sampled((path,)) == ()

    def test_the_corpus_reading_is_non_empty(self) -> None:
        """Not pinned to a count — the corpus grows every cycle and a pinned
        number here would be re-baselined rather than read."""
        rows = ar.sampled()
        assert len(rows) > 0
        assert all(a.in_loop for a in rows)


class TestReport:
    def test_report_names_both_shielded_rows(self) -> None:
        text = ar.report()
        assert "manufactured_candidates" in text
        assert "understatement" in text

    def test_report_publishes_the_residue(self) -> None:
        text = ar.report()
        for test_id in ar.unpinned():
            assert test_id.split("::")[-1] in text

    def test_main_rejects_an_unknown_verb(self) -> None:
        assert ar.main(["nonsense"]) == 2
