"""Price the repair, don't just name the disease (Q-055).

D-034 measured how far the two SIMD dispatches land apart and sorted the five
flipping claims into four fragility classes.  It stopped one step short of the
question the classes exist to answer: **for each claim, what would it cost to
make the assertion true on both machines, and is what survives still the claim
that was made?**

That step needs no new simulation.  Every contested assertion writes down its
own acceptance interval, so the minimum admitting tolerance is arithmetic on
numbers already banked in ``results/dispatch-divergence/``.  The central
identity is that D-034's own instrument already answered it::

    widen_factor = 1 + excursion

An excursion is a *distance*; the same number read as a *cost* is the factor by
which the tolerance must grow.  Nobody read it that way, so the repair question
looked like it needed another measurement round.  It did not.

What the three kinds of claim cost is not commensurable, which is the point:

* **band** (two-sided tolerance around a target) — widening is well defined.
  The tolerance is scaffolding around the target, so a wider one still asserts
  the target.  Report the factor and the margin it leaves.
* **threshold** (one-sided, ``value > lo``) — the threshold *is* the claim.
  Lowering it to admit the other machine does not loosen the assertion, it
  replaces it with a weaker one, so the honest figure is what fraction of the
  asserted effect survives against the claim's own null.
* **categorical** (set non-emptiness) — there is no widening operator at all.
  A set is empty or it is not.

Usage::

    python3 -m eval.mppi_sandbox.repair_admissibility \\
        results/dispatch-divergence/avx512-skx.json \\
        results/dispatch-divergence/avx2-masked.json

**This module asserts nothing about the numbers it prints** — same rule
:mod:`eval.mppi_sandbox.dispatch_divergence` adopted, and for the same reason:
a test pinning a dispatch-dependent value would fail on CI for precisely the
reason the file exists to document.  Its tests cover the arithmetic and the
verdict logic; the readings live in the journal and in ``results/``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Any

#: Above this factor a widened band is judged to have stopped asserting its
#: original claim: the tolerance has more than doubled, so the repaired
#: interval contains the whole span between the two machines *plus* the
#: original band.  This is a **judgement**, not a measurement -- stated as a
#: constant so that disagreeing with it is a one-line edit rather than an
#: argument with the code.
MAX_HONEST_WIDEN = 2.0

#: The null a one-sided ratio claim is asserted against.  All four thresholds
#: in the divergent set are ratios where 1.0 means "no effect".
RATIO_NULL = 1.0


@dataclass(frozen=True)
class Repair:
    """What it would take to make one claim hold on both dispatches."""

    claim: str
    kind: str  # band | threshold | categorical
    verdict: str
    #: multiplier the acceptance half-width needs (band only)
    widen_factor: float | None = None
    #: threshold the assertion would have to drop to (threshold only)
    repaired_threshold: float | None = None
    #: fraction of the asserted effect that survives that drop (threshold only)
    effect_retained: float | None = None
    note: str = ""

    def widen_factor_for_margin(self, margin: float) -> float | None:
        """Factor leaving the outlying machine ``margin`` of the new half-width.

        The minimum admitting factor leaves exactly zero by construction, which
        is a repair only in the sense that the assertion still runs.  Asking for
        a stated margin is how "carries both machines" becomes a claim with a
        number attached.
        """
        if self.widen_factor is None:
            return None
        if not 0.0 <= margin < 1.0:
            raise ValueError(f"margin must be in [0, 1), got {margin}")
        return self.widen_factor / (1.0 - margin)

    def margin_at_factor(self, factor: float) -> float | None:
        """Inverse of :meth:`widen_factor_for_margin` -- what a proposal leaves.

        Negative means the proposed factor does not admit the other machine.
        """
        if self.widen_factor is None:
            return None
        if factor <= 0:
            raise ValueError(f"factor must be positive, got {factor}")
        return 1.0 - self.widen_factor / factor


def _band_repair(name: str, excursion: float) -> Repair:
    factor = 1.0 + excursion
    honest = factor <= MAX_HONEST_WIDEN
    return Repair(
        claim=name,
        kind="band",
        verdict="widenable" if honest else "widening-destroys-discrimination",
        widen_factor=factor,
        note=(
            f"tolerance x{factor:.3f} admits both"
            if honest else
            f"tolerance x{factor:.3f} > x{MAX_HONEST_WIDEN:g}: the repaired band "
            f"contains the machine split and the original band, so it no longer "
            f"resolves what it was built to resolve"
        ),
    )


def _threshold_repair(name: str, lo: float, worst: float) -> Repair:
    """A one-sided claim: the number in the assertion is the assertion."""
    asserted = lo - RATIO_NULL
    surviving = worst - RATIO_NULL
    retained = (surviving / asserted) if asserted else None
    return Repair(
        claim=name,
        kind="threshold",
        verdict="threshold-is-the-claim",
        repaired_threshold=worst,
        effect_retained=retained,
        note=(
            f"dropping {lo:g} -> {worst:.5g} keeps "
            f"{'n/a' if retained is None else f'{retained:.1%}'} of the asserted "
            f"effect over the null {RATIO_NULL:g}; the surviving statement is not "
            f"the one that was reported"
        ),
    )


def _categorical_repair(name: str) -> Repair:
    return Repair(
        claim=name,
        kind="categorical",
        verdict="no-widening-operator",
        note="set non-emptiness has no tolerance to widen; on the other machine "
             "the claim cannot be stated, not merely cannot be met",
    )


def price(claim_a: dict, claim_b: dict, name: str) -> Repair:
    """Price the repair for one claim measured on two machines.

    ``claim_a`` is the arm the constants were calibrated on, ``claim_b`` the
    arm they fail on.  Only ``b``'s reading can drive the cost -- ``a`` passes
    by construction, so a repair that admits ``b`` admits both.
    """
    if claim_b.get("categorical"):
        return _categorical_repair(name)
    lo, hi = claim_b.get("lo"), claim_b.get("hi")
    if lo is not None and hi is not None:
        exc = claim_b.get("excursion")
        if exc is None:
            raise ValueError(f"{name}: two-sided claim with no excursion")
        return _band_repair(name, exc)
    if lo is not None:
        return _threshold_repair(name, lo, min(claim_a["value"], claim_b["value"]))
    raise ValueError(f"{name}: claim is neither categorical, band, nor lower-bound")


@dataclass
class Bill:
    """The whole divergent set, priced."""

    repairs: list[Repair] = field(default_factory=list)

    @property
    def widenable(self) -> list[Repair]:
        return [r for r in self.repairs if r.verdict == "widenable"]

    def summary(self) -> str:
        n = len(self.repairs)
        w = len(self.widenable)
        return (f"{w}/{n} repairable by widening; "
                f"{n - w}/{n} need a canonical machine, a re-read, or a retraction")


def price_all(a: dict, b: dict) -> Bill:
    shared = [k for k in a["claims"] if k in b["claims"]]
    return Bill([price(a["claims"][k], b["claims"][k], k) for k in shared])


def report(bill: Bill, margin: float = 0.10) -> str:
    rows = [
        f"{'claim':<28} {'kind':<12} {'verdict':<34} {'cost':>12} "
        f"{f'x@{margin:.0%}margin':>14}",
    ]
    for r in bill.repairs:
        if r.kind == "band":
            cost = f"x{r.widen_factor:.3f}"
            atm = f"x{r.widen_factor_for_margin(margin):.3f}"
        elif r.kind == "threshold":
            cost = f"->{r.repaired_threshold:.5g}"
            atm = ("n/a" if r.effect_retained is None
                   else f"{r.effect_retained:.1%} kept")
        else:
            cost, atm = "n/a", "n/a"
        rows.append(f"{r.claim:<28} {r.kind:<12} {r.verdict:<34} {cost:>12} {atm:>14}")
    rows += ["", bill.summary()]
    for r in bill.repairs:
        rows.append(f"  {r.claim}: {r.note}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("calibrated", help="measurement JSON from the calibrated arm")
    ap.add_argument("other", help="measurement JSON from the arm that fails")
    ap.add_argument("--margin", type=float, default=0.10,
                    help="residual margin to price the widening at (default 0.10)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args(argv)

    with open(args.calibrated) as fa, open(args.other) as fb:
        bill = price_all(json.load(fa), json.load(fb))

    if args.json:
        payload: list[dict[str, Any]] = [
            {**vars(r), "widen_at_margin": r.widen_factor_for_margin(args.margin)}
            for r in bill.repairs
        ]
        print(json.dumps({"repairs": payload, "summary": bill.summary()},
                         indent=2, sort_keys=True))
    else:
        print(report(bill, margin=args.margin))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
