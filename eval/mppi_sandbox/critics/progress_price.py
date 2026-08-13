# SPDX-License-Identifier: BSD-3-Clause
"""`ProgressPriceCritic` — the freeze, priced into the planner.

D-241 shipped `freeze_price.freeze_duration` and deliberately stopped there:
*"It does not price the freeze into any planner — that is the mechanism-grade
successor, and D-021's lesson (do not ship an unmeasured cost term) is the
reason it does not land in the same cycle as its own metric."* The metric then
measured, on `cafe_freezing_v0` at 3 seeds, that the freeze is real and that the
risk channel is what buys it: `stock_mppi` 0/3 runs exceed the scene's 2.0 s
limit, `risk_mppi` 2/3, `social_mppi` 2/3 — with **9/9 reaching the goal**, so
every completion-based freeze proxy in the tree is blind to all of it.

This is that successor, and its one design commitment is that **the cost term
and the acceptance key measure the same quantity**. `freeze_duration` grades the
longest contiguous interval whose *along-path* speed falls below
:data:`freeze_price.STALL_SPEED_MPS`; this critic charges each rollout for the
along-path progress it fails to make against that same threshold, importing the
constant rather than respelling it. A future change to the metric's notion of
"stalled" moves the price with it; `test_progress_price.py` pins the two
together so they cannot silently decouple, the same way
`test_freeze_duration.py` pins the threshold to `StockMPPI.creep_speed`.

Why along-path and not ground speed
-----------------------------------
`MPPIParams.w_speed` already penalises `(v - v_ref)²` with `v_ref` floored at
`creep_speed`, and it does not prevent the freeze — because it prices **ground**
speed. A robot arcing around a pedestrian, or pirouetting in place, carries
ground speed and makes no progress, and pays nothing. The yaml comment says
*"stopped without progress"*, not *"stopped"*. Charging arclength progress is
what makes the term non-redundant with the speed cost that is already there.

Shape of the charge
-------------------
Per rollout `k`, per step `h`::

    deficit = max(0, stall_speed·dt - Δs[k,h])
    cost[k] = w_freeze · Σ_h deficit²

`Δs` is the increase in projected arclength along the reference polyline. The
hinge is one-sided by construction: a rollout that makes progress at or above
the stall threshold pays exactly zero, so the term is silent on every healthy
trajectory and cannot bias the speed profile of a run that was never freezing.
It is quadratic in the deficit for the same reason `w_path` is quadratic — a
rollout that is fully stopped should be more than twice as expensive as one at
half the threshold.

Backing up is charged as heavily as its deficit implies (`Δs < 0` ⇒ deficit
> `stall_speed·dt`) and deliberately not clipped: reversing along the path is
worse than standing still, and the metric that grades this scene would score
both as stalled.

`w_freeze = 0.0` is the default everywhere, and at 0 the critic returns zeros
without projecting — so every arm's shipped behaviour is byte-identical to the
run recorded before this term existed, matching the ablation invariant every
other critic in this package holds.
"""

from __future__ import annotations

import numpy as np

from ..freeze_price import STALL_SPEED_MPS


def arclength_along(pts: np.ndarray, path_xy: np.ndarray) -> np.ndarray:
    """Projected arclength [m] of each point `(N,2)` along polyline `(M,2)`.

    The vectorised counterpart of `path_tracking_metrics.completion_percent`,
    which loops in Python over trajectory rows — fine for a `(T,6)` run record,
    unusable for the `K·H` rollout points priced every control step.

    Each point projects onto the *nearest* segment; its arclength is that
    segment's cumulative start plus the clamped along-segment offset. Identical
    construction to `stock_mppi._polyline_distance`, which already computes the
    projection and then throws the arclength away.
    """
    pts = np.asarray(pts, dtype=float)
    a, b = path_xy[:-1], path_xy[1:]                      # (S,2)
    d = b - a
    seg_len = np.linalg.norm(d, axis=1)                   # (S,)
    len2 = np.maximum(seg_len ** 2, 1e-12)
    cum = np.concatenate(([0.0], np.cumsum(seg_len)))     # (S+1,)

    ap = pts[:, None, :] - a[None]                        # (N,S,2)
    t = np.clip((ap * d[None]).sum(axis=2) / len2, 0.0, 1.0)   # (N,S)
    proj = a[None] + t[..., None] * d[None]               # (N,S,2)
    nearest = np.linalg.norm(pts[:, None, :] - proj, axis=2).argmin(axis=1)

    idx = np.arange(len(pts))
    return cum[nearest] + t[idx, nearest] * seg_len[nearest]


class ProgressPriceCritic:
    """Charges rollouts for along-path progress they fail to make.

    Parameters
    ----------
    w_freeze:
        Weight on the summed squared progress deficit. `0.0` (the default)
        disables the term entirely — no projection is computed and the returned
        cost is exactly zero, preserving the ablation invariant.
    stall_speed:
        Along-path speed [m/s] at or above which a step is free. Defaults to
        the metric's own threshold, :data:`freeze_price.STALL_SPEED_MPS`.
    """

    def __init__(self, w_freeze: float = 0.0,
                 stall_speed: float = STALL_SPEED_MPS):
        self.w_freeze = float(w_freeze)
        self.stall_speed = float(stall_speed)

    def cost(self, traj: np.ndarray, path_xy: np.ndarray, dt: float,
             start_xy: np.ndarray | None = None) -> np.ndarray:
        """`(K,)` freeze price for rollouts `traj` of shape `(K,H,>=2)`.

        `start_xy` is the robot's current position. When given, the first
        rollout step is charged against it, so a plan that stops immediately
        pays from step 0 rather than from step 1 — without it the term is blind
        to exactly the decision it exists to price.
        """
        K = traj.shape[0]
        if self.w_freeze == 0.0:
            return np.zeros(K)

        xy = np.asarray(traj[..., :2], dtype=float)        # (K,H,2)
        H = xy.shape[1]
        s = arclength_along(xy.reshape(K * H, 2), path_xy).reshape(K, H)
        if start_xy is not None:
            s0 = arclength_along(np.asarray(start_xy, dtype=float).reshape(1, 2),
                                 path_xy)
            s = np.concatenate([np.broadcast_to(s0, (K, 1)), s], axis=1)

        deficit = np.maximum(self.stall_speed * dt - np.diff(s, axis=1), 0.0)
        return self.w_freeze * (deficit ** 2).sum(axis=1)
