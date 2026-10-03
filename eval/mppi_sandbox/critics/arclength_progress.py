# SPDX-License-Identifier: BSD-3-Clause
"""`ArclengthProgressCritic` — reward forward progress along the path (D-511).

D-510 left city_figure8_v1 unmeasurable for a controller reason: every arm
prices only `dist_goal`, and a figure-8 has to end near where it began, so stock
MPPI drives 1.74 m to the goal and skips 16.3 m of loop. The existing
`ProgressPriceCritic` (D-243) cannot fix that, and the reason is its projection,
not its weight: `arclength_along` projects each point onto the *nearest*
segment, and on a path that returns near its start the nearest segment to the
shortcut is the path's own final segment. Driving toward the goal therefore
reads as ~15 m of instantaneous progress — the freeze price *pays* for the
shortcut it should forbid.

This critic fixes the projection, not the weight:

* **Windowed.** Points project only onto the part of the polyline whose
  arclength lies in ``[s_robot - back, s_robot + ahead]``. A rollout cannot
  claim arclength it has not driven to.
* **Monotone robot arclength.** ``s_robot`` is advanced from the robot's own
  pose through the same window and never decreases, so the crossing at the
  centre of a figure-8 cannot alias the robot onto the other lobe.

Cost per rollout ``k`` (a reward, so it is subtracted)::

    cost[k] = -w_progress * (s_window(traj[k, -1]) - s_robot)

Separately, :meth:`goal_gate` says whether the goal attractor should apply at
all: only once the remaining arclength ``L - s_robot`` is within
``goal_gate`` metres. Without it the terminal ``dist_goal²`` term keeps pulling
toward a goal that is geometrically close and topologically far.

`w_progress = 0.0` is the default; the controller then never constructs a
projection and the goal gate is open, so every run recorded before this term
existed is byte-identical (D-027 ablation invariant).
"""

from __future__ import annotations

import numpy as np


def arclength_windowed(pts: np.ndarray, path_xy: np.ndarray,
                       lo: float, hi: float) -> np.ndarray:
    """Arclength [m] of each point `(N,2)` projected onto the path window [lo, hi].

    Segments whose arclength span does not overlap the window are excluded;
    the result is clipped to the window, so a point beside an excluded
    segment reads as the window edge rather than as that segment's arclength.
    """
    pts = np.asarray(pts, dtype=float)
    a, b = path_xy[:-1], path_xy[1:]
    d = b - a
    seg_len = np.linalg.norm(d, axis=1)
    len2 = np.maximum(seg_len ** 2, 1e-12)
    cum = np.concatenate(([0.0], np.cumsum(seg_len)))
    live = (cum[1:] >= lo) & (cum[:-1] <= hi)                # (S,)

    ap = pts[:, None, :] - a[None]
    t = np.clip((ap * d[None]).sum(axis=2) / len2, 0.0, 1.0)
    dist = np.linalg.norm(ap - t[..., None] * d[None], axis=2)
    dist[:, ~live] = np.inf
    nearest = dist.argmin(axis=1)
    idx = np.arange(len(pts))
    s = cum[nearest] + t[idx, nearest] * seg_len[nearest]
    return np.clip(s, lo, hi)


class ArclengthProgressCritic:
    """Stateful progress reward over a windowed, monotone path projection."""

    def __init__(self, path_xy: np.ndarray, w_progress: float = 0.0,
                 ahead: float = 3.5, back: float = 0.5,
                 goal_gate: float = 3.0, detour_ratio: float = 0.0):
        self.path_xy = np.asarray(path_xy, dtype=float)
        self.w_progress = float(w_progress)
        self.ahead, self.back = float(ahead), float(back)
        self.goal_gate_m = float(goal_gate)
        # D-512: also open the gate when the remaining path is no longer than
        # `detour_ratio` x the straight-line distance to the goal, i.e. the goal
        # is not "geometrically close, topologically far". 0 = off (D-511).
        self.detour_ratio = float(detour_ratio)
        self._xy = self.path_xy[0]
        self.length = float(np.linalg.norm(np.diff(self.path_xy, axis=0),
                                           axis=1).sum())
        self.s_robot = 0.0

    def update(self, xy: np.ndarray) -> float:
        """Advance `s_robot` from the robot pose; never moves backward."""
        if self.w_progress == 0.0:
            return self.s_robot
        self._xy = np.asarray(xy, dtype=float).reshape(2)
        s = arclength_windowed(np.asarray(xy, dtype=float).reshape(1, 2),
                               self.path_xy, self.s_robot - self.back,
                               self.s_robot + self.back)[0]
        self.s_robot = max(self.s_robot, float(s))
        return self.s_robot

    def goal_gate(self) -> float:
        """1.0 if the goal attractor should apply, else 0.0."""
        if self.w_progress == 0.0:
            return 1.0
        remaining = self.length - self.s_robot
        if remaining <= self.goal_gate_m:
            return 1.0
        euclid = float(np.linalg.norm(self.path_xy[-1] - self._xy))
        return 1.0 if remaining <= self.detour_ratio * euclid else 0.0

    def cost(self, traj: np.ndarray) -> np.ndarray:
        """`(K,)` progress reward (negative cost) for rollouts `(K,H,>=2)`."""
        K = traj.shape[0]
        if self.w_progress == 0.0:
            return np.zeros(K)
        s_end = arclength_windowed(traj[:, -1, :2], self.path_xy,
                                   self.s_robot - self.back,
                                   self.s_robot + self.ahead)
        return -self.w_progress * (s_end - self.s_robot)
