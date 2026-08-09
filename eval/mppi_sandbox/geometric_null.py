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
"""

from __future__ import annotations

from dataclasses import dataclass

from .margin_free import RungComparison
from .scene_transplant import (CONVOY_LAM, CONVOY_MARGIN, CONVOY_SCENARIO,
                               CONVOY_W75_CLEARANCES, CONVOY_WEIGHT)

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


def _comparison(a: tuple[float, ...], b: tuple[float, ...],
                censoring: str) -> RungComparison:
    """Both arms on one rung, `b` in the class's `risk` slot.

    :class:`~margin_free.RungComparison` names its two samples `stock` and
    `risk` after the population it was built for. Here the slots carry
    whichever pair the caller states; the class computes `A = P(b > a) + ½P(=)`
    and cares about nothing else. The `censoring` field is carried through
    unused, exactly as it is on the census.
    """
    return RungComparison(scenario=NULL_SCENARIO, weight=NULL_WEIGHT,
                          declared_margin=NULL_MARGIN, censoring=censoring,
                          stock=a, risk=b)


def versus_stock() -> RungComparison:
    """Geometric null against stock. Does geometry alone move clearance?"""
    return _comparison(CONVOY_W75_CLEARANCES["stock_mppi"], NULL_CLEARANCES,
                       "GEOMETRIC_NULL_VS_STOCK")


def mechanism_versus_stock() -> RungComparison:
    """The recorded risk arm against stock — D-166's `A = 1.0000` rung,
    rebuilt here from the same constants so the three readings share a
    denominator rather than being quoted from the journal."""
    return _comparison(CONVOY_W75_CLEARANCES["stock_mppi"],
                       CONVOY_W75_CLEARANCES["risk_mppi"],
                       "MECHANISM_VS_STOCK")


def versus_geometry() -> RungComparison:
    """Risk arm against the geometric null, head-to-head and paired by seed.
    This is the comparison the verdict is taken from."""
    return _comparison(NULL_CLEARANCES, CONVOY_W75_CLEARANCES["risk_mppi"],
                       "MECHANISM_VS_GEOMETRIC_NULL")


def louder_versus_geometry() -> RungComparison:
    """The refused `w_geom = 5.0` head-to-head. Reported, never graded — see
    :data:`LOUDER_NULL`."""
    return _comparison(LOUDER_NULL["clearances"],
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
        total = mechanism_versus_stock().paired_delta
        if total == 0.0:
            raise ZeroDivisionError(
                "the mechanism has no gain over stock on this rung, so there "
                "is no share of it to attribute — read `versus_stock` instead")
        return 1.0 - versus_geometry().paired_delta / total

    @property
    def equivalence_margin(self) -> float:
        """The smallest ε at which the head-to-head reads `EQUIVALENT`. The
        number a reader compares against their own tolerance instead of
        against one this module picked for them."""
        return versus_geometry().equivalence_margin()

    @property
    def verdict(self) -> str:
        if not self.admissible:
            return NULL_INADMISSIBLE
        geom, mech, head = (versus_stock(), mechanism_versus_stock(),
                            versus_geometry())
        if geom.effect < self.inert_effect and mech.effect < self.inert_effect:
            return BOTH_INERT
        if head.effect < self.inert_effect:
            return GEOMETRY_SUFFICES
        return REPRESENTATION_ADDS if head.superiority > 0.5 else GEOMETRY_WINS

    def __str__(self) -> str:  # pragma: no cover - formatting
        g, m, h = versus_stock(), mechanism_versus_stock(), versus_geometry()
        return (f"{self.verdict}: geom-vs-stock A={g.superiority:.4f} "
                f"risk-vs-stock A={m.superiority:.4f} "
                f"risk-vs-geom A={h.superiority:.4f} "
                f"residual_share={self.residual_share:.4f} "
                f"eq_margin={self.equivalence_margin:.4f}m")


def attribution() -> Attribution:
    """The measured reading, admissibility taken from the recorded walk."""
    return Attribution(admissible=all(NULL_ADMISSIBILITY.values()))


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
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
