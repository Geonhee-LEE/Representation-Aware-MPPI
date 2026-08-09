# SPDX-License-Identifier: BSD-3-Clause
"""Is the declared margin the instrument at fault — or only convoy's?

STATE's standing suspicion after D-160 was that the acceptance yamls, not the
controllers, produce the repo's uniform `NONE_TWO_SIDED`: *"Neither scene's
declared `min_distance_to_obstacle` sits inside its own clearance distribution,
and if that holds for `cafe_obstacle_crossing_v0` too then the acceptance yaml
is the finding, not the arms."*

Crossing has never been walked, so the census this module can close has a
denominator of **2**, and on those two the suspicion is **half right and half
wrong**. (Until D-163 the reason was that it *could* not be walked —
`scene_transplant.crossing_screen` returned `NO_RUNG_TRANSPLANTS` 0/4. It now
returns `PARTIAL_TRANSPLANT` 1/4: the scene is walkable at `w = 250`, and the
denominator here stays 2 only because nobody has spent those 64 runs yet. That
is a *schedulable* gap, where the previous one was a closed door.)

**Convoy: the margin really is outside its own distribution.** 0.30 m against a
pooled range of [0.8914, 1.2066] — every run clears it by at least 0.59 m. No
re-grading, seed count, or controller change makes that margin discriminate,
and the diagnosis "the acceptance yaml is the finding" is exactly right *here*.

**head_on: it is not, at any rung.** 0.40 m is interior to the pooled 32-seed
range at all four of the band's weights, and interior to **both arms' ranges**
at `w ∈ {150, 250}`::

    rung      stock range        risk range         margin interior to both?
    w =  75   [0.1597, 0.3176]   [0.3100, 0.4710]   no  (stock ceiling)
    w = 100   [0.2216, 0.3705]   [0.3606, 0.5370]   no  (stock ceiling)
    w = 150   [0.2808, 0.4959]   [0.2237, 0.6196]   **yes**
    w = 250   [0.3811, 0.6651]   [0.3472, 0.7481]   **yes**

So the band's declared margin is well placed on half its rungs, and D-157's
`NONE_TWO_SIDED` cannot be blamed on it there.

**What the gap between those two rows is.** Interiority is being asked at two
different scopes and they do not agree: `w ∈ {150, 250}` are interior at the
**rung** (32 pooled seeds per arm) and still censored at the **block** (the two
16-seed halves D-157 unions over). A margin can sit inside an arm's full range
while sitting outside one of its halves, and that is not a rounding artefact —
it is the whole 2/4-vs-0/4 delta. `PlacementCensus.scope_disagreement` names
the rungs where it happens rather than letting a reader pick the flattering
scope, because the pooled reading is the one that makes the band look
two-sided.

The consequence for the successor question is that the two scenes need
**different repairs**, and neither is "re-declare the margin" alone: convoy's
margin is mis-declared, head_on's is not and its censoring is a seed-count and
effect-size fact (D-158). One verdict, three causes now.

Reported, never thresholded (D-044). Nothing here asserts that any margin is
well placed — the readings are today's and would become permanent reds the
moment a scene is re-declared or re-walked. No simulation runs; the clearances
are the constants D-152/153/155/160 recorded.
"""

from __future__ import annotations

from dataclasses import dataclass

from .separation_reproduction import Reproduction

#: The declared margin lies strictly inside this arm's recorded clearance
#: range: some runs are unsafe, some are safe, so the margin discriminates.
INTERIOR = "INTERIOR"

#: Every recorded clearance is above the margin — the arm is pinned at a floor
#: and the margin is too easy to say anything about it.
ABOVE_ALL = "ABOVE_ALL"

#: Every recorded clearance is below the margin — a ceiling; the margin is too
#: hard.
BELOW_ALL = "BELOW_ALL"


def _placement(values: tuple[float, ...], margin: float) -> str:
    lo, hi = min(values), max(values)
    if lo < margin < hi:
        return INTERIOR
    return ABOVE_ALL if lo >= margin else BELOW_ALL


@dataclass(frozen=True)
class ArmPlacement:
    """Where one arm's clearance range sits relative to the declared margin."""

    arm: str
    clearances: tuple[float, ...]
    margin: float

    def __post_init__(self) -> None:
        if not self.clearances:
            raise ValueError(
                f"arm {self.arm!r} has no recorded clearances; a placement "
                "over an empty range reads as 'not interior', which is the "
                "empty-population-reads-as-clean shape (D-107)"
            )

    @property
    def span(self) -> tuple[float, float]:
        return min(self.clearances), max(self.clearances)

    @property
    def verdict(self) -> str:
        return _placement(self.clearances, self.margin)

    @property
    def interior(self) -> bool:
        return self.verdict == INTERIOR


#: The margin is interior to both arms' full recorded ranges at this rung.
WELL_PLACED = "WELL_PLACED"

#: Interior to at least one arm but not both — the rung is one-sided.
ONE_ARM_ONLY = "ONE_ARM_ONLY"

#: Interior to neither arm.
MISPLACED = "MISPLACED"


@dataclass(frozen=True)
class RungPlacement:
    """One recorded rung's margin placement, at rung and at block scope.

    Both scopes are carried because they disagree and the disagreement is the
    finding; a single `interior` boolean would have to pick one, and whichever
    it picked would be the answer to a question the reader did not ask.
    """

    scenario: str
    weight: float
    margin: float
    reproduction: Reproduction

    @property
    def arms(self) -> tuple[ArmPlacement, ArmPlacement]:
        """Placement per arm over the **pooled** seeds of both blocks."""
        ref, rep = self.reproduction.reference, self.reproduction.replication
        out = []
        for a, b in ((ref.headroom.a, rep.headroom.a),
                     (ref.headroom.b, rep.headroom.b)):
            out.append(ArmPlacement(arm=a.arm,
                                    clearances=tuple(a.clearances)
                                    + tuple(b.clearances),
                                    margin=self.margin))
        return out[0], out[1]

    @property
    def verdict(self) -> str:
        a, b = self.arms
        n = sum(1 for arm in (a, b) if arm.interior)
        if n == 2:
            return WELL_PLACED
        return ONE_ARM_ONLY if n == 1 else MISPLACED

    @property
    def block_interior(self) -> bool:
        """Whether the margin is interior to **every arm of every block**.

        The scope D-157's `Reproduction.censored` actually grades. Strictly
        stronger than `verdict == WELL_PLACED`: pooling two 16-seed halves can
        manufacture an interior range that neither half has.
        """
        for block in (self.reproduction.reference, self.reproduction.replication):
            for arm in (block.headroom.a, block.headroom.b):
                if _placement(tuple(arm.clearances), self.margin) != INTERIOR:
                    return False
        return True

    @property
    def scope_disagreement(self) -> bool:
        """Interior when the seeds are pooled, censored when they are not."""
        return self.verdict == WELL_PLACED and not self.block_interior

    def __str__(self) -> str:
        return f"w={self.weight:g} :: {self.verdict}"


#: Every measured rung's margin is interior to both arms (pooled).
ALL_WELL_PLACED = "ALL_WELL_PLACED"

#: At least one rung's margin is interior to neither arm.
SOME_MISPLACED = "SOME_MISPLACED"

#: No rung is misplaced, but not all are well placed either.
SOME_ONE_SIDED = "SOME_ONE_SIDED"


@dataclass(frozen=True)
class PlacementCensus:
    """Margin placement across every rung this repo has actually walked."""

    rungs: tuple[RungPlacement, ...]

    def __post_init__(self) -> None:
        if not self.rungs:
            raise ValueError(
                "a placement census over no rungs cannot say whether any "
                "margin is well declared; name the walked rungs"
            )

    @property
    def coverage(self) -> tuple[int, int]:
        return (sum(1 for r in self.rungs if r.verdict == WELL_PLACED),
                len(self.rungs))

    @property
    def misplaced(self) -> tuple[tuple[str, float], ...]:
        return tuple((r.scenario, r.weight) for r in self.rungs
                     if r.verdict == MISPLACED)

    @property
    def scope_disagreement(self) -> tuple[tuple[str, float], ...]:
        """Rungs that read interior pooled and censored per block."""
        return tuple((r.scenario, r.weight) for r in self.rungs
                     if r.scope_disagreement)

    @property
    def verdict(self) -> str:
        if self.misplaced:
            return SOME_MISPLACED
        n, total = self.coverage
        return ALL_WELL_PLACED if n == total else SOME_ONE_SIDED

    def __str__(self) -> str:
        n, total = self.coverage
        return f"{self.verdict} {n}/{total} well placed"


def census() -> PlacementCensus:
    """The five walked rungs: the band's four plus convoy's one.

    `cafe_obstacle_crossing_v0` contributes nothing — it has never been walked,
    so its declared margin is unjudgeable here. Since D-163 that is a gap in
    the *schedule* rather than in what is possible: the screen now says the
    scene is walkable at `w = 250`, so this census has a rung it could grow by
    one, which the 0/4 reading said it never would. Naming that out loud rather
    than letting a 3-scene population quietly become a 2-scene one is D-159's
    rule.
    """
    from .scene_transplant import (
        CONVOY_MARGIN,
        CONVOY_SCENARIO,
        CONVOY_WEIGHT,
        convoy_w75_walk,
    )
    from .scorable_band import PUBLISHED_MARGIN, PUBLISHED_SCENARIO
    from .separation_reproduction import (
        w75_reproduction,
        w100_reproduction,
        w150_reproduction,
        w250_reproduction,
    )

    band = ((75.0, w75_reproduction()), (100.0, w100_reproduction()),
            (150.0, w150_reproduction()), (250.0, w250_reproduction()))
    rungs = [
        RungPlacement(scenario=PUBLISHED_SCENARIO, weight=w,
                      margin=PUBLISHED_MARGIN, reproduction=rep)
        for w, rep in band
    ]
    rungs.append(RungPlacement(scenario=CONVOY_SCENARIO, weight=CONVOY_WEIGHT,
                               margin=CONVOY_MARGIN,
                               reproduction=convoy_w75_walk()))
    return PlacementCensus(rungs=tuple(rungs))


def main(argv: list[str] | None = None) -> int:
    c = census()
    print(c)
    for r in c.rungs:
        a, b = r.arms
        print(f"  {r.scenario} {r}")
        for arm in (a, b):
            lo, hi = arm.span
            print(f"    {arm.arm:10s} [{lo:.4f}, {hi:.4f}] {arm.verdict}")
        if r.scope_disagreement:
            print("    ^ interior pooled, censored per block")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
