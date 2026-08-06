"""Which assertions has no run ever evaluated? — STATE #1 and #2, generalising D-101.

D-101 found ``manufactured_candidates <= collateral`` — documented for thirty-odd
cycles, asserted by a ``slow`` test, and **false**.  It did not survive because it
was subtle.  It survived because the test *died two ``assert``s earlier*, so the
line was never reached, and a claim nobody evaluates cannot go red.

D-100 had diagnosed the same defect shape (a property of the population promoted
to an invariant) in the *same test function*, two ``assert``s up.  Diagnosing a
class is not sweeping it: the repair fixed the statement the run reached and left
the identical one below it standing.  That is the whole argument for this module.
The question "which other assertions are like that?" cannot be answered by reading
— reading is what installed both defects — and it cannot be answered by running,
because the run stops at the first failure.  It has to be answered *structurally*,
from the recorded failures plus the source.

What is measured
----------------

Two populations, and they are not the same one:

**Shielded.** For each row of :data:`simd_attribution.CI_FAILURES` whose failing
statement can be pinned to an ordinal, every ``assert`` **after** it in the same
test function.  The run reached the failure and stopped; those statements were
never executed by the job that was supposed to execute them.  D-101's line is one
of these, and this module is what makes it the *derived* answer rather than the
lucky one.

**Sampled.** ``assert``s inside a ``for``/``while`` body that iterates a measured
population.  A loop-body ``assert`` turns "check every member" into "check members
until one fails", so a green reading means *the first violator does not exist*,
not *no violator exists* — and the violator it names is whichever the iteration
order reached first, which is a sampling policy nobody chose.  D-101 hit this too:
two separate CI rows named the harmless half of a four-site finding because the
loop asserted inside its body.

Both are *unevaluated-claim* populations.  Neither is a bug list.  A shielded
``assert`` may well be true; the finding is that **its truth is unmeasured**, and
the suite's green does not cover it.

What is *not* claimed
---------------------

This module does not decide whether a shielded assertion is true.  It cannot: the
whole point is that no run has produced a reading.  It reports the population, and
it reports **all** of it rather than the population-relation subset.  That filter
was in the first cut, on the argument that D-100 and D-101 were both population
relations — and it would have hidden the more interesting of the two rows the scan
actually found.  ``test_the_shipped_loud_arm_is_healthier_yet_understated_more``'s
shielded statement is ``shipped.understatement > audited.understatement``, an
ordinary scalar comparison that grades :data:`OTHER`, and it is the statement the
test's own docstring calls section 3's counterexample.  The shape of a claim is
not its importance; :attr:`Assertion.is_population_claim` is kept as an annotation
and is not applied as a filter anywhere.

Nor does it pin every row, and the six it cannot are not a deficiency.  They are
the ``TIMEOUT`` rows: a test killed by the clock has no failing statement, so
there is nothing for a later assertion to be shielded *by*.  Every one of the
eight ``ASSERTION`` rows pins.  :func:`unpinned` publishes the residue rather
than hiding it, per D-076/D-081 — the emptiness a scan cannot reach is part of
its reading.

Usage::

    python3 -m eval.mppi_sandbox.assert_reach report
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

from . import simd_attribution as sa

REPO_ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------
# 1. Claim kinds.  The three that matter are the shapes D-100/D-101 were.
# --------------------------------------------------------------------------

#: ``a <= b`` / ``a >= b`` / ``a.issubset(b)`` — a containment between two
#: populations.  D-101's defect.
SUBSET = "SUBSET"

#: ``a == {literal}`` / ``a == (...)`` — a measured population pinned to a
#: written-down one.  Goes stale silently when the population moves.
SET_EQUALITY = "SET_EQUALITY"

#: ``len(a) == n`` / ``0 < len(a) < len(b)`` — a count claim over a population.
CARDINALITY = "CARDINALITY"

#: Everything else.  Reported in the totals, excluded from the headline.
OTHER = "OTHER"

KINDS: tuple[str, ...] = (SUBSET, SET_EQUALITY, CARDINALITY, OTHER)

#: The kinds a population-relation finding can take.  D-100 was
#: :data:`CARDINALITY`, D-101 was :data:`SUBSET`; :data:`SET_EQUALITY` is the
#: third shape the same promotion produces and is included on that argument,
#: not because an instance has been found.  **Annotation only** — nothing
#: filters on it, because the one row it would have excluded is the one that
#: matters most (see the module docstring).
POPULATION_KINDS: frozenset[str] = frozenset({SUBSET, SET_EQUALITY, CARDINALITY})

@dataclass(frozen=True)
class Assertion:
    """One ``assert`` statement, in source order within its test function."""

    test_id: str
    ordinal: int  # 0-based position among the function's asserts
    lineno: int
    kind: str
    in_loop: bool
    text: str

    @property
    def is_population_claim(self) -> bool:
        return self.kind in POPULATION_KINDS


@dataclass(frozen=True)
class Shielded:
    """An ``assert`` a recorded failure stopped the run before reaching."""

    assertion: Assertion
    failure_id: str
    failed_at: int  # ordinal of the failing assert


# --------------------------------------------------------------------------
# 2. Reading the corpus.
# --------------------------------------------------------------------------


def _resolve(test_id: str) -> tuple[Path, tuple[str, ...]]:
    """``file::Class::test_name`` → (path, name-path within the module)."""
    parts = test_id.split("::")
    return REPO_ROOT / parts[0], tuple(parts[1:])


def _find_function(tree: ast.Module, names: tuple[str, ...]) -> ast.FunctionDef | None:
    node: ast.AST = tree
    for name in names:
        found = None
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and child.name == name:
                found = child
                break
        if found is None:
            return None
        node = found
    return node if isinstance(node, ast.FunctionDef) else None


def _is_len_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
    )


def _is_literal_population(node: ast.AST) -> bool:
    """A written-down set/tuple/list/dict — the thing a measurement gets pinned to."""
    return isinstance(node, (ast.Set, ast.Tuple, ast.List, ast.Dict))


def classify(test: ast.expr) -> str:
    """Grade one ``assert``'s test expression by claim shape."""
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Attribute):
        if test.func.attr in ("issubset", "issuperset"):
            return SUBSET
    if not isinstance(test, ast.Compare):
        return OTHER

    ops = [type(op) for op in test.ops]
    operands = [test.left, *test.comparators]

    # `len(x) == n`, `0 < len(x) < len(y)` -- any comparison naming a count.
    if any(_is_len_call(o) for o in operands):
        return CARDINALITY

    # `a <= b` / `a >= b` between two non-numeric operands is a containment.
    # A numeric literal on either side makes it an ordinary bound, not a
    # population relation -- `assert ratio <= 1.0` is not what D-101 was.
    if ops and all(op in (ast.LtE, ast.GtE) for op in ops):
        numeric = any(
            isinstance(o, ast.Constant) and isinstance(o.value, (int, float))
            for o in operands
        )
        if not numeric:
            return SUBSET

    if ops == [ast.Eq] and any(_is_literal_population(o) for o in operands):
        return SET_EQUALITY

    return OTHER


def _loop_asserts(fn: ast.FunctionDef) -> set[int]:
    """Line numbers of ``assert``s lexically inside a ``for``/``while`` body."""
    inside: set[int] = set()
    for node in ast.walk(fn):
        if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    inside.add(child.lineno)
    return inside


def asserts_in(test_id: str) -> tuple[Assertion, ...]:
    """Every ``assert`` in one test function, in source order.

    Order is the load-bearing part: "after the failure" is an ordinal claim, and
    ``ast.walk`` does not preserve source order, so the walk is sorted by line.
    """
    path, names = _resolve(test_id)
    if not path.exists():
        return ()
    source = path.read_text(encoding="utf-8")
    fn = _find_function(ast.parse(source), names)
    if fn is None:
        return ()

    lines = source.splitlines()
    in_loop = _loop_asserts(fn)
    nodes = sorted(
        (n for n in ast.walk(fn) if isinstance(n, ast.Assert)),
        key=lambda n: (n.lineno, n.col_offset),
    )
    return tuple(
        Assertion(
            test_id=test_id,
            ordinal=i,
            lineno=n.lineno,
            kind=classify(n.test),
            in_loop=n.lineno in in_loop,
            text=lines[n.lineno - 1].strip() if n.lineno <= len(lines) else "",
        )
        for i, n in enumerate(nodes)
    )


# --------------------------------------------------------------------------
# 3. Pinning the failure to an ordinal.
# --------------------------------------------------------------------------

#: The commit CI run ``31042602721`` was taken on.  Line numbers are only
#: meaningful against a tree, which is D-043's lesson arriving in a new place.
RUN_COMMIT = "d6b60c8d2cd70513ef47165ce6f928eaaa2007db"
RUN_ID = "31042602721"

#: ``file::test -> (line, source text)`` for the failing statement of every
#: **assertion** row of that run, transcribed from the job log's traceback
#: footers (``path.py:NNN: AssertionError``).
#:
#: This field is the whole reason the module works, and
#: :data:`simd_attribution.CI_FAILURES` does not carry it.  That census was
#: transcribed from ``short test summary info``, which prints the failing
#: expression with both operands elided (``assert {'exclusion_s...'} == ...``)
#: and **no line number** -- so it can say a test failed but not *where*, and
#: "which assertions did the failure shield" is exactly a where-question.  The
#: first cut of this module tried to recover the position from the printed
#: operator shape and pinned **3 of 14**, missing D-101's own site, because a
#: function with three ``==`` assertions is genuinely not pinnable that way.
#: The number was in the log the entire time, two lines below the text that was
#: transcribed.
#:
#: The text is stored with the line so drift is declared rather than silent:
#: :func:`moved` reports every row whose line no longer holds what it held, and
#: an ordinal computed against a moved line would be a fabrication.
FAILED_AT: dict[str, tuple[int, str]] = {
    "eval/mppi_sandbox/tests/test_ab_temperature_protocol.py"
    "::test_protocol_moves_the_effect_size_but_not_its_sign": (
        196, "assert float(d_single.mean()) > 1.25 * float(d_perarm.mean())"),
    "eval/mppi_sandbox/tests/test_denominator_scope.py"
    "::TestD028sMechanismIsTemperatureConditional"
    "::test_the_shipped_loud_arm_is_healthier_yet_understated_more": (
        170, "assert shipped.goal_distance < audited.goal_distance / 3, ("),
    "eval/mppi_sandbox/tests/test_exclusion_scope.py"
    "::test_the_exclusion_list_manufactured_exactly_two_candidates": (
        287, "assert set(es.manufactured_candidates(effect)) == {"),
    "eval/mppi_sandbox/tests/test_exclusion_scope.py"
    "::test_self_entries_are_the_majority_and_are_left_alone": (
        362, "assert not masked.manufactured_candidate, ("),
    "eval/mppi_sandbox/tests/test_exposure_timing_band.py"
    "::TestTheBandConstantIsMeasured"
    "::test_reportable_scenes_land_inside_the_declared_band": (
        94, "assert max(ratios.values()) == pytest.approx(hi, abs=0.05), ratios"),
    "eval/mppi_sandbox/tests/test_hazard_exposure.py"
    "::test_refutation_reproduces_from_simulation": (
        357, 'assert shared == {0.4}, "the two arms no longer share a rung"'),
    "eval/mppi_sandbox/tests/test_horizon_audit.py"
    "::TestScaleMatchedWeightIsHorizonDependent"
    "::test_the_prescribed_weight_moves_with_the_horizon": (
        170, "assert swing > 1.2, ("),
    "eval/mppi_sandbox/tests/test_scale_match.py"
    "::TestThePrescriptionLandsWhereItSaysItWill"
    "::test_the_prescribed_weight_achieves_the_requested_ratio": (
        206, "assert got == pytest.approx(target, rel=0.25)"),
}

#: Files that have been edited since :data:`RUN_COMMIT`.  Only one has, and it
#: is the D-100/D-101 file -- so its two rows are read at the run's commit via
#: :func:`_source_at`, not at HEAD.  Recorded rather than derived so that a test
#: can check the derivation still agrees with it.
MOVED_FILES: tuple[str, ...] = ("eval/mppi_sandbox/tests/test_exclusion_scope.py",)


def _source_at(rel: str, commit: str) -> str:
    """The file as it stood at ``commit``.  Empty string if git cannot say."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "show", f"{commit}:{rel}"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout if out.returncode == 0 else ""


def _asserts_at_run(test_id: str) -> tuple[tuple[int, int, str, str], ...]:
    """``(ordinal, lineno, text, kind)`` for the test's asserts **as CI ran them**.

    ``kind`` comes off the parsed node, not off ``text``.  ``text`` is one
    *source line*, and a multi-line ``assert`` truncates mid-expression
    (``assert swing > 1.2, (``) — re-parsing that would grade by whatever
    happens to fit on the first line.
    """
    rel = test_id.split("::", 1)[0]
    names = tuple(test_id.split("::")[1:])
    source = (_source_at(rel, RUN_COMMIT) if rel in MOVED_FILES
              else (REPO_ROOT / rel).read_text(encoding="utf-8"))
    if not source:
        return ()
    fn = _find_function(ast.parse(source), names)
    if fn is None:
        return ()
    lines = source.splitlines()
    nodes = sorted(
        (n for n in ast.walk(fn) if isinstance(n, ast.Assert)),
        key=lambda n: (n.lineno, n.col_offset),
    )
    return tuple(
        (i, n.lineno,
         lines[n.lineno - 1].strip() if n.lineno <= len(lines) else "",
         classify(n.test))
        for i, n in enumerate(nodes)
    )


def moved() -> tuple[str, ...]:
    """Rows whose recorded line no longer holds the recorded text.

    Non-empty means the transcription has drifted from the tree it describes and
    every ordinal below is suspect.  Reported, never repaired silently.
    """
    out = []
    for test_id, (line, text) in sorted(FAILED_AT.items()):
        found = [t for _, ln, t, _k in _asserts_at_run(test_id) if ln == line]
        if not found or found[0] != text:
            out.append(test_id)
    return tuple(out)


def failing_ordinal(test_id: str) -> int | None:
    """Which ``assert`` of the function CI stopped on, from the recorded line."""
    record = FAILED_AT.get(test_id)
    if record is None:
        return None
    line, text = record
    for ordinal, ln, t, _kind in _asserts_at_run(test_id):
        if ln == line and t == text:
            return ordinal
    return None


def unpinned(census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES) -> tuple[str, ...]:
    """Census rows this module cannot place — the reading's blind spot.

    The ``TIMEOUT`` rows are here permanently and correctly: a job killed by the
    clock has no failing statement, so there is nothing for a later assertion to
    be shielded *by*.  They are not a matcher deficiency.
    """
    return tuple(f.test_id for f in census if failing_ordinal(f.test_id) is None)


# --------------------------------------------------------------------------
# 4. The two populations.
# --------------------------------------------------------------------------


def shielded(census: tuple[sa.CiFailure, ...] = sa.CI_FAILURES) -> tuple[Shielded, ...]:
    """Assertions a recorded failure stopped the run before reaching.

    Read at :data:`RUN_COMMIT`, because that is the tree whose execution is
    being described.  An assertion added since is not something that run failed
    to reach; it is something that run never had.
    """
    out: list[Shielded] = []
    for failure in census:
        at = failing_ordinal(failure.test_id)
        if at is None:
            continue
        for ordinal, line, text, kind in _asserts_at_run(failure.test_id):
            if ordinal <= at:
                continue
            out.append(Shielded(
                Assertion(
                    test_id=failure.test_id, ordinal=ordinal, lineno=line,
                    kind=kind, in_loop=False, text=text,
                ),
                failure_id=failure.test_id, failed_at=at,
            ))
    return tuple(out)


def sampled(paths: tuple[Path, ...] | None = None) -> tuple[Assertion, ...]:
    """Loop-body ``assert``s across the test corpus (STATE #2).

    Independent of :func:`shielded`: a loop-body ``assert`` is under-evaluated
    whether or not its test ever failed.
    """
    files = paths if paths is not None else tuple(
        sorted((REPO_ROOT / "eval" / "mppi_sandbox" / "tests").glob("test_*.py"))
    )
    out: list[Assertion] = []
    for path in files:
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:  # a probe file outside the repo -- the unit controls
            rel = path.as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("test_"):
                continue
            for a in _asserts_of(rel, fn, path):
                if a.in_loop:
                    out.append(a)
    return tuple(out)


def _asserts_of(rel: str, fn: ast.FunctionDef, path: Path) -> tuple[Assertion, ...]:
    """Fallback for methods, whose ``file::name`` id does not resolve top-level."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    in_loop = _loop_asserts(fn)
    nodes = sorted(
        (n for n in ast.walk(fn) if isinstance(n, ast.Assert)),
        key=lambda n: (n.lineno, n.col_offset),
    )
    return tuple(
        Assertion(
            test_id=f"{rel}::{fn.name}",
            ordinal=i,
            lineno=n.lineno,
            kind=classify(n.test),
            in_loop=n.lineno in in_loop,
            text=lines[n.lineno - 1].strip() if n.lineno <= len(lines) else "",
        )
        for i, n in enumerate(nodes)
    )


def population_claims(rows: tuple[Shielded, ...] | None = None) -> tuple[Shielded, ...]:
    """The headline: shielded assertions that assert a *population relation*."""
    return tuple(s for s in (shielded() if rows is None else rows)
                 if s.assertion.is_population_claim)


def census(rows: tuple[Shielded, ...] | None = None) -> dict[str, int]:
    """Shielded assertions by claim kind."""
    rows = shielded() if rows is None else rows
    counts = {k: 0 for k in KINDS}
    for s in rows:
        counts[s.assertion.kind] += 1
    return counts


# --------------------------------------------------------------------------
# 5. Report.
# --------------------------------------------------------------------------


def report() -> str:
    rows = shielded()
    lines = [
        "assert_reach — assertions no run has evaluated",
        "",
        f"  recorded failures: {len(sa.CI_FAILURES)}"
        f"  pinned: {len(sa.CI_FAILURES) - len(unpinned())}"
        f"  unpinned: {len(unpinned())}",
        f"  shielded assertions: {len(rows)}",
        f"  of which population claims: {len(population_claims(rows))}",
        "",
        "  by kind: " + ", ".join(f"{k}={v}" for k, v in census(rows).items()),
        "",
    ]
    for s in rows:
        a = s.assertion
        mark = "population" if a.is_population_claim else "scalar"
        lines.append(
            f"  {a.kind:<13} {a.test_id.split('::')[-1]}:{a.lineno}"
            f"  (#{a.ordinal} > failed #{s.failed_at})  [{mark}]"
        )
        lines.append(f"      {a.text}")
    loop_rows = sampled()
    lines += [
        "",
        f"  loop-body assertions across the corpus: {len(loop_rows)}"
        f"  (population claims: {sum(1 for a in loop_rows if a.is_population_claim)})",
        "",
        "  unpinned rows (this reading's blind spot):",
    ]
    lines += [f"    {t.split('::')[-1]}" for t in unpinned()]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] != "report":
        print(f"usage: python3 -m eval.mppi_sandbox.assert_reach report", file=sys.stderr)
        return 2
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
