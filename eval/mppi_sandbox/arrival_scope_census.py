# SPDX-License-Identifier: BSD-3-Clause
"""Which scenes does an arrival-scoped `freeze_duration` change, and how?

STATE's bottleneck after D-250: the contamination was removed from one *grid*,
not from the *metric*. `run.py` still computes `freeze_duration` over the whole
trajectory for every scene, so `freeze_duration_max` grades post-arrival idling
everywhere it is declared. The question this module answers is the blast radius
— *"does re-grading the acceptance key arrival-scoped change any other scene's
pass, or is `cafe_freezing_v0` the only scene that simulates far enough past
arrival to be bitten?"*

Measured answer: **`cafe_freezing_v0` is not special.** Every scene that
arrives is contaminated, from 25.0 % (`cafe_convoy_v0`) to 100.0 %
(`cafe_head_on_v0`, `cafe_obstacle_crossing_v0`). What makes the freezing scene
special is only that it is the one scene that *declares* `freeze_duration_max`
— the defect is in the metric, and the single declaration is all that has been
containing it.

Why this is not the ratio census Q-145 asked for
------------------------------------------------
Q-145's lean (b) was to flag scenes where `duration_s >> time_to_goal`, on the
reasoning that a long tail after arrival is the *precondition* for post-arrival
idling to be graded. The precondition is real. As a **predictor** it is
refuted, and by its own sweep:

    scene                        ratio    post-arrival share
    city_curved_v0                1.06                56.5 %
    cafe_obstacle_crossing_v0     1.21               100.0 %
    cafe_convoy_v0                1.24                25.0 %
    cafe_straight_v0              1.68                87.5 %
    cafe_head_on_v0               1.73               100.0 %
    cafe_freezing_v0              1.77                87.5 %

The two columns are close to **anti**-ordered at the top: the *lowest* ratio in
the table (`city_curved_v0`, 1.06) carries more contamination than the *highest*
but one, and the only 100 % cells sit at ratios 1.21 and 1.73. Any threshold on
the ratio that clears `city_curved_v0` also clears a scene whose whole-trajectory
reading is *entirely* post-arrival. The reason is structural rather than a
sampling accident: the ratio measures how much time is left after arrival, and
contamination measures whether *the longest stall* falls in that window. A run
can idle for two seconds in a one-second tail it never enters, and a run can
park for 0.4 s in a short tail that still beats every stall it had underway.

So :func:`sweep` reports the ratio — it is cheap and it is what Q-145 asked to
see — but the verdict is taken off the scope disagreement itself, which is the
quantity the acceptance key actually reads. This resolves Q-145 toward (a) over
(b): the precondition census would not have found this.

The third category: arrival that is not a measurement
-----------------------------------------------------
Re-grading arrival-scoped is not uniformly an improvement, and two of the eight
scenes say so:

* `city_figure8_v0` is a **closed loop** — its start pose *is* its goal pose
  (both `(-25.0, -2.5, 0.0)`, tolerances 0.3 m / 0.4 rad). `time_to_goal`
  is the first timestep inside both tolerances, so it fires at **t = 0.0**,
  before the robot has moved. The arrival-scoped reading over an empty window
  is `0.00` — not a corrected freeze but no freeze at all, and it would be
  `0.00` for any controller on any seed. Whole-trajectory reads 29.60 s there.
  Swapping one unusable number for another is not a fix, and a scene like this
  needs a lap-aware arrival predicate before it can be graded on either scope.
* `cafe_cut_in_v0` **never arrives**, so the two scopes coincide *by
  construction* (`freeze_duration_before` documents the identity). Its 0.0 %
  share is not a clean bill of health; it is the absence of a reading.

Both are `ARRIVAL_UNUSABLE`, kept distinct from `CLEAN` so that a future cycle
wiring `freeze_duration_max` into more scenes cannot read "share = 0 %" off
either one and conclude the scope question is settled there.

CLI:
    python -m eval.mppi_sandbox.arrival_scope_census        # rc=1 on drift
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from eval.path_tracking_metrics import Goal, time_to_goal

from .freeze_price import (ARRIVAL_EPS_S, arrival_is_usable, freeze_duration,
                           freeze_duration_before)
from .run import ROBOT_RADIUS, load_scenario, make_controller, simulate

SCENARIO_DIR = Path(__file__).resolve().parents[2] / "eval" / "scenarios"

#: The arm and seed the census is measured at. `stock_mppi` deliberately: the
#: census is a property of the *scene* (how long it simulates past arrival, and
#: whether it arrives at all), and reading it through the plainest controller
#: keeps it from tracking any tuning this branch does to the risk-aware arms.
CENSUS_ARM = "stock_mppi"
CENSUS_SEED = 0

#: Post-arrival share above which a scene's whole-trajectory `freeze_duration`
#: is called contaminated. Not a knife edge in today's data — the arriving
#: scenes measure 25.0 % to 100.0 %, so every rung between ~1 % and ~25 % gives
#: the same census and the exact value is not load-bearing.
POST_ARRIVAL_SHARE_MAX = 0.10

#: `ARRIVAL_EPS_S` is re-exported from `freeze_price`, where it moved once
#: `run.check_acceptance` began reading the same predicate. Imported rather
#: than restated so the census and the acceptance grade cannot disagree about
#: which scenes have a usable arrival (D-047).

VERDICT_CLEAN = "CLEAN"
VERDICT_CONTAMINATED = "CONTAMINATED"
VERDICT_ARRIVAL_UNUSABLE = "ARRIVAL_UNUSABLE"


@dataclass(frozen=True)
class SceneScope:
    """One scene's whole-vs-arrival-scoped `freeze_duration` reading."""

    scene: str
    duration_s: float
    arrival_s: float | None
    whole: float
    before: float

    @property
    def arrives(self) -> bool:
        """Did this run reach the goal pose at a time that measures anything?

        False both when the run never arrives and when it "arrives" at t=0
        because the start pose is already inside the goal tolerance — the two
        cases differ in cause but agree in consequence: there is no window in
        which an arrival-scoped reading could differ from the whole one for a
        reason having to do with the trajectory.

        Delegates to `freeze_price.arrival_is_usable`, which is the same test
        `run.check_acceptance` applies before grading the scoped reading — this
        census and the acceptance key answer "is this scene gradeable on the
        arrival scope?" with one predicate, not two.
        """
        return arrival_is_usable(self.arrival_s)

    @property
    def duration_ratio(self) -> float | None:
        """`duration_s / time_to_goal` — Q-145's precondition. `None` if unusable."""
        if not self.arrives:
            return None
        return self.duration_s / self.arrival_s

    @property
    def post_arrival_share(self) -> float | None:
        """Fraction of the whole-trajectory reading that sits after arrival.

        `None` when there is no freeze to apportion (`whole == 0`) or no usable
        arrival — in both cases a share would be an arithmetic artifact rather
        than a reading.
        """
        if not self.arrives or self.whole <= 0.0:
            return None
        return 1.0 - self.before / self.whole

    @property
    def verdict(self) -> str:
        if not self.arrives:
            return VERDICT_ARRIVAL_UNUSABLE
        share = self.post_arrival_share
        if share is None:
            return VERDICT_CLEAN
        return (VERDICT_CONTAMINATED if share > POST_ARRIVAL_SHARE_MAX
                else VERDICT_CLEAN)


def scene_paths() -> list[Path]:
    """Every shipped scene file that `load_scenario` accepts.

    `lam_windows.yaml` sits in the same directory and is a variant *table*, not
    a scene — it has no `start` key and `load_scenario` raises on it. Filtering
    by "does the loader accept it" rather than by a hand-listed exclusion keeps
    this correct when the next non-scene yaml lands (D-047).
    """
    out = []
    for path in sorted(SCENARIO_DIR.glob("*.yaml")):
        try:
            load_scenario(path)
        except (KeyError, TypeError):
            continue
        out.append(path)
    return out


def measure(scenario_path: str | Path, *, arm: str = CENSUS_ARM,
            seed: int = CENSUS_SEED) -> SceneScope:
    """Run one scene once and take **both** stall readings off that single run.

    Both scopes off one trajectory, never off two runs — D-250's method. Two
    runs would differ by the controller's own noise as well as by the scope,
    and the whole point is to attribute the difference to the scope alone.
    """
    scenario = load_scenario(scenario_path)
    ctrl = make_controller(arm, scenario, seed=seed, robot_radius=ROBOT_RADIUS)
    traj = simulate(scenario, ctrl)

    acc = scenario.acceptance
    arrival = time_to_goal(
        traj, Goal(*scenario.goal),
        xy_tol=float(acc.get("goal_xy_tol", 0.2)),
        yaw_tol=float(acc.get("goal_yaw_tol", 0.3)),
    )
    return SceneScope(
        scene=Path(scenario_path).stem,
        duration_s=float(traj[-1, 0]),
        arrival_s=arrival,
        whole=freeze_duration(traj, scenario.waypoints),
        before=freeze_duration_before(traj, scenario.waypoints, arrival),
    )


@lru_cache(maxsize=1)
def sweep() -> tuple[SceneScope, ...]:
    """Every shipped scene, measured once. Cached — the suite reads it repeatedly."""
    return tuple(measure(p) for p in scene_paths())


# Measured 2026-08-14 at `stock_mppi`, seed 0. Every arriving scene is
# contaminated; the two `ARRIVAL_UNUSABLE` entries are the closed-loop figure-8
# (arrives at t=0) and the cut-in (never arrives).
#
# Direction is asymmetric, like `acceptance_coverage`'s: a scene *leaving*
# CONTAMINATED is a win and must be re-pinned in the same commit, never a
# failure. Only an unpinned scene, or one that drifts to a verdict this census
# does not record, is a finding.
VERDICT_CENSUS = {
    "cafe_convoy_v0": VERDICT_CONTAMINATED,
    "cafe_cut_in_v0": VERDICT_ARRIVAL_UNUSABLE,
    "cafe_freezing_v0": VERDICT_CONTAMINATED,
    "cafe_head_on_v0": VERDICT_CONTAMINATED,
    "cafe_obstacle_crossing_v0": VERDICT_CONTAMINATED,
    "cafe_straight_v0": VERDICT_CONTAMINATED,
    "city_curved_v0": VERDICT_CONTAMINATED,
    "city_figure8_v0": VERDICT_ARRIVAL_UNUSABLE,
}


def ratio_ranks_contamination(rows: Sequence[SceneScope]) -> bool:
    """Does Q-145's `duration_s / time_to_goal` rank-order the contamination?

    The question Q-145 left for measurement, as a predicate rather than a
    paragraph. True iff sorting the arriving scenes by duration ratio also
    sorts them by post-arrival share — i.e. iff the cheap precondition census
    could stand in for the scope reading.

    **False on today's sweep**, which is why the census above is taken off the
    scope disagreement instead. Exposed as a function so that a future scene set
    re-answers it automatically rather than inheriting this cycle's verdict.
    """
    usable = [r for r in rows if r.post_arrival_share is not None
              and r.duration_ratio is not None]
    by_ratio = sorted(usable, key=lambda r: r.duration_ratio)
    shares = [r.post_arrival_share for r in by_ratio]
    return all(a <= b for a, b in zip(shares, shares[1:]))


def drift(rows: Sequence[SceneScope]) -> list[str]:
    """Scenes whose verdict is unpinned or disagrees with the census."""
    found = []
    for row in rows:
        expected = VERDICT_CENSUS.get(row.scene)
        if expected is None:
            found.append(f"{row.scene}: unpinned ({row.verdict})")
        elif expected != row.verdict:
            found.append(f"{row.scene}: census {expected} vs measured {row.verdict}")
    for scene in sorted(set(VERDICT_CENSUS) - {r.scene for r in rows}):
        found.append(f"{scene}: pinned but not measured (scene removed?)")
    return found


def format_table(rows: Sequence[SceneScope]) -> str:
    lines = [f"{'scene':28s} {'dur':>7s} {'arrival':>8s} {'ratio':>7s} "
             f"{'whole':>7s} {'before':>7s} {'post%':>7s}  verdict"]
    for row in rows:
        ratio = row.duration_ratio
        share = row.post_arrival_share
        lines.append(
            f"{row.scene:28s} {row.duration_s:7.2f} "
            f"{('%.2f' % row.arrival_s) if row.arrival_s is not None else 'never':>8s} "
            f"{('%.2f' % ratio) if ratio is not None else '-':>7s} "
            f"{row.whole:7.2f} {row.before:7.2f} "
            f"{('%.1f' % (100 * share)) if share is not None else '-':>7s}  "
            f"{row.verdict}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default=CENSUS_ARM)
    ap.add_argument("--seed", type=int, default=CENSUS_SEED)
    args = ap.parse_args(argv)

    if (args.arm, args.seed) == (CENSUS_ARM, CENSUS_SEED):
        rows = sweep()
    else:
        rows = tuple(measure(p, arm=args.arm, seed=args.seed)
                     for p in scene_paths())

    print(format_table(rows))
    print()
    print(f"ratio_ranks_contamination: {ratio_ranks_contamination(rows)}")

    found = drift(rows)
    if found:
        print("\narrival_scope_census — DRIFT:")
        for line in found:
            print(f"  {line}")
        return 1
    print(f"\narrival_scope_census — {len(rows)} scenes, census holds.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
