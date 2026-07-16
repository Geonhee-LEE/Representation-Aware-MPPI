# SPDX-License-Identifier: BSD-3-Clause
"""Visibility-gated MPPI — StockMPPI that charges only *observed* obstacles.

The sandbox baseline (`stock_mppi`) plans against oracle obstacle knowledge:
its soft barrier + hard collision penalty sum over *every* obstacle at its
ground-truth position, regardless of whether the robot could actually see it.
Under that model occlusion can never change a collision outcome — it only
changes how blind the approach *looks* (STATE bottleneck, 2026-07-13).

This variant closes that gap on the *cost* side. At each control step it
filters the obstacle set to those the robot currently observes — nearest
surface within `sensing_range` AND not hidden in the line-of-sight shadow of a
*nearer* obstacle disc — and lets the inherited StockMPPI cost act on that
subset only. The visibility geometry mirrors ``GTBevProducer._occlusion``
(D-012), so the representation-side observability mask and this
controller-side gate agree by construction.

Consequence (the Q-017 unblock this enables): an obstacle occluded behind a
nearer one is invisible to the planner, so a visibility-gated robot drives
toward a hidden pocket the oracle baseline routes around — occlusion finally
moves a clearance/collision outcome, and an epistemic-aware controller has a
real failure to beat.

Ablation invariant: with ``sensing_range = inf`` (default) and no obstacle
occluding another, every obstacle is observed, so the gate is a no-op and the
run reproduces ``stock_mppi`` byte-for-byte. Inter-obstacle occlusion still
fires at infinite range (a nearer disc hides a farther one on the same ray) —
that is the intended lever, so the invariant holds only when no such shadow
exists.
"""

from __future__ import annotations

import numpy as np

from ..dynamics import Limits
from .stock_mppi import MPPIParams, StockMPPI


class VisibilityGatedMPPI(StockMPPI):
    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3,
                 sensing_range: float = float("inf")):
        super().__init__(scenario, seed=seed, params=params, limits=limits,
                         robot_radius=robot_radius)
        # StockMPPI.__init__ bound self.obstacles = scenario.obstacles; keep the
        # ground-truth set separately and expose the per-step visible subset.
        self._all_obstacles = list(self.obstacles)
        self.sensing_range = sensing_range
        self.last_observed = list(self.obstacles)   # introspection for tests

    def command(self, state: np.ndarray, t: float) -> np.ndarray:
        self.last_observed = self.observed_obstacles(state[:2], t)
        self.obstacles = self.last_observed          # inherited _cost reads this
        return super().command(state, t)

    def observed_obstacles(self, robot_xy: np.ndarray, t: float) -> list:
        """Obstacles visible from ``robot_xy`` at time ``t``.

        Visible = nearest surface within ``sensing_range`` AND the robot→center
        ray is not blocked by a *nearer* obstacle disc. A disc never occludes
        itself.
        """
        robot_xy = np.asarray(robot_xy, dtype=float)
        centers = [ob.position(t) for ob in self._all_obstacles]
        dists = [float(np.linalg.norm(c - robot_xy)) for c in centers]
        observed = []
        for i, ob in enumerate(self._all_obstacles):
            if dists[i] - ob.radius > self.sensing_range:
                continue
            if self._occluded(robot_xy, centers[i], dists[i], i, centers, dists):
                continue
            observed.append(ob)
        return observed

    def _occluded(self, robot_xy, target_c, target_d, target_i,
                  centers, dists) -> bool:
        """True if a nearer obstacle disc crosses the robot→target sightline."""
        seg = target_c - robot_xy
        seg_len2 = max(float(seg @ seg), 1e-12)
        for j, oc in enumerate(self._all_obstacles):
            if j == target_i or dists[j] >= target_d:
                continue                              # only strictly nearer discs
            u = np.clip(float((centers[j] - robot_xy) @ seg) / seg_len2, 0.0, 1.0)
            foot = robot_xy + u * seg
            if float(np.linalg.norm(foot - centers[j])) <= oc.radius:
                return True
        return False
