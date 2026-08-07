# SPDX-License-Identifier: BSD-3-Clause
"""Near-miss scoring: the margin the collision count cannot see.

Why this exists
---------------
D-119's matrix reported, on the same 64 seeds, two numbers that are both true
and only one of which is reassuring:

    collision_rate = 0.0000
    min_clearance  = 0.0016 m

Nothing collided, and something passed within **1.6 mm** (`stock_mppi` on
`cafe_head_on_v0`). The north star names "near-miss <= Y" as a first-class
acceptance term; the harness scored that 1.6 mm pass as a clean success,
because a collision counter saturates precisely where the interesting safety
question starts. A metric whose best possible reading is "did not quite touch"
cannot distinguish a controller that keeps half a metre from one that is one
grid cell from a fatality.

The threshold is the scene's, not ours
--------------------------------------
The tempting move is a module-level `NEAR_MISS_M = 0.1`. It is wrong here: the
shipped scenes already declare what they want, and they disagree —
`cafe_head_on_v0` asks 0.40 m (an oncoming pedestrian), `cafe_convoy_v0` and
`cafe_obstacle_crossing_v0` ask 0.30. A global constant would overrule the
scene that asked for more and flatter the scene that asked for less. So the
threshold is read per-scene from the acceptance block via
`feasibility.declared_margin`, which is the single statement of where that key
lives (D-047).

Undeclared is not zero
----------------------
`cafe_freezing_v0` contains obstacles and declares **no** margin. The
convenient default (`0.0`) makes its near-miss band the empty interval
`[0, 0)`, under which every run is safe and the cell reports a perfect
`0.0000` for free — D-107's empty-population-reads-as-clean, arriving in the
safety headline. So an undeclared margin is `None` and its cell is **excluded
from the near-miss denominator by name**, exactly as `LAM_UNCALIBRATED` cells
are excluded from the avoidance denominator rather than scored at a guessed
temperature (D-119).

Note this is a *third* denominator, not a re-slice of the avoidance one.
Counting collisions needs no threshold; counting near-misses does. So the
near-miss population is a strict subset of the avoidance population, and the
two move independently — `cafe_freezing_v0` is a perfectly good collision
measurement and not a near-miss measurement at all.

`unsafe_rate` is the headline, and `near_miss_rate` is not
----------------------------------------------------------
`near_miss_rate` alone is **not monotone in safety**. Its band is
`[0, margin)`, so a run that degrades from a 1 mm graze into an actual
collision *leaves* the near-miss set and the rate goes **down**. A controller
could improve its near-miss rate by colliding more. That is not a hypothetical
about a future controller — it is a property of the interval, and
`test_near_miss.py` pins it in both directions.

`unsafe_rate = (near_miss + collision) / n` is the same band opened downward
to `(-inf, margin)`, so it is monotone: any degradation in clearance can only
move a run into it. That is the number a headline may carry. The decomposition
is still reported, because "3 grazes" and "3 collisions" call for different
work — but the scalar that gets compared across controllers is the monotone
one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .feasibility import declared_margin

#: Per-run verdicts, safest first.
SAFE = "SAFE"
NEAR_MISS = "NEAR_MISS"
COLLISION = "COLLISION"


def is_scorable_margin(margin: float | None) -> bool:
    """Can this margin produce a near-miss finding at all?

    `None` (undeclared) and any non-positive value both give an empty band
    `[0, margin)`, under which no run can ever be a near miss and the cell
    reports a clean sheet it never earned. Both are refusals, and they are the
    same refusal — a threshold that cannot be crossed is not a threshold.
    """
    return margin is not None and float(margin) > 0.0


def classify(clearance: float, margin: float) -> str:
    """Grade one run's minimum clearance against the scene's declared margin.

    Boundary is closed on the safe side: `clearance == margin` is `SAFE`, since
    the scene asked for *at least* that much. Collision is threshold-free —
    `clearance < 0` is interpenetration whatever the scene declared — which is
    why it is tested first and why a cell with no declared margin can still be
    scored for collisions.
    """
    if not is_scorable_margin(margin):
        raise ValueError(
            f"margin {margin!r} yields an empty near-miss band; "
            "a cell with no scorable margin is excluded by name, not scored"
        )
    if clearance < 0.0:
        return COLLISION
    return NEAR_MISS if clearance < float(margin) else SAFE


@dataclass(frozen=True)
class NearMissStats:
    """Safety decomposition of one seed ensemble against one margin."""

    n: int
    margin: float
    safe: int
    near_misses: int
    collisions: int

    @property
    def near_miss_rate(self) -> float:
        """Fraction that grazed. **Non-monotone in safety** — see the module
        docstring. Report it, do not rank on it."""
        return self.near_misses / self.n if self.n else float("nan")

    @property
    def collision_rate(self) -> float:
        return self.collisions / self.n if self.n else float("nan")

    @property
    def unsafe_rate(self) -> float:
        """Fraction that came closer than the scene allows, collisions
        included. Monotone in clearance, so this is the comparable scalar."""
        if not self.n:
            return float("nan")
        return (self.near_misses + self.collisions) / self.n


def score(clearances: Iterable[float], margin: float) -> NearMissStats:
    """Classify an ensemble of per-run minimum clearances."""
    verdicts = [classify(c, margin) for c in clearances]
    return NearMissStats(
        n=len(verdicts),
        margin=float(margin),
        safe=verdicts.count(SAFE),
        near_misses=verdicts.count(NEAR_MISS),
        collisions=verdicts.count(COLLISION),
    )


def margin_for(scenario) -> float | None:
    """The scene's declared margin, or `None`. Thin alias so callers scoring
    safety do not import the *feasibility screen* to ask a safety question."""
    return declared_margin(scenario)


def score_runs(runs: Sequence, margin: float) -> NearMissStats:
    """`score` over anything with a `.clearance` (e.g. `ab.ArmRun`)."""
    return score([r.clearance for r in runs], margin)
