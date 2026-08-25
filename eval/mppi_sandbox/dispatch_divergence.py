"""Measure *how far apart* the two SIMD dispatches land, not merely that they differ.

D-033 established the coordinate: with numpy held at 1.26.4, masking AVX-512 off
via ``NPY_DISABLE_CPU_FEATURES`` reproduces the GitHub runner's failure value to
all 17 digits.  What it did **not** establish is the magnitude of the split, and
the natural reading of "FP drift amplified past a threshold" is that the two
machines straddle a knife edge — that the constants are *almost* right on AVX2
and a slightly looser tolerance would cover both.

That reading has a cheap decisive test, because the acceptance interval of every
contested claim is written down in its own assertion.  For each of the five
tests that flip, this module recomputes the contested scalar and reports it
against that interval, so the split can be stated as a **relative excursion**
(how far outside, as a fraction of the interval's own half-width) rather than as
a pass/fail.  A knife edge gives excursions just over 1.0.  Anything much larger
means the two dispatches are not two noisy reads of one quantity — they are two
different measurements, and no tolerance honest enough to admit both would be
tight enough to assert anything (Q-055).

Run it on both arms of the same box::

    python3 -m eval.mppi_sandbox.dispatch_divergence --out /tmp/avx512.json
    NPY_DISABLE_CPU_FEATURES=AVX512F,AVX512CD,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL \\
        python3 -m eval.mppi_sandbox.dispatch_divergence --out /tmp/avx2.json
    python3 -m eval.mppi_sandbox.dispatch_divergence --compare /tmp/avx512.json /tmp/avx2.json

**Every statistic is computed by calling the test module's own helpers.**  A
second copy of the call sequence would be free to drift away from the assertion
it claims to characterise — the same failure mode D-028 avoided by deriving the
weight's effect from the real ``_cost`` rather than re-implementing it.  The
cost is an import of the test package, which is deliberate: this file measures
those tests and nothing else.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True)
class Claim:
    """One contested scalar, with the acceptance interval its test asserts."""

    test: str
    #: what the number means, in one line
    quantity: str
    value: float
    #: closed acceptance interval, as the assertion states it.  ``None`` on a
    #: side means the assertion is one-sided.
    lo: float | None
    hi: float | None
    #: True when the claim is categorical (set equality) rather than a scalar
    #: band -- excursion is then undefined and reported as ``None``.
    categorical: bool = False
    detail: str = ""

    @property
    def passes(self) -> bool:
        if self.lo is not None and self.value < self.lo:
            return False
        if self.hi is not None and self.value > self.hi:
            return False
        return True

    @property
    def excursion(self) -> float | None:
        """Distance outside the interval, in units of its own half-width.

        0.0 inside; 1.0 exactly one half-width outside; ``None`` for one-sided
        or categorical claims, where "half-width" has no meaning.  Reported
        rather than thresholded -- this module measures, it does not judge.
        """
        if self.categorical or self.lo is None or self.hi is None:
            return None
        half = (self.hi - self.lo) / 2.0
        if half <= 0:
            return None
        centre = (self.lo + self.hi) / 2.0
        return max(0.0, (abs(self.value - centre) - half) / half)


def _scale_match_achieved_ratio() -> Claim:
    """`weight_for_ratio` asks for 0.25; `verify_ratio` says what it got."""
    from .scale_match import verify_ratio, weight_for_ratio
    from .tests import test_scale_match as t

    target = 0.25
    w = weight_for_ratio(t._crossing(), "w_voo", ratio=target, lam=t.LAM_HI)
    got = verify_ratio(t._crossing(), "w_voo", w, lam=t.LAM_HI)
    return Claim(
        test="test_scale_match::test_the_prescribed_weight_achieves_the_requested_ratio",
        quantity="achieved cost-spread ratio for a weight prescribed at 0.25",
        value=float(got),
        lo=target * 0.75, hi=target * 1.25,
        detail=f"prescribed weight w={float(w):.6g}",
    )


def _horizon_weight_swing() -> Claim:
    """How much the scale-matched weight moves over the admissible horizons.

    Only the two rungs the assertion uses are simulated; the fixture's third
    (frozen) rung runs to the full timeout by construction and this statistic
    does not read it.
    """
    from . import horizon_audit as ha
    from . import scale_match
    from .tests import test_horizon_audit as t

    scen = t.load_scenario(t.CROSSING)
    rates = {H: scale_match.exchange_rate(scen, "w_voo", lam=t.LAM, horizon=H)
             for H in (ha.SHIPPED_HORIZON, t.FREE_H)}
    swing = (rates[t.FREE_H].weight_for_ratio(0.25)
             / rates[ha.SHIPPED_HORIZON].weight_for_ratio(0.25))
    return Claim(
        test="test_horizon_audit::test_the_prescribed_weight_moves_with_the_horizon",
        quantity=f"scale-matched w_voo swing over H {ha.SHIPPED_HORIZON}->{t.FREE_H}",
        value=float(swing),
        lo=1.2, hi=None,
        detail="one-sided: the claim is that the weight is NOT horizon-transferable",
    )


def _ab_protocol_overstatement() -> Claim:
    """Single-`lam` clearance gap over the per-arm one — Q-039's effect size."""
    from .tests import test_ab_temperature_protocol as t

    _, _, d_single = t._paired(0.4, 0.4)
    _, _, d_perarm = t._paired(0.8, 1.6)
    single, perarm = float(d_single.mean()), float(d_perarm.mean())
    return Claim(
        test="test_ab_temperature_protocol::test_protocol_moves_the_effect_size_but_not_its_sign",
        quantity="single-lam clearance gap / per-arm clearance gap",
        value=single / perarm,
        lo=1.25, hi=None,
        detail=f"single={single:.6g} m, per-arm={perarm:.6g} m",
    )


def _exposure_band_hi() -> Claim:
    """Widest reportable scene duration ratio vs the declared band ceiling."""
    from . import exposure as exp
    from .tests import test_exposure_timing_band as t

    ratios = {p: t._duration_ratio(p) for p in t._obstacle_scenes()
              if p != t.DEFECT_SCENE}
    hi_declared = exp.TIMING_RATIO_BAND[1]
    worst = max(ratios.values())
    return Claim(
        test="test_exposure_timing_band::test_reportable_scenes_land_inside_the_declared_band",
        quantity="max reportable-scene duration ratio vs TIMING_RATIO_BAND[1]",
        value=float(worst),
        lo=hi_declared - 0.05, hi=hi_declared + 0.05,
        detail=f"argmax={max(ratios, key=ratios.get)}",
    )


def _hazard_shared_rungs() -> Claim:
    """Whether the two arms still share an admissible `lam` rung at all."""
    from . import ab
    from .tests import test_hazard_exposure as t

    scen = t.load_scenario(t.CONVOY_STAGGERED)
    shared = set.intersection(*(
        set(ab.admissible_lams(ab.lam_ladder(scen, c, [0.4], seeds=range(4))))
        for c in ("stock_mppi", "risk_mppi")))
    return Claim(
        test="test_hazard_exposure::test_refutation_reproduces_from_simulation",
        quantity="size of the shared admissible-lam set (expected {0.4}, i.e. 1)",
        value=float(len(shared)),
        lo=1.0, hi=1.0,
        categorical=True,
        detail=f"shared={sorted(shared)}",
    )


#: The five slow tests that flip between AVX-512 and AVX2 (D-033).  Ordered
#: cheapest-first so a truncated run still says something.
CLAIMS: dict[str, Callable[[], Claim]] = {
    "hazard_shared_rungs": _hazard_shared_rungs,
    "scale_match_achieved_ratio": _scale_match_achieved_ratio,
    "ab_protocol_overstatement": _ab_protocol_overstatement,
    "horizon_weight_swing": _horizon_weight_swing,
    "exposure_band_hi": _exposure_band_hi,
}


def dispatch_fingerprint() -> dict[str, Any]:
    """Name the machine the numbers came off, in the report itself.

    Reuses ``eval/conftest.py``'s :func:`simd_found` rather than reading the CPU
    dict a second way.  Two fingerprints that could disagree would be worse than
    none -- the whole point of this file is that the machine identity is the
    load-bearing coordinate, so it gets exactly one definition.
    """
    from eval.conftest import CALIBRATED_NUMPY, CALIBRATED_SIMD, simd_found

    found = list(simd_found())
    return {
        "numpy": np.__version__,
        "numpy_calibrated": np.__version__ == CALIBRATED_NUMPY,
        "simd": found,
        "simd_calibrated": CALIBRATED_SIMD in found,
    }


def measure(only: list[str] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"env": dispatch_fingerprint(), "claims": {}}
    for name, fn in CLAIMS.items():
        if only and name not in only:
            continue
        print(f"  measuring {name} ...", file=sys.stderr, flush=True)
        claim = fn()
        out["claims"][name] = asdict(claim) | {
            "passes": claim.passes, "excursion": claim.excursion}
    return out


def compare(a: dict, b: dict) -> str:
    """Table of the same claim measured on two machines."""
    def _tag(env):
        return (f"numpy {env['numpy']}  "
                f"AVX512={'yes' if env.get('simd_calibrated') else 'no'}  "
                f"({len(env['simd'])} extensions found)")

    rows = [
        f"A: {_tag(a['env'])}",
        f"B: {_tag(b['env'])}",
        "",
        f"{'claim':<28} {'A':>14} {'B':>14} {'B/A':>8} {'excursion(B)':>13} {'A ok':>5} {'B ok':>5}",
    ]
    for name in a["claims"]:
        if name not in b["claims"]:
            continue
        ca, cb = a["claims"][name], b["claims"][name]
        ratio = (cb["value"] / ca["value"]) if ca["value"] else float("nan")
        exc = cb["excursion"]
        rows.append(
            f"{name:<28} {ca['value']:>14.6g} {cb['value']:>14.6g} "
            f"{ratio:>8.4g} {('n/a' if exc is None else f'{exc:.3g}'):>13} "
            f"{str(ca['passes']):>5} {str(cb['passes']):>5}")
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", help="write the measurement JSON here")
    ap.add_argument("--only", nargs="*", help="measure only these claim keys")
    ap.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"),
                    help="print a two-machine comparison table and exit")
    args = ap.parse_args(argv)

    if args.compare:
        with open(args.compare[0]) as fa, open(args.compare[1]) as fb:
            print(compare(json.load(fa), json.load(fb)))
        return 0

    report = measure(args.only)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
