# SPDX-License-Identifier: BSD-3-Clause
"""Q-148's both-on arm: pick the replacement ratio, at the radius the A/B runs at.

`both_on_cell` re-placed the published cell on the planner's support and stopped
one step short on purpose — it returns the sign-robust bracket and the contended
ratio and *does not pick*, leaving the choice as Q-148's open question. This
module picks, and the pick turns out not to be the coin-flip the question's
framing implied. Two measurements settle it.

Measurement 1 — the headline was taken at the wrong geometry
-------------------------------------------------------------

D-260 reports the published cell (`0.3587`) as robustly `ATTRACT`: 5 of 7 radii,
`INDETERMINATE` at `r=0.3`, `UNPLACEABLE` at `r=1.25`. But Q-148's A/B does not
run on a radius sweep. It runs on **one scene** — `cafe_blind_corner_v0`, the
occlusion scenario the question names as its next action — and that scene's
occluder wall is five overlapping discs of radius **0.3** (`SCENE_RADIUS`).

`r=0.3` is the single radius at which the published cell does *not* read
`ATTRACT`. Its band `[0.1704, 0.5770]` is the widest in the set (width `0.4066`,
2.07x the `r=0.5` band) and it contains `0.3587`, so at the A/B's own geometry
the published cell is `INDETERMINATE` — neither the cancelling cell D-256 placed
it as, nor the attract cell D-260 corrected it to. D-260's correction is sound
about the radii it surveyed and **silent about the only one that is going to be
run**; the survey's default `r=0.5` is an instrument default, not the scene.

That is not a third sign error on top of two. It is the observation that a
per-radius survey answers a question the A/B never asks unless someone states
which radius the A/B is at, and nobody had.

Measurement 2 — sign-robustness is transferable, contendedness is not
----------------------------------------------------------------------

Across the six posed radii the bands do not share a common point:
`max(band.lo) = 0.6386` (at `r=0.5`) exceeds `min(band.hi) = 0.5770` (at
`r=0.3`), and those two bands are outright **disjoint**. So:

- **no constant ratio is `INDETERMINATE` at every radius** — the contended cell
  exists only per-geometry, as `band.mean(r)`;
- **sign-robust constants do exist** — any ratio `< 0.1704` is `ATTRACT` at
  every posed radius and any ratio `> 0.8347` is `REPEL` at every one.

Read naively that favours a sign-robust pick: it is the only choice that is a
constant of the branch rather than a function of the scene. The naive reading is
wrong, and measurement 2's real content is why.

The pick, and why it is not a coin flip
-----------------------------------------

Q-148 already stated the desideratum, in the sentence that created the fourth
arm: *"both-on 은 상쇄 근 근처에서 잡아야 두 arm 이 실제로 겨루는 cell 이 된다"* —
the both-on cell has to be caught **near the cancelling root** or the two arms
do not actually contend. The arm exists for exactly one reason: the original
three-arm design's both-on cell at 1:1 was, in D-256's words, a disguised re-run
of the repel arm, and D-260 then found the published replacement would have been
a disguised re-run of the *attract* arm.

A sign-robust cell is that same failure a third time, and now by construction: a
ratio outside the bracket puts the summed split on one arm's side for every root
in the band, which is what "this arm dominates the sum" means. Sign-robustness
and duplication are the same property under two names. The fourth arm cannot be
bought at a ratio chosen to guarantee one arm wins the sum, because the whole
point of running it is to find out which arm wins in closed loop.

So the pick is **the contended ratio at the scene's radius** —
`band.mean(0.3) = 0.4121` — and `INDETERMINATE` is accepted as the correct sign
reading for it rather than tuned away. `INDETERMINATE` says the *instrument*
does not resolve which side of zero the cost-field sum is on; it does not say
the A/B is unattributable. The A/B is adjudicated on near-miss and clearance
(Q-148's next action, and D-250's warning off `d_reached`), which are closed-loop
outcomes that need no cost-field sign at all. Trading a resolved sign for a cell
where the arms genuinely contend is the trade this experiment is *for*.

What this costs, stated plainly
---------------------------------

The chosen ratio is a function of the scene, not a constant. Move the A/B to a
different occluder radius and `0.4121` is not the contended cell there — at
`r=0.5` it is robustly `ATTRACT`, the very duplication this pick avoids. That is
a real fragility and it is the price of measurement 2: contendedness does not
transfer, so a scene change forces a re-pick. :func:`transfers_to` is the guard,
so the fragility is checked rather than remembered.

`SCENE_RADIUS` is *quoted*, not imported
------------------------------------------

`cafe_blind_corner_v0.yaml` lives on `p3-blind-corner-occlusion-scenario`
(PR #68, unmerged for eight cycles). Quoting the number keeps this module free of
the unmerged branch — importing it would be the branch-stacking the feasibility
filter forbids. The provenance is recorded here and
:func:`scene_radius_provenance` states what must be re-checked when #68 lands.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import both_on_cell as boc
from .cancelling_stability import DEFAULT_RADII
from .epistemic_sign import ATTRACT, REPEL

#: Occluder radius of `cafe_blind_corner_v0`'s wall discs — the geometry Q-148's
#: A/B actually runs at. Quoted from the scene yaml on PR #68 (`dynamic_obstacles`
#: `wall_0..wall_4`, all `radius: 0.3`), deliberately not imported; see the
#: module docstring's last section.
SCENE_RADIUS = 0.3

#: The two things a both-on cell can be chosen to be. `CONTENDED` is this
#: module's pick; `SIGN_ROBUST` is named so the rejected option has a handle in
#: tests rather than only in prose.
CONTENDED = "CONTENDED"
SIGN_ROBUST = "SIGN_ROBUST"


@dataclass(frozen=True)
class Pick:
    """A chosen both-on cell plus the reading that justifies it."""

    radius: float
    ratio: float
    kind: str
    placement: boc.Placement

    @property
    def sign(self) -> str:
        return self.placement.sign

    @property
    def is_duplicate_of_a_single_arm(self) -> bool:
        """Does the sum sit on one arm's side for every root in the band?

        The property the fourth arm exists to *not* have. True exactly when the
        sign resolves, which is why a sign-robust pick cannot serve here.
        """
        return self.sign in (ATTRACT, REPEL)

    def __str__(self) -> str:  # pragma: no cover - formatting
        return (f"r={self.radius:.2f} ratio={self.ratio:.4f} {self.kind} "
                f"sign={self.sign} duplicate={self.is_duplicate_of_a_single_arm}")


def scene_band(radius: float = SCENE_RADIUS):
    """The root band at the A/B scene's geometry, or `None` if unposed."""
    return boc.rollout_band(radius)


def published_cell_at_scene_radius(radius: float = SCENE_RADIUS) -> boc.Placement | None:
    """D-256's `0.3587` read at the radius the A/B runs at — measurement 1.

    Reads `INDETERMINATE`, against D-260's `ATTRACT` headline, because that
    headline's radii do not include the scene's except as one dissenting row.
    """
    band = scene_band(radius)
    return None if band is None else boc.place_at_ratio(boc.PUBLISHED_RATIO, band)


def pick(radius: float = SCENE_RADIUS) -> Pick | None:
    """The replacement ratio: the contended cell at the scene's radius.

    `None` where the geometry poses no question — a caller must not silently
    fall back to another radius's ratio, which is the substitution measurement 2
    shows is unsound (the bands do not share a point).
    """
    band = scene_band(radius)
    if band is None:
        return None
    ratio = boc.contended_ratio(band)
    return Pick(radius, ratio, CONTENDED, boc.place_at_ratio(ratio, band))


def common_indeterminate_interval(radii=DEFAULT_RADII) -> tuple[float, float] | None:
    """The ratios that are `INDETERMINATE` at *every* posed radius, or `None`.

    Measured `None`: `max(lo) = 0.6386 > min(hi) = 0.5770`. This is measurement
    2's first half and the reason :func:`pick` is parameterised by radius at all
    — were this interval non-empty, a single contended constant would exist and
    the scene's geometry would not need stating.
    """
    bands = [b for b in (boc.rollout_band(r) for r in radii) if b is not None]
    lo, hi = max(b.lo for b in bands), min(b.hi for b in bands)
    return None if lo >= hi else (lo, hi)


def common_sign_robust_halflines(radii=DEFAULT_RADII) -> tuple[float, float]:
    """`(attract_below, repel_above)` holding at *every* posed radius.

    Measurement 2's second half: measured `(0.1704, 0.8347)`, both non-empty.
    Sign-robust constants exist where contended ones do not — which is the
    asymmetry that makes the naive reading of measurement 2 favour the option
    this module rejects on the separate ground that it duplicates an arm.
    """
    bands = [b for b in (boc.rollout_band(r) for r in radii) if b is not None]
    return min(b.lo for b in bands), max(b.hi for b in bands)


def transfers_to(chosen: Pick, radius: float) -> bool:
    """Is `chosen`'s ratio still a contended cell at another geometry?

    The stated fragility, made checkable. Measured `False` for the scene pick at
    `r=0.5` (where `0.4121` is robustly `ATTRACT`), so moving the A/B's scene
    obliges a re-pick rather than a re-use.
    """
    band = boc.rollout_band(radius)
    if band is None:
        return False
    return boc.place_at_ratio(chosen.ratio, band).sign == boc.INDETERMINATE


def scene_radius_provenance() -> dict:
    """What `SCENE_RADIUS` is quoted from, and what to re-check when #68 lands.

    Returned as data rather than left in prose so a future cycle can assert on
    it: if the merged yaml's occluder radius is not this value, every number in
    this module is about a scene that no longer exists.
    """
    return {
        "value": SCENE_RADIUS,
        "source": "eval/scenarios/cafe_blind_corner_v0.yaml",
        "branch": "autoresearch/p3-blind-corner-occlusion-scenario",
        "pr": 68,
        "key": "dynamic_obstacles[*].radius (wall_0..wall_4)",
        "recheck_on_merge": True,
    }


def format_pick() -> str:  # pragma: no cover - manual read
    band = scene_band()
    chosen = pick()
    published = published_cell_at_scene_radius()
    common = common_indeterminate_interval()
    lo, hi = common_sign_robust_halflines()
    return "\n".join([
        f"ratio_pick — Q-148's both-on arm at the A/B scene (r={SCENE_RADIUS})",
        f"  scene band          [{band.lo:.4f}, {band.hi:.4f}] width {band.width:.4f}",
        f"  published {boc.PUBLISHED_RATIO} reads {published.sign} here "
        f"(D-260 headline: ATTRACT, surveyed elsewhere)",
        f"  PICK                {chosen.ratio:.4f}  {chosen.kind}  "
        f"sign={chosen.sign}  duplicate={chosen.is_duplicate_of_a_single_arm}",
        f"  contended constant across radii: "
        f"{'none — bands share no point' if common is None else common}",
        f"  sign-robust constants:  ATTRACT < {lo:.4f}   REPEL > {hi:.4f}",
        f"  transfers to r=0.5: {transfers_to(chosen, 0.5)}",
    ])


if __name__ == "__main__":     # pragma: no cover - manual read
    print(format_pick())
