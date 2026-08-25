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
* every run still **arrives** at the goal — xy *and* yaw, at some step, not the
  final step's xy alone (:func:`completes`; Q-146),
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

from eval.mppi_sandbox.freeze_price import (FREEZING_SCENE, freeze_duration,
                                            freeze_duration_before)

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
#:
#: Extended to `3e5` / `1e6` (D-246) because at :data:`PAIRED_LAM` the grid was
#: **still improving at its top cell** and `NONE_ADMISSIBLE_TREND_OPEN` said so.
#: The extension closed it, and in the direction nobody extrapolated: exceedance
#: **turns around** — `3e4 -> 8/12`, `1e5 -> 6/12`, `3e5 -> 12/12`, `1e6 -> 12/12`
#: — so `1e5` is an interior minimum and pricing progress harder makes the
#: freezing *worse*. The grid now measures failure on both sides of its best
#: cell, which is what :func:`optimum_is_bracketed` reports and what makes the
#: `NONE_ADMISSIBLE` at this temperature a result rather than a stopping point.
GRID = (0.0, 1e2, 3e2, 1e3, 3e3, 1e4, 3e4, 1e5, 3e5, 1e6)

#: Clearance regressions smaller than this are not called regressions (metres).
#: Same constant `three_arm` uses for the same purpose.
EPS_CLEARANCE = 1e-6

#: The two stall readings a cell carries, and the axis every verdict below is
#: now taken along.
#:
#: * :data:`SCOPE_BEFORE` — longest stall within `t <= arrival`. **The reading a
#:   freeze claim on this scene needs**, and the default, because the scene
#:   simulates ~10x past arrival (D-248).
#: * :data:`SCOPE_WHOLE` — longest stall over the whole trajectory. What
#:   `freeze_duration` returns and what D-244/D-245/D-246 graded. Kept, not
#:   deleted, so those decisions' numbers reproduce from this module rather than
#:   only from their journals.
#:
#: Both come off the **same** simulation, so a cell cannot improve one reading
#: in a pass the other was not taken in — the module's discipline (1), applied
#: to the scope axis.
SCOPE_BEFORE = "before"
SCOPE_WHOLE = "whole"
SCOPES = (SCOPE_BEFORE, SCOPE_WHOLE)

#: Default scope for every verdict. `before`, because D-248 measured the
#: whole-trajectory reading on this scene to be **99.1-99.9 % post-arrival
#: idling** — grading a finished run for sitting at the goal it reached. A
#: caller who wants D-246's numbers asks for :data:`SCOPE_WHOLE` by name.
DEFAULT_SCOPE = SCOPE_BEFORE

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
    longest: tuple[float, ...]      # [s] per seed, seed-ordered — WHOLE traj
    clearance: tuple[float, ...]    # [m] per seed, same runs
    reached: tuple[bool, ...]
    limit: float
    #: [s] per seed, longest stall within `t <= arrival` — the `before` scope.
    #: Defaults to `longest` so a cell built by an older caller reads as the
    #: whole-trajectory cell it is, rather than silently claiming an
    #: arrival-scoped reading it never took.
    longest_before: tuple[float, ...] = ()
    #: First-arrival time [s] per seed, `None` where the run never arrived.
    #: Carried because it is what makes `longest_before` *checkable*: a cell
    #: whose runs never arrive has `before == whole` by construction, and
    #: without this column that identity is invisible on the page.
    arrival: tuple[float | None, ...] = ()

    def __post_init__(self) -> None:
        if not self.longest_before:
            object.__setattr__(self, "longest_before", self.longest)
        if not self.arrival:
            object.__setattr__(self, "arrival", (None,) * len(self.longest))

    @property
    def n(self) -> int:
        return len(self.longest)

    def longest_in(self, scope: str = DEFAULT_SCOPE) -> tuple[float, ...]:
        """Per-seed longest stall under `scope`. See :data:`SCOPES`."""
        if scope == SCOPE_BEFORE:
            return self.longest_before
        if scope == SCOPE_WHOLE:
            return self.longest
        raise ValueError(f"unknown scope {scope!r}; expected one of {SCOPES}")

    def n_exceed_in(self, scope: str = DEFAULT_SCOPE) -> int:
        """Runs breaching `limit` under `scope`."""
        return int(sum(1 for x in self.longest_in(scope) if x > self.limit))

    def median_longest_in(self, scope: str = DEFAULT_SCOPE) -> float:
        vals = self.longest_in(scope)
        return float(np.median(vals)) if vals else float("nan")

    @property
    def n_exceed(self) -> int:
        """Whole-trajectory exceedance — D-244/D-245/D-246's quantity.

        Deliberately **not** re-pointed at the `before` scope. Those decisions
        quote this number, and a property that silently changed meaning would
        rewrite their arithmetic in place instead of correcting it in the open.
        Verdicts default to `before` via :data:`DEFAULT_SCOPE`; this stays put.
        """
        return self.n_exceed_in(SCOPE_WHOLE)

    @property
    def n_exceed_before(self) -> int:
        return self.n_exceed_in(SCOPE_BEFORE)

    @property
    def n_arrived(self) -> int:
        """Runs with a first-arrival time — **not** :attr:`n_reached`.

        The two disagree on this grid and the gap is not noise: `ab.reached_goal`
        tests the **final** timestep's xy against the scene's tolerance, while
        `path_tracking_metrics.time_to_goal` tests xy **and yaw** at *any* step.
        At `w_freeze = 1e6` every run is `reached` and **none** arrives — parked
        on the goal, never at the goal heading. Carried so an arrival-scoped
        exceedance can be read against the number of runs it was actually
        measurable on (Q-146).
        """
        return int(sum(1 for a in self.arrival if a is not None))

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
                f"exceed before {self.n_exceed_before:2d}/{self.n:2d} "
                f"(whole {self.n_exceed:2d}/{self.n:2d})  "
                f"median longest {self.median_longest_in():5.2f}s  "
                f"arrived {self.n_arrived:2d}/{self.n:2d}  "
                # 4 decimals: at EPS_CLEARANCE the third admissibility clause
                # turns on differences a 3-decimal print renders as a tie, which
                # is how a knife edge and a plateau look identical on the page.
                f"worst clear {self.worst_clearance:7.4f}m  "
                f"reached {self.n_reached:2d}/{self.n:2d}")


def completes(cell: WeightCell) -> bool:
    """Admissibility's completion clause — stated once, read by two callers.

    `n_arrived`, not `n_reached` (Q-146). The two disagree on this grid and the
    gap is structural: `ab.reached_goal` tests the **final** timestep's xy,
    while `path_tracking_metrics.time_to_goal` tests xy **and yaw** at *any*
    step. A run parked on the goal at the wrong heading is `reached` and never
    `arrived` — at `w_freeze = 1e6`, 12/12 and 0/12 respectively.

    **Measured: on the D-250 grid this changes no cell and no verdict** (D-254).
    Q-146 predicted the censored cells would move; they do not, and the reason
    is worth keeping. `freeze_duration_before` defines `arrival = None` to mean
    `before == whole`, so a never-arriving run is scored on its *whole*
    trajectory — and on this scene that reading is large, so clause 1 convicts
    `1e5`/`3e5`/`1e6` (1, 11, 12 of 12 exceeding) before completion is ever
    consulted. The two clauses are **correlated here, not independent**, which is
    exactly why the wrong predicate was invisible for four cycles.

    The residual the fix does remove is a cell clause 1 cannot reach: runs that
    **never stall and never arrive** — smooth all the way, ending on the goal's
    xy at the wrong heading. There `before == whole` is small, clearance is fine,
    and `n_reached` certified it complete. That cell is admissible under the old
    predicate and inadmissible under this one; it is not on the current grid, so
    this is a latent-correctness fix rather than a result.

    A function rather than an inlined comparison because :func:`verdict` applies
    the same clause to the baseline for `NO_FREEZE_TO_PRICE`; two spellings is
    how a fix reaches one caller and leaves the other reading the old predicate
    (D-047's one-statement rule).
    """
    return cell.n_arrived == cell.n


def admissible(cell: WeightCell, base: WeightCell,
               eps: float = EPS_CLEARANCE,
               scope: str = DEFAULT_SCOPE) -> bool:
    """All three clauses of the module docstring, on the full ensemble."""
    return (cell.n_exceed_in(scope) == 0
            and completes(cell)
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
    from eval.path_tracking_metrics import Goal, time_to_goal

    scen = load_scenario(scene)
    limit = scene_limit(scene)
    if scen.goal is None:
        raise ValueError(f"{scene} declares no goal — the arrival-scoped "
                         "stall is undefined without one")
    goal = Goal(*scen.goal)
    # Named at the call site, not closed over: `default_lam_sites` is a static
    # detector and would bill a closured temperature as DEFAULTS (three_arm.walk
    # carries the same note for the same reason).
    params = MPPIParams(lam=lam)
    cells = []
    for w in weights:
        runs = seed_sweep(scen, arm, seeds=seeds, params=params,
                          w_freeze=float(w))
        arrivals = tuple(time_to_goal(r.traj, goal) for r in runs)
        cells.append(WeightCell(
            w_freeze=float(w),
            longest=tuple(freeze_duration(r.traj, scen.waypoints)
                          for r in runs),
            clearance=tuple(r.clearance for r in runs),
            reached=tuple(bool(r.reached_goal) for r in runs),
            limit=limit,
            # Same run, same function, different rows — see
            # `freeze_price.freeze_duration_before`.
            longest_before=tuple(
                freeze_duration_before(r.traj, scen.waypoints, a)
                for r, a in zip(runs, arrivals)),
            arrival=arrivals,
        ))
    return tuple(cells)


def admissible_mask(cells: Sequence[WeightCell],
                    eps: float = EPS_CLEARANCE,
                    scope: str = DEFAULT_SCOPE) -> tuple[bool, ...]:
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
    return (False,) + tuple(admissible(c, base, eps, scope) for c in cells[1:])


def trend_is_open(cells: Sequence[WeightCell],
                  scope: str = DEFAULT_SCOPE) -> bool:
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

    **The open trend was then closed, and it did not resolve the way the
    extrapolation read** (D-246): `3e5` and `1e6` are both `12/12`, so the
    improvement reverses rather than continuing and `1e5` is an interior
    minimum. Worth stating plainly because it is the case *against* reading
    this predicate as a forecast — it says "the grid ended mid-slope", never
    "the next cell will be better". Use :func:`optimum_is_bracketed` for the
    complementary reading, which is what licenses a `NONE_ADMISSIBLE`.

    Read off `n_exceed` rather than clearance because `n_exceed` is the clause
    that is failing: at `PAIRED_LAM` every grid cell fails clause 1, so the
    clearance clause is never the binding one and a clearance trend would be
    reporting on a constraint that is not active.
    """
    if len(cells) < 2:
        return False
    return cells[-1].n_exceed_in(scope) < cells[-2].n_exceed_in(scope)


def optimum_is_bracketed(cells: Sequence[WeightCell],
                         scope: str = DEFAULT_SCOPE) -> bool:
    """Did the grid measure failure **above** its best cell, not just at it?

    The question a `NONE_ADMISSIBLE` has to answer to be a result: "no weight
    buys the freeze" is only licensed if the sweep walked *past* the best cell
    and watched it get worse. If the best cell is the last one taken, the grid
    stopped at the optimum and everything above it is unmeasured.

    Strictly stronger than ``not trend_is_open`` (D-246), which is why both
    exist. :func:`trend_is_open` compares the top **two** cells and so only
    fires on a *strict* improvement; a grid whose exceedance goes ``8, 6, 6``
    ends flat, reads closed there, and is still short — its best cell is its
    last. This reads the whole candidate range against the top cell and catches
    that.

    Measured shape at :data:`PAIRED_LAM` (D-246), which is why this is not
    hypothetical: ``8/12 -> 6/12 -> 12/12 -> 12/12`` over
    ``3e4, 1e5, 3e5, 1e6``. The optimum is interior, both flanks fail, and the
    curve is **non-monotone** — so "walk up until it stops improving" is not a
    valid stopping rule for this sweep and this is the reading that replaces it.

    The ablation (``cells[0]``) is excluded: it is the denominator, not a
    candidate, and it anchors the bottom of the range by construction.
    """
    if len(cells) < 3:
        return False
    candidates = cells[1:]
    best = min(c.n_exceed_in(scope) for c in candidates)
    return best < candidates[-1].n_exceed_in(scope)


def verdict(cells: Sequence[WeightCell],
            eps: float = EPS_CLEARANCE,
            scope: str = DEFAULT_SCOPE) -> str:
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
    if base.n_exceed_in(scope) == 0 and completes(base):
        return "NO_FREEZE_TO_PRICE"

    mask = admissible_mask(cells, eps, scope)
    idx = [i for i, ok in enumerate(mask) if ok]
    if not idx:
        return ("NONE_ADMISSIBLE_TREND_OPEN" if trend_is_open(cells, scope)
                else "NONE_ADMISSIBLE")
    if idx[-1] == len(cells) - 1:
        return "EDGE_OPEN"
    if idx != list(range(idx[0], idx[-1] + 1)):
        return "FRAGMENTED"
    if len(idx) == 1:
        return "KNIFE_EDGE"
    return f"PLATEAU width={len(idx)}"


def verdict_ladder(cells: Sequence[WeightCell],
                   epsilons: Sequence[float] = EPS_LADDER,
                   scope: str = DEFAULT_SCOPE) -> dict[float, str]:
    """The verdict at each clearance tolerance, off **one** set of cells.

    Free: the runs are already taken, and only the third admissibility clause
    reads `eps`. This is the cheap half of the plateau question — whether an
    apparent knife edge is a real one or a weight disqualified by a clearance
    difference smaller than the sandbox resolves.
    """
    return {float(e): verdict(cells, eps=e, scope=scope) for e in epsilons}


def verdict_is_threshold_robust(cells: Sequence[WeightCell],
                                epsilons: Sequence[float] = EPS_LADDER,
                                scope: str = DEFAULT_SCOPE) -> bool:
    """True when every rung agrees. A False here is not a failure — it is the
    finding, and it says the verdict must be quoted with its tolerance."""
    return len(set(verdict_ladder(cells, epsilons, scope).values())) == 1


def scope_disagrees(cells: Sequence[WeightCell],
                    eps: float = EPS_CLEARANCE) -> bool:
    """Do the two scopes reach **different verdicts** on the same runs?

    The reading D-248 turned into a predicate. When this is True, one of the
    two verdicts is grading post-arrival idling, and which one is not a matter
    of opinion: `before` is the freeze, `whole` is the freeze plus however long
    the harness kept simulating a finished run.

    True on this scene's grid at :data:`PAIRED_LAM` — `NO_FREEZE_TO_PRICE`
    against D-246's `NONE_ADMISSIBLE` — which is the whole content of the
    re-read. Exposed as a function so a *future* scene's grid announces the
    same contamination without anyone re-deriving it by hand.
    """
    return (verdict(cells, eps, SCOPE_BEFORE)
            != verdict(cells, eps, SCOPE_WHOLE))


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
    ap.add_argument("--scope", choices=SCOPES, default=DEFAULT_SCOPE)
    args = ap.parse_args(argv)

    cells = sweep(args.scene, args.arm, weights=args.weights,
                  seeds=tuple(range(args.seeds)), lam=args.lam)
    mask = admissible_mask(cells, scope=args.scope)
    print(f"freeze_weight — {args.scene} arm={args.arm} "
          f"n={args.seeds} lam={args.lam} limit={cells[0].limit}s "
          f"scope={args.scope}\n")
    for cell, ok in zip(cells, mask):
        tag = "ADMISSIBLE" if ok else ("ablation" if cell.w_freeze == 0 else "")
        print(f"  {cell}  {tag}")
    print(f"\n  verdict: {verdict(cells, scope=args.scope)}")
    for eps, v in verdict_ladder(cells, scope=args.scope).items():
        print(f"    eps={eps:<8g} {v}")
    print(f"  threshold-robust: "
          f"{verdict_is_threshold_robust(cells, scope=args.scope)}")
    # The re-read's headline, printed unconditionally: a grid whose two scopes
    # disagree has one verdict that is grading post-arrival idling.
    print(f"  scope disagreement: {scope_disagrees(cells)}  "
          f"(before={verdict(cells, scope=SCOPE_BEFORE)} | "
          f"whole={verdict(cells, scope=SCOPE_WHOLE)})")
    # Printed beside the verdict because it is what says whether the verdict is
    # an answer or a stopping point — a `NONE_ADMISSIBLE` read off an
    # unbracketed grid is the over-claim D-245 split the enum to prevent.
    print(f"  optimum bracketed: "
          f"{optimum_is_bracketed(cells, scope=args.scope)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
