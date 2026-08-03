"""Does a guard's clean reading survive the failure it was built for? (Q-063, STATE #1/#2)

D-047 found :func:`tree_provenance.undeclared_drift` unable to see a violation
of the rule it enforces.  It compares the worktree against ``HEAD`` and exempts
the five declared local-only paths, so **staging** a snapshot file removes the
drift it looks for *and* the path sits on its allow-list.  The instrument reads
cleanest at the moment the rule breaks.

Q-063 asks that of the whole suite, and leans **(b)**: a structural pass rather
than injecting a failure per guard by hand, because the blind spot was
expressible as one predicate — *allow-list ∩ watched surface* — and a shape that
exists once usually exists twice.  Hand-injecting failures would also reproduce
D-046's own defect one level up: the failures worth injecting are the ones
nobody thought of.

Two properties, and they are not the same question
--------------------------------------------------

**Revocability** (Q-063's half).  A guard whose population is a *difference
between two observations* can be emptied by making the two observations agree.
If the forbidden act is what makes them agree, the guard goes **quieter** as the
violation lands.  A guard whose population is an *enumeration* (``git
ls-files``, a document scan) cannot be silenced that way — the offending item is
still there to be listed.  So ``DIFFERENCE`` populations are the ones that need
a mirror, and ``ENUMERATION`` ones do not.

**Bite** (STATE #2's half, D-046's shape).  An exemption that currently removes
*nothing* from its population is a filter whose place is held by coincidence.
D-046 found exactly one — ``_sites_from_claim_scope`` lacked a ``kind`` filter
and nothing revealed it, because every citation on that claim happened to be
``other-quantity``.  An inert exemption is not a bug on its own; it is the state
in which a bug is undetectable, which is why it is reported rather than pruned.

Both are computed over a population this module does **not** type out.  Guards
are discovered by globbing the package and asking the AST which public functions
filter a population against a set — D-045's lesson, applied to the registry of
registries.  A hand-written list of guards would be the fifth consecutive
hand-written list to come up short.

What "exemption provenance" adds
--------------------------------

Each exemption is tagged ``TYPED`` (the filter set is a module constant someone
wrote by hand) or ``DERIVED`` (it is computed).  Three consecutive cycles found
a ``TYPED`` set short — D-045 the excluded surfaces, D-046 the citation list,
D-047 the push guard's copy of it.  ``DERIVED`` exemptions have failed
differently and less often, so the tag is the prior, not a verdict.

Fast half: pure AST plus a bounded number of guard calls.  No simulation.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent

#: Populations that are a difference between two observations of the same
#: object.  Detected structurally; the vocabulary is only for the *name-based*
#: half (a call named like a diff), and any two-call set operation is caught
#: without it.
_DIFF_NAMES = ("diff", "drift", "delta", "compare", "changed")

#: A ``Sub`` between numbers is arithmetic, not an exemption.  A constant is
#: treated as set-valued only if its module-level initializer is a collection
#: display or a collection call.
_SET_CALLS = ("set", "frozenset", "sorted", "tuple", "list", "dict")

SENSE_SUB = "SUB"
SENSE_NOT_IN = "NOT_IN"
SENSE_IN = "IN"

KIND_DIFFERENCE = "DIFFERENCE"
KIND_ENUMERATION = "ENUMERATION"

PROV_TYPED = "TYPED"
PROV_DERIVED = "DERIVED"
PROV_PARAMETER = "PARAMETER"
#: A collection display written at the filter site itself — ``if k in ('a',
#: 'b')``.  Set-valued, and structurally a filter, but not a *registry*: there
#: is no second statement of it that could go short, which is the failure mode
#: every one of D-045/D-046/D-047 turned on.  Tagged rather than dropped,
#: because "excluded with a reason" is the standing rule (D-038).
PROV_INLINE = "INLINE"


class GuardScanError(RuntimeError):
    """The scan could not resolve something it must not silently skip."""


@dataclass(frozen=True)
class Exemption:
    """A set-valued expression used to remove members from a guard's population."""

    expr: str
    sense: str
    provenance: str
    constant: str | None = None
    key: str = ""


@dataclass(frozen=True)
class Guard:
    """A public function that reports violations after filtering a population."""

    module: str
    name: str
    lineno: int
    population: str
    population_kind: str
    exemptions: tuple[Exemption, ...] = field(default_factory=tuple)
    population_key: str = ""

    @property
    def qualname(self) -> str:
        return f"{self.module}.{self.name}"

    @property
    def typed_exemptions(self) -> tuple[Exemption, ...]:
        return tuple(e for e in self.exemptions if e.provenance == PROV_TYPED)


def core_name(expr: ast.expr) -> str:
    """The accessor a set-valued expression is *about*, independent of spelling.

    Mirror detection compares one guard's population against another's
    exemption, and the two are almost never written the same way:
    ``unregistered_citations`` filters ``derived_citations(root)`` against a
    set **comprehension over** ``COINCIDENTAL``, while ``stale_coincidences``
    iterates a generator **over** ``COINCIDENTAL`` and filters against a set
    comprehension over ``derived_citations(root)``.  The pair is a textbook
    mirror and a string comparison sees four unrelated expressions.

    The first draft of this module compared unparsed source and found **one**
    mirror where there are three — the fifth consecutive cycle whose first-draft
    scan was wrong about its own population, and again in the direction that
    *deletes* evidence: an undetected mirror promotes a sound guard into
    Q-063's answer set.
    """
    if isinstance(expr, (ast.SetComp, ast.ListComp, ast.GeneratorExp, ast.DictComp)):
        if expr.generators:
            return core_name(expr.generators[0].iter)
        return ast.unparse(expr)
    if isinstance(expr, ast.Call):
        name = _callee_name(expr)
        if name in _SET_CALLS and expr.args:
            return core_name(expr.args[0])
        return name or ast.unparse(expr)
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    if isinstance(expr, ast.Subscript):
        return core_name(expr.value)
    return ast.unparse(expr)


# --------------------------------------------------------------------------
# module scanning
# --------------------------------------------------------------------------


def package_modules(package: Path | None = None) -> tuple[Path, ...]:
    """Every module in the sandbox package, globbed rather than typed (D-045)."""
    base = package or PACKAGE
    return tuple(sorted(p for p in base.glob("*.py") if p.name != "__init__.py"))


def _set_valued_constants(tree: ast.Module) -> dict[str, ast.expr]:
    """Module-level UPPER names whose initializer is a collection."""
    out: dict[str, ast.expr] = {}
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        for tgt in targets:
            if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                continue
            if isinstance(value, (ast.Set, ast.Tuple, ast.List, ast.Dict)):
                out[tgt.id] = value
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name) \
                    and value.func.id in _SET_CALLS:
                out[tgt.id] = value
    return out


def _imported_upper(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                local = alias.asname or alias.name
                if local.isupper():
                    names.add(local)
    return names


def _aliases(fn: ast.FunctionDef) -> dict[str, ast.expr]:
    """Local ``name = expr`` bindings, so a filter through an alias resolves.

    ``undeclared_drift`` binds ``allow = DECLARED_LOCAL_ONLY if declared is None
    else declared`` and then filters ``p not in allow``.  A scan that only looks
    for a constant in the ``in`` position misses it — the first draft of this
    module did, and reported the very guard Q-063 was written about as having no
    exemption at all.
    """
    out: dict[str, ast.expr] = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.setdefault(node.targets[0].id, node.value)
    return out


def _resolve(expr: ast.expr, aliases: dict[str, ast.expr], depth: int = 3) -> ast.expr:
    if depth <= 0:
        return expr
    if isinstance(expr, ast.Name) and expr.id in aliases:
        return _resolve(aliases[expr.id], aliases, depth - 1)
    if isinstance(expr, ast.IfExp):
        # `A if cond else B` — the default arm is the one the guard ships with.
        return _resolve(expr.body, aliases, depth - 1)
    return expr


def _provenance(expr: ast.expr, consts: dict[str, ast.expr], imported: set[str],
                params: set[str]) -> tuple[str, str | None]:
    names = [n.id for n in ast.walk(expr) if isinstance(n, ast.Name)]
    typed = [n for n in names if n in consts or n in imported]
    has_call = any(isinstance(n, ast.Call) for n in ast.walk(expr))
    if not typed and not has_call and isinstance(expr, (ast.Set, ast.Tuple, ast.List, ast.Dict)):
        return PROV_INLINE, None
    if typed and not has_call:
        return PROV_TYPED, typed[0]
    if typed and has_call:
        # e.g. `set(DECLARED_LOCAL_ONLY)` — still a hand-typed registry.
        callees = [n.func.id for n in ast.walk(expr)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        if all(c in _SET_CALLS for c in callees):
            return PROV_TYPED, typed[0]
        return PROV_DERIVED, typed[0]
    if has_call:
        return PROV_DERIVED, None
    if any(n in params for n in names):
        return PROV_PARAMETER, None
    return PROV_DERIVED, None


def _is_set_valued(expr: ast.expr, consts: dict[str, ast.expr],
                   imported: set[str]) -> bool:
    if isinstance(expr, (ast.Set, ast.List, ast.Tuple, ast.Dict, ast.SetComp,
                         ast.ListComp, ast.DictComp, ast.GeneratorExp)):
        return True
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) \
            and expr.func.id in _SET_CALLS:
        return True
    if isinstance(expr, ast.Name) and (expr.id in consts or expr.id in imported):
        return True
    if isinstance(expr, ast.Constant):
        return False
    return False


def _difference_kind(expr: ast.expr, module_fns: dict[str, ast.FunctionDef],
                     src: str, depth: int = 2) -> str:
    """``DIFFERENCE`` when the population is two observations compared.

    Two routes, deliberately both structural: a set operation whose *both*
    operands are calls (two observations of the same object), or a call into a
    same-module function that itself does one — the ``_diff(committed,
    worktree)`` case, where the comparison is one frame down.  The name-based
    fallback (:data:`_DIFF_NAMES`) exists only for shell-outs like ``git diff``,
    whose comparison is not in the AST at all.
    """
    for node in ast.walk(expr):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Sub, ast.BitAnd, ast.BitXor)):
            if isinstance(_unwrap(node.left), ast.Call) and isinstance(_unwrap(node.right), ast.Call):
                return KIND_DIFFERENCE
    for node in ast.walk(expr):
        if isinstance(node, ast.Call):
            name = _callee_name(node)
            if name is None:
                continue
            if any(tok in name.lower() for tok in _DIFF_NAMES):
                return KIND_DIFFERENCE
            if depth > 0 and name in module_fns:
                inner = module_fns[name]
                for sub in ast.walk(inner):
                    if isinstance(sub, (ast.Return, ast.Assign)) and getattr(sub, "value", None) is not None:
                        if _difference_kind(sub.value, module_fns, src, depth - 1) == KIND_DIFFERENCE:
                            return KIND_DIFFERENCE
                if _shells_out_to_git_diff(inner):
                    return KIND_DIFFERENCE
    if _has_git_diff_literal(expr):
        return KIND_DIFFERENCE
    return KIND_ENUMERATION


def _has_git_diff_literal(node: ast.AST) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                and sub.value.strip() == "diff":
            return True
    return False


def _shells_out_to_git_diff(fn: ast.FunctionDef) -> bool:
    return _has_git_diff_literal(fn)


def _unwrap(expr: ast.expr) -> ast.expr:
    while isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) \
            and expr.func.id in _SET_CALLS and expr.args:
        expr = expr.args[0]
    return expr


def _callee_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _enclosing_population(fn: ast.FunctionDef, target: ast.AST) -> ast.expr | None:
    """The iterable the filter site removes members from."""
    best: ast.expr | None = None
    for node in ast.walk(fn):
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            if any(t is target for t in ast.walk(node)):
                if node.generators:
                    best = node.generators[0].iter
        elif isinstance(node, ast.For):
            if any(t is target for t in ast.walk(node)):
                best = node.iter
    return best


def _guards_in(path: Path) -> list[Guard]:
    src = path.read_text()
    tree = ast.parse(src)
    consts = _set_valued_constants(tree)
    imported = _imported_upper(tree)
    module_fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    out: list[Guard] = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name.startswith("_"):
            continue
        aliases = _aliases(fn)
        params = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
        exemptions: list[Exemption] = []
        populations: list[ast.expr] = []

        for node in ast.walk(fn):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
                left, right = _resolve(node.left, aliases), _resolve(node.right, aliases)
                if not (_is_set_valued(left, consts, imported)
                        and _is_set_valued(right, consts, imported)):
                    continue
                prov, const = _provenance(right, consts, imported, params)
                exemptions.append(Exemption(ast.unparse(right), SENSE_SUB, prov, const,
                                            core_name(right)))
                populations.append(node.left)
            elif isinstance(node, ast.Compare) and len(node.ops) == 1 \
                    and isinstance(node.ops[0], (ast.In, ast.NotIn)):
                container = _resolve(node.comparators[0], aliases)
                if not _is_set_valued(container, consts, imported):
                    continue
                sense = SENSE_NOT_IN if isinstance(node.ops[0], ast.NotIn) else SENSE_IN
                prov, const = _provenance(container, consts, imported, params)
                pop = _enclosing_population(fn, node)
                if pop is None:
                    # A membership test with nothing being iterated is a
                    # *dispatch* (`if key in ('a', 'b'): ...`), not a filter
                    # over a population.  Admitting these put `run.main` and
                    # `dispatch_fingerprint` in the guard pool on the first
                    # draft — six false guards whose "exemption" removes no
                    # member of anything.
                    continue
                exemptions.append(Exemption(ast.unparse(container), sense, prov, const,
                                            core_name(container)))
                populations.append(pop)

        if not exemptions or not populations:
            continue
        pop_expr = populations[0]
        resolved_pop = _resolve(pop_expr, aliases)
        kind = _difference_kind(resolved_pop, module_fns, src)
        if kind == KIND_ENUMERATION:
            # the population may be bound earlier in the body than the filter
            for alias_expr in aliases.values():
                if _difference_kind(alias_expr, module_fns, src) == KIND_DIFFERENCE:
                    resolved_pop, kind = alias_expr, KIND_DIFFERENCE
                    break
        out.append(Guard(
            module=path.stem,
            name=fn.name,
            lineno=fn.lineno,
            population=ast.unparse(resolved_pop),
            population_kind=kind,
            exemptions=tuple(dict.fromkeys(exemptions)),
            population_key=core_name(resolved_pop),
        ))
    return out


def guards(package: Path | None = None) -> tuple[Guard, ...]:
    """Every public function in the package that filters a population by a set."""
    out: list[Guard] = []
    for path in package_modules(package):
        out.extend(_guards_in(path))
    return tuple(out)


# --------------------------------------------------------------------------
# the two questions
# --------------------------------------------------------------------------


def mirrors(pool: Iterable[Guard] | None = None) -> tuple[tuple[str, str], ...]:
    """Guard pairs that read the same two sets in opposite directions.

    ``unregistered_local_only`` (derived − declared) and
    ``underived_declarations`` (declared − derived) are a mirror: neither can
    go quietly short, because a miss on one side is a hit on the other.  A
    ``DIFFERENCE`` guard *without* one is where Q-063's failure lives.
    """
    pool = tuple(pool if pool is not None else guards())
    found: set[tuple[str, str]] = set()
    for a in pool:
        for b in pool:
            if a.qualname >= b.qualname or a.module != b.module:
                continue
            a_ex = {e.key for e in a.exemptions}
            b_ex = {e.key for e in b.exemptions}
            if a.population_key in b_ex and b.population_key in a_ex:
                found.add((a.qualname, b.qualname))
    return tuple(sorted(found))


def exemption_watchers(pool: Iterable[Guard] | None = None) -> dict[str, tuple[str, ...]]:
    """For each ``TYPED`` exemption set, the guards whose *population* it is.

    :func:`mirrors` asks a same-module, role-swapped question and therefore
    misses the cover D-047 actually shipped: ``local_only_audit`` watches
    ``DECLARED_LOCAL_ONLY`` while ``tree_provenance`` is the module that exempts
    it, and the new ``staged_declarations`` intersects the set rather than
    filtering by it.  The general form of "who is watching the allow-list" is
    cross-module and does not involve role-swapping at all: an allow-list is
    covered when *someone's population is that list*.
    """
    pool = tuple(pool if pool is not None else guards())
    by_population: dict[str, list[str]] = {}
    for g in pool:
        by_population.setdefault(g.population_key, []).append(g.qualname)
    out: dict[str, tuple[str, ...]] = {}
    for g in pool:
        for e in g.typed_exemptions:
            watchers = [w for w in by_population.get(e.key, []) if w != g.qualname]
            out.setdefault(e.key, tuple(sorted(watchers)))
    return out


def unwatched_exemptions(pool: Iterable[Guard] | None = None) -> tuple[str, ...]:
    """``TYPED`` allow-lists that no guard's population is.

    Coverage here is coverage *by existence*, not by act — and the distinction
    is the second half of D-047.  ``DECLARED_LOCAL_ONLY`` had two watchers
    before D-047 (``stale_declarations`` for tracked-ness,
    ``underived_declarations`` for re-derivability) and **both read clean while
    the rule was being broken**, because neither watched *staging*.  So a
    non-empty result here is a hole, and an empty one is not a clearance.

    **Module layer only.**  The scan surface is the package's own modules, so
    "no watcher" means no *module-level* function enumerates the list — it does
    not mean nothing checks it.  All three currently-unwatched lists are named
    in ``tests/``, and ``SCOPED_CLAIMS`` is compared against
    :func:`claim_scope.instrumented_claims` there rather than in a module
    function.  :func:`test_layer_mentions` reports that second layer instead of
    letting this one imply its absence, per D-038: an exclusion stated is
    auditable, an exclusion implied is a hole.
    """
    return tuple(sorted(k for k, v in exemption_watchers(pool).items() if not v))


def test_layer_mentions(package: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Test modules naming each ``TYPED`` allow-list — the layer :func:`guards` cannot see.

    A mention is not a check.  This exists so that :func:`unwatched_exemptions`
    is read as "no module-level watcher" rather than "unchecked", which is a
    materially different and much stronger claim.
    """
    base = (package or PACKAGE) / "tests"
    keys = set(exemption_watchers())
    out: dict[str, tuple[str, ...]] = {k: () for k in keys}
    if not base.is_dir():
        return out
    for path in sorted(base.glob("test_*.py")):
        text = path.read_text()
        for key in keys:
            if key in text:
                out[key] = out[key] + (path.name,)
    return out


def revocable(pool: Iterable[Guard] | None = None) -> tuple[Guard, ...]:
    """Guards whose population is a difference the offender can collapse."""
    pool = tuple(pool if pool is not None else guards())
    return tuple(g for g in pool if g.population_kind == KIND_DIFFERENCE)


def unmirrored_revocable(pool: Iterable[Guard] | None = None) -> tuple[Guard, ...]:
    """Q-063 (b)'s answer: revocable + exempting + no mirror to catch the collapse.

    Non-empty means a guard that, at the moment its rule is broken in the way
    that matters, reads *cleaner* than it did before — and nothing else in its
    module reads the same pair of sets from the other side.
    """
    pool = tuple(pool if pool is not None else guards())
    paired = {name for pair in mirrors(pool) for name in pair}
    return tuple(g for g in revocable(pool)
                 if g.exemptions and g.qualname not in paired)


# --------------------------------------------------------------------------
# bite (STATE #2 / D-046's coincidence shape)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bite:
    """Runtime reading of whether an exemption currently removes anything."""

    guard: str
    exemption: str
    population_size: int
    exempt_size: int
    overlap: int

    @property
    def verdict(self) -> str:
        if self.population_size == 0:
            return "VACUOUS"
        if self.overlap == 0:
            return "INERT"
        if self.overlap == self.population_size:
            return "TOTAL"
        return "BITES"


def bite(guard_name: str, population: Iterable, exempt: Iterable,
         exemption_name: str = "") -> Bite:
    """Score one exemption against the population it filters.

    Callers supply the two sets because a general evaluator would have to
    execute arbitrary guard internals; the *pairing* is what this module
    derives, and :func:`unbitten` asserts the derived pairs are all scored.
    """
    pop = set(population)
    ex = set(exempt)
    return Bite(guard=guard_name, exemption=exemption_name,
                population_size=len(pop), exempt_size=len(ex),
                overlap=len(pop & ex))


def unbitten(scored: Iterable[Bite], pool: Iterable[Guard] | None = None) -> tuple[str, ...]:
    """Derived (guard, exemption) pairs with a ``TYPED`` set that nobody scored.

    The mirror of :func:`bite`, for the same reason ``underived_declarations``
    exists: an unscored pair is indistinguishable from a pair that scored clean.
    Only ``TYPED`` exemptions are required — a derived exemption cannot go
    short by omission, which is the failure mode the score is looking for.
    """
    pool = tuple(pool if pool is not None else guards())
    have = {(b.guard, b.exemption) for b in scored}
    missing = []
    for g in pool:
        for e in g.typed_exemptions:
            if (g.qualname, e.constant or e.key) not in have:
                missing.append(f"{g.qualname} ~ {e.constant or e.key}")
    return tuple(sorted(set(missing)))


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def report(package: Path | None = None) -> str:
    pool = guards(package)
    lines = [
        f"guards discovered: {len(pool)} over {len(package_modules(package))} modules",
        f"  DIFFERENCE populations : {len(revocable(pool))}",
        f"  ENUMERATION populations: {len(pool) - len(revocable(pool))}",
        f"  TYPED exemptions       : {sum(len(g.typed_exemptions) for g in pool)}"
        f" / {sum(len(g.exemptions) for g in pool)}",
        "",
        "mirrored pairs:",
    ]
    for a, b in mirrors(pool):
        lines.append(f"  {a}  <->  {b}")
    if not mirrors(pool):
        lines.append("  (none)")
    lines += ["", "TYPED allow-lists and who watches them:"]
    for key, watchers in sorted(exemption_watchers(pool).items()):
        lines.append(f"  {key}: {', '.join(watchers) if watchers else '(nobody)'}")
    lines += ["", "revocable and unmirrored (Q-063):"]
    for g in unmirrored_revocable(pool):
        ex = ", ".join(f"{e.expr} [{e.provenance}]" for e in g.exemptions)
        lines.append(f"  {g.qualname}:{g.lineno}")
        lines.append(f"      population: {g.population}")
        lines.append(f"      exempts   : {ex}")
    if not unmirrored_revocable(pool):
        lines.append("  (none)")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
