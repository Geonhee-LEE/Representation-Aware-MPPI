# SPDX-License-Identifier: BSD-3-Clause
"""Which of D-041's 52 shipped-``lam`` sites make a claim a temperature can move.

D-041 counted **52** call sites that build a controller with no ``params``,
step it, and therefore weight at ``MPPIParams().lam`` — the rung D-040 found
admissible in **0 of 24** calibrated cells.  Q-061 then asked the obvious
follow-up: is 52 the number of *claims to re-measure*?  It is not, and Q-061
says why — several of those sites assert an **identity between two runs**
(``test_same_seed_identical_trajectory``,
``test_all_knobs_zero_reproduces_stock_byte_for_byte``), and a temperature that
enters both sides of an identity cancels.  Q-061's lean is (c), *answer it by
instrumentation*: re-run each site at two admissible rungs and see which
assertions survive.  At two rungs that is 104 simulations, and it is #15's
work.

This module is the half that runs today, for free, on the syntax tree.  It does
**not** decide which sites are temperature-dependent.  It brackets the bill:

``ANCHORED``
    an assertion compares a run-derived quantity against a **pure numeric
    literal** — ``assert dist_goal <= 0.3``, ``assert clearance > 0.0``.  The
    literal is a physical anchor measured at a rung nothing admits, which is
    exactly the defect D-040 found in ``exposure_band_hi``.  These need the
    re-run.
``COMPARATIVE``
    both operands of an ordering are run-derived — ``assert heavy.mean_speed <
    0.8 * shipped.mean_speed``.  Temperature does not cancel here: D-039 is the
    proof, where the self-vs-baseline verdict *flipped* between ``lam = 1.6``
    and the shipped ``0.1``.  These need the re-run too.
``IDENTITY``
    an equality between two run-derived quantities, tolerances excluded —
    ``assert_array_equal(simulate(s, stock), simulate(s, risk0))``.  This is
    the class Q-061 conjectures is temperature-symmetric.
``STRUCTURAL``
    a literal compared against ``len()`` / ``.shape`` / ``.size`` — a claim
    about array geometry, not about physics.
``OPAQUE``
    anything else: ``assert result["collision"] is False``, ``assert x``,
    ``pytest.raises``.  Statically unjudged.
``SILENT``
    the site reaches **no** assertion at all.

The bracket, and the reason it is a bracket in both directions:

    lower bound = ANCHORED + COMPARATIVE     definitely temperature-relevant
    upper bound = D-041's 52                 nothing is cleared statically

``IDENTITY`` is **not** subtracted.  It would be the whole point of the
exercise to subtract it, and that is precisely why it must not be: "these two
runs agree at ``lam = 0.1``" is evidence that they agree *at that rung*, not a
proof that the agreement is a contract.  Discharging it is what Q-061 (c)'s
instrumentation is *for*, and a static pass that pre-empted the instrument
would be asserting the conclusion.  ``OPAQUE`` is likewise unsubtracted, for
the plainer reason that ``result["collision"] is False`` is a physical claim
this module simply cannot read.  So the middle band is *unresolved*, not
*cleared* — the distinction D-036 drew between rescoping and retracting.

**Both approximations point the same way, deliberately.**  D-041's post-mortem
was that a false ``True`` over-counts while a false ``False`` deletes evidence,
so every rule here is biased to over-count:

1. **Assertion reachability is over-approximated.**  Sixteen of the 52 sites
   sit in helpers (``_response``, ``_closed_loop``, ``_ratio``, ``_deltas``),
   whose runs feed assertions in *callers*.  A site's assertion set is
   therefore its own function's asserts plus those of every function that
   transitively calls it — an over-approximation, since a caller may assert
   about something else entirely.  Ignoring callers instead would have scored
   every helper ``SILENT``, which is D-041's ``simulates`` bug reappearing at
   one level of remove.
2. **A site takes the strongest class it can reach**, in the order
   ANCHORED > COMPARATIVE > STRUCTURAL > OPAQUE > IDENTITY > SILENT.  A site
   that reaches one anchored assertion and nine identities is ``ANCHORED``.

**Tolerances are not anchors, and the distinction is what makes the number
non-trivial.**  ``assert_array_equal(a, b)`` carries no literal;
``np.allclose(a, b, atol=1e-9)`` and ``pytest.approx(x, rel=0.20)`` do, and
scoring those literals as anchors would have read nearly every identity as
``ANCHORED`` — available, stable, and 100 % by construction, which is the
failure D-041 named in Q-060's counting plan.  So ``atol`` / ``rtol`` / ``abs``
/ ``rel`` are excluded by name, and a test pins that exclusion rather than
leaving it as a comment.

**A literal is an anchor only if it is a pure literal.**  ``0.8 *
shipped.mean_speed`` contains a ``Name``, so it is run-derived and its
comparison is ``COMPARATIVE``, not ``ANCHORED`` — a relative bound moves with
whatever it is relative to.  Getting this wrong inflates the *lower* bound,
which unlike the other errors here would be a false claim rather than a
conservative one: a lower bound has to be sound.

Nothing simulates.  Every number is a read of the repo's own syntax tree, the
same property that lets :mod:`default_lam_sites`, :mod:`claim_scope` and
:mod:`operating_point` police claims that are not.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from .default_lam_sites import (
    DEFAULTS,
    REPO_ROOT,
    Site,
    _import_maps,
    _sources,
    _target,
    sites as _all_sites,
)

#: Kwarg names that carry a *tolerance*, not an anchor.  A tolerance bounds the
#: disagreement between two run-derived quantities; the temperature enters both
#: and cancels, so the literal says nothing about the operating point.
TOLERANCE_KWARGS: frozenset[str] = frozenset({"atol", "rtol", "abs", "rel"})

#: Calls that assert an equality without an ``==``.  ``assert_array_equal`` and
#: friends are the spelling this repo actually uses for its identity claims.
_EQUALITY_CALLS: frozenset[str] = frozenset({
    "assert_array_equal", "assert_allclose", "assert_array_almost_equal",
    "allclose", "array_equal", "array_equiv",
})

#: Attribute/call names whose value is array geometry rather than physics.
_STRUCTURAL_SUBJECTS: frozenset[str] = frozenset({"len", "shape", "size", "ndim"})

#: ``pytest.approx(x, rel=...)`` is a wrapper, not an operand.  Left wrapped, the
#: ``Call`` node makes its argument look run-derived and a banked constant reads
#: as an identity -- see :func:`_operands`.
_WRAPPER_CALLS: frozenset[str] = frozenset({"approx"})

ANCHORED = "ANCHORED"
COMPARATIVE = "COMPARATIVE"
STRUCTURAL = "STRUCTURAL"
OPAQUE = "OPAQUE"
IDENTITY = "IDENTITY"
SILENT = "SILENT"

#: Strongest first.  A site inherits the strongest class it can reach, so this
#: order is the whole bias policy in one line: anything that might depend on the
#: temperature outranks the one class that might not.
PRECEDENCE: tuple[str, ...] = (
    ANCHORED, COMPARATIVE, STRUCTURAL, OPAQUE, IDENTITY, SILENT)

#: The two classes that are *known* to move with the temperature.  The lower
#: bound on Q-061's re-run bill is exactly their union.
TEMPERATURE_RELEVANT: frozenset[str] = frozenset({ANCHORED, COMPARATIVE})


def _local_banked(tree: ast.AST) -> frozenset[str]:
    """Module-level names bound to a literal -- ``ROBOT_RADIUS = 0.3``.

    A banked constant compared against a measurement is an **anchor**, not a
    run-derived quantity, and missing that is fail-open: it reads
    ``assert measured == pytest.approx(TARGET_SPEED_INERTNESS[target])`` -- a
    table of numbers recorded at some past operating point, which is D-040's
    ``exposure_band_hi`` defect exactly -- as a temperature-symmetric identity.
    """
    out = set()
    for node in getattr(tree, "body", ()):
        targets = ([node.target] if isinstance(node, ast.AnnAssign)
                   else node.targets if isinstance(node, ast.Assign) else [])
        value = getattr(node, "value", None)
        if value is None:
            continue
        if any(isinstance(s, (ast.Name, ast.Attribute, ast.Call))
               for s in ast.walk(value)):
            continue
        for t in targets:
            if isinstance(t, ast.Name):
                out.add(t.id)
    return frozenset(out)


def banked_names(sources: dict) -> dict[str, frozenset[str]]:
    """Per module, every spelling that reads a banked literal.

    Local names (``ROBOT_RADIUS``) *and* the dotted ones — ``exp.CRUISE_SPEED_MPS``
    — because a constant does not stop being a constant when it is imported.
    That was the third fail-open in this module's own history: reading only
    local names classified
    ``assert got.cruise_speed == pytest.approx(exp.CRUISE_SPEED_MPS, rel=0.05)``
    as an ``IDENTITY`` between two run-derived values, when it is a measurement
    checked against a number banked at some past operating point — D-040's
    defect verbatim.  All three misses shrank the lower bound, never inflated
    it; a bound that is only ever wrong in one direction is a bound with a bug,
    not a conservative bound.
    """
    local = {modname: _local_banked(tree)
             for _p, (_s, tree, modname) in sources.items()}
    out: dict[str, frozenset[str]] = {}
    for _p, (_s, tree, modname) in sources.items():
        names, alias = _import_maps(tree, modname)
        seen = set(local.get(modname, frozenset()))
        for bare, (module, attr) in names.items():        # from X import CONST
            if attr in local.get(module, frozenset()):
                seen.add(bare)
        for local_alias, module in alias.items():         # from X import Y as y
            for const in local.get(module, frozenset()):
                seen.add(f"{local_alias}.{const}")
        out[modname] = frozenset(seen)
    return out


def _is_pure_literal(node: ast.AST, banked: frozenset[str] = frozenset()) -> bool:
    """True iff ``node`` evaluates to a number with no run-derived input.

    ``0.3``, ``2 * 0.15`` and ``TARGET_SPEED_INERTNESS[target]`` (a banked
    table) are pure; ``0.8 * shipped.mean_speed`` is not.  A ``Subscript``
    checks only its **container**: the index may be a loop or parametrize
    variable, but every value in a literal table is still a literal.
    """
    return _pure(node, banked) and _numeric(node, banked)


def _dotted(node: ast.AST) -> str | None:
    """``exp.CRUISE_SPEED_MPS`` -> that string; anything deeper -> ``None``."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return None


def _pure(node: ast.AST, banked: frozenset[str]) -> bool:
    if isinstance(node, ast.Subscript):
        return _pure(node.value, banked)          # the index need not be literal
    if isinstance(node, ast.Name):
        return node.id in banked
    if isinstance(node, ast.Attribute):
        return _dotted(node) in banked
    if isinstance(node, ast.Call):
        return False
    return all(_pure(c, banked) for c in ast.iter_child_nodes(node))


def _numeric(node: ast.AST, banked: frozenset[str]) -> bool:
    """``node`` mentions at least one number -- excludes ``assert a == ""``."""
    if isinstance(node, ast.Subscript):
        return _numeric(node.value, banked)
    if isinstance(node, ast.Name):
        return node.id in banked
    if isinstance(node, ast.Attribute):
        return _dotted(node) in banked
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    return any(_numeric(c, banked) for c in ast.iter_child_nodes(node))


def _is_structural(node: ast.AST) -> bool:
    """True iff ``node`` reads array geometry -- ``len(x)``, ``a.shape[0]``."""
    for sub in ast.walk(node):
        name = (sub.func.id if isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Name) else None)
        if name in _STRUCTURAL_SUBJECTS:
            return True
        if isinstance(sub, ast.Attribute) and sub.attr in _STRUCTURAL_SUBJECTS:
            return True
    return False


def _equality_call(node: ast.AST) -> ast.Call | None:
    """The innermost ``assert_array_equal``-style call inside ``node``, if any."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            name = (sub.func.attr if isinstance(sub.func, ast.Attribute)
                    else sub.func.id if isinstance(sub.func, ast.Name) else None)
            if name in _EQUALITY_CALLS:
                return sub
    return None


def _unwrap(node: ast.AST) -> list[ast.AST]:
    """``pytest.approx(x, rel=0.2)`` -> ``[x]``; anything else -> itself."""
    if isinstance(node, ast.Call):
        name = (node.func.attr if isinstance(node.func, ast.Attribute)
                else node.func.id if isinstance(node.func, ast.Name) else None)
        if name in _WRAPPER_CALLS:
            return [*node.args, *(k.value for k in node.keywords
                                  if k.arg and k.arg not in TOLERANCE_KWARGS)]
    return [node]


def _operands(test: ast.AST) -> list[ast.AST]:
    """The comparison operands to judge, tolerance kwargs and wrappers stripped."""
    call = _equality_call(test)
    if call is not None:
        raw = [*call.args, *(k.value for k in call.keywords
                             if k.arg and k.arg not in TOLERANCE_KWARGS)]
    elif isinstance(test, ast.Compare):
        raw = [test.left, *test.comparators]
    else:
        return []
    return [u for o in raw for u in _unwrap(o)]


def classify_assertion(test: ast.AST,
                       banked: frozenset[str] = frozenset()) -> str:
    """One assertion's class, on its syntax alone.

    Order is the bias: an anchor beats an ordering beats geometry, and
    ``IDENTITY`` is reached only when every operand is run-derived *and* the
    relation is an equality.
    """
    # Handed a whole ``ast.Assert`` instead of its ``.test``, every rule below
    # finds no operands and returns OPAQUE -- a silent downgrade, so unwrap
    # rather than trust the caller.  (It caught this module's own tests first.)
    if isinstance(test, ast.Assert):
        test = test.test
    ops = _operands(test)
    literals = [o for o in ops if _is_pure_literal(o, banked)]
    others = [o for o in ops if not _is_pure_literal(o, banked)]
    if literals and others:
        if any(_is_structural(o) for o in others):
            return STRUCTURAL
        return ANCHORED
    if not others or literals:
        return OPAQUE                      # all-literal, or nothing to compare
    if _equality_call(test) is not None:
        return IDENTITY
    if isinstance(test, ast.Compare):
        if all(isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for op in test.ops):
            return COMPARATIVE
        if all(isinstance(op, ast.Eq) for op in test.ops):
            return IDENTITY
    return OPAQUE


def _asserts(fn: ast.AST) -> list[ast.AST]:
    """Every assertion inside ``fn`` -- both spellings.

    ``ast.Assert`` alone is **not** enough, and the misses are exactly the
    sites Q-061 quotes: ``test_same_seed_identical_trajectory`` and
    ``test_all_knobs_zero_reproduces_stock_byte_for_byte`` state their identity
    as ``np.testing.assert_array_equal(a, b)`` -- a bare ``Expr``, no ``assert``
    keyword in the function at all.  Reading only ``ast.Assert`` scored eight
    sites ``SILENT``, i.e. *makes no claim*, when what they make is the one
    kind of claim this module exists to find.  Fail-open, and in D-041's
    dangerous direction: a false ``SILENT`` deletes evidence.
    """
    out = [n.test for n in ast.walk(fn) if isinstance(n, ast.Assert)]
    for n in ast.walk(fn):
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call):
            func = n.value.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name) else None)
            if name and (name in _EQUALITY_CALLS or name.startswith("assert")):
                out.append(n.value)
    return out


def _call_graph(sources: dict) -> dict[tuple[str, str], set[tuple[str, str]]]:
    """``caller -> callees``, both qualified ``(module, name)``."""
    graph: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for _, (_src, tree, modname) in sources.items():
        names, alias = _import_maps(tree, modname)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            callees = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    target = _target(node, names, alias)
                    if target is not None:
                        callees.add(target)
            graph[(modname, fn.name)] = callees
    return graph


def _callers_of(graph: dict, node: tuple[str, str]) -> set[tuple[str, str]]:
    """Transitive callers of ``node`` -- the over-approximation of reachability."""
    reverse: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for caller, callees in graph.items():
        for callee in callees:
            reverse[callee].add(caller)
    seen, stack = set(), [node]
    while stack:
        cur = stack.pop()
        for caller in reverse.get(cur, ()):
            if caller not in seen:
                seen.add(caller)
                stack.append(caller)
    return seen


@dataclass(frozen=True)
class Judged:
    """One shipped-``lam`` site plus the strongest assertion it can reach."""

    site: Site
    kind: str                       # one of PRECEDENCE
    reached: tuple[str, ...]        # every assertion class reachable, sorted
    n_assertions: int

    @property
    def needs_rerun(self) -> bool:
        """Known to be temperature-relevant -- counts toward the lower bound."""
        return self.kind in TEMPERATURE_RELEVANT


def judge(root: Path | None = None) -> tuple[Judged, ...]:
    """Classify every D-041 weighting site by what its assertions assert."""
    sources = _sources(root)
    graph = _call_graph(sources)

    # Assertion classes are resolved per *defining* module, because ``banked``
    # is a module-level fact: the same literal table is an anchor where it is
    # defined and invisible from anywhere else.
    by_qualified: dict[tuple[str, str], list[str]] = {}
    banked_by_module = banked_names(sources)
    for _, (_src, tree, modname) in sources.items():
        banked = banked_by_module[modname]
        for fn in ast.walk(tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                by_qualified[(modname, fn.name)] = [
                    classify_assertion(t, banked) for t in _asserts(fn)]

    path_to_mod = {str(p.relative_to(root or REPO_ROOT)): m
                   for p, (_s, _t, m) in sources.items()}

    out: list[Judged] = []
    for site in _all_sites(root):
        if site.kind != DEFAULTS or not site.simulates:
            continue
        modname = path_to_mod[site.path]
        owner = (modname, site.function)
        scope = {owner} | _callers_of(graph, owner)
        tests = [c for fn in scope for c in by_qualified.get(fn, ())]
        classes = sorted(set(tests))
        kind = next((k for k in PRECEDENCE if k in classes), SILENT)
        out.append(Judged(site=site, kind=kind, reached=tuple(classes),
                          n_assertions=len(tests)))
    return tuple(out)


@dataclass(frozen=True)
class Bracket:
    """The bill Q-061 (c) would pay, bracketed rather than decided."""

    counts: dict          # class -> number of sites
    total: int

    @property
    def lower(self) -> int:
        """Sites whose claim is *known* to move with the temperature."""
        return sum(self.counts.get(k, 0) for k in TEMPERATURE_RELEVANT)

    @property
    def upper(self) -> int:
        """D-041's census.  Nothing is cleared by a static pass."""
        return self.total

    @property
    def unresolved(self) -> int:
        """The band the instrument has to decide: identity, opaque, structural."""
        return self.total - self.lower

    @property
    def simulations_at_two_rungs(self) -> tuple[int, int]:
        """Q-061 (c) costs two admissible rungs per site, not one."""
        return self.lower * 2, self.upper * 2


def bracket(root: Path | None = None) -> Bracket:
    judged = judge(root)
    counts = {k: sum(1 for j in judged if j.kind == k) for k in PRECEDENCE}
    return Bracket(counts={k: v for k, v in counts.items() if v},
                   total=len(judged))


def report(root: Path | None = None) -> str:
    from .operating_point import SHIPPED_LAM

    b = bracket(root)
    lo_sims, hi_sims = b.simulations_at_two_rungs
    rows = [
        f"D-041 sites weighting at MPPIParams().lam = {SHIPPED_LAM:g} : {b.total}",
        "",
    ]
    for kind in PRECEDENCE:
        if kind in b.counts:
            mark = "*" if kind in TEMPERATURE_RELEVANT else " "
            rows.append(f" {mark} {kind:<12} {b.counts[kind]:>3d}")
    rows += [
        "",
        f"lower bound (* known temperature-relevant) : {b.lower}",
        f"unresolved by a static pass                : {b.unresolved}",
        f"upper bound (D-041, nothing cleared)       : {b.upper}",
        "",
        f"Q-061 (c) at two admissible rungs: {lo_sims} to {hi_sims} simulations",
        "",
        f"{'class':<13} {'site':<52} {'reaches'}",
    ]
    for j in sorted(judge(root), key=lambda j: (PRECEDENCE.index(j.kind),
                                                j.site.path, j.site.line)):
        loc = f"{j.site.path}:{j.site.line}"
        rows.append(f"{j.kind:<13} {loc:<52} {','.join(j.reached) or '-'}")
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
