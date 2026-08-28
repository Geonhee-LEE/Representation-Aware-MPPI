# SPDX-License-Identifier: BSD-3-Clause
"""Should 경로추종 be scored on all four of its `CLAUDE.md` clauses?

STATE's bottleneck after D-489, in its own words: *"`CLASS_AXIS` instruments
경로추종 with cross-track alone, but `CLAUDE.md`'s north star names four clauses
for it — and as of D-488 the two missing columns both exist on disk. The
contract is now under-instrumented by choice rather than by cost."* This module
answers that decision and nothing else. No rollout is bought.

The answer is **yes, with the three clauses that have columns — and the widening
cannot rescue the tracking line, only bury it further.** Four findings, each
derived rather than asserted.

**#1 — the fourth clause is unbought, not unmeasurable, and it is priced.**
`CLAUDE.md` names *"cross-track error / heading error / smoothness /
time-to-goal"*. Three have a per-arm-per-scene census (`cte_vacuity.CTE_SEED0`
for the first, `axis_purchase.AXIS_SEED0` for the last two). `heading error` has
**none** — but :func:`path_tracking_metrics.heading_error` exists and is a pure
function of `(traj, path)`, exactly like the two D-488 bought for 58.6 s. So the
gap is a census nobody ran, not a metric the tree cannot compute, and
:func:`unbought_clauses` reports it with :data:`HEADING_UNBOUGHT_ROLLOUTS`
beside it. Stating the gap is the load-bearing part: D-488's own scope note
warns that *"a class with a line today may lose it once smoothness is scored"*,
and a report that widened from one clause to three while silently dropping the
fourth would be making the same omission one clause smaller.

**#2 — widening the axis set costs scenes, and the two effects must not be
reported as one number.** The tracking class owns **7** scenes on cross-track
alone; `AXIS_SEED0` censuses only the **4** joint ones, so a three-clause
contract is stated over 4 of 7 — it loses the three inert-block scenes D-487
named. That is not a defect of the widening (those three cannot rank a field
anyway, D-487 finding #2) but it means a frontier that grows after widening has
**two** candidate causes: more axes, or fewer scenes. :func:`frontier_under`
takes an explicit `pool`, and :func:`widening_is_monotone` compares the one- and
three-clause frontiers **on the common population** so the axis effect is read
with the population held fixed. This is D-489's lesson — *separate the causes
before reporting the number* — applied before the number is quoted rather than
after a tamper test catches it.

**#3 — the non-arrival must be cut from every clause column, not just the one
that reports it.** `axis_purchase.time_column` omits `essps_mppi ×
cafe_obstacle_crossing_v0` because it never reached the goal, but that same cell
carries a finite `cte_rms` and a finite `jerk_lat`. A domination test that
compares arms on their *shared* columns (`baseline_domination.dominates` does,
by construction) would therefore judge that arm on two clauses while excusing it
from the third — scoring an arm on how tidily it failed and then not charging it
for failing. :func:`clause_columns` gates the arm out of **all** clause columns
of a scene where any clause reports a non-arrival. That is D-489's arrival gate
re-derived on a wider column set, and it is the reason this module builds its
own columns instead of calling `baseline_domination.columns`.

**#4 — the widening cannot produce a tracking contract line.** Domination is
antitone in the axis count: adding a column can only remove domination
relations, never create one, so a frontier can only grow. The tracking frontier
is already **3** wide on cross-track alone (D-487, `NO_FRONTIER_SINGLETON`), so
no amount of further instrumentation can shrink it to a singleton.
:func:`widening_is_monotone` checks the implication holds on this data rather
than resting on the argument, and :func:`line_under` confirms the three-clause
total-order winner is `None`. The decision is therefore **safe in the direction
that matters**: instrumenting 경로추종 more fully strengthens D-487's refusal
and cannot silently overturn it. What it *can* do is change which arm holds the
plurality, which is a record claim and is left to `class_contract`.

**#5 — fully instrumented, the tracking class reproduces D-486 on its own.**
The widened frontier is **8 of 8** arms — but that raw width is the inflation
D-486 named, because `geometric_mppi` and `stock_mppi` are bit-identical on all
three clauses. Collapsed, it is **7 of 7**: *every distinct arm is
non-dominated*, so the tracking class alone now says what D-486 said of the
joint surface. The duplicate structure moved again — **one** pair here against
**two** on the clearance axis, because `frozen_risk_mppi` and `risk_mppi` are
identical on clearance and separate on cross-track. That is a fifth disjoint
column set on which the inert-channel signature reproduces, and it is why
:func:`duplicate_groups` recomputes per clause set instead of importing
`class_contract`'s answer.

Scope
-----

* **Seed 0**, inherited whole from both censuses. Every finding here is a
  seed-0 finding, as is every finding on this branch.
* **This module decides; it does not re-point `CLASS_AXIS`.** Rewriting that
  constant would move D-487's and D-489's shipped census keys under them in the
  same cycle that argues for the move. The decision is recorded here with its
  derivation; a follow-up cycle re-derives the contract keys against it.
* **Smoothness is `jerk_lat`.** `axis_purchase.smoothness_column` offers three
  statistics and the class needs one; the choice is pinned as
  :data:`SMOOTHNESS_KEY` so a later cycle changing it makes tests disagree.

CLI:
    python -m eval.mppi_sandbox.tracking_instrumentation   # rc=1 on drift
"""

from __future__ import annotations

import sys

#: The four clauses `CLAUDE.md`'s north star names for 경로추종, quoted in its
#: own order: *"cross-track error / heading error / smoothness / time-to-goal
#: 동시 만족"*. Typed because it is a *definition* read off the constitution
#: file, not a copy of a registry (D-047) — the same standing
#: :data:`class_contract.CLASS_AXIS` has.
NORTH_STAR_CLAUSES: tuple[str, ...] = (
    "cross-track error",
    "heading error",
    "smoothness",
    "time-to-goal",
)

#: Clause -> the reader in :mod:`path_tracking_metrics` that computes it. Every
#: clause has one; that is finding #1's point. Used by :func:`reader_for` to
#: prove the unbought clause is unbought rather than unmeasurable.
CLAUSE_READER: dict[str, str] = {
    "cross-track error": "cross_track_error",
    "heading error": "heading_error",
    "smoothness": "smoothness",
    "time-to-goal": "time_to_goal",
}

#: Which statistic of :func:`axis_purchase.smoothness_column` scores the
#: smoothness clause. Pinned, not defaulted: three are on disk and a contract
#: that quietly changed which one it meant would move its own numbers.
SMOOTHNESS_KEY: str = "jerk_lat"

#: Rollouts a seed-0 heading-error census would cost beyond what is on disk.
#: `heading_error` is a pure function of the trajectory, so this is D-488's
#: figure exactly — 8 arms × the 4 joint scenes — and at that cycle's measured
#: rate (`axis_purchase.MEASURED_SECONDS`) it is under a minute. Recorded so the
#: gap in finding #1 is a *priced* gap; D-488's own lesson was that three cycles
#: deferred a census without ever putting a number on it.
HEADING_UNBOUGHT_ROLLOUTS: int = 32

#: The census this module pins. Each entry is load-bearing for the P5 report's
#: 경로추종 section.
CENSUS: dict[str, str] = {
    "verdict": "WIDEN_TO_CENSUSED",
    "censused_clauses": "3",
    "unbought_clauses": "heading error",
    "unmeasurable_clauses": "none",
    "single_clause_scenes": "7",
    "widened_scenes": "4",
    "frontier_single_clause": "3",
    "frontier_widened": "8",
    "distinct_frontier_widened": "7",
    "duplicate_groups_widened": "geometric_mppi=stock_mppi",
    "widening_is_monotone": "yes",
    "line_widened": "",
    "arrival_coverage": "4/4",
}


def clauses() -> tuple[str, ...]:
    """The north-star clauses for 경로추종."""
    return NORTH_STAR_CLAUSES


def reader_for(clause: str) -> object | None:
    """The `path_tracking_metrics` callable computing `clause`, or `None`.

    Resolved by import rather than asserted, so a clause whose reader is renamed
    or deleted reads as unmeasurable here instead of staying true in prose.
    """
    from eval import path_tracking_metrics

    return getattr(path_tracking_metrics, CLAUSE_READER[clause], None)


def censused_clauses() -> tuple[str, ...]:
    """Clauses with a per-arm-per-scene column on disk, in north-star order.

    Derived by asking each census for a column rather than by a typed list: a
    clause is censused iff some scene yields a non-empty column for it.
    """
    return tuple(c for c in NORTH_STAR_CLAUSES if any(_raw_column(c, s) for s in _scene_pool()))


def unbought_clauses() -> tuple[str, ...]:
    """Clauses with a reader but no column — finding #1's population."""
    censused = set(censused_clauses())
    return tuple(
        c for c in NORTH_STAR_CLAUSES
        if c not in censused and reader_for(c) is not None
    )


def unmeasurable_clauses() -> tuple[str, ...]:
    """Clauses with neither a column nor a reader.

    Expected empty. Kept distinct from :func:`unbought_clauses` because the two
    call for different actions — buy a census, versus write a metric — and a
    report that merged them would price the second like the first.
    """
    censused = set(censused_clauses())
    return tuple(
        c for c in NORTH_STAR_CLAUSES
        if c not in censused and reader_for(c) is None
    )


def _scene_pool() -> tuple[str, ...]:
    """Scenes the 경로추종 class owns on its current single axis."""
    from .class_contract import scenes

    return scenes("tracking")


def _raw_column(clause: str, scene: str) -> dict[str, float]:
    """`{arm: higher-is-better score}` for one clause on one scene, ungated.

    Sign normalisation happens here once, as `baseline_domination._cte_column`
    does it: all three censused clauses are ceilings (lower is better), so all
    three are negated. A domination test that got one direction backwards would
    invert the frontier silently.
    """
    from .axis_purchase import AXIS_SEED0, smoothness_column, time_column
    from .cte_vacuity import CTE_SEED0

    if clause == "cross-track error":
        return {a: -v for a, v in CTE_SEED0.get(scene, {}).items()}
    if clause == "time-to-goal":
        if scene not in AXIS_SEED0:
            return {}
        return {a: -v for a, v in time_column(scene).items()}
    if clause == "smoothness":
        if scene not in AXIS_SEED0:
            return {}
        return {a: -v for a, v in smoothness_column(scene, SMOOTHNESS_KEY).items()}
    return {}


def non_arrivals(scene: str) -> frozenset[str]:
    """Arms that did not reach the goal on `scene`, per the arrival census.

    Empty for scenes outside that census — absence of a reading is not a
    certificate of arrival, and :func:`arrival_coverage` reports where the gate
    is blind rather than letting this empty set pass for a clean bill.
    """
    from .axis_purchase import unfinished

    return frozenset(arm for arm, s in unfinished() if s == scene)


def clause_columns(
    pool: tuple[str, ...] | None = None,
    clause_set: tuple[str, ...] | None = None,
) -> dict[tuple[str, str], dict[str, float]]:
    """`(scene, clause) -> {arm: higher-is-better}`, arrival-gated.

    Finding #3: an arm that never arrived is cut from **every** clause column of
    that scene, not only from the one that noticed. Scenes are kept only where
    all requested clauses yield a column, so no arm is ever compared on a column
    another arm is missing — `baseline_domination.columns`'s rule, restated
    because the gate makes this module build its own.
    """
    scene_pool = _scene_pool() if pool is None else pool
    cset = censused_clauses() if clause_set is None else clause_set
    out: dict[tuple[str, str], dict[str, float]] = {}
    for scene in scene_pool:
        cols = {c: _raw_column(c, scene) for c in cset}
        if not all(cols.values()):
            continue
        cut = non_arrivals(scene)
        for clause in cset:
            out[(scene, clause)] = {
                a: v for a, v in cols[clause].items() if a not in cut
            }
    return out


def population(clause_set: tuple[str, ...] | None = None) -> tuple[str, ...]:
    """Scenes a contract over `clause_set` can actually be stated on.

    Finding #2's cost side. Widening the clause set narrows this, so a frontier
    read after widening has two causes and this function isolates one of them.
    """
    cols = clause_columns(clause_set=clause_set)
    return tuple(sorted({s for s, _ in cols}))


def common_population() -> tuple[str, ...]:
    """Scenes stateable under **both** the one- and three-clause instrumentations.

    The population :func:`widening_is_monotone` compares over, so the axis
    effect is read with the scene set held fixed.
    """
    one = set(population(("cross-track error",)))
    return tuple(sorted(one & set(population(censused_clauses()))))


def arms_in(cols: dict[tuple[str, str], dict[str, float]]) -> tuple[str, ...]:
    """Arms appearing in any column of `cols`."""
    return tuple(sorted({a for c in cols.values() for a in c}))


def frontier_under(
    clause_set: tuple[str, ...] | None = None,
    pool: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Arms no other arm dominates, over `pool` on `clause_set`."""
    from .baseline_domination import dominates

    cols = clause_columns(pool=pool, clause_set=clause_set)
    pool_arms = arms_in(cols)
    return tuple(
        a for a in pool_arms
        if not any(dominates(a, b, cols) for b in pool_arms if b != a)
    )


def duplicate_groups(
    clause_set: tuple[str, ...] | None = None,
    pool: tuple[str, ...] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Arm classes bit-identical on every column of `clause_set` over `pool`.

    Required before any frontier width is quoted. Two identical arms are
    mutually non-dominated **by construction**, so a raw width counts a tradeoff
    that does not exist — D-486's finding, and D-487 showed the duplicate
    structure is *axis-relative*, so it must be recomputed per clause set rather
    than inherited from the joint surface.
    """
    cols = clause_columns(pool=pool, clause_set=clause_set)
    seen: list[list[str]] = []
    for arm in arms_in(cols):
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


def distinct_frontier_under(
    clause_set: tuple[str, ...] | None = None,
    pool: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """:func:`frontier_under` with each duplicate class collapsed to one member.

    The honest width. On the widened clause set the raw frontier is the entire
    arm list, which reads as "instrumenting more made every arm incomparable"
    when part of it is two pairs of identical arms being counted twice.
    """
    dupes = {b for g in duplicate_groups(clause_set, pool) for b in g[1:]}
    return tuple(a for a in frontier_under(clause_set, pool) if a not in dupes)


def widening_is_monotone() -> bool:
    """Does the three-clause frontier contain the one-clause one, same scenes?

    Finding #4's check. Domination is antitone in the axis count, so this must
    hold; it is derived anyway because the argument is about the *columns* and
    the gate makes this module's columns its own — a gating bug that dropped an
    arm asymmetrically would break the implication and nothing else would say so.
    """
    pool = common_population()
    narrow = set(frontier_under(("cross-track error",), pool))
    wide = set(frontier_under(censused_clauses(), pool))
    return narrow <= wide


def line_under(clause_set: tuple[str, ...] | None = None) -> str | None:
    """The arm winning every scene of the population outright, or `None`.

    `class_contract.total_order_winner`'s test on this module's gated,
    multi-clause columns. An arm must be strictly ahead on **every** clause of
    **every** scene, which is what a contract line over a conjunction of clauses
    ("동시 만족") means.
    """
    cols = clause_columns(clause_set=clause_set)
    if not cols:
        return None
    for arm in arms_in(cols):
        if all(
            arm in col and all(col[arm] > v for a, v in col.items() if a != arm)
            for col in cols.values()
        ):
            return arm
    return None


def arrival_coverage(clause_set: tuple[str, ...] | None = None) -> tuple[int, int]:
    """`(censused, total)` scenes of the population with an arrival reading.

    D-489 finding #6 restated on this population: the gate speaks only where
    `axis_purchase` censused, and a coverage below total means the frontier
    above was computed with some cells never asked.
    """
    from .axis_purchase import AXIS_SEED0

    pool = population(clause_set)
    return sum(1 for s in pool if s in AXIS_SEED0), len(pool)


def verdict() -> str:
    """The decision this module exists to record.

    `WIDEN_TO_CENSUSED` — instrument 경로추종 with every clause that has a
    column, state the unbought one. Any other reading means a premise moved and
    the decision must be re-argued rather than inherited.
    """
    if unmeasurable_clauses():
        return "CLAUSE_UNMEASURABLE"
    if not unbought_clauses():
        return "WIDEN_TO_ALL"
    if not widening_is_monotone():
        return "WIDENING_NOT_MONOTONE"
    return "WIDEN_TO_CENSUSED"


def census() -> dict[str, str]:
    """Derived census, compared against :data:`CENSUS` by :func:`drift`."""
    censused = censused_clauses()
    line = line_under()
    cov = arrival_coverage()
    return {
        "verdict": verdict(),
        "censused_clauses": str(len(censused)),
        "unbought_clauses": ",".join(unbought_clauses()) or "none",
        "unmeasurable_clauses": ",".join(unmeasurable_clauses()) or "none",
        "single_clause_scenes": str(len(population(("cross-track error",)))),
        "widened_scenes": str(len(population(censused))),
        "frontier_single_clause": str(len(frontier_under(("cross-track error",)))),
        "frontier_widened": str(len(frontier_under(censused))),
        "distinct_frontier_widened": str(len(distinct_frontier_under(censused))),
        "duplicate_groups_widened": ";".join(
            "=".join(g) for g in duplicate_groups(censused)
        ) or "none",
        "widening_is_monotone": "yes" if widening_is_monotone() else "no",
        "line_widened": line or "",
        "arrival_coverage": f"{cov[0]}/{cov[1]}",
    }


def drift() -> tuple[str, ...]:
    """Keys where the derived census disagrees with the pinned one."""
    got = census()
    return tuple(
        f"{k}: pinned={v!r} got={got.get(k)!r}"
        for k, v in sorted(CENSUS.items())
        if got.get(k) != v
    )


def format_table() -> str:
    """One line per north-star clause: reader, column, and what that implies."""
    censused = set(censused_clauses())
    rows = ["  clause                 reader                 column"]
    for c in NORTH_STAR_CLAUSES:
        reader = CLAUSE_READER[c] if reader_for(c) is not None else "-"
        col = "censused" if c in censused else f"unbought ({HEADING_UNBOUGHT_ROLLOUTS} rollouts)"
        rows.append(f"  {c:<22} {reader:<22} {col}")
    return "\n".join(rows)


def main() -> int:  # pragma: no cover - CLI
    print(format_table())
    print()
    for k, v in census().items():
        print(f"  {k:<24} {v}")
    bad = drift()
    if bad:
        print("\nDRIFT:")
        for line in bad:
            print(f"  {line}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
