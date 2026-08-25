# SPDX-License-Identifier: BSD-3-Clause
"""Is the seed-level correlation between arms positive? (the feed's rider on STATE #1)

STATE's next-action #1 spends **256 rollouts** widening four excited scenes to
eight seeds. The `2026-08-19 16:00` feed entry (Pairing Seeds, `2512.24145`)
attaches a rider to that spend, and the rider is cheap enough to settle before
the rollouts are bought: paired-across-arms evaluation beats unpaired at the
same budget **iff the seed-level correlation between the two arms is positive**.
Theorem 1 there is `Var(D_pair) = Var(D_ind) - (2/n)*Cov(Y(1,s), Y(0,s))`, so
the sign of that covariance is the whole precondition, and the entry's own
limit #2 is explicit that *"negative seed-level correlation reverses the
variance comparison."*

The check costs **zero rollouts**: :data:`clearance_census.SEED_ENSEMBLE` is an
8 arm x 8 seed matrix already on disk, and a per-seed correlation is arithmetic
over it. This module is that arithmetic.

**The answer is no — not branch-wide, and the failures are not in the tail.**
Of the 26 non-degenerate arm pairs, `9` are negative, and the two most negative
are `essps_mppi` x `stock_mppi` at `-0.7402` and `gap_gated_mppi` x `stock_mppi`
at `-0.6984` — both against the **baseline**, which is the comparison
`clearance_census`'s whole deficit claim is made in. At `rho = -0.7402` the
predicted sd ratio `sqrt(1 - rho)` is `1.32`, i.e. pairing would **inflate** the
standard deviation of that difference by 32 %, not shrink it.

So the feed's transfer-risk caveat #4 is confirmed in the direction it warned
about, and then some. It read the source paper's `rho = 0.681-0.993` (an
economic ABM where two arms share nearly all dynamics) as *"a best case that our
setting will not match"* and reasoned that two MPPI arms with different cost
functions diverge trajectories, and divergence decorrelates. Measured here the
range is `-0.7402` to `+0.7963`: not merely lower, but **straddling zero**. The
rider therefore survives as a **per-pair** test and dies as a branch-wide
policy — there is no single answer to "should the 8-seed widening be reported
paired", only an answer per arm pair, and it has to be taken on the scene being
widened rather than borrowed from this one.

What the module does **not** claim, stated because the branch's habit is to
state it:

* **This is one scene.** :data:`clearance_census.SCENE_PATH` is
  `cafe_freezing_v0`, the `PEAK_SCENE`. The four scenes STATE #1 widens
  (`convoy`, `cut_in`, `head_on`, `obstacle_crossing`) are **not** measured
  here and their correlations are unknown. What carries is the *shape* of the
  finding — that the sign varies by pair — not any particular value.
* **One metric.** Clearance only. The feed entry's own caveat that `rho` is
  per-metric applies: nothing here licenses a claim about cross-track, which is
  the column D-363/D-365 actually turn on.
* **n = 8.** A correlation on eight points has a wide sampling interval and no
  confidence interval is computed. The finding rests on the **sign pattern
  across 26 pairs**, not on any single coefficient being accurate to 4 dp.
* **It does not reach D-365's decisive pair.** The feed's limit #3 already
  disqualified it: `0.1964` vs `0.1441` is cross-*scene*, and common random
  numbers need a shared draw to hold common. That gap stays open.

A by-product worth keeping: the two pairs at exactly `+1.0000` are
`geometric_mppi` x `stock_mppi` and `frozen_risk_mppi` x `risk_mppi`, which are
the two pairs `clearance_census` already pins as **reproducing each other in
every column**. Perfect seed-level correlation is the signature of an inert
channel, so this statistic detects the thing that module documents by hand — and
:data:`DEGENERATE` excludes them from the population rather than letting two
constructed `1.0`s flatter the branch-wide count.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from statistics import fmean

from .clearance_census import BASELINE, SEED_ENSEMBLE, SEEDS

#: Pairs whose two arms reproduce each other exactly on every seed, so their
#: correlation is `+1.0` by construction rather than by measurement.
#: `clearance_census` pins both as inert-channel signatures; counting them in
#: the branch-wide tally would report two identities as two successes.
DEGENERATE: tuple[tuple[str, str], ...] = (
    ("frozen_risk_mppi", "risk_mppi"),
    ("geometric_mppi", "stock_mppi"),
)

#: `sqrt(1 - rho)` is the predicted ratio of paired to independent standard
#: deviation. Above this the pairing is not worth the bookkeeping; below `1.0`
#: it helps; above `1.0` it actively hurts. Named so the verdict thresholds and
#: the docstring cannot drift apart.
NEUTRAL_SD_RATIO = 1.0


def pearson(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Seed-level Pearson correlation between two arms' clearance columns.

    Written out rather than pulled from `statistics.correlation` so the
    zero-variance case is this module's decision: an arm that clears the same
    metres on all eight seeds has no seed-level variation to correlate, and the
    honest reading is `0.0` (pairing neither helps nor hurts) rather than a
    `ZeroDivisionError` that a caller would have to guess the meaning of.
    """
    if len(a) != len(b):
        raise ValueError(f"columns differ in width: {len(a)} vs {len(b)}")
    mean_a, mean_b = fmean(a), fmean(b)
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    dev_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    dev_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    if dev_a == 0.0 or dev_b == 0.0:
        return 0.0
    return cov / (dev_a * dev_b)


@dataclass(frozen=True)
class PairReading:
    """One arm pair's precondition, graded."""

    arm_a: str
    arm_b: str
    rho: float

    @property
    def degenerate(self) -> bool:
        """Do the two arms reproduce each other, making `rho` an identity?"""
        return tuple(sorted((self.arm_a, self.arm_b))) in DEGENERATE

    @property
    def sd_ratio(self) -> float:
        """`sqrt(1 - rho)` — predicted paired/independent standard deviation.

        Theorem 1's variance identity divided through by `Var(D_ind)` and
        square-rooted. `rho > 0` puts this below `1.0` (pairing shrinks the
        interval); `rho < 0` puts it above (pairing widens it).

        Clamped at zero because the identity pairs in :data:`DEGENERATE`
        correlate to `1.0 + 2.2e-16` in float, and `(-2.2e-16) ** 0.5` is a
        **complex number** in Python, not a `ValueError` — so the unclamped
        form printed `x0.000+0.000j` rather than failing. A ratio that silently
        changes type is worse than one that raises; this is the one place the
        arithmetic can leave the reals, and it is closed here.
        """
        return max(0.0, 1.0 - self.rho) ** 0.5

    @property
    def verdict(self) -> str:
        """`DEGENERATE` | `PAIRED_HELPS` | `PAIRED_INERT` | `PAIRED_HURTS`."""
        if self.degenerate:
            return "DEGENERATE"
        if self.rho > 0.0:
            return "PAIRED_HELPS"
        if self.rho == 0.0:
            return "PAIRED_INERT"
        return "PAIRED_HURTS"


def readings() -> tuple[PairReading, ...]:
    """Every unordered arm pair in the ensemble, sorted by correlation."""
    pairs = [
        PairReading(a, b, pearson(SEED_ENSEMBLE[a], SEED_ENSEMBLE[b]))
        for a, b in itertools.combinations(sorted(SEED_ENSEMBLE), 2)
    ]
    return tuple(sorted(pairs, key=lambda r: (r.rho, r.arm_a, r.arm_b)))


def population() -> tuple[PairReading, ...]:
    """The pairs the branch-wide count is taken over — degenerates excluded."""
    return tuple(r for r in readings() if not r.degenerate)


def against_baseline() -> tuple[PairReading, ...]:
    """Pairs involving :data:`clearance_census.BASELINE`, degenerates excluded.

    This is the population that bears on the deficit claim: `clearance_census`
    measures every arm against `stock_mppi`, so if the 8-seed widening is ever
    reported as a paired difference it is *these* correlations whose sign
    decides whether the pairing bought anything.
    """
    return tuple(
        r for r in population() if BASELINE in (r.arm_a, r.arm_b)
    )


def branch_wide_verdict() -> str:
    """`UNIFORMLY_POSITIVE` if every non-degenerate pair correlates positively.

    Anything else is `SIGN_VARIES`, which is the finding: it means there is no
    branch-wide pairing policy to adopt, only a per-pair test to run on the
    scene actually being widened.
    """
    pop = population()
    return "UNIFORMLY_POSITIVE" if all(r.rho > 0.0 for r in pop) else "SIGN_VARIES"


def main() -> None:
    """Print the pair table and the verdict. `python3 -m ...pairing_precondition`."""
    print(f"pairing_precondition — {len(SEED_ENSEMBLE)} arms x {SEEDS} seeds "
          f"on clearance, one scene")
    for r in readings():
        mark = " (identity)" if r.degenerate else ""
        print(f"  {r.rho:+.4f}  sd x{r.sd_ratio:.3f}  {r.verdict:<13s} "
              f"{r.arm_a} x {r.arm_b}{mark}")
    pop = population()
    negative = [r for r in pop if r.rho < 0.0]
    print(f"\npopulation {len(pop)} pairs ({len(readings()) - len(pop)} degenerate "
          f"excluded); {len(negative)} negative")
    print(f"verdict: {branch_wide_verdict()}")
    print("\nagainst the baseline (the deficit claim's own comparison):")
    for r in against_baseline():
        other = r.arm_b if r.arm_a == BASELINE else r.arm_a
        print(f"  {r.rho:+.4f}  sd x{r.sd_ratio:.3f}  {other}")


if __name__ == "__main__":  # pragma: no cover
    main()
