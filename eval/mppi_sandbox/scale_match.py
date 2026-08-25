# SPDX-License-Identifier: BSD-3-Clause
"""Pick a cost weight in units of the baseline it competes with — and find the
fixed point that prescription hides.

Where this comes from
---------------------
D-027 *swept* `ObservationValueCritic` at `w_voo = 200` (inherited from
whatever `w_epist` happened to be) and found it was a **disguised temperature
change**: 6.19× the baseline's median per-step cost spread, median ESS
77.9 → 1.00, i.e. argmin-over-draws. It **shipped the default at `w_voo = 0.0`**
on the strength of exactly that result — D-027 Decision (5), "default 는 하나도
안 움직인다", pinned by the byte-identical-no-op ablation invariant. Read this
paragraph as a record of a *rejected* rung, never of a shipped configuration:
the earlier wording ("shipped ... at `w_voo = 200`") said the opposite and
D-405 inherited the mistake (corrected in D-406). D-028 then built the general instrument
(`weight_units.measure`) and established *which* denominator that ratio has to
use — the arm the weight is **added to**, never the arm **carrying** it, since
a weight bad enough to derail a run inflates its own denominator and the worse
it is the better it looks.

That leaves a prescription without a procedure. STATE item #1 wants a `lam`
window for an arm that actually carries `w_voo`, "at a scale-matched weight",
and D-028 says where to read the exchange rate. This module is that step made
callable: `exchange_rate` measures it on the undamaged arm, `weight_for_ratio`
inverts it, and `damage guard` below refuses to report when the probe itself
derailed.

The finding: the prescription is a fixed point, not two steps
-------------------------------------------------------------
"Scale-match the weight, then calibrate the temperature" reads like a pipeline.
It is not, because the ratio's two halves have opposite `lam` sensitivity.
Measured on `cafe_obstacle_crossing_v0` over the factor-2 ladder
(`calibrate_lam.DEFAULT_LADDER`, 0.05 → 6.4, a **128×** span), on the shipped
`risk_mppi` arm:

===========  ==================  ================  ===================
`lam`        `per_unit` (ptp f)  `rest` (median)   `w` for ratio 0.1
===========  ==================  ================  ===================
0.05         2.621               187.98            7.172
0.1          2.459               133.46            5.428
0.2          2.585               175.96            6.807
0.4          2.482               135.92            5.476
0.8          2.476               112.55            4.545
1.6          2.356               101.21            4.296
3.2          2.525                85.97            3.405
6.4          2.339                83.12            3.555
===========  ==================  ================  ===================

**The numerator is a property of the term; the denominator is a property of the
temperature.** `per_unit` — the term's own spread at unit weight — moves only
**1.12×** across a 128× change in `lam`, so the exchange rate is essentially a
constant of the critic. But `rest`, the landscape it is priced against, falls
**2.26×** as `lam` rises: a hotter softmax averages more of the cloud into the
update, the loop tracks differently, and the baseline cost spread it presents
shrinks. The scale-matched weight is their quotient and inherits the
denominator's swing — **2.11×** end to end.

So the weight that is "10 % of baseline" at the shipped `lam = 0.1` is
**5.43**, and the same 10 % at `lam = 3.2` is **3.41**. Calibrating a window
for a fixed scale-matched weight therefore asks the arm to hold a ratio it only
has at one rung. `scale_matched_ladder` is the alternative this module offers:
hold the **ratio** fixed across the ladder and let the weight vary per rung, so
every rung is compared at the same scale rather than at the same number.

Which of the two is the honest protocol is not settled here — it depends on
whether the quantity you intend to ship is a weight or a ratio, and this module
deliberately implements both rather than picking (see the cycle report).

Cost
----
`exchange_rate` is **one closed-loop run** (plus one for the damage baseline,
cached by the caller if it is doing a ladder). A full `scale_matched_ladder`
over the eight-rung default is ~9 runs, ~1 min — a script-scale measurement,
not a suite-scale one. The committed tests probe two rungs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .controllers.stock_mppi import MPPIParams
from .weight_units import ADDITIVE_WEIGHTS, NON_ADDITIVE_KNOBS, measure

#: How much longer than the undamaged baseline a probe run may take before its
#: measured `rest` is treated as self-inflicted. D-028's counterexample is the
#: extreme case — `w_voo = 200` runs 1000 steps against the baseline's 114
#: (8.8×) and inflates the denominator 10.9× — but the failure is continuous,
#: not a cliff, so the guard trips well before that. 1.25× allows the ordinary
#: few-step variation between arms (measured 92–122 steps across the whole
#: ladder on one scene) without admitting a run that is visibly limping.
DAMAGE_TOLERANCE = 1.25

#: Weight the exchange rate is probed at. Small enough not to steer the arm
#: (the damage guard checks, rather than assuming), large enough that
#: `spread_per_unit_weight` is not a ratio of two near-zero floats. D-028
#: measured the closed-loop rate at w = 1 / 7 / 200 as 2.50 / 2.34 / 5.30 — the
#: first two agree to 7 %, the third is the derailed arm grading itself.
DEFAULT_PROBE_WEIGHT = 1.0


@dataclass(frozen=True)
class ExchangeRate:
    """What one unit of `term` buys, priced against the arm it is added to.

    Measured at one `(scenario, controller, lam)` with the term set to
    `probe_weight` and everything else at the arm's shipped values — so `rest`
    is the *shipped baseline's* landscape, not an isolated one. That matters
    for the intended use: `lam_windows.yaml`'s `risk_mppi` cells were measured
    with `w_risk = 40` live, so a weight scale-matched against an isolated
    baseline would not be commensurable with them.
    """

    term: str
    lam: float
    probe_weight: float
    #: `ptp(f)` — the term's per-sample spread at unit weight. Near-invariant
    #: in `lam` (1.12× over 128×); this is the transferable half.
    per_unit: float
    #: Median per-step spread of everything else. Moves 2.26× over the same
    #: ladder; this is the half that makes the prescription a fixed point.
    rest: float
    n_steps: int
    baseline_n_steps: int

    @property
    def ratio(self) -> float:
        """The probe weight's own ratio — `weight_for_ratio` inverts this."""
        return float(self.probe_weight * self.per_unit / self.rest)

    @property
    def damage(self) -> float:
        """Probe run length over undamaged run length.

        D-028's inversion detector. `> DAMAGE_TOLERANCE` means the probe
        weight already steered the arm off the baseline whose spread it is
        being divided by, so `rest` is partly the weight's own wreckage and
        the rate flatters itself.
        """
        return float(self.n_steps / self.baseline_n_steps)

    @property
    def is_undamaged(self) -> bool:
        return self.damage <= DAMAGE_TOLERANCE

    def weight_for_ratio(self, ratio: float) -> float:
        """Weight at which this term's spread is `ratio` × the baseline's.

        Linear because `ptp(w·f) = w·ptp(f)` exactly on a fixed batch
        (`weight_units.batch_per_unit_spread`, constant to machine precision).
        The *measurement* is still not extrapolable — D-028 pinned that the
        closed-loop rate moves 2.1× between w = 1 and w = 200 — so a weight
        returned here is a **starting point to re-measure at**, not a number to
        trust at 40× the probe. `verify_ratio` closes that loop.
        """
        if self.per_unit <= 0.0:
            raise ValueError(
                f"{self.term} has zero spread at lam={self.lam} — it "
                f"multiplies an identically-zero term on this arm (the D-021 "
                f"condition), so no weight gives it a ratio.")
        return float(ratio * self.rest / self.per_unit)

    def __str__(self) -> str:
        return (f"{self.term} @ lam={self.lam:g}: per_unit={self.per_unit:.4g} "
                f"rest={self.rest:.4g} ratio={self.ratio:.4g} "
                f"damage={self.damage:.2f}x")


def _n_steps(table: dict) -> int:
    """Run length from any row — every row is the same closed-loop run."""
    if not table:
        raise ValueError("empty spread table — no live weights on this arm")
    return next(iter(table.values())).n_steps


def exchange_rate(scenario, term: str = "w_voo", *,
                  lam: float,
                  horizon: int = MPPIParams().horizon,
                  probe_weight: float = DEFAULT_PROBE_WEIGHT,
                  controller: str = "risk_mppi",
                  seed: int = 0,
                  baseline_n_steps: int | None = None,
                  **arm_kwargs) -> ExchangeRate:
    """Measure `term`'s exchange rate against the arm it is being added to.

    Two runs: the arm at `term = 0` (the undamaged baseline, for the damage
    guard) and the arm at `term = probe_weight`. Pass `baseline_n_steps` to
    reuse the first across a ladder.

    `horizon` defaults to the shipped rollout length. It is a parameter because
    almost every term here is a **sum over H** rollout steps, so `per_unit`
    scales with the horizon and a weight scale-matched at one `H` is a
    different ratio at another: `w_voo` is not transferable across a horizon
    change any more than it is across a `lam` change (D-029). `horizon_audit`
    is where that stops being a caveat and becomes the reason the
    `(w_voo, horizon)` 2×2 has only one admissible rung.

    Raises for the knobs that have no exchange rate at all — `weight_units`
    already established that `k_margin_per_sigma` is in metres, not in cost
    units, and asking for its ratio is a category error rather than a
    measurement that happens to fail.
    """
    if term in NON_ADDITIVE_KNOBS:
        raise ValueError(
            f"{term} is not an additive cost coefficient — its unit is "
            f"{NON_ADDITIVE_KNOBS[term]}, so it has no baseline-spread ratio "
            f"and no scale-matched weight (D-028).")
    if term not in ADDITIVE_WEIGHTS:
        raise KeyError(f"unknown cost weight {term!r}")

    params = MPPIParams(lam=lam, horizon=int(horizon))
    if baseline_n_steps is None:
        baseline_n_steps = _n_steps(
            measure(scenario, controller, seed=seed, params=params,
                    **{**arm_kwargs, term: 0.0}))

    table = measure(scenario, controller, seed=seed, params=params,
                    **{**arm_kwargs, term: float(probe_weight)})
    if term not in table:
        raise ValueError(
            f"{term} is not live on this arm at lam={lam} — `measure` skips "
            f"zero-weight terms, so the probe weight never reached the cost.")
    row = table[term]
    return ExchangeRate(
        term=term, lam=lam, probe_weight=float(probe_weight),
        per_unit=row.spread_per_unit_weight, rest=row.rest_median,
        n_steps=row.n_steps, baseline_n_steps=int(baseline_n_steps),
    )


def check_undamaged(rate: ExchangeRate) -> None:
    """Raise if `rate`'s probe weight already steered the arm it is priced
    against — D-028's inversion, as a precondition.

    Split out of `weight_for_ratio` so the check can be asserted against an
    already-measured rate. Each damaged-regime measurement is a derailed
    closed-loop run (1000 steps against a healthy ~100), so a test suite that
    re-probes for every assertion pays ~40 s a time.
    """
    if not rate.is_undamaged:
        raise ValueError(
            f"probe weight {rate.probe_weight:g} already damaged the arm "
            f"({rate.n_steps} steps vs baseline {rate.baseline_n_steps}, "
            f"{rate.damage:.2f}x > {DAMAGE_TOLERANCE}) — its `rest` is partly "
            f"self-inflicted, so the exchange rate flatters itself (D-028). "
            f"Probe lower.")


def weight_for_ratio(scenario, term: str = "w_voo", *,
                     ratio: float, lam: float,
                     require_undamaged: bool = True,
                     **kwargs) -> float:
    """One call: what weight makes `term` `ratio` × the baseline at this `lam`?

    `require_undamaged` enforces D-028 — if the probe weight already derailed
    the arm, the denominator is the weight's own wreckage and the answer would
    be silently too large. Set it False only to *study* the damaged regime.
    """
    rate = exchange_rate(scenario, term, lam=lam, **kwargs)
    if require_undamaged:
        check_undamaged(rate)
    return rate.weight_for_ratio(ratio)


def scale_matched_ladder(scenario, term: str = "w_voo", *,
                         ratio: float,
                         lams: Iterable[float],
                         controller: str = "risk_mppi",
                         seed: int = 0,
                         probe_weight: float = DEFAULT_PROBE_WEIGHT,
                         **arm_kwargs) -> dict[float, float]:
    """`{lam: weight}` holding the **ratio** fixed across the ladder.

    The alternative protocol to "pick one scale-matched weight and sweep `lam`
    under it". Because `rest` falls with `lam` (2.26× over the default ladder),
    a fixed weight silently rises in ratio as the ladder climbs — the arm at
    the top of the ladder is a *louder* arm than the one at the bottom, and any
    window it produces is a window for a moving target. Holding the ratio fixed
    costs one extra run per rung and makes the rungs commensurable.

    Returns weights, not a calibration; feed it to `ab.lam_ladder` per rung.
    """
    lams = list(lams)
    base = None
    out: dict[float, float] = {}
    for lam in lams:
        rate = exchange_rate(scenario, term, lam=lam, controller=controller,
                             seed=seed, probe_weight=probe_weight,
                             baseline_n_steps=base, **arm_kwargs)
        # Baseline length is re-derived per rung: the loop's own step count
        # moves with the temperature (92 -> 122 over the default ladder), so
        # reusing the first rung's would make the damage guard read a real
        # temperature effect as weight damage.
        base = None
        out[lam] = rate.weight_for_ratio(ratio)
    return out


def verify_ratio(scenario, term: str, weight: float, *, lam: float,
                 **kwargs) -> float:
    """Re-measure the ratio actually achieved at `weight` — closes D-028's loop.

    `weight_for_ratio` extrapolates from a unit-weight probe along an algebra
    that is exactly linear on a fixed batch but *not* in closed loop, where a
    different weight steers to a different state sequence. This runs the arm at
    the prescribed weight and reports what it really came out as, which is the
    number a report should quote.
    """
    rate = exchange_rate(scenario, term, lam=lam, probe_weight=weight, **kwargs)
    return rate.ratio


def format_ladder(ladder: dict[float, float], rates: Sequence[ExchangeRate] = (),
                  ) -> str:
    """Markdown for the `{lam: weight}` schedule, with the two halves split out
    so a reader can see which one moved."""
    by_lam = {r.lam: r for r in rates}
    head = ["| `lam` | `per_unit` | `rest` | weight |", "|---|---|---|---|"]
    rows = []
    for lam, w in sorted(ladder.items()):
        r = by_lam.get(lam)
        pu = f"{r.per_unit:.4g}" if r else "—"
        rest = f"{r.rest:.4g}" if r else "—"
        rows.append(f"| {lam:g} | {pu} | {rest} | **{w:.4g}** |")
    return "\n".join(head + rows)
