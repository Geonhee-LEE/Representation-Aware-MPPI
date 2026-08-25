"""Screen every ``TYPED`` exemption for masking — STATE #1, generalising D-050.

D-050 found one mask.  ``tree_provenance.undeclared_drift`` reads a
worktree-vs-``HEAD`` difference and exempts ``DECLARED_LOCAL_ONLY``, so at the
exact moment its rule is broken — ``git add STATE.md`` — the offending path is
removed from the population *before* the act can appear in it.  The guard reads
clean.  The collapse is real and unobservable.

The way D-050 proved it was **suppression**: call the guard again with
``declared={}`` and see whether the path is in the population after all.  That
is the only method that has ever detected a mask in this package, and this
module's first result is about the method rather than about any guard:

    Of the 12 ``(guard, TYPED exemption)`` pairs the scan derives, **exactly one
    — ``undeclared_drift`` — takes its exemption as a parameter.**

D-050 could run its probe because ``undeclared_drift`` happens to accept
``declared=``, a parameter that exists so :func:`tree_provenance.verify` can
pass a stamp's own allow-list, *not* so anyone could audit it.  The one mask
ever found was found through a keyword argument that is there for an unrelated
reason.  That is D-046's "a coincidence was holding a filter's place", one layer
up: the coincidence was holding the *probe's* place.

So the screen does not stop at reporting 11 unfalsifiable pairs.  A hard-wired
constant is still a **module global**, and Python resolves globals at call time,
so :func:`suppress` sets the attribute on the module that *defines* the guard
and calls it again.  Every pair becomes runnable, and the population of
suppression routes is derived from the AST rather than typed.

Verdicts, and the scoping is the point:

``CANDIDATE``
    The reading **grows** under suppression.  The exemption removes members the
    guard would otherwise report.  This is *not* proof of masking — masking also
    requires that the removed members are the ones the offence produces, which
    only :mod:`guard_direction`'s dynamic probe can say.  It is the candidate
    set for that probe, which is what STATE #1 asked for.
``INERT``
    The reading is unchanged under suppression.  The exemption removes nothing
    at ``HEAD`` — D-046's coincidence shape, where an unscored exemption is
    indistinguishable from a clean one.
``VACUOUS``
    The registry is already empty at ``HEAD``, so suppression cannot change
    anything and ``INERT`` would mean nothing.  Reported separately rather than
    folded into ``INERT``, because the two are different facts.
``UNPOPULATED``
    ``VACUOUS``'s argument one level down, and D-088's finding.  The registry is
    non-empty but the *guard reads nothing* at ``HEAD``, and nothing under
    suppression either — so, exactly as with an empty registry, suppression
    cannot change anything and ``INERT`` would mean nothing.  The two emptinesses
    are structurally identical and only the first was named, so for three cycles
    the second was reported as ``INERT``: a claim about the **exemption** when
    the fact was about the guard's **subject**.

    It is not an edge case.  Both ``DIFFERENCE`` guards land here whenever the
    repository is in its ordinary state, and the flip is invisible in the old
    vocabulary:

    ===============================  ================  ==============
    pair                             subject empty     subject present
    ===============================  ================  ==============
    ``undeclared_drift``             ``UNPOPULATED``   ``CANDIDATE``
    ``staged_declarations``          ``UNPOPULATED``   ``DIVERGES``
    ===============================  ================  ==============

    Measured, not argued: a ``--depth 1`` checkout has a clean worktree, so the
    first row's left cell is what CI reads and the dev machine reads the right;
    ``git add`` one declared path and the second row moves 1→0.  Both used to
    read ``INERT``, so the screen's verdict for a pair was a function of the
    working tree that no verdict name disclosed.
``DIVERGES``
    The reading changed but did not grow.  Not the bite shape; named so it
    cannot be silently counted as one.
``UNRUNNABLE`` / ``DEAD``
    The guard could not be called, or suppression did not take.  D-050's lesson
    applied to this module's own instrument: a liveness act runs first, so
    ``INERT`` means *the exemption removes nothing* rather than *my suppression
    silently failed*.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import guard_reflexivity as gr

#: How the exemption's registry can be replaced for the duration of one call.
ROUTE_PARAMETER = "PARAMETER"
ROUTE_MODULE_GLOBAL = "MODULE_GLOBAL"
ROUTE_UNREACHABLE = "UNREACHABLE"

VERDICT_CANDIDATE = "CANDIDATE"
VERDICT_INERT = "INERT"
VERDICT_VACUOUS = "VACUOUS"
VERDICT_UNPOPULATED = "UNPOPULATED"
VERDICT_DIVERGES = "DIVERGES"
VERDICT_UNRUNNABLE = "UNRUNNABLE"
VERDICT_DEAD = "DEAD"


@dataclass(frozen=True)
class Route:
    """How a guard's typed exemption can be suppressed, derived not declared."""

    guard: str
    constant: str
    route: str
    #: For ``PARAMETER``: the keyword whose default is the registry.
    parameter: str | None = None
    #: The module whose global binding the guard actually reads.
    binding_module: str | None = None

    @property
    def key(self) -> tuple[str, str]:
        return (self.guard, self.constant)


@dataclass(frozen=True)
class Screen:
    """One ``(guard, exemption)`` pair read at ``HEAD`` and under suppression."""

    guard: str
    constant: str
    route: str
    verdict: str
    head_size: int = 0
    suppressed_size: int = 0
    registry_size: int = 0
    note: str = ""

    @property
    def revealed(self) -> int:
        """Members the exemption is removing from the guard's own reading."""
        return max(0, self.suppressed_size - self.head_size)


# --------------------------------------------------------------------------
# routes — derived from the guard's own source, never typed
# --------------------------------------------------------------------------


def _parameter_defaults(fn: ast.FunctionDef) -> dict[str, str]:
    """Parameter name -> the ``Name`` its default resolves to, if any."""
    out: dict[str, str] = {}
    args = fn.args
    positional = args.posonlyargs + args.args
    for arg, default in zip(positional[len(positional) - len(args.defaults):],
                            args.defaults):
        if isinstance(default, ast.Name):
            out[arg.arg] = default.id
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        if isinstance(default, ast.Name):
            out[arg.arg] = default.id
    return out


def _substitutes_for(fn: ast.FunctionDef, constant: str) -> str | None:
    """A parameter that stands in for *constant* inside the body.

    Three spellings, and the third one is why this function has a docstring.
    Either the parameter's own default is the registry
    (``declared=DECLARED_LOCAL_ONLY``), or the body rebinds a parameter from it,
    or — the ``None``-default idiom this package actually uses —

        allow = DECLARED_LOCAL_ONLY if declared is None else declared

    where the assignment target is a **local**, not the parameter.  The first
    draft required the target to be a parameter name and therefore missed
    ``tree_provenance.undeclared_drift``: the one guard in the package with a
    parameter route, the guard D-050 was about, and the guard this whole module
    was written to generalise from.  Ninth first-draft scan in ten cycles wrong
    about its own population, and again in the under-counting direction — it
    reported 12 module-global routes and 0 parameter routes, i.e. that D-050's
    own probe was impossible.

    So the test is on the ``IfExp`` rather than on the binding: a conditional
    that chooses between *constant* and a parameter is a substitution route no
    matter what the result is called.
    """
    direct = _parameter_defaults(fn)
    for param, name in direct.items():
        if name == constant:
            return param
    names = {a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs}
    for node in ast.walk(fn):
        if isinstance(node, ast.IfExp):
            arms = [node.body, node.orelse]
            mentions_const = any(isinstance(a, ast.Name) and a.id == constant
                                 for a in arms)
            params = [a.id for a in arms if isinstance(a, ast.Name) and a.id in names]
            if mentions_const and params:
                return params[0]
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in names:
            continue
        if any(isinstance(n, ast.Name) and n.id == constant
               for n in ast.walk(node.value)):
            return target.id
    return None


def routes(pool: Iterable[gr.Guard] | None = None,
           package: Path | None = None) -> tuple[Route, ...]:
    """Suppression route for every derived ``(guard, TYPED exemption)`` pair.

    The population is :attr:`gr.Guard.typed_exemptions` — the same set every
    ``TYPED`` screen in the package consumes — so this module cannot go short by
    disagreeing with them about who is in scope.  What it adds is *whether the
    exemption can be taken away*, which none of them ask.
    """
    base = package or gr.PACKAGE
    pool = tuple(pool if pool is not None else gr.guards(base))
    sources: dict[str, dict[str, ast.FunctionDef]] = {}
    for path in gr.package_modules(base):
        tree = ast.parse(path.read_text())
        sources[path.stem] = {n.name: n for n in tree.body
                              if isinstance(n, ast.FunctionDef)}
    out: list[Route] = []
    seen: set[tuple[str, str]] = set()
    for guard in pool:
        fn = sources.get(guard.module, {}).get(guard.name)
        for exemption in guard.typed_exemptions:
            const = exemption.constant
            if const is None or (guard.qualname, const) in seen:
                continue
            seen.add((guard.qualname, const))
            param = _substitutes_for(fn, const) if fn is not None else None
            if param is not None:
                out.append(Route(guard.qualname, const, ROUTE_PARAMETER,
                                 parameter=param, binding_module=guard.module))
                continue
            module = _binding_module(guard.module, const)
            out.append(Route(guard.qualname, const,
                             ROUTE_MODULE_GLOBAL if module else ROUTE_UNREACHABLE,
                             binding_module=module))
    return tuple(sorted(out, key=lambda r: r.key))


def _binding_module(module: str, constant: str) -> str | None:
    """The module whose global namespace the guard's body actually resolves.

    A ``from .tree_provenance import DECLARED_LOCAL_ONLY`` binds the name in the
    *importing* module, and that is the binding the guard's body reads — so
    suppression must patch there, not at the definition site.  Checked by
    ``getattr`` rather than by reading the import statement, because an import
    that was later shadowed would make the syntactic answer wrong.
    """
    try:
        mod = importlib.import_module(f"{__package__}.{module}")
    except Exception:  # pragma: no cover - import failure is itself a finding
        return None
    return module if hasattr(mod, constant) else None


def unsuppressible(pool: Iterable[gr.Guard] | None = None,
                   package: Path | None = None) -> tuple[str, ...]:
    """Pairs with no suppression route — a mask there is undetectable.

    Kept as its own function, and asserted empty in the tests, for the reason
    :func:`gr.unbitten` exists: the interesting number is not how many pairs
    were screened but how many *could not be*.
    """
    return tuple(f"{r.guard} ~ {r.constant}"
                 for r in routes(pool, package) if r.route == ROUTE_UNREACHABLE)


def parameterised(pool: Iterable[gr.Guard] | None = None,
                  package: Path | None = None) -> tuple[str, ...]:
    """Pairs D-050's probe could have run on **without** this module.

    At the time of writing this is a one-element tuple, and that element is the
    guard D-050 was about.  The count is the module's own justification.
    """
    return tuple(f"{r.guard} ~ {r.constant}"
                 for r in routes(pool, package) if r.route == ROUTE_PARAMETER)


# --------------------------------------------------------------------------
# suppression — the probe, with a liveness act in front of it
# --------------------------------------------------------------------------


def _empty_like(value: Any) -> Any:
    if isinstance(value, dict):
        return {}
    if isinstance(value, set):
        return set()
    if isinstance(value, frozenset):
        return frozenset()
    if isinstance(value, list):
        return []
    return ()


def _reading(value: Any) -> tuple[str, ...]:
    """Normalise a guard's return value to a comparable set of statements.

    Guards in this package return lists, tuples, dicts, dataclasses and — for
    the ``report`` pair — plain text.  Comparing sizes alone would call a
    reordering a change; comparing reprs alone would make a dict's iteration
    order load-bearing.  Sorted statements is the form that is stable under both.

    The **dataclass** arm is the second first-draft defect, and it is the one
    that would have made this module useless at its own job.  ``undeclared_drift``
    returns a :class:`tree_provenance.Drift` — three tuples in a frozen
    dataclass.  Collapsed to ``(repr(value),)`` it is a one-element reading on
    both sides of the suppression, so ``set(head) < set(after)`` can never hold
    and the guard whose mask D-050 *proved* comes out ``DIVERGES``.  A screen
    that cannot re-find the only positive result in the literature it
    generalises is not a screen.  Fields are flattened instead.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        out: list[str] = []
        for field in dataclasses.fields(value):
            member = getattr(value, field.name)
            out.extend(f"{field.name}:{item}" for item in _reading(member))
        return tuple(sorted(out))
    if isinstance(value, str):
        return tuple(sorted(line for line in value.splitlines() if line.strip()))
    if isinstance(value, dict):
        return tuple(sorted(f"{k}={v!r}" for k, v in value.items()))
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(sorted(repr(v) for v in value))
    return (repr(value),)


def _call(fn) -> Any:
    """Call a guard with no arguments, refusing rather than guessing.

    Every guard in the derived population has defaults for all of its
    parameters.  One that does not is :data:`VERDICT_UNRUNNABLE`, not a
    fabricated argument.
    """
    sig = inspect.signature(fn)
    for param in sig.parameters.values():
        if param.default is inspect.Parameter.empty and param.kind in (
                param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY):
            raise TypeError(f"required parameter {param.name!r}")
    return fn()


def screen_one(route: Route) -> Screen:
    """Read one pair at ``HEAD`` and again with its registry suppressed."""
    module_name, _, guard_name = route.guard.rpartition(".")
    try:
        mod = importlib.import_module(f"{__package__}.{module_name}")
        fn = getattr(mod, guard_name)
    except Exception as exc:  # pragma: no cover - import failure is a finding
        return Screen(route.guard, route.constant, route.route,
                      VERDICT_UNRUNNABLE, note=f"import: {exc}")

    binding = route.binding_module or module_name
    try:
        holder = importlib.import_module(f"{__package__}.{binding}")
        original = getattr(holder, route.constant)
    except Exception as exc:  # pragma: no cover
        return Screen(route.guard, route.constant, route.route,
                      VERDICT_UNRUNNABLE, note=f"registry: {exc}")

    registry_size = len(original) if hasattr(original, "__len__") else 0
    if registry_size == 0:
        return Screen(route.guard, route.constant, route.route, VERDICT_VACUOUS,
                      registry_size=0,
                      note="registry empty at HEAD — suppression cannot change anything")

    try:
        head = _reading(_call(fn))
    except Exception as exc:
        return Screen(route.guard, route.constant, route.route,
                      VERDICT_UNRUNNABLE, registry_size=registry_size,
                      note=f"call at HEAD: {exc}")

    blank = _empty_like(original)
    if route.route == ROUTE_PARAMETER and route.parameter:
        def _suppressed():
            return fn(**{route.parameter: blank})
        took = True
    else:
        def _suppressed():
            return _call(fn)
        took = False

    try:
        if route.route == ROUTE_PARAMETER and route.parameter:
            after = _reading(_suppressed())
        else:
            setattr(holder, route.constant, blank)
            # Liveness: the patch must actually be readable as empty from the
            # namespace the guard's body resolves, or INERT below would mean
            # "my suppression silently failed" rather than "nothing was removed".
            took = len(getattr(holder, route.constant)) == 0
            after = _reading(_call(fn)) if took else ()
    except Exception as exc:
        return Screen(route.guard, route.constant, route.route,
                      VERDICT_UNRUNNABLE, head_size=len(head),
                      registry_size=registry_size,
                      note=f"call under suppression: {exc}")
    finally:
        if route.route != ROUTE_PARAMETER:
            setattr(holder, route.constant, original)

    if not took:
        return Screen(route.guard, route.constant, route.route, VERDICT_DEAD,
                      head_size=len(head), registry_size=registry_size,
                      note="suppression did not take")

    if not head and not after:
        # D-088. The registry is non-empty (VACUOUS already returned), but the
        # guard's subject population is empty, so there was nothing for the
        # exemption to remove and the suppression was never actually tested.
        # Reporting this as INERT states a fact about the exemption when the
        # only fact available is about the input — and which of the two a pair
        # gets depends on the working tree, which no verdict used to disclose.
        return Screen(route.guard, route.constant, route.route,
                      VERDICT_UNPOPULATED,
                      head_size=0, suppressed_size=0,
                      registry_size=registry_size,
                      note="guard read nothing at HEAD — suppression untested")

    if after == head:
        return Screen(route.guard, route.constant, route.route, VERDICT_INERT,
                      head_size=len(head), suppressed_size=len(after),
                      registry_size=registry_size)
    if set(head) < set(after):
        return Screen(route.guard, route.constant, route.route, VERDICT_CANDIDATE,
                      head_size=len(head), suppressed_size=len(after),
                      registry_size=registry_size)
    return Screen(route.guard, route.constant, route.route, VERDICT_DIVERGES,
                  head_size=len(head), suppressed_size=len(after),
                  registry_size=registry_size,
                  note="changed without growing — not the bite shape")


def screen(pool: Iterable[gr.Guard] | None = None,
           package: Path | None = None) -> tuple[Screen, ...]:
    """Every derived pair, read both ways."""
    return tuple(screen_one(r) for r in routes(pool, package))


def candidates(screened: Iterable[Screen] | None = None) -> tuple[str, ...]:
    """Pairs whose exemption is removing members — the dynamic probe's work list.

    Handed to :mod:`guard_direction`, which is the only thing that can turn a
    candidate into a verdict: growth under suppression says the exemption bites,
    not that what it removes is what the offence produces.
    """
    scored = tuple(screened if screened is not None else screen())
    return tuple(sorted(f"{s.guard} ~ {s.constant} (+{s.revealed})"
                        for s in scored if s.verdict == VERDICT_CANDIDATE))


def masking_candidates(screened: Iterable[Screen] | None = None,
                       pool: Iterable[gr.Guard] | None = None,
                       package: Path | None = None) -> tuple[str, ...]:
    """:func:`candidates` intersected with revocability — the answer to STATE #1.

    Bite alone is a **weak** screen, and saying so is most of this function's
    value: 6 of 12 pairs grow under suppression, and on inspection every one of
    the five that are not D-050's is an exemption *doing its job*.  Suppress
    ``ADAPTERS`` and all 7 predicates are unadapted; suppress
    ``DECLARED_LOCAL_ONLY`` in ``unregistered_local_only`` and all 5 declared
    paths are unregistered.  Growth under suppression means the exemption
    removes members.  That is what an exemption is **for**.

    D-048 supplies the missing half, and it is structural rather than semantic:
    a mask requires the offence to be able to *collapse* the population, and an
    ``ENUMERATION`` population still contains the offender after the offence —
    only a ``DIFFERENCE`` can go quiet.  So masking ⟹ bites **and** revocable.

    Intersecting the two leaves exactly **one** pair, and it is
    ``tree_provenance.undeclared_drift ~ DECLARED_LOCAL_ONLY`` — D-050's own.

    The second ``DIFFERENCE`` guard, ``local_only_audit.staged_declarations``,
    does not qualify, and D-088 corrected *why*.  The mechanism given here was
    right — it narrows **down to** the registry rather than subtracting it, so
    suppression empties its population instead of growing it — but it was
    attached to the wrong verdict.  Emptying a population is ``DIVERGES``
    ("changed without growing"), and that is what the pair measures once
    anything is staged: 1→0.  The ``INERT`` it was quoted for is what it reads
    when the index is empty, i.e. exactly when the described mechanism does
    **not** run.  The prose and the number were never about the same event, and
    no measurement contradicted it because the index is empty in every ordinary
    run.  Under D-088's vocabulary that case is ``UNPOPULATED`` and says so.

    The masking class stays bounded at **one**, but state the warrant honestly:
    it is one candidate among the pairs that were *actually probed*, and
    :func:`unscreened` now carries the rest.  On a clean checkout the unprobed
    set includes both ``DIFFERENCE`` guards — the whole population from which a
    second mask could come — so the bound is a real measurement only on a tree
    where the subjects exist.  That is weaker than "by measurement over all 12
    typed pairs" as this docstring used to claim, and it is the claim the
    numbers support.
    """
    scored = tuple(screened if screened is not None else screen(pool, package))
    guard_pool = tuple(pool if pool is not None else gr.guards(package or gr.PACKAGE))
    revocable = {g.qualname for g in gr.revocable(guard_pool)}
    return tuple(sorted(f"{s.guard} ~ {s.constant} (+{s.revealed})"
                        for s in scored
                        if s.verdict == VERDICT_CANDIDATE and s.guard in revocable))


def unscreened(screened: Iterable[Screen] | None = None) -> tuple[str, ...]:
    """Pairs the screen could not read — the mirror :func:`candidates` needs.

    An empty candidate set is a clearance only if nothing was skipped on the way
    to it.  Fifth registry in this package to get this treatment, for the reason
    D-045 gave the first four.

    ``UNPOPULATED`` belongs here and its absence was D-088's second half.  The
    skip it names is *silent* in a way ``UNRUNNABLE`` and ``DEAD`` are not: those
    two announce a broken mechanism, whereas a pair whose subject was empty ran
    perfectly and produced no information — and used to be filed under ``INERT``,
    which reads as a result.  A clean checkout could therefore report **zero
    candidates and zero skips** while two of its pairs had never been probed.
    That is this package's recurring defect (absence read as a clean bill:
    ``push_preflight.VACUOUS``, ``git_surface.NO_REMOTE_BRANCHES``,
    ``local_only_audit``'s inversion, ``ci_verdict``'s late aggregate) in the
    module written to hunt exactly this shape, which is why it is worth the name.

    ``VACUOUS`` deliberately stays out: an empty registry exempts nothing under
    any working tree, so there is no unprobed pair hiding behind it.  The
    difference between the two is whether the emptiness is a property of the
    package or of this run.
    """
    scored = tuple(screened if screened is not None else screen())
    return tuple(sorted(f"{s.guard} ~ {s.constant}: {s.verdict} {s.note}".strip()
                        for s in scored
                        if s.verdict in (VERDICT_UNRUNNABLE, VERDICT_DEAD,
                                         VERDICT_UNPOPULATED)))


def report(package: Path | None = None) -> str:
    scored = screen(package=package)
    lines = [f"typed exemption pairs screened: {len(scored)}"]
    by_route: dict[str, int] = {}
    for r in routes(package=package):
        by_route[r.route] = by_route.get(r.route, 0) + 1
    lines.append("  routes: " + ", ".join(f"{k}={v}" for k, v in sorted(by_route.items())))
    for s in scored:
        detail = f"{s.head_size}->{s.suppressed_size}" if s.suppressed_size else "-"
        lines.append(f"  {s.verdict:10s} {s.guard} ~ {s.constant} [{s.route}] {detail}")
    lines.append(f"bites (weak screen): {len(candidates(scored))}")
    for c in candidates(scored):
        lines.append(f"  {c}")
    masks = masking_candidates(scored)
    lines.append(f"masking candidates (bites AND revocable): {len(masks)}")
    for m in masks:
        lines.append(f"  {m}")
    lines.append(f"unscreened: {len(unscreened(scored))}")
    for u in unscreened(scored):
        lines.append(f"  {u}")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 1 if (unsuppressible() or unscreened()) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
