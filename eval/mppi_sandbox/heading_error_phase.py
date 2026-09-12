# SPDX-License-Identifier: BSD-3-Clause
"""Localize where `heading_err_rms` comes from in the knee+shape residual.

`test_knee_shape_ensemble.py` (D-430) found the avoidance problem on
`cafe_obstacle_crossing_v0` solved (16/16 clearance) but `heading_err_rms_max`
still failing on 10 of 16 seeds under the `knee+shape` arm. STATE named the
open question as *where* in those trajectories the error comes from —
avoidance maneuver, recovery, or steady driving — before proposing a knob.

The first attempt at an answer used a discrete clearance-band phase split
(avoidance / recovery / steady) at `AVOIDANCE_BAND = 0.30` — the same value
the `knee`/`shape` knobs are already set to. It reported **100% steady, 0%
avoidance, 0% recovery on every one of the 10 failing seeds** — apparently the
opposite of what the residual's own name suggests. That reading is an
artifact, not a finding: the compact-support barrier's whole job is to keep
clearance just outside its own band, and measured minimum clearance across
all 16 seeds is 0.3001–0.3279 m — **strictly above 0.30 on every seed, by as
little as 0.0001 m** (`test_the_barrier_never_enters_its_own_band` pins this).
A `clearance <= 0.30` test therefore fires on zero timesteps by construction,
not because avoidance never happens. Widening the band to 0.5–2.5 m (tried
during triage, not shipped as a knob) flips the verdict almost entirely to
"avoidance dominates" instead — which shows the *discrete*-phase framing
itself is not well-posed on this scene: obstacle proximity is continuous
here, not bimodal, so any fixed cut is reporting where the cut is, not where
the error is.

The threshold-free replacement: correlate clearance(t) with |heading_error(t)|
within each run (Spearman, reusing `avoidance_price.spearman`). This needs no
band at all. The answer is unambiguous and holds for **all 16 seeds, passing
and failing alike**: rho is negative for every one (range -0.117 to -0.599,
median ≈ -0.32) — heading error rises as the robot nears the obstacle, never
the reverse. The location of each failing seed's single worst heading-error
instant confirms it directly: peak clearance at that instant is 0.32–1.05 m
across the 10 failing seeds, well inside the scene's un-obstructed cruising
ceiling (~3.0 m clearance is typical mid-run). So the residual is a
near-obstacle effect, not a steady-driving one — the opposite of the naive
banded read, and the answer STATE's next-action asked for.
"""

from __future__ import annotations

import numpy as np

from eval.path_tracking_metrics import heading_error

from . import ab
from .avoidance_price import spearman
from .controllers.stock_mppi import MPPIParams
from .obstacles import CircleObstacle
from .scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"
#: Same value as `test_collision_knee.GATE` / `test_barrier_shape.GATE` — the
#: knee+shape arm's own hard clearance knob. Kept here only to reproduce that
#: arm and to document the boundary artifact above; it is *not* used as a
#: localization threshold (see module docstring).
AVOIDANCE_BAND = 0.30
#: The scenario's own declared threshold (cafe_obstacle_crossing_v0.yaml).
HEADING_ERR_RMS_MAX = 0.30
ROBOT_RADIUS = 0.3
SEEDS = tuple(range(16))
#: Calibration for the peak-location claim: well above every observed peak
#: clearance among the 10 failing seeds (max measured 1.05 m) and well below
#: the run's un-obstructed cruising ceiling (~3.0 m) — see
#: `test_failing_seeds_peak_error_sits_near_the_obstacle`.
NEAR_OBSTACLE_CLEARANCE = 1.5


def per_timestep_clearance(
    traj: np.ndarray, obstacles: list[CircleObstacle], robot_radius: float,
) -> np.ndarray:
    """(T,) surface-to-surface clearance to the nearest obstacle at each step.

    Same reduction as `obstacles.min_clearance`, minus the final min-over-time
    — that scalar is exactly what this array reduces to under `.min()`, so the
    two cannot silently disagree.
    """
    if not obstacles:
        return np.full(len(traj), np.inf)
    t, xy = traj[:, 0], traj[:, 1:3]
    per_ob = np.stack([
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ], axis=0)
    return per_ob.min(axis=0)


def heading_clearance_correlation(
    traj: np.ndarray, path: np.ndarray, obstacles: list[CircleObstacle],
    robot_radius: float = ROBOT_RADIUS,
) -> float:
    """Spearman rho between clearance(t) and |heading_error(t)| over one run.

    Negative ⇒ heading error rises as the robot nears the obstacle. No band,
    no fitted cut — a rank correlation over the whole trajectory.
    """
    clearance = per_timestep_clearance(traj, obstacles, robot_radius)
    he = np.abs(heading_error(traj, path))
    return spearman(clearance, he)


def peak_heading_error_location(
    traj: np.ndarray, path: np.ndarray, obstacles: list[CircleObstacle],
    robot_radius: float = ROBOT_RADIUS,
) -> tuple[float, float]:
    """(t, clearance) at the single largest |heading_error| instant of one run."""
    clearance = per_timestep_clearance(traj, obstacles, robot_radius)
    he = np.abs(heading_error(traj, path))
    i = int(np.argmax(he))
    return float(traj[i, 0]), float(clearance[i])


def seed_sweep_knee_shape(seeds: tuple[int, ...] = SEEDS, scenario_path: str = CROSSING):
    """`ab.ArmRun` list for the `knee+shape` arm — the arm D-430 found
    clearance-clean but heading-residual-positive on this scene."""
    scenario = load_scenario(scenario_path)
    params = MPPIParams(collision_margin=AVOIDANCE_BAND, obs_barrier_band=AVOIDANCE_BAND)
    return scenario, ab.seed_sweep(scenario, "stock_mppi", seeds=list(seeds), params=params)


def failing_seed_localization(
    scenario_path: str = CROSSING, seeds: tuple[int, ...] = SEEDS,
) -> dict[int, dict]:
    """{seed: {heading_rms, rho, peak_t, peak_clearance}} for every seed
    failing `heading_err_rms_max` under the `knee+shape` arm."""
    scenario, runs = seed_sweep_knee_shape(seeds, scenario_path)
    out = {}
    for r in runs:
        he_rms = float(np.sqrt(np.mean(heading_error(r.traj, scenario.waypoints) ** 2)))
        if he_rms <= HEADING_ERR_RMS_MAX:
            continue
        peak_t, peak_clr = peak_heading_error_location(
            r.traj, scenario.waypoints, scenario.obstacles)
        out[r.seed] = {
            "heading_rms": he_rms,
            "rho": heading_clearance_correlation(
                r.traj, scenario.waypoints, scenario.obstacles),
            "peak_t": peak_t,
            "peak_clearance": peak_clr,
        }
    return out
