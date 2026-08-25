# SPDX-License-Identifier: BSD-3-Clause
"""Is `cafe_freezing_v0`'s missing clearance bar the same placement failure? No — it is strictly easier, and it is the one that can be checked against seeds.

D-365 split the two vacuity mechanisms: the 경로추종 column fails by **width**
(the arms do not differ, so no constant exists to shop for) and the 물체회피
column fails by **placement** (the arms differ by `0.1964 m` and the declared
`0.40` sits above the whole attained range). Only the second is repairable by
moving a number. STATE's follow-up asked whether `cafe_freezing_v0` — the one
obstacle-bearing scene that declares no `min_distance_to_obstacle` at all
(`threshold_vacuity.CENSUS` calls it `UNDECLARED`) — belongs to that repairable
class. Both operands were already pinned, so this is arithmetic on disk.

**It belongs to it, and it is the easiest member, for a reason no other scene
on the branch can supply.** `cafe_freezing_v0` is `clearance_census.PEAK_SCENE`,
so its clearance harvest is not a seed-0 row but the whole `SEED_ENSEMBLE` —
eight arms at eight seeds, 64 numbers. That buys two things at once:

**Finding #1 — the spread is far too wide to be a width failure.** At seed 0
the eight arms span `0.3319`–`0.7856 m`, a spread of `0.4537 m`. Every scene in
:data:`spread_generality.CENSUS` spreads `0.1964`–`0.3512`, so this scene
out-spreads the widest *graded* clearance scene on the branch by `1.29x` and
D-365's vacuous `cafe_head_on_v0` by `2.31x`. :data:`SPREAD_RANK` pins the
comparison. There is nothing here that a bar could fail to cut for lack of
dispersion.

**Finding #2 — and unlike every spread on this branch, that one is measured
across seeds rather than asserted at seed 0.** The per-seed spread runs
`0.4390`–`0.4989` over the eight seeds: a `0.0599 m` swing, **13.5 %** of the
statistic's own value, and the *smallest* seed's spread still exceeds every
scene in :data:`spread_generality.CENSUS`. This does not discharge
`excursion_tracking.SEED_SCOPE` — that pin is about four other scenes and their
ensembles have not been bought — but it is the branch's first evidence on the
question it names, and the direction is that arm spread is **not** a seed-noise
artefact. :data:`PER_SEED_SPREAD` carries the column.

**Bound (D-374):** :data:`COMMON_WINDOW`'s width is graded against this scene's
A-A null floor in :mod:`floor_reach` — `5.44x` on the adversarial reading, so it
clears, but by less than :mod:`aa_calibration`'s arm-gap ratio for the same
scene. A gap ratio is not the number that licenses a bar declaration; the window
ratio is. Read `floor_reach` before quoting the interval below as declarable.

**Finding #3 — the seed-robust discriminating window is `0.4354 m` wide.** A
bar discriminates on a seed iff it sits strictly inside that seed's attained
range (`margin_placement.INTERIOR`, same definition). Intersecting the eight
per-seed ranges leaves `(0.3359, 0.7713)`: **any** value in there cuts the arm
population on **all eight** seeds. Set beside D-365's two repairs, the ordering
inverts STATE's:

* `cafe_head_on_v0` — the constant exists and must be **moved**, and the target
  interval is `(0.0039, 0.2003)` read off **one** seed, so the move could still
  land outside the range the other seven attain. Nobody has checked.
* `cafe_freezing_v0` — the constant must be **added**, the target interval is
  `2.2x` wider than head_on's whole single-seed spread, and it is verified on
  eight seeds. The cheaper repair is the one STATE ranked second.

**What this does not claim.** The bar's *value* is scene intent and stays
user-blocked — this module reports the interval a value may be drawn from and
proposes none, exactly as D-365 argued about which constant is mis-set without
proposing what it should become.

Scope, stated before the numbers because it bounds them:

* **One scene.** `cafe_freezing_v0` is the only scene with an eight-seed
  clearance ensemble on disk, which is precisely why findings #2 and #3 are
  available here and nowhere else. Nothing here generalises to the other seven
  and :data:`SEED_ENSEMBLE_SCENES` pins the denominator at 1.
* **Eight rows, six distinct arms.** `geometric_mppi` reproduces `stock_mppi`
  in every column (an inert channel, pinned as such by `clearance_census`) and
  `frozen_risk_mppi` reproduces `risk_mppi`. Duplicates cannot extend a range,
  so the windows below are unaffected — but a reader counting arms on either
  side of a bar is counting six, not eight. :data:`DUPLICATE_ROWS` names them.
* **`min_distance_to_obstacle` only**, as `threshold_vacuity` swept. The scene's
  other silent keys are that module's `UNSWEPT_KEYS`, unchanged by this one.
* **Discrimination is across arms, not across seeds for a fixed arm.** A bar in
  the window separates the registry; it says nothing about whether one arm's
  own eight seeds straddle it. That is a different question and a narrower
  window — :func:`arm_straddle` reports it rather than leaving it implied.

Zero rollouts: every operand is `clearance_census.SEED_ENSEMBLE`.

CLI:
    python -m eval.mppi_sandbox.declaration_gap   # rc=1 on drift from the pins
"""

from __future__ import annotations

import sys

from . import spread_generality, threshold_vacuity
from .clearance_census import SEED_ENSEMBLE, SEEDS

#: The scene this module is about. `UNDECLARED` in
#: :data:`threshold_vacuity.CENSUS` and `clearance_census.PEAK_SCENE`.
SCENE = "cafe_freezing_v0"

#: Scenes with an eight-seed clearance ensemble on disk. The denominator of
#: findings #2 and #3, pinned so their reach cannot be read as wider than 1.
SEED_ENSEMBLE_SCENES: tuple[str, ...] = (SCENE,)

#: `(duplicate, original)` rows in :data:`clearance_census.SEED_ENSEMBLE`. Both
#: pairs are recorded facts about the registry, not measurement noise: the
#: geometric channel is inert and `frozen_risk_mppi` freezes a channel that does
#: not move on this scene. Six arms are distinct.
DUPLICATE_ROWS: tuple[tuple[str, str], ...] = (
    ("geometric_mppi", "stock_mppi"),
    ("frozen_risk_mppi", "risk_mppi"),
)

#: `seed -> (lo, hi, spread)` in metres, 4 dp — the attained clearance range
#: across all registry arms, one entry per seed of the ensemble.
PER_SEED_SPREAD: dict[int, tuple[float, float, float]] = {
    0: (0.3319, 0.7856, 0.4537),
    1: (0.3342, 0.7732, 0.4390),
    2: (0.3069, 0.7809, 0.4740),
    3: (0.3181, 0.7713, 0.4532),
    4: (0.3158, 0.7871, 0.4713),
    5: (0.3329, 0.8318, 0.4989),
    6: (0.3312, 0.7831, 0.4519),
    7: (0.3359, 0.7785, 0.4426),
}

#: The intersection of every seed's attained range: `(lo, hi)` in metres, 4 dp.
#: A declared `min_distance_to_obstacle` strictly inside this interval cuts the
#: arm population on **all eight** seeds. Finding #3.
COMMON_WINDOW: tuple[float, float] = (0.3359, 0.7713)

#: `(this scene's seed-0 spread, widest scene in spread_generality.CENSUS and
#: its spread, D-365's vacuous scene and its spread)`. Finding #1's comparison,
#: pinned so a re-take of either harvest goes red here rather than quietly
#: reordering the ranking the finding is read off.
SPREAD_RANK: tuple[float, str, float, str, float] = (
    0.4537, "cafe_cut_in_v0", 0.3512, "cafe_head_on_v0", 0.1964,
)

#: Verdict for a scene whose criterion is absent while its attained range is
#: wide — repairable by *adding* a constant, the sibling of D-365's
#: `REPAIRABLE_BY_PLACEMENT` (repairable by *moving* one).
DECLARATION_GAP = "DECLARATION_GAP"

#: Verdict for an absent criterion whose attained range could not host one.
#: Not reached on this branch; named so :func:`verdict` has both outcomes and a
#: future scene landing here is a stated result rather than a missing branch.
UNGRADEABLE = "UNGRADEABLE"


def _rows() -> tuple[tuple[float, ...], ...]:
    """The ensemble as `arm -> per-seed clearances`, in a stable arm order."""
    return tuple(SEED_ENSEMBLE[arm] for arm in sorted(SEED_ENSEMBLE))


def per_seed_spread() -> dict[int, tuple[float, float, float]]:
    """`seed -> (lo, hi, spread)` across arms, 4 dp. Recomputed, not recalled."""
    rows = _rows()
    out: dict[int, tuple[float, float, float]] = {}
    for seed in range(SEEDS):
        col = [row[seed] for row in rows]
        lo, hi = min(col), max(col)
        out[seed] = (round(lo, 4), round(hi, 4), round(hi - lo, 4))
    return out


def common_window() -> tuple[float, float]:
    """Bar values that discriminate on *every* seed, as an open interval.

    The intersection of the per-seed attained ranges. Returned even when empty
    (`lo >= hi`); :func:`verdict` is what turns that into a judgement, so a
    caller reading the interval never has to also consult a label.
    """
    spread = per_seed_spread()
    lo = max(row[0] for row in spread.values())
    hi = min(row[1] for row in spread.values())
    return (round(lo, 4), round(hi, 4))


def window_width() -> float:
    """Width of :func:`common_window` in metres, 4 dp; `0.0` if empty."""
    lo, hi = common_window()
    return round(max(0.0, hi - lo), 4)


def verdict() -> str:
    """:data:`DECLARATION_GAP` if a seed-robust bar exists, else :data:`UNGRADEABLE`.

    Asked of the window rather than of a spread threshold on purpose (D-044):
    there is no constant here to tune, only the question of whether the
    intersection is non-empty, which is the property the repair needs.
    """
    return DECLARATION_GAP if window_width() > 0.0 else UNGRADEABLE


def arm_straddle() -> dict[str, tuple[float, float]]:
    """`arm -> (lo, hi)` over its own eight seeds, 4 dp.

    The narrower question scope bullet #4 separates out: a bar inside an arm's
    own range makes *that arm* pass on some seeds and fail on others, which is
    not what :func:`common_window` measures and would be wrong to infer from it.
    """
    return {
        arm: (round(min(vals), 4), round(max(vals), 4))
        for arm, vals in sorted(SEED_ENSEMBLE.items())
    }


def straddling_arms(margin: float) -> tuple[str, ...]:
    """Arms whose own seed range strictly contains `margin`, sorted."""
    return tuple(
        arm for arm, (lo, hi) in arm_straddle().items() if lo < margin < hi
    )


def spread_rank() -> tuple[float, str, float, str, float]:
    """This scene's seed-0 spread against the graded clearance population.

    Reads :data:`spread_generality.CENSUS` for the comparison rather than
    restating its numbers, so a re-take there propagates here instead of the
    two drifting apart.
    """
    census = spread_generality.CENSUS
    widest = max(census, key=lambda s: census[s][2])
    vacuous = spread_generality.REPAIRABLE_BY_PLACEMENT[0]
    return (
        per_seed_spread()[0][2],
        widest,
        census[widest][2],
        vacuous,
        census[vacuous][2],
    )


def main() -> int:
    """Print the window and the ranking; rc=1 on drift from the pins."""
    spread = per_seed_spread()
    print(f"scene {SCENE} — {threshold_vacuity.CENSUS[SCENE]} in threshold_vacuity")
    for seed in sorted(spread):
        lo, hi, sprd = spread[seed]
        print(f"  seed {seed}  [{lo:.4f}, {hi:.4f}]  spread {sprd:.4f}")
    lo, hi = common_window()
    print(f"\ncommon window ({lo:.4f}, {hi:.4f})  width {window_width():.4f}  -> {verdict()}")
    own, widest, widest_sprd, vac, vac_sprd = spread_rank()
    print(
        f"seed-0 spread {own:.4f} vs widest graded {widest} {widest_sprd:.4f} "
        f"({own / widest_sprd:.2f}x) vs vacuous {vac} {vac_sprd:.4f} ({own / vac_sprd:.2f}x)"
    )
    print(f"arms straddling the window midpoint: {straddling_arms((lo + hi) / 2) or '(none)'}")

    rc = 0
    if spread != PER_SEED_SPREAD:
        print("DRIFT: per-seed spread differs from PER_SEED_SPREAD", file=sys.stderr)
        rc = 1
    if (lo, hi) != COMMON_WINDOW:
        print("DRIFT: common window differs from COMMON_WINDOW", file=sys.stderr)
        rc = 1
    if spread_rank() != SPREAD_RANK:
        print("DRIFT: spread ranking differs from SPREAD_RANK", file=sys.stderr)
        rc = 1
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
