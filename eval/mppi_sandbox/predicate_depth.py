"""Do the scan's expression predicates read the same expression at the same depth? (Q-066)

D-050 found one depth mismatch by accident.  :func:`guard_reflexivity._is_set_valued`
did not follow a call into its own module's source; :func:`guard_reflexivity._difference_kind`
has since it was written.  Both are applied to **the same expression** in
``_guards_in``, so extracting a helper — the duplicate-removing refactor D-045
through D-049 prescribed every cycle — turned one operand into a bare call, failed
the shallower predicate, skipped the ``BitAnd`` arm, and dropped a guard out of the
registry entirely.  Not downgraded.  Absent.

The mismatch was load-bearing for roughly thirty cycles and was found by tripping
over it.  Q-066 asks the question deliberately, of every predicate rather than of
the two that happened to collide.

What is measured
----------------

Not "how deep does the code look", which is a reading of the source and would
repeat the error D-050 made — the shallow predicate was believed deep because
someone read it.  Instead each predicate is **run** against a ladder of probe
expressions that wrap one ground in increasing indirection:

``BARE`` → ``SET_CALL`` (``set(X)``) → ``COMP`` (``{v for v in X}``) →
``ALIAS`` (local ``a = X``, then ``a``) → ``CALL_1`` (``_p1()`` returning ``X``) →
``CALL_2`` (``_p2()`` returning ``_p1()``).

Following is not being right
----------------------------

A predicate can give the right answer at a rung without reading through it —
``_is_set_valued`` returns ``True`` for *any* comprehension, so it is right about
``{v for v in REGISTRY}`` for a reason that has nothing to do with ``REGISTRY``.
Counting that as depth is D-050's own mistake in miniature: a shape matching for a
cause that never fires.

So every rung is applied to **two** grounds — one the predicate answers positively
and one it answers negatively — and a predicate *follows* a rung only when **both**
readings survive it:

- both survive          ⇒ :data:`FOLLOWS`   — the wrapper is transparent
- positive survives only ⇒ :data:`OPAQUE`   — the wrapper decides, not the content
- positive does not      ⇒ :data:`BLOCKS`   — the wrapper is a wall

``OPAQUE`` is the interesting verdict and it exists because of D-050: a predicate
that answers from the wrapper is indistinguishable from a deep one on positive
probes alone, which is exactly how a masked collapse looks.

Liveness, so a reading means something
--------------------------------------

A predicate whose two grounds already agree is not discriminating, and every rung
would score ``FOLLOWS`` for free.  :func:`measure` raises rather than scoring when
that holds — the same rule :mod:`guard_direction` applies to a guard that reads
empty before the offence.

The adapter table is typed; its completeness is not
---------------------------------------------------

:data:`ADAPTERS` supplies each predicate's other arguments and its two grounds —
knowledge that cannot be derived, since the grounds encode what the predicate is
*for*.  :func:`unadapted_predicates` compares the table's keys against
:func:`expr_predicates`, which globs the module's own AST for parameters annotated
``ast.expr``, and the tests assert it empty.  The table may be typed.  Its
population is derived — D-045's rule, and the reason D-049's registry was found
short.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from . import guard_reflexivity as gr

#: Both readings survive the wrapper — the predicate reads through it.
FOLLOWS = "FOLLOWS"
#: The positive reading survives and the negative does not: the wrapper is
#: answering, not the expression inside it.  A depth that is not a depth.
OPAQUE = "OPAQUE"
#: The positive reading does not survive — the predicate stops here.
BLOCKS = "BLOCKS"

#: Rung order, shallowest first.  Order is reported, not assumed: a predicate may
#: follow ``CALL_1`` and block ``ALIAS``, and two of them do.
RUNGS = ("BARE", "SET_CALL", "COMP", "ALIAS", "CALL_1", "CALL_2")

_MODULE = Path(__file__).with_name("guard_reflexivity.py")


class ProbeError(RuntimeError):
    """A predicate could not be probed, or its liveness check did not hold."""


# --------------------------------------------------------------------------
# the probe module — parsed, never executed
# --------------------------------------------------------------------------

#: One source text carrying every rung over both grounds.  ``REGISTRY`` is a
#: module-level UPPER collection so the ``consts`` arm of the predicates binds;
#: ``OTHER`` is the same so that a negative ground differing only in *identity*
#: (``core_name``) is available alongside one differing in *kind* (``5``).
_PROBE_SRC = '''
REGISTRY = {"a", "b"}
OTHER = {"c", "d"}


def _seen():
    return {"a"}


def _known():
    return {"b"}


def _p1_REGISTRY():
    return REGISTRY


def _p2_REGISTRY():
    return _p1_REGISTRY()


def _p1_OTHER():
    return OTHER


def _p2_OTHER():
    return _p1_OTHER()


def _p1_SCALAR():
    return 5


def _p2_SCALAR():
    return _p1_SCALAR()


def _p1_DIFF():
    return _seen() - _known()


def _p2_DIFF():
    return _p1_DIFF()


def _p1_ENUM():
    return REGISTRY


def _p2_ENUM():
    return _p1_ENUM()


def _p1_SEQ():
    return ["diff", "--cached"]


def _p2_SEQ():
    return _p1_SEQ()


def _p1_SEQ2():
    return ["status"]


def _p2_SEQ2():
    return _p1_SEQ2()


def site():
    a_REGISTRY = REGISTRY
    a_OTHER = OTHER
    a_SCALAR = 5
    a_DIFF = _seen() - _known()
    a_ENUM = REGISTRY
    a_SEQ = ["diff", "--cached"]
    a_SEQ2 = ["status"]
'''

_PROBE_TREE = ast.parse(_PROBE_SRC)
_PROBE_CONSTS = gr._set_valued_constants(_PROBE_TREE)
_PROBE_FNS = {n.name: n for n in _PROBE_TREE.body if isinstance(n, ast.FunctionDef)}
_PROBE_SITE = _PROBE_FNS["site"]
_PROBE_ALIASES = gr._aliases(_PROBE_SITE)


def _rung_expr(rung: str, ground: str) -> ast.expr:
    """The probe expression for *rung* wrapping *ground*.

    Built by parsing source rather than by constructing nodes, so that what the
    predicate sees is what a scan of a real module would hand it.
    """
    if rung == "BARE":
        return _ground_expr(ground)
    if rung == "SET_CALL":
        return _parse_expr(f"set({_ground_src(ground)})")
    if rung == "COMP":
        return _parse_expr("{v for v in %s}" % _ground_src(ground))
    if rung == "ALIAS":
        return _parse_expr(f"a_{ground}")
    if rung == "CALL_1":
        return _parse_expr(f"_p1_{ground}()")
    if rung == "CALL_2":
        return _parse_expr(f"_p2_{ground}()")
    raise ProbeError(f"unknown rung {rung!r}")


def _ground_src(ground: str) -> str:
    return {
        "REGISTRY": "REGISTRY",
        "OTHER": "OTHER",
        "SCALAR": "5",
        "DIFF": "_seen() - _known()",
        "ENUM": "REGISTRY",
        "SEQ": '["diff", "--cached"]',
        "SEQ2": '["status"]',
    }[ground]


def _ground_expr(ground: str) -> ast.expr:
    return _parse_expr(_ground_src(ground))


def _parse_expr(src: str) -> ast.expr:
    node = ast.parse(src, mode="eval").body
    return node


# --------------------------------------------------------------------------
# derived population
# --------------------------------------------------------------------------


def expr_predicates(module: Path | None = None) -> tuple[str, ...]:
    """Module-level functions taking a parameter annotated ``ast.expr``.

    Derived from the module's own source, per STATE's instruction not to type the
    list — the registry that D-049 found short was typed, and so was the one
    D-047 found short before it.
    """
    tree = ast.parse((module or _MODULE).read_text())
    out: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for arg in node.args.args:
            if arg.annotation is not None and ast.unparse(arg.annotation) == "ast.expr":
                out.append(node.name)
                break
    return tuple(sorted(out))


def co_applied(module: Path | None = None) -> tuple[tuple[str, str], ...]:
    """Predicate pairs handed **the identically spelled** first argument.

    ⚠ This is the *narrow* relation and it is a lower bound.  The first draft of
    this module shipped only this one and it **does not contain D-050's own
    pair** — ``_guards_in`` hands ``_is_set_valued`` the *operands*
    (``left``/``right``) and ``_difference_kind`` the *population* traced from
    ``node.left``, so the two never share an argument spelling even though they
    are reading the same ``&`` expression.  Eighth first-draft scan in nine
    cycles to be wrong about its own population, and again in the under-counting
    direction.  Use :func:`co_derived` for the relation that bites; this one is
    kept because a shared spelling is the strongest form of the relation and is
    worth reporting separately.
    """
    return _pairs_by_key(module, _argument_key)


def co_derived(module: Path | None = None) -> tuple[tuple[str, str], ...]:
    """Predicate pairs whose arguments descend from the **same loop variable**.

    This is the relation D-050's failure lives in.  Sameness is traced through
    local bindings — plain assignment, tuple unpacking (``left, right = ...``)
    and ``list.append`` (how ``populations`` is filled) — back to the ``for``
    targets of the enclosing function.  Two predicates are co-derived when their
    arguments are both reading the same scanned object, whether or not they are
    handed the same node of it.

    Restricting roots to loop targets is what keeps this from degenerating: every
    call in ``_guards_in`` also mentions ``aliases`` and ``consts``, and rooting
    on those would pair every predicate with every other.
    """
    return _pairs_by_key(module, _root_keys)


def _argument_key(fn: ast.FunctionDef, call: ast.Call) -> tuple[str, ...]:
    return (ast.unparse(call.args[0]),)


def _root_keys(fn: ast.FunctionDef, call: ast.Call) -> tuple[str, ...]:
    return tuple(sorted(_roots(call.args[0], _bindings(fn), _loop_targets(fn))))


def _pairs_by_key(module: Path | None,
                  key: "Callable[[ast.FunctionDef, ast.Call], tuple[str, ...]]",
                  ) -> tuple[tuple[str, str], ...]:
    tree = ast.parse((module or _MODULE).read_text())
    preds = set(expr_predicates(module))
    pairs: set[tuple[str, str]] = set()
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        buckets: dict[str, set[str]] = {}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = gr._callee_name(node)
            if name not in preds:
                continue
            for k in key(fn, node):
                buckets.setdefault(k, set()).add(name)
        for names in buckets.values():
            ordered = sorted(names)
            for i, a in enumerate(ordered):
                for b in ordered[i + 1:]:
                    pairs.add((a, b))
    return tuple(sorted(pairs))


def _bindings(fn: ast.FunctionDef) -> dict[str, ast.expr]:
    """Local name → expression, including tuple unpacking and ``.append``.

    ``gr._aliases`` handles only single-target assignment, which is correct for
    what it does and insufficient here: ``left, right = _resolve(...), _resolve(...)``
    and ``populations.append(node.left)`` are both load-bearing links in the
    chain from a predicate's argument back to the node it came from.
    """
    out: dict[str, ast.expr] = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                out.setdefault(target.id, node.value)
            elif isinstance(target, ast.Tuple) and isinstance(node.value, ast.Tuple) \
                    and len(target.elts) == len(node.value.elts):
                for t, v in zip(target.elts, node.value.elts):
                    if isinstance(t, ast.Name):
                        out.setdefault(t.id, v)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            if isinstance(func, ast.Attribute) and func.attr == "append" \
                    and isinstance(func.value, ast.Name) and node.value.args:
                out.setdefault(func.value.id, node.value.args[0])
    return out


def _loop_targets(fn: ast.FunctionDef) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out


def _roots(expr: ast.expr, bindings: dict[str, ast.expr], targets: set[str],
           depth: int = 6) -> set[str]:
    if depth <= 0:
        return set()
    names = {n.id for n in ast.walk(expr) if isinstance(n, ast.Name)}
    out = names & targets
    for name in names - targets:
        if name in bindings:
            out |= _roots(bindings[name], bindings, targets, depth - 1)
    return out


# --------------------------------------------------------------------------
# adapters
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Adapter:
    """How to call one predicate, and the two grounds that make it discriminate."""

    call: Callable[[ast.expr], object]
    positive: str
    negative: str


def _call_core_name(expr: ast.expr) -> object:
    return gr.core_name(expr)


def _call_is_set_valued(expr: ast.expr) -> object:
    return gr._is_set_valued(expr, _PROBE_CONSTS, set(), _PROBE_FNS)


def _call_difference_kind(expr: ast.expr) -> object:
    return gr._difference_kind(expr, _PROBE_FNS, _PROBE_SRC)


def _call_provenance(expr: ast.expr) -> object:
    return gr._provenance(expr, _PROBE_CONSTS, set(), set())[0]


def _call_resolve(expr: ast.expr) -> object:
    return ast.unparse(gr._resolve(expr, _PROBE_ALIASES))


def _call_unwrap(expr: ast.expr) -> object:
    return ast.unparse(gr._unwrap(expr))


def _call_unwrap_seq(expr: ast.expr) -> object:
    return gr._unwrap_seq(expr)


#: Typed — the grounds encode what each predicate is *for*, which no scan recovers.
#: Its completeness is checked by :func:`unadapted_predicates`.
ADAPTERS: dict[str, Adapter] = {
    # "is this expression about REGISTRY, or about something else"
    "core_name": Adapter(_call_core_name, "REGISTRY", "OTHER"),
    # "is this a collection, or a scalar"
    "_is_set_valued": Adapter(_call_is_set_valued, "REGISTRY", "SCALAR"),
    # "is this population a difference, or an enumeration"
    "_difference_kind": Adapter(_call_difference_kind, "DIFF", "ENUM"),
    # "is this a typed registry, or something derived"
    "_provenance": Adapter(_call_provenance, "REGISTRY", "DIFF"),
    # "does this resolve to REGISTRY, or to something else"
    "_resolve": Adapter(_call_resolve, "REGISTRY", "OTHER"),
    "_unwrap": Adapter(_call_unwrap, "REGISTRY", "OTHER"),
    # "which literal strings does this argument list state" — grounds must be
    # list *displays*, not names: the first draft used REGISTRY/OTHER and the
    # liveness check rejected it, because a Name reads `()` either way.
    "_unwrap_seq": Adapter(_call_unwrap_seq, "SEQ", "SEQ2"),
}


def unadapted_predicates(module: Path | None = None) -> tuple[str, ...]:
    """Derived predicates with no adapter — the audit's own blind spot.

    Asserted empty in the tests, so a new ``ast.expr`` predicate cannot enter the
    scan without entering this probe too.
    """
    return tuple(sorted(set(expr_predicates(module)) - set(ADAPTERS)))


def stale_adapters(module: Path | None = None) -> tuple[str, ...]:
    """Adapters naming a predicate that no longer exists — the mirror check.

    :mod:`guard_direction` shipped :func:`stale_probes` on principle and it
    reported a deleted guard within the hour.  Same shape, same reason.
    """
    return tuple(sorted(set(ADAPTERS) - set(expr_predicates(module))))


# --------------------------------------------------------------------------
# measurement
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Reading:
    predicate: str
    rung: str
    verdict: str

    @property
    def key(self) -> str:
        return f"{self.predicate}@{self.rung}"


def measure(predicate: str) -> tuple[Reading, ...]:
    """Run one predicate over every rung, against both of its grounds.

    Raises :class:`ProbeError` when the two grounds do not already disagree at
    ``BARE`` — without that, every rung scores ``FOLLOWS`` for free and the
    reading is about nothing.
    """
    adapter = ADAPTERS.get(predicate)
    if adapter is None:
        raise ProbeError(f"no adapter for {predicate!r}")
    base_pos = adapter.call(_rung_expr("BARE", adapter.positive))
    base_neg = adapter.call(_rung_expr("BARE", adapter.negative))
    if base_pos == base_neg:
        raise ProbeError(
            f"{predicate} does not discriminate its grounds at BARE "
            f"({adapter.positive} and {adapter.negative} both read {base_pos!r}) — "
            "a rung ladder over a dead predicate measures nothing"
        )
    out: list[Reading] = []
    for rung in RUNGS:
        pos = adapter.call(_rung_expr(rung, adapter.positive))
        neg = adapter.call(_rung_expr(rung, adapter.negative))
        if pos != base_pos:
            verdict = BLOCKS
        elif neg != base_neg:
            verdict = OPAQUE
        else:
            verdict = FOLLOWS
        out.append(Reading(predicate, rung, verdict))
    return tuple(out)


def depth_profile(predicate: str) -> tuple[str, ...]:
    """The rungs *predicate* reads through, in ladder order."""
    return tuple(r.rung for r in measure(predicate) if r.verdict == FOLLOWS)


def profiles(module: Path | None = None) -> dict[str, tuple[str, ...]]:
    return {p: depth_profile(p) for p in sorted(ADAPTERS) if p in expr_predicates(module)}


def disagreements(module: Path | None = None) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Co-applied predicate pairs whose depth profiles differ, and on which rungs.

    D-050's pair must appear here or the instrument is not measuring what its
    docstring says — pinned as a test rather than asserted in prose.
    """
    prof = profiles(module)
    out: list[tuple[str, str, tuple[str, ...]]] = []
    for a, b in co_derived(module):
        if a not in prof or b not in prof:
            continue
        diff = tuple(r for r in RUNGS if (r in prof[a]) != (r in prof[b]))
        if diff:
            out.append((a, b, diff))
    return tuple(out)


def opaque_readings(module: Path | None = None) -> tuple[str, ...]:
    """Every ``(predicate, rung)`` where the wrapper answers instead of the content.

    Not a bug list.  ``_is_set_valued`` is *supposed* to call a comprehension
    set-valued whatever it iterates.  It is a list of the places where a positive
    probe alone would have reported a depth the predicate does not have — the
    reason this module runs a negative ladder at all.
    """
    out: list[str] = []
    for pred in sorted(ADAPTERS):
        if pred not in expr_predicates(module):
            continue
        out.extend(r.key for r in measure(pred) if r.verdict == OPAQUE)
    return tuple(out)


# --------------------------------------------------------------------------
# declared vs measured depth
# --------------------------------------------------------------------------


def declared_depths(module: Path | None = None) -> dict[str, int]:
    """Each predicate's own ``depth=`` default, read off its signature.

    A fourth statement of the same property, in the shape D-049 named: the
    predicates declare 2, 2 and 3, nothing compares those numbers against each
    other, and nothing compares them against what the ladder measures.
    """
    tree = ast.parse((module or _MODULE).read_text())
    out: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        args = node.args.args
        defaults = node.args.defaults
        if not defaults:
            continue
        for arg, default in zip(args[len(args) - len(defaults):], defaults):
            if arg.arg == "depth" and isinstance(default, ast.Constant) \
                    and isinstance(default.value, int):
                out[node.name] = default.value
    return out


def provenance_depth_exposure(package: Path | None = None) -> tuple[tuple[str, str, str], ...]:
    """Guard exemptions that :func:`_provenance` calls ``DERIVED`` but that reach a
    hand-typed registry one same-module call frame down.

    This is what the ``_is_set_valued`` / ``_provenance`` disagreement *buys* when
    it fires.  The two are handed the same ``right`` in ``_guards_in``:
    ``_is_set_valued`` follows a same-module call (D-050's fix), ``_provenance``
    stops at it.  So an exemption whose registry is reached through one helper is
    admitted as a guard and then classified ``DERIVED`` — and every ``TYPED``
    screen (:attr:`Guard.typed_exemptions`, :func:`guard_reflexivity.bite`,
    :func:`guard_reflexivity.unwatched_exemptions`) silently skips it.

    **At HEAD this returns ``()``** — the exposure is latent, not live, and it is
    reported as a re-derived zero rather than an assertion because that is the
    only form in which a zero stays true.  It is worth shipping anyway for the
    reason D-050 gave: "extract the duplicated registry behind a helper" is the
    refactor five consecutive decisions prescribed, and it is exactly the edit
    that turns this count positive.

    **What to do when it is positive (Q-067 → D-052, option (b)).**  A non-zero
    reading is a *warning about the call site*, not a defect in
    :func:`guard_reflexivity._provenance` — which declines to follow the call on
    purpose, because "is this a hand-typed registry" is a question about the
    place it is asked and does not survive a frame change.  The prescribed
    repair is to **name the helper's registry at the call site**: pass it as an
    argument, or bind it to a module-level constant the guard's own expression
    mentions.  Widening the predicate is the wrong repair; it would re-label
    genuinely derived populations ``TYPED`` and quietly grow every screen that
    consumes that label.

    The exposure is now larger than D-051 priced it, because the set of screens
    that go blind has grown: :attr:`guard_reflexivity.Guard.typed_exemptions`,
    :func:`guard_reflexivity.bite`, :func:`guard_reflexivity.unwatched_exemptions`
    and — added this cycle — the whole population of
    :mod:`exemption_masking`, whose 12 pairs are exactly the ``TYPED`` ones.  An
    exemption that slips to ``DERIVED`` is not screened for masking at all.
    """
    base = package or gr.PACKAGE
    out: list[tuple[str, str, str]] = []
    pool = gr.guards(base)
    for path in gr.package_modules(base):
        tree = ast.parse(path.read_text())
        consts = gr._set_valued_constants(tree)
        imported = gr._imported_upper(tree)
        fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for guard in pool:
            if guard.module != path.stem:
                continue
            for exemption in guard.exemptions:
                if exemption.provenance != gr.PROV_DERIVED:
                    continue
                try:
                    expr = ast.parse(exemption.expr, mode="eval").body
                except SyntaxError:  # pragma: no cover - defensive
                    continue
                for node in ast.walk(expr):
                    if not isinstance(node, ast.Call):
                        continue
                    callee = gr._callee_name(node)
                    if callee not in fns:
                        continue
                    for sub in ast.walk(fns[callee]):
                        if isinstance(sub, ast.Return) and sub.value is not None:
                            prov, const = gr._provenance(sub.value, consts, imported, set())
                            if prov == gr.PROV_TYPED and const is not None:
                                out.append((guard.qualname, exemption.expr, const))
    return tuple(sorted(set(out)))


def report(module: Path | None = None) -> str:
    lines: list[str] = []
    preds = expr_predicates(module)
    lines.append(f"expression predicates (derived): {len(preds)}")
    lines.append(f"  unadapted: {unadapted_predicates(module) or '()'}")
    lines.append(f"  stale adapters: {stale_adapters(module) or '()'}")
    lines.append("")
    declared = declared_depths(module)
    lines.append("depth profile (rungs read through):")
    for pred, prof in sorted(profiles(module).items()):
        dec = declared.get(pred)
        dec_s = f"  declared depth={dec}" if dec is not None else ""
        lines.append(f"  {pred:20s} {len(prof)}/{len(RUNGS)} {list(prof)}{dec_s}")
    lines.append("")
    lines.append(f"co-applied pairs (same spelling): {len(co_applied(module))}")
    lines.append(f"co-derived pairs (same loop variable): {len(co_derived(module))}")
    dis = disagreements(module)
    lines.append(f"depth disagreements among them: {len(dis)}")
    for a, b, rungs in dis:
        lines.append(f"  {a} vs {b} — differ on {list(rungs)}")
    lines.append("")
    opa = opaque_readings(module)
    lines.append(f"opaque readings (wrapper answers, not content): {len(opa)}")
    for key in opa:
        lines.append(f"  {key}")
    lines.append("")
    exp = provenance_depth_exposure()
    lines.append(f"provenance depth exposure (DERIVED but TYPED one frame down): {len(exp)}")
    for qual, expr, const in exp:
        lines.append(f"  {qual} — {expr} -> {const}")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - CLI
    print(report())
    return 1 if (unadapted_predicates() or stale_adapters()) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
