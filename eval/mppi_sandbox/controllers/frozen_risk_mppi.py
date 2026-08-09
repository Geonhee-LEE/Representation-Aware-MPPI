# SPDX-License-Identifier: BSD-3-Clause
"""The **structural null arm** — `RiskMPPI` minus the motion model, same weight.

:mod:`controllers.geometric_mppi` is the branch's *calibrated* null: it removes
the representation and puts a differently-shaped term in the same slot, which
buys a new coefficient (`w_geom`) that then has to be matched to the risk arm
somehow. Two matching criteria have been walked and both failed — ESS-matching
does not identify the verdict (D-169/D-170), gain-matching determines it
(D-171). The failures are symmetric enough to indict the *form*.

This arm is the other move: keep the term, keep its coefficient, and remove the
representation's **input**.

    RiskMPPI(producer=GTBevProducer(...))      ← anticipated sweep over t₀..t₀+3s
    FrozenRiskMPPI(producer=FrozenBevProducer) ← the same blob at t₀ only

Everything downstream of the producer is the same object: the same
`w_risk = 40.0`, the same `RiskInflationCritic` / `ShadowCostCritic` /
`ObservationValueCritic` defaults, the same `_extra_cost` summation, the same
DYNAMIC channel index. `FrozenRiskMPPI` overrides **only** which producer is
constructed, and inherits `RiskMPPI.command` / `_extra_cost` verbatim so the
two arms cannot drift apart in the consuming path.

Why that matters for the verdict
---------------------------------

There is no coefficient to calibrate, so the question "at what loudness is this
null a fair comparison?" — the question both prior criteria existed to answer,
and the one both answered badly — is **not posed**. `structural_null`
verifies the parity mechanically rather than trusting this docstring.

The ablation invariant is inherited and still holds: `w_risk = 0` (with the
critic weights at their zero defaults) makes this byte-identical to
`stock_mppi`, exactly as it does for `RiskMPPI`, because the producer is never
even rendered when no consumer is active.

What it costs
--------------

The frozen arm is **quieter** at equal `w_risk`: `GTBevProducer`'s DYNAMIC row
is a max over `predict_samples` blobs along the sweep, this one is a single
blob, and a max over ten samples of a moving obstacle covers more cells at
value ≥ any single sample's. So the frozen arm's `_extra_cost` is
pointwise ≤ the risk arm's on a moving scene, its softmax is correspondingly
flatter, and `ab.ess_band` may refuse the rung with **no knob to fix it** —
which is the price of not having a knob to mis-set. Refusal is then a fact
about the ablation, not a calibration failure, and it is reported as such.
"""

from __future__ import annotations

from ..representations import FrozenBevProducer
from .risk_mppi import RiskMPPI


class FrozenRiskMPPI(RiskMPPI):
    """`RiskMPPI` with a :class:`FrozenBevProducer`. No other difference."""

    def __init__(self, scenario, seed: int = 0, *, blob_scale: float = 1.5,
                 producer=None, **kwargs):
        # `producer` stays overridable so a test can inject a stub, but the
        # default is the frozen one — that default *is* the ablation.
        super().__init__(
            scenario, seed=seed, blob_scale=blob_scale,
            producer=(producer if producer is not None
                      else FrozenBevProducer(scenario.obstacles,
                                             blob_scale=blob_scale)),
            **kwargs)
