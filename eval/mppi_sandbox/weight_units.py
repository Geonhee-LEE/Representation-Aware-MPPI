# SPDX-License-Identifier: BSD-3-Clause
"""Q-049 — measure a cost weight in units of the cost it competes against.

D-027 shipped `ObservationValueCritic` and then found that the naive weight
(`w_voo = 200`, inherited from what `w_epist` happened to be set to) was
**6.19× the median per-step baseline cost spread** on the scene it was swept
on. At that weight the softmax collapses — median ESS 77.9 → 1.00, i.e.
argmin-over-draws — so `lam` is inert and the arm collides. The weight was not
a strong information preference; it was a **disguised temperature change**.

That measurement was scene- and term-specific, done by hand inside
`test_observation_value_critic`. Q-049 asks whether the hazard is repo-wide:
none of the shipped critic weights (`w_risk = 40`, `w_epist`,
`k_margin_per_sigma`, `w_terminal = 30`) has ever been stated relative to the
baseline it competes with. This module is the general instrument.

## Method — leave-one-out, by toggling the weight, not by re-deriving the cost

Every term in `StockMPPI._cost` / `RiskMPPI._extra_cost` is `w · f(traj)`, so
for a fixed rollout batch::

    cost(w) - cost(w := 0)  ==  w · f(traj)      exactly

Measuring the term by *zeroing its own weight and re-evaluating the real
`_cost`* therefore needs no second copy of the cost formula, and cannot drift
away from the controller the way a re-implementation would (the failure mode
`ab.median_ess`'s docstring names for ESS). The comparison denominator is the
**rest of the cost** — `cost - w·f` — not the total, so a term is never priced
against a baseline that already contains it. That makes the same statistic
well-defined for add-on critics *and* for terms living inside the baseline
(`w_terminal`), which a "share of total" statistic would not.

## Which statistic — say it before dividing by it

`REPORTING_STATISTIC = "median"`. The per-step spread distribution is heavily
right-skewed: `w_collision = 1e4` is an indicator, so any step whose rollout
cloud straddles a collision boundary contributes a spike two orders of
magnitude above the typical step. On `cafe_obstacle_crossing_v0` the total-cost
spread reads **median 79.09 vs mean 3806.8** — a 48× disagreement, and picking
silently is the D-024 mistake class (a screen driven by a quantity nobody
declared). Both are returned; the ratio properties use the median, and
`TermSpread.statistic_disagreement` exists so a caller can check whether the
choice was load-bearing on *their* scene rather than trusting this paragraph.

## The precondition the ratio has, and which shipped knob fails it

"`w` is `r×` the baseline spread" presumes `ptp(w·f)` is **linear in `w`** —
otherwise `r` is a function of the weight it is supposed to describe and says
nothing transferable. That holds for every additive coefficient. It does
**not** hold for `k_margin_per_sigma`, which is not a coefficient on a term at
all: it shrinks `clear` *inside* `exp(-clear/scale)` and inside the
`clear < 0` indicator, so `cost(k) - cost(0)` is not proportional to `k`.
`k_margin_per_sigma` is in **metres of clearance**, not in cost units, and
`measure()` refuses to report a ratio for it. See `unit_spread_is_linear`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .controllers import make_controller
from .controllers.stock_mppi import MPPIParams
from .run import ROBOT_RADIUS, simulate

#: Which of (median, mean) the `ratio_*` properties divide by. Named here
#: rather than chosen at the call site — see the module docstring.
REPORTING_STATISTIC = "median"

#: Additive cost coefficients, `name -> (owner-attribute-path)`. Zeroing one
#: removes exactly its own term from `_cost`, leaving every other term bitwise
#: unchanged. `w_path` is included even though nothing sweeps it: it is the
#: dominant baseline term, and a ratio is only interpretable next to it.
ADDITIVE_WEIGHTS: dict[str, str] = {
    "w_path": "p.w_path",
    "w_speed": "p.w_speed",
    "w_omega": "p.w_omega",
    "w_obs_soft": "p.w_obs_soft",
    "w_collision": "p.w_collision",
    "w_terminal": "p.w_terminal",
    "w_risk": "w_risk",
    "w_epist": "shadow.w_epist",
    "w_voo": "observation.w_voo",
}

#: Knobs that change the cost but are **not** coefficients on an additive term.
#: Their natural unit is not "multiples of the baseline cost spread" — see the
#: module docstring's precondition section.
NON_ADDITIVE_KNOBS: dict[str, str] = {
    "k_margin_per_sigma": "metres of clearance (shifts `clear` inside "
                          "exp(-clear/scale) and the collision indicator)",
}


def _get(ctrl, path: str):
    obj = ctrl
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


def _set(ctrl, path: str, value) -> None:
    parts = path.split(".")
    obj = ctrl
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


def _has(ctrl, path: str) -> bool:
    try:
        _get(ctrl, path)
    except AttributeError:
        return False
    return True


@dataclass(frozen=True)
class TermSpread:
    """One cost term's per-sample spread, at its shipped weight, vs the rest.

    `spread_*` is over `w·f(traj)` — what this term alone contributes to the
    per-sample cost range the softmax sees. `rest_*` is over `cost - w·f`,
    which is what it competes against. Both are aggregates over the control
    steps of one closed-loop run.
    """

    name: str
    weight: float
    n_steps: int
    spread_median: float
    spread_mean: float
    rest_median: float
    rest_mean: float

    @property
    def ratio(self) -> float:
        """Shipped weight's term spread as a multiple of the rest of the cost.

        `> 1` means this single term spans more of the per-sample cost range
        than everything else put together — the D-027 condition, under which
        the softmax is effectively deciding on this term alone and `lam` was
        calibrated for a landscape that no longer exists.
        """
        return float(self.spread_median / self.rest_median)

    @property
    def ratio_mean(self) -> float:
        """The same ratio under the statistic this module did *not* pick."""
        return float(self.spread_mean / self.rest_mean)

    @property
    def spread_per_unit_weight(self) -> float:
        """`ptp(f)` — the term's spread at weight 1, i.e. the exchange rate.

        This is the transferable number: multiply by a candidate weight to get
        its ratio without re-running. Only meaningful because the spread is
        linear in the weight (`unit_spread_is_linear`).
        """
        return float(self.spread_median / self.weight) if self.weight else 0.0

    @property
    def statistic_disagreement(self) -> float:
        """max/min of the two ratios — how load-bearing the median/mean pick is."""
        a, b = abs(self.ratio), abs(self.ratio_mean)
        lo, hi = min(a, b), max(a, b)
        return float(hi / lo) if lo > 0 else float("inf")

    def __str__(self) -> str:
        return (f"{self.name:<14} w={self.weight:<10.4g} "
                f"spread={self.spread_median:<10.4g} "
                f"rest={self.rest_median:<10.4g} ratio={self.ratio:.3g}")


def measure(scenario, controller: str = "risk_mppi", *, seed: int = 0,
            params: MPPIParams | None = None,
            robot_radius: float = ROBOT_RADIUS,
            **arm_kwargs) -> dict[str, TermSpread]:
    """Leave-one-out spread table for one (scenario, arm) over a full run.

    Terms whose weight is 0 on this arm are skipped — they contribute exactly
    nothing and their ratio would be 0/rest by construction, which is a fact
    about the arm, not a measurement. Knobs in `NON_ADDITIVE_KNOBS` are never
    reported; `measure` raises if one is non-zero, because their presence makes
    every *other* term's ratio conditional on a knob the table cannot show.
    """
    for knob, unit in NON_ADDITIVE_KNOBS.items():
        if float(arm_kwargs.get(knob, 0.0)) != 0.0:
            raise ValueError(
                f"{knob}={arm_kwargs[knob]} is not an additive cost "
                f"coefficient — its unit is {unit}, so it has no "
                f"baseline-spread ratio, and leaving it on makes every other "
                f"row conditional on it. Measure at {knob}=0.")

    ctrl = make_controller(controller, scenario, seed=seed,
                           robot_radius=robot_radius,
                           params=params or MPPIParams(), **arm_kwargs)
    live = {n: p for n, p in ADDITIVE_WEIGHTS.items()
            if _has(ctrl, p) and float(_get(ctrl, p)) != 0.0}
    weights = {n: float(_get(ctrl, p)) for n, p in live.items()}

    spreads: dict[str, list[float]] = {n: [] for n in live}
    rests: dict[str, list[float]] = {n: [] for n in live}
    inner = ctrl._cost

    def _record(traj, t0):
        full = inner(traj, t0)
        for name, path in live.items():
            w = weights[name]
            _set(ctrl, path, 0.0)
            try:
                without = inner(traj, t0)
            finally:
                _set(ctrl, path, w)
            spreads[name].append(float(np.ptp(full - without)))
            rests[name].append(float(np.ptp(without)))
        return full

    ctrl._cost = _record
    simulate(scenario, ctrl)

    return {
        name: TermSpread(
            name=name, weight=weights[name], n_steps=len(spreads[name]),
            spread_median=float(np.median(spreads[name])),
            spread_mean=float(np.mean(spreads[name])),
            rest_median=float(np.median(rests[name])),
            rest_mean=float(np.mean(rests[name])),
        )
        for name in live
    }


_KNOB_PATH = {"k_margin_per_sigma": "critic.k_margin_per_sigma"}


def batch_per_unit_spread(scenario, knob: str, weights, *, seed: int = 0,
                          params: MPPIParams | None = None,
                          **arm_kwargs) -> list[float]:
    """`ptp(cost(w) - cost(0)) / w` for one knob on a **fixed rollout batch**.

    The batch is held fixed on purpose. The ratio's precondition is a statement
    about the *cost algebra* — "is this knob a coefficient on a term?" — and
    that question is only well-posed at a fixed `traj`. Vary the weight in
    closed loop and the pose sequence moves too, so a non-constant result would
    confound the algebra with the steering (it does: see
    `closed_loop_per_unit_spread`, which is a different and also useful number).

    For an additive coefficient the returned values are equal to machine
    precision. For `k_margin_per_sigma` they are not, because it shifts `clear`
    inside `exp(-clear/scale)` and inside the `clear < 0` indicator — it has no
    weight-independent exchange rate, hence no baseline-spread ratio.
    """
    path = _KNOB_PATH.get(knob, ADDITIVE_WEIGHTS.get(knob))
    if path is None:
        raise KeyError(f"unknown knob {knob!r}")
    # One controller, one batch. The knob is then driven through `_set` rather
    # than through the constructor, so `w_terminal` (an `MPPIParams` field) and
    # `w_voo` (a critic attribute) take the identical code path, and the batch
    # is provably the same for every weight.
    ctrl = make_controller("risk_mppi", scenario, seed=seed,
                           robot_radius=ROBOT_RADIUS,
                           params=params or MPPIParams(),
                           **{**arm_kwargs, **_render_forcing(arm_kwargs)})
    traj, t0 = _first_batch(ctrl, scenario)
    out: list[float] = []
    for w in weights:
        _set(ctrl, path, float(w))
        full = ctrl._cost(traj, t0)
        _set(ctrl, path, 0.0)
        without = ctrl._cost(traj, t0)
        out.append(float(np.ptp(full - without)) / float(w) if w else 0.0)
    return out


def _render_forcing(arm_kwargs: dict) -> dict:
    """Make `RiskMPPI.command` render the BEV even on an all-zero arm.

    `command` skips the render when every consumption weight is 0, which would
    leave `_bev = None` and silently zero every epistemic term under test. A
    tiny `w_risk` is enough to flip `active`; it is then overwritten by `_set`
    before any measurement, so it never enters a reported number.
    """
    return {} if any(float(arm_kwargs.get(k, 0.0)) != 0.0
                     for k in ("w_risk", "w_epist", "w_voo",
                               "k_margin_per_sigma")) else {"w_risk": 1.0}


def _first_batch(ctrl, scenario):
    """One rollout batch from the scenario start pose, with the BEV rendered.

    Uses the controller's own `command` to populate `_bev` / `_robot_xy`, then
    re-rolls the same batch, so the cost sees exactly what the controller saw.
    """
    state = np.zeros(5)
    state[:3] = scenario.start[:3]
    ctrl.command(state, 0.0)
    p, lim = ctrl.p, ctrl.limits
    rng = np.random.default_rng(0)
    controls = np.clip(rng.normal(0.0, [p.sigma_v, p.sigma_w],
                                  size=(p.samples, p.horizon, 2)), -1e3, 1e3)
    controls[..., 0] = np.clip(controls[..., 0] + scenario.target_speed,
                               lim.v_min, lim.v_max)
    controls[..., 1] = np.clip(controls[..., 1], -lim.omega_max, lim.omega_max)
    from .dynamics import step
    states = np.broadcast_to(state, (p.samples, 5)).copy()
    traj = np.empty((p.samples, p.horizon, 5))
    for h in range(p.horizon):
        states = step(states, controls[:, h], p.dt, lim)
        traj[:, h] = states
    return traj, 0.0


def shadow_batch(ctrl, *, K: int = 64, H: int = 30) -> np.ndarray:
    """A rollout batch placed **inside the epistemic shadow**, for margin tests.

    `RiskInflationCritic` and `ShadowCostCritic` both read σ *at the rollout
    point*, and D-021 established that on `cafe_obstacle_crossing_v0` the real
    rollout cloud never reaches a σ > 0 cell at the shipped horizon. So a
    closed-loop measurement of `k_margin_per_sigma` reads exactly 0 — true, but
    it measures the scene, not the knob. This synthesises the batch the knob
    *would* need in order to be live, so its cost algebra can be examined
    independently of whether any scene currently exercises it.

    Requires `ctrl._bev` to be populated (call `ctrl.command` first).
    """
    from .representations import RiskChannel
    bev = ctrl._bev
    if bev is None:
        raise ValueError("controller has no BEV — call ctrl.command(...) first")
    grid = bev.stack[RiskChannel.EPISTEMIC]
    n = grid.shape[0]
    ax = bev.origin[0] + (np.arange(n) + 0.5) * bev.resolution
    ay = bev.origin[1] + (np.arange(n) + 0.5) * bev.resolution
    cx, cy = np.meshgrid(ax, ay)
    sel = grid > 0.5
    if not sel.any():
        raise ValueError("no shadow cells in this BEV — pick another pose")
    pts = np.stack([cx[sel], cy[sel]], axis=1)
    idx = np.linspace(0, len(pts) - 1, K * H).astype(int)
    traj = np.zeros((K, H, 5))
    traj[..., :2] = pts[idx].reshape(K, H, 2)
    traj[..., 3] = 0.3
    return traj


def closed_loop_per_unit_spread(scenario, term: str, weights, *, seed: int = 0,
                                params: MPPIParams | None = None,
                                **arm_kwargs) -> list[float]:
    """`spread_per_unit_weight` re-measured at each weight, in closed loop.

    Not the linearity test (`batch_per_unit_spread` is). This asks the
    *practical* question the ratio invites: can I measure the exchange rate
    once at a small weight and extrapolate to the weight I intend to ship?
    The answer on `cafe_obstacle_crossing_v0` is no — see the module docstring.
    """
    out = []
    for w in weights:
        table = measure(scenario, seed=seed, params=params,
                        **{**arm_kwargs, term: float(w)})
        out.append(table[term].spread_per_unit_weight if term in table else 0.0)
    return out


def format_table(table: dict[str, TermSpread]) -> str:
    """Markdown table, ordered by ratio descending — loudest term first."""
    rows = sorted(table.values(), key=lambda t: -t.ratio)
    out = ["| term | weight | spread (median) | rest (median) | ratio | per unit |",
           "|---|---|---|---|---|---|"]
    out += [f"| `{r.name}` | {r.weight:g} | {r.spread_median:.4g} | "
            f"{r.rest_median:.4g} | **{r.ratio:.3g}** | "
            f"{r.spread_per_unit_weight:.4g} |" for r in rows]
    return "\n".join(out)
