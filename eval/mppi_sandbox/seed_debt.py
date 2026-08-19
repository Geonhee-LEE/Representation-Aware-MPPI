# SPDX-License-Identifier: BSD-3-Clause
"""The 256-rollout seed debt was paid on 2026-08-17 and nobody looked.

`STATE.md`'s next-action #1 asks whether `cafe_head_on_v0`'s `0.1964 m` target
interval survives eight seeds and prices it at **64 rollouts (~90 s)**. Its #2
widens all four excited scenes and prices that at **256 rollouts**. Both
numbers are wrong in the same direction and by the same mechanism:
:data:`scene_transfer.MEASURED_SCENES` already holds **8 arms x 8 seeds on all
five hostable scenes**, taken across D-330/332/333, and `head_on` specifically
since D-332. The debt costs **zero rollouts**. This module is the arithmetic
that was standing between the branch and its own harvest.

That is the same shape as D-315 (a green receipt re-earned because nothing told
a cycle to look) and the same shape as D-367 (a rider settled from a matrix
already on disk). Three cycles in a row the cheapest available act was to read
what the branch had already measured, and the reason it kept not happening is
that the *price* was written down in prose and the *data* was written down in a
different module.

**Finding #1 — the interval survives, at half the width, and its top collapses.**
Intersecting `head_on`'s eight per-seed attained ranges leaves
:data:`WINDOW`'s `(0.0043, 0.1044)`, width `0.1001 m`. D-365 read `(0.0039,
0.2003)` off seed 0 and quoted `0.1964`. So the repair is real — a moved
`min_distance_to_obstacle` strictly inside the window cuts the arm population
on **all eight** seeds — but the room is **1.96x narrower** than STATE has been
carrying, and the binding constraint is the *ceiling*, not the floor: the floor
moves `0.0039 -> 0.0043` while the ceiling drops `0.2003 -> 0.1044`. One seed
does it. `cbf_mppi` attains `0.1044` on seed 4 against `0.18`-`0.22` on the
other seven, so the best arm's worst seed is what a seed-robust bar has to
clear, and reading the ceiling off seed 0 overstated the target by `0.0959 m`.

**Bound (D-374):** every :data:`WINDOWS` entry is graded against its own scene's
A-A null floor in :mod:`floor_reach`. All four clear on the adversarial reading
(`1.52x`–`3.89x`) but all four clear by **less** than
:mod:`aa_calibration`'s arm-gap ratio for the same scene, `cafe_head_on_v0`
worst at `4.11x` → `2.31x`. The window is what a declaration rests on, so the
gap ratio must not be quoted in its place. `cafe_obstacle_crossing_v0`'s `1.52x`
is the thinnest clearance margin on the branch.

**Finding #2 — D-366's ordering is right and by 2x more than it knew.**
`freezing`'s window is `0.4354 m` (`declaration_gap.COMMON_WINDOW`) against
`head_on`'s `0.1001`. STATE ranks the two repairs `2.2x` apart, which is
`0.4354` against `head_on`'s **seed-0** spread. At equal seed width the ratio
is :data:`WINDOW_RATIO` = `4.35x`. The cheaper-repair-first ordering D-366
established was therefore understated by its own comparison, and the gap it
should have quoted is twice as large.

**Finding #3 — D-367's sign finding reproduces on a second scene, and the
majority flips.** D-367 measured `9` of `26` non-degenerate pairs negative on
`freezing` and concluded the pairing rider "survives per-pair and dies as a
policy", explicitly refusing to extend the values to the four widened scenes.
Taken here on `head_on`: **`17` of `26` negative**, range `-0.5614` to
`+0.7218`. So the *shape* transferred exactly as D-367 said it would, and the
*balance* did not — on `freezing` a pair picked blind is more likely to be
helped by pairing, on `head_on` it is more likely to be hurt. The baseline
column is worse than the tally: **4 of 6** `stock_mppi` pairs grade
`PAIRED_HURTS` against D-367's 3 of 6, and the worst is `social_mppi` at
`rho = -0.5614`, i.e. a predicted `sd_ratio` of `1.2496` -- pairing would widen
that interval by 25 %. This is the second scene in a row where the negative
end lands on the comparison the deficit claims are made in.

A by-product that is now a reproduced signature rather than a coincidence: the
two pairs at exactly `+1.0000` are again `geometric_mppi x stock_mppi` and
`frozen_risk_mppi x risk_mppi`, the two inert-channel pairs. D-367 saw this on
`freezing` and called perfect seed correlation "the signature of an inert
channel". It holds on a scene with completely different geometry, which is what
promotes it from an observation to a check.

**The on-disk harvest was re-measured once, to check it was worth trusting.**
Reading a two-day-old pinned matrix instead of buying 64 fresh rollouts is only
cheaper if the matrix is still true, so this cycle re-ran `head_on`'s full
8 x 8 (117 s) and compared: **all 64 values reproduce to 4 dp, exactly.** That
is the licence for findings #1 and #3, and it is also the first end-to-end
determinism check this branch has taken across a two-day gap — the sandbox is
seed-reproducible at ensemble width, which nothing had verified. The `~90 s`
STATE budgeted was therefore not wasted-if-spent, merely unnecessary; the
verification cost it and the harvest did not.

Scope, stated before anything above gets quoted at more than it earns:

* **Clearance only.** Every ensemble here is `min_clearance`. The vacuity that
  D-362/D-363 turn on is *cross-track*, and no ensemble of that column exists at
  seed width — so the `cte_rms_max` half of STATE's grading surface is **not**
  touched by this module and its seed debt is genuinely unpaid.
* **`n = 8` per correlation.** D-367's caveat carries verbatim: eight points
  give a wide sampling interval, no CI is computed, and the finding rests on the
  sign pattern across 26 pairs rather than on any coefficient's 4th dp.
* **The windows are intersections, not recommendations.** A value inside
  :data:`WINDOW` grades the registry on all eight seeds; which value to declare
  is scene intent and stays the user's call (D-365/D-366's split).
* **It still does not reach D-365's decisive pair.** `0.1964` vs `0.1441` is
  cross-*scene*; the feed's limit #3 and D-367 both disqualify pairing there,
  and re-measuring `head_on` at eight seeds does not create a shared draw with
  `convoy`. That gap is open and this module does not narrow it.
"""

from __future__ import annotations

import itertools

from .pairing_precondition import DEGENERATE, NEUTRAL_SD_RATIO, pearson
from .scene_transfer import (
    CONVOY_ENSEMBLE,
    CUT_IN_ENSEMBLE,
    HEAD_ON_ENSEMBLE,
    OBSTACLE_CROSSING_ENSEMBLE,
)

#: The baseline arm every `PAIRED_HURTS` reading below is scored against.
#: Shared with `clearance_census.BASELINE` by the test rather than imported, so
#: a rename there goes red here instead of silently re-scoping finding #3.
BASELINE = "stock_mppi"

#: The scene finding #1 is about, and the one `STATE.md` priced at 64 rollouts.
SCENE = "cafe_head_on_v0"

#: The four scenes `STATE.md` next-action #2 priced at **256 rollouts**, mapped
#: to the ensembles that already hold them. `freezing` is deliberately absent:
#: it is the scene D-366/D-367 already harvested, so including it would inflate
#: the count of debt this module discharges.
ENSEMBLES: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_convoy_v0": CONVOY_ENSEMBLE,
    "cafe_cut_in_v0": CUT_IN_ENSEMBLE,
    "cafe_head_on_v0": HEAD_ON_ENSEMBLE,
    "cafe_obstacle_crossing_v0": OBSTACLE_CROSSING_ENSEMBLE,
}

#: Rollouts `STATE.md` budgeted for next-action #2, and the rollouts it actually
#: costs. Pinned as a pair so the finding cannot be quoted without its baseline.
BUDGETED_ROLLOUTS = 256
ACTUAL_ROLLOUTS = 0

#: `scene -> (lo, hi)` — the intersection of the eight per-seed attained
#: clearance ranges, 4 dp. A `min_distance_to_obstacle` strictly inside cuts the
#: arm population on **every** seed. All four are non-empty, which is itself the
#: result: every scene STATE wanted to widen is gradeable at seed width.
WINDOWS: dict[str, tuple[float, float]] = {
    "cafe_convoy_v0": (0.3230, 0.5454),
    "cafe_cut_in_v0": (0.0382, 0.3046),
    "cafe_head_on_v0": (0.0043, 0.1044),
    "cafe_obstacle_crossing_v0": (0.0192, 0.1490),
}

#: :data:`SCENE`'s seed-robust window — finding #1's headline, named separately
#: because it is the one STATE's next-action #1 asked for by name.
WINDOW: tuple[float, float] = WINDOWS[SCENE]

#: D-365's seed-0 reading of the same interval: `(lo, hi, spread)`. Kept beside
#: :data:`WINDOW` so the `1.96x` narrowing is checkable in one place and the
#: ceiling's `0.2003 -> 0.1044` collapse cannot be quoted without its origin.
SEED0_RANGE: tuple[float, float, float] = (0.0039, 0.2003, 0.1964)

#: `declaration_gap.COMMON_WINDOW`'s width in metres — `cafe_freezing_v0`'s
#: seed-robust room, finding #2's numerator. Pinned by value rather than
#: imported so this module's arithmetic does not silently follow a re-take of
#: that one; `test_seed_debt` pins the two equal.
FREEZING_WINDOW_WIDTH = 0.4354

#: Freezing's window width divided by :data:`SCENE`'s, 2 dp. STATE quotes
#: `2.2x` for the same comparison taken against a **seed-0** spread; finding #2.
WINDOW_RATIO = 4.35

#: `(negative, non_degenerate)` non-degenerate pair counts on :data:`SCENE`,
#: and D-367's same pair on `cafe_freezing_v0`. Finding #3's whole claim is the
#: change between these two, so they are pinned adjacent.
HEAD_ON_SIGNS: tuple[int, int] = (17, 26)
FREEZING_SIGNS: tuple[int, int] = (9, 26)

#: `(lo, hi)` of the non-degenerate correlations on :data:`SCENE`, 4 dp. It
#: straddles zero, which is the regime the source's limit #2 says reverses the
#: variance comparison — the same verdict D-367 reached on the other scene.
RHO_RANGE: tuple[float, float] = (-0.5614, 0.7218)

#: `(negative_baseline_pairs, baseline_pairs)` on :data:`SCENE`, and D-367's.
#: The tally that matters more than the branch-wide one: these are the
#: comparisons the clearance deficit is claimed in.
HEAD_ON_BASELINE_HURT: tuple[int, int] = (4, 6)
FREEZING_BASELINE_HURT: tuple[int, int] = (3, 6)

#: Verdict for a scene whose seed-robust window is non-empty — the repair D-365
#: named survives the widening.
SURVIVES = "SURVIVES"

#: Verdict for an empty intersection: no single bar value grades every seed, so
#: the repair would be seed-dependent. Not reached by any of the four scenes;
#: named so :func:`verdict` has both outcomes rather than a missing branch.
SEED_DEPENDENT = "SEED_DEPENDENT"


def per_seed_spread(scene: str) -> dict[int, tuple[float, float, float]]:
    """`seed -> (lo, hi, spread)` across arms on `scene`, 4 dp.

    The same statistic `declaration_gap.per_seed_spread` takes on `freezing`,
    with the ensemble as a parameter — which is the whole reason this module is
    short. That function hard-codes its scene, so widening to four scenes by
    calling it was not available; the arithmetic is re-stated rather than
    imported, and `test_seed_debt` pins the two equal on the shared scene.
    """
    ensemble = ENSEMBLES[scene]
    rows = tuple(ensemble[arm] for arm in sorted(ensemble))
    width = len(rows[0])
    out: dict[int, tuple[float, float, float]] = {}
    for seed in range(width):
        col = [row[seed] for row in rows]
        lo, hi = min(col), max(col)
        out[seed] = (round(lo, 4), round(hi, 4), round(hi - lo, 4))
    return out


def common_window(scene: str) -> tuple[float, float]:
    """Intersection of `scene`'s per-seed attained ranges, `(lo, hi)`, 4 dp.

    Returned even when empty (`lo >= hi`), per `declaration_gap.common_window`'s
    precedent: :func:`verdict` is what turns an empty interval into a
    judgement, so a caller reading the interval never also has to read a label.
    """
    spread = per_seed_spread(scene)
    lo = max(row[0] for row in spread.values())
    hi = min(row[1] for row in spread.values())
    return (round(lo, 4), round(hi, 4))


def window_width(scene: str) -> float:
    """Width of :func:`common_window` in metres, 4 dp; `0.0` if empty."""
    lo, hi = common_window(scene)
    return round(max(0.0, hi - lo), 4)


def verdict(scene: str) -> str:
    """:data:`SURVIVES` if a seed-robust bar exists on `scene`, else
    :data:`SEED_DEPENDENT`.

    Asked of the intersection rather than of a width threshold (D-044): there is
    no constant to tune here, only whether the interval is non-empty, which is
    exactly the property the repair needs.
    """
    return SURVIVES if window_width(scene) > 0.0 else SEED_DEPENDENT


def narrowing() -> float:
    """Seed-0 spread divided by the seed-robust width on :data:`SCENE`, 2 dp.

    Finding #1's `1.96x`. Derived from :data:`SEED0_RANGE` and the recomputed
    window so a re-take of the ensemble moves this rather than leaving the
    docstring's factor pointing at a stale pair.
    """
    return round(SEED0_RANGE[2] / window_width(SCENE), 2)


def correlations(scene: str) -> tuple[tuple[float, str, str], ...]:
    """`(rho, arm_a, arm_b)` for every arm pair on `scene`, ascending.

    Degenerate pairs are **included** — excluding them is
    :func:`non_degenerate`'s job, and a caller wanting the reproduced `+1.0000`
    signature needs to be able to see it.
    """
    ensemble = ENSEMBLES[scene]
    out = [
        (round(pearson(ensemble[a], ensemble[b]), 4), a, b)
        for a, b in itertools.combinations(sorted(ensemble), 2)
    ]
    return tuple(sorted(out))


def is_degenerate(arm_a: str, arm_b: str) -> bool:
    """Do the two arms reproduce each other, making `rho` an identity?

    Reads `pairing_precondition.DEGENERATE` rather than re-listing the pairs, so
    finding #3's reproduction claim and D-367's population share one census.
    """
    return tuple(sorted((arm_a, arm_b))) in DEGENERATE


def non_degenerate(scene: str) -> tuple[tuple[float, str, str], ...]:
    """:func:`correlations` minus the pairs whose `rho` is `+1.0` by identity."""
    return tuple(
        row for row in correlations(scene) if not is_degenerate(row[1], row[2])
    )


def signs(scene: str) -> tuple[int, int]:
    """`(negative, non_degenerate_total)` on `scene`. Finding #3's tally."""
    rows = non_degenerate(scene)
    return (sum(1 for rho, _a, _b in rows if rho < 0.0), len(rows))


def rho_range(scene: str) -> tuple[float, float]:
    """`(lo, hi)` of `scene`'s non-degenerate correlations, 4 dp."""
    rows = non_degenerate(scene)
    return (rows[0][0], rows[-1][0])


def straddles_zero(scene: str) -> bool:
    """Does `scene`'s correlation range contain both signs?

    The property that kills the rider as a branch-wide policy (D-367): a range
    entirely above zero would license pairing everywhere, one entirely below
    would forbid it everywhere, and only a straddle forces the per-pair test.
    """
    lo, hi = rho_range(scene)
    return lo < 0.0 < hi


def sd_ratio(rho: float) -> float:
    """`sqrt(1 - rho)` — predicted paired/independent sd ratio, 4 dp.

    Above :data:`pairing_precondition.NEUTRAL_SD_RATIO` pairing inflates the
    interval. Restated here rather than imported because that module attaches it
    to its own `PairReading`; the test pins the two agreeing on a shared `rho`.
    """
    return round((1.0 - rho) ** 0.5, 4)


def baseline_hurt(scene: str) -> tuple[tuple[float, str, float], ...]:
    """`(rho, arm, sd_ratio)` for :data:`BASELINE` pairs that pairing *hurts*.

    Ascending in `rho`, so the worst comparison reads first. Finding #3's
    sharper half: the branch-wide tally counts pairs nobody compares, while
    every row here is a comparison the clearance deficit is actually claimed in.
    """
    out = []
    for rho, arm_a, arm_b in non_degenerate(scene):
        if BASELINE not in (arm_a, arm_b):
            continue
        ratio = sd_ratio(rho)
        if ratio > NEUTRAL_SD_RATIO:
            other = arm_b if arm_a == BASELINE else arm_a
            out.append((rho, other, ratio))
    return tuple(sorted(out))


def baseline_signs(scene: str) -> tuple[int, int]:
    """`(hurt, total)` :data:`BASELINE` pairs on `scene`."""
    total = sum(
        1 for _rho, a, b in non_degenerate(scene) if BASELINE in (a, b)
    )
    return (len(baseline_hurt(scene)), total)


def degenerate_pairs(scene: str) -> tuple[tuple[str, str], ...]:
    """Pairs on `scene` whose measured `rho` is exactly `+1.0`, sorted.

    Derived from the measurement, **not** read off :data:`DEGENERATE` — that is
    what makes the reproduced inert-channel signature a check rather than a
    restatement. The test pins this equal to `DEGENERATE` on both scenes.
    """
    return tuple(
        (a, b) for rho, a, b in correlations(scene) if rho == 1.0
    )


def format_report() -> str:
    """One-screen summary for a human reading the cycle's output."""
    lines = [
        f"seed debt — {BUDGETED_ROLLOUTS} rollouts budgeted, "
        f"{ACTUAL_ROLLOUTS} spent (already on disk since D-332/D-333)",
        "",
        f"{'scene':<28}{'window':>20}{'width':>9}{'verdict':>16}",
    ]
    for scene in sorted(ENSEMBLES):
        lo, hi = common_window(scene)
        lines.append(
            f"{scene:<28}{f'({lo:.4f}, {hi:.4f})':>20}"
            f"{window_width(scene):>9.4f}{verdict(scene):>16}"
        )
    neg, total = signs(SCENE)
    lo, hi = rho_range(SCENE)
    hurt, base_total = baseline_signs(SCENE)
    lines += [
        "",
        f"finding #1  {SCENE} window {WINDOW} vs seed-0 "
        f"{SEED0_RANGE[:2]} — {narrowing()}x narrower; "
        f"ceiling {SEED0_RANGE[1]:.4f} -> {WINDOW[1]:.4f}",
        f"finding #2  freezing {FREEZING_WINDOW_WIDTH:.4f} / "
        f"{window_width(SCENE):.4f} = {WINDOW_RATIO}x "
        f"(STATE quotes 2.2x, against a seed-0 spread)",
        f"finding #3  {neg}/{total} negative on {SCENE} vs "
        f"{FREEZING_SIGNS[0]}/{FREEZING_SIGNS[1]} on freezing; "
        f"range {lo:+.4f}..{hi:+.4f}, straddles_zero={straddles_zero(SCENE)}",
        f"            baseline pairs hurt: {hurt}/{base_total} "
        f"(D-367: {FREEZING_BASELINE_HURT[0]}/{FREEZING_BASELINE_HURT[1]})",
    ]
    for rho, arm, ratio in baseline_hurt(SCENE):
        lines.append(f"              {rho:+.4f}  sd_ratio {ratio:.4f}  {arm}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(format_report())
