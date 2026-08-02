# SPDX-License-Identifier: BSD-3-Clause
"""Static hazard-*exposure* screen — a simulation-free predictor of Q-040.

Measured 2026-08-02 18:00, adding five actors to `cafe_obstacle_crossing_v0`
split its two controllers' admissible `lam` windows (`stock_mppi` [0.4, 0.8]
vs `risk_mppi` [1.6, 3.2]) where they had overlapped completely while the
scene was empty. It is the **only** `per_arm` cell in the eight-scene matrix —
and `cafe_convoy_v0` carries the *same five actors* at the *same* footprint
without the effect. So obstacle **count** cannot be what predicts separation.

Q-040 asks what does. The mechanism 18:00 established is cost *magnitude*: the
arm carrying the extra cost term moved 8x, the arm without it 2x, so windows
separate when the two arms' cost landscapes scale differently. A collision
term's contribution is a **time-integral**, which is why this module measures
time-in-contest rather than obstacle count:

    a scene's hazard exposure is the fraction of its nominal traversal
    during which the reference-following robot is within `contest_radius`
    of at least one obstacle.

"Nominal" means the reference path walked at `target_speed_mps` with **no
controller in the loop**. That is deliberate, and it is what makes this a
*screen* in feasibility.py's sense rather than another measurement: it costs
milliseconds, it cannot depend on which controller you were going to run, and
it therefore predicts a property of the (scene, pair) cell from the scenario
yaml alone. The price is that it ignores the detour the planner would actually
take — so treat a verdict as a *prediction to be falsified by calibration*,
never as a substitute for `lam_windows.yaml`.

Correlation over eight scenes with one positive is not evidence — any
statistic that happens to rank the crossing scene first would "separate" it.
The claim is only worth making because it is checked by a **controlled
intervention** in `eval/scenarios/variants/`: hold obstacle count, footprint,
speed and geometry fixed, change *only* the schedule, and see whether the
windows follow the exposure. See `tests/test_hazard_exposure.py`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from .obstacles import CircleObstacle
from .scenario import Scenario, load_scenario

#: Surface-to-surface distance under which the robot is "in contest" with an
#: obstacle. Not a collision threshold — scenes set `min_distance_to_obstacle`
#: around 0.30 m, so 1.0 m is comfortably the band where a collision cost term
#: is *active but not yet dominant*, which is the regime that sets how far the
#: two arms' cost magnitudes diverge.
CONTEST_RADIUS = 1.0

#: Matches `ab.run_arm` / the sandbox diff-drive footprint.
ROBOT_RADIUS = 0.3

#: Nominal-traversal sampling step. 0.1 s over a ~20 s scene is 200 samples x
#: 5 obstacles — microseconds, and fine enough that a 0.75 m/s actor moves
#: 7.5 cm between samples.
DT = 0.1


@dataclass(frozen=True)
class HazardExposure:
    """One scene's nominal-traversal exposure profile."""

    scenario: str
    n_obstacles: int
    traversal_s: float
    #: Seconds of the traversal spent within `CONTEST_RADIUS` of >= 1 obstacle.
    contested_s: float
    #: Largest number of obstacles simultaneously inside `CONTEST_RADIUS`.
    peak_contesting: int
    #: Closest surface-to-surface approach along the *nominal* path. Negative
    #: means the reference path itself passes through an obstacle — expected,
    #: since the nominal robot does not dodge.
    min_clearance: float

    @property
    def contested_fraction(self) -> float:
        """`contested_s / traversal_s` — the scale-free form, since scenes
        differ in both length and speed (`cafe_obstacle_crossing_v0` runs at
        0.3 m/s, `cafe_convoy_v0` at the 0.5 m/s default)."""
        return self.contested_s / self.traversal_s if self.traversal_s > 0 else 0.0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.scenario}: {self.n_obstacles} obs, "
                f"contested {self.contested_s:.1f}/{self.traversal_s:.1f} s "
                f"({self.contested_fraction:.0%}), peak {self.peak_contesting}, "
                f"min clearance {self.min_clearance:+.2f} m")


def nominal_traversal(scenario: Scenario, dt: float = DT) -> np.ndarray:
    """(T, 3) `[t, x, y]` of the reference path walked at `target_speed`.

    Arc-length parameterised over the waypoint polyline, so a scene's own
    `target_speed_mps` sets both the duration and — crucially for a moving
    obstacle — *when* the robot is at each point. Two scenes with identical
    actor schedules and different speeds have different exposure, which is
    the correct behaviour: the hazard is a rendezvous, not a place.
    """
    xy = np.asarray(scenario.waypoints, dtype=float)[:, :2]
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    s_wp = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s_wp[-1])
    speed = max(float(scenario.target_speed), 1e-6)
    duration = total / speed
    t = np.arange(0.0, duration + dt, dt)
    s = np.minimum(t * speed, total)
    return np.stack([t,
                     np.interp(s, s_wp, xy[:, 0]),
                     np.interp(s, s_wp, xy[:, 1])], axis=1)


def clearance_matrix(traj: np.ndarray, obstacles: Sequence[CircleObstacle],
                     robot_radius: float = ROBOT_RADIUS) -> np.ndarray:
    """(T, N) surface-to-surface clearance per sample per obstacle.

    Empty `(T, 0)` when the scene has no obstacles — callers must handle that
    rather than get a silent `+inf`, because "no obstacles" is exactly the
    defect 17:00's screen found in four of eight scenes.
    """
    t, xy = traj[:, 0], traj[:, 1:3]
    if not obstacles:
        return np.empty((len(t), 0))
    return np.stack([
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ], axis=1)


def hazard_exposure(path: str, *, contest_radius: float = CONTEST_RADIUS,
                    dt: float = DT) -> HazardExposure:
    """Screen one scenario yaml. Simulates nothing."""
    scen = load_scenario(path)
    traj = nominal_traversal(scen, dt=dt)
    clear = clearance_matrix(traj, scen.obstacles)
    duration = float(traj[-1, 0])
    if clear.shape[1] == 0:
        return HazardExposure(scenario=os.path.basename(path), n_obstacles=0,
                              traversal_s=duration, contested_s=0.0,
                              peak_contesting=0, min_clearance=float("inf"))
    contesting = clear < contest_radius                      # (T, N) bool
    return HazardExposure(
        scenario=os.path.basename(path),
        n_obstacles=clear.shape[1],
        traversal_s=duration,
        contested_s=float(contesting.any(axis=1).sum()) * dt,
        peak_contesting=int(contesting.sum(axis=1).max()),
        min_clearance=float(clear.min()),
    )


def screen_scenarios(paths: Iterable[str], **kw) -> list[HazardExposure]:
    """Screen many, sorted by descending exposure — the ranking Q-040 asks
    about is the whole output, so return it ordered rather than making every
    caller re-sort."""
    return sorted((hazard_exposure(p, **kw) for p in paths),
                  key=lambda e: e.contested_fraction, reverse=True)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse
    import glob

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenarios", default="eval/scenarios/*.yaml")
    ap.add_argument("--contest-radius", type=float, default=CONTEST_RADIUS)
    args = ap.parse_args(argv)

    from .calibrate_lam import is_scenario_yaml
    paths = [p for p in sorted(glob.glob(args.scenarios)) if is_scenario_yaml(p)]
    for e in screen_scenarios(paths, contest_radius=args.contest_radius):
        print(e)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
