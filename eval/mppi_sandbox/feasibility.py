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

#: `StockMPPI.goal_slowdown_gain`. Mirrored by value for the same reason as
#: `DEFAULT_ROBOT_RADIUS` — this module must not import the controller stack.
DEFAULT_SLOWDOWN_GAIN = 0.8

#: The acceptance key by which a scene declares how much room it wants kept.
#: Named once, here, because two consumers read it and they must not disagree
#: about *which* key means "margin" (D-047).
MARGIN_KEY = "min_distance_to_obstacle"


def declared_margin(scenario: Scenario) -> float | None:
    """The clearance this scene *declares* it wants, or `None` if it declares
    none.

    `None` is the whole point of this reader existing. The key is optional and
    two of the shipped obstacle-bearing scenes differ on it — `cafe_head_on_v0`
    asks for 0.40 m, `cafe_convoy_v0` for 0.30, and `cafe_freezing_v0` declares
    nothing at all while still containing obstacles. Anything that folds the
    absent case into a number has silently decided what the scene refused to
    say, and the two consumers here need *opposite* defaults:

      * `goal_ball_clearance` (screening) substitutes `0.0`, which is the
        optimistic reading — an undeclared margin must never let the screen
        retire a scene a controller could actually finish.
      * `near_miss` (measurement) refuses instead, because the optimistic
        reading of an absent margin is an **empty near-miss band**: every run
        scores clean, the cell reports `0.0000`, and D-107's
        empty-population-reads-as-clean lands in the safety headline.

    Returning `None` is what lets those two stay different on purpose rather
    than by one of them forgetting.
    """
    raw = scenario.acceptance.get(MARGIN_KEY)
    return None if raw is None else float(raw)


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


#: Acceptance keys whose verdict is decided entirely by the obstacle set. On a
#: scene with no obstacles `min_obstacle_clearance` is `+inf` and `collision`
#: is `False` unconditionally, so each of these passes *vacuously* — the run
#: reports a clean avoidance result having never been near anything.
OBSTACLE_DEPENDENT_ACCEPTANCE = ("collision", "min_distance_to_obstacle")


def declared_obstacle_checks(scenario: Scenario) -> tuple[str, ...]:
    """Obstacle-dependent acceptance keys this scenario declares."""
    return tuple(k for k in OBSTACLE_DEPENDENT_ACCEPTANCE
                 if k in scenario.acceptance)


def vacuous_acceptance_checks(scenario: Scenario) -> tuple[str, ...]:
    """Declared obstacle checks that cannot fail, because there is nothing to hit.

    A non-empty result is a scenario defect of the same family as Q-037's
    occupied goal ball: the yaml states a safety requirement that the harness
    will always mark satisfied. Q-037's contradiction made a scene impossible;
    this one makes it impossible to fail, which is the more dangerous of the
    two because it inflates rather than depresses the reported numbers.
    """
    return () if scenario.obstacles else declared_obstacle_checks(scenario)


def is_avoidance_measurable(scenario: Scenario) -> bool:
    """Can this scene contribute a meaningful obstacle-avoidance number?

    Only if something is actually in the world. This is the per-scene predicate
    behind the denominator of any cross-scene avoidance aggregate: at 2026-08-02
    17:00 four of the eight shipped scenes answered False — including the one
    *named* `obstacle_crossing`, whose hazards existed only in the Gazebo world
    file the NumPy sandbox never loads.
    """
    return bool(scenario.obstacles)


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


@dataclass(frozen=True)
class GoalApproach:
    """Verdict of the goal-revisit screen for one scenario (Q-047 → D-026).

    `goal_ball_clearance` above asks whether the robot can *be* at the goal.
    This asks a different question the same way — statically, from the yaml —
    namely whether the reference path lets it *get there*: does the path enter
    the goal's neighbourhood before the end?
    """

    scenario: str
    #: Euclidean d(start, goal). At or below `goal_xy_tol` the completion guard
    #: is satisfied by the initial state, before the robot has moved.
    start_goal_distance: float
    goal_xy_tol: float
    #: Distance below which `v_ref` is throttled below `target_speed`.
    ramp_radius: float
    #: Closest the path comes to the goal *outside* its final approach, and
    #: where. `inf` / `nan` when the whole path is one monotone approach.
    interior_min_distance: float
    interior_min_at_fraction: float

    @property
    def completion_guard_is_sound(self) -> bool:
        """False when standing still satisfies `ab.reached_goal`.

        That guard reads the **last sample only**, so on a closed path a run
        that never leaves the start reports `reached_goal=True`. Measured
        2026-08-03: `city_figure8_v0` at a 0.016 m/s cruise scored 3/4 reached.
        """
        return self.start_goal_distance > self.goal_xy_tol

    @property
    def approach_is_monotone(self) -> bool:
        """False when the path re-enters the speed ramp with distance left.

        Both `v_ref = min(target, max(gain·d_goal, creep))` and the terminal
        cost `w_terminal · d_goal[-1]²` are functions of *Euclidean distance to
        goal*, not of *remaining arclength*. The two agree only while the path
        approaches its goal monotonically; where they disagree the loop parks
        on its own goal in the middle of a route it has not finished.

        Threshold provenance, stated because it is this screen's soft spot: the
        length scale is the **ramp** radius, while the measured 2x2 says the
        **terminal** term is what binds (dropping the ramp alone moves nothing;
        dropping `w_terminal` moves driven arclength 13.1 → 73.2 m). The
        terminal pull has no natural radius — it acts at every distance — so
        the ramp supplies the only principled per-scene length scale available
        without a rollout. This predicate is therefore a detector of revisits
        calibrated on the *weaker* of the two terms: conservative in the right
        direction, but a scene revisiting its goal at several times the ramp
        radius would pass here and could still be distorted. None of the
        shipped 8 does.
        """
        return self.interior_min_distance >= self.ramp_radius

    @property
    def is_traversable(self) -> bool:
        return self.completion_guard_is_sound and self.approach_is_monotone


def ramp_radius(scenario: Scenario,
                goal_slowdown_gain: float = DEFAULT_SLOWDOWN_GAIN) -> float:
    """Distance to goal below which `StockMPPI` throttles the speed reference.

    Solves `gain · d = target_speed` — the exact point where the goal ramp
    starts binding, per scene, rather than a shared constant. Read it as the
    radius of the ball inside which slowing down is *intended*.
    """
    return float(scenario.target_speed) / max(goal_slowdown_gain, 1e-9)


def goal_approach(scenario: Scenario, *,
                  goal_slowdown_gain: float = DEFAULT_SLOWDOWN_GAIN
                  ) -> GoalApproach:
    """Screen a scenario's reference path for goal revisits. Simulates nothing.

    "Interior" is everything before the **final approach**, defined without a
    tunable: walk back from the last waypoint while `d_goal <= ramp_radius` and
    drop that contiguous suffix. What remains is the part of the route the
    controller is supposed to drive at speed, so any point of it inside the
    ramp radius is an *early* slowdown — the ramp biting with path left to go.
    """
    xy = scenario.waypoints[:, :2]
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = cum[-1] if cum[-1] > 0 else 1.0
    d_goal = np.linalg.norm(xy - scenario.goal[:2], axis=1)
    radius = ramp_radius(scenario, goal_slowdown_gain)

    # Strip the trailing contiguous run inside the ramp — that one is legitimate.
    end = len(d_goal)
    while end > 0 and d_goal[end - 1] <= radius:
        end -= 1

    if end == 0:                       # whole path inside the ramp
        i, best = 0, float(d_goal.min())
    else:
        i = int(np.argmin(d_goal[:end]))
        best = float(d_goal[i])

    return GoalApproach(
        scenario=scenario.name,
        start_goal_distance=float(
            np.linalg.norm(scenario.start[:2] - scenario.goal[:2])),
        goal_xy_tol=float(scenario.acceptance.get("goal_xy_tol", 0.2)),
        ramp_radius=radius,
        interior_min_distance=best,
        interior_min_at_fraction=float(cum[i] / total),
    )


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
    # Optimistic on purpose: an undeclared margin must not let this screen
    # retire a scene. `declared_margin` owns the key; the `0.0` is this
    # caller's policy for the absent case, not the reader's (see its docstring).
    required = declared_margin(scenario) or 0.0
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
