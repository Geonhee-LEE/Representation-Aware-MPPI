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

:data:`CENSUSES` is a typed tuple, and typing it is a real limit rather
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

The fourth entry arrived by the same route as the second, one cycle later and
one registry over.  D-330 shipped a **cosmetic** ``if arm in
REPRESENTATION_ARMS`` tag in a printer, which matched ``guard_reflexivity``'s
entry shape and would have registered a *category* constant as a watched
exemption in four allow-list registries.  The pre-empt ran, read clean on its
three, and the suite went red 811 s later — four of the seven moved pins sitting
in registries this module's own ``Not covered:`` line names.  That line had
excused the omission on the grounds that joining the population "is a deliberate
act"; the tag was not a deliberate act, and the excuse was wrong in its premise
rather than its accounting.  **The detector reads shape, not intent** — so a
population a cycle cannot mean to join is exactly the one it needs warning
about, and the derivation costs 0.35 s.

Cost is the constraint that makes this worth having at all: the whole pass runs
in a couple of seconds against the suite it pre-empts, and
:func:`test_the_whole_pass_is_cheaper_than_the_suite_it_pre_empts` is what holds
that true as entries are added.  Anything that has to run the suite to answer
belongs in the suite.

The sixth entry is the third to arrive from *neither* list — ``loop_reach``
(D-317), ``consumer_reach`` (D-344), and now ``default_lam_sites``, which cost
D-433 an overnight strand.  Three of the same shape is no longer a run of bad
luck about which censuses got typed; see :func:`lam_site_census`, and Q-183 for
whether the candidate population can be derived instead of typed at all.

Usage — Phase 3, immediately before staging:

.. code-block:: console

   $ python3 -m eval.mppi_sandbox.census_preempt
   CLEAN  guard_tally        N guards, pin N (test_guard_reflexivity.py)
   CLEAN  loop_reach_reading 66 population claims, all in READING
   CLEAN  citation_sites     0 unregistered magnitude citations
   CLEAN  exemption_registry 8 unwatched allow-lists, pin matches (…)
   census_preempt — 4 censuses re-derived, all clean.

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
        return f"{self.status:<6} {self.census:<22} {self.detail}"


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
# 4. guard_reflexivity.unwatched_exemptions() vs the set literal that pins it
# --------------------------------------------------------------------------

#: The assertion that pins the unwatched allow-list set.  Parsed, not copied,
#: for :func:`pinned_guard_tally`'s reason.
EXEMPTION_PIN_TEST = "test_guard_reflexivity.py"


def pinned_unwatched_exemptions(tests: Path | None = None) -> set[str] | None:
    """The allow-list names the suite pins ``unwatched_exemptions()`` to.

    Recognises ``set(<name>) == {"A", "B", ...}`` where ``<name>`` was assigned
    from an :func:`~guard_reflexivity.unwatched_exemptions` call earlier in the
    same function.  ``None`` means the pin was not found, which
    :func:`exemption_registry` reports as ``DRIFT`` on
    :func:`pinned_guard_tally`'s reasoning — failing open would hand back a
    clean reading earned by reading nothing.
    """
    path = (tests or TESTS) / EXEMPTION_PIN_TEST
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound = {name for name, call in _assignments(fn).items()
                 if _is_call_to(call, "unwatched_exemptions")}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            if not _is_set_of(node.left, bound):
                continue
            names = _string_set(node.comparators[0])
            if names is not None:
                return names
    return None


def _is_call_to(expr: ast.expr, func_name: str) -> bool:
    """Is ``expr`` a call to ``func_name`` (bare or dotted)?"""
    for node in ast.walk(expr):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else (
                func.id if isinstance(func, ast.Name) else "")
            if name == func_name:
                return True
    return False


def _is_set_of(expr: ast.expr, bound: set[str]) -> bool:
    """``set(<an unwatched-derived name>)`` or ``set(<the call itself>)``."""
    if not isinstance(expr, ast.Call):
        return False
    if not (isinstance(expr.func, ast.Name) and expr.func.id == "set"):
        return False
    if not expr.args:
        return False
    arg = expr.args[0]
    if isinstance(arg, ast.Name):
        return arg.id in bound
    return _is_call_to(arg, "unwatched_exemptions")


def _string_set(expr: ast.expr) -> set[str] | None:
    """The literal ``{"A", "B"}`` as a set of ``str``, or ``None``."""
    if not isinstance(expr, ast.Set):
        return None
    out: set[str] = set()
    for elt in expr.elts:
        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
            return None
        out.add(elt.value)
    return out


def exemption_registry() -> Reading:
    """Did this cycle's code enter the ``TYPED`` allow-list population?

    The census **D-330 paid 811 s for**, and the reason this module's own
    ``Not covered:`` line is one entry shorter than it was.  That line used to
    excuse the omission with *"joined only by typing a new module-level
    exemption set, which is a deliberate act with its own red test; no cycle
    has been surprised by it."*  A cycle then got surprised by it: a
    **cosmetic** ``if arm in REPRESENTATION_ARMS`` tag in a printer matched
    ``guard_reflexivity``'s entry shape, which would have registered a
    *category* constant as a watched exemption across four allow-list
    registries.  Nothing about that was deliberate, and the red test arrived
    thirteen minutes late.

    So the excuse was wrong in its premise rather than its accounting: the
    detector reads **shape, not intent**, and a shape can be typed by accident
    in a line that means nothing.  The derivation costs 0.35 s.
    """
    from . import guard_reflexivity as gr

    derived = set(gr.unwatched_exemptions())
    pinned = pinned_unwatched_exemptions()
    if pinned is None:
        return Reading("exemption_registry", DRIFT,
                       f"{len(derived)} unwatched allow-lists, pin NOT FOUND "
                       f"in {EXEMPTION_PIN_TEST} — the assertion moved; "
                       "re-point pinned_unwatched_exemptions")
    entered = sorted(derived - pinned)
    left = sorted(pinned - derived)
    if entered or left:
        parts = []
        if entered:
            parts.append(f"{len(entered)} entered: {', '.join(entered[:3])}"
                         + (" …" if len(entered) > 3 else ""))
        if left:
            parts.append(f"{len(left)} left: {', '.join(left[:3])}"
                         + (" …" if len(left) > 3 else ""))
        return Reading("exemption_registry", DRIFT,
                       "; ".join(parts) + " — a TYPED allow-list population "
                       "moved; if the entrant is a *category* constant the "
                       "repair is to delete the membership test, not to bump "
                       "the pin (D-330)")
    return Reading("exemption_registry", CLEAN,
                   f"{len(derived)} unwatched allow-lists, pin matches "
                   f"({EXEMPTION_PIN_TEST})")


# --------------------------------------------------------------------------
# 5. consumer_reach.findings() vs the list literals that pin it
# --------------------------------------------------------------------------

#: The assertions that pin the two dead-code residues.  Parsed, not copied, for
#: :func:`pinned_guard_tally`'s reason.
REACH_PIN_TEST = "test_consumer_reach.py"

#: ``census kind -> the ``consumer_reach`` callable whose residue is pinned``.
#: Two populations, not one: a definition can be unreached at *function* scope
#: while its module is reached, so the two lists move independently.
REACH_KINDS: tuple[str, ...] = ("findings", "module_findings")


def pinned_reach_residue(kind: str,
                         tests: Path | None = None) -> set[str] | None:
    """The qualnames the suite pins ``consumer_reach.<kind>()`` to.

    Recognises ``sorted(<gen over cr.<kind>()>) == ["a", "b", ...]``.  ``None``
    means the pin was not found, reported as ``DRIFT`` on
    :func:`pinned_guard_tally`'s reasoning: a clean reading earned by reading
    nothing is the defect this module exists to remove.
    """
    path = (tests or TESTS) / REACH_PIN_TEST
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.Eq):
            continue
        if not _calls_exactly(node.left, kind):
            continue
        names = _string_elements(node.comparators[0])
        if names is not None:
            return names
    return None


def _calls_exactly(expr: ast.expr, name: str) -> bool:
    """Does ``expr`` contain a call to exactly ``name``?

    Exact rather than suffix matching: ``module_findings`` must not answer for
    ``findings``, or the two populations collapse into one pin and a move in
    either goes unread.
    """
    for node in ast.walk(expr):
        if isinstance(node, ast.Call):
            func = node.func
            called = func.attr if isinstance(func, ast.Attribute) else (
                func.id if isinstance(func, ast.Name) else "")
            if called == name:
                return True
    return False


def _string_elements(expr: ast.expr) -> set[str] | None:
    """The string constants of a list/tuple literal, or ``None``."""
    if not isinstance(expr, (ast.List, ast.Tuple)):
        return None
    out: set[str] = set()
    for elt in expr.elts:
        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
            return None
        out.add(elt.value)
    return out


def consumer_reach_residue() -> Reading:
    """Did this cycle add a definition nobody calls?

    The census **D-344's branch paid two red receipts for** (12:00 cost 1305 s),
    and the one this module's ``Not covered:`` line did not name — so it was in
    neither the covered set nor the scoped-out one.  That is strictly worse than
    an admitted omission: :func:`uncovered` exists precisely so a clean reading
    states its own scope, and a census absent from *both* lists is invisible to
    that discipline.  D-318 wrote "read the ``UNCOVERED`` line"; a reader who
    did was still not told about this one.

    The joining move is the most ordinary thing a cycle does — add a helper and
    wire its caller in a later commit, or ship a constructor the tests exercise
    and production does not.  Both residues are pinned as *populations* rather
    than counts (D-343), so the repair direction is legible: wire a caller, or
    edit the list in the same commit.  The derivation costs ~0.9 s.
    """
    from . import consumer_reach as cr

    parts: list[str] = []
    total = 0
    for kind in REACH_KINDS:
        derived = {r.definition.qualname for r in getattr(cr, kind)()}
        total += len(derived)
        pinned = pinned_reach_residue(kind)
        if pinned is None:
            return Reading("consumer_reach_residue", DRIFT,
                           f"{kind} pin NOT FOUND in {REACH_PIN_TEST} — the "
                           "assertion moved; re-point pinned_reach_residue")
        entered = sorted(derived - pinned)
        left = sorted(pinned - derived)
        if entered:
            parts.append(f"{kind} +{len(entered)}: {', '.join(entered[:3])}"
                         + (" …" if len(entered) > 3 else ""))
        if left:
            parts.append(f"{kind} -{len(left)}: {', '.join(left[:3])}"
                         + (" …" if len(left) > 3 else ""))
    if parts:
        return Reading("consumer_reach_residue", DRIFT,
                       "; ".join(parts) + " — a dead-code residue moved; wire "
                       "a production caller (the verdict flips to LIVE) or "
                       "edit the pinned list in this commit (D-044)")
    return Reading("consumer_reach_residue", CLEAN,
                   f"{total} pinned residue entries across "
                   f"{len(REACH_KINDS)} populations ({REACH_PIN_TEST})")


# --------------------------------------------------------------------------
# 6. default_lam_sites.census() vs the triple that pins it
# --------------------------------------------------------------------------

#: The assertion that pins the lam-site triple.  Parsed, not copied, for
#: :func:`pinned_guard_tally`'s reason.
LAM_PIN_TEST = "test_default_lam_sites.py"

#: The three counts the pin carries, in the order the assertion writes them.
LAM_KINDS: tuple[str, ...] = ("decides", "defaults", "forwards")


def pinned_lam_triple(tests: Path | None = None) -> dict[str, int] | None:
    """The ``(decides, defaults, forwards)`` triple the suite pins.

    Recognises ``(c.decides, c.defaults, c.forwards) == (N, N, N)`` where ``c``
    was assigned from a :func:`~default_lam_sites.census` call.  Keyed on the
    **attribute names** rather than on tuple position, so a reordered assertion
    is read correctly instead of silently transposing two counts.

    ``None`` means the pin was not found, reported as ``DRIFT`` on
    :func:`pinned_guard_tally`'s reasoning.
    """
    path = (tests or TESTS) / LAM_PIN_TEST
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        bound = {name for name, call in _assignments(fn).items()
                 if _is_call_to(call, "census")}
        if not bound:
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare) or len(node.ops) != 1:
                continue
            if not isinstance(node.ops[0], ast.Eq):
                continue
            keys = _census_attrs(node.left, bound)
            values = _int_elements(node.comparators[0])
            if keys is None or values is None or len(keys) != len(values):
                continue
            if set(keys) != set(LAM_KINDS):
                continue
            return dict(zip(keys, values))
    return None


def _census_attrs(expr: ast.expr, bound: set[str]) -> list[str] | None:
    """``(c.decides, c.defaults, …)`` as the list of attribute names."""
    if not isinstance(expr, ast.Tuple):
        return None
    out: list[str] = []
    for elt in expr.elts:
        if not isinstance(elt, ast.Attribute):
            return None
        if not (isinstance(elt.value, ast.Name) and elt.value.id in bound):
            return None
        out.append(elt.attr)
    return out


def _int_elements(expr: ast.expr) -> list[int] | None:
    """The int constants of a tuple/list literal, in order, or ``None``."""
    if not isinstance(expr, (ast.Tuple, ast.List)):
        return None
    out: list[int] = []
    for elt in expr.elts:
        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, int)
                and not isinstance(elt.value, bool)):
            return None
        out.append(elt.value)
    return out


def lam_site_census() -> Reading:
    """Did this cycle add a call site that decides, defaults, or forwards ``lam``?

    **The third census to be in neither list**, and the one that says the
    ``Not covered:`` discipline is not enough on its own.  ``loop_reach``
    (D-317) and ``consumer_reach`` (D-344) each arrived the same way; this one
    cost D-433 an overnight strand — that cycle swept ``w_omega`` through a
    single ``run_scenario(..., params=MPPIParams(**kw))`` call, which entered
    ``forwards`` as one site, left the pin red at 42 against a derived 43, and
    its own push gate refused.  The commit sat unmeasured until 02:00 the next
    morning, and the pre-empt read ``CLEAN`` the whole time.

    The joining move is the most ordinary thing a *measuring* cycle does: run a
    sweep.  Every knob sweep this branch has shipped — D-428, D-430, D-433 —
    moved ``forwards`` by exactly one, so this is not a rare shape but the
    signature of the work the roadmap is currently made of.  That is what makes
    the omission expensive rather than merely untidy: the census most likely to
    move was the census nobody was reading.

    Pinned as a **triple** rather than a total, and read back by attribute name,
    because the counts move independently and a compensating pair (one site
    migrating between kinds) is exactly what the separate pins exist to catch.
    The derivation costs ~0.6 s.
    """
    from . import default_lam_sites as dls

    c = dls.census()
    derived = {kind: getattr(c, kind) for kind in LAM_KINDS}
    pinned = pinned_lam_triple()
    if pinned is None:
        return Reading("lam_site_census", DRIFT,
                       f"derived {tuple(derived[k] for k in LAM_KINDS)}, pin "
                       f"NOT FOUND in {LAM_PIN_TEST} — the assertion moved; "
                       "re-point pinned_lam_triple")
    moved = [f"{k} {pinned[k]}→{derived[k]}"
             for k in LAM_KINDS if pinned[k] != derived[k]]
    if moved:
        return Reading("lam_site_census", DRIFT,
                       ", ".join(moved) + " — a lam call site entered or left; "
                       "bump the pinned triple (and the separately pinned "
                       f"total) in {LAM_PIN_TEST} in this commit, naming the "
                       "entrant as that file's comment sequence does")
    return Reading("lam_site_census", CLEAN,
                   f"{c.total} lam sites "
                   f"({'/'.join(str(derived[k]) for k in LAM_KINDS)}), "
                   f"pin matches ({LAM_PIN_TEST})")


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------
# 7. the shipped-scene population vs the set literal that pins it
# --------------------------------------------------------------------------

#: The test whose module-level set literals pin the avoidance-scene population.
SCENE_PIN_TEST = "test_avoidance_coverage.py"

#: The pinned name.  ``AVOIDANCE_REPORTABLE`` is derived *from* this one by a
#: set difference in the same file, so pinning the base name covers both: a
#: scene that enters ``AVOIDANCE_CAPABLE`` enters the reportable set too unless
#: it is the one documented subtraction.
SCENE_PIN_NAME = "AVOIDANCE_CAPABLE"


def pinned_avoidance_capable(tests: Path | None = None) -> set[str] | None:
    """The scene names the suite pins the avoidance-capable population to.

    Read out of the test's module-level ``AVOIDANCE_CAPABLE = {...}`` literal
    rather than restated here, for :func:`pinned_guard_tally`'s reason: there
    is exactly one statement of this population and it is not in this file.
    ``None`` means the literal was not found, which :func:`scene_population`
    reports as ``DRIFT`` — failing open would hand back a clean reading earned
    by reading nothing.
    """
    path = (tests or TESTS) / SCENE_PIN_TEST
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = {t.id for t in node.targets if isinstance(t, ast.Name)}
        if SCENE_PIN_NAME not in targets:
            continue
        return _string_set(node.value)
    return None


def scene_population() -> Reading:
    """Did this cycle add, drop, or re-classify a shipped scenario scene?

    The **fourth** census to arrive from neither list, and the first whose
    population is a directory of data files rather than a shape in the source.
    Measured 2026-08-24 10:00: a tenth yaml sitting in ``eval/scenarios/``
    failed two pinned assertions in 0.16 s, while this pass re-derived its six
    censuses and reported *all clean* — and ``uncovered()`` did not name the
    omission either, so D-318's "read the ``UNCOVERED`` line" would not have
    warned anyone.  Absent from both lists reads exactly like coverage, which
    is the defect this module exists for (D-317 / D-344 / D-433).

    The entry is cheap for the reason the omission was expensive: the
    derivation is a glob plus a per-scene predicate, ~0.2 s, against a
    ~1444 s suite.  It is also the census a *scene-addition* cycle joins by
    construction — Q-197's implementation cycle is precisely such a cycle, and
    this is what re-prices it from two suites to one.
    """
    import glob as _glob

    from .feasibility import is_avoidance_measurable
    from .scenario import load_scenario

    pinned = pinned_avoidance_capable()
    if pinned is None:
        return Reading("scene_population", DRIFT,
                       f"pin {SCENE_PIN_NAME} NOT FOUND in {SCENE_PIN_TEST} "
                       "— the literal moved; re-point "
                       "pinned_avoidance_capable")
    paths = sorted(p for p in _glob.glob("eval/scenarios/*.yaml")
                   if "lam_windows" not in p)
    derived: set[str] = set()
    for path in paths:
        try:
            scene = load_scenario(path)
        except Exception:  # a malformed yaml is the suite's finding, not ours
            continue
        if is_avoidance_measurable(scene):
            derived.add(scene.name)
    entered = sorted(derived - pinned)
    left = sorted(pinned - derived)
    if entered or left:
        parts = []
        if entered:
            parts.append(f"{len(entered)} entered: {', '.join(entered[:3])}"
                         + (" …" if len(entered) > 3 else ""))
        if left:
            parts.append(f"{len(left)} left: {', '.join(left[:3])}"
                         + (" …" if len(left) > 3 else ""))
        return Reading("scene_population", DRIFT,
                       "; ".join(parts) + f" — the scene population {SCENE_PIN_TEST} "
                       "pins moved; an added scene must be entered in BOTH "
                       f"{SCENE_PIN_NAME} and the derived-and-compared counts "
                       "D-454 enumerates (23 glob consumers, 4 literal pins)")
    return Reading("scene_population", CLEAN,
                   f"{len(paths)} shipped scenes, {len(derived)} avoidance-capable, "
                   f"pin matches ({SCENE_PIN_TEST})")


# --------------------------------------------------------------------------
# 8. the shipped-scene *count* vs the integer literals that pin it
# --------------------------------------------------------------------------
#
# Entry 7 above covers the scene *set* — which names are avoidance-capable.  It
# does not cover the scene *count*, and the two move together but are pinned
# apart: eight tests assert the integer ``8`` about the shipped matrix, none of
# them through ``AVOIDANCE_CAPABLE``.  D-455 shipped entry 7 and named four
# literals still uncovered; this entry is that work list, and taking it turned
# up two things the list did not have.
#
# **The count pins cannot be found by grep, and this is the reason.** The
# shipped-scene count and the controller-arm count are *both 8*.  So ``== 8``
# is ambiguous at the shape level — ``len(col) == 8`` in
# ``test_head_on_threshold_cannot_be_passed_by_any_arm`` is a column of eight
# **arms** and does not move when a ninth scene lands, while ``len(rows) == 8``
# one file over is scenes and does.  No AST signature separates them; only the
# quantity's meaning does.  That is why the registry below is typed, and why
# typing it is not the same concession the module docstring makes for
# :data:`CENSUSES`: here the population is *enumerable* and enumerated, and the
# decoys are enumerated beside it so the next reader does not re-derive the
# disambiguation from scratch.
#
# Consequence for the list D-455 left: of its four literals, ``len(col) == 8``
# is a **decoy** — an arm count that a scene-addition cycle must *not* touch —
# and the remaining three are joined by **six more** scene pins that were on
# nobody's list.  A cycle that had worked D-455's list literally would have
# bumped one pin that should not move and missed six that must.

#: ``test file -> test functions whose body pins the shipped-scene count``.
#:
#: Read by AST at the named function, never restated as a number here: the
#: count lives in the assertions and this file holds only their addresses.
SCENE_COUNT_PINS: dict[str, tuple[str, ...]] = {
    "test_scene_eligibility.py": (
        "test_three_of_eight_scenes_are_eligible",
        "test_exclusions_are_a_set_not_a_first_match",
    ),
    "test_city_crossing_scene.py": (
        "test_the_scene_is_deliberately_outside_the_eight_scene_matrix",
    ),
    "test_cte_peak_vacuity.py": ("test_widening_cost_matches_the_rms_columns",),
    "test_exposure_timing_band.py": ("test_obstacle_free_scenes_do_not_vote",),
    "test_path_curvature.py": ("test_six_of_eight_scenes_have_no_curvature",),
    "test_arrival_scope_census.py": ("test_every_shipped_scene_is_swept",),
    "test_epistemic_reach_screen.py": ("test_matrix_partitions_into_audible_and_deaf",),
    "test_lam_window_regeneration.py": (
        "test_the_regeneration_covers_the_whole_shipped_matrix",
    ),
}

#: Sites that read as scene pins to a grep for ``== 8`` and are **not** — the
#: arm-count collisions.  Recorded rather than merely omitted: an omission and a
#: deliberate exclusion look identical from outside, which is the defect
#: D-317/D-344/D-433/D-455 each paid for one level down.
SCENE_COUNT_DECOYS: dict[str, tuple[str, ...]] = {
    "test_threshold_vacuity.py": ("test_head_on_threshold_cannot_be_passed_by_any_arm",),
    "test_tail_stability.py": ("test_census_covers_both_binding_scenes",),
}


def _ints_compared_in(path: Path, func: str) -> set[int] | None:
    """Every integer constant inside an ``==`` comparison in ``func``.

    ``None`` means the file or the function was not found — reported as
    ``DRIFT`` rather than skipped, for :func:`pinned_avoidance_capable`'s
    reason: a reading earned by reading nothing is not a clean reading.

    Constants are collected from anywhere in the comparison, so a pin written
    as a product (``8 * 8 * 7`` — scenes x arms x seeds) is matched on its
    scene factor without this function having to know which factor that is.
    """
    if not path.exists():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != func:
            continue
        found: set[int] = set()
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Compare):
                continue
            if not any(isinstance(op, ast.Eq) for op in sub.ops):
                continue
            for operand in ast.walk(sub):
                if (isinstance(operand, ast.Constant)
                        and isinstance(operand.value, int)
                        and not isinstance(operand.value, bool)):
                    found.add(operand.value)
        return found
    return None


def scene_count_pins(tests: Path | None = None) -> Reading:
    """Did this cycle add or drop a scene without bumping the count pins?

    The companion to :func:`scene_population`, and the half of Q-197's blast
    radius that entry did not reach.  ``scene_population`` compares the
    avoidance-capable *set* against ``AVOIDANCE_CAPABLE``; a scene can enter
    ``eval/scenarios/`` and move **eight** integer assertions in seven other
    files without touching that set at all — a scene with no obstacles is not
    avoidance-capable, so entry 7 stays clean while the matrix width changes
    underneath it.

    Cost is the usual argument: eight AST parses, ~0.05 s, against a ~1681 s
    suite in which these eight failures would arrive as eight separate reds.
    """
    root = tests or TESTS
    paths = sorted(p for p in __import__("glob").glob("eval/scenarios/*.yaml")
                   if "lam_windows" not in p)
    derived = len(paths)
    missing: list[str] = []
    stale: list[str] = []
    for fname, funcs in sorted(SCENE_COUNT_PINS.items()):
        for func in funcs:
            ints = _ints_compared_in(root / fname, func)
            if ints is None:
                missing.append(f"{fname}::{func}")
            elif derived not in ints:
                stale.append(f"{fname}::{func}")
    if missing:
        return Reading("scene_count_pins", DRIFT,
                       f"{len(missing)} pin site(s) NOT FOUND: "
                       f"{', '.join(missing[:3])}"
                       + (" …" if len(missing) > 3 else "")
                       + " — the assertion moved or was renamed; re-point "
                         "SCENE_COUNT_PINS")
    if stale:
        return Reading("scene_count_pins", DRIFT,
                       f"{derived} shipped scenes, but {len(stale)} pin site(s) "
                       f"do not assert it: {', '.join(stale[:3])}"
                       + (" …" if len(stale) > 3 else "")
                       + f" — bump each to {derived} in this commit. Do NOT "
                         "touch the arm-count decoys "
                         f"({', '.join(sorted(SCENE_COUNT_DECOYS))}): both "
                         "populations are 8 and only the meaning separates them")
    return Reading("scene_count_pins", CLEAN,
                   f"{derived} shipped scenes, "
                   f"{sum(len(v) for v in SCENE_COUNT_PINS.values())} count pins "
                   f"agree ({len(SCENE_COUNT_PINS)} files, "
                   f"{sum(len(v) for v in SCENE_COUNT_DECOYS.values())} arm-count "
                   "decoys excluded)")


# --------------------------------------------------------------------------

#: The censuses re-derived by one pass, as ``(name, callable)``.  Typed, and the
#: typing is declared in the module docstring rather than defended: what keeps
#: it honest is :func:`uncovered` plus the per-entry tampers in the tests.
CENSUSES: tuple[tuple[str, Callable[[], Reading]], ...] = (
    ("guard_tally", guard_tally),
    ("loop_reach_reading", loop_reach_reading),
    ("citation_sites", citation_sites),
    ("exemption_registry", exemption_registry),
    ("consumer_reach_residue", consumer_reach_residue),
    ("lam_site_census", lam_site_census),
    ("scene_population", scene_population),
    ("scene_count_pins", scene_count_pins),
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
     "the *accountability* list of (module, attribute) pairs, still hand-typed "
     "and still un-re-derived; its old excuse — 'a deliberate act, no cycle "
     "has been surprised by it' — was falsified by D-330 and the entry it "
     "excused is now covered by the `exemption_registry` census above, which "
     "re-derives the allow-list population the accident actually joined"),
    ("extremum_reading.SITE_CLASSES",
     "re-derived by `extremum_reading.sweep` in both directions, so the "
     "reconciliation *is* the watcher and it runs in the suite (Q-090)"),
    ("key_discrimination narrow-key composition",
     "pinned as `(hits, live)` in `test_key_discrimination.py`, and a cycle "
     "joins it by writing a call site with a recorded return into "
     "`citation_audit.SCANNED_DOCS` — so a **doc-only** commit moves it (D-452) "
     "and the ~2 s budget cannot cover it: the derivation needs the full "
     "`consumer_reach` walk that `consumer_reach_residue` above already spends "
     "~0.9 s on for a different population. Listed rather than derived because "
     "this census went red four times (D-381 / D-395 / D-404 / D-452) while "
     "sitting in neither list, and its absence from both read as coverage"),
)


def uncovered() -> tuple[tuple[str, str], ...]:
    """The censuses this pass omits, with reasons.  See :data:`UNCOVERED`."""
    return UNCOVERED


def readings() -> tuple[Reading, ...]:
    """Re-derive every covered census.  ~2 s total."""
    return tuple(fn() for _, fn in CENSUSES)


def _scope_clause() -> str:
    """The ``Not covered:`` caveat — printed on **every** verdict.

    D-318 told readers to read this clause because D-317 paid 785 s for a check
    whose scope was narrower than it looked.  Until D-381 the clause was on the
    clean branch only, so the one reader who most needed it — a cycle staring at
    ``DRIFTED``, about to edit a census — was the one reader who never saw it.
    That is the D-380 shape one level out: healthy-state and finding-state
    rendering differently, with the *finding* the side that loses information.
    A caveat that a finding suppresses is a caveat that is absent exactly when
    it is load-bearing.
    """
    return f"Not covered: {', '.join(name for name, _ in UNCOVERED)}."


def report(rows: tuple[Reading, ...] | None = None) -> str:
    rows = readings() if rows is None else rows
    lines = [r.line() for r in rows]
    drift = [r for r in rows if r.is_drift]
    if drift:
        lines.append(
            f"census_preempt — {len(drift)} of {len(rows)} censuses DRIFTED. "
            "Repair in this commit; the suite would report the same red. "
            f"{_scope_clause()} A drifted census does not narrow this pass's "
            "scope, and does not widen it either — repairing what went red "
            "leaves the omitted four exactly as unread as a clean pass does.")
    else:
        lines.append(
            f"census_preempt — {len(rows)} censuses re-derived, all clean. "
            f"{_scope_clause()}")
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
