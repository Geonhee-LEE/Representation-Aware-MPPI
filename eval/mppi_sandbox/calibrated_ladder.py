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
                channel: str = "w_voo") -> tuple[Point, ...]:
    """Re-take :data:`MEASURED_SEEDS` — one closed-loop run per seed.

    Same body as :func:`sweep` with the loop moved from `(lam, weight)` to
    `seed`, so the ensemble and the ladder cannot diverge in isolation or in
    how the ratio is read.
    """
    from .ab import DEFAULT_SEEDS
    from .controllers.stock_mppi import MPPIParams
    from .weight_units import measure

    lam, weight = ENSEMBLE_CELL if cell is None else cell
    cfg = {channel: float(weight)}
    cfg.update({c: 0.0 for c in EPISTEMIC_CHANNELS if c != channel})

    out = []
    for seed in (DEFAULT_SEEDS if seeds is None else seeds):
        params = MPPIParams(lam=float(lam))
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
