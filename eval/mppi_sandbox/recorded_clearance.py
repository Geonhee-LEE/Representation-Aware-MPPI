# SPDX-License-Identifier: BSD-3-Clause
"""Which scenes actually hold a per-seed clearance ensemble — derived, not typed.

`scene_eligibility` reports the successor question's coverage as *N of the
eligible scenes are measured*, and it decided membership with a one-element
literal::

    RECORDED_SCENES: frozenset[str] = frozenset({PUBLISHED_SCENARIO})

The comment above it takes D-047 seriously about the **name** — `PUBLISHED_SCENARIO`
is imported rather than spelled, so the two cannot drift on spelling. It does not
take it seriously about the **membership**, and that is the half that moved. The
repo holds *two* per-seed clearance ensembles, not one:

- `separation_reproduction`'s rungs — 32 seeds on `cafe_head_on_v0`, which is
  the scene the literal names; and
- `clearance_census.SEED_ENSEMBLE` — **8 seeds × 8 arms on `cafe_freezing_v0`**,
  which the literal has never named.

So the literal under-reports by one scene. Today that costs nothing, and *that
is the hazard rather than the reassurance*: `cafe_freezing_v0` is excluded from
the census under `NO_DECLARED_MARGIN`, and `measured` is `eligible and scenario
in RECORDED_SCENES`, so the missing member is masked by an exclusion and every
printed count is right by accident. The masking is not stable. STATE's own
third claude-actionable is `freeze-margin` — *decide whether `cafe_freezing_v0`
declares a `min_distance_to_obstacle`* — and it is a one-line yaml edit. The
cycle that lands it flips the scene to eligible, and on the next line the census
would report it **unmeasured** while an 8×8 ensemble for it sits in
`clearance_census`. The bottleneck sentence would then name a scene to go
measure that has already been measured, which is the D-412 failure exactly one
layer down: a true sentence that is a false lead.

This module is the derivation. Each entry in :data:`SOURCES` is a *reader*, not
a copy: it calls into the module that owns the ensemble and reports the scene
that module says it is pinned to, so a source that re-pins itself moves this
census with it and a source that is deleted stops contributing. Nothing here
re-simulates — every input is already a constant in the tree, and the whole
census costs milliseconds.

Reported, never thresholded, for the population (D-044/D-107): a scene with an
ensemble is listed with its seed count, and the seed count is what a reader
needs in order to know whether "measured" means 32 seeds or 8. Collapsing that
to a boolean is what let a one-element set stand for two years of ensembles.

The one graded statement is :func:`drift`, and it is graded in the direction
that can be wrong: it convicts when a *derived* scene is missing from a caller's
typed set, because that is the direction that under-reports coverage. A typed
set naming a scene this module cannot find is reported too — as `UNSOURCED` —
but it is not an error here, since an ensemble may live in a module this
registry has not yet been taught to read. `UNSOURCED` names the gap out loud so
that the omission cannot read as a clean census, which is the D-318 lesson about
a check whose scope is narrower than it looks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

#: A scene is "per-seed measured" only with **more than one** seed. A single
#: run is a reading, not an ensemble, and every scene in `runs/*.json` has
#: exactly one (seed 0) — folding those in would mark all eight scenes measured
#: and make the coverage count meaningless.
MIN_SEEDS = 2

#: Verdicts.
IN_SYNC = "IN_SYNC"
#: A scene this module derives is absent from the caller's typed set — the
#: under-reporting direction, and the only one graded.
MISSING = "MISSING"
#: The caller's set names a scene no registered source accounts for. Reported,
#: not convicted: the ensemble may live somewhere this registry cannot read.
UNSOURCED = "UNSOURCED"


@dataclass(frozen=True)
class Ensemble:
    """One recorded per-seed clearance ensemble, as its owning module reports it."""

    #: Where it lives, for a reader who wants to go look.
    source: str
    #: The scene the source module says the ensemble was taken on.
    scenario: str
    #: How many distinct seeds it spans.
    n_seeds: int
    #: How many arms were walked at each seed.
    n_arms: int

    def __str__(self) -> str:
        return (f"{self.scenario}: {self.n_seeds} seeds x {self.n_arms} arms "
                f"({self.source})")


def _from_clearance_census() -> Ensemble:
    """`clearance_census.SEED_ENSEMBLE` — the 8x8 the literal never named.

    Scene is read from the module's own `PEAK_SCENE` re-export rather than
    spelled, so re-pinning the census re-pins this row.
    """
    from . import clearance_census as cc

    rows = cc.SEED_ENSEMBLE
    widths = {len(v) for v in rows.values()}
    return Ensemble(
        source="clearance_census.SEED_ENSEMBLE",
        scenario=cc.PEAK_SCENE,
        n_seeds=min(widths) if widths else 0,
        n_arms=len(rows),
    )


def _from_separation_reproduction() -> Ensemble:
    """`separation_reproduction`'s published rungs — 32 seeds, both arms.

    The scene is taken off each rung's own `Headroom`, which is the field the
    rung carries; the seed count is the union of every rung's reference and
    replication seed lists, which is the field `SeedBlock` exists to carry.
    A census spanning two scenes would be a bug in the source rather than a
    reading this module may average, so it raises rather than picking one.
    """
    from . import separation_reproduction as sr

    census = sr.published_census()
    seeds: set[int] = set()
    scenes: set[str] = set()
    for _weight, rep in census.reproductions:
        seeds.update(rep.seeds)
        scenes.add(rep.pooled.scenario)
    if len(scenes) != 1:
        raise ValueError(
            f"published_census() spans {sorted(scenes)} — a per-scene "
            "coverage row cannot be derived from a multi-scene census"
        )
    return Ensemble(
        source="separation_reproduction.published_census()",
        scenario=scenes.pop(),
        n_seeds=len(seeds),
        n_arms=2,
    )


#: Every module known to hold a per-seed clearance ensemble. Adding an ensemble
#: to the tree without adding it here is the failure this module exists to make
#: visible once — `UNSOURCED` in the other direction, and a stale `MISSING` in
#: this one. The list is short on purpose: it is a registry of *readers*, and a
#: reader that stops resolving is a loud `ImportError`, not a silent drop.
SOURCES: tuple[Callable[[], Ensemble], ...] = (
    _from_clearance_census,
    _from_separation_reproduction,
)


def ensembles() -> tuple[Ensemble, ...]:
    """Every registered ensemble, read from its owning module."""
    return tuple(sorted((src() for src in SOURCES),
                        key=lambda e: (e.scenario, e.source)))


def recorded_scenes() -> frozenset[str]:
    """Scenes with at least :data:`MIN_SEEDS` seeds of recorded clearance."""
    return frozenset(e.scenario for e in ensembles() if e.n_seeds >= MIN_SEEDS)


@dataclass(frozen=True)
class Drift:
    """A caller's typed set graded against the derivation."""

    derived: frozenset[str]
    declared: frozenset[str]

    @property
    def missing(self) -> frozenset[str]:
        """Derived but not declared — the under-reporting direction."""
        return self.derived - self.declared

    @property
    def unsourced(self) -> frozenset[str]:
        """Declared but not derived — reported, not convicted."""
        return self.declared - self.derived

    @property
    def verdict(self) -> str:
        if self.missing:
            return MISSING
        if self.unsourced:
            return UNSOURCED
        return IN_SYNC

    @property
    def in_sync(self) -> bool:
        """Only `MISSING` is a failure; see the module docstring."""
        return not self.missing


def drift(declared: frozenset[str] | None = None) -> Drift:
    """Grade `scene_eligibility.RECORDED_SCENES` (or a given set) against source."""
    if declared is None:
        from .scene_eligibility import RECORDED_SCENES

        declared = RECORDED_SCENES
    return Drift(derived=recorded_scenes(), declared=frozenset(declared))


def format_grade() -> str:
    rows = ensembles()
    d = drift()
    lines = [f"recorded clearance — {len(rows)} ensembles, "
             f"{len(d.derived)} scenes at >= {MIN_SEEDS} seeds",
             ""]
    lines += [f"  {e}" for e in rows]
    lines.append("")
    lines.append(f"  verdict: {d.verdict}")
    if d.missing:
        lines.append(f"  MISSING from the declared set: {', '.join(sorted(d.missing))}")
    if d.unsourced:
        lines.append(f"  UNSOURCED (declared, no registered reader): "
                     f"{', '.join(sorted(d.unsourced))}")
    return "\n".join(lines)


def main() -> int:
    print(format_grade())
    return 0 if drift().in_sync else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
