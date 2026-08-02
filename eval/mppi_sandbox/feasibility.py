# SPDX-License-Identifier: BSD-3-Clause
"""Static feasibility preconditions for sandbox scenarios.

Why this exists
---------------
The 2026-08-02 16:00 calibration pass measured `lam` windows over the 8-scene
matrix and found `cafe_cut_in_v0` **uncalibratable for both controllers** — no
temperature at which every seed reached the goal — at a per-seed ESS spread of
1.00x, i.e. as reproducible as a scene gets. That cycle correctly refused to
call it a temperature result and filed Q-037: is an uncompletable scene a
defect in the *scene*, or a genuine capability gap in every controller?

It is a defect in the scene, and it needs no closed-loop run to see:

    goal            (0.0, -4.0),  goal_xy_tol 0.2
    ped_cut_in      terminal waypoint (0.0, -3.8) at t = 5.0, held forever
    radii           obstacle 0.3 + robot 0.3 = 0.6

The most favourable point in the goal ball is 0.4 m from the parked
pedestrian's centre, so the best achievable clearance *anywhere the run is
allowed to stop* is **-0.2 m**. The scenario's own acceptance block demands
`goal_reached: 1` **and** `collision: 0`; those two are mutually unsatisfiable
by construction. No controller, representation, or temperature repairs it.

Generalise the retirement, not the retiree
------------------------------------------
16:00's lesson was that blacklisting a scene by name finds the next
pathological scene the same expensive way — ~500 closed-loop runs. So this
module states the *precondition* instead: a scenario is completable only if its
goal ball is not permanently occupied. Screening all 8 shipped scenes costs
milliseconds and no simulation, and `cafe_cut_in_v0` is the only failure — the
next-worst scene clears by 1.87 m, so the criterion is nowhere near its
decision boundary.

This complements `calibrate_lam.SceneCalibration.completes_anywhere`, which
detects the same condition *empirically* but only after a full ladder. The two
should agree; `tests/test_scenario_feasibility.py` pins that they do.

Necessary, not sufficient
-------------------------
`goal_ball_clearance` is deliberately **optimistic**: it maximises over the
goal ball and over arrival time, and with several obstacles it takes the min of
per-obstacle optima, which no single point need attain simultaneously. So a
negative verdict is a *proof* of infeasibility, while a positive one only means
"not refuted here" — the scene may still be uncompletable for reasons en route
(corridor too narrow, horizon too short) that this check does not model. That
asymmetry is the point: the screen may never retire a scene that a controller
could actually finish.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .dynamics import Limits
from .obstacles import CircleObstacle
from .scenario import Scenario, load_scenario

#: Robot footprint circle. Mirrors `run.ROBOT_RADIUS`; imported lazily-by-value
#: rather than from `.run` to keep this module free of the simulation stack
#: (a feasibility screen that needs the controller registry to import is not a
#: precondition).
DEFAULT_ROBOT_RADIUS = 0.3

#: Time grid resolution for the arrival-window scan, seconds.
_SCAN_DT = 0.1

#: Seconds to scan past the end of the last obstacle schedule. Positions are
#: held constant after that, so one sample suffices; the margin only makes the
#: held segment visible on the grid.
_TAIL_S = 1.0


@dataclass(frozen=True)
class GoalReachability:
    """Verdict of the goal-ball occupancy screen for one scenario."""

    scenario: str
    #: Best clearance (m, surface-to-surface) achievable at any point of the
    #: goal ball at any time the robot could plausibly be there. Negative =
    #: the goal ball is provably inside an obstacle. `inf` if no obstacles.
    best_clearance: float
    #: Clearance the acceptance block demands, if it declares one; else 0.0.
    required_clearance: float
    #: Earliest time the robot could reach the goal, from path arclength and
    #: `Limits.v_max`. Clearance before this is irrelevant.
    earliest_arrival_s: float
    #: Id-index of the obstacle attaining `best_clearance`, or None.
    blocking_obstacle: int | None

    @property
    def is_reachable(self) -> bool:
        """True unless the goal ball is *provably* occupied.

        Geometric floor only (clearance >= 0): can the robot physically be at
        the goal without interpenetration? This is the condition that decides
        whether a scene can enter an ablation matrix at all.
        """
        return self.best_clearance >= 0.0

    @property
    def meets_acceptance(self) -> bool:
        """True unless the goal ball violates the scene's *declared* margin.

        Stricter than `is_reachable` whenever the scenario sets
        `min_distance_to_obstacle`. A scene can be geometrically reachable yet
        unable to satisfy its own acceptance block — worth separating, because
        the fix differs: relax the margin vs move the obstacle.
        """
        return self.best_clearance >= self.required_clearance


def _path_length(waypoints: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(np.diff(waypoints[:, :2], axis=0), axis=1)))


def earliest_arrival(scenario: Scenario, limits: Limits | None = None) -> float:
    """Lower bound (s) on when the robot can first be at the goal.

    Straight-line arclength of the reference path at `v_max`, ignoring
    acceleration limits and steering — deliberately loose, since making the
    bound smaller only makes the screen more optimistic, and the screen must
    never retire a scene a controller could finish.
    """
    lim = limits or Limits()
    return _path_length(scenario.waypoints) / max(lim.v_max, 1e-9)


def _scan_times(obstacles: list[CircleObstacle], t_start: float) -> np.ndarray:
    """Time grid from `t_start` to just past the last scheduled waypoint."""
    ends = [ob.schedule[-1, 0] for ob in obstacles if len(ob.schedule)]
    t_end = max([*ends, t_start]) + _TAIL_S
    return np.arange(t_start, t_end + _SCAN_DT, _SCAN_DT)


def goal_ball_clearance(
    scenario: Scenario,
    *,
    robot_radius: float = DEFAULT_ROBOT_RADIUS,
    limits: Limits | None = None,
) -> GoalReachability:
    """Screen whether the goal ball is permanently occupied.

    For each obstacle, the best clearance attainable from *some* point of the
    goal ball at time t is `|goal - centre(t)| + tol - r_obs - r_robot` (step
    directly away from that obstacle, staying inside the ball). Taking the min
    over obstacles and the max over admissible arrival times gives an upper
    bound on what any controller could achieve while stopped at the goal.
    """
    tol = float(scenario.acceptance.get("goal_xy_tol", 0.2))
    required = float(scenario.acceptance.get("min_distance_to_obstacle", 0.0))
    t0 = earliest_arrival(scenario, limits)

    if not scenario.obstacles:
        return GoalReachability(
            scenario=scenario.name, best_clearance=float("inf"),
            required_clearance=required, earliest_arrival_s=t0,
            blocking_obstacle=None,
        )

    times = _scan_times(scenario.obstacles, t0)
    goal_xy = np.asarray(scenario.goal[:2], dtype=float)
    # (n_obs, n_t) best-in-ball clearance against each obstacle over time.
    per_obstacle = np.stack([
        np.linalg.norm(ob.position(times) - goal_xy, axis=1)
        + tol - ob.radius - robot_radius
        for ob in scenario.obstacles
    ])
    binding = per_obstacle.min(axis=0)          # tightest obstacle at each t
    t_best = int(np.argmax(binding))            # most favourable arrival time
    return GoalReachability(
        scenario=scenario.name,
        best_clearance=float(binding[t_best]),
        required_clearance=required,
        earliest_arrival_s=t0,
        blocking_obstacle=int(np.argmin(per_obstacle[:, t_best])),
    )


def screen_scenarios(
    paths, *, robot_radius: float = DEFAULT_ROBOT_RADIUS,
) -> list[GoalReachability]:
    """Run the screen over scenario yaml paths, sorted by name."""
    return [
        goal_ball_clearance(load_scenario(p), robot_radius=robot_radius)
        for p in sorted(str(Path(p)) for p in paths)
    ]
