"""Which tests actually roll out — derived statically, and measured for free.

Q-203's problem, stated in its own units: the lam cascade cannot be enumerated
inside a cycle.  Three cycles tried and all three timed out — a ``-x``-less fast
subset over 420 s, a narrowed ten-module selection over 150 s, a ``-k``
selection killed at six minutes.  The cause is the same each time and it is not
the suite's size: the lam test modules put **table** assertions and **rollout**
assertions in the same file, so neither module selection nor ``-k`` separates
them, and ``-m "not slow"`` does not filter them because nobody ever marked
them.

You cannot mark what you cannot name.  This module names it two ways.

Two readings, and the gap between them is the answer
----------------------------------------------------

* :func:`derived_rollout_tests` — Q-203 option **(b)**.  Walk the call graph
  from a declared set of rollout primitives (:data:`ROLLOUT_PRIMITIVES`) and
  report the test functions that reach one.  Costs ~0.1 s; runs on every
  ``census_preempt`` if anyone wants it there.
* :func:`parse_durations` — Q-203 option **(a)**.  Read the ``--durations``
  block pytest already prints, and report what the clock says.  Costs **zero**
  extra suite time, because ``push_preflight record`` runs the suite anyway and
  keeps its full terminal output in a sidecar log (``<out>.log``).  The flag is
  pure byproduct — this is Q-168's shape, an instrument that falls out of a run
  someone is already paying for.

:func:`compare` puts them side by side.  ``derived_only`` is where the static
walk over-approximates; ``measured_only`` is the **indirect call** the walk
missed, and per Q-203 that set *is* the real answer, because it is the part a
census cannot be trusted to hold.

Why the walk is name-based, and why that is the safe direction
--------------------------------------------------------------

Resolving ``ab.seed_sweep`` through imports, aliases, re-exports and
``getattr`` is a static-analysis project.  This is not one.  The graph here is
keyed on the **called name alone** — ``seed_sweep`` reaches, wherever it was
bound from — so two unrelated functions sharing a name are conflated.

That conflation only ever adds tests to the derived set, never removes one.
For the use this is put to (deciding what to mark ``@pytest.mark.slow``) an
over-mark costs a test that runs in the slow lane unnecessarily, and an
under-mark costs a timeout of the kind that has now eaten three cycles.  The
error is therefore pointed the cheap way on purpose, and :func:`compare` is how
the expensive direction gets caught anyway: anything the walk missed shows up in
``measured_only`` the next time a receipt is taken.

The primitive set is declared, not inferred, and pinned by a test
-----------------------------------------------------------------

:data:`ROLLOUT_PRIMITIVES` is a literal, which is D-047's hazard — a hand-typed
copy of a registry drifts away from it silently, exactly as the push rule's
three-path ``grep`` drifted from ``DECLARED_LOCAL_ONLY``'s five.  The mitigation
is not to infer it (there is nothing to infer it *from*: "spends wall clock" is
not a property the source declares) but to **pin** it: a test asserts every name
here still resolves to a function in :mod:`eval.mppi_sandbox.ab`, so a rename
turns the literal red instead of quietly emptying the derived set.

An emptied derived set is the failure mode that matters, because it presents as
"no test rolls out" — a clean-looking reading, and the same shape D-317 paid
785 s for.  :func:`derived_rollout_tests` therefore has a non-emptiness test of
its own.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from . import tree_provenance as tp

#: Functions whose call is a rollout — i.e. whose cost is simulation, not
#: assertion.  ``seed_sweep`` is the floor: every scenario-running helper in the
#: sandbox reaches the simulator through it (``lam_ladder`` calls it in a loop,
#: ``arrival_spread``/``avoidance_*``/``barrier_ceiling`` all call it directly).
#: ``lam_ladder`` is listed anyway so a test that calls only the ladder is
#: derived in one hop rather than two, which keeps the graph legible.
ROLLOUT_PRIMITIVES = frozenset({"seed_sweep", "lam_ladder"})

#: Directories walked to build the call graph.  Relative to the repo root.
SOURCE_DIRS = ("eval/mppi_sandbox", "eval/mppi_sandbox/tests", "eval/tests")

#: pytest's ``--durations`` lines: ``0.12s call     path::test_name``.  Only the
#: ``call`` phase is read — ``setup``/``teardown`` time belongs to fixtures, and
#: attributing a fixture's rollout to the test that happened to trigger it first
#: would mark one test slow and its siblings fast for no reason a reader could
#: check.
_DURATION_LINE = re.compile(
    r"^\s*([0-9]+\.[0-9]+)s\s+call\s+(\S+::\S+)\s*$", re.MULTILINE
)


@dataclass(frozen=True)
class Comparison:
    """The two readings, partitioned.  ``measured_only`` is Q-203's answer."""

    both: tuple[str, ...]
    derived_only: tuple[str, ...]
    measured_only: tuple[str, ...]

    def describe(self) -> str:
        return (
            f"both={len(self.both)} "
            f"derived_only={len(self.derived_only)} "
            f"measured_only={len(self.measured_only)}"
        )


def _root(root: Path | None = None) -> Path:
    return root or tp.REPO_ROOT


def _bindings(tree: ast.Module, stem: str) -> tuple[dict[str, str], dict[str, str]]:
    """This file's import namespace, split into module aliases and name imports.

    Returns ``(alias → module_stem, imported_name → "module_stem.name")``.  Only
    the last path component is kept, because two modules with the same stem do
    not exist in this tree and carrying the full dotted path would make the
    graph keys unreadable for no gained precision.
    """
    aliases: dict[str, str] = {}
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = alias.name.rsplit(".", 1)[-1]
                aliases[alias.asname or target] = target
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").rsplit(".", 1)[-1]
            for alias in node.names:
                # `from . import ab` / `from eval.mppi_sandbox import ab` bind a
                # *module*; `from ...ab import seed_sweep` binds a *function*.
                # Told apart by case-free convention here: the sandbox has no
                # module named like a function, so a lowercase target that is
                # also a file in the package is a module.
                bound = alias.asname or alias.name
                if node.level and not mod:
                    aliases[bound] = alias.name
                else:
                    names[bound] = f"{mod}.{alias.name}" if mod else alias.name
                    aliases.setdefault(bound, alias.name)
    aliases.setdefault(stem, stem)
    return aliases, names


def _called_qualnames(
    node: ast.AST, stem: str, aliases: dict[str, str], names: dict[str, str],
    local: set[str],
) -> set[str]:
    """Every call under *node*, resolved to ``module.func`` where it can be.

    ``ab.seed_sweep()`` resolves through *aliases*; a bare ``seed_sweep()``
    resolves through *names* (an ``import from``) or *local* (defined in this
    file).  A call this cannot key — ``d["k"]()``, a method on an expression, a
    name bound at runtime — is **dropped** rather than guessed, which is the
    under-approximating direction and is why :func:`compare` exists.
    """
    out: set[str] = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            mod = aliases.get(func.value.id)
            if mod:
                out.add(f"{mod}.{func.attr}")
        elif isinstance(func, ast.Name):
            if func.id in names:
                out.add(names[func.id])
            elif func.id in local:
                out.add(f"{stem}.{func.id}")
    return out


def call_graph(root: Path | None = None) -> dict[str, set[str]]:
    """Map ``module.func`` to the qualified names it calls.

    Keyed on ``module.func`` rather than the bare name.  The bare-name version
    was tried first and measured **2428 of ~4233 tests** reaching a rollout —
    57% of the suite, which is not a marker signal, it is noise.  The cause is
    ordinary helper names (``run``, ``report``, ``build``) colliding across
    modules and welding the whole graph into one component.  Qualifying the key
    costs an import table per file and removes the collision.
    """
    graph: dict[str, set[str]] = {}
    base = _root(root)
    for rel in SOURCE_DIRS:
        directory = base / rel
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            stem = path.stem
            aliases, names = _bindings(tree, stem)
            local = {
                n.name
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    graph.setdefault(f"{stem}.{node.name}", set()).update(
                        _called_qualnames(node, stem, aliases, names, local)
                    )
    return graph


def qualified_primitives() -> frozenset[str]:
    """:data:`ROLLOUT_PRIMITIVES` as ``ab.<name>``, the graph's key form."""
    return frozenset(f"ab.{n}" for n in ROLLOUT_PRIMITIVES)


def reaching_names(root: Path | None = None) -> frozenset[str]:
    """``module.func`` names that transitively reach a rollout primitive.

    Least-fixed-point over :func:`call_graph`; the primitives themselves are in
    the result, so a test calling one directly is reported without a special
    case.
    """
    graph = call_graph(root)
    reaching = set(qualified_primitives())
    changed = True
    while changed:
        changed = False
        for name, called in graph.items():
            if name not in reaching and called & reaching:
                reaching.add(name)
                changed = True
    return frozenset(reaching)


def derived_rollout_tests(root: Path | None = None) -> tuple[str, ...]:
    """``path::test_name`` for every test function that reaches a rollout.

    Paths are repo-relative so the output can be diffed against a
    ``--durations`` reading, whose node ids pytest also prints repo-relative
    when invoked from the root.
    """
    base = _root(root)
    reaching = reaching_names(root)
    out: list[str] = []
    for rel in SOURCE_DIRS:
        directory = base / rel
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("test_*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            stem = path.stem
            aliases, names = _bindings(tree, stem)
            local = {
                n.name
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test_"):
                    continue
                called = _called_qualnames(node, stem, aliases, names, local)
                if called & reaching:
                    out.append(f"{path.relative_to(base)}::{node.name}")
    return tuple(sorted(set(out)))


def parse_durations(text: str) -> dict[str, float]:
    """Node id → slowest ``call``-phase duration seen in *text*.

    *text* is the whole terminal output of a receipt run.  Under
    ``push_preflight record_sharded`` that is **fourteen** concatenated pytest
    streams, so there are fourteen ``--durations`` blocks and a node id can
    appear more than once (a shard boundary does not split a test, but a rerun
    or a parametrised id can repeat).  The max is kept, because the question the
    number answers is "could this test have caused the timeout".
    """
    out: dict[str, float] = {}
    for seconds, nodeid in _DURATION_LINE.findall(text):
        value = float(seconds)
        if value > out.get(nodeid, -1.0):
            out[nodeid] = value
    return out


def measured_rollout_tests(text: str, threshold: float = 1.0) -> tuple[str, ...]:
    """Node ids from *text* whose ``call`` phase took at least *threshold* s.

    The default is deliberately low.  A rollout in this sandbox costs ~0.31 s
    (D-467), so a test that does one is already above a pure-assertion test by
    an order of magnitude, and the interesting tail — the ones that sweep seeds
    or walk a ladder — is tens of seconds.  A high threshold would hide exactly
    the single-rollout tests the derived walk is most likely to be right about.
    """
    return tuple(sorted(n for n, s in parse_durations(text).items() if s >= threshold))


def compare(text: str, threshold: float = 1.0, root: Path | None = None) -> Comparison:
    """Partition the derived and measured sets.

    A node id is compared as pytest prints it, so a parametrised measured id
    (``test_x[case]``) will not match the derived id (``test_x``); the base name
    is stripped for the comparison so parametrisation does not manufacture a
    false ``measured_only``.
    """
    derived = set(derived_rollout_tests(root))
    measured = {_debracket(n) for n in measured_rollout_tests(text, threshold)}
    return Comparison(
        both=tuple(sorted(derived & measured)),
        derived_only=tuple(sorted(derived - measured)),
        measured_only=tuple(sorted(measured - derived)),
    )


def _debracket(nodeid: str) -> str:
    """``a.py::test_x[case-3]`` → ``a.py::test_x``."""
    head, sep, _ = nodeid.partition("[")
    return head if sep else nodeid


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.lam_rollout",
        description="Which tests roll out — derived statically, measured for free.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("derive", help="static call-graph walk (Q-203 option b)")
    for name in ("measure", "compare"):
        p = sub.add_parser(name, help="read a receipt's --durations sidecar log")
        p.add_argument("log", type=Path)
        p.add_argument("--threshold", type=float, default=1.0)

    args = ap.parse_args(argv)

    if args.cmd == "derive":
        tests = derived_rollout_tests()
        for nodeid in tests:
            print(nodeid)
        print(f"lam_rollout — {len(tests)} test(s) reach a rollout primitive.")
        return 0

    try:
        text = args.log.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"lam_rollout — unreadable log {args.log}: {exc}")
        return 0

    if args.cmd == "measure":
        rows = sorted(parse_durations(text).items(), key=lambda kv: -kv[1])
        rows = [(n, s) for n, s in rows if s >= args.threshold]
        for nodeid, seconds in rows:
            print(f"{seconds:8.2f}s  {nodeid}")
        if not rows:
            print(
                "lam_rollout — NO_DURATIONS: the log carries no `--durations` "
                "block. Re-take the receipt with `-- ... --durations=40`."
            )
        return 0

    cmp = compare(text, args.threshold)
    print(f"lam_rollout — {cmp.describe()}")
    for label, group in (
        ("measured_only (indirect call the walk missed — Q-203's answer)",
         cmp.measured_only),
        ("derived_only (walk over-approximated)", cmp.derived_only),
    ):
        print(f"\n== {label} ==")
        for nodeid in group:
            print(f"  {nodeid}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
