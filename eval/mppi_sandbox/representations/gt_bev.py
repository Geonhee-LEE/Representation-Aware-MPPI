# SPDX-License-Identifier: BSD-3-Clause
"""Ground-truth BEV producer — the sandbox's first D-012 representation.

Renders a (5, H, W) risk stack + (5, H, W) observability mask on an
ego-centered, world-axis-aligned grid, from the scenario's ground-truth
obstacle state. "GT" means the *perception* is oracle-grade; the point is
to give cost critics (D-013/D-014) a contract-correct input so the
algorithm ceiling can be measured before any learned producer exists.

Channels (RiskChannel order, D-012):
- STATIC (0):  occupancy risk of schedule-less obstacles (1.0 inside disc,
  Gaussian skirt outside). Observed within sensing range + line-of-sight.
- DYNAMIC (1): *anticipatory* risk of scripted obstacles — union of
  Gaussian blobs swept along the obstacle's predicted positions over the
  next `predict_horizon_s`, decayed over prediction time. A rollout
  sampling this static field sees where the obstacle is *going to be*.
- TRAVERSABILITY (2): 0.0 everywhere (flat world). Observed like STATIC.
- EPISTEMIC (3): normalized σ ∈ [0, 1]. 0 where the robot can see;
  1 beyond sensing range and inside occlusion shadows cast by obstacle
  discs. Mask is all-True: we always know how ignorant we are.
- ALEATORIC (4): unimplemented → all-unobserved row, zero data (D-012:
  renderers can land later with zero cost-side change).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import N_CHANNELS, RiskChannel


@dataclass
class BevStack:
    stack: np.ndarray        # (5, H, W) float32
    mask: np.ndarray         # (5, H, W) bool — True = observed/evaluated
    origin: np.ndarray       # (2,) world xy of cell [0, 0] corner
    resolution: float

    def sample(self, channel: RiskChannel, pts: np.ndarray,
               unobserved_value: float = 1.0) -> np.ndarray:
        """Nearest-cell lookup for (N, 2) world points.

        Out-of-grid or unobserved cells return `unobserved_value`
        (pessimistic prior — D-012: unobserved ≠ zero risk).
        """
        idx = np.floor((pts - self.origin) / self.resolution).astype(int)
        h, w = self.stack.shape[1:]
        inside = ((idx[:, 0] >= 0) & (idx[:, 0] < w)
                  & (idx[:, 1] >= 0) & (idx[:, 1] < h))
        out = np.full(len(pts), unobserved_value, dtype=float)
        r, c = idx[inside, 1], idx[inside, 0]
        vals = self.stack[channel, r, c].astype(float)
        observed = self.mask[channel, r, c]
        out[inside] = np.where(observed, vals, unobserved_value)
        return out


class GTBevProducer:
    def __init__(self, obstacles, *, grid_size: int = 64,
                 resolution: float = 0.125, sensing_range: float = 5.0,
                 predict_horizon_s: float = 3.0, predict_samples: int = 10,
                 blob_scale: float = 1.5):
        self.obstacles = obstacles
        self.n = grid_size
        self.res = resolution
        self.r_sense = sensing_range
        self.t_pred = predict_horizon_s
        self.n_pred = predict_samples
        self.blob_scale = blob_scale   # blob sigma = blob_scale * radius

    def render(self, robot_xy: np.ndarray, t: float) -> BevStack:
        n, res = self.n, self.res
        half = n * res / 2.0
        origin = np.asarray(robot_xy, dtype=float) - half
        # cell-center world coordinates, row-major [y, x]
        ax = origin[0] + (np.arange(n) + 0.5) * res
        ay = origin[1] + (np.arange(n) + 0.5) * res
        cx, cy = np.meshgrid(ax, ay)                       # (H, W)
        cells = np.stack([cx.ravel(), cy.ravel()], axis=1)  # (N, 2)

        stack = np.zeros((N_CHANNELS, n, n), dtype=np.float32)
        mask = np.zeros((N_CHANNELS, n, n), dtype=bool)

        in_range = (np.linalg.norm(cells - robot_xy, axis=1)
                    <= self.r_sense).reshape(n, n)
        occluded = self._occlusion(robot_xy, cells, t).reshape(n, n)
        visible = in_range & ~occluded

        static_obs = [o for o in self.obstacles if len(o.schedule) == 0]
        dynamic_obs = [o for o in self.obstacles if len(o.schedule) > 0]

        # STATIC: hard occupancy + Gaussian skirt
        for ob in static_obs:
            d = np.linalg.norm(cells - [ob.x, ob.y], axis=1).reshape(n, n)
            sig = self.blob_scale * ob.radius
            stack[RiskChannel.STATIC] = np.maximum(
                stack[RiskChannel.STATIC],
                np.where(d <= ob.radius, 1.0,
                         np.exp(-0.5 * ((d - ob.radius) / sig) ** 2)))
        mask[RiskChannel.STATIC] = visible

        # DYNAMIC: predicted-sweep risk, decaying over prediction time
        taus = np.linspace(0.0, self.t_pred, self.n_pred)
        decay = np.exp(-taus / self.t_pred)
        for ob in dynamic_obs:
            pos = ob.position(t + taus)                    # (n_pred, 2)
            sig = self.blob_scale * ob.radius
            d = np.linalg.norm(cells[:, None, :] - pos[None], axis=2)
            blob = np.exp(-0.5 * (d / sig) ** 2) * decay[None]
            stack[RiskChannel.DYNAMIC] = np.maximum(
                stack[RiskChannel.DYNAMIC],
                blob.max(axis=1).reshape(n, n))
        mask[RiskChannel.DYNAMIC] = visible

        # TRAVERSABILITY: flat world — zero risk where observed
        mask[RiskChannel.TRAVERSABILITY] = visible

        # EPISTEMIC: σ=0 seen, σ=1 unseen (range or occlusion shadow)
        stack[RiskChannel.EPISTEMIC] = np.where(visible, 0.0, 1.0)
        mask[RiskChannel.EPISTEMIC] = True   # ignorance is always evaluated

        # ALEATORIC: unimplemented → all-unobserved row (D-012)

        return BevStack(stack=stack, mask=mask, origin=origin, resolution=res)

    def _occlusion(self, robot_xy: np.ndarray, cells: np.ndarray,
                   t: float) -> np.ndarray:
        """True where the robot→cell ray passes through an obstacle disc."""
        occ = np.zeros(len(cells), dtype=bool)
        for ob in self.obstacles:
            c = ob.position(t) if len(ob.schedule) else np.array([ob.x, ob.y])
            seg = cells - robot_xy                          # (N, 2)
            seg_len2 = np.maximum((seg * seg).sum(axis=1), 1e-12)
            u = np.clip(((c - robot_xy) * seg).sum(axis=1) / seg_len2, 0.0, 1.0)
            foot = robot_xy + u[:, None] * seg
            blocked = np.linalg.norm(foot - c, axis=1) <= ob.radius
            # only cells strictly beyond the disc are shadowed
            behind = (np.linalg.norm(cells - robot_xy, axis=1)
                      > np.linalg.norm(c - robot_xy) + ob.radius)
            occ |= blocked & behind
        return occ
