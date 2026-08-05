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

What it found on the first run is not a per-registry verdict but a structural
one, and it partitions the seven:

**Two of the seven cannot be negative-controlled through their own name at
all.**  ``predicate_vacuity.EXCLUDED_TESTS`` and ``guard_vacuity.EXCLUDED_TESTS``
are each read in exactly one place — an ``excluded: Sequence[str] =
EXCLUDED_TESTS`` **default argument**, evaluated once at ``def`` time and bound
into the function object.  Rebinding the module global afterwards changes
nothing any caller can observe, so no monkeypatch of that name is a control over
those readers; the only way in is to pass ``excluded=`` explicitly, which
controls the *parameter*, not the *registry*.  That is a real and cheap
distinction to have written down: a registry consumed only as a default is one
whose name is decorative at every site but its own.

So the reading is two-layer, and the static layer runs first because it decides
whether the dynamic layer means anything:

1. :func:`references` / :func:`binding` — where is the registry read, and is the
   read ``CALL_TIME`` or ``DEF_TIME``?  A registry with no ``CALL_TIME`` read
   outside its own module is ``UNREACHABLE``.
2. :func:`control` — for the reachable ones, patch the global, call a reader
   that returns an integer, restore, and report the delta.

:data:`CONTROLS` is itself a hand-typed registry of tampers, which is the
recursion this package keeps meeting.  It is not hidden: it is enumerated,
:func:`uncontrolled` names every registry in :data:`REGISTRIES` that it omits,
and the omission list is the module's own work list rather than its clearance.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
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


def _reads(name: str, tree: ast.AST) -> list[ast.AST]:
    """Load-context references to ``name``, bare or as ``mod.NAME``.

    The assignment that *defines* the registry is a ``Store`` and is excluded:
    a registry always names itself once, and counting that as a read would make
    every registry look reachable from its own definition.
    """
    out: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            if isinstance(node.ctx, ast.Load):
                out.append(node)
        elif isinstance(node, ast.Attribute) and node.attr == name:
            if isinstance(node.ctx, ast.Load):
                out.append(node)
    return out


def references(registry: tuple[str, str],
               package: Path | None = None) -> tuple[Reference, ...]:
    """Every read of ``registry`` across the package's modules.

    Scans modules only.  ``tests/`` is deliberately out of scope: a test that
    reads the name is the layer this module is trying to *validate*, not part of
    the surface a tamper has to reach.
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
        for node in _reads(name, tree):
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


@dataclass(frozen=True)
class Control:
    """One negative control, run."""

    registry: str
    reader: str
    verdict: str
    baseline: int
    tampered: int
    note: str = ""

    @property
    def delta(self) -> int:
        return self.tampered - self.baseline


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
)


def control(tamper: Tamper) -> Control:
    """Run one negative control, restoring the registry unconditionally."""
    mod_name, attr = tamper.registry
    module = importlib.import_module(f"eval.mppi_sandbox.{mod_name}")
    if binding(tamper.registry) != CALL_TIME:
        return Control(f"{mod_name}.{attr}", tamper.reader,
                       VERDICT_UNREACHABLE, 0, 0,
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


def uncontrolled() -> tuple[str, ...]:
    """Entries of :data:`REGISTRIES` with neither a tamper nor an excuse.

    The honest complement of :func:`controls`.  Empty here only because
    :func:`unreachable` absorbs the two ``EXCLUDED_TESTS`` registries; if a
    future registry joins :data:`REGISTRIES` without a tamper, this names it
    rather than letting the census read complete.
    """
    covered = {f"{t().registry[0]}.{t().registry[1]}" for t in TAMPERS}
    covered |= set(unreachable())
    return tuple(sorted(f"{m}.{n}" for m, n in REGISTRIES
                        if f"{m}.{n}" not in covered))


def report() -> str:
    lines = ["registry                              reader                              verdict   base -> tampered"]
    for c in controls():
        lines.append(f"{c.registry:<38}{c.reader:<36}{c.verdict:<10}{c.baseline} -> {c.tampered}")
    for name in unreachable():
        lines.append(f"{name:<38}{'(default-arg only)':<36}{VERDICT_UNREACHABLE:<10}—")
    if uncontrolled():
        lines.append(f"uncontrolled: {', '.join(uncontrolled())}")
    return "\n".join(lines)


if __name__ == "__main__":                                  # pragma: no cover
    print(report())
