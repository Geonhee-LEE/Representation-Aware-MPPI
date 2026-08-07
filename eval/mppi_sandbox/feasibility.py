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


# ---------------------------------------------------------------------------
# En-route clearance (Q-108)
# ---------------------------------------------------------------------------
#
# `goal_ball_clearance` above answers "can the robot *stop* where it is told
# to". D-120 raised the harder question one station earlier: `cafe_head_on_v0`
# and `cafe_obstacle_crossing_v0` are 8/8 unsafe against their own declared
# margins on both controllers, and nothing distinguishes (i) the cost term
# being unable to hold that room from (ii) the scene geometry forbidding it.
#
# The goal-ball trick does not extend by simply sweeping the station index.
# It works because the goal ball is somewhere the robot must *end and stay*,
# so maximising over arrival time is the only freedom there is. En route the
# robot has two more: it may pick *when* it occupies each station, and it may
# stand off laterally. Take the max over both independently and every dynamic
# scene screens clean — the pedestrian is always somewhere else at some time.
# So the bound below is a maximin over whole *schedules* instead:
#
#     max  over admissible schedules  min  over time  clearance
#
# A schedule is any station-vs-time trace that starts at station 0, ends at
# the goal station, and moves no faster than `Limits.v_max`; at each instant
# the robot may sit anywhere within `corridor_half_width` of the reference
# path. That is a bottleneck (maximin) dynamic program on the station × time
# grid, and it is what makes the screen bite: on a head-on encounter the
# pedestrian sweeps *every* station the robot must occupy, so no schedule
# avoids a zero-longitudinal-separation instant and the whole margin has to
# come out of the lateral budget.
#
# Still one-sided in the same direction as the goal-ball screen. The
# relaxations — point robot, instantaneous lateral motion, no yaw, no
# acceleration limit, backing up allowed — all *add* freedom, so a verdict of
# "cannot meet the margin" is a proof and "can" is only "not refuted here".

#: Arclength spacing of the station grid, metres.
_STATION_DS = 0.05

#: Time step of the schedule grid, seconds. Matches `_SCAN_DT`'s resolution;
#: named separately because this one also sets the DP's reachability window.
_SCHEDULE_DT = 0.1

#: Lateral offsets sampled across the corridor. The farthest point of a
#: segment from a single obstacle is always an endpoint, but with several
#: obstacles the best stand-off is a maximin in `e` that can sit anywhere
#: between them, so the interior is sampled rather than assumed away.
_LATERAL_SAMPLES = 21

#: `run.TIMEOUT_FACTOR`. Mirrored by value for the same reason as
#: `DEFAULT_ROBOT_RADIUS` — this module must not import the simulation stack.
DEFAULT_TIMEOUT_FACTOR = 4.0

#: The acceptance key by which a scene declares a hard lateral budget. Named
#: once for the same reason as `MARGIN_KEY` (D-047).
CORRIDOR_KEY = "cte_max"


def declared_corridor(scenario: Scenario) -> float | None:
    """The hard lateral budget this scene declares, or `None` if it declares
    none.

    Deliberately does **not** fall back to `cte_rms_max`. An rms bound is a
    statement about the whole run and a corridor is a statement about every
    instant; a transient excursion far outside `cte_rms_max` can still leave
    the rms compliant, so reading one as the other would let this screen
    retire a scene a controller could actually pass. Five of the eight shipped
    scenes — including `cafe_head_on_v0`, the one demanding the largest margin
    — declare only the rms bound, so the absent case is the common one and
    must stay visible rather than be filled in.
    """
    raw = scenario.acceptance.get(CORRIDOR_KEY)
    return None if raw is None else float(raw)


@dataclass(frozen=True)
class PathClearance:
    """Verdict of the en-route bottleneck screen for one scenario."""

    scenario: str
    #: Lateral half-width the robot was allowed to use, metres.
    corridor_half_width: float
    #: Best worst-instant clearance (m, surface-to-surface) attainable by any
    #: admissible schedule. `inf` if the scene has no obstacles.
    best_clearance: float
    #: Clearance the acceptance block demands, if it declares one; else 0.0.
    #: Same optimistic policy as `goal_ball_clearance` and for the same
    #: reason — see `declared_margin`.
    required_clearance: float
    #: Path fraction at which the optimal schedule is tightest.
    binding_station_fraction: float
    #: Time (s) at which the optimal schedule is tightest.
    binding_time_s: float
    #: Horizon the schedule search was allowed, seconds.
    horizon_s: float

    @property
    def is_reachable(self) -> bool:
        """True unless *every* schedule interpenetrates somewhere en route."""
        return self.best_clearance >= 0.0

    @property
    def meets_acceptance(self) -> bool:
        """True unless the scene's own declared margin is unattainable.

        False is the (ii) branch of Q-108: no controller holds that much room
        in this corridor, so the number is a scene-declaration defect and not
        a controller target.
        """
        return self.best_clearance >= self.required_clearance


def _stations(waypoints: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Resample the reference polyline to `_STATION_DS` spacing.

    Returns `(points (N,2), normals (N,2))` — unit left-normals of the local
    tangent, so `p + e * n` sweeps the corridor at that station.
    """
    xy = np.asarray(waypoints[:, :2], dtype=float)
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    n_st = max(int(np.ceil(total / _STATION_DS)) + 1, 2)
    s = np.linspace(0.0, total, n_st)
    pts = np.stack([np.interp(s, cum, xy[:, 0]), np.interp(s, cum, xy[:, 1])],
                   axis=1)
    tang = np.gradient(pts, axis=0)
    norm = np.linalg.norm(tang, axis=1, keepdims=True)
    tang = tang / np.where(norm > 0, norm, 1.0)
    normals = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
    return pts, normals


def _clearance_grid(scenario: Scenario, pts, normals, times, w, robot_radius):
    """(N_station, N_time) best-over-lateral-offset clearance."""
    offsets = (np.array([0.0]) if w <= 0.0
               else np.linspace(-w, w, _LATERAL_SAMPLES))
    centres = np.stack([ob.position(times) for ob in scenario.obstacles])  # (M,K,2)
    radii = np.array([ob.radius for ob in scenario.obstacles])[:, None, None]
    best = np.full((len(pts), len(times)), -np.inf)
    for e in offsets:
        here = (pts + e * normals)[None, :, None, :]        # (1,N,1,2)
        d = np.linalg.norm(here - centres[:, None, :, :], axis=-1)  # (M,N,K)
        np.maximum(best, (d - radii - robot_radius).min(axis=0), out=best)
    return best


def path_clearance(
    scenario: Scenario,
    *,
    corridor_half_width: float | None = None,
    robot_radius: float = DEFAULT_ROBOT_RADIUS,
    limits: Limits | None = None,
    timeout_factor: float = DEFAULT_TIMEOUT_FACTOR,
) -> PathClearance:
    """Best worst-instant clearance any admissible schedule can hold.

    `corridor_half_width` defaults to the scene's declared `cte_max`; a scene
    that declares none has stated no hard lateral bound, so the default is
    then unbounded and the screen is vacuous by construction. Pass an explicit
    width to ask the useful question instead — `required_corridor` bisects it.
    """
    w = (corridor_half_width if corridor_half_width is not None
         else declared_corridor(scenario))
    required = declared_margin(scenario) or 0.0
    horizon = float(scenario.expected_duration * timeout_factor)

    if not scenario.obstacles or w is None or not np.isfinite(w):
        return PathClearance(
            scenario=scenario.name,
            corridor_half_width=float("inf") if w is None else float(w),
            best_clearance=float("inf"), required_clearance=required,
            binding_station_fraction=float("nan"), binding_time_s=float("nan"),
            horizon_s=horizon,
        )

    pts, normals = _stations(scenario.waypoints)
    times = np.arange(0.0, horizon + _SCHEDULE_DT, _SCHEDULE_DT)
    grid = _clearance_grid(scenario, pts, normals, times, float(w), robot_radius)

    v_max = (limits or Limits()).v_max
    reach = max(int(np.floor(v_max * _SCHEDULE_DT / _STATION_DS)), 1)

    # Bottleneck DP. value[j] = best worst-instant clearance of any schedule
    # that starts at station 0 at t=0 and is at station j now. Backing up is
    # allowed (a relaxation, hence still an upper bound), so the predecessor
    # window is symmetric.
    n_st = len(pts)
    value = np.full(n_st, -np.inf)
    value[0] = grid[0, 0]
    best_at_goal, best_t = value[-1], 0.0
    for k in range(1, len(times)):
        shifted = [value]
        for d in range(1, reach + 1):
            up = np.full(n_st, -np.inf); up[d:] = value[:-d]
            dn = np.full(n_st, -np.inf); dn[:-d] = value[d:]
            shifted += [up, dn]
        value = np.minimum(np.maximum.reduce(shifted), grid[:, k])
        if value[-1] > best_at_goal:
            best_at_goal, best_t = value[-1], float(times[k])

    # Locate the binding instant: the tightest cell on the station grid at the
    # arrival time that attained the optimum, reported for legibility only.
    if np.isfinite(best_at_goal):
        col = np.argmin(np.abs(times - best_t))
        j = int(np.argmin(np.abs(grid[:, col] - best_at_goal)))
        frac = j / (n_st - 1)
    else:
        frac = float("nan")

    return PathClearance(
        scenario=scenario.name,
        corridor_half_width=float(w),
        best_clearance=float(best_at_goal),
        required_clearance=required,
        binding_station_fraction=float(frac),
        binding_time_s=best_t,
        horizon_s=horizon,
    )


#: Widest corridor `required_corridor` will consider before giving up, metres.
#: Well past any indoor scene; a scene needing more than this is not failing
#: for want of search range.
_CORRIDOR_CEILING = 8.0

#: Bisection tolerance on the returned width, metres.
_CORRIDOR_TOL = 0.01


def required_corridor(
    scenario: Scenario,
    *,
    robot_radius: float = DEFAULT_ROBOT_RADIUS,
    limits: Limits | None = None,
) -> float | None:
    """Narrowest lateral budget at which the declared margin is attainable.

    This is the number Q-108 actually wants. `path_clearance` answers "is this
    margin reachable *given* a corridor"; a scene that declares no `cte_max`
    has no corridor to plug in, and the interesting quantity is the one the
    geometry demands rather than one the yaml happens to state. Returns `None`
    if no corridor up to `_CORRIDOR_CEILING` suffices.

    `best_clearance` is monotone non-decreasing in the corridor width — extra
    lateral room is never worse, since the narrower corridor's schedules stay
    admissible — so bisection is sound.
    """
    def ok(w: float) -> bool:
        return path_clearance(scenario, corridor_half_width=w,
                              robot_radius=robot_radius,
                              limits=limits).meets_acceptance

    if ok(0.0):
        return 0.0
    if not ok(_CORRIDOR_CEILING):
        return None
    lo, hi = 0.0, _CORRIDOR_CEILING
    while hi - lo > _CORRIDOR_TOL:
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi
