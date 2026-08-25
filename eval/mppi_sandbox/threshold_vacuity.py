# SPDX-License-Identifier: BSD-3-Clause
"""Does a declared safety threshold sit where the arms actually are? — STATE #1.

D-356 found `cafe_convoy_v0`'s `min_distance_to_obstacle: 0.30` grading nothing:
the worst clearance either arm of the branch's headline reached was `0.3297 m`,
so the criterion could not fail, and a `p_o` built on it integrated over an
empty band. `STATE.md` then generalised the worry — *"how much of this project's
pass/fail signal is structurally incapable of failing"* — and named the cheap
discharge: compare every scene's declared threshold against the clearance range
its arms actually attain, using tables already on disk.

This is that sweep, and it returns three things the one-scene reading could not.

**1. Vacuity has two directions, and the branch had only ever seen one.**
`cafe_head_on_v0` declares `min_distance_to_obstacle: 0.40` and the *best* arm
in the registry attains `0.2003 m` (`cbf_mppi`, seed 0); the other seven land in
`0.0039`–`0.0146`. So the criterion cannot **pass** — all 8/8 arms fail it, on
every run, and have since the scene landed. That is the same defect class as
D-241/D-344 and D-356, mirrored: a threshold outside the attained range grades
nothing whichever side it falls on, and a `VACUOUS_FAIL` is the more dangerous
of the two because it reads as *the scene is hard* rather than as *the scene is
broken*. `cafe_head_on_v0` is the scene D-131 measured this project's first
scored mechanism claim on.

**2. D-356's verdict is population-scoped, and this widens it rather than
confirming it.** On `cafe_convoy_v0` the declared `0.30` is **not** vacuous over
the eight-arm registry — `essps_mppi` attains `0.2874 m` at seed 0 and fails it.
It is vacuous over the *two* arms D-356 measured (`risk_mppi` / `stock_mppi`,
worst `0.3297`). Both readings are correct about their own population, and the
scene-level statement is the weaker one: the threshold discriminates, just not
between the arms the headline compared. Recorded because the natural
generalisation of D-356 — "convoy's threshold grades nothing" — is false, and
this module would have shipped it as true had it walked only the headline pair.

**3. One scene with obstacles declares no clearance threshold at all.**
`cafe_freezing_v0` has two obstacles and no `min_distance_to_obstacle` key, so
there is no criterion to be vacuous. It is the scene `clearance_census` took its
whole eight-seed registry on, i.e. the scene this branch has the *most*
clearance data for and the least clearance grading. That is `acceptance_coverage`'s
defect one layer out: that module asks whether a declared key is computed, and
cannot see a key nobody declared.

Scope, stated before the numbers because it bounds them:

* **Seed 0, eight arms**, from :data:`scene_census.SCENE_SEED0` and
  :data:`clearance_census.SHIPPED_ARM_CLEARANCE`. No new rollouts — every figure
  here was already on disk, which is what made the sweep affordable.
* A seed-0 range is a **lower bound on the attained range**, so it can only
  over-report vacuity, never under-report it. :func:`widened` re-grades the two
  scenes with eight-seed columns on disk (`freezing`, and `convoy`/`cut_in` via
  :data:`scene_census.PAIRED_ENSEMBLE`) and reports whether the extra seeds move
  the verdict. They do not — which is evidence about these scenes, not a licence
  to skip the check elsewhere.
* **Only `min_distance_to_obstacle`.** The other declared keys
  (`time_to_goal_max`, `freeze_duration_max`, …) have the same failure mode and
  are **not** swept here, because the attained ranges for them are not on disk
  and this cycle declined to buy them with rollouts. :data:`UNSWEPT_KEYS` names
  them so the gap is a constant rather than an omission. One of them has since
  been closed: :mod:`cte_vacuity` bought the 64 rollouts and swept `cte_rms_max`
  (D-358), finding **five** vacuous scenes to this column's one — and finding
  them on the opposite side, since a cross-track bar is a ceiling where this
  one is a floor. `UNSWEPT_KEYS` below still lists `cte_rms_max`, correctly:
  it is derived as the keys *this* sweep does not cover.

CLI:
    python -m eval.mppi_sandbox.threshold_vacuity     # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from .clearance_census import SEED_ENSEMBLE, SHIPPED_ARM_CLEARANCE
from .scene_census import PAIRED_ENSEMBLE, SCENE_OBSTACLES, SCENE_SEED0

#: The acceptance key this module sweeps. Named rather than inlined so
#: :data:`UNSWEPT_KEYS` can be checked against the scenarios for completeness.
SWEPT_KEY = "min_distance_to_obstacle"

#: Declared acceptance keys with the same vacuity exposure that this sweep does
#: **not** cover, because no attained-range table exists for them on disk.
#: Derived by :func:`undeclared_key_gap`, pinned here so a newly-declared key of
#: a new kind shows up as drift instead of silently widening the blind spot.
UNSWEPT_KEYS: tuple[str, ...] = (
    "collision", "completion_min", "cte_max", "cte_rms_max",
    "cut_in_detection_latency_max", "freeze_duration_max", "goal_reached",
    "goal_xy_tol", "goal_yaw_tol", "heading_err_rms_max", "jerk_lat_max",
    "time_to_goal_max", "time_to_goal_max_ratio",
    "yield_or_pass_decision_time_max",
)

#: `scene -> verdict`, the census this module exists to pin. A scene moving
#: between verdicts is a real change in what the acceptance matrix measures and
#: should fail the suite on the cycle that causes it.
#:
#: Direction is asymmetric, as in :mod:`acceptance_coverage`: turning a
#: `VACUOUS_*` into `DISCRIMINATING` is a **win** — fix the threshold and shrink
#: this census in the same commit. Only an unpinned move is a finding.
CENSUS: dict[str, str] = {
    "cafe_convoy_v0": "DISCRIMINATING",
    "cafe_cut_in_v0": "DISCRIMINATING",
    "cafe_freezing_v0": "UNDECLARED",
    "cafe_head_on_v0": "VACUOUS_FAIL",
    "cafe_obstacle_contested_v0": "VACUOUS_PASS",
    "cafe_obstacle_crossing_v0": "DISCRIMINATING",
    "cafe_straight_v0": "UNMEASURABLE",
    "city_curved_v0": "UNMEASURABLE",
    "city_figure8_v0": "UNMEASURABLE",
}

#: The arm pair D-356 measured on `cafe_convoy_v0`, and the verdict that pair
#: yields. Pinned beside :data:`CENSUS` because the two disagree on the same
#: scene and the disagreement is finding #2 — a reader who sees only one of them
#: draws the wrong conclusion about the other.
HEADLINE_PAIR: tuple[str, tuple[str, ...], str] = (
    "cafe_convoy_v0", ("risk_mppi", "stock_mppi"), "VACUOUS_PASS",
)

_SCENARIO_DIR = Path(__file__).resolve().parents[2] / "eval" / "scenarios"


@dataclass(frozen=True)
class Verdict:
    """One scene's threshold read against the clearance its arms attain."""

    scene: str
    declared: float | None
    lo: float | None
    hi: float | None
    n_arms: int
    grade: str

    def line(self) -> str:
        dec = "     -" if self.declared is None else f"{self.declared:>6.2f}"
        if self.lo is None:
            rng = "          -        "
        else:
            rng = f"{self.lo:>8.4f} .. {self.hi:<8.4f}"
        return f"{self.grade:<15}{self.scene:<28}{dec}  {rng}  n={self.n_arms}"


def declared_thresholds() -> dict[str, float]:
    """`scene -> declared min_distance_to_obstacle`, read from the scenarios.

    Derived by loading the yaml rather than restating it: D-047's failure was a
    hand-typed copy of a registry that had since grown, and a threshold census
    that mirrors the scenarios has exactly the same exposure.
    """
    out: dict[str, float] = {}
    for path in sorted(_SCENARIO_DIR.glob("*.yaml")):
        if path.stem == "lam_windows":  # a table, not a scenario
            continue
        acc = (yaml.safe_load(path.read_text()) or {}).get("acceptance") or {}
        if SWEPT_KEY in acc:
            out[path.stem] = float(acc[SWEPT_KEY])
    return out


def undeclared_key_gap() -> tuple[str, ...]:
    """Every acceptance key across the scenarios except :data:`SWEPT_KEY`.

    The mirror of :data:`UNSWEPT_KEYS`. This is what makes the blind spot a
    measured constant instead of a sentence in the docstring.
    """
    keys: set[str] = set()
    for path in sorted(_SCENARIO_DIR.glob("*.yaml")):
        if path.stem == "lam_windows":
            continue
        acc = (yaml.safe_load(path.read_text()) or {}).get("acceptance") or {}
        keys.update(acc)
    return tuple(sorted(keys - {SWEPT_KEY}))


def attained(scene: str) -> dict[str, float]:
    """`arm -> min_clearance_m` at seed 0 for `scene`, from the pinned tables.

    `cafe_freezing_v0` lives in :data:`clearance_census.SHIPPED_ARM_CLEARANCE`
    and the other four hostable scenes in :data:`scene_census.SCENE_SEED0`; the
    split is that constant's own convention, followed rather than duplicated.
    Scenes with no obstacles return `{}` — every arm's clearance is `+inf`
    there, so the question is not posed.
    """
    if SCENE_OBSTACLES[scene] == 0:
        return {}
    if scene == "cafe_freezing_v0":
        return {arm: row[0] for arm, row in SHIPPED_ARM_CLEARANCE.items()}
    return dict(SCENE_SEED0[scene])


def grade_scene(scene: str, population: dict[str, float] | None = None) -> Verdict:
    """Grade one scene's declared threshold against an attained-clearance range.

    `population` defaults to the whole seed-0 registry; passing a subset is how
    :data:`HEADLINE_PAIR` re-grades the same scene over the two arms D-356
    compared, which is the reading that makes vacuity population-scoped.
    """
    declared = declared_thresholds().get(scene)
    col = attained(scene) if population is None else population
    if not col:
        return Verdict(scene, declared, None, None, 0, "UNMEASURABLE")
    lo, hi = min(col.values()), max(col.values())
    if declared is None:
        return Verdict(scene, None, lo, hi, len(col), "UNDECLARED")
    if declared <= lo:
        grade = "VACUOUS_PASS"      # nothing can fail it
    elif declared > hi:
        grade = "VACUOUS_FAIL"      # nothing can pass it
    else:
        grade = "DISCRIMINATING"
    return Verdict(scene, declared, lo, hi, len(col), grade)


def sweep() -> tuple[Verdict, ...]:
    """Every shipped scene, graded. The population :data:`CENSUS` pins."""
    return tuple(grade_scene(s) for s in sorted(SCENE_OBSTACLES))


def widened() -> dict[str, tuple[str, str]]:
    """`scene -> (seed0_grade, widened_grade)` where 8-seed columns exist.

    A seed-0 range is a lower bound on the attained range, so it can only
    over-report vacuity. This re-grades against every seed on disk and reports
    whether the wider evidence moves the verdict — the honest check on finding
    #1, since `VACUOUS_FAIL` on one seed would be a much weaker claim than
    `VACUOUS_FAIL` on eight.

    **Both grades are taken over the same arms**, which is the whole difficulty.
    The eight-seed columns on disk cover the full registry only on
    `cafe_freezing_v0`; on `convoy`/`cut_in` they cover a *pair*. Grading the
    pair's widened range against the registry's seed-0 range would attribute a
    population change to the seeds — finding #2's error, committed by the
    instrument that reports it. So the narrow grade is restricted to the same
    arms before the comparison, and any move here is the seeds alone.
    """
    out: dict[str, tuple[str, str]] = {}
    wide: dict[str, dict[str, float]] = {
        "cafe_freezing_v0": {a: min(row) for a, row in SEED_ENSEMBLE.items()},
    }
    for (scene, arm), (base_col, arm_col) in PAIRED_ENSEMBLE.items():
        wide.setdefault(scene, {})
        wide[scene][arm] = min(arm_col)
        wide[scene]["stock_mppi"] = min(base_col)
    for scene, col in sorted(wide.items()):
        narrow = {a: v for a, v in attained(scene).items() if a in col}
        out[scene] = (grade_scene(scene, narrow).grade,
                      grade_scene(scene, col).grade)
    return out


def drift() -> tuple[str, ...]:
    """Scenes whose graded verdict disagrees with :data:`CENSUS`."""
    bad = [f"{v.scene}: {CENSUS.get(v.scene, '<unpinned>')} -> {v.grade}"
           for v in sweep() if CENSUS.get(v.scene) != v.grade]
    keys = undeclared_key_gap()
    if keys != UNSWEPT_KEYS:
        bad.append(f"UNSWEPT_KEYS: pinned {UNSWEPT_KEYS} != derived {keys}")
    return tuple(bad)


def main() -> int:
    for v in sweep():
        print(v.line())
    scene, arms, _ = HEADLINE_PAIR
    pair = {a: attained(scene)[a] for a in arms}
    print(f"\nD-356 pair on {scene}: {grade_scene(scene, pair).grade} "
          f"(vs {grade_scene(scene).grade} over the full registry)")
    for s, (narrow, wide) in widened().items():
        moved = "moved" if narrow != wide else "unmoved"
        print(f"widened {s:<28}{narrow} -> {wide}  ({moved})")
    bad = drift()
    for line in bad:
        print(f"DRIFT  {line}")
    print(f"\nthreshold_vacuity — {len(sweep())} scenes, "
          f"{sum(1 for v in sweep() if v.grade.startswith('VACUOUS'))} vacuous, "
          f"{len(bad)} drift. Unswept keys: {len(UNSWEPT_KEYS)}.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
