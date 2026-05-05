# SPDX-License-Identifier: BSD-3-Clause
"""Path-tracking metrics v0 for the Representation-Aware-MPPI project.

North-star alignment: "perfect obstacle avoidance + path tracking in all
environments" — quantifying the *path tracking* half. v0 is intentionally
qualitative-grade (P5 will calibrate against real-world rosbag truth).

API contract
------------
- A *trajectory* is shape (T, 6): columns = [t, x, y, yaw, v, omega].
- A *reference path* is shape (M, 3): columns = [x, y, yaw_target].
  Yaw at each waypoint is the tangent direction (path-frame).
- Path is treated as a piecewise-linear polyline; cross-track error is
  perpendicular distance to the nearest segment.

Metrics
-------
- cross_track_error(traj, path)  -> ndarray (T,)  signed [m]
- heading_error(traj, path)      -> ndarray (T,)  wrapped [-pi, pi] [rad]
- completion_percent(traj, path) -> ndarray (T,)  in [0, 1]
- time_deviation(traj, path, target_speed) -> ndarray (T,) [s]
- smoothness(traj)               -> dict (jerk_lat, jerk_lon, accel_var)
- goal_reached(traj, goal, xy_tol=0.2, yaw_tol=0.3) -> bool
- summary(traj, path, **kw)      -> dict of scalars (one row of a CSV)

All functions are pure (no I/O, no globals). Designed to be wrapped by
a ROS2 node that subscribes to /odom + /plan and logs to a CSV.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


# ---------------------------------------------------------------- helpers

def _wrap_pi(a: np.ndarray) -> np.ndarray:
    """Wrap angles to [-pi, pi]."""
    return (a + np.pi) % (2 * np.pi) - np.pi


def _cumulative_arclength(path: np.ndarray) -> np.ndarray:
    """(M,) cumulative arclength along a piecewise-linear path. path[0]=0."""
    seg = np.diff(path[:, :2], axis=0)
    seg_len = np.linalg.norm(seg, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg_len)])
    return cum


def _project_onto_polyline(xy: np.ndarray, path: np.ndarray):
    """Project a single (x, y) onto the closest segment of the path.

    Returns (foot_xy, signed_perp_dist, arclength_at_foot, segment_idx, t_param)
    where signed_perp_dist is positive on the path's left (path tangent ×
    z-up = left-normal convention).
    """
    p = path[:, :2]
    a = p[:-1]                              # (M-1, 2) seg starts
    b = p[1:]                               # (M-1, 2) seg ends
    ab = b - a                              # (M-1, 2)
    L2 = np.einsum("ij,ij->i", ab, ab)      # (M-1,) seg length squared
    L2 = np.where(L2 == 0, 1e-12, L2)
    t = np.einsum("ij,j->i", xy - a, ab[0]) if False else \
        np.einsum("ij,ij->i", xy - a, ab) / L2
    t = np.clip(t, 0.0, 1.0)
    foot = a + t[:, None] * ab              # (M-1, 2)
    diff = xy - foot                        # (M-1, 2)
    d2 = np.einsum("ij,ij->i", diff, diff)
    seg = int(np.argmin(d2))
    foot_xy = foot[seg]
    # signed perpendicular distance (positive = left of path direction)
    nrm = np.array([-ab[seg, 1], ab[seg, 0]]) / np.sqrt(L2[seg])
    signed = float(np.dot(xy - foot_xy, nrm))
    cum = _cumulative_arclength(path)
    arclen = cum[seg] + t[seg] * np.sqrt(L2[seg])
    return foot_xy, signed, arclen, seg, float(t[seg])


# ---------------------------------------------------------------- metrics

def cross_track_error(traj: np.ndarray, path: np.ndarray) -> np.ndarray:
    """Signed perpendicular distance robot → nearest path segment, per t."""
    out = np.empty(len(traj))
    for i, row in enumerate(traj):
        _, signed, _, _, _ = _project_onto_polyline(row[1:3], path)
        out[i] = signed
    return out


def heading_error(traj: np.ndarray, path: np.ndarray) -> np.ndarray:
    """Yaw error between robot heading and path tangent, wrapped [-pi, pi]."""
    out = np.empty(len(traj))
    for i, row in enumerate(traj):
        _, _, _, seg, _ = _project_onto_polyline(row[1:3], path)
        # tangent yaw from segment direction (path's stored yaw_target may
        # be a control directive, not necessarily the segment direction)
        a, b = path[seg, :2], path[seg + 1, :2]
        seg_yaw = float(np.arctan2(b[1] - a[1], b[0] - a[0]))
        out[i] = float(_wrap_pi(np.array([row[3] - seg_yaw]))[0])
    return out


def completion_percent(traj: np.ndarray, path: np.ndarray) -> np.ndarray:
    """Fraction of path length covered by the closest-point arclength, in [0, 1]."""
    cum = _cumulative_arclength(path)
    total = float(cum[-1]) if cum[-1] > 0 else 1e-12
    out = np.empty(len(traj))
    for i, row in enumerate(traj):
        _, _, arclen, _, _ = _project_onto_polyline(row[1:3], path)
        out[i] = float(np.clip(arclen / total, 0.0, 1.0))
    return out


def time_deviation(
    traj: np.ndarray,
    path: np.ndarray,
    target_speed: float,
) -> np.ndarray:
    """Actual time minus expected time at this completion %, given target speed.

    Positive = robot is behind schedule. target_speed in m/s, must be > 0.
    """
    if target_speed <= 0:
        raise ValueError("target_speed must be positive")
    cum = _cumulative_arclength(path)
    total = float(cum[-1])
    out = np.empty(len(traj))
    t0 = float(traj[0, 0])
    for i, row in enumerate(traj):
        _, _, arclen, _, _ = _project_onto_polyline(row[1:3], path)
        expected = arclen / target_speed
        actual = float(row[0]) - t0
        out[i] = actual - expected
    return out


def smoothness(traj: np.ndarray) -> dict:
    """Action-smoothness summary: jerk integrals + accel variance.

    Decomposes acceleration into longitudinal (along robot heading) and
    lateral (perpendicular). Returns scalars; integrals are L2 over time.
    """
    if len(traj) < 4:
        return {"jerk_lat": 0.0, "jerk_lon": 0.0, "accel_var": 0.0}
    t = traj[:, 0]
    dt = np.diff(t)
    dt = np.where(dt <= 0, 1e-6, dt)
    # finite-diff velocity (already in traj[:, 4]) → accel
    v = traj[:, 4]
    omega = traj[:, 5]
    yaw = traj[:, 3]
    a_lon = np.diff(v) / dt
    # lateral accel = v * omega (planar kinematic estimate)
    a_lat = (v[:-1] + v[1:]) * 0.5 * (omega[:-1] + omega[1:]) * 0.5
    # jerk = d(accel)/dt
    j_lon = np.diff(a_lon) / dt[:-1]
    j_lat = np.diff(a_lat) / dt[:-1]
    return {
        "jerk_lat": float(np.sqrt(np.sum(j_lat ** 2 * dt[:-1]))),
        "jerk_lon": float(np.sqrt(np.sum(j_lon ** 2 * dt[:-1]))),
        "accel_var": float(np.var(np.concatenate([a_lon, a_lat]))),
    }


@dataclass
class Goal:
    x: float
    y: float
    yaw: float


def goal_reached(
    traj: np.ndarray,
    goal: Goal,
    xy_tol: float = 0.2,
    yaw_tol: float = 0.3,
) -> bool:
    """True if any timestep falls within both xy and yaw tolerances of goal."""
    dxy = np.linalg.norm(traj[:, 1:3] - np.array([goal.x, goal.y]), axis=1)
    dyaw = np.abs(_wrap_pi(traj[:, 3] - goal.yaw))
    return bool(np.any((dxy <= xy_tol) & (dyaw <= yaw_tol)))


def summary(
    traj: np.ndarray,
    path: np.ndarray,
    *,
    target_speed: float = 0.5,
    goal: Optional[Goal] = None,
    xy_tol: float = 0.2,
    yaw_tol: float = 0.3,
) -> dict:
    """One-row scalar summary suitable for CSV append. north-star metric stub."""
    cte = cross_track_error(traj, path)
    he = heading_error(traj, path)
    cp = completion_percent(traj, path)
    td = time_deviation(traj, path, target_speed)
    sm = smoothness(traj)
    g = goal if goal is not None else Goal(*path[-1])
    return {
        "cte_rms": float(np.sqrt(np.mean(cte ** 2))),
        "cte_max": float(np.max(np.abs(cte))),
        "heading_err_rms": float(np.sqrt(np.mean(he ** 2))),
        "heading_err_max": float(np.max(np.abs(he))),
        "completion_final": float(cp[-1]),
        "time_deviation_final": float(td[-1]),
        "jerk_lat": sm["jerk_lat"],
        "jerk_lon": sm["jerk_lon"],
        "accel_var": sm["accel_var"],
        "goal_reached": int(goal_reached(traj, g, xy_tol, yaw_tol)),
    }
