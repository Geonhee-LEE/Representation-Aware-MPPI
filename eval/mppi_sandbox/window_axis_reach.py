# SPDX-License-Identifier: BSD-3-Clause
"""How far does D-273's `OFF_AXIS` reach — and which consumers cannot be asked?

D-273 graded **one** cell. `window_axis_key` composes an axis check onto
`lam_window_key.lookup` and answers, for `(cafe_freezing_v0, risk_mppi)` at the
ladder's cost field, that the window is `OFF_AXIS` in both key states. The
obvious follow-up is to run that instrument over the other consumers. This
module is what happens when you try, and the answer is not a longer list of
cells.

**Most consumers do not resolve through `lam_window_key.lookup` at all.** They
go through `lam_window_index.resolve`, whose signature is::

    resolve(scenario, controller, weight: float, index=None) -> Resolution

A `float`. There is nowhere to put `w_voo`. The index was built (D-145 era) to
pick *which table* is calibrated at a caller's barrier weight, and it inherited
`lam_window_key`'s one-scalar view of the cost field along the way. So the axis
question is not merely unanswered for those consumers — it is **unaskable
through the API they use**. Handing `window_axis_key` a consumer that resolves
through the index does not grade it `OFF_AXIS`; it has no place to accept the
field that would make the grade mean anything.

That is the finding, and it is structural rather than per-cell: the reach of
D-273 is bounded by *which resolver a consumer happens to call*, not by which
cost field it happens to run in.

The measurement
---------------

Of **10 production call sites** that resolve a λ window, **1** can put the axis
question — and it is `window_axis_key.q154`, the lookup D-273 wrote to ask it.
Every other production resolution in the repo, including all four in
`lam_window_index` itself and `scene_transplant`'s rung screen, goes through a
scalar. So D-273's reach is exactly the cell D-273 was written for; the ~30
consumers the follow-up expected to grade are, on inspection, mostly test call
sites, and the production ones cannot be graded at all.

The dangerous half is the enforcing path
----------------------------------------

`comparison_headroom.assert_certified` is the one entry point in this family
that **raises** — D-143's gap was that "`resolve` supplied the window and
nothing consumed it", and that function is the fix. It resolves through the
index, one level down in `certify`. So the strictest guard the window family
owns is also axis-blind: an operating point off-axis in exactly D-273's sense
passes it as `CERTIFIED`, and it does so while raising on the axis it *can*
see. A guard that refuses loudly on one axis and is structurally silent on
another reads, to its caller, as though it checked both.

That site is only visible to a **transitive** notion of enforcement, and the
first version of this module did not have one: it tested the enclosing function
for a `raise`, `certify` does not raise, and the reading came back naming a
different function entirely. :func:`enforcing_functions` closes the call graph
downward from the raising functions, and says in its own docstring that it is
an upper bound rather than proof the `raise` is conditioned on the window.

What is derived and what is declared
------------------------------------

The discriminator is not a list of which functions are scalar-only. It is read
off the signature of the resolver that *can* ask the question: whichever
parameter of `window_axis_key.lookup` carries the cost field names the
capability (:data:`COST_FIELD_PARAM`), and every resolver is graded by whether
it has one. The day `lam_window_index.resolve` grows a `cost_field=` parameter,
this module reports it without being edited — the same discipline
`window_axis_key.calibrated_axes` uses to read the axis set off `ab.lam_ladder`
rather than typing `w_voo` (D-047).

:data:`RESOLVERS` *is* declared, following `lam_window_index.TABLES`'s stated
precedent: a resolver merely omitted from a derived scan is indistinguishable
from one that does not exist. `test_every_window_importer_is_classified` is the
guard that keeps the declaration honest — a new module that imports
`lam_window_key` must be either a registered resolver or a scanned consumer.

What this deliberately does not do
----------------------------------

  * **Widen `lam_window_index.resolve`.** Adding `cost_field=` there is the
    repair this measurement argues for, but it is a change to the enforcing
    path of a guard three modules depend on, and measuring it in the same cycle
    that changes it is the pattern D-268 (d) and D-274 both declined. Q-157.
  * **Grade any cell.** No window is resolved here and no run is taken. The
    population is call sites; the verdict is about API reach.
  * **Call the blind consumers wrong.** `AXIS_BLIND` is a statement that the
    question cannot be put, not that the answer would be `OFF_AXIS`. Several of
    these consumers may well run at the calibrated default on every axis.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .default_lam_sites import (
    REPO_ROOT,
    _enclosing,
    _import_maps,
    _sources,
    _target,
)

#: The resolver can be handed a whole cost field, so `window_axis_key`'s
#: question is expressible through it.
COST_FIELD = "COST_FIELD"

#: The resolver takes a scalar weight. A caller running off-default on any
#: other axis has nowhere to say so, and no composition of guards downstream
#: can recover the information.
SCALAR_ONLY = "SCALAR_ONLY"

#: A consumer that reaches only :data:`SCALAR_ONLY` resolvers.
AXIS_BLIND = "AXIS_BLIND"

#: A consumer that reaches a :data:`COST_FIELD` resolver.
AXIS_AWARE = "AXIS_AWARE"

#: An :data:`AXIS_BLIND` consumer whose enclosing function raises on refusal —
#: i.e. one that *enforces* a window it cannot fully check.
BLIND_ENFORCEMENT = "BLIND_ENFORCEMENT"

#: The window-resolution entry points, declared rather than discovered — see
#: the module docstring for why, and `lam_window_index.TABLES` for the
#: precedent. Order is (module, attribute).
RESOLVERS: tuple[tuple[str, str], ...] = (
    ("eval.mppi_sandbox.lam_window_key", "lookup"),
    ("eval.mppi_sandbox.lam_window_index", "resolve"),
    ("eval.mppi_sandbox.window_axis_key", "lookup"),
)

#: Modules that legitimately import `lam_window_key` without resolving a
#: window: they cite it, index its rows, or audit it. Declared for the same
#: reason as :data:`RESOLVERS`, and kept small on purpose.
NON_RESOLVING_IMPORTERS: frozenset[str] = frozenset({
    "eval.mppi_sandbox.citation_audit",     # registers citation sites
    "eval.mppi_sandbox.calibrate_lam",      # writes the tables
    "eval.mppi_sandbox.separation_reproduction",
    "eval.mppi_sandbox.ab",
})


def cost_field_param() -> str:
    """The parameter name that *means* "the caller's whole cost field".

    Read off `window_axis_key.lookup` — the resolver that can ask the axis
    question defines what asking looks like. Typing the string here instead
    would be the second statement that drifts (D-047).
    """
    from . import window_axis_key

    for name, p in inspect.signature(window_axis_key.lookup).parameters.items():
        ann = p.annotation
        text = ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))
        if "Mapping" in str(text):
            return name
    raise LookupError("window_axis_key.lookup has no cost-field parameter")


#: Resolved once at import for readability; :func:`cost_field_param` is the
#: authority and tests call it directly.
COST_FIELD_PARAM = cost_field_param()


def _load(module: str, attr: str):
    import importlib

    return getattr(importlib.import_module(module), attr)


def grade_resolver(module: str, attr: str) -> str:
    """:data:`COST_FIELD` or :data:`SCALAR_ONLY`, from the signature alone."""
    params = inspect.signature(_load(module, attr)).parameters
    return COST_FIELD if COST_FIELD_PARAM in params else SCALAR_ONLY


def resolvers() -> dict[tuple[str, str], str]:
    """Every registered resolver with its grade."""
    return {(m, a): grade_resolver(m, a) for m, a in RESOLVERS}


@dataclass(frozen=True)
class Consumer:
    """One call site that resolves a λ window."""

    path: str
    line: int
    #: Enclosing `def` name, or `"<module>"` at module scope.
    function: str
    resolver: tuple[str, str]
    grade: str
    #: The enclosing function contains a `raise` — it enforces, not reports.
    enforces: bool

    @property
    def is_test(self) -> bool:
        return "/tests/" in self.path or Path(self.path).name.startswith("test_")

    @property
    def verdict(self) -> str:
        if self.grade == COST_FIELD:
            return AXIS_AWARE
        return BLIND_ENFORCEMENT if self.enforces else AXIS_BLIND

    def __str__(self) -> str:
        return (f"{self.path}:{self.line} {self.function}() "
                f"-> {self.resolver[0].rsplit('.', 1)[-1]}.{self.resolver[1]} "
                f":: {self.verdict}")


def _raises(fn: ast.AST | None) -> bool:
    return fn is not None and any(isinstance(n, ast.Raise) for n in ast.walk(fn))


def enforcing_functions(root: Path | None = None) -> frozenset[tuple[str, str]]:
    """Functions that sit on a refusing path, as an explicit **over-approximation**.

    Seeded by the functions that contain a `raise` and closed downward through
    the call graph: if a raising function calls `F`, then `F` is on a path that
    can refuse. The closure is what makes the measurement see
    `comparison_headroom.assert_certified` — it raises, but the `resolve` call
    it enforces lives one level down in `certify`, so the enclosing-function
    test alone misses exactly the site the docstring is about. That miss was
    the first reading this module produced.

    It is an upper bound, and named as one. A purely syntactic scan cannot show
    that the `raise` is *conditioned on* the resolution — only that a caller of
    this code refuses at all. :data:`BLIND_ENFORCEMENT` is therefore a set to
    read, not a count to minimise, and :func:`report` prints its members.
    """
    sources = _sources(root)
    calls: dict[tuple[str, str], set[tuple[str, str]]] = {}
    raising: set[tuple[str, str]] = set()
    for _path, (_src, tree, modname) in sources.items():
        names, alias = _import_maps(tree, modname)
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            key = (modname, fn.name)
            if any(isinstance(n, ast.Raise) for n in ast.walk(fn)):
                raising.add(key)
            out = calls.setdefault(key, set())
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    target = _target(node, names, alias)
                    if target is not None:
                        out.add(target)
    seen = set(raising)
    stack = list(raising)
    while stack:
        for callee in calls.get(stack.pop(), ()):
            if callee not in seen:
                seen.add(callee)
                stack.append(callee)
    return frozenset(seen)


def consumers(root: Path | None = None) -> tuple[Consumer, ...]:
    """Every call site of a registered resolver, graded by what it can express.

    Resolver *definitions* are excluded — `lam_window_index.resolve` calls
    `lam_window_key.lookup` internally, and counting that as a consumer would
    make the index look axis-aware because of the very call that discards the
    field.
    """
    targets = resolvers()
    enforcers = enforcing_functions(root)
    out: list[Consumer] = []
    for path, (_src, tree, modname) in _sources(root).items():
        names, alias = _import_maps(tree, modname)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = _target(node, names, alias)
            if target not in targets:
                continue
            fn = _enclosing(tree, node)
            key = (modname, getattr(fn, "name", None))
            if key in targets:
                continue                      # the resolver's own definition
            rel = path.relative_to(root or REPO_ROOT).as_posix()
            out.append(Consumer(
                path=rel, line=node.lineno,
                function=getattr(fn, "name", "<module>"),
                resolver=target, grade=targets[target],
                enforces=_raises(fn) or key in enforcers))
    return tuple(sorted(out, key=lambda c: (c.path, c.line)))


def window_importers(root: Path | None = None) -> frozenset[str]:
    """Modules importing `lam_window_key`, by module name."""
    key = "eval.mppi_sandbox.lam_window_key"
    found = set()
    for _path, (_src, tree, modname) in _sources(root).items():
        _names, alias = _import_maps(tree, modname)
        if any(v == key or v.startswith(key + ".") for v in alias.values()):
            found.add(modname)
    return frozenset(found)


@dataclass(frozen=True)
class Census:
    consumers: tuple[Consumer, ...]

    def _of(self, verdict: str) -> tuple[Consumer, ...]:
        return tuple(c for c in self.consumers if c.verdict == verdict)

    @property
    def aware(self) -> tuple[Consumer, ...]:
        return self._of(AXIS_AWARE)

    @property
    def blind(self) -> tuple[Consumer, ...]:
        return self._of(AXIS_BLIND)

    @property
    def blind_enforcement(self) -> tuple[Consumer, ...]:
        return self._of(BLIND_ENFORCEMENT)

    @property
    def production(self) -> tuple[Consumer, ...]:
        return tuple(c for c in self.consumers if not c.is_test)

    @property
    def reach(self) -> float:
        """Fraction of consumers the axis question can even be put to."""
        return len(self.aware) / len(self.consumers) if self.consumers else 0.0


def census(root: Path | None = None) -> Census:
    return Census(consumers=consumers(root))


def report(root: Path | None = None) -> str:
    c = census(root)
    lines = [
        "window_axis_reach — can D-273's question be put to this consumer?",
        "",
        f"cost-field parameter: {COST_FIELD_PARAM!r}",
    ]
    for (m, a), g in resolvers().items():
        lines.append(f"  {m.rsplit('.', 1)[-1]}.{a}: {g}")
    lines += [
        "",
        f"consumers {len(c.consumers)} "
        f"(production {len(c.production)}, test {len(c.consumers) - len(c.production)})",
        f"  {AXIS_AWARE} {len(c.aware)}   {AXIS_BLIND} {len(c.blind)}   "
        f"{BLIND_ENFORCEMENT} {len(c.blind_enforcement)}",
        f"  reach {c.reach:.1%}",
    ]
    if c.blind_enforcement:
        lines += ["", "enforcing while axis-blind:"]
        lines += [f"  {x}" for x in c.blind_enforcement]
    return "\n".join(lines)


if __name__ == "__main__":       # pragma: no cover
    print(report())
