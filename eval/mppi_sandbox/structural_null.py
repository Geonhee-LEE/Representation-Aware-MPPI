# SPDX-License-Identifier: BSD-3-Clause
"""Is the structural null actually one-variable? The check, not the claim.

:mod:`controllers.frozen_risk_mppi` says in prose that it differs from
:class:`~controllers.risk_mppi.RiskMPPI` in exactly one thing — the producer's
prediction — and in **no** coefficient. That sentence is the entire argument for
why neither D-170's under-identification nor D-171's circularity can arise
here, so it is worth more than a docstring's word.

This module makes it a reading.

Why the parity check is the load-bearing one
---------------------------------------------

D-171's finding was not "gain-matching is a bad criterion". It was that *the
match residual and the verdict statistic are one quantity seen twice* — a
coupling nobody could see from the shipped coefficient, and which only became
visible when it was tested for directly. The lesson that cycle bought, and that
STATE asked the next one to apply, was: **screen the instrument before walking
a ladder in it**, because the screen costs 0 sim runs and the ladder does not.

The structural null's instrument claim is "there is no ladder". The screen for
*that* is coefficient parity: enumerate every scalar the two arms multiply a
cost by, and require the sets to be equal. If they are, the calibration
question is not merely unanswered but **unposed**, and both prior failure modes
are inapplicable by construction rather than by argument. If they are not, this
is a third calibrated null wearing a structural label, and it inherits every
objection the other two collected.

The dual check, and why one without the other proves nothing
--------------------------------------------------------------

Parity alone is satisfied perfectly by comparing an arm to **itself**. So the
screen has two halves and needs both:

- :func:`coefficient_parity` — every cost coefficient equal. Ensures the swap
  is not secretly a calibration.
- :func:`prediction_parity` — the producers differ, and differ *only* in the
  prediction-sample count. Ensures the swap is not secretly a no-op.

A structural ablation is exactly the conjunction: `COEFFICIENTS_SHARED` and
`PREDICTION_REMOVED`. Either alone is a null result about the check itself.

What this module deliberately does not report
-----------------------------------------------

A verdict. The screen says the comparison is *well-posed*; it says nothing
about which arm holds more clearance, and it cannot — no rung has been walked
with this arm yet. The one thing it does predict is a refusal risk with no
remedy: at equal `w_risk` the frozen arm's DYNAMIC row is a single blob where
the risk arm's is a max over `predict_samples` of them, so the frozen cost is
pointwise no larger, its softmax is flatter, and `ab.ess_band` may refuse the
rung. That refusal would be **uncalibratable** by design — see
:data:`LOUDNESS_UNCALIBRATABLE` — and is the price paid for the two failure
modes this construction does not have.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from .controllers.stock_mppi import MPPIParams

#: Arm-level cost coefficients that live on the controller rather than in
#: `MPPIParams`. Each is a scalar the arm multiplies a cost (or a margin) by,
#: so a difference in any of them is a calibration difference — which is the
#: thing a structural ablation claims not to have. Attribute paths are resolved
#: with `getattr` chaining; an arm that lacks one (e.g. `StockMPPI`) reports it
#: as absent rather than as zero, because "no such term" and "term switched
#: off" are different states.
ARM_COEFFICIENTS: tuple[str, ...] = (
    "w_risk",
    "critic.k_margin_per_sigma",
    "critic.delta_max",
    "shadow.w_epist",
    "observation.w_voo",
    "robot_radius",
)

#: The producer field whose value *is* the ablation. One sample means the
#: DYNAMIC channel is rendered at `t₀` only — no motion model.
PREDICTION_FIELD = "n_pred"

#: Named so a later cycle reading an ESS refusal does not diagnose it as a bad
#: coefficient choice and go looking for a better one. There is no coefficient
#: to choose; a refusal here means the ablation is inadmissible on that rung,
#: which is a fact to report rather than a knob to turn.
LOUDNESS_UNCALIBRATABLE = "LOUDNESS_UNCALIBRATABLE"

_ABSENT = object()


def _resolve(obj, path: str):
    cur = obj
    for part in path.split("."):
        cur = getattr(cur, part, _ABSENT)
        if cur is _ABSENT:
            return _ABSENT
    return cur


def _coefficients(arm) -> dict[str, object]:
    """Every scalar `arm` multiplies a cost by, keyed by name.

    Covers both halves: `MPPIParams` (shared sampler/cost weights, including
    `lam` — a temperature difference is a calibration difference too) and
    :data:`ARM_COEFFICIENTS`. Absent attributes are recorded as absent.
    """
    out: dict[str, object] = {}
    for f in dataclasses.fields(MPPIParams):
        out[f"p.{f.name}"] = _resolve(arm, f"p.{f.name}")
    for path in ARM_COEFFICIENTS:
        out[path] = _resolve(arm, path)
    return out


@dataclass(frozen=True)
class ParityReading:
    """Which coefficients differ between two arms, and the verdict."""

    diverged: tuple[str, ...]
    #: `name → (a_value, b_value)` for each diverged coefficient, so a failure
    #: names the number rather than only the field.
    values: dict[str, tuple[object, object]]

    @property
    def shared(self) -> bool:
        return not self.diverged

    @property
    def verdict(self) -> str:
        return "COEFFICIENTS_SHARED" if self.shared else "COEFFICIENTS_DIVERGED"


def coefficient_parity(arm_a, arm_b) -> ParityReading:
    """Do two arms multiply every cost by the same scalars?

    `COEFFICIENTS_SHARED` is the structural null's precondition: it means no
    ladder exists to walk, so D-170's under-identification and D-171's
    circularity — both defects *of a ladder* — cannot be expressed. It is not
    itself evidence that the arms differ at all; pair it with
    :func:`prediction_parity`.
    """
    ca, cb = _coefficients(arm_a), _coefficients(arm_b)
    diverged, values = [], {}
    for name in sorted(set(ca) | set(cb)):
        va, vb = ca.get(name, _ABSENT), cb.get(name, _ABSENT)
        if va is _ABSENT and vb is _ABSENT:
            continue
        if va is _ABSENT or vb is _ABSENT or va != vb:
            diverged.append(name)
            values[name] = (None if va is _ABSENT else va,
                            None if vb is _ABSENT else vb)
    return ParityReading(tuple(diverged), values)


@dataclass(frozen=True)
class PredictionReading:
    """Whether the ablated arm's producer actually dropped the motion model."""

    baseline_samples: int | None
    ablated_samples: int | None
    #: Producer settings other than :data:`PREDICTION_FIELD` that differ. A
    #: non-empty tuple means the producer swap moved more than one variable,
    #: which is the same defect as a coefficient difference wearing a different
    #: hat — the ablation would no longer be attributable to the prediction.
    other_diffs: tuple[str, ...]

    @property
    def verdict(self) -> str:
        if self.baseline_samples is None or self.ablated_samples is None:
            return "NO_PRODUCER"
        if self.other_diffs:
            return "PRODUCER_MULTIVARIATE"
        if self.ablated_samples >= self.baseline_samples:
            return "PREDICTION_PRESENT"
        return "PREDICTION_REMOVED"


#: Producer settings that must match for the swap to be one-variable. Excludes
#: `obstacles` (identity, not a setting) and :data:`PREDICTION_FIELD` (the
#: variable under ablation).
PRODUCER_SETTINGS: tuple[str, ...] = ("n", "res", "r_sense", "blob_scale")


def prediction_parity(baseline_arm, ablated_arm) -> PredictionReading:
    """Did the producer swap remove prediction — and *only* prediction?"""
    pa, pb = getattr(baseline_arm, "producer", None), getattr(
        ablated_arm, "producer", None)
    if pa is None or pb is None:
        return PredictionReading(None, None, ())
    other = tuple(s for s in PRODUCER_SETTINGS
                  if getattr(pa, s, _ABSENT) != getattr(pb, s, _ABSENT))
    return PredictionReading(getattr(pa, PREDICTION_FIELD, None),
                             getattr(pb, PREDICTION_FIELD, None), other)


@dataclass(frozen=True)
class StructuralScreen:
    """The conjunction. Both halves, or the screen has not been passed."""

    parity: ParityReading
    prediction: PredictionReading

    @property
    def well_posed(self) -> bool:
        return (self.parity.verdict == "COEFFICIENTS_SHARED"
                and self.prediction.verdict == "PREDICTION_REMOVED")

    @property
    def verdict(self) -> str:
        return ("STRUCTURAL_ABLATION" if self.well_posed
                else f"{self.parity.verdict}/{self.prediction.verdict}")


def screen(baseline_arm, ablated_arm) -> StructuralScreen:
    """Screen an ablation pair before any rung is walked. Costs 0 sim runs.

    This is D-171's generalised rule applied one step earlier than it was
    written: that cycle checked a *match quantity* for coupling to the verdict
    before walking a ladder in it. Here there is no match quantity, so the
    thing to check before walking is that the claim "no match quantity exists"
    is true of the objects rather than of the prose.
    """
    return StructuralScreen(coefficient_parity(baseline_arm, ablated_arm),
                            prediction_parity(baseline_arm, ablated_arm))
