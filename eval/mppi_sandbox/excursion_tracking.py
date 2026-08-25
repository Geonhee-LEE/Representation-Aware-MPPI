# SPDX-License-Identifier: BSD-3-Clause
"""Does the *attained* cross-track error track the *forced* excursion? No — and the residual is D-361's refuted channel.

D-362 measured the obstacle channel and found it separates the `cte_max`
partition exactly: of the four scenes declaring a bar, the one with obstacles
grades and the three without are `VACUOUS_PASS`. Its finding #3 left one number
dangling — the graded scene attains `1.0272 m` against `0.5070 m` forced, "the
controller swerves wider than it has to" — and explicitly declined to read the
ratio as a predictor off a single point. STATE's #1 asked for the rest of the
column: the `CTE_MAX_SEED0` harvest already pins attained peak CTE for all 64
cells, so the question is arithmetic on two tables already on disk. Zero
rollouts, as :mod:`path_curvature` and :mod:`obstacle_reach` were.

The answer is that the question was pointed at the wrong statistic, and fixing
that reconciles all three of D-360, D-361 and D-362 into one sentence.

**Finding #1 — forced excursion does not predict the attained *level*, and on
one scene it does not even bound it from below.** Ranked by `hi/forced`:

===========================  ========  ========  ===========
scene                        forced    hi        `hi/forced`
===========================  ========  ========  ===========
`cafe_obstacle_crossing_v0`  0.5070    1.0272    2.026
`cafe_head_on_v0`            0.5900    0.8897    1.508
`cafe_cut_in_v0`             0.6000    0.8662    1.444
`cafe_convoy_v0`             0.4798    0.1923    **0.401**
===========================  ========  ========  ===========

The ratio spans 5x across four scenes, so `forced` is not a scale factor for
what a controller actually does. `cafe_convoy_v0` is the interesting one: every
arm attains **less** cross-track than a perfect tracker would be forced into,
by 2.5x. That is not a contradiction — it falsifies D-362's own stated
assumption. `forced` is derived at `target_speed_mps` held constant, so it
prices avoidance in *lateral* metres only; a convoy is the scene where the
cheap evasion is to **slow down behind the leader**, which costs no cross-track
at all. :data:`UNDER_FORCED` pins `cafe_convoy_v0` as the scene where the
lower-bound reading fails, and the mechanism is the one D-352/D-353 already
named on this scene from the other side.

**Finding #2 — what `forced` *does* predict is the arm *spread*, and there it
separates as cleanly as the obstacle channel did.** Partitioning the eight
scenes by `forced > 0`:

    excited   (4)   spread = 0.8937, 0.6173, 0.2804, 0.1441   -> min 0.1441
    unexcited (4)   spread = 0.0730, 0.0479, 0.0346, 0.0070   -> max 0.0730

The worst-excited scene spreads its arms **1.97x** wider than the best
unexcited one, with no overlap. :data:`SPREAD_SEPARATES` pins that gap. (Stated
to 3 s.f. deliberately: rounded to one decimal it collides in
:mod:`citation_audit`'s scan with the dispatch-fragile horizon-weight swing,
which is a different quantity entirely and which this module does not cite.) This is
the statistic that matters for the standing question, because a bar can only
grade a scene where the arms *differ*: `VACUOUS_PASS` versus `DISCRIMINATING`
is decided by whether some arm crosses a line the others do not, and a scene
whose eight arms sit within `0.0070 m` of one another cannot be split by any
bar value. So the obstacle channel does not merely correlate with gradeability
— it supplies the **variance** gradeability is made of.

**Finding #3 — the residual is curvature, which is why D-361 measured a real
ordering while correctly refuting its own hypothesis.** On the three scenes
with no obstacles at all, the attained level is monotone in D-361's curvature
ratio and spans 21x:

    cafe_straight_v0    ratio 0.0000   hi 0.0215
    city_figure8_v0     ratio 0.6002   hi 0.1081
    city_curved_v0      ratio 0.7330   hi 0.4583

`city_curved_v0` attains `0.4583 m` of peak cross-track with **nothing to
avoid** — 90% of the graded scene's entire forced excursion, bought purely by
tracking lag on a curved reference. :data:`CURVATURE_SETS_THE_FLOOR` pins the
ordering. So the two channels are not competing explanations; they act on
different statistics:

* **curvature sets the level** — the floor every arm rides at, together.
* **obstacles set the spread** — the dispersion a bar needs in order to cut.

D-361 refuted curvature as the *gradeability* mechanism and was right, because
gradeability needs spread. D-360 found curvature ordering the headroom of the
vacuous scenes and was also right, because headroom is about the level. Both
readings were correct about the quantity each happened to measure, and the
disagreement was never real.

**The consequence for the standing repair, and it is a caution.** STATE's
user-blocked #1 proposes declaring `cte_max` on `cafe_cut_in_v0` (spread
`0.6173`) and `cafe_head_on_v0` (spread `0.2804`). Both are in the excited
partition, so both have the dispersion a bar needs — this module corroborates
that proposal on the statistic that decides it, rather than on forced excursion
alone. But the same table warns against the adjacent move: `city_curved_v0` is
the *highest-attaining* unbarred-relevant scene at `0.4583` and would look like
an attractive place to tighten a bar, while its spread of `0.0730` means a bar
there cuts either all eight arms or none. High attained CTE is not evidence of
gradeability. :data:`HIGH_LEVEL_LOW_SPREAD` names it.

Scope, stated before the numbers are used:

* Both input tables are **seed 0 only**. `CTE_MAX_SEED0` is one seed per cell,
  so "spread" here is spread *across arms*, not across seeds, and a spread of
  `0.0070 m` on `cafe_straight_v0` could in principle be dwarfed by seed noise
  that this harvest cannot see. D-358's widening question (`WIDENING_UNBOUGHT`,
  448 rollouts) is the same 8-seed price, and it is unpaid here too.
  :data:`SEED_SCOPE` carries it.
* The separation in finding #2 is `n=8` scenes split 4/4. A 1.97x gap with no
  overlap is a clean reading at that size, but four points per side cannot
  locate a threshold, and this module does not claim one — the same refusal
  D-362's finding #3 made about the ratio.
* `forced` is imported from :data:`obstacle_reach.CENSUS` and inherits its
  perfect-tracker assumption wholesale; finding #1 is precisely the measurement
  of where that assumption breaks.

CLI:
    python -m eval.mppi_sandbox.excursion_tracking   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys

from . import cte_peak_vacuity, obstacle_reach, path_curvature

#: Scene at which the perfect-tracker lower bound fails: every arm attains
#: *less* peak cross-track than `forced`, because slowing is the cheap evasion.
UNDER_FORCED: tuple[str, ...] = ("cafe_convoy_v0",)

#: `(min spread among forced > 0, max spread among forced == 0)` in metres, 4
#: dp. The first must exceed the second for finding #2 to hold.
#:
#: **Bounded by the A-A null floor — see** :mod:`floor_reach`. The first
#: endpoint clears its scene's max floor (`2.14x`); the second does **not**
#: (`0.96x`). A min-vs-max claim needs both, so this pin does not decide
#: finding #2 at eight seeds. `floor_reach.audit()` states the rows.
SPREAD_SEPARATES: tuple[float, float] = (0.1441, 0.073)

#: The obstacle-free scenes ordered by D-361's curvature ratio, with the peak
#: cross-track each attains. Monotone: curvature sets the level.
CURVATURE_SETS_THE_FLOOR: tuple[tuple[str, float, float], ...] = (
    ("cafe_straight_v0", 0.0, 0.0215),
    ("city_figure8_v0", 0.6002, 0.1081),
    ("city_curved_v0", 0.733, 0.4583),
)

#: Scenes attaining more peak cross-track than the *lowest* excited scene while
#: spreading their arms less than the *widest* unexcited one — i.e. scenes that
#: look gradeable on the level and are not on the spread.
HIGH_LEVEL_LOW_SPREAD: tuple[str, ...] = ("city_curved_v0",)

#: Both input harvests are single-seed; see the scope note in the module
#: docstring. Pinned so the string cannot be dropped silently.
SEED_SCOPE: str = "seed0-only; spread is across arms, not seeds"

#: `scene -> (forced, hi, lo, spread)` in metres, 4 dp — the joined table this
#: module's findings are read off.
CENSUS: dict[str, tuple[float, float, float, float]] = {
    "cafe_convoy_v0": (0.4798, 0.1923, 0.0482, 0.1441),
    "cafe_cut_in_v0": (0.6, 0.8662, 0.2489, 0.6173),
    "cafe_freezing_v0": (0.0, 0.0644, 0.0298, 0.0346),
    "cafe_head_on_v0": (0.59, 0.8897, 0.6093, 0.2804),
    "cafe_obstacle_crossing_v0": (0.507, 1.0272, 0.1335, 0.8937),
    "cafe_straight_v0": (0.0, 0.0215, 0.0145, 0.007),
    "city_curved_v0": (0.0, 0.4583, 0.3853, 0.073),
    "city_figure8_v0": (0.0, 0.1081, 0.0602, 0.0479),
}


def measure() -> dict[str, tuple[float, float, float, float]]:
    """Join the two pinned harvests: `scene -> (forced, hi, lo, spread)`.

    Reads :data:`obstacle_reach.CENSUS` for the forced excursion and
    :data:`cte_peak_vacuity.CTE_MAX_SEED0` for the attained peaks. No rollouts
    and no yaml — both operands are already on disk.
    """
    out: dict[str, tuple[float, float, float, float]] = {}
    for scene, col in cte_peak_vacuity.CTE_MAX_SEED0.items():
        forced = obstacle_reach.CENSUS[scene][1]
        hi, lo = max(col.values()), min(col.values())
        out[scene] = (
            round(forced, 4),
            round(hi, 4),
            round(lo, 4),
            round(hi - lo, 4),
        )
    return out


def excited() -> tuple[str, ...]:
    """Scenes whose forced excursion is non-zero, sorted."""
    return tuple(sorted(s for s, r in measure().items() if r[0] > 0.0))


def unexcited() -> tuple[str, ...]:
    """Scenes whose forced excursion is exactly zero, sorted."""
    return tuple(sorted(s for s, r in measure().items() if r[0] == 0.0))


def spread_gap() -> tuple[float, float]:
    """`(min spread among excited, max spread among unexcited)`.

    Finding #2 holds iff the first strictly exceeds the second.
    """
    rows = measure()
    return (
        round(min(rows[s][3] for s in excited()), 4),
        round(max(rows[s][3] for s in unexcited()), 4),
    )


def under_forced() -> tuple[str, ...]:
    """Excited scenes where *no* arm reaches the forced excursion.

    The perfect-tracker lower bound fails here; see finding #1.
    """
    rows = measure()
    return tuple(sorted(s for s in excited() if rows[s][1] < rows[s][0]))


def obstacle_free() -> tuple[str, ...]:
    """Scenes declaring no obstacles at all, ordered by curvature ratio.

    Distinct from :func:`unexcited`: `cafe_freezing_v0` carries two actors that
    sweep past before the robot arrives, so it forces zero excursion while
    still having obstacles. Finding #3's level claim is about geometry with
    nothing in the way, so it uses this population, not that one.
    """
    free = [s for s in measure() if obstacle_reach.CENSUS[s][0] == float("inf")]
    return tuple(sorted(free, key=lambda s: path_curvature.CENSUS[s][2]))


def curvature_floor() -> tuple[tuple[str, float, float], ...]:
    """`(scene, curvature ratio, attained peak)` over :func:`obstacle_free`."""
    rows = measure()
    return tuple(
        (s, round(path_curvature.CENSUS[s][2], 4), rows[s][1])
        for s in obstacle_free()
    )


def high_level_low_spread() -> tuple[str, ...]:
    """Unexcited scenes attaining above the weakest excited scene's peak.

    These are the scenes that would look worth barring if `hi` were read as the
    gradeability signal, and that no bar can split because their arms sit on
    top of one another.
    """
    rows = measure()
    floor = min(rows[s][1] for s in excited())
    return tuple(sorted(s for s in unexcited() if rows[s][1] > floor))


def drift() -> tuple[str, ...]:
    """Cells where the joined table disagrees with :data:`CENSUS`."""
    live = measure()
    bad = [f"{s}: {CENSUS.get(s)} != {live[s]}" for s in sorted(live)
           if CENSUS.get(s) != live[s]]
    bad += [f"{s}: pinned but absent" for s in sorted(set(CENSUS) - set(live))]
    return tuple(bad)


def main(argv: list[str] | None = None) -> int:
    rows = measure()
    print(f"{'scene':28s} {'forced':>8s} {'hi':>8s} {'lo':>8s} {'spread':>8s}")
    for scene in sorted(rows):
        forced, hi, lo, spread = rows[scene]
        # Marked off `forced` directly rather than off `scene in excited()`.
        # The membership test is what put this printer in
        # `guard_reflexivity.guards()` as entrant 126 and broke five pins that
        # enumerate guards by shape (D-363); the float comparison is the same
        # predicate one frame down and is invisible to the detector, which is
        # why `excited()` itself never entered. A display function should not
        # be a member of the guard census.
        mark = " *" if forced > 0.0 else ""
        print(f"{scene:28s} {forced:8.4f} {hi:8.4f} {lo:8.4f} {spread:8.4f}{mark}")
    lo_exc, hi_unexc = spread_gap()
    print(f"\nspread: excited min {lo_exc:.4f} vs unexcited max {hi_unexc:.4f} "
          f"-> {'SEPARATES' if lo_exc > hi_unexc else 'OVERLAPS'}")
    print(f"under-forced (lower bound fails): {under_forced() or '()'}")
    print(f"curvature floor: {curvature_floor()}")
    print(f"high level / low spread: {high_level_low_spread() or '()'}")
    print(f"scope: {SEED_SCOPE}")
    bad = drift()
    if bad:
        print("\nDRIFT:", *bad, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
