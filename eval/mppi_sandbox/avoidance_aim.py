# SPDX-License-Identifier: BSD-3-Clause
"""Q-188: is the avoidance response too **small**, or pointed the wrong **way**?

D-444 closed Q-187's timing branch on `cafe_obstacle_crossing_v0`: the response
is anticipatory — 16/16 seeds leave the path 0.9-2.7 s *before* closest
approach, with 1 reactive row out of 122 — and it still grazes at 0.00-0.06 m.
So the swerve is early, and it is ineffective. Q-188 is the branch that reading
opened and did not name: an early swerve that buys nothing is either

- **(a) magnitude** — the excursion is real but too small; even aimed perfectly
  away from the hazard it could not have produced clearance. Then a cost-side
  lever survives (cf. D-427's compact support), because the controller wants
  the right thing and does not want it hard enough.
- **(b) aim** — the excursion is large enough that a perfectly-aimed one would
  have cleared, but its direction does not convert into separation. Then the
  thing at fault is what the controller is steering *toward* — the reference
  path — which is where this project's representation hypothesis lives.

The discriminator: a budget comparison at one instant
-----------------------------------------------------

Everything is read at the **closest-approach index**, because that is the only
instant at which "did it clear" is decided. At that index three lengths are
measured, all in metres, all surface-to-surface where that is meaningful:

``deviation``
    How far the robot body is from the reference polyline. This is the *size*
    of the excursion — what it cost in tracking error.
``on_path_clearance``
    The clearance the robot **would have had** at that same instant had it been
    standing at its own path foot. This is the counterfactual baseline, and it
    is a real number rather than a modelling assumption because the hazard's
    position at that time is logged: the actor is where it is regardless of
    where the robot chose to be.
``gain = clearance - on_path_clearance``
    What the excursion actually bought.

``required = TARGET_CLEARANCE - on_path_clearance`` is what it needed to buy.
The two branches then separate without any further modelling, because
``gain <= deviation`` always (moving `d` metres can increase a distance by at
most `d`):

    deviation < required   ->  (a): no aim could have sufficed at this size
    deviation >= required
        and gain < required ->  (b): the size sufficed, the direction did not

The ratio ``gain / deviation`` is reported alongside as ``aim_efficiency`` in
[-1, 1] — 1.0 is a swerve pointed straight away from the hazard, 0.0 one that
slides along the hazard's bearing, negative one that closes on it. It is a
diagnostic, not the verdict: the verdict is the budget comparison, which is
scale-free in a way a ratio is not.

Three things this deliberately does not do
------------------------------------------

1. **It does not use peak deviation.** Q-188 was drafted as "per-seed *peak*
   lateral deviation vs the required offset", and peak is the wrong instant:
   D-444 already established the excursion is early, so its peak may occur
   seconds before the encounter and be irrelevant to the clearance that was
   decided later. Reading both lengths at one index is what makes the
   comparison a budget rather than two unrelated statistics. `peak_deviation`
   is still recorded per seed so a reader can see how far the two diverge.

2. **It does not fold `TARGET_CLEARANCE` into the module's conclusions.** The
   target is a scenario-level choice, so :func:`classify` takes it and
   :func:`verdicts_over_targets` sweeps a ladder — the same discipline D-444
   applied to its deviation threshold, and for the same reason: a knife-edge
   constant chosen after seeing the answer would manufacture the verdict.

3. **It does not drop a seed that already cleared.** ``required <= 0`` means
   the path itself was safe at that instant and the reading has no work to do;
   that is a third bucket (`SUFFICIENT`), not a row to discard. Excluding it
   would bias the sample toward the hard seeds and re-run the D-358 vacuity
   error from the other direction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from eval.mppi_sandbox.avoidance_timing import (
    ARMS,
    SCENE,
    SEEDS,
    clearance_series,
    closest_approach_index,
    cross_track_series,
)

__all__ = [
    "ARMS",
    "SCENE",
    "SEEDS",
    "TARGETS",
    "SeedAim",
    "classify",
    "foot_points",
    "measure_arm",
    "score_one_run",
    "verdicts_over_targets",
]

#: Clearance targets in metres, swept rather than fixed. 0.20 m is the robot's
#: own radius (a body-width of daylight); 0.30 m is where D-426's knee parked
#: the runs it converted, so it is the value this scene has already been shown
#: to be able to reach.
TARGETS: tuple[float, ...] = (0.10, 0.20, 0.30)


def foot_points(traj: np.ndarray, waypoints: np.ndarray) -> np.ndarray:
    """Per-timestep nearest point on the reference polyline, shape (T, 2).

    :func:`avoidance_timing.cross_track_series` computes the same projection
    and returns only its norm. This returns the point itself, which Q-188 needs
    in order to ask what the clearance would have been *there*. The two agree
    by construction — :func:`test_foot_points_agree_with_cross_track_series`
    pins that they do not drift apart.
    """
    xy = traj[:, 1:3]
    ref = np.asarray(waypoints)[:, :2]
    a, b = ref[:-1], ref[1:]
    seg = b - a                                    # (S, 2)
    denom = np.einsum("sk,sk->s", seg, seg)
    denom = np.where(denom > 0.0, denom, 1.0)
    rel = xy[:, None, :] - a[None, :, :]           # (T, S, 2)
    u = np.clip(np.einsum("tsk,sk->ts", rel, seg) / denom, 0.0, 1.0)
    foot = a[None, :, :] + u[:, :, None] * seg[None, :, :]   # (T, S, 2)
    best = np.argmin(np.linalg.norm(xy[:, None, :] - foot, axis=2), axis=1)
    return foot[np.arange(foot.shape[0]), best]


def on_path_clearance_at(traj: np.ndarray, waypoints: np.ndarray, obstacles,
                         robot_radius: float, index: int) -> float:
    """Clearance the robot would have had at `index` standing on its path foot.

    The hazard's position at that instant is taken from the log, so this is a
    counterfactual about the *robot* only. Minimised over obstacles, exactly as
    :func:`avoidance_timing.clearance_series` is, so the two are comparable
    term by term.
    """
    if not obstacles:
        return float("inf")
    t = traj[index:index + 1, 0]
    foot = foot_points(traj, waypoints)[index]
    return float(min(
        float(np.linalg.norm(foot - ob.position(t)[0])) - ob.radius - robot_radius
        for ob in obstacles
    ))


@dataclass(frozen=True)
class SeedAim:
    """One seed's budget at its own closest-approach instant.

    Every field is metres except `seed`, `index` and `aim_efficiency`.
    """

    seed: int
    index: int
    t_s: float
    #: Achieved surface-to-surface clearance at closest approach.
    clearance: float
    #: Counterfactual clearance at the path foot, same instant.
    on_path_clearance: float
    #: Distance from the reference polyline at that instant.
    deviation: float
    #: Largest distance from the polyline anywhere in the run.
    peak_deviation: float

    @property
    def gain(self) -> float:
        """What the excursion bought, in metres of clearance."""
        return self.clearance - self.on_path_clearance

    @property
    def aim_efficiency(self) -> float:
        """`gain / deviation`, in [-1, 1]. NaN when the robot was on its path."""
        if self.deviation <= 0.0:
            return float("nan")
        return self.gain / self.deviation

    def required(self, target: float) -> float:
        """Clearance still owed at the foot to reach `target`. May be <= 0."""
        return target - self.on_path_clearance


def score_one_run(traj: np.ndarray, waypoints: np.ndarray, obstacles,
                  robot_radius: float, *, seed: int) -> SeedAim:
    """Score a single logged trajectory. No target is applied here.

    The target enters only at :func:`classify`, so one integration can be read
    against the whole ladder — the same re-scoring trick D-444 used, and the
    reason a threshold can be reported as a sweep instead of defended as a
    number.
    """
    clr = clearance_series(traj, obstacles, robot_radius)
    xte = cross_track_series(traj, waypoints)
    i = closest_approach_index(clr)
    return SeedAim(
        seed=seed,
        index=i,
        t_s=float(traj[i, 0]),
        clearance=float(clr[i]),
        on_path_clearance=on_path_clearance_at(
            traj, waypoints, obstacles, robot_radius, i),
        deviation=float(xte[i]),
        peak_deviation=float(np.max(xte)),
    )


def classify(row: SeedAim, target: float) -> str:
    """Q-188's branch for one seed at one target.

    ``SUFFICIENT`` — the path foot already met the target; nothing was owed.
    ``MAGNITUDE``  — the excursion is smaller than what was owed, so no aim
                     could have cleared. Q-188 (a).
    ``AIM``        — the excursion is at least what was owed and still did not
                     buy it. Q-188 (b).
    ``CLEARED``    — something was owed and the excursion delivered it.
    """
    required = row.required(target)
    if required <= 0.0:
        return "SUFFICIENT"
    if row.deviation < required:
        return "MAGNITUDE"
    if row.gain >= required:
        return "CLEARED"
    return "AIM"


def counts(rows: tuple[SeedAim, ...], target: float) -> dict[str, int]:
    """Bucket a set of seeds at one target. All four keys always present."""
    out = {"SUFFICIENT": 0, "MAGNITUDE": 0, "AIM": 0, "CLEARED": 0}
    for row in rows:
        out[classify(row, target)] += 1
    return out


def verdict(bucket: dict[str, int]) -> str:
    """Map one target's counts onto Q-188's two branches.

    Conservative in the same way :func:`avoidance_timing.verdict` is: only the
    seeds that were *owed* something vote, and a split without a clear majority
    reads ``MIXED`` rather than rounding toward whichever branch is cheaper to
    act on.
    """
    mag, aim = bucket["MAGNITUDE"], bucket["AIM"]
    decided = mag + aim
    if decided == 0:
        return "NO_DEFICIT: no seed was owed clearance it failed to get"
    if mag >= 2 * aim:
        return "MAGNITUDE: the excursion is too small for any aim to clear; (a)"
    if aim >= 2 * mag:
        return "AIM: the excursion is big enough and misdirected; (b)"
    return "MIXED: no majority; the scene holds both failure modes"


def verdicts_over_targets(rows: tuple[SeedAim, ...],
                          targets: tuple[float, ...] = TARGETS,
                          ) -> dict[float, str]:
    """The verdict at each rung of the ladder. Stability across rungs is the
    thing a reader should check before believing any single one."""
    return {t: verdict(counts(rows, t)) for t in targets}


def measure_arm(scenario, w_heading: float,
                seeds: tuple[int, ...] = SEEDS) -> tuple[SeedAim, ...]:
    """Run one arm and score every seed. 16 integrations, no target applied."""
    from eval.mppi_sandbox import ab
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds),
                         params=MPPIParams(w_heading=w_heading))
    # D-443's precondition, in the function whose output is undefined without
    # it rather than in one of its callers: a truncated run's closest-approach
    # index may sit before the encounter ever happened.
    stalled = [r.seed for r in runs if not r.reached_goal]
    if stalled:
        raise RuntimeError(
            f"w_heading={w_heading}: seed(s) {stalled} did not reach goal; "
            "the aim reading is not defined over a truncated run"
        )
    return tuple(
        score_one_run(r.traj, scenario.waypoints, scenario.obstacles,
                      ab.ROBOT_RADIUS, seed=r.seed)
        for r in runs
    )
