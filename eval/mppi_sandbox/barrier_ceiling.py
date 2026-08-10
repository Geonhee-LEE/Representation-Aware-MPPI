# SPDX-License-Identifier: BSD-3-Clause
"""Q-110 — is there *any* weight at which the soft barrier wins the verdict?

Why this exists
---------------
Two independent mechanisms have now bought multiplicative clearance on
`cafe_head_on_v0` and moved no verdict. D-119's risk channel held **32×** the
stock arm's clearance and stayed 8/8 unsafe; D-124's two-sided-gap gate held
**1.7×** and stayed 8/8. Both arms sit near 0.01 m against a scene that
declares 0.40 m. Q-110 reads that agreement as evidence the binding constraint
is not the barrier's *shape* but its *scale* — and asks the cheap question no
cycle had asked before changing a third cost shape: raise `w_obs_soft` until
something gives, and see what gives first.

The question has to be asked with an admissibility rule attached
----------------------------------------------------------------
"Does a weight exist where `unsafe_rate` drops" is not by itself answerable,
because two ways of dropping it are already known to this repo and neither is
a statement about the cost term:

* **Freeze.** `ab.assert_all_reached` exists because a 2026-08-02 sweep
  produced a +1.53 m berth at p = 1.19e-07 that was entirely an arm giving up
  early. Clearance is purchasable with liveness at any barrier weight, and an
  arm that does not finish has no admissible safety number.
* **A disguised temperature change.** D-027 shipped a critic weight that was
  6.19× the baseline cost spread and collapsed the softmax to argmin-over-
  draws (median ESS 77.9 → 1.00). At that point `lam` is inert, and the arm's
  behaviour changed because the *sampler* changed, not because the term did.
  `weight_units` is the instrument for that, and Q-049 asked whether the
  hazard was repo-wide; this module is the first sweep that walks a weight far
  enough to find out.

So a rung is **admissible** only when its arm reached the goal on every seed
*and* every seed's ESS is inside `ab.ess_band`. Both filters are pre-existing
project rules, applied here rather than invented here — the verdict below is
just what survives them.

What the three verdicts mean
----------------------------
`RELIEVED` — some admissible rung beats the baseline's `unsafe_rate`. The
barrier can win at a scale the sampler and the liveness rule both permit, and
Q-110's answer is that this was a tuning gap.

`BOUGHT_INADMISSIBLY` — `unsafe_rate` does drop, but only at rungs that fail
liveness or the ESS band. The barrier "wins" by ceasing to be a cost-term
change. This is the D-027 finding generalised from one critic weight to the
baseline's own obstacle term.

`SATURATED` — no rung drops `unsafe_rate`, admissible or not. The declared
margin is out of the barrier's reach at every scale tried.

The two negative verdicts are both "no" to Q-110 and they are **not**
interchangeable, which is why they are separate strings: `SATURATED` says the
term cannot move the verdict, `BOUGHT_INADMISSIBLY` says it can and the price
is the thing being measured. Only the first supports the representation
hypothesis on its own; the second says the operating point was never clean
enough to test it.

What a null here is worth
--------------------------
Q-110 flagged the risk that this sweep degenerates into tuning and drifts off
the project's core bet. It does not, because of the direction of the expected
answer: if no weight reaches 0.40 m, that is a measurement *supporting* the
claim that a scalar barrier over raw geometry is the wrong input — the thing
the representation programme exists to replace. A null is the headline, not a
failed experiment.

Scope
-----
`sweep` varies one knob at a time against a fixed `lam`, because the two knobs
are not interchangeable: `w_obs_soft` scales the barrier's contribution
linearly, while `obs_soft_scale` changes *where* the barrier has support and
so is not a pure gain. Reporting them on one axis would invite reading a
2-D surface off a 1-D walk.

Not a ratio against `w_path`
-----------------------------
The tempting summary — "sweep the `w_obs_soft`/`w_path` ratio" — is wrong here
and the reason is worth stating, because Q-110 itself is phrased that way.
Scaling *every* weight by `c` is exactly equivalent to scaling `lam` by `c`,
so a pure ratio would be a temperature change wearing a weight's name. Raising
`w_obs_soft` alone is not that: `w_speed`, `w_omega`, `w_terminal` and
`w_collision` stay put, so the ratio against each of them moves differently
and the effective temperature moves too. That last part is why the ESS filter
is not optional — it is the only thing separating the two readings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from ..path_tracking_metrics import cross_track_error
from . import ab, feasibility, near_miss, weight_units
from .controllers.stock_mppi import MPPIParams
from .scenario import Scenario

RELIEVED = "RELIEVED"
BOUGHT_INADMISSIBLY = "BOUGHT_INADMISSIBLY"
SATURATED = "SATURATED"

#: Knobs `sweep` will vary. Named so a caller cannot silently sweep a knob
#: whose relationship to the barrier is not linear-in-the-weight.
WEIGHT_KNOB = "w_obs_soft"
SCALE_KNOB = "obs_soft_scale"
KNOBS = (WEIGHT_KNOB, SCALE_KNOB)

#: `unsafe_rate` improvements below this are noise on an 8-seed ensemble
#: (one seed in eight is 0.125, so anything under half a seed is not a rung
#: distinguishing itself from its neighbour).
MIN_IMPROVEMENT = 1.0 / 16.0


@dataclass(frozen=True)
class Rung:
    """One knob value, one seed ensemble, one verdict-relevant row.

    `spread_ratio` is `weight_units.TermSpread.ratio` for the barrier at this
    rung — the term's per-sample cost spread as a multiple of everything it
    competes against. It is a **report**, not a filter: `ess_in_band` is the
    filter, and the ratio is here so a reader can see *why* a rung left the
    band rather than only that it did.

    `n_in_band` / `n_reached` are the witnesses behind the two verdict bools.
    They are here because **this** is the object a walk records, and until
    2026-08-11 it was where both counts died: `ab.summarize` gained
    `n_in_band` on 2026-08-11 03:00 (D-187) so that a future walk would pool
    as a point, but `_rung` read only `stats.ess_in_band` off it and the count
    went no further. `WalkCount.from_sweep` — the constructor that consumes it
    — had **no non-test caller**, so `COUNT_EXACT` stayed unreachable from any
    real walk, which is the D-138 reader-only-contract shape and the state
    D-044 says gets a check muted. `None` on both means a record predating
    this, and stays honest rather than being back-filled: the count was
    destroyed at walk time and no re-read recovers it.
    """

    knob: str
    value: float
    n: int
    unsafe_rate: float
    mean_clearance: float
    min_clearance: float
    all_reached: bool
    median_ess: float
    ess_in_band: bool | None
    spread_ratio: float = float("nan")
    #: Worst seed's `cte_rms`, and the scene's own bound on it (`None` if the
    #: scene declares no `cte_rms_max`). Worst rather than mean, because the
    #: scene's key is a bound each run must meet, not an ensemble average.
    cte_rms_worst: float = float("nan")
    declared_cte_rms_max: float | None = None
    n_in_band: int | None = None
    n_reached: int | None = None

    def __post_init__(self) -> None:
        """Refuse a rung whose counts contradict the bools they witness.

        Same rule as `ab.SweepStats.__post_init__`, restated here rather than
        inherited because the fields are copied across the `_rung` boundary
        independently — a pass-through is exactly where the two can drift
        apart without either side being wrong on its own.
        """
        if self.n_in_band is not None and self.ess_in_band is not None:
            if self.ess_in_band != (self.n_in_band == self.n):
                raise ValueError(
                    f"Rung({self.knob}={self.value}): ess_in_band="
                    f"{self.ess_in_band} contradicts n_in_band="
                    f"{self.n_in_band}/{self.n}")
        if self.n_reached is not None:
            if bool(self.all_reached) != (self.n_reached == self.n):
                raise ValueError(
                    f"Rung({self.knob}={self.value}): all_reached="
                    f"{self.all_reached} contradicts n_reached="
                    f"{self.n_reached}/{self.n}")

    @property
    def n_out_of_band(self) -> int | None:
        """The `k` a rate estimator wants, so that `WalkCount.from_sweep`
        accepts a `Rung` on the same duck type it accepts `ab.SweepStats` —
        this is what gives that constructor a production caller."""
        return None if self.n_in_band is None else self.n - self.n_in_band

    @property
    def n_froze(self) -> int | None:
        """Completion's `k`. `None` when the count is unknown."""
        return None if self.n_reached is None else self.n - self.n_reached

    @property
    def admissible(self) -> bool:
        """Both pre-existing filters, and `None` (unknown band) is not a pass."""
        return bool(self.all_reached) and self.ess_in_band is True

    @property
    def tracking_ok(self) -> bool | None:
        """Does every seed also hold the scene's *other* declared key?

        Deliberately **not** folded into `admissible`. The two answer different
        questions and the project has twice paid for conflating them (D-116,
        D-119): `admissible` asks whether this rung's number is evidence about
        the cost term at all, while `tracking_ok` asks what the rung costs on
        the axis the scene also grades. A rung can be perfectly good evidence
        *and* an unacceptable controller. `None` when the scene declares no
        bound — unknown, not a pass.
        """
        if self.declared_cte_rms_max is None:
            return None
        return bool(self.cte_rms_worst <= self.declared_cte_rms_max)

    @property
    def inadmissible_because(self) -> tuple[str, ...]:
        """Why this rung is not evidence — empty iff `admissible`."""
        why = []
        if not self.all_reached:
            why.append("froze")
        if self.ess_in_band is not True:
            why.append("ess_out_of_band" if self.ess_in_band is False
                       else "ess_unknown")
        return tuple(why)

    def __str__(self) -> str:
        mark = "ok " if self.admissible else "!  "
        track = {True: "track_ok", False: "TRACK_BROKEN", None: "track_?"}
        return (f"{mark}{self.knob}={self.value:<9.4g} "
                f"unsafe={self.unsafe_rate:.4f} "
                f"mean_clr={self.mean_clearance:.4f} "
                f"cte_rms={self.cte_rms_worst:.4f} "
                f"ess={self.median_ess:7.1f} "
                f"{track[self.tracking_ok]} "
                f"{','.join(self.inadmissible_because) or '-'}")


@dataclass(frozen=True)
class SweepResult:
    """One knob's walk, its baseline rung, and what survived the filters."""

    scenario: str
    knob: str
    lam: float
    margin: float
    baseline: Rung
    rungs: tuple[Rung, ...] = ()
    verdict: str = SATURATED

    @property
    def admissible_rungs(self) -> tuple[Rung, ...]:
        return tuple(r for r in self.rungs if r.admissible)

    @property
    def best_admissible(self) -> Rung | None:
        """Lowest `unsafe_rate` among admissible rungs; ties break on clearance."""
        adm = self.admissible_rungs
        if not adm:
            return None
        return min(adm, key=lambda r: (r.unsafe_rate, -r.mean_clearance))

    @property
    def ceiling(self) -> Rung | None:
        """The largest-`value` admissible rung — where the knob stops being a
        cost-term change. `None` when even the baseline is inadmissible."""
        adm = self.admissible_rungs
        return max(adm, key=lambda r: r.value) if adm else None

    @property
    def clearance_gain(self) -> float:
        """Best admissible rung's `mean_clearance` as a multiple of baseline's.

        The number D-119 and D-124 both reported (32×, 1.7×) and neither could
        convert into a verdict — computed here for the *same* mechanism at a
        different scale so the three are comparable.
        """
        best = self.best_admissible
        if best is None or not self.baseline.mean_clearance:
            return float("nan")
        return best.mean_clearance / self.baseline.mean_clearance

    def __str__(self) -> str:
        head = (f"{self.scenario} · {self.knob} @ lam={self.lam} · "
                f"margin={self.margin} · {self.verdict}")
        return "\n".join([head, f"   base {self.baseline}"]
                         + [f"        {r}" for r in self.rungs])


def classify(baseline: Rung, rungs: Sequence[Rung],
             min_improvement: float = MIN_IMPROVEMENT) -> str:
    """Which of the three verdicts this walk supports.

    Improvement is measured against `baseline.unsafe_rate`, not against the
    scene's margin, because the question is whether *this knob* moves the
    verdict — a rung that is unsafe on every seed at both ends has answered
    that regardless of how far from 0.40 m it sits.
    """
    improved = [r for r in rungs
                if baseline.unsafe_rate - r.unsafe_rate >= min_improvement]
    if not improved:
        return SATURATED
    if any(r.admissible for r in improved):
        return RELIEVED
    return BOUGHT_INADMISSIBLY


def cte_rms(traj, path_xy) -> float:
    """`sqrt(mean(e**2))` over one run's samples — the scene's own key.

    Sample-averaged, matching `feasibility.min_cte_rms`'s optimand exactly, so
    a measured value and that module's lower bound are comparable numbers
    rather than two similarly-named ones.
    """
    e = cross_track_error(np.asarray(traj), np.asarray(path_xy))
    return float(np.sqrt(np.mean(np.square(e))))


def _score(scenario: Scenario, *, params: MPPIParams, knob: str, value: float,
           margin: float, seeds: Sequence[int], controller: str,
           measure_spread: bool) -> Rung:
    # `params` is keyword-only so every call site *names* the temperature it
    # forwards. `default_lam_sites` classifies syntactically, and a positional
    # params object reads to it as "no lam named here" — which is exactly the
    # DEFAULTS finding this module would otherwise ship two of.
    runs = ab.seed_sweep(scenario, controller, seeds, params=params)
    stats = ab.summarize(runs)
    nm = near_miss.score_runs(runs, margin)
    ratio = float("nan")
    if measure_spread:
        table = weight_units.measure(scenario, controller, params=params)
        term = table.get(WEIGHT_KNOB)
        ratio = term.ratio if term is not None else float("nan")
    path_xy = scenario.waypoints[:, :2]
    worst = max((cte_rms(r.traj, path_xy) for r in runs), default=float("nan"))
    return Rung(
        knob=knob,
        value=float(value),
        n=stats.n,
        unsafe_rate=nm.unsafe_rate,
        mean_clearance=stats.mean_clearance,
        min_clearance=stats.min_clearance,
        all_reached=stats.all_reached,
        median_ess=stats.median_ess,
        ess_in_band=stats.ess_in_band,
        spread_ratio=ratio,
        cte_rms_worst=worst,
        declared_cte_rms_max=feasibility.declared_cte_rms(scenario),
        # Carry both witnesses, not just the verdicts they collapse to. This
        # is the line that makes `WalkCount.from_sweep` reachable from a real
        # walk; without it the count `summarize` computes dies one frame up.
        n_in_band=stats.n_in_band,
        n_reached=stats.n_reached,
    )


def sweep(scenario: Scenario, knob: str, values: Sequence[float], *,
          lam: float, scenario_name: str = "",
          seeds: Sequence[int] = tuple(ab.DEFAULT_SEEDS),
          controller: str = "stock_mppi",
          measure_spread: bool = True) -> SweepResult:
    """Walk one barrier knob at a fixed temperature and classify the walk.

    `lam` is required and has no default on purpose: the shipped `0.1` puts
    this scene's softmax at a median ESS of ~1 of 256, where the weighted
    update is argmin-over-draws and *no* additive term is audible unless it
    flips the argmin. A sweep run there would report `SATURATED` about the
    sampler while appearing to report it about the barrier.

    The scene's own declared margin is the safety bar (`near_miss.margin_for`);
    a scene that declares none is refused rather than scored against a
    convenient default, which is D-120's `unscored_margin` rule.
    """
    if knob not in KNOBS:
        raise ValueError(f"unknown knob {knob!r} — sweepable: {list(KNOBS)}")
    margin = near_miss.margin_for(scenario)
    if not near_miss.is_scorable_margin(margin):
        raise ValueError(
            f"{scenario_name or 'scenario'} declares no scorable margin "
            f"({margin!r}) — a barrier sweep needs a bar the scene set, not "
            "one this module picked")

    base_params = MPPIParams(lam=lam)
    baseline = _score(scenario, params=base_params, knob=knob,
                      value=getattr(base_params, knob), margin=margin,
                      seeds=seeds, controller=controller,
                      measure_spread=measure_spread)
    rungs = tuple(
        _score(scenario, params=MPPIParams(lam=lam, **{knob: float(v)}),
               knob=knob, value=v, margin=margin, seeds=seeds,
               controller=controller, measure_spread=measure_spread)
        for v in values)
    return SweepResult(
        scenario=scenario_name,
        knob=knob,
        lam=float(lam),
        margin=float(margin),
        baseline=baseline,
        rungs=rungs,
        verdict=classify(baseline, rungs),
    )


def _main(argv: Sequence[str] | None = None) -> int:
    import argparse

    from .scenario import load_scenario

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario")
    ap.add_argument("--knob", default=WEIGHT_KNOB, choices=list(KNOBS))
    ap.add_argument("--lam", type=float, required=True)
    ap.add_argument("--values", type=float, nargs="+", required=True)
    ap.add_argument("--seeds", type=int, default=8)
    ap.add_argument("--controller", default="stock_mppi")
    args = ap.parse_args(argv)

    scen = load_scenario(args.scenario)
    res = sweep(scen, args.knob, args.values, lam=args.lam,
                scenario_name=args.scenario, seeds=range(args.seeds),
                controller=args.controller)
    print(res)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
