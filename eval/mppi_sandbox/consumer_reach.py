"""Which alternative constructors does no production code ever call? — STATE #1, generalising D-188.

D-187 added `SweepStats.n_in_band`, tested it, and wrote into its journal that a
walk taken from there "records `n_in_band` and pools as a point instead of a
bound".  D-188 found that prospectus false: the object a census walk actually
*records* is `barrier_ceiling.Rung`, `_rung()` read only `stats.ess_in_band`, and
so `WalkCount.from_sweep` — the consumer the whole two-cycle argument was for —
was reachable from **no production path at all**.  It was fully implemented,
fully tested, and dead.

STATE priced the generalisation as "a grep for non-test callers".  That pricing
is wrong in the direction this module exists to fix, and the instance is
`from_sweep` itself::

    $ grep -rn from_sweep eval/mppi_sandbox/*.py
    barrier_ceiling.py:131:    went no further. `WalkCount.from_sweep` — the …
    barrier_ceiling.py:180:        \"\"\"The `k` a rate estimator wants, so that …
    barrier_ceiling.py:345:        # is the line that makes `WalkCount.from_sweep`
    seed_count_licence.py:423:    def from_sweep(cls, name: str, stats) …

Four hits outside the definition, three of them in **prose** — a docstring, a
paragraph of module commentary, and the comment D-188 wrote to explain the fix.
A grep reads clean and the constructor is still dead.  D-047's rule ("a comment
is not a measurement") has a caller-counting corollary: **a mention is not a
call**, and only a parser can tell them apart.  So the population here is built
from `ast`, and comments and strings are invisible to it by construction.

What is measured
----------------

**Population A — alternative constructors**: every `classmethod` and
`staticmethod` defined on a class in `eval/mppi_sandbox/`, of which `from_sweep`
is one.  Bounded, nameable, and the exact shape of the defect.  This is the
population `check` **grades**.

**Population B — module-level public functions** (D-191).  D-189 measured this
one and left it out, on the grounds that ~96 entries would bury a 1-item
residue.  That was right about the residue and wrong as a permanent silence:
four consecutive cycles then found defects *inside* the instrument layer, which
is what a surface nobody calls looks like from outside.  It is reported here
**separately**, never merged into A's tally, so the 1-item residue stays
readable.

What B actually contains, measured rather than assumed:

===========================  =====  ==================================
verdict                      n      reading
===========================  =====  ==================================
``LIVE``                     623    ordinary package interior
``TEST_ONLY``                 96    **not** a defect in this population
``REFERENCED_NOT_CALLED``      8    dispatch-reachable, ungraded
``FRAMEWORK_DISPATCHED``       2    ``pytest_*`` hooks — see below
``DEFERRED_BY_COST``           1    too expensive to run — see below
``UNREACHED``                  9    **the finding**
===========================  =====  ==================================

The 96 are the reason B is reported and not graded: they are `assert_*`,
`*_census`, `*_screen` helpers, and a helper a test suite calls **is being
used for its purpose**.  Grading `TEST_ONLY` here would be red by construction
on day one, and a check that cannot be cleared is one that gets muted (D-044).

`UNREACHED` is the verdict that means the same thing in both populations —
nothing, anywhere, in production or in tests, calls this — and it is an order
of magnitude smaller than the count D-189 was avoiding.  **That is the answer
to "is this a large write-only surface?": the instrument layer is 96 helpers
doing their job plus 11 functions with no caller at all.**

Why the *coverage* pragma is not the key for `DEFERRED_BY_COST`
----------------------------------------------------------------

`reading_record.take_and_record` is `UNREACHED` and is **not** dead code: it
costs 2k concurrent five-minute suite runs, so the fast suite cannot reach it
by construction.  STATE priced the fix as "key it on the ``# pragma: no cover``
marker rule".  Measured, that key is wrong in the direction this module exists
to fix — the same shape as D-189's *a mention is not a call*:

===============================================  =====
``pragma: no cover`` in population B (744 fns)      48
  of those, graded ``LIVE``                         43
  graded ``UNREACHED``                               1
===============================================  =====

The marker's 48 uses say ``- CLI`` (13×), *bare* (8×), ``- reporting`` (5×),
``- reporting sugar`` (3×), ``- defended`` (3×) …  It is a **coverage**
directive — "do not count this line against the coverage total" — and it is
silent about whether anything calls the function.  That it currently singles
out one residue member is a *coincidence of the other 43 having callers*: two
dozen of them are `report()` / `main()` bodies that are `LIVE` only because
their own ``if __name__ == "__main__"`` block calls them.  Delete that block in
a routine refactor and the bare-pragma rule would grade the newly-dead reporter
`DEFERRED_BY_COST` instead of `UNREACHED` — an exemption that **hides a
finding**, granted by a marker that was never making that claim.

So the verdict is keyed on a marker that states *this* claim and no other::

    def take_and_record(...):  # pragma: no cover -- deferred-by-cost: <why>

Still a valid coverage pragma (coverage.py matches the substring, so nothing
about coverage changes), but the trailing clause is the function saying, at its
own definition site, *why nothing calls it*.  It is read off the **signature**
— not the body — so a comment further down cannot confer it, and it is derived
per-definition rather than kept in a central list: a registry of exempt names
is the unwatched allow list `guard_reflexivity` counts.  The marker is
self-serve by construction, so its watcher is the residue pin in
`test_consumer_reach.py`: a function cannot take this verdict without the pin
changing in the same commit.

Why `FRAMEWORK_DISPATCHED` is a verdict and not an exemption
------------------------------------------------------------

`loop_reach.pytest_configure` / `pytest_unconfigure` have no in-repo call site
**by construction** — pytest resolves plugin hooks by name, exactly as the
interpreter resolves `__new__`, which is why the dunder rule below exists.  The
tempting fix is to filter them out.  That would make a fifth unwatched allow
list, which is the defect `guard_reflexivity` counts.  So they are *graded into
their own verdict* instead: visible in the report, excluded from the finding,
and nothing is hidden behind a filter nobody reads.  The rule is a naming
convention the framework itself defines, so a new hook needs no edit here.

**Reach**, per definition name, split by where the call site lives:

=========================  ===========================================
verdict                    meaning
=========================  ===========================================
``LIVE``                   ≥ 1 call from a non-test module
``REFERENCED_NOT_CALLED``  0 such calls, but the name is *mentioned* in
                           non-test code as an attribute or a string —
                           it may be reached through a dispatch table,
                           so it is reported and **not** graded
``TEST_ONLY``              0 non-test calls, 0 non-test mentions, ≥ 1
                           call from ``tests/`` — the ``from_sweep``
                           shape, and the finding
``UNREACHED``              nothing calls it anywhere
=========================  ===========================================

Two error directions, and they are not symmetric
------------------------------------------------

Matching is by **bare name**, because `WalkCount.from_sweep(...)` parses as a
call on an `Attribute` whose `.value` is a name the parser cannot resolve to a
class without a type checker.  So two classes that both define `from_json` share
one tally, and a live one rescues a dead one.  That under-reports: it can hide a
finding, never manufacture one.  `REFERENCED_NOT_CALLED` bends the same way on
purpose — a name that appears as a string literal is assumed dispatch-reachable
rather than dead, because a registry keyed on `"from_sweep"` is a real pattern
in this package and a false alarm is what gets an instrument muted (D-044).

The residue is therefore a **lower bound** on dead constructors, which is the
useful direction for a guard: everything it names is a finding, and the ones it
misses were already invisible.

Why the definition's own module counts as a caller
---------------------------------------------------

A constructor called only from its defining module is live — that is how a
`classmethod` used by a sibling `classmethod` looks, and it is fine.  What
`from_sweep` lacks is not a *foreign* caller, it is any caller: the object that
would carry the argument reaches the right shape (D-188 saw to that) and then
nobody invokes the consumer.  Duck-type compatibility is not reachability, and
this module is the difference.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

SANDBOX_DIR = Path(__file__).resolve().parent
TESTS_DIRNAME = "tests"

#: Decorator names that mark an alternative constructor.
CONSTRUCTOR_DECORATORS = ("classmethod", "staticmethod")

#: Naming convention by which pytest resolves plugin hooks.  Not an allow list
#: of function names — a prefix the *framework* defines, the same shape as the
#: `__dunder__` rule in `definitions()`.  Members grade `FRAMEWORK_DISPATCHED`.
FRAMEWORK_HOOK_PREFIX = "pytest_"

#: The marker by which a definition states that *running* it is what nobody can
#: afford — not that its lines are uninteresting to a coverage report.  A
#: sub-form of the coverage pragma so `coverage.py` still honours it, but the
#: trailing clause is the discriminating part: the bare `# pragma: no cover`
#: appears 48× in this package and means `- CLI` / `- reporting` / `- defended`,
#: which say nothing about reachability.  See the module docstring.
DEFERRED_MARKER = "pragma: no cover -- deferred-by-cost"


@dataclass(frozen=True)
class Definition:
    """One `classmethod`/`staticmethod`, or one module-level public function."""

    module: str
    cls: str
    name: str
    lineno: int
    kind: str
    #: `"constructor"` (population A) or `"module"` (population B).
    scope: str = "constructor"
    #: Whether the **signature** carries `DEFERRED_MARKER`.
    deferred: bool = False

    @property
    def qualname(self) -> str:
        if not self.cls:
            return f"{self.module}.{self.name}"
        return f"{self.module}.{self.cls}.{self.name}"


@dataclass(frozen=True)
class Reach:
    """How a definition is reached, and from where."""

    definition: Definition
    prod_calls: int
    test_calls: int
    prod_mentions: int
    verdict: str

    @property
    def is_finding(self) -> bool:
        """What counts as a defect differs by population, and must.

        For a constructor, `TEST_ONLY` **is** the defect — `from_sweep` was
        implemented, tested, and reachable from no production path.  For a
        module-level function, `TEST_ONLY` is the normal state of an assertion
        helper and grading it would be red on day one (D-044).  `UNREACHED` is
        the verdict that reads the same way in both: no caller anywhere.

        `DEFERRED_BY_COST` is *not* a finding in either population — it is the
        `FRAMEWORK_DISPATCHED` shape, an absence of callers with a structural
        reason stated at the definition site rather than debt.
        """
        if self.definition.scope == "module":
            return self.verdict == "UNREACHED"
        return self.verdict in ("TEST_ONLY", "UNREACHED")


def _decorator_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names


def _is_test_path(path: Path) -> bool:
    return TESTS_DIRNAME in path.parts or path.name.startswith("test_")


def _is_deferred(lines: list[str], node: ast.AST) -> bool:
    """Does this definition's **signature** carry `DEFERRED_MARKER`?

    Signature, not body: a marker inside the body would let a comment anywhere
    in a hundred-line function confer an exemption on it, and the claim being
    made ("nothing calls this, and here is why") belongs at the definition
    site.  Decorator lines sit above `node.lineno` and are excluded for the
    same reason — a decorator is shared, and this claim is per-definition.

    The marker must be a **trailing** comment on a signature line.  Comments
    are not AST nodes, so the range between `def` and the first body statement
    silently swallows a free-standing comment line sitting just under the
    header — which is body-position prose wearing the signature's address, and
    is exactly what the first draft of this graded `DEFERRED_BY_COST`.  Lines
    that are nothing but a comment are therefore dropped, which keeps the
    multi-line ``):  # pragma …`` form that `take_and_record` itself uses.
    """
    body = getattr(node, "body", None)
    if not body:
        return False
    signature = lines[node.lineno - 1:body[0].lineno - 1]
    return any(DEFERRED_MARKER in line for line in signature
               if not line.strip().startswith("#"))


def source_files(root: Path | None = None) -> list[Path]:
    """Every `.py` file in the package, tests included, deterministically ordered."""
    base = SANDBOX_DIR if root is None else Path(root)
    return sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)


def _parse(path: Path) -> ast.Module | None:
    tree, _ = _parse_with_lines(path)
    return tree


def _parse_with_lines(path: Path) -> tuple[ast.Module | None, list[str]]:
    """The tree plus the source lines `_is_deferred` reads the signature from."""
    try:
        text = path.read_text(encoding="utf-8")
        return ast.parse(text, filename=str(path)), text.splitlines()
    except (SyntaxError, UnicodeDecodeError):
        return None, []


def definitions(root: Path | None = None) -> list[Definition]:
    """Every alternative constructor defined in non-test modules of the package.

    Definitions inside ``tests/`` are excluded from the *population* — a
    test-local helper called only by tests is not the defect; the defect is
    production code carrying a consumer no production code consumes.
    """
    found: list[Definition] = []
    for path in source_files(root):
        if _is_test_path(path):
            continue
        tree, lines = _parse_with_lines(path)
        if tree is None:
            continue
        module = path.stem
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            for item in cls.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                # Dunders are excluded by *rule*, not by an allow list. The
                # object-protocol hooks (`__new__`, `__init_subclass__`,
                # `__class_getitem__`) are called by the interpreter and so have
                # no in-repo call site by construction — but naming them in a
                # module-global set would add a fifth **unwatched allow list**
                # to a package that pins itself at four, and an exemption
                # registry nothing watches is the defect `guard_reflexivity`
                # exists to count. A rule needs no watcher.
                if item.name.startswith("__"):
                    continue
                decs = _decorator_names(item)
                kind = next((d for d in CONSTRUCTOR_DECORATORS if d in decs), None)
                if kind is None:
                    continue
                found.append(Definition(module=module, cls=cls.name,
                                        name=item.name, lineno=item.lineno,
                                        kind=kind,
                                        deferred=_is_deferred(lines, item)))
    return found


def module_functions(root: Path | None = None) -> list[Definition]:
    """Every module-level **public** function in non-test modules (population B).

    Module-level means `tree.body`, not `ast.walk` — a closure defined inside
    another function is that function's private business and has no independent
    call surface.  Underscore-prefixed names are excluded by the same reasoning
    that excludes dunders below: a leading `_` is the language's own statement
    that the name is not part of the module's surface, so "nothing outside
    calls it" is the author's intent rather than a finding.
    """
    found: list[Definition] = []
    for path in source_files(root):
        if _is_test_path(path):
            continue
        tree, lines = _parse_with_lines(path)
        if tree is None:
            continue
        for item in tree.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.name.startswith("_"):
                continue
            found.append(Definition(module=path.stem, cls="", name=item.name,
                                    lineno=item.lineno, kind="function",
                                    scope="module",
                                    deferred=_is_deferred(lines, item)))
    return found


def _called_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def call_census(root: Path | None = None) -> tuple[dict[str, int], dict[str, int],
                                                   dict[str, int]]:
    """Count calls and bare mentions by name, split production vs `tests/`.

    Returns ``(prod_calls, test_calls, prod_mentions)``.  A *mention* is an
    attribute access or string literal carrying the name **without** calling it
    — the dispatch-table escape hatch described in the module docstring.  A
    ``def`` statement is not a mention: a definition is not its own caller.
    """
    prod_calls: dict[str, int] = {}
    test_calls: dict[str, int] = {}
    prod_mentions: dict[str, int] = {}

    for path in source_files(root):
        tree = _parse(path)
        if tree is None:
            continue
        is_test = _is_test_path(path)
        calls = test_calls if is_test else prod_calls

        called_nodes: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _called_name(node)
                if name is not None:
                    calls[name] = calls.get(name, 0) + 1
                    called_nodes.add(id(node.func))

        if is_test:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and id(node) not in called_nodes:
                prod_mentions[node.attr] = prod_mentions.get(node.attr, 0) + 1
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Only an exact-match string is treated as a dispatch key; a
                # docstring that happens to contain the name is prose, and
                # prose is what the grep in the docstring above got wrong.
                key = node.value.strip()
                if key.isidentifier():
                    prod_mentions[key] = prod_mentions.get(key, 0) + 1
    return prod_calls, test_calls, prod_mentions


def _grade(prod_calls: int, test_calls: int, prod_mentions: int,
           name: str = "", deferred: bool = False) -> str:
    if prod_calls > 0:
        return "LIVE"
    if prod_mentions > 0:
        return "REFERENCED_NOT_CALLED"
    if test_calls > 0:
        return "TEST_ONLY"
    if deferred:
        # Ordered *after* the reachability verdicts, never before: the marker
        # explains an absence of callers, so a definition that has one is LIVE
        # regardless of what its signature claims. A marker that could override
        # a measurement would be an exemption; this one only labels a residue
        # member the measurement has already put there.
        return "DEFERRED_BY_COST"
    if name.startswith(FRAMEWORK_HOOK_PREFIX):
        # Graded, not filtered — see the module docstring.  A hook pytest
        # resolves by name has no in-repo call site by construction, the same
        # way `__new__` has none, and hiding that behind a filter would be the
        # unwatched allow list this package pins itself against.
        return "FRAMEWORK_DISPATCHED"
    return "UNREACHED"


VERDICTS = ("LIVE", "REFERENCED_NOT_CALLED", "TEST_ONLY",
            "FRAMEWORK_DISPATCHED", "DEFERRED_BY_COST", "UNREACHED")


def reaches(root: Path | None = None,
            population: list[Definition] | None = None) -> list[Reach]:
    """Grade a population (default: every alternative constructor)."""
    prod_calls, test_calls, prod_mentions = call_census(root)
    out: list[Reach] = []
    for defn in (definitions(root) if population is None else population):
        # The `def` line is itself neither a call nor a mention, so nothing has
        # to be subtracted here; `_called_name` only fires on `ast.Call`.
        pc = prod_calls.get(defn.name, 0)
        tc = test_calls.get(defn.name, 0)
        pm = prod_mentions.get(defn.name, 0)
        out.append(Reach(definition=defn, prod_calls=pc, test_calls=tc,
                         prod_mentions=pm,
                         verdict=_grade(pc, tc, pm, defn.name, defn.deferred)))
    return sorted(out, key=lambda r: r.definition.qualname)


def module_reaches(root: Path | None = None) -> list[Reach]:
    """Grade population B — module-level public functions."""
    return reaches(root, population=module_functions(root))


def findings(root: Path | None = None) -> list[Reach]:
    """Population A's residue — constructors no production path reaches."""
    return [r for r in reaches(root) if r.is_finding]


def module_findings(root: Path | None = None) -> list[Reach]:
    """Population B's residue — public functions nothing calls **anywhere**."""
    return [r for r in module_reaches(root) if r.is_finding]


def _tally(rows: list[Reach]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    return counts


def _section(title: str, rows: list[Reach], quiet: tuple[str, ...],
             empty: str) -> list[str]:
    counts = _tally(rows)
    lines = [f"consumer_reach — {len(rows)} {title} "
             + ", ".join(f"{k}={counts.get(k, 0)}" for k in VERDICTS),
             ""]
    for r in rows:
        if r.verdict in quiet:
            continue
        d = r.definition
        lines.append(
            f"  {r.verdict:<22} {d.qualname}:{d.lineno} "
            f"(prod_calls={r.prod_calls} tests={r.test_calls} "
            f"mentions={r.prod_mentions})")
    if len(lines) == 2:
        lines.append(f"  ({empty})")
    return lines


def report(root: Path | None = None) -> str:
    """Both populations, tallied separately — never summed (D-191).

    B's 96 `TEST_ONLY` helpers are listed only in `report --module`; folding
    them into the default view is exactly the burial D-189 refused.
    """
    return "\n".join(
        _section("alternative constructors", reaches(root),
                 quiet=("LIVE",), empty="every constructor has a production caller")
        + [""]
        + _section("module-level public functions", module_reaches(root),
                   quiet=("LIVE", "TEST_ONLY", "REFERENCED_NOT_CALLED"),
                   empty="every public function has a caller somewhere")
        + ["  (TEST_ONLY / REFERENCED_NOT_CALLED elided — see `report --module`)"])


def module_report(root: Path | None = None) -> str:
    """Population B in full, including the 96 test-facing helpers."""
    return "\n".join(_section("module-level public functions",
                              module_reaches(root), quiet=("LIVE",),
                              empty="every public function has a caller somewhere"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("report", "check"), nargs="?",
                    default="report")
    ap.add_argument("--module", action="store_true",
                    help="population B in full, including the test-facing helpers")
    args = ap.parse_args(argv)

    print(module_report() if args.module else report())
    if args.mode == "check":
        # `check` grades **A only**.  B's residue is reported and pinned by a
        # test (`test_consumer_reach.py`) rather than gated: 11 uncalled
        # functions cannot be cleared in one cycle, and a red that stands for
        # weeks is a red nobody reads (D-044).  The pin is the ratchet —
        # B's residue cannot grow without an explicit edit.
        bad = findings()
        if bad:
            print("", file=sys.stderr)
            for r in bad:
                print(f"{r.verdict} {r.definition.qualname} — implemented, "
                      f"tested, and called by no production path", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
