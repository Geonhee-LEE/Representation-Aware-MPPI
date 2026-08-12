# SPDX-License-Identifier: BSD-3-Clause
"""PredictedGeometryCritic — speed-scaled anisotropic pedestrian cost.

A port of the cost term only from PGIF-MPPI (arxiv 2608.08323, Mundane,
Springer SPAR; no code released, reimplemented from the stated equation).
This is the branch's **third arm**, and the axis it adds is *time*:

    ShadowCostCritic        epistemic sigma at the rollout point  — neither
    GeometricMPPI           min-clearance to obstacles **now**    — static geometry
    PredictedGeometryCritic anisotropic field at predicted pose   — predicted geometry

D-166/geometric_null established the static-geometry null as the arm the
representation term has to beat. That null reads the obstacle set at the
*current* instant. A pedestrian walking across the path is not a disc at its
current position — it is a cone opening in the direction it is going — and
neither existing arm can express that, so a comparison between them cannot
say whether the epistemic channel is buying anything a *predicted* geometric
term would also buy. This critic is that term.

The form (paper's equation, all four constants as published)::

    C_ped(q) = sum_i exp(-0.5 * [(d_par / sigma_par)^2 + (d_perp / sigma_perp)^2])
    cost_k   = w_ped * sum_h C_ped(x_kh)

with `d_par` the signed along-heading offset from the pedestrian, `d_perp` the
lateral one, and the anisotropy carried entirely by three constants:

    sigma_par  = 1.2 + 0.5 * s_i   ahead of the pedestrian   (grows with speed)
    sigma_par  = 0.5 m             behind it
    sigma_perp = 0.6 m             laterally

So cutting in front is charged far more than passing behind, and the front
lobe stretches with the pedestrian's speed. No network, no dataset, no
training run — closed form, and parallel across rollouts.

Two conditions on how this arm is *graded*, both taken from the source paper's
own table and both non-negotiable here:

1. **Report the timeout rate beside the collision rate, always.** The paper's
   abstract headline is "0% collisions at all density levels"; its Table 1
   shows the Hard level converting an 82% collision rate into a **59% timeout
   rate** (18% -> 41% success). The method does not remove failures, it
   changes their type — the paper says so in its own words ("predicted
   anisotropic fields occupy a large portion of the workspace, leaving few low
   cost trajectories"). A collision-only reading would score a freezing robot
   as a solved problem, which is exactly the failure `dont-freeze-dont-crash`
   exists to name.
2. **Do not give the planner the simulator's own pedestrian motion model.**
   The paper predicts its orbital pedestrians with exact circular kinematics —
   the planner's motion model *is* the generator's, so prediction error is
   identically zero and the reported numbers are an upper bound no real
   tracker reproduces. Here the sandbox's pedestrians follow piecewise-linear
   waypoint schedules (`CircleObstacle.schedule`), and this critic deliberately
   does **not** read them: it takes one position and one velocity at `t0` and
   extrapolates **constant-velocity**. On a straight leg CV is exact; through a
   waypoint corner it is wrong, and it is supposed to be. `position(t0 + h*dt)`
   appears nowhere in this module, and `test_cv_prediction_ignores_the_schedule`
   pins that as a behavioural property rather than a reading convention.

Contract (mirrors D-013 / ShadowCostCritic so P5 ablation attribution holds):

- standalone — never overloads the baseline obstacle term
- add-only: cost >= 0
- `w_ped = 0.0` default -> exact no-op -> baseline reproduction (ablation invariant)
- **dynamic obstacles only**: an obstacle with an empty schedule is a wall or a
  fixture, not a pedestrian, and is already priced by the baseline obstacle
  term. Charging it here would double-count and break the standalone contract.
- a pedestrian at rest (speed < `STATIC_SPEED_EPS`) has no defined heading, so
  the anisotropy degenerates to an isotropic `sigma_perp` disc rather than to
  an arbitrary direction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SIGMA_PAR_BASE = 1.2      # m, ahead-lobe extent at zero speed
SIGMA_PAR_PER_SPEED = 0.5  # m per (m/s), ahead-lobe growth with pedestrian speed
SIGMA_PAR_BEHIND = 0.5    # m, behind-lobe extent (speed-independent)
SIGMA_PERP = 0.6          # m, lateral extent
STATIC_SPEED_EPS = 1e-3   # m/s below which heading is undefined


@dataclass
class PredictedGeometryCritic:
    w_ped: float = 0.0    # additive cost per unit field per rollout point — 0 = no-op

    def cost(self, obstacles, xy_flat: np.ndarray, K: int,
             t0: float, dt: float) -> np.ndarray:
        """(K,) additive anisotropic pedestrian cost.

        `xy_flat` is the (K*H, 2) stack of rollout world points (row-major over
        rollouts then horizon), `K` the rollout count. Rollout point `h` is
        taken to be at time `t0 + dt*(h+1)`, matching `StockMPPI`'s own
        `times = t0 + dt * arange(1, H + 1)`.
        """
        if self.w_ped == 0.0 or not obstacles:
            return np.zeros(K)
        peds = [ob for ob in obstacles if len(ob.schedule) > 0]
        if not peds:
            return np.zeros(K)

        xy = np.asarray(xy_flat, dtype=float).reshape(K, -1, 2)
        H = xy.shape[1]
        times = t0 + dt * np.arange(1, H + 1)          # (H,)

        field = np.zeros((K, H))
        for ob in peds:
            p0 = np.asarray(ob.position(t0), dtype=float).reshape(2)
            vel = np.asarray(ob.velocity(t0), dtype=float).reshape(2)
            speed = float(np.linalg.norm(vel))
            # constant-velocity extrapolation — deliberately NOT ob.position(t)
            pred = p0[None, :] + vel[None, :] * times[:, None]   # (H, 2)
            d = xy - pred[None, :, :]                            # (K, H, 2)

            if speed < STATIC_SPEED_EPS:
                r = np.linalg.norm(d, axis=-1)
                field += np.exp(-0.5 * (r / SIGMA_PERP) ** 2)
                continue

            heading = vel / speed
            d_par = d @ heading                                  # (K, H) signed
            d_perp = np.linalg.norm(d - d_par[..., None] * heading, axis=-1)
            sigma_par = np.where(d_par >= 0.0,
                                 SIGMA_PAR_BASE + SIGMA_PAR_PER_SPEED * speed,
                                 SIGMA_PAR_BEHIND)
            field += np.exp(-0.5 * ((d_par / sigma_par) ** 2
                                    + (d_perp / SIGMA_PERP) ** 2))

        return self.w_ped * field.sum(axis=1)
