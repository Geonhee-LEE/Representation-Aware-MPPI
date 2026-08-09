# SPDX-License-Identifier: BSD-3-Clause
"""Does the representation term buy anything **over geometry**? (STATE #1)

D-166 established that the risk arm holds more clearance than stock on 5 of 6
walked rungs, margin-free, across all three eligible scenes — the branch's first
positive reading that no threshold choice can move. STATE's bottleneck is the
immediate successor question and it is an **attribution** question, not a
significance one: *is the epistemic/BEV quantity doing the work, or would any
proximity term do it?*

`research/feed.md`'s 2026-08-09 entry (arxiv 2607.16591) is why that is not
rhetorical. It reports dynamics-model disagreement correlating **0.108 ± 0.014**
with true collision proximity over ~50K states, and — the part with no CI wide
enough to wave off — a **33 pp** substitution gap: at matched λ and paired seeds
in the same one-variable cost slot, plain **min-lidar** collides 1% where
dynamics-uncertainty collides 34%. Its own note is the sharp one: min-lidar
winning is not a representation result, it is the geometric baseline available
with no learning at all, *which is precisely why it is the arm this project has
not run*.

:mod:`controllers.geometric_mppi` is that arm. This module grades it.

Why the head-to-head, not two comparisons against stock
-------------------------------------------------------

The obvious read is to compute `A(risk vs stock)` and `A(geom vs stock)` and
compare the two numbers. :func:`versus_stock` and :func:`mechanism_versus_stock`
report exactly those, because they are the two the branch's prior work is
denominated in — but the **verdict** is taken from :func:`versus_geometry`,
which puts the two arms directly against each other on the same seeds.

The reason is pairing. Both arms were walked on seeds 0–31 of one scene at one
`(λ, w_obs_soft, margin)`, so seed `i` is one seed's *three* outcomes and the
risk−geom difference is paired exactly as the risk−stock one is. Comparing two
`A`-values against a shared third arm throws that pairing away and cannot
produce a CI on the difference that matters; the head-to-head keeps it and
:meth:`margin_free.RungComparison.equivalence` can then return `EQUIVALENT` —
"indistinguishable at effect size ε" — which is the verdict this question most
plausibly deserves and which no pair of separate `A`s can express.

What a tie would and would not mean
-----------------------------------

If the two arms are indistinguishable, the honest statement is **not** "the
representation is worthless". It is that on this scene, at this rung, the
clearance ordering the branch has been reporting is reproduced by a term
carrying no learned channel, no motion model, and no uncertainty estimate —
i.e. the positive result is not *attributable* to the representation until a
scene is found where the two arms part. That is a strictly weaker claim than
2607.16591's and it is the one these runs can support.

The coefficient caveat in :mod:`controllers.geometric_mppi` bounds the other
direction and is load-bearing: `w_geom = w_risk` is a shape argument, not a
measured scale match, so a null arm that **loses** may merely be quieter. A null
arm that ties or wins is not exposed to that objection.

The shape argument is measurably wrong, and that is the first finding
---------------------------------------------------------------------

The controller docstring's defence of `w_geom = w_risk = 40.0` — both summands
peak at 1.0 at contact and decay — was walked first and **refused**. At the
recorded rung's own λ = 0.8 the null's softmax runs at median ESS **12.40**
against the risk arm's **105.07** and stock's **109.77**, i.e. 4/8 seeds outside
`ab.ess_band`, and a λ ladder finds **no shared admissible temperature**: stock
and risk are admissible only at λ = 0.8 (8/8), where the null is not, and the
null's best rung is λ = 1.6 (7/8), where stock is 1/8 and risk 0/8. Equal
coefficient is **not** equal loudness, so the one-variable swap as first written
was a two-variable one — the term *and* the sampler's operating point.

The null is therefore calibrated by the sampler's own response instead: hold
λ = 0.8 (the rung's temperature, unchanged for all three arms) and pick the
`w_geom` whose median ESS lands on the risk arm's. That is a stricter match than
`scale_match`'s cost-ratio, not a weaker one — it equalises the quantity the
comparison is actually sensitive to.

The measured answer
-------------------

At the ESS-matched null (`w_geom = 2.5`, 32/32 seeds in band, 32/32 reached):

===================  ========  ==================  ======================
comparison           `A`       paired Δ (m)        95% CI
===================  ========  ==================  ======================
risk vs stock        1.0000    +0.1480             [+0.1324, +0.1627]
**geom vs stock**    0.9868    **+0.1143**         [+0.1002, +0.1301]
**risk vs geom**     0.6953    **+0.0337**         [+0.0161, +0.0505]
===================  ========  ==================  ======================

So the verdict is :data:`REPRESENTATION_ADDS` — the head-to-head CI excludes
zero — and the honest headline is the **share**: a term with no learned channel,
no motion model and no uncertainty estimate reproduces **77%**
(:attr:`Attribution.residual_share`) of the clearance gain the branch has been
attributing to the representation, on the population's most separated rung.
D-166's `A = 1.0000` for risk-vs-stock is matched by geometry at `A = 0.9868`.

And the residual does not survive turning the null up one rung. At
`w_geom = 5.0` the null recovers **91%** (Δ = +0.1351) and the head-to-head
reads `EQUIVALENT` at ε = 0.05 m with CI `[-0.0073, +0.0337]` ∋ 0. That rung is
**refused** — 32-seed ESS is out of band, and :data:`LOUDER_NULL` records it as
data the verdict does not consume — but a residual that is 23% at one admissible
coefficient and indistinguishable one rung up is not a stable 23%.

The 8-seed licence bit again, in the direction D-163 recorded: `w_geom = 5.0`
was admissible on 8 seeds (8/8 in band) and **inadmissible** on 32. The cheap
measurement is the permissive one, twice now.

The census, and why the second rung does not join it
----------------------------------------------------

That reading exists on **one rung of one scene**, and STATE's successor
question is whether the 23% is a property of the rung or of the scene. So the
rung is a record (:class:`NullRung`) rather than a set of module constants, and
the verdict is taken over a :class:`NullCensus` — which reports **coverage
first**, against :func:`margin_free.census`'s six walked rungs, because a
verdict over a subset that does not name the subset is D-107's shape.

The second rung was walked 2026-08-10 03:00: `cafe_head_on_v0` at
`w_obs_soft = 75`, the first attempt on a **different scene**. It is refused,
twice over, and neither refusal is about the answer being unwelcome:

1. **31/32 seeds in band.** Every seed reached the goal; seed 25's softmax ran
   at ESS **134.15** against a band of `[12.8, 128.0]`. `assert_ess_in_band` is
   all-seeds, so this is the same rule that refused :data:`LOUDER_NULL`,
   applied to a rung whose numbers would have been convenient. The direction
   matters and it is the unhelpful one: **above** the band is a softmax too
   near uniform — the term too *quiet* to rank rollouts, not too loud.
2. **The calibration does not identify a coefficient on this scene.** The
   `w_geom` ladder `{1, 2, 2.5, 4, 8}` moves the sampler's median ESS from
   115.86 to 115.64 — a span of **0.19%** of the risk arm's 115.90. D-167 picks
   `w_geom` by landing the null's ESS on the risk arm's; here every candidate
   lands there, so the pick (`w_geom = 2.0`) is the ladder's spacing and not a
   measurement. :attr:`NullRung.coefficient_identification` reads `FLAT`.

The refused numbers point the **other way**, which is exactly why they are kept
and exactly why they are not quoted as a result: `residual_share = 0.0485`
against convoy's `0.7725`. Geometry reproduces 77% of the gain on one scene and
5% on the other. Both cannot be *the* residual — but a `FLAT` calibration is
the condition under which "the null lost because it is quieter" cannot be
excluded, and that is the objection this arm was built to be immune to. So the
census still reads :data:`SINGLE_RUNG` at **1/6**, and STATE's question is
live, not answered.
"""

from __future__ import annotations

from dataclasses import dataclass

from .margin_free import RungComparison
from .scene_transplant import (CONVOY_LAM, CONVOY_MARGIN, CONVOY_SCENARIO,
                               CONVOY_W75_CLEARANCES, CONVOY_WEIGHT)
from .separation_reproduction import W75_CLEARANCES as _HEADON_W75_RECORDED


def _mean(xs) -> float:
    """Plain arithmetic mean. Local so this module keeps importing no numpy —
    every quantity here is a length-16/32 tuple of recorded floats."""
    xs = tuple(xs)
    return sum(xs) / len(xs)

#: The rung the null was walked at. Chosen as convoy `w = 75` because D-166
#: ranks it the population's **largest** effect — `A = 1.0000`, the two arms'
#: clearance ranges disjoint over 32 seeds. If geometry reproduces the branch's
#: single most separated rung, the attribution question is answered there or
#: nowhere; a tie on a rung that barely separates would say much less.
NULL_SCENARIO = CONVOY_SCENARIO
NULL_LAM = CONVOY_LAM
NULL_WEIGHT = CONVOY_WEIGHT
NULL_MARGIN = CONVOY_MARGIN

#: `w_geom`, calibrated by the sampler's response rather than by matching
#: `RiskMPPI`'s shipped `w_risk = 40.0` numerically — see the module docstring.
#: At λ = 0.8 this arm's median ESS is 86.08 over 32 seeds against the risk
#: arm's 105.07 and stock's 109.77, all three inside `ab.ess_band(256)`.
NULL_W_GEOM = 2.5

#: The λ ladder that refused the equal-coefficient swap, `n_in_band / 8` at
#: `w_obs_soft = 75` on `cafe_convoy_v0`. Kept as data because the *absence*
#: of a shared admissible column is the reason this module calibrates at all,
#: and a claim that reads "no shared λ exists" should carry the rungs it was
#: read off. Every rung had all 8 seeds reach the goal, so these are
#: temperature refusals and not completion ones.
LAM_LADDER: dict[float, dict[str, int]] = {
    0.4: {"stock_mppi": 0, "risk_mppi": 0, "geometric_mppi": 0},
    0.8: {"stock_mppi": 8, "risk_mppi": 8, "geometric_mppi": 4},
    1.6: {"stock_mppi": 1, "risk_mppi": 0, "geometric_mppi": 7},
    3.0: {"stock_mppi": 0, "risk_mppi": 0, "geometric_mppi": 3},
    6.0: {"stock_mppi": 0, "risk_mppi": 0, "geometric_mppi": 3},
}

#: `w_geom = 40.0` — the equal-coefficient swap the controller docstring
#: argued for and the ladder above refused. Named so the refusal is citable.
EQUAL_COEFFICIENT_W_GEOM = 40.0

#: Walked 2026-08-10 02:00: `cafe_convoy_v0`, λ = 0.8, `w_obs_soft = 75`,
#: `w_geom = 2.5`, seeds 0–31 in order. Admissibility in
#: :data:`NULL_ADMISSIBILITY` — read it before reading these.
NULL_CLEARANCES: tuple[float, ...] = (
    1.0947, 1.1030, 1.0960, 1.0539, 1.1164, 1.0567, 1.1334, 1.0890,
    1.0458, 1.1335, 1.0822, 1.0791, 1.0953, 1.0321, 1.1020, 1.1009,
    1.0940, 1.0709, 1.0119, 1.0253, 1.1007, 1.0857, 1.1477, 1.1090,
    1.1137, 1.0828, 1.0540, 1.1629, 1.1093, 0.9821, 1.1521, 1.0119,
)

#: The null walk's own admissibility, in the two terms the branch refuses on:
#: every seed reached the goal, and every seed's softmax sat inside
#: `ab.ess_band`. Recorded as data rather than asserted in prose because
#: :func:`attribution` **refuses to grade** when either is false — an arm that
#: did not drive or was sampled at a bad temperature produces a verdict about
#: the run, wearing the mechanism's name (`scorable_band`'s `ESS_OUT_OF_BAND`
#: rule, one arm over).
NULL_ADMISSIBILITY: dict[str, bool] = {"all_reached": True,
                                       "ess_in_band": True}

#: The same walk one coefficient rung up (`w_geom = 5.0`), where the null
#: recovers 91% of the mechanism's gain and the head-to-head reads
#: `EQUIVALENT`. **Refused**: 8/8 seeds were in band on the calibration
#: ensemble and 32/32 were not on the walk, so `ess_in_band` is False and
#: :func:`attribution` never reads these. Kept because "the residual is 23% at
#: the admissible coefficient" and "the residual is stable" are different
#: claims and only the first is measured; a reader who is shown the first
#: without this rung would reasonably infer the second.
LOUDER_NULL: dict[str, object] = {
    "w_geom": 5.0,
    "all_reached": True,
    "ess_in_band": False,
    "median_ess": 80.31,
    "clearances": (
        1.1411, 1.0695, 1.2025, 1.0775, 1.1870, 1.1044, 1.1671, 1.0942,
        1.0172, 1.1078, 1.0688, 1.0987, 1.0997, 1.1079, 1.0878, 1.1604,
        1.0973, 1.1529, 1.0247, 1.0389, 1.1529, 1.0967, 1.1107, 1.1170,
        1.1040, 1.0626, 1.0630, 1.0964, 1.1394, 1.0529, 1.1732, 1.1189,
    ),
}

#: The null walk was not admissible, so no attribution verdict is taken. Named
#: rather than folded into a tie because "the arms are indistinguishable" and
#: "one arm's runs are inadmissible" are opposite epistemic states and an
#: empty-denominator reading that looks like a verdict is D-107's shape
#: (D-107 / D-120 / D-127 / D-145 / D-150 / D-151 / D-158).
NULL_INADMISSIBLE = "NULL_INADMISSIBLE"

#: Neither arm separates from stock — there is no effect for either to own, so
#: the attribution question has no content on this rung.
BOTH_INERT = "BOTH_INERT"

#: The two arms are indistinguishable head-to-head at the stated ε, and the
#: geometric arm does separate from stock. The branch's clearance result is
#: **reproduced without the representation**, so it is not attributable to it
#: on this rung.
GEOMETRY_SUFFICES = "GEOMETRY_SUFFICES"

#: The risk arm holds strictly more clearance than the geometric null
#: head-to-head. The representation buys something geometry does not — the
#: only verdict here that supports the branch's premise.
REPRESENTATION_ADDS = "REPRESENTATION_ADDS"

#: The geometric null holds strictly more clearance than the risk arm — the
#: direction 2607.16591 predicts. Note the coefficient caveat cuts the *other*
#: way here and so does not soften this reading.
GEOMETRY_WINS = "GEOMETRY_WINS"


#: Below this fraction, the median-ESS ladder is called **flat**: the whole
#: `w_geom` ladder moves the sampler's ESS by less than 10% of the arm the null
#: is matched to, so "the coefficient that matches the risk arm's ESS" names a
#: range rather than a value. Stated here rather than inlined so the reading
#: can be re-taken at another tolerance without editing the verdict logic —
#: `Attribution.inert_effect`'s convention, one level down.
FLAT_ESS_RESPONSE = 0.10

#: More than one attribution verdict is reachable across the rung's own
#: `w_geom` ladder, so the verdict is a **free parameter** and not a reading.
#:
#: This is the state D-169 measured on `cafe_head_on_v0` and it is strictly
#: stronger than :data:`FLAT_ESS_RESPONSE`'s caveat. `FLAT` says the criterion
#: failed to pin a coefficient; that is only a *problem* if the unpinned range
#: changes the answer, which nobody had checked. Here it does — the whole span
#: :data:`REPRESENTATION_ADDS` → :data:`GEOMETRY_SUFFICES` → :data:`GEOMETRY_WINS`
#: is reachable — so the rung is refused for a reason that no further seeds fix.
VERDICT_UNIDENTIFIED = "VERDICT_UNIDENTIFIED"


@dataclass(frozen=True)
class NullRung:
    """One rung's geometric-null walk, carried with the arms it is paired to.

    The module shipped with D-167 read a single rung off module constants, so
    "run the null on another rung" meant editing the verdict logic. The rung is
    a **record** here instead, and the constants above are one instance of it
    (:data:`CONVOY_W75_NULL`) rather than the only rung expressible.

    `stock` and `risk` are the recorded arms at the same `(scenario, λ, weight)`
    — not re-run for this comparison. That is the whole reason a rung costs one
    calibration plus one walk: two thirds of every head-to-head is already on
    disk, and reusing it is also what keeps this census sharing a denominator
    with :func:`margin_free.census`.
    """

    scenario: str
    lam: float
    weight: float
    margin: float
    #: The ESS-calibrated coefficient this walk was taken at. Per rung, never
    #: transported: λ is calibrated per scene (D-160) and the null's loudness
    #: is calibrated against *this* rung's risk arm, so a `w_geom` from one
    #: rung is not evidence about another.
    w_geom: float
    clearances: tuple[float, ...]
    all_reached: bool
    ess_in_band: bool
    #: The recorded arms, keyed `stock_mppi` / `risk_mppi`.
    recorded: dict[str, tuple[float, ...]]
    #: `w_geom → median ESS` over the calibration ensemble, and the risk arm's
    #: median ESS on the same ensemble. Both `None` on rungs walked before the
    #: census existed — which is a third state, not a False (see
    #: :attr:`coefficient_identification`).
    ess_ladder: dict[float, float] | None = None
    ess_target: float | None = None
    #: `w_geom → clearances` on the **calibration ensemble** (not the 32-seed
    #: walk), so the ladder that picked the coefficient can be asked what the
    #: *other* candidates would have concluded. `None` on rungs walked before
    #: D-169, which is `UNRECORDED` and not a False — see
    #: :attr:`verdict_identification`.
    clearance_ladder: dict[float, tuple[float, ...]] | None = None

    @property
    def admissible(self) -> bool:
        """Reached, sampled in band, **and** the ladder agrees on a verdict.

        The third clause is D-169's and it refuses a rung the first two would
        pass: a walk can be perfectly executed and still not carry a reading,
        if the coefficient it was executed at was picked by a criterion that
        does not distinguish it from coefficients yielding a different answer.
        `UNRECORDED` does not refuse — that would retroactively ungrade
        :data:`CONVOY_W75_NULL`, whose ladder was never asked this question,
        and "unmeasured" is not "failed" (`coefficient_identification`'s rule,
        one property up).
        """
        return (self.all_reached and self.ess_in_band
                and self.verdict_identification != VERDICT_UNIDENTIFIED)

    @property
    def ess_response(self) -> float | None:
        """How far the sampler's median ESS moves across the whole `w_geom`
        ladder, as a fraction of the arm the null is being matched to.

        This is the calibration's **own** diagnostic. D-167 picks `w_geom` by
        landing the null's median ESS on the risk arm's; that criterion only
        identifies a coefficient if ESS actually responds to `w_geom` over the
        ladder walked. Where it does not, every candidate "matches" and the
        pick is the ladder's own arbitrary spacing.
        """
        if not self.ess_ladder or not self.ess_target:
            return None
        vals = list(self.ess_ladder.values())
        return (max(vals) - min(vals)) / self.ess_target

    @property
    def coefficient_identification(self) -> str:
        """`IDENTIFIED` / `FLAT` / `UNRECORDED` — three states, not two.

        `UNRECORDED` is kept distinct from `FLAT` for the reason this module
        keeps :data:`NULL_INADMISSIBLE` distinct from a tie: "the criterion
        could not pin the coefficient" and "nobody wrote down whether it
        could" are opposite epistemic states.
        """
        r = self.ess_response
        if r is None:
            return "UNRECORDED"
        return "FLAT" if r < FLAT_ESS_RESPONSE else "IDENTIFIED"

    def _ladder_arms(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        """The recorded arms truncated to the calibration ensemble's seeds.

        The ladder is walked at 16 seeds and the recorded arms hold 32, both
        seed-ordered from 0, so the shared prefix is the paired comparison. Any
        ladder verdict must be read against *these* and not against the 32-seed
        arms, or the seed sets differ between the two things being compared.
        """
        n = len(next(iter(self.clearance_ladder.values())))  # type: ignore[union-attr]
        return (self.recorded["stock_mppi"][:n], self.recorded["risk_mppi"][:n])

    @property
    def behavioural_response(self) -> float | None:
        """How far the ladder moves **achieved clearance**, as a fraction of
        the mechanism's own gain over stock on the same seeds.

        The companion to :attr:`ess_response`, and the reason that one is not
        sufficient on its own. ESS measures how peaked the softmax is; this
        measures what the robot did. D-169 measured them decoupled by two
        orders of magnitude — 1.7% ESS response against 176% behavioural
        response over `w_geom ∈ [10, 160]` — so a coefficient the ESS criterion
        calls "matched" is not thereby one the trajectory calls matched.
        """
        if not self.clearance_ladder:
            return None
        stock, risk = self._ladder_arms()
        gain = _mean(risk) - _mean(stock)
        if gain == 0.0:
            return None
        means = [_mean(c) for c in self.clearance_ladder.values()]
        return (max(means) - min(means)) / gain

    @property
    def ladder_verdicts(self) -> dict[float, str]:
        """`w_geom → attribution verdict` over the recorded ladder.

        Each entry is the verdict this module would have published had the
        calibration picked that coefficient. Built through
        :class:`Attribution` itself rather than reimplementing the branch
        logic, so the two cannot drift.
        """
        if not self.clearance_ladder:
            return {}
        stock, risk = self._ladder_arms()
        out: dict[float, str] = {}
        for w, clear in sorted(self.clearance_ladder.items()):
            probe = NullRung(
                scenario=self.scenario, lam=self.lam, weight=self.weight,
                margin=self.margin, w_geom=w, clearances=clear,
                # The ladder rungs are being asked "what verdict would this
                # coefficient have produced", which is a question about the
                # verdict logic and not about that walk's admissibility — so
                # the probe is admissible by construction and the refusal is
                # reported once, at the rung level, by
                # `verdict_identification`.
                all_reached=True, ess_in_band=True,
                recorded={"stock_mppi": stock, "risk_mppi": risk})
            out[w] = probe.attribution().verdict
        return out

    @property
    def verdict_identification(self) -> str:
        """`IDENTIFIED` / :data:`VERDICT_UNIDENTIFIED` / `UNRECORDED`.

        The question :attr:`coefficient_identification` leaves open. A flat ESS
        ladder is harmless if every coefficient on it yields the same verdict;
        it is fatal if they disagree, and only this property can tell the two
        apart. Three states for the reason that one has: "no ladder was
        recorded" is not "the ladder agreed".
        """
        if not self.clearance_ladder:
            return "UNRECORDED"
        return ("IDENTIFIED" if len(set(self.ladder_verdicts.values())) <= 1
                else VERDICT_UNIDENTIFIED)

    def _comparison(self, a: tuple[float, ...], b: tuple[float, ...],
                    censoring: str) -> RungComparison:
        """Both arms on this rung, `b` in the class's `risk` slot.

        :class:`~margin_free.RungComparison` names its two samples `stock` and
        `risk` after the population it was built for. Here the slots carry
        whichever pair the caller states; the class computes
        `A = P(b > a) + ½P(=)` and cares about nothing else. The `censoring`
        field is carried through unused, exactly as it is on the census.
        """
        return RungComparison(scenario=self.scenario, weight=self.weight,
                              declared_margin=self.margin, censoring=censoring,
                              stock=a, risk=b)

    def versus_stock(self) -> RungComparison:
        """Geometric null against stock. Does geometry alone move clearance?"""
        return self._comparison(self.recorded["stock_mppi"], self.clearances,
                                "GEOMETRIC_NULL_VS_STOCK")

    def mechanism_versus_stock(self) -> RungComparison:
        """The recorded risk arm against stock, rebuilt from the same
        constants the census reads so the three readings share a denominator
        rather than being quoted from a journal."""
        return self._comparison(self.recorded["stock_mppi"],
                                self.recorded["risk_mppi"],
                                "MECHANISM_VS_STOCK")

    def versus_geometry(self) -> RungComparison:
        """Risk arm against the geometric null, head-to-head and paired by
        seed. This is the comparison the verdict is taken from."""
        return self._comparison(self.clearances, self.recorded["risk_mppi"],
                                "MECHANISM_VS_GEOMETRIC_NULL")

    def attribution(self) -> Attribution:
        return Attribution(rung=self, admissible=self.admissible)

    def __str__(self) -> str:  # pragma: no cover - formatting
        return (f"{self.scenario:<32} w={self.weight:<6g} "
                f"w_geom={self.w_geom:<5g} {self.attribution()}")


#: The rung D-167 walked: convoy `w = 75`, the population's **largest** effect
#: (`A = 1.0000`, the two arms' clearance ranges disjoint over 32 seeds).
CONVOY_W75_NULL = NullRung(
    scenario=NULL_SCENARIO, lam=NULL_LAM, weight=NULL_WEIGHT,
    margin=NULL_MARGIN, w_geom=NULL_W_GEOM, clearances=NULL_CLEARANCES,
    all_reached=NULL_ADMISSIBILITY["all_reached"],
    ess_in_band=NULL_ADMISSIBILITY["ess_in_band"],
    recorded=CONVOY_W75_CLEARANCES,
)


#: The second rung the null was walked at, and the first on a **different
#: scene**: `cafe_head_on_v0` `w_obs_soft = 75`, λ = 0.8, the published band's
#: lower rung (`A = 0.9980`, D-166's second-largest effect). Walked 2026-08-10
#: 03:00 at the ESS-closest coefficient on a 16-seed ladder.
#:
#: **Refused.** 32/32 seeds reached the goal and **31/32** sat inside
#: `ab.ess_band(256)` — one short of the rule every walk on this branch is held
#: to (`assert_ess_in_band` is all-seeds, not most-seeds). So this rung
#: contributes to :func:`null_rungs` and **not** to :attr:`NullCensus.graded`,
#: which is the distinction the census exists to keep: a walk that happened is
#: not the same object as a reading that counts.
#: The extension D-169 bought, and the measurement that reframed the rung:
#: `w_geom → clearances` at 16 seeds on `cafe_head_on_v0` `w = 75`, λ = 0.8.
#: Every rung here had **16/16 seeds reach the goal and 16/16 in band**, so
#: none of them is refusable on the grounds the 32-seed `w_geom = 2.0` walk was.
#:
#: STATE asked for the ladder to be extended upward "until median ESS
#: responds", on the model that the null was too **quiet** to rank rollouts.
#: Extended 20× past the old top rung, it still does not respond — 1.7% of the
#: risk arm's ESS across `w_geom ∈ [10, 160]` — while mean clearance travels
#: 0.2856 → 0.5099. The term was never quiet; the sampler's ESS is simply blind
#: to it on this scene, so the criterion that reads ESS cannot pick between
#: coefficients that disagree about the answer.
#: Every rung of :data:`HEADON_W75_CLEARANCE_LADDER`, `(n_reached, n_in_band)`
#: out of 16. Recorded because the docstring below claims none of these rungs
#: is refusable on the 32-seed walk's grounds, and that claim should be a
#: constant a test can read rather than prose.
HEADON_W75_LADDER_ADMISSIBILITY: dict[float, tuple[int, int]] = {
    10.0: (16, 16), 20.0: (16, 16), 40.0: (16, 16),
    80.0: (16, 16), 160.0: (16, 16),
}

HEADON_W75_CLEARANCE_LADDER: dict[float, tuple[float, ...]] = {
    10.0: (
        0.3191, 0.2604, 0.2150, 0.2767, 0.3036, 0.2512, 0.3337, 0.2879,
        0.1842, 0.2615, 0.3055, 0.3209, 0.2695, 0.2911, 0.3244, 0.3652,
    ),
    20.0: (
        0.3453, 0.3439, 0.3112, 0.3266, 0.3692, 0.3330, 0.3196, 0.2716,
        0.2683, 0.3229, 0.3935, 0.3914, 0.2921, 0.2918, 0.3880, 0.2914,
    ),
    40.0: (
        0.3750, 0.3511, 0.4118, 0.3629, 0.3692, 0.3807, 0.3466, 0.3341,
        0.3166, 0.3553, 0.3566, 0.4177, 0.3922, 0.3775, 0.3755, 0.3267,
    ),
    80.0: (
        0.4502, 0.3134, 0.4159, 0.4039, 0.4380, 0.4393, 0.4392, 0.4183,
        0.4135, 0.4918, 0.3963, 0.3702, 0.3739, 0.4323, 0.4311, 0.4564,
    ),
    160.0: (
        0.4346, 0.5085, 0.4376, 0.5063, 0.5786, 0.4840, 0.5465, 0.5619,
        0.4837, 0.5403, 0.4877, 0.5118, 0.5396, 0.4805, 0.5625, 0.4938,
    ),
}

HEADON_W75_NULL = NullRung(
    scenario="cafe_head_on_v0.yaml", lam=0.8, weight=75.0, margin=0.40,
    w_geom=2.0,
    clearances=(
        0.2492, 0.2730, 0.2550, 0.2928, 0.2184, 0.2862, 0.2053, 0.2403,
        0.1918, 0.2260, 0.2515, 0.2515, 0.1989, 0.2012, 0.2472, 0.2335,
        0.1990, 0.2749, 0.2487, 0.1777, 0.2279, 0.3289, 0.2386, 0.2758,
        0.2514, 0.2638, 0.2048, 0.2848, 0.2480, 0.1971, 0.2773, 0.3079,
    ),
    all_reached=True,
    ess_in_band=False,
    recorded=_HEADON_W75_RECORDED,
    # The offending seed, in the direction that matters: 25 ran at ESS 134.15
    # against `ab.ess_band(256) == (12.8, 128.0)` — **above**, so the softmax
    # was too near uniform. The term was too quiet to rank rollouts, which is
    # the same thing the flat ladder says one line down.
    #: 16 seeds per rung, at the rung's own λ = 0.8. The risk arm's median ESS
    #: on the same ensemble is 115.90 and stock's is 115.17.
    ess_ladder={1.0: 115.80, 2.0: 115.86, 2.5: 115.80, 4.0: 115.76,
                8.0: 115.64, 10.0: 116.01, 20.0: 115.23, 40.0: 114.98,
                80.0: 115.15, 160.0: 114.04},
    ess_target=115.90,
    clearance_ladder=HEADON_W75_CLEARANCE_LADDER,
)


def versus_stock() -> RungComparison:
    """:data:`CONVOY_W75_NULL`'s null-vs-stock reading (D-167's shipped one)."""
    return CONVOY_W75_NULL.versus_stock()


def mechanism_versus_stock() -> RungComparison:
    """:data:`CONVOY_W75_NULL`'s recorded risk arm against stock."""
    return CONVOY_W75_NULL.mechanism_versus_stock()


def versus_geometry() -> RungComparison:
    """:data:`CONVOY_W75_NULL`'s head-to-head — the verdict comparison."""
    return CONVOY_W75_NULL.versus_geometry()


def louder_versus_geometry() -> RungComparison:
    """The refused `w_geom = 5.0` head-to-head. Reported, never graded — see
    :data:`LOUDER_NULL`."""
    return CONVOY_W75_NULL._comparison(LOUDER_NULL["clearances"],
                                       CONVOY_W75_CLEARANCES["risk_mppi"],
                                       "MECHANISM_VS_LOUDER_NULL_REFUSED")


def shared_admissible_lams() -> tuple[float, ...]:
    """Temperatures where **all three** arms had every seed in band.

    Empty on the recorded ladder, which is the whole reason `w_geom` is
    calibrated rather than set equal to `w_risk`. A function rather than a
    constant so the claim is recomputed from :data:`LAM_LADDER` instead of
    being asserted next to it.
    """
    return tuple(lam for lam, row in sorted(LAM_LADDER.items())
                 if all(n == 8 for n in row.values()))


@dataclass(frozen=True)
class Attribution:
    """Is the branch's clearance result attributable to the representation?"""

    #: `|A − ½|` below this counts as no separation. 0.10 corresponds to a
    #: 60/40 win rate over the cross pairs — well inside what 32×32 pairs can
    #: distinguish, and stated here rather than inlined so a reading can be
    #: re-taken at another threshold without editing the verdict logic.
    inert_effect: float = 0.10
    #: TOST band for the head-to-head, in metres of paired clearance
    #: difference. 0.05 m is the ε D-166 used for the census's one tie. It is
    #: reported alongside :attr:`equivalence_margin`, never instead of it —
    #: ε is exactly the magnitude this branch has now twice chosen wrong
    #: (D-164's declared margins, D-165's derived ones).
    eps: float = 0.05
    admissible: bool = True
    #: The rung this reading is about. Defaults to D-167's so every call site
    #: that predates the census keeps meaning what it meant.
    rung: NullRung = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.rung is None:
            object.__setattr__(self, "rung", CONVOY_W75_NULL)

    @property
    def residual_share(self) -> float:
        """Fraction of the mechanism's clearance gain the **null** reproduces:
        `1 − Δ(risk−geom) / Δ(risk−stock)`.

        The headline number, and deliberately a share rather than the residual
        itself. `A` says which arm is ahead and the CI says whether that is
        real; neither says *how much of the reported effect survives removing
        the representation*, which is the question STATE asks. Measured 0.7725
        at the admissible coefficient.
        """
        total = self.rung.mechanism_versus_stock().paired_delta
        if total == 0.0:
            raise ZeroDivisionError(
                "the mechanism has no gain over stock on this rung, so there "
                "is no share of it to attribute — read `versus_stock` instead")
        return 1.0 - self.rung.versus_geometry().paired_delta / total

    @property
    def equivalence_margin(self) -> float:
        """The smallest ε at which the head-to-head reads `EQUIVALENT`. The
        number a reader compares against their own tolerance instead of
        against one this module picked for them."""
        return self.rung.versus_geometry().equivalence_margin()

    @property
    def verdict(self) -> str:
        if not self.admissible:
            return NULL_INADMISSIBLE
        geom, mech, head = (self.rung.versus_stock(),
                            self.rung.mechanism_versus_stock(),
                            self.rung.versus_geometry())
        if geom.effect < self.inert_effect and mech.effect < self.inert_effect:
            return BOTH_INERT
        if head.effect < self.inert_effect:
            return GEOMETRY_SUFFICES
        return REPRESENTATION_ADDS if head.superiority > 0.5 else GEOMETRY_WINS

    def __str__(self) -> str:  # pragma: no cover - formatting
        g, m, h = (self.rung.versus_stock(),
                   self.rung.mechanism_versus_stock(),
                   self.rung.versus_geometry())
        return (f"{self.verdict}: geom-vs-stock A={g.superiority:.4f} "
                f"risk-vs-stock A={m.superiority:.4f} "
                f"risk-vs-geom A={h.superiority:.4f} "
                f"residual_share={self.residual_share:.4f} "
                f"eq_margin={self.equivalence_margin:.4f}m")


def attribution() -> Attribution:
    """The measured reading, admissibility taken from the recorded walk."""
    return Attribution(admissible=all(NULL_ADMISSIBILITY.values()))


#: No rung in the census produced a gradable reading (every walk inadmissible,
#: or none walked). An empty denominator, named so it cannot be misread as a
#: tie — D-107's shape.
NO_GRADED_RUNG = "NO_GRADED_RUNG"

#: Exactly one rung is graded. The attribution reading exists but says nothing
#: about whether it travels; this is the state D-167 shipped in and STATE named
#: as the weakest base the branch has put a claim on.
SINGLE_RUNG = "SINGLE_RUNG"

#: Every graded rung reads :data:`REPRESENTATION_ADDS`. The residual is not a
#: one-rung artefact — which is a statement about *reproducibility*, not about
#: size: the shares may still differ by a factor.
RESIDUAL_HOLDS = "RESIDUAL_HOLDS"

#: Every graded rung reads :data:`GEOMETRY_SUFFICES` or :data:`GEOMETRY_WINS`.
GEOMETRY_SUFFICES_THROUGHOUT = "GEOMETRY_SUFFICES_THROUGHOUT"

#: Graded rungs disagree, **and** some scene contributes two or more of them,
#: so the disagreement is separable from the scene it was measured in.
RESIDUAL_RUNG_DEPENDENT = "RESIDUAL_RUNG_DEPENDENT"

#: Graded rungs disagree but every scene contributes at most one, so "the
#: residual depends on the rung" and "the residual depends on the scene" are
#: the same statement about this data and neither is measured. The verdict a
#: two-rung two-scene census earns, and the reason it is not
#: :data:`RESIDUAL_RUNG_DEPENDENT`.
SCENE_CONFOUNDED_WITH_RUNG = "SCENE_CONFOUNDED_WITH_RUNG"


@dataclass(frozen=True)
class NullCensus:
    """The attribution reading over however many rungs have been walked.

    STATE's question is *is the 23% residual a rung property or a scene
    property*, and the honest first answer a census can give is neither — it
    reports **coverage** first and a verdict second, because the population is
    :func:`margin_free.census`'s six walked rungs and this module has walked a
    strict subset of them. :attr:`separates_scene_from_rung` is the property
    that says whether the question in STATE's title is answerable at all from
    the current coverage; it is False until one scene contributes two rungs.
    """

    rungs: tuple[NullRung, ...]

    @property
    def population(self) -> int:
        """Walked rungs available to be nulled — `margin_free`'s six. Read
        rather than hard-coded so growing that census grows this denominator
        instead of silently improving this one's coverage."""
        from .margin_free import census as mf_census

        return len(mf_census().rungs)

    @property
    def graded(self) -> tuple[NullRung, ...]:
        return tuple(r for r in self.rungs if r.admissible)

    @property
    def coverage(self) -> tuple[int, int]:
        return len(self.graded), self.population

    @property
    def scenes(self) -> tuple[str, ...]:
        return tuple(sorted({r.scenario for r in self.graded}))

    @property
    def separates_scene_from_rung(self) -> bool:
        """True iff some scene contributes ≥ 2 graded rungs. Until then a
        disagreement between rungs is also a disagreement between scenes."""
        counts: dict[str, int] = {}
        for r in self.graded:
            counts[r.scenario] = counts.get(r.scenario, 0) + 1
        return any(n >= 2 for n in counts.values())

    @property
    def verdicts(self) -> dict[str, str]:
        return {f"{r.scenario}@{r.weight:g}": r.attribution().verdict
                for r in self.graded}

    @property
    def shares(self) -> dict[str, float]:
        """`residual_share` per graded rung — the headline quantity, kept
        per-rung rather than averaged. A mean over two rungs measured at
        different `w_geom` on different scenes is not a quantity."""
        return {f"{r.scenario}@{r.weight:g}": r.attribution().residual_share
                for r in self.graded}

    @property
    def exposed_to_quiet_null(self) -> tuple[str, ...]:
        """Graded rungs whose `REPRESENTATION_ADDS` reading rests on a
        coefficient the ESS criterion did not pin.

        The controller's residual asymmetry, made countable: a null that
        **loses** may merely be quieter, so on a rung where `w_geom` could have
        been raised without the sampler objecting, a win for the mechanism is
        exactly the reading that objection eats. A tie or a loss for the
        mechanism is not exposed and is not listed here.
        """
        return tuple(
            key for key, rung in
            ((f"{r.scenario}@{r.weight:g}", r) for r in self.graded)
            if rung.coefficient_identification == "FLAT"
            and rung.attribution().verdict == REPRESENTATION_ADDS)

    @property
    def verdict_unidentified(self) -> tuple[str, ...]:
        """Rungs refused because their own `w_geom` ladder reaches more than
        one verdict — read over **all** rungs, not just graded ones, since
        being unidentified is precisely what keeps a rung out of `graded`.

        Distinct from :attr:`exposed_to_quiet_null`, which is the *survivable*
        version of the same worry: that one lists graded rungs where a flat
        ladder leaves a win open to the quiet-null objection, this one lists
        rungs where the ladder was checked and the objection is **realised**.
        """
        return tuple(f"{r.scenario}@{r.weight:g}" for r in self.rungs
                     if r.verdict_identification == VERDICT_UNIDENTIFIED)

    @property
    def verdict(self) -> str:
        graded = self.graded
        if not graded:
            return NO_GRADED_RUNG
        if len(graded) == 1:
            return SINGLE_RUNG
        seen = set(self.verdicts.values())
        if seen == {REPRESENTATION_ADDS}:
            return RESIDUAL_HOLDS
        if seen <= {GEOMETRY_SUFFICES, GEOMETRY_WINS, BOTH_INERT}:
            return GEOMETRY_SUFFICES_THROUGHOUT
        return (RESIDUAL_RUNG_DEPENDENT if self.separates_scene_from_rung
                else SCENE_CONFOUNDED_WITH_RUNG)

    def __str__(self) -> str:  # pragma: no cover - formatting
        n, m = self.coverage
        exposed = self.exposed_to_quiet_null
        unid = self.verdict_unidentified
        return (f"{self.verdict}: rungs {n}/{m} · scenes {len(self.scenes)} · "
                f"separates scene from rung: "
                f"{'yes' if self.separates_scene_from_rung else 'no'} · "
                f"quiet-null exposure: {len(exposed)}/{n}"
                + (f" {list(exposed)}" if exposed else "")
                + (f" · verdict-unidentified: {list(unid)}" if unid else ""))


def null_rungs() -> tuple[NullRung, ...]:
    """Every rung this module has walked the null on — **including refused
    ones**. `NullCensus.graded` is what filters; a walk that is dropped from
    the list entirely is a walk nobody can see was refused."""
    return (CONVOY_W75_NULL, HEADON_W75_NULL)


def census() -> NullCensus:
    """The measured census over :func:`null_rungs`."""
    return NullCensus(rungs=null_rungs())


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    c = census()
    print(c)
    for r in c.rungs:
        print(f"  {r}")
        resp = r.ess_response
        print(f"    w_geom={r.w_geom:g} calibration="
              f"{r.coefficient_identification}"
              + (f" (ESS span {resp:.2%} of target)" if resp is not None
                 else ""))
    a = attribution()
    print(a)
    print(f"  shared admissible lams: {shared_admissible_lams() or 'none'}")
    for label, c in (("geom vs stock", versus_stock()),
                     ("risk vs stock", mechanism_versus_stock()),
                     ("risk vs geom ", versus_geometry()),
                     ("risk vs loud*", louder_versus_geometry())):
        lo, hi = c.bootstrap_ci()
        print(f"  {label}: A={c.superiority:.4f} paired_delta="
              f"{c.paired_delta:+.4f} CI=[{lo:+.4f}, {hi:+.4f}] "
              f"TOST(eps={a.eps})={c.equivalence(a.eps)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
