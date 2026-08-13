# SPDX-License-Identifier: BSD-3-Clause
"""Does `w_freeze`'s optimum have a **width**, or is it one lucky grid point?

D-243 priced the freeze into the planner and hit STATE's target on the arm that
was failing: `social_mppi` at `w_freeze = 1e4` went from 2/3 to 0/3 runs
exceeding `cafe_freezing_v0`'s declared 2.0 s limit, worst-case clearance
0.965 -> 0.985 m. It also recorded that the weight is **not monotone** — `1e2`
was worse than not wiring the term at all (3/3) and `1e5` bought the freeze back
while collapsing clearance to 0.844.

That leaves the setting standing on an interior optimum read off **four** grid
points at **n=3**, which is the weakest part of the claim and STATE's stated
bottleneck. This module answers the narrower question that actually decides
whether `1e4` is quotable:

    is the admissible set a contiguous **plateau** several grid points wide,
    or a single **knife-edge** cell with failure on both sides?

A plateau is a setting. A knife-edge at n=3 is a seed artifact until proven
otherwise, and the honest response to one is to widen the seed ensemble rather
than quote the centre.

What this module does differently from D-243's sweep
----------------------------------------------------
1. **One simulation, both readings.** D-243 read freeze and clearance from
   separate passes. `ab.run_arm` returns the trajectory *and* the clearance it
   was scored at, so `freeze_duration` is computed from the same run whose
   clearance is reported. A weight that buys freeze by paying clearance cannot
   hide in the gap between two sweeps.
2. **Paired seeds, n=12.** `ab.seed_sweep` keeps runs seed-ordered, so every
   weight is scored on the *same* twelve seeds and the comparison against the
   `w_freeze = 0` baseline is paired by construction (`ab.paired_delta`).
3. **The limit is read, not typed.** `LIMIT` comes from the scene's own
   `acceptance.freeze_duration_max`, the same key `run.check_acceptance` grades
   against — the D-243 discipline of importing the constant rather than
   respelling it, applied one level up.

Admissibility
-------------
A weight is **admissible** when all three hold on the full seed ensemble:

* no run exceeds the scene's declared `freeze_duration_max`,
* every run still reaches the goal,
* worst-case clearance is not below the `w_freeze = 0` baseline's, beyond
  :data:`EPS_CLEARANCE`.

The third clause is what makes the reading a *price* and not a score: a term
that removes the freeze by driving through the pedestrian has not solved the
problem the scene poses, and D-243's `1e5` cell is exactly that failure.

Deliberately **not** decided here: which admissible weight to ship. This module
reports the shape of the admissible set; naming a default is a separate call
that should be made against a plateau, not against a verdict.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from eval.mppi_sandbox.freeze_price import FREEZING_SCENE, freeze_duration

#: The arm D-243 measured. Any arm inheriting `StockMPPI` carries `w_freeze`.
ARM = "social_mppi"

#: The temperature D-243's cell was measured at — `StockMPPI`'s shipped default,
#: reached by passing no `params` at all. Every number in D-243 is this lam.
D243_LAM = 0.1

#: The temperature the branch's *paired* comparisons run at (`three_arm.LAM`,
#: the lam `calibrate_lam` admitted). STATE asked for the freeze result at
#: "n=12, matched λ" — meaning this one.
#:
#: **The two are not interchangeable and this module is how that was found.**
#: `social_mppi` on `cafe_freezing_v0`, seeds 0/1, longest along-path stall:
#: `3.30 / 1.70 s` at :data:`D243_LAM`, and `81.90 / 71.70 s` at
#: :data:`PAIRED_LAM` — 40x the scene's declared 2.0 s limit, 90% of the run
#: spent stalled, and `reached` still true on both (so `three_arm`'s
#: completion-based freeze detector stays blind, exactly as D-241 recorded).
#: A `w_freeze` cell is therefore quotable only *with* its temperature; the
#: default here is D-243's so that re-reading its claim reproduces its numbers,
#: not so that 0.1 is endorsed.
PAIRED_LAM = 0.8

#: Default for :func:`sweep` — see the note on :data:`PAIRED_LAM`.
LAM = D243_LAM

#: n=12. `ab.seed_sweep` preserves order, so every weight sees the same twelve.
SEEDS = tuple(range(12))

#: Log grid, refined 3x between the two D-243 points that bracket its optimum
#: (`1e3` -> 1/3 exceed, `1e5` -> 3/3). `0.0` is the ablation and must lead:
#: every other cell is denominated against it.
GRID = (0.0, 1e2, 3e2, 1e3, 3e3, 1e4, 3e4, 1e5)

#: Clearance regressions smaller than this are not called regressions (metres).
#: Same constant `three_arm` uses for the same purpose.
EPS_CLEARANCE = 1e-6

#: `three_arm.EPS_LADDER`, and it is load-bearing here for the same reason it is
#: there: at `EPS_CLEARANCE` a **sub-millimetre** clearance wobble convicts a
#: weight, so a verdict taken at one tolerance is a claim about the tolerance as
#: much as about the weight. :func:`verdict_ladder` reports the verdict at each
#: rung off one set of cells — no re-simulation — and
#: :func:`verdict_is_threshold_robust` says whether the answer survived the walk.
EPS_LADDER = (EPS_CLEARANCE, 1e-3, 1e-2, 5e-2)


def scene_limit(scene: str = FREEZING_SCENE) -> float:
    """The scene's own `freeze_duration_max`, in seconds.

    Read rather than typed: this is the number `run.check_acceptance` grades
    against, so a scene that re-tunes its limit re-tunes this sweep with it.
    """
    from eval.mppi_sandbox.scenario import load_scenario

    acceptance = load_scenario(scene).acceptance
    if "freeze_duration_max" not in acceptance:
        raise ValueError(f"{scene} declares no freeze_duration_max — "
                         "this sweep has nothing to grade against")
    return float(acceptance["freeze_duration_max"])


@dataclass(frozen=True)
class WeightCell:
    """One `w_freeze` value, scored on the whole seed ensemble."""

    w_freeze: float
    longest: tuple[float, ...]      # [s] per seed, seed-ordered
    clearance: tuple[float, ...]    # [m] per seed, same runs
    reached: tuple[bool, ...]
    limit: float

    @property
    def n(self) -> int:
        return len(self.longest)

    @property
    def n_exceed(self) -> int:
        return int(sum(1 for x in self.longest if x > self.limit))

    @property
    def n_reached(self) -> int:
        return int(sum(1 for r in self.reached if r))

    @property
    def worst_clearance(self) -> float:
        return float(min(self.clearance)) if self.clearance else float("nan")

    @property
    def median_longest(self) -> float:
        return float(np.median(self.longest)) if self.longest else float("nan")

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"w_freeze {self.w_freeze:8.0f}  "
                f"exceed {self.n_exceed:2d}/{self.n:2d}  "
                f"median longest {self.median_longest:5.2f}s  "
                # 4 decimals: at EPS_CLEARANCE the third admissibility clause
                # turns on differences a 3-decimal print renders as a tie, which
                # is how a knife edge and a plateau look identical on the page.
                f"worst clear {self.worst_clearance:7.4f}m  "
                f"reached {self.n_reached:2d}/{self.n:2d}")


def admissible(cell: WeightCell, base: WeightCell,
               eps: float = EPS_CLEARANCE) -> bool:
    """All three clauses of the module docstring, on the full ensemble."""
    return (cell.n_exceed == 0
            and cell.n_reached == cell.n
            and cell.worst_clearance >= base.worst_clearance - eps)


def sweep(scene: str = FREEZING_SCENE, arm: str = ARM, *,
          weights: Sequence[float] = GRID,
          seeds: Sequence[int] = SEEDS,
          lam: float = LAM) -> tuple[WeightCell, ...]:
    """Run `arm` on `scene` at every weight, paired across `seeds`.

    Freeze and clearance come from the **same** run — `ab.run_arm` hands back
    the trajectory it scored — so no weight can improve one reading in a pass
    the other reading was not taken in.
    """
    from eval.mppi_sandbox.ab import seed_sweep
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
    from eval.mppi_sandbox.scenario import load_scenario

    scen = load_scenario(scene)
    limit = scene_limit(scene)
    # Named at the call site, not closed over: `default_lam_sites` is a static
    # detector and would bill a closured temperature as DEFAULTS (three_arm.walk
    # carries the same note for the same reason).
    params = MPPIParams(lam=lam)
    cells = []
    for w in weights:
        runs = seed_sweep(scen, arm, seeds=seeds, params=params,
                          w_freeze=float(w))
        cells.append(WeightCell(
            w_freeze=float(w),
            longest=tuple(freeze_duration(r.traj, scen.waypoints)
                          for r in runs),
            clearance=tuple(r.clearance for r in runs),
            reached=tuple(bool(r.reached_goal) for r in runs),
            limit=limit,
        ))
    return tuple(cells)


def admissible_mask(cells: Sequence[WeightCell],
                    eps: float = EPS_CLEARANCE) -> tuple[bool, ...]:
    """Per-cell admissibility against `cells[0]`, which must be the ablation.

    The ablation is denominator, not candidate: it is the state the term is
    supposed to improve on, so it is excluded from the admissible set even when
    it happens to satisfy the clauses. A run where it does satisfy them means
    the scene is not freezing this arm at all, and `verdict` says so.
    """
    if not cells:
        return ()
    if cells[0].w_freeze != 0.0:
        raise ValueError("cells[0] must be the w_freeze = 0 ablation; "
                         f"got {cells[0].w_freeze}")
    base = cells[0]
    return (False,) + tuple(admissible(c, base, eps) for c in cells[1:])


def trend_is_open(cells: Sequence[WeightCell]) -> bool:
    """Is the exceedance count **still falling** at the top of the grid?

    The distinction this exists for, found by running the sweep at
    :data:`PAIRED_LAM`: an empty admissible set has two very different causes,
    and the bare ``NONE_ADMISSIBLE`` string cannot tell them apart.

    * The grid was walked and every weight *measurably* failed — the term does
      not buy the freeze at any tested strength. A result.
    * The grid **ended while the term was still working**. At `lam = 0.8` the
      top three cells run `1e4 -> 12/12`, `3e4 -> 8/12`, `1e5 -> 6/12` exceed:
      nothing is admissible, but the last cell is the best one measured and
      the next one up was never taken. That is not "no weight works", it is
      "the grid stops here", and quoting the former from the latter is the
      same over-claim `EDGE_OPEN` already guards on the admissible side.

    Read off `n_exceed` rather than clearance because `n_exceed` is the clause
    that is failing: at `PAIRED_LAM` every grid cell fails clause 1, so the
    clearance clause is never the binding one and a clearance trend would be
    reporting on a constraint that is not active.
    """
    if len(cells) < 2:
        return False
    return cells[-1].n_exceed < cells[-2].n_exceed


def verdict(cells: Sequence[WeightCell],
            eps: float = EPS_CLEARANCE) -> str:
    """The shape of the admissible set — the question this module exists for.

    * ``NO_FREEZE_TO_PRICE`` — the ablation already passes; nothing to buy, and
      any apparent optimum is measuring noise. Checked **first**: every other
      verdict presumes the baseline fails.
    * ``NONE_ADMISSIBLE`` — no weight clears all three clauses, and the grid
      does not end mid-improvement, so the failure is measured rather than
      merely unreached.
    * ``NONE_ADMISSIBLE_TREND_OPEN`` — no weight is admissible **but the top
      cell is still improving on its neighbour**, so the grid ran out before
      the question was answered. See :func:`trend_is_open`.
    * ``PLATEAU width=N`` — N >= 2 contiguous admissible grid points. A setting.
    * ``KNIFE_EDGE`` — exactly one, with measured failure on both sides.
    * ``EDGE_OPEN`` — the admissible set touches the top of the grid, so its
      upper end is unmeasured; widen before quoting a centre.
    * ``FRAGMENTED`` — admissible cells with an inadmissible gap between them.
      Either genuinely multi-modal or seed noise; both mean n=12 is not enough.
    """
    if not cells:
        return "NONE_ADMISSIBLE"
    base = cells[0]
    if base.n_exceed == 0 and base.n_reached == base.n:
        return "NO_FREEZE_TO_PRICE"

    mask = admissible_mask(cells, eps)
    idx = [i for i, ok in enumerate(mask) if ok]
    if not idx:
        return ("NONE_ADMISSIBLE_TREND_OPEN" if trend_is_open(cells)
                else "NONE_ADMISSIBLE")
    if idx[-1] == len(cells) - 1:
        return "EDGE_OPEN"
    if idx != list(range(idx[0], idx[-1] + 1)):
        return "FRAGMENTED"
    if len(idx) == 1:
        return "KNIFE_EDGE"
    return f"PLATEAU width={len(idx)}"


def verdict_ladder(cells: Sequence[WeightCell],
                   epsilons: Sequence[float] = EPS_LADDER
                   ) -> dict[float, str]:
    """The verdict at each clearance tolerance, off **one** set of cells.

    Free: the runs are already taken, and only the third admissibility clause
    reads `eps`. This is the cheap half of the plateau question — whether an
    apparent knife edge is a real one or a weight disqualified by a clearance
    difference smaller than the sandbox resolves.
    """
    return {float(e): verdict(cells, eps=e) for e in epsilons}


def verdict_is_threshold_robust(cells: Sequence[WeightCell],
                                epsilons: Sequence[float] = EPS_LADDER
                                ) -> bool:
    """True when every rung agrees. A False here is not a failure — it is the
    finding, and it says the verdict must be quoted with its tolerance."""
    return len(set(verdict_ladder(cells, epsilons).values())) == 1


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=FREEZING_SCENE)
    ap.add_argument("--arm", default=ARM)
    ap.add_argument("--seeds", type=int, default=len(SEEDS))
    ap.add_argument("--weights", type=float, nargs="+", default=list(GRID))
    # Named, not defaulted: `--lam PAIRED_LAM` is the whole next reading, and a
    # CLI that only *prints* its temperature reads as DEFAULTS to
    # `default_lam_sites` — which is the same criticism, mechanised.
    ap.add_argument("--lam", type=float, default=LAM)
    args = ap.parse_args(argv)

    cells = sweep(args.scene, args.arm, weights=args.weights,
                  seeds=tuple(range(args.seeds)), lam=args.lam)
    mask = admissible_mask(cells)
    print(f"freeze_weight — {args.scene} arm={args.arm} "
          f"n={args.seeds} lam={args.lam} limit={cells[0].limit}s\n")
    for cell, ok in zip(cells, mask):
        tag = "ADMISSIBLE" if ok else ("ablation" if cell.w_freeze == 0 else "")
        print(f"  {cell}  {tag}")
    print(f"\n  verdict: {verdict(cells)}")
    for eps, v in verdict_ladder(cells).items():
        print(f"    eps={eps:<8g} {v}")
    print(f"  threshold-robust: {verdict_is_threshold_robust(cells)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
