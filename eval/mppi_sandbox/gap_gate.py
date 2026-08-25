# SPDX-License-Identifier: BSD-3-Clause
"""Two-sided-gap gate on the obstacle soft barrier (MorphoCopter-MPC borrow).

The sandbox's soft barrier is a per-obstacle, **summed, monotone** repulsive
exponential (`stock_mppi._cost`)::

    cost += w_obs_soft * exp(-clear / obs_soft_scale).sum(axis=1)

Summed over two *flanking* obstacles, that barrier is **maximal exactly on the
line the robot has to drive down** — the narrow passage is where the cost peaks,
so the penalty's monotonicity is itself the defect. MorphoCopter-MPC
(arXiv:2605.15999, Modi/Liang/Zheng) names this and multiplies the exponential
by one extra scalar::

    Jo = Wo · (1 − (μ² − 1)²) · exp(1 − d⋆²/d₀²)

with **μ the cost-reduction factor, 0 at a passage centreline and 1 for a
single-sided obstacle**. The gate is `1 − (0−1)² = 0` inside a two-sided gap
(barrier off) and `1 − 0 = 1` against a lone obstacle (barrier unmodified).
Same exponential family the sandbox already runs, so the borrow is a factor and
not a cost-function rewrite.

Two things here are deliberately **not** the paper's:

1. **μ is closed-form, not estimated.** The paper recovers μ from DBSCAN-
   clustered LiDAR line segments (its Algorithm 2). The sandbox's obstacles are
   analytic circles with known centres, so the opposite-side test is a dot
   product and the whole gate is cheaper than the pipeline it replaces. It is
   therefore a μ *by analogy*, not a port — see `two_sided_mu`.

2. **μ carries a distance-imbalance term the paper's does not need.** A pure
   opposite-sidedness test reads μ = 0 whenever two obstacles straddle the
   robot — *including* when the robot is pressed against one of them and the
   second is far away on the other side. That configuration would switch the
   soft barrier fully off next to a wall the robot is about to hit, leaving
   only the hard `w_collision · (clear < 0)` term to hold the scene's declared
   margin. So μ is `max(alignment, imbalance)`: **zero only at a genuine
   centreline — opposed *and* equidistant** — and restoring the barrier as the
   robot drifts toward either side. This is the one direction the gate may not
   err in, and it is pinned in `tests/test_gap_gate.py`.

The gate multiplies the **soft** barrier only. The hard collision term is
untouched by construction (it is not a function of μ anywhere in this module),
because the soft term is what mis-shapes the corridor and the hard term is what
holds the margin.
"""

from __future__ import annotations

import numpy as np

#: Below this total clearance the imbalance ratio is numerically meaningless
#: (both obstacles are touching the robot); the alignment term carries μ alone.
_EPS = 1e-9


def two_sided_mu(delta: np.ndarray, clear: np.ndarray) -> np.ndarray:
    """Cost-reduction factor μ ∈ [0,1] per rollout point.

    `delta` is (..., N, 2) robot→obstacle-centre vectors and `clear` is
    (..., N) surface clearances, for the same N obstacles in the same order.
    Returns (...,) with **0 at a passage centreline** and **1 for a single-
    sided obstacle**, matching the paper's convention.

    μ is taken over the **two nearest** obstacles, which is what makes it a
    property of the *passage* rather than of the obstacle list: a third wall
    ten metres away is not part of the gap the robot is threading.

    μ = max(alignment, imbalance), where

    * ``alignment = (û₁·û₂ + 1) / 2`` — 0 iff the two nearest obstacles are
      exactly opposed (robot between them), 1 iff they lie in the same
      direction (robot outside them, i.e. effectively one-sided).
    * ``imbalance = |c₁ − c₂| / (c₁ + c₂)`` — 0 iff the robot is equidistant
      from both, → 1 as it closes on one of them.

    Taking the **max** means the barrier is disabled only where *both* read
    zero. With a single obstacle (N = 1) there is no pair, so μ ≡ 1 and the
    barrier passes through unmodified.
    """
    delta = np.asarray(delta, dtype=float)
    clear = np.asarray(clear, dtype=float)
    n_obs = clear.shape[-1]
    if n_obs < 2:
        return np.ones(clear.shape[:-1])

    # Two nearest by clearance. argpartition would do, but N is small and a
    # full argsort keeps the tie order deterministic across numpy versions.
    order = np.argsort(clear, axis=-1)[..., :2]                  # (...,2)
    c = np.take_along_axis(clear, order, axis=-1)                # (...,2)
    d = np.take_along_axis(delta, order[..., None], axis=-2)     # (...,2,2)

    norm = np.maximum(np.linalg.norm(d, axis=-1), _EPS)          # (...,2)
    u = d / norm[..., None]
    cos = np.clip((u[..., 0, :] * u[..., 1, :]).sum(axis=-1), -1.0, 1.0)
    alignment = 0.5 * (cos + 1.0)

    # Clip at zero: once a surface is breached its signed clearance is negative
    # and the ratio stops meaning "how far off-centre am I". The hard collision
    # term owns that regime.
    c_pos = np.maximum(c, 0.0)
    total = c_pos.sum(axis=-1)
    imbalance = np.where(
        total > _EPS,
        np.abs(c_pos[..., 0] - c_pos[..., 1]) / np.maximum(total, _EPS),
        0.0,
    )
    return np.clip(np.maximum(alignment, imbalance), 0.0, 1.0)


def gate_factor(mu: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Multiplicative factor on the soft barrier: ``1 − s·(μ² − 1)²``.

    `strength` s blends between the unmodified barrier and the paper's gate,
    and is the ablation knob:

    * ``s = 0`` → factor ≡ 1 for every μ, i.e. **byte-identical to
      `stock_mppi`** (the invariant every representation hook in this sandbox
      carries — cf. `RiskMPPI`'s `w_epist = 0`).
    * ``s = 1`` → the paper's `1 − (μ² − 1)²`: 0 at μ = 0, 1 at μ = 1.

    Monotone non-decreasing in μ on [0,1] and bounded to [1−s, 1], so it can
    only ever *reduce* the barrier — the gate cannot manufacture repulsion.
    """
    mu = np.clip(np.asarray(mu, dtype=float), 0.0, 1.0)
    return 1.0 - float(strength) * np.square(np.square(mu) - 1.0)
