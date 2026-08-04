"""Which guard clauses has the suite never made fire? — STATE #1, generalising D-058.

Four consecutive cycles found the same defect wearing different clothes: a
predicate whose trigger **cannot occur**, passing forever, reading like a check.
D-055 (the liveness bar scored the fixture), D-056 (the probeability bar had the
sign flipped), D-057 (`grid_unseen`'s vacuity check sat on a renderer floor, so
an empty world read 2.73 %), D-058 (`shadow_batch`'s `ValueError("no shadow
cells in this BEV")` could not fire — the grid corners guarantee `sel.any()` on
every scene that renders at all).

All four were found **by hand**, each from the previous one's wreckage.  STATE #1
asks for the systematic pass, and the first thing a systematic pass owes is a
statement of the population it walks.

The population, and why it is one and not three
-----------------------------------------------

STATE #1 says "three known members now calibrate the search".  They do not — not
this search.  Of the four findings exactly **one**, D-058, is a *guard clause* in
the syntactic sense this module can discover: ``if <cond>: raise <Exc>``.  D-057's
defect is a **bar** inside a boolean property (`unseen.min() > 0.0`), D-056's is a
**verdict comparison**, D-055's is a **fixture reading**.  They share a *shape* —
a predicate offered its population and never biting — but only one of them is
reachable by scanning for ``raise``.

So this instrument's calibration set is **1**, and saying so is the point.  A
scan calibrated against a population that cannot contain three of its four
ground-truth members is D-045's shape yet again (a registry checked against a
population too small to hold its omissions), and the honest move is to name the
bound rather than to quietly count four.  :data:`CALIBRATION` carries the one
member; :func:`miscalibrated` is the mirror, pinned empty.

Never-fired is a necessary condition, not the finding
------------------------------------------------------

A guard whose trigger cannot occur is *necessarily* a guard no test ever makes
raise.  The converse is false and loudly so: most argument-validation raises in
this package are simply untested.  So the measurement is a **superset**, and its
value is entirely in how it is partitioned.

The partition that matters is whether the guard was ever **offered** its
population.  D-058's guard was called on every rendering scene, in every cycle,
for twenty-two days, and never fired — that is what made it damning.  A guard in
a function nothing calls has told us nothing at all; its silence is the
*function's*, not the guard's.  Hence three verdicts and not two:

``FIRES``
    The ``raise`` line executed.  The guard is demonstrably live: some input in
    the suite reaches its trigger.  Nothing to ask here.
``NEVER_FIRED``
    The enclosing function ran, the ``raise`` did not.  **The candidate set.**
    The guard was offered inputs and declined every one.  D-058's guard sat
    here, and so does every future instance of its shape.
``UNREACHED``
    The enclosing function never ran.  The guard's silence is uninformative —
    this is the ``UNDECIDABLE`` verdict :mod:`probe_reach` keeps separate from
    ``MUTE_FIXTURE`` for the same reason, and D-050's rule applies: a probe that
    cannot separate "not asked" from "asked and silent" has measured nothing.

Unconditional raises are excluded, and that is a decision
----------------------------------------------------------

``raise NotImplementedError`` at the top of an abstract method is not a guard —
its trigger is "the function ran", so it is trivially reachable and carries no
claim that could be vacuous.  Only a ``raise`` with at least one enclosing ``if``
*inside the same function* is scored.  :func:`unconditional` reports the excluded
set rather than dropping it silently, because the size of what a scan refuses is
the number D-045 through D-052 kept finding nobody had written down.

The reading is the suite's, not the code's
-------------------------------------------

``NEVER_FIRED`` is a statement about **this test suite**, not about the
possible-input space.  A guard can be perfectly triggerable by an input no test
supplies.  That is why the verdict is named for what was observed rather than for
what it might mean, and why :func:`never_fired` returns candidates rather than
findings.  Confirming one requires the D-058 move: work out what the callers
guarantee, then show the trigger is unsatisfiable.  This module says *where to
look*, and its whole claim is that the list is short enough to look at.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

VERDICT_FIRES = "FIRES"
VERDICT_NEVER_FIRED = "NEVER_FIRED"
VERDICT_UNREACHED = "UNREACHED"

#: Package root scanned for guard clauses.  Tests live inside it and are skipped:
#: a guard clause in a test is the test's own assertion machinery, not a subject.
PACKAGE = Path(__file__).resolve().parent

#: Directory names under :data:`PACKAGE` whose modules are not subjects.
EXCLUDED_DIRS = frozenset({"tests", "__pycache__"})

#: The suite run to produce the reading, relative to the repo root.  Fast half
#: only — the slow half costs ~8 min (see ``eval/conftest.py``) and a guard that
#: only fires under ``--slow`` would score ``NEVER_FIRED`` here.  That is a known
#: bound on the reading, reported by :func:`Census.suite`, not a silent one.
DEFAULT_SUITE = (
    "eval/mppi_sandbox/tests/",
    "eval/tests/test_path_tracking_metrics.py",
    "eval/tests/test_run_metrics.py",
)

#: Ground truth: guard clauses **known** to have had an unsatisfiable trigger,
#: as ``(module, function, exception)``.  Exactly one — see the module docstring
#: on why the other three findings of this shape are not in this population.
#: D-058 fixed it by siting the batch on ``scene_points()`` and pinning a test
#: that makes it raise, so on a correct tree it now reads ``FIRES``.
CALIBRATION = (("weight_units", "shadow_batch", "ValueError"),)


@dataclass(frozen=True)
class GuardClause:
    """One ``if <cond>: raise <Exc>`` inside a function of the package."""

    module: str
    #: Dotted name within the module; nested functions keep their parent prefix.
    function: str
    #: Line of the ``raise`` statement — the line coverage reports iff it fired.
    lineno: int
    #: Source of the **nearest** enclosing ``if`` test.  Where several nest, this
    #: is the innermost, which is the one that decides.
    condition: str
    exception: str
    #: Statement lines of the enclosing function excluding every ``raise`` in it.
    #: Executed ⇔ the function ran.  The ``if`` test's own line is in here, so
    #: even a function that is nothing but a guard is scored correctly.
    body_lines: frozenset[int]
    path: Path

    @property
    def site(self) -> str:
        return f"{self.module}.{self.function}:{self.lineno}"

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.site} if {self.condition} → {self.exception}"


@dataclass(frozen=True)
class Firing:
    """A guard clause plus what the suite did to it."""

    clause: GuardClause
    verdict: str

    @property
    def is_candidate(self) -> bool:
        """Offered its population and never bit — the set STATE #1 asked for."""
        return self.verdict == VERDICT_NEVER_FIRED

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.verdict:<12} {self.clause}"


def _qualname(stack: Sequence[str]) -> str:
    return ".".join(stack)


def _function_defs(tree: ast.Module) -> Iterable[tuple[str, ast.AST]]:
    """Yield ``(qualname, node)`` for every function, nested ones included."""

    def walk(node: ast.AST, stack: tuple[str, ...]):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                here = stack + (child.name,)
                yield _qualname(here), child
                yield from walk(child, here)
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, stack + (child.name,))
            else:
                yield from walk(child, stack)

    yield from walk(tree, ())


def _own_statements(fn: ast.AST) -> list[ast.stmt]:
    """Statements belonging to ``fn`` itself, not to a function nested in it.

    A nested ``def``'s body runs when *it* is called, which can be long after —
    or instead of — the outer function.  Counting those lines as the outer
    function's would score a guard ``NEVER_FIRED`` on evidence that belongs to a
    closure someone else invoked.
    """
    out: list[ast.stmt] = []

    def walk(node: ast.AST):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, ast.stmt):
                out.append(child)
            walk(child)

    for stmt in getattr(fn, "body", []):
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            continue
        out.append(stmt)
        walk(stmt)
    return out


def _guarding_if(fn: ast.AST, target: ast.Raise) -> ast.If | None:
    """The innermost ``if`` of ``fn`` whose body (or ``orelse``) holds ``target``.

    Walks outside-in and keeps the last match, so nesting resolves to the test
    that actually decides.  Returns ``None`` for an unconditional raise.
    """
    found: ast.If | None = None

    def contains(branch: list[ast.stmt]) -> bool:
        return any(target is node for stmt in branch for node in ast.walk(stmt))

    def walk(node: ast.AST):
        nonlocal found
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, ast.If) and (contains(child.body)
                                              or contains(child.orelse)):
                found = child
            walk(child)

    walk(fn)
    return found


def _exception_name(node: ast.Raise) -> str:
    exc = node.exc
    if isinstance(exc, ast.Call):
        exc = exc.func
    if isinstance(exc, ast.Name):
        return exc.id
    if isinstance(exc, ast.Attribute):
        return exc.attr
    return ast.unparse(node.exc) if node.exc is not None else "<re-raise>"


def _modules(package: Path = PACKAGE) -> list[Path]:
    return sorted(p for p in package.rglob("*.py")
                  if not (EXCLUDED_DIRS & set(p.relative_to(package).parts)))


def _scan(package: Path = PACKAGE) -> tuple[list[GuardClause], list[GuardClause]]:
    """``(guarded, unconditional)`` — both populations, from the AST."""
    guarded: list[GuardClause] = []
    unconditional: list[GuardClause] = []
    for path in _modules(package):
        module = path.relative_to(package).with_suffix("").as_posix().replace("/", ".")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for qualname, fn in _function_defs(tree):
            statements = _own_statements(fn)
            raises = [s for s in statements if isinstance(s, ast.Raise)]
            if not raises:
                continue
            body_lines = frozenset(s.lineno for s in statements
                                   if not isinstance(s, ast.Raise))
            for node in raises:
                if node.exc is None:  # bare ``raise`` — re-raises, asserts nothing
                    continue
                guard = _guarding_if(fn, node)
                clause = GuardClause(
                    module=module,
                    function=qualname,
                    lineno=node.lineno,
                    condition=ast.unparse(guard.test) if guard is not None else "",
                    exception=_exception_name(node),
                    body_lines=body_lines,
                    path=path,
                )
                (guarded if guard is not None else unconditional).append(clause)
    return guarded, unconditional


def guard_clauses(package: Path = PACKAGE) -> tuple[GuardClause, ...]:
    """Every ``if <cond>: raise <Exc>`` in the package, derived from the AST.

    Derived and not typed: a hand-written list of guards would be the sixth
    consecutive hand-written list in this package to come up short (D-045,
    D-046, D-047, D-050, D-052).
    """
    return tuple(_scan(package)[0])


def unconditional(package: Path = PACKAGE) -> tuple[GuardClause, ...]:
    """Raises with no enclosing ``if`` — refused by the scan, reported anyway.

    Their trigger is "the function ran", so they cannot be vacuous in the sense
    STATE #1 means.  Named so the population this scan walks is stated rather
    than assumed.
    """
    return tuple(_scan(package)[1])


def classify(clauses: Iterable[GuardClause],
             executed: dict[Path, frozenset[int]]) -> tuple[Firing, ...]:
    """Score each clause against a per-file set of executed line numbers.

    Pure — the coverage run is :func:`measure`'s job.  Kept separate so the
    partition's semantics are testable without a suite run.
    """
    out = []
    for clause in clauses:
        lines = executed.get(clause.path, frozenset())
        if clause.lineno in lines:
            verdict = VERDICT_FIRES
        elif clause.body_lines & lines:
            verdict = VERDICT_NEVER_FIRED
        else:
            verdict = VERDICT_UNREACHED
        out.append(Firing(clause=clause, verdict=verdict))
    return tuple(out)


def measure(suite: Sequence[str] = DEFAULT_SUITE,
            root: Path | None = None) -> dict[Path, frozenset[int]]:
    """Run ``suite`` under coverage and return the executed lines per file.

    A subprocess, because the suite imports the very modules being measured and
    an in-process start would miss every line executed at import time.
    """
    root = root or PACKAGE.parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        data_file = Path(tmp) / "cov"
        subprocess.run(
            [sys.executable, "-m", "coverage", "run",
             f"--data-file={data_file}", f"--source={PACKAGE}",
             "-m", "pytest", *suite, "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=900, check=False,
        )
        import coverage  # local: only the measuring path needs it

        data = coverage.CoverageData(basename=str(data_file))
        data.read()
        return {Path(f).resolve(): frozenset(data.lines(f) or ())
                for f in data.measured_files()}


@dataclass(frozen=True)
class Census:
    """The partition, plus the bounds it was taken under."""

    firings: tuple[Firing, ...]
    excluded: tuple[GuardClause, ...]
    suite: tuple[str, ...]

    def of(self, verdict: str) -> tuple[Firing, ...]:
        return tuple(f for f in self.firings if f.verdict == verdict)

    @property
    def candidates(self) -> tuple[Firing, ...]:
        return self.of(VERDICT_NEVER_FIRED)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        counts = " ".join(
            f"{v}={len(self.of(v))}"
            for v in (VERDICT_FIRES, VERDICT_NEVER_FIRED, VERDICT_UNREACHED))
        return (f"{len(self.firings)} guard clauses ({counts}); "
                f"{len(self.excluded)} unconditional raises excluded")


def census(package: Path = PACKAGE,
           suite: Sequence[str] = DEFAULT_SUITE,
           executed: dict[Path, frozenset[int]] | None = None) -> Census:
    """Discover, measure, partition.  Pass ``executed`` to skip the suite run."""
    guarded, excluded = _scan(package)
    lines = measure(suite) if executed is None else executed
    return Census(firings=classify(guarded, lines),
                  excluded=tuple(excluded),
                  suite=tuple(suite))


def never_fired(cens: Census) -> tuple[Firing, ...]:
    """The candidate set: offered inputs by the suite, declined every one.

    Candidates, not findings — see the module docstring.  Confirming one is
    D-058's move and cannot be done by counting.
    """
    return cens.candidates


def miscalibrated(cens: Census) -> tuple[str, ...]:
    """Known-vacuous guards this scan fails to score ``FIRES`` — pinned empty.

    The mirror over :data:`CALIBRATION`.  A member absent from the discovered
    population means the scan cannot see the one defect it was built from; a
    member present but not ``FIRES`` means D-058's fix stopped holding.  Both
    read as failures here rather than as a silent clean bill.
    """
    by_key = {(f.clause.module, f.clause.function, f.clause.exception): f
              for f in cens.firings}
    out = []
    for key in CALIBRATION:
        found = by_key.get(key)
        if found is None:
            out.append(f"{'.'.join(key[:2])} — not discovered by the scan")
        elif found.verdict != VERDICT_FIRES:
            out.append(f"{'.'.join(key[:2])} — {found.verdict}, expected FIRES")
    return tuple(out)


def report(cens: Census) -> str:  # pragma: no cover - reporting sugar
    lines = [str(cens), ""]
    for firing in sorted(cens.candidates, key=lambda f: f.clause.site):
        lines.append(f"  NEVER_FIRED  {firing.clause}")
    unreached = cens.of(VERDICT_UNREACHED)
    if unreached:
        lines.append("")
        lines.append(f"  ({len(unreached)} UNREACHED — enclosing function "
                     f"never ran; silence uninformative)")
    problems = miscalibrated(cens)
    if problems:
        lines.append("")
        lines.extend(f"  ⚠ CALIBRATION: {p}" for p in problems)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report(census()))
