# SPDX-License-Identifier: BSD-3-Clause
"""The scene axis of the clearance census — and it overturns the branch claim.

:mod:`clearance_census` closed the **seed** axis: no representation arm
out-clears plain `stock_mppi` on any of eight seeds (D-328). Both that reading
and D-327's before it were taken on one scene, `cafe_freezing_v0`, and both said
so. `STATE.md` then named the scene axis "the widest untested edge" and "the one
axis that could still overturn it". This module tests that edge, and the edge
wins: **the claim is scene-scoped, and on a second scene it is false.**

`social_mppi` out-clears plain MPPI on `cafe_cut_in_v0` by `+0.1187 m` in the
eight-seed mean, on **8 of 8 seeds**, worst seed `+0.0573`. That is the same
paired-per-seed test :func:`clearance_census.seed_grade` applies, run to the
same width, and it answers the branch-level question the other way: a
representation arm *has* bought clearance. What D-327/D-328 measured was true of
`cafe_freezing_v0` and is not a property of the arms.

Two further readings fall out, and they cut in opposite directions:

* **`cbf_mppi`'s win is scene-scoped too.** The constraint arm that leads
  `cafe_freezing_v0` `8/8` at `+0.228 m` *loses* on `cafe_cut_in_v0`
  (`-0.0570 m`, seed 0). So the bar D-328 set for the representation arms is
  itself not a fixed bar, and "the constraint buys the clearance" is not a
  scene-independent statement either.
* **Not every seed-0 flip survives the seeds.** `risk_mppi` leads the baseline
  on `cafe_convoy_v0` at seed 0 (`+0.0281 m`) and the ensemble kills it —
  `2/8`, mean `-0.0241 m`. Recorded because it is the control: the same
  procedure that promotes the `cut_in` result demotes this one, so the
  promotion is not an artifact of looking until something won.

Scope, stated before the numbers because it bounds them:

* **Five of eight scenarios can host this measurement at all.**
  `cafe_straight_v0`, `city_curved_v0` and `city_figure8_v0` declare **zero
  obstacles**, so `min_clearance` is `+inf` for every arm and every gap is
  `nan` — the census is not merely uninformative there, it is undefined. See
  :func:`unmeasurable_scenes`, which derives the set by loading the scenarios
  rather than restating it, and :data:`SCENE_OBSTACLES`, which pins it.
* The `cut_in` and `convoy` columns are **one arm each**, paired against the
  baseline across seeds `0..7`. The full 8-arm × 8-seed ensemble was not run on
  these scenes; :data:`SCENE_SEED0` carries the whole registry at seed 0 only.
* One seed-0 flip is left **unmeasured on purpose**: `gap_gated_mppi` leads on
  `cafe_head_on_v0` by `+0.0021 m`. That is a sixth of the `0.0128 m` D-326
  declined to call a regression, so it sits below this repo's own
  discrimination floor and an ensemble on it would be pricing noise.

Cost, measured 2026-08-17 (this branch keeps inheriting estimates that run
15–20× long, so these are clock readings): the seed-0 registry sweep is
`7–34 s` per scene, and a two-arm × 8-seed paired column is `67 s` on
`cafe_cut_in_v0` and `28 s` on `cafe_convoy_v0`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .clearance_census import BASELINE, SEEDS

#: `scene -> number of declared obstacles`, for every scenario in
#: `eval/scenarios/` except the `lam_windows.yaml` table, which is not a
#: scenario. Pinned against :func:`scene_obstacle_counts`, which derives it.
#:
#: The zeros are the load-bearing entries. A clearance census on a scene with no
#: obstacles returns `+inf` for every arm — the arms are not tied there, the
#: question is not posed — and three of the eight scenarios are in that state.
SCENE_OBSTACLES: dict[str, int] = {
    "cafe_convoy_v0": 5,
    "cafe_cut_in_v0": 1,
    "cafe_freezing_v0": 2,
    "cafe_head_on_v0": 1,
    "cafe_obstacle_contested_v0": 5,
    "cafe_obstacle_crossing_v0": 5,
    "cafe_straight_v0": 0,
    "city_curved_v0": 0,
    "city_figure8_v0": 0,
}

#: `scene -> {arm -> min_clearance_m}` at seed 0, `lam = 0.8`, `w_voo = 5` —
#: the operating point of :data:`clearance_census.SHIPPED_ARM_CLEARANCE`, whose
#: `cafe_freezing_v0` column is therefore the same measurement and is *not*
#: duplicated here. Only the four other hostable scenes are recorded.
SCENE_SEED0: dict[str, dict[str, float]] = {
    "cafe_obstacle_crossing_v0": {
        "cbf_mppi": 0.3255, "geometric_mppi": 0.0597, "stock_mppi": 0.0597,
        "essps_mppi": 0.0373, "gap_gated_mppi": 0.0266,
        "frozen_risk_mppi": 0.0167, "risk_mppi": 0.0167, "social_mppi": 0.0049,
    },
    # Measured 2026-08-24 on the scene's first cycle (D-457). Read this column
    # against `cafe_obstacle_crossing_v0` directly above it: the two scenes are
    # identical but for actor schedule phase, so the difference IS the contest.
    # Every arm's clearance is an order of magnitude larger here (0.43-0.73 vs
    # 0.005-0.33) because the contested band is not threadable at cruise and
    # the arms yield instead. The discriminating axis therefore moves off
    # clearance and onto time: trajectory length spans 166 steps
    # (`social_mppi`) to 1001 (`risk_mppi`) at near-identical completion,
    # a 6x spread where crossing_v0's arms were nearly tied.
    "cafe_obstacle_contested_v0": {
        "cbf_mppi": 0.7314, "geometric_mppi": 0.7268, "stock_mppi": 0.7268,
        "social_mppi": 0.6082, "frozen_risk_mppi": 0.5417, "risk_mppi": 0.5417,
        "essps_mppi": 0.4626, "gap_gated_mppi": 0.4323,
    },
    "cafe_convoy_v0": {
        "cbf_mppi": 0.5573, "frozen_risk_mppi": 0.4287, "risk_mppi": 0.4287,
        "geometric_mppi": 0.4006, "stock_mppi": 0.4006, "social_mppi": 0.3873,
        "gap_gated_mppi": 0.3637, "essps_mppi": 0.2874,
    },
    "cafe_cut_in_v0": {
        "social_mppi": 0.3783, "geometric_mppi": 0.2601, "stock_mppi": 0.2601,
        "cbf_mppi": 0.2031, "gap_gated_mppi": 0.0654,
        "frozen_risk_mppi": 0.0377, "risk_mppi": 0.0377, "essps_mppi": 0.0271,
    },
    "cafe_head_on_v0": {
        "cbf_mppi": 0.2003, "gap_gated_mppi": 0.0146, "geometric_mppi": 0.0125,
        "stock_mppi": 0.0125, "frozen_risk_mppi": 0.0095, "risk_mppi": 0.0095,
        "essps_mppi": 0.0090, "social_mppi": 0.0039,
    },
}

#: `(scene, arm) -> (baseline_column, arm_column)`, each a `SEEDS`-wide tuple of
#: minimum clearance in metres at seeds `0..SEEDS-1`.
#:
#: Two entries, chosen before they were run: the largest seed-0 flip
#: (`cut_in`/`social`) and the smallest one above the discrimination floor
#: (`convoy`/`risk`). Recording both is what makes the first a result rather
#: than a search — the procedure that confirms one refutes the other.
PAIRED_ENSEMBLE: dict[tuple[str, str], tuple[tuple[float, ...], tuple[float, ...]]] = {
    ("cafe_cut_in_v0", "social_mppi"): (
        (0.2601, 0.1652, 0.1652, 0.2777, 0.2175, 0.2191, 0.2604, 0.2595),
        (0.3783, 0.3241, 0.3046, 0.3350, 0.3727, 0.3688, 0.3554, 0.3352),
    ),
    ("cafe_convoy_v0", "risk_mppi"): (
        (0.4006, 0.4334, 0.4021, 0.3792, 0.4425, 0.4293, 0.4337, 0.4501),
        (0.4287, 0.3991, 0.3297, 0.4083, 0.4271, 0.3665, 0.3796, 0.4395),
    ),
}

#: The seed-0 flip left deliberately unmeasured, and the floor that excludes it.
#: `0.0128 m` is the gap D-326 declined to call a regression; a `+0.0021 m` lead
#: is a sixth of it. Named so the decision is a constant a later cycle can
#: revisit, not a sentence in a docstring.
DISCRIMINATION_FLOOR_M = 0.0128
UNMEASURED_FLIP: tuple[str, str, float] = ("cafe_head_on_v0", "gap_gated_mppi", 0.0021)


def scene_obstacle_counts() -> dict[str, int]:
    """Derive :data:`SCENE_OBSTACLES` by loading every scenario.

    Derived rather than restated for D-047's reason: the population grows every
    time someone adds a yaml, and a hand-written census of a growing population
    is the failure this repo keeps paying for. The test pins the two equal.
    """
    import glob
    import os

    from .scenario import load_scenario

    out: dict[str, int] = {}
    for path in sorted(glob.glob("eval/scenarios/*.yaml")):
        name = os.path.basename(path)[:-len(".yaml")]
        if name == "lam_windows":  # a parameter table, not a scenario
            continue
        out[name] = len(load_scenario(path).obstacles)
    return out


def unmeasurable_scenes() -> tuple[str, ...]:
    """Scenes where a clearance census is undefined, not merely uninformative.

    No obstacles means `min_clearance` is `+inf` for every arm, so every gap is
    `nan`. Returned as a set of names rather than a boolean so a caller that
    walks scenarios can skip them by construction instead of filtering `nan`
    out of its results afterwards — the second form silently reports a smaller
    population as though it were the whole one (D-241).
    """
    return tuple(s for s, n in sorted(SCENE_OBSTACLES.items()) if n == 0)


def hostable_scenes() -> tuple[str, ...]:
    """Scenes that can host the census — the complement of the above."""
    return tuple(s for s, n in sorted(SCENE_OBSTACLES.items()) if n > 0)


@dataclass(frozen=True)
class PairedVerdict:
    """One arm's standing against the baseline across seeds, on one scene.

    Deliberately the same shape as :class:`clearance_census.SeedVerdict`, and
    computed the same paired-per-seed way, so the two scenes' answers are
    comparable rather than merely adjacent.
    """

    scene: str
    arm: str
    mean_gap: float
    worst_gap: float
    best_gap: float
    beats_baseline: int

    @property
    def sign_is_stable(self) -> bool:
        """Does the gap keep its sign on every seed?"""
        return (self.best_gap < 0.0) or (self.worst_gap > 0.0)

    @property
    def buys_clearance(self) -> bool:
        """Does this arm out-clear the baseline, stably, on this scene?

        Both conditions, not just the mean: a positive mean with a mixed sign
        is what `cafe_convoy_v0` would have looked like had its seed-0 lead
        been slightly larger, and that is not a result.
        """
        return self.mean_gap > 0.0 and self.sign_is_stable


def paired_grade(scene: str, arm: str) -> PairedVerdict:
    """Grade one :data:`PAIRED_ENSEMBLE` entry."""
    base, col = PAIRED_ENSEMBLE[(scene, arm)]
    gaps = [a - b for a, b in zip(col, base)]
    return PairedVerdict(
        scene=scene,
        arm=arm,
        mean_gap=sum(gaps) / len(gaps),
        worst_gap=min(gaps),
        best_gap=max(gaps),
        beats_baseline=sum(g > 0.0 for g in gaps),
    )


def representation_buys_clearance_somewhere() -> bool:
    """The branch-level question, widened from one scene to two.

    :func:`clearance_census.any_representation_arm_wins_on_any_seed` asks it of
    eight seeds on one scene and measures `False`. This asks it across the
    scenes measured here and measures **`True`** — which is why the negative
    result has to be re-scoped rather than restated.
    """
    return any(paired_grade(s, a).buys_clearance for s, a in PAIRED_ENSEMBLE)


def seed0_winners(scene: str) -> tuple[str, ...]:
    """Arms out-clearing the baseline on `scene` at seed 0, best first.

    Seed 0 only — :data:`PAIRED_ENSEMBLE` exists because two of these did not
    survive being asked again at seven more seeds.
    """
    col = SCENE_SEED0[scene]
    base = col[BASELINE]
    return tuple(a for a, c in sorted(col.items(), key=lambda kv: -kv[1])
                 if c > base)


def format_grade() -> str:
    """One-screen scene census. For a human reading the cycle's output."""
    lines = [
        f"scene census — seed 0, lam=0.8 "
        f"({len(hostable_scenes())}/{len(SCENE_OBSTACLES)} scenes hostable)",
        "",
        f"unmeasurable (0 obstacles): {', '.join(unmeasurable_scenes())}",
        "",
        f"{'scene':<28}{'baseline':>10}  seed-0 arms above it",
    ]
    for scene in sorted(SCENE_SEED0):
        won = seed0_winners(scene)
        lines.append(f"{scene:<28}{SCENE_SEED0[scene][BASELINE]:>10.4f}  "
                     f"{', '.join(won) if won else '(none)'}")
    lines += ["", f"paired ensembles ({SEEDS} seeds, gap = arm - baseline):"]
    for scene, arm in sorted(PAIRED_ENSEMBLE):
        v = paired_grade(scene, arm)
        lines.append(f"  {scene:<26}{arm:<18}mean {v.mean_gap:+.4f}  "
                     f"worst {v.worst_gap:+.4f}  {v.beats_baseline}/{SEEDS}  "
                     f"buys_clearance={v.buys_clearance}")
    lines += [
        "",
        f"representation_buys_clearance_somewhere = "
        f"{representation_buys_clearance_somewhere()}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(format_grade())
