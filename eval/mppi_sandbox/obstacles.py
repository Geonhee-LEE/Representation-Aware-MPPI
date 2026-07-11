# SPDX-License-Identifier: BSD-3-Clause
"""Circle obstacles: static or scripted by time-stamped waypoints.

Matches the `dynamic_obstacles:` block of eval/scenarios/*.yaml:

    dynamic_obstacles:
      - id: ped_head_on
        init: { x: 0.0, y: -5.5 }
        waypoints:
          - { t: 0.0, x: 0.0, y: -5.5 }
          - { t: 6.0, x: 0.0, y:  0.5 }

Position is piecewise-linear in t; held at the last waypoint afterwards.
An obstacle with no waypoints is static at `init`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

DEFAULT_RADIUS = 0.3  # actor capsule footprint (matches cafe3 pedestrians)


@dataclass
class CircleObstacle:
    x: float
    y: float
    radius: float = DEFAULT_RADIUS
    # (W, 3) rows [t, x, y]; empty = static
    schedule: np.ndarray = field(default_factory=lambda: np.empty((0, 3)))

    def position(self, t) -> np.ndarray:
        """Position(s) at time t. Scalar t -> (2,); array (H,) -> (H, 2)."""
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        if len(self.schedule) == 0:
            pos = np.broadcast_to([self.x, self.y], (len(t_arr), 2)).copy()
        else:
            ts = self.schedule[:, 0]
            pos = np.stack([
                np.interp(t_arr, ts, self.schedule[:, 1]),
                np.interp(t_arr, ts, self.schedule[:, 2]),
            ], axis=1)
        return pos[0] if np.isscalar(t) or np.asarray(t).ndim == 0 else pos

    @classmethod
    def from_yaml(cls, entry: dict) -> "CircleObstacle":
        init = entry.get("init", {})
        wps = entry.get("waypoints", [])
        schedule = (np.array([[w["t"], w["x"], w["y"]] for w in wps], dtype=float)
                    if wps else np.empty((0, 3)))
        return cls(
            x=float(init.get("x", 0.0)),
            y=float(init.get("y", 0.0)),
            radius=float(entry.get("radius", DEFAULT_RADIUS)),
            schedule=schedule,
        )


def min_clearance(traj: np.ndarray, obstacles: list[CircleObstacle],
                  robot_radius: float) -> float:
    """Minimum surface-to-surface clearance over a logged (T, 6) trajectory.

    Negative = interpenetration (collision). +inf if no obstacles.
    """
    if not obstacles:
        return float("inf")
    t, xy = traj[:, 0], traj[:, 1:3]
    clearances = [
        np.linalg.norm(xy - ob.position(t), axis=1) - ob.radius - robot_radius
        for ob in obstacles
    ]
    return float(np.min(clearances))
