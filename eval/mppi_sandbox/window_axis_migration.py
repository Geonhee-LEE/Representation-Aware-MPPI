# SPDX-License-Identifier: BSD-3-Clause
"""What would Q-157 option (b) actually cost — and is it a call-site edit at all?

D-275 measured that 9 of 10 production window resolutions cannot express the
axis question, because `lam_window_index.resolve` takes a `weight: float`.
Q-157 asks whether to widen it, and leans to **(b) required `cost_field=`** on
the grounds that (a) optional leaves silence as the default. Its own next
action deferred the choice until someone counted the migration: *partition each
site by whether the weight it passes is a literal or forwarded, because the
47 test sites are probably passing literals and would be mechanical.*

This module is that count, and it reports two things Q-157 did not price.

**The test half of the lean is right; the production half inverts it.** Of the
47 test call sites, 28 pass a **literal** — mechanical, exactly as Q-157
guessed. Of the 10 production sites, **zero** do. Not one production caller of
a window resolver knows its weight as a constant at the call site.

**And the dominant production class is not a call-site edit.** Four of the nine
blind production sites read the weight off an **attribute of a record** —
`row.weight`, `self.weight`, `cell.weight`. Making `cost_field` required does
not edit those nine calls; it requires the *record types feeding them* to carry
a cost field. That is a data-model change, and it is upstream of every line
this census can point at.

The site that matters most is in that class
-------------------------------------------

`comparison_headroom.certify` — the sole production `BLIND_ENFORCEMENT` site,
the one D-275 named as the reason any of this is worth doing — resolves at
`row.weight`, where `row` is a `Headroom`. So reaching the enforcing path with
the axis question means `Headroom` grows a cost field, and every producer of a
`Headroom` has to fill it. The most valuable site to migrate sits in the most
expensive class, which is the opposite of the ordering a cheap-first migration
would pick.

What the classes mean
---------------------

The vocabulary is the AST form of the argument, fixed before the counts were
read (D-241) and derived rather than chosen — these are the node kinds Python
admits in that position, not a set of labels selected to be flattering:

  * :data:`LITERAL` — a constant. The site knows its weight statically, so it
    can name a field statically. **Mechanical.**
  * :data:`LOCAL` — bound inside the enclosing function (loop variable,
    assignment). A field can be built where the weight is built. **Site-local.**
  * :data:`FORWARDED` — a parameter of the enclosing function. The field has to
    enter that signature too, so the migration escapes the call site upward.
  * :data:`RECORD_FIELD` — an attribute of some record. The record type has no
    cost field; adding one is a **data-model** change.
  * :data:`DERIVED` — the return of a call. Whatever produced the weight is
    where a field would come from; needs a read, not a rule.
  * :data:`COMPUTED` — anything else (subscript, arithmetic).

:func:`cost_class` maps those onto the four kinds of work, and it is the
partition Q-157 asked for. It deliberately does **not** produce a single number
of hours: the point of the measurement is that the classes differ in kind, and
collapsing them to a count is what made (b) look like a 57-line edit.

What is derived and what is declared
------------------------------------

The weight parameter is read off each scalar-only resolver's own signature —
the `float`-annotated parameter *is* the thing a cost field would replace —
mirroring `window_axis_reach.cost_field_param`, which reads the capability off
`window_axis_key.lookup` (D-047: the second statement of a quantity drifts).
The resolver population is `window_axis_reach.RESOLVERS`, not a second list;
when a resolver is registered there, it is counted here without an edit. And
the day `resolve` grows `cost_field=`, it grades `COST_FIELD` upstream and
drops out of this census on its own.

What this does not do
---------------------

  * **Choose between (a), (b) and (c).** Q-157 said not to choose before the
    number existed. The number now exists and it argues about *sequencing*, not
    about which option wins.
  * **Claim the test sites are free.** 28 mechanical of 47 leaves 19 that are
    not, and 4 of those are `RECORD_FIELD` too.
  * **Resolve any window.** No run is taken; the population is call sites.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .default_lam_sites import (
    REPO_ROOT,
    _enclosing,
    _import_maps,
    _sources,
    _target,
)
from .window_axis_reach import COST_FIELD, RESOLVERS, grade_resolver

#: A constant at the call site.
LITERAL = "LITERAL"

#: Bound inside the enclosing function.
LOCAL = "LOCAL"

#: A parameter of the enclosing function.
FORWARDED = "FORWARDED"

#: An attribute of a record.
RECORD_FIELD = "RECORD_FIELD"

#: The return value of a call.
DERIVED = "DERIVED"

#: Any other expression.
COMPUTED = "COMPUTED"

#: The argument is not passed — the resolver's default applies.
DEFAULTED = "DEFAULTED"

#: Edit the call site; it already names its weight as a constant.
MECHANICAL = "MECHANICAL"

#: Build the field where the weight is built. No signature or type changes.
SITE_LOCAL = "SITE_LOCAL"

#: The enclosing function's signature has to carry the field too.
SIGNATURE = "SIGNATURE"

#: A record type has to carry the field, and every producer has to fill it.
DATA_MODEL = "DATA_MODEL"

#: Every argument form :func:`classify` can return. Declared rather than
#: discovered, for `RESOLVERS`' stated reason: a form merely omitted from a
#: derived scan is indistinguishable from one that does not occur.
#: `test_every_argument_form_has_a_cost_class` keeps it in step with
#: :data:`COST_CLASS`, so adding a form without pricing it fails.
FORMS: tuple[str, ...] = (
    LITERAL, LOCAL, FORWARDED, RECORD_FIELD, DERIVED, COMPUTED, DEFAULTED,
)

#: Argument form → the kind of work migrating it is.
COST_CLASS: dict[str, str] = {
    LITERAL: MECHANICAL,
    LOCAL: SITE_LOCAL,
    DERIVED: SITE_LOCAL,
    COMPUTED: SITE_LOCAL,
    DEFAULTED: SITE_LOCAL,
    FORWARDED: SIGNATURE,
    RECORD_FIELD: DATA_MODEL,
}


def cost_class(form: str) -> str:
    """The kind of work migrating an argument of this `form` implies."""
    try:
        return COST_CLASS[form]
    except KeyError:  # pragma: no cover - guarded by test
        raise LookupError(f"unclassified argument form: {form}") from None


def _resolver_fn(resolver: tuple[str, str]):
    return getattr(importlib.import_module(resolver[0]), resolver[1])


def weight_param(resolver: tuple[str, str]) -> str | None:
    """The `float`-annotated parameter of `resolver`, or None if it has none.

    That parameter is precisely what a cost field would replace, so reading it
    off the signature keeps this census correct through a rename. A resolver
    that already takes a cost field (`window_axis_key.lookup`) has nothing to
    migrate and returns None.
    """
    if grade_resolver(*resolver) == COST_FIELD:
        return None
    for name, p in inspect.signature(_resolver_fn(resolver)).parameters.items():
        ann = p.annotation
        text = ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))
        if "float" in str(text):
            return name
    return None


def scalar_resolvers() -> dict[tuple[str, str], str]:
    """Registered resolvers that still take a scalar, with their param name."""
    return {r: p for r in RESOLVERS if (p := weight_param(r)) is not None}


def _parameter_names(fn: ast.AST | None) -> frozenset[str]:
    if fn is None or not hasattr(fn, "args"):
        return frozenset()
    a = fn.args
    names = {x.arg for x in (*a.posonlyargs, *a.args, *a.kwonlyargs)}
    if a.vararg:
        names.add(a.vararg.arg)
    if a.kwarg:
        names.add(a.kwarg.arg)
    return frozenset(names)


def classify(arg: ast.expr | None, fn: ast.AST | None) -> str:
    """The argument form of `arg` passed inside `fn`."""
    if arg is None:
        return DEFAULTED
    if isinstance(arg, ast.Constant):
        return LITERAL
    if isinstance(arg, ast.Attribute):
        return RECORD_FIELD
    if isinstance(arg, ast.Name):
        return FORWARDED if arg.id in _parameter_names(fn) else LOCAL
    if isinstance(arg, ast.Call):
        return DERIVED
    return COMPUTED


@dataclass(frozen=True)
class Site:
    """One scalar-resolving call site, with the form of its weight argument."""

    path: str
    line: int
    function: str
    resolver: tuple[str, str]
    form: str

    @property
    def is_test(self) -> bool:
        return "/tests/" in self.path or Path(self.path).name.startswith("test_")

    @property
    def cost(self) -> str:
        return cost_class(self.form)

    def __str__(self) -> str:
        return (f"{self.path}:{self.line} {self.function}() "
                f"-> {self.resolver[0].rsplit('.', 1)[-1]}.{self.resolver[1]} "
                f":: {self.form} / {self.cost}")


def _weight_arg(node: ast.Call, resolver: tuple[str, str],
                param: str) -> ast.expr | None:
    for kw in node.keywords:
        if kw.arg == param:
            return kw.value
    order = list(inspect.signature(_resolver_fn(resolver)).parameters)
    i = order.index(param)
    return node.args[i] if i < len(node.args) else None


def sites(root: Path | None = None) -> tuple[Site, ...]:
    """Every scalar-resolver call site, graded by its weight argument's form.

    Mirrors `window_axis_reach.consumers` — same population, same exclusion of
    the resolvers' own definitions — but reads the argument rather than the
    signature. Sites that already resolve through a cost-field resolver are
    absent, because there is nothing to migrate at them.

    The exclusion is keyed on **every** registered resolver, not just the
    scalar ones. `window_axis_key.lookup` composes the axis check onto
    `lam_window_key.lookup` and so contains a scalar call in its own body;
    counting it would bill the migration for the one production function that
    already carries a cost field. It is the mirror of the trap
    `window_axis_reach.consumers` names — there, including a definition made
    the index look axis-*aware*; here it would make the cost look larger.
    """
    targets = scalar_resolvers()
    definitions = frozenset(RESOLVERS)
    out: list[Site] = []
    for path, (_src, tree, modname) in _sources(root).items():
        names, alias = _import_maps(tree, modname)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = _target(node, names, alias)
            if target not in targets:
                continue
            fn = _enclosing(tree, node)
            if (modname, getattr(fn, "name", None)) in definitions:
                continue                      # the resolver's own definition
            out.append(Site(
                path=path.relative_to(root or REPO_ROOT).as_posix(),
                line=node.lineno,
                function=getattr(fn, "name", "<module>"),
                resolver=target,
                form=classify(_weight_arg(node, target, targets[target]), fn)))
    return tuple(sorted(out, key=lambda s: (s.path, s.line)))


@dataclass(frozen=True)
class Partition:
    """Q-157's requested count, split the way the costs actually split."""

    production: tuple[Site, ...]
    test: tuple[Site, ...]

    @property
    def total(self) -> int:
        return len(self.production) + len(self.test)

    def forms(self, *, test: bool) -> Counter:
        return Counter(s.form for s in (self.test if test else self.production))

    def costs(self, *, test: bool) -> Counter:
        return Counter(s.cost for s in (self.test if test else self.production))

    @property
    def mechanical_production(self) -> tuple[Site, ...]:
        return tuple(s for s in self.production if s.cost == MECHANICAL)

    @property
    def data_model_production(self) -> tuple[Site, ...]:
        return tuple(s for s in self.production if s.cost == DATA_MODEL)


def partition(root: Path | None = None) -> Partition:
    """Split :func:`sites` into production and test."""
    all_sites = sites(root)
    return Partition(
        production=tuple(s for s in all_sites if not s.is_test),
        test=tuple(s for s in all_sites if s.is_test))


def report(root: Path | None = None) -> str:
    """Human-readable partition — the artifact Q-157's next action asked for."""
    p = partition(root)
    lines = [
        f"window_axis_migration — {p.total} scalar-resolving call sites",
        f"  production {len(p.production)}: "
        f"{dict(sorted(p.forms(test=False).items()))}",
        f"    by cost:   {dict(sorted(p.costs(test=False).items()))}",
        f"  test       {len(p.test)}: {dict(sorted(p.forms(test=True).items()))}",
        f"    by cost:   {dict(sorted(p.costs(test=True).items()))}",
        "",
        "  production sites requiring a data-model change:",
    ]
    lines.extend(f"    {s}" for s in p.data_model_production)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(report())
