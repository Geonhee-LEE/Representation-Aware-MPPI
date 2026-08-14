# SPDX-License-Identifier: BSD-3-Clause
"""Does the sampler survive the weight at which `w_voo` finally becomes audible?

D-265 and D-266 left two *different* collapses on the table and no reading that
tells them apart:

- **Ratio collapse** (D-265, `cafe_obstacle_crossing_v0`): the audibility ratio
  peaks at `w = 50` and falls back to `0.0488` at `200`. The cause was measured
  and is in the *denominator* — `rest_median` jumps `117 → 10183` (87x) because
  a loud arm steers into the geometry where `w_collision` detonates.
- **ESS collapse** (D-027): pushing a weight far enough degenerates the softmax
  — the effective sample size falls out of its admissible band and the "planner"
  is following one or two rollouts. D-027 put that ceiling at `6.19x`.

These are not the same failure, and on `cafe_obstacle_crossing_v0` they cannot
be separated: the ratio dies there, so any ESS reading at `w = 200` is taken on
a run whose ratio already collapsed for an unrelated reason.

`cafe_freezing_v0` is the scene that separates them. D-266 measured its ladder
as **monotone rising, with no ratio collapse at all** — `0.0581 → 0.1662 →
0.3841 → 0.8924 → 3.2644`, and a `rest_median` that moves only `52.9 → 216`
(4.1x, versus 87x on the reference). So the ratio's own denominator is quiet
right up to `w = 200`, where the channel is audible by a factor of 32 over the
`0.1` bar. That makes it the one place this branch can ask D-027's question
cleanly: **at the weight where the attract channel is finally loud, is the
sampler still weighting more than one rollout?**

## The two answers mean opposite things for `ARM_SCALE`

- `ESS_HELD` — the ladder's top rung is a usable operating point on this scene.
  D-266's finding (no common audible weight across scenes) stands, but the
  obstruction is scene-disjointness alone, not a sampler ceiling sitting under
  every candidate scale.
- `ESS_COLLAPSED` — the audible region on this scene is bought by softmax
  degeneracy, and `cafe_freezing_v0`'s monotone rise is an artefact of the same
  class D-265 found on the reference scene, just relocated from the ratio's
  denominator to the sampler. The audible set would then be empty on *this*
  scene too, for a second and independent reason.

## What was measured: neither answer — the premise was wrong

`ESS_DEGENERATE_THROUGHOUT`. Median ESS is **1.0000** at `w ∈ {20, 50, 200}`,
`1.0053` at `5`, and `1.8749` at `1`, against a band of `(12.8, 128.0)` for
`K = 256`. The sampler is weighting **one rollout** — not at the top of the
ladder, but at *every* rung, including `w = 1` where the attract channel is
inaudible (`ratio 0.0581`) and the arm is therefore doing almost nothing.

That rules out D-027's ceiling as the explanation, and the direction of the
one non-degenerate reading is the argument: ESS is *highest* at the quietest
rung and falls to exactly 1.0 as the weight rises. If the arm were driving the
collapse, `w = 1` would sit in band and fall out later. It does not — it starts
at `1.87`, already 6.8x below the floor. **Whatever collapsed this softmax was
there before the epistemic arm was turned up**, so the honest reading is that
this scene was run at a temperature that does not weight, and the verdict says
so in its own name rather than borrowing D-027's.

The consequence lands on D-266, not on this module: `cafe_freezing_v0`'s
"monotone rise to `3.2644` with no collapse" — the property that made it the
separating scene — was measured on runs whose planner was following a single
rollout. The ratio arithmetic is unaffected (it is a leave-one-out read on the
cost field, not on the weights), but the *trajectory* those costs were
evaluated along is not a planned one in any meaningful sense. `lam` for this
scene is the thing to measure next; `calibrate_lam` exists and this ladder
never called it.

## What this module does not do

It does not re-derive the ratio. D-266 measured that and the numbers live in
`arm_audibility.SCENE_CURVES`; re-computing them here would be the D-047 shape
(one quantity, two statements free to drift). This module reads ESS off the
same isolation and *pairs* the two readings, so a rung carries both numbers or
neither.

It also does not pick `ARM_SCALE`. D-266 established that no reading taken on
the scenes available here transfers to `cafe_blind_corner_v0`, and that scope
is unchanged by this measurement — a sampler ceiling measured on `freezing` is
a fact about `freezing`. The scale pick stays behind PR #68.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ab import ess_band, run_arm
#: `AUDIBLE_RATIO` is imported, never restated — a caller reading `audible`
#: here and `grade` there must not pick up two different bars (D-047).
from .arm_audibility import AUDIBLE_RATIO, EPISTEMIC_CHANNELS, SCENE_CURVES

#: The scene D-266 measured as monotone-rising with a quiet denominator — the
#: only one of the three where a top-rung ESS reading is not confounded by the
#: ratio having already collapsed for a different reason.
PEAK_SCENE = "cafe_freezing_v0"

#: Measured ladder — `(w_voo, median ESS, K, reached_goal)` on `PEAK_SCENE`
#: in :data:`ISOLATION` at seed 0, paired rung-for-rung with D-266's ratios.
#: Recorded rather than recomputed on import: five closed-loop runs (~13 s
#: each), and the shape is the finding. Re-take with :func:`sweep_ess`.
#:
#: The admissible band at `K = 256` is `(12.8, 128.0)`. **Every rung is below
#: its floor, and the quietest rung is the closest to it.**
MEASURED_ESS: tuple[tuple[float, float, int, bool], ...] = (
    (1.0,     1.8749, 256, True),
    (5.0,     1.0053, 256, True),
    (20.0,    1.0000, 256, True),
    (50.0,    1.0000, 256, True),
    (200.0,   1.0000, 256, True),
)

#: The isolation every rung is taken in — identical to `arm_audibility.grade`
#: and to D-266's ladder, so the ESS reading and the ratio reading describe the
#: same controller configuration.
ISOLATION = {"w_risk": 0.0, "k_margin_per_sigma": 0.0}


@dataclass(frozen=True)
class Rung:
    """One ladder point: the sampler reading paired with D-266's ratio."""

    weight: float
    median_ess: float
    n_samples: int
    reached_goal: bool
    ratio: float | None = None

    @property
    def band(self) -> tuple[float, float]:
        return ess_band(self.n_samples)

    @property
    def ess_in_band(self) -> bool | None:
        """`None` when the run reported no ESS — unknown, not compliant.

        The tri-state is `ab.ArmRun`'s and is kept for its reason: a controller
        that logged nothing has an *unmeasured* ESS, and folding that into
        `False` would report a collapse nobody observed.
        """
        if not self.n_samples or self.median_ess != self.median_ess:
            return None
        lo, hi = self.band
        return bool(lo <= self.median_ess <= hi)

    @property
    def audible(self) -> bool | None:
        """Did D-266's ratio clear the `0.1` bar at this weight?"""
        if self.ratio is None:
            return None
        return bool(self.ratio >= AUDIBLE_RATIO)


def _ratios(scene: str = PEAK_SCENE) -> dict[float, float]:
    """D-266's measured `(weight -> ratio)` for `scene`, read not retyped."""
    return {float(w): float(r) for w, r, _rest in SCENE_CURVES[scene]}


def sweep_ess(scenario, weights=None, *, seed: int = 0,
              channel: str = "w_voo", scene: str = PEAK_SCENE) -> tuple[Rung, ...]:
    """Take the ESS ladder in D-266's isolation, pairing each rung with its ratio.

    One closed-loop run per weight (~13 s each), so this is a minutes-scale
    call and no test walks it — :data:`MEASURED_ESS` caches the result the same
    way `arm_audibility.MEASURED_CURVE` caches the ratios.

    `weights` defaults to exactly the weights D-266 measured the ratio at, so
    every rung can carry both numbers. Passing a weight D-266 did not measure
    is allowed and yields `ratio=None` — an unpaired rung, which `verdict`
    counts as unresolved rather than silently treating as inaudible.
    """
    ratios = _ratios(scene)
    ladder = tuple(sorted(ratios)) if weights is None else tuple(float(w) for w in weights)
    out = []
    for w in ladder:
        arm = run_arm(scenario, "risk_mppi", seed,
                      **{channel: float(w)},
                      **{c: 0.0 for c in EPISTEMIC_CHANNELS if c != channel},
                      **ISOLATION)
        out.append(Rung(weight=float(w), median_ess=arm.median_ess,
                        n_samples=arm.n_samples, reached_goal=arm.reached_goal,
                        ratio=ratios.get(float(w))))
    return tuple(out)


def verdict(rungs) -> dict:
    """Did the sampler hold where the channel became audible?

    Reports the two questions separately rather than as one flag, because they
    fail independently: a ladder can hold ESS everywhere and never become
    audible, and it can become audible only on rungs whose ESS has left the
    band. Only the second is D-027's ceiling.
    """
    rungs = tuple(rungs)
    if not rungs:
        return {"verdict": "NO_RUNGS", "audible_rungs": (), "held": None}

    unknown = tuple(r.weight for r in rungs if r.ess_in_band is None)
    audible = tuple(r for r in rungs if r.audible)
    out_of_band = tuple(r.weight for r in rungs if r.ess_in_band is False)

    if unknown:
        name = "ESS_UNMEASURED"
    elif len(out_of_band) == len(rungs):
        # Out of band at *every* rung, including ones below the audibility bar.
        # This is not D-027's ceiling and must not be reported as one: nothing
        # fell, because nothing was ever in band. See the module docstring.
        name = "ESS_DEGENERATE_THROUGHOUT"
    elif not audible:
        name = "NEVER_AUDIBLE"
    elif all(r.ess_in_band for r in audible):
        name = "ESS_HELD"
    else:
        name = "ESS_COLLAPSED"

    return {
        "verdict": name,
        "scene": PEAK_SCENE,
        "audible_rungs": tuple(r.weight for r in audible),
        "out_of_band_rungs": out_of_band,
        "unmeasured_rungs": unknown,
        "held": None if unknown else (name == "ESS_HELD"),
        # True only when the ladder contains an in-band rung to fall from, so
        # a `False` here says the ladder cannot address D-027 at all.
        "can_address_d027_ceiling": bool(
            not unknown and len(out_of_band) < len(rungs)),
        # The scope D-266 fixed and this measurement does not widen.
        "transfers_to_ab_scene": False,
        "ab_scene_blocked_by": "PR #68 (unmerged)",
    }
