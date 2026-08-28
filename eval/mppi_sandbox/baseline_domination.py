# SPDX-License-Identifier: BSD-3-Clause
"""Is any single arm non-dominated on the north star? — the P5 baseline question.

`STATE.md` has carried *"Choose P5's baseline controller"* as `Next
claude-actionable` #1 for three cycles, with a stated cheap first cut: read
:func:`baseline_matrix.reportable_surface` together with the per-arm `cte_*` and
clearance censuses already on disk and check whether **any single arm is
non-dominated on the north-star metrics across the completable scenes**. STATE
also named the fork in advance: *"If one is, the baseline is chosen; if none is,
that is itself the P5 finding and the report needs a per-class contract rather
than a single baseline."*

This module takes that reading. **The answer is the second branch**, and it is
not close.

**1. On the joint surface every distinct arm is non-dominated.** Over the four
scenes where both north-star axes are recorded, no arm dominates any other:
every distinct pair has each side winning at least two of the eight columns.
The Pareto frontier is the *entire registry*. There is no single-baseline
choice to make, and the reason is the tension :mod:`cte_vacuity` already named
from one side — the arm that buys clearance is the arm that loses cross-track.

**2. One "non-domination" is duplication, not tradeoff, and it had to be
separated out.** `geometric_mppi` and `stock_mppi` are **bit-identical on all
eight joint columns** (0-0 in the pairwise win table). Two identical arms are
mutually non-dominated by construction, so a frontier count that includes both
overstates the frontier's width by one. :func:`duplicates` reports the classes
and :attr:`Verdict.distinct_frontier` collapses them — **7 distinct arms**, not
8. This is the same inert-channel signature :mod:`clearance_census` pinned
(`geometric_mppi` reproduces the baseline in all three of *its* columns); it
reproduces it here too, on a disjoint column set, which is independent
confirmation that the geometric channel does not bite.

**3. Read one axis at a time and you get a decisive — and contradictory —
answer, which is why the joint read is the one that counts.** On clearance
alone `cbf_mppi` dominates **all seven** other arms outright. On cross-track
alone it is dominated, and the frontier is `essps_mppi` / `frozen_risk_mppi` /
`risk_mppi`. So each single-axis reading nominates a baseline, the two
nominations are disjoint, and a P5 report that quoted either in isolation would
name a "winner" the other axis refutes. The north star demands both at once.

Scope, stated before the numbers because it bounds them hard:

* **Seed 0.** Both source censuses are seed-0 columns
  (:data:`cte_vacuity.CTE_SEED0`, :func:`threshold_vacuity.attained`). A
  frontier is a statement about *ranking*, and seed-0 rankings are the weakest
  evidence this branch has; :data:`WIDENING_UNBOUGHT` prices the re-take rather
  than leaving the gap silent. Finding #1 is soft in the *safe* direction —
  more seeds can only add tradeoffs, never remove them, so a frontier that is
  already the whole registry cannot shrink into a single baseline.
* **Four of eight completable scenes.** The two axes do not cover the same
  surface and neither covers all of it — see :func:`coverage`. Clearance is not
  *posed* on three scenes (zero obstacles, every arm clears `+inf`) and
  `cafe_obstacle_contested_v0` has no recorded `cte_rms` column at all. The
  joint surface is their intersection, and it is derived here rather than
  typed so a new census moves it in the same commit.
* **One joint cell is inadmissible**, and it belongs to the clearance winner.
  `reportable_surface().empty` is exactly `cbf_mppi × cafe_obstacle_crossing_v0`
  — the single empty window in the reportable 64 (D-482/Q-206: structurally
  negative, 17 temperatures × 8 seeds, best 6/8 against an 8/8 bar). So one of
  `cbf_mppi`'s four joint scenes contributes numbers taken at a temperature the
  calibration table does not admit. :func:`inadmissible_joint_cells` derives
  this rather than asserting the frontier is clean; it does not change finding
  #1 (dropping the scene leaves the frontier the whole registry) but it does
  bound how hard finding #3's `cbf_mppi` sweep may be quoted.

**What this does not do.** It does not rank the arms and it does not pick a
baseline, because the reading is that neither is available from what is on
disk. Time-to-goal and smoothness — two of the north star's four 경로추종
clauses — have **no** per-arm-per-scene census in the tree at all
(:data:`UNCENSUSED_AXES`), so even the two-axis frontier here is a *lower*
bound on the true tradeoff width.

CLI:
    python -m eval.mppi_sandbox.baseline_domination   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

#: North-star axes named in `CLAUDE.md` that have **no** per-arm-per-scene
#: census on disk. Pinned as a constant rather than left as a silence: the
#: frontier below is computed on two axes, and a reader who does not know the
#: other two are missing will read "the whole registry is non-dominated" as a
#: complete statement when it is a partial one.
UNCENSUSED_AXES: tuple[str, ...] = ("time_to_goal", "smoothness")

#: Rollouts a full eight-seed re-take of both columns would cost, unbought this
#: cycle. `8 seeds × 8 arms × 4 joint scenes`, less the seed-0 column already on
#: disk. Same convention as :data:`cte_vacuity.WIDENING_UNBOUGHT`.
WIDENING_UNBOUGHT: int = 8 * 8 * 4 - 8 * 4

#: The census this module pins. Each entry is a fact the suite should fail on
#: if it moves silently, because each is load-bearing for the P5 report.
CENSUS: dict[str, str] = {
    "joint_frontier": "ALL_DISTINCT_ARMS",
    "clearance_frontier": "cbf_mppi",
    "cte_frontier": "essps_mppi,frozen_risk_mppi,risk_mppi",
    "duplicate_class": "geometric_mppi,stock_mppi",
    "joint_scenes": "4",
    "distinct_frontier_width": "7",
}


def _clearance_column(scene: str) -> dict[str, float]:
    """Per-arm attained clearance, higher-is-better. `{}` if not posed."""
    from .threshold_vacuity import attained

    return dict(attained(scene))


def _cte_column(scene: str) -> dict[str, float]:
    """Per-arm cross-track RMS, **negated** so higher-is-better like clearance.

    Sign normalisation happens here, once, rather than at each comparison site:
    a clearance bar is a floor and a cross-track bar is a ceiling
    (:mod:`cte_vacuity` finding #2), and a domination test that got one of the
    two directions backwards would silently invert the frontier.
    """
    from .cte_vacuity import CTE_SEED0

    return {arm: -v for arm, v in CTE_SEED0.get(scene, {}).items()}


def arms() -> tuple[str, ...]:
    """The controllers the calibration table can be quoted over.

    Read from :func:`baseline_matrix.reportable_surface`, not from `REGISTRY`,
    for that function's own stated reason: the question is what *this table*
    supports, so a controller with no calibrated cells is not a candidate
    baseline no matter that it is importable (D-047 — nothing typed).
    """
    from .baseline_matrix import reportable_surface

    return reportable_surface().controllers


def completable() -> tuple[str, ...]:
    """Scene stems no geometry screen convicts, from the reportable surface."""
    from .baseline_matrix import reportable_surface

    return tuple(Path(s).stem for s in reportable_surface().completable)


def coverage() -> dict[str, tuple[str, ...]]:
    """Which completable scenes each axis actually reaches.

    The three keys are deliberately not derivable from one another, and the
    gaps have different causes: `clearance_only`/`cte_only` scenes are missing
    the *other* column, and they are missing it for unrelated reasons — a
    zero-obstacle scene does not *pose* the clearance question (every arm
    clears `+inf`), whereas `cafe_obstacle_contested_v0` simply has no recorded
    `cte_rms` column. One is a property of the scene, the other of the census.
    """
    comp = completable()
    clear = tuple(s for s in comp if _clearance_column(s))
    cte = tuple(s for s in comp if _cte_column(s))
    return {
        "clearance": clear,
        "cte": cte,
        "joint": tuple(s for s in comp if s in clear and s in cte),
    }


def columns(axes: tuple[str, ...] = ("clear", "cte")) -> dict[tuple[str, str], dict[str, float]]:
    """`(scene, axis) -> {arm: higher-is-better score}` over the joint surface.

    Restricted to scenes where **every** requested axis is present, so a
    domination test never compares two arms on a column one of them is missing
    — that would grade absence as a loss.
    """
    build = {"clear": _clearance_column, "cte": _cte_column}
    out: dict[tuple[str, str], dict[str, float]] = {}
    for scene in completable():
        cols = {a: build[a](scene) for a in axes}
        if not all(cols[a] for a in axes):
            continue
        for axis in axes:
            out[(scene, axis)] = cols[axis]
    return out


def duplicates(axes: tuple[str, ...] = ("clear", "cte")) -> tuple[tuple[str, ...], ...]:
    """Arm classes that are bit-identical on every column.

    Why this is separate from :func:`frontier`: two identical arms are mutually
    non-dominated **by construction**, so counting them both inflates the
    frontier's width without a single real tradeoff behind it. Reporting "8 arms
    non-dominated" when one pair is a duplicate would be the
    :mod:`clearance_census` inert-channel finding re-committed by the instrument
    meant to detect it.
    """
    cols = columns(axes)
    seen: list[list[str]] = []
    for arm in arms():
        for group in seen:
            other = group[0]
            if all(
                abs(c[arm] - c[other]) < 1e-12
                for c in cols.values()
                if arm in c and other in c
            ):
                group.append(arm)
                break
        else:
            seen.append([arm])
    return tuple(tuple(g) for g in seen if len(g) > 1)


def dominates(a: str, b: str, cols: dict[tuple[str, str], dict[str, float]]) -> bool:
    """Does `b` dominate `a`? — weakly better everywhere, strictly better once."""
    shared = [c for c in cols.values() if a in c and b in c]
    if not shared:
        return False
    return (all(c[b] >= c[a] for c in shared)
            and any(c[b] > c[a] for c in shared))


def frontier(axes: tuple[str, ...] = ("clear", "cte")) -> tuple[str, ...]:
    """Arms no other arm dominates, over the joint surface for `axes`."""
    cols = columns(axes)
    return tuple(
        a for a in arms()
        if not any(dominates(a, b, cols) for b in arms() if b != a)
    )


def inadmissible_joint_cells() -> tuple[tuple[str, str], ...]:
    """`(scene, arm)` pairs on the joint surface with no admissible λ window.

    Derived from `reportable_surface().empty` intersected with the joint
    scenes, so it moves when the calibration table does. An empty window means
    the numbers that cell contributes were taken at a temperature the table
    does not admit — which does not invalidate the frontier (see module
    docstring) but does bound how the affected arm may be quoted.
    """
    from .baseline_matrix import reportable_surface

    joint = set(coverage()["joint"])
    return tuple(sorted(
        (Path(s).stem, c)
        for s, c in reportable_surface().empty
        if Path(s).stem in joint
    ))


def distinct_frontier(axes: tuple[str, ...] = ("clear", "cte")) -> tuple[str, ...]:
    """The frontier with each duplicate class collapsed to one representative."""
    front = frontier(axes)
    drop = {arm for group in duplicates(axes) for arm in group[1:]}
    return tuple(a for a in front if a not in drop)


def census() -> dict[str, str]:
    """The derived counterpart of :data:`CENSUS`."""
    front = frontier()
    dups = duplicates()
    all_distinct = set(front) == set(arms())
    return {
        "joint_frontier": "ALL_DISTINCT_ARMS" if all_distinct else ",".join(front),
        "clearance_frontier": ",".join(frontier(("clear",))),
        "cte_frontier": ",".join(frontier(("cte",))),
        "duplicate_class": ";".join(",".join(g) for g in dups),
        "joint_scenes": str(len(coverage()["joint"])),
        "distinct_frontier_width": str(len(distinct_frontier())),
    }


def drift() -> tuple[str, ...]:
    """Keys where the derived census disagrees with the pinned one."""
    got = census()
    return tuple(
        f"{k}: pinned {CENSUS[k]!r} != derived {got.get(k)!r}"
        for k in sorted(CENSUS) if CENSUS[k] != got.get(k)
    )


def main() -> int:
    cov = coverage()
    got = census()
    print(f"baseline_domination — joint surface: {len(cov['joint'])} of "
          f"{len(completable())} completable scenes, {len(arms())} arms")
    for axis in ("clearance", "cte", "joint"):
        print(f"  {axis:<10} {len(cov[axis])} scene(s): {', '.join(cov[axis])}")
    print(f"  joint frontier      : {got['joint_frontier']}")
    print(f"  distinct width      : {got['distinct_frontier_width']} "
          f"(duplicates: {got['duplicate_class'] or 'none'})")
    print(f"  clearance-only front: {got['clearance_frontier']}")
    print(f"  cte-only front      : {got['cte_frontier']}")
    if inadmissible_joint_cells():
        cells = ", ".join(f"{a} x {s}" for s, a in inadmissible_joint_cells())
        print(f"  ⚠ inadmissible cell(s) on the joint surface: {cells}")
    print(f"  uncensused axes     : {', '.join(UNCENSUSED_AXES)}; "
          f"widening unbought: {WIDENING_UNBOUGHT} rollouts")
    bad = drift()
    for line in bad:
        print(f"  DRIFT {line}")
    print(f"{len(bad)} drift.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
