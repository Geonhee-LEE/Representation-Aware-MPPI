# SPDX-License-Identifier: BSD-3-Clause
"""Does the arm separation in first-arrival time survive the paired protocol?

STATE #1. D-247 shipped `time_to_goal` (first-arrival time) to grade
`cafe_freezing_v0`'s declared `time_to_goal_max`, and noticed something it was
not built for: the three arms' arrival times **do not overlap** at n=3 —
`stock_mppi` 7.4–7.8 s, `social_mppi` 8.8–9.0 s, `risk_mppi` 9.0–9.1 s — while
the same runs' `duration_s` ranges overlap heavily. That is the shape
`research/feed.md`'s DRA-MPPI entry (2026-08-13 20:00) prescribes: price the
freeze as a **duration regression at matched safety**, not with a predicate.

D-247 declined to quote the ranking, on the grounds that n=3 does not license
one (D-235; and D-241 recorded n=1 inverting a ranking on this same scene).
This module takes the reading that does.

Two things change at once, and that is the whole design
------------------------------------------------------

D-247's numbers came from `freeze_price.profile_arm`, which passes no `params`
— so they are at the **shipped `lam = 0.1`**, exactly the trap D-244 found in
D-243's `w_freeze` cells. The paired protocol this module is asked to apply runs
at :data:`three_arm.LAM` = 0.8. So "widen D-247 to the paired protocol" moves
**n from 3 to 12 and λ from 0.1 to 0.8 in the same step**, and a difference
between the two readings would be unattributable.

:func:`walk` therefore measures **both** temperatures over the same twelve
seeds. The λ = 0.1 column is D-247's own condition at n = 12 (does the
separation survive the seeds alone?); the λ = 0.8 column is the branch's paired
condition (does it survive the temperature the comparisons actually run at?).
Each is a paired comparison in its own right, and the pair of them is what makes
either one readable.

Censoring is the failure mode this metric has and clearance does not
--------------------------------------------------------------------

`time_to_goal` is `None` when a run never arrives, and at `lam = 0.8` this scene
is known to stall `social_mppi` for ~80 s (D-244). A mean taken over the runs
that *did* arrive is therefore biased **fast**, and biased fast precisely in the
arm that froze — the frozen seeds leave the average rather than lengthening it.
That is the arrival-time face of the `BOUGHT_WITH_FREEZE` trap `three_arm`
guards on the clearance side, and it is worse here: a freeze makes clearance
look *good*, but it makes arrival time look good by **disappearing**.

So :class:`ArrivalComparison` refuses before it reports. Any `None` on either
side of the pair and every statistic is withheld behind
:data:`ARRIVAL_CENSORED` — not dropped, not imputed, not `inf`. The count of
arrivals is reported beside the verdict so the refusal is legible.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

from eval.mppi_sandbox.freeze_price import FREEZING_SCENE
from eval.mppi_sandbox.run import SIM_DT

#: D-247's three arms, in the order it reported them. `stock_mppi` leads because
#: it is the denominator every comparison here is taken against.
ARMS = ("stock_mppi", "social_mppi", "risk_mppi")

#: The arm the others are denominated against.
BASE_ARM = ARMS[0]

#: n=12, D-235's protocol. `ab.seed_sweep` preserves order, so every arm at
#: every temperature sees the same twelve seeds at the same indices — which is
#: what makes the differences below paired rather than merely simultaneous.
SEEDS = tuple(range(12))

#: The temperature D-247's separation was measured at — `StockMPPI`'s shipped
#: default, reached by passing no `params`. Named, not inherited, so this
#: module's own reading of D-247 is reproducible against its numbers.
D247_LAM = 0.1

#: The temperature the branch's paired comparisons run at (`three_arm.LAM`).
PAIRED_LAM = 0.8

#: Both, walked over one seed ensemble. The order is the order they are
#: reported in and is chosen so the *reproduction* column comes first.
LAMS = (D247_LAM, PAIRED_LAM)

#: Tie band for the sign test (seconds). **Half** a simulator step, and derived
#: from `run.SIM_DT` rather than typed so the two cannot drift apart (D-241's
#: pattern, pinned by test).
#:
#: First-arrival time is a trajectory *timestamp*, so it is quantised to
#: `SIM_DT` exactly: every non-zero difference between two arrivals is at least
#: one full step. A half-step band therefore admits **only exact ties** while
#: staying safe against float representation of the timestamps — it is not a
#: materiality threshold, and nothing here grades an arm against it.
EPS_ARRIVAL_S = SIM_DT / 2.0

ARRIVAL_CENSORED = "ARRIVAL_CENSORED"
SEPARATED_SLOWER = "SEPARATED_SLOWER"
SEPARATED_FASTER = "SEPARATED_FASTER"
NOT_SEPARATED = "NOT_SEPARATED"


@dataclass(frozen=True)
class ArmArrivals:
    """One arm, one temperature, first-arrival time on every seed.

    `arrivals[i]` is `None` exactly when seed `SEEDS[i]` never reached the goal
    — the same predicate `goal_reached` uses, pinned to it by test in
    `test_time_to_goal`. Storing the `None` rather than filtering it is what
    lets :class:`ArrivalComparison` see the censoring at all.
    """

    arm: str
    lam: float
    seeds: tuple[int, ...]
    arrivals: tuple[float | None, ...]

    def __post_init__(self) -> None:
        if len(self.seeds) != len(self.arrivals):
            raise ValueError(
                f"{self.arm} lam={self.lam:g}: {len(self.seeds)} seeds against "
                f"{len(self.arrivals)} arrivals — the readings are paired by "
                "seed index, so unequal lengths mean the pairing is not what "
                "this class assumes")
        if not self.seeds:
            raise ValueError("an arm reading needs at least one seed")

    @property
    def n(self) -> int:
        return len(self.seeds)

    @property
    def n_arrived(self) -> int:
        return sum(1 for a in self.arrivals if a is not None)

    @property
    def complete(self) -> bool:
        """Did every seed arrive? The precondition for any statistic here."""
        return self.n_arrived == self.n

    @property
    def span(self) -> tuple[float, float]:
        """(min, max) over the seeds that arrived — D-247's "range".

        Deliberately readable even when censored, because the span of the
        survivors is a *description* of the runs that finished and is never
        used as an arm-level claim. :attr:`ArrivalComparison.verdict` is the
        thing that refuses; this is not.
        """
        got = [a for a in self.arrivals if a is not None]
        if not got:
            raise ValueError(f"{self.arm} lam={self.lam:g}: no seed arrived — "
                             "there is no span to report")
        return (min(got), max(got))

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        if self.n_arrived == 0:
            return (f"{self.arm:12s} lam={self.lam:<4g} "
                    f"arrived {self.n_arrived:2d}/{self.n:2d}  (no arrivals)")
        lo, hi = self.span
        return (f"{self.arm:12s} lam={self.lam:<4g} "
                f"arrived {self.n_arrived:2d}/{self.n:2d}  "
                f"span {lo:6.2f}-{hi:6.2f}s")


def spans_overlap(a: ArmArrivals, b: ArmArrivals) -> bool:
    """Do the two arms' arrival spans overlap? D-247's n=3 reading, restated.

    This is the **weak** reading and is kept only so the n=12 walk can be laid
    beside the n=3 claim in the same terms it was made in. Non-overlapping
    spans of two 12-run samples is not a separation result — it is an order
    statistic with no interval on it, and it is exactly what
    :meth:`ArrivalComparison.verdict` replaces. Raises if either arm censored:
    a span over survivors cannot be compared across arms that lost different
    seeds.
    """
    for x in (a, b):
        if not x.complete:
            raise ValueError(
                f"{x.arm} lam={x.lam:g} arrived on {x.n_arrived}/{x.n} seeds — "
                "spans of different survivor sets are not comparable")
    alo, ahi = a.span
    blo, bhi = b.span
    return alo <= bhi and blo <= ahi


@dataclass(frozen=True)
class ArrivalComparison:
    """One arm against the base arm, paired by seed index at one temperature."""

    base: ArmArrivals
    arm: ArmArrivals

    def __post_init__(self) -> None:
        if self.base.seeds != self.arm.seeds:
            raise ValueError(
                f"{self.arm.arm} vs {self.base.arm}: seed ensembles differ — "
                "these readings are paired by seed index")
        if self.base.lam != self.arm.lam:
            raise ValueError(
                f"{self.arm.arm} vs {self.base.arm}: lam "
                f"{self.arm.lam:g} against {self.base.lam:g} — a paired "
                "comparison across two temperatures compares nothing")

    @property
    def n(self) -> int:
        return self.base.n

    @property
    def censored(self) -> bool:
        """Did any seed on either side fail to arrive?

        The disjunction is the point: a base seed that never arrives removes a
        *pair*, so the arm's own completeness is not sufficient.
        """
        return not (self.base.complete and self.arm.complete)

    @property
    def diffs(self) -> tuple[float, ...]:
        """Per-seed `arm - base` arrival time [s]. Raises when censored.

        Raising rather than returning the arrived subset is the whole guard:
        the subset is a well-formed list of floats that means nothing, and
        every statistic below would compute happily on it.
        """
        if self.censored:
            raise ValueError(
                f"{self.arm.arm} vs {self.base.arm} at lam={self.arm.lam:g}: "
                f"arrived {self.arm.n_arrived}/{self.n} and "
                f"{self.base.n_arrived}/{self.n} — a difference over the seeds "
                "that arrived is biased fast in whichever arm froze")
        return tuple(float(a) - float(b)
                     for b, a in zip(self.base.arrivals, self.arm.arrivals))

    @property
    def _comparison(self):
        """This pair as the branch's existing paired-bootstrap object.

        `declared_margin` / `censoring` are carried by that class for the
        threshold route and are used by **no** statistic on it, so they are
        passed neutral — the same borrow, for the same reason, that
        `paired_step.PairedStep._comparison` documents.
        """
        from eval.mppi_sandbox.margin_free import RungComparison

        if self.censored:
            raise ValueError(f"{self.arm.arm}: censored — see `diffs`")
        return RungComparison(
            scenario=FREEZING_SCENE, weight=self.arm.lam,
            declared_margin=0.0, censoring="",
            stock=tuple(float(a) for a in self.base.arrivals),
            risk=tuple(float(a) for a in self.arm.arrivals))

    @property
    def mean_step(self) -> float:
        """Mean per-seed arrival-time difference [s]. Positive = arm is slower."""
        return self._comparison.paired_delta

    def ci(self, *, reps: int = 2000, alpha: float = 0.05,
           seed: int = 0) -> tuple[float, float]:
        """Paired bootstrap CI of :attr:`mean_step`, resampling seeds."""
        return self._comparison.bootstrap_ci(reps=reps, alpha=alpha, seed=seed)

    @property
    def sign_p(self) -> float:
        """Exact two-sided sign-test p on :attr:`diffs`, ties at one step."""
        from eval.mppi_sandbox.paired_step import sign_test_p

        return sign_test_p(self.diffs, tol=EPS_ARRIVAL_S)

    @property
    def verdict(self) -> str:
        """Censoring first, then whether the paired CI excludes zero.

        Censoring outranks the interval by construction: an interval computed
        over an incomplete pairing is not a weaker answer, it is an answer to a
        different question (how fast were the runs that finished). Like
        `paired_step.PairedStep.verdict` this is a **separation** reading and
        says nothing about whether a step of this size matters to a robot.
        """
        if self.censored:
            return ARRIVAL_CENSORED
        lo, hi = self.ci()
        if lo > 0.0:
            return SEPARATED_SLOWER
        if hi < 0.0:
            return SEPARATED_FASTER
        return NOT_SEPARATED

    def __str__(self) -> str:  # pragma: no cover - formatting
        head = (f"{self.arm.arm:12s} vs {self.base.arm:12s} "
                f"lam={self.arm.lam:<4g} n={self.n:2d}  ")
        if self.censored:
            return (head + f"arrived {self.arm.n_arrived}/{self.n} vs "
                    f"{self.base.n_arrived}/{self.n}  {ARRIVAL_CENSORED}")
        lo, hi = self.ci()
        return (head + f"mean {self.mean_step:+6.2f}s "
                f"[{lo:+6.2f}, {hi:+6.2f}]  {self.verdict:18s} "
                f"p={self.sign_p:.3f}")


@dataclass(frozen=True)
class StallSplit:
    """One run's along-path stall, split at its own arrival time.

    `freeze_price.freeze_duration` measures the longest stalled episode over the
    **whole** trajectory, and this scene keeps simulating after the goal is
    reached. So a run that arrives and then sits still scores an enormous
    "freeze" for doing exactly what a finished run should do.

    That is not hypothetical on this scene: `social_mppi` seed 0 at
    :data:`PAIRED_LAM` arrives at **10.1 s**, runs to **93.1 s**, and reports a
    longest stall of **81.90 s** — of which **20 of 847** stalled steps fall
    before arrival. The number D-244/D-245/D-246 graded against the scene's
    declared 2.0 s limit is therefore dominated by post-arrival idling.

    `before` is the reading a freeze claim needs; `whole` is the one those
    decisions used. Both are carried so the gap is visible rather than swapped
    silently.
    """

    arm: str
    seed: int
    lam: float
    #: First-arrival time [s], `None` if the run never arrived.
    arrival: float | None
    #: Longest stalled episode within `t <= arrival` [s]. `whole` when the run
    #: never arrived — with no arrival there is no post-arrival phase to
    #: exclude, so the two readings coincide by construction rather than by a
    #: convention that could be mistaken for a measurement.
    before: float
    #: Longest stalled episode over the whole trajectory [s] — `freeze_duration`.
    whole: float
    #: Whole-sim duration [s], carried so `whole - arrival` is checkable.
    duration: float

    @property
    def post_arrival_share(self) -> float:
        """Fraction of `whole` that `before` does not account for.

        `0.0` for a run that never arrived (nothing is post-arrival) and for one
        whose longest episode is entirely pre-arrival. Near `1.0` is the
        contamination this class exists to surface.
        """
        if self.whole <= 0.0:
            return 0.0
        return max(0.0, (self.whole - self.before) / self.whole)

    def exceeds(self, limit: float) -> bool:
        """Does the **pre-arrival** stall breach `limit` [s]?

        Deliberately not the whole-trajectory reading: this is the predicate a
        freeze claim on this scene should have been using.
        """
        return self.before > limit

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        got = "never" if self.arrival is None else f"{self.arrival:5.1f}s"
        return (f"{self.arm:12s} seed={self.seed:2d} lam={self.lam:<4g} "
                f"arrive {got}  stall before {self.before:6.2f}s / "
                f"whole {self.whole:6.2f}s  "
                f"post-arrival share {self.post_arrival_share:5.1%}")


def stall_split(scene: str = FREEZING_SCENE, *, arm: str = BASE_ARM,
                seed: int = 0, lam: float = PAIRED_LAM) -> StallSplit:
    """Simulate one run and split its stall at its own arrival time."""
    import numpy as np

    from eval.mppi_sandbox.ab import run_arm
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
    from eval.mppi_sandbox.freeze_price import freeze_duration
    from eval.mppi_sandbox.scenario import load_scenario
    from eval.path_tracking_metrics import Goal, time_to_goal

    scen = load_scenario(scene)
    run = run_arm(scen, arm, seed, params=MPPIParams(lam=lam))
    traj = run.traj
    arrival = time_to_goal(traj, Goal(*scen.goal))
    whole = freeze_duration(traj, scen.waypoints)
    if arrival is None:
        before = whole
    else:
        # Truncate to the arrival timestep and re-read with the *same*
        # function, so `before` and `whole` cannot differ by anything except
        # the rows they were given.
        head = traj[traj[:, 0] <= arrival]
        before = (freeze_duration(head, scen.waypoints)
                  if head.shape[0] >= 2 else 0.0)
    return StallSplit(arm=arm, seed=int(seed), lam=float(lam), arrival=arrival,
                      before=float(before), whole=float(whole),
                      duration=float(traj[-1, 0]))


def stall_splits(scene: str = FREEZING_SCENE, *,
                 arms: Sequence[str] = ARMS,
                 seeds: Sequence[int] = (0, 1, 2),
                 lam: float = PAIRED_LAM) -> tuple[StallSplit, ...]:
    """:func:`stall_split` over an arm x seed grid."""
    return tuple(stall_split(scene, arm=a, seed=s, lam=lam)
                 for a in arms for s in seeds)


def sweep(scene: str = FREEZING_SCENE, *,
          arms: Sequence[str] = ARMS,
          seeds: Sequence[int] = SEEDS,
          lam: float = PAIRED_LAM) -> tuple[ArmArrivals, ...]:
    """Run every arm on `scene` at one temperature, paired across `seeds`.

    Arrival time is read off the **same** trajectory `ab.run_arm` scored, so no
    arm's arrival reading comes from a pass its completion reading did not.
    """
    from eval.mppi_sandbox.ab import seed_sweep
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams
    from eval.mppi_sandbox.scenario import load_scenario
    from eval.path_tracking_metrics import Goal, time_to_goal

    scen = load_scenario(scene)
    if scen.goal is None:
        raise ValueError(f"{scene} declares no goal — first-arrival time is "
                         "undefined without one")
    # `Goal(*scenario.goal)` is `run.run_scenario`'s own construction, and the
    # default tolerances below are `summary`'s — so an arrival read here is the
    # same number the run JSON carries and `time_to_goal_max` grades.
    goal = Goal(*scen.goal)
    # Named at the call site, not closed over: `default_lam_sites` is a static
    # detector and would bill a closured temperature as DEFAULTS.
    params = MPPIParams(lam=lam)
    out = []
    for arm in arms:
        runs = seed_sweep(scen, arm, seeds=seeds, params=params)
        out.append(ArmArrivals(
            arm=arm, lam=float(lam), seeds=tuple(int(s) for s in seeds),
            arrivals=tuple(time_to_goal(r.traj, goal) for r in runs),
        ))
    return tuple(out)


def compare(readings: Sequence[ArmArrivals],
            base_arm: str = BASE_ARM) -> tuple[ArrivalComparison, ...]:
    """Every non-base arm against the base arm, at one temperature."""
    by_arm = {r.arm: r for r in readings}
    if base_arm not in by_arm:
        raise ValueError(f"{base_arm} is not among the readings "
                         f"({', '.join(by_arm)}) — nothing to denominate against")
    base = by_arm[base_arm]
    return tuple(ArrivalComparison(base=base, arm=r)
                 for r in readings if r.arm != base_arm)


def walk(scene: str = FREEZING_SCENE, *,
         arms: Sequence[str] = ARMS,
         seeds: Sequence[int] = SEEDS,
         lams: Sequence[float] = LAMS) -> dict[float, tuple[ArmArrivals, ...]]:
    """:func:`sweep` at both temperatures — the module's actual reading.

    See the module docstring: widening D-247 moves `n` and `λ` together, so the
    two columns are what make either attributable.
    """
    return {float(lam): sweep(scene, arms=arms, seeds=seeds, lam=lam)
            for lam in lams}


def separation_survives(readings: Sequence[ArmArrivals],
                        base_arm: str = BASE_ARM) -> bool:
    """Is **every** non-base arm separated from the base at this temperature?

    D-247's claim was that the three arms' arrival times do not overlap. Its
    n=12 form is this conjunction: one unresolved or censored pair and the
    ranking is not licensed, which is the same all-or-nothing shape
    `three_arm.is_interaction` uses for the same reason.
    """
    comparisons = compare(readings, base_arm=base_arm)
    return bool(comparisons) and all(
        c.verdict in (SEPARATED_SLOWER, SEPARATED_FASTER)
        for c in comparisons)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=FREEZING_SCENE)
    ap.add_argument("--arms", nargs="+", default=list(ARMS))
    ap.add_argument("--seeds", type=int, default=len(SEEDS))
    ap.add_argument("--lams", nargs="+", type=float, default=list(LAMS))
    args = ap.parse_args(argv)

    seeds = tuple(range(args.seeds))
    print(f"arrival_spread — {args.scene}, n={len(seeds)}, "
          f"first-arrival time vs {BASE_ARM}\n")
    for lam in args.lams:
        readings = sweep(args.scene, arms=args.arms, seeds=seeds, lam=lam)
        print(f"  lam = {lam:g}")
        for r in readings:
            print(f"    {r}")
        for c in compare(readings, base_arm=args.arms[0]):
            print(f"    {c}")
        print(f"    separation_survives = "
              f"{separation_survives(readings, base_arm=args.arms[0])}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
