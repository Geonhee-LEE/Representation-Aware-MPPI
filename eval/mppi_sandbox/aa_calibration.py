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
which is what a working null test is supposed to do.** Per scene, the largest
true between-arm gap of eight-seed means against that scene's own null floor:

    column      scene              A-B gap   p95 floor   max floor   verdict
    clearance   cafe_freezing_v0    0.4606      0.0733      0.0800    6.28x  ABOVE
    cte_max     cafe_convoy_v0      0.0633      0.0659      0.0673    0.96x  BELOW
    cte_max     city_curved_v0      0.0163      0.0472      0.0760    0.35x  BELOW

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

**Finding #3 — the per-scene lesson replicates, with the same shape as the
source's.** Islam et al. get a spurious separation on Half-Cheetah and none on
Hopper, and attribute it to environment dynamics. Here the ratio of max floor to
real gap is `1.06x` on `cafe_convoy_v0` against `4.66x` on `city_curved_v0` —
the same "it depends on the scene" result, and the obstacle-free scene is the
worse one. That is consistent with D-370 finding #3 (seven of eight arms tie
there, so its real gap is made by one arm) and it means an A-A calibration
**licenses nothing about a scene it was not run on**. The six scenes this module
does not cover keep no floor at all. :data:`UNCALIBRATED` names them.

**Finding #4 — this re-prices the branch's own next action, and changes its
noun.** For a balanced split of a *fixed finite* set the null is a permutation,
not a resample, so its spread is exact rather than asymptotic:
`rms|mean(A) - mean(B)| = 2 * sigma_pop / sqrt(n - 1)`. The test suite checks
that identity holds to `1e-12` on all 24 arm-rows. Quadrupling seeds `8 -> 32`
therefore shrinks the floor by `sqrt(31/7)` = **`2.10x`** at fixed dispersion —
so the way to make the cross-track column readable is **more seeds on the pair
that binds**, not more scenes at eight seeds.
:data:`excursion_seed_width.REMAINING_DEBT` prices STATE's standing next action
— the other six scenes at eight seeds — at **384 rollouts**, and every one of
those measurements would land under a floor of the same size. Quadrupling seeds
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

from . import clearance_census, excursion_seed_width

#: Seeds per arm in both source ensembles. Both are positionally paired on it.
SEEDS = 8

#: Number of distinct unordered balanced splits of :data:`SEEDS` into halves —
#: `C(8,4)/2`. The whole null distribution, enumerated rather than sampled.
SPLITS = 35

#: `(column, scene)` pairs this module calibrates, and where each reads from.
#: `cte_max` rows come from D-370's two-scene widening; `min_clearance` from
#: D-332's peak-scene ensemble, which is a single scene of eight arms.
CALIBRATED: tuple[tuple[str, str], ...] = (
    ("clearance", "cafe_freezing_v0"),
    ("cte_max", "cafe_convoy_v0"),
    ("cte_max", "city_curved_v0"),
)

#: Scenes with a seed ensemble but **no** A-A floor of their own. A calibration
#: does not transfer across scenes (finding #3), so these are uncalibrated and
#: any claim resting on them carries no resolution bound.
UNCALIBRATED: tuple[str, ...] = (
    "cafe_head_on_v0",
    "cafe_obstacle_crossing_v0",
    "cafe_straight_v0",
    "city_open_v0",
    "city_straight_v0",
    "cafe_cut_in_v0",
)

#: `scene -> (largest true between-arm gap of 8-seed means, p95 null floor,
#: max null floor)` in metres, 4 dp. Finding #1.
FLOOR_VERDICT: dict[str, tuple[float, float, float]] = {
    "cafe_freezing_v0": (0.4606, 0.0733, 0.0800),
    "cafe_convoy_v0": (0.0633, 0.0659, 0.0673),
    "city_curved_v0": (0.0163, 0.0472, 0.0760),
}

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
#: The alternative to `excursion_seed_width.REMAINING_DEBT`'s 384, not an
#: addition to it — and the only one of the two that can decide the claim.
RESOLUTION_DEBT: int = 512


def _ensemble(scene: str) -> dict[str, tuple[float, ...]]:
    """`arm -> per-seed row` for `scene`, from whichever harvest holds it."""
    if scene == clearance_census.PEAK_SCENE:
        return clearance_census.SEED_ENSEMBLE
    return excursion_seed_width.SEED_ENSEMBLE[scene]


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


def arm_floor(scene: str, arm: str, p: float = 0.95) -> tuple[float, float]:
    """`(p-quantile, max)` of one arm's null gap distribution, 4 dp."""
    gaps = null_gaps(_ensemble(scene)[arm])
    return (round(_quantile(gaps, p), 4), round(gaps[-1], 4))


def p95_floor(scene: str) -> float:
    """Scene null floor: the largest 95th-percentile null gap over its arms.

    Taken over arms rather than pooled because a claim may rest on any one arm,
    so the floor a claim must clear is set by the noisiest arm available to it.
    """
    return round(max(arm_floor(scene, a)[0] for a in _ensemble(scene)), 4)


def max_floor(scene: str) -> float:
    """Adversarial null floor: the largest gap any split of any arm reaches."""
    return round(max(arm_floor(scene, a)[1] for a in _ensemble(scene)), 4)


def real_gap(scene: str) -> float:
    """Largest true between-arm difference of full eight-seed means, 4 dp.

    The A-B counterpart of :func:`null_gaps`: same harness, same seeds, but the
    two groups are genuinely different configurations.
    """
    means = [sum(r) / len(r) for r in _ensemble(scene).values()]
    return round(max(means) - min(means), 4)


def clears_floor(scene: str, strict: bool = False) -> bool:
    """Whether `scene`'s real gap exceeds its null floor.

    `strict` uses the adversarial :func:`max_floor`; the default uses
    :func:`p95_floor`. A scene that fails this has no readable between-arm
    signal at :data:`SEEDS` seeds, whatever bar is placed on it.
    """
    return real_gap(scene) > (max_floor(scene) if strict else p95_floor(scene))


def headroom(scene: str) -> float:
    """`real_gap / p95_floor` — how many times over the scene clears its null."""
    return round(real_gap(scene) / p95_floor(scene), 2)


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
        mf = max_floor(scene)
        if value < mf:
            out.append((value, scene, mf))
    return tuple(out)


def drift() -> tuple[str, ...]:
    """Cells where the live reading disagrees with this module's pins."""
    bad = []
    for scene, pinned in sorted(FLOOR_VERDICT.items()):
        live = (real_gap(scene), p95_floor(scene), max_floor(scene))
        if live != pinned:
            bad.append(f"{scene}: {live} != {pinned}")
    if below_floor_endpoints() != BOTH_BELOW_FLOOR:
        bad.append(f"endpoints: {below_floor_endpoints()} != {BOTH_BELOW_FLOOR}")
    for scene in calibrated_scenes():
        if len(null_gaps(next(iter(_ensemble(scene).values())))) != SPLITS:
            bad.append(f"{scene}: split count != {SPLITS}")
    return tuple(bad)


def main(argv: list[str] | None = None) -> int:
    print(f"A-A null calibration — {SEEDS} seeds, {SPLITS} balanced splits, 0 rollouts\n")
    print(f"{'column':10s} {'scene':26s} {'A-B':>8s} {'p95':>8s} {'max':>8s}  verdict")
    for column, scene in CALIBRATED:
        gap, p95, mx = real_gap(scene), p95_floor(scene), max_floor(scene)
        if gap > mx:
            verdict = f"ABOVE  ({headroom(scene):.2f}x)"
        elif gap > p95:
            verdict = f"INSIDE ({headroom(scene):.2f}x)"
        else:
            verdict = f"BELOW  ({headroom(scene):.2f}x)"
        print(f"{column:10s} {scene:26s} {gap:8.4f} {p95:8.4f} {mx:8.4f}  {verdict}")
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
