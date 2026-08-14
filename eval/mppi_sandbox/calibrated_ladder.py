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


def seed_points(rows=MEASURED_SEEDS) -> tuple[Point, ...]:
    """The ensemble rows as :class:`Point`\\ s at :data:`ENSEMBLE_CELL`."""
    lam, weight = ENSEMBLE_CELL
    return tuple(
        Point(lam=lam, weight=weight, median_ess=ess, n_samples=k,
              ratio=ratio, reached_goal=reached, seed=seed)
        for seed, ess, k, ratio, reached in rows
    )


def seed_census(rows=MEASURED_SEEDS) -> dict:
    """Per-condition counts over the ensemble — fractions, not booleans.

    Stored this way on D-019's own precedent: a boolean collapses `7/8` and
    `0/8` into the same `False`, and the difference between a near-miss and a
    clean failure is the whole reading. Callers derive the verdict from the
    counts; nothing here decides.
    """
    pts = seed_points(rows)
    n = len(pts)
    return {
        "n": n,
        "cell": ENSEMBLE_CELL,
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


def ess_span(rows=MEASURED_SEEDS) -> float | None:
    """`max / min` median ESS across the ensemble — `None` on an empty read.

    D-019 measured per-seed ESS spans of ~5× and that number is the reason this
    ensemble exists. Reported so the claim can be checked on this cell rather
    than carried over from the cell D-019 read it on.
    """
    ess = [p.median_ess for p in seed_points(rows) if p.median_ess == p.median_ess]
    if not ess or min(ess) <= 0:
        return None
    return max(ess) / min(ess)


def seed_verdict(rows=MEASURED_SEEDS) -> dict:
    """Is :data:`ENSEMBLE_CELL` a window, or seed 0's luck?

    The vocabulary is fixed here before the counts are read (D-241): the
    tempting failure is to see `k/8` and reach for whichever word flatters it.
    Only unanimity earns the word *window*, because that is exactly the
    predicate D-019 showed `admissible` to be — anything less is a rate, and a
    rate at `n = 8` licenses nothing about `n = 16`.
    """
    c = seed_census(rows)
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
        "ess_span": ess_span(rows),
        # An ensemble on one scene at one cell says nothing about the other two.
        "transfers_to_ab_scene": False,
        "comparable_to": f"readings at n={n} only (D-019(b))",
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
