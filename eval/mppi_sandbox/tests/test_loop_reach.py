"""Tests for :mod:`loop_reach` — does the counter count what it says it counts?

The first test here is the one whose answer is known independently (D-102's
lesson): a loop over ``()`` containing a population assertion must come back
``EMPTY``, and a ``@pytest.mark.skip``-ed one must come back ``NOT_RUN``.  If the
instrument cannot tell those two apart it is not measuring vacuity, it is
measuring absence, and every ``slow``-marked test in the corpus would be
published as a finding.

The controls run under a real ``pytest`` subprocess rather than ``exec`` because
pytest **rewrites** assert statements, and a line counter that agreed with bare
``exec`` but disagreed with the rewriter would be wrong about the only execution
anyone cares about.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from eval.mppi_sandbox import assert_reach as ar
from eval.mppi_sandbox import loop_reach as lr

# --------------------------------------------------------------------------
# The control corpus.  Every loop below carries a *population* claim, so
# `targets()` picks it up; the element counts are written down here and are the
# answer the instrument has to reproduce.
# --------------------------------------------------------------------------

CONTROL = '''\
import pytest


def test_empty_loop():
    for x in ():
        assert set(x) <= {1, 2}


def test_singleton_loop():
    for x in ({1},):
        assert x <= {1, 2}


def test_three_loop():
    for x in ({1}, {2}, {3}):
        assert x <= {1, 2, 3}


@pytest.mark.skip(reason="control: this one never runs")
def test_skipped_loop():
    for x in ({1},):
        assert x <= {1}


def test_nested_inner_empty():
    for outer in (1, 2, 3):
        for inner in ():
            assert set(inner) <= {1}
'''

#: name -> (expected grade, expected element count).  Written down before the
#: instrument was pointed at them.
EXPECTED: dict[str, tuple[str, int]] = {
    "test_empty_loop": (lr.EMPTY, 0),
    "test_singleton_loop": (lr.SINGLETON, 1),
    "test_three_loop": (lr.SAMPLED, 3),
    "test_skipped_loop": (lr.NOT_RUN, 0),
    "test_nested_inner_empty": (lr.EMPTY, 0),
}


@pytest.fixture(scope="module")
def control_file(tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("loop_reach_control") / "test_control_corpus.py"
    path.write_text(CONTROL, encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def control_rows(control_file, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("loop_reach_run")
    return lr.run(tmp=tmp, paths=(control_file,))


def _by_name(rows) -> dict[str, tuple[str, int]]:
    return {t.test_id.split("::")[-1]: (g, n) for t, g, n in rows}


# --------------------------------------------------------------------------
# 1. The negative controls.
# --------------------------------------------------------------------------


def test_every_control_loop_is_reached_as_a_target(control_rows):
    """All five controls are population claims — the reading covers them."""
    assert set(_by_name(control_rows)) == set(EXPECTED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_control_grades_match_the_written_down_answer(control_rows, name):
    assert _by_name(control_rows)[name] == EXPECTED[name]


def test_empty_and_skipped_are_distinguished(control_rows):
    """The load-bearing discrimination: vacuity is not absence.

    Both are zero executions of the assert.  Only one is a finding.  If this
    collapses, every ``slow``-marked test in the corpus reads as vacuous.
    """
    got = _by_name(control_rows)
    assert got["test_empty_loop"][0] == lr.EMPTY
    assert got["test_skipped_loop"][0] == lr.NOT_RUN
    assert got["test_empty_loop"][0] != got["test_skipped_loop"][0]


def test_nested_loop_pins_the_inner_header(control_rows):
    """An outer loop that ran 3× must not mask an inner loop that ran 0×."""
    assert _by_name(control_rows)["test_nested_inner_empty"] == (lr.EMPTY, 0)


# --------------------------------------------------------------------------
# 2. The target set itself.
# --------------------------------------------------------------------------


def test_targets_are_exactly_assert_reachs_population_loop_asserts():
    """No second definition of "population claim" — one statement of it."""
    want = {(a.test_id, a.lineno)
            for a in ar.sampled() if a.is_population_claim}
    got = {(t.test_id, t.assert_line) for t in lr.targets()}
    assert got == want


def test_every_target_has_a_loop_header_above_its_assert():
    for t in lr.targets():
        assert t.loop_line < t.assert_line, t


def test_loop_header_lines_really_are_loop_statements():
    """The discriminator is only sound if the watched line is the ``for``."""
    for t in lr.targets():
        tree = ast.parse(t.path.read_text(encoding="utf-8"))
        headers = {n.lineno for n in ast.walk(tree)
                   if isinstance(n, (ast.For, ast.While, ast.AsyncFor))}
        assert t.loop_line in headers, t


def test_loop_header_is_the_innermost_enclosing_one():
    """Outermost would report a nested-empty loop as sampled — the control
    ``test_nested_inner_empty`` is the case, checked here structurally too."""
    for t in lr.targets():
        tree = ast.parse(t.path.read_text(encoding="utf-8"))
        enclosing = [
            n.lineno for n in ast.walk(tree)
            if isinstance(n, (ast.For, ast.While, ast.AsyncFor))
            and any(isinstance(c, ast.Assert) and c.lineno == t.assert_line
                    for c in ast.walk(n))
        ]
        assert t.loop_line == max(enclosing), t


# --------------------------------------------------------------------------
# 3. Grading arithmetic, independent of any run.
# --------------------------------------------------------------------------


def _target(tmp_path: Path) -> lr.Target:
    p = tmp_path / "t.py"
    p.write_text("x\n", encoding="utf-8")
    return lr.Target(test_id=f"{p}::test_x", kind=ar.SUBSET,
                     assert_line=10, loop_line=9, text="assert a <= b")


@pytest.mark.parametrize("loop,hits,want", [
    (0, 0, (lr.NOT_RUN, 0)),
    (1, 0, (lr.EMPTY, 0)),
    (1, 1, (lr.SINGLETON, 1)),
    (1, 7, (lr.SAMPLED, 7)),
    (4, 2, (lr.SAMPLED, 2)),
])
def test_grade_table(tmp_path, loop, hits, want):
    t = _target(tmp_path)
    resolved = str(t.path.resolve())
    counts = {f"{resolved}:{t.loop_line}": loop, f"{resolved}:{t.assert_line}": hits}
    assert lr.grade(t, counts) == want


def test_missing_counts_read_as_not_run(tmp_path):
    """A run that produced no counts file must not read as a corpus of
    vacuities — absence of measurement is ``NOT_RUN``, never ``EMPTY``."""
    assert lr.grade(_target(tmp_path), {}) == (lr.NOT_RUN, 0)


def test_unevaluated_is_exactly_the_zero_element_grades():
    assert lr.UNEVALUATED == {lr.NOT_RUN, lr.EMPTY}
    assert lr.SINGLETON not in lr.UNEVALUATED


def test_unevaluated_is_derived_from_the_grader_not_copied_out_of_it(monkeypatch):
    """D-104.  The set is recomputed by calling :func:`grade`, not typed beside it.

    Shipped as a literal, it was a ``TYPED`` allow-list with no module-level
    enumerator — ``guard_reflexivity.unwatched_exemptions`` went five-to-six
    within one test run of it being written, which is D-073 / D-080 / D-101's
    second-order cost for a fourth time.  The assertion above cannot tell the
    two apart: a copied literal and a derived set have the same value until the
    grader changes, which is exactly when a copy stops being right.

    So this asserts the *dependency* rather than the value.  Renaming what
    ``grade`` returns for the zero-element cases must move the set with it; if
    this test can be made to pass with the grader saying something else, the set
    is a copy again.
    """
    monkeypatch.setattr(lr, "EMPTY", "NO_ELEMENTS_AT_ALL")
    assert lr.unevaluated_grades() == {lr.NOT_RUN, "NO_ELEMENTS_AT_ALL"}


def test_the_derivation_covers_both_ways_of_seeing_no_element():
    """``NOT_RUN`` and ``EMPTY`` are different facts and both must be probed.

    A derivation that only ran the "nothing ran" probe would return a
    one-element set and still look derived.  This is the negative control for
    the probe list, not for the grader.
    """
    assert len(lr.unevaluated_grades()) == 2
    assert lr.SAMPLED not in lr.unevaluated_grades()


def test_census_totals_every_row(control_rows):
    c = lr.census(control_rows)
    assert sum(c.values()) == len(control_rows)
    assert set(c) == set(lr.GRADES)


# --------------------------------------------------------------------------
# 4. The counter's own mechanism.
# --------------------------------------------------------------------------


def test_measure_returns_empty_when_nothing_is_watched(control_file, tmp_path):
    """Watching no line is not the same as the run failing — the plugin still
    writes a (empty) counts file, so callers can tell the two apart."""
    assert lr.measure((str(control_file),), (), tmp_path) == {}


def test_counts_survive_pytest_assert_rewriting(control_file, tmp_path):
    """The rewriter must preserve the assert's line number, or every count is
    attributed to the wrong statement.  Checked head-on, not assumed."""
    tgt = lr.targets((control_file,))
    three = next(t for t in tgt if t.test_id.endswith("test_three_loop"))
    counts = lr.measure(
        (str(control_file),),
        ((str(three.path.resolve()), three.assert_line),),
        tmp_path,
    )
    assert counts.get(f"{str(three.path.resolve())}:{three.assert_line}") == 3


def test_deselecting_a_test_reads_as_not_run(control_file, tmp_path):
    """``-k`` filtering is the third way to get zero, and it is absence too."""
    rows = lr.run(tmp=tmp_path, paths=(control_file,), extra=("-k", "three"))
    got = _by_name(rows)
    assert got["test_three_loop"] == (lr.SAMPLED, 3)
    assert got["test_empty_loop"][0] == lr.NOT_RUN, (
        "a deselected test must not be reported as a vacuous loop")


# --------------------------------------------------------------------------
# 5. The recorded reading — a drift guard, at zero runtime cost.
# --------------------------------------------------------------------------


def test_recorded_reading_covers_exactly_todays_targets():
    """A new population-claim loop must force a re-measurement.

    The reading costs ~90 s to take, so it is not re-taken every suite run.
    What *is* checked every run is that the corpus has not grown a claim the
    reading never saw — which is the only way :data:`READING` can quietly stop
    describing the thing it names.
    """
    want = {t.test_id.split("::")[-1] for t in lr.targets()}
    assert set(lr.READING) == want, (
        "the population-claim loop set moved — re-run "
        "`python3 -m eval.mppi_sandbox.loop_reach report` and update READING")


def test_the_reading_found_no_vacuity():
    """The finding itself, pinned: nothing here was under-evaluated.

    If a future edit makes one of these loops empty, this is what goes red —
    which is the whole reason an empty reading is worth recording (D-076/D-081)
    rather than noting "found nothing" in a journal and moving on.
    """
    assert all(g not in lr.UNEVALUATED for g, _ in lr.READING.values())
    assert all(n >= 2 for _, n in lr.READING.values()), (
        "a population claim established on one element is D-101's grammar")


def test_slow_only_rows_are_named_and_real():
    """The caveat is machine-checkable: every ``SLOW_ONLY`` name is a real row,
    so the prose cannot drift away from the set it describes."""
    assert lr.SLOW_ONLY <= set(lr.READING)
    for name in lr.SLOW_ONLY:
        assert lr.READING[name][0] == lr.SAMPLED


# --------------------------------------------------------------------------
# 6. The report.
# --------------------------------------------------------------------------


def test_report_names_every_unevaluated_row(control_rows):
    """A grade nobody prints is not a reading.

    The expected count is *derived* from :data:`EXPECTED` rather than written
    twice: the first draft hard-coded 2 and the instrument said 3, and the
    instrument was right — ``test_nested_inner_empty`` is the third.  A count
    restated by hand is a second source of truth that can only ever be wrong.
    """
    want = {n for n, (g, _) in EXPECTED.items() if g in lr.UNEVALUATED}
    got = {t.test_id.split("::")[-1] for t, g, _ in control_rows
           if g in lr.UNEVALUATED}
    assert got == want
