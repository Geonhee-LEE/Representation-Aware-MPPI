"""STATE #1: which guard clauses has the suite never made fire? (D-059).

Each test states a fact that would have to change for the module's conclusion to
change, rather than pinning today's counts.  The counts live in the journal.

The one exception is :data:`guard_vacuity.CALIBRATION`, which is ground truth
rather than a count: D-058's guard is *known* to have been unfirable and *known*
to have been fixed, so a scan that cannot score it ``FIRES`` is broken in a way
no synthetic fixture would reveal.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import guard_vacuity as gv


@pytest.fixture(scope="module")
def clauses():
    return gv.guard_clauses()


def _plant(root: Path, name: str, source: str) -> Path:
    path = root / f"{name}.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# The population the scan walks
# --------------------------------------------------------------------------

def test_calibration_member_is_discovered(clauses):
    """D-058's guard is in the population, or the scan cannot see its own origin.

    A scan built from one finding that cannot rediscover that finding is
    D-045's shape — a registry checked against a population too small to hold
    its omissions.
    """
    sites = {(c.module, c.function, c.exception) for c in clauses}
    for key in gv.CALIBRATION:
        assert key in sites, f"{key} not discovered — the scan cannot see D-058"


def test_calibration_set_is_one_not_four():
    """The four findings of this shape are not four members of this population.

    D-055/D-056/D-057 are a fixture reading, a verdict comparison and a boolean
    bar; none is an ``if ...: raise``.  If someone widens CALIBRATION to four
    without widening the scan, the mirror starts asserting over guards that
    cannot exist and goes permanently red.
    """
    assert len(gv.CALIBRATION) == 1


def test_scan_is_derived_not_typed(tmp_path):
    """A guard nobody typed into this package is still found.

    Five hand-written registries in this package have come up short (D-045,
    D-046, D-047, D-050, D-052).  This one is computed from the AST, which is
    only demonstrable against source the module has never seen.
    """
    _plant(tmp_path, "planted", """
        def f(x):
            if x < 0:
                raise ValueError("negative")
            return x
    """)
    found = gv.guard_clauses(tmp_path)
    assert [(c.module, c.function, c.exception, c.condition) for c in found] == [
        ("planted", "f", "ValueError", "x < 0")
    ]


def test_unconditional_raises_are_excluded_and_reported(tmp_path):
    """``raise NotImplementedError`` is not a guard, and the refusal is counted.

    Its trigger is "the function ran", so it cannot be vacuous in STATE #1's
    sense.  Dropping it silently would leave the scanned population unstated —
    the omission D-045 through D-052 kept finding.
    """
    _plant(tmp_path, "mixed", """
        def abstract(self):
            raise NotImplementedError

        def guarded(x):
            if not x:
                raise ValueError("empty")
    """)
    assert [c.function for c in gv.guard_clauses(tmp_path)] == ["guarded"]
    assert [c.function for c in gv.unconditional(tmp_path)] == ["abstract"]


def test_bare_reraise_is_not_a_guard(tmp_path):
    """``raise`` with no exception re-raises; it asserts nothing about inputs."""
    _plant(tmp_path, "rethrow", """
        def f(x):
            try:
                return 1 / x
            except ZeroDivisionError:
                if x == 0:
                    raise
    """)
    assert gv.guard_clauses(tmp_path) == ()
    assert gv.unconditional(tmp_path) == ()


def test_innermost_if_is_the_condition(tmp_path):
    """Where guards nest, the reported condition is the one that decides.

    The outer test is a precondition for reaching the guard; the inner one is
    the trigger.  Reporting the outer would misdescribe what has to be true for
    the raise to fire — the exact question a vacuity triage asks.
    """
    _plant(tmp_path, "nested", """
        def f(a, b):
            if a is not None:
                if b < 0:
                    raise ValueError("b")
    """)
    assert gv.guard_clauses(tmp_path)[0].condition == "b < 0"


def test_tests_directory_is_not_a_subject():
    """A guard clause in a test is that test's assertion machinery.

    Scanning them would flood the candidate set with raises whose whole purpose
    is to fire on a failure that is *supposed* not to occur.
    """
    assert all("tests" not in c.path.parts for c in gv.guard_clauses())


# --------------------------------------------------------------------------
# The partition
# --------------------------------------------------------------------------

def _one(tmp_path, source):
    path = _plant(tmp_path, "subject", source)
    return gv.guard_clauses(tmp_path)[0], path


GUARD_SOURCE = """
    def f(x):
        y = x + 1
        if y < 0:
            raise ValueError("negative")
        return y
"""


def test_fires_when_the_raise_line_executed(tmp_path):
    clause, path = _one(tmp_path, GUARD_SOURCE)
    verdict = gv.classify([clause], {path: frozenset({clause.lineno})})[0]
    assert verdict.verdict == gv.VERDICT_FIRES
    assert not verdict.is_candidate


def test_never_fired_when_the_function_ran_but_the_raise_did_not(tmp_path):
    """The candidate verdict: the guard was offered inputs and declined them.

    This is the state D-058's guard sat in for twenty-two days.
    """
    clause, path = _one(tmp_path, GUARD_SOURCE)
    verdict = gv.classify([clause], {path: clause.body_lines})[0]
    assert verdict.verdict == gv.VERDICT_NEVER_FIRED
    assert verdict.is_candidate


def test_unreached_is_not_folded_into_never_fired(tmp_path):
    """A guard in a function nothing called has told us nothing.

    D-050's rule: a probe that cannot separate "not asked" from "asked and
    silent" has measured nothing.  :mod:`probe_reach` keeps ``UNDECIDABLE``
    apart from ``MUTE_FIXTURE`` for this reason and so does this.
    """
    clause, path = _one(tmp_path, GUARD_SOURCE)
    verdict = gv.classify([clause], {path: frozenset()})[0]
    assert verdict.verdict == gv.VERDICT_UNREACHED
    assert not verdict.is_candidate


def test_a_guard_only_function_is_still_scored(tmp_path):
    """A function that is *nothing but* a guard must not read ``UNREACHED``.

    Its only non-raise statement is the ``if`` itself, which executes whenever
    the function runs.  If ``body_lines`` excluded the ``if`` test, every such
    guard would score ``UNREACHED`` and drop out of the candidate set —
    silently, and exactly for the guards with the least around them to hide in.
    """
    clause, path = _one(tmp_path, """
        def check(x):
            if not x:
                raise ValueError("empty")
    """)
    assert clause.body_lines
    got = gv.classify([clause], {path: clause.body_lines})[0]
    assert got.verdict == gv.VERDICT_NEVER_FIRED


def test_a_nested_functions_lines_are_not_the_outer_functions(tmp_path):
    """A closure running is not evidence that its definer's guard was offered.

    Counting the inner body as the outer's would score the outer guard
    ``NEVER_FIRED`` on evidence belonging to a function someone else invoked —
    a candidate set contaminated by exactly the confusion the ``UNREACHED``
    verdict exists to prevent.
    """
    _plant(tmp_path, "closure", """
        def outer(x):
            def inner(y):
                return y * 2
            if x < 0:
                raise ValueError("negative")
            return inner
    """)
    outer = next(c for c in gv.guard_clauses(tmp_path) if c.function == "outer")
    inner_line = 3  # ``return y * 2``
    assert inner_line not in outer.body_lines


def test_methods_keep_their_class_in_the_qualname(tmp_path):
    """Two classes may define the same method name; the site must disambiguate."""
    _plant(tmp_path, "cls", """
        class A:
            def check(self, x):
                if x:
                    raise ValueError("a")

        class B:
            def check(self, x):
                if x:
                    raise ValueError("b")
    """)
    assert sorted(c.function for c in gv.guard_clauses(tmp_path)) == [
        "A.check", "B.check"
    ]


# --------------------------------------------------------------------------
# The mirror
# --------------------------------------------------------------------------

def _census(firings):
    return gv.Census(firings=tuple(firings), excluded=(), suite=())


def test_miscalibrated_flags_a_calibration_member_gone_quiet(tmp_path):
    """If D-058's guard stops firing, the mirror says so rather than reading clean.

    That is the regression this whole module exists to catch: the fix that made
    the guard firable being undone, leaving a guard that passes forever.
    """
    module, function, exc = gv.CALIBRATION[0]
    clause, _ = _one(tmp_path, GUARD_SOURCE)
    quiet = gv.Firing(
        clause=gv.GuardClause(module=module, function=function,
                              lineno=clause.lineno, condition=clause.condition,
                              exception=exc, body_lines=clause.body_lines,
                              path=clause.path),
        verdict=gv.VERDICT_NEVER_FIRED,
    )
    problems = gv.miscalibrated(_census([quiet]))
    assert len(problems) == 1
    assert "NEVER_FIRED" in problems[0]


def test_miscalibrated_flags_a_calibration_member_the_scan_lost():
    """Absent from the population is a worse failure than present and silent.

    A scan that stops discovering ``shadow_batch`` — a rename, a refactor, an
    ``EXCLUDED_DIRS`` typo — would otherwise report a clean partition over a
    population missing the one guard whose answer is known.
    """
    problems = gv.miscalibrated(_census([]))
    assert len(problems) == 1
    assert "not discovered" in problems[0]


@pytest.mark.slow
def test_calibration_member_fires_under_the_real_suite():
    """End-to-end: coverage over the module that exercises D-058's guard.

    Scoped to ``test_weight_units.py`` rather than the whole suite — the
    calibration claim is about one guard, and a full run costs ~8 min.  A
    narrower suite can only make this test *stricter*: fewer tests means fewer
    chances for the raise to execute.
    """
    pytest.importorskip("coverage", reason="measure() shells out to coverage")
    executed = gv.measure(("eval/mppi_sandbox/tests/test_weight_units.py",))
    cens = gv.census(suite=(), executed=executed)
    assert gv.miscalibrated(cens) == ()
