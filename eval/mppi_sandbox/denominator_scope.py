# SPDX-License-Identifier: BSD-3-Clause
"""D-028's denominator finding, re-measured at the temperature the repo ships.

D-028 priced `w_voo = 200` two ways on `cafe_obstacle_crossing_v0` and found
the *denominator* was the load-bearing choice: 6.19x against the healthy arm
the weight is added to, 1.46x against the arm that carries it. Both exceed 1,
so the verdict ("this one term spans more of the cost range than everything
else") survived either way; only the margin moved. That measurement was taken
at `lam = 1.6`.

The repo ships `lam = 0.1`. This module re-reads the same pair there, and the
three things D-028 concluded from the `lam = 1.6` reading do not survive the
move.

## 1. The verdict flips, and it flips on the self-referential side

Self-referential ratio **1.464 -> 0.0488**. At the shipped temperature the
statistic computed on the weight's own arm calls `w_voo = 200` a *negligible*
term -- five percent of what it competes with -- when measured against the
baseline it is added to it is still **3.30x**, and D-027 established that this
exact weight collapses the softmax. The understatement grows **9.15x ->
67.7x**. A statistic that understated a hazard at the temperature nobody ships
inverts the verdict at the temperature everybody does.

## 2. D-028 Decision (3) is false here -- the guard *is* the competitor

D-028 explicitly ruled the collision term out of the mechanism: `w_collision =
1e4` is the repo's largest weight, but its median per-step spread was
**exactly 0 on both arms**, so it was a guard rather than a competitor, and
the inflation was ordinary path-tracking cost. At `lam = 0.1` the loud arm's
`w_collision` median spread is **exactly 1e4** and the `w_voo` row's `rest`
denominator is **10183**, versus 724 at `lam = 1.6`. The denominator is the
collision indicator.

Stated precisely, because the number invites a wrong reading: **nothing
collides.** The executed trajectory's minimum clearance is 0.0119 m, which is
*better* than the baseline arm's 0.0097 m. The 1e4 is a spread over the
**rollout cloud** -- at the median control step some of the K = 256 sampled
rollouts cross the collision boundary and some do not, so `ptp(w_collision.f)`
is the full indicator height. The two temperatures inflate the same
denominator by two unrelated mechanisms.

## 3. And the understatement is not driven by damage

D-028 Decision (2)'s mechanism was that the loud arm never finishes -- 1000
steps against the baseline's 114 -- so ordinary path cost is evaluated on a
trajectory that has gone bad, and D-028 predicted the understatement therefore
"grows with the damage". At `lam = 0.1` the loud arm is dramatically *healthier*:
**116 steps against the baseline's 93** (1.25x, not 8.8x), final goal distance
0.290 m against 3.821 m at `lam = 1.6`. Damage went down by every measure
available and the understatement went **up 7.4x**.

So "graded on its own wreckage" is the right slogan and the wrong mechanism.
What sets the understatement is not how badly the arm is damaged but **which
term captures the `rest` denominator** -- and that can be a term the weight
never touched. :func:`read` therefore reports `dominant_term` rather than a
damage proxy: the finding is only interpretable next to the name of whatever
supplied the denominator.

## 4. The non-transferability D-028 warned about is also `lam = 1.6`-specific

D-028 Decision (5) measured the closed-loop per-unit exchange rate at
`w = 1 / 7 / 200` as **2.497 / 2.337 / 5.299** -- a 2.27x swing -- and
concluded that a cheap small-weight probe cannot be used to choose a shipping
weight ("measure at the weight you will ship"). At `lam = 0.1` the same ladder
reads **2.658 / 2.576 / 2.483**, a swing of **1.07x**. At the shipped
temperature the cheap probe is accurate to seven percent, and the methodology
rule D-028 wrote down is an artifact of the derailing arm.

## Scope

One scene, one seed, one weight, two temperatures, on `AVX512_SKX` (D-033).
The claim is *not* that the self-referential ratio always understates by 67x;
it is that D-028's three supporting mechanisms are each conditional on a
temperature the repo does not ship, which the sections stating them do not
say. `lam` was already known to be scene-specific; this adds that the
*mechanism attribution* is `lam`-specific too.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .controllers import make_controller
from .controllers.stock_mppi import MPPIParams
from .obstacles import min_clearance
from .run import ROBOT_RADIUS, simulate
from .weight_units import measure

#: The temperature D-027/D-028 measured at, and the one the repo ships.
#: Both are named because every finding in this module is a difference
#: between them, and an unlabelled `lam` is the D-021 mistake class.
AUDITED_LAM = 1.6
SHIPPED_LAM = 0.1

#: The weight D-027 found collapses the softmax, and the term it sits on.
LOUD_WEIGHT = 200.0
AUDITED_TERM = "w_voo"

#: `w_risk` / `k_margin_per_sigma` off, matching `test_weight_units` so the
#: ratios here are comparable to D-028's rather than merely similar.
ISOLATION: dict[str, float] = {"w_risk": 0.0, "k_margin_per_sigma": 0.0}

#: Below this, :attr:`DenominatorReading.self_ratio` reads as "this term does
#: not dominate the cost range" -- the negation of the D-027 condition that
#: `ratio > 1` is defined to detect. The point of this module is that the
#: same weight lands on opposite sides of it depending on `lam`.
VERDICT_THRESHOLD = 1.0


@dataclass(frozen=True)
class DenominatorReading:
    """Both denominators for one term, at one temperature, plus the mechanism.

    `dominant_term` is the load-bearing field. A ratio without it is what
    D-028 reported, and the reason its mechanism generalised incorrectly: the
    same understatement is produced by ordinary path cost on a derailed arm
    (`lam = 1.6`) and by the collision guard's rollout-cloud straddle on a
    nearly healthy one (`lam = 0.1`).
    """

    lam: float
    weight: float
    term: str
    #: term spread / rest spread, both on the arm carrying the weight
    self_ratio: float
    #: the same numerator's per-unit rate x weight, over the *baseline* arm's
    #: rest spread -- the arm the weight is being added to
    against_baseline: float
    #: the arm's own `rest` denominator, the quantity that actually moves
    rest_median: float
    baseline_rest_median: float
    #: name and median spread of the largest term inside `rest`
    dominant_term: str
    dominant_spread: float
    #: closed-loop health, so a damage explanation can be checked rather than assumed
    steps: int
    baseline_steps: int
    min_clearance: float
    baseline_min_clearance: float
    goal_distance: float
    baseline_goal_distance: float

    @property
    def understatement(self) -> float:
        """How many times smaller the self-referential ratio reads.

        D-028's headline was 4.2x at `lam = 1.6` using the exchange rate
        probed on the baseline trajectory; computed consistently from one
        arm's per-unit rate it is 9.15x there and 67.7x at `lam = 0.1`.
        """
        return float(self.against_baseline / self.self_ratio)

    @property
    def verdict(self) -> str:
        """What the self-referential statistic *says*, in D-027's own terms."""
        return ("dominates" if self.self_ratio > VERDICT_THRESHOLD
                else "negligible")

    @property
    def baseline_verdict(self) -> str:
        return ("dominates" if self.against_baseline > VERDICT_THRESHOLD
                else "negligible")

    @property
    def verdicts_disagree(self) -> bool:
        """True when the choice of denominator changes the conclusion itself,
        not merely its margin. False at `lam = 1.6`; true at `lam = 0.1`."""
        return self.verdict != self.baseline_verdict

    @property
    def rest_inflation(self) -> float:
        """The loud arm's denominator as a multiple of the baseline's."""
        return float(self.rest_median / self.baseline_rest_median)

    @property
    def step_inflation(self) -> float:
        """Damage proxy D-028 used: 8.8x at `lam = 1.6`, 1.25x at `lam = 0.1`."""
        return float(self.steps / self.baseline_steps)

    def __str__(self) -> str:
        return (f"lam={self.lam:<5g} self={self.self_ratio:<8.4g} "
                f"({self.verdict}) baseline={self.against_baseline:<8.4g} "
                f"({self.baseline_verdict}) understated={self.understatement:.3g}x "
                f"denominator={self.dominant_term}")


def _health(scenario, lam: float, weight: float, seed: int):
    ctrl = make_controller("risk_mppi", scenario, seed=seed,
                           robot_radius=ROBOT_RADIUS,
                           params=MPPIParams(lam=lam), **ISOLATION,
                           **{AUDITED_TERM: weight})
    traj = simulate(scenario, ctrl)
    clear = float(min_clearance(traj, scenario.obstacles, ROBOT_RADIUS))
    goal = float(np.linalg.norm(traj[-1, 1:3] - np.asarray(scenario.goal[:2])))
    return len(traj), clear, goal


def read(scenario, *, lam: float, weight: float = LOUD_WEIGHT,
         seed: int = 0) -> DenominatorReading:
    """Measure both denominators for :data:`AUDITED_TERM` at one temperature.

    Four closed-loop runs: the leave-one-out table for the loud and baseline
    arms (which is where the ratios come from), plus a plain simulate of each
    to record clearance and goal distance -- `measure` hooks `_cost` and
    returns spreads, not trajectory health, and the whole point of section 3
    is that the health has to be read rather than inferred from the ratio.
    """
    loud = measure(scenario, params=MPPIParams(lam=lam), seed=seed,
                   **ISOLATION, **{AUDITED_TERM: weight})
    base = measure(scenario, params=MPPIParams(lam=lam), seed=seed,
                   **ISOLATION, **{AUDITED_TERM: 0.0})

    row = loud[AUDITED_TERM]
    # `w_collision`'s row excludes only the collision term, so its `rest` is
    # the closest thing to "the baseline landscape" that is defined on both
    # arms -- D-028 used it as the baseline denominator and it is reused here
    # so the two modules' numbers are comparable rather than merely similar.
    baseline_rest = base["w_collision"].rest_median
    against_baseline = row.spread_per_unit_weight * weight / baseline_rest

    others = {n: s.spread_median for n, s in loud.items() if n != AUDITED_TERM}
    dominant = max(others, key=others.__getitem__)

    steps, clear, goal = _health(scenario, lam, weight, seed)
    b_steps, b_clear, b_goal = _health(scenario, lam, 0.0, seed)

    return DenominatorReading(
        lam=lam, weight=weight, term=AUDITED_TERM,
        self_ratio=row.ratio, against_baseline=float(against_baseline),
        rest_median=row.rest_median, baseline_rest_median=float(baseline_rest),
        dominant_term=dominant, dominant_spread=float(others[dominant]),
        steps=steps, baseline_steps=b_steps,
        min_clearance=clear, baseline_min_clearance=b_clear,
        goal_distance=goal, baseline_goal_distance=b_goal,
    )


def format_table(readings) -> str:
    """Markdown table, newest-style: one row per temperature."""
    head = ("| `lam` | self | verdict | vs baseline | verdict | understated | "
            "denominator | steps |\n|---|---|---|---|---|---|---|---|\n")
    rows = "".join(
        f"| {r.lam:g} | {r.self_ratio:.4g} | {r.verdict} | "
        f"{r.against_baseline:.4g} | {r.baseline_verdict} | "
        f"{r.understatement:.3g}x | `{r.dominant_term}` | "
        f"{r.steps} vs {r.baseline_steps} |\n"
        for r in readings)
    return head + rows
