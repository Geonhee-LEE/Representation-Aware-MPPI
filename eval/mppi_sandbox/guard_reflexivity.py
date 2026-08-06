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
#: ``observed & REGISTRY`` — a filter written the other way round.  D-048's
#: scan read ``-``, ``in`` and ``not in`` and therefore **could not see
#: ``local_only_audit.staged_declarations``**, the guard D-047 had shipped one
#: cycle earlier to close D-011's hole.  A population selected *down to* a
#: registry is filtered by it as surely as one with the registry removed; the
#: two spellings differ only in which side survives.
SENSE_AND = "AND"

KIND_DIFFERENCE = "DIFFERENCE"
KIND_ENUMERATION = "ENUMERATION"

#: What the guard hands back.  A ``COLLECTION`` reading can be asked *does it
#: name this offence*; a ``SCALAR`` one cannot, because it has no members.  The
#: distinction is deliberately **not** a filter on :func:`guards` — the pool is a
#: count of visible *spellings* (D-072/D-073) and dropping members would rewrite
#: thirty-three cycles of census provenance.  It exists because the *probe
#: obligation* (:mod:`guard_direction`) needs a narrower population than the
#: census does, and inheriting the census's is what left it demanding an
#: executed direction reading from a function that renders a string.
READING_COLLECTION = "COLLECTION"
READING_SCALAR = "SCALAR"

#: Return annotations with no members.  Read off the annotation rather than
#: inferred from the body, so the answer is the one the author declared.
_SCALAR_ANNOTATIONS = frozenset({"str", "int", "float", "bool", "bytes"})

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
    reading: str = READING_COLLECTION
    """:data:`READING_COLLECTION` or :data:`READING_SCALAR` — see the constants."""

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
    """Where the exemption's set came from — a **syntactic** question, on purpose.

    Q-067, resolved by D-052 to option (b): this predicate does **not** follow a
    same-module call, and that is a decision rather than the omission D-050 found
    in :func:`_is_set_valued`.  The two predicates are asked different questions
    and only one of the answers survives a frame change.

    ``_is_set_valued`` asks *is this a collection* — a property of the value, so
    following ``_helper()`` into its ``return`` is simply reading the same fact
    at the place it is written, and D-050's finding was that not following it
    **deleted a guard**.  ``_provenance`` asks *is this exemption a hand-typed
    registry* — a property of **this call site**, and it does not survive the
    frame: a population that is genuinely derived (``glob`` → ``set``) but happens
    to route through a typed constant one frame down would be re-labelled
    ``TYPED``, which is the false direction for a screen whose whole job is to
    find registries nobody derives.  Following would trade a known, currently
    empty exposure for an unbounded one.

    The cost of (b) is real and is stated rather than hidden:
    :func:`predicate_depth.provenance_depth_exposure` counts exemptions that are
    ``DERIVED`` here but reach a typed registry one call down, and every such
    exemption is invisible to :attr:`Guard.typed_exemptions`, :func:`bite`,
    :func:`unwatched_exemptions` **and** :mod:`exemption_masking`'s screen.  It
    reads ``()`` at ``HEAD``.  When it goes positive — and D-050's prescribed
    "extract the duplicated registry behind a helper" refactor is exactly the
    edit that does it — the required action is to **name the helper's registry at
    the call site** (pass it, or alias it to a module constant), not to widen
    this predicate.  That keeps provenance answerable where it is asked.
    """
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


def _reading_kind(fn: ast.FunctionDef) -> str:
    """Does this function's declared return have members?

    ``X | None`` is read through to ``X``: an optional scalar is still a scalar,
    and that is the one shape (``str | None``) where unparsing the whole
    annotation would answer wrongly.  An **unannotated** function is treated as
    a collection — the conservative direction, because the cost of a wrong
    ``COLLECTION`` is a probe somebody has to write and the cost of a wrong
    ``SCALAR`` is an obligation silently dropped, which is D-045's failure mode.
    """
    if fn.returns is None:
        return READING_COLLECTION
    node = fn.returns
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        parts = [node.left, node.right]
    else:
        parts = [node]
    named = {ast.unparse(p) for p in parts} - {"None"}
    if named and named <= _SCALAR_ANNOTATIONS:
        return READING_SCALAR
    return READING_COLLECTION


def _returns_set_valued(fn: ast.FunctionDef, consts: dict[str, ast.expr],
                        imported: set[str], module_fns: dict[str, ast.FunctionDef],
                        depth: int) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and node.value is not None:
            if _is_set_valued(node.value, consts, imported, module_fns, depth):
                return True
    return False


def _is_set_valued(expr: ast.expr, consts: dict[str, ast.expr],
                   imported: set[str],
                   module_fns: dict[str, ast.FunctionDef] | None = None,
                   depth: int = 2) -> bool:
    """Is *expr* a collection this scan can treat as a population or a filter?

    The same-module call arm (``module_fns``) is D-050's fix and its absence was
    the finding.  :func:`_difference_kind` has followed a call into its own
    module's source since it was written; this predicate did not, so the two
    resolved *the same expression* at two different depths.  The consequence was
    not a mis-ranking, it was a **deletion**: extracting ``staged_changes`` out
    of ``staged_declarations`` — a refactor that removes a duplicated statement,
    which is precisely the remedy D-045 through D-049 kept prescribing — turned
    the surviving one-liner's left operand into a bare call, failed this test,
    skipped the ``BitAnd`` arm, and dropped the guard out of the guard registry
    entirely.  Not downgraded.  Absent.
    """
    if isinstance(expr, (ast.Set, ast.List, ast.Tuple, ast.Dict, ast.SetComp,
                         ast.ListComp, ast.DictComp, ast.GeneratorExp)):
        return True
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        if expr.func.id in _SET_CALLS:
            return True
        if module_fns and depth > 0 and expr.func.id in module_fns:
            return _returns_set_valued(module_fns[expr.func.id], consts, imported,
                                       module_fns, depth - 1)
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
                if not (_is_set_valued(left, consts, imported, module_fns)
                        and _is_set_valued(right, consts, imported, module_fns)):
                    continue
                prov, const = _provenance(right, consts, imported, params)
                exemptions.append(Exemption(ast.unparse(right), SENSE_SUB, prov, const,
                                            core_name(right)))
                populations.append(node.left)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitAnd):
                left, right = _resolve(node.left, aliases), _resolve(node.right, aliases)
                if not (_is_set_valued(left, consts, imported, module_fns)
                        and _is_set_valued(right, consts, imported, module_fns)):
                    continue
                # The registry is whichever side is a named set; the other is
                # the observation being narrowed to it.  When both are named,
                # the right side is the filter, matching ``Sub``'s convention.
                r_prov, r_const = _provenance(right, consts, imported, params)
                l_prov, l_const = _provenance(left, consts, imported, params)
                if r_prov == PROV_TYPED or l_prov != PROV_TYPED:
                    filt, pop, prov, const = right, node.left, r_prov, r_const
                else:
                    filt, pop, prov, const = left, node.right, l_prov, l_const
                exemptions.append(Exemption(ast.unparse(filt), SENSE_AND, prov, const,
                                            core_name(filt)))
                populations.append(pop)
            elif isinstance(node, ast.Compare) and len(node.ops) == 1 \
                    and isinstance(node.ops[0], (ast.In, ast.NotIn)):
                container = _resolve(node.comparators[0], aliases)
                if not _is_set_valued(container, consts, imported, module_fns):
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
            reading=_reading_kind(fn),
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


def scalar_readings(pool: Iterable[Guard] | None = None) -> tuple[Guard, ...]:
    """Guards that hand back a value with no members — renderers and graders.

    Published rather than quietly dropped, per D-038: an exclusion nobody can
    count is the shape D-045/D-046/D-047 each found.  Nothing here is removed
    from :func:`guards`; this is the set :func:`revocable_collections` subtracts
    and the number a reader can check it against.
    """
    pool = tuple(pool if pool is not None else guards())
    return tuple(g for g in pool if g.reading == READING_SCALAR)


def revocable_collections(pool: Iterable[Guard] | None = None) -> tuple[Guard, ...]:
    """:func:`revocable`, minus the guards whose reading has no members.

    The population an **executed** direction reading can be demanded of.
    :func:`revocable` answers a question about the population's *shape* and is
    right to include a renderer whose counts come from a difference; asking that
    renderer whether it "names the offence" is a category error, because a
    string names nothing in the sense the probe means.  Recovering the
    population by parsing the rendered text would be a second statement of the
    rule, which is the failure D-045 and D-047 are both instances of.
    """
    pool = tuple(pool if pool is not None else guards())
    return tuple(g for g in revocable(pool) if g.reading == READING_COLLECTION)


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
# Q-064: the acts, not the sets
# --------------------------------------------------------------------------
#
# D-048's finding was that ``DECLARED_LOCAL_ONLY`` had *more watchers than any
# other allow-list* and stayed broken for ~30 cycles anyway, because both
# watchers observed the wrong verb.  :func:`exemption_watchers` counts watchers;
# it cannot see that two of them look through the same window.  What follows
# counts **windows**.
#
# A guard observes the repository through a bounded vocabulary of acts — git
# subcommands and filesystem reads — and each act has a *scope*: the state a
# change must reach before that act can see it.  The scopes are derived from
# the invocation's own literal arguments, never declared per guard.

#: The state a change must reach before an act can observe it.  Ordered by how
#: late in the write path the change becomes visible.
SCOPE_WORKTREE = "WORKTREE"
SCOPE_INDEX = "INDEX"
SCOPE_COMMIT = "COMMIT"
#: Sees the *set of paths* git is tracking, not their content.  Index-backed,
#: so it notices a newly ``git add``-ed **path**, and is blind to a
#: modification of a path already tracked.  That blindness is exactly why
#: ``stale_declarations`` read clean through D-047: every snapshot file was
#: already tracked, so the violating edit never changed the name set.
SCOPE_NAMESET = "NAMESET"
SCOPE_UNKNOWN = "UNKNOWN"

#: git subcommands that can only report committed state.
_COMMIT_VERBS = ("log", "ls-tree", "cat-file", "show", "rev-parse", "rev-list",
                 "merge-base")
#: git subcommands that report path *names* rather than content.
_NAMESET_VERBS = ("ls-files", "for-each-ref", "branch", "ls-remote")
#: ``Path`` accessors that read the working tree.
_FS_VERBS = ("read_text", "read_bytes", "open", "glob", "rglob", "iterdir",
             "exists", "is_file", "is_dir", "stat")


@dataclass(frozen=True)
class Act:
    """One observation a guard makes, and the state it can observe."""

    tool: str
    verb: str
    scope: str
    site: str
    spelling: str = ""

    @property
    def key(self) -> str:
        return f"{self.tool}:{self.verb}"


def _git_scope(args: tuple[str, ...]) -> str:
    """Scope of a git invocation, from its own literal arguments."""
    if not args:
        return SCOPE_UNKNOWN
    verb, rest = args[0], args[1:]
    if verb in ("diff", "diff-index", "diff-files", "status", "stash"):
        if any(a in ("--cached", "--staged") for a in rest):
            return SCOPE_INDEX
        # A ref range (``a..b`` / ``a...b``) makes diff a commit-vs-commit
        # question; a bare ref leaves the worktree on one side.
        if any(".." in a for a in rest if not a.startswith("-")):
            return SCOPE_COMMIT
        return SCOPE_WORKTREE
    if verb in _COMMIT_VERBS:
        return SCOPE_COMMIT
    if verb in _NAMESET_VERBS:
        # ``--others`` lists untracked files, which exist only in the worktree.
        if any(a == "--others" for a in rest):
            return SCOPE_WORKTREE
        return SCOPE_NAMESET
    return SCOPE_UNKNOWN


def _literal_args(call: ast.Call, local_lists: dict[str, list[str]]) -> tuple[str, ...]:
    """String literals a call passes, resolving ``*args`` bound to a local list.

    ``_committed_on_branches`` builds ``args = ["log", "--name-only", ...]`` and
    splats it; reading only direct ``Constant`` arguments would score that act
    ``UNKNOWN`` and silently drop a ``COMMIT`` observation.
    """
    out: list[str] = []
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            out.append(arg.value)
        elif isinstance(arg, ast.Starred) and isinstance(arg.value, ast.Name):
            out.extend(local_lists.get(arg.value.id, []))
        elif isinstance(arg, ast.JoinedStr):
            # f"origin/main...{ref}" — the literal halves carry the range marker
            out.append("".join(v.value for v in arg.values
                               if isinstance(v, ast.Constant) and isinstance(v.value, str)))
    return tuple(out)


def _local_string_lists(fn: ast.FunctionDef) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, (ast.List, ast.Tuple)):
            vals = [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if vals:
                out[node.targets[0].id] = vals
    return out


def _acts_in_body(fn: ast.FunctionDef, module: str) -> list[Act]:
    """Acts performed directly in one function body."""
    local_lists = _local_string_lists(fn)
    out: list[Act] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        callee = _callee_name(node)
        site = f"{module}:{node.lineno}"
        if callee == "_git":
            args = _literal_args(node, local_lists)
            out.append(Act("git", args[0] if args else "?", _git_scope(args), site,
                           " ".join(args)))
        elif callee in ("run", "check_output", "Popen") and node.args:
            first = _unwrap_seq(node.args[0])
            if first and first[0] == "git":
                args = tuple(a for a in first[1:] if a != "-C")
                # ``subprocess.run(("git", *args))`` inside ``_git`` is the
                # *dispatcher*, not an observation — it names no subcommand, so
                # it has no scope.  Counting it gave every git-touching guard a
                # phantom ``UNKNOWN`` act, which is D-048's "filter site with no
                # population" one layer down: a call that decides nothing.
                if args and args[0] != "*":
                    out.append(Act("git", args[0], _git_scope(args), site,
                                   " ".join(args)))
        elif callee in _FS_VERBS:
            out.append(Act("fs", callee, SCOPE_WORKTREE, site, callee))
    return out


def _unwrap_seq(expr: ast.expr) -> tuple[str, ...]:
    """String constants of a list/tuple display, ignoring non-literal members."""
    if not isinstance(expr, (ast.List, ast.Tuple)):
        return ()
    out: list[str] = []
    for e in expr.elts:
        if isinstance(e, ast.Constant) and isinstance(e.value, str):
            out.append(e.value)
        elif isinstance(e, ast.Starred):
            out.append("*")
    return tuple(out)


def _module_functions(package: Path | None = None) -> dict[str, dict[str, ast.FunctionDef]]:
    out: dict[str, dict[str, ast.FunctionDef]] = {}
    for path in package_modules(package):
        tree = ast.parse(path.read_text())
        out[path.stem] = {n.name: n for n in ast.walk(tree)
                          if isinstance(n, ast.FunctionDef)}
    return out


def acts_of(qualname: str, package: Path | None = None,
            depth: int = 4) -> tuple[Act, ...]:
    """Every act reachable from a guard, following calls across the package.

    The wrapper matters: no guard calls ``subprocess`` itself — they call
    ``_git(...)``, and the *scope-deciding literal* (``--cached``, a ``..``
    range) sits at the call site, not in the wrapper.  So attribution has to
    walk the call graph, and stopping at module boundaries would credit
    ``local_only_audit`` with none of ``tree_provenance``'s observations.
    """
    fns = _module_functions(package)
    module, _, name = qualname.partition(".")
    seen: set[tuple[str, str]] = set()
    out: list[Act] = []

    def visit(mod: str, fn_name: str, budget: int) -> None:
        if budget < 0 or (mod, fn_name) in seen:
            return
        seen.add((mod, fn_name))
        fn = fns.get(mod, {}).get(fn_name)
        if fn is None:
            return
        out.extend(_acts_in_body(fn, mod))
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                callee = _callee_name(node)
                if callee is None or callee == fn_name:
                    continue
                if callee in fns.get(mod, {}):
                    visit(mod, callee, budget - 1)
                else:
                    for other, members in fns.items():
                        if other != mod and callee in members:
                            visit(other, callee, budget - 1)

    visit(module, name, depth)
    return tuple(dict.fromkeys(out))


def watched_operations(pool: Iterable[Guard] | None = None,
                       package: Path | None = None) -> dict[str, tuple[Act, ...]]:
    """Q-064 (b): the acts each guard performs, derived from its own code."""
    pool = tuple(pool if pool is not None else guards(package))
    return {g.qualname: acts_of(g.qualname, package) for g in pool}


def scope_coverage(pool: Iterable[Guard] | None = None,
                   package: Path | None = None) -> dict[str, dict[str, object]]:
    """For each ``TYPED`` allow-list: how many watchers, through how many windows.

    ``watchers > scopes`` is the D-048 shape stated in the vocabulary that
    explains it — the redundancy is real but it is redundancy *of window*, and
    a list watched three times through two windows is watched twice.
    """
    pool = tuple(pool if pool is not None else guards(package))
    acts = watched_operations(pool, package)
    out: dict[str, dict[str, object]] = {}
    for key, watchers in exemption_watchers(pool).items():
        scopes: set[str] = set()
        for w in watchers:
            scopes |= {a.scope for a in acts.get(w, ()) if a.scope != SCOPE_UNKNOWN}
        out[key] = {
            "watchers": watchers,
            "scopes": tuple(sorted(scopes)),
            "redundant": len(watchers) > len(scopes),
        }
    return out


#: Tokens a guard's *name* uses to claim a scope.  This half is a typed
#: vocabulary and is declared as one (D-038): unlike the registries D-045 to
#: D-047 found short, its failure mode is **under**-detection — a name spelled
#: with a word not listed here maps to nothing and is skipped, never
#: mis-attributed.  Q-064 (a)'s hand-declared rule-side half is *not* attempted.
NAME_SCOPE_CLAIMS = {
    "staged": SCOPE_INDEX,
    "cached": SCOPE_INDEX,
    "committed": SCOPE_COMMIT,
    "commits": SCOPE_COMMIT,
    "tracked": SCOPE_NAMESET,
    "untracked": SCOPE_WORKTREE,
    "drift": SCOPE_WORKTREE,
}


def nominal_scope(name: str) -> str | None:
    """The scope a guard's name claims, or ``None`` if it claims none."""
    for token, scope in NAME_SCOPE_CLAIMS.items():
        if token in name.lower():
            return scope
    return None


def misnamed_scopes(pool: Iterable[Guard] | None = None,
                    package: Path | None = None) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Guards whose name claims a scope none of their acts observe.

    This is the residue D-048 left behind.  The name is the fourth statement of
    a registry — after the constant, the prose, and the check — and it is the
    one nothing compares against the code.  A guard called ``staged`` that never
    reads the index hands a reader the clearance its name promises.
    """
    pool = tuple(pool if pool is not None else guards(package))
    acts = watched_operations(pool, package)
    out: list[tuple[str, str, tuple[str, ...]]] = []
    for g in pool:
        claimed = nominal_scope(g.name)
        if claimed is None:
            continue
        observed = tuple(sorted({a.scope for a in acts.get(g.qualname, ())
                                 if a.scope != SCOPE_UNKNOWN}))
        if observed and claimed not in observed:
            out.append((g.qualname, claimed, observed))
    return tuple(sorted(out))


def unobserved_scopes(pool: Iterable[Guard] | None = None,
                      package: Path | None = None) -> tuple[str, ...]:
    """Scopes the package demonstrates it *can* reach, but no guard reaches.

    Derived on both sides: the vocabulary is fixed, the reached set comes from
    the guards' own acts.  A scope in this result is a window the suite has the
    machinery to look through and does not.
    """
    acts = watched_operations(pool, package)
    reached = {a.scope for v in acts.values() for a in v}
    return tuple(sorted({SCOPE_WORKTREE, SCOPE_INDEX, SCOPE_COMMIT, SCOPE_NAMESET}
                        - reached))


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
    lines += ["", "acts by scope (Q-064):"]
    acts = watched_operations(pool, package)
    by_scope: dict[str, set[str]] = {}
    for qual, found in acts.items():
        for a in found:
            by_scope.setdefault(a.scope, set()).add(a.key)
    for scope in (SCOPE_WORKTREE, SCOPE_INDEX, SCOPE_COMMIT, SCOPE_NAMESET):
        seen = ", ".join(sorted(by_scope.get(scope, ()))) or "(nothing observes this)"
        lines.append(f"  {scope}: {seen}")
    lines += ["", "allow-lists by window:"]
    for key, cover in sorted(scope_coverage(pool, package).items()):
        lines.append(f"  {key}: {len(cover['watchers'])} watcher(s) through "
                     f"{len(cover['scopes'])} window(s) {cover['scopes']}")
    lines += ["", "name claims a scope its acts do not observe:"]
    for qual, claimed, observed in misnamed_scopes(pool, package):
        lines.append(f"  {qual}: name claims {claimed}, acts observe {observed}")
    if not misnamed_scopes(pool, package):
        lines.append("  (none)")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
