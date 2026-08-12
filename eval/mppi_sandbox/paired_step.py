# SPDX-License-Identifier: BSD-3-Clause
"""Seed-widening the off-family 2x2 — and the estimand that cannot be widened.

STATE ranked this cycle's job as "6 -> 20 paired seeds with a CI on both steps
of `city_crossing_v0`", on the grounds that D-223's two steps (+0.0486 m alone,
-0.0085 m beside the risk term) are sub-5 cm and 6 seeds cannot separate either
from noise. The loop is trivial. The statistic is not, and the reason is the
finding this module exists to state:

**`three_arm.ped_step` is a difference of ensemble minima.**
`SweepStats.min_clearance` is `min` over the seed ensemble, so the step is
``min_i c_i(w_ped=50) - min_j c_j(w_ped=0)`` — the two minima are attained at
seeds `i` and `j` that need not be equal, and usually are not. Two consequences,
and only the second is about noise:

1. **It is not paired.** The seeds are shared, the statistic does not use that.
   Every other paired reading on this branch (`ab.paired_delta`,
   `margin_free.RungComparison`) differences *within* a seed; this one does not,
   so the variance reduction pairing exists to buy is discarded before the CI
   is taken.

2. **It is not the same quantity at n = 6 and n = 20.** A sample minimum is
   non-increasing in `n` by construction: `min` over a superset cannot be
   larger. So `E[min_n]` decreases with `n` for any non-degenerate clearance
   distribution, and the 20-seed cell means something the 6-seed cell did not.
   Widening does not sharpen this estimand, it **moves** it — and the step is a
   *difference* of two such quantities, so the drift does not even carry a
   known sign; the two cells drift by different amounts and the difference can
   go either way.

That is `seed_count_licence`'s finding about the all-seeds ESS gate,
``(1-p)^n``, in the second estimand of the same branch: a number whose
definition depends on `n` may not be quoted at two values of `n`. There, the
consequence was that a 16-seed pre-read licensed rungs a 32-seed walk refused.
Here it is milder and more insidious — nothing errors, the table just silently
stops comparing to the one D-223 published.

What this module does about it
------------------------------

It reports **both** estimands and never silently substitutes one for the other:

- :attr:`PairedStep.worst_step` — the `three_arm.ped_step` quantity, carried so
  the 20-seed table can be laid beside D-223's 6-seed one, and carried with
  :func:`min_step_is_n_dependent` next to it so the comparison is read with its
  caveat rather than without.
- :attr:`PairedStep.mean_step` — mean per-seed `w_ped=50 - w_ped=0` clearance,
  the estimand that *is* fixed under `n`, with a paired bootstrap CI. The CI
  comes from :class:`margin_free.RungComparison`, not from a second bootstrap
  written here: the branch has one statement of the resampling rule (resample
  **seeds**, keep the pairing) and D-047 is the standing reason not to acquire
  a second one that can drift from it.
- :attr:`PairedStep.sign_p` — the exact two-sided sign test on the paired
  differences. D-222/D-223's claim is about a **sign** ("standalone helps,
  with-risk hurts, the mirror image of the cafe family"), not a magnitude, and
  the sign test is the reading that answers the claim actually made: it is
  exact (`math.comb`, no asymptotics, no resampling), assumes nothing about the
  clearance distribution, and is unaffected by the one-seed tails that make a
  mean gap look decisive (`ab.paired_delta`'s own warning).

Reported, never thresholded (D-044): :attr:`PairedStep.verdict` grades
separation from zero at the 95 % level, and nothing here asserts what the
answer must be. The recorded 20-seed walk is in :data:`WALK_20` so tests read a
population instead of spending 80 sim runs (~3 min) to re-derive one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .margin_free import RungComparison
from .three_arm import LAM, W_PED_COLS, W_RISK_ROWS

__all__ = [
    "SCENE",
    "SEEDS_20",
    "WALK_20",
    "MIN_IS_N_DEPENDENT",
    "MEAN_IS_N_STABLE",
    "SEPARATED_POSITIVE",
    "SEPARATED_NEGATIVE",
    "NOT_SEPARATED",
    "PairedStep",
    "min_step_is_n_dependent",
    "sign_test_p",
    "paired_step",
    "steps",
    "nested_worst_steps",
    "estimand_drift",
]

#: The off-family scene, at D-223's retuned (uncensored) operating point.
SCENE = "eval/scenarios/variants/city_crossing_v0.yaml"

#: STATE's ask: 6 -> 20. Superset of D-223's `(0..5)`, so the 6-seed reading is
#: a *prefix* of this one and :func:`nested_worst_steps` can show the drift on
#: the same runs rather than by comparing two walks.
SEEDS_20 = tuple(range(20))

#: Analytic verdicts — returned without consulting any data, because they are
#: properties of `min` and of the mean, not findings about these arms
#: (`seed_count_licence.licence_direction`'s precedent).
MIN_IS_N_DEPENDENT = "MIN_IS_N_DEPENDENT"
MEAN_IS_N_STABLE = "MEAN_IS_N_STABLE"

SEPARATED_POSITIVE = "SEPARATED_POSITIVE"
SEPARATED_NEGATIVE = "SEPARATED_NEGATIVE"
NOT_SEPARATED = "NOT_SEPARATED"

#: Per-seed clearances (m) of the 20-seed 2x2 walked 2026-08-12 20:00 KST on
#: :data:`SCENE` at `lam = 0.8`, keyed `(w_risk, w_ped)`, seed-ordered 0..19.
#: Every cell reached the goal on every seed — recorded in
#: :data:`WALK_20_REACHED` so a freeze cannot hide inside a clearance table
#: (`three_arm.step_bought_with_freeze`'s reason for existing).
WALK_20: dict[tuple[float, float], tuple[float, ...]] = {
    (40.0, 0.0): (
        0.4349, 0.3970, 0.3882, 0.3504, 0.4173, 0.4471, 0.4595, 0.4143,
        0.4278, 0.3756, 0.4481, 0.5256, 0.3393, 0.3777, 0.3036, 0.3815,
        0.3619, 0.3666, 0.4143, 0.3403),
    (40.0, 50.0): (
        0.4454, 0.3418, 0.4106, 0.3655, 0.4319, 0.3802, 0.3799, 0.4076,
        0.4818, 0.4148, 0.3630, 0.4659, 0.3722, 0.4135, 0.3643, 0.3496,
        0.3247, 0.2441, 0.2777, 0.2794),
    (0.0, 0.0): (
        0.4460, 0.2415, 0.4168, 0.3985, 0.3753, 0.3014, 0.3183, 0.3796,
        0.4538, 0.3460, 0.3284, 0.3549, 0.2501, 0.3000, 0.2597, 0.3415,
        0.4200, 0.3032, 0.3294, 0.3295),
    (0.0, 50.0): (
        0.3757, 0.3204, 0.4412, 0.2901, 0.3325, 0.3239, 0.3216, 0.2942,
        0.3559, 0.3553, 0.4277, 0.3454, 0.2748, 0.3907, 0.2254, 0.3294,
        0.2820, 0.3097, 0.3021, 0.3038),
}

#: `n_reached` per cell of the same walk. Kept as a count beside the
#: clearances, never derived from them.
WALK_20_REACHED: dict[tuple[float, float], int] = {
    (40.0, 0.0): 20,
    (40.0, 50.0): 20,
    (0.0, 0.0): 20,
    (0.0, 50.0): 20,
}


def min_step_is_n_dependent() -> str:
    """`MIN_IS_N_DEPENDENT` — the direction, with no data consulted.

    `min` over a seed ensemble is non-increasing under adding seeds, so the
    quantity `three_arm.ped_step` reports is indexed by `n`. This is a theorem
    about the statistic; calling it with a population would be re-measuring it
    (`seed_count_licence`'s point 1, and its three re-measurements).
    """
    return MIN_IS_N_DEPENDENT


def mean_step_is_n_stable() -> str:
    """`MEAN_IS_N_STABLE` — the mean paired difference estimates the same
    population quantity at every `n`; only its precision moves."""
    return MEAN_IS_N_STABLE


def sign_test_p(diffs, tol: float = 1e-9) -> float:
    """Exact two-sided sign-test p on paired differences.

    Ties (|d| <= `tol`) are **dropped**, the conventional handling, and the
    test is then binomial(n_effective, 1/2). Exact via `math.comb`: no normal
    approximation, so a 20-seed reading is not being graded by an asymptotic
    that 20 does not license. Returns `1.0` when every pair ties — no evidence
    of a sign, which is the honest reading of an inert arm.
    """
    pos = sum(1 for d in diffs if d > tol)
    neg = sum(1 for d in diffs if d < -tol)
    n = pos + neg
    if n == 0:
        return 1.0
    k = min(pos, neg)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2.0 * tail)


@dataclass(frozen=True)
class PairedStep:
    """One row of the 2x2, read in both estimands on one seed ensemble."""

    scene: str
    w_risk: float
    #: Per-seed clearances at `w_ped = 0` and `w_ped = 50`, seed-ordered and
    #: index-paired — the same contract `ab.paired_delta` enforces.
    base: tuple[float, ...]
    arm: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.base) != len(self.arm):
            raise ValueError(
                f"w_risk={self.w_risk:g}: {len(self.base)} baseline against "
                f"{len(self.arm)} arm clearances — the cells are paired by "
                "seed index, so unequal lengths mean the pairing is not what "
                "this class assumes")
        if not self.base:
            raise ValueError("a paired step needs at least one seed")

    @property
    def n(self) -> int:
        return len(self.base)

    @property
    def worst_step(self) -> float:
        """`three_arm.ped_step`'s quantity: difference of ensemble minima.

        Reported so the 20-seed table can be laid beside D-223's, and reported
        as a property named `worst_` rather than `step` so no caller can reach
        it believing it is the paired one.
        """
        return min(self.arm) - min(self.base)

    @property
    def diffs(self) -> tuple[float, ...]:
        """Per-seed `arm - base`. The paired quantity `worst_step` discards."""
        return tuple(a - b for b, a in zip(self.base, self.arm))

    @property
    def _comparison(self) -> RungComparison:
        """This row as the branch's existing paired-bootstrap object.

        `declared_margin` / `censoring` are carried by that class for the
        threshold route and are used by **no** statistic on it; they are passed
        as the neutral values because this reading is margin-free by
        construction — it never grades a run against a threshold.
        """
        return RungComparison(
            scenario=self.scene, weight=self.w_risk, declared_margin=0.0,
            censoring="", stock=self.base, risk=self.arm)

    @property
    def mean_step(self) -> float:
        """Mean per-seed difference (m) — the `n`-stable estimand."""
        return self._comparison.paired_delta

    def ci(self, *, reps: int = 2000, alpha: float = 0.05,
           seed: int = 0) -> tuple[float, float]:
        """Paired bootstrap CI of :attr:`mean_step`, seeds resampled."""
        return self._comparison.bootstrap_ci(reps=reps, alpha=alpha, seed=seed)

    @property
    def sign_counts(self) -> tuple[int, int, int]:
        """(seeds where the term helped, hurt, tied) at 1e-9 m."""
        d = self.diffs
        return (sum(1 for x in d if x > 1e-9), sum(1 for x in d if x < -1e-9),
                sum(1 for x in d if abs(x) <= 1e-9))

    @property
    def sign_p(self) -> float:
        """Exact two-sided sign-test p on :attr:`diffs`."""
        return sign_test_p(self.diffs)

    @property
    def verdict(self) -> str:
        """Does the paired CI exclude zero, and on which side?

        This is a *separation* reading, not a size one: it says the sign is
        resolved at 95 %, and says nothing about whether a step of this size
        matters to a robot. `margin_free.RungComparison.equivalence_margin` is
        the reading for that question and is deliberately left to the caller's
        own tolerance (D-165's reason).
        """
        lo, hi = self.ci()
        if lo > 0.0:
            return SEPARATED_POSITIVE
        if hi < 0.0:
            return SEPARATED_NEGATIVE
        return NOT_SEPARATED

    def __str__(self) -> str:  # pragma: no cover - formatting
        lo, hi = self.ci()
        pos, neg, tie = self.sign_counts
        return (f"w_risk={self.w_risk:5.1f}  n={self.n:2d}  "
                f"worst {self.worst_step:+.4f}  "
                f"mean {self.mean_step:+.4f} "
                f"[{lo:+.4f}, {hi:+.4f}]  {self.verdict:18s} "
                f"sign {pos}+/{neg}-/{tie}=  p={self.sign_p:.3f}")


def paired_step(w_risk: float, walk=None, scene: str = SCENE) -> PairedStep:
    """Build one row from a recorded walk (default :data:`WALK_20`)."""
    walk = WALK_20 if walk is None else walk
    return PairedStep(scene=scene, w_risk=w_risk,
                      base=tuple(walk[(w_risk, W_PED_COLS[0])]),
                      arm=tuple(walk[(w_risk, W_PED_COLS[1])]))


def steps(walk=None, scene: str = SCENE) -> dict[float, PairedStep]:
    """Both rows of the 2x2, keyed by `w_risk`."""
    return {w: paired_step(w, walk=walk, scene=scene) for w in W_RISK_ROWS}


def nested_worst_steps(w_risk: float, walk=None,
                       prefixes=(6, 20)) -> dict[int, float]:
    """:attr:`PairedStep.worst_step` re-read on nested seed prefixes.

    The demonstration behind :func:`min_step_is_n_dependent`, taken on **one**
    walk rather than two: seeds 0..5 of this ensemble are exactly D-223's, so
    the `n = 6` entry reproduces the published number and the `n = 20` entry
    is the same runs plus fourteen more. Any movement between them is the
    estimand's `n`-dependence and cannot be a difference of walks.
    """
    walk = WALK_20 if walk is None else walk
    out = {}
    for k in prefixes:
        base = tuple(walk[(w_risk, W_PED_COLS[0])])[:k]
        arm = tuple(walk[(w_risk, W_PED_COLS[1])])[:k]
        out[k] = PairedStep(scene=SCENE, w_risk=w_risk,
                            base=base, arm=arm).worst_step
    return out


def estimand_drift(walk=None, prefixes=(6, 20)) -> dict[float, float]:
    """How far each row's `worst_step` moved between the two prefixes (m).

    Not a verdict. The number a reader needs to decide whether laying the
    20-seed table beside D-223's is defensible for their purpose — which is
    the same shape as `equivalence_margin` reporting ε instead of choosing it.
    """
    lo, hi = min(prefixes), max(prefixes)
    return {w: (nested_worst_steps(w, walk=walk, prefixes=prefixes)[hi]
                - nested_worst_steps(w, walk=walk, prefixes=prefixes)[lo])
            for w in W_RISK_ROWS}


def main() -> int:  # pragma: no cover - CLI
    print(f"{SCENE.rsplit('/', 1)[-1]}  lam={LAM}  n={len(SEEDS_20)} paired seeds")
    for w, s in steps().items():
        print(f"  {s}")
    print(f"  {min_step_is_n_dependent()}: worst-case step drift 6->20 = "
          + ", ".join(f"w_risk={w:g}: {d:+.4f} m"
                      for w, d in estimand_drift().items()))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
