# SPDX-License-Identifier: BSD-3-Clause
"""ObservationValueCritic — the aggregate value-of-observation replacement for
the per-cell shadow cost (2404.07781 borrow; D-021 finding #2 / #4).

D-021 measured `ShadowCostCritic` **signal-free** on `cafe_obstacle_crossing_v0`
at the shipped `H = 30`: the per-sample cost spread is exactly 0.00 at all 92
control steps and `w_epist = 200` executes a byte-identical trajectory to
`w_epist = 0` on 4/4 seeds. The reason is structural, not a tuning failure:

    cost_k = w_epist · Σ_h σ(x_kh)

samples σ **at the rollout point**. It is a *distance-to-unseen* cost — it only
becomes non-constant once some rollout actually enters a shadow. On this scene
the rollout cloud reaches far *along* the path while the shadows sit *lateral
to and behind* the actors, so every sample collects the same σ = 0 and the term
cancels exactly in the softmax. D-021 finding #4 pinned the consequence: the
obvious scalar summary ("live iff max reach ≥ distance to nearest unseen cell")
is false on 28 of those 92 steps, because **direction has to enter the
statement, not just distance**.

This critic changes the construction rather than the weight. Following
2404.07781's stated thesis — that evaluating each occlusion individually
"can result in conflicting priorities for the planner, as individual occlusion
costs may appear to be in opposition", and that the fix is one aggregate map
whose cell value is the information the vehicle gains by *visiting* that cell —
the field here is

    V(q) = fraction of the currently-shadowed cells that become visible
           from observation location q                         ∈ [0, 1]
    cost_k = w_voo · Σ_h (1 − V(x_kh))

A **value-of-observation-at-a-location** cost, not a distance-to-unseen cost.
The difference that matters for D-021:

- Distance-to-unseen is zero wherever the rollouts actually go, because going
  there does not enter a shadow. Silence is the *typical* case.
- Value-of-observation is evaluated at exactly the locations the rollouts do
  reach, and it varies between them whenever the occluder geometry differs —
  a lateral offset that peeks around an actor scores higher than one that does
  not. Silence requires there to be no shadow at all.

Direction-dependence (the question the feed flagged as *the* reason to read the
RA-L PDF — unsettled here, the fetch was unavailable in this session): the
stored value is a **scalar per location**, but its *construction* is bearing-
dependent, because visibility from `q` runs the same robot→cell ray test the
producer uses, against the same discs. Two locations equidistant from the
nearest shadow cell therefore score differently when they sit on opposite sides
of the occluder. `test_observation_value_critic.py` pins that as a constructed
counterexample — it is the D-021 #4 geometry stated positively.

Contract (mirrors D-013 / Q-017 so P5 ablation attribution holds):
- standalone — never overloads the baseline obstacle term or the shadow cost
- add-only: cost ≥ 0 (V ∈ [0, 1], w_voo ≥ 0)
- w_voo = 0.0 default → exact no-op → baseline reproduction (ablation invariant)
- no shadowed cells in range → zero map → constant cost → **honest silence**,
  reported (`n_targets == 0`) rather than hidden
- out-of-grid rollout points score V = 0 (pessimistic: a location we cannot
  evaluate is credited with revealing nothing — D-012's unobserved ≠ free)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..representations import RiskChannel


def _blocked(q: np.ndarray, targets: np.ndarray, centers: np.ndarray,
             radii: np.ndarray) -> np.ndarray:
    """(M, N) True where the q_i → target_j ray is occluded by some disc.

    Identical geometry to `GTBevProducer._occlusion` (segment-to-centre foot
    distance ≤ radius, and the target strictly beyond the disc), lifted to a
    many-observers batch. Keeping the two in sync is what lets the value map be
    read as "what the producer would render from there".
    """
    seg = targets[None, :, :] - q[:, None, :]                  # (M, N, 2)
    seg_len2 = np.maximum((seg * seg).sum(axis=2), 1e-12)      # (M, N)
    out = np.zeros(seg_len2.shape, dtype=bool)
    d_target = np.sqrt(seg_len2)
    for c, r in zip(centers, radii):
        to_c = c[None, None, :] - q[:, None, :]                # (M, 1, 2)
        u = np.clip((to_c * seg).sum(axis=2) / seg_len2, 0.0, 1.0)
        foot = q[:, None, :] + u[..., None] * seg
        hit = np.linalg.norm(foot - c, axis=2) <= r
        behind = d_target > np.linalg.norm(c[None, :] - q, axis=1)[:, None] + r
        out |= hit & behind
    return out


def observation_value_map(producer, bev, robot_xy: np.ndarray, t: float, *,
                          stride: int = 4, target_stride: int = 2):
    """Aggregate value-of-observation map over the rendered BEV window.

    Returns `(value, n_targets)` where `value` is an (n, n) float array aligned
    cell-for-cell with `bev.stack`, and `n_targets` the number of shadow cells
    the map was built against (0 ⇒ the map is identically zero and the term is
    silent *for a stated reason*).

    Targets are the cells that are **unseen while in sensing range** — i.e. the
    occlusion shadows, not the beyond-range halo. Crediting the halo would make
    the field a proxy for "drive forward", which the path term already owns.

    Cost model: `stride` subsamples observation locations, `target_stride` the
    targets; the coarse map is nearest-neighbour upsampled. At the shipped
    64×64 / stride 4 / target_stride 2 that is 256 observers × ~120 targets ×
    n_obstacles segment tests per control step — milliseconds, no simulation.
    """
    grid = bev.stack[RiskChannel.EPISTEMIC]
    n = grid.shape[0]
    res = bev.resolution
    ax = bev.origin[0] + (np.arange(n) + 0.5) * res
    ay = bev.origin[1] + (np.arange(n) + 0.5) * res
    cx, cy = np.meshgrid(ax, ay)                               # (n, n)

    robot_xy = np.asarray(robot_xy, dtype=float)
    d_robot = np.hypot(cx - robot_xy[0], cy - robot_xy[1])
    shadow = (grid > 0.5) & (d_robot <= producer.r_sense)

    tgt = shadow[::target_stride, ::target_stride]
    targets = np.stack([cx[::target_stride, ::target_stride][tgt],
                        cy[::target_stride, ::target_stride][tgt]], axis=1)
    if len(targets) == 0:
        return np.zeros((n, n)), 0

    qx = cx[::stride, ::stride]
    qy = cy[::stride, ::stride]
    q = np.stack([qx.ravel(), qy.ravel()], axis=1)             # (M, 2)

    centers = np.array([(ob.position(t) if len(ob.schedule)
                         else np.array([ob.x, ob.y]))
                        for ob in producer.obstacles], dtype=float)
    radii = np.array([ob.radius for ob in producer.obstacles], dtype=float)

    in_range = (np.linalg.norm(targets[None] - q[:, None], axis=2)
                <= producer.r_sense)                           # (M, N)
    visible = in_range
    if len(centers):
        visible = visible & ~_blocked(q, targets, centers, radii)

    coarse = visible.mean(axis=1).reshape(qx.shape)
    value = np.repeat(np.repeat(coarse, stride, axis=0), stride, axis=1)
    return value[:n, :n], len(targets)


@dataclass
class ObservationValueCritic:
    w_voo: float = 0.0      # additive cost per unit *missed* observation value
    stride: int = 4
    target_stride: int = 2

    def cost(self, producer, bev, robot_xy: np.ndarray, t: float,
             xy_flat: np.ndarray, K: int) -> np.ndarray:
        """(K,) additive per-rollout missed-observation-value cost.

        `xy_flat` is the (K·H, 2) stack of rollout world points (row-major over
        rollouts then horizon), `K` the rollout count — same convention as
        `ShadowCostCritic.cost`, so the two are drop-in comparable in an A/B.
        """
        if self.w_voo == 0.0 or bev is None:
            return np.zeros(K)
        value, n_targets = observation_value_map(
            producer, bev, robot_xy, t,
            stride=self.stride, target_stride=self.target_stride)
        if n_targets == 0:
            return np.zeros(K)

        idx = np.floor((xy_flat - bev.origin) / bev.resolution).astype(int)
        n = value.shape[0]
        inside = ((idx[:, 0] >= 0) & (idx[:, 0] < n)
                  & (idx[:, 1] >= 0) & (idx[:, 1] < n))
        v = np.zeros(len(xy_flat))          # out-of-grid reveals nothing
        v[inside] = value[idx[inside, 1], idx[inside, 0]]
        return self.w_voo * (1.0 - v).reshape(K, -1).sum(axis=1)
