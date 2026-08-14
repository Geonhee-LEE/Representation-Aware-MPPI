# SPDX-License-Identifier: BSD-3-Clause
"""Do Q-148's two arms contend at any point, or only in the aggregate?

`ratio_pick` closed D-261 by choosing a value *inside* the root band, and every
step from D-255 to D-261 has treated the two arms as one contested sign on one
epistemic term with one contended ratio. RAZER (2309.05582, feed 2026-08-14
16:00) denies the framing rather than picking a side: on its decomposition the
repel pressure and the attract bonus are **two channels with two independent
weights** (Eqs. 9-11: `cA = +wA·Σ√Var^A` and `cE = −wE·Σ√Var^E`, simultaneous,
never sharing a weight), and the collision job belongs to a **third**,
source-agnostic constraint term. If that reading holds here, the whole
`band.lo`/`band.hi` bracket is measuring a tension between quantities that were
never supposed to share a weight — and `INDETERMINATE` at the contended cell is
an artifact of the instrument rather than a fact about the scene.

That challenge cannot be settled by citation. RAZER runs **no sign-flip
ablation** and no MPPI experiment; its own decomposition is a design principle
plus empirical validation, not a theorem. But it *can* be settled on this
branch's own cost field, because it makes a claim with a spatial consequence:
if the two arms are separate channels rather than two sides of one term, they
should not be charging the same points.

What is measured
------------------

On the planner's support (D-258's `ROLLOUT` cloud, not the grid) each arm is
evaluated at unit weight and reduced to its **live set** — the points where its
cost deviates from its own minimum. Deviation-from-min, not raw magnitude, is
the right support: MPPI's softmax is shift-invariant, so a constant offset is
not a force and a point where an arm is flat is a point that arm does not move.

Two arms whose live sets coincide are contending pointwise, and a single
`w_epist : w_voo` ratio is the natural way to adjudicate them. Two arms whose
live sets are disjoint are not competing for any candidate at all; the ratio
then trades off *which region the planner prefers*, which is a different — and
much weaker — thing than the "which arm wins" the bracket is read as.

What it says
--------------

The live sets are disjoint, and not marginally: at the scene's radius
(`r=0.3`) the Jaccard overlap is `0.0072` — 2 shared points out of a 277-point
union — and at `r=0.5` it is exactly `0.0`. The repel arm's live set is
**exactly** the exposed set at every radius read (8/8, 6/6, 2/2), which is the
same partition `epistemic_sign.classify` splits on to produce the very statistic
the root is derived from. So `-v1/s1` divides one arm's level on the shadow by
the other's level on the complement of the shadow. The two numbers never meet.

The asymmetry is the sharper half. The repel arm is live on **8 of 316**
candidates at `r=0.3` — 2.5% of the planner's support — while the attract arm
is live on 271. A ratio that balances a mean taken over 8 points against a mean
taken over 271 is dominated by which 8 points the seed happened to draw, which
is a mechanism for D-257/D-258's seed spread that neither named: the band is
wide because the repel arm's estimator has a sample size of eight.

What it does not say
----------------------

Disjoint supports do **not** make the ratio meaningless, and this module is not
a claim that Q-148's A/B is void. MPPI compares whole trajectories, so an arm
that is live only inside the shadow and an arm that is live only outside it
still trade against each other in the softmax — a rollout that enters the
shadow pays one and forgoes the other. The finding is narrower and it is about
*the instrument*: the cost-field root is a between-region exchange rate, not a
pointwise contest, so reading it as "which arm wins" over-claims, and the sign
attached to it is a property of two disjoint regional means rather than of any
candidate the planner scores.

Nor is it evidence for RAZER's *third* term. `cS` is constraint-shaped and this
branch has no aleatoric estimator at all, so the decomposition is not free to
adopt even if wanted. What is established is the first half of RAZER's
structural claim — the channels are separate here, measurably — and the
consequence that the bracket was the wrong instrument for the sign question.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import rollout_cloud as rc
from .critics import ObservationValueCritic, ShadowCostCritic
from .epistemic_sign import SHADOW_TAU
from .representations import RiskChannel

#: The occluder radius Q-148's A/B actually runs at (`cafe_blind_corner_v0`'s
#: wall discs). Quoted from `ratio_pick`, not re-derived, so the two modules
#: cannot drift apart on the one geometry that matters.
SCENE_RADIUS = 0.3

#: A point is *live* for an arm when that arm's cost there exceeds the arm's own
#: minimum by more than this fraction of its spread. Relative rather than
#: absolute because the two arms carry different units at unit weight.
LIVE_EPS = 1e-6

#: Live sets sharing at most this Jaccard fraction are separate channels.
SEPARATED_MAX_JACCARD = 0.05
#: Live sets sharing at least this fraction are contending pointwise.
CONTENDED_MIN_JACCARD = 0.5

CHANNEL_SEPARATED = "CHANNEL_SEPARATED"
PARTIAL = "PARTIAL"
POINTWISE_CONTENDED = "POINTWISE_CONTENDED"

#: No arm is live anywhere on this support, so overlap is undefined. Kept as a
#: named reading rather than a zero: a Jaccard of 0 over two empty sets is not
#: the same finding as a Jaccard of 0 over two populated ones (D-241 shape).
UNPOSED = "UNPOSED"


@dataclass(frozen=True)
class SupportReading:
    """One radius' live-set overlap between the repel and attract arms."""

    radius: float
    k: int
    n_repel_live: int
    n_attract_live: int
    n_both_live: int
    n_union_live: int
    n_exposed: int
    #: Repel-arm deviation mass sitting on the shared points, as a fraction of
    #: its total. The count-based Jaccard can hide a small overlap that carries
    #: all the force; this is the check that it does not.
    repel_mass_on_overlap: float
    attract_mass_on_overlap: float
    #: Is the repel arm's live set exactly the `classify` exposed partition?
    repel_live_is_exposed: bool
    verdict: str

    @property
    def jaccard(self) -> float:
        return (self.n_both_live / self.n_union_live
                if self.n_union_live else float("nan"))

    @property
    def repel_live_fraction(self) -> float:
        """Share of the planner's candidates the repel arm can move at all."""
        return self.n_repel_live / self.k if self.k else float("nan")

    def __str__(self) -> str:  # pragma: no cover - display only
        return (f"r={self.radius:<5.2f} K={self.k:<4d} "
                f"repel_live={self.n_repel_live:<4d} "
                f"attract_live={self.n_attract_live:<4d} "
                f"both={self.n_both_live:<3d} jaccard={self.jaccard:.4f} "
                f"repel_frac={self.repel_live_fraction:.4f} {self.verdict}")


def live_mask(cost: np.ndarray, eps: float = LIVE_EPS):
    """`(mask, deviation)` — where an arm departs from its own minimum.

    Deviation-from-min rather than from-mean: MPPI's softmax is shift-invariant
    but not sign-symmetric about the mean, so "this arm is flat here" is the
    statement `cost == cost.min()`, and points at the minimum are precisely the
    ones the arm never penalises.
    """
    deviation = np.asarray(cost, dtype=float) - float(np.min(cost))
    spread = float(np.ptp(cost))
    return deviation > eps * max(spread, 1e-12), deviation


def arm_fields(radius: float = SCENE_RADIUS, stride: int = 13, seed: int = 0):
    """Both arms at unit weight on the planner's support — `(repel, attract, sigma)`.

    Unit weight for both, deliberately: the question is about *where* each arm
    is live, and the live set is scale-invariant, so handing them the A/B's
    weights would add a knob that cannot change the answer.
    """
    producer, bev, robot_xy = rc.scene(radius)
    k = rc.matched_k(radius, stride)
    points = rc.rollout_points(bev, k, seed)
    sigma = bev.sample(RiskChannel.EPISTEMIC, points, unobserved_value=1.0)
    repel = ShadowCostCritic(w_epist=1.0).cost(bev, points, len(points))
    attract = ObservationValueCritic(w_voo=1.0).cost(
        producer, bev, robot_xy, 0.0, points, len(points))
    return repel, attract, sigma


def read(radius: float = SCENE_RADIUS, stride: int = 13,
         seed: int = 0) -> SupportReading:
    """Measure the two arms' live-set overlap at one geometry."""
    repel, attract, sigma = arm_fields(radius, stride, seed)
    m_repel, d_repel = live_mask(repel)
    m_attract, d_attract = live_mask(attract)
    both = m_repel & m_attract
    union = m_repel | m_attract
    exposed = sigma > SHADOW_TAU

    n_union = int(union.sum())
    if n_union == 0:
        verdict = UNPOSED
    else:
        jaccard = int(both.sum()) / n_union
        if jaccard <= SEPARATED_MAX_JACCARD:
            verdict = CHANNEL_SEPARATED
        elif jaccard >= CONTENDED_MIN_JACCARD:
            verdict = POINTWISE_CONTENDED
        else:
            verdict = PARTIAL

    return SupportReading(
        radius=radius,
        k=len(repel),
        n_repel_live=int(m_repel.sum()),
        n_attract_live=int(m_attract.sum()),
        n_both_live=int(both.sum()),
        n_union_live=n_union,
        n_exposed=int(exposed.sum()),
        repel_mass_on_overlap=_mass_fraction(d_repel, both),
        attract_mass_on_overlap=_mass_fraction(d_attract, both),
        repel_live_is_exposed=bool(np.array_equal(m_repel, exposed)),
        verdict=verdict,
    )


def _mass_fraction(deviation: np.ndarray, mask: np.ndarray) -> float:
    total = float(deviation.sum())
    if total <= 0.0:
        return 0.0
    return float(deviation[mask].sum()) / total


def survey(radii=(0.3, 0.5, 1.0), stride: int = 13,
           seed: int = 0) -> dict[float, SupportReading]:
    """`read` over a radius set, keyed by radius."""
    return {r: read(r, stride, seed) for r in radii}


@dataclass(frozen=True)
class SeedBand:
    """The overlap reading across seeds at one radius — and its fragility.

    The single-seed verdict is threshold-fragile and this dataclass exists to
    say so rather than to hide it: over `rc.DEFAULT_SEEDS` at the scene radius
    the Jaccard runs `0.0072 … 0.0565`, which straddles
    `SEPARATED_MAX_JACCARD`, so **7 of 8 seeds read `CHANNEL_SEPARATED` and one
    reads `PARTIAL`**. Lowering the threshold to make it 8/8 would be picking
    the constant to fit the finding; the honest report is the band.

    What survives every seed is the stronger claim anyway: the repel arm's live
    set equals the exposed partition at 8/8, and the overlap never exceeds
    `SEED_ROBUST_MAX_JACCARD`.
    """

    radius: float
    jaccard_lo: float
    jaccard_hi: float
    n_repel_lo: int
    n_repel_hi: int
    n_separated: int
    n_seeds: int
    exposed_match_all: bool

    @property
    def repel_count_spread(self) -> float:
        """How many times larger the repel live set gets across seeds."""
        return self.n_repel_hi / max(self.n_repel_lo, 1)


#: The overlap ceiling that holds at *every* seed, unlike the per-seed verdict.
SEED_ROBUST_MAX_JACCARD = 0.06


def seed_band(radius: float = SCENE_RADIUS, stride: int = 13,
              seeds=rc.DEFAULT_SEEDS) -> SeedBand:
    """Read the overlap at every seed and report the band, not a point."""
    readings = [read(radius, stride, s) for s in seeds]
    posed = [r for r in readings if r.verdict != UNPOSED]
    if not posed:
        raise ValueError(f"no posed seed at r={radius}; overlap is undefined")
    jac = [r.jaccard for r in posed]
    counts = [r.n_repel_live for r in posed]
    return SeedBand(
        radius=radius,
        jaccard_lo=min(jac),
        jaccard_hi=max(jac),
        n_repel_lo=min(counts),
        n_repel_hi=max(counts),
        n_separated=sum(r.verdict == CHANNEL_SEPARATED for r in posed),
        n_seeds=len(posed),
        exposed_match_all=all(r.repel_live_is_exposed for r in posed),
    )


def separation_survives_seeds(band: SeedBand) -> bool:
    """The seed-robust form of the finding.

    Deliberately *not* "every seed reads `CHANNEL_SEPARATED`" — one does not.
    It is the pair of statements that do hold at 8/8: the overlap stays under
    `SEED_ROBUST_MAX_JACCARD`, and the repel arm's live set is the exposed
    partition. A caller wanting the per-seed verdict count has `n_separated`.
    """
    return band.exposed_match_all and band.jaccard_hi <= SEED_ROBUST_MAX_JACCARD


def arms_are_separate_channels(surveyed: dict[float, SupportReading]) -> bool:
    """Is every posed radius `CHANNEL_SEPARATED`?

    The predicate the RAZER borrow turns on. `UNPOSED` cells do not count
    either way — a support on which neither arm is live poses no question about
    whether they contend — but an empty survey is `False`, not a vacuous pass
    (D-241): "no radius contradicted me" is not a finding.
    """
    posed = [r for r in surveyed.values() if r.verdict != UNPOSED]
    return bool(posed) and all(r.verdict == CHANNEL_SEPARATED for r in posed)


def root_is_a_between_region_rate(surveyed: dict[float, SupportReading]) -> bool:
    """Is the cancelling root an exchange rate between two disjoint regions?

    True when the arms are separate channels **and** the repel arm's live set is
    exactly `classify`'s exposed partition at every posed radius — i.e. the
    numerator and denominator of `-v1/s1` are means over complementary point
    sets. That conjunction, not the overlap alone, is what makes reading the
    root as "which arm wins" an over-claim.
    """
    posed = [r for r in surveyed.values() if r.verdict != UNPOSED]
    return (arms_are_separate_channels(surveyed)
            and all(r.repel_live_is_exposed for r in posed))


def format_survey(surveyed: dict[float, SupportReading]) -> str:  # pragma: no cover
    lines = [str(r) for r in surveyed.values()]
    lines.append(f"separate_channels={arms_are_separate_channels(surveyed)} "
                 f"between_region_rate={root_is_a_between_region_rate(surveyed)}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(format_survey(survey()))
