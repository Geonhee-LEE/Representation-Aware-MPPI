# SPDX-License-Identifier: BSD-3-Clause
"""A census of the census: which modules *hold* a per-seed ensemble, derived.

:mod:`recorded_clearance` answers "which scenes have a recorded per-seed
clearance ensemble" by calling a hand-written tuple of readers,
:data:`recorded_clearance.SOURCES`. That set has now been wrong **twice in
three cycles**, and the second time is the one that matters, because it was
wrong *after* being converted from a literal to a derivation:

- D-413 replaced a one-element literal (`RECORDED_SCENES`) with
  `recorded_scenes()`, derived from the readers.
- D-416 then found `scene_census.PAIRED_ENSEMBLE` — 8 seeds x 2 arms on
  `cafe_convoy_v0` — was never registered as a reader, so the derivation missed
  it too.

The reason no guard caught it is structural and worth stating once. `declared`
came *from* `derived` (`RECORDED_SCENES = recorded_scenes()`), so an
unregistered reader shrinks both sides together and `drift()` returns
`IN_SYNC` — live, green, and blind. **Comparing two sets can only find
disagreement; it can never find a gap the two share.** Breaking that requires a
third reading taken from somewhere neither side controls, which is the tree
itself.

So this module does not ask the registry anything. It walks the package source
with :mod:`ast`, finds module-level constants that *structurally are* seed-
indexed float ensembles, and grades :data:`recorded_clearance.SOURCES` against
what it found. Nothing is imported and nothing is executed — every input is a
literal already sitting in the tree, so the whole census costs milliseconds and
cannot be perturbed by an import side effect.

What the scan can see, and what it cannot
-----------------------------------------

The structural test alone (a module-level ``UPPER_CASE`` constant whose leaves
include a float row of width >= :data:`recorded_clearance.MIN_SEEDS`) matches
**82** constants across the package. That is not a signal — it sweeps in ladder
grids, ESS bands, seed lists, timing ratios and threshold tables, none of which
are clearance ensembles. Publishing 82 "unregistered ensembles" would be a
census nobody reads, which is the failure mode D-044 names.

The narrowing is :data:`VOCABULARY`, and it is **typed**, not derived. That is a
real limit and it is stated here rather than hidden, per D-318: a check whose
scope is narrower than it looks reads exactly like a clean one. Two things keep
the limit honest:

1. :func:`uncovered` returns every structurally-shaped constant the vocabulary
   filtered out, and :func:`format_grade` prints the count. The omission is
   loud by construction.
2. :func:`vocabulary_gap` grades the vocabulary against the registry itself —
   every *constant-backed* source already in :data:`recorded_clearance.SOURCES`
   must match the vocabulary. If a future reader registers an ensemble named
   outside it, that is a failure here, not a silent narrowing. The vocabulary
   cannot quietly stop covering the set it exists to audit.

The graded direction
--------------------

Only :data:`UNREGISTERED` convicts — a constant that looks like a per-seed
ensemble and that no registered reader accounts for. That is the direction that
*under-reports coverage*, and under-reported coverage is what sends a cycle to
re-measure a scene the tree already measured (D-416, and D-412 one layer up).

The reverse, :data:`UNSCANNED` — a registered source this scan cannot see — is
reported and **not** an error. It has a legitimate population of exactly the
kind `separation_reproduction.published_census()` represents: an ensemble
assembled by a function rather than parked in one literal. The scan is
deliberately literal-only; calling into the package to resolve those would
reintroduce the import coupling this module exists to avoid.

Usage::

    python3 -m eval.mppi_sandbox.source_reach
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from .recorded_clearance import MIN_SEEDS

#: The package whose module-level constants are scanned.
PACKAGE = Path(__file__).resolve().parent

#: Name tokens that mark a constant as *a clearance ensemble* rather than some
#: other float table. Typed, not derived — see the module docstring. Held to
#: the registry by :func:`vocabulary_gap`, which fails if a registered
#: constant-backed source ever falls outside it.
VOCABULARY: frozenset[str] = frozenset({"ENSEMBLE", "CLEARANCE", "CLEARANCES"})

#: Verdicts.
IN_SYNC = "IN_SYNC"
#: A vocabulary-matching constant in a module **no** registered reader touches.
#: The under-reporting direction, and the only conviction.
UNREGISTERED = "UNREGISTERED"
#: A registered source with no literal constant behind it (e.g. a function).
#: Reported, never convicted.
UNSCANNED = "UNSCANNED"
#: A constant whose module *is* registered but which the reader does not name.
#: Reported, never convicted — one reader legitimately aggregates several
#: constants, which is exactly what `separation_reproduction.published_census()`
#: does over the four `W*_CLEARANCES` tables.
UNNAMED = "UNNAMED"


@dataclass(frozen=True)
class Site:
    """One module-level constant that structurally holds seed-indexed floats."""

    #: Module stem, e.g. ``scene_census``.
    module: str
    #: Constant name, e.g. ``PAIRED_ENSEMBLE``.
    name: str
    #: Widest float row found under it — the seed count, at its most generous.
    width: int
    #: Container type of the constant itself.
    kind: str

    @property
    def qualname(self) -> str:
        """``module.NAME`` — the form `recorded_clearance.Ensemble.source` uses."""
        return f"{self.module}.{self.name}"

    @property
    def in_vocabulary(self) -> bool:
        """Does the constant's name carry a clearance-ensemble token?"""
        return bool(set(self.name.split("_")) & VOCABULARY)

    def __str__(self) -> str:
        return f"{self.qualname}: width {self.width} ({self.kind})"


def _row_width(value: object) -> int:
    """Widest tuple-of-floats anywhere under ``value``; 0 if there is none.

    Recurses through dicts, lists and tuples so a nested ensemble
    (``{(scene, arm): (baseline_row, challenger_row)}``) reports its *row*
    width rather than the width of the pair holding it.
    """
    if isinstance(value, (tuple, list)):
        if value and all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in value
        ):
            return len(value)
        return max((_row_width(x) for x in value), default=0)
    if isinstance(value, dict):
        return max((_row_width(x) for x in value.values()), default=0)
    return 0


def _constants(path: Path) -> tuple[tuple[str, object, str], ...]:
    """Every module-level ``UPPER_CASE`` constant with a literal value.

    Non-literal right-hand sides (calls, comprehensions, names) are skipped:
    resolving them would mean importing, and the point of the scan is to read
    the tree without running it.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):  # pragma: no cover -- unreadable source
        return ()
    out: list[tuple[str, object, str]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                continue
            name, value_node = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name) or node.value is None:
                continue
            name, value_node = node.target.id, node.value
        else:
            continue
        if not name.isupper():
            continue
        try:
            value = ast.literal_eval(value_node)
        except (ValueError, SyntaxError, TypeError):
            continue
        out.append((name, value, type(value).__name__))
    return tuple(out)


def sites(package: Path | None = None) -> tuple[Site, ...]:
    """Every module-level constant structurally shaped like a seed ensemble.

    Structural only — no vocabulary filter. This is the broad population;
    :func:`ensemble_sites` is the narrowed one and :func:`uncovered` is the
    difference between them.
    """
    root = PACKAGE if package is None else package
    found: list[Site] = []
    for path in sorted(root.glob("*.py")):
        for name, value, kind in _constants(path):
            width = _row_width(value)
            if width >= MIN_SEEDS:
                found.append(Site(module=path.stem, name=name, width=width, kind=kind))
    return tuple(found)


def ensemble_sites(package: Path | None = None) -> tuple[Site, ...]:
    """The :func:`sites` whose names carry :data:`VOCABULARY` tokens."""
    return tuple(s for s in sites(package) if s.in_vocabulary)


def uncovered(package: Path | None = None) -> tuple[Site, ...]:
    """The :func:`sites` the vocabulary filtered out — the scan's blind spot.

    Returned rather than discarded so the narrowing is a reading a caller can
    print, not an assumption buried in a filter (D-318).
    """
    return tuple(s for s in sites(package) if not s.in_vocabulary)


def registered() -> tuple[str, ...]:
    """Every ``module.NAME`` that :data:`recorded_clearance.SOURCES` reports.

    Read from the live readers rather than from their source text, so a reader
    that re-pins itself moves this set with it — the same discipline
    `recorded_clearance` applies to scenes.
    """
    from .recorded_clearance import ensembles

    return tuple(sorted({e.source for e in ensembles()}))


def _is_constant_backed(source: str) -> bool:
    """Does a registered source name a literal constant rather than a call?"""
    return not source.endswith(")")


@dataclass(frozen=True)
class Reach:
    """The tree's ensemble sites graded against the registry."""

    found: tuple[Site, ...]
    declared: tuple[str, ...]

    @property
    def _declared_modules(self) -> frozenset[str]:
        """Module stems any registered reader draws from."""
        return frozenset(d.split(".", 1)[0] for d in self.declared)

    @property
    def unregistered(self) -> tuple[Site, ...]:
        """Sites in modules **no** registered reader touches — the conviction.

        Module-level rather than constant-level on purpose. A reader may
        legitimately aggregate several constants of its own module, so a
        constant the reader does not name is weak evidence; a whole module the
        registry has never heard of is not.
        """
        known = set(self.declared)
        modules = self._declared_modules
        return tuple(
            s
            for s in self.found
            if s.qualname not in known and s.module not in modules
        )

    @property
    def unnamed(self) -> tuple[Site, ...]:
        """Sites whose module is registered but which no reader names."""
        known = set(self.declared)
        modules = self._declared_modules
        return tuple(
            s for s in self.found if s.qualname not in known and s.module in modules
        )

    @property
    def unscanned(self) -> tuple[str, ...]:
        """Registered sources with no literal constant behind them."""
        seen = {s.qualname for s in self.found}
        return tuple(d for d in self.declared if d not in seen)

    @property
    def verdict(self) -> str:
        if self.unregistered:
            return UNREGISTERED
        if self.unnamed:
            return UNNAMED
        if self.unscanned:
            return UNSCANNED
        return IN_SYNC

    @property
    def in_sync(self) -> bool:
        """Only :data:`UNREGISTERED` is a failure; see the module docstring."""
        return not self.unregistered


def reach(package: Path | None = None) -> Reach:
    """Grade :data:`recorded_clearance.SOURCES` against the tree."""
    return Reach(found=ensemble_sites(package), declared=registered())


def vocabulary_gap() -> tuple[str, ...]:
    """Registered constant-backed sources whose names miss :data:`VOCABULARY`.

    Non-empty means the typed vocabulary has stopped covering the very registry
    it narrows — the narrowing would then be silently dropping registered
    ensembles, which is exactly the failure this module was built to make
    impossible. Graded by the tests.
    """
    out: list[str] = []
    for source in registered():
        if not _is_constant_backed(source):
            continue
        name = source.rsplit(".", 1)[-1]
        if not set(name.split("_")) & VOCABULARY:
            out.append(source)
    return tuple(out)


def format_grade(package: Path | None = None) -> str:
    r = reach(package)
    skipped = uncovered(package)
    lines = [
        f"source reach — {len(r.found)} ensemble-shaped sites "
        f"(>= {MIN_SEEDS} seeds, name in {sorted(VOCABULARY)}), "
        f"{len(r.declared)} registered sources",
        "",
    ]
    known = set(r.declared)
    unnamed = {s.qualname for s in r.unnamed}
    for s in r.found:
        mark = "ok " if s.qualname in known else ("~  " if s.qualname in unnamed else "NEW")
        lines.append(f"  [{mark}] {s}")
    lines.append("")
    lines.append(f"  verdict: {r.verdict}")
    if r.unregistered:
        lines.append(
            "  UNREGISTERED (module has no reader at all): "
            + ", ".join(s.qualname for s in r.unregistered)
        )
    if r.unnamed:
        lines.append(
            "  UNNAMED (module registered, constant not named): "
            + ", ".join(s.qualname for s in r.unnamed)
        )
    if r.unscanned:
        lines.append(
            "  UNSCANNED (registered, not a literal constant): "
            + ", ".join(r.unscanned)
        )
    lines.append(
        f"  UNCOVERED: {len(skipped)} structurally-shaped constants carry no "
        f"{sorted(VOCABULARY)} token and were not graded"
    )
    return "\n".join(lines)


def main() -> int:
    print(format_grade())
    return 0 if reach().in_sync else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
