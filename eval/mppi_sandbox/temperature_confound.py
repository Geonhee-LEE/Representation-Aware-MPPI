# SPDX-License-Identifier: BSD-3-Clause
"""How much of a cross-controller delta is the controller, and how much is λ?

Why this exists
---------------
Q-107. `baseline_matrix.pick_lam` resolves a temperature **per cell**, and on
`cafe_obstacle_crossing_v0` the two arms' admissible windows are disjoint —
`stock_mppi` gets `0.8`, `risk_mppi` gets `3.2`. Each cell is individually in
band, so each cell's number is a real number about that controller. The
headline then subtracts them across the controller axis, and that subtraction
is exactly the arrangement `ab.assert_single_lam_ab` refuses in so many words.
Q-107 asked whether the resulting delta is a controller difference or a
temperature difference, and answered: *measure it before building anything.*

The decomposition
-----------------
For arms `a @ λa` and `b @ λb`, the reported delta splits **exactly** — this
is an identity, not a model::

    reported   = M(b@λb) - M(a@λa)
    matched@λb = M(b@λb) - M(a@λb)      # both arms at b's rung
    temp_a     = M(a@λb) - M(a@λa)      # same controller, temperature only

    reported  ==  matched@λb  +  temp_a

and symmetrically at `λa` via `M(b@λa)`. Two matched comparisons, two
temperature terms, one reported delta. `confound_share` is `|temp| /
|reported|`: the fraction of the published gap that a *single controller*
reproduces by changing nothing but its temperature.

The result that decided Q-107
-----------------------------
Measured 2026-08-08 on `cafe_obstacle_crossing_v0`, 8 seeds, the matrix's own
rungs (`stock@0.8` vs `risk@3.2`, gap 4×). Sign is `risk - stock`::

    metric          reported   matched@0.8   matched@3.2   share   verdict
    min_clearance   +0.0205      -0.0078       +0.0150     1.381   SIGN_FLIP
    mean_clearance  +0.0418      +0.0618       +0.0214     0.487   ROBUST
    unsafe_rate     +0.0000      -0.1250       +0.0000       inf   MASKED

The confound is not a rounding term. On `min_clearance` the published delta
says `risk_mppi` keeps 20 mm more room; run both arms at `0.8` and it keeps
**8 mm less** — the temperature term is 138% of the delta it is inside. On
`unsafe_rate`, the headline safety scalar, the published delta is exactly zero
while a matched comparison finds one seed in eight. `mean_clearance` survives,
and only just: 48.7% against a 50% line, which is a pass by 1.3 points and
should be read as one.

Halving the gap helps and does not fix it
-----------------------------------------
Re-run at `ab.lam_for`'s rungs (`stock@0.8` vs `risk@1.6`, gap 2×) and the
confound share on `mean_clearance` roughly halves with the log-gap, 0.487 →
0.252. The other two verdicts do not move: `min_clearance` is still
`SIGN_FLIP` (the inverting rung is `0.8`, which both protocols keep) and
`unsafe_rate` is still `MASKED`. So consulting the gap-minimising reader is a
real reduction in a quantitative impurity and no answer at all to the
qualitative ones.

The part that makes (b) unavailable
-----------------------------------
Every matched comparison above is measured with at least one arm **outside**
its Q-026 ESS band, and that is not an implementation shortcut: on a scene
whose windows are disjoint, "both arms at one temperature" and "both arms in
band" cannot hold at once. That is what `verdict="per_arm"` *means*. So the
trade Q-107 posed — clean comparison vs sample retention — was not the real
one. Both available protocols are impure, and they are impure in different
ways: the per-arm delta carries a temperature confound, the matched delta
carries an out-of-band arm. Hence `MatchedDelta.out_of_band`: the number is
reportable, and never reportable without that flag.

Not a second `pick_lam`
-----------------------
This module chooses no rungs. It reads whatever pair it is handed and prices
the gap between them, which is why it also surfaces that the tree already
contains **two** answers to "which rung does this cell run at":
`baseline_matrix.pick_lam` (log-middle of the arm's own window) and
`ab.ABTemperature.lam_for` (the rung minimising the log-gap to the other arm).
On this scene they disagree — 4× gap vs 2× — and the measured confound share
tracks the gap: 49% at 4×, 25% at 2×. Adding a third statement of that choice
here would be D-047 for the third time.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

#: Verdicts, worst-first. `classify` returns the **first** that applies, so the
#: order is the ladder: a delta whose sign is not stable under temperature is
#: not additionally graded on what fraction of it temperature explains.
UNMEASURABLE = "UNMEASURABLE"
SIGN_FLIP = "SIGN_FLIP"
MASKED = "MASKED"
TEMPERATURE_DOMINATED = "TEMPERATURE_DOMINATED"
ROBUST = "ROBUST"

#: `|temp| / |reported|` at or above which the published gap is more
#: temperature than controller. One half, because that is the point where the
#: same controller reproduces most of its rival's reported advantage by
#: changing only λ. Named so a change to it is a diff, not drift.
DOMINANCE_SHARE = 0.5

#: Below this, a delta is treated as absent. Deliberately *not* zero: an exact
#: `0.0` reported delta with a non-zero matched one is the `MASKED` finding,
#: and float noise on a rate metric must not be allowed to counterfeit it.
DEFAULT_TOL = 1e-9


@dataclass(frozen=True)
class ArmPoint:
    """One arm's metric value at one temperature, with its admissibility."""

    controller: str
    lam: float
    value: float
    #: `ab.SweepStats.ess_in_band` — `None` when the sweep could not say.
    #: Carried rather than re-derived because the whole point of a matched
    #: comparison here is that one of its arms is out of band.
    ess_in_band: bool | None = None
    all_reached: bool = True

    @property
    def key(self) -> tuple[str, float]:
        return (self.controller, float(self.lam))


@dataclass(frozen=True)
class MatchedDelta:
    """`b - a` with both arms at one temperature, plus what that cost."""

    lam: float
    #: `M(b@lam) - M(a@lam)`.
    delta: float
    #: `reported - delta`. The same-controller temperature term; the identity
    #: `reported == delta + temperature` holds exactly by construction.
    temperature: float
    #: True when either arm ran outside its ESS band at this rung. On a
    #: disjoint-window scene this is true for **every** matched rung, which is
    #: the finding, not a defect.
    out_of_band: bool

    def confound_share(self, reported: float) -> float:
        """Fraction of the reported gap reproduced by temperature alone.

        `inf` when the reported gap is zero — a masked delta is not "0%
        confounded", it is a published number that a temperature change makes
        appear from nothing, and returning 0.0 there would read as clean.
        """
        if reported == 0.0:
            return float("inf") if self.temperature != 0.0 else 0.0
        return abs(self.temperature) / abs(reported)

    def as_dict(self, reported: float) -> dict:
        return {
            "lam": self.lam,
            "delta": self.delta,
            "temperature": self.temperature,
            "confound_share": self.confound_share(reported),
            "out_of_band": self.out_of_band,
        }


@dataclass(frozen=True)
class Decomposition:
    """The reported delta, every temperature-matched counterpart, a verdict."""

    metric: str
    a: str
    b: str
    lam_a: float
    lam_b: float
    reported: float
    matched: tuple[MatchedDelta, ...]
    verdict: str
    tol: float = DEFAULT_TOL

    @property
    def lam_gap(self) -> float:
        lo, hi = sorted((float(self.lam_a), float(self.lam_b)))
        return hi / lo if lo > 0 else float("inf")

    @property
    def max_confound_share(self) -> float:
        """Worst case over matched rungs; `0.0` when none could be formed."""
        if not self.matched:
            return 0.0
        return max(m.confound_share(self.reported) for m in self.matched)

    @property
    def reportable_as_controller_delta(self) -> bool:
        """May the headline attribute this gap to the controller axis?"""
        return self.verdict == ROBUST

    def as_dict(self) -> dict:
        return {
            "metric": self.metric,
            "arms": [self.a, self.b],
            "lams": [self.lam_a, self.lam_b],
            "lam_gap": self.lam_gap,
            "reported": self.reported,
            "matched": [m.as_dict(self.reported) for m in self.matched],
            "max_confound_share": self.max_confound_share,
            "verdict": self.verdict,
        }


def _sign(x: float, tol: float) -> int:
    if x > tol:
        return 1
    if x < -tol:
        return -1
    return 0


def classify(reported: float, matched: Sequence[MatchedDelta],
             tol: float = DEFAULT_TOL,
             dominance: float = DOMINANCE_SHARE) -> str:
    """Grade a decomposition. First rung of the ladder that applies wins.

    `UNMEASURABLE` is *not* decided here — it is a property of the runs, not
    of the arithmetic, so `decompose` raises it before any of this is reached.
    """
    if not matched:
        return UNMEASURABLE
    r = _sign(reported, tol)
    signs = [_sign(m.delta, tol) for m in matched]
    if r != 0 and any(s != 0 and s != r for s in signs):
        return SIGN_FLIP
    if r == 0 and any(s != 0 for s in signs):
        return MASKED
    shares = [m.confound_share(reported) for m in matched]
    if shares and max(shares) >= dominance:
        return TEMPERATURE_DOMINATED
    return ROBUST


def decompose(points: Iterable[ArmPoint], a: str, b: str,
              lam_a: float, lam_b: float, metric: str = "metric",
              tol: float = DEFAULT_TOL,
              dominance: float = DOMINANCE_SHARE) -> Decomposition:
    """Split `M(b@lam_b) - M(a@lam_a)` into controller and temperature parts.

    `points` supplies up to the four `(arm, λ)` cells; the two diagonal ones
    are required (they are the published comparison) and each off-diagonal one
    yields a matched rung if present. A point whose sweep did not reach the
    goal is dropped rather than differenced — an unfinished run's clearance is
    not a statement about clearance (`baseline_matrix.NOT_REACHED`, same rule).
    """
    lam_a, lam_b = float(lam_a), float(lam_b)
    by_key: dict[tuple[str, float], ArmPoint] = {}
    for p in points:
        if p.all_reached:
            by_key[p.key] = p

    try:
        a_at_a = by_key[(a, lam_a)]
        b_at_b = by_key[(b, lam_b)]
    except KeyError as exc:
        raise ValueError(
            f"no reported delta for {metric}: the published pair "
            f"({a}@{lam_a}, {b}@{lam_b}) is missing or did not reach — "
            f"missing {exc.args[0]}") from None

    reported = b_at_b.value - a_at_a.value

    matched: list[MatchedDelta] = []
    # `dict.fromkeys` rather than a set: order is the report order, and when
    # the two published rungs coincide there is one matched comparison, not
    # the same one twice.
    for lam in dict.fromkeys((lam_b, lam_a)):
        pa, pb = by_key.get((a, lam)), by_key.get((b, lam))
        if pa is None or pb is None:
            continue
        delta = pb.value - pa.value
        matched.append(MatchedDelta(
            lam=lam,
            delta=delta,
            temperature=reported - delta,
            # `is False` on purpose: `None` means the sweep could not say, and
            # "unknown" must not be recorded as "in band".
            out_of_band=(pa.ess_in_band is False or pb.ess_in_band is False),
        ))

    return Decomposition(
        metric=metric, a=a, b=b, lam_a=lam_a, lam_b=lam_b,
        reported=reported, matched=tuple(matched),
        verdict=classify(reported, matched, tol=tol, dominance=dominance),
        tol=tol,
    )


#: Scalars a decomposition can be taken over. Each maps a finished seed
#: ensemble to one number. Sign convention is **raw** — higher is better for
#: clearance, worse for `unsafe_rate` — because the verdict is about sign
#: *stability*, and normalising the direction here would hide which way a flip
#: went.
METRICS: dict[str, Callable] = {
    "min_clearance": lambda stats, safety: stats.min_clearance,
    "mean_clearance": lambda stats, safety: stats.mean_clearance,
    "mean_speed": lambda stats, safety: stats.mean_speed,
    "unsafe_rate": lambda stats, safety: (
        float("nan") if safety is None else safety.unsafe_rate),
}


def measure(scenario_path: str, controllers: Sequence[str],
            lams: Sequence[float], seeds: Iterable[int] = range(8),
            metrics: Sequence[str] = ("min_clearance", "mean_clearance",
                                      "unsafe_rate")) -> dict:
    """Sweep the `controllers × lams` grid once and decompose every metric.

    One sweep per cell, reused across metrics — the grid is the expensive part
    (~0.85 s per run on `cafe_obstacle_crossing_v0`) and the metrics are all
    functions of the same runs.
    """
    from .ab import seed_sweep, summarize
    from .controllers.stock_mppi import MPPIParams
    from .feasibility import declared_margin
    from .near_miss import is_scorable_margin, score_runs
    from .scenario import load_scenario

    scenario = load_scenario(scenario_path)
    margin = declared_margin(scenario)
    seeds = list(seeds)

    grid: dict[tuple[str, float], tuple] = {}
    for ctrl in controllers:
        for lam in lams:
            runs = seed_sweep(scenario, ctrl, seeds,
                              params=MPPIParams(lam=float(lam)))
            stats = summarize(runs)
            safety = (score_runs(runs, margin)
                      if is_scorable_margin(margin) else None)
            grid[(ctrl, float(lam))] = (stats, safety)

    a, b = controllers[0], controllers[1]
    lam_a, lam_b = float(lams[0]), float(lams[-1])
    out = {
        "scenario": scenario_path,
        "seeds": len(seeds),
        "margin": margin,
        "grid": [
            {"controller": c, "lam": l, "ess_in_band": s.ess_in_band,
             "all_reached": s.all_reached, "median_ess": s.median_ess,
             **{m: METRICS[m](s, sf) for m in metrics}}
            for (c, l), (s, sf) in sorted(grid.items())
        ],
        "decompositions": [],
    }
    for m in metrics:
        points = [
            ArmPoint(controller=c, lam=l, value=METRICS[m](s, sf),
                     ess_in_band=s.ess_in_band, all_reached=s.all_reached)
            for (c, l), (s, sf) in grid.items()
        ]
        out["decompositions"].append(
            decompose(points, a, b, lam_a, lam_b, metric=m).as_dict())
    return out


def _main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenario",
                    default="eval/scenarios/cafe_obstacle_crossing_v0.yaml")
    ap.add_argument("--arms", nargs=2,
                    default=["stock_mppi", "risk_mppi"])
    ap.add_argument("--lams", nargs="+", type=float, default=[0.8, 3.2],
                    help="first is arm-a's rung, last is arm-b's")
    ap.add_argument("--seeds", type=int, default=8)
    args = ap.parse_args(argv)

    result = measure(args.scenario, args.arms, args.lams,
                     seeds=range(args.seeds))
    print(json.dumps(result, indent=2, default=float))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
