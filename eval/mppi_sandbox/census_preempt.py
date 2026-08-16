"""The pre-empt is a **set** of census re-derivations, not one check.

Sixteen cycles have now shipped a module or a test and discovered at suite time
that the addition joined a population somebody's registry pins — *"every
instrument built to audit a population becomes a member of one"* (D-312/D-313).
The cheap counter-move was found early: re-derive the census before the suite,
in the ~0.3 s it takes, and repair the pin in the same commit.

D-317's cycle is why this module exists, and the shape of its failure is the
whole design.  It **ran** the pre-empt.  ``guard_reflexivity.guards()`` came
back unchanged and clean — and the suite still went red, on ``loop_reach``,
because the test the cycle had just written was a *population claim* and
:data:`loop_reach.READING` had never seen it.  Two censuses, one checked.  The
cost was a full 785 s red suite plus the 788 s green one, which was the whole of
that cycle's 30-minute overrun.

So the finding is not "run the pre-empt" — that was already known and already
done.  It is that **``guards()`` answers one question** ("did I add a guard?")
**and silently declines another** ("did I add a population claim?"), and a cycle
holding one clean reading cannot tell which of the two it took.  A check whose
scope is narrower than its apparent scope reads exactly like a clean one.

What is covered, and what is not
--------------------------------

:data:`CENSUSES` is a typed tuple of three, and typing it is a real limit rather
than an oversight — this package's own D-045/D-047 lesson is that hand-written
population lists come up short, and there is no AST signature that reliably
separates "a census a cycle can join" from any other derived collection.  What
the module does instead of pretending otherwise:

* every entry carries the **registry it reconciles against**, and that registry
  is *read*, never restated here (D-047).  ``loop_reach``'s reading is compared
  against ``loop_reach.READING``; the guard tally against the literal parsed out
  of the assertion that pins it, not against a tally typed into this file.
  There is exactly one statement of each number and this is not it;
* :func:`uncovered` names the censuses a reader should know are absent, so the
  omission is the module's work list rather than its clearance
  (``exemption_control.uncontrolled``'s discipline, applied one level up);
* each entry has a **tamper** in the tests: perturb the derivation, assert the
  check goes ``DRIFT``.  An entry that cannot be made to bite is an entry whose
  clean reading means nothing — which is the exact defect this module was
  written for, and the reason it would otherwise reproduce it.

Cost is the constraint that makes this worth having at all: the three
derivations measure 0.33 s, 0.71 s and 0.89 s, so the whole pass is under two
seconds against the 13-minute suite it pre-empts.  Anything that has to run the
suite to answer belongs in the suite.

Usage — Phase 3, immediately before staging:

.. code-block:: console

   $ python3 -m eval.mppi_sandbox.census_preempt
   CLEAN  guard_tally        N guards, pin N (test_guard_reflexivity.py)
   CLEAN  loop_reach_reading 66 population claims, all in READING
   CLEAN  citation_sites     0 unregistered magnitude citations
   census_preempt — 3 censuses re-derived, all clean.

``rc=1`` on any ``DRIFT``; ``rc=0`` clean.  ``DRIFT`` is a finding you repair in
this commit, not a caveat — it is the same red the suite would give you twelve
minutes later.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PACKAGE = Path(__file__).resolve().parent
TESTS = PACKAGE / "tests"

#: The census agreed with its registry.
CLEAN = "CLEAN"
#: The derivation moved and the registry did not.  Repair before the suite.
DRIFT = "DRIFT"


@dataclass(frozen=True)
class Reading:
    """One census re-derived and reconciled against its registry."""

    census: str
    status: str
    detail: str

    @property
    def is_drift(self) -> bool:
        return self.status == DRIFT

    def line(self) -> str:
        return f"{self.status:<6} {self.census:<18} {self.detail}"


# --------------------------------------------------------------------------
# 1. guard_reflexivity.guards() vs the literal that pins it
# --------------------------------------------------------------------------

#: The assertion that pins the guard tally.  Parsed, not copied — see
#: :func:`pinned_guard_tally`.
GUARD_PIN_TEST = "test_guard_reflexivity.py"


def pinned_guard_tally(tests: Path | None = None) -> int | None:
    """The integer the test suite pins ``len(guards())`` to, or ``None``.

    Read out of the assertion itself rather than restated here: the tally is a
    running one that has moved on most cycles this year, and a second copy of it
    living in the pre-empt would be one more thing to forget — the failure this
    module exists to remove, reintroduced at the level of the fix.

    Recognises the three shapes the suite uses: a direct ``len(gr.guards()) ==
    N``; ``len(pool) == N`` where ``pool`` was assigned from a ``guards()`` call
    earlier in the same function; and — the one that actually pins it —
    ``len(pool) == N`` where ``pool`` is a **pytest fixture parameter** whose
    body returns ``gr.guards()``.  The first draft of this parser handled only
    the first two and reported ``pin NOT FOUND``, which is the correct verdict
    for a parser that cannot see the pin but was not the state of the tree; the
    fixture case is not an edge case here, it is the whole population.

    ``None`` means the pin was not found, which :func:`guard_tally` reports as
    ``DRIFT`` — a pin that moved out from under the parser is exactly as
    actionable as a tally that moved, and failing open would hand back a clean
    reading earned by reading nothing.
    """
    path = (tests or TESTS) / GUARD_PIN_TEST
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fixtures = _guards_fixtures(tree)
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound = {name for name, call in _assignments(fn).items()
                 if _is_guards_call(call)}
        bound |= {a.arg for a in fn.args.args if a.arg in fixtures}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            if not _is_len_of(node.left, bound):
                continue
            right = node.comparators[0]
            if isinstance(right, ast.Constant) and isinstance(right.value, int):
                return right.value
    return None


def _guards_fixtures(tree: ast.Module) -> set[str]:
    """Names of module-level functions that ``return`` a ``guards()`` call.

    Deliberately not keyed on the ``@pytest.fixture`` decorator: what makes the
    parameter a guards population is what the function *returns*, and a helper
    called directly would bind the same way.
    """
    out: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Return) and sub.value is not None \
                    and _is_guards_call(sub.value):
                out.add(node.name)
                break
    return out


def _assignments(fn: ast.AST) -> dict[str, ast.expr]:
    """``name -> assigned expression`` for simple single-target assignments."""
    out: dict[str, ast.expr] = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                out[target.id] = node.value
    return out


def _is_guards_call(expr: ast.expr) -> bool:
    """Is ``expr`` a call to ``guards()`` (bare, dotted, or wrapped in a set)?"""
    for node in ast.walk(expr):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else (
                func.id if isinstance(func, ast.Name) else "")
            if name == "guards":
                return True
    return False


def _is_len_of(expr: ast.expr, bound: set[str]) -> bool:
    """``len(<a guards-derived name>)`` or ``len(<a guards() call>)``."""
    if not isinstance(expr, ast.Call):
        return False
    if not (isinstance(expr.func, ast.Name) and expr.func.id == "len"):
        return False
    if not expr.args:
        return False
    arg = expr.args[0]
    if isinstance(arg, ast.Name):
        return arg.id in bound
    return _is_guards_call(arg)


def guard_tally() -> Reading:
    """Did this cycle add a function ``guard_reflexivity`` reads as a guard?

    The check D-317's cycle *did* run.  It is kept — it caught the class twice —
    but it is now one of three rather than the whole pre-empt, which is the
    correction.
    """
    from . import guard_reflexivity as gr

    derived = len(gr.guards())
    pinned = pinned_guard_tally()
    if pinned is None:
        return Reading("guard_tally", DRIFT,
                       f"{derived} guards, pin NOT FOUND in {GUARD_PIN_TEST} "
                       "— the assertion moved; re-point pinned_guard_tally")
    if derived != pinned:
        delta = derived - pinned
        return Reading("guard_tally", DRIFT,
                       f"{derived} guards vs pin {pinned} ({delta:+d}) — bump "
                       "the tallies before the suite; run "
                       "`python3 -c 'from eval.mppi_sandbox import "
                       "guard_reflexivity as gr; print([g.name for g in "
                       "gr.guards()])'` for the entrants")
    return Reading("guard_tally", CLEAN,
                   f"{derived} guards, pin {pinned} ({GUARD_PIN_TEST})")


# --------------------------------------------------------------------------
# 2. loop_reach.targets() vs READING — the one D-317's cycle missed
# --------------------------------------------------------------------------

def loop_reach_reading() -> Reading:
    """Did this cycle add (or delete) a loop-body population claim?

    The census that went red at 05:00 on 2026-08-17 while ``guards()`` read
    clean.  ``READING`` is a hand-written record of how many elements each
    population-claim assertion actually saw, so a *new* claim is not merely
    unrecorded — it is unrecorded in a registry whose test demands exact
    equality (``set(READING) == want``), and equality fails in both directions.
    """
    from . import loop_reach as lr

    want = {t.test_id.split("::")[-1] for t in lr.targets()}
    recorded = set(lr.READING)
    missing = sorted(want - recorded)
    retired = sorted(recorded - want)
    if missing or retired:
        parts = []
        if missing:
            parts.append(f"{len(missing)} unrecorded: {', '.join(missing[:3])}"
                         + (" …" if len(missing) > 3 else ""))
        if retired:
            parts.append(f"{len(retired)} retired: {', '.join(retired[:3])}"
                         + (" …" if len(retired) > 3 else ""))
        return Reading("loop_reach_reading", DRIFT,
                       "; ".join(parts) + " — run `python3 -m "
                       "eval.mppi_sandbox.loop_reach report` and update READING")
    return Reading("loop_reach_reading", CLEAN,
                   f"{len(want)} population claims, all in READING")


# --------------------------------------------------------------------------
# 3. citation_audit — did this cycle's prose restate a measured magnitude?
# --------------------------------------------------------------------------

def citation_sites() -> Reading:
    """Did this cycle's journal / decisions prose cite an unregistered figure?

    The census a **REPORT-phase** write joins, which is why it belongs beside
    the other two rather than in a separate habit: D-043 already established
    that 4a/4a-bis prose is inside the verification surface, and this is the
    check that surface fails on.
    """
    from . import citation_audit as ca

    sites = ca.unregistered()
    if sites:
        shown = ", ".join(f"{path}:{line}" for _, path, _, line in sites[:3])
        return Reading("citation_sites", DRIFT,
                       f"{len(sites)} unregistered magnitude citation(s): "
                       f"{shown}" + (" …" if len(sites) > 3 else "")
                       + " — register in claim_scope / citation_audit")
    return Reading("citation_sites", CLEAN,
                   "0 unregistered magnitude citations")


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

#: The censuses re-derived by one pass, as ``(name, callable)``.  Typed, and the
#: typing is declared in the module docstring rather than defended: what keeps
#: it honest is :func:`uncovered` plus the per-entry tampers in the tests.
CENSUSES: tuple[tuple[str, Callable[[], Reading]], ...] = (
    ("guard_tally", guard_tally),
    ("loop_reach_reading", loop_reach_reading),
    ("citation_sites", citation_sites),
)

#: Censuses a cycle can join that this pass deliberately does **not** re-derive,
#: with the reason.  Named so the pass's clean reading is scoped out loud — the
#: precise failure D-317's cycle hit was a check reading narrower than it looked.
UNCOVERED: tuple[tuple[str, str], ...] = (
    ("inert_surface pins",
     "the pin set moves on any edit to a *reader*, not on adding a module; "
     "`inert_surface staged` already sits in the Phase 3 commit block and "
     "answers it at the only moment it is answerable (D-199)"),
    ("tsv_timestamp audit",
     "population is `results/*.tsv` rows, which a cycle joins in Phase 3 by "
     "appending — covered by the placed `tsv_timestamp check` (D-154)"),
    ("exemption_control.REGISTRIES",
     "joined only by typing a new module-level exemption set, which is a "
     "deliberate act with its own red test; no cycle has been surprised by it"),
    ("extremum_reading.SITE_CLASSES",
     "re-derived by `extremum_reading.sweep` in both directions, so the "
     "reconciliation *is* the watcher and it runs in the suite (Q-090)"),
)


def uncovered() -> tuple[tuple[str, str], ...]:
    """The censuses this pass omits, with reasons.  See :data:`UNCOVERED`."""
    return UNCOVERED


def readings() -> tuple[Reading, ...]:
    """Re-derive every covered census.  ~2 s total."""
    return tuple(fn() for _, fn in CENSUSES)


def report(rows: tuple[Reading, ...] | None = None) -> str:
    rows = readings() if rows is None else rows
    lines = [r.line() for r in rows]
    drift = [r for r in rows if r.is_drift]
    if drift:
        lines.append(
            f"census_preempt — {len(drift)} of {len(rows)} censuses DRIFTED. "
            "Repair in this commit; the suite would report the same red.")
    else:
        lines.append(
            f"census_preempt — {len(rows)} censuses re-derived, all clean. "
            f"Not covered: {', '.join(name for name, _ in UNCOVERED)}.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in ("report", "check"):
        print(f"usage: python3 -m {__spec__.name} [report|check]",
              file=sys.stderr)
        return 2
    rows = readings()
    print(report(rows))
    return 1 if any(r.is_drift for r in rows) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
