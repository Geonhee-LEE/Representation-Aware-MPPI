# SPDX-License-Identifier: BSD-3-Clause
"""Does the cross-track **peak** bar grade what the RMS bar could not? — STATE #1c.

D-358 swept `cte_rms_max` over eight scenes and found **five** whose bar no arm
can fail: a `VACUOUS_PASS` column that reads as *경로추종 is solved everywhere*
while grading nothing. Its own scope note named the cheapest next column —
`cte_max`, the peak on the same trajectory, declared by 4 scenes — and left it
unswept rather than smuggled in. This is that column.

**Finding #1 is a negative, and it is the reason the column was worth buying.**
Of the 4 scenes that declare `cte_max`, **1 discriminates and 3 are
`VACUOUS_PASS`** — and they are the **same** 1 and the same 3 that D-358's RMS
sweep graded that way. `cafe_obstacle_crossing_v0` discriminates on both bars
(`cte_max` 1.0 against a `1.0272` peak from `cbf_mppi`; `cte_rms_max` 0.40
against a `0.5384` RMS); `straight` / `curved` / `figure8` are vacuous on both.
So **the peak bar grades exactly the partition the RMS bar already graded, and
buys no new cell.** :data:`RMS_BLIND` is empty, and that emptiness is the
result: the five vacuous cross-track cells are **not** an artefact of reading
the wrong statistic off the trajectory. Swapping RMS for peak — the obvious
"maybe we measured it wrong" repair, and free once the rollouts exist — does
not move a single scene. Whatever makes those bars ungradeable survives a
change of statistic.

**Finding #2 — what the vacuity *is* ordered by is path curvature, which is the
research feed's hypothesis arriving as a measurement.** The `2026-08-19 08:00`
feed entry (Nav2 #5925) argued that the dominant cross-track failure mode of a
horizon-based sampler is *excited by path curvature*, so a straight scene cannot
fail a cross-track bar at any value — reframing D-358's vacuous cells as a
**scene-geometry** gap rather than a threshold gap, and thereby escaping the
threshold-shopping refusal that killed D-356/357/358 alternative (c). Headroom
(declared / attained `hi`; 1.0 = about to grade) ranks the three vacuous scenes
the same way on **both** statistics:

=====================  ==============  =============
scene                  peak headroom   RMS headroom
=====================  ==============  =============
`city_curved_v0`       **2.18x**       **3.84x**
`city_figure8_v0`      9.25x           20.0x
`cafe_straight_v0`     23.26x          22.7x
=====================  ==============  =============

The curved scene is nearest to grading on either bar; the straight one is an
order of magnitude away on either. Two independent statistics giving the same
monotone ordering is what finding #1's negative makes worth saying: the
ordering is a property of the **scenes**, not of the statistic. It does **not**
say what any bar's value should be — only which scenes a bar can discriminate
in at all, which is the question the user-blocked judgement actually turns on.

Scope, stated before the numbers because it bounds them:

* **Seed 0, eight arms, eight scenes** — 64 closed-loop rollouts, the same
  construction as :data:`cte_vacuity.CTE_SEED0` but reading `metrics["cte_max"]`
  instead of `metrics["cte_rms"]`. Pinned in :data:`CTE_MAX_SEED0`.
* A seed-0 range is a **lower bound on the attained range**, so as in D-358 this
  can only over-report `VACUOUS_PASS`: more seeds widen `hi`, and a wider `hi`
  moves a scene only *toward* `DISCRIMINATING`. The three vacuous scenes are an
  upper bound, and `city_curved_v0`'s 2.18x headroom makes it the one most
  likely to fall with more seeds. :data:`WIDENING_UNBOUGHT` carries the cost.
* **4 of 8 scenes declare no `cte_max` at all** (`convoy`, `cut_in`, `freezing`,
  `head_on`) and grade `UNDECLARED`. That is `acceptance_coverage`'s blind spot
  again (D-357 finding #3): a key nobody declared cannot be vacuous, and the
  four undeclared scenes include the two this branch's headline runs on.
* The curvature ordering in finding #2 is **observational** — three points, read
  off scene names, with no curvature radius computed. It corroborates the feed's
  mechanism; it does not test it. :data:`CURVATURE_UNMEASURED` names that.

CLI:
    python -m eval.mppi_sandbox.cte_peak_vacuity   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from .threshold_vacuity import Verdict

#: The acceptance key this module sweeps — the *peak* counterpart of
#: :data:`cte_vacuity.SWEPT_KEY`, on the same trajectories.
SWEPT_KEY = "cte_max"

#: `scene -> {arm: cte_max}` at seed 0 over the full eight-arm registry, from 64
#: rollouts (`run_scenario(..., seed=0)`, `metrics["cte_max"]`). Ordered
#: worst-first within each scene so the `hi` that decides `VACUOUS_PASS` is the
#: first number a reader sees.
CTE_MAX_SEED0: dict[str, dict[str, float]] = {
    "cafe_convoy_v0": {
        "gap_gated_mppi": 0.1923, "social_mppi": 0.1707, "essps_mppi": 0.1234,
        "cbf_mppi": 0.1080, "geometric_mppi": 0.0902, "stock_mppi": 0.0902,
        "frozen_risk_mppi": 0.0626, "risk_mppi": 0.0482,
    },
    "cafe_cut_in_v0": {
        "essps_mppi": 0.8662, "cbf_mppi": 0.8371, "geometric_mppi": 0.4208,
        "stock_mppi": 0.4208, "risk_mppi": 0.3640, "frozen_risk_mppi": 0.2792,
        "gap_gated_mppi": 0.2684, "social_mppi": 0.2489,
    },
    "cafe_freezing_v0": {
        "geometric_mppi": 0.0644, "stock_mppi": 0.0644, "frozen_risk_mppi": 0.0611,
        "risk_mppi": 0.0489, "cbf_mppi": 0.0416, "essps_mppi": 0.0360,
        "gap_gated_mppi": 0.0360, "social_mppi": 0.0298,
    },
    "cafe_head_on_v0": {
        "social_mppi": 0.8897, "cbf_mppi": 0.8632, "risk_mppi": 0.8035,
        "essps_mppi": 0.7063, "frozen_risk_mppi": 0.6941, "gap_gated_mppi": 0.6093,
        "geometric_mppi": 0.6093, "stock_mppi": 0.6093,
    },
    "cafe_obstacle_crossing_v0": {
        "cbf_mppi": 1.0272, "risk_mppi": 0.3997, "frozen_risk_mppi": 0.2958,
        "geometric_mppi": 0.2793, "stock_mppi": 0.2793, "gap_gated_mppi": 0.2471,
        "social_mppi": 0.2348, "essps_mppi": 0.1335,
    },
    "cafe_straight_v0": {
        "cbf_mppi": 0.0215, "frozen_risk_mppi": 0.0215, "gap_gated_mppi": 0.0215,
        "geometric_mppi": 0.0215, "risk_mppi": 0.0215, "social_mppi": 0.0215,
        "stock_mppi": 0.0215, "essps_mppi": 0.0145,
    },
    "city_curved_v0": {
        "cbf_mppi": 0.4583, "frozen_risk_mppi": 0.4583, "gap_gated_mppi": 0.4583,
        "geometric_mppi": 0.4583, "risk_mppi": 0.4583, "social_mppi": 0.4583,
        "stock_mppi": 0.4583, "essps_mppi": 0.3853,
    },
    "city_figure8_v0": {
        "cbf_mppi": 0.1081, "frozen_risk_mppi": 0.1081, "gap_gated_mppi": 0.1081,
        "geometric_mppi": 0.1081, "risk_mppi": 0.1081, "social_mppi": 0.1081,
        "stock_mppi": 0.1081, "essps_mppi": 0.0602,
    },
}

#: Per-scene grade, pinned so :func:`drift` fails when a rollout or a declared
#: bar moves under this module.
CENSUS: dict[str, str] = {
    "cafe_convoy_v0": "UNDECLARED",
    "cafe_cut_in_v0": "UNDECLARED",
    "cafe_freezing_v0": "UNDECLARED",
    "cafe_head_on_v0": "UNDECLARED",
    "cafe_obstacle_crossing_v0": "DISCRIMINATING",
    "cafe_straight_v0": "VACUOUS_PASS",
    "city_curved_v0": "VACUOUS_PASS",
    "city_figure8_v0": "VACUOUS_PASS",
}

#: `arm -> scenes whose declared `cte_max` it exceeds`. The whole non-vacuous
#: signal this column carries is one cell, and naming it as a census makes that
#: narrowness a constant rather than a thing a reader has to notice.
PEAK_TENSION: dict[str, tuple[str, ...]] = {
    "cbf_mppi": ("cafe_obstacle_crossing_v0",),
}

#: Scenes vacuous on `cte_rms_max` but discriminating on `cte_max`. **Empty**,
#: and that is finding #1: the peak bar grades the same partition the RMS bar
#: already graded, so the vacuity survives a change of trajectory statistic.
RMS_BLIND: tuple[str, ...] = ()

#: The eight-seed widening this module could not afford, same shape as D-358's:
#: 8 scenes x 8 arms x 7 further seeds. `city_curved_v0` at 1.09x headroom is
#: the cell most likely to change if it is ever bought.
WIDENING_UNBOUGHT: int = 8 * 8 * 7

#: Finding #2 is an *ordering over three scenes read off their names*, not a
#: curvature measurement. Computing min curvature radius from
#: `Scenario.waypoints` and comparing it to the sampler's `horizon x v_max`
#: reach is the test that would promote corroboration to evidence — deliberately
#: not done here, and named so the gap is a constant rather than a silence.
CURVATURE_UNMEASURED: str = (
    "min curvature radius vs horizon x v_max reach, per scene — the feed's "
    "Nav2 #5925 mechanism stated as a testable claim; 3-point name-ordering only"
)

_SCENARIO_DIR = Path(__file__).resolve().parents[2] / "eval" / "scenarios"


def declared_thresholds() -> dict[str, float]:
    """`scene -> declared cte_max`, read from the scenarios on disk.

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


def grade_scene(scene: str, population: dict[str, float] | None = None) -> Verdict:
    """Grade one scene's `cte_max` against the peak cross-track its arms attain.

    Same ceiling comparison as :func:`cte_vacuity.grade_scene` — a bar at or
    above the attained `hi` cannot fail, one below `lo` cannot pass — because
    `cte_max` is a ceiling on the same trajectory. The operator is shared; the
    *statistic* is what differs, and finding #1 is that the difference decides a
    scene's grade even when the bar is left alone.
    """
    declared = declared_thresholds().get(scene)
    col = CTE_MAX_SEED0.get(scene, {}) if population is None else population
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
    return tuple(grade_scene(s) for s in sorted(CTE_MAX_SEED0))


def failing_arms(scene: str) -> tuple[str, ...]:
    """Arms whose seed-0 `cte_max` exceeds `scene`'s declared bar."""
    declared = declared_thresholds().get(scene)
    if declared is None:
        return ()
    return tuple(sorted(a for a, v in CTE_MAX_SEED0[scene].items() if v > declared))


def tension() -> dict[str, tuple[str, ...]]:
    """`arm -> scenes it fails`, derived. The census :data:`PEAK_TENSION` pins."""
    out: dict[str, list[str]] = {}
    for scene in sorted(CTE_MAX_SEED0):
        for arm in failing_arms(scene):
            out.setdefault(arm, []).append(scene)
    return {a: tuple(v) for a, v in sorted(out.items())}


def headroom() -> dict[str, float]:
    """`scene -> declared / attained-hi` for every `VACUOUS_PASS` scene.

    Finding #2's ordering. A headroom near `1.0` is a scene one seed away from
    grading; a headroom of 23 is a scene no bar change reaches. Derived so the
    docstring table cannot drift away from the pins above it.
    """
    out: dict[str, float] = {}
    for v in sweep():
        if v.grade == "VACUOUS_PASS" and v.declared is not None and v.hi:
            out[v.scene] = round(v.declared / v.hi, 4)
    return dict(sorted(out.items(), key=lambda kv: kv[1]))


def rms_blind() -> tuple[str, ...]:
    """Scenes vacuous on `cte_rms_max` but discriminating on `cte_max`.

    Finding #1, derived against :mod:`cte_vacuity` rather than restated, so the
    two columns cannot disagree about which scenes they disagree about. It comes
    back **empty** — the negative this module exists to record.
    """
    from . import cte_vacuity

    out = []
    for v in sweep():
        if v.grade != "DISCRIMINATING":
            continue
        if cte_vacuity.grade_scene(v.scene).grade.startswith("VACUOUS"):
            out.append(v.scene)
    return tuple(out)


def drift() -> tuple[str, ...]:
    """Scenes, tension rows, or the RMS-blind set disagreeing with their census."""
    bad = [f"{v.scene}: {CENSUS.get(v.scene, '<unpinned>')} -> {v.grade}"
           for v in sweep() if CENSUS.get(v.scene) != v.grade]
    if tension() != PEAK_TENSION:
        bad.append(f"PEAK_TENSION: pinned {PEAK_TENSION} != derived {tension()}")
    if rms_blind() != RMS_BLIND:
        bad.append(f"RMS_BLIND: pinned {RMS_BLIND} != derived {rms_blind()}")
    return tuple(bad)


def main() -> int:
    for v in sweep():
        print(v.line())
    print()
    for arm, scenes in tension().items():
        print(f"fails cte_max  {arm:<20}{', '.join(scenes)}")
    for scene, h in headroom().items():
        print(f"headroom  {scene:<32}{h:>8.2f}x")
    bad = drift()
    for line in bad:
        print(f"DRIFT  {line}")
    graded = [v for v in sweep() if v.grade != "UNDECLARED"]
    vac = sum(1 for v in graded if v.grade.startswith("VACUOUS"))
    print(f"\ncte_peak_vacuity — {len(graded)} scenes declare {SWEPT_KEY}, "
          f"{vac} vacuous, {len(graded) - vac} discriminating; "
          f"{len(sweep()) - len(graded)} UNDECLARED. "
          f"RMS-blind: {len(RMS_BLIND)}. {len(bad)} drift. "
          f"Widening unbought: {WIDENING_UNBOUGHT} rollouts.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
