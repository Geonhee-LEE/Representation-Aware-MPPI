# SPDX-License-Identifier: BSD-3-Clause
"""Can the 경로추종 half of the acceptance matrix fail? — STATE #1, second column.

D-357 swept the matrix's **clearance** column and found one scene vacuous:
`cafe_head_on_v0` declares `min_distance_to_obstacle: 0.40` where the best arm
attains `0.2003 m`, so the criterion cannot pass. That sweep named its own blind
spot in :data:`threshold_vacuity.UNSWEPT_KEYS` — 14 declared keys with the same
exposure and no attained-range table on disk — and `STATE.md` named the cheapest
discharge: take the same reading on `cte_rms_max`, which carries the north star's
경로추종 clause exactly as `min_distance_to_obstacle` carries 물체회피.

This is that sweep, and the column reads **the mirror image of the clearance one**.

**1. Five of eight scenes cannot fail their cross-track bar.** Not one, five.
`cafe_straight_v0` declares `0.20` and the *worst* arm in the registry attains
`0.0088` — a **23×** margin; `city_figure8_v0` declares `0.50` against a worst of
`0.0250` (**20×**); `cafe_freezing_v0` `0.50` against `0.0231`; `cafe_convoy_v0`
`0.50` against `0.0706`; `city_curved_v0` `0.50` against `0.1303`. In each the
whole eight-arm registry passes by more than an order of magnitude, on every run,
and has since the scenes landed.

**2. The failing direction is inverted, and that is the dangerous half.** A
clearance bar is a **floor** (attained ≥ declared) and a cross-track bar is a
**ceiling** (attained ≤ declared), so the two vacuity verdicts swap sides: the
clearance column's single defect was `VACUOUS_FAIL` (nothing can pass), while
every defect here is `VACUOUS_PASS` (nothing can fail). D-357 argued
`VACUOUS_FAIL` is the more dangerous *of the two it could see* because it reads
as "the scene is hard". The reading now available is worse: a `VACUOUS_PASS`
column reads as **"경로추종 is solved everywhere"**, and five green cells saying
so were never able to say anything else. Half the north star has been graded by
a criterion that has never once discriminated on 5/8 of the branch's scenes.

**3. The arm that wins clearance is the arm that fails cross-track.** On the
three scenes where the bar *does* discriminate, the failing arms are
`cbf_mppi` (on `cafe_head_on_v0` and `cafe_obstacle_crossing_v0`),
`social_mppi` (`head_on`) and `essps_mppi` (`cut_in`). `cbf_mppi` is
:mod:`clearance_census`'s one genuine winner — the only arm that out-clears the
`stock_mppi` baseline, by `+0.228 m` in the eight-seed mean. So the single arm
this branch has measured buying 물체회피 is the single arm that fails 경로추종
twice, and the north star demands **both at once**. That tension is recorded in
:data:`CLEARANCE_TENSION`; it is a two-column reading no single-column sweep
could produce, which is the argument for having taken the second column at all.

Scope, stated before the numbers because it bounds them:

* **Seed 0, eight arms, eight scenes** — 64 closed-loop rollouts taken this
  cycle, since no `cte_rms` table existed on disk (that absence is precisely
  what :data:`threshold_vacuity.UNSWEPT_KEYS` recorded). Pinned in
  :data:`CTE_SEED0`.
* A seed-0 range is a **lower bound on the attained range**, so it can only
  over-report `VACUOUS_PASS`: more seeds can only widen `hi`, and a wider `hi`
  can only move a scene *toward* `DISCRIMINATING`. Finding #1 is therefore
  soft in the safe direction — the five may be fewer, never more. Unlike D-357
  this module ships **no** `widened()`, because no eight-seed `cte_rms` column
  exists on disk and this cycle declined to buy 448 more rollouts for it.
  :data:`WIDENING_UNBOUGHT` names that as a constant rather than a silence.
* **Only `cte_rms_max`.** `cte_max` (the peak, declared by 4 scenes) is a
  different bar on the same trajectory and is **not** swept; the sweep would be
  nearly free now that the rollouts are pinned, and is left as the next step
  rather than smuggled in. :data:`UNSWEPT_KEYS` carries the remaining gap.

CLI:
    python -m eval.mppi_sandbox.cte_vacuity     # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .threshold_vacuity import Verdict

#: The acceptance key this module sweeps — the 경로추종 counterpart of
#: :data:`threshold_vacuity.SWEPT_KEY`.
SWEPT_KEY = "cte_rms_max"

#: `scene -> {arm: cte_rms}` at seed 0 over the full eight-arm registry, from 64
#: rollouts taken for this sweep (`run_scenario(..., seed=0)`, `metrics["cte_rms"]`).
#: Ordered worst-first within each scene so the `hi` that decides `VACUOUS_PASS`
#: is the first number a reader sees.
CTE_SEED0: dict[str, dict[str, float]] = {
    "cafe_convoy_v0": {
        "social_mppi": 0.0706, "gap_gated_mppi": 0.0590, "geometric_mppi": 0.0412,
        "stock_mppi": 0.0412, "cbf_mppi": 0.0364, "essps_mppi": 0.0322,
        "frozen_risk_mppi": 0.0265, "risk_mppi": 0.0194,
    },
    "cafe_cut_in_v0": {
        "essps_mppi": 0.5636, "cbf_mppi": 0.2554, "risk_mppi": 0.1351,
        "frozen_risk_mppi": 0.1284, "social_mppi": 0.1143, "geometric_mppi": 0.1054,
        "stock_mppi": 0.1054, "gap_gated_mppi": 0.1029,
    },
    "cafe_freezing_v0": {
        "frozen_risk_mppi": 0.0231, "geometric_mppi": 0.0216, "stock_mppi": 0.0216,
        "risk_mppi": 0.0204, "gap_gated_mppi": 0.0145, "cbf_mppi": 0.0119,
        "social_mppi": 0.0085, "essps_mppi": 0.0061,
    },
    "cafe_head_on_v0": {
        "social_mppi": 0.3639, "cbf_mppi": 0.3301, "risk_mppi": 0.2766,
        "frozen_risk_mppi": 0.2643, "geometric_mppi": 0.2009, "stock_mppi": 0.2009,
        "gap_gated_mppi": 0.1992, "essps_mppi": 0.1148,
    },
    "cafe_obstacle_crossing_v0": {
        "cbf_mppi": 0.5384, "risk_mppi": 0.1992, "frozen_risk_mppi": 0.1313,
        "geometric_mppi": 0.1240, "stock_mppi": 0.1240, "gap_gated_mppi": 0.1000,
        "social_mppi": 0.0574, "essps_mppi": 0.0369,
    },
    "cafe_straight_v0": {
        "cbf_mppi": 0.0088, "frozen_risk_mppi": 0.0088, "gap_gated_mppi": 0.0088,
        "geometric_mppi": 0.0088, "risk_mppi": 0.0088, "social_mppi": 0.0088,
        "stock_mppi": 0.0088, "essps_mppi": 0.0025,
    },
    "city_curved_v0": {
        "cbf_mppi": 0.1303, "frozen_risk_mppi": 0.1303, "gap_gated_mppi": 0.1303,
        "geometric_mppi": 0.1303, "risk_mppi": 0.1303, "social_mppi": 0.1303,
        "stock_mppi": 0.1303, "essps_mppi": 0.1096,
    },
    "city_figure8_v0": {
        "cbf_mppi": 0.0250, "frozen_risk_mppi": 0.0250, "gap_gated_mppi": 0.0250,
        "geometric_mppi": 0.0250, "risk_mppi": 0.0250, "social_mppi": 0.0250,
        "stock_mppi": 0.0250, "essps_mppi": 0.0144,
    },
}

#: `scene -> verdict`, the census this module exists to pin. As in
#: :mod:`threshold_vacuity` the direction is asymmetric: turning a `VACUOUS_*`
#: into `DISCRIMINATING` is a **win** — tighten the bar and shrink this census in
#: the same commit. Only an unpinned move is a finding.
CENSUS: dict[str, str] = {
    "cafe_convoy_v0": "VACUOUS_PASS",
    "cafe_cut_in_v0": "DISCRIMINATING",
    "cafe_freezing_v0": "VACUOUS_PASS",
    "cafe_head_on_v0": "DISCRIMINATING",
    "cafe_obstacle_crossing_v0": "DISCRIMINATING",
    "cafe_straight_v0": "VACUOUS_PASS",
    "city_curved_v0": "VACUOUS_PASS",
    "city_figure8_v0": "VACUOUS_PASS",
}

#: Finding #3: `arm -> scenes where it fails its cte_rms_max`, over the three
#: scenes whose bar discriminates. Pinned beside :data:`CENSUS` because the
#: cross-column reading — that `cbf_mppi` is simultaneously
#: :mod:`clearance_census`'s only genuine winner and this column's most frequent
#: failure — is the finding, and a reader who sees only one column cannot get it.
CLEARANCE_TENSION: dict[str, tuple[str, ...]] = {
    "cbf_mppi": ("cafe_head_on_v0", "cafe_obstacle_crossing_v0"),
    "essps_mppi": ("cafe_cut_in_v0",),
    "social_mppi": ("cafe_head_on_v0",),
}

#: The eight-seed widening D-357 could afford and this module could not: no
#: `cte_rms` ensemble exists on disk, and buying one is 8 scenes x 8 arms x 7
#: further seeds. Named so the missing check is a constant, not an omission.
WIDENING_UNBOUGHT: int = 8 * 8 * 7

#: Declared acceptance keys still unswept by *either* vacuity module, derived by
#: :func:`unswept_key_gap`. `cte_max` heads the list: 4 scenes declare it, the
#: rollouts to grade it are already pinned in :data:`CTE_SEED0`, and it is the
#: cheapest remaining column.
UNSWEPT_KEYS: tuple[str, ...] = (
    "collision", "completion_min", "cte_max",
    "cut_in_detection_latency_max", "freeze_duration_max", "goal_reached",
    "goal_xy_tol", "goal_yaw_tol", "heading_err_rms_max", "jerk_lat_max",
    "time_to_goal_max", "time_to_goal_max_ratio",
    "yield_or_pass_decision_time_max",
)

_SCENARIO_DIR = Path(__file__).resolve().parents[2] / "eval" / "scenarios"


def declared_thresholds() -> dict[str, float]:
    """`scene -> declared cte_rms_max`, read from the scenarios on disk.

    Derived rather than restated, for D-047's reason: a hand-typed copy of a
    registry that later grows is the defect, not the convenience.
    """
    out: dict[str, float] = {}
    for path in sorted(_SCENARIO_DIR.glob("*.yaml")):
        if path.stem == "lam_windows":  # a table, not a scenario
            continue
        acc = (yaml.safe_load(path.read_text()) or {}).get("acceptance") or {}
        if SWEPT_KEY in acc:
            out[path.stem] = float(acc[SWEPT_KEY])
    return out


def unswept_key_gap() -> tuple[str, ...]:
    """Every acceptance key no vacuity module sweeps — the mirror of
    :data:`UNSWEPT_KEYS`.

    Subtracts *both* swept keys, so landing this module shrinks
    :data:`threshold_vacuity.UNSWEPT_KEYS` by exactly one entry rather than
    leaving two censuses disagreeing about the same gap.
    """
    from .threshold_vacuity import SWEPT_KEY as CLEARANCE_KEY

    keys: set[str] = set()
    for path in sorted(_SCENARIO_DIR.glob("*.yaml")):
        if path.stem == "lam_windows":
            continue
        acc = (yaml.safe_load(path.read_text()) or {}).get("acceptance") or {}
        keys.update(acc)
    return tuple(sorted(keys - {SWEPT_KEY, CLEARANCE_KEY}))


def grade_scene(scene: str, population: dict[str, float] | None = None) -> Verdict:
    """Grade one scene's `cte_rms_max` against the cross-track its arms attain.

    **The comparison is inverted relative to
    :func:`threshold_vacuity.grade_scene`, and that is finding #2.** Clearance
    declares a floor, so a threshold at or below the attained `lo` is
    `VACUOUS_PASS`; cross-track declares a ceiling, so it is a threshold at or
    above the attained `hi` that nothing can fail. Sharing the `Verdict` shape
    while flipping the test is deliberate: the two columns are the same reading
    of opposite-signed criteria, and a single generic helper parameterised by a
    comparison operator would hide precisely the asymmetry worth naming.
    """
    declared = declared_thresholds().get(scene)
    col = CTE_SEED0.get(scene, {}) if population is None else population
    if not col:
        return Verdict(scene, declared, None, None, 0, "UNMEASURABLE")
    lo, hi = min(col.values()), max(col.values())
    if declared is None:
        return Verdict(scene, None, lo, hi, len(col), "UNDECLARED")
    if declared >= hi:
        grade = "VACUOUS_PASS"      # a ceiling above every arm: nothing can fail
    elif declared < lo:
        grade = "VACUOUS_FAIL"      # a ceiling below every arm: nothing can pass
    else:
        grade = "DISCRIMINATING"
    return Verdict(scene, declared, lo, hi, len(col), grade)


def sweep() -> tuple[Verdict, ...]:
    """Every shipped scene, graded. The population :data:`CENSUS` pins."""
    return tuple(grade_scene(s) for s in sorted(CTE_SEED0))


def failing_arms(scene: str) -> tuple[str, ...]:
    """Arms whose seed-0 `cte_rms` exceeds `scene`'s declared bar."""
    declared = declared_thresholds().get(scene)
    if declared is None:
        return ()
    return tuple(sorted(a for a, v in CTE_SEED0[scene].items() if v > declared))


def tension() -> dict[str, tuple[str, ...]]:
    """`arm -> scenes it fails`, derived. The census :data:`CLEARANCE_TENSION` pins."""
    out: dict[str, list[str]] = {}
    for scene in sorted(CTE_SEED0):
        for arm in failing_arms(scene):
            out.setdefault(arm, []).append(scene)
    return {a: tuple(v) for a, v in sorted(out.items())}


def drift() -> tuple[str, ...]:
    """Scenes, tension rows, or the key gap disagreeing with their census."""
    bad = [f"{v.scene}: {CENSUS.get(v.scene, '<unpinned>')} -> {v.grade}"
           for v in sweep() if CENSUS.get(v.scene) != v.grade]
    if tension() != CLEARANCE_TENSION:
        bad.append(f"CLEARANCE_TENSION: pinned {CLEARANCE_TENSION} "
                   f"!= derived {tension()}")
    keys = unswept_key_gap()
    if keys != UNSWEPT_KEYS:
        bad.append(f"UNSWEPT_KEYS: pinned {UNSWEPT_KEYS} != derived {keys}")
    return tuple(bad)


def main() -> int:
    for v in sweep():
        print(v.line())
    print()
    for arm, scenes in tension().items():
        print(f"fails cte  {arm:<20}{', '.join(scenes)}")
    bad = drift()
    for line in bad:
        print(f"DRIFT  {line}")
    vac = sum(1 for v in sweep() if v.grade.startswith("VACUOUS"))
    print(f"\ncte_vacuity — {len(sweep())} scenes, {vac} vacuous "
          f"({vac}/{len(sweep())} cannot fail), {len(bad)} drift. "
          f"Unswept keys: {len(UNSWEPT_KEYS)}. "
          f"Widening unbought: {WIDENING_UNBOUGHT} rollouts.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
