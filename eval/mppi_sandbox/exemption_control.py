"""Negative controls for the package's typed exemption sets — D-076's bite
measurement generalised from one registry to all seven.

D-076 measured *bite* for ``magnitude_survival.SELF_DEFINING`` and found it
removes **0 of 22**.  D-078 shipped the complementary half for a different
guard: a **negative control** — tamper the input so the guard *must* fire, and
assert it fires exactly once.  The two answer different questions and only the
pair is informative:

* **bite** — does this exemption remove any member of the population it filters
  *as the tree stands*?  Zero is a fact about the population.
* **control** — would tampering the registry move any reading at all?  Zero is a
  fact about the **wiring**, and it is the one that turns a passing test into a
  vacuous one.  D-075's ``"no D-074 value survives"`` passed for the second
  reason, and a control would have caught it on the cycle that wrote it.

:mod:`exemption_masking` already measures the first, generically, by suppressing
a derived guard/constant pair and watching the population grow.  Nothing
measured the second, and this module is that.

**Both ``EXCLUDED_TESTS`` registries were default-arg-only** — read as
``excluded: Sequence[str] = EXCLUDED_TESTS``, evaluated once at ``def`` time and
bound into the function object, so rebinding the module global afterwards
changes nothing any caller can observe.  The only way in was ``excluded=``,
which controls the *parameter*, not the *registry*.

D-080 (answering Q-085) then corrected two things about that finding and acted
on it:

* **The published count was wrong.**  D-079 wrote that each registry "is read in
  exactly one place".  True of ``guard_vacuity``'s — it has exactly one reader —
  and false of ``predicate_vacuity``'s, which has **17** across four modules.
  The cause was in this file: :func:`references` keyed on the *attribute name*
  and dropped the module, so two registries sharing the name ``EXCLUDED_TESTS``
  received each other's reads as a union and the smaller reading was printed for
  both.  Reads are now attributed by resolved owning module, and
  :func:`unresolved_reads` reports the loads that resolve to nothing rather than
  guessing at them.
* **The fix/declare choice splits**, and :func:`affordable_readers` decides it
  rather than taste — Q-085's own stated procedure, mechanised.  A control is
  worth having only if it is cheap enough to run every cycle, so each reader is
  priced ``PURE`` or ``SUBPROCESS``.  ``predicate_vacuity``'s has 15 pure
  readers, so the cheapest of them (:func:`exclusion_scope.price`, pure
  arithmetic) now reads at call time and the registry is controllable — option
  (a).  ``guard_vacuity``'s sole reader spends a suite run, so option (a) is
  dead **by Q-085's own rule** and it is declared instead, in
  :data:`DECLARED_DEF_TIME`, with :func:`undeclared_unreachable` keeping the
  declaration from being silent — option (b).

So the reading is two-layer, and the static layer runs first because it decides
whether the dynamic layer means anything:

1. :func:`references` / :func:`binding` — where is the registry read, and is the
   read ``CALL_TIME`` or ``DEF_TIME``?  Reads inside the defining module count;
   a registry with no ``CALL_TIME`` read anywhere is ``UNREACHABLE``.
2. :func:`reader_cost` / :func:`affordable_readers` — what would a control
   through each reader *cost*?  ``UNREACHABLE`` plus "no affordable reader" is
   the pair that makes declaring the only honest option.
3. :func:`control` — for the reachable ones, patch the global, call a reader
   that returns an integer, restore, and report the delta.

:data:`TAMPERS` is itself a hand-typed registry of tampers, which is the
recursion this package keeps meeting.  It is not hidden: it is enumerated,
:func:`uncontrolled` names every registry in :data:`REGISTRIES` that it omits,
and the omission list is the module's own work list rather than its clearance.
:data:`DECLARED_DEF_TIME` — the excuse list D-080 added — is in
:data:`REGISTRIES` and carries its own tamper for the same reason.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

PACKAGE = Path(__file__).resolve().parent

#: A read evaluated when the function is *called* — patchable through the name.
CALL_TIME = "CALL_TIME"
#: A read evaluated when the module is *imported* (module level, or a default
#: argument expression).  Patching the name afterwards cannot reach it.
DEF_TIME = "DEF_TIME"

VERDICT_BITES = "BITES"
VERDICT_INERT = "INERT"
VERDICT_UNREACHABLE = "UNREACHABLE"

#: The typed exemption / registry sets this module is accountable for, as
#: ``(module, attribute)``.  ``CARRIED_FIELDS`` is included although
#: ``tests/test_reading_record.py`` already tampers it — the point of a census
#: is that the covered case sits in the same table as the uncovered ones, where
#: its coverage is a reading rather than a memory.
REGISTRIES: tuple[tuple[str, str], ...] = (
    ("magnitude_survival", "SELF_DEFINING"),
    ("reading_record", "CARRIED_FIELDS"),
    ("guard_reflexivity", "NAME_SCOPE_CLAIMS"),
    ("claim_scope", "SCOPED_CLAIMS"),
    ("claim_scope", "DEGENERATE_READINGS"),
    ("lam_dependence", "TEMPERATURE_RELEVANT"),
    ("predicate_vacuity", "EXCLUDED_TESTS"),
    ("guard_vacuity", "EXCLUDED_TESTS"),
    ("exemption_control", "DECLARED_DEF_TIME"),
    ("suite_memo", "TREE_SUFFIXES"),
    ("suite_memo", "TREE_SKIP"),
    ("extremum_reading", "HULL_REPAIRED_BY"),
    ("extremum_reading", "SITE_CLASSES"),
    ("scene_separability", "TTC_FAMILY"),
)


@dataclass(frozen=True)
class Reference:
    """One place a registry's name is read."""

    module: str
    #: ``CALL_TIME`` or ``DEF_TIME``.
    binding: str
    lineno: int
    #: Enclosing function's dotted name, or ``""`` at module level.
    function: str

    @property
    def own_module(self) -> str:
        return self.module


def _default_nodes(tree: ast.AST) -> set[int]:
    """``id()`` of every node inside a default-argument expression."""
    out: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.Lambda)):
            continue
        for expr in list(node.args.defaults) + list(node.args.kw_defaults):
            if expr is None:
                continue
            for sub in ast.walk(expr):
                out.add(id(sub))
    return out


def _enclosing(tree: ast.AST) -> dict[int, str]:
    """``id(node) -> enclosing function name``, ``""`` at module level."""
    out: dict[int, str] = {}

    def walk(node: ast.AST, fn: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = fn
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{fn}.{child.name}" if fn else child.name
            out[id(child)] = name
            walk(child, name)

    walk(tree, "")
    return out


def _module_aliases(tree: ast.AST) -> dict[str, str]:
    """Local alias → module stem, for every module import in ``tree``.

    ``from eval.mppi_sandbox import predicate_vacuity as pv`` binds ``pv``;
    ``from . import guard_vacuity`` binds ``guard_vacuity``;
    ``import eval.mppi_sandbox.predicate_vacuity as pv`` binds ``pv``.
    Function-local imports are included — :func:`ast.walk` reaches them, and a
    reader that imports inside its body reads the same registry as one that
    imports at the top.
    """
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                stem = alias.name.rsplit(".", 1)[-1]
                out[alias.asname or stem] = stem
    return out


def _name_owners(name: str, tree: ast.AST) -> dict[str, str]:
    """Bare-name imports of ``name``: ``from X import NAME`` → ``{NAME: X}``."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        for alias in node.names:
            if alias.name == name:
                out[alias.asname or alias.name] = node.module.rsplit(".", 1)[-1]
    return out


def _reads(name: str, tree: ast.AST, own_stem: str) -> list[tuple[ast.AST, str]]:
    """``(node, owning module stem)`` for every load of ``name``.

    The owner is **resolved**, not assumed.  A bare ``NAME`` belongs to the
    scanning module unless it was imported from another one; a ``pv.NAME``
    attribute belongs to whatever ``pv`` was imported as.  An attribute whose
    base is not a resolvable module alias — ``self.NAME``, a subscript — owns
    nothing and is reported as ``""`` by :func:`unresolved_reads` rather than
    guessed at.

    Resolving is the whole point.  Keying on the attribute name alone, as this
    did until D-080, makes ``predicate_vacuity.EXCLUDED_TESTS`` and
    ``guard_vacuity.EXCLUDED_TESTS`` indistinguishable: both got the *union* of
    the two read sets, so each was credited with 17 reads it does not have.

    The assignment that *defines* the registry is a ``Store`` and is excluded:
    a registry always names itself once, and counting that as a read would make
    every registry look reachable from its own definition.
    """
    aliases = _module_aliases(tree)
    owners = _name_owners(name, tree)
    out: list[tuple[ast.AST, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            if isinstance(node.ctx, ast.Load):
                out.append((node, owners.get(name, own_stem)))
        elif isinstance(node, ast.Attribute) and node.attr == name:
            if not isinstance(node.ctx, ast.Load):
                continue
            base = node.value
            if isinstance(base, ast.Name):
                out.append((node, aliases.get(base.id, "")))
            elif isinstance(base, ast.Attribute):
                out.append((node, aliases.get(base.attr, base.attr)))
            else:
                out.append((node, ""))
    return out


def _scan(registry: tuple[str, str],
          package: Path | None,
          resolved: bool) -> tuple[Reference, ...]:
    base = package or PACKAGE
    module, name = registry
    out: list[Reference] = []
    for path in sorted(base.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:                                # pragma: no cover
            continue
        defaults = _default_nodes(tree)
        enclosing = _enclosing(tree)
        for node, owner in _reads(name, tree, path.stem):
            if (owner == module) is not resolved:
                continue
            fn = enclosing.get(id(node), "")
            at_def = id(node) in defaults or not fn
            out.append(Reference(module=path.stem,
                                 binding=DEF_TIME if at_def else CALL_TIME,
                                 lineno=getattr(node, "lineno", 0),
                                 function=fn))
    return tuple(out)


def references(registry: tuple[str, str],
               package: Path | None = None) -> tuple[Reference, ...]:
    """Every read of ``registry`` across the package's modules.

    Reads are attributed by **resolved owning module**, so a registry is
    credited only with the reads that are actually of *it* — see :func:`_reads`
    for what that fixed.

    Scans modules only.  ``tests/`` is deliberately out of scope: a test that
    reads the name is the layer this module is trying to *validate*, not part of
    the surface a tamper has to reach.
    """
    return _scan(registry, package, resolved=True)


def unresolved_reads(registry: tuple[str, str],
                     package: Path | None = None) -> tuple[Reference, ...]:
    """Loads of the registry's *name* that resolve to no module — the blind spot.

    :func:`references` drops these because attributing them would be a guess.
    Reporting them separately is what keeps that drop from being silent: a
    non-empty result means the resolved count is a **lower** bound.
    """
    base = package or PACKAGE
    _, name = registry
    out: list[Reference] = []
    for path in sorted(base.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:                                # pragma: no cover
            continue
        defaults = _default_nodes(tree)
        enclosing = _enclosing(tree)
        for node, owner in _reads(name, tree, path.stem):
            if owner:
                continue
            fn = enclosing.get(id(node), "")
            at_def = id(node) in defaults or not fn
            out.append(Reference(module=path.stem,
                                 binding=DEF_TIME if at_def else CALL_TIME,
                                 lineno=getattr(node, "lineno", 0),
                                 function=fn))
    return tuple(out)


def binding(registry: tuple[str, str],
            package: Path | None = None) -> str:
    """``CALL_TIME`` if any read outside the defining module's own top level is
    evaluated per call, else ``DEF_TIME``.

    Reads inside the defining module count — a registry consumed only by its own
    module is still consumed.  What does *not* count is the docstring-level and
    module-level mention, which is why :func:`_reads` drops the ``Store``.
    """
    refs = references(registry, package)
    return CALL_TIME if any(r.binding == CALL_TIME for r in refs) else DEF_TIME


# ---------------------------------------------------------------------------
# What a control over this registry would *cost* — Q-085's decision procedure.

#: Reader that reaches a ``subprocess`` call.  A control through it costs a
#: suite run, so it is a control nobody runs every cycle.
SUBPROCESS = "SUBPROCESS"
#: Reader that does not.  A control through it is affordable per cycle.
PURE = "PURE"


@dataclass(frozen=True)
class ReaderCost:
    """One reader of a registry, priced."""

    module: str
    function: str
    cost: str


def _direct_subprocess(tree: ast.AST) -> set[str]:
    """Functions in ``tree`` whose own body calls ``subprocess.*``."""
    enclosing = _enclosing(tree)
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) \
                and fn.value.id == "subprocess":
            out.add(enclosing.get(id(node), ""))
    return out


def _local_calls(tree: ast.AST) -> dict[str, set[str]]:
    """Function → set of bare names it calls, within the same module."""
    enclosing = _enclosing(tree)
    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name:
            out.setdefault(enclosing.get(id(node), ""), set()).add(name)
    return out


def _costs(tree: ast.AST) -> dict[str, str]:
    """Every function in ``tree``, priced by transitive reach to ``subprocess``.

    Transitive **within the module only**: :func:`predicate_vacuity.measure`
    spends its subprocess inside ``_run_recorder``, so a direct-call test would
    price it ``PURE`` and answer Q-085 backwards.  Cross-module reach is not
    followed — an unfollowed edge can only price a reader too cheaply, so the
    ``PURE`` set is an upper bound and every ``SUBPROCESS`` verdict is sound.
    """
    direct = _direct_subprocess(tree)
    calls = _local_calls(tree)
    dirty = {f for f in direct if f}
    changed = True
    while changed:                      # transitive closure; modules are small
        changed = False
        for fn, called in calls.items():
            if fn and fn not in dirty and called & dirty:
                dirty.add(fn)
                changed = True
    every = set(calls) | dirty | {f for f in _enclosing(tree).values() if f}
    return {f: (SUBPROCESS if f in dirty else PURE) for f in every if f}


def reader_cost(registry: tuple[str, str],
                package: Path | None = None) -> tuple[ReaderCost, ...]:
    """Each distinct reader of ``registry``, priced ``PURE`` or ``SUBPROCESS``.

    This is Q-085's stated decision procedure, mechanised: *"(a) 를 고르면
    저렴한 non-subprocess reader 가 존재하는지부터 확인해야 하고, 없으면 (a)
    는 자동으로 죽는다."*  Eyeballing it is what produced the premise D-080
    had to withdraw.
    """
    base = package or PACKAGE
    cache: dict[str, dict[str, str]] = {}
    out: list[ReaderCost] = []
    seen: set[tuple[str, str]] = set()
    for ref in references(registry, package):
        if not ref.function or (ref.module, ref.function) in seen:
            continue
        seen.add((ref.module, ref.function))
        if ref.module not in cache:
            cache[ref.module] = _costs(ast.parse(
                (base / f"{ref.module}.py").read_text()))
        out.append(ReaderCost(ref.module, ref.function,
                              cache[ref.module].get(ref.function, PURE)))
    return tuple(sorted(out, key=lambda r: (r.module, r.function)))


def affordable_readers(registry: tuple[str, str],
                       package: Path | None = None) -> tuple[ReaderCost, ...]:
    """Readers a per-cycle negative control could go through.

    Empty ⇒ Q-085's option (a) is dead for this registry *by its own rule*, and
    declaring the default-arg binding is the only honest move left.
    """
    return tuple(r for r in reader_cost(registry, package) if r.cost == PURE)


@dataclass(frozen=True)
class Tamper:
    """A negative control: how to break ``registry``, and what should notice."""

    registry: tuple[str, str]
    #: ``original -> tampered`` value.  Takes the live value so a tamper can be
    #: built out of the real population rather than a guessed literal.
    patch: Callable[[object], object]
    #: The reading that should move, as an integer.
    read: Callable[[], int]
    #: ``"grows"`` or ``"shrinks"`` — asserted, not merely recorded, because a
    #: reading that moves the *wrong* way is not a passing control.
    expect: str
    #: Dotted name of the reader, for the report.
    reader: str
    #: Module whose namespace holds the binding to patch, when that is *not*
    #: the module in :attr:`registry`.  Empty means the two coincide.
    #:
    #: They coincide for every tamper whose reader reaches the registry as an
    #: attribute (``war.RESOLVERS``): patching the declaring module is what the
    #: reader loads.  A reader that did ``from war import RESOLVERS`` binds its
    #: own module-level name at import, and patching the declarer leaves it on
    #: the original — the aliasing hazard :func:`_live_module` documents one
    #: frame further out, arriving through a from-import instead of a re-exec.
    #:
    #: Splitting the two is what lets :attr:`registry` stay the registry's
    #: **identity**.  :func:`binding` resolves reads to their owning module, so
    #: naming the reader here would ask it about a name that module imports
    #: rather than owns — it answers ``DEF_TIME``, :func:`control` short-circuits
    #: to ``UNREACHABLE``, and the reader is never called at all.  That is a
    #: control reporting *no reading* for a registry that is correctly wired,
    #: which is the same class of defect as the ``__main__`` one below.  It
    #: reported ``0 -> 0`` until :data:`UNMEASURED` landed; the miswiring is
    #: still silent, but it no longer looks like a measurement.
    bound_in: str = ""


@dataclass(frozen=True)
class Control:
    """One negative control, run.

    :attr:`baseline` and :attr:`tampered` are ``None`` — never ``0`` — when the
    reader was **not run**.  The distinction is the whole point: a short-circuit
    has no reading, and a placeholder that renders like one is a fabricated
    measurement.  ``UNREACHABLE`` used to carry ``0, 0``, which is
    indistinguishable in :func:`report` from a control that genuinely read zero
    on both sides, and the 07:00 cycle of 2026-08-15 read exactly that row as a
    measurement and spent its overrun chasing a :func:`sites` bug that does not
    exist (D-277's closing note).  ``None`` cannot be misread as a count, and
    :attr:`delta` refuses rather than subtracting two placeholders into a
    confident ``0``.
    """

    registry: str
    reader: str
    verdict: str
    baseline: int | None
    tampered: int | None
    note: str = ""

    @property
    def delta(self) -> int | None:
        """The move, or ``None`` when the reader was never run.

        Deliberately not ``0`` in the unmeasured case: ``delta == 0`` is the
        signature of :data:`VERDICT_INERT` — a registry that was tampered and
        did not move — and an unreachable one was never tampered at all.
        Collapsing the two hands callers a passing-looking number for a control
        that never ran.
        """
        if self.baseline is None or self.tampered is None:
            return None
        return self.tampered - self.baseline

    @property
    def measured(self) -> bool:
        """Whether a reading exists at all — false iff :func:`control` short-circuited."""
        return self.baseline is not None and self.tampered is not None


# ---------------------------------------------------------------------------
# The tampers.
#
# Each reader below is chosen to be *pure and cheap* — no suite run, no disk
# scan where a pure one exists.  A control that costs a subprocess is a control
# nobody runs every cycle, and an unrun control is the thing this module exists
# to prevent.


def _self_defining() -> Tamper:
    from eval.mppi_sandbox import magnitude_survival as ms
    from eval.mppi_sandbox import published_ratios as pr

    def patch(original):
        cell = pr.PUBLISHED[0]
        return tuple(original) + ((cell.decision, cell.site, ms.KINDS[0]),)

    return Tamper(("magnitude_survival", "SELF_DEFINING"), patch,
                  lambda: ms.exemption_bite()[0], "grows",
                  "magnitude_survival.exemption_bite")


def _carried_fields() -> Tamper:
    from eval.mppi_sandbox import reading_record as rr
    return Tamper(("reading_record", "CARRIED_FIELDS"),
                  lambda original: tuple(original) + ("a_field_no_cell_supplies",),
                  lambda: len(rr.uncarried_fields()), "grows",
                  "reading_record.uncarried_fields")


def _name_scope_claims() -> Tamper:
    from eval.mppi_sandbox import guard_reflexivity as gr
    probe = ("staged_declarations", "committed_tree", "untracked_paths")

    def read() -> int:
        return sum(1 for n in probe if gr.nominal_scope(n) is not None)

    return Tamper(("guard_reflexivity", "NAME_SCOPE_CLAIMS"),
                  lambda original: {k: v for k, v in original.items()
                                    if k not in ("staged", "committed")},
                  read, "shrinks", "guard_reflexivity.nominal_scope")


def _scoped_claims() -> Tamper:
    from eval.mppi_sandbox import claim_scope as cs

    def patch(original):
        extra = dataclasses.replace(original[0], claim="__control__",
                                    reading_calibrated=0.0, reading_other=0.0)
        return tuple(original) + (extra,)

    return Tamper(("claim_scope", "SCOPED_CLAIMS"), patch,
                  lambda: len(cs.unscannable_readings()), "grows",
                  "claim_scope.unscannable_readings")


def _degenerate_readings() -> Tamper:
    from eval.mppi_sandbox import claim_scope as cs
    return Tamper(("claim_scope", "DEGENERATE_READINGS"),
                  lambda original: tuple(original)
                  + (cs.SCOPED_CLAIMS[0].reading_calibrated,),
                  lambda: len(cs.unscannable_readings()), "grows",
                  "claim_scope.unscannable_readings")


def _temperature_relevant() -> Tamper:
    from eval.mppi_sandbox import lam_dependence as ld
    counts = {ld.ANCHORED: 3, ld.COMPARATIVE: 2, ld.SILENT: 5}

    return Tamper(("lam_dependence", "TEMPERATURE_RELEVANT"),
                  lambda original: frozenset(original - {ld.COMPARATIVE}),
                  lambda: ld.Bracket(counts=counts, total=10).lower, "shrinks",
                  "lam_dependence.Bracket.lower")


def _excluded_tests_pv() -> Tamper:
    """The control D-079 said could not exist — see :func:`exclusion_scope.price`.

    It could not exist while all 17 readers bound the registry as a default
    argument.  D-080 made the cheapest of them read at call time, so the name is
    now controllable at the price of one addition.
    """
    from eval.mppi_sandbox import exclusion_scope as es
    return Tamper(("predicate_vacuity", "EXCLUDED_TESTS"),
                  lambda original: tuple(original) + ("tests/__control__.py",),
                  es.price, "grows", "exclusion_scope.price")


#: Registries deliberately left reachable only through an explicit parameter,
#: with the reading that justifies it.  Q-085 asked whether a default-arg-only
#: registry should be fixed or declared; D-080 answers **both**, split by
#: :func:`affordable_readers` — fix the one that has a cheap reader, declare the
#: one that does not.  ``guard_vacuity.EXCLUDED_TESTS`` has exactly one reader
#: and it spends a suite run, so a control through it is one nobody would run;
#: its control is the ``excluded=`` parameter, which
#: ``tests/test_guard_witness.py`` already exercises.
DECLARED_DEF_TIME: dict[str, str] = {
    "guard_vacuity.EXCLUDED_TESTS":
        "sole reader guard_vacuity.measure is SUBPROCESS-priced; "
        "control exists only as the excluded= parameter",
}


def _declared_def_time() -> Tamper:
    """This module's own excuse list, controlled by this module.

    :data:`DECLARED_DEF_TIME` is a typed exemption set like the eight it sits
    beside, so leaving it out would be the exact evasion the census exists to
    forbid — and ``guard_reflexivity.unwatched_exemptions`` noticed it within
    one test run of its being written.  Dropping the declaration must make
    :func:`undeclared_unreachable` name the registry it was excusing.
    """
    return Tamper(("exemption_control", "DECLARED_DEF_TIME"),
                  lambda original: {}, lambda: len(undeclared_unreachable()),
                  "grows", "exemption_control.undeclared_unreachable")


def _tree_suffixes() -> Tamper:
    """:mod:`suite_memo`'s file-type allow-list, controlled through its scope.

    The memo's key includes a digest of the tree the nested run imports, and
    this list decides which files that digest can see.  A narrowing here is a
    *silent* widening of what the cache will serve: drop ``.py`` and the memo
    stops noticing source edits, which is the failure that reads as a saving.
    """
    from eval.mppi_sandbox import suite_memo as sm
    return Tamper(("suite_memo", "TREE_SUFFIXES"),
                  lambda original: tuple(s for s in original if s != ".py"),
                  sm.digest_scope, "shrinks", "suite_memo.digest_scope")


def _tree_skip() -> Tamper:
    """The other half of the same scope — the directories it refuses to read."""
    from eval.mppi_sandbox import suite_memo as sm
    return Tamper(("suite_memo", "TREE_SKIP"),
                  lambda original: frozenset(original | {"tests"}),
                  sm.digest_scope, "shrinks", "suite_memo.digest_scope")


def _resolvers() -> Tamper:
    """`window_axis_reach.RESOLVERS` — controlled on entry, still unwatched.

    D-275 declared this registry rather than discovering it, following
    `lam_window_index.TABLES`, and D-276's `window_axis_migration.sites` reads
    it as its own population.  That is what put ``RESOLVERS`` on
    `guard_reflexivity.unwatched_exemptions`: a typed allow-list with no
    module-level enumerator.  The D-080 answer applies unchanged — give it a
    control now rather than a sixth watcher, so it is *controlled* while
    unwatched, and the two properties stay distinct (see
    `test_this_module_gives_the_four_unwatched_lists_a_control_not_a_watcher`).

    Shrinking the registry must move the migration census: drop a resolver and
    its call sites stop being counted (49 -> 28 for ``lam_window_index.resolve``).

    The registry is `window_axis_reach`'s, but the name this patches is
    `window_axis_migration`'s — the two are split via :attr:`Tamper.bound_in`,
    and both halves are load-bearing:

    * **Patch the reader.** `window_axis_migration` does ``from
      .window_axis_reach import RESOLVERS``, binding its own module-level name
      at import, so patching the declarer leaves the reader on the original
      tuple and the control reads ``INERT`` against a live registry.
    * **Identify the declarer.** Naming the reader in :attr:`Tamper.registry`
      instead would send :func:`binding` looking for reads *owned by*
      `window_axis_migration`; :func:`_reads` resolves that name to its
      from-import source, finds none, and answers ``DEF_TIME``, so
      :func:`control` short-circuits to ``UNREACHABLE`` with no reading at all
      (``0 -> 0`` before :data:`UNMEASURED`) and :func:`sites` is never
      called.  D-277: that reading is what the 07:00
      cycle of 2026-08-15 spent its overrun mis-attributing to the ``__main__``
      path, which `sites` in fact survives — it returns 49 under both.
    """
    from eval.mppi_sandbox import window_axis_migration as wam
    return Tamper(("window_axis_reach", "RESOLVERS"),
                  lambda original: tuple(
                      r for r in original if r[1] != "resolve"),
                  lambda: len(wam.sites()), "shrinks",
                  "window_axis_migration.sites",
                  bound_in="window_axis_migration")


def _hull_repaired_by() -> Tamper:
    """`extremum_reading.HULL_REPAIRED_BY` — the D-080 shape, unchanged.

    D-312 built an instrument to audit extremum readings and it joined the
    population it audits: two of its three functions carry typed allow-lists
    with no module-level enumerator, so ``unwatched_exemptions`` grew from six
    to eight within one test run.  This is the half that genuinely *is* an
    exemption — :func:`extremum_reading.unrepaired_hulls` drops keys that
    appear here and nothing puts them back — so it gets a control rather than
    a watcher, exactly as ``DECLARED_DEF_TIME`` and ``RESOLVERS`` did.

    Emptying the registry must make the hull reading name the site it was
    excusing: `calibrated_ladder.k_axis_bracket`'s hull is repaired by D-308's
    contiguity predicate, and with the repair off the record the reading goes
    from ``0`` unrepaired hulls to ``1``.  Reader and declarer coincide —
    `unrepaired_hulls` reaches the registry as a module attribute — so no
    :attr:`bound_in` split is needed.
    """
    from eval.mppi_sandbox import extremum_reading as er
    return Tamper(("extremum_reading", "HULL_REPAIRED_BY"),
                  lambda original: type(original)(),
                  lambda: len(er.unrepaired_hulls()), "grows",
                  "extremum_reading.unrepaired_hulls")


def _site_classes() -> Tamper:
    """`extremum_reading.SITE_CLASSES` — controlled even though it is *not* an exemption.

    D-313: this registry is on ``unwatched_exemptions`` because that scan
    matches populations **by name** and :func:`extremum_reading.sweep` binds
    its AST re-derivation to a local called ``found``.  The list is in fact
    reconciled in *both* directions — ``found_keys - SITE_CLASSES`` goes red as
    ``unregistered``, ``SITE_CLASSES - found_keys`` is reported as ``retired``
    — so calling it an allow-list is the scan's limit, not the module's hole.

    The control is written anyway, and the reason is the pin in
    `test_this_module_gives_the_four_unwatched_lists_a_control_not_a_watcher`:
    ``unwatched <= controlled`` is asserted, so a cycle that adds a typed list
    cannot leave it merely counted.  Paying that here also *demonstrates* the
    both-directions claim — dropping a registered key does not make the sweep
    quiet, it makes ``unregistered`` name the key that was dropped, which is
    the behaviour a one-directional allow-list could not produce.
    """
    from eval.mppi_sandbox import extremum_reading as er
    return Tamper(("extremum_reading", "SITE_CLASSES"),
                  lambda original: {k: v for k, v in original.items()
                                    if k != next(iter(sorted(original)))},
                  lambda: len(er.sweep()["unregistered"]), "grows",
                  "extremum_reading.sweep")


def _observables() -> Tamper:
    """`scene_separability.OBSERVABLES` — the D-080 shape, on a list nobody declared.

    D-339: the ninth entry on ``unwatched_exemptions``, and the first that
    arrived without any cycle adding a registry.  ``OBSERVABLES`` has been a
    module-level tuple since D-334; what changed is that D-338 made
    :func:`scene_separability.constant_at_every_index` read it **by name at the
    call site** instead of through a same-module helper.  Before that edit
    ``_provenance`` stopped at the helper and graded the exemption ``DERIVED``,
    which every ``TYPED`` screen skips — so the registry was unwatched *and*
    invisible, the strictly worse of the two states this census distinguishes.

    Shrinking the registry must move the constant-observable reading: drop
    `obstacle_speed` and :func:`scene_separability.obstacle_side_observables`
    goes from naming two always-constant observables to one.  That reading is
    the right target rather than the guard itself because it is the quantity
    D-336 concluded from — the control therefore demonstrates that the
    conclusion depends on the registry, not merely that the predicate does.

    Reader and declarer coincide (`obstacle_side_observables` reaches
    ``OBSERVABLES`` as a module global in its own module), so no
    :attr:`bound_in` split is needed — the `_resolvers` hazard does not apply.
    """
    from eval.mppi_sandbox import scene_separability as ss
    return Tamper(("scene_separability", "OBSERVABLES"),
                  lambda original: tuple(o for o in original
                                         if o != "obstacle_speed"),
                  lambda: len(ss.obstacle_side_observables()), "shrinks",
                  "scene_separability.obstacle_side_observables")


def _ttc_family() -> Tamper:
    """`scene_separability.TTC_FAMILY` — the tenth, and a *domain* declaration.

    D-349: D-347 named the two time-to-collision columns once so the family
    split would be a constant rather than a literal re-typed at each call
    site, which is exactly the move that makes a tuple visible to the
    ``TYPED`` screen — so the registry arrived on ``unwatched_exemptions``
    the moment it was written, without anybody intending an allow-list.  That
    is the same route ``OBSERVABLES`` took (D-339) and the second member of
    what is now clearly a category: a *domain* declaration, not an exemption,
    caught by a scan that matches populations by name.

    Controlled rather than argued out of the census, for the reason
    `test_this_module_gives_the_four_unwatched_lists_a_control_not_a_watcher`
    states: an exemption written to spare one registry is the hole this census
    exists to find.  Shrinking the family must move a reading that consumes
    the split — :func:`scene_separability.ttc_family_columns` goes from two
    columns to one.  That is the right target rather than
    :func:`ttc_family_has_the_heavier_tail`, whose ``bool`` does **not** move
    under the shrink (measured): the surviving single-member ``min(ttc)``
    still loses to ``max(rest)``, so a control pointed there would have been
    vacuous in the direction that matters and would have reported coverage it
    did not have.

    The reading is the count of tail-table columns
    :func:`scene_separability.is_ttc_family` admits, which is one frame wider
    than the predicate itself and is deliberate: a control that read the
    predicate at a single fixed name would move under the tamper only if that
    name happened to be the one dropped.  Counting over the live column set
    makes the control independent of *which* member the tamper removes.

    Reader and declarer coincide (`is_ttc_family` reaches ``TTC_FAMILY`` as a
    module global in its own module), so no :attr:`bound_in` split is needed —
    the `_resolvers` hazard does not apply.
    """
    from eval.mppi_sandbox import scene_separability as ss
    return Tamper(("scene_separability", "TTC_FAMILY"),
                  lambda original: tuple(o for o in original if o != "ttc"),
                  lambda: len([o for o in ss.tail_extensions_by_observable()
                               if ss.is_ttc_family(o)]), "shrinks",
                  "scene_separability.is_ttc_family")


def _vocabulary() -> Tamper:
    """`source_reach.VOCABULARY` — the tenth entrant, and the third arriving with its own auditor.

    D-419: D-417 shipped :func:`source_reach.vocabulary_gap`, whose
    ``set(name.split("_")) & VOCABULARY`` is the AND shape D-049 admits.  That
    one line enrolled the function in the guard population *and* put its typed
    registry on ``unwatched_exemptions`` — so the census of the census became a
    member of the census it audits, for the eighteenth consecutive cycle.  Four
    pins across four modules went red on the same edit and none of them was
    ``census_preempt``'s (D-318, second landing).

    Only one token in the registry is load-bearing for the reading, and that is
    worth stating rather than hiding behind a generic "drop the first element":
    dropping ``CLEARANCE`` or ``CLEARANCES`` moves :func:`vocabulary_gap` not at
    all (0 → 0), because every registered constant-backed source carrying a
    clearance token carries ``ENSEMBLE`` as well.  Dropping ``ENSEMBLE`` takes
    the gap 0 → 2.  A control that shrank the registry by its sorted-first
    element would therefore have been **vacuous** — green, and measuring
    nothing — which is precisely the failure `test_no_control_is_vacuous`
    exists to catch.  The tamper names ``ENSEMBLE`` for that reason.

    Reader and declarer coincide (:func:`vocabulary_gap` reaches ``VOCABULARY``
    as a module global in its own module), so no :attr:`bound_in` split is
    needed — the `_resolvers` hazard does not apply.
    """
    from eval.mppi_sandbox import source_reach as sr
    return Tamper(("source_reach", "VOCABULARY"),
                  lambda original: type(original)(
                      t for t in original if t != "ENSEMBLE"),
                  lambda: len(sr.vocabulary_gap()), "grows",
                  "source_reach.vocabulary_gap")


#: Every tamper this module knows how to build.  Deliberately a list of
#: **factories**, not values: a tamper closes over the live registry, and
#: building them at import time would freeze a population the control is
#: supposed to read fresh.
TAMPERS: tuple[Callable[[], Tamper], ...] = (
    _self_defining,
    _carried_fields,
    _name_scope_claims,
    _scoped_claims,
    _degenerate_readings,
    _temperature_relevant,
    _excluded_tests_pv,
    _declared_def_time,
    _tree_suffixes,
    _tree_skip,
    _resolvers,
    _hull_repaired_by,
    _site_classes,
    _observables,
    _ttc_family,
    _vocabulary,
)


def _live_module(mod_name: str):
    """The module object the *readers* see, not a fresh copy of it.

    ``python -m eval.mppi_sandbox.exemption_control`` runs this file as
    ``__main__``; :func:`importlib.import_module` then loads a **second,
    independent** copy under the real dotted name, and patching that copy is
    invisible to a reader executing in ``__main__``.  That misgraded this
    module's own registry as ``INERT`` on the ``__main__`` path while the same
    control read ``BITES`` under a normal import — a negative control whose
    verdict depended on how it was launched, which is precisely the class of
    defect this module exists to find.
    """
    target = PACKAGE / f"{mod_name}.py"
    main = sys.modules.get("__main__")
    main_file = getattr(main, "__file__", None)
    if main_file and Path(main_file).resolve() == target:
        return main
    return importlib.import_module(f"eval.mppi_sandbox.{mod_name}")


def control(tamper: Tamper) -> Control:
    """Run one negative control, restoring the registry unconditionally."""
    mod_name, attr = tamper.registry
    module = _live_module(tamper.bound_in or mod_name)
    if binding(tamper.registry) != CALL_TIME:
        return Control(f"{mod_name}.{attr}", tamper.reader,
                       VERDICT_UNREACHABLE, None, None,
                       note="read only at def time — no name-level control exists")
    original = getattr(module, attr)
    baseline = tamper.read()
    try:
        setattr(module, attr, tamper.patch(original))
        tampered = tamper.read()
    finally:
        setattr(module, attr, original)
    moved = (tampered > baseline) if tamper.expect == "grows" else (tampered < baseline)
    return Control(f"{mod_name}.{attr}", tamper.reader,
                   VERDICT_BITES if moved else VERDICT_INERT,
                   baseline, tampered,
                   note="" if moved else f"expected the reading to {tamper.expect}")


def controls() -> tuple[Control, ...]:
    """Every declared control, run."""
    return tuple(control(build()) for build in TAMPERS)


def inert(scored: tuple[Control, ...] | None = None) -> tuple[str, ...]:
    """Registries whose tamper moved no reading — the failures.

    Distinct from :func:`unreachable`: an ``INERT`` registry *is* read at call
    time and still nothing noticed, which means either the reader is the wrong
    one or the guard downstream is not wired to it.  Both need a human.
    """
    scored = controls() if scored is None else scored
    return tuple(sorted(c.registry for c in scored if c.verdict == VERDICT_INERT))


def unreachable(package: Path | None = None) -> tuple[str, ...]:
    """Registries no monkeypatch of their name can reach.

    Not a defect on its own — a default argument is a legitimate way to make a
    registry overridable per call.  It *is* a limit on what any negative control
    over that name can claim, and the limit is what this reports.
    """
    return tuple(sorted(f"{m}.{n}" for m, n in REGISTRIES
                        if binding((m, n), package) != CALL_TIME))


def undeclared_unreachable(package: Path | None = None) -> tuple[str, ...]:
    """``UNREACHABLE`` registries with neither a fix nor a written reason.

    :func:`unreachable` reports a *limit*; this reports the limits nobody has
    accounted for.  A registry may legitimately be default-arg-only — but then
    :data:`DECLARED_DEF_TIME` has to say so and say why, which is the whole of
    Q-085's option (b).  Non-empty means the package is carrying an
    uncontrollable registry silently, which is the state D-079 found and D-080
    is meant to end.
    """
    return tuple(n for n in unreachable(package) if n not in DECLARED_DEF_TIME)


def uncontrolled() -> tuple[str, ...]:
    """Entries of :data:`REGISTRIES` with neither a tamper nor an excuse.

    The honest complement of :func:`controls`.  Empty here only because
    :func:`unreachable` absorbs ``guard_vacuity.EXCLUDED_TESTS``; if a future
    registry joins :data:`REGISTRIES` without a tamper, this names it rather
    than letting the census read complete.
    """
    covered = {f"{t().registry[0]}.{t().registry[1]}" for t in TAMPERS}
    covered |= set(unreachable())
    return tuple(sorted(f"{m}.{n}" for m, n in REGISTRIES
                        if f"{m}.{n}" not in covered))


#: How a reading that does not exist is rendered.  Shared by both halves of
#: :func:`report` so the short-circuited controls and the never-controllable
#: registries below them read the same way, rather than one printing a number.
UNMEASURED = "—"


def report() -> str:
    lines = ["registry                              reader                              verdict   base -> tampered"]
    for c in controls():
        reading = f"{c.baseline} -> {c.tampered}" if c.measured else UNMEASURED
        lines.append(f"{c.registry:<38}{c.reader:<36}{c.verdict:<10}{reading}")
    for name in unreachable():
        why = DECLARED_DEF_TIME.get(name, "(default-arg only)")
        lines.append(f"{name:<38}{why[:34]:<36}{VERDICT_UNREACHABLE:<10}{UNMEASURED}")
    if undeclared_unreachable():
        lines.append(f"undeclared unreachable: {', '.join(undeclared_unreachable())}")
    if uncontrolled():
        lines.append(f"uncontrolled: {', '.join(uncontrolled())}")
    return "\n".join(lines)


if __name__ == "__main__":                                  # pragma: no cover
    print(report())
