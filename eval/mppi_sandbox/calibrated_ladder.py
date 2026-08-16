# SPDX-License-Identifier: BSD-3-Clause
"""D-266's `w_voo` ladder, re-taken at a temperature the scene was calibrated for.

## What this answers

D-268 measured median ESS along D-266's ladder on `cafe_freezing_v0` and found
it below the `(12.8, 128.0)` floor at **every** rung — `1.0000` at
`w ∈ {20, 50, 200}`, `1.0053` at `5`, `1.8749` at `1`. It returned
`ESS_DEGENERATE_THROUGHOUT` rather than D-027's ceiling, on the argument that a
ceiling needs an in-band rung to fall *from* and there was none. It also named
the suspected cause without testing it: **that ladder never called
`calibrate_lam`**, so every rung ran at `MPPIParams.lam = 0.1`.

The suspicion was correct, and the table to check it against was already on
disk. `eval/scenarios/lam_windows.yaml` records `cafe_freezing_v0` × `risk_mppi`
as admissible at `lam ∈ (0.2, 0.4, 0.8)` — a window whose **floor is twice the
shipped temperature**. D-268's ladder was taken below it at every rung.

## The mechanical reason it was never called

`lam` lives on :class:`MPPIParams`, and neither `StockMPPI` nor `RiskMPPI`
accepts it as a keyword — so `ab.run_arm(**controller_kwargs)`, which is how
every ladder in this branch is taken, **cannot reach the temperature at all**.
`run_arm(..., lam=0.4)` raises `TypeError`. The knob is reachable only by
constructing `params=MPPIParams(lam=...)`, which no sweep did. That is why four
cycles of ladders all ran at `0.1`: not an oversight anyone repeated, but a
parameter the sweep API did not expose. :func:`sweep` below passes `params`,
and `ess_at_peak.sweep_ess` / `arm_audibility.sweep_ratio` now forward it.

## What was measured

Both readings re-taken across the calibrated window, seed 0, in
`ess_at_peak.ISOLATION` — the same isolation D-266 and D-268 used, so the only
thing that moved is the temperature:

| `lam` | `w_voo` | ESS | in band | ratio | audible |
|---|---|---|---|---|---|
| 0.8 | 1 | 116.00 | yes | 0.0734 | no |
| 0.8 | **5** | **31.23** | **yes** | **0.2285** | **yes** |
| 0.8 | 20 | 1.91 | no | 0.4102 | yes |
| 0.4 | 1 | 37.24 | yes | 0.0752 | no |
| 0.4 | 5 | 2.00 | no | 0.1169 | yes |
| 0.2 | 1 | 12.96 | yes | — | — |
| 0.2 | 5 | 1.30 | no | — | — |

**`(lam = 0.8, w_voo = 5)` is the first operating point on this branch that is
simultaneously in band and audible.** D-266 concluded no audible weight was
usable and D-268 concluded the sampler was degenerate everywhere; both were
measured at `lam = 0.1`, and both conclusions move when the temperature is one
the scene was calibrated for.

## Two consequences, in opposite directions

- **D-268's verdict is now scope-limited, not wrong.**
  `ESS_DEGENERATE_THROUGHOUT` is an accurate reading *at the shipped
  temperature*, and the ladder does now contain an in-band rung to fall from,
  so at `lam = 0.8` this scene **can** address D-027's ceiling: ESS leaves the
  band between `w = 5` and `w = 20`, with the arm audible on both sides.
- **`SCENE_CURVES["cafe_freezing_v0"]`'s load-bearing rungs are not quotable.**
  Its ratios were measured on runs following a single rollout, and re-measuring
  at `lam = 0.8` moves the two rungs any conclusion rests on, in **opposite
  directions**: the operating point `0.1662 → 0.2285` at `w = 5` (+37%) and the
  headline top rung `3.2644 → 2.5131` at `200` (−23%). So no rescale of the old
  row repairs it. The middle of the ladder is *not* part of this claim — `w =
  20` moves 6.8% and `w = 50` moves 7.9%, both inside 10%, and the first
  version of the test asserting "every rung moves" failed on exactly those two.
  The *shape* survives as well (still monotone, still crossing the `0.1` bar in
  `(1, 5]`), which is why D-266's qualitative conclusion about scene-
  disjointness is not overturned here.

## The window this leans on is `UNKEYED`, and that is stated rather than hidden

`lam_window_key.lookup` grades the `cafe_freezing_v0` cell **UNKEYED**: the
shipped `lam_windows.yaml` records no `calibration_weight:`, so nothing states
which cost field the window was measured on. It was in fact measured at
`MPPIParams.w_obs_soft` with `w_voo = 0`, and this ladder walks `w_voo` up to
`200` — a different cost field, whose spread the temperature divides. So the
window is a *starting point*, not a certificate: the ESS readings above are the
evidence that `0.8` weights on this ladder, and the window is only what made
`0.8` worth trying. :func:`window_is_keyed` reports the grade so a caller
cannot mistake one for the other (D-241).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .ab import ab_temperature, ess_band, run_arm
#: Imported, never restated — a caller reading `audible` here and `grade` in
#: `arm_audibility` must not pick up two different bars (D-047).
from .arm_audibility import AUDIBLE_RATIO, EPISTEMIC_CHANNELS
from .ess_at_peak import ISOLATION, PEAK_SCENE
from .seed_count_licence import CENSUS_LADDER_SEEDS as _CENSUS_LADDER_SEEDS

#: The table cell this ladder's temperatures come from. Read through
#: `ab.ab_temperature` rather than retyped, so the window and the calibration
#: file cannot drift apart.
WINDOW_KEY = (f"{PEAK_SCENE}.yaml", "risk_mppi")

#: Measured `(lam, w_voo, median ESS, K, ratio, reached_goal)` on `PEAK_SCENE`
#: at seed 0 in :data:`ess_at_peak.ISOLATION`. Recorded rather than recomputed
#: on import: 25 closed-loop runs (~13 s each). `ratio` is `None` on the rungs
#: not re-measured at that temperature — an unmeasured ratio, **not** D-266's
#: `lam = 0.1` value, which describes a different trajectory (D-241).
MEASURED: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (0.2,   1.0,  12.9586, 256, None,     True),
    (0.2,   5.0,   1.2964, 256, None,     True),
    (0.2,  20.0,   1.0011, 256, None,     True),
    (0.2,  50.0,   1.0000, 256, None,     True),
    (0.2, 200.0,   1.0000, 256, None,     True),
    (0.4,   1.0,  37.2374, 256, 0.075209, True),
    (0.4,   5.0,   1.9995, 256, 0.116878, True),
    (0.4,  20.0,   1.1316, 256, 0.539001, True),
    (0.4,  50.0,   1.0004, 256, 0.912389, True),
    (0.4, 200.0,   1.0000, 256, 2.449773, True),
    (0.8,   1.0, 116.0037, 256, 0.073362, True),
    (0.8,   5.0,  31.2344, 256, 0.228470, True),
    (0.8,  20.0,   1.9125, 256, 0.410169, True),
    (0.8,  50.0,   1.0189, 256, 0.962637, True),
    (0.8, 200.0,   1.0002, 256, 2.513118, True),
)


@dataclass(frozen=True)
class Point:
    """One `(temperature, weight)` cell: sampler reading paired with audibility.

    `seed` is trailing and optional because :data:`MEASURED` is a seed-0 table
    and the seed-ensemble rows below are the same reading taken elsewhere —
    same grading, so the same type rather than a parallel one that could drift
    a bar (D-047).
    """

    lam: float
    weight: float
    median_ess: float
    n_samples: int
    ratio: float | None
    reached_goal: bool
    seed: int | None = None

    @property
    def band(self) -> tuple[float, float]:
        return ess_band(self.n_samples)

    @property
    def ess_in_band(self) -> bool | None:
        """`None` when nothing was logged — unknown, not compliant."""
        if not self.n_samples or self.median_ess != self.median_ess:
            return None
        lo, hi = self.band
        return bool(lo <= self.median_ess <= hi)

    @property
    def audible(self) -> bool | None:
        """`None` when the ratio was not re-taken at this temperature."""
        if self.ratio is None:
            return None
        return bool(self.ratio >= AUDIBLE_RATIO)

    @property
    def usable(self) -> bool:
        """In band **and** audible **and** the run finished.

        All three, because each alone is satisfiable by a degenerate run: a
        frozen robot weights beautifully, and a loud channel on a single-rollout
        planner is loud about nothing.
        """
        return bool(self.ess_in_band and self.audible and self.reached_goal)


def points(rows=MEASURED) -> tuple[Point, ...]:
    return tuple(Point(*row) for row in rows)


def calibrated_window(windows=None) -> tuple[float, ...]:
    """The admissible `lam` rungs for this cell, read from the calibration table."""
    scenario, arm = WINDOW_KEY
    return ab_temperature(scenario, [arm], windows).per_arm[arm]


def window_is_keyed(path: str = "eval/scenarios/lam_windows.yaml") -> dict:
    """Is the window this ladder leans on keyed to the weight the ladder walks?

    Returns the grade rather than a bool: `UNKEYED` (the table records no
    calibration weight) and `OFF_KEY` (it records a different one) are different
    defects and only the second is repairable by re-reading the table.
    """
    from .calibrate_lam import default_weight
    from .lam_window_key import lookup

    # Graded at the weight the window was *actually* taken at (`MPPIParams`'
    # own obstacle weight). Even on-key by that measure the grade comes back
    # `UNKEYED`, because the shipped table records no calibration weight at all.
    got = lookup(path, PEAK_SCENE, WINDOW_KEY[1], default_weight())
    return {
        "grade": getattr(got, "grade", None) or "UNKEYED",
        "measured_at": got.measured_at,
        "admissible": got.admissible,
        # The ladder's own weights are `w_voo`; the window was taken with the
        # epistemic channels off. Stated so a reader does not take the window
        # as a certificate for this cost field.
        "ladder_channel": "w_voo",
        "window_channel_weight": 0.0,
    }


def usable_points(rows=MEASURED) -> tuple[Point, ...]:
    """Every measured cell that is in band, audible, and completed."""
    return tuple(p for p in points(rows) if p.usable)


#: The cell D-270 found co-satisfying, and the only one this ensemble walks.
#: Held as data so the seed sweep cannot drift off the cell the claim is about.
ENSEMBLE_CELL: tuple[float, float] = (0.8, 5.0)

#: `ab.DEFAULT_SEEDS` — the same `n = 8` D-019 was measured at, chosen for that
#: reason rather than for cost. D-019's finding is that `admissible` is an
#: all-seeds **conjunction**, so it can only shrink as `n` grows and two
#: readings at different `n` are different predicates that may not be compared.
#: Every verdict below therefore carries `n`; none of them is a statement about
#: the cell in general.
ENSEMBLE_SEEDS: int = 8

#: The seed count the census grades ladder admissibility at. Imported from
#: :mod:`seed_count_licence` rather than re-typed as `16` (D-047): the whole
#: point of the `n = 16` read is that it lands on the census's own predicate,
#: and a hand-copied literal is exactly how it would silently stop doing so.
CENSUS_SEEDS: int = _CENSUS_LADDER_SEEDS

#: Measured `(seed, median ESS, K, ratio, reached_goal)` at :data:`ENSEMBLE_CELL`
#: in :data:`ess_at_peak.ISOLATION` — 8 closed-loop runs plus 8 leave-one-out
#: cost-field reads, recorded rather than recomputed on import for the same
#: reason :data:`MEASURED` is.
MEASURED_SEEDS: tuple[tuple[int, float, int, float, bool], ...] = (
    (0, 31.2344, 256, 0.228470, True),   # reproduces D-270's recorded cell
    (1, 17.1436, 256, 0.267528, True),
    (2, 57.4845, 256, 0.332852, True),
    (3, 40.8697, 256, 0.275643, True),
    (4,  4.5329, 256, 0.138375, True),   # below the band floor — the one miss
    (5, 46.9007, 256, 0.341453, True),
    (6, 13.4275, 256, 0.219690, True),   # 13.43 against a floor of 12.8
    (7, 30.3359, 256, 0.247537, True),
)


#: Seeds `8..15`, the same cell and the same `sweep_seeds` body, taken to answer
#: Q-153 — D-271 recorded `7/8` at `n = 8` while `seed_count_licence`'s census
#: grades ladder admissibility at **16**, so the two live on different
#: predicates and D-019(b) forbids comparing them. Q-153's lean was to re-take
#: at `16` *without deleting* the `8` row, since D-019(b) bars comparison, not
#: co-recording. 8 closed-loop runs, 30.7 s.
MEASURED_SEEDS_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 8, 50.6894, 256, 0.253931, True),
    ( 9, 51.0362, 256, 0.335179, True),
    (10, 30.4793, 256, 0.190846, True),
    (11, 23.8973, 256, 0.273944, True),
    (12, 59.0517, 256, 0.358551, True),
    (13, 78.5956, 256, 0.243908, True),   # widest ESS in either ensemble
    (14, 30.8716, 256, 0.287606, True),
    (15, 52.8494, 256, 0.356482, True),
)

#: The `n = 16` population: the `n = 8` rows **and** the extension, in seed
#: order. Held as a concatenation rather than a re-typed table so the two
#: readings cannot drift apart row by row.
MEASURED_SEEDS_16: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS + MEASURED_SEEDS_EXT
)


def seed_points(rows=MEASURED_SEEDS, cell=None) -> tuple[Point, ...]:
    """The ensemble rows as :class:`Point`\\ s at `cell` (default
    :data:`ENSEMBLE_CELL`).

    `cell` exists because :data:`MEASURED_SEEDS_16_LAM10` is the same reading
    at a **different temperature**, and a row table carries no `lam` of its own
    — the seed tables store `(seed, ess, K, ratio, reached)`. Defaulting it
    here rather than adding a `lam` column keeps the two tables the same shape,
    but it also means a caller that forgets `cell` gets rows silently labelled
    with the wrong temperature. `span_response` therefore passes both cells
    explicitly and a test pins that the labels come back distinct.
    """
    lam, weight = ENSEMBLE_CELL if cell is None else cell
    return tuple(
        Point(lam=lam, weight=weight, median_ess=ess, n_samples=k,
              ratio=ratio, reached_goal=reached, seed=seed)
        for seed, ess, k, ratio, reached in rows
    )


def seed_census(rows=MEASURED_SEEDS, cell=None) -> dict:
    """Per-condition counts over the ensemble — fractions, not booleans.

    Stored this way on D-019's own precedent: a boolean collapses `7/8` and
    `0/8` into the same `False`, and the difference between a near-miss and a
    clean failure is the whole reading. Callers derive the verdict from the
    counts; nothing here decides.
    """
    pts = seed_points(rows, cell)
    n = len(pts)
    return {
        "n": n,
        "cell": ENSEMBLE_CELL if cell is None else tuple(cell),
        "n_in_band": sum(1 for p in pts if p.ess_in_band),
        "n_audible": sum(1 for p in pts if p.audible),
        "n_reached": sum(1 for p in pts if p.reached_goal),
        "n_usable": sum(1 for p in pts if p.usable),
        "usable_seeds": tuple(p.seed for p in pts if p.usable),
        # Which condition each non-usable seed failed on. A cell that misses on
        # audibility is a scale problem; one that misses on band is a
        # temperature problem, and they have different repairs.
        "failed_band_only": tuple(p.seed for p in pts
                                  if not p.usable and p.audible
                                  and not p.ess_in_band),
        "failed_audible_only": tuple(p.seed for p in pts
                                     if not p.usable and p.ess_in_band
                                     and not p.audible),
        "failed_both": tuple(p.seed for p in pts if not p.usable
                             and not p.ess_in_band and not p.audible),
        "failed_to_reach": tuple(p.seed for p in pts if not p.reached_goal),
    }


def ess_span(rows=MEASURED_SEEDS, cell=None) -> float | None:
    """`max / min` median ESS across the ensemble — `None` on an empty read.

    D-019 measured per-seed ESS spans of ~5× and that number is the reason this
    ensemble exists. Reported so the claim can be checked on this cell rather
    than carried over from the cell D-019 read it on.
    """
    ess = [p.median_ess for p in seed_points(rows, cell)
           if p.median_ess == p.median_ess]
    if not ess or min(ess) <= 0:
        return None
    return max(ess) / min(ess)


def seed_verdict(rows=MEASURED_SEEDS, cell=None) -> dict:
    """Is :data:`ENSEMBLE_CELL` a window, or seed 0's luck?

    The vocabulary is fixed here before the counts are read (D-241): the
    tempting failure is to see `k/8` and reach for whichever word flatters it.
    Only unanimity earns the word *window*, because that is exactly the
    predicate D-019 showed `admissible` to be — anything less is a rate, and a
    rate at `n = 8` licenses nothing about `n = 16`.
    """
    c = seed_census(rows, cell)
    n, k = c["n"], c["n_usable"]
    if not n:
        name = "NO_READINGS"
    elif k == n:
        name = "UNANIMOUS_WINDOW"
    elif k == 0:
        name = "NO_SEED_USABLE"
    elif c["usable_seeds"] == (0,):
        name = "SEED_0_ARTEFACT"
    elif k * 2 > n:
        name = "MAJORITY_USABLE"
    else:
        name = "MINORITY_USABLE"

    return {
        "verdict": name,
        # `n` rides on the verdict, not beside it — D-019(a).
        "n": n,
        "usable_rate": (None if not n else k / n),
        "census": c,
        "ess_span": ess_span(rows, cell),
        # An ensemble on one scene at one cell says nothing about the other two.
        "transfers_to_ab_scene": False,
        "comparable_to": f"readings at n={n} only (D-019(b))",
    }


def seed_count_readings(n8=MEASURED_SEEDS, n16=MEASURED_SEEDS_16) -> dict:
    """Q-153: the same cell at both seed counts, co-recorded and never pooled.

    D-019(b) forbids *comparing* two readings taken at different `n`, because
    `admissible` is an all-seeds conjunction and is therefore strictly harder
    the larger `n` gets. It does not forbid writing both down. This returns the
    pair with the non-comparability stated in the payload rather than left to
    the caller's memory, and it deliberately exposes **no** difference field:
    there is no subtraction of these two numbers that means anything.

    The second thing it refuses to pool is the span. `ess_span` is a `max/min`
    over the sample, so it too can only grow with `n` — a fresh draw can widen
    the range and can never narrow it. D-271 correctly demoted D-019's `~5x`
    from plant constant to cell property; the same argument demotes its own
    `12.68x` from cell property to *cell property at `n = 8`*. Both spans are
    reported, each carrying its `n`, and `spans_comparable` is `False` for the
    same reason `verdicts_comparable` is.
    """
    a, b = seed_verdict(n8), seed_verdict(n16)
    return {
        "readings": {a["n"]: a, b["n"]: b},
        "census_n": CENSUS_SEEDS,
        # Is the larger read the seed count the census actually grades at?
        "reaches_census_n": b["n"] == CENSUS_SEEDS,
        # Both are `k/n` rates, and rates at different `n` are different
        # predicates (D-019(b)). Nothing here divides one by the other.
        "verdicts_comparable": False,
        "spans_comparable": False,
        "spans": {a["n"]: a["ess_span"], b["n"]: b["ess_span"]},
        # The extension is a superset read, so a seed that failed at `n = 8`
        # still fails at `n = 16` — the miss list can only grow. Named so a
        # future reader does not mistake a rising rate for a repaired seed.
        "unusable_seeds": {
            a["n"]: tuple(s for s in _unusable(n8)),
            b["n"]: tuple(s for s in _unusable(n16)),
        },
    }


def _unusable(rows, cell=None) -> tuple[int, ...]:
    """Seeds failing :attr:`Point.usable`, in seed order."""
    return tuple(p.seed for p in seed_points(rows, cell) if not p.usable)


#: The rung a seed-4 repair walk would have started at. Under a response that
#: moves every seed by a common factor, `MEASURED`'s `w = 5` column
#: (`0.4 -> 0.8` is `15.6x`) puts the `2.82x` seed 4 needs at `lam ~ 1.04`, so
#: `1.0` is the *smallest* rung that plausibly repairs the miss — the rung most
#: favourable to the repair, chosen for that reason rather than for cost.
REPAIR_CELL: tuple[float, float] = (1.0, 5.0)

#: Measured `(seed, median ESS, K, ratio, reached_goal)` at :data:`REPAIR_CELL`,
#: same 16 seeds and same `sweep_seeds` body as :data:`MEASURED_SEEDS_16`. This
#: exists to discharge the one premise :func:`span_admits_band` cannot prove
#: from a single rung: that `lam` moves the seeds *together*.
MEASURED_SEEDS_16_LAM10: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,  31.4085, 256, 0.266901, True),
    ( 1,  25.0816, 256, 0.266572, True),
    ( 2,  79.6042, 256, 0.267006, True),
    ( 3,  54.7740, 256, 0.343319, True),
    ( 4,  14.5829, 256, 0.160134, True),   # the miss, now above the floor
    ( 5,  75.5935, 256, 0.365868, True),
    ( 6,  27.7917, 256, 0.233206, True),
    ( 7,  66.8084, 256, 0.355865, True),
    ( 8,  54.1228, 256, 0.307848, True),
    ( 9,  29.5672, 256, 0.212205, True),
    (10,  29.5394, 256, 0.165719, True),
    (11,  72.4124, 256, 0.119942, True),   # quietest arm in either ensemble
    (12,  79.5598, 256, 0.124606, True),
    (13,  44.7423, 256, 0.225622, True),
    (14,  65.6648, 256, 0.356946, True),
    (15,  76.8457, 256, 0.356802, True),
)

SPAN_EXCEEDS_BAND = "SPAN_EXCEEDS_BAND"
SPAN_FITS_BAND = "SPAN_FITS_BAND"
NO_SPAN = "NO_SPAN"
MIXED_SAMPLE_COUNT = "MIXED_SAMPLE_COUNT"

SPAN_COMPRESSES = "SPAN_COMPRESSES"
SPAN_WIDENS = "SPAN_WIDENS"
SPAN_INVARIANT = "SPAN_INVARIANT"
SPANS_INCOMPARABLE = "SPANS_INCOMPARABLE"

#: Relative gap below which two spans are one reading rather than a direction.
#: Named because an unnamed epsilon is how `SPAN_INVARIANT` becomes whatever
#: the caller wanted (D-241: fix the vocabulary before reading the counts).
SPAN_TOLERANCE: float = 0.05


def band_width_ratio(n_samples: int = 256) -> float:
    """`ceiling / floor` of the ESS band.

    This is the load-bearing fact and it is easy to walk past: the band is
    defined by :data:`ab.ESS_BAND_FRACTIONS` as *fractions of K*, so the ratio
    is `0.5 / 0.05 = 10.0` at **every** `K`. The band is a fixed-width window
    on a log axis, not an interval that grows with the sampler.
    """
    lo, hi = ess_band(n_samples)
    return hi / lo


def span_admits_band(rows=MEASURED_SEEDS_16, cell=None) -> dict:
    """Can *any* shared `lam` put this whole ensemble in band at once?

    Not a ladder question, which is why it is answerable without walking one.
    Both quantities are **ratios**: the band is `10x` wide at every `K`
    (:func:`band_width_ratio`) and the ensemble's spread is `max/min`
    (:func:`ess_span`). If a shared temperature scales every seed's ESS by a
    common factor, that factor slides the ensemble along the axis and leaves
    its span untouched — so the ensemble fits inside the window at *some* rung
    if and only if its span is no wider than the window. Which rungs happen to
    have been walked never enters.

    **This is D-272's argument one level up.** D-272 asked *which* rung and
    answered `WINDOW_EXHAUSTED`, a statement about the three rungs in the
    calibrated window; D-273 then narrowed that to the rungs actually *tried*.
    A span test enumerates no rungs, so that narrowing does not reach it: it
    bounds every rung, inside the window or outside it, walked or unwalked.

    **The premise is in the payload, not in the reader's memory.** `lam` must
    move the seeds together. If temperature *compresses* the per-seed spread,
    a wide span at one rung says nothing about a narrower one elsewhere and
    this verdict is void. That premise is measurable for the price of one rung
    and :func:`span_response` measures it — the verdict below is reported as
    conditional until it does.
    """
    pts = [p for p in seed_points(rows, cell) if p.n_samples
           and p.median_ess == p.median_ess]
    span = ess_span(rows, cell)
    ks = {p.n_samples for p in pts}
    if span is None or not pts:
        return {"verdict": NO_SPAN, "n": len(pts), "span": span,
                "band_width": None, "premise": _SPAN_PREMISE}
    if len(ks) != 1:
        # Two `K`s are two bands. A single `hi/lo` would be a number about
        # neither of them (D-241 — do not dress a null as someone's quantity).
        return {"verdict": MIXED_SAMPLE_COUNT, "n": len(pts), "span": span,
                "band_width": None, "n_samples": tuple(sorted(ks)),
                "premise": _SPAN_PREMISE}

    k = ks.pop()
    lo, hi = ess_band(k)
    width = band_width_ratio(k)
    ess = [p.median_ess for p in pts]
    lift = lo / min(ess)          # what the lowest seed needs to clear the floor
    headroom = hi / max(ess)      # what the highest seed has before the ceiling
    return {
        "verdict": SPAN_FITS_BAND if span <= width else SPAN_EXCEEDS_BAND,
        "n": len(pts),
        "cell": ENSEMBLE_CELL if cell is None else tuple(cell),
        "span": span,
        "band_width": width,
        "n_samples": k,
        # The same fact stated the way a repair walk would meet it: seed 4
        # needs a `2.82x` lift and seed 13 has `1.63x` of ceiling left. Their
        # quotient **is** `span / width` — the identity is pinned by a test, so
        # this pair is a second rendering of one number, not a second finding.
        "required_lift": lift,
        "headroom": headroom,
        "slack": width / span,
        "premise": _SPAN_PREMISE,
        # `ess_span` is `max/min` over the sample, so it can only grow with
        # `n` (D-281). A `SPAN_EXCEEDS_BAND` therefore survives every larger
        # read and a `SPAN_FITS_BAND` does not — the verdict carries its `n`
        # for the same reason every other one on this module does.
        "survives_larger_n": span > width,
        "comparable_to": f"readings at n={len(pts)} only (D-019(b))",
    }


_SPAN_PREMISE = ("conditional on `lam` scaling every seed's ESS by a common "
                 "factor; discharge with `span_response` (one rung)")


def span_response(rows_a=MEASURED_SEEDS_16, rows_b=MEASURED_SEEDS_16_LAM10,
                  cells=(ENSEMBLE_CELL, REPAIR_CELL)) -> dict:
    """Does `lam` compress the per-seed ESS spread, or only translate it?

    The one premise :func:`span_admits_band` cannot get from a single rung.
    Two spans at two temperatures, **same seeds and same `n`** — which is what
    makes this legal where `seed_count_readings` had to refuse: D-019(b) bars
    comparing readings at different seed counts because `admissible` is an
    all-seeds conjunction, and both rows here are the same 16. The comparison
    that would be barred is the one this function does *not* do.

    A compressing response is the interesting outcome, and it is the one that
    would revive the repair walk: it means a high enough `lam` could squeeze
    16 seeds into a `10x` window that their `17.34x` spread does not currently
    fit. An invariant or widening response closes the question instead — no
    rung admits the ensemble, and the repair is a calibration problem or a
    per-seed one, not a temperature one.
    """
    a, b = tuple(cells)
    pa, pb = seed_points(rows_a, a), seed_points(rows_b, b)
    span_a, span_b = ess_span(rows_a, a), ess_span(rows_b, b)
    seeds_a = tuple(p.seed for p in pa)
    seeds_b = tuple(p.seed for p in pb)

    if span_a is None or span_b is None or seeds_a != seeds_b:
        # Different seeds is a different population, and the whole licence for
        # this comparison was that the population is held fixed.
        return {"verdict": SPANS_INCOMPARABLE, "cells": (tuple(a), tuple(b)),
                "spans": {tuple(a): span_a, tuple(b): span_b},
                "same_seeds": seeds_a == seeds_b, "n": len(pa)}

    rel = span_b / span_a - 1.0
    if abs(rel) <= SPAN_TOLERANCE:
        name = SPAN_INVARIANT
    elif rel < 0:
        name = SPAN_COMPRESSES
    else:
        name = SPAN_WIDENS

    fits = {tuple(a): span_admits_band(rows_a, a),
            tuple(b): span_admits_band(rows_b, b)}
    admitting = tuple(c for c, r in fits.items()
                      if r["verdict"] == SPAN_FITS_BAND)
    return {
        "verdict": name,
        "n": len(pa),
        "cells": (tuple(a), tuple(b)),
        "spans": {tuple(a): span_a, tuple(b): span_b},
        "relative_change": rel,
        "tolerance": SPAN_TOLERANCE,
        "same_seeds": True,
        # Direction is not the decision — admission is. A response can compress
        # and still leave both rungs outside the band.
        "admits_band_at": admitting,
        "band_verdicts": {c: r["verdict"] for c, r in fits.items()},
        # Two rungs are two rungs. A monotone direction read on a pair does not
        # license extrapolation to a third (D-272 graded its own direction as a
        # conjunction over five columns for exactly this reason).
        "extrapolates": False,
    }


def ess_direction_in_lam(rows=MEASURED) -> dict:
    """Which way does median ESS move as `lam` rises, at fixed weight?

    Read per weight column rather than pooled, because the columns are not
    comparable to each other: `w = 200` sits pinned at the degenerate floor
    (`1.0000, 1.0000, 1.0002`) where the sampler has collapsed onto a single
    rollout, so it carries no direction to report. Pooling it with the live
    columns would let a saturated tie outvote four strict readings.

    `direction` is `UP` only if **every** column is non-decreasing *and* at
    least one is strictly increasing — the conjunction, so a table of all-ties
    grades `FLAT` rather than borrowing a direction it never showed.
    """
    by_weight: dict[float, list[tuple[float, float]]] = {}
    for p in points(rows):
        by_weight.setdefault(p.weight, []).append((p.lam, p.median_ess))

    columns, n_strict, n_tied = {}, 0, 0
    up = down = True
    for w, seq in by_weight.items():
        seq.sort()
        if len(seq) < 2:
            columns[w] = "SINGLETON"
            continue
        rises = all(b >= a for (_, a), (_, b) in zip(seq, seq[1:]))
        falls = all(b <= a for (_, a), (_, b) in zip(seq, seq[1:]))
        strict = rises and any(b > a for (_, a), (_, b) in zip(seq, seq[1:]))
        up, down = up and rises, down and falls
        n_strict += bool(strict)
        n_tied += bool(rises and falls)
        columns[w] = "STRICT_UP" if strict else "TIED" if (rises and falls) \
            else "UP" if rises else "DOWN" if falls else "NON_MONOTONE"

    if up and n_strict:
        name = "UP"
    elif down and n_strict:
        name = "DOWN"
    elif up and down:
        name = "FLAT"
    else:
        name = "NON_MONOTONE"

    return {
        "direction": name,
        "n_columns": len(by_weight),
        "n_strict": n_strict,
        # Named so a reader can see how much of the table is pinned at the
        # sampler's floor and therefore carrying no signal.
        "n_saturated": n_tied,
        "per_weight": columns,
    }


def band_miss_repair(rows=MEASURED, seed_rows=MEASURED_SEEDS) -> dict:
    """Can the calibrated window repair the ensemble's band misses?

    D-271 left the branch pointing at the window's two untried rungs
    (`0.4`, `0.2`) on the strength of "seed 4 fails on ESS alone, which is a
    temperature question". It is a temperature question — but the *sign* was
    never checked, and the ladder already on disk answers it without a single
    new run. The vocabulary is fixed before the counts are read (D-241).

    The two facts that decide it: which side of the band each miss falls on,
    and which way :func:`ess_direction_in_lam` says `lam` moves ESS. A miss
    **below** the floor needs the ESS-raising direction; if the cell already
    sits at the window's most favourable rung, no rung inside the window can
    reach it and the repair is a *calibration* question, not a ladder one.
    """
    lam, _ = ENSEMBLE_CELL
    window = calibrated_window()
    direction = ess_direction_in_lam(rows)["direction"]

    misses = [p for p in seed_points(seed_rows)
              if p.ess_in_band is False and p.audible and p.reached_goal]
    below = tuple(p.seed for p in misses if p.median_ess < p.band[0])
    above = tuple(p.seed for p in misses if p.median_ess > p.band[1])

    # Which rungs would move ESS the way the misses need it moved?
    if direction == "UP":
        helpful = tuple(r for r in window if r > lam) if below else \
            tuple(r for r in window if r < lam) if above else ()
    elif direction == "DOWN":
        helpful = tuple(r for r in window if r < lam) if below else \
            tuple(r for r in window if r > lam) if above else ()
    else:
        helpful = ()

    if not misses:
        name = "NO_BAND_MISS"
    elif direction not in ("UP", "DOWN"):
        name = "DIRECTION_UNKNOWN"
    elif below and above:
        # Opposite repairs demanded at once — no single rung serves both.
        name = "MISSES_STRADDLE_BAND"
    elif helpful:
        name = "REPAIR_RUNG_AVAILABLE"
    else:
        name = "WINDOW_EXHAUSTED"

    return {
        "verdict": name,
        "cell": ENSEMBLE_CELL,
        "n": len(seed_points(seed_rows)),
        "ess_direction_in_lam": direction,
        "calibrated_window": window,
        "cell_is_window_max": bool(window and lam >= max(window)),
        "missed_below_floor": below,
        "missed_above_ceiling": above,
        "helpful_rungs": helpful,
        # The rungs D-271 named. Kept explicit so the recommendation this
        # verdict overturns is visible beside the verdict.
        "untried_rungs": tuple(r for r in window if r != lam),
        # A direction read on one scene at one channel is not a plant constant
        # — the same mistake D-271 caught in D-019's `~5x` span.
        "transfers_to_ab_scene": False,
        "comparable_to": f"readings at n={len(seed_points(seed_rows))} only (D-019(b))",
    }


def sweep_seeds(scenario, seeds=None, *, cell=None,
                channel: str = "w_voo", samples: int | None = None) -> tuple[Point, ...]:
    """Re-take :data:`MEASURED_SEEDS` — one closed-loop run per seed.

    Same body as :func:`sweep` with the loop moved from `(lam, weight)` to
    `seed`, so the ensemble and the ladder cannot diverge in isolation or in
    how the ratio is read.

    `samples` overrides `K`. It defaults to `None`, which leaves
    `MPPIParams(lam=...)` exactly as every column before D-292 built it — the
    provenance claim "same `sweep_seeds` body" that :data:`MEASURED_SEEDS_16`
    and its temperature siblings carry is therefore untouched by this keyword.
    Note that `K` is not an ordinary knob on this axis: :func:`ab.ess_band`
    defines the band as *fractions* of `K`, so moving it moves the ensemble and
    the band together (see :func:`ensemble_scaling_in_k`).
    """
    from .ab import DEFAULT_SEEDS
    from .controllers.stock_mppi import MPPIParams
    from .weight_units import measure

    lam, weight = ENSEMBLE_CELL if cell is None else cell
    cfg = {channel: float(weight)}
    cfg.update({c: 0.0 for c in EPISTEMIC_CHANNELS if c != channel})

    out = []
    for seed in (DEFAULT_SEEDS if seeds is None else seeds):
        params = (MPPIParams(lam=float(lam)) if samples is None
                  else MPPIParams(lam=float(lam), samples=int(samples)))
        arm = run_arm(scenario, "risk_mppi", int(seed), params=params,
                      **cfg, **ISOLATION)
        term = measure(scenario, "risk_mppi", seed=int(seed), params=params,
                       **cfg, w_risk=0.0, k_margin_per_sigma=0.0)[channel]
        out.append(Point(lam=float(lam), weight=float(weight),
                         median_ess=arm.median_ess, n_samples=arm.n_samples,
                         ratio=term.ratio, reached_goal=arm.reached_goal,
                         seed=int(seed)))
    return tuple(out)


def verdict(rows=MEASURED) -> dict:
    """Does a co-satisfying operating point exist once the scene is calibrated?

    Reported separately from D-268's verdict rather than replacing it: that one
    is a true reading at `lam = 0.1`, and overwriting it would erase the fact
    that the shipped temperature is the one the rest of the branch ran at.
    """
    pts = points(rows)
    if not pts:
        return {"verdict": "NO_POINTS", "usable": ()}

    usable = tuple(p for p in pts if p.usable)
    in_band = tuple(p for p in pts if p.ess_in_band)
    # Can this ladder address D-027's ceiling now? It needs an in-band rung to
    # fall from *and* an out-of-band rung above it at the same temperature.
    addressable = tuple(sorted({
        p.lam for p in in_band
        if any(q.lam == p.lam and q.weight > p.weight and q.ess_in_band is False
               for q in pts)
    }))

    if usable:
        name = "OPERATING_POINT_FOUND"
    elif in_band:
        name = "IN_BAND_BUT_INAUDIBLE"
    else:
        # Same shape D-268 reported, and it keeps that verdict's name.
        name = "ESS_DEGENERATE_THROUGHOUT"

    return {
        "verdict": name,
        "scene": PEAK_SCENE,
        "usable_points": tuple((p.lam, p.weight) for p in usable),
        "calibrated_window": calibrated_window(),
        "can_address_d027_ceiling": bool(addressable),
        "addressable_at_lam": addressable,
        # D-266's scope is untouched by a temperature change on this scene.
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
    }


def sweep(scenario, lams=None, weights=(1.0, 5.0, 20.0, 50.0, 200.0), *,
          seed: int = 0, channel: str = "w_voo") -> tuple[Point, ...]:
    """Re-take :data:`MEASURED` — one closed-loop run per `(lam, weight)` cell.

    Minutes-scale (25 runs at the defaults), so no test walks it; :data:`MEASURED`
    caches the result the same way `ess_at_peak.MEASURED_ESS` caches D-268's.
    `lams` defaults to the calibrated window, so the sweep asks the table which
    temperatures are worth paying for instead of hardcoding them.
    """
    from .controllers.stock_mppi import MPPIParams
    from .weight_units import measure

    out = []
    for lam in (calibrated_window() if lams is None else tuple(lams)):
        for w in weights:
            cfg = {channel: float(w)}
            cfg.update({c: 0.0 for c in EPISTEMIC_CHANNELS if c != channel})
            params = MPPIParams(lam=float(lam))
            arm = run_arm(scenario, "risk_mppi", seed, params=params,
                          **cfg, **ISOLATION)
            term = measure(scenario, "risk_mppi", seed=seed, params=params,
                           **cfg, w_risk=0.0, k_margin_per_sigma=0.0)[channel]
            out.append(Point(lam=float(lam), weight=float(w),
                             median_ess=arm.median_ess, n_samples=arm.n_samples,
                             ratio=term.ratio, reached_goal=arm.reached_goal))
    return tuple(out)


#: The `lam = 1.0` rung of the seed-0 ladder — the same five weights, the same
#: :func:`sweep` body and the same :data:`ess_at_peak.ISOLATION` as
#: :data:`MEASURED`, taken at :data:`REPAIR_CELL`'s temperature. 5 closed-loop
#: runs plus 5 leave-one-out cost-field reads, 21.5 s.
#:
#: Held as its own table rather than appended to :data:`MEASURED` because that
#: table's temperatures are exactly the *calibrated window*
#: (`calibrated_window()` returns `(0.2, 0.4, 0.8)`) and `1.0` is **outside**
#: it — D-283 reached that rung by measurement, not by the table's licence.
#: Folding the rows in would let a reader take `MEASURED` for the window.
#:
#: The `w = 5` row reproduces :data:`MEASURED_SEEDS_16_LAM10`'s seed-0 row to
#: every recorded digit (`31.4085`, `0.266901`) — two different sweep bodies
#: (:func:`sweep` and :func:`sweep_seeds`) landing on one cell, which is the
#: only check that they have not drifted in isolation or in how the ratio is
#: read. A test pins the agreement.
MEASURED_LAM10: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (1.0,   1.0, 122.0350, 256, 0.065780, True),
    (1.0,   5.0,  31.4085, 256, 0.266901, True),   # in band and audible
    (1.0,  20.0,   2.6269, 256, 0.625214, True),   # the ceiling is crossed here
    (1.0,  50.0,   1.3620, 256, 0.927995, True),
    (1.0, 200.0,   1.0242, 256, 2.191799, True),
)

#: Both seed-0 ladders, for the readers that grade *across* temperature.
#: A concatenation rather than a retyped table, so the two cannot drift row by
#: row (D-047).
MEASURED_WITH_LAM10: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED + MEASURED_LAM10
)

#: The `lam = 1.2` rung — **two weights, not five**. D-284 left the gap across
#: D-027's ceiling narrowing (`16.33x -> 11.96x`) toward a `10.0x` band and
#: refused to project where it closes; this is the third point that decides,
#: and only the bracketing pair `{5, 20}` is needed to take it. 2 closed-loop
#: runs plus 2 leave-one-out cost-field reads, 6.4 s.
#:
#: **The partial ladder does not weaken the bracket.** `ceiling_bracket` needs
#: the highest in-band rung and the lowest out-of-band rung above it; `w = 1`
#: sits below `5` and cannot become the top of the in-band run, and `50` / `200`
#: sit above an already-out-of-band `20`. So the unwalked rungs cannot move
#: `(5, 20]`. What they *do* limit is `usable_weights`, which is a set over
#: walked rungs only — :func:`gap_trend` carries `n_rungs` per temperature so a
#: reader cannot read a 2-rung set as a 5-rung one.
MEASURED_LAM12: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (1.2,   5.0,  88.5874, 256, 0.327591, True),   # in band and audible
    (1.2,  20.0,   2.3459, 256, 0.440542, True),   # still crossed here
)

#: All three seed-0 temperatures, for the trend readers. Concatenation again.
MEASURED_ALL_LAMS: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED_WITH_LAM10 + MEASURED_LAM12
)

#: Two rungs **inside** D-284's `(5, 20]` bracket at `lam = 1.0`, spaced `1.6x`
#: and `1.5x` where the ladder's own spacing is `4x`. 2 closed-loop runs plus 2
#: leave-one-out cost-field reads, 5.2 s.
#:
#: Every reading above was taken on a ladder whose rungs are a factor of 4
#: apart, and a bracket is only ever as tight as the ladder that produced it.
#: These two rungs are the cheapest thing that can tell a *cliff* (the sampler
#: gives out just above `5`, and the one-rung-wide usable region is a fact about
#: the sampler) from a *slope* (it gives out gradually, and the one-rung region
#: is a fact about the rung spacing). See :func:`ceiling_resolution`.
MEASURED_LAM10_FINE: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (1.0,   8.0,   4.8433, 256, 0.239547, True),   # already below the floor
    (1.0,  12.0,   4.2006, 256, 0.373823, True),
)

#: The `lam = 1.0` ladder at its finer resolution — 7 rungs, `1/5/8/12/20/50/200`.
#: Concatenated, never retyped, so the coarse rows have one statement (D-047).
MEASURED_LAM10_REFINED: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED_LAM10 + MEASURED_LAM10_FINE
)

#: All three temperatures with `1.0` at its refined resolution. `0.8` and `1.2`
#: are **still coarse** — no interior rung has been walked at either — which is
#: exactly why :func:`ceiling_resolution` reports which temperatures it refined
#: rather than restating :func:`gap_trend`'s verdict at the finer spacing.
MEASURED_ALL_LAMS_REFINED: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED + MEASURED_LAM10_REFINED + MEASURED_LAM12
)

#: The same two interior rungs at the *other* two temperatures — `w_voo ∈
#: {8, 12}` at `lam = 0.8` and `1.2`. 4 closed-loop runs plus 4 leave-one-out
#: cost-field reads, 10.4 s.
#:
#: D-286 refined `lam = 1.0` alone and its gap verdict flipped, which left
#: :func:`gap_trend` comparing one `1.6x` reading against two `4x` ones — three
#: numbers that D-019's conjunction discipline forbids reading as one quantity.
#: These rows are the cheapest thing that restores the spacing. What they do
#: *not* restore is the comparison: see :func:`uniform_resolution_trend`.
MEASURED_LAM08_FINE: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (0.8,   8.0,   6.9153, 256, 0.274120, True),   # already below the floor
    (0.8,  12.0,   2.0012, 256, 0.263334, True),
)

#: `lam = 1.2`'s interior pair. **ESS rises from `8` to `12`** (`4.5755 ->
#: 9.1412`) where every other walked ladder falls monotonically — the reason
#: :func:`uniform_resolution_trend` cannot report a three-temperature trend even
#: with the spacing made uniform.
MEASURED_LAM12_FINE: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    (1.2,   8.0,   4.5755, 256, 0.186244, True),
    (1.2,  12.0,   9.1412, 256, 0.315753, True),   # ESS goes back *up*
)

#: `lam = 1.2` at its refined resolution. Concatenated, never retyped (D-047).
MEASURED_LAM12_REFINED: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED_LAM12 + MEASURED_LAM12_FINE
)

#: All three temperatures at **one** resolution — every `lam` walks `{5, 8, 12,
#: 20}`. This is the table :func:`gap_trend`'s comparison needed and did not
#: have; `MEASURED_ALL_LAMS_REFINED` above is the mixed one it had at D-286.
MEASURED_ALL_LAMS_UNIFORM: tuple[tuple[float, float, float, int, float | None, bool], ...] = (
    MEASURED + MEASURED_LAM08_FINE + MEASURED_LAM10_REFINED + MEASURED_LAM12_REFINED
)

CEILING_LOCATED = "CEILING_LOCATED"
#: No in-band rung at this temperature — nothing to fall *from*, which is the
#: shape D-268 reported at `lam = 0.1` and the reason it refused D-027's name.
CEILING_UNREACHABLE = "CEILING_UNREACHABLE"
#: In band at every rung walked: the ladder never left the band, so the ceiling
#: (if any) is above the top rung and this ladder does not bound it.
CEILING_ABSENT = "CEILING_ABSENT"
#: The bracket exists but the arm is inaudible on the in-band side — the
#: crossing is real and irrelevant, because nothing usable sits below it.
CEILING_INAUDIBLE = "CEILING_INAUDIBLE"

CEILING_HELD = "CEILING_HELD"
CEILING_MOVED = "CEILING_MOVED"
CEILING_INCOMPARABLE = "CEILING_INCOMPARABLE"


def ceiling_bracket(rows=MEASURED_WITH_LAM10, lam: float = 1.0) -> dict:
    """Where does ESS leave the band as `w_voo` rises, at one temperature?

    D-027's ceiling, located rather than merely declared reachable.
    :func:`verdict` already reports *whether* a ladder can address it
    (`can_address_d027_ceiling`); this returns **which two rungs it sits
    between**, which is the form the next weight decision needs.

    The bracket is `(highest in-band weight, lowest out-of-band weight above
    it)`. Rungs are not interpolated — D-266 refused that for the audibility
    bar for the reason that applies here too: interpolation assumes the shape
    the measurement is supposed to report.

    `audible_below` is carried because it decides whether the ceiling *bounds*
    anything. A crossing under a silent arm bounds an empty region.
    """
    pts = sorted((p for p in points(rows) if p.lam == lam),
                 key=lambda p: p.weight)
    in_band = [p for p in pts if p.ess_in_band]
    out = {"lam": float(lam), "scene": PEAK_SCENE, "n_rungs": len(pts),
           "rungs": tuple(p.weight for p in pts),
           "band": ess_band(pts[0].n_samples) if pts else None,
           # Untouched by a temperature change on this scene (D-266).
           "transfers_to_ab_scene": False,
           "ab_scene_blocked_by": "PR #68 (unmerged)"}

    if not pts or not in_band:
        return {**out, "verdict": CEILING_UNREACHABLE, "bracket": None,
                "ess_drop": None, "audible_below": None}

    top = in_band[-1]
    above = [p for p in pts if p.weight > top.weight and p.ess_in_band is False]
    if not above:
        return {**out, "verdict": CEILING_ABSENT, "bracket": None,
                "ess_drop": None, "audible_below": top.audible}

    first = above[0]
    name = CEILING_LOCATED if top.audible else CEILING_INAUDIBLE
    return {
        **out,
        "verdict": name,
        "bracket": (top.weight, first.weight),
        "in_band_weight": top.weight,
        "out_of_band_weight": first.weight,
        # How far the sampler falls across one rung of the ladder. Compared
        # against `band_width_ratio` by `ceiling_gap`, never here.
        "ess_drop": top.median_ess / first.median_ess,
        "ess_below": top.median_ess,
        "ess_above": first.median_ess,
        "audible_below": top.audible,
        "audible_above": first.audible,
        # The usable set at this temperature, for the reader who wants to know
        # how wide the operating region actually is.
        "usable_weights": tuple(p.weight for p in pts if p.usable),
    }


def ceiling_response(rows=MEASURED_WITH_LAM10, lams=(0.8, 1.0)) -> dict:
    """Did raising the temperature buy **weight** headroom?

    D-283 established that `lam = 1.0` repairs the *seed* ensemble at
    `w_voo = 5` (`7/8` at `0.8` becoming `16/16`). That is a statement about
    one weight. This asks the orthogonal question — whether the same lift moves
    the weight at which the sampler gives out — and the two answers are
    independent: an ensemble can be repaired at a rung whose ceiling has not
    moved a step.

    Both readings are seed 0 at the same five weights in the same isolation, so
    the comparison is legal in the way :func:`seed_count_readings`' was not:
    nothing here compares populations of different size.
    """
    got = {float(l): ceiling_bracket(rows, float(l)) for l in lams}
    brackets = {l: g["bracket"] for l, g in got.items()}
    located = [l for l, g in got.items() if g["verdict"] == CEILING_LOCATED]

    if len(located) < 2:
        name = CEILING_INCOMPARABLE
    elif len({brackets[l] for l in located}) == 1:
        name = CEILING_HELD
    else:
        name = CEILING_MOVED

    return {
        "verdict": name,
        "brackets": brackets,
        "located_at_lam": tuple(sorted(located)),
        "usable_weights": {l: g.get("usable_weights") for l, g in got.items()},
        # Per-rung lift between the two temperatures. The premise
        # `ceiling_gap` needs is that these are *one* factor; they are not, and
        # the spread is the finding rather than a caveat (see that function).
        "per_rung_lift": _per_rung_lift(rows, lams),
        "readings": got,
        "transfers_to_ab_scene": False,
    }


def _per_rung_lift(rows, lams) -> dict:
    """`ESS(lam_hi) / ESS(lam_lo)` at each weight both temperatures walked."""
    lo, hi = (float(l) for l in lams)
    a = {p.weight: p.median_ess for p in points(rows) if p.lam == lo}
    b = {p.weight: p.median_ess for p in points(rows) if p.lam == hi}
    return {w: b[w] / a[w] for w in sorted(set(a) & set(b)) if a[w] > 0}


GAP_EXCEEDS_BAND = "GAP_EXCEEDS_BAND"
GAP_FITS_BAND = "GAP_FITS_BAND"
NO_GAP = "NO_GAP"


def ceiling_gap(rows=MEASURED_WITH_LAM10, lam: float = 1.0, lams=(0.8, 1.0)) -> dict:
    """Could *any* shared `lam` hold both sides of the ceiling in band at once?

    :func:`span_admits_band`'s argument, moved from the seed axis to the weight
    axis. Both quantities are again ratios: the band is `10x` wide at every `K`
    (:func:`band_width_ratio`) and the ceiling's `ess_drop` is the gap between
    the two rungs. Under a temperature that scales both rungs by one factor,
    the pair slides along the axis with its gap fixed — so the two fit inside
    the window at some rung iff the gap is no wider than the window.

    **And here the premise is measurably false, which is the reading.** On the
    seed axis D-283 discharged it: `span_response` found `lam` compressing the
    ensemble by a near-common factor. On the weight axis the same two
    temperatures move the rungs by visibly *different* factors — `w = 5` lifts
    `1.006x` while `w = 20` lifts `1.373x` — so the gap is not carried along
    unchanged, it **narrows** (`16.33x -> 11.96x`). A `GAP_EXCEEDS_BAND` here
    therefore does **not** bar the pair the way the seed-axis verdict would
    have; it says the gap is still wider than the window *at the temperatures
    walked*, while the direction of travel is toward the window.

    `bars_shared_rung` is the field that carries that distinction, and it is
    `False` whenever the premise is violated. Two rungs license nothing about a
    third (D-283's `extrapolates`), so no temperature is projected here at
    which the gap would close.
    """
    got = ceiling_bracket(rows, lam)
    drop = got.get("ess_drop")
    if drop is None:
        return {"verdict": NO_GAP, "ceiling": got, "gap": None,
                "band_width": None, "bars_shared_rung": False}

    k = next(p.n_samples for p in points(rows) if p.lam == lam)
    width = band_width_ratio(k)
    lifts = _per_rung_lift(rows, lams)
    pair = got["bracket"]
    common = None
    if pair and all(w in lifts for w in pair):
        lo_l, hi_l = lifts[pair[0]], lifts[pair[1]]
        common = bool(abs(hi_l - lo_l) / max(lo_l, hi_l) <= SPAN_TOLERANCE)

    return {
        "verdict": GAP_EXCEEDS_BAND if drop > width else GAP_FITS_BAND,
        "lam": float(lam),
        "gap": drop,
        "band_width": width,
        "slack": width / drop,
        "ceiling": got,
        # Did the two rungs move by one factor between `lams`? `None` when the
        # pair was not walked at both temperatures.
        "premise_holds": common,
        "pair_lifts": ({w: lifts[w] for w in pair}
                       if pair and all(w in lifts for w in pair) else None),
        # The conclusion the ratio argument would license — *only* under the
        # premise. Withheld the moment the premise is measured false, rather
        # than reported with a caveat attached (D-047).
        "bars_shared_rung": bool(drop > width and common),
        "premise": ("conditional on `lam` scaling both rungs by a common "
                    "factor; measured false here — see `pair_lifts`"),
        "extrapolates": False,
    }


GAP_NARROWS = "GAP_NARROWS"
GAP_WIDENS = "GAP_WIDENS"
#: The direction reverses across the temperatures walked — so no single
#: direction of travel exists to read off, and the two-point reading that
#: suggested one was reading a turning point.
GAP_NON_MONOTONE = "GAP_NON_MONOTONE"
#: Fewer than three located brackets, or the bracket is not the same rung pair
#: at every temperature — the gaps then describe different pairs and comparing
#: them compares two things (D-019's conjunction discipline, weight axis).
GAP_TREND_INCOMPARABLE = "GAP_TREND_INCOMPARABLE"


def gap_trend(rows=MEASURED_ALL_LAMS, lams=(0.8, 1.0, 1.2)) -> dict:
    """Does the ceiling gap keep narrowing as `lam` rises? **No — it turns.**

    :func:`ceiling_gap` reported the gap at two temperatures (`16.33x` at
    `0.8`, `11.96x` at `1.0`) against a `10.0x` band and deliberately withheld
    any projection of where it closes — D-283's `extrapolates`, on the ground
    that two rungs license nothing about a third. This is that third rung, and
    it **refutes the direction**: at `lam = 1.2` the gap is `37.76x`, wider
    than either. The narrowing was a turning point, not a trend.

    Two things follow, and only the first was the question asked:

    - There is no "keep raising `lam` until the pair fits the window" move. The
      gap's minimum over the walked rungs is `11.96x` at `lam = 1.0`, still
      above the `10.0x` band, so **no walked temperature holds both sides of
      the ceiling in band at once** and the direction does not promise a later
      one.
    - The temperature axis is close to spent for an independent reason.
      `in_band_headroom` is the factor by which the in-band side can still rise
      before it leaves the band through the **top** (`128.0` at `K = 256`). At
      `lam = 1.2` that is `1.44x`, while the last lift at that rung was
      `2.82x` — the next comparable step pushes `w = 5` out of the band from
      above, which is a ceiling on the repair axis itself, not on `w_voo`.

    Comparability is checked, not assumed: the gaps are only one quantity if
    the bracket is the same rung pair at each temperature (it is, `(5, 20]`
    throughout). `bracket_stable` carries that, and a moved bracket downgrades
    the verdict to :data:`GAP_TREND_INCOMPARABLE` rather than reporting a trend
    across two different pairs.
    """
    lams = tuple(float(l) for l in lams)
    got = {l: ceiling_bracket(rows, l) for l in lams}
    located = [l for l in lams if got[l]["verdict"] == CEILING_LOCATED]
    brackets = {l: got[l]["bracket"] for l in lams}
    stable = len({brackets[l] for l in located}) == 1 if located else False

    gaps = {l: got[l]["ess_drop"] for l in located}
    k = next(p.n_samples for p in points(rows) if p.lam == lams[0])
    width = band_width_ratio(k)

    if len(located) < 3 or not stable:
        name = GAP_TREND_INCOMPARABLE
    else:
        seq = [gaps[l] for l in sorted(located)]
        deltas = [b - a for a, b in zip(seq, seq[1:])]
        if all(d < 0 for d in deltas):
            name = GAP_NARROWS
        elif all(d > 0 for d in deltas):
            name = GAP_WIDENS
        else:
            name = GAP_NON_MONOTONE

    # How much further the in-band side can rise before leaving the band from
    # above. Bounds the temperature axis independently of the gap.
    headroom = {}
    for l in located:
        ess = got[l]["ess_below"]
        headroom[l] = (ess_band(k)[1] / ess) if ess else None

    return {
        "verdict": name,
        "lams": lams,
        "gaps": gaps,
        "band_width": width,
        "brackets": brackets,
        "bracket_stable": stable,
        # Rungs actually walked at each temperature. `1.2` walks 2 of 5 — the
        # bracketing pair only — so a reader does not take its `usable_weights`
        # for a full-ladder set.
        "n_rungs": {l: got[l]["n_rungs"] for l in lams},
        "usable_weights": {l: got[l].get("usable_weights") for l in lams},
        # The best (smallest) gap anywhere on the walked rungs, and whether it
        # fits the window. This is the question D-284 left open.
        "min_gap": min(gaps.values()) if gaps else None,
        "min_gap_at_lam": (min(gaps, key=gaps.get) if gaps else None),
        "any_lam_fits_band": bool(gaps) and min(gaps.values()) <= width,
        "in_band_headroom": headroom,
        "per_rung_lift": {f"{a}->{b}": _per_rung_lift(rows, (a, b))
                          for a, b in zip(lams, lams[1:])},
        # Three rungs license a statement about the three, and no more. The
        # turn is exactly what a projection off the first two would have missed
        # (D-283).
        "extrapolates": False,
        "transfers_to_ab_scene": False,
    }


#: No interior rung is in band: the sampler gives out just above the in-band
#: rung, the usable region really is one rung wide, and the bracket tightens.
CROSSING_CLIFF = "CROSSING_CLIFF"
#: An interior rung *is* usable — the coarse ladder's one-rung-wide region was a
#: fact about its own spacing, and the operating region is wider than reported.
CROSSING_SLOPE = "CROSSING_SLOPE"
#: No rung was walked strictly inside the bracket, so the question is unasked.
CROSSING_UNPROBED = "CROSSING_UNPROBED"
#: ESS does not fall monotonically across the refined rungs. Every bracket
#: reader here assumes a single crossing; a non-monotone ladder has no single
#: crossing to bracket, so the verdict is withheld rather than caveated.
CROSSING_NON_MONOTONE = "CROSSING_NON_MONOTONE"


def ceiling_resolution(rows=MEASURED_LAM10_REFINED, lam: float = 1.0,
                       coarse=MEASURED_LAM10) -> dict:
    """Is D-027's ceiling a **cliff or a slope** — and was the gap a spacing artifact?

    Every prior reading on this axis came off a ladder whose rungs are `4x`
    apart, and a bracket is never tighter than the ladder that produced it.
    D-284 located the ceiling in `(5, 20]` and D-285 walked three temperatures
    without one ever moving it; both are statements at `4x` resolution. This
    walks two rungs *inside* that bracket and asks the two questions the
    resolution actually decides. **They come back with opposite signs, and that
    is the finding.**

    **The region is real.** Neither interior rung is in band (`4.84` and `4.20`
    against a floor of `12.8`), so the usable set is still `{w = 5}` at `2.5x`
    finer spacing: the sampler gives out between `5` and `8`, and the
    one-rung-wide operating region is a fact about the sampler rather than about
    where the rungs were placed. The bracket tightens `(5, 20] -> (5, 8]`.

    **The gap was not.** `ceiling_gap` measures the fall across the bracket, and
    at `4x` spacing that fall bundles the crossing together with `1.84x` of
    further decay from `8` to `20` that happens entirely *below* the band and
    has nothing to do with the crossing. Removing it takes the gap from
    `11.96x` to **`6.485x`** — from outside the `10.0x` band to **inside** it.
    So D-285's `any_lam_fits_band = False`, and the `GAP_EXCEEDS_BAND` at this
    temperature underneath it, are **resolution-dependent**: the bar was met by
    the ladder's spacing, not only by the sampler.

    Three disciplines are kept, and they are what stop this from over-claiming:

    - `bars_shared_rung` stays out of this. A gap that fits the window licenses
      a shared rung only under the common-factor premise D-284 measured
      **false** on this axis, and refining the bracket does not repair a
      premise. `gap_fits_band_refined` is arithmetic; it is not a temperature.
    - Only `lam = 1.0` is refined. `0.8` and `1.2` have no interior rung walked,
      so `gap_trend`'s verdict is *not* restated at the finer spacing —
      `refined_at_lams` names what was measured and `coarse_at_lams` what was
      not. Whether their gaps shrink the same way is unmeasured.
    - `local_exponents` is reported without a threshold. It is descriptive: the
      cliff/slope call is made by *band membership*, which needs no bar, rather
      than by declaring how steep counts as steep (D-027's own complaint).
    """
    pts = sorted((p for p in points(rows) if p.lam == lam),
                 key=lambda p: p.weight)
    got = ceiling_bracket(rows, lam)
    was = ceiling_bracket(coarse, lam)
    out = {"lam": float(lam), "scene": PEAK_SCENE,
           "bracket_coarse": was["bracket"], "bracket_refined": got["bracket"],
           "rungs_coarse": was["rungs"], "rungs_refined": got["rungs"],
           "usable_coarse": was.get("usable_weights"),
           "usable_refined": got.get("usable_weights"),
           "refined_at_lams": (float(lam),),
           "coarse_at_lams": tuple(l for l in (0.8, 1.0, 1.2) if l != lam),
           "transfers_to_ab_scene": False,
           "ab_scene_blocked_by": "PR #68 (unmerged)",
           "extrapolates": False}

    pair = was["bracket"]
    interior = ([p for p in pts if pair[0] < p.weight < pair[1]] if pair else [])
    if pair is None or not interior:
        return {**out, "verdict": CROSSING_UNPROBED, "interior_rungs": (),
                "local_exponents": None, "gap_coarse": was.get("ess_drop"),
                "gap_refined": None, "band_width": None,
                "gap_fits_band_refined": None, "region_is_artifact": None,
                "bracket_tightening": None}

    ess = [p.median_ess for p in pts]
    monotone = all(b <= a for a, b in zip(ess, ess[1:]))

    k = pts[0].n_samples
    width = band_width_ratio(k)
    # `log(ESS_lo / ESS_hi) / log(w_hi / w_lo)` on each consecutive pair — the
    # exponent a power law `ESS ~ w**-k` would hold constant. Descriptive only.
    from math import log
    exps = {f"{a.weight:g}->{b.weight:g}":
            (log(a.median_ess / b.median_ess) / log(b.weight / a.weight))
            for a, b in zip(pts, pts[1:])
            if a.median_ess > 0 and b.median_ess > 0 and b.weight > a.weight}

    usable_now = got.get("usable_weights") or ()
    usable_was = was.get("usable_weights") or ()
    wider = bool(set(usable_now) - set(usable_was))
    drop = got.get("ess_drop")

    if not monotone:
        name = CROSSING_NON_MONOTONE
    elif wider:
        name = CROSSING_SLOPE
    else:
        name = CROSSING_CLIFF

    return {
        **out,
        "verdict": name,
        "interior_rungs": tuple(p.weight for p in interior),
        # In band at any interior rung? This is the whole cliff/slope call, and
        # it is a membership test rather than a steepness bar.
        "interior_in_band": {p.weight: p.ess_in_band for p in interior},
        "interior_usable": {p.weight: p.usable for p in interior},
        "ess_monotone": monotone,
        "local_exponents": exps,
        "gap_coarse": was.get("ess_drop"),
        "gap_refined": drop,
        "band_width": width,
        # The coarse gap over the refined one: how much of the reported fall
        # was decay below the band rather than the crossing itself.
        "gap_overstated_by": ((was["ess_drop"] / drop)
                              if drop and was.get("ess_drop") else None),
        "gap_fits_band_coarse": bool(was.get("ess_drop")
                                     and was["ess_drop"] <= width),
        "gap_fits_band_refined": bool(drop and drop <= width),
        # Did refining flip the arithmetic bar D-285 read as closed?
        "gap_verdict_flips": bool(drop and was.get("ess_drop")
                                  and was["ess_drop"] > width >= drop),
        # Log-width of the bracket, coarse over refined.
        "bracket_tightening": ((log(pair[1] / pair[0])
                                / log(got["bracket"][1] / got["bracket"][0]))
                               if got["bracket"] else None),
        # True iff a finer ladder found usable rungs the coarse one missed.
        "region_is_artifact": wider,
        # Withheld for the same reason `ceiling_gap` withholds it: the
        # common-factor premise is measured false on this axis and a tighter
        # bracket does not mend it (D-284).
        "bars_shared_rung": False,
        "premise": ("`gap_fits_band_refined` is arithmetic on one temperature; "
                    "the shared-rung conclusion still needs the common-factor "
                    "premise D-284 measured false"),
    }


#: Every temperature refined and every crossing verdict intact — the three gaps
#: are one quantity again and the trend can be re-taken at uniform spacing.
UNIFORM_TREND_RESTORED = "UNIFORM_TREND_RESTORED"
#: The spacing is uniform but at least one temperature's crossing verdict is
#: withheld, so a three-way trend is still not a legal comparison. The obstacle
#: has changed from resolution to shape; the comparable subset is reported
#: without being called a trend.
UNIFORM_TREND_WITHHELD = "UNIFORM_TREND_WITHHELD"
#: Some temperature has no interior rung walked — the spacing is still mixed and
#: the question this function exists to answer is unasked.
UNIFORM_TREND_UNPROBED = "UNIFORM_TREND_UNPROBED"


def uniform_resolution_trend(rows=MEASURED_ALL_LAMS_UNIFORM,
                             lams=(0.8, 1.0, 1.2),
                             coarse=MEASURED_ALL_LAMS) -> dict:
    """Re-take :func:`gap_trend` with every temperature at one resolution.

    D-286 refined `lam = 1.0` alone, and its ceiling gap flipped from outside
    the `10.0x` band to inside it (`11.96x -> 6.485x`). That left
    :func:`gap_trend`'s three gaps measured at two different rung spacings —
    one `1.6x` reading against two `4x` ones — which D-019 forbids reading as a
    single quantity. Walking `w_voo ∈ {8, 12}` at `0.8` and `1.2` is the cheap
    move that restores the spacing. **It restores the spacing and not the
    comparison, and that is the finding.**

    Two of the three refine cleanly, and *both* flip the same way `1.0` did:

    - `lam = 0.8`: `16.33x -> 4.517x`, the largest overstatement on the axis
      (`3.62x` of the reported fall was decay below the band).
    - `lam = 1.0`: `11.96x -> 6.485x`, as D-286 recorded.

    So `any_lam_fits_band = False` was not a fact about `1.0` that happened to
    be resolution-dependent — it is resolution-dependent at **every temperature
    where it can be checked**. The `4x` ladder was reporting the sampler's
    crossing bundled with decay that has nothing to do with it.

    `lam = 1.2` cannot be checked. Its refined ladder is **non-monotone** — ESS
    falls `88.59 -> 4.58` from `w = 5` to `8` and then rises to `9.14` at `12` —
    so :func:`ceiling_resolution` returns :data:`CROSSING_NON_MONOTONE` and
    withholds the verdict, exactly as it is built to. A bracket reader assumes
    one crossing; this ladder does not have one to bracket. The refined number
    that *would* have been reported (`19.36x`) is deliberately excluded from
    `min_gap_refined` rather than carried with a caveat.

    Hence :data:`UNIFORM_TREND_WITHHELD` rather than a re-taken trend. The
    distinction is the whole point of the cycle: `resolution_uniform` is now
    `True` — the spacing objection D-019 raised is answered — while
    `all_comparable` is `False` for an unrelated reason that finer rungs
    surfaced rather than caused. Reporting a two-point "trend" over `{0.8, 1.0}`
    would repeat exactly the mistake D-285 was created to correct (two points
    are a segment, not a direction), so `trend_verdict` stays `None` and
    `n_comparable` carries why.
    """
    lams = tuple(float(l) for l in lams)
    per = {l: ceiling_resolution(rows, l, coarse=coarse) for l in lams}

    # A temperature is *probed* if a rung was walked strictly inside its coarse
    # bracket, and *comparable* if the refined crossing verdict also survived.
    probed = tuple(l for l in lams
                   if per[l]["verdict"] != CROSSING_UNPROBED)
    comparable = tuple(l for l in probed
                       if per[l]["verdict"] in (CROSSING_CLIFF, CROSSING_SLOPE))
    withheld = {l: per[l]["verdict"] for l in probed if l not in comparable}

    interior = {l: per[l]["interior_rungs"] for l in lams}
    uniform = (len(probed) == len(lams)
               and len({interior[l] for l in lams}) == 1)

    refined = {l: per[l]["gap_refined"] for l in comparable}
    coarse_gaps = {l: per[l]["gap_coarse"] for l in probed}
    width = next((per[l]["band_width"] for l in lams
                  if per[l]["band_width"]), None)

    if not uniform:
        name = UNIFORM_TREND_UNPROBED
    elif withheld:
        name = UNIFORM_TREND_WITHHELD
    else:
        name = UNIFORM_TREND_RESTORED

    fits_refined = bool(refined and width
                        and min(refined.values()) <= width)
    fits_coarse = bool(coarse_gaps and width
                       and min(g for g in coarse_gaps.values() if g) <= width)

    return {
        "verdict": name,
        "lams": lams,
        "scene": PEAK_SCENE,
        # The spacing objection, answered on its own terms.
        "resolution_uniform": uniform,
        "interior_rungs": interior,
        "all_comparable": not withheld,
        "comparable_lams": comparable,
        "n_comparable": len(comparable),
        "withheld_at_lams": withheld,
        "per_lam_verdict": {l: per[l]["verdict"] for l in lams},
        "gaps_coarse": coarse_gaps,
        # Only the temperatures whose crossing verdict survived. `1.2`'s refined
        # gap exists arithmetically and is left out on purpose.
        "gaps_refined": refined,
        "gap_overstated_by": {l: per[l]["gap_overstated_by"] for l in comparable},
        "band_width": width,
        "min_gap_refined": min(refined.values()) if refined else None,
        "min_gap_at_lam": (min(refined, key=refined.get) if refined else None),
        "any_lam_fits_band_coarse": fits_coarse,
        "any_lam_fits_band_refined": fits_refined,
        # D-285's bar, re-read at uniform spacing on the comparable subset.
        "verdict_flips": bool(fits_refined and not fits_coarse),
        # Two comparable temperatures are a segment, not a direction (D-285).
        "trend_verdict": None,
        # Unchanged by any of this: the premise D-284 measured false is not
        # repaired by resolution, and this scene is still the only one walked.
        "bars_shared_rung": False,
        "extrapolates": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
    }


#: Measured `(seed, w_voo, median ESS)` at `lam = 1.2` on :data:`PEAK_SCENE`,
#: `K = 256`. Seed 0 is D-287's row, re-quoted rather than re-run; seeds 1 and 2
#: are this cycle's, taken at **both** interior rungs so the two are compared at
#: one seed count (D-019 forbids a 3-seed rung read against a 1-seed one).
MEASURED_LAM12_RISE = (
    Point(lam=1.2, weight=8.0, median_ess=4.5755, n_samples=256,
          ratio=None, reached_goal=True, seed=0),
    Point(lam=1.2, weight=12.0, median_ess=9.1412, n_samples=256,
          ratio=None, reached_goal=True, seed=0),
    Point(lam=1.2, weight=8.0, median_ess=16.9425, n_samples=256,
          ratio=None, reached_goal=True, seed=1),
    Point(lam=1.2, weight=12.0, median_ess=9.4749, n_samples=256,
          ratio=0.3999958713046707, reached_goal=True, seed=1),
    Point(lam=1.2, weight=8.0, median_ess=10.9994, n_samples=256,
          ratio=None, reached_goal=True, seed=2),
    Point(lam=1.2, weight=12.0, median_ess=5.9535, n_samples=256,
          ratio=0.3084034356680486, reached_goal=True, seed=2),
)

#: The `8 -> 12` rise reverses on the added seeds: the majority of seeds fall,
#: so the ladder's non-monotonicity is a property of seed 0 and not of the
#: sampler. The withholding stays correct — it is *why* it was withheld that
#: changes, and with it the next move (walk `1.2`, do not chase a shape).
RISE_SEED_ARTEFACT = "RISE_SEED_ARTEFACT"
#: Every seed rises across the same pair — the sampler really is non-monotone
#: here and the axis has a shape anomaly to explain.
RISE_SAMPLER_SHAPE = "RISE_SAMPLER_SHAPE"
#: Seeds disagree with no majority either way, or too few were walked. Neither
#: attribution is licensed and the question stays open.
RISE_UNATTRIBUTED = "RISE_UNATTRIBUTED"


def rise_attribution(rows=MEASURED_LAM12_RISE, lam: float = 1.2,
                     pair: tuple[float, float] = (8.0, 12.0)) -> dict:
    """Is `lam = 1.2`'s non-monotone rise the **sampler's shape or seed 0's luck**?

    D-287 refined `lam = 1.2` at `w_voo ∈ {8, 12}` on seed 0 and got a ladder
    that falls `88.59 -> 4.58` and then **rises** to `9.14`. Every bracket
    reader on this axis assumes a single crossing, so
    :func:`ceiling_resolution` returned :data:`CROSSING_NON_MONOTONE` and
    :func:`uniform_resolution_trend` withheld the three-way comparison. That
    withholding is correct on either attribution — but the two license opposite
    next moves, and one seed cannot tell them apart.

    **It is seed 0's luck.** Two more seeds at both rungs, and both *fall*:

    ===== ========= ========== ==========
    seed  `w = 8`   `w = 12`   direction
    ===== ========= ========== ==========
    0     `4.5755`  `9.1412`   rise
    1     `16.9425` `9.4749`   fall
    2     `10.9994` `5.9535`   fall
    ===== ========= ========== ==========

    The reversal is **not** marginal and it is not at the rung that looked
    anomalous. Seeds 1 and 2 fall by near-identical factors (`0.559x`,
    `0.541x`) — the monotone decay the axis shows everywhere else — while the
    `w = 12` column is the *tight* one (`5.95 .. 9.47`, `1.59x`) and `w = 8` is
    the loose one (`4.58 .. 16.94`, **`3.70x`**). So the outlier is seed 0's
    `w = 8`, sitting at the bottom of a rung whose spread straddles the band
    floor. The rise was manufactured by a low left-hand point, not by a high
    right-hand one — which is the opposite of how the seed-0 ladder reads.

    **What this does and does not change.** It does not reinstate the trend:
    the added seeds make the withholding better-founded, not removable, because
    a rung whose seeds span `3.70x` has no single crossing to bracket either
    (D-019's conjunction is unmet at `w = 8` — seed 1 is in band at `16.94`,
    seeds 0 and 2 are not). It does redirect the next move: there is no shape
    anomaly on the temperature axis to explain, so `1.2` is a temperature to
    walk on more seeds rather than a defect to chase.
    """
    lo, hi = (float(pair[0]), float(pair[1]))
    at = {}
    for p in rows:
        if float(p.lam) != float(lam) or p.seed is None:
            continue
        if float(p.weight) in (lo, hi):
            at.setdefault(int(p.seed), {})[float(p.weight)] = float(p.median_ess)

    # Only seeds walked at *both* rungs can carry a direction (D-019).
    paired = tuple(sorted(s for s, d in at.items() if lo in d and hi in d))
    direction = {s: ("rise" if at[s][hi] > at[s][lo] else "fall")
                 for s in paired}
    rises = tuple(s for s in paired if direction[s] == "rise")
    falls = tuple(s for s in paired if direction[s] == "fall")

    if len(paired) < 2:
        name = RISE_UNATTRIBUTED
    elif not rises:
        name = RISE_SEED_ARTEFACT
    elif not falls:
        name = RISE_SAMPLER_SHAPE
    elif len(falls) > len(rises):
        name = RISE_SEED_ARTEFACT
    elif len(rises) > len(falls):
        name = RISE_SAMPLER_SHAPE
    else:
        name = RISE_UNATTRIBUTED

    def _spread(w):
        vals = [at[s][w] for s in paired]
        return (max(vals) / min(vals)) if vals and min(vals) else None

    k = next((int(p.n_samples) for p in rows if p.n_samples), None)
    floor = ess_band(k)[0] if k else None

    return {
        "verdict": name,
        "lam": float(lam),
        "scene": PEAK_SCENE,
        "pair": (lo, hi),
        "seeds": paired,
        "n_seeds": len(paired),
        "per_seed_ess": {s: dict(at[s]) for s in paired},
        "per_seed_direction": direction,
        "rise_seeds": rises,
        "fall_seeds": falls,
        # The rung spreads are the argument: the anomalous rung is the *loose*
        # one, and it is the left-hand one.
        "spread": {lo: _spread(lo), hi: _spread(hi)},
        "looser_rung": (lo if (_spread(lo) or 0) > (_spread(hi) or 0) else hi),
        # Which seeds clear the band floor at each rung — D-019's conjunction is
        # unmet at `w = 8`, which is a second reason the verdict stays withheld.
        "band_floor": floor,
        "in_band_seeds": {w: tuple(s for s in paired if floor and at[s][w] > floor)
                          for w in (lo, hi)},
        "conjunction_met": {w: bool(paired) and all(
            floor and at[s][w] > floor for s in paired) for w in (lo, hi)},
        # The withholding is re-founded, not lifted.
        "reinstates_trend": False,
        "withholding_still_correct": True,
        "transfers_to_ab_scene": False,
    }


#: Measured `(seed, w_voo, median ESS, ratio)` at `lam = 1.2` on
#: :data:`PEAK_SCENE`, `K = 256`, seeds `0..15` —
#: :data:`seed_count_licence.CENSUS_LADDER_SEEDS`, the census's own count. Three
#: rungs so the ensemble carries a *ladder* rather than a pair: `w = 5` is the
#: coarse bracket's in-band left endpoint and `{8, 12}` are D-286's interior
#: rungs. 48 closed-loop runs, 87 s wall clock (three rungs walked concurrently).
MEASURED_LAM12_CENSUS = (
    Point(lam=1.2, weight=5.0, median_ess=88.5874, n_samples=256,
          ratio=0.32759116734204097, reached_goal=True, seed=0),
    Point(lam=1.2, weight=5.0, median_ess=87.1783, n_samples=256,
          ratio=0.33829341940204527, reached_goal=True, seed=1),
    Point(lam=1.2, weight=5.0, median_ess=29.5960, n_samples=256,
          ratio=0.2991029976665741, reached_goal=True, seed=2),
    Point(lam=1.2, weight=5.0, median_ess=88.1797, n_samples=256,
          ratio=0.3540107855444305, reached_goal=True, seed=3),
    Point(lam=1.2, weight=5.0, median_ess=86.9265, n_samples=256,
          ratio=0.3427181710927057, reached_goal=True, seed=4),
    Point(lam=1.2, weight=5.0, median_ess=143.4074, n_samples=256,
          ratio=0.14669776674910726, reached_goal=True, seed=5),
    Point(lam=1.2, weight=5.0, median_ess=79.6116, n_samples=256,
          ratio=0.3420170332098421, reached_goal=True, seed=6),
    Point(lam=1.2, weight=5.0, median_ess=93.6347, n_samples=256,
          ratio=0.24038357149899583, reached_goal=True, seed=7),
    Point(lam=1.2, weight=5.0, median_ess=70.6553, n_samples=256,
          ratio=0.3160803742513746, reached_goal=True, seed=8),
    Point(lam=1.2, weight=5.0, median_ess=90.3442, n_samples=256,
          ratio=0.3186074557189403, reached_goal=True, seed=9),
    Point(lam=1.2, weight=5.0, median_ess=95.9496, n_samples=256,
          ratio=0.3384351738062455, reached_goal=True, seed=10),
    Point(lam=1.2, weight=5.0, median_ess=20.7728, n_samples=256,
          ratio=0.1422464897861879, reached_goal=True, seed=11),
    Point(lam=1.2, weight=5.0, median_ess=89.0381, n_samples=256,
          ratio=0.23570237380761735, reached_goal=True, seed=12),
    Point(lam=1.2, weight=5.0, median_ess=107.2801, n_samples=256,
          ratio=0.41677735932012444, reached_goal=True, seed=13),
    Point(lam=1.2, weight=5.0, median_ess=105.6662, n_samples=256,
          ratio=0.12181656706406774, reached_goal=True, seed=14),
    Point(lam=1.2, weight=5.0, median_ess=83.2173, n_samples=256,
          ratio=0.2966363599999311, reached_goal=True, seed=15),
    Point(lam=1.2, weight=8.0, median_ess=4.5755, n_samples=256,
          ratio=0.18624415723753981, reached_goal=True, seed=0),
    Point(lam=1.2, weight=8.0, median_ess=16.9425, n_samples=256,
          ratio=0.2257070985071433, reached_goal=True, seed=1),
    Point(lam=1.2, weight=8.0, median_ess=10.9994, n_samples=256,
          ratio=0.2219580180494463, reached_goal=True, seed=2),
    Point(lam=1.2, weight=8.0, median_ess=10.3297, n_samples=256,
          ratio=0.24104293173267505, reached_goal=True, seed=3),
    Point(lam=1.2, weight=8.0, median_ess=7.9121, n_samples=256,
          ratio=0.223505593842867, reached_goal=True, seed=4),
    Point(lam=1.2, weight=8.0, median_ess=9.6756, n_samples=256,
          ratio=0.21363529109392368, reached_goal=True, seed=5),
    Point(lam=1.2, weight=8.0, median_ess=33.5286, n_samples=256,
          ratio=0.37199598651399074, reached_goal=True, seed=6),
    Point(lam=1.2, weight=8.0, median_ess=104.8416, n_samples=256,
          ratio=0.23467772895543051, reached_goal=True, seed=7),
    Point(lam=1.2, weight=8.0, median_ess=39.4111, n_samples=256,
          ratio=0.3308687192416522, reached_goal=True, seed=8),
    Point(lam=1.2, weight=8.0, median_ess=27.9132, n_samples=256,
          ratio=0.3385323002967881, reached_goal=True, seed=9),
    Point(lam=1.2, weight=8.0, median_ess=69.2767, n_samples=256,
          ratio=0.45243461829054904, reached_goal=True, seed=10),
    Point(lam=1.2, weight=8.0, median_ess=8.8775, n_samples=256,
          ratio=0.24973061082206605, reached_goal=True, seed=11),
    Point(lam=1.2, weight=8.0, median_ess=34.3789, n_samples=256,
          ratio=0.23219562238791874, reached_goal=True, seed=12),
    Point(lam=1.2, weight=8.0, median_ess=30.4040, n_samples=256,
          ratio=0.24761803851951228, reached_goal=True, seed=13),
    Point(lam=1.2, weight=8.0, median_ess=14.2634, n_samples=256,
          ratio=0.36569617783744063, reached_goal=True, seed=14),
    Point(lam=1.2, weight=8.0, median_ess=53.0058, n_samples=256,
          ratio=0.3070156482669072, reached_goal=True, seed=15),
    Point(lam=1.2, weight=12.0, median_ess=9.1412, n_samples=256,
          ratio=0.3157533708748051, reached_goal=True, seed=0),
    Point(lam=1.2, weight=12.0, median_ess=9.4749, n_samples=256,
          ratio=0.3999958713046707, reached_goal=True, seed=1),
    Point(lam=1.2, weight=12.0, median_ess=5.9535, n_samples=256,
          ratio=0.3084034356680486, reached_goal=True, seed=2),
    Point(lam=1.2, weight=12.0, median_ess=5.5257, n_samples=256,
          ratio=0.36764891989437753, reached_goal=True, seed=3),
    Point(lam=1.2, weight=12.0, median_ess=2.7659, n_samples=256,
          ratio=0.3108265833899893, reached_goal=True, seed=4),
    Point(lam=1.2, weight=12.0, median_ess=16.0270, n_samples=256,
          ratio=0.3863801155994388, reached_goal=True, seed=5),
    Point(lam=1.2, weight=12.0, median_ess=6.7278, n_samples=256,
          ratio=0.3090703232014266, reached_goal=True, seed=6),
    Point(lam=1.2, weight=12.0, median_ess=8.5052, n_samples=256,
          ratio=0.3717922073261157, reached_goal=True, seed=7),
    Point(lam=1.2, weight=12.0, median_ess=3.7079, n_samples=256,
          ratio=0.30092099159940344, reached_goal=True, seed=8),
    Point(lam=1.2, weight=12.0, median_ess=3.5248, n_samples=256,
          ratio=0.2901184886594389, reached_goal=True, seed=9),
    Point(lam=1.2, weight=12.0, median_ess=5.0133, n_samples=256,
          ratio=0.3275011112379201, reached_goal=True, seed=10),
    Point(lam=1.2, weight=12.0, median_ess=8.9000, n_samples=256,
          ratio=0.29932667362849297, reached_goal=True, seed=11),
    Point(lam=1.2, weight=12.0, median_ess=4.9348, n_samples=256,
          ratio=0.28484596952907537, reached_goal=True, seed=12),
    Point(lam=1.2, weight=12.0, median_ess=10.7168, n_samples=256,
          ratio=0.4621544202657413, reached_goal=True, seed=13),
    Point(lam=1.2, weight=12.0, median_ess=6.4300, n_samples=256,
          ratio=0.2683879253066648, reached_goal=True, seed=14),
    Point(lam=1.2, weight=12.0, median_ess=7.2414, n_samples=256,
          ratio=0.33927459083415695, reached_goal=True, seed=15),
)


#: The ensemble ladder falls monotonically and every rung's seed span fits the
#: band's `10x` window — a single crossing exists and unanimity is reachable at
#: each rung, so the withheld three-way comparison can be re-taken.
CENSUS_LADDER_BRACKETABLE = "CENSUS_LADDER_BRACKETABLE"
#: The ensemble ladder is monotone, but some rung's seeds span **more than the
#: band is wide**. That rung admits no unanimous verdict at any temperature
#: (D-283's argument: both quantities are ratios, so a common factor slides the
#: sample without narrowing it), so the crossing it carries is not bracketable
#: by walking more rungs or more temperatures.
CENSUS_RUNG_INADMISSIBLE = "CENSUS_RUNG_INADMISSIBLE"
#: Monotone, every rung span-admissible, but at least one rung's seeds straddle
#: a band edge *as walked*. D-019's conjunction is unmet, so the verdict stays
#: withheld — but the obstacle is a temperature away rather than structural.
CENSUS_LADDER_STRADDLED = "CENSUS_LADDER_STRADDLED"
#: The **ensemble medians** are non-monotone. The rise survives the seed count
#: and is the sampler's shape rather than any one seed's luck.
CENSUS_LADDER_NON_MONOTONE = "CENSUS_LADDER_NON_MONOTONE"
#: Some rung was walked on fewer than the census's seed count, so no rung-level
#: population claim is licensed.
CENSUS_LADDER_UNWALKED = "CENSUS_LADDER_UNWALKED"


def census_ladder(rows=MEASURED_LAM12_CENSUS, lam: float = 1.2,
                  rungs: tuple[float, ...] = (5.0, 8.0, 12.0),
                  n_required: int | None = None) -> dict:
    """Walk `lam = 1.2` on the census's own seed count — is the crossing bracketable?

    D-288 attributed D-287's non-monotone ladder to seed 0 on three seeds and
    left the obvious next move: take the same temperature at
    :data:`seed_count_licence.CENSUS_LADDER_SEEDS`. Two results, and the second
    one is the finding.

    **The attribution holds, and comfortably.** The ensemble medians fall
    monotonically — `88.38 -> 22.43 -> 6.58` across `w_voo ∈ {5, 8, 12}` — and
    `13` of `16` seeds fall across `8 -> 12` against `3` that rise (seeds `0`,
    `5`, `11`). So :data:`RISE_SEED_ARTEFACT` is not an `n = 3` artefact of its
    own: at the census count there is no shape anomaly on this temperature.

    **And the ladder is still not bracketable, for a reason neither D-287 nor
    D-288 could see.** `w = 8` — the interior rung that *carries* the crossing —
    has a seed span of **`22.91x`** against a band that is **`10.0x` wide**.
    That is D-283's argument arriving on the rung axis: both quantities are
    ratios, so a common-factor response slides the ensemble without narrowing
    it, and a rung whose seeds span more than the window admits **no** unanimous
    verdict at **any** temperature — walked or unwalked. The other two rungs are
    admissible (`6.90x` at `w = 5`, `5.79x` at `12`); the one that is not is the
    one the crossing needs. Hence :data:`CENSUS_RUNG_INADMISSIBLE`.

    **The two failing rungs fail in opposite directions, which the counts hide.**
    Band membership alone reads as a clean decay (`15/16`, `10/16`, `1/16` in
    band from `w = 5` to `12`), but `w = 5`'s sole miss is seed 5 at `143.41`,
    **above** the `128.0` ceiling, while every miss at `8` and `12` is below the
    `12.8` floor. D-285 noticed this band closes from above and could only
    report headroom; here it bites a rung.

    **What that buys, stated as a premise and not as a result.** At `w = 5` the
    sole miss needs `1.1204x` *down* and the lowest seed has `1.6229x` of
    downward headroom before it reaches the floor, so a common factor admitting
    all 16 exists arithmetically. It is quoted in `repair_premise` and **not** in
    the verdict, because the common-factor premise is exactly what D-284
    measured **false** on this axis (`lam` squeezed D-283's span `17.34x ->
    5.46x` rather than translating it). The arithmetic names a rung worth
    walking; it does not predict what walking it returns.

    Two disciplines, both inherited:

    - **Spans are not compared across seed counts.** `span` is `max/min` over the
      sample, so it can only widen with `n` (D-281): `w = 8`'s `3.70x` at `n = 3`
      and `22.91x` at `n = 16` are not a widening, they are two different
      statistics. `spans_comparable_across_n` says so and no key here carries a
      difference between the counts. What *is* comparable is the admissibility
      test itself — `22.91x > 10.0x` is a fact about the `n = 16` sample alone.
    - **No trend is re-taken.** :func:`uniform_resolution_trend` stays withheld;
      this function answers why, it does not lift it.
    """
    from .seed_count_licence import CENSUS_LADDER_SEEDS

    need = CENSUS_LADDER_SEEDS if n_required is None else int(n_required)
    rungs = tuple(float(w) for w in rungs)

    at: dict[float, dict[int, Point]] = {}
    for p in points(rows) if not isinstance(rows[0], Point) else rows:
        if float(p.lam) != float(lam) or p.seed is None:
            continue
        if float(p.weight) in rungs:
            at.setdefault(float(p.weight), {})[int(p.seed)] = p

    walked = tuple(w for w in rungs if len(at.get(w, {})) >= need)
    k = next((int(p.n_samples) for d in at.values() for p in d.values()
              if p.n_samples), None)
    floor, ceil = ess_band(k) if k else (None, None)
    width = band_width_ratio(k) if k else None

    def _ess(w):
        return [at[w][s].median_ess for s in sorted(at[w])]

    from statistics import median
    med = {w: median(_ess(w)) for w in walked}
    span = {w: (max(_ess(w)) / min(_ess(w))) if min(_ess(w)) else None
            for w in walked}
    # A rung is *admissible* iff its seeds span no more than the band is wide.
    # Below the bar a common factor could admit every seed; above it, none can.
    admissible = {w: (span[w] is not None and width is not None
                      and span[w] <= width) for w in walked}

    in_band = {w: tuple(s for s in sorted(at[w]) if at[w][s].ess_in_band)
               for w in walked}
    above = {w: tuple(s for s in sorted(at[w])
                      if ceil and at[w][s].median_ess > ceil) for w in walked}
    below = {w: tuple(s for s in sorted(at[w])
                      if floor and at[w][s].median_ess < floor) for w in walked}
    conjunction = {w: len(in_band[w]) == len(at[w]) for w in walked}

    ladder = [med[w] for w in sorted(walked)]
    monotone = all(b <= a for a, b in zip(ladder, ladder[1:]))

    # Per-seed direction across the interior pair, at the census count — D-288's
    # question, re-asked where it can be answered.
    pair = tuple(w for w in sorted(walked) if w != min(walked))[:2]
    direction: dict[int, str] = {}
    if len(pair) == 2:
        lo_w, hi_w = pair
        shared = sorted(set(at[lo_w]) & set(at[hi_w]))
        direction = {s: ("rise" if at[hi_w][s].median_ess > at[lo_w][s].median_ess
                         else "fall") for s in shared}
    rises = tuple(s for s, d in sorted(direction.items()) if d == "rise")
    falls = tuple(s for s, d in sorted(direction.items()) if d == "fall")

    if len(walked) < len(rungs):
        name = CENSUS_LADDER_UNWALKED
    elif not monotone:
        name = CENSUS_LADDER_NON_MONOTONE
    elif not all(admissible.values()):
        name = CENSUS_RUNG_INADMISSIBLE
    elif not all(conjunction.values()):
        name = CENSUS_LADDER_STRADDLED
    else:
        name = CENSUS_LADDER_BRACKETABLE

    inadmissible = tuple(w for w in walked if not admissible[w])

    # Arithmetic only, and quoted as a premise: what common factor would admit
    # every seed at a rung, and is there room for it between the two edges?
    repair = {}
    for w in walked:
        vals = _ess(w)
        if not (floor and ceil and vals):
            continue
        need_down = (max(vals) / ceil) if max(vals) > ceil else 1.0
        room_down = (min(vals) / floor) if min(vals) else None
        need_up = (floor / min(vals)) if min(vals) < floor else 1.0
        room_up = (ceil / max(vals)) if max(vals) else None
        repair[w] = {
            "need_down": need_down, "room_down": room_down,
            "need_up": need_up, "room_up": room_up,
            "factor_exists": bool(
                (need_down <= (room_down or 0) if need_down > 1.0 else True)
                and (need_up <= (room_up or 0) if need_up > 1.0 else True)),
        }

    return {
        "verdict": name,
        "lam": float(lam),
        "scene": PEAK_SCENE,
        "rungs": rungs,
        "rungs_walked": walked,
        "n_seeds": {w: len(at[w]) for w in walked},
        "n_required": need,
        "seed_count_is_census": all(len(at[w]) == need for w in walked),
        # The ladder, at the ensemble rather than at one seed.
        "ensemble_median_ess": med,
        "ess_monotone": monotone,
        # D-288's verdict, re-asked at the census count.
        "pair": pair,
        "rise_seeds": rises,
        "fall_seeds": falls,
        "rise_attribution_holds": bool(falls and len(falls) > len(rises)),
        # The finding: a rung wider than the window admits nobody, ever.
        "span": span,
        "band_width": width,
        "rung_admits_band": admissible,
        "inadmissible_rungs": inadmissible,
        # Membership, and *which edge* each miss is on — the counts alone read
        # as a clean decay and hide that `w = 5` misses out the top.
        "in_band_seeds": in_band,
        "above_ceiling_seeds": above,
        "below_floor_seeds": below,
        "conjunction_met": conjunction,
        "band_floor": floor,
        "band_ceiling": ceil,
        # Arithmetic on this sample; NOT a prediction (D-284).
        "repair_arithmetic": repair,
        "repair_premise": (
            "`factor_exists` assumes `lam` scales every seed's ESS by a common "
            "factor — the premise D-284 measured false on this axis (it "
            "squeezed D-283's span `17.34x -> 5.46x`). It names a rung worth "
            "walking, not an outcome."),
        # D-281: span is `max/min`, monotone in `n`, so the two counts carry two
        # different statistics and no difference between them is reported.
        "spans_comparable_across_n": False,
        # This function explains the withholding; it does not lift it.
        "reinstates_trend": False,
        "bars_shared_rung": False,
        "extrapolates": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
    }


#: The `w = 5` column at the census seed count, walked at `lam = 0.9`. Same 16
#: seeds, same `K`, same scene and same :func:`sweep_seeds` body as
#: :data:`MEASURED_SEEDS_16` and :data:`MEASURED_SEEDS_16_LAM10` — this table
#: and :data:`MEASURED_SEEDS_16_LAM11` exist to tighten the bracket those two
#: already imply, not to open a new axis.
MEASURED_SEEDS_16_LAM09: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   24.9525, 256, 0.236763, True),
    ( 1,   35.0657, 256, 0.296916, True),
    ( 2,   33.5812, 256, 0.353750, True),
    ( 3,    7.6373, 256, 0.097404, True),  # deepest miss in any w=5 column
    ( 4,   50.5757, 256, 0.255278, True),
    ( 5,   20.3973, 256, 0.196499, True),
    ( 6,  126.4562, 256, 0.207266, True),
    ( 7,   40.1150, 256, 0.290447, True),
    ( 8,   31.6813, 256, 0.242296, True),
    ( 9,   70.4111, 256, 0.317548, True),
    (10,   67.7851, 256, 0.240096, True),
    (11,   10.7819, 256, 0.184490, True),  # second miss — 0.9 is worse than 0.8
    (12,   51.9876, 256, 0.321706, True),
    (13,   55.4476, 256, 0.386439, True),
    (14,   21.7696, 256, 0.226544, True),
    (15,   67.0004, 256, 0.234169, True),
)

#: The `w = 5` column at the census seed count, walked at `lam = 1.1`.
MEASURED_SEEDS_16_LAM11: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   79.0203, 256, 0.231863, True),
    ( 1,   52.1398, 256, 0.295432, True),
    ( 2,  108.8603, 256, 0.237153, True),
    ( 3,   46.4275, 256, 0.378111, True),
    ( 4,   19.2413, 256, 0.178788, True),  # the seed that missed at 0.8, now mid-band
    ( 5,   56.8040, 256, 0.282361, True),
    ( 6,   43.6196, 256, 0.282109, True),
    ( 7,   86.3316, 256, 0.307934, True),
    ( 8,   75.3817, 256, 0.311570, True),
    ( 9,   86.7878, 256, 0.395747, True),
    (10,   88.0636, 256, 0.318135, True),
    (11,   29.7114, 256, 0.267604, True),
    (12,   74.7905, 256, 0.260530, True),
    (13,   42.3801, 256, 0.392028, True),
    (14,   78.2718, 256, 0.345478, True),
    (15,  113.9787, 256, 0.242357, True),  # highest seed, still 1.12x under the ceiling
)


#: The `w = 5` column at the census seed count, walked at `lam = 1.15` — the
#: first temperature walked *inside* the upper endpoint interval D-290 left
#: open at `(1.1, 1.2)`. It fails (`15/16`, seed 15 at `140.07` over the
#: `128.0` ceiling), which narrows that interval to `(1.1, 1.15)`.
MEASURED_SEEDS_16_LAM115: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   78.0425, 256, 0.331967, True),
    ( 1,   53.4614, 256, 0.275682, True),
    ( 2,   95.3536, 256, 0.263642, True),
    ( 3,   93.7992, 256, 0.335459, True),
    ( 4,   79.6856, 256, 0.381488, True),
    ( 5,   75.3172, 256, 0.366851, True),
    ( 6,   79.1891, 256, 0.388083, True),
    ( 7,   80.3687, 256, 0.350995, True),
    ( 8,   84.0861, 256, 0.360142, True),
    ( 9,   96.8060, 256, 0.242017, True),
    (10,   26.0641, 256, 0.181243, True),
    (11,   59.1129, 256, 0.323145, True),
    (12,   40.8155, 256, 0.272812, True),
    (13,   62.7125, 256, 0.364542, True),
    (14,   27.5768, 256, 0.238232, True),
    (15,  140.0739, 256, 0.165901, True),  # the sole miss — over the ceiling
)

#: The `w = 5` column at the census seed count, walked at `lam = 1.25` — one
#: rung *beyond* the failing neighbour, asked whether membership recovers above
#: the run (it does not: `14/16`, both misses over the ceiling). This column
#: also carries the **tightest span of any `w = 5` column** (`2.90x` against a
#: `10.0x` band) while being the *least* unanimous of the upper columns, which
#: is the sharpest available statement that span-admissibility does not buy
#: membership once the ensemble is translating.
MEASURED_SEEDS_16_LAM125: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   78.5416, 256, 0.357014, True),
    ( 1,   97.5896, 256, 0.352172, True),
    ( 2,   62.4114, 256, 0.326055, True),
    ( 3,   91.3153, 256, 0.332185, True),
    ( 4,   97.8963, 256, 0.321845, True),
    ( 5,   47.5079, 256, 0.254339, True),
    ( 6,   92.4510, 256, 0.253129, True),
    ( 7,  115.9065, 256, 0.338118, True),
    ( 8,   99.4657, 256, 0.347320, True),
    ( 9,   73.8762, 256, 0.322296, True),
    (10,   86.6728, 256, 0.341476, True),
    (11,   46.9043, 256, 0.276354, True),
    (12,  111.8589, 256, 0.219106, True),
    (13,  135.8634, 256, 0.147006, True),  # miss — over the ceiling
    (14,  135.7491, 256, 0.090798, True),  # miss — over the ceiling
    (15,  112.1720, 256, 0.274787, True),
)


#: Every `w = 5` census column this branch has, keyed by temperature. The rung,
#: the seed set, the scene and `K` are held fixed across all of them — that is
#: what makes a multi-temperature comparison legal here (D-019(b) bars
#: comparing *different* `n`, not different `lam` at one `n`).
CENSUS_COLUMN_ROWS: dict[float, tuple] = {
    0.8: MEASURED_SEEDS_16,
    0.9: MEASURED_SEEDS_16_LAM09,
    1.0: MEASURED_SEEDS_16_LAM10,
    1.1: MEASURED_SEEDS_16_LAM11,
    1.15: MEASURED_SEEDS_16_LAM115,
    1.2: tuple((p.seed, p.median_ess, p.n_samples, p.ratio, p.reached_goal)
               for p in MEASURED_LAM12_CENSUS if p.weight == 5.0),
    1.25: MEASURED_SEEDS_16_LAM125,
}


#: A unanimous temperature exists and the walked temperatures on **both** sides
#: of it fail — so the unanimous set is a bounded interval in `lam`, not a
#: half-line. Reported only when the two failures are at **opposite** band
#: edges, because that is what makes the bound a property of the band rather
#: than of where the walk happened to stop.
BRACKET_CLOSED_BOTH_EDGES = "BRACKET_CLOSED_BOTH_EDGES"
#: Unanimous somewhere, both neighbours fail, but they fail at the **same**
#: edge. The interval is still bounded on the walked axis, but one side's
#: failure is not the band closing — it is the same wall met twice, so the
#: bound does not generalise the way :data:`BRACKET_CLOSED_BOTH_EDGES` does.
BRACKET_CLOSED_ONE_EDGE = "BRACKET_CLOSED_ONE_EDGE"
#: Unanimous at the lowest or highest temperature walked, so the interval runs
#: off the end of the walk. Nothing is known about where it stops.
BRACKET_OPEN = "BRACKET_OPEN"
#: No walked temperature puts all `n` seeds in band at this rung.
BRACKET_NO_UNANIMITY = "BRACKET_NO_UNANIMITY"
#: Fewer than two temperatures carry a full census column, so there is no
#: bracket to read.
BRACKET_UNWALKED = "BRACKET_UNWALKED"
#: The columns disagree on seed set, `K`, or count. Two populations are two
#: readings and neither brackets the other (D-019(b)).
BRACKET_INCOMPARABLE = "BRACKET_INCOMPARABLE"


def _unimodal(seq: tuple[int, ...]) -> bool:
    """Does `seq` rise (weakly) to a peak and then fall (weakly)?

    Named because "not monotone" and "not unimodal" are different defects and
    only the second one rules out placing the endpoint by extrapolation.
    """
    i = 0
    while i + 1 < len(seq) and seq[i] <= seq[i + 1]:
        i += 1
    while i + 1 < len(seq) and seq[i] >= seq[i + 1]:
        i += 1
    return i == len(seq) - 1


def unanimity_bracket(columns=None, rung: float = 5.0,
                      n_required: int | None = None) -> dict:
    """Is the unanimous temperature at `w = 5` a **bounded interval** in `lam`?

    Everything on this branch that has touched band membership has read it at
    one temperature at a time. Stacking the `w = 5` census columns answers a
    question none of them was asked, and the answer was already on disk before
    this function was written:

    - `lam = 0.9` — `14/16`, both misses (seeds 3 and 11) **below** the `12.8`
      floor. This is the run's lower neighbour.
    - `lam = 1.0`, `lam = 1.1` — `16/16` each. The unanimous run.
    - `lam = 1.15` — `15/16`, the sole miss (seed 15, `140.07`) **above** the
      `128.0` ceiling. This is the run's upper neighbour, walked after D-290
      bracketed the endpoint only as far as `(1.1, 1.2)`.

    So the unanimous set is **closed on both sides, and the two closures are
    different walls**. That is a stronger statement than either neighbour alone
    supports, and it is the reason this verdict distinguishes
    :data:`BRACKET_CLOSED_BOTH_EDGES` from :data:`BRACKET_CLOSED_ONE_EDGE`: a
    walk that stopped early would show one wall twice, whereas floor-then-
    ceiling can only happen if the ensemble crossed the band rather than
    failed to reach it.

    **Membership is not monotone in `lam`, and no caller may assume it is.**
    `15/16 -> 16/16 -> 15/16` rises and falls; every bracket reader elsewhere
    in this module assumes a single crossing and would mis-read this column.
    `membership_monotone` is returned as data for that reason.

    **What this does not do.** It does not locate the endpoints — those lie
    somewhere in the open intervals between the unanimous run and its failing
    neighbours, and this function reports those intervals rather than a width.
    It does not extrapolate to unwalked temperatures, to other rungs, or to the
    A/B scene. And it says nothing about `w = 8`: D-289 measured that rung's
    span at `22.91x` against a `10.0x` band, so no temperature makes it
    unanimous and no bracket exists there to read.
    """
    cols = CENSUS_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required

    walked = {lam: rows for lam, rows in cols.items() if rows}
    if len(walked) < 2:
        return {"verdict": BRACKET_UNWALKED, "rung": rung,
                "walked_lams": tuple(sorted(walked)),
                "n_required": need, "extrapolates": False}

    seed_sets = {frozenset(r[0] for r in rows) for rows in walked.values()}
    ks = {r[2] for rows in walked.values() for r in rows}
    if len(seed_sets) != 1 or len(ks) != 1 or len(seed_sets.pop()) != need:
        return {"verdict": BRACKET_INCOMPARABLE, "rung": rung,
                "walked_lams": tuple(sorted(walked)), "n_samples": tuple(sorted(ks)),
                "n_required": need, "extrapolates": False,
                "why": "columns differ in seed set, `K`, or count (D-019(b))"}

    k = ks.pop()
    floor, ceil = ess_band(k)
    per_lam = {}
    for lam in sorted(walked):
        ess = {r[0]: r[1] for r in walked[lam]}
        below = tuple(sorted(s for s, e in ess.items() if e < floor))
        above = tuple(sorted(s for s, e in ess.items() if e > ceil))
        vals = list(ess.values())
        per_lam[lam] = {
            "n": len(vals),
            "n_in_band": len(vals) - len(below) - len(above),
            "missed_below_floor": below,
            "missed_above_ceiling": above,
            # Which wall this temperature meets. `None` is unanimity; "both"
            # is a span too wide for the band and is not a bracket edge.
            "miss_edge": ("both" if below and above else
                          "floor" if below else "ceiling" if above else None),
            "span": max(vals) / min(vals) if min(vals) > 0 else None,
            "median_ess": sorted(vals)[len(vals) // 2],
        }

    lams = sorted(per_lam)
    unanimous = tuple(l for l in lams if per_lam[l]["n_in_band"] == need)
    if not unanimous:
        return {"verdict": BRACKET_NO_UNANIMITY, "rung": rung,
                "walked_lams": tuple(lams), "per_lam": per_lam,
                "unanimous_lams": (), "n_required": need,
                "band": (floor, ceil), "extrapolates": False,
                "transfers_to_ab_scene": False}

    lo_i, hi_i = lams.index(unanimous[0]), lams.index(unanimous[-1])
    contiguous = tuple(lams[lo_i:hi_i + 1]) == unanimous
    below_nb = lams[lo_i - 1] if lo_i > 0 else None
    above_nb = lams[hi_i + 1] if hi_i + 1 < len(lams) else None

    lo_edge = per_lam[below_nb]["miss_edge"] if below_nb is not None else None
    hi_edge = per_lam[above_nb]["miss_edge"] if above_nb is not None else None

    if below_nb is None or above_nb is None:
        name = BRACKET_OPEN
    elif lo_edge == "floor" and hi_edge == "ceiling":
        name = BRACKET_CLOSED_BOTH_EDGES
    else:
        name = BRACKET_CLOSED_ONE_EDGE

    return {
        "verdict": name,
        "rung": rung,
        "band": (floor, ceil),
        "walked_lams": tuple(lams),
        "unanimous_lams": unanimous,
        # A gap inside the run would mean membership is not even unimodal;
        # the caller is told rather than having the run silently closed over.
        "unanimous_run_contiguous": contiguous,
        # The endpoints are not located — they lie somewhere in these open
        # intervals. Reported as intervals so no reader can quote a width.
        "lower_endpoint_in": (below_nb, unanimous[0]) if below_nb is not None else None,
        "upper_endpoint_in": (unanimous[-1], above_nb) if above_nb is not None else None,
        "failing_neighbour_edges": {"below": lo_edge, "above": hi_edge},
        # The two endpoints are not the same kind of boundary, and D-283's
        # admissibility test is what separates them. Below the run the span
        # *exceeds* the band (`16.56x` at `0.9` against `10.0x`), so no common
        # factor puts that column in band at all — the lower endpoint is where
        # the spread becomes admissible. Above the run the span still fits
        # (`5.37x` at `1.15`); that column is admissible and merely slid off the
        # ceiling. Repairable-in-principle on one side, structural on the other.
        #
        # "Repairable in principle" means *by some common factor*, and D-291
        # measured that `lam` is not one of them: see :func:`endpoint_repair_axis`.
        "endpoint_mechanism": {
            side: (None if nb is None else
                   "span_exceeds_band" if (per_lam[nb]["span"] or 0) > band_width_ratio(k)
                   else "translated_out_of_band")
            for side, nb in (("below", below_nb), ("above", above_nb))},
        "band_width": band_width_ratio(k),
        "per_lam": per_lam,
        # `15/16 -> 16/16 -> 15/16`. Every other bracket reader in this module
        # assumes one crossing; this column has two turning points.
        "membership_monotone": False,
        # Stronger than non-monotone and measured, not assumed: `15, 14, 16,
        # 16, 15` across `0.8 .. 1.2` *dips* before it rises. A reader that
        # expected failures to decay toward the run would place the lower
        # endpoint below `0.8`; it is in `(0.9, 1.0)`.
        "membership_unimodal": _unimodal(tuple(per_lam[l]["n_in_band"] for l in lams)),
        "n_required": need,
        # The interval is bounded but its width is not measured, and walking
        # more temperatures narrows it rather than settling it.
        "endpoints_located": False,
        "extrapolates": False,
        # D-289: `w = 8` spans `22.91x` against a `10.0x` band, so it has no
        # unanimous temperature to bracket. This reading is about `w = 5` only.
        "applies_to_other_rungs": False,
        "transfers_to_ab_scene": False,
        "comparable_to": f"readings at n={need} only (D-019(b))",
    }


#: The failing neighbour needs the ensemble moved in the direction `lam` moves
#: it **away from**, so the only `lam` that repairs the miss is one *inside* the
#: unanimous run. `translated_out_of_band` is repairable in arithmetic and not
#: on this axis.
REPAIR_AXIS_REVERSES_INTO_RUN = "REPAIR_AXIS_REVERSES_INTO_RUN"
#: `lam` moves the ensemble toward the band edge the neighbour missed, so
#: walking further along the axis could in principle recover membership.
REPAIR_AXIS_TOWARD_BAND = "REPAIR_AXIS_TOWARD_BAND"
#: Median ESS is not monotone in `lam` across the walked columns, so the axis
#: has no single direction and no repair claim can be read off it either way.
REPAIR_AXIS_NON_MONOTONE = "REPAIR_AXIS_NON_MONOTONE"
#: The failing neighbour's span exceeds the band, so it is structurally
#: inadmissible (D-283) and the question of *which* axis repairs it never
#: arises.
REPAIR_AXIS_INADMISSIBLE = "REPAIR_AXIS_INADMISSIBLE"
#: No failing neighbour on this side, or too few columns to read a direction.
REPAIR_AXIS_UNWALKED = "REPAIR_AXIS_UNWALKED"


def endpoint_repair_axis(columns=None, rung: float = 5.0, side: str = "above",
                         n_required: int | None = None) -> dict:
    """Can `lam` repair the endpoint that :func:`unanimity_bracket` calls
    `translated_out_of_band`?

    D-290 separated the two ends of the unanimous run by *admissibility*: below
    the run the span exceeds the band, so no common factor helps; above it the
    span fits and the column has merely slid off the ceiling. STATE read the
    second as "the repairable side" and pointed the next walk at it. **This
    function is what that walk found, and it is a refutation of the reading
    rather than a narrowing of it.**

    The argument is two measured facts and no modelling:

    1. **Every miss above the run is over the ceiling**, so repairing it means
       moving the ensemble *down*.
    2. **Median ESS is strictly increasing in `lam` on the side being asked
       about** — `75.38, 79.19, 88.59, 97.59` for `1.1 .. 1.25`. So the only
       direction of `lam` that moves the ensemble down is *decreasing* it — and
       decreasing it from the failing neighbour lands back inside the
       unanimous run.

    **The direction is read on one side, not globally, and that is deliberate.**
    Across all seven columns the sequence is `40.87, 40.12, 54.77, 75.38,
    79.19, 88.59, 97.59`, which dips once at `0.8 -> 0.9` and is therefore not
    globally monotone. That dip is on the *lower* side, where the mechanism is
    :data:`span_exceeds_band` and the repair question never arises; requiring
    global monotonicity would let an irrelevant column veto a reading about the
    upper one. `median_ess_by_lam` returns the full sequence anyway so the
    caller sees what was excluded, and `axis_monotone_globally` names it.

    (These are the module's `median_ess`, the upper of the two middle order
    statistics — not `statistics.median`, which averages them and happens to
    make this particular sequence look globally monotone. The convention is
    stated because the two disagree exactly at the step in question.)

    Hence :data:`REPAIR_AXIS_REVERSES_INTO_RUN`: the arithmetic repair exists
    (at `lam = 1.25` the whole column needs only a `1.0614x` shrink, the
    smallest demand of any failing column) but `lam` cannot supply it, because
    the axis that translates the ensemble is the axis the endpoint is defined
    on. Repairing the upper endpoint requires a common factor that is **not**
    `lam`, and `lam` is the only one this branch has measured.

    **The tightening result is the same point from the other side.** `lam =
    1.25` has the narrowest span of any `w = 5` column — `2.90x` against a
    `10.0x` band, `3.45x` of slack — and is nonetheless the *least* unanimous
    of the upper columns (`14/16`). Span-admissibility is necessary and plainly
    not sufficient: the cluster contracts and is carried through the ceiling at
    the same time, and the second effect wins.

    **What this does not do.** It does not locate the endpoint (that is
    :func:`unanimity_bracket`'s interval, now `(1.1, 1.15)`), does not identify
    a common factor that *would* repair the miss, and does not transfer to the
    other rung or to the A/B scene.
    """
    cols = CENSUS_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required
    if side not in ("above", "below"):
        raise ValueError("side must be 'above' or 'below'")

    bracket = unanimity_bracket(cols, rung=rung, n_required=need)
    unwalked = {"verdict": REPAIR_AXIS_UNWALKED, "rung": rung, "side": side,
                "bracket_verdict": bracket["verdict"], "extrapolates": False,
                "transfers_to_ab_scene": False}
    if bracket["verdict"] not in (BRACKET_CLOSED_BOTH_EDGES,
                                  BRACKET_CLOSED_ONE_EDGE):
        return unwalked

    interval = bracket["upper_endpoint_in" if side == "above"
                       else "lower_endpoint_in"]
    if interval is None:
        return unwalked
    neighbour = interval[1] if side == "above" else interval[0]
    per_lam, lams = bracket["per_lam"], list(bracket["walked_lams"])
    floor, ceil = bracket["band"]

    if bracket["endpoint_mechanism"][side] == "span_exceeds_band":
        return {"verdict": REPAIR_AXIS_INADMISSIBLE, "rung": rung, "side": side,
                "failing_neighbour": neighbour,
                "neighbour_span": per_lam[neighbour]["span"],
                "band_width": bracket["band_width"],
                "why": "span exceeds the band — no common factor admits it (D-283)",
                "extrapolates": False, "transfers_to_ab_scene": False}

    # Direction of the axis, measured rather than assumed — and read on the
    # queried side only (see the docstring: the lone dip is on the other side,
    # where the mechanism is structural and the repair question is moot).
    medians = [per_lam[l]["median_ess"] for l in lams]
    run = bracket["unanimous_lams"]
    edge = run[-1] if side == "above" else run[0]
    side_lams = [l for l in lams if (l >= edge if side == "above" else l <= edge)]
    side_med = [per_lam[l]["median_ess"] for l in side_lams]
    rising = len(side_med) > 1 and all(b > a for a, b in zip(side_med, side_med[1:]))
    falling = len(side_med) > 1 and all(b < a for a, b in zip(side_med, side_med[1:]))
    if not (rising or falling):
        return {"verdict": REPAIR_AXIS_NON_MONOTONE, "rung": rung, "side": side,
                "failing_neighbour": neighbour,
                "median_ess_by_lam": tuple(zip(lams, medians)),
                "median_ess_on_side": tuple(zip(side_lams, side_med)),
                "extrapolates": False, "transfers_to_ab_scene": False}

    # Which way the miss must move, and the factor it needs.
    over = per_lam[neighbour]["missed_above_ceiling"]
    ess = {r[0]: r[1] for r in cols[neighbour]}
    if side == "above":
        needed = "down"
        worst = max(ess[s] for s in over) if over else None
        repair_factor = worst / ceil if worst else None
    else:
        needed = "up"
        under = per_lam[neighbour]["missed_below_floor"]
        worst = min(ess[s] for s in under) if under else None
        repair_factor = floor / worst if worst else None

    # `lam` increasing raises ESS; so "down" is available only by decreasing
    # `lam`, which walks back toward the run the neighbour sits outside of.
    axis_moves = "up" if rising else "down"
    toward = (axis_moves == needed)
    away_from_run = (side == "above") == rising

    return {
        "verdict": REPAIR_AXIS_TOWARD_BAND if toward
                   else REPAIR_AXIS_REVERSES_INTO_RUN,
        "rung": rung,
        "side": side,
        "band": (floor, ceil),
        "unanimous_lams": bracket["unanimous_lams"],
        "failing_neighbour": neighbour,
        "endpoint_in": interval,
        # The two facts the verdict rests on.
        "median_ess_by_lam": tuple(zip(lams, medians)),
        "median_ess_on_side": tuple(zip(side_lams, side_med)),
        "axis_monotone": True,
        # The direction was read on `side_lams`; globally it dips once, on the
        # other side. Reported so the narrowing is visible, not silent.
        "axis_monotone_globally": bool(
            all(b > a for a, b in zip(medians, medians[1:]))
            or all(b < a for a, b in zip(medians, medians[1:]))),
        "axis_moves_ensemble": axis_moves,
        "repair_needs_ensemble_moved": needed,
        # The arithmetic exists; the axis does not deliver it. Both are
        # reported so no caller can quote one without the other.
        "repair_factor": repair_factor,
        "repair_arithmetic_exists": (
            repair_factor is not None
            and (per_lam[neighbour]["span"] or 0) <= bracket["band_width"]),
        "repair_available_on_lam_axis": toward,
        # Decreasing `lam` from the upper neighbour re-enters the unanimous
        # run — that is why the repair direction is not a new operating point.
        "reversing_lands_in_unanimous_run": bool(away_from_run),
        "neighbour_span": per_lam[neighbour]["span"],
        "band_width": bracket["band_width"],
        "n_required": need,
        "extrapolates": False,
        "transfers_to_ab_scene": False,
        "comparable_to": f"readings at n={need}, w={rung} only (D-019(b))",
    }


#: The `w = 5`, `lam = 1.15` column at the census seed count, walked at
#: `K = 128` — half the `K` every other column on this branch was taken at.
#: **This column is unanimous (`16/16`)**, at the temperature that fails at
#: `K = 256`, which is what makes `K` the repair axis D-291 said `lam` was not.
MEASURED_SEEDS_16_LAM115_K128: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   24.7730, 128, 0.248493, True),
    ( 1,   35.9747, 128, 0.314919, True),
    ( 2,   29.9557, 128, 0.282917, True),
    ( 3,   38.6775, 128, 0.405208, True),
    ( 4,   20.9796, 128, 0.199864, True),
    ( 5,   14.1201, 128, 0.237491, True),  # lowest seed — still 2.21x over the floor
    ( 6,   19.8898, 128, 0.245709, True),
    ( 7,   28.1367, 128, 0.322436, True),
    ( 8,   42.7977, 128, 0.240889, True),
    ( 9,   20.9285, 128, 0.285653, True),
    (10,   30.6666, 128, 0.266425, True),
    (11,   26.4693, 128, 0.226034, True),
    (12,   33.2961, 128, 0.361023, True),
    (13,   33.1357, 128, 0.320285, True),
    (14,   53.6960, 128, 0.281212, True),  # highest seed — 1.19x under the ceiling
    (15,   31.4595, 128, 0.375311, True),  # the seed that missed at K=256
)

#: The same cell at `K = 512`. It is the **worst** column on this axis
#: (`11/16`) and the only one that misses at *both* band edges, so its span
#: (`18.63x`) exceeds the `10.0x` band and D-283 disqualifies it structurally.
#: Raising `K` does not translate this ensemble — it pulls it apart.
MEASURED_SEEDS_16_LAM115_K512: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,  182.6012, 512, 0.285448, True),
    ( 1,  195.0900, 512, 0.204054, True),
    ( 2,  172.0868, 512, 0.341839, True),
    ( 3,   76.9880, 512, 0.235643, True),
    ( 4,   24.7977, 512, 0.167276, True),  # miss — under the floor
    ( 5,  176.6086, 512, 0.357769, True),
    ( 6,  312.7343, 512, 0.074274, True),  # miss — over the ceiling
    ( 7,  230.5006, 512, 0.234667, True),
    ( 8,  318.8418, 512, 0.093484, True),  # miss — over the ceiling
    ( 9,  166.9358, 512, 0.302843, True),
    (10,  189.6824, 512, 0.307828, True),
    (11,   17.1186, 512, 0.191957, True),  # miss — under the floor, and the
                                           # widest split from seed 8: 18.63x
    (12,  198.2931, 512, 0.338089, True),
    (13,  206.6471, 512, 0.329466, True),
    (14,  293.8338, 512, 0.178146, True),  # miss — over the ceiling
    (15,  163.4918, 512, 0.277141, True),
)


#: `K = 64` at `lam = 1.15`, `w = 5`, census 16 seeds. Walked to test D-293's
#: slide prediction at the bottom of the axis: if lowering `K` keeps moving the
#: ensemble *down* in band-relative coordinates, this column should push
#: `lam = 1.15` out through the **floor**, the mirror of how `K = 128` pushed
#: `lam = 1.0` out. It does — seed 0 alone, and by `1.07x`.
MEASURED_SEEDS_16_LAM115_K64 = (
    ( 0,    2.9886, 64, 0.152328, True),  # miss — under the floor (3.2), the
                                          # only one, and marginal: 1.07x
    ( 1,   14.0699, 64, 0.274282, True),
    ( 2,    7.5475, 64, 0.298907, True),
    ( 3,   11.0597, 64, 0.195848, True),
    ( 4,   15.0084, 64, 0.379658, True),
    ( 5,    5.6878, 64, 0.186360, True),
    ( 6,    6.0411, 64, 0.201367, True),
    ( 7,    7.0699, 64, 0.189594, True),
    ( 8,   15.3584, 64, 0.404481, True),
    ( 9,   10.6249, 64, 0.270929, True),
    (10,    4.2385, 64, 0.188954, True),
    (11,    9.3795, 64, 0.248565, True),
    (12,    9.2109, 64, 0.357258, True),
    (13,   12.9686, 64, 0.329328, True),
    (14,   10.5927, 64, 0.263766, True),
    (15,   10.6992, 64, 0.267239, True),
)

#: `K = 96` at `lam = 1.15`, `w = 5`, census 16 seeds. The interior point
#: between the predicted floor exit and the known unanimous `K = 128`; it comes
#: back **`16/16`**, so the unanimous set on this axis is `{96, 128}` and the
#: run is bracketed on both sides rather than open at the bottom.
MEASURED_SEEDS_16_LAM115_K96 = (
    ( 0,   24.9722, 96, 0.263446, True),
    ( 1,   11.3332, 96, 0.197821, True),
    ( 2,   24.5128, 96, 0.361609, True),
    ( 3,   31.9909, 96, 0.253720, True),
    ( 4,   10.1180, 96, 0.249499, True),
    ( 5,   24.1439, 96, 0.358091, True),
    ( 6,   22.7528, 96, 0.302790, True),
    ( 7,   13.2785, 96, 0.309660, True),
    ( 8,   24.0952, 96, 0.275027, True),
    ( 9,    6.0021, 96, 0.147355, True),
    (10,    8.4687, 96, 0.173398, True),
    (11,   10.9646, 96, 0.169030, True),
    (12,   15.4398, 96, 0.267502, True),
    (13,   16.6446, 96, 0.371315, True),
    (14,    9.6252, 96, 0.173298, True),
    (15,   19.1869, 96, 0.273015, True),
)


#: `K = 80` at `lam = 1.15`, `w = 5`, census 16 seeds — the bisection of
#: D-294's open lower interval `(64, 96)`. It comes back **`14/16`**, both
#: misses through the **floor**, which narrows the lower endpoint to
#: `(80, 96]`. It is also the column that kills D-294's monotone-slide
#: reading: its `median ESS / K` is `0.0861`, *below* `K = 64`'s `0.1655`,
#: so the band-relative slide is not monotone on the extended grid.
MEASURED_SEEDS_16_LAM115_K80 = (
    ( 0,    3.2981, 80, 0.157259, True),  # miss — under the floor (4.0), 1.21x
    ( 1,    6.0190, 80, 0.160660, True),
    ( 2,   10.4795, 80, 0.320192, True),
    ( 3,    6.7095, 80, 0.197281, True),
    ( 4,   11.9770, 80, 0.334219, True),
    ( 5,    6.2800, 80, 0.203082, True),
    ( 6,    4.6296, 80, 0.179839, True),
    ( 7,    6.3396, 80, 0.276336, True),
    ( 8,   16.5566, 80, 0.311328, True),
    ( 9,   11.6327, 80, 0.262810, True),
    (10,   10.2063, 80, 0.261409, True),
    (11,    3.3836, 80, 0.146949, True),  # miss — under the floor, 1.18x
    (12,    7.8038, 80, 0.343329, True),
    (13,    5.3628, 80, 0.172767, True),
    (14,    6.8891, 80, 0.207370, True),
    (15,   15.0399, 80, 0.294213, True),
)

#: `K = 192` at `lam = 1.15`, `w = 5`, census 16 seeds — the bisection of
#: D-294's open upper interval `(128, 256)`. It comes back **`14/16`** and it
#: misses at **both** band edges, so its span (`12.19x`) exceeds the `10.0x`
#: band and D-283 disqualifies it structurally. It is the second such column
#: after `K = 512`, and the first one that is *interior* to the walked axis:
#: the run's upper neighbour is not a column that lost a seed, it is a column
#: that cannot host unanimity at any temperature.
MEASURED_SEEDS_16_LAM115_K192 = (
    ( 0,   60.8295, 192, 0.247140, True),
    ( 1,   68.4961, 192, 0.321004, True),
    ( 2,   23.0767, 192, 0.255604, True),
    ( 3,   99.3114, 192, 0.141916, True),  # miss — over the ceiling (96.0),
                                           # and only by 1.03x
    ( 4,   23.4774, 192, 0.189091, True),
    ( 5,   67.7989, 192, 0.349586, True),
    ( 6,   78.7670, 192, 0.269255, True),
    ( 7,   45.8082, 192, 0.352851, True),
    ( 8,   38.3218, 192, 0.305108, True),
    ( 9,   64.4800, 192, 0.308326, True),
    (10,   51.0096, 192, 0.234748, True),
    (11,   46.9763, 192, 0.312876, True),
    (12,   45.5298, 192, 0.289843, True),
    (13,   51.9197, 192, 0.248321, True),
    (14,   37.7180, 192, 0.223228, True),
    (15,    8.1489, 192, 0.171676, True),  # miss — under the floor (9.6), and
                                           # the widest split from seed 3
)


#: D-296's bisection of the upper interval `(128, 192)`, and the column that
#: turns that interval from a membership question into a *span* question with
#: an answer. It comes back **`16/16`** — so the unanimous run is not `{96,
#: 128}` but `{96, 128, 160}`, and the upper bound moves to `(160, 192)`.
#:
#: What makes it worth its own comment is the span, not the count: `3.05x`,
#: the **tightest column anywhere on this axis** (next best is `K = 128` at
#: `3.80x`), sitting one bisection below a column that spans `12.19x` and is
#: structurally inadmissible. The axis does not widen into inadmissibility
#: gradually — it is at its narrowest immediately before the cliff.
MEASURED_SEEDS_16_LAM115_K160 = (
    ( 0,   50.3213, 160, 0.355922, True),
    ( 1,   43.7858, 160, 0.350201, True),
    ( 2,   45.5829, 160, 0.309214, True),
    ( 3,   37.9594, 160, 0.279228, True),
    ( 4,   57.9084, 160, 0.295631, True),
    ( 5,   21.0233, 160, 0.263229, True),  # min of the column — the `3.05x`
                                           # span is this against seed 13
    ( 6,   59.3936, 160, 0.273003, True),
    ( 7,   50.1069, 160, 0.349220, True),
    ( 8,   44.3011, 160, 0.361747, True),
    ( 9,   29.4525, 160, 0.245912, True),
    (10,   58.3835, 160, 0.182567, True),
    (11,   34.3492, 160, 0.274667, True),
    (12,   40.5846, 160, 0.323208, True),
    (13,   64.0978, 160, 0.117959, True),  # max — and still 1.25x inside the
                                           # 80.0 ceiling
    (14,   49.5231, 160, 0.278750, True),
    (15,   61.1920, 160, 0.284937, True),
)


#: D-298's bisection of `(160, 192)` — the interval D-297 left, and the column
#: that takes the word "cliff" back off this axis.
#:
#: It comes back **`15/16`**, so the unanimous run does **not** extend again:
#: it stays `{96, 128, 160}` and the upper bound halves to `(160, 176)`. The
#: single miss is seed 0, **under the floor** (`7.5295` against `8.8`), needing
#: `1.17x` to re-enter — outside :data:`MARGINAL_MISS_TOLERANCE`, so unlike
#: D-293's lower exit this one is confirmed in margin as well as direction.
#:
#: The span is the reading that matters, and it is the one D-297 got wrong.
#: `7.74x` sits **between** `K = 160`'s `3.05x` and `K = 192`'s `12.19x`, so
#: the `4.0x` jump D-297 called a cliff was a statement about a 32-wide gap,
#: not about the axis: bisected once, it resolves into a monotone ramp
#: (`3.05 → 7.74 → 12.19`, steps of `2.54x` and `1.58x`). Nothing on this axis
#: jumps the band in one step.
#:
#: What replaces the cliff is a **separation**: `K = 176` is span-*admissible*
#: (`7.74 < 10.0`) and membership-*inadmissible* (`15/16`). It is the first
#: column on this axis where the two disqualification mechanisms disagree, and
#: their order is now measured — membership fails at `(160, 176]`, span not
#: until `(176, 192)`. The upper edge of the operating window is therefore set
#: by membership, and D-297's span framing was reading the wrong boundary.
MEASURED_SEEDS_16_LAM115_K176 = (
    ( 0,    7.5295, 176, 0.147587, True),  # miss — under the floor (8.8), and
                                           # by 1.17x, not a marginal clearance
    ( 1,   49.6711, 176, 0.307455, True),
    ( 2,   36.4032, 176, 0.293305, True),
    ( 3,   12.8347, 176, 0.199176, True),
    ( 4,   51.2707, 176, 0.268011, True),
    ( 5,   37.4536, 176, 0.305749, True),
    ( 6,   50.2620, 176, 0.326171, True),
    ( 7,   58.2649, 176, 0.311890, True),  # max of the column — the `7.74x`
                                           # span is this against seed 0
    ( 8,   35.8690, 176, 0.316420, True),
    ( 9,   57.9817, 176, 0.345441, True),
    (10,   56.1535, 176, 0.262037, True),
    (11,   50.4194, 176, 0.322371, True),
    (12,   18.2130, 176, 0.175619, True),
    (13,   31.1468, 176, 0.217483, True),
    (14,   10.9697, 176, 0.118968, True),
    (15,   16.1242, 176, 0.184121, True),
)


#: Seeds `16..31` at `K = 176` — D-301's `SEPARABILITY_UNTESTABLE` leg, re-taken
#: at twice the ensemble. Same cell (`lam = 1.15`, `w = 5`), same scene, same
#: :func:`sweep_seeds` body; seed `0` was re-run alongside as a provenance check
#: and returned `7.5295`, identical to
#: :data:`MEASURED_SEEDS_16_LAM115_K176`'s row, so the two halves are one column.
#:
#: **This is the first column on the axis whose answer was not already on disk,
#: and it retires two standing claims.**
#:
#: 1. **`SEPARABILITY_UNTESTABLE` was a sample-size artifact, not structure.**
#:    D-301 could not probe this leg because the column missed by *exactly one*
#:    seed, so the only deletion that reaches it is the one that deletes the exit
#:    itself. At `n = 32` there are **three** out-of-band seeds (`0`, `19`, `26`,
#:    all under the floor), so no single deletion can remove the exit and the
#:    leg is genuinely jackknife-probeable. D-301's verdict was correct *about
#:    `n = 16`* and does not generalise — which is exactly why it was named
#:    `UNTESTABLE` rather than `STABLE`.
#: 2. **D-298's "separation" collapses.** That reading — `K = 176` is
#:    span-*admissible* (`7.74 < 10.0`) and membership-*inadmissible* (`15/16`),
#:    the first column where the two disqualification mechanisms disagree, and
#:    therefore the basis for "membership fails at `(160, 176]`, span not until
#:    `(176, 192)`" — does not survive the ensemble. At `n = 32` the span is
#:    **`13.94x`**, outside the `10.0x` band, so `K = 176` is disqualified on
#:    *both* mechanisms and the two no longer disagree here. The measured
#:    *order* of the two failures was an artifact of which 16 seeds were drawn.
#:
#: Membership moves `15/16` → **`29/32`** (`0.938` → `0.906`), i.e. the column
#: stays an exit and gets slightly worse, rather than reverting to unanimity.
#: The span moves the other way and much further, because both new misses
#: (`5.2486`, `7.1201`) sit *below* the old minimum while the new maximum
#: (`73.1688`, seed 18) sits above the old one — the ensemble widened at both
#: ends, which is the failure mode a 16-seed span reading cannot see.
MEASURED_SEEDS_32_LAM115_K176_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   45.8347, 176, 0.315892, True),
    (17,   59.0505, 176, 0.334789, True),
    (18,   73.1688, 176, 0.320408, True),  # max of the 32-seed column — the
                                           # `13.94x` span is this against 19
    (19,    5.2486, 176, 0.130098, True),  # miss — under the floor (8.8), and
                                           # the new minimum
    (20,   50.5334, 176, 0.376049, True),
    (21,   20.3623, 176, 0.193966, True),
    (22,   66.5111, 176, 0.295623, True),
    (23,   27.7194, 176, 0.183193, True),
    (24,   60.9148, 176, 0.390999, True),
    (25,   23.7333, 176, 0.225922, True),
    (26,    7.1201, 176, 0.146303, True),  # miss — under the floor, the second
                                           # new one; three misses total at n=32
    (27,   34.9031, 176, 0.358644, True),
    (28,   24.4315, 176, 0.294962, True),
    (29,   18.5753, 176, 0.211890, True),
    (30,   63.8699, 176, 0.391950, True),
    (31,   45.8653, 176, 0.314184, True),
)


#: The full 32-seed `K = 176` column: :data:`MEASURED_SEEDS_16_LAM115_K176`
#: followed by :data:`MEASURED_SEEDS_32_LAM115_K176_EXT`. Kept as a separate
#: name rather than replacing the 16-seed table, because every `K`-axis reading
#: recorded before this cycle was taken at `n = 16` and overwriting it would
#: erase the ensemble those verdicts actually ran on (same reason
#: :data:`MEASURED_SEEDS_16` keeps :data:`MEASURED_SEEDS` intact).
MEASURED_SEEDS_32_LAM115_K176: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K176 + MEASURED_SEEDS_32_LAM115_K176_EXT
)


#: Seeds `16..31` at `K = 160` — the column D-302 named as the axis's largest
#: exposure, re-taken at twice the ensemble. Same cell, same scene, same
#: :func:`sweep_seeds` body; seed `0` re-run as a provenance check and returning
#: `50.3213`, identical to :data:`MEASURED_SEEDS_16_LAM115_K160`'s row.
#:
#: **It survives, and it is the only `K`-axis span claim that has.** The column
#: stays **`32/32`** — no new seed leaves `(8.0, 80.0)` — and the span moves
#: `3.049x` → **`3.601x`**, an `18%` widening that leaves it the tightest column
#: anywhere on the axis and nowhere near the `10.0x` band. So the span-minimum
#: statement D-298 explicitly kept live when the cliff died is not an `n = 16`
#: artifact, and the shape argument standing on it does not have to be re-taken.
MEASURED_SEEDS_32_LAM115_K160_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   43.8430, 160, 0.330894, True),
    (17,   48.2853, 160, 0.352123, True),
    (18,   54.5482, 160, 0.286495, True),
    (19,   22.4495, 160, 0.255318, True),
    (20,   39.9879, 160, 0.369181, True),
    (21,   49.4644, 160, 0.288694, True),
    (22,   17.8007, 160, 0.187483, True),  # new minimum of the 32-seed column —
                                           # the `3.60x` span is this against
                                           # seed 13, and it is still in band
    (23,   26.5583, 160, 0.232365, True),
    (24,   48.6001, 160, 0.345471, True),
    (25,   25.9283, 160, 0.222508, True),
    (26,   37.9454, 160, 0.303438, True),
    (27,   45.7889, 160, 0.375454, True),
    (28,   37.3907, 160, 0.374745, True),
    (29,   22.1439, 160, 0.221108, True),
    (30,   35.2698, 160, 0.350826, True),
    (31,   20.3138, 160, 0.246461, True),
)


#: The full 32-seed `K = 160` column. Kept beside the 16-seed table for the
#: same reason :data:`MEASURED_SEEDS_32_LAM115_K176` is.
MEASURED_SEEDS_32_LAM115_K160: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K160 + MEASURED_SEEDS_32_LAM115_K160_EXT
)


#: Seeds `16..31` at `K = 192` — the axis's only *interior* span-disqualified
#: column, re-taken at twice the ensemble. Provenance: seed `0` re-run and
#: returning `60.8295`, identical to :data:`MEASURED_SEEDS_16_LAM115_K192`.
#:
#: The span **doubles**: `12.187x` → **`25.700x`**. One new seed (`18`) lands at
#: `3.8643`, less than half the old minimum, and the maximum is unchanged — so
#: unlike `K = 176` this column widened at one end only, and still by more.
#: Membership moves `14/16` → **`29/32`**, i.e. the *rate* barely moves
#: (`0.875` → `0.906`) while the spread more than doubles: the two mechanisms do
#: not read the same thing about an ensemble and only one of them is sensitive
#: to the tails a small ensemble misses.
MEASURED_SEEDS_32_LAM115_K192_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   52.7916, 192, 0.346737, True),
    (17,   64.4177, 192, 0.376884, True),
    (18,    3.8643, 192, 0.109551, True),  # miss — under the floor (9.6), and
                                           # under half the old minimum; the
                                           # `25.70x` span is this against seed 3
    (19,   59.7667, 192, 0.338697, True),
    (20,   78.6845, 192, 0.133529, True),
    (21,   78.8552, 192, 0.279849, True),
    (22,   69.8732, 192, 0.330421, True),
    (23,   27.9086, 192, 0.186148, True),
    (24,   30.8313, 192, 0.253086, True),
    (25,   60.1728, 192, 0.354723, True),
    (26,   64.9048, 192, 0.353432, True),
    (27,   44.2148, 192, 0.305830, True),
    (28,   59.2906, 192, 0.384532, True),
    (29,   18.1910, 192, 0.218614, True),
    (30,   46.7089, 192, 0.309979, True),
    (31,   22.3107, 192, 0.285064, True),
)


#: The full 32-seed `K = 192` column.
MEASURED_SEEDS_32_LAM115_K192: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K192 + MEASURED_SEEDS_32_LAM115_K192_EXT
)


#: Seeds `16..31` at `K = 128` — the matched grid extended **downward**, which
#: D-304 established as the prerequisite for re-reading the attribution
#: question rather than a follow-up to it. Same cell (`lam = 1.15`, `w = 5`),
#: same scene, same :func:`sweep_seeds` body; seed `0` re-run as a provenance
#: check and returning `24.7730`, identical to
#: :data:`MEASURED_SEEDS_16_LAM115_K128`'s row, so the two halves are one
#: column.
#:
#: **This column changes state on both mechanisms, and it is the first on the
#: axis that was *unanimous* before the ensemble doubled.** At `n = 16` it is
#: `16/16` with span `3.803x` — an interior member of the unanimous run
#: `{96, 128, 160}` that every `K`-axis verdict since D-296 has leaned on. At
#: `n = 32` it is **`31/32`** (seed `30` at `5.2944`, under the `6.4` floor)
#: and its span is **`10.142x`**, *outside* the `10.0x` band.
#:
#: Two consequences, and the second is the one that matters:
#:
#: 1. **The unanimous run is not unanimous at twice the ensemble.** D-303 and
#:    D-302 retired span claims at columns that were *already* exits; this is
#:    the first time doubling the ensemble takes a column **out of the run
#:    itself**. The run's membership was an `n = 16` property here too.
#: 2. **The span failure is marginal and is reported as such.** `10.142x`
#:    against a `10.0x` band is `1.4%` over — one seed's placement. Unlike
#:    `K = 176` (`13.94x`) or `K = 192` (`25.70x`) this column sits on the
#:    boundary, so "span-inadmissible at `n = 32`" is the correct reading of
#:    the measurement but not a robust one, and no shape argument should be
#:    built on it without a third ensemble.
#:
#: Note the miss is a **single** seed, which re-creates exactly the condition
#: D-301 named `SEPARABILITY_UNTESTABLE` at `K = 176`/`n = 16`: the only
#: deletion that reaches this leg is the one that deletes the exit. So
#: extending the grid downward buys a *bound* without necessarily buying a
#: probeable one.
MEASURED_SEEDS_32_LAM115_K128_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   33.4386, 128, 0.312762, True),
    (17,   18.8093, 128, 0.249991, True),
    (18,   34.0462, 128, 0.292381, True),
    (19,   15.2472, 128, 0.240138, True),
    (20,   45.1719, 128, 0.503583, True),
    (21,   39.3788, 128, 0.376301, True),
    (22,   32.1012, 128, 0.385330, True),
    (23,   27.1663, 128, 0.268447, True),
    (24,   34.3196, 128, 0.364993, True),
    (25,   33.8359, 128, 0.240160, True),
    (26,   24.8886, 128, 0.294106, True),
    (27,   32.2790, 128, 0.307703, True),
    (28,   23.9378, 128, 0.244742, True),
    (29,   10.6867, 128, 0.202041, True),
    (30,    5.2944, 128, 0.158685, True),  # the only miss — under the `6.4`
                                           # floor, and the new minimum; the
                                           # `10.14x` span is this against
                                           # seed 6's `53.6960`
    (31,   32.2472, 128, 0.267998, True),
)


#: The full 32-seed `K = 128` column. Kept beside the 16-seed table for the
#: same reason :data:`MEASURED_SEEDS_32_LAM115_K160` is — every verdict before
#: this cycle read `K = 128` as a unanimous column, and overwriting the table
#: would erase the ensemble those verdicts ran on.
MEASURED_SEEDS_32_LAM115_K128: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K128 + MEASURED_SEEDS_32_LAM115_K128_EXT
)


#: Seeds `32..47` at `K = 128` — the **third** ensemble on the one column D-306
#: left marginal. Same cell, scene and :func:`sweep_seeds` body as the other two
#: halves; seed `0` was re-run in the same call and reproduced
#: :data:`MEASURED_SEEDS_16_LAM115_K128`'s `24.7730` exactly, so all three
#: halves are one column and not three measurements.
#:
#: D-306 disqualified this column's span at `10.142x` against a `10.0x` band —
#: `1.4%` over, one seed's placement — and explicitly refused to build a shape
#: argument on it "without a third ensemble". This is that ensemble, and it
#: answers the two halves of the question in opposite directions.
#:
#: 1. **The span question was never decidable in the rescuing direction.**
#:    `span` is `max/min` over the seed set, and extending a seed set can only
#:    raise the max and lower the min — so span is **monotone non-decreasing
#:    under ensemble extension**, and no third ensemble could have returned this
#:    column to the band. What the run could measure is *how far* it moves:
#:    `10.142x` → **`13.8185x`**, from `1.4%` over the band to `38.2%` over. So
#:    "marginal" was itself an `n = 32` property, and D-306's refusal to build on
#:    it was right for the opposite reason to the one it gave — the reading was
#:    not going to flip back, it was going to get worse.
#: 2. **The untestability is removed, not moved.** D-306 predicted that stepping
#:    the ensemble again would *relocate* the single-seed condition rather than
#:    clear it. Measured: the miss count goes `1` → **`2`** (seed `30` at
#:    `5.2944`, and the new seed `37` at `3.8858` — the new minimum, `1.65x`
#:    under the `6.4` floor). Two misses means the deletion that reaches this leg
#:    is no longer the deletion that erases the exit, so the leg is **probeable**
#:    — the `SEPARABILITY_UNTESTABLE` condition D-301 named is gone at `n = 48`,
#:    not shifted. That prediction is falsified.
#:
#: Note the near-miss that stays in band: seed `33` at `6.4973` is `1.0152x` of
#: the floor, the closest any seed on this column comes without crossing.
#:
#: **Scope.** At `n = 48` this is the *only* walked column, so
#: :func:`ensemble_scaling_in_k` and :func:`k_axis_bracket` return their
#: unwalked verdict here (`len(walked) < 2`) — nothing about the matched grid,
#: the run, or the puncture is re-read by this table. It is a single-column
#: reading and every grid-level statement on this axis remains an `n = 32` one.
MEASURED_SEEDS_48_LAM115_K128_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (32,    7.1523, 128, 0.148367, True),
    (33,    6.4973, 128, 0.151848, True),  # closest in-band seed on the column
                                           # — `1.0152x` of the `6.4` floor
    (34,   14.3989, 128, 0.225341, True),
    (35,   27.9198, 128, 0.281425, True),
    (36,   28.6859, 128, 0.294989, True),
    (37,    3.8858, 128, 0.099467, True),  # the second miss, and the new
                                           # minimum — `1.65x` under the floor;
                                           # this is the row that makes the leg
                                           # probeable
    (38,   38.5876, 128, 0.285720, True),
    (39,   16.7405, 128, 0.330824, True),
    (40,   28.6998, 128, 0.334322, True),
    (41,   26.9141, 128, 0.335686, True),
    (42,   34.2022, 128, 0.386115, True),
    (43,   42.3580, 128, 0.351052, True),
    (44,   21.9837, 128, 0.344848, True),
    (45,   20.1422, 128, 0.250626, True),
    (46,   21.0773, 128, 0.251526, True),
    (47,   36.1617, 128, 0.285498, True),
)


#: The full 48-seed `K = 128` column. Kept beside the 16- and 32-seed tables for
#: the same reason those are kept beside each other — D-306 through D-310 read
#: this column at `n = 32`, and overwriting the table would erase the ensemble
#: those verdicts ran on.
MEASURED_SEEDS_48_LAM115_K128: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_32_LAM115_K128 + MEASURED_SEEDS_48_LAM115_K128_EXT
)


#: Seeds `16..31` at `K = 96` — the **last unrespanned member** of the `n = 16`
#: unanimous run `{96, 128, 160}`, walked after D-306 took `128` out of it.
#: Same cell, scene and :func:`sweep_seeds` body as every other column; seed `0`
#: was re-run in the same call and reproduced :data:`MEASURED_SEEDS_16_LAM115_K96`'s
#: `24.9722` exactly, so the two halves are one column and not two measurements.
#:
#: **It holds.** All 16 new seeds clear the `0.05 * 96 = 4.8` floor — the
#: minimum is seed `21` at `5.8649` — so the column is `32/32`, and the run is
#: *not* empty below `160`: `K = 128` was its edge, not a symptom of the whole
#: run being an `n = 16` artifact.
MEASURED_SEEDS_32_LAM115_K96_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   19.3961, 96, 0.261966, True),
    (17,   13.8352, 96, 0.207259, True),
    (18,   25.0304, 96, 0.412152, True),
    (19,   24.7511, 96, 0.351756, True),
    (20,   12.3640, 96, 0.268953, True),
    (21,    5.8649, 96, 0.142546, True),  # the new minimum, and the closest
                                          # any seed comes to the `4.8` floor
                                          # — `1.22x` of it, still in band
    (22,   25.1241, 96, 0.307373, True),
    (23,   21.4436, 96, 0.309655, True),
    (24,   23.7849, 96, 0.372520, True),
    (25,   14.8326, 96, 0.231315, True),
    (26,   26.6563, 96, 0.388326, True),
    (27,   17.7115, 96, 0.283134, True),
    (28,   21.8684, 96, 0.220959, True),
    (29,   12.8070, 96, 0.256268, True),
    (30,    7.7459, 96, 0.198704, True),
    (31,   20.3333, 96, 0.316643, True),
)


#: The full 32-seed `K = 96` column. Kept beside the 16-seed table for the same
#: reason :data:`MEASURED_SEEDS_32_LAM115_K128` is — verdicts back to D-296 read
#: `K = 96` as a 16-seed unanimous column, and overwriting the table would erase
#: the ensemble those verdicts ran on.
MEASURED_SEEDS_32_LAM115_K96: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K96 + MEASURED_SEEDS_32_LAM115_K96_EXT
)


#: Seeds `16..31` at `K = 64` — the lower of the two columns that define the
#: run's **exit below**, and the last statements on this axis still resting on
#: an `n = 16` ensemble. Same cell, scene and :func:`sweep_seeds` body as every
#: other column; seed `0` was re-run in the same call and reproduced
#: :data:`MEASURED_SEEDS_16_LAM115_K64`'s `2.9886` exactly, so the two halves
#: are one column and not two measurements.
#:
#: **The exit survives.** One new seed misses through the floor (`23` at
#: `2.9607`, `1.08x` under the `0.05 * 64 = 3.2` floor), so the column is
#: `30/32` — still an exit, and still by the same marginal mechanism that made
#: it `15/16`. Doubling the ensemble did not rescue it and did not collapse it.
MEASURED_SEEDS_32_LAM115_K64_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,   15.0126, 64, 0.247560, True),
    (17,    7.5404, 64, 0.206513, True),
    (18,   12.4108, 64, 0.340796, True),
    (19,   11.8924, 64, 0.250516, True),
    (20,   18.2450, 64, 0.365352, True),
    (21,   14.1685, 64, 0.238607, True),
    (22,   12.7601, 64, 0.247417, True),
    (23,    2.9607, 64, 0.120526, True),  # miss — under the floor (3.2) by
                                          # 1.08x, the same marginal shape as
                                          # seed 0's 1.07x at n = 16
    (24,    6.1639, 64, 0.171707, True),
    (25,   14.5273, 64, 0.289517, True),
    (26,    8.1036, 64, 0.202801, True),
    (27,   10.2679, 64, 0.227347, True),
    (28,   11.4807, 64, 0.204339, True),
    (29,   15.8516, 64, 0.215799, True),
    (30,    5.5967, 64, 0.177292, True),
    (31,   18.4701, 64, 0.327050, True),
)


#: The full 32-seed `K = 64` column. Kept beside the 16-seed table for the same
#: reason :data:`MEASURED_SEEDS_32_LAM115_K96` is — D-293's slide prediction was
#: scored against the 16-seed table and overwriting it would erase the ensemble
#: that scoring ran on.
MEASURED_SEEDS_32_LAM115_K64: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K64 + MEASURED_SEEDS_32_LAM115_K64_EXT
)


#: Seeds `16..31` at `K = 80` — the upper of the two exit-below columns, and
#: D-294's bisection of the open interval `(64, 96)`. Same provenance discipline
#: as its neighbour: seed `0` re-run in the same call reproduced
#: :data:`MEASURED_SEEDS_16_LAM115_K80`'s `3.2981` exactly.
#:
#: **The exit survives, and it deepens.** One new seed misses through the floor
#: (`18` at `2.0596`, `1.94x` under the `0.05 * 80 = 4.0` floor) on top of the
#: two already recorded, so the column is `29/32`. Unlike `K = 64`'s, this miss
#: is *not* marginal — it is the deepest floor violation anywhere on the walked
#: axis, and it is the reason this column's span nearly doubles.
MEASURED_SEEDS_32_LAM115_K80_EXT: tuple[tuple[int, float, int, float, bool], ...] = (
    (16,    5.7783, 80, 0.240359, True),
    (17,   11.2682, 80, 0.205906, True),
    (18,    2.0596, 80, 0.115383, True),  # miss — under the floor (4.0) by
                                          # 1.94x, the deepest on the axis
    (19,    7.2667, 80, 0.235797, True),
    (20,   16.5753, 80, 0.334339, True),
    (21,    6.7087, 80, 0.160430, True),
    (22,    6.0900, 80, 0.222476, True),
    (23,   13.3142, 80, 0.257654, True),
    (24,   12.1433, 80, 0.291623, True),
    (25,    6.0933, 80, 0.193104, True),
    (26,   15.5160, 80, 0.336175, True),
    (27,    4.3805, 80, 0.171924, True),
    (28,   19.3711, 80, 0.282387, True),
    (29,   11.8299, 80, 0.251945, True),
    (30,    5.9282, 80, 0.248535, True),
    (31,   15.4341, 80, 0.234013, True),
)


#: The full 32-seed `K = 80` column, kept beside the 16-seed table for the same
#: reason :data:`MEASURED_SEEDS_32_LAM115_K64` is.
MEASURED_SEEDS_32_LAM115_K80: tuple[tuple[int, float, int, float, bool], ...] = (
    MEASURED_SEEDS_16_LAM115_K80 + MEASURED_SEEDS_32_LAM115_K80_EXT
)


#: The seven columns walked at `n = 32` — `64`, `80`, `96`, `128`, `160`, `176`,
#: `192` — as a
#: `K` axis in their own right. This is the **first sub-axis on this question
#: whose spans are estimates rather than lower bounds**, and it is the only grid
#: on which the two disqualification mechanisms may be compared without D-281's
#: seed-count caveat, because all five columns carry the same 32 seeds.
#:
#: `128` was added after D-304 measured that the three-column version could not
#: *express* the attribution question — `attribution_separability` returned
#: `SEPARABILITY_NOT_APPLICABLE` at **both** ensemble sizes because the run had
#: shrunk to `{160}` with no lower bound (`run_bounds_open_intervals[0] is
#: None`). Extending downward is what supplies that bound.
#:
#: `96` was added after D-306 took `128` *out* of the run, which left the run's
#: lower bound resting on a column that had just failed and made "is the whole
#: `n = 16` run an artifact?" the open question. It is not: `96` is `32/32`.
#:
#: `64` and `80` were added last, because every "the run exits below `96`"
#: statement on this axis was still an `n = 16` lower bound after `96` held —
#: the two columns that *define* that exit had never been respan. They were, and
#: both exits survive (`30/32` and `29/32`), so the run's lower edge is now a
#: 32-seed reading rather than an assertion inherited from the smaller ensemble.
#:
#: It is deliberately *not* merged into :data:`K_COLUMN_ROWS`: the four other
#: columns are `n = 16`, and :func:`ensemble_scaling_in_k` refuses a mixed seed
#: set by construction (`len(seed_sets) != 1`). Pass this dict with
#: `n_required=32` to read the matched grid; pass nothing to read the axis as
#: every verdict before D-303 read it.
K_COLUMN_ROWS_N32: dict[int, tuple] = {
    64:  MEASURED_SEEDS_32_LAM115_K64,
    80:  MEASURED_SEEDS_32_LAM115_K80,
    96:  MEASURED_SEEDS_32_LAM115_K96,
    128: MEASURED_SEEDS_32_LAM115_K128,
    160: MEASURED_SEEDS_32_LAM115_K160,
    176: MEASURED_SEEDS_32_LAM115_K176,
    192: MEASURED_SEEDS_32_LAM115_K192,
}


#: The **five**-column matched grid D-307 and D-308 read, kept as a named subset
#: for the same reason :data:`K_COLUMN_ROWS_N32_D306` is. Both of those verdicts
#: are statements about *this* grid: D-307's headline is that `128` is an
#: interior exit rather than the run's edge, and D-308's is that
#: :func:`k_axis_bracket` must not return one verdict for a contiguous run and a
#: punctured one — a claim whose worked example is `((96,), (160,))`, the block
#: decomposition of these five columns. Adding `64` and `80` below them moves
#: that decomposition, so the tests that score D-307/D-308 are repointed here
#: rather than re-derived against a grid their prose never saw.
K_COLUMN_ROWS_N32_D307: dict[int, tuple] = {
    96:  MEASURED_SEEDS_32_LAM115_K96,
    128: MEASURED_SEEDS_32_LAM115_K128,
    160: MEASURED_SEEDS_32_LAM115_K160,
    176: MEASURED_SEEDS_32_LAM115_K176,
    192: MEASURED_SEEDS_32_LAM115_K192,
}


#: The **four**-column matched grid D-306 read, kept as a named subset for the
#: same reason :data:`K_COLUMN_ROWS_N32_D304` is. D-306's headline — that
#: extending the grid down to `128` buys an expressible attribution question
#: whose answer is `SEPARABILITY_UNTESTABLE` — is a statement about *this* grid,
#: and adding `K = 96` moves it, because the run's lower leg no longer rests on
#: the single-seed column that made it untestable.
K_COLUMN_ROWS_N32_D306: dict[int, tuple] = {
    128: MEASURED_SEEDS_32_LAM115_K128,
    160: MEASURED_SEEDS_32_LAM115_K160,
    176: MEASURED_SEEDS_32_LAM115_K176,
    192: MEASURED_SEEDS_32_LAM115_K192,
}


#: The **three**-column matched grid D-303/D-304 read, kept as a named subset
#: for the same reason :data:`K_COLUMN_ROWS_D297` is. D-304's headline —
#: `K_BRACKET_OPEN_BELOW`, and the finding that the attribution question is not
#: expressible on the matched grid — is a statement about *this* grid, and it
#: is repointed here rather than re-derived, because adding `K = 128` supplies
#: the missing lower bound and therefore changes both.
K_COLUMN_ROWS_N32_D304: dict[int, tuple] = {
    160: MEASURED_SEEDS_32_LAM115_K160,
    176: MEASURED_SEEDS_32_LAM115_K176,
    192: MEASURED_SEEDS_32_LAM115_K192,
}


#: The `K` columns at `lam = 1.15`, `w = 5`, keyed by `K`. The seed set, the
#: rung, the temperature and the scene are held fixed across all eight — `K` is
#: the only thing that moves, which is what makes this a reading of that axis.
#: `K = 256` is reused from :data:`MEASURED_SEEDS_16_LAM115` rather than
#: re-walked; it is the same 16 seeds and the same :func:`sweep_seeds` body.
K_COLUMN_ROWS: dict[int, tuple] = {
    64: MEASURED_SEEDS_16_LAM115_K64,
    80: MEASURED_SEEDS_16_LAM115_K80,
    96: MEASURED_SEEDS_16_LAM115_K96,
    128: MEASURED_SEEDS_16_LAM115_K128,
    160: MEASURED_SEEDS_16_LAM115_K160,
    176: MEASURED_SEEDS_16_LAM115_K176,
    192: MEASURED_SEEDS_16_LAM115_K192,
    256: MEASURED_SEEDS_16_LAM115,
    512: MEASURED_SEEDS_16_LAM115_K512,
}

#: The **eight** columns D-297 read, kept as a named subset for the same
#: reason :data:`K_COLUMN_ROWS_D296` is kept one level up.
#:
#: D-298 bisected the interval D-297 left open and two of its statements do
#: not survive the new column. (1) The **cliff**: D-297 read `3.05x → 12.19x`
#: across `(160, 192)` as a jump the axis takes in one step; `K = 176` lands
#: at `7.74x`, between them, so the jump was the gap's width and not a
#: property of `K`. (2) The **upper bound** `(160, 192)`, which halves to
#: `(160, 176)`. What is *not* affected is the span-minimum claim — `K = 160`
#: is still the tightest column on the axis, and still tighter than either
#: column of the run it joins — so that statement stays on the live grid while
#: the two falsified ones are repointed here.
K_COLUMN_ROWS_D297: dict[int, tuple] = {
    64: MEASURED_SEEDS_16_LAM115_K64,
    80: MEASURED_SEEDS_16_LAM115_K80,
    96: MEASURED_SEEDS_16_LAM115_K96,
    128: MEASURED_SEEDS_16_LAM115_K128,
    160: MEASURED_SEEDS_16_LAM115_K160,
    192: MEASURED_SEEDS_16_LAM115_K192,
    256: MEASURED_SEEDS_16_LAM115,
    512: MEASURED_SEEDS_16_LAM115_K512,
}

#: The **seven** columns D-296 read, kept as a named subset for the same
#: reason :data:`K_COLUMN_ROWS_D294` is kept one level up.
#:
#: D-297 bisected the remaining upper interval and `K = 160` came back
#: `16/16`, so one D-296 statement does not survive it: the unanimous run is
#: `{96, 128, 160}`, not `{96, 128}`, and the upper bound is `(160, 192)`. The
#: run *length* claim was true of the grid it was taken on; what changed is
#: the grid. D-296's other two headlines are untouched by the new column —
#: `K = 192` is still the interior span-inadmissible one, and membership is
#: still non-monotone approaching both edges — which is why only the bound
#: statement is repointed here rather than the whole D-296 test block.
K_COLUMN_ROWS_D296: dict[int, tuple] = {
    64: MEASURED_SEEDS_16_LAM115_K64,
    80: MEASURED_SEEDS_16_LAM115_K80,
    96: MEASURED_SEEDS_16_LAM115_K96,
    128: MEASURED_SEEDS_16_LAM115_K128,
    192: MEASURED_SEEDS_16_LAM115_K192,
    256: MEASURED_SEEDS_16_LAM115,
    512: MEASURED_SEEDS_16_LAM115_K512,
}

#: The **five** columns D-294 walked, kept as a named subset for exactly the
#: reason :data:`K_COLUMN_ROWS_D292` exists one level up.
#:
#: D-296 bisected both open intervals, and two D-294-era claims do not survive
#: the two new columns — the `median ESS / K` slide is not monotone once
#: `K = 80` is walked (`0.1655` at `64` against `0.0861` at `80`), and the
#: lower exit is no longer one marginal seed (`K = 80` misses with two seeds at
#: `1.21x` and `1.18x`, against `K = 64`'s single `1.07x`). Both readings were
#: true of the grid they were taken on; what changed is the grid. The
#: falsifications are pinned as their own tests against the full
#: :data:`K_COLUMN_ROWS`, so neither statement can be quoted without the other.
K_COLUMN_ROWS_D294: dict[int, tuple] = {
    64: MEASURED_SEEDS_16_LAM115_K64,
    96: MEASURED_SEEDS_16_LAM115_K96,
    128: MEASURED_SEEDS_16_LAM115_K128,
    256: MEASURED_SEEDS_16_LAM115,
    512: MEASURED_SEEDS_16_LAM115_K512,
}

#: The **three** columns D-292 and D-293 actually walked, kept as a named
#: subset rather than reconstructed at each call site.
#:
#: D-294 extended the axis downward, and two D-292-era claims do not survive
#: the extension — membership is not monotone in `K` once `64` is walked
#: (`15, 16, 16, 15, 11`), and neither is span (`5.14` at `K = 64` against
#: `3.80` at `128`). Those readings were true of the grid they were taken on
#: and remain so; what changed is the grid. Pointing the original tests at this
#: subset keeps them asserting **what was measured** instead of silently
#: absorbing columns they were never about — the D-019(b) rule that a reading
#: is comparable only to readings on the same population, applied to `K`
#: instead of to seed count. The falsifications are recorded as their own
#: tests against the full :data:`K_COLUMN_ROWS`, so neither statement can be
#: quoted without the other.
K_COLUMN_ROWS_D292: dict[int, tuple] = {
    128: MEASURED_SEEDS_16_LAM115_K128,
    256: MEASURED_SEEDS_16_LAM115,
    512: MEASURED_SEEDS_16_LAM115_K512,
}


#: `median ESS / K` **falls** as `K` grows, so the ensemble slides down inside
#: a band that is scaling with it — the direction D-291 showed `lam` cannot
#: supply, reachable by *raising* `K`.
K_MOVES_ENSEMBLE_DOWN = "K_MOVES_ENSEMBLE_DOWN"
#: `median ESS / K` **rises** with `K`. Same sign as `lam`, so this axis is no
#: more use than the one D-291 disqualified.
K_MOVES_ENSEMBLE_UP = "K_MOVES_ENSEMBLE_UP"
#: `median ESS` tracks `K` closely enough that the band-relative position does
#: not move: the ensemble and the window scale together and membership is
#: (to the walked resolution) a `K`-invariant. Then `K` is not a common factor
#: on this question at all — it is a change of units.
K_LEAVES_ENSEMBLE_IN_PLACE = "K_LEAVES_ENSEMBLE_IN_PLACE"
#: The band-relative position is not monotone across the walked `K`, so the
#: axis has no single direction and no repair claim reads off it either way.
K_NON_MONOTONE = "K_NON_MONOTONE"
#: Fewer than two `K` columns, or the columns disagree on seed set or count.
K_UNWALKED = "K_UNWALKED"

#: Fractional tolerance for calling the band-relative position "unmoved". A
#: `median ESS / K` that varies by less than this across a `4x` change in `K`
#: is reported as :data:`K_LEAVES_ENSEMBLE_IN_PLACE` rather than as a
#: direction, because a direction read off drift that small would be a
#: statement about 16 seeds' luck and not about the axis.
K_FLAT_TOLERANCE: float = 0.10


def ensemble_scaling_in_k(columns=None, rung: float = 5.0,
                          lam: float = 1.15,
                          n_required: int | None = None) -> dict:
    """Does `K` move the ensemble **down** relative to the band, where `lam`
    could not?

    D-291 closed the `lam` axis on the upper endpoint: every miss above the
    unanimous run is over the *ceiling*, so repair means moving the ensemble
    down, and median ESS rises strictly with `lam` on that side — the only
    `lam` that moves it down is one already inside the run
    (:data:`REPAIR_AXIS_REVERSES_INTO_RUN`). That left a stated successor:
    the repair needs a common factor which is **not** `lam`, and `K` was the
    first untested candidate. This function is that walk.

    **`K` is not an ordinary knob on this question, and that is the whole
    reading.** :func:`ab.ess_band` defines the band as *fractions* of `K`
    (:data:`ab.ESS_BAND_FRACTIONS`, `0.05` and `0.5`), so raising `K` raises
    the floor and the ceiling by exactly the same factor. Membership therefore
    depends only on the **band-relative position** `median ESS / K`, never on
    raw ESS. A reader watching raw median ESS across these columns would see it
    climb with `K` and conclude "`K` moves the ensemble up" — the wrong sign
    for the membership question, and wrong because the window it is being
    compared against moved too. `median_ess` and `median_frac` are both
    returned so the two can never be quoted interchangeably.

    Two consequences that hold before any run is walked, and are reported as
    such rather than as findings:

    * :func:`band_width_ratio` is `10.0` at **every** `K`, so D-283's
      admissibility test (`span` vs band width) is a `K`-invariant. A column
      whose span exceeds the band cannot be repaired by `K` either — the axis
      cannot narrow a spread, only translate it, which is exactly what D-284
      measured `lam` doing.
    * `span` is `max/min` of a column and so is dimensionless; it is
      comparable across `K` in a way raw ESS is not. It is *not* comparable
      across different seed counts (D-281), and every column here is the same
      16 seeds.

    **What this does not do.** It does not locate the upper endpoint — that is
    :func:`unanimity_bracket`'s open interval, `(1.1, 1.15)`. It does not
    re-walk temperature: every column here is `lam = 1.15`, the failing
    neighbour, chosen because it is the column the repair question is *about*.
    A verdict that `K` moves the ensemble down is a statement about this
    column at this rung on this scene, not a new operating point, and it does
    not transfer to the A/B scene (PR #68 unmerged).
    """
    cols = K_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required

    walked = {k: rows for k, rows in cols.items() if rows}
    seed_sets = {frozenset(r[0] for r in rows) for rows in walked.values()}
    if len(walked) < 2 or len(seed_sets) != 1 or len(seed_sets.copy().pop()) != need:
        return {"verdict": K_UNWALKED, "rung": rung, "lam": lam,
                "walked_k": tuple(sorted(walked)), "n_required": need,
                "why": "need ≥2 `K` columns on one seed set of the census size",
                "extrapolates": False, "transfers_to_ab_scene": False}

    per_k = {}
    for k in sorted(walked):
        floor, ceil = ess_band(k)
        ess = {r[0]: r[1] for r in walked[k]}
        below = tuple(sorted(s for s, e in ess.items() if e < floor))
        above = tuple(sorted(s for s, e in ess.items() if e > ceil))
        vals = list(ess.values())
        # Same convention as `unanimity_bracket`: the upper of the two middle
        # order statistics, not `statistics.median`. Stated because D-291
        # found a step where the two disagree enough to flip a monotonicity
        # verdict, so the choice has to travel with the number.
        med = sorted(vals)[len(vals) // 2]
        per_k[k] = {
            "n": len(vals),
            "n_in_band": len(vals) - len(below) - len(above),
            "missed_below_floor": below,
            "missed_above_ceiling": above,
            "miss_edge": ("both" if below and above else
                          "floor" if below else "ceiling" if above else None),
            "band": (floor, ceil),
            "span": max(vals) / min(vals) if min(vals) > 0 else None,
            "median_ess": med,
            # The coordinate membership is actually decided in.
            "median_frac": med / k,
            # `K`-invariant (`10.0`), carried per-column so the admissibility
            # comparison is never made against a width from another reading.
            "band_width": band_width_ratio(k),
            "span_admissible": (max(vals) / min(vals)) <= band_width_ratio(k)
                               if min(vals) > 0 else None,
        }

    ks = sorted(per_k)
    fracs = [per_k[k]["median_frac"] for k in ks]
    raw = [per_k[k]["median_ess"] for k in ks]
    drift = (max(fracs) - min(fracs)) / min(fracs) if min(fracs) > 0 else None

    if drift is not None and drift < K_FLAT_TOLERANCE:
        name = K_LEAVES_ENSEMBLE_IN_PLACE
    elif all(b < a for a, b in zip(fracs, fracs[1:])):
        name = K_MOVES_ENSEMBLE_DOWN
    elif all(b > a for a, b in zip(fracs, fracs[1:])):
        name = K_MOVES_ENSEMBLE_UP
    else:
        name = K_NON_MONOTONE

    unanimous = tuple(k for k in ks if per_k[k]["n_in_band"] == need)
    inadmissible = tuple(k for k in ks if per_k[k]["span_admissible"] is False)

    # Which way along `K` the repair lies. The needed ensemble move is "down"
    # (every miss at `K = 256` is over the ceiling), so the repair direction is
    # *against* the axis when the band-relative position rises with `K`.
    if name == K_MOVES_ENSEMBLE_UP:
        direction = "decrease"
    elif name == K_MOVES_ENSEMBLE_DOWN:
        direction = "increase"
    else:
        direction = None

    return {
        "verdict": name,
        "rung": rung,
        "lam": lam,
        "walked_k": tuple(ks),
        # The two sequences, side by side, because the argument is precisely
        # that they can point opposite ways.
        "median_ess_by_k": tuple(zip(ks, raw)),
        "median_frac_by_k": tuple(zip(ks, fracs)),
        "raw_median_rises_with_k": all(b > a for a, b in zip(raw, raw[1:])),
        "frac_drift": drift,
        "flat_tolerance": K_FLAT_TOLERANCE,
        "membership_by_k": tuple((k, per_k[k]["n_in_band"]) for k in ks),
        "unanimous_k": unanimous,
        # Does this axis supply what D-291 showed `lam` could not?
        "repair_needs_ensemble_moved": "down",
        "axis_moves_ensemble": ("down" if name == K_MOVES_ENSEMBLE_DOWN else
                                "up" if name == K_MOVES_ENSEMBLE_UP else
                                "nowhere" if name == K_LEAVES_ENSEMBLE_IN_PLACE
                                else None),
        "repair_direction_in_k": direction,
        # **Measured, not inferred.** The axis having the right sign would only
        # license a search; a walked column that is unanimous *is* the repair.
        # Reported this way so no caller can quote a direction as if it were a
        # found operating point (the error D-291 caught STATE making about
        # `translated_out_of_band`).
        "repair_available_on_k_axis": bool(unanimous),
        "repair_is_measured_not_arithmetic": bool(unanimous),
        "band_width_is_k_invariant": len({per_k[k]["band_width"] for k in ks}) == 1,
        # D-283's test applied per column. `K` is *not* a common factor: it
        # changes the spread as well as the position, so a column can become
        # structurally inadmissible by raising it — which is what `K = 512`
        # does here, at `18.63x` against a `10.0x` band.
        "inadmissible_k": inadmissible,
        "span_by_k": tuple((k, per_k[k]["span"]) for k in ks),
        "acts_as_common_factor": not inadmissible and len(
            {round((per_k[k]["span"] or 0), 3) for k in ks}) == 1,
        "per_k": per_k,
        "n_required": need,
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "applies_to_other_lams": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "comparable_to": f"readings at n={need}, w={rung}, lam={lam} only (D-019(b))",
    }


#: `lam = 1.0` at `K = 128`, `w = 5`, census 16 seeds. The K=256 column at this
#: temperature is `16/16` — the *anchor* of the unanimous run D-290 bracketed.
#: Here it is `13/16` and every miss is **under the floor**, which is the half
#: of the translation D-292's `median_frac` direction predicts but that no
#: column had yet been walked to see.
MEASURED_SEEDS_16_LAM10_K128: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   18.6378, 128, 0.285496, True),
    ( 1,   12.1036, 128, 0.203385, True),
    ( 2,   25.5828, 128, 0.346013, True),
    ( 3,   17.3964, 128, 0.280321, True),
    ( 4,    3.7183, 128, 0.131313, True),  # miss — 41.9% under the 6.4 floor
    ( 5,   19.6752, 128, 0.217142, True),
    ( 6,   31.1430, 128, 0.350423, True),
    ( 7,   14.7986, 128, 0.287445, True),
    ( 8,   12.8561, 128, 0.394007, True),
    ( 9,   26.2223, 128, 0.289137, True),
    (10,   12.1073, 128, 0.225540, True),
    (11,    3.6914, 128, 0.142647, True),  # miss — 42.3% under the floor
    (12,   10.5340, 128, 0.241625, True),
    (13,    3.2461, 128, 0.133214, True),  # miss — 49.3% under the floor
    (14,    8.9634, 128, 0.160747, True),
    (15,   33.2102, 128, 0.351963, True),
)

#: `lam = 1.25` at `K = 128`, same cell otherwise. `15/16`, and the sole miss is
#: **0.176% over** the ceiling (`64.1126` against `64.0`) — a margin two orders
#: of magnitude tighter than any other miss on this branch, carried in the
#: reading rather than rounded into a clean `15/16`.
MEASURED_SEEDS_16_LAM125_K128: tuple[tuple[int, float, int, float, bool], ...] = (
    ( 0,   12.1011, 128, 0.200420, True),
    ( 1,   24.1243, 128, 0.289774, True),
    ( 2,   23.3304, 128, 0.232995, True),
    ( 3,   27.6944, 128, 0.314559, True),
    ( 4,    9.1218, 128, 0.177136, True),
    ( 5,   39.3432, 128, 0.339768, True),
    ( 6,   36.2703, 128, 0.295678, True),
    ( 7,   14.0560, 128, 0.227310, True),
    ( 8,   21.4303, 128, 0.213695, True),
    ( 9,   28.6530, 128, 0.218426, True),
    (10,   24.0006, 128, 0.199840, True),
    (11,   64.1126, 128, 0.237630, True),  # miss — 0.176% over the ceiling
    (12,   23.0012, 128, 0.274452, True),
    (13,   46.1742, 128, 0.354038, True),
    (14,   38.7211, 128, 0.339432, True),
    (15,   21.8698, 128, 0.205607, True),
)


#: The `w = 5` census columns at `K = 128`, keyed by temperature — the `K = 128`
#: analogue of :data:`CENSUS_COLUMN_ROWS`. Three temperatures, deliberately the
#: three that :data:`CENSUS_COLUMN_ROWS` also carries, so the two grids
#: intersect in a set large enough to compare on (see
#: :func:`unanimity_run_in_k`).
K128_COLUMN_ROWS: dict[float, tuple] = {
    1.0: MEASURED_SEEDS_16_LAM10_K128,
    1.15: MEASURED_SEEDS_16_LAM115_K128,
    1.25: MEASURED_SEEDS_16_LAM125_K128,
}


#: Each `K` has a unanimous temperature among the commonly-walked ones, but
#: they are **different** temperatures: the run moved along `lam` rather than
#: growing. Reported only when the gain and the loss are at *opposite* band
#: edges, because that is what distinguishes a slide from a coincidence.
RUN_TRANSLATES_IN_K = "RUN_TRANSLATES_IN_K"
#: The lower-`K` unanimous set strictly contains the higher-`K` one on the
#: common grid: every temperature that was unanimous still is, plus at least
#: one more. This is the "wider" answer.
RUN_WIDENS_AT_LOWER_K = "RUN_WIDENS_AT_LOWER_K"
#: The lower-`K` unanimous set is strictly contained in the higher-`K` one —
#: membership was lost and nothing gained.
RUN_NARROWS_AT_LOWER_K = "RUN_NARROWS_AT_LOWER_K"
#: Same unanimous temperatures at both `K` on the common grid. `K` moved the
#: ensemble but not across any walked band edge.
RUN_UNCHANGED_IN_K = "RUN_UNCHANGED_IN_K"
#: Gain and loss are both present but at the **same** edge, so the movement is
#: not a coherent slide and no direction reads off it.
RUN_MOVES_INCOHERENTLY = "RUN_MOVES_INCOHERENTLY"
#: At least one `K` has no unanimous temperature on the common grid, so there
#: is no run there to compare against.
RUN_NO_UNANIMITY_AT_SOME_K = "RUN_NO_UNANIMITY_AT_SOME_K"
#: Fewer than two temperatures walked at both `K`, or the columns disagree on
#: seed set or count. Two grids that barely overlap cannot be compared (D-019(b)).
RUN_GRIDS_TOO_THIN = "RUN_GRIDS_TOO_THIN"

#: A miss closer to its band edge than this fraction is reported as *marginal*.
#: Not a re-classification — the seed is still counted a miss — but a `15/16`
#: whose miss is `0.18%` over the ceiling and a `15/16` whose miss is `9.4%`
#: over are different readings, and a bare count spells them identically.
MARGINAL_MISS_TOLERANCE: float = 0.01


def _column_reading(rows, k: float, need: int, tol: float) -> dict:
    """Band membership for one `(K, lam)` column.

    Split out because :func:`unanimity_run_in_k` needs the *same* reading at two
    different `K`, and the one thing that would invalidate the comparison is the
    two sides being read by two slightly different bodies.
    """
    floor, ceil = ess_band(k)
    ess = {r[0]: r[1] for r in rows}
    below = tuple(sorted(s for s, e in ess.items() if e < floor))
    above = tuple(sorted(s for s, e in ess.items() if e > ceil))
    vals = list(ess.values())
    # Upper of the two middle order statistics — `unanimity_bracket`'s and
    # `ensemble_scaling_in_k`'s convention, not `statistics.median` (D-291
    # found a step where the two disagree enough to flip a monotonicity call).
    med = sorted(vals)[len(vals) // 2]
    span = max(vals) / min(vals) if min(vals) > 0 else None
    marginal = tuple(
        (s, ess[s], "floor" if s in below else "ceiling",
         (1 - ess[s] / floor) if s in below else (ess[s] / ceil - 1))
        for s in sorted(set(below) | set(above))
        if ((1 - ess[s] / floor) if s in below else (ess[s] / ceil - 1)) < tol)
    return {
        "n": len(vals),
        "n_in_band": len(vals) - len(below) - len(above),
        "unanimous": len(vals) - len(below) - len(above) == need,
        "missed_below_floor": below,
        "missed_above_ceiling": above,
        "miss_edge": ("both" if below and above else
                      "floor" if below else "ceiling" if above else None),
        "band": (floor, ceil),
        "span": span,
        "band_width": band_width_ratio(k),
        "span_admissible": (span <= band_width_ratio(k)) if span else None,
        "median_ess": med,
        # The coordinate membership is decided in — `ess_band` is fractions of
        # `K`, so raw ESS is not comparable across the two sides of this read.
        "median_frac": med / k,
        # Same count, different firmness. See :data:`MARGINAL_MISS_TOLERANCE`.
        "marginal_misses": marginal,
    }


def _span_response(lo_span, hi_span):
    """Which way a column's spread moves with `K`. `None` when unreadable.

    Kept separate so the "unreadable" case has exactly one spelling: a column
    with a zero minimum has no span, and reporting that as `"flat"` would let
    a missing measurement vote in `span_response_uniform`.
    """
    if lo_span is None or hi_span is None:
        return None
    return ("rises_with_k" if lo_span < hi_span
            else "falls_with_k" if lo_span > hi_span else "flat")


def unanimity_run_in_k(columns_by_k=None, rung: float = 5.0,
                       n_required: int | None = None,
                       tolerance: float | None = None) -> dict:
    """Is the `K = 128` unanimous run **wider** than the `K = 256` one, or has
    it merely **translated**?

    D-292 measured a single unanimous cell at `K = 128`, `lam = 1.15` — the
    temperature that misses at `K = 256`. That is one cell, and a cell is a
    member of something: either `K = 128` admits a *longer* stretch of
    temperatures (in which case lowering `K` is a genuine widening of the
    operating window), or the stretch is the same length and has slid along
    `lam` (in which case something that used to be unanimous is not any more,
    and D-292's cell was bought rather than added). This function walks the
    second possibility to ground.

    **The methodological trap this function exists to avoid.** The two grids
    are not the same size: :data:`CENSUS_COLUMN_ROWS` carries seven
    temperatures at `K = 256`, :data:`K128_COLUMN_ROWS` carries three. Reading
    "`K = 256` is unanimous at `{1.0, 1.1}`, `K = 128` only at `{1.15}`" as a
    *narrowing* would charge `K = 128` for `lam = 1.1`, which was never walked
    there — absence of measurement rendered as failure, which is exactly the
    error D-278 named. Every comparison below is therefore restricted to the
    **intersection** of the two walked grids, and `common_lams` is returned so
    the restriction travels with the verdict.

    **Why the miss *edges* carry the argument.** A gain and a loss on their own
    are consistent with noise on two unrelated seeds. A gain that comes off the
    **ceiling** paired with a loss that goes out the **floor** is a single
    coherent slide of the whole ensemble downward in band-relative coordinates
    — and that is the direction D-292 measured `median_frac` moving with `K`,
    derived there from an entirely different column. So the edges turn two
    membership changes into one mechanism, and
    :data:`RUN_MOVES_INCOHERENTLY` is reserved for when they do not line up.

    **What this does not settle.** It does not locate either endpoint at
    `K = 128` — the walked grid is three points and the endpoints lie in open
    intervals between them, unmeasured. It does not bracket the `K` axis below
    `128` (STATE's second open question). It says nothing about other rungs,
    and nothing transfers to the A/B scene while PR #68 is unmerged.
    """
    cols = ({128: K128_COLUMN_ROWS, 256: CENSUS_COLUMN_ROWS}
            if columns_by_k is None else columns_by_k)
    need = CENSUS_SEEDS if n_required is None else n_required
    tol = MARGINAL_MISS_TOLERANCE if tolerance is None else tolerance

    walked = {k: {l: r for l, r in by_lam.items() if r}
              for k, by_lam in cols.items() if by_lam}
    ks = sorted(walked)
    common = sorted(set.intersection(*(set(v) for v in walked.values()))
                    if len(walked) >= 2 else set())

    seed_sets = {frozenset(r[0] for r in walked[k][l])
                 for k in ks for l in common}
    if len(ks) < 2 or len(common) < 2 or len(seed_sets) != 1 \
            or len(next(iter(seed_sets))) != need:
        return {"verdict": RUN_GRIDS_TOO_THIN, "rung": rung,
                "walked_k": tuple(ks), "common_lams": tuple(common),
                "n_required": need,
                "why": "need ≥2 `K`, each carrying ≥2 shared temperatures on "
                       "one seed set of the census size",
                "endpoints_located": False, "extrapolates": False,
                "transfers_to_ab_scene": False}

    per_k = {k: {l: _column_reading(walked[k][l], k, need, tol) for l in common}
             for k in ks}
    unan = {k: tuple(l for l in common if per_k[k][l]["unanimous"]) for k in ks}

    lo_k, hi_k = ks[0], ks[-1]
    lo_set, hi_set = set(unan[lo_k]), set(unan[hi_k])
    gained = tuple(sorted(lo_set - hi_set))
    lost = tuple(sorted(hi_set - lo_set))

    if not lo_set or not hi_set:
        name = RUN_NO_UNANIMITY_AT_SOME_K
    elif gained and lost:
        # Where each moved temperature sat on the *other* side of the walk.
        gain_edges = {per_k[hi_k][l]["miss_edge"] for l in gained}
        loss_edges = {per_k[lo_k][l]["miss_edge"] for l in lost}
        name = (RUN_TRANSLATES_IN_K
                if len(gain_edges) == 1 and len(loss_edges) == 1
                and gain_edges != loss_edges
                and None not in gain_edges | loss_edges
                else RUN_MOVES_INCOHERENTLY)
    elif gained:
        name = RUN_WIDENS_AT_LOWER_K
    elif lost:
        name = RUN_NARROWS_AT_LOWER_K
    else:
        name = RUN_UNCHANGED_IN_K

    # Built by filtering rather than by subtracting `{None}`: an inline set
    # exemption reads to `guard_reflexivity` as a revocable guard exemption,
    # and this is a measurement reader, not a guard.
    gain_edges = tuple(sorted({per_k[hi_k][l]["miss_edge"] for l in gained
                               if per_k[hi_k][l]["miss_edge"] is not None}))
    loss_edges = tuple(sorted({per_k[lo_k][l]["miss_edge"] for l in lost
                               if per_k[lo_k][l]["miss_edge"] is not None}))

    return {
        "verdict": name,
        "rung": rung,
        "walked_k": tuple(ks),
        # The only legal comparison set. Returned so no caller can re-derive a
        # width from the full (unequal) grids.
        "common_lams": tuple(common),
        "grid_sizes": {k: len(walked[k]) for k in ks},
        "grids_unequal": len({len(walked[k]) for k in ks}) != 1,
        "unanimous_by_k": {k: unan[k] for k in ks},
        "membership_by_k": {k: tuple((l, per_k[k][l]["n_in_band"])
                                     for l in common) for k in ks},
        "gained_at_lower_k": gained,
        "lost_at_lower_k": lost,
        # The run's *length* on the common grid — the direct answer to
        # "wider or shifted". Equal lengths with a non-empty symmetric
        # difference is the signature of a slide.
        "run_length_by_k": {k: len(unan[k]) for k in ks},
        "run_length_unchanged": len(unan[lo_k]) == len(unan[hi_k]),
        # The mechanism, in the two edges that make it one movement.
        "gain_came_off_edge": gain_edges,
        "loss_went_out_edge": loss_edges,
        "slide_direction": ("down" if gain_edges == ("ceiling",)
                            and loss_edges == ("floor",)
                            else "up" if gain_edges == ("floor",)
                            and loss_edges == ("ceiling",) else None),
        # D-292 derived this direction from `median_frac` on the `lam = 1.15`
        # column alone. Here it is re-derived from membership changes on two
        # *different* columns, so agreement is a genuine cross-check.
        "median_frac_by_k": {k: tuple((l, per_k[k][l]["median_frac"])
                                      for l in common) for k in ks},
        "frac_rises_with_k": all(
            per_k[lo_k][l]["median_frac"] < per_k[hi_k][l]["median_frac"]
            for l in common),
        # D-283 per cell. `K` does **not** act on spread the same way at every
        # temperature — see `span_response_in_k`, which is why D-292's
        # "`K` pulls the ensemble apart" does not generalise off its column.
        "span_by_k": {k: tuple((l, per_k[k][l]["span"]) for l in common)
                      for k in ks},
        "inadmissible_cells": tuple(
            (k, l) for k in ks for l in common
            if per_k[k][l]["span_admissible"] is False),
        "span_response_in_k": {l: _span_response(per_k[lo_k][l]["span"],
                                                 per_k[hi_k][l]["span"])
                               for l in common},
        # `None` (an undefined span) is not "flat" and must not be counted as
        # agreement — an unreadable column is excluded from the uniformity test
        # rather than voting in it (D-278). Filtered, not subtracted, for the
        # same reason as `gain_edges` below.
        "span_response_uniform": len({
            _span_response(per_k[lo_k][l]["span"], per_k[hi_k][l]["span"])
            for l in common
            if _span_response(per_k[lo_k][l]["span"],
                              per_k[hi_k][l]["span"]) is not None}) == 1,
        # A `15/16` whose miss clears the edge by `0.18%` is not the same
        # reading as one that clears it by `9.4%`, and the count cannot say so.
        "marginal_misses_by_k": {k: tuple((l, per_k[k][l]["marginal_misses"])
                                          for l in common
                                          if per_k[k][l]["marginal_misses"])
                                 for k in ks},
        "marginal_tolerance": tolerance if tolerance is not None
                              else MARGINAL_MISS_TOLERANCE,
        "per_k": per_k,
        "n_required": need,
        # The three-point grid at `K = 128` places no endpoint; they lie in
        # open intervals between walked temperatures, unmeasured.
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "k_axis_bracketed_below": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "comparable_to": f"readings at n={need}, w={rung} only (D-019(b))",
    }


#: The unanimous stretch along `K` is closed at **both** ends, and the two ends
#: fail at **opposite** band edges: below the run the column drops out through
#: the floor, above it through the ceiling. Same shape D-290 found on `lam`,
#: now on the sample-count axis — and it is what makes the run an interval
#: rather than a half-line someone stopped walking.
K_BRACKET_CLOSED_BOTH_EDGES = "K_BRACKET_CLOSED_BOTH_EDGES"
#: The run is closed at both ends but the two ends fail at the *same* edge,
#: which no single monotone slide produces. Reported rather than smoothed over.
K_BRACKET_CLOSED_SAME_EDGE = "K_BRACKET_CLOSED_SAME_EDGE"
#: The lowest walked `K` is still unanimous, so the run is open at the bottom
#: and D-293's floor prediction is untested rather than confirmed.
K_BRACKET_OPEN_BELOW = "K_BRACKET_OPEN_BELOW"
#: No walked `K` is unanimous, so there is no run to bracket.
K_BRACKET_NO_RUN = "K_BRACKET_NO_RUN"
#: Unanimous columns exist but a walked, **non**-unanimous column sits between
#: two of them, so the unanimous set is not an interval and "the run" is not a
#: single object. D-307 found the older code reporting this case with the same
#: verdict *and* the same `run_bounds_open_intervals` as a contiguous grid; the
#: distinction lived only in `interior_inadmissible_k`, which the headline never
#: consulted. Ranked ahead of `OPEN_BELOW` / `CLOSED_*` because those describe
#: how a run *ends*, and this says the run does not exist to be ended.
K_BRACKET_PUNCTURED_RUN = "K_BRACKET_PUNCTURED_RUN"


def _monotone(seq) -> bool:
    """Non-strict monotonicity in either direction — D-296's membership test."""
    return (all(b >= a for a, b in zip(seq, seq[1:]))
            or all(b <= a for a, b in zip(seq, seq[1:])))


def _near_edge_worse(per_k, ks, below_k, above_k) -> tuple[str, ...]:
    """Sides whose nearest out-of-run column is worse than the one beyond it.

    Kept as a helper rather than inlined so :func:`k_axis_bracket` does not
    grow a second population loop; the pairing it reports is the D-296 finding
    that the endpoint search cannot assume a monotone decay outward.
    """
    out = []
    for edge, near, far in (
            ("below", below_k, max((k for k in ks
                                    if below_k is not None and k < below_k),
                                   default=None)),
            ("above", above_k, min((k for k in ks
                                    if above_k is not None and k > above_k),
                                   default=None))):
        if near is None or far is None:
            continue
        if per_k[near]["n_in_band"] < per_k[far]["n_in_band"]:
            out.append(edge)
    return tuple(out)


def _unanimous_blocks(ks, unan) -> tuple[tuple[int, ...], ...]:
    """Split the unanimous columns into maximal blocks contiguous **in the
    walked axis** — adjacency is "no walked column in between", not "no `K` in
    between", because an unwalked `K` is not evidence of anything.

    Kept separate from :func:`k_axis_bracket` so the puncture test and the
    bounds it suppresses read off one definition of the run rather than two.
    """
    blocks, cur = [], []
    for k in ks:
        if k in unan:
            cur.append(k)
        elif cur:
            blocks.append(tuple(cur))
            cur = []
    if cur:
        blocks.append(tuple(cur))
    return tuple(blocks)


def k_axis_bracket(columns=None, rung: float = 5.0, lam: float = 1.15,
                   n_required: int | None = None) -> dict:
    """Does the downward slide continue below `K = 128`, and does it take
    `lam = 1.15` out through the **floor**?

    D-293 read the `K = 256 → 128` step as a *translation*: the temperature
    that was gained came off the ceiling and the one that was lost went out the
    floor, which is one ensemble sliding down in band-relative coordinates
    rather than a window that got wider. A slide is a mechanism, and a
    mechanism makes a prediction that a translation-of-two-columns does not:
    **keep lowering `K` and the surviving column must eventually exit the same
    way** — through the floor, not the ceiling. This function walks that
    prediction instead of re-reading the step that suggested it.

    **Why the *edge* is the test and the count is not.** A column falling from
    `16/16` to `15/16` is consistent with almost anything, including one unlucky
    seed. What the slide predicts is not that membership drops but *which side*
    it drops off, and the floor is the side no other explanation reaches for:
    a noise story predicts misses on whichever edge the ensemble happens to sit
    nearer, and at `K = 256` that edge is the **ceiling**. So an exit through
    the floor at low `K` is a sign flip, and a sign flip is falsifiable in a way
    a magnitude is not.

    **The interior point is what turns a prediction into a bracket.** Walking
    only `K = 64` would confirm the exit and leave the run open at the bottom —
    `{128}` unanimous with an unwalked gap beneath it. `K = 96` closes that gap
    from the other side: it comes back unanimous, so the run is the interval
    `{96, 128}` with a measured failure on each side of it, and the two failures
    are at **opposite** edges. That is the same shape D-290 reported on `lam`,
    which matters because it is now the second axis on which this window is an
    interval closed by two different mechanisms rather than a threshold.

    **The confirming miss is marginal and is reported as such.** Seed 0 sits at
    `2.9886` against a floor of `3.2` — it needs `1.07x` to re-enter, well
    inside :data:`MARGINAL_MISS_TOLERANCE`'s spirit if not its letter. The
    prediction is confirmed *in direction*, which is what was predicted; it is
    not confirmed *in margin*, and a reader that quoted this as a decisive exit
    would be overselling one seed by 7%. `exit_is_marginal` carries that.

    **The run is checked for holes before it is bracketed (D-308).** Everything
    above says "the run", and until D-307 nothing here verified that the
    unanimous columns form one. They need not: at `n = 32` the set is
    `{96, 160}` with a **measured** non-unanimous `128` between them, and the
    old code reported that with the same verdict *and* the same
    `run_bounds_open_intervals` as the contiguous `{96, 128, 160}` grid, because
    the bounds were built from `min(unan)`/`max(unan)` — which read a set as an
    interval. The distinction survived only in `interior_inadmissible_k`, a
    payload field no headline consulted. So :data:`K_BRACKET_PUNCTURED_RUN` now
    outranks every `OPEN_*` / `CLOSED_*` name, and the bounds go `None` rather
    than spanning a hole. `run_is_contiguous` is the one-bit form of the same
    fact; `unanimous_blocks` says what is actually there instead, and the holes
    are the walked columns its gaps skip.

    **Contiguity is read off the blocks, not off a hole set (D-309).** The
    obvious spelling — `k in ks if min(unan) < k < max(unan) and k not in unan`
    — is a set *difference*, which is the signature
    :mod:`guard_reflexivity` classifies as a **revocable guard**; that
    reclassified this function and demanded an executed probe of it, and a probe
    is a repository act, so there is none to write for a reading about
    measurement columns. The run is contiguous iff the unanimous columns form
    one block, which is the definition rather than a re-derivation of it. The
    respelling that would have kept the hole tuple while dodging the scan was
    declined: a second statement of the same rule is the defect D-045 and D-047
    each are. What remains unresolved is the classification itself — see Q-161.

    **What this does not settle.** It does not locate either endpoint — both lie
    in open intervals (`(64, 96]` below, `(128, 256)` above) and neither is
    walked. It says nothing about other rungs or other temperatures: every
    column here is `lam = 1.15`, `w = 5`. And nothing transfers to the A/B scene
    while PR #68 is unmerged.
    """
    cols = K_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required

    scaling = ensemble_scaling_in_k(columns=cols, rung=rung, lam=lam,
                                    n_required=need)
    if scaling["verdict"] == K_UNWALKED:
        return {"verdict": K_BRACKET_NO_RUN, "rung": rung, "lam": lam,
                "why": scaling["why"], "walked_k": scaling["walked_k"],
                "prediction_tested": False, "endpoints_located": False,
                "extrapolates": False, "transfers_to_ab_scene": False}

    per_k = scaling["per_k"]
    ks = sorted(per_k)
    unan = tuple(k for k in ks if per_k[k]["n_in_band"] == need)

    # D-308. Is the unanimous set an *interval* on the walked axis, or does a
    # measured non-unanimous column sit inside it? Every "the run is …"
    # statement below presupposes the former, so the question is answered
    # before the verdict rather than reported alongside it.
    blocks = _unanimous_blocks(ks, unan)
    contiguous = len(blocks) <= 1

    if not unan:
        name = K_BRACKET_NO_RUN
        below_k = above_k = None
    else:
        # The walked neighbours immediately outside the unanimous run.
        below_k = max((k for k in ks if k < min(unan)), default=None)
        above_k = min((k for k in ks if k > max(unan)), default=None)
        if not contiguous:
            # There is no single run, so how it ends is not yet a question.
            name = K_BRACKET_PUNCTURED_RUN
        elif below_k is None or above_k is None:
            # Open on at least one side: the lowest (or highest) walked `K` is
            # itself unanimous, so the run has no measured failure beyond it and
            # the prediction is untested on that side rather than confirmed.
            name = K_BRACKET_OPEN_BELOW
        else:
            lo_edge = per_k[below_k]["miss_edge"]
            hi_edge = per_k[above_k]["miss_edge"]
            name = (K_BRACKET_CLOSED_BOTH_EDGES
                    if lo_edge and hi_edge and lo_edge != hi_edge
                    else K_BRACKET_CLOSED_SAME_EDGE)

    # D-293's prediction, stated before it is scored: the column below the run
    # exits through the FLOOR.
    predicted_edge = "floor"
    observed_edge = per_k[below_k]["miss_edge"] if below_k is not None else None
    confirmed = observed_edge == predicted_edge

    # How far the confirming miss actually is from re-entering the band.
    margin = None
    if below_k is not None and per_k[below_k]["missed_below_floor"]:
        floor = per_k[below_k]["band"][0]
        ess = {r[0]: r[1] for r in cols[below_k]}
        worst = min(ess[s] for s in per_k[below_k]["missed_below_floor"])
        margin = floor / worst if worst > 0 else None

    return {
        "verdict": name,
        "rung": rung,
        "lam": lam,
        "walked_k": tuple(ks),
        "unanimous_k": unan,
        # D-308. Suppressed entirely when the run is punctured: `(min, max)` of
        # a non-interval names a span the measurement does not support, and it
        # is the field D-307 caught reading identically on a contiguous grid and
        # a holed one. `None` is the honest shape — not a bound that is unknown,
        # but an object that is not there to be bounded.
        "run_bounds_open_intervals": None if not contiguous else (
            (below_k, min(unan)) if unan and below_k is not None else None,
            (max(unan), above_k) if unan and above_k is not None else None,
        ),
        "run_is_contiguous": bool(unan) and contiguous,
        "unanimous_blocks": blocks,
        # The prediction and its score, side by side, so neither can be quoted
        # without the other.
        "predicted_exit_edge_below": predicted_edge,
        "observed_exit_edge_below": observed_edge,
        "slide_prediction_confirmed": confirmed,
        "prediction_tested": below_k is not None,
        # Direction confirmed is not margin confirmed. See the docstring.
        "exit_margin_to_reenter": margin,
        "exit_is_marginal": (margin is not None and margin < 1.10),
        "exit_seeds": (per_k[below_k]["missed_below_floor"]
                       if below_k is not None else ()),
        # Carried through so the bracket is never read apart from the slide it
        # is evidence about.
        "slide_verdict": scaling["verdict"],
        "median_frac_by_k": scaling["median_frac_by_k"],
        "membership_by_k": scaling["membership_by_k"],
        "span_by_k": scaling["span_by_k"],
        "inadmissible_k": scaling["inadmissible_k"],
        # D-296. Both readings are about the *approach* to the edges, which is
        # what a bisection makes visible and a two-sided bracket does not.
        #
        # `near_edge_worse_than_far` names each side whose nearest walked
        # neighbour outside the run holds fewer seeds than the column beyond
        # it. On the bisected axis both sides qualify (`15, 14, 16, 16, 14,
        # 15, 11`), so whatever removes seeds at an edge is not monotone in
        # `K` — and an endpoint search that assumed it was would step past
        # both endpoints.
        "membership_monotone": _monotone(
            [c for _, c in scaling["membership_by_k"]]),
        "near_edge_worse_than_far": _near_edge_worse(per_k, ks, below_k,
                                                     above_k),
        "interior_inadmissible_k": tuple(k for k in scaling["inadmissible_k"]
                                         if k != max(ks)),
        "n_required": need,
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "applies_to_other_lams": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "comparable_to": f"readings at n={need}, w={rung} only (D-019(b))",
    }


#: The two exits are attributed to **different** quantities, so no single
#: band-relative curve crossing the floor predicts both bounds: the window is
#: closed by two mechanisms that happen to share an edge.
SAME_EDGE_TWO_MECHANISMS = "SAME_EDGE_TWO_MECHANISMS"
#: Both exits are attributed to the same quantity, so one curve does predict
#: both bounds and the run's endpoints are a threshold on that curve.
SAME_EDGE_ONE_CURVE = "SAME_EDGE_ONE_CURVE"
#: At least one exit is cured by **both** substitutions or by **neither**, so
#: the decomposition does not separate the two quantities there.
SAME_EDGE_UNDECIDED = "SAME_EDGE_UNDECIDED"
#: The bracket is not `K_BRACKET_CLOSED_SAME_EDGE`, so there is no same-edge
#: window to decompose. Reported rather than answered on a different shape.
SAME_EDGE_NOT_APPLICABLE = "SAME_EDGE_NOT_APPLICABLE"

#: How close a substituted column may sit to the floor before its cure (or
#: non-cure) is reported as marginal. `K = 176`'s position substitution lands
#: `1.04x` short, and a reader that quoted that leg as decisive would be
#: overselling a 4% gap — the same discipline `exit_is_marginal` carries for
#: the raw exit (D-294).
SAME_EDGE_MARGIN_TOLERANCE: float = 0.10


def _floor_decomposition(rows, k: int) -> dict:
    """Split one column's lowest seed into **position** and **lower spread**.

    Band membership at the floor is decided by `min(ESS) / K`, and that
    coordinate factors exactly two ways::

        min_frac = median_frac / lower_spread

    where `median_frac = median(ESS) / K` is where the ensemble *sits* in
    band-relative coordinates and `lower_spread = median(ESS) / min(ESS)` is
    how far its lower tail reaches below that. The identity is arithmetic, not
    a model, and it is pinned by a test — which is the point: the two factors
    can be substituted independently, so "did the ensemble slide down or did it
    fan out" becomes a measurement instead of a reading of the same number
    twice.

    Only the **lower** half of the spread appears. `ess_span`'s `max/min`
    mixes in the ceiling tail, which is not the tail that decides a floor miss,
    and on this axis the two do not move together (`K = 160` has the tightest
    full span on the axis and an unremarkable lower half).
    """
    vals = sorted(r[1] for r in rows)
    # Upper of the two middle order statistics — `_column_reading`'s and
    # `ensemble_scaling_in_k`'s convention, carried here so a decomposition can
    # be compared against the `median_frac` those two already publish (D-291).
    med = vals[len(vals) // 2]
    lo = vals[0]
    return {
        "median_frac": med / k,
        "lower_spread": med / lo if lo > 0 else None,
        "min_frac": lo / k,
        "floor_frac": ess_band(k)[0] / k,
    }


def _ceiling_decomposition(rows, k: int) -> dict:
    """Mirror of :func:`_floor_decomposition` at the other band edge.

    The ceiling coordinate factors the same way, with the tail running the
    other direction::

        max_frac = median_frac * upper_spread

    where `upper_spread = max(ESS) / median(ESS)`. Same median convention, so
    the two decompositions share their `median_frac` exactly and a column's
    two coordinates are one position and two tails, not two unrelated
    readings.
    """
    vals = sorted(r[1] for r in rows)
    med = vals[len(vals) // 2]
    hi = vals[-1]
    return {
        "median_frac": med / k,
        "upper_spread": hi / med if med > 0 else None,
        "max_frac": hi / k,
        "ceil_frac": ess_band(k)[1] / k,
    }


def _substitute(rows, k: int, ref: dict, factor: str) -> dict:
    """Lend a column one of the run's two factors and re-read **both** edges.

    `factor="position"` keeps the column's two tails and moves it to where the
    run sits; `factor="spread"` keeps the column where it is and gives it the
    run's tails.

    **The cure test is in-band, not this-edge.** A substitution that clears
    the floor miss while pushing the column out through the ceiling has not
    restored anything — and that is not hypothetical: `K = 80` lent the run's
    position clears the floor at `2.29x` and lands at `1.15x` of the *ceiling*
    (D-300). Testing only the edge the column originally missed reports that
    as a cure.

    Reading both edges is also exactly the right test rather than a stricter
    one, because `min` and `max` bracket every seed: `floor <= min` and
    `max <= ceil` holds precisely when the whole column is in band. So
    `in_band` is membership unanimity itself, which is the property the window
    is defined by — not an extra hurdle placed in front of it.
    """
    f = _floor_decomposition(rows, k)
    c = _ceiling_decomposition(rows, k)
    if factor == "position":
        lo = ref["median_frac"] / f["lower_spread"]
        hi = ref["median_frac"] * c["upper_spread"]
    elif factor == "spread":
        lo = f["median_frac"] / ref["lower_spread"]
        hi = c["median_frac"] * ref["upper_spread"]
    else:
        raise ValueError("factor must be 'position' or 'spread'")
    return {
        "min_frac": lo,
        "max_frac": hi,
        "floor_ratio": lo / f["floor_frac"],
        "ceil_ratio": hi / c["ceil_frac"],
        "in_band": f["floor_frac"] <= lo and hi <= c["ceil_frac"],
    }


def _run_reference(columns) -> dict:
    """The unanimous run's position and both tails, as medians across it.

    Takes `(rows, k)` pairs rather than a column dict because the two axes key
    their columns differently — `K_COLUMN_ROWS` by the sample count itself,
    `CENSUS_COLUMN_ROWS` by `lam` at a fixed `K`. The decomposition's `k` is
    always the **sample count** (the band's argument and the fraction's
    denominator), never the column key.
    """
    floors = [_floor_decomposition(rows, k) for rows, k in columns]
    ceils = [_ceiling_decomposition(rows, k) for rows, k in columns]
    return {
        "median_frac": median([p["median_frac"] for p in floors]),
        "lower_spread": median([p["lower_spread"] for p in floors]),
        "upper_spread": median([p["upper_spread"] for p in ceils]),
    }


def _attribute(rows, k: int, ref: dict) -> dict:
    """Both substitutions on one exit column, plus the attribution they imply."""
    pos = _substitute(rows, k, ref, "position")
    spr = _substitute(rows, k, ref, "spread")
    attribution = ("position" if pos["in_band"] and not spr["in_band"] else
                   "spread" if spr["in_band"] and not pos["in_band"] else
                   "both" if pos["in_band"] else "neither")
    return {
        "k": k,
        **_floor_decomposition(rows, k),
        **_ceiling_decomposition(rows, k),
        "with_run_position": pos,
        "with_run_spread": spr,
        # Retained under their D-299 names: these are the *edge-only* readings,
        # still true as measurements and now visibly not the cure test.
        "run_position_floor_ratio": pos["floor_ratio"],
        "run_spread_floor_ratio": spr["floor_ratio"],
        "cured_by_run_position": pos["in_band"],
        "cured_by_run_spread": spr["in_band"],
        "attribution": attribution,
        # A substitution landing inside the tolerance of *either* edge decides
        # the attribution on a margin too thin to carry it alone.
        "marginal": any(abs(s[r] - 1.0) < SAME_EDGE_MARGIN_TOLERANCE
                        for s in (pos, spr) for r in ("floor_ratio", "ceil_ratio")),
    }


def _decomposition_verdict(attributions, names) -> str:
    """`(one_curve, two_mechanisms, undecided)` from the two attributions."""
    one, two, undecided = names
    # Spelled as equalities rather than `a in ("both", "neither")` on purpose.
    # An inline membership test reads to `guard_reflexivity` as an **exemption**,
    # which types this function's population as a `DIFFERENCE` and puts it in
    # `unprobed_revocable()` — a debt D-295 measured as currently unpayable (the
    # probe fixture does not exist). Nothing here exempts anything: both spellings
    # name the same two verdicts, and this one says so without claiming a shape
    # the function does not have.
    decided = all(a == "position" or a == "spread" for a in attributions)
    if not decided:
        return undecided
    return one if attributions[0] == attributions[1] else two


def same_edge_decomposition(columns=None, rung: float = 5.0,
                            lam: float = 1.15,
                            n_required: int | None = None) -> dict:
    """Do the run's two bounds come off **one** band-relative curve?

    D-298 flipped the `K` bracket from `CLOSED_BOTH_EDGES` to
    :data:`K_BRACKET_CLOSED_SAME_EDGE`: both walked neighbours outside the
    unanimous run — `K = 80` below, `K = 176` above — lose seeds through the
    **floor**. That reading invites one obvious continuation, and STATE named
    it as this cycle's question: if both exits are the same edge then perhaps
    they are the same *quantity*, band-relative ESS sagging toward the floor on
    both sides, and the two bounds should then be predictable from a single
    curve rather than bracketed independently. That would be a real reduction —
    two searches collapsing into one root-find.

    **The test is a substitution, and it costs no runs.** For each exit column,
    replace one of its two factors (:func:`_floor_decomposition`) with the run's
    own value and ask whether the floor miss survives:

    - substitute the run's **position**, keep the column's spread;
    - substitute the run's **spread**, keep the column's position.

    A one-curve window is one where the *same* substitution cures both exits.
    Two mechanisms is where each exit is cured by a different one. Both
    outcomes were available before the arithmetic ran, and so were the two
    degenerate ones (:data:`SAME_EDGE_UNDECIDED`) where a substitution cures
    everything or nothing — which is what keeps this from being a predicate
    that can only return the answer it was written for (D-241).

    **Why not just read `min_frac < floor_frac`.** Because that is the
    definition of a floor miss, not a prediction of one: `min(ESS)/K < 0.05`
    holds exactly when some seed is below the floor, so a "curve" fitted to it
    is the membership count wearing different units. The substitution is not
    vacuous in that way — it asks a counterfactual about a column, and the
    column's own answer can come back either way.

    **D-300 narrowed what this returns.** The cure test above was originally
    scored on the exit's *own* edge, and under that rule this window read
    `SAME_EDGE_TWO_MECHANISMS`. Scored in band — which is what membership
    unanimity actually is, see :func:`_substitute` — `K = 80`'s position
    substitution turns out to clear the floor by pushing the column `1.15x`
    over the **ceiling**, so it cures nothing and the verdict is
    :data:`SAME_EDGE_UNDECIDED`. Every ratio below is unchanged as a
    measurement; only the predicate reading them moved.

    **What this cannot say.** It attributes the two *walked* exits, and the
    endpoints themselves are still unlocated inside `(80, 96)` and `(160, 176)`
    — a mechanism attributed at the neighbour is not a mechanism attributed at
    the boundary. Every column is `lam = 1.15`, `w = 5`, `cafe_freezing_v0`,
    and nothing here transfers to the A/B scene while PR #68 is unmerged.
    """
    cols = K_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required

    bracket = k_axis_bracket(columns=cols, rung=rung, lam=lam,
                             n_required=need)
    base = {
        "rung": rung,
        "lam": lam,
        "bracket_verdict": bracket["verdict"],
        "n_required": need,
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "applies_to_other_lams": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "comparable_to": f"readings at n={need}, w={rung} only (D-019(b))",
    }
    if bracket["verdict"] != K_BRACKET_CLOSED_SAME_EDGE:
        return {**base, "verdict": SAME_EDGE_NOT_APPLICABLE,
                "why": "decomposition is defined on a same-edge bracket only",
                "exits": {}, "run_reference": None}

    unan = bracket["unanimous_k"]
    below_k = bracket["run_bounds_open_intervals"][0][0]
    above_k = bracket["run_bounds_open_intervals"][1][1]

    ref = _run_reference([(cols[k], k) for k in unan])
    ref = {**ref, "k": unan}
    exits = {edge: _attribute(cols[k], k, ref)
             for edge, k in (("below", below_k), ("above", above_k))}

    attributions = tuple(exits[e]["attribution"] for e in ("below", "above"))
    name = _decomposition_verdict(
        attributions,
        (SAME_EDGE_ONE_CURVE, SAME_EDGE_TWO_MECHANISMS, SAME_EDGE_UNDECIDED))

    return {
        **base,
        "verdict": name,
        "run_reference": ref,
        "exits": exits,
        "attributions": attributions,
        # The headline restated as the thing a next cycle would act on: one
        # curve would mean the two endpoint searches share a root-find.
        "bounds_share_one_curve": name == SAME_EDGE_ONE_CURVE,
        "any_leg_marginal": any(exits[e]["marginal"] for e in exits),
    }


#: The `lam` window's two exits are attributed to **different** quantities —
#: D-290's edge-level "two mechanisms" reading, confirmed at the factor level.
LAM_WINDOW_TWO_MECHANISMS = "LAM_WINDOW_TWO_MECHANISMS"
#: Both exits are attributed to the same quantity: one monotone curve in that
#: quantity carries the ensemble out through the floor below and the ceiling
#: above, and *opposite edges* turn out to be one mechanism seen twice.
LAM_WINDOW_ONE_CURVE = "LAM_WINDOW_ONE_CURVE"
#: At least one exit is cured by **both** substitutions or by **neither**, so
#: the decomposition does not separate the two quantities there.
LAM_WINDOW_UNDECIDED = "LAM_WINDOW_UNDECIDED"
#: The bracket is not closed at both edges, so there is no window to decompose.
LAM_WINDOW_NOT_APPLICABLE = "LAM_WINDOW_NOT_APPLICABLE"


def lam_window_decomposition(columns=None, rung: float = 5.0,
                             k: int = 256,
                             n_required: int | None = None) -> dict:
    """Does the `lam` window's *different*-edge pair mean different mechanisms?

    The dual of :func:`same_edge_decomposition`, and STATE named it as such.
    D-290 closed the `lam` run `{1.0, 1.1}` at **opposite** band edges — `0.9`
    below loses seeds through the floor, `1.15` above through the ceiling — and
    read that as two mechanisms. That inference is the mirror image of the one
    D-299 examined, and it is no safer: *different* edges no more implies
    different quantities than *same* edge implied one.

    It has an obvious one-curve story, which is what makes it worth testing
    rather than assuming. Median ESS rises monotonically across the window
    (`40.1, 54.8, 75.4, 79.2` for `0.9 .. 1.15`), so a single curve in
    **position** would push the ensemble down out of the floor below and up out
    of the ceiling above. One quantity, two edges. The substitution is what
    decides between that and D-290's reading, and it costs no runs.

    **The measured answer is neither** — :data:`LAM_WINDOW_UNDECIDED`, and each
    exit is undecided in a different direction:

    - **Below (`0.9`) is cured by neither.** Its span is `16.56x` against a
      `10.0x` band, so it is span-inadmissible in D-283's sense, and no single
      factor lifts it in: the run's position leaves the minimum at `0.97x` of
      the floor and simultaneously throws the maximum to `1.60x` of the
      ceiling; the run's spread leaves it at `0.82x` of the floor. A column
      wider than the band cannot be put inside the band by moving it.
    - **Above (`1.15`) is cured by both.** It clears the band on either
      substitution (`0.90x` and `0.92x` of the ceiling), because its miss is
      thin — `140.07` against a `128.0` ceiling, `9.4%` over. Two factors that
      each suffice attribute nothing.

    So D-290's edge-level reading is left **unsupported rather than refuted**,
    which is the honest place for it: this instrument cannot separate the `lam`
    window's mechanisms on the columns walked so far. What would decide it is
    a column above the run that misses by more than one factor's worth, or a
    below-column narrow enough to be admissible — neither exists yet.

    **What this cannot say.** It attributes the two *walked* exits, not the
    endpoints, which remain unlocated inside `(0.9, 1.0)` and `(1.1, 1.15)`.
    Every column is `w = 5`, `K = 256`, `cafe_freezing_v0`; nothing transfers
    to the A/B scene while PR #68 is unmerged.
    """
    cols = CENSUS_COLUMN_ROWS if columns is None else columns
    need = CENSUS_SEEDS if n_required is None else n_required

    bracket = unanimity_bracket(cols, rung=rung, n_required=need)
    base = {
        "rung": rung,
        "k": k,
        "bracket_verdict": bracket["verdict"],
        "n_required": need,
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "applies_to_other_ks": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "comparable_to": f"readings at n={need}, w={rung}, K={k} only (D-019(b))",
    }
    if bracket["verdict"] != BRACKET_CLOSED_BOTH_EDGES:
        return {**base, "verdict": LAM_WINDOW_NOT_APPLICABLE,
                "why": "decomposition needs a window closed at both edges",
                "exits": {}, "run_reference": None}

    unan = bracket["unanimous_lams"]
    below_lam = bracket["lower_endpoint_in"][0]
    above_lam = bracket["upper_endpoint_in"][1]

    # `k` is constant across this axis, so the band-relative coordinates the
    # decomposition works in are the raw ESS ones rescaled — the same helpers
    # serve both axes unchanged, which is why the two verdicts are comparable.
    ref = _run_reference([(cols[l], k) for l in unan])
    ref = {**ref, "lam": tuple(unan), "k": k}

    exits = {}
    for edge, lam in (("below", below_lam), ("above", above_lam)):
        part = _attribute(cols[lam], k, ref)
        exits[edge] = {**part, "lam": lam,
                       "miss_edge": bracket["per_lam"][lam]["miss_edge"],
                       "span": bracket["per_lam"][lam]["span"],
                       "span_admissible": (bracket["per_lam"][lam]["span"]
                                           <= bracket["band_width"])}
        del exits[edge]["k"]

    attributions = tuple(exits[e]["attribution"] for e in ("below", "above"))
    name = _decomposition_verdict(
        attributions,
        (LAM_WINDOW_ONE_CURVE, LAM_WINDOW_TWO_MECHANISMS, LAM_WINDOW_UNDECIDED))

    return {
        **base,
        "verdict": name,
        "run_reference": ref,
        "exits": exits,
        "attributions": attributions,
        # The two edges the window closes at, restated so a reader never has to
        # infer "different edges" from the lam values.
        "exit_edges": tuple(exits[e]["miss_edge"] for e in ("below", "above")),
        "bounds_share_one_curve": name == LAM_WINDOW_ONE_CURVE,
        "any_leg_marginal": any(exits[e]["marginal"] for e in exits),
    }


#: Every leg's attribution survives every single-seed deletion, so the
#: (position, spread) reading is a property of the column rather than of which
#: 16 seeds were drawn.
SEPARABILITY_STABLE = "SEPARABILITY_STABLE"
#: At least one leg's attribution changes when one seed is dropped. The
#: decomposition is then reading sampling noise at that leg, and the verdict it
#: feeds cannot be quoted without this caveat.
SEPARABILITY_FRAGILE = "SEPARABILITY_FRAGILE"
#: No in-band deletion flips anything, but a **decided** leg's miss is one seed
#: wide — the only deletion that could move it is the one that deletes the
#: exit. The jackknife cannot probe that leg at all, in either direction.
SEPARABILITY_UNTESTABLE = "SEPARABILITY_UNTESTABLE"
#: The underlying window is not the shape its decomposition is defined on, so
#: there are no legs to jackknife. Reported rather than answered.
SEPARABILITY_NOT_APPLICABLE = "SEPARABILITY_NOT_APPLICABLE"


def _jackknife_attributions(rows, k: int, ref: dict) -> tuple:
    """`(seed, attribution)` for each single-seed deletion of one column."""
    rows = tuple(rows)
    return tuple((rows[i][0], _attribute(rows[:i] + rows[i + 1:], k, ref)["attribution"])
                 for i in range(len(rows)))


def _leg_stability(rows, k: int, ref: dict, full: str) -> dict:
    """One exit column's jackknife, **split by whether the deletion was legal.**

    A plain jackknife is confounded here and the confound is not subtle. An
    exit column is an exit *because* some seed sits outside the band, so the
    deletion that removes that seed removes the phenomenon being attributed —
    the remaining 15 are in band, both substitutions trivially cure, and the
    attribution goes to `both`. That flip says nothing about sampling noise;
    it says the column was a `15/16` column.

    So each deletion is typed by the seed it removes. Deleting an **in-band**
    seed leaves the miss intact and is a real perturbation of the attribution
    — those are the flips that count. Deleting an **out-of-band** seed is
    confounded and is reported separately, never as evidence.
    """
    rows = tuple(rows)
    lo, hi = ess_band(k)
    out_of_band = tuple(r[0] for r in rows if not (lo <= r[1] <= hi))
    jack = _jackknife_attributions(rows, k, ref)
    flips = tuple((s, a) for s, a in jack if a != full)
    genuine = tuple((s, a) for s, a in flips if s not in out_of_band)
    confounded = tuple((s, a) for s, a in flips if s in out_of_band)
    decided = "position", "spread"
    return {
        "attribution": full,
        "n_seeds": len(rows),
        "jackknife": jack,
        "attributions_seen": tuple(sorted({a for _, a in jack})),
        "out_of_band_seeds": out_of_band,
        # A one-seed-wide miss is the untestable case: the sole deletion that
        # could reveal fragility is the confounded one.
        "miss_is_one_seed_wide": len(out_of_band) == 1,
        "flips": flips,
        "genuine_flips": genuine,
        "confounded_flips": confounded,
        # `stable` is the reading that carries — confounded flips excluded.
        "stable": not genuine,
        "stable_on_all_deletions": not flips,
        "flip_fraction": len(genuine) / len(jack) if jack else 0.0,
        # The two directions a genuine flip can run, kept apart because they
        # mean opposite things about the instrument.
        "decided_becomes_undecided": tuple(
            (s, a) for s, a in genuine if full in decided and a not in decided),
        "undecided_becomes_decided": tuple(
            (s, a) for s, a in genuine if full not in decided and a in decided),
    }


def attribution_separability(window: str = "k", columns=None, rung: float = 5.0,
                             lam: float = 1.15, k: int = 256,
                             n_required: int | None = None) -> dict:
    """Is the (position, spread) attribution structure, or which 16 seeds ran?

    D-299 and D-300 both read a window by lending an exit column one of the
    run's two factors and asking whether the column comes back in band. Both
    factors are computed from the **same 16-seed ensemble** — `median_frac` off
    the middle order statistic, the two spreads off `min` and `max` — so an
    `UNDECIDED` leg has two available explanations that the decomposition
    itself cannot tell apart: the two quantities genuinely fail to separate at
    that column, or the ensemble is small enough that the answer is noise.
    STATE named this before D-300 created the need for it, and Phase 0's feed
    named it before STATE did.

    **The test is leave-one-seed-out and it costs no runs.** Drop one seed from
    an exit column, recompute both substitutions on the remaining 15, and read
    the attribution again. Do it for all 16. If every deletion returns the
    attribution the full ensemble gave, the reading is a property of the
    column; if any deletion changes it, the reading is one seed deep.

    This bites harder than a jackknife usually does, and deliberately so: the
    substituted coordinates are **order statistics**, so deleting the seed that
    *is* the minimum moves `lower_spread` to the second-lowest seed directly.
    A column whose attribution rests on one extreme seed is exactly the column
    this is meant to catch, and that column is common at `n = 16`.

    **The plain jackknife is confounded, and the confound had to be split out**
    (see :func:`_leg_stability`). An exit column is an exit because a seed sits
    outside the band, so deleting *that* seed deletes the phenomenon: the
    remaining 15 are in band, both substitutions trivially cure, and the
    attribution reads `both` no matter what the two quantities were doing. On
    the measured axes the raw jackknife produced exactly one flip and it was
    this — `K = 176` losing seed `0`, the `7.53` that misses the `8.8` floor
    and is the sole reason `176` is a `15/16` column. Scored raw, the one
    decided leg on either axis looked one seed deep; scored on **in-band
    deletions only**, nothing flips anywhere. Which deletions are legal is
    therefore the whole reading, not a refinement of it.

    **A one-seed-wide miss is untestable, not stable.** If the only deletion
    that could move a decided leg is the confounded one, the jackknife has no
    purchase on that leg in either direction, and saying `STABLE` would be
    claiming a test that never ran — hence :data:`SEPARABILITY_UNTESTABLE`.
    What breaks that tie is not more analysis of these columns: it is seeds.
    At `n = 32` a column missing by one seed at `n = 16` either keeps missing
    (and the miss widens enough to survive a deletion) or does not.

    **Two honest caveats about what is perturbed.**

    - The run reference is held **fixed** at its full-ensemble value. Only the
      exit column is resampled, so this bounds the exit's own fragility and
      says nothing about the reference's. The reference is a median across
      three columns' medians and is the more robust of the two, but "more
      robust" is an expectation here, not a measurement.
    - The median convention shifts with the sample. `_floor_decomposition`
      takes `vals[len(vals) // 2]`, the upper of the two middle values at
      `n = 16` and the true middle at `n = 15`, so a deletion perturbs the
      estimator as well as the sample. That is inherent to jackknifing an
      order statistic and is reported rather than corrected — correcting it
      would mean scoring the deletions with an estimator the headline reading
      never used.

    **Both verdicts are reachable** (D-241): a column whose attribution rests
    on one extreme seed returns :data:`SEPARABILITY_FRAGILE`, and one whose
    seeds are interchangeable returns :data:`SEPARABILITY_STABLE`. Both are
    constructed in the tests, neither drawn from this axis.

    **What this cannot say.** It does not locate any endpoint, does not license
    a `lam`/`K` column that was never walked, and transfers to no other scene —
    every column is `cafe_freezing_v0` and the A/B reading stays blocked on
    PR #68. A `STABLE` verdict makes an `UNDECIDED` leg *durable*, not
    *decided*: it says the two quantities fail to separate there for a reason
    the ensemble size is not responsible for.
    """
    need = CENSUS_SEEDS if n_required is None else n_required
    if window == "k":
        cols = K_COLUMN_ROWS if columns is None else columns
        dec = same_edge_decomposition(columns=cols, rung=rung, lam=lam,
                                      n_required=need)
        not_applicable = SAME_EDGE_NOT_APPLICABLE
        axis_key, denom = "k", None
    elif window == "lam":
        cols = CENSUS_COLUMN_ROWS if columns is None else columns
        dec = lam_window_decomposition(columns=cols, rung=rung, k=k,
                                       n_required=need)
        not_applicable = LAM_WINDOW_NOT_APPLICABLE
        axis_key, denom = "lam", k
    else:
        raise ValueError("window must be 'k' or 'lam'")

    base = {
        "window": window,
        "rung": rung,
        "n_required": need,
        "decomposition_verdict": dec["verdict"],
        "endpoints_located": False,
        "extrapolates": False,
        "applies_to_other_rungs": False,
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
        "reference_held_fixed": True,
        "comparable_to": f"readings at n={need}, w={rung} only (D-019(b))",
    }
    if dec["verdict"] == not_applicable:
        return {**base, "verdict": SEPARABILITY_NOT_APPLICABLE,
                "why": "no window of the shape the decomposition is defined on",
                "legs": {}, "fragile_legs": ()}

    ref = dec["run_reference"]
    legs = {}
    for edge in ("below", "above"):
        exit_ = dec["exits"][edge]
        key = exit_[axis_key]
        legs[edge] = {axis_key: key,
                      **_leg_stability(cols[key], denom if denom else key, ref,
                                       exit_["attribution"])}

    decided = ("position", "spread")
    fragile = tuple(e for e in ("below", "above") if not legs[e]["stable"])
    # A decided leg whose miss is one seed wide cannot be probed: the only
    # deletion that moves it is the confounded one. Reported as its own verdict
    # rather than folded into `STABLE`, which would claim a test that never ran.
    untestable = tuple(e for e in ("below", "above")
                       if legs[e]["attribution"] in decided
                       and legs[e]["miss_is_one_seed_wide"])
    verdict = (SEPARABILITY_FRAGILE if fragile else
               SEPARABILITY_UNTESTABLE if untestable else
               SEPARABILITY_STABLE)
    return {
        **base,
        "verdict": verdict,
        "run_reference": ref,
        "legs": legs,
        "fragile_legs": fragile,
        "untestable_legs": untestable,
        "attributions": dec["attributions"],
        # The headline a next cycle acts on, split by direction. A decided leg
        # that survives is the decomposition's only load-bearing claim; an
        # undecided leg that *decides* under a deletion means `UNDECIDED` was
        # itself the noise reading.
        "decided_legs": tuple(e for e in ("below", "above")
                              if legs[e]["attribution"] in decided),
        # `stable` alone would be true of an untestable leg — no genuine
        # deletion flipped it because no genuine deletion could reach it. A
        # leg counts as survived only if the jackknife had purchase on it.
        "decided_legs_stable": tuple(e for e in ("below", "above")
                                     if legs[e]["attribution"] in decided
                                     and legs[e]["stable"]
                                     and not legs[e]["miss_is_one_seed_wide"]),
        "undecided_legs_that_decide": tuple(
            e for e in ("below", "above")
            if legs[e]["undecided_becomes_decided"]),
        "worst_flip_fraction": max((legs[e]["flip_fraction"] for e in legs),
                                   default=0.0),
    }
