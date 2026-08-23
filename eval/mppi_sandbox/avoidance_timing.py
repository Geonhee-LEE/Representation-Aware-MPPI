# SPDX-License-Identifier: BSD-3-Clause
"""Q-187: does the avoidance response **precede** closest approach, or follow it?

D-442 measured that on `cafe_obstacle_crossing_v0` detour and clearance are
*negatively* correlated (rho ~ -0.54): the seeds that leave the reference path
most are the ones that pass **closest** to the hazard. That breaks the premise
both Q-185 and Q-186 rested on — the deviation is not buying clearance. Q-187
asks the follow-up that the sign implies but does not establish:

- **(a) timing** — the robot does deviate, but *late*: it swerves after it is
  already alongside the hazard, so the path cost is paid and the clearance is
  not bought. Then the lever is lookahead / horizon / hazard radius.
- **(b) reference** — the global path is what ignores the obstacle, and MPPI
  fights it every step. Then the thing to change is the path, not the
  controller, which is where this project's representation hypothesis lives.

The discriminator Q-187 named, reproduced rather than re-invented: per seed,
compare **when the robot first leaves the path** against **when it is closest
to the hazard**. Order is the whole reading.

    deviation *before* closest approach  ->  the response is anticipatory; a
                                             late-swerve story (a) is refuted
                                             and (b) survives
    deviation *after* closest approach   ->  the response is reactive; (a) is
                                             live and the cheap knobs D-426
                                             already priced are the next move

What this measures, and the two things it does not
--------------------------------------------------

The statistic is a **lead time** per seed: ``t_closest - t_deviate``, in
seconds, positive when deviation comes first. It is reported per seed and
summarised by a sign count, deliberately *not* by a mean: the question is
ordinal ("which came first"), and a mean over a bimodal set (D-429 measured
exactly that bimodality on this scene) would report a middle no seed occupies.

1. **The deviation threshold is a choice, and a knife-edge choice would
   manufacture the answer.** ``first_deviation_index`` takes the threshold
   explicitly and :func:`lead_times` sweeps several, so a reader sees whether
   the sign count survives the choice or is an artefact of one value. The
   default ladder is anchored to the robot radius — "the body has left the
   path by its own half-width" is a physical statement, not a tuned one.

2. **A seed that never crosses the threshold has no deviation index**, and
   that is a *finding*, not a row to drop: it means the robot tracked the path
   through the encounter. :class:`SeedTiming` carries ``deviated=False`` for
   those and :func:`sign_counts` reports them in their own bucket, because
   silently excluding them would bias the surviving sample toward exactly the
   swerving seeds the question is about (the D-358 vacuity family: a metric
   that cannot fire must not be read as if it fired).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SCENE = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
SEEDS: tuple[int, ...] = tuple(range(16))
ARMS: tuple[float, float] = (0.0, 32.0)

#: Deviation thresholds in metres. Anchored to the robot radius rather than
#: tuned: the sweep exists so the verdict is reported against a ladder, not a
#: single value that could be chosen after seeing the answer.
THRESHOLDS: tuple[float, ...] = (0.10, 0.20, 0.30, 0.40)


def clearance_series(traj: np.ndarray, obstacles, robot_radius: float) -> np.ndarray:
    """Per-timestep surface-to-surface clearance, minimised over obstacles.

    The scalar :func:`obstacles.min_clearance` collapses this to its minimum;
    Q-187 needs the argmin's *index*, so the series is rebuilt here from the
    same expression rather than re-derived differently.
    """
    if not obstacles:
        return np.full(traj.shape[0], np.inf)
    t, xy = traj[:, 0], traj[:, 1:3]
    per_ob = [
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ]
    return np.min(np.vstack(per_ob), axis=0)


def cross_track_series(traj: np.ndarray, waypoints: np.ndarray) -> np.ndarray:
    """Per-timestep distance from the reference polyline.

    Unsigned: Q-187 asks *when* the robot left the path, not which side it
    left toward.
    """
    xy = traj[:, 1:3]
    ref = np.asarray(waypoints)[:, :2]
    a, b = ref[:-1], ref[1:]
    seg = b - a                                    # (S, 2)
    denom = np.einsum("sk,sk->s", seg, seg)
    denom = np.where(denom > 0.0, denom, 1.0)
    rel = xy[:, None, :] - a[None, :, :]           # (T, S, 2)
    u = np.clip(np.einsum("tsk,sk->ts", rel, seg) / denom, 0.0, 1.0)
    foot = a[None, :, :] + u[:, :, None] * seg[None, :, :]
    return np.min(np.linalg.norm(xy[:, None, :] - foot, axis=2), axis=1)


def closest_approach_index(clearances: np.ndarray) -> int:
    """Index of minimum clearance. Ties resolve to the earliest."""
    return int(np.argmin(clearances))


def first_deviation_index(cross_track: np.ndarray, threshold: float) -> int | None:
    """First index whose cross-track distance exceeds `threshold`.

    ``None`` when the robot never left the path by that much — a real outcome
    on this scene, and one the caller must not silently drop.
    """
    hits = np.flatnonzero(cross_track > threshold)
    return int(hits[0]) if hits.size else None


@dataclass(frozen=True)
class SeedTiming:
    """One seed's ordering at one threshold."""

    seed: int
    threshold: float
    deviated: bool
    #: ``t_closest - t_deviate`` in seconds; NaN when `deviated` is False.
    lead_s: float
    t_closest_s: float
    min_clearance: float

    @property
    def anticipatory(self) -> bool:
        """Deviation strictly precedes closest approach."""
        return self.deviated and self.lead_s > 0.0


def time_one_run(traj: np.ndarray, waypoints: np.ndarray, obstacles,
                 robot_radius: float, *, seed: int,
                 threshold: float) -> SeedTiming:
    """Score a single logged trajectory at one deviation threshold."""
    clr = clearance_series(traj, obstacles, robot_radius)
    xte = cross_track_series(traj, waypoints)
    i_close = closest_approach_index(clr)
    i_dev = first_deviation_index(xte, threshold)
    t = traj[:, 0]
    return SeedTiming(
        seed=seed,
        threshold=threshold,
        deviated=i_dev is not None,
        lead_s=float("nan") if i_dev is None else float(t[i_close] - t[i_dev]),
        t_closest_s=float(t[i_close]),
        min_clearance=float(clr[i_close]),
    )


def sign_counts(rows: tuple[SeedTiming, ...]) -> dict[str, int]:
    """Ordinal summary: how many seeds anticipated, reacted, never deviated.

    Three buckets and not two — `never` is reported rather than folded into
    either side, because a seed that held the path is evidence *against* the
    late-swerve story in a different way than one that swerved early.
    """
    never = sum(1 for r in rows if not r.deviated)
    early = sum(1 for r in rows if r.anticipatory)
    late = sum(1 for r in rows if r.deviated and not r.anticipatory)
    return {"anticipatory": early, "reactive": late, "never_deviated": never}


def measure_arm(scenario, w_heading: float,
                seeds: tuple[int, ...] = SEEDS,
                thresholds: tuple[float, ...] = THRESHOLDS,
                ) -> dict[float, tuple[SeedTiming, ...]]:
    """Run one arm and time every seed at every threshold. 16 integrations.

    The sweep over thresholds costs nothing extra: the trajectories are
    integrated once and re-scored, which is the whole reason the threshold can
    be reported as a ladder instead of defended as a single number.
    """
    from eval.mppi_sandbox import ab
    from eval.mppi_sandbox.controllers.stock_mppi import MPPIParams

    runs = ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds),
                         params=MPPIParams(w_heading=w_heading))
    robot_radius = ab.ROBOT_RADIUS
    # D-443's precondition, for the same reason it holds in `avoidance_price`:
    # a truncated run has no closest-approach index that means anything, since
    # the encounter it would index may never have happened.
    stalled = [r.seed for r in runs if not r.reached_goal]
    if stalled:
        raise RuntimeError(
            f"w_heading={w_heading}: seed(s) {stalled} did not reach goal; "
            "the timing reading is not defined over a truncated run"
        )
    out: dict[float, tuple[SeedTiming, ...]] = {}
    for th in thresholds:
        out[th] = tuple(
            time_one_run(r.traj, scenario.waypoints, scenario.obstacles,
                         robot_radius, seed=r.seed, threshold=th)
            for r in runs
        )
    return out


def verdict(counts: dict[str, int]) -> str:
    """Map one threshold's sign counts onto Q-187's two branches.

    Deliberately conservative: a split that is not a clear majority reads
    `MIXED` rather than being rounded toward whichever branch is cheaper to
    act on. D-442 was reached by refusing exactly that kind of rounding.
    """
    early, late = counts["anticipatory"], counts["reactive"]
    decided = early + late
    if decided == 0:
        return "NO_DEVIATION: every seed held the path at this threshold"
    if early >= 2 * late:
        return "ANTICIPATORY: deviation precedes closest approach; (a) late-swerve refuted"
    if late >= 2 * early:
        return "REACTIVE: deviation follows closest approach; (a) live"
    return "MIXED: no majority ordering; the scene holds both modes"
