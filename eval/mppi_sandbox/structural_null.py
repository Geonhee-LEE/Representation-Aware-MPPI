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


# ==========================================================================
# The walk. The screen above says the comparison is well-posed; everything
# below is what happened when it was actually spent.
# ==========================================================================

#: The rung, chosen for the same reason D-167 chose it: convoy `w = 75` is the
#: population's **largest** effect (`A = 1.0000`, the arms' clearance ranges
#: disjoint over 32 seeds). A null that reproduces the branch's most separated
#: rung is answering the attribution question there or nowhere.
FROZEN_SCENARIO = "cafe_convoy_v0.yaml"
FROZEN_LAM = 0.8
FROZEN_WEIGHT = 75.0
FROZEN_MARGIN = 0.30

#: Q-123's gating measurement, walked 2026-08-10 09:00: 8 seeds of
#: `frozen_risk_mppi` at the rung above. Per D-163 the 8-seed licence is the
#: **permissive** one, so this read was usable for refutation only — and it did
#: not refute: median ESS **108.61** against the risk arm's 105.07 on the same
#: ensemble, `8/8` in band, `8/8` at goal. Recorded because the next constant
#: is what the same arm did at 32 seeds, and the pair is the reading.
FROZEN_PREREAD: dict[str, object] = {
    "n": 8, "median_ess": 108.6052, "n_in_band": 8, "n_reached": 8,
    "risk_median_ess": 105.0715,
}

#: The 32-seed walk. Seeds 0–31 in order, same `(scenario, λ, weight)`, so
#: these pair positionally with `scene_transplant.CONVOY_W75_CLEARANCES`.
FROZEN_W75_CLEARANCES: tuple[float, ...] = (
    1.1479, 1.1128, 1.2007, 1.0724, 1.2251, 1.0565, 1.1518, 1.1261,
    1.0454, 1.1627, 1.0681, 1.1175, 1.1814, 1.1402, 1.0760, 1.0773,
    1.0162, 1.1407, 1.0297, 1.0560, 1.1318, 1.1584, 1.1682, 1.1478,
    1.1856, 1.0326, 1.0611, 1.1436, 1.1783, 1.0013, 1.0937, 1.0799,
)

#: Per-seed median ESS on the same walk. Carried per seed rather than as an
#: arm median because :attr:`StructuralRung.refusal_side` is a statement about
#: *which* seeds refused and on which side of the band — a question an arm
#: median cannot answer, and the one that turns out to matter here.
FROZEN_W75_ESS: tuple[float, ...] = (
    109.78, 108.70, 23.09, 102.96, 108.51, 111.90, 113.63, 32.95,
    11.78, 35.11, 23.38, 85.61, 117.62, 90.21, 70.59, 102.79,
    63.65, 97.93, 81.72, 109.27, 114.82, 106.90, 72.43, 111.67,
    55.84, 114.21, 32.40, 111.86, 106.88, 53.81, 18.52, 36.17,
)

#: `ab.ess_band(256)`, inlined so this module keeps importing no `ab` — every
#: quantity here is a recorded float. Pinned against the live function by test.
FROZEN_ESS_BAND: tuple[float, float] = (12.8, 128.0)

#: The refusal happened; this names which end of the band it happened at.
REFUSAL_AT_FLOOR = "REFUSAL_AT_FLOOR"
REFUSAL_AT_CEILING = "REFUSAL_AT_CEILING"
REFUSAL_BOTH_SIDES = "REFUSAL_BOTH_SIDES"
NO_REFUSAL = "NO_REFUSAL"

#: The side the controller docstring **predicted**. Its argument: a max over
#: `predict_samples` blobs covers more cells at value ≥ any single sample's, so
#: the frozen arm's cost is pointwise ≤ the risk arm's, its softmax flatter,
#: its ESS *higher* — which refuses at the ceiling. Named as a constant so the
#: prediction and the measurement are two objects that can disagree.
PREDICTED_REFUSAL_SIDE = REFUSAL_AT_CEILING

#: The prediction held: the arm refused, on the side the pointwise-≤ argument
#: says it must.
PRICE_PAID_AS_PREDICTED = "PRICE_PAID_AS_PREDICTED"

#: The arm refused — so the price named in the docstring is real — but on the
#: **other** side, which means the pointwise-≤ argument is not the mechanism
#: that charged it. A prediction that is right about the bill and wrong about
#: the reason is worth separating from one that is right about both, because
#: only the second licenses using the argument on the next arm.
PRICE_PAID_OTHER_SIDE = "PRICE_PAID_OTHER_SIDE"

#: No refusal at all; the price was not charged on this rung.
PRICE_UNPAID = "PRICE_UNPAID"

#: The cheap read passed and the expensive one refused — D-163's direction,
#: recorded a third time (crossing's `WINDOW_SHIFTED`, `geometric_null`'s
#: `w_geom = 5.0`, and now this). Not a defect of either measurement: it is
#: what "the 8-seed licence is permissive" *means*, stated as a reading so the
#: branch stops re-learning it by surprise.
LICENCE_PERMISSIVE = "LICENCE_PERMISSIVE"

#: Both seed counts agree. Says nothing about whether 8 would have caught a
#: refusal — only that there was none to catch.
LICENCE_CONCORDANT = "LICENCE_CONCORDANT"

#: The cheap read refused and the expensive one did not. Never observed on this
#: branch, and it is the direction D-163's licence forbids relying on; kept so
#: the reading is total rather than two-valued-by-luck.
LICENCE_CONSERVATIVE = "LICENCE_CONSERVATIVE"

#: Head-to-head verdicts. Deliberately *not* `geometric_null`'s names: that
#: module asks "does the representation beat geometry", this one asks the
#: narrower question "does the **motion model** beat the same channel frozen at
#: `t₀`", and reusing the names would let a reader carry one answer to the
#: other question.
PREDICTION_ADDS = "PREDICTION_ADDS"
PREDICTION_INERT = "PREDICTION_INERT"
PREDICTION_HURTS = "PREDICTION_HURTS"
BOTH_INERT = "BOTH_INERT"

#: The walk is inadmissible, so no head-to-head verdict is taken from it. The
#: same refusal `geometric_null.NULL_INADMISSIBLE` names, kept separate because
#: here it is **uncalibratable**: there is no coefficient whose adjustment
#: could move the refusing seed back into the band.
WALK_INADMISSIBLE = "WALK_INADMISSIBLE"


@dataclass(frozen=True)
class StructuralRung:
    """One structural-null walk, carried with the arms it is paired to.

    Shaped after :class:`geometric_null.NullRung` and short one field: there is
    no `w_geom`, which is the entire point of the construction. The recorded
    arms are reused rather than re-run, so this rung shares a denominator with
    :func:`margin_free.census` exactly as the geometric one does.
    """

    scenario: str
    lam: float
    weight: float
    margin: float
    clearances: tuple[float, ...]
    #: Per-seed median ESS, same ordering as :attr:`clearances`.
    ess: tuple[float, ...]
    band: tuple[float, float]
    n_reached: int
    #: The 8-seed pre-read's `n_in_band`, or `None` if none was taken.
    preread_in_band: int | None = None
    preread_n: int | None = None
    #: The recorded arms, keyed `stock_mppi` / `risk_mppi`.
    recorded: dict[str, tuple[float, ...]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if len(self.ess) != len(self.clearances):
            raise ValueError(
                f"{len(self.clearances)} clearances against {len(self.ess)} "
                "ESS readings — both are per-seed and positionally paired, so "
                "unequal lengths mean the pairing is not what this class "
                "assumes")

    @property
    def n(self) -> int:
        return len(self.clearances)

    @property
    def n_in_band(self) -> int:
        lo, hi = self.band
        return sum(1 for e in self.ess if lo <= e <= hi)

    @property
    def admissible(self) -> bool:
        """Every seed at goal **and** every seed in band.

        All-seeds, not most-seeds — the rule every walk on this branch is held
        to (`ab.assert_ess_in_band`), and the one that refused head_on `w = 75`
        at 31/32. Applying it here costs the branch its best-looking number,
        which is the only circumstance under which a rule is worth anything.
        """
        return self.n_reached == self.n and self.n_in_band == self.n

    @property
    def refusal_side(self) -> str:
        lo, hi = self.band
        below = any(e < lo for e in self.ess)
        above = any(e > hi for e in self.ess)
        if below and above:
            return REFUSAL_BOTH_SIDES
        if below:
            return REFUSAL_AT_FLOOR
        if above:
            return REFUSAL_AT_CEILING
        return NO_REFUSAL

    @property
    def price_direction(self) -> str:
        """Is the docstring's predicted failure mode the one that fired?

        Measured `REFUSAL_AT_FLOOR` against a predicted ceiling. So the arm is
        *not* uniformly flatter: its median ESS does drop below the risk arm's
        over 32 seeds (94.07 vs 105.07), and the single refusing seed is too
        **peaked**, not too flat. The pointwise-≤ cost argument is sound about
        the cost and does not carry to the softmax, because ESS is a property
        of the cost *spread* across rollouts and a uniformly smaller cost can
        be more sharply spread.
        """
        side = self.refusal_side
        if side == NO_REFUSAL:
            return PRICE_UNPAID
        return (PRICE_PAID_AS_PREDICTED if side == PREDICTED_REFUSAL_SIDE
                else PRICE_PAID_OTHER_SIDE)

    @property
    def seed_licence(self) -> str | None:
        """How the cheap read and the walk compare. `None` if no pre-read."""
        if self.preread_in_band is None or self.preread_n is None:
            return None
        cheap_ok = self.preread_in_band == self.preread_n
        walk_ok = self.n_in_band == self.n
        if cheap_ok and not walk_ok:
            return LICENCE_PERMISSIVE
        if walk_ok and not cheap_ok:
            return LICENCE_CONSERVATIVE
        return LICENCE_CONCORDANT

    def _comparison(self, a: tuple[float, ...], b: tuple[float, ...],
                    censoring: str):
        from .margin_free import RungComparison
        return RungComparison(scenario=self.scenario, weight=self.weight,
                              declared_margin=self.margin, censoring=censoring,
                              stock=a, risk=b)

    def versus_stock(self):
        """The frozen null against stock. Does the channel move clearance at
        all once its motion model is gone?"""
        return self._comparison(self.recorded["stock_mppi"], self.clearances,
                                "STRUCTURAL_NULL_VS_STOCK")

    def mechanism_versus_stock(self):
        """The recorded risk arm against stock, rebuilt from the constants the
        census reads rather than quoted from a journal."""
        return self._comparison(self.recorded["stock_mppi"],
                                self.recorded["risk_mppi"],
                                "MECHANISM_VS_STOCK")

    def versus_frozen(self):
        """Risk against the frozen null, paired by seed. The comparison a
        verdict would be taken from — if this rung were admissible."""
        return self._comparison(self.clearances, self.recorded["risk_mppi"],
                                "MECHANISM_VS_STRUCTURAL_NULL")

    @property
    def residual_share(self) -> float:
        """`1 − Δ(risk − frozen) / Δ(risk − stock)` — the fraction of the
        mechanism's clearance gain the **frozen** arm reproduces.

        A number, not a verdict: :attr:`verdict` refuses this rung, and this
        property is readable anyway for the same reason
        :data:`geometric_null.LOUDER_NULL` is kept — "the residual is X at the
        admissible rung" and "the residual is stable" are different claims, and
        hiding the refused rung is what makes a reader infer the second from
        the first.
        """
        total = self.mechanism_versus_stock().paired_delta
        if total == 0.0:
            raise ZeroDivisionError(
                "the mechanism has no gain over stock on this rung, so there "
                "is no share of it to attribute — read `versus_stock` instead")
        return 1.0 - self.versus_frozen().paired_delta / total

    def verdict(self, *, inert_effect: float = 0.10) -> str:
        if not self.admissible:
            return WALK_INADMISSIBLE
        null, mech, head = (self.versus_stock(), self.mechanism_versus_stock(),
                            self.versus_frozen())
        if null.effect < inert_effect and mech.effect < inert_effect:
            return BOTH_INERT
        if head.effect < inert_effect:
            return PREDICTION_INERT
        return PREDICTION_ADDS if head.superiority > 0.5 else PREDICTION_HURTS

    def __str__(self) -> str:  # pragma: no cover - formatting
        return (f"{self.scenario} w={self.weight:g} :: {self.verdict()} "
                f"[{self.refusal_side}/{self.price_direction}] "
                f"in_band={self.n_in_band}/{self.n} "
                f"residual_share={self.residual_share:.4f}")


def convoy_w75_frozen() -> StructuralRung:
    """The walked rung. Refused at 31/32, and the refusal has no knob."""
    from .scene_transplant import CONVOY_W75_CLEARANCES
    return StructuralRung(
        scenario=FROZEN_SCENARIO, lam=FROZEN_LAM, weight=FROZEN_WEIGHT,
        margin=FROZEN_MARGIN, clearances=FROZEN_W75_CLEARANCES,
        ess=FROZEN_W75_ESS, band=FROZEN_ESS_BAND, n_reached=32,
        preread_in_band=int(FROZEN_PREREAD["n_in_band"]),  # type: ignore[arg-type]
        preread_n=int(FROZEN_PREREAD["n"]),  # type: ignore[arg-type]
        recorded=CONVOY_W75_CLEARANCES)
