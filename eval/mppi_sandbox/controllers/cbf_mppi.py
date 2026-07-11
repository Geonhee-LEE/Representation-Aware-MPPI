# SPDX-License-Identifier: BSD-3-Clause
"""CBF-filtered MPPI — bardhh/cbfkit's safety-filter architecture in NumPy.

Pipeline (cbfkit: planner → nominal → safety controller, docs/cbfkit_analysis.md):

    nominal MPPI (stock_mppi or risk_mppi) → u_nom
    CBF-QP projection:  min ‖u − u_nom‖²  s.t.  ḣ_i(u) ≥ −α·h_i,  u ∈ box

Barrier per obstacle (moving, velocity feedforward): the unicycle's
relative-degree problem is solved with the standard offset point
p_l = p + l·[cosθ, sinθ] (cbfkit: `olfatisaber2002approximate` dynamics):

    h  = ‖p_l − p_o‖² − d_safe²
    ḣ  = 2 (p_l − p_o)·(J(θ) u − v_o),   J(θ) = [[c, −l·s], [s, l·c]]

J is full-rank for l > 0, so each barrier is one linear constraint in
u = (v, ω). The 2-variable QP is solved exactly by active-set enumeration
(unconstrained / one active / pairs) — no external solver.

v0 caveats (documented in docs/cbfkit_analysis.md): the plant is
accel-limited while the CBF assumes kinematic commands — absorbed by
`safety_margin`; an infeasible QP falls back to the minimum-violation
candidate (never crashes the control loop).
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

from ..dynamics import Limits
from .risk_mppi import RiskMPPI
from .stock_mppi import MPPIParams, StockMPPI


def solve_qp_2d(u_nom: np.ndarray, A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Exact min ‖u − u_nom‖² s.t. A u ≥ b for 2-D u via active-set enumeration.

    Returns the feasible minimizer, or the minimum-violation candidate if
    the constraint set is empty (CBF infeasibility under input bounds).
    """
    tol = 1e-9
    candidates = [u_nom]
    for i in range(len(A)):
        a = A[i]
        n2 = a @ a
        if n2 < tol:
            continue
        # projection onto the boundary a·u = b
        candidates.append(u_nom + (b[i] - a @ u_nom) / n2 * a)
    for i, j in combinations(range(len(A)), 2):
        M = np.stack([A[i], A[j]])
        if abs(np.linalg.det(M)) < tol:
            continue
        candidates.append(np.linalg.solve(M, np.array([b[i], b[j]])))

    best, best_cost = None, np.inf
    worst_violation = [np.inf, None]
    for u in candidates:
        violation = float(np.maximum(b - A @ u, 0.0).max(initial=0.0))
        if violation <= 1e-7:
            cost = float((u - u_nom) @ (u - u_nom))
            if cost < best_cost:
                best, best_cost = u, cost
        elif violation < worst_violation[0]:
            worst_violation = [violation, u]
    return best if best is not None else worst_violation[1]


class CBFMPPI(StockMPPI):
    """`nominal` selects the performance layer; the CBF-QP guards the floor."""

    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3,
                 nominal: str = "stock_mppi",
                 cbf_alpha: float = 1.0,
                 safety_margin: float = 0.25,
                 offset_l: float = 0.15,
                 dt: float = 0.1,
                 **nominal_kwargs):
        super().__init__(scenario, seed=seed, params=params, limits=limits,
                         robot_radius=robot_radius)
        if nominal == "stock_mppi":
            self.nominal = StockMPPI(scenario, seed=seed, params=params,
                                     limits=limits, robot_radius=robot_radius)
        elif nominal == "risk_mppi":
            self.nominal = RiskMPPI(scenario, seed=seed, params=params,
                                    limits=limits, robot_radius=robot_radius,
                                    **nominal_kwargs)
        else:
            raise KeyError(f"unknown nominal '{nominal}'")
        self.alpha = cbf_alpha
        self.margin = safety_margin
        self.l = offset_l
        self.dt = dt

    def command(self, state: np.ndarray, t: float) -> np.ndarray:
        u_nom = self.nominal.command(state, t)
        if not self.obstacles:
            return u_nom

        lim = self.limits
        x, y, th = state[0], state[1], state[2]
        c, s = np.cos(th), np.sin(th)
        p_l = np.array([x + self.l * c, y + self.l * s])
        J = np.array([[c, -self.l * s], [s, self.l * c]])

        # one-step *reachable* box (accel-limited plant clips commands the
        # same way) — makes command ≈ realized, closing the kinematic-CBF /
        # accel-limited-plant gap that otherwise lets h dip below 0
        v, w = state[3], state[4]
        v_lo = max(lim.v_min, v - lim.accel_max * self.dt)
        v_hi = min(lim.v_max, v + lim.accel_max * self.dt)
        w_lo = max(-lim.omega_max, w - lim.alpha_max * self.dt)
        w_hi = min(lim.omega_max, w + lim.alpha_max * self.dt)
        rows_a = [np.array([1.0, 0.0]), np.array([-1.0, 0.0]),
                  np.array([0.0, 1.0]), np.array([0.0, -1.0])]
        rows_b = [v_lo, -v_hi, w_lo, -w_hi]

        for ob in self.obstacles:
            p_o = ob.position(t)
            v_o = ob.velocity(t)
            d_safe = ob.radius + self.robot_radius + self.margin
            delta = p_l - p_o
            h = delta @ delta - d_safe ** 2
            # 2·Δᵀ J u ≥ −α h + 2·Δᵀ v_o
            rows_a.append(2.0 * delta @ J)
            rows_b.append(-self.alpha * h + 2.0 * delta @ v_o)

        return solve_qp_2d(u_nom, np.stack(rows_a), np.array(rows_b))
