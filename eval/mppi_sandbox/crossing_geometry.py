# SPDX-License-Identifier: BSD-3-Clause
"""Q-190: is `cafe_obstacle_crossing_v0` a fair test bed for *lateral* avoidance?

D-446 measured, over 32 logged runs, that the hazard bearing at the deciding
instant lies almost entirely along the path tangent (`bearing_tangent_frac`
0.800-1.000, means 0.956 / 0.929). It concluded that a path-normal excursion is
structurally orthogonal to the separation direction and so cannot buy clearance
at any magnitude — which retired three cost-side sweeps (D-430 / D-433 / D-440)
on principle rather than by exhaustion. Q-190 asks whether that conclusion is
about the **controller**, the **scene**, or the **instant it was read at**:

- **(a) scene defect** — the actors' courses are parameterised nearly parallel
  to the reference path, so the scene named "crossing" never crosses. Then
  every null result on this branch is a statement about the scene, and a
  genuinely lateral scenario has to be added before any controller work.
- **(b) the instant is special** — the actors really do cross, and the bearing
  aligns with the path only because that is what closest approach *is*.

The two readings, and why both are needed
-----------------------------------------

**Reading A — the scene, from the yaml alone.** Each scripted actor's course is
a straight leg between time-stamped waypoints, so its direction is available
with no sim at all. :func:`actor_courses` reports `|c_hat . t_hat|`, the share
of each actor's course lying along the path tangent. Under (a) these are near
1; under (b) near 0. This is the cheaper half and it settles the literal claim.

**Reading B — the instant, from the 32 runs already logged.** Reading A can
only refute (a); it cannot *explain* the measured 0.929. The explanation, if
(b) holds, is a one-line kinematic identity. For two bodies at constant
velocity the range `|h - p|` is stationary exactly when the separation is
orthogonal to the relative velocity, so at a closest approach

    u . t_hat  =  +/- ( v_rel x t_hat ) / |v_rel|                        (CPA)

with `u` the unit bearing to the hazard, `t_hat` the path tangent, and
`v_rel = v_hazard - v_robot`. The right-hand side is a function of the two
*velocities only* — it knows nothing about where either body is. So under (b)
the measured `bearing_tangent_frac` is predicted, run by run, by the velocities
at that instant, and the residual between prediction and measurement is the
falsifiable quantity. :func:`score_one_run_cpa` reports both sides, plus the
identity's precondition (`cpa_orthogonality`) so a failure can be attributed to
the instant rather than left ambiguous.

What was measured, and the correction it forces
----------------------------------------------

Reading A is exact and settles (a): all five actors run `|c_hat . t_hat| =
0.0000` — dead perpendicular to the path, at 0.75 m/s. The scene crosses as
named, so no null lateral-avoidance result on it is a scene artefact.

Reading B then found the identity *not* satisfied by D-446's number: measured
0.956 / 0.929 against a prediction of 0.750 / 0.743, a one-sided residual of
about +0.2 on every one of the 32 seeds. The precondition rules out the
obvious culprit — `cpa_orthogonality` is 0.006-0.133 (mean 0.044 / 0.051), so
the instant really is a stationary point of the range and (CPA) does apply.

The gap is a **frame** difference, and naming it is this module's main result.
D-446 reads the bearing from the **foot** on the reference path, because its
own identity `gain = -d . u` is a first-order expansion about the foot — that
is correct for what D-446 was computing. (CPA) is a statement about the
**robot**. Measured from the robot the same 32 instants give 0.741 / 0.729
against the predicted 0.750 / 0.743: mean absolute gap 0.030 / 0.035, max
0.096, KINEMATIC at bands 0.10 and 0.20 on 16/16 seeds in both arms. The
foot-origin reading exceeds the robot-origin one by +0.215 / +0.200 (range
+0.100 to +0.295), one-signed — the excursion's own contribution, since a
path-normal displacement moves the origin sideways off a bearing that points
down the path.

So Q-190 answers **(b)**, and D-446's geometry is sound in its own frame — but
the number 0.956 / 0.929 must not be quoted as "how tangential this encounter
is". The encounter's own figure is **0.73**, which sits just above the
isotropic split (0.707) rather than near 1. D-446's verdict ladder swept
0.50 / 0.707 / 0.85 and returned TIMING at all three; against the robot-origin
values (range 0.622-0.816) the **0.85 rung would carry no tangential votes at
all**. The lever call survives at the two lower rungs and is not overturned
here, but it rests on a smaller margin than the foot-frame number advertises,
and that is the opening a cycle wanting to re-open cost-side tuning has.

Because the identity has no scene in it, the tangential-at-closest-approach
geometry generalises: it is a property of any crossing encounter in which the
actor is the faster body, not a defect of this yaml.

What this deliberately does not do
----------------------------------

1. **It does not re-measure `bearing_tangent_frac`.** It calls
   :func:`avoidance_budget.score_one_run`, so the measured side of the residual
   is D-446's number term for term. A second opinion about the measured value
   would make the residual uninterpretable — the whole point is that only the
   *predicted* side is new.
2. **It does not fix the residual tolerance.** :func:`explains_over_bands`
   sweeps it, for D-445's reason: a verdict that moves with the constant that
   produced it was never a verdict.
3. **It does not claim (CPA) holds exactly.** Neither body is at constant
   velocity over the encounter and the actor set is re-minimised at every
   sample, so the identity is an approximation whose error is *the measurement*.
   It is reported signed, not as an absolute score.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from eval.mppi_sandbox.avoidance_aim import foot_points
from eval.mppi_sandbox.avoidance_budget import (
    ARMS,
    SCENE,
    SEEDS,
    _tangent_at,
    _unit,
    score_one_run,
)

__all__ = [
    "ARMS",
    "BANDS",
    "SCENE",
    "SEEDS",
    "ActorCourse",
    "SeedCPA",
    "actor_courses",
    "course_verdict",
    "explains",
    "explains_over_bands",
    "measure_arm",
    "residuals",
    "score_one_run_cpa",
]

#: Residual bands, in units of `|u . t_hat|` (dimensionless, range [0, 1]), at
#: which "the CPA identity explains the measurement" is called. 0.10 is a tenth
#: of the full range; the flanking rungs ask whether the call survives a
#: stricter and a looser bar. Swept, never fixed — see the docstring.
BANDS: tuple[float, ...] = (0.05, 0.10, 0.20)

#: `|c_hat . t_hat|` above which an actor's course counts as *along* the path.
#: 0.707 is the isotropic split (45 degrees) — the same rung `avoidance_budget`
#: uses for the same kind of directional call.
COURSE_ALONG: float = 0.707


@dataclass(frozen=True)
class ActorCourse:
    """One scripted actor's straight-line course, relative to the path."""

    index: int
    #: Unit course direction, averaged over the schedule's legs by displacement.
    course: tuple[float, float]
    #: Path tangent nearest the actor's mid-course point.
    tangent: tuple[float, float]
    #: `|c_hat . t_hat|` — share of the course lying along the path. 1 = along.
    course_tangent_frac: float
    #: Scripted speed, m/s, from the schedule's total displacement over its span.
    speed: float


@dataclass(frozen=True)
class SeedCPA:
    """One seed's closest-approach instant, measured *and* predicted."""

    seed: int
    index: int
    t_s: float
    #: D-446's number, unmodified: `|u . t_hat|` from `avoidance_budget`, with
    #: `u` the bearing from the *foot* on the reference path to the hazard.
    measured: float
    #: The same share read from the *robot* instead of the foot,
    #: `|(h - p)_hat . t_hat|`. This is the origin (CPA) is stated about; the
    #: gap to :attr:`measured` is the excursion's own contribution, not the
    #: scene's. See the module docstring.
    measured_from_robot: float
    #: `|v_rel x t_hat| / |v_rel|` — the (CPA) identity's prediction.
    predicted: float
    #: Robot speed at the instant, m/s. The identity's only free variable here.
    robot_speed: float
    #: Hazard speed at the instant, m/s.
    hazard_speed: float
    #: `|v_rel|`, m/s. The prediction is undefined (NaN) when this is 0.
    rel_speed: float
    #: `|(h - p)_hat . v_rel_hat|` — the identity's *precondition*, measured
    #: directly. Exactly 0 at a true closest approach of two constant-velocity
    #: bodies; anything else means the instant is not a stationary point of
    #: this pair's range, so (CPA) does not apply and the residual below is
    #: explained by the instant, not by the scene.
    cpa_orthogonality: float

    @property
    def residual(self) -> float:
        """`measured - predicted`. Signed: the identity is an approximation."""
        return self.measured - self.predicted


def actor_courses(scenario) -> tuple[ActorCourse, ...]:
    """Reading A: each scripted actor's course angle. No integration at all.

    Static obstacles (no schedule) have no course and are skipped rather than
    reported with a zero direction, which would drag the population toward
    "not along the path" for a body that never moves.
    """
    ref = np.asarray(scenario.waypoints, dtype=float)[:, :2]
    out: list[ActorCourse] = []
    for i, ob in enumerate(scenario.obstacles):
        sched = np.asarray(getattr(ob, "schedule", np.empty((0, 3))), dtype=float)
        if len(sched) < 2:
            continue
        legs = sched[1:, 1:3] - sched[:-1, 1:3]
        travelled = float(np.sum(np.linalg.norm(legs, axis=1)))
        if travelled <= 0.0:
            continue
        course = _unit(sched[-1, 1:3] - sched[0, 1:3])
        span = float(sched[-1, 0] - sched[0, 0])
        mid = 0.5 * (sched[0, 1:3] + sched[-1, 1:3])
        t_hat = _tangent_at(ref, mid)
        out.append(ActorCourse(
            index=i,
            course=(float(course[0]), float(course[1])),
            tangent=(float(t_hat[0]), float(t_hat[1])),
            course_tangent_frac=float(abs(np.dot(course, t_hat))),
            speed=(travelled / span if span > 0.0 else float("nan")),
        ))
    return tuple(out)


def course_verdict(courses: tuple[ActorCourse, ...],
                   along: float = COURSE_ALONG) -> str:
    """Does the yaml describe a crossing? Reading A's whole output."""
    if not courses:
        return "NO_ACTOR: the scene has no scripted course to read"
    n_along = sum(1 for c in courses if c.course_tangent_frac >= along)
    if n_along == len(courses):
        return ("SCENE_DEFECT: every actor's course lies along the reference "
                "path, so this scene never crosses it and cannot test lateral "
                "avoidance")
    if n_along == 0:
        return ("CROSSING: no actor's course lies along the reference path — "
                "the scene crosses it as named, so a tangential bearing at "
                "closest approach is not explained by the courses")
    return (f"MIXED: {n_along}/{len(courses)} actor courses lie along the path; "
            "the scene holds both geometries")


def _robot_velocity(traj: np.ndarray, i: int) -> np.ndarray:
    """Body velocity in the plane, from the logged `[t, x, y, yaw, v, omega]`.

    Read off the log rather than differenced: the log carries `v` and `yaw`
    exactly, and a finite difference would fold the integrator's step into a
    quantity the identity treats as instantaneous.
    """
    yaw, v = float(traj[i, 3]), float(traj[i, 4])
    return v * np.array([np.cos(yaw), np.sin(yaw)])


def score_one_run_cpa(traj: np.ndarray, waypoints: np.ndarray, obstacles,
                      robot_radius: float, *, seed: int) -> SeedCPA:
    """Reading B for one logged run: the measured bearing and its prediction.

    The measured side is delegated to :func:`avoidance_budget.score_one_run` so
    the two readings cannot drift apart; only `predicted` is computed here.
    """
    if not obstacles:
        raise ValueError("the CPA identity is undefined with no hazard")
    budget = score_one_run(traj, waypoints, obstacles, robot_radius, seed=seed)
    i = budget.index
    t = float(traj[i, 0])

    p = traj[i, 1:3].astype(float)
    # Same minimisation `score_one_run` used, so `measured` and `predicted`
    # describe the same hazard as well as the same instant.
    haz = min(obstacles,
              key=lambda ob: float(np.linalg.norm(p - ob.position(np.array([t]))[0]))
              - ob.radius)
    v_haz = np.asarray(haz.velocity(t), dtype=float)
    v_rob = _robot_velocity(traj, i)
    v_rel = v_haz - v_rob
    rel_speed = float(np.linalg.norm(v_rel))

    # Tangent taken at the *foot*, exactly where `avoidance_budget` takes it —
    # taking it at the robot instead would compare two frames, not two claims.
    f = foot_points(traj, waypoints)[i].astype(float)
    t_hat = _tangent_at(np.asarray(waypoints, dtype=float), f)

    h = haz.position(np.array([t]))[0].astype(float)
    if rel_speed > 0.0:
        cross = float(v_rel[0] * t_hat[1] - v_rel[1] * t_hat[0])
        predicted = abs(cross) / rel_speed
        orthogonality = abs(float(np.dot(_unit(h - p), v_rel / rel_speed)))
    else:
        predicted = float("nan")
        orthogonality = float("nan")
    measured_from_robot = float(abs(np.dot(_unit(h - p), t_hat)))

    return SeedCPA(
        seed=seed,
        index=i,
        t_s=t,
        measured=budget.bearing_tangent_frac,
        measured_from_robot=measured_from_robot,
        predicted=predicted,
        robot_speed=float(np.linalg.norm(v_rob)),
        hazard_speed=float(np.linalg.norm(v_haz)),
        rel_speed=rel_speed,
        cpa_orthogonality=orthogonality,
    )


def residuals(rows: tuple[SeedCPA, ...]) -> dict[str, float]:
    """Population summary of Reading B. Empty input -> all NaN, not an error."""
    keys = ("measured", "measured_from_robot", "predicted", "residual",
            "robot_speed", "hazard_speed", "cpa_orthogonality")
    if not rows:
        return {k: float("nan") for k in keys}
    out = {k: float(np.mean([getattr(r, k) for r in rows])) for k in keys}
    out["abs_residual_max"] = float(np.max([abs(r.residual) for r in rows]))
    return out


def explains(rows: tuple[SeedCPA, ...], band: float) -> str:
    """Does the (CPA) identity account for the measured bearing, at one band?

    Only seeds with a defined prediction vote — a seed whose relative velocity
    vanished at the deciding instant has no identity to test, and counting it
    either way would let a degenerate run cast a vote about kinematics.
    """
    voting = tuple(r for r in rows if np.isfinite(r.predicted))
    if not voting:
        return "NO_PREDICTION: no seed had a defined relative velocity"
    ok = sum(1 for r in voting if abs(r.measured_from_robot - r.predicted) <= band)
    if ok == len(voting):
        return ("KINEMATIC: the tangential bearing is what closest approach "
                "*is* for these velocities, not a property of this scene")
    if ok == 0:
        return ("UNEXPLAINED: the measured bearing is not the one the "
                "velocities predict; something other than closest-approach "
                "geometry is setting it")
    return (f"PARTIAL: {ok}/{len(voting)} seeds within the band")


def explains_over_bands(rows: tuple[SeedCPA, ...],
                        bands: tuple[float, ...] = BANDS) -> dict[float, str]:
    """The call at each rung. Stability across rungs is what a reader checks."""
    return {b: explains(rows, b) for b in bands}


def measure_arm(scenario, w_heading: float,
                seeds: tuple[int, ...] = SEEDS) -> tuple[SeedCPA, ...]:
    """Run one arm and score every seed. 16 integrations, no band applied."""
    from eval.mppi_sandbox import ab
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds),
                         params=MPPIParams(w_heading=w_heading))
    # D-443's precondition, restated where it bites: a truncated run's
    # closest-approach index may sit before the encounter ever happened.
    stalled = [r.seed for r in runs if not r.reached_goal]
    if stalled:
        raise RuntimeError(
            f"w_heading={w_heading}: seed(s) {stalled} did not reach goal; "
            "the CPA identity is not defined over a truncated run"
        )
    return tuple(
        score_one_run_cpa(r.traj, scenario.waypoints, scenario.obstacles,
                          ab.ROBOT_RADIUS, seed=r.seed)
        for r in runs
    )
