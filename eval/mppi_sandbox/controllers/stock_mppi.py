# SPDX-License-Identifier: BSD-3-Clause
"""Pure-NumPy vanilla MPPI (Williams et al. 2017 information-theoretic form).

Sandbox baseline controller — the reference every representation-aware
variant is measured against. Deterministic: all sampling flows through a
seeded numpy Generator, so identical (scenario, seed) → identical run.

Cost = path-tracking (perpendicular distance^2 to reference polyline)
     + speed tracking (ramped down near goal so the robot stops)
     + obstacle soft barrier + hard collision penalty
     + terminal goal distance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..critics import ProgressPriceCritic
from ..dynamics import Limits, step
from ..gap_gate import gate_factor, two_sided_mu


@dataclass
class MPPIParams:
    horizon: int = 30
    samples: int = 256
    dt: float = 0.1
    lam: float = 0.1                       # softmax temperature
    sigma_v: float = 0.15
    sigma_w: float = 0.5
    w_path: float = 20.0
    w_speed: float = 2.0
    w_obs_soft: float = 10.0
    obs_soft_scale: float = 0.3            # [m] barrier decay length
    obs_barrier_band: float = 0.0          # [m] >0 ⇒ compact-support barrier (D-427)
    w_collision: float = 1.0e4
    collision_margin: float = 0.0          # [m] clearance at which w_collision fires
    w_terminal: float = 30.0
    w_omega: float = 0.5                   # rotation effort — no free pirouettes
    w_heading: float = 0.0                  # heading error vs path tangent (D-440)
    goal_slowdown_gain: float = 0.8        # v_ref = min(v*, gain·dist_to_goal)
    creep_speed: float = 0.08              # floor so the robot finishes the path


def _polyline_distance(pts: np.ndarray, path_xy: np.ndarray) -> np.ndarray:
    """Min perpendicular distance from each point (N,2) to polyline (M,2)."""
    a, b = path_xy[:-1], path_xy[1:]                     # (S,2)
    d = b - a
    len2 = np.maximum((d * d).sum(axis=1), 1e-12)        # (S,)
    ap = pts[:, None, :] - a[None]                       # (N,S,2)
    t = np.clip((ap * d[None]).sum(axis=2) / len2, 0.0, 1.0)
    proj = a[None] + t[..., None] * d[None]              # (N,S,2)
    return np.linalg.norm(pts[:, None, :] - proj, axis=2).min(axis=1)


def _polyline_tangent_yaw(pts: np.ndarray, path_xy: np.ndarray) -> np.ndarray:
    """Yaw [rad] of the polyline segment nearest each point (N,2) -> (N,).

    Same projection as `_polyline_distance`, but keeps the argmin segment
    instead of the distance. Deliberately a separate pass rather than a second
    return value on `_polyline_distance`: that function is on the hot path for
    every rollout of every arm, and `w_heading = 0` (the shipped default) must
    not pay for a quantity it does not use.

    The reference is the *segment direction*, matching
    `eval.path_tracking_metrics.heading_error` verbatim — the metric this term
    is meant to be able to move. Scenarios also carry a per-waypoint
    `yaw_target`, but that is a control directive and is not what the metric
    scores, so pricing it here would leave the residual unpriced all over again.
    """
    a, b = path_xy[:-1], path_xy[1:]                     # (S,2)
    d = b - a
    len2 = np.maximum((d * d).sum(axis=1), 1e-12)        # (S,)
    ap = pts[:, None, :] - a[None]                       # (N,S,2)
    t = np.clip((ap * d[None]).sum(axis=2) / len2, 0.0, 1.0)
    proj = a[None] + t[..., None] * d[None]              # (N,S,2)
    seg = np.linalg.norm(pts[:, None, :] - proj, axis=2).argmin(axis=1)  # (N,)
    return np.arctan2(d[seg, 1], d[seg, 0])


def _wrap_pi(x: np.ndarray) -> np.ndarray:
    """Wrap angles to [-pi, pi]."""
    return (x + np.pi) % (2.0 * np.pi) - np.pi


class StockMPPI:
    def __init__(self, scenario, seed: int = 0,
                 params: MPPIParams | None = None,
                 limits: Limits | None = None,
                 robot_radius: float = 0.3,
                 gap_gate_strength: float = 0.0,
                 w_freeze: float = 0.0):
        self.p = params or MPPIParams()
        # Freeze price (D-243). Lives on the baseline rather than on RiskMPPI
        # because the freeze it prices is not a representation effect — the
        # metric measured it on every arm — and because a term only some arms
        # can carry cannot be ablated against the others. w_freeze = 0 is the
        # shipped default and returns exactly zero, so this is byte-identical
        # to every run recorded before the term existed.
        self.progress = ProgressPriceCritic(w_freeze)
        # Two-sided-gap gate on the soft barrier (see ..gap_gate). 0 = off, and
        # `_cost` then takes the legacy branch untouched, so the default is
        # byte-identical to every run recorded before the gate existed.
        self.gap_gate_strength = float(gap_gate_strength)
        self.limits = limits or Limits()
        self.rng = np.random.default_rng(seed)
        self.path_xy = scenario.waypoints[:, :2]
        self.goal_xy = scenario.goal[:2]
        self.target_speed = scenario.target_speed
        self.obstacles = scenario.obstacles
        self.robot_radius = robot_radius
        self.U = np.zeros((self.p.horizon, 2))           # warm-started plan
        self.U[:, 0] = scenario.target_speed
        # Per-step effective sample size of the softmax, 1/sum(w^2). Recorded
        # here rather than reconstructed by the caller because a reconstruction
        # re-derives `exp(-(cost-min)/lam)` and would keep agreeing with a
        # controller that had stopped weighting that way. See `ab.median_ess`.
        self.ess_log: list[float] = []

    def command(self, state: np.ndarray, t: float) -> np.ndarray:
        p, lim = self.p, self.limits
        # Recorded for the freeze price, which charges the first rollout step
        # against where the robot actually is (see ProgressPriceCritic.cost).
        self._start_xy = np.asarray(state[:2], dtype=float)
        noise = self.rng.normal(
            0.0, [p.sigma_v, p.sigma_w], size=(p.samples, p.horizon, 2))
        controls = self.U[None] + noise                  # (K,H,2)
        controls[..., 0] = np.clip(controls[..., 0], lim.v_min, lim.v_max)
        controls[..., 1] = np.clip(controls[..., 1], -lim.omega_max, lim.omega_max)

        # rollout: (K,5) advanced H steps with the shared plant model
        states = np.broadcast_to(state, (p.samples, 5)).copy()
        traj = np.empty((p.samples, p.horizon, 5))
        for h in range(p.horizon):
            states = step(states, controls[:, h], p.dt, lim)
            traj[:, h] = states

        cost = self._cost(traj, t)
        beta = cost.min()
        w = np.exp(-(cost - beta) / self._softmax_lam(cost))
        w /= w.sum()
        self.ess_log.append(float(1.0 / np.square(w).sum()))

        self.U = self.U + np.einsum("k,khu->hu", w, noise)
        self.U[:, 0] = np.clip(self.U[:, 0], lim.v_min, lim.v_max)
        self.U[:, 1] = np.clip(self.U[:, 1], -lim.omega_max, lim.omega_max)

        u0 = self.U[0].copy()
        self.U[:-1] = self.U[1:]                          # receding-horizon shift
        return u0

    def _softmax_lam(self, cost: np.ndarray) -> float:
        """Temperature this step's softmax weights at. Constant `p.lam` here.

        The hook exists so a controller that *solves* for the temperature
        (`controllers.essps_mppi`) can do so without restating the weighting
        line — one `exp(-(cost-min)/lam)` in the tree, one place for it to be
        wrong. Called after `_cost` and before normalization, so an override
        sees exactly the vector the weights are taken over.
        """
        return self.p.lam

    def _soft_barrier(self, clear: np.ndarray) -> np.ndarray:
        """Per-point soft-barrier cost. Shape-preserving, so both `_cost`
        branches call it and neither reorders its accumulation.

        Default (`obs_barrier_band = 0`) is the legacy global exponential
        `exp(-clear / obs_soft_scale)`, which is **positive at every
        clearance** — at the 0.30 m gate it still returns `e^-1 = 0.37` and it
        never reaches zero. That is the mechanism D-426 priced: the term goes
        on paying to retreat long after the acceptance check is satisfied, so
        clearance is bought by pushing the whole trajectory off the path and
        `cte_*` fails in `min_distance_to_obstacle`'s place.

        With a band > 0 the barrier instead has **compact support** — a
        quadratic hinge, steep inside `[0, band]` and *exactly* zero above it.
        This is barrier **shape**, not barrier **position**: `collision_margin`
        translates the whole cliff (D-410), which is why it traded 1:1; this
        leaves the far field completely unpriced and so has nothing to pay
        tracking error with.

        The two forms agree at `clear = 0` (both return 1.0), so `w_obs_soft`
        keeps its calibrated meaning across the switch instead of silently
        becoming a different weight.
        """
        p = self.p
        if p.obs_barrier_band <= 0.0:
            return np.exp(-clear / p.obs_soft_scale)
        return np.maximum(0.0, (p.obs_barrier_band - clear)
                          / p.obs_barrier_band) ** 2

    def _cost(self, traj: np.ndarray, t0: float) -> np.ndarray:
        p = self.p
        K, H, _ = traj.shape
        xy = traj[..., :2].reshape(K * H, 2)

        d_path = _polyline_distance(xy, self.path_xy).reshape(K, H)
        cost = p.w_path * (d_path ** 2).sum(axis=1)

        dist_goal = np.linalg.norm(traj[..., :2] - self.goal_xy, axis=2)  # (K,H)
        v_ref = np.minimum(self.target_speed,
                           np.maximum(p.goal_slowdown_gain * dist_goal,
                                      p.creep_speed))
        cost += p.w_speed * ((traj[..., 3] - v_ref) ** 2).sum(axis=1)
        cost += p.w_omega * (traj[..., 4] ** 2).sum(axis=1)

        # Heading error against the path tangent (D-440). Zero by default, and
        # the branch is skipped entirely at w_heading = 0, so every run recorded
        # before this term existed is byte-identical.
        #
        # Why this term did not exist until now: `heading_err_rms` has been an
        # acceptance threshold since P5 scoping, but nothing in this cost read
        # `traj[..., 2]` at all. `w_omega` prices the rotation *rate* and
        # `w_path` prices the *lateral offset*; neither is the angle the metric
        # scores. The two sweeps that failed to move the residual (D-430
        # `w_speed`, D-433 `w_omega`) were therefore both sweeping knobs that
        # do not point at it — which is exactly why both merely reshuffled.
        if p.w_heading > 0.0:
            seg_yaw = _polyline_tangent_yaw(xy, self.path_xy).reshape(K, H)
            e_theta = _wrap_pi(traj[..., 2] - seg_yaw)
            cost += p.w_heading * (e_theta ** 2).sum(axis=1)

        if self.obstacles:
            times = t0 + p.dt * np.arange(1, H + 1)
            margin = self._extra_margin(xy, t0).reshape(K, H)
            if self.gap_gate_strength <= 0.0:
                for ob in self.obstacles:
                    pos = ob.position(times)                          # (H,2)
                    clear = (np.linalg.norm(traj[..., :2] - pos[None], axis=2)
                             - ob.radius - self.robot_radius - margin)  # (K,H)
                    cost += p.w_obs_soft * self._soft_barrier(clear).sum(axis=1)
                    cost += p.w_collision * (clear < p.collision_margin).any(axis=1)
            else:
                # Gated branch. Same two terms and the same accumulation order
                # (over H, then over obstacles), but the soft barrier is scaled
                # per rollout *point* by the two-sided-gap factor, which is a
                # property of the configuration and so cannot be computed
                # inside a per-obstacle loop.
                clears, deltas = [], []
                for ob in self.obstacles:
                    pos = ob.position(times)                          # (H,2)
                    delta = pos[None] - traj[..., :2]                 # (K,H,2)
                    clears.append(np.linalg.norm(delta, axis=2)
                                  - ob.radius - self.robot_radius - margin)
                    deltas.append(delta)
                clear = np.stack(clears, axis=-1)                     # (K,H,N)
                delta = np.stack(deltas, axis=-2)                     # (K,H,N,2)
                gate = gate_factor(two_sided_mu(delta, clear),
                                   self.gap_gate_strength)            # (K,H)
                cost += (gate[..., None] * p.w_obs_soft
                         * self._soft_barrier(clear)).sum(axis=(1, 2))
                # Hard term is *not* gated — that is the whole safety argument
                # for the soft one being gateable at all.
                cost += p.w_collision * (clear < p.collision_margin).any(axis=1).sum(axis=1)

        cost += p.w_terminal * dist_goal[:, -1] ** 2
        cost += self.progress.cost(traj, self.path_xy, p.dt,
                                   getattr(self, "_start_xy", None))
        return cost + self._extra_cost(traj, t0)

    # -------- representation hooks (no-ops in the baseline; see risk_mppi)

    def _extra_margin(self, xy_flat: np.ndarray, t0: float) -> np.ndarray:
        """(K·H,) additional clearance shrink per rollout point (D-013)."""
        return np.zeros(len(xy_flat))

    def _extra_cost(self, traj: np.ndarray, t0: float) -> np.ndarray:
        """(K,) additional cost per rollout (e.g., BEV risk consumption)."""
        return np.zeros(traj.shape[0])
