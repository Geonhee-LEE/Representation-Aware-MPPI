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

**Population**: every `classmethod` and `staticmethod` defined on a class in
`eval/mppi_sandbox/` — the alternative-constructor shape, of which `from_sweep`
is one.  Bounded, nameable, and the exact shape of the defect; module-level
functions are a far larger population whose dead members are mostly CLI helpers,
and folding them in would bury the finding in noise.

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


@dataclass(frozen=True)
class Definition:
    """One `classmethod`/`staticmethod`, located."""

    module: str
    cls: str
    name: str
    lineno: int
    kind: str

    @property
    def qualname(self) -> str:
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
        return self.verdict == "TEST_ONLY"


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


def source_files(root: Path | None = None) -> list[Path]:
    """Every `.py` file in the package, tests included, deterministically ordered."""
    base = SANDBOX_DIR if root is None else Path(root)
    return sorted(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return None


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
        tree = _parse(path)
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
                                        kind=kind))
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


def _grade(prod_calls: int, test_calls: int, prod_mentions: int) -> str:
    if prod_calls > 0:
        return "LIVE"
    if prod_mentions > 0:
        return "REFERENCED_NOT_CALLED"
    if test_calls > 0:
        return "TEST_ONLY"
    return "UNREACHED"


def reaches(root: Path | None = None) -> list[Reach]:
    """Grade every alternative constructor in the package."""
    prod_calls, test_calls, prod_mentions = call_census(root)
    out: list[Reach] = []
    for defn in definitions(root):
        # The `def` line is itself neither a call nor a mention, so nothing has
        # to be subtracted here; `_called_name` only fires on `ast.Call`.
        pc = prod_calls.get(defn.name, 0)
        tc = test_calls.get(defn.name, 0)
        pm = prod_mentions.get(defn.name, 0)
        out.append(Reach(definition=defn, prod_calls=pc, test_calls=tc,
                         prod_mentions=pm,
                         verdict=_grade(pc, tc, pm)))
    return sorted(out, key=lambda r: r.definition.qualname)


def findings(root: Path | None = None) -> list[Reach]:
    """The `TEST_ONLY` residue — constructors only their own tests reach."""
    return [r for r in reaches(root) if r.is_finding]


def report(root: Path | None = None) -> str:
    rows = reaches(root)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    lines = [
        f"consumer_reach — {len(rows)} alternative constructors "
        + ", ".join(f"{k}={counts.get(k, 0)}"
                    for k in ("LIVE", "REFERENCED_NOT_CALLED", "TEST_ONLY",
                              "UNREACHED")),
        "",
    ]
    for r in rows:
        if r.verdict == "LIVE":
            continue
        d = r.definition
        lines.append(
            f"  {r.verdict:<22} {d.qualname}:{d.lineno} "
            f"(prod_calls={r.prod_calls} tests={r.test_calls} "
            f"mentions={r.prod_mentions})")
    if len(lines) == 2:
        lines.append("  (every constructor has a production caller)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("report", "check"), nargs="?",
                    default="report")
    args = ap.parse_args(argv)

    print(report())
    if args.mode == "check":
        bad = findings()
        if bad:
            print("", file=sys.stderr)
            for r in bad:
                print(f"TEST_ONLY {r.definition.qualname} — implemented, tested, "
                      f"and called by no production path", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
