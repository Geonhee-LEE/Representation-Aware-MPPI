# SPDX-License-Identifier: BSD-3-Clause
"""The A-A null test: what gap does this harness manufacture from a known-zero effect?

Every separation claim on this branch is a difference between group means taken
over seeds. None of them has ever been compared against the difference the
harness produces when the true effect is **known to be zero**. That comparison
is the A-A test, and the 2026-08-19 20:00 feed entry (Islam et al. 2017,
`1708.04133`) is the reason to run it: the authors take **one identical
configuration**, run it 10 times changing only the seed, split the runs 5-vs-5,
and find the two halves of the same configuration separate at `p = 0.0016` on
one environment — and *fail* to separate (`p = 0.1825`) on another. Identical
configurations can be made to look different by seed grouping alone, and whether
they are is a **per-scene** property.

This module runs that test on data already on disk. A single arm's eight seed
values are eight draws from one configuration, so any difference between two
halves of them is null by construction. Splitting `SEEDS = 8` into two groups of
four gives :data:`SPLITS` = 35 distinct unordered splits, which is the **entire**
null distribution — not a sample of it. **Zero rollouts.**

Scope and borrowed-method limits, stated before the numbers are used:

* **The p-value does not transfer, and is not used.** The feed entry flags the
  source's footnote 12: their statistic is averaged across training iterations,
  which are autocorrelated, so `p = 0.0016` is inflated. What survives is the
  qualitative protocol. Guardrail (i) of the suggested TODO — compare
  *per-episode terminal statistics*, never time series — is satisfied here by
  construction: `cte_max` and `min_clearance` are one terminal scalar per run.
* **Deep-RL policy gradients, not MPPI.** Named-scope exception, method only, in
  the style the archive used for MC-MPPI `2605.24813`.
* **A max over 35 splits is a maximum.** The source did one random split; this
  enumerates all of them. So :func:`max_floor` is adversarial and generous to
  the null, and :func:`p95_floor` is the fairer reading. Both are reported and
  the findings below name which one they use.

**Finding #1 — the calibration separates the graded column from the vacuous one,
which is what a working null test is supposed to do.** Per cell, the largest
true between-arm gap of eight-seed means against that cell's own null floor.
D-371 ran three rows; D-372 widened it to seven at **zero further rollouts** by
reading `scene_transfer._COLUMNS` — the five-scene clearance harvest that was
already on disk — instead of the single-scene ensemble beside it:

    column      scene                      A-B gap   p95 floor   max floor   verdict
    clearance   cafe_freezing_v0            0.4606      0.0733      0.0800    6.28x  ABOVE
    clearance   cafe_head_on_v0             0.1781      0.0393      0.0433    4.53x  ABOVE
    clearance   cafe_cut_in_v0              0.3265      0.1338      0.1543    2.44x  ABOVE
    clearance   cafe_convoy_v0              0.2704      0.0526      0.0572    5.14x  ABOVE
    clearance   cafe_obstacle_crossing_v0   0.2101      0.0708      0.0855    2.97x  ABOVE
    cte_max     cafe_convoy_v0              0.0633      0.0659      0.0673    0.96x  BELOW
    cte_max     city_curved_v0              0.0163      0.0472      0.0760    0.35x  BELOW

**The split is by column and the two populations do not overlap**: every
clearance row clears its own null on the adversarial reading (`2.44x`–`6.28x`),
and neither `cte_max` row clears on either reading. :data:`COLUMN_VERDICT` pins
the two tallies, derived from :data:`CALIBRATED` rather than typed.

The clearance column — the one that grades, whose bar intervals D-366/D-368
measured and which sits in the user-blocked queue — clears its own null by
**`6.28x`** on the p95 floor and `5.76x` on the adversarial max. Nothing here
threatens it. The cross-track column clears its null on **neither** scene and by
neither reading: `cafe_convoy_v0`'s largest real arm difference is `0.96x` its
p95 floor — the wrong side of 1 even before the adversarial max is reached — and
`city_curved_v0`'s is `0.35x`. The excited scene, the one D-363 picked *because*
its arms differ most, is the one whose margin is thinnest relative to its own
noise.

That is a fourth candidate mechanism for D-358's five `VACUOUS_PASS` cells, and
it is not any of the three the branch has already proposed. Not threshold
placement (D-365), not scene geometry (D-362), not arm population (D-370): the
cross-track signal is **below the resolution this harness has at eight seeds**.
Those three could each be repaired by choosing something better — a bar value, a
scene, a set of arms. This one cannot. :data:`FLOOR_VERDICT` pins all three.

**Finding #2 — the number D-370 used to refute D-363 is itself below the floor,
so the inversion is arithmetic and not evidence.** D-370's
:data:`excursion_seed_width.ROBUST_SEPARATION` is `(0.0612, 0.0730)`: the worst
excited seed spread against the widest unexcited one, `0.838x`, the wrong side
of 1. Both numbers sit under their own scene's max floor — `0.0612 < 0.0673` on
`cafe_convoy_v0` and `0.0730 < 0.0760` on `city_curved_v0`. So the null can
manufacture a gap as large as either endpoint of the comparison that refuted
D-363, and the honest verdict is symmetric: **D-363's separation and D-370's
inversion of it are both undecidable at eight seeds**, in either direction.
:data:`BOTH_BELOW_FLOOR` records it.

This is the direction the branch's guards are built to catch and had no way to
see: D-370 was careful, reproduced seed 0 to 4 dp, declined the unlicensed
paired reading, and downgraded rather than refuted — and still quoted two
numbers that a zero-effect null reaches. A caveat about seed *scope* (is one
seed enough?) is not a caveat about seed *resolution* (is any number this size
readable?), and `SEED_SCOPE` only ever asked the first.

**Finding #3 — the axis is the column, and `cafe_convoy_v0` is the controlled
experiment that says so.** D-371 read the split as *per-scene*, in the shape of
the source's own Half-Cheetah-vs-Hopper result: within `cte_max` the floor/gap
ratio is `1.06x` on `cafe_convoy_v0` against `4.66x` on `city_curved_v0`, and it
called the obstacle-free scene the worse one. That per-scene spread is real and
still pinned — but it was the only reading available from **one row per column**,
and it is not the dominant one.

`cafe_convoy_v0` is the single scene calibrated in *both* columns, so it holds
scene geometry, arm population, operating point and seed set fixed and varies
only which quantity is read. Its clearance gap clears by `5.14x`; its `cte_max`
gap, **on the same eight runs**, does not clear at all. So the unreadability of
the cross-track column is not a property of a hard scene — convoy is a scene
whose clearance signal is five times its own noise. :data:`CONVOY_SPLIT` records
the pair, and :func:`both_column_scenes` names why it is the only row that can
settle this.

What survives of D-371's caution is the transfer rule, and it is unchanged: an
A-A calibration **licenses nothing about a scene it was not run on**. But the
uncovered set is now three rather than six, and the three that moved out cost
arithmetic rather than rollouts — their ensembles were already recorded.
:data:`UNCALIBRATED` names what is left, and every one of those lacks a seed
ensemble in either harvest.

**Finding #3a — this discharges a user-blocked hold.** `cafe_head_on_v0` was the
scene `STATE.md` held a bar declaration on *because* it was uncalibrated. It
clears its floor by `4.53x`, above the adversarial max too, so D-368's interval
cuts a difference the harness can resolve. :data:`HEAD_ON_DECLARATION` records
it. This is the opposite outcome to the `cte_max` bar D-371 downgraded, and the
contrast is the point: the same test licensed one declaration and withdrew the
other.

**Finding #4 — this re-prices the branch's own next action, and changes its
noun.** For a balanced split of a *fixed finite* set the null is a permutation,
not a resample, so its spread is exact rather than asymptotic:
`rms|mean(A) - mean(B)| = 2 * sigma_pop / sqrt(n - 1)`. The test suite checks
that identity holds to `1e-12` on all 24 arm-rows. Quadrupling seeds `8 -> 32`
therefore shrinks the floor by `sqrt(31/7)` = **`2.10x`** at fixed dispersion —
so the way to make the cross-track column readable is **more seeds on the pair
that binds**, not more scenes at eight seeds.
:data:`excursion_seed_width.REMAINING_DEBT` prices STATE's standing next action
— the remaining scenes at eight seeds — at **320 rollouts**, and every one of
those measurements would land under a floor of the same size. **One of them has
since been bought and it did not**: `cafe_head_on_v0` grades `cte_max` at
`3.12x` its own floor (`tail_mean.third_baseline_ratio`), so "under a floor of
the same size" is a claim about the *floor*, not about every scene's gap — a
large enough effect clears an 8-seed floor without more seeds. Quadrupling seeds
on the binding pair halves the floor and costs `8 arms x 32 seeds x 2 scenes` =
**512 rollouts** (:data:`RESOLUTION_DEBT`). Comparable price; only the second one
can decide the claim. This module does not spend either.

CLI:
    python -m eval.mppi_sandbox.aa_calibration   # rc=1 on drift from the pins
"""

from __future__ import annotations

import math
import sys
from itertools import combinations

from . import clearance_census, excursion_seed_width, scene_transfer

#: Seeds per arm in both source ensembles. Both are positionally paired on it.
SEEDS = 8

#: Number of distinct unordered balanced splits of :data:`SEEDS` into halves —
#: `C(8,4)/2`. The whole null distribution, enumerated rather than sampled.
SPLITS = 35

#: `(column, scene)` pairs this module calibrates, and where each reads from.
#: `cte_max` rows come from D-370's two-scene widening; `clearance` from
#: :data:`scene_transfer._COLUMNS`, the five-scene 8x8 harvest D-332/D-333 took.
#:
#: D-372 grew this from three rows to seven at **zero rollouts**. The clearance
#: ensembles were already on disk for every hostable scene; D-371 calibrated one
#: of them because it reached for `clearance_census.SEED_ENSEMBLE` (a single
#: scene) and never for the five-scene registry beside it.
CALIBRATED: tuple[tuple[str, str], ...] = (
    ("clearance", "cafe_freezing_v0"),
    ("clearance", "cafe_head_on_v0"),
    ("clearance", "cafe_cut_in_v0"),
    ("clearance", "cafe_convoy_v0"),
    ("clearance", "cafe_obstacle_crossing_v0"),
    ("cte_max", "cafe_convoy_v0"),
    ("cte_max", "city_curved_v0"),
    ("cte_max", "cafe_head_on_v0"),
)

#: Scenes with **no** A-A floor in any column. A calibration does not transfer
#: across scenes (D-371 finding #3), so any claim resting on these carries no
#: resolution bound. All three lack a seed ensemble entirely — unlike D-371's
#: list, which named three scenes whose ensembles were already recorded.
UNCALIBRATED: tuple[str, ...] = (
    "cafe_straight_v0",
    "city_open_v0",
    "city_straight_v0",
)

#: `(column, scene) -> (largest true between-arm gap of 8-seed means, p95 null
#: floor, max null floor)` in metres, 4 dp.
#:
#: Keyed by the **pair**, not the scene: `cafe_convoy_v0` carries both columns
#: and they land on opposite sides of their floors, so a scene-keyed pin cannot
#: state this table. That collision is :data:`CONVOY_SPLIT`.
FLOOR_VERDICT: dict[tuple[str, str], tuple[float, float, float]] = {
    ("clearance", "cafe_freezing_v0"): (0.4606, 0.0733, 0.0800),
    ("clearance", "cafe_head_on_v0"): (0.1781, 0.0393, 0.0433),
    ("clearance", "cafe_cut_in_v0"): (0.3265, 0.1338, 0.1543),
    ("clearance", "cafe_convoy_v0"): (0.2704, 0.0526, 0.0572),
    ("clearance", "cafe_obstacle_crossing_v0"): (0.2101, 0.0708, 0.0855),
    ("cte_max", "cafe_convoy_v0"): (0.0633, 0.0659, 0.0673),
    ("cte_max", "city_curved_v0"): (0.0163, 0.0472, 0.0760),
    ("cte_max", "cafe_head_on_v0"): (0.2960, 0.0948, 0.1084),
}

#: The two columns' verdicts, as populations rather than as scenes:
#: `column -> (rows, rows clearing the p95 floor, rows clearing the max floor)`.
#:
#: **Finding #1 (D-372), as re-counted 2026-08-20 — the divide is by column,
#: but it is a *majority*, not a partition.** Clearance clears its own null on
#: **5 of 5** scenes and by the adversarial reading too, `2.44x`–`6.28x`.
#: `cte_max` clears on **1 of 3**.
#:
#: That row used to read `0 of 2`, and the correction is not a new measurement.
#: D-388 bought `cafe_head_on_v0`'s `cte_max` column (64 rollouts) and pinned it
#: in `excursion_seed_width.SEED_ENSEMBLE`, where every floor function here
#: reaches it — :func:`_ensemble` dispatches straight into that dict — but it
#: never added the cell to :data:`CALIBRATED`, which is the population this
#: table counts. So the ensemble was *gradeable and graded* (`tail_mean.
#: third_baseline_ratio()` has returned `3.12x` since that cycle) while the
#: module owning the column verdict kept reporting that no `cte_max` cell had
#: ever cleared. Two modules disagreed about the same column for want of one
#: tuple entry, and nothing went red: :func:`drift` checks
#: :data:`FLOOR_VERDICT` *against* :data:`CALIBRATED` and both omitted it
#: together. A census can only be audited against something it does not derive
#: from — see `test_calibrated_covers_every_pinned_cte_max_ensemble`.
#:
#: The column reading survives the correction and is weaker than it was: at
#: eight rows `cte_max` still clears far less often than clearance, but "the
#: maximum never grades" is refuted by a cell this branch bought itself.
COLUMN_VERDICT: dict[str, tuple[int, int, int]] = {
    "clearance": (5, 5, 5),
    "cte_max": (3, 1, 1),
}

#: Columns whose tally above is assembled from **more than one operating point**
#: and therefore may not be quoted as a single experiment (D-391).
#:
#: `cte_max`'s three rows are not commensurable. Two of them — `cafe_convoy_v0`
#: and `cafe_head_on_v0` — have since been re-harvested at `tail_mean.retake`'s
#: operating point, where **both clear** (`1.46x`, `4.93x`); the third,
#: `city_curved_v0`, is still the `run_scenario(...)`-defaults harvest and is
#: degenerate under `tail_mean.excited` besides. So the shipped `1 of 3` is a
#: count over a mixed population: at one operating point the two gradeable rows
#: read `2 of 2`, and the row that drags the tally down is the one no aligned
#: measurement exists for.
#:
#: Kept as a marker rather than a corrected tuple on purpose — correcting it
#: needs `city_curved_v0` re-harvested (~64 rollouts), which is a measurement
#: this pin cannot make by re-typing. `clearance` is absent from this set: its
#: five rows are one harvest.
MIXED_OPERATING_POINT_COLUMNS: frozenset[str] = frozenset({"cte_max"})

#: **Finding #2 (D-372) — one scene settled it, and the second scene unsettles
#: it.** `cafe_convoy_v0` holds scene geometry, arm population, operating point
#: and seed set **fixed** and varies only which quantity is read.
#: `(column, gap, p95 floor, headroom)`: clearance clears by `5.14x`, and
#: `cte_max` on the same eight runs does not clear at all.
#:
#: That was read as showing the cross-track column unreadable *as a column*.
#: Since 2026-08-20 there is a **second** both-columns scene — `cafe_head_on_v0`,
#: registered late (see :data:`COLUMN_VERDICT`) — and it does not reproduce the
#: split: clearance clears by `4.53x` and `cte_max` clears too, by `3.12x`. So
#: the controlled comparison exists twice and disagrees with itself, which
#: makes convoy's split a fact about convoy unless something further explains
#: the difference. `tail_mean.contrast_replicates()` reports the same failure
#: from the other side of the branch.
#:
#: **Resolved (Q-175 → D-390), and the resolution retires this pin's headline.**
#: The two columns were not built by the same code path: `SEED_ENSEMBLE`'s
#: `cte_max` rows reproduce under `run_scenario(...)` defaults and not at all
#: under the `lam=OPERATING_LAM` + epistemic-isolation operating point
#: `tail_mean.retake` uses. Re-harvested at the latter
#: (`tail_mean.CTE_MAX_AT_OPERATING_POINT`, 128 rollouts), `cafe_convoy_v0`'s
#: `cte_max` **clears** — `1.46x` on the p95 floor, `1.31x` adversarial.
#:
#: So "the same eight runs" was false in the `cte_max` term, and with it the
#: split: this row does not record a column landing on the wrong side of its
#: floor while its neighbour clears. It records two experiments. The `0.96x`
#: below is kept rather than deleted (the D-387 convention) so prose quoting it
#: finds the retraction attached — `tail_mean.RETIRED_BY_ALIGNMENT` and
#: `tail_mean.ALIGNED_CELLS` carry the replacement. Nothing here touches the
#: clearance term, which is measured at its own operating point and unaffected.
CONVOY_SPLIT: tuple[tuple[str, float, float, float], ...] = (
    ("clearance", 0.2704, 0.0526, 5.14),
    ("cte_max", 0.0633, 0.0659, 0.96),
)

#: The user-blocked declaration this cycle was picked to protect, and its
#: verdict. D-368 measured `cafe_head_on_v0`'s clearance bar interval as
#: `(0.0043, 0.1044)` and `STATE.md` held the declaration one cycle because the
#: scene was `UNCALIBRATED`. It is now calibrated and it **clears**: `0.1781`
#: against a `0.0393` p95 floor (`4.53x`) and above the `0.0433` adversarial max
#: as well. The hold is discharged — the bar separates arms this harness can
#: actually tell apart. Contrast the `cte_max` bar in user-blocked #3, which
#: D-371 downgraded for failing exactly this test.
HEAD_ON_DECLARATION: tuple[str, float, float, float, bool] = (
    "cafe_head_on_v0",
    0.1781,
    0.0393,
    4.53,
    True,
)

#: D-370's `ROBUST_SEPARATION` endpoints against the max floor of the scene each
#: was measured on: `(value, scene, max floor)`. Both are below. Finding #2.
BOTH_BELOW_FLOOR: tuple[tuple[float, str, float], ...] = (
    (0.0612, "cafe_convoy_v0", 0.0673),
    (0.0730, "city_curved_v0", 0.0760),
)

#: What this module leaves standing of the cross-track spread comparison, in one
#: string — pinned so the symmetry of the verdict cannot be quietly dropped.
VERDICT: str = (
    "D-363's separation and D-370's inversion are both below the 8-seed A-A "
    "floor; the cross-track spread comparison is undecidable in either direction"
)

#: Rollouts to halve the cross-track null floor: 8 arms x 32 seeds x 2 scenes.
#: The alternative to `excursion_seed_width.REMAINING_DEBT`'s 320, not an
#: addition to it — and the only one of the two that can decide the claim.
RESOLUTION_DEBT: int = 512


def _ensemble(column: str, scene: str) -> dict[str, tuple[float, ...]]:
    """`arm -> per-seed row` for `(column, scene)`, from the harvest holding it.

    Dispatch is on the **column first**. D-371's version took `scene` alone,
    which was unambiguous only while no scene carried two columns; `cafe_convoy
    _v0` carries both, so a scene-keyed lookup would have silently returned its
    `cte_max` row to a caller asking for clearance — and those two land on
    opposite sides of their floors (:data:`CONVOY_SPLIT`).
    """
    if column == "cte_max":
        return excursion_seed_width.SEED_ENSEMBLE[scene]
    if column == "clearance":
        return scene_transfer._COLUMNS[scene]
    raise KeyError(f"no ensemble for column {column!r}")


def null_gaps(row: tuple[float, ...]) -> tuple[float, ...]:
    """Every `|mean(A) - mean(B)|` over the balanced splits of one arm's seeds.

    `row` is one arm at one scene, so the two halves differ only by which seeds
    landed in which group: the true effect is **zero** by construction. Returns
    all :data:`SPLITS` values, ascending. Complements are deduplicated by
    requiring seed 0 in the first group.
    """
    n = len(row)
    idx = set(range(n))
    half = n // 2
    out = []
    for group in combinations(range(n), half):
        if 0 not in group:
            continue
        rest = sorted(idx - set(group))
        out.append(abs(sum(row[i] for i in group) / half - sum(row[i] for i in rest) / half))
    return tuple(sorted(out))


def _quantile(values: tuple[float, ...], p: float) -> float:
    """Upper-tail quantile by ceiling rank — no interpolation, no numpy."""
    return values[min(len(values) - 1, math.ceil(p * len(values)) - 1)]


def arm_floor(column: str, scene: str, arm: str, p: float = 0.95) -> tuple[float, float]:
    """`(p-quantile, max)` of one arm's null gap distribution, 4 dp."""
    gaps = null_gaps(_ensemble(column, scene)[arm])
    return (round(_quantile(gaps, p), 4), round(gaps[-1], 4))


def p95_floor(column: str, scene: str) -> float:
    """Cell null floor: the largest 95th-percentile null gap over its arms.

    Taken over arms rather than pooled because a claim may rest on any one arm,
    so the floor a claim must clear is set by the noisiest arm available to it.
    """
    return round(max(arm_floor(column, scene, a)[0] for a in _ensemble(column, scene)), 4)


def max_floor(column: str, scene: str) -> float:
    """Adversarial null floor: the largest gap any split of any arm reaches."""
    return round(max(arm_floor(column, scene, a)[1] for a in _ensemble(column, scene)), 4)


def real_gap(column: str, scene: str) -> float:
    """Largest true between-arm difference of full eight-seed means, 4 dp.

    The A-B counterpart of :func:`null_gaps`: same harness, same seeds, but the
    two groups are genuinely different configurations.
    """
    means = [sum(r) / len(r) for r in _ensemble(column, scene).values()]
    return round(max(means) - min(means), 4)


def clears_floor(column: str, scene: str, strict: bool = False) -> bool:
    """Whether the cell's real gap exceeds its null floor.

    `strict` uses the adversarial :func:`max_floor`; the default uses
    :func:`p95_floor`. A cell that fails this has no readable between-arm
    signal at :data:`SEEDS` seeds, whatever bar is placed on it.
    """
    floor = max_floor(column, scene) if strict else p95_floor(column, scene)
    return real_gap(column, scene) > floor


def headroom(column: str, scene: str) -> float:
    """`real_gap / p95_floor` — how many times over the cell clears its null."""
    return round(real_gap(column, scene) / p95_floor(column, scene), 2)


def column_verdict(column: str) -> tuple[int, int, int]:
    """`(rows, rows clearing p95, rows clearing max)` for one column.

    The statistic :data:`COLUMN_VERDICT` pins. Derived rather than typed so the
    table cannot drift from the rows in :data:`CALIBRATED`.
    """
    rows = [s for c, s in CALIBRATED if c == column]
    return (
        len(rows),
        sum(clears_floor(column, s) for s in rows),
        sum(clears_floor(column, s, strict=True) for s in rows),
    )


def both_column_scenes() -> tuple[str, ...]:
    """Scenes calibrated in **more than one** column, sorted.

    These are the only rows that can separate a column effect from a scene
    effect, because everything except the column is held fixed across them.
    """
    seen: dict[str, int] = {}
    for _, scene in CALIBRATED:
        seen[scene] = seen.get(scene, 0) + 1
    return tuple(sorted(s for s, n in seen.items() if n > 1))


def calibrated_scenes() -> tuple[str, ...]:
    """Scenes carrying a floor, sorted. Everything else is :data:`UNCALIBRATED`."""
    return tuple(sorted({scene for _, scene in CALIBRATED}))


def below_floor_endpoints() -> tuple[tuple[float, str, float], ...]:
    """D-370's `ROBUST_SEPARATION` endpoints that sit under their scene's floor.

    Finding #2. Each endpoint was measured on a different scene, so each is
    checked against the floor of the scene it came from, not a pooled one.
    """
    exc, unexc = excursion_seed_width.ENDPOINTS
    lo, hi = excursion_seed_width.ROBUST_SEPARATION
    out = []
    for value, scene in ((lo, exc), (hi, unexc)):
        mf = max_floor("cte_max", scene)
        if value < mf:
            out.append((value, scene, mf))
    return tuple(out)


def drift() -> tuple[str, ...]:
    """Cells where the live reading disagrees with this module's pins."""
    bad = []
    if tuple(sorted(FLOOR_VERDICT)) != tuple(sorted(CALIBRATED)):
        bad.append(f"pinned cells {tuple(sorted(FLOOR_VERDICT))} != CALIBRATED")
    for cell, pinned in sorted(FLOOR_VERDICT.items()):
        column, scene = cell
        live = (real_gap(column, scene), p95_floor(column, scene), max_floor(column, scene))
        if live != pinned:
            bad.append(f"{cell}: {live} != {pinned}")
    if below_floor_endpoints() != BOTH_BELOW_FLOOR:
        bad.append(f"endpoints: {below_floor_endpoints()} != {BOTH_BELOW_FLOOR}")
    for column in sorted(COLUMN_VERDICT):
        if column_verdict(column) != COLUMN_VERDICT[column]:
            bad.append(f"{column}: {column_verdict(column)} != {COLUMN_VERDICT[column]}")
    live_split = tuple(
        (c, real_gap(c, "cafe_convoy_v0"), p95_floor(c, "cafe_convoy_v0"), headroom(c, "cafe_convoy_v0"))
        for c, s in CALIBRATED
        if s == "cafe_convoy_v0"
    )
    if live_split != CONVOY_SPLIT:
        bad.append(f"convoy split: {live_split} != {CONVOY_SPLIT}")
    for column, scene in CALIBRATED:
        if len(null_gaps(next(iter(_ensemble(column, scene).values())))) != SPLITS:
            bad.append(f"{(column, scene)}: split count != {SPLITS}")
    return tuple(bad)


def main(argv: list[str] | None = None) -> int:
    print(f"A-A null calibration — {SEEDS} seeds, {SPLITS} balanced splits, 0 rollouts\n")
    print(f"{'column':10s} {'scene':26s} {'A-B':>8s} {'p95':>8s} {'max':>8s}  verdict")
    for column, scene in CALIBRATED:
        gap = real_gap(column, scene)
        p95, mx = p95_floor(column, scene), max_floor(column, scene)
        head = headroom(column, scene)
        if gap > mx:
            verdict = f"ABOVE  ({head:.2f}x)"
        elif gap > p95:
            verdict = f"INSIDE ({head:.2f}x)"
        else:
            verdict = f"BELOW  ({head:.2f}x)"
        print(f"{column:10s} {scene:26s} {gap:8.4f} {p95:8.4f} {mx:8.4f}  {verdict}")
    print("\nby column (rows / clear p95 / clear max):")
    for column in sorted(COLUMN_VERDICT):
        n, p, m = column_verdict(column)
        print(f"  {column:10s} {n} rows, {p} clear p95, {m} clear max")
    print(f"\nboth-column scenes (column effect vs scene effect): {both_column_scenes()}")
    for c, gap, p95, head in CONVOY_SPLIT:
        print(f"  cafe_convoy_v0 {c:10s} gap {gap:.4f} vs p95 {p95:.4f} = {head:.2f}x")
    print(f"\nD-370 ROBUST_SEPARATION endpoints below their scene's max floor:")
    for value, scene, mf in below_floor_endpoints():
        print(f"  {value:.4f} on {scene:26s} < max floor {mf:.4f}")
    print(f"\nuncalibrated scenes ({len(UNCALIBRATED)}): {', '.join(UNCALIBRATED)}")
    print(f"verdict: {VERDICT}")
    print(f"resolution debt: {RESOLUTION_DEBT} rollouts (32 seeds on the binding pair)")
    bad = drift()
    if bad:
        print("\nDRIFT:", *bad, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
