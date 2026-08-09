# SPDX-License-Identifier: BSD-3-Clause
"""Does the published band's protocol transplant to a second scene — and when
it does, does that scene admit the two-sided rung the first one cannot?

`scene_eligibility` (D-159) cut the successor question's population from 8
scenes to **3**, and found that only one of the three had ever been walked:
`cafe_head_on_v0`, precisely the scene `margin_sweep` capped at arm coverage
**1/4** (D-158). STATE's next step was therefore concrete — walk
`cafe_convoy_v0`, both arms, at *its* declared margin 0.30 m. This module is
that walk plus the screen it turned out to need first.

**The screen: 1 of the band's 4 rungs transplants, not 4.** "The same protocol"
is not a free move across scenes, because the protocol includes an operating
point and λ is calibrated **per scene** (`calibrate_lam`, D-142: 6 of 14
arm-cells move between `w = 10` and `w = 75`). Asking which of the band's rungs
`w ∈ {75, 100, 150, 250}` can be walked on convoy at the band's own λ = 0.8,
against the calibration tables `lam_window_index` already owns::

    rung      convoy stock        convoy risk         verdict
    w =  75   [0.8]               [0.8]               TRANSPLANTS
    w = 100   [1.1314]            [1.1314]            LAM_NOT_ADMISSIBLE
    w = 150   (no convoy cell)    (no convoy cell)    NO_CELL
    w = 250   (no convoy cell)    (no convoy cell)    NO_CELL

So the cross-scene comparison has a denominator of **1**, fixed before any run.
This is D-159's lesson one level down: there the population was scenes, here it
is rungs within a scene, and both times the screen is cheaper than the
measurement and changes what the measurement can mean. Walking convoy at λ =
0.8 for `w = 100` would have produced a number — an inadmissible one, since
convoy/risk at that weight weights outside the ESS band there.

**The walk, at the one rung that transplants.** `cafe_convoy_v0`, `w = 75`,
λ = 0.8, margin **0.30 m**, seeds 0–31 per arm, 64/64 reaching goal and 64/64
inside the ESS band — a fully admissible operating point, and the first
recorded per-seed clearances for any scene other than `cafe_head_on_v0`.

The result is `NO_HEADROOM_SAFE`: **every one of the 64 runs clears the
margin**, the worst by 0.5914 m. Both arms sit at :data:`FLOOR`, so the block
is `BOTH_ARMS_CENSORED` and the rung is `NONE_TWO_SIDED` — the same verdict
`cafe_head_on_v0` returns, reached from the **opposite boundary**. On head_on
`stock_mppi` is at a ceiling because nothing it does clears 0.40 m; on convoy
both arms are at a floor because everything clears 0.30 m. A census that reads
only the verdict sees one failure mode where there are two, and the direction
is the whole difference: head_on's censoring says the scene is too hard for the
declared margin, convoy's says it is too easy for it.

**And re-grading cannot repair convoy either, for a third distinct reason.**
`margin_sweep` does not even reach `NO_TWO_SIDED_MARGIN` here — it returns
`NO_RECORDED_SEPARATION`, its vacuity verdict, because that module grades
whether a *recorded* separation survives re-grading and convoy recorded none
to survive. The substantive answer is in the fields: `two_sided` is empty, and
the reason is not that the arms nearly coincide as at head_on's `w ∈ {75, 100}`
(overlap 7.6 mm and 9.9 mm). Convoy's arms are **disjoint**: `stock_mppi` tops
out at 1.0086 m and
`risk_mppi` bottoms out at 1.0284 m, so `arm_overlap` is **−0.0198 m** — a
*negative* overlap, a case the published band never produced. No threshold is
interior to either arm's range and both, at any value, so the unrepairability
is stronger than head_on's rather than weaker.

That negative overlap is also the one genuinely good piece of news, and it is a
statement about the **mechanism** and not about safety (the D-124 trap, and it
bites here in the mirror direction — `Headroom.sub_margin` is False because
both means are *above* the margin, not below it). The arms separate completely
in clearance: every `risk_mppi` run is safer than every `stock_mppi` run,
32 against 32, which the band's own rungs never achieved. What that cannot be
is a safety delta, because the safety headline it would move — `unsafe_rate` —
is 0.0000 on both arms and has been the whole time.

**Two of the three eligible scenes are now measured and neither admits a
two-sided rung.** Only `cafe_obstacle_crossing_v0` is left, and the prior it
inherits is worse than the one convoy inherited: two scenes, two boundaries,
one verdict.

Reported, never thresholded (D-044). No test asserts convoy is two-sided or
that any transplant count is non-zero — the 1/4 and the `NONE_TWO_SIDED` are
today's honest readings and would become permanent reds the moment a rung is
recalibrated. Nothing here runs a simulation: the clearances are constants and
the screen reads yaml.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .comparison_headroom import Headroom
from .lam_window_index import NO_CELL, NO_TABLE_AT_WEIGHT, resolve
from .margin_sweep import MarginSweep
from .separation_reproduction import Reproduction, reproduction_at

#: The scene has a calibrated cell at this weight and the reference λ is
#: admissible on **both** arms, so the reference protocol runs unchanged.
TRANSPLANTS = "TRANSPLANTS"

#: A cell exists at this weight but the reference λ is outside at least one
#: arm's admissible window. A run here would produce a number that
#: `assert_ess_in_band` refuses — not a comparison. The window is **non-empty**,
#: so some other λ would be admissible: the rung is refused at the *reference*
#: operating point, and buying it back costs cross-scene λ comparability.
LAM_NOT_ADMISSIBLE = "LAM_NOT_ADMISSIBLE"

#: A cell exists at this weight and at least one arm's admissible window is
#: **empty** — no λ whatsoever weights inside the ESS band there.
#:
#: Distinguished from :data:`LAM_NOT_ADMISSIBLE` because the two differ in what
#: they permit, which is D-157's "the reasons differ in kind" one scope down.
#: A `LAM_NOT_ADMISSIBLE` rung can be walked by giving something up (the shared
#: λ); an empty window offers nothing to give up — the weight itself is
#: unwalkable on that arm, and only re-calibrating at a *different weight*
#: reaches a run. Collapsing both into "blocked" makes 0/4 look like one fact
#: when it is two, and hides that one of them has no repair at this rung.
NO_ADMISSIBLE_LAM = "NO_ADMISSIBLE_LAM"

#: No table is calibrated at this weight, or the table has no row for this
#: scene. The window is unmeasured rather than empty, so the rung is not
#: refused — it is unscreenable until someone runs `calibrate_lam` there.
UNCALIBRATED = "UNCALIBRATED"

#: Verdicts under which the reference protocol may actually be walked.
WALKABLE = (TRANSPLANTS,)


@dataclass(frozen=True)
class RungTransplant:
    """One reference rung screened against a second scene's λ calibration."""

    scenario: str
    weight: float
    lam: float
    arms: tuple[str, str]

    @property
    def windows(self) -> tuple[tuple[str, tuple[float, ...] | None], ...]:
        """Each arm's admissible λ window at this weight; `None` when unknown.

        `Resolution.usable` is `None` under every refusal, which is why the
        two cases below are distinguished by the refusal verdict rather than by
        an empty tuple: an *empty* window (calibrated, nothing admissible) and
        an *unmeasured* one read identically otherwise, and only the first is a
        fact about the scene.
        """
        out = []
        for arm in self.arms:
            r = resolve(self.scenario, arm, self.weight)
            usable = None if r.verdict in (NO_CELL, NO_TABLE_AT_WEIGHT) \
                else tuple(r.usable or ())
            out.append((arm, usable))
        return tuple(out)

    @property
    def verdict(self) -> str:
        windows = self.windows
        if any(w is None for _, w in windows):
            return UNCALIBRATED
        if any(len(w) == 0 for _, w in windows):
            return NO_ADMISSIBLE_LAM
        if all(any(abs(x - self.lam) <= 1e-9 for x in w) for _, w in windows):
            return TRANSPLANTS
        return LAM_NOT_ADMISSIBLE

    @property
    def walkable(self) -> bool:
        return self.verdict in WALKABLE

    def __str__(self) -> str:
        return f"w={self.weight:g} :: {self.verdict}"


#: No rung of the reference band can be walked on this scene at the reference
#: λ. Named because a screen that returns nothing reads, in every other field,
#: exactly like one that was never run (D-107).
NO_RUNG_TRANSPLANTS = "NO_RUNG_TRANSPLANTS"

#: Some but not all rungs transplant — the cross-scene comparison exists and
#: its denominator is smaller than the reference band's.
PARTIAL_TRANSPLANT = "PARTIAL_TRANSPLANT"

#: Every reference rung transplants; the second scene can be walked as a full
#: replica of the band.
FULL_TRANSPLANT = "FULL_TRANSPLANT"


@dataclass(frozen=True)
class TransplantScreen:
    """The reference band's rungs screened against one second scene."""

    scenario: str
    rungs: tuple[RungTransplant, ...]

    def __post_init__(self) -> None:
        if not self.rungs:
            raise ValueError(
                "a transplant screen over no rungs cannot say whether the "
                "protocol moves; name the reference band's weights"
            )

    @property
    def walkable(self) -> tuple[float, ...]:
        return tuple(r.weight for r in self.rungs if r.walkable)

    @property
    def blocked(self) -> tuple[tuple[float, str], ...]:
        """Each non-walkable rung with **why** — the reasons differ in kind and
        collapsing them to a count loses the actionable half (D-157): an
        `UNCALIBRATED` rung is one `calibrate_lam` run from being screenable,
        a `LAM_NOT_ADMISSIBLE` one is not."""
        return tuple((r.weight, r.verdict) for r in self.rungs
                     if not r.walkable)

    @property
    def coverage(self) -> tuple[int, int]:
        return len(self.walkable), len(self.rungs)

    @property
    def verdict(self) -> str:
        n, total = self.coverage
        if n == 0:
            return NO_RUNG_TRANSPLANTS
        return FULL_TRANSPLANT if n == total else PARTIAL_TRANSPLANT

    def __str__(self) -> str:
        n, total = self.coverage
        return f"{self.scenario} :: {self.verdict} {n}/{total}"


#: The reference band this module screens against: `cafe_head_on_v0`'s four
#: separated rungs, all walked at λ = 0.8 (`scorable_band.PUBLISHED_LAM`).
REFERENCE_WEIGHTS: tuple[float, ...] = (75.0, 100.0, 150.0, 250.0)

CONVOY_SCENARIO = "cafe_convoy_v0.yaml"

#: `cafe_convoy_v0`'s declared `min_distance_to_obstacle`, read off the
#: scenario yaml by `feasibility.declared_margin`. **Not** 0.40 m — quoting the
#: band's margin here is exactly the cross-scope error D-159 named.
CONVOY_MARGIN = 0.30

#: The λ the walk below ran at, and the band's own. Admissible on both convoy
#: arms at `w = 75` and at no other reference weight — see the module docstring.
CONVOY_LAM = 0.8

CONVOY_WEIGHT = 75.0


def convoy_screen() -> TransplantScreen:
    """The band's four rungs screened against `cafe_convoy_v0`. 1/4."""
    from .scorable_band import PUBLISHED_ARMS

    return TransplantScreen(
        scenario=CONVOY_SCENARIO,
        rungs=tuple(
            RungTransplant(scenario=CONVOY_SCENARIO, weight=w,
                           lam=CONVOY_LAM, arms=PUBLISHED_ARMS)
            for w in REFERENCE_WEIGHTS
        ),
    )


#: Minimum clearance in metres per seed on `cafe_convoy_v0` at λ = 0.8,
#: `w_obs_soft = 75`, seeds 0–31 in order, both arms. Walked 2026-08-09; 64/64
#: reached the goal and 64/64 weighted inside the ESS band.
#:
#: The blocks are named 0–15 / 16–31 for continuity with the band's walks, but
#: unlike those this scene has **no prior record** to reproduce — nothing was
#: ever measured on convoy before, so the reference block is a first
#: measurement rather than a re-derivation, and `Reproduction`'s verdict here
#: grades this walk's internal consistency only. Said out loud because the
#: object is the same one D-152/153 used for genuine replications.
#:
#: Every value in both arms is above the 0.30 m margin: `stock_mppi` spans
#: [0.8914, 1.0086] and `risk_mppi` spans [1.0284, 1.2066]. The ranges are
#: **disjoint** — the arms separate completely in clearance while the safety
#: headline cannot move at all.
CONVOY_W75_CLEARANCES: dict[str, tuple[float, ...]] = {
    "stock_mppi": (
        0.9499, 1.0086, 1.0060, 0.9946, 1.0055, 0.9818, 0.9858, 0.9742,
        0.9179, 0.9888, 0.9524, 1.0020, 0.9877, 0.9650, 0.9803, 0.9038,
        0.9702, 0.9699, 0.9904, 0.8914, 0.9821, 0.9935, 0.9842, 0.9954,
        1.0083, 0.9773, 0.9475, 0.9310, 0.9652, 0.9296, 0.9589, 0.9706,
    ),
    "risk_mppi": (
        1.0798, 1.1469, 1.1583, 1.0889, 1.1828, 1.1518, 1.1728, 1.0754,
        1.0999, 1.1244, 1.0997, 1.0630, 1.1798, 1.1178, 1.1127, 1.1089,
        1.0284, 1.0982, 1.1305, 1.0815, 1.1159, 1.0691, 1.1687, 1.1179,
        1.2066, 1.1762, 1.1274, 1.1768, 1.1110, 1.0983, 1.0490, 1.0867,
    ),
}

CONVOY_REFERENCE_SEEDS = 16


def convoy_w75_walk() -> Reproduction:
    """The measured `cafe_convoy_v0` walk, graded at **its own** margin."""
    from .scorable_band import PUBLISHED_ARMS

    return reproduction_at(CONVOY_SCENARIO, CONVOY_LAM, CONVOY_MARGIN,
                           CONVOY_WEIGHT, PUBLISHED_ARMS,
                           CONVOY_W75_CLEARANCES, CONVOY_REFERENCE_SEEDS)


def convoy_w75_sweep() -> MarginSweep:
    """Every threshold the convoy walk's clearances can express. None is
    two-sided — the arms are disjoint."""
    return MarginSweep(reproduction=convoy_w75_walk())


CROSSING_SCENARIO = "cafe_obstacle_crossing_v0.yaml"

#: `cafe_obstacle_crossing_v0`'s declared `min_distance_to_obstacle`. Equal to
#: convoy's 0.30 m and unequal to the band's 0.40 m — a coincidence between two
#: scene constants, not a shared one (D-159).
CROSSING_MARGIN = 0.30


def crossing_screen() -> TransplantScreen:
    """The band's four rungs screened against `cafe_obstacle_crossing_v0`. 0/4.

    The third and last eligible scene (D-159) cannot host the successor
    question at all, and the screen says so at zero run cost — STATE planned a
    64-run walk here.

    The four refusals are **not** one fact repeated::

        w =  75   stock [4.5255]  risk (empty)   NO_ADMISSIBLE_LAM
        w = 100   stock (empty)   risk (empty)   NO_ADMISSIBLE_LAM
        w = 150   (no cell)       (no cell)      UNCALIBRATED
        w = 250   (no cell)       (no cell)      UNCALIBRATED

    At `w = 75` the stock arm *is* calibrated — at λ = 4.5255, nowhere near the
    band's 0.8 — while `risk_mppi` has no admissible λ at that weight at all.
    That empty window is the harder half: convoy's blocked rung offered a
    different λ and this one offers none, so the walkable-scene population is
    **2, not 3**, and it is closed by calibration facts rather than by anything
    a controller does.
    """
    from .scorable_band import PUBLISHED_ARMS, PUBLISHED_LAM

    return TransplantScreen(
        scenario=CROSSING_SCENARIO,
        rungs=tuple(
            RungTransplant(scenario=CROSSING_SCENARIO, weight=w,
                           lam=PUBLISHED_LAM, arms=PUBLISHED_ARMS)
            for w in REFERENCE_WEIGHTS
        ),
    )


#: The two measured scenes reach one verdict from opposite boundaries.
CEILING_CENSORED = "CEILING_CENSORED"
FLOOR_CENSORED = "FLOOR_CENSORED"
MIXED_CENSORING = "MIXED_CENSORING"
NOT_CENSORED = "NOT_CENSORED"


def censoring_direction(headroom: Headroom) -> str:
    """Which boundary a block's censored arms sit at, if any.

    `SeedBlock.censoring` counts *how many* arms are pinned; this says **which
    way**, and the two measured scenes differ only in this field. Without it
    `cafe_head_on_v0` (nothing clears 0.40 m) and `cafe_convoy_v0` (everything
    clears 0.30 m) are one indistinguishable `BOTH_ARMS_CENSORED`, and the
    remedies they imply are opposite: one scene wants an easier margin, the
    other a harder one.
    """
    rates = [arm.unsafe_rate for arm in (headroom.a, headroom.b)]
    at_floor = sum(1 for r in rates if r == 0.0)
    at_ceiling = sum(1 for r in rates if r == 1.0)
    if not at_floor and not at_ceiling:
        return NOT_CENSORED
    if at_floor and at_ceiling:
        return MIXED_CENSORING
    return FLOOR_CENSORED if at_floor else CEILING_CENSORED


def disjoint_arms(sweep: MarginSweep) -> bool:
    """Whether the two arms' clearance ranges do not meet at all.

    Strictly stronger than `MarginSweep.NO_TWO_SIDED_MARGIN`, which the band's
    `w ∈ {75, 100}` also return on a *positive* overlap. A negative
    `arm_overlap` means no threshold is interior to both arms even in the
    pooled ensemble, so no seed count and no re-grading reaches one.
    """
    return sweep.arm_overlap < 0.0
