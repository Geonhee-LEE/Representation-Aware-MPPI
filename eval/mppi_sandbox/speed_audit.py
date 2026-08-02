# SPDX-License-Identifier: BSD-3-Clause
"""Why the closed loop does not drive at `target_speed_mps` (Q-045 → D-024).

D-022 measured the crossing scene finishing in 9.2 s against a 16.7 s nominal
and attributed the gap to the controller "not tracking `target_speed_mps`"
(plan 0.36, realized 0.54 m/s). D-023 then had to declare a **timing band**
(0.557–2.038) over the reportable obstacle-carrying scenes because that gap is
what makes `nominal_traversal` wrong. Q-045 asked which of three things is the
defect:

    (a) the **scenario setting** — a speed nothing enforces
    (b) the **cost weights** — `w_terminal = 30.0` against `w_speed = 2.0`
    (c) the **absence of a speed-tracking term** in the shipped objective

Measured answers, in increasing order of how much they change:

* **(c) is false by inspection.** `StockMPPI._cost` has carried
  `w_speed * ((v - v_ref) ** 2).sum()` since the baseline landed. The term is
  not missing, and it is not inert either — see `test_speed_term_is_live`.
* **(b) is true and two-directional.** `w_terminal = 0` drops realized speed
  0.519 → 0.146 m/s; `w_speed = 60` drops it to 0.237. Both interventions
  reduce it, from opposite sides of the same ratio, which is what makes this a
  cause rather than a correlate (the D-018 discipline).
* **(a) is false, and this is the finding.** Sweeping `target_speed_mps` over
  **4×** (0.15 / 0.30 / 0.60) moves realized speed by **3 %**
  (0.508 / 0.519 / 0.523). The declared target enters the controller only
  through the warm start `U[:, 0]` and the `v_ref` cap, and neither survives
  the first few updates. So "a speed nothing enforces" is a true *description*
  and a useless *repair*: setting the declaration correctly changes nothing.

The consequence for D-022/D-023 is sharper than a correction. The **overshoot
ratio is an artifact of the declaration, not a property of the controller** —
at `target_speed_mps: 0.6` the identical controller on the identical scene
shows realized/target = **0.87**, i.e. *undershoot*. Quoting "the loop
overshoots by 1.8×" describes the number someone typed into a yaml file. The
band D-023 measured is real, but its cause is not a tracking failure to be
fixed; it is that `nominal_traversal` is driven by a **quantity the closed loop
does not read**.

What actually sets the cruise speed is `min(v_max, f(w_terminal / w_speed))`:
`v_max` binds below ~0.6 m/s (cruise/`v_max` = 1.00 at 0.6, 0.84 at 0.4) and
the weight ratio binds above it (cruise pins at ~0.71 for `v_max` of both 0.8
and 1.2). `target_speed_mps` appears in neither.

### The closed form that does NOT work

Treating the horizon as one constant-speed segment gives a stationary point

    Δ* = w_terminal · T · D / (w_speed · H + w_terminal · T²),   T = H · dt

with `D = d_goal - v_ref · T`. It is the obvious model, it has the right
qualitative content (the terminal term buys speed, the ratio is what matters),
and it is **quantitatively refuted** — see `test_analytic_stationary_point_is_refuted`.
Measured cruise runs *above* it near the goal (0.714 vs 0.462 at d = 1.5) and
*below* it far away at low `w_terminal` (0.215 vs 0.576 at d = 3.6), and the
sign of the error flips with `w_terminal`. The reason is the same one D-021
kept running into: at the shipped `lam = 0.1` the softmax median ESS on this
scene is **1.46 of K = 256**, so `U += Σ w_k · noise_k` is argmin-over-draws,
not a gradient step toward a stationary point. A closed form derived from
"MPPI optimises its cost" is not a description of a controller running at
ESS ≈ 1. It is kept here, refuted and pinned, so the next cycle does not
re-derive it and believe it.

### Why `mean_speed` is the wrong statistic

`ab.mean_speed` averages over three regimes that answer different questions:
the acceleration transient (`accel_max = 1.0` → ~0.7 s to reach cruise), the
cruise, and the goal-slowdown ramp (`v_ref = 0.8 · d_goal` inside ~0.9 m). A
run that stalls and a run that cruises then brakes can share a mean. Binning by
distance-to-goal does **not** fix it — on a single-pass path large `d_goal` *is*
early time, so a distance bin at the far end is mostly transient. That confound
is what made the analytic model look plausible for one value of `w_terminal`.
`cruise_speed` excludes both ends explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import ab
from .controllers.stock_mppi import MPPIParams
from .scenario import Scenario

# Regime cuts for `cruise_speed`. `T_TRANSIENT_S` clears the acceleration ramp
# (v_max / accel_max = 0.8 s at the defaults, rounded up); `D_RAMP_M` clears
# the goal slowdown, which begins at v_ref = goal_slowdown_gain * d_goal
# falling below target_speed, i.e. d_goal < target / 0.8 <= 1.0 m for every
# scene in the matrix.
T_TRANSIENT_S = 1.0
D_RAMP_M = 1.0

# Measured 2026-08-03 on cafe_obstacle_crossing_v0, seeds 0-3, shipped params.
# Realized mean speed against a 4x sweep of the declared target. The spread is
# the evidence for Q-045 (a) being a non-cause; asserted in the tests.
TARGET_SPEED_INERTNESS = {0.15: 0.508, 0.30: 0.519, 0.60: 0.523}


@dataclass(frozen=True)
class SpeedResponse:
    """Realized speed of one (scenario, weight) cell over a seed ensemble."""
    mean_speed: float
    cruise_speed: float
    median_ess: float
    n_reached: int
    n_seeds: int

    @property
    def all_reached(self) -> bool:
        return self.n_reached == self.n_seeds


def cruise_speed(traj: np.ndarray, scenario: Scenario, *,
                 t_transient: float = T_TRANSIENT_S,
                 d_ramp: float = D_RAMP_M) -> float:
    """Median speed with the accel transient and the goal ramp excluded.

    The statistic `mean_speed` should have been for every claim of the form
    "this arm drove faster" — see the module docstring for why the mean and the
    distance-binned mean are both confounded. Returns NaN if the run never
    leaves the excluded regimes (a stall), which is information, not an error:
    a stalled arm has no cruise speed and should not be credited with one.
    """
    t = traj[:, 0]
    d_goal = np.linalg.norm(traj[:, ab.COL_XY] - scenario.goal[:2], axis=1)
    live = (t >= t_transient) & (d_goal >= d_ramp)
    if live.sum() < 3:
        return float("nan")
    return float(np.median(traj[live, ab.COL_V]))


def speed_response(scenario: Scenario, controller: str = "stock_mppi",
                   seeds=range(4), *, params: MPPIParams | None = None,
                   v_max: float | None = None, **arm_kwargs) -> SpeedResponse:
    """Run a seed ensemble and report what speed it actually drove at."""
    kwargs = dict(arm_kwargs)
    if params is not None:
        kwargs["params"] = params
    runs = ab.seed_sweep(scenario, controller, seeds, v_max=v_max, **kwargs)
    return SpeedResponse(
        mean_speed=float(np.mean([r.mean_speed for r in runs])),
        cruise_speed=float(np.nanmedian(
            [cruise_speed(r.traj, scenario) for r in runs])),
        median_ess=float(np.median([r.median_ess for r in runs])),
        n_reached=int(sum(r.reached_goal for r in runs)),
        n_seeds=len(runs),
    )


def overshoot_ratio(response: SpeedResponse, scenario: Scenario) -> float:
    """Realized / declared — the quantity D-022 reported as ~1.8.

    Provided so the artifact is computable, **not** because it is a controller
    property. Its denominator is a yaml field the loop does not read, so it
    moves when nothing about the controller does. Any use of this number must
    quote the `target_speed_mps` it was taken against.
    """
    return response.mean_speed / max(float(scenario.target_speed), 1e-9)


def analytic_cruise_speed(d_goal: float, v_ref: float, *,
                          params: MPPIParams | None = None,
                          v_max: float = 0.8) -> float:
    """**REFUTED** one-segment stationary point. Do not use as a predictor.

    Minimises `w_speed·H·Δ² + w_terminal·(D − Δ·T)²` over a constant-speed
    horizon. Retained only so `test_analytic_stationary_point_is_refuted` can
    pin the disagreement — the shipped controller runs at ESS ≈ 1, where the
    update is argmin-over-draws rather than a step toward this optimum. See the
    module docstring.
    """
    p = params or MPPIParams()
    horizon_s = p.horizon * p.dt
    residual = max(d_goal - v_ref * horizon_s, 0.0)
    delta = (p.w_terminal * horizon_s * residual
             / (p.w_speed * p.horizon + p.w_terminal * horizon_s ** 2))
    return float(min(v_max, v_ref + delta))
