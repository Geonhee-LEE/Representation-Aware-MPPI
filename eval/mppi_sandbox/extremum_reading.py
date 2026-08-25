"""Sweep the sandbox for `min`/`max` over a set consumed as an interval (STATE #1).

The bottleneck sentence this answers, verbatim: *"The `K` axis keeps producing
the same class of defect: a `min`/`max` taken over a growing set and then used
in an interval test (D-307, D-308, and now D-311's span). Three instances are
three too many to keep finding one per cycle — the axis needs to be swept for
the rest of them."*

What the sweep actually found
-----------------------------

The sweep is not the grep the TODO asked for, because the grep does not
discriminate: ``min``/``max`` over a single iterable occurs **176** times in
:mod:`eval.mppi_sandbox`, and hand-ruling on 176 sites is not a cycle's work
and would be wrong by the third one. The discriminator is what the extremum is
*consumed by* — an extremum that is printed, stored, or returned cannot lie
about an interval because no interval is being asserted. Filtered to sites whose
value reaches a comparison operator, the population is **36**, which collapses
to **34** distinct ``(module, function, expression)`` readings — ``margin_free``
tests its two sets against each other in both directions, so two of its four
expressions each occur twice.

And on those 34 the class does not hold together. It splits three ways, and
only one of the three is a defect:

:data:`EXTREME_IS_THE_QUESTION` (17 sites)
    The extreme *is* the quantity being asked about. Degeneracy guards
    (``min(vals) > 0``), all-equal tests (``max(spends) - min(spends) < 1e-12``),
    single-endpoint membership (``lam >= max(window)``), and — the instructive
    one — :func:`margin_free.censoring_alignment`'s ``min(censored) >
    max(scoreable)``, which proves two sets are disjointly ordered. That proof
    is *sound under holes*: a gap inside either set cannot make a separated pair
    overlap. Sites here are correct and stay correct.

:data:`HULL_OVER_A_SET` (2 sites)
    Two extremes stand in for an interval. Lies exactly when the index admits
    **holes** — and whether it can is a property of what indexes the set, not of
    the expression. Both sites are :func:`calibrated_ladder.k_axis_bracket`'s
    ``min(unan)``/``max(unan)``, i.e. D-307's finding, already repaired by
    D-308's contiguity predicate. **The sweep found no unrepaired instance.**

:data:`MONOTONE_UNDER_EXTENSION` (15 sites)
    A sample statistic in a threshold test. Not wrong — one-directional. ``span
    = max/min`` over a seed ensemble is monotone non-decreasing under adding
    seeds, so a span that fails a band can never be rescued by measuring more
    (D-311, which cost an ensemble to learn); ``min(gaps) <= width`` is monotone
    the other way, so once true it can never go false. The defect is not in the
    code, it is in **spending a measurement on the direction that cannot move**.

Why the class looked bigger than it is
--------------------------------------

D-307, D-308 and D-311 were read as three instances of one defect. They are
two instances of two different things: D-307/D-308 are the hull shape at one
site, and D-311 is the monotonicity shape, which is not a bug at all. The
`K` axis was not producing a defect class at a rate of one per cycle; it was
producing one repaired bug and one reading discipline.

The discipline already existed, in one module
---------------------------------------------

:mod:`relief_interval`'s header states the hull hazard outright — *"The tempting
formulation is per-scene intervals ``[threshold, ceiling]`` and an interval
intersection. That is unsound here … **admissibility is not known to be
contiguous in the weight**"* — and it ships set intersection instead, with
``threshold``/``ceiling`` surviving as reports from which no verdict is
computed. That was written for the ``w_obs_soft`` axis well before D-307 hit the
same wall on `K`. So the knowledge was in the repo the whole time and stayed
local to the module that earned it, which is why the `K` axis paid for it again.
That is the finding worth carrying, and it is the reason this module is a
*registry* rather than a fix: there is nothing to fix.

Granularity, stated because it bounds the reading
-------------------------------------------------

Sites are keyed by ``(module, function, expression)``. A function that uses the
same expression in two roles — :func:`calibrated_ladder.census_ladder` computes
``min(vals)`` both as a degeneracy guard and as a span denominator — collapses
to one entry, and the entry carries the **more hazardous** of the two readings.
So the counts above are an upper bound on hazard, not an exact census, and
``MONOTONE_UNDER_EXTENSION`` is the class that absorbs the ambiguity.
"""

from __future__ import annotations

import ast
import pathlib
from typing import NamedTuple

#: The extreme itself is the question. Sound under holes and under extension.
EXTREME_IS_THE_QUESTION = "EXTREME_IS_THE_QUESTION"
#: Two extremes stand in for an interval. Lies iff the index admits holes.
HULL_OVER_A_SET = "HULL_OVER_A_SET"
#: A sample statistic in a threshold test. Sound, but the verdict can only
#: ever move one way under a larger sample.
MONOTONE_UNDER_EXTENSION = "MONOTONE_UNDER_EXTENSION"

#: Verdicts, worst first — used to order the summary and to pick a headline.
CLASSES = (HULL_OVER_A_SET, MONOTONE_UNDER_EXTENSION, EXTREME_IS_THE_QUESTION)

SWEEP_CLEAN = "EXTREMUM_SWEEP_CLEAN"
SWEEP_UNREPAIRED_HULL = "EXTREMUM_SWEEP_UNREPAIRED_HULL"
SWEEP_UNREGISTERED = "EXTREMUM_SWEEP_UNREGISTERED_SITES"

#: Functions whose hull reading has been repaired, and by what. A hull site is
#: a finding until it appears here; this is the only place a hull site is
#: allowed to be quiet.
HULL_REPAIRED_BY = {
    ("calibrated_ladder.py", "k_axis_bracket"): "D-308 contiguity predicate "
                                                "(`len(blocks) <= 1`)",
}

#: The 36 distinct comparison-consuming readings, keyed by
#: `(module, function, expression)`. Regenerate the *population* with
#: :func:`scan_sites`; the classification is the hand judgement this module
#: exists to record, and :func:`sweep` fails when the two disagree.
SITE_CLASSES: dict[tuple[str, str, str], str] = {
    # --- the extreme is the question -------------------------------------
    ("ab.py", "lam_gap", "min(lams)"): EXTREME_IS_THE_QUESTION,
    ("arm_freeze.py", "allocation_is_controlled", "max(spends)"): EXTREME_IS_THE_QUESTION,
    ("arm_freeze.py", "allocation_is_controlled", "min(spends)"): EXTREME_IS_THE_QUESTION,
    ("calibrated_ladder.py", "band_miss_repair", "max(window)"): EXTREME_IS_THE_QUESTION,
    ("calibrated_ladder.py", "census_ladder", "min(walked)"): EXTREME_IS_THE_QUESTION,
    # D-321 retired `("calibrated_ladder.py", "k_axis_bracket", "max(ks)")`.
    # It was `interior_inadmissible_k`'s `k != max(ks)` filter, classified here
    # as EXTREME_IS_THE_QUESTION because the top walked column is genuinely the
    # thing being asked about. The classification was right and the *site* was
    # the defect: "not the top column" is not what "interior to the run" means,
    # so the whole expression was deleted rather than reclassified. Recorded
    # here rather than silently dropped — `sweep()["retired"]` named it, which
    # is the reconciliation working in the direction D-313 said it does.
    ("horizon_audit.py", "_row", "max(steps)"): EXTREME_IS_THE_QUESTION,
    # Separation via extremes is sound under holes — the counterexample that
    # keeps the class from being "every min/max over a set".
    ("margin_free.py", "censoring_alignment", "min(censored)"): EXTREME_IS_THE_QUESTION,
    ("margin_free.py", "censoring_alignment", "max(scoreable)"): EXTREME_IS_THE_QUESTION,
    ("margin_free.py", "censoring_alignment", "min(scoreable)"): EXTREME_IS_THE_QUESTION,
    ("margin_free.py", "censoring_alignment", "max(censored)"): EXTREME_IS_THE_QUESTION,
    # D-334.  `is_constant` asks whether an observable's eight seed values are
    # all the same, and spells it `max(...) == min(...)`.  That is the class's
    # definition rather than a borderline case: the equality is exactly
    # equivalent to "the set is a single value" and stays so under holes and
    # under extension, because both extremes are recomputed from whatever the
    # set contains.  It is *not* HULL_OVER_A_SET — no interval is being stood
    # in for; the two extremes are the question, and the question is whether
    # they coincide.  The distinction matters here because the verdict this
    # site carries (an observable is a scenario constant, so separating on it
    # is an oracle read) is the whole of D-334.
    # D-335 re-spelled both sites `tbl[...]` when `is_constant` grew a `table`
    # argument so the causal readings could reuse it. The classification is
    # untouched -- what the site *asks* did not change, only which table it
    # asks it of -- but the registry key is the expression text, so the rename
    # had to be paid here or the sweep would have read two unregistered sites.
    ("scene_separability.py", "is_constant", "max(tbl[s][observable])"): EXTREME_IS_THE_QUESTION,
    ("scene_separability.py", "is_constant", "min(tbl[s][observable])"): EXTREME_IS_THE_QUESTION,
    # D-349.  `ttc_family_has_the_heavier_tail` spells "every TTC-family tail
    # exceeds every other tail" as `min(ttc) > max(rest)`.  The two extremes
    # are the binding constraints of a universally-quantified claim, which is
    # the same shape `margin_free.censoring_alignment` carries above and is
    # sound under holes: dropping any interior member of either list cannot
    # make a false claim true, because the witness that would refute it is an
    # extreme by construction.  Not HULL_OVER_A_SET -- neither list is being
    # stood in for by its interval; only its worst case is consulted, and the
    # worst case is what the sentence is about.  The docstring at the site
    # makes the same argument in the other direction (a mean-vs-mean version
    # "would have passed on one outlier"), so the strictness is deliberate.
    ("scene_separability.py", "ttc_family_has_the_heavier_tail", "min(ttc)"): EXTREME_IS_THE_QUESTION,
    ("scene_separability.py", "ttc_family_has_the_heavier_tail", "max(rest)"): EXTREME_IS_THE_QUESTION,
    ("predicate_inputs.py", "calls_stationary", "max(self.calls)"): EXTREME_IS_THE_QUESTION,
    ("predicate_inputs.py", "calls_stationary", "min(self.calls)"): EXTREME_IS_THE_QUESTION,
    # `open_above` / `open_below` ask a single-endpoint question ("is anything
    # tested beyond this end"), so a hole inside `chosen` does not reach them.
    ("relief_interval.py", "open_above", "max(chosen)"): EXTREME_IS_THE_QUESTION,
    ("relief_interval.py", "open_above", "max(tested)"): EXTREME_IS_THE_QUESTION,
    ("relief_interval.py", "open_below", "min(chosen)"): EXTREME_IS_THE_QUESTION,
    ("relief_interval.py", "open_below", "min(tested)"): EXTREME_IS_THE_QUESTION,
    # --- hull over a set (D-307; repaired by D-308) ------------------------
    ("calibrated_ladder.py", "k_axis_bracket", "min(unan)"): HULL_OVER_A_SET,
    ("calibrated_ladder.py", "k_axis_bracket", "max(unan)"): HULL_OVER_A_SET,
    # --- monotone under extension (D-311's shape) --------------------------
    ("arm_audibility.py", "window_verdict", "max((r for _, r, _ in curve))"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "ess_span", "min(ess)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "_column_reading", "min(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "census_ladder", "max(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "census_ladder", "min(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "ensemble_scaling_in_k", "max(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "ensemble_scaling_in_k", "min(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "ensemble_scaling_in_k", "min(fracs)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "gap_trend", "min(gaps.values())"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "unanimity_bracket", "min(vals)"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "uniform_resolution_trend",
     "min(refined.values())"): MONOTONE_UNDER_EXTENSION,
    ("calibrated_ladder.py", "uniform_resolution_trend",
     "min((g for g in coarse_gaps.values() if g))"): MONOTONE_UNDER_EXTENSION,
    ("reading_record.py", "gap_spread", "min(gaps)"): MONOTONE_UNDER_EXTENSION,
    ("reading_record.py", "ratio_spread", "min(per)"): MONOTONE_UNDER_EXTENSION,
    ("temperature_confound.py", "classify", "max(shares)"): MONOTONE_UNDER_EXTENSION,
}

#: Calls that wrap an extremum without changing whether it reaches a comparison.
_TRANSPARENT_CALLS = frozenset({"abs", "float", "bool", "round"})


class Site(NamedTuple):
    """One `min`/`max` over a single iterable, and where it lands."""

    module: str
    function: str
    expression: str
    lineno: int
    consumed_in_comparison: bool

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.module, self.function, self.expression)


def _sandbox_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent


def _reaches_comparison(chain: list[ast.AST]) -> bool:
    """Does this extremum's value flow into a comparison operator?

    Walks the ancestor chain outward, passing through the operations that carry
    a value unchanged (arithmetic, `if`/`else`, boolean joins, and the handful
    of transparent builtins) and stopping at anything that consumes it some
    other way — a `return`, a dict entry, a keyword argument. Reaching an
    :class:`ast.Compare` is what makes an extremum capable of asserting an
    interval; not reaching one is what makes the other 142 sites irrelevant.
    """
    for node in reversed(chain[:-1]):
        if isinstance(node, ast.Compare):
            return True
        if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.IfExp, ast.BoolOp)):
            continue
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _TRANSPARENT_CALLS):
            continue
        return False
    return False


def scan_sites(root: pathlib.Path | None = None) -> tuple[Site, ...]:
    """Enumerate every `min`/`max` over a single iterable in the sandbox.

    Derived from the source rather than typed, per D-047: a registry that
    restates its own population is short at whichever element nobody
    remembered. The multi-argument forms (``max(a, b)``) are excluded because
    they are a clamp on two known values, not a reading over a set.
    """
    base = _sandbox_root() if root is None else root
    sites: list[Site] = []
    for path in sorted(base.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ("min", "max")
                    and len(node.args) == 1):
                continue
            chain: list[ast.AST] = [node]
            cursor: ast.AST = node
            while cursor in parents:
                cursor = parents[cursor]
                chain.append(cursor)
            chain.reverse()
            function = next(
                (n.name for n in reversed(chain)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
                "<module>")
            sites.append(Site(path.name, function, ast.unparse(node),
                              node.lineno, _reaches_comparison(chain)))
    return tuple(sites)


def comparison_sites(root: pathlib.Path | None = None) -> tuple[Site, ...]:
    """The subset that can assert an interval — 36 of 176 at D-312."""
    return tuple(s for s in scan_sites(root) if s.consumed_in_comparison)


def unrepaired_hulls() -> tuple[tuple[str, str, str], ...]:
    """Hull sites with no repair on record. Empty is the whole claim."""
    return tuple(sorted(
        key for key, cls in SITE_CLASSES.items()
        if cls == HULL_OVER_A_SET and (key[0], key[1]) not in HULL_REPAIRED_BY))


def sweep(root: pathlib.Path | None = None) -> dict:
    """Classify the axis, and refuse to stay quiet when the source moves.

    Two ways this goes red, and they fail for opposite reasons. **Unregistered
    sites** mean the source grew an extremum that reaches a comparison and
    nobody ruled on it — the sweep's coverage claim is stale, which is the
    failure mode that made this a per-cycle discovery in the first place.
    **Unrepaired hulls** mean a site that reads a set as an interval has no
    repair on record; that is a finding about the code, not about the registry.

    Registered-but-absent keys are reported (``retired``) and do **not** go red:
    deleting a site is a repair, and a check that punishes the fix is one that
    gets muted (D-044).
    """
    found = comparison_sites(root)
    found_keys = {s.key for s in found}
    unregistered = tuple(sorted(found_keys - set(SITE_CLASSES)))
    retired = tuple(sorted(set(SITE_CLASSES) - found_keys))
    hulls = unrepaired_hulls()

    if unregistered:
        verdict = SWEEP_UNREGISTERED
    elif hulls:
        verdict = SWEEP_UNREPAIRED_HULL
    else:
        verdict = SWEEP_CLEAN

    return {
        "verdict": verdict,
        "total_extremum_sites": len(scan_sites(root)),
        "comparison_sites": len(found),
        "by_class": {cls: sum(1 for k in found_keys
                              if SITE_CLASSES.get(k) == cls)
                     for cls in CLASSES},
        "unregistered": unregistered,
        "retired": retired,
        "unrepaired_hulls": hulls,
        "hull_repairs": tuple(sorted(HULL_REPAIRED_BY)),
    }


def main(argv: list[str] | None = None) -> int:
    reading = sweep()
    print(f"extremum_reading — {reading['verdict']}: "
          f"{reading['comparison_sites']} of {reading['total_extremum_sites']} "
          f"extremum sites reach a comparison.")
    for cls in CLASSES:
        print(f"  {cls:26s} {reading['by_class'][cls]}")
    for key in reading["unregistered"]:
        print(f"  UNREGISTERED: {key[0]}::{key[1]} — {key[2]}")
    for key in reading["unrepaired_hulls"]:
        print(f"  UNREPAIRED HULL: {key[0]}::{key[1]} — {key[2]}")
    for key in reading["retired"]:
        print(f"  retired (not a finding): {key[0]}::{key[1]} — {key[2]}")
    return 0 if reading["verdict"] == SWEEP_CLEAN else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
