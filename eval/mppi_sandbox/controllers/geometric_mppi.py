# SPDX-License-Identifier: BSD-3-Clause
"""The **geometric null arm** — min-clearance in the risk term's cost slot.

`research/feed.md`'s 2026-08-09 entry (arxiv 2607.16591) is the first surfaced
result aimed straight at this branch's premise. Two of its numbers matter here
and they are not the headline. `corr(σ_dyn, ρ) = 0.108 ± 0.014` over ~50K
visited states says dynamics-model disagreement barely ranks true collision
proximity; the **substitution** result says what to do about it — at matched λ
and paired seeds, a plain **min-lidar** term in the same one-variable cost slot
collides **1%** where the dynamics-uncertainty term collides **34%**.

The entry's own honest note is the reason this module exists: *min-lidar winning
is not a representation result — it is the geometric baseline, available with no
learning at all, which is precisely why it is the arm the project has not run.*

What the null actually swaps
----------------------------

`RiskMPPI`'s live term on every walked rung is `w_risk` × the BEV **DYNAMIC**
channel summed over rollout points — Gaussian blobs laid along each scripted
obstacle's *predicted* sweep. That is the anticipation claim: yield early, give
a wide berth, rather than react at the rollout instant.

`GeometricMPPI` puts a term of the same shape in the same slot
(:meth:`StockMPPI._extra_cost`) and takes the anticipation out:

    cost += w_geom · Σ_t exp( −min_n( ‖x_t − p_n(t₀)‖ − r_n − r_robot ) / scale )

Three properties, each chosen so the swap is one variable rather than several:

- **Obstacle positions are frozen at `t₀`.** `p_n(t₀)`, not `p_n(t)`. This is
  what one lidar scan gives you: where things are now, with no motion model and
  no channel producer. It is the whole difference from the DYNAMIC channel,
  which is a *prediction* rendered forward over the horizon.
- **Reduced by `min` over obstacles, not summed.** A lidar returns the nearest
  return per bearing; the sandbox's own soft barrier sums `exp(−clear/scale)`
  over every obstacle independently, which is a different (and less
  lidar-shaped) quantity. `min` is what makes this the *min-lidar* null and not
  a second copy of the barrier.
- **`w_geom = 0` ⇒ byte-identical to `stock_mppi`.** The ablation invariant
  every controller on this branch carries (`RiskMPPI`'s `w_epist` / `w_voo`
  defaults exist for the same reason), pinned by test rather than asserted.

On the coefficient — the obvious choice was measured and refused
-----------------------------------------------------------------

The first draft set `w_geom = w_risk = 40.0`: the same number in the same slot,
defended by a *shape* argument rather than a measurement, on the grounds that
both summands are ≈1 at contact and decay to 0 with distance (the DYNAMIC
channel's blob peaks at 1.0, `exp(−clear/scale)` equals 1.0 at `clear = 0`).

That argument is wrong and the sandbox says so. At the recorded rung's own
λ = 0.8 the equal-coefficient null runs at median ESS **12.40** against the risk
arm's **105.07** — 4 of 8 seeds outside `ab.ess_band` — and a λ ladder finds no
temperature admissible for all three arms at once. Equal coefficient is not
equal loudness, so the "one-variable swap" as first written moved two variables:
the term and the sampler's operating point.

:mod:`geometric_null` therefore calibrates `w_geom` by the sampler's own
response at fixed λ, which is a *stricter* match than
`scale_match.weight_for_ratio`'s cost-ratio rather than a weaker one — it
equalises the quantity the comparison is actually sensitive to. (The
cost-ratio route is also not available off the shelf: it cannot be pointed at
`w_geom` without a `scale_match.ADDITIVE_WEIGHTS` entry.)

The residual asymmetry still holds and still matters: a null arm that loses is
not thereby a weaker *mechanism*, only possibly a quieter one, whereas a null
arm that ties or wins is not exposed to that objection at all.
"""

from __future__ import annotations

import numpy as np

from ..dynamics import Limits
from .stock_mppi import MPPIParams, StockMPPI


def frozen_min_clearance(traj_xy: np.ndarray, obstacles, t0: float,
                         robot_radius: float) -> np.ndarray:
    """`(K,H)` nearest-obstacle clearance with the scene **frozen at `t₀`**.

    Split out from the controller so the "no motion model" property is testable
    on its own: feeding a moving obstacle and two different `t0` must move the
    answer, while feeding two different rollout *times* at one `t0` must not.
    """
    if not obstacles:
        return np.full(traj_xy.shape[:2], np.inf)
    per_obstacle = []
    for ob in obstacles:
        pos = np.asarray(ob.position(np.array([t0])), dtype=float)[0]  # (2,)
        per_obstacle.append(np.linalg.norm(traj_xy - pos, axis=2)
                            - ob.radius - robot_radius)
    return np.min(np.stack(per_obstacle, axis=-1), axis=-1)


class GeometricMPPI(StockMPPI):
    """`StockMPPI` + a frozen min-clearance penalty in `RiskMPPI`'s cost slot."""

    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3,
                 w_geom: float = 0.0,
                 geom_scale: float | None = None):
        super().__init__(scenario, seed=seed, params=params, limits=limits,
                         robot_radius=robot_radius)
        self.w_geom = float(w_geom)
        # Defaults to the barrier's own decay length so the null is not
        # silently given a second free parameter to be tuned on.
        self.geom_scale = (float(self.p.obs_soft_scale) if geom_scale is None
                           else float(geom_scale))
        if self.geom_scale <= 0.0:
            raise ValueError("geom_scale must be positive — it is a decay "
                             "length in metres")

    def _extra_cost(self, traj: np.ndarray, t0: float) -> np.ndarray:
        K = traj.shape[0]
        if self.w_geom == 0.0 or not self.obstacles:
            return np.zeros(K)
        clear = frozen_min_clearance(traj[..., :2], self.obstacles, t0,
                                     self.robot_radius)
        # Clipped before the exponential for the same reason the barrier is
        # not: a deep interpenetration would otherwise overflow to inf and
        # make one rollout's cost non-finite, which the softmax cannot rank.
        return self.w_geom * np.exp(
            -np.clip(clear, -3.0 * self.geom_scale, None) / self.geom_scale
        ).sum(axis=1)
