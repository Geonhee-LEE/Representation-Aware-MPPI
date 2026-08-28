# SPDX-License-Identifier: BSD-3-Clause
"""What do the two uncensused north-star axes cost, and what do they change?

STATE's bottleneck after D-487: the per-class contract names one arm for 물체회피
and declines for 경로추종, but both lines are claims about **2 of the north
star's 4 axes**. :data:`baseline_domination.UNCENSUSED_AXES` — `time_to_goal`
and `smoothness` — had no per-arm-per-scene census anywhere in the tree, and the
bottleneck's stated cheap first cut was to *"check whether `runs/*.json` already
carries a per-run time-to-goal that no census reads, before pricing a rollout
sweep."*

**The first cut looks in the wrong place, and the right place is cheaper.**
`runs/*.json` is not a census and cannot be made into one: its 48 files carry
four controller *labels* (`stock`, `risk`, `cbf-stock`, `cbf-risk`), not the
eight-arm registry :func:`baseline_domination.arms` reports, and their `metrics`
block predates `time_to_goal` entirely — the field is absent from every one of
them. What those files *do* carry is `acceptance.time_to_goal_max` reading
`"skipped"`, which is the acceptance layer recording that it wanted the number
and did not have it.

The cheaper route is that **both axes are pure functions of the trajectory**.
`path_tracking_metrics.time_to_goal(traj, goal, …)` and
`path_tracking_metrics.smoothness(traj)` need nothing but the array
:func:`clearance_census.retake` already builds for all eight arms and then
discards. So the census is not a new sweep — it is the *same* rollouts with two
more readers attached. Measured end to end: **58.6 s for 32 rollouts** (8 arms ×
the 4 joint scenes, seed 0, 2026-08-28). The bottleneck had been standing for
several cycles on a cost nobody had priced, and the cost was under a minute.

Findings
--------

**#1 — `cbf_mppi` buys its clearance with time, and the P5 report has to say
so.** This is the result STATE predicted in its own words ("the obstacle line is
exactly the kind of result a time-to-goal column could refute — `cbf_mppi` buys
clearance, and clearance is usually bought with time") and it reproduces on
every joint scene. `cbf_mppi` is the D-487 obstacle contract line and it is
**never the fastest arm**, ranking 5/8, 7/8, **8/8** and 6/7 across the four:

    scene                        cbf_mppi   best         rank
    cafe_convoy_v0                 10.1     8.8           5/8
    cafe_freezing_v0                8.7     5.7           7/8
    cafe_head_on_v0                16.1     8.4           8/8
    cafe_obstacle_crossing_v0       8.8     7.6           6/7

`cafe_head_on_v0` is the sharp cell: dead last at **+7.7 s / +92 %** over the
fastest arm. Note what this does *not* do — it does not overturn the obstacle
line, because :data:`class_contract.CLASS_AXIS` instruments 물체회피 with
clearance alone and `CLAUDE.md` files time-to-goal under 경로추종. The contract
survives as *stated*; what dies is the reading that it is unqualified. A report
naming `cbf_mppi` the obstacle baseline while withholding that it is the slowest
arm on the surface it was chosen over is one measurement short of honest, so
:func:`price_of_the_line` derives the table rather than leaving it to prose.

**#2 — the tracking plurality candidate is ranked on a scene it never
finishes.** `essps_mppi` — D-487's `tracking_plurality`, 6/7 raw and 3/4 once
the inert-block scenes are removed — returns `time_to_goal is None` on
`cafe_obstacle_crossing_v0`, and by `time_to_goal`'s construction (D-241:
``goal_reached(...) == (time_to_goal(...) is not None)``) that means it does not
reach the goal. It nevertheless holds a `cte_rms` of `0.0369` there, and that
number is inside :data:`cte_vacuity.CTE_SEED0` and therefore inside the column
D-487's tracking record was computed from. A cross-track RMS taken over a run
that never arrives is a measure of how tidily an arm failed. :func:`unfinished`
names these cells so a later cycle re-taking the tracking record can decide
whether to drop them; this cycle does **not** re-derive that record, because the
per-class contract is `class_contract`'s to state and changing it from here
would put the same claim in two modules.

**#3 — the duplicate structure reproduces on both new axes.** `geometric_mppi ==
stock_mppi` and `frozen_risk_mppi == risk_mppi` are bit-identical in **all four
recorded columns on all four scenes**. That is the inert-channel signature
(D-326's `geometric_mppi` reading) landing on a third and fourth disjoint column
set, and it matters for the same reason D-487 flagged it: a class's *distinct*
arm count, not its raw one, is what a frontier width may be quoted over.

Scope, stated before the numbers are reused
-------------------------------------------

* **Seed 0 only, 4 joint scenes.** The population is
  :func:`baseline_domination.coverage`'s `joint` key, so these rows line up
  cell-for-cell with the clearance and cross-track columns already censused and
  a later cycle can join them without re-deriving the scene set.
  :data:`WIDENING_UNBOUGHT` prices the eight-seed version in the same convention
  as `cte_vacuity` and `baseline_domination` rather than leaving it a silence.
* **`time_to_goal` is not usable on every scene in the tree**, and this module
  does not claim it is. `arrival_scope_census` measured `city_figure8_v0` as a
  closed loop whose start pose *is* its goal pose, so arrival fires at `t = 0.0`
  for any controller on any seed. That scene is outside the joint surface, so no
  cell here is affected — but a cycle widening this census past the joint four
  must screen for it. :data:`ARRIVAL_UNUSABLE_SCENES` carries the one known case.
* **This is a per-arm census; `arrival_scope_census` is not.** That module reads
  `time_to_goal` and predates this one, which is close enough to look like
  duplication. It sweeps *scenes* at a fixed arm (`CENSUS_ARM = "stock_mppi"`),
  which is the reading its own question needs and cannot rank a field of arms.
  `UNCENSUSED_AXES` was accurate when written.
* **No claim about the joint frontier.** Adding axes can only make domination
  harder, so D-486's "the frontier is the whole registry" is monotone in the
  axis count and cannot be overturned by buying more axes. Nothing here needs to
  re-derive it, and :func:`drift` deliberately does not pin it.

CLI:
    python -m eval.mppi_sandbox.axis_purchase   # rc=1 on drift from CENSUS
"""

from __future__ import annotations

import sys

#: The axes this module buys, in `baseline_domination`'s own spelling so the two
#: constants can be tested equal rather than eyeballed.
AXES: tuple[str, ...] = ("time_to_goal", "smoothness")

#: Wall-clock and rollout count for the seed-0 census below, measured rather
#: than estimated (2026-08-28). Recorded because the bottleneck it discharges
#: was a *pricing* question — three cycles deferred this census without ever
#: putting a number on it, and the number is under a minute. Same lesson as
#: `clearance_census`'s docstring: price a run before scoping around its cost.
MEASURED_SECONDS: float = 58.6
MEASURED_ROLLOUTS: int = 32

#: Rollouts an eight-seed widening of both columns would cost beyond what is on
#: disk. `8 seeds × 8 arms × 4 joint scenes` less the seed-0 column recorded
#: here — same convention and same arithmetic as
#: :data:`baseline_domination.WIDENING_UNBOUGHT`, which prices the *other* two
#: axes over the identical surface.
WIDENING_UNBOUGHT: int = 8 * 8 * 4 - 8 * 4

#: Scenes where first-arrival time is structurally not a measurement, with the
#: reason. `city_figure8_v0` is a closed loop — start pose == goal pose — so
#: `time_to_goal` fires at `t = 0.0` before the robot moves, for any controller
#: on any seed (`arrival_scope_census`, D-252). None of these are on the joint
#: surface; the constant exists so a widening cycle screens instead of discovers.
ARRIVAL_UNUSABLE_SCENES: dict[str, str] = {
    "city_figure8_v0": "closed loop; start pose is goal pose, arrival at t=0.0",
}

#: `scene -> arm -> (time_to_goal_s | None, jerk_lat, jerk_lon, accel_var)`.
#:
#: One closed-loop run per cell at the operating point
#: :data:`clearance_census.retake` uses — seed 0, `lam = OPERATING_LAM`,
#: `w_voo = OPERATING_W_VOO` and :data:`ess_at_peak.ISOLATION` for the arms whose
#: constructors take them, per `clearance_census.takes_epistemic_kwargs`. Sharing
#: that operating point is the point: these cells are joinable with the clearance
#: and cross-track columns without a re-take, which is what makes the two
#: uncensused axes cheap.
#:
#: `None` in the first slot is **never-arrived**, not missing data — see
#: :func:`unfinished` and finding #2.
AXIS_SEED0: dict[str, dict[str, tuple[float | None, float, float, float]]] = {
    "cafe_convoy_v0": {
        "cbf_mppi":         (10.1, 1.6593, 40.2665, 0.052381),
        "essps_mppi":       (12.4, 1.6922, 39.9535, 0.153091),
        "frozen_risk_mppi": (8.8,  2.5660, 35.9854, 0.234206),
        "gap_gated_mppi":   (9.9,  1.9682, 42.4593, 0.057468),
        "geometric_mppi":   (10.1, 1.9085, 41.4508, 0.054452),
        "risk_mppi":        (8.8,  2.5660, 35.9854, 0.234206),
        "social_mppi":      (8.8,  2.1169, 36.9061, 0.257442),
        "stock_mppi":       (10.1, 1.9085, 41.4508, 0.054452),
    },
    "cafe_freezing_v0": {
        "cbf_mppi":         (8.7,  1.8136, 31.7547, 0.023963),
        "essps_mppi":       (7.7,  1.3528, 31.9783, 0.135349),
        "frozen_risk_mppi": (5.8,  1.9175, 32.3858, 0.251955),
        "gap_gated_mppi":   (9.1,  1.5511, 42.1650, 0.034713),
        "geometric_mppi":   (8.2,  1.7198, 37.2739, 0.032795),
        "risk_mppi":        (5.8,  1.9175, 32.3858, 0.251955),
        "social_mppi":      (5.7,  2.2770, 25.4659, 0.204916),
        "stock_mppi":       (8.2,  1.7198, 37.2739, 0.032795),
    },
    "cafe_head_on_v0": {
        "cbf_mppi":         (16.1, 3.3280, 52.7212, 0.063998),
        "essps_mppi":       (9.6,  1.8443, 37.3478, 0.039336),
        "frozen_risk_mppi": (10.3, 2.2269, 45.3380, 0.049277),
        "gap_gated_mppi":   (9.7,  2.4681, 40.1740, 0.041656),
        "geometric_mppi":   (8.4,  2.3928, 40.3427, 0.039330),
        "risk_mppi":        (10.3, 2.2269, 45.3380, 0.049277),
        "social_mppi":      (9.0,  2.2445, 44.3984, 0.044013),
        "stock_mppi":       (8.4,  2.3928, 40.3427, 0.039330),
    },
    "cafe_obstacle_crossing_v0": {
        "cbf_mppi":         (8.8,  2.3695, 39.1472, 0.344944),
        "essps_mppi":       (None, 2.2458, 47.1356, 0.278455),
        "frozen_risk_mppi": (7.7,  2.5659, 41.4892, 0.364601),
        "gap_gated_mppi":   (8.1,  2.3592, 38.7830, 0.279224),
        "geometric_mppi":   (7.6,  2.2941, 41.4338, 0.342121),
        "risk_mppi":        (7.7,  2.5659, 41.4892, 0.364601),
        "social_mppi":      (9.7,  2.8748, 42.3460, 0.385596),
        "stock_mppi":       (7.6,  2.2941, 41.4338, 0.342121),
    },
}

#: The arm D-487 named as the 물체회피 contract line. Not a copy of that
#: module's census — :func:`price_of_the_line` reads `class_contract` at call
#: time and this constant only records which arm the findings above were written
#: about, so a contract that moves makes the tests disagree rather than silently
#: re-point the prose (D-047).
DOCUMENTED_LINE: str = "cbf_mppi"

#: The census this module pins. Each is load-bearing for the P5 report.
CENSUS: dict[str, str] = {
    "scenes": "4",
    "arms": "8",
    "line_ever_fastest": "no",
    "line_worst_scene": "cafe_head_on_v0",
    "line_worst_rank": "8/8",
    "unfinished_cells": "essps_mppi@cafe_obstacle_crossing_v0",
    "duplicate_pairs": "frozen_risk_mppi=risk_mppi,geometric_mppi=stock_mppi",
    "distinct_arms": "6",
}


def scenes() -> tuple[str, ...]:
    """Scenes censused here, in `baseline_domination.coverage`'s joint order."""
    return tuple(AXIS_SEED0)


def arms() -> tuple[str, ...]:
    """Arms censused here. Derived from the table, not restated."""
    return tuple(sorted(next(iter(AXIS_SEED0.values()))))


def time_column(scene: str) -> dict[str, float]:
    """Per-arm first-arrival time [s]. Never-arrived cells are **omitted**.

    Omission rather than a sentinel: a rank taken over this column must not
    place a non-arrival anywhere in the order, because "never reached the goal"
    is not slower-than — it is off the scale the column measures. Callers that
    need to know which cells were dropped ask :func:`unfinished`.
    """
    return {a: v[0] for a, v in AXIS_SEED0[scene].items() if v[0] is not None}


def smoothness_column(scene: str, key: str = "jerk_lat") -> dict[str, float]:
    """Per-arm smoothness, lower-is-better. `key` selects the statistic."""
    idx = {"jerk_lat": 1, "jerk_lon": 2, "accel_var": 3}[key]
    return {a: v[idx] for a, v in AXIS_SEED0[scene].items()}


def unfinished() -> tuple[tuple[str, str], tuple[str, ...]]:
    """`((arm, scene), …)` cells whose run never reached the goal.

    Finding #2's population. These are the cells where a cross-track number
    exists and describes a run that did not arrive.
    """
    return tuple(
        (arm, scene)
        for scene, row in AXIS_SEED0.items()
        for arm, v in sorted(row.items())
        if v[0] is None
    )


def duplicate_pairs() -> tuple[tuple[str, str], ...]:
    """Arms bit-identical in every recorded column on every censused scene."""
    import itertools

    return tuple(
        (a, b)
        for a, b in itertools.combinations(arms(), 2)
        if all(AXIS_SEED0[s][a] == AXIS_SEED0[s][b] for s in AXIS_SEED0)
    )


def distinct_arms() -> int:
    """Arms remaining once each duplicate pair is collapsed to one member."""
    dupes = {b for _, b in duplicate_pairs()}
    return len(set(arms()) - dupes)


def rank_of(scene: str, arm: str) -> tuple[int, int] | None:
    """`(rank, field_size)` of `arm` on `scene` by time, 1 = fastest.

    `None` if the arm did not arrive — consistent with :func:`time_column`'s
    refusal to place a non-arrival in the order.
    """
    col = time_column(scene)
    if arm not in col:
        return None
    order = sorted(col.items(), key=lambda kv: (kv[1], kv[0]))
    names = [a for a, _ in order]
    return names.index(arm) + 1, len(names)


def price_of_the_line() -> dict[str, tuple[float, float, int, int]]:
    """Finding #1's table: `scene -> (line_time, best_time, rank, field)`.

    The arm is read from :mod:`class_contract` at call time rather than from
    :data:`DOCUMENTED_LINE`, so a contract that moves to a different arm
    re-derives this table instead of leaving the prose pointing at the old one.
    """
    from .class_contract import contract_line

    arm, _ = contract_line("obstacle")
    if arm is None:
        return {}
    out = {}
    for scene in scenes():
        col = time_column(scene)
        r = rank_of(scene, arm)
        if arm not in col or r is None:
            continue
        out[scene] = (col[arm], min(col.values()), r[0], r[1])
    return out


def line_is_ever_fastest() -> bool:
    """Does the obstacle contract line lead the time column on any scene?"""
    return any(rank == 1 for _, _, rank, _ in price_of_the_line().values())


def worst_scene_for_line() -> tuple[str, int, int] | None:
    """`(scene, rank, field)` where the line ranks worst. `None` if no table."""
    table = price_of_the_line()
    if not table:
        return None
    scene = max(table, key=lambda s: table[s][2] / table[s][3])
    return scene, table[scene][2], table[scene][3]


def census() -> dict[str, str]:
    """Re-derive :data:`CENSUS` from the table. A dict compare is the drift test."""
    worst = worst_scene_for_line()
    return {
        "scenes": str(len(scenes())),
        "arms": str(len(arms())),
        "line_ever_fastest": "yes" if line_is_ever_fastest() else "no",
        "line_worst_scene": worst[0] if worst else "",
        "line_worst_rank": f"{worst[1]}/{worst[2]}" if worst else "",
        "unfinished_cells": ",".join(f"{a}@{s}" for a, s in unfinished()),
        "duplicate_pairs": ",".join(f"{a}={b}" for a, b in duplicate_pairs()),
        "distinct_arms": str(distinct_arms()),
    }


def drift() -> tuple[str, ...]:
    """Keys where the pinned census disagrees with the derived one."""
    got = census()
    return tuple(sorted(k for k in CENSUS if CENSUS[k] != got.get(k)))


def retake(*, seed: int = 0) -> dict[str, dict[str, tuple]]:
    """Re-measure the whole table. Not called by tests (~59 s).

    Mirrors :func:`clearance_census.retake`'s operating point exactly so the two
    censuses stay joinable; returns :data:`AXIS_SEED0`'s shape so a drift check
    is a dict comparison rather than a re-reading of prose.
    """
    from eval.path_tracking_metrics import Goal, smoothness, time_to_goal

    from .baseline_domination import coverage
    from .clearance_census import takes_epistemic_kwargs
    from .controllers import REGISTRY, make_controller
    from .controllers.stock_mppi import MPPIParams
    from .ess_at_peak import ISOLATION
    from .essps import OPERATING_LAM, OPERATING_W_VOO
    from .run import ROBOT_RADIUS, simulate
    from .scenario import load_scenario

    out: dict[str, dict[str, tuple]] = {}
    for scene in coverage()["joint"]:
        sc = load_scenario(f"eval/scenarios/{scene}.yaml")
        acc = sc.acceptance
        goal = Goal(*sc.goal)
        xy = float(acc.get("goal_xy_tol", 0.2))
        yaw = float(acc.get("goal_yaw_tol", 0.3))
        out[scene] = {}
        for name in sorted(REGISTRY):
            kw = dict(w_voo=OPERATING_W_VOO, w_epist=0.0, **ISOLATION) \
                if takes_epistemic_kwargs(name, sc) else {}
            ctrl = make_controller(name, sc, seed=seed, robot_radius=ROBOT_RADIUS,
                                   params=MPPIParams(lam=OPERATING_LAM), **kw)
            traj = simulate(sc, ctrl)
            ttg = time_to_goal(traj, goal, xy, yaw)
            sm = smoothness(traj)
            out[scene][name] = (
                None if ttg is None else round(float(ttg), 4),
                round(sm["jerk_lat"], 4),
                round(sm["jerk_lon"], 4),
                round(sm["accel_var"], 6),
            )
    return out


def format_table() -> str:
    """Finding #1's table, rendered."""
    rows = ["  scene                        line   best   rank"]
    for scene, (line, best, rank, field) in price_of_the_line().items():
        rows.append(f"  {scene:28s} {line:5.1f}  {best:5.1f}   {rank}/{field}")
    return "\n".join(rows)


def main() -> int:  # pragma: no cover - CLI
    d = drift()
    print(f"axis_purchase — {len(scenes())} scenes x {len(arms())} arms, seed 0")
    print(f"  price: {MEASURED_ROLLOUTS} rollouts in {MEASURED_SECONDS:.1f}s; "
          f"{WIDENING_UNBOUGHT} unbought for an 8-seed widening")
    print(format_table())
    print(f"  line ever fastest   : {'yes' if line_is_ever_fastest() else 'no'}")
    print(f"  unfinished cells    : "
          f"{', '.join(f'{a}@{s}' for a, s in unfinished()) or 'none'}")
    print(f"  distinct arms       : {distinct_arms()} of {len(arms())}")
    if d:
        print(f"DRIFT: {', '.join(d)}")
        return 1
    print("no drift from CENSUS")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
