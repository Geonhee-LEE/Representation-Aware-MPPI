# SPDX-License-Identifier: BSD-3-Clause
"""Is `ess_band` admissibility choosing which null gets believed?

Q-124. Three nulls now exist and STATE noticed they order the same way twice:

===========================  ============  ================
null                         admissible?   `residual_share`
===========================  ============  ================
ESS-matched geometry (2.5)   yes           0.7725
louder geometry (5.0)        no            0.9130
frozen prediction            no            0.9539
===========================  ============  ================

Read down the right column against the left one and the worry states itself:
every null the filter **admits** is also the one most favourable to the
representation, because a low share means the null reproduced little and the
mechanism keeps the rest. If that is systematic, then "the representation adds
23% at the admissible rung" is a statement about `ab.ess_band` and the census's
`graded` set is a *selected sample* rather than a denominator — D-171's defect
one level up, and this time in the quantity the branch actually publishes.

The screen, and why it is directional
--------------------------------------

D-171 counted the fraction of rung pairs ordered the same way by two
quantities. The same statistic works here with one change: the concern is
**signed**. D-171 asked whether a match residual and a verdict were one
quantity, and either direction of coupling would have been that. Here only one
direction is the accusation — admissible ⇒ *lower* share ⇒ friendlier to the
representation. A filter that systematically admitted the nulls that made the
representation look **worse** would be an odd filter, but it would not be the
thing that makes the published 23% unsafe to quote. So :attr:`Screen.coupling`
counts pairs in that one direction and 0.5 is independence, not 0.

Why a coupling number alone would have been the wrong instrument
------------------------------------------------------------------

Because on the three walked nulls it reads **1.0000**, and 1.0000 is worth
nothing there. Two of the three are refusals, so exactly one label is
`admissible`, and the chance that the single admitted null lands on the lowest
of three shares by luck alone is **1/3**. Perfect coupling is the *best*
reading the population can produce and it is still p = 0.3333.

That is a fact about the census's size, not about its data, and it is knowable
before the shares are looked at — which is why :attr:`Screen.verdict` consults
:attr:`Screen.min_achievable_p` first. A screen whose most extreme possible
outcome cannot clear its own significance level returns
:data:`SCREEN_UNDERPOWERED` and **no** finding, in either direction. Without
that guard this module's first output would have been "coupling 1.0000,
selection confirmed", and the branch would have retracted its census on the
strength of a coin that landed once.

The second population, and the answer: the ladder can be screened
------------------------------------------------------------------

`CONVOY_W75_CLEARANCE_LADDER` holds **seven** rungs at the same scene and
weight, with per-rung admissibility already in
`CONVOY_W75_LADDER_ADMISSIBILITY`. Same screen, five times the comparable
pairs — and unlike the strict population it is **answerable**.

It was not, for one rung. D-174 read this ladder at six rungs and got
`SCREEN_UNDERPOWERED`: four admissible against two refused is 15 labellings,
best-case p **1/15 = 0.0667**, missing `ALPHA` by a single point.
:attr:`Screen.points_needed` priced that at **+1**, and D-175 paid it — a 7th
rung walked at `w_geom = 15`, interior to the existing spacing so it is an
interpolation and not an extrapolation, `(16, 16)` admissible. Five admissible
against two refused is 21 labellings, best-case p **1/21 = 0.0476**, which
clears `ALPHA = 0.05` by the narrowest margin this population admits.

Measured, the powered screen reads **coupling 0.6000 at p = 0.4286** →
:data:`SELECTION_INDEPENDENT`. So Q-124's answer is *no*: `ess_band`
admissibility does not select `residual_share`. Note what the extra rung did
and did not change — the coupling barely moved (0.6250 → 0.6000) and the p
value rose. The rung bought the *right to read* the number, not the number.

The strict 32-seed population remains `SCREEN_UNDERPOWERED` at **+3**, so this
is an answer about the ladder and not about the census's own strictness (Q-125
is which of the two the census calls its own).

The one piece of evidence that is not underpowered
----------------------------------------------------

:attr:`Screen.span_reading` is a statement about the observed set rather than
about a reference distribution, so small `n` does not void it — and on the
ladder it reads :data:`ADMISSIBLE_SPANS_REFUSED`. The admissible rungs cover
shares **0.3302 → 1.0041**, essentially the whole range, and *both* refused
rungs (0.9172, 0.9930) sit inside that span. `w_geom = 20` is admissible at a
share of **1.0041** — a null reproducing slightly more than the entire
mechanism gain, which is maximally *unflattering* to the representation, and
the filter admitted it anyway.

That is a direct counterexample to the mechanism STATE feared: on this ladder
`ess_band` demonstrably does not keep out the nulls that make the
representation look bad. It is evidence, not proof, and it lives at 16-seed
strictness rather than the census's 32.

Why the two populations disagree, and why it is not a contradiction
---------------------------------------------------------------------

`w_geom = 5.0` is **admissible at 16 seeds `(16, 16)` and refused at 32** —
:func:`licence_split` reads :data:`LICENCE_SPLIT` on exactly that rung. Under
an all-seeds band rule admissibility can only be lost as seeds are added, so
the 16-seed ladder is a systematically more permissive filter than the one the
branch publishes at. The two screens are the same question at two strictnesses;
only the strict one is the census's own, and it is the one with no power.

What this does and does not license
-------------------------------------

It does **not** clear the census. What it does is convert STATE's worry from a
suspicion into a priced, bounded task: one more ladder rung makes the 16-seed
screen answerable, and the census's own strictness needs three more nulls
before the question is even askable there. Until then the one graded number
carries a denominator whose selection properties are *uncharacterised* — which
is a weaker and more accurate thing to say than either "selected" or "clean".
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from itertools import combinations


def _binom(n: int, k: int) -> float:
    return math.comb(n, k) if 0 <= k <= n else 0.0

#: Significance level the permutation test is read at. Stated here rather than
#: inlined so the screen can be re-taken at another level without editing the
#: verdict logic — `geometric_null.FLAT_ESS_RESPONSE`'s convention.
ALPHA = 0.05

#: Admissibility and `residual_share` move together in the direction that
#: flatters the representation, and the population is large enough that the
#: reading could have come out otherwise. The census's `graded` set must be
#: treated as a selected sample until the filter is changed or characterised.
SELECTION_SUSPECTED = "SELECTION_SUSPECTED"

#: The coupling is within chance of independence on a population that had the
#: power to show otherwise. Admissibility is not choosing the share here.
SELECTION_INDEPENDENT = "SELECTION_INDEPENDENT"

#: The population cannot answer the question at :data:`ALPHA` **even if the
#: coupling were perfect** — too few admissible or too few refused points. No
#: finding is returned in either direction, and in particular a coupling of
#: 1.0000 from such a population is not evidence of selection.
#:
#: This is deliberately checked before the measured coupling is consulted, so
#: the verdict cannot depend on a number the population was never able to
#: license. Distinguished from :data:`SELECTION_INDEPENDENT` because "no
#: coupling" and "no power to detect coupling" are opposite epistemic states —
#: the branch's recurring D-107 shape, in the screen this time.
SCREEN_UNDERPOWERED = "SCREEN_UNDERPOWERED"

#: Not enough comparable pairs to compute a coupling at all (fewer than two
#: distinct labels, or every share tied).
NO_COMPARABLE_PAIRS = "NO_COMPARABLE_PAIRS"

#: The admissible points' share range **contains** every refused point's share.
#: The qualitative companion to the coupling: a filter that selected on share
#: could not admit both the lowest and the highest reading in the population.
#: Stronger than a p-value in one specific way — it is a statement about the
#: observed set rather than about a reference distribution.
ADMISSIBLE_SPANS_REFUSED = "ADMISSIBLE_SPANS_REFUSED"

#: Every refused point's share lies outside the admissible span. Consistent
#: with selection, though on a small population also consistent with luck.
ADMISSIBLE_SEPARATED = "ADMISSIBLE_SEPARATED"

#: Some refused points inside the admissible span, some outside.
ADMISSIBLE_OVERLAPS = "ADMISSIBLE_OVERLAPS"

#: A coefficient that is admissible in one population and refused in the other.
#: Under an all-seeds band rule admissibility is monotone non-increasing in
#: seed count, so this always resolves as "the smaller ensemble was permissive"
#: rather than as a contradiction — D-163's licence, named here so a reader
#: comparing the two screens does not have to re-derive why they differ.
LICENCE_SPLIT = "LICENCE_SPLIT"

#: The populations agree on every shared coefficient.
LICENCE_AGREED = "LICENCE_AGREED"

#: The two populations share **no** coefficient, so agreement was never tested.
#: Distinguished from :data:`LICENCE_AGREED` because an empty intersection
#: returns "no disagreements found" from a comparison that never happened —
#: D-107's shape, and the exact hazard `guard_reflexivity` flagged when
#: :func:`licence_split`'s `&` entered the `&`-shaped registry (D-174). The
#: frozen null already carries `w_geom is None` for a principled reason, so a
#: future population of only structural arms would hit this rather than read as
#: consensus.
LICENCE_NO_OVERLAP = "LICENCE_NO_OVERLAP"


@dataclass(frozen=True)
class Point:
    """One null: was it admitted, and how much of the gain did it reproduce?"""

    label: str
    admissible: bool
    residual_share: float
    #: Seeds the admissibility judgement was taken on. Carried because the
    #: whole disagreement between this module's two populations is a seed-count
    #: difference, and a `Point` that did not know its own count could not say
    #: so.
    n_seeds: int
    #: The geometric coefficient, or `None` for a null that has none (the
    #: structural arm). :func:`licence_split` joins the two populations on this
    #: rather than on :attr:`label`, because the labels are formatted strings
    #: and `w_geom=5` / `w_geom=5.0` are the same rung — a join on text silently
    #: dropped exactly the rung the two populations disagree about.
    w_geom: float | None = None


def _comparable(points: tuple[Point, ...]) -> list[tuple[Point, Point]]:
    """Pairs that split on admissibility **and** differ in share.

    Ties on either axis carry no ordering information, so they are dropped
    rather than counted as agreement — `gain_effect_coupling`'s rule, kept
    identical so the two screens' numbers are comparable.
    """
    return [(a, b) for a, b in combinations(points, 2)
            if a.admissible != b.admissible
            and a.residual_share != b.residual_share]


def _coupling(points: tuple[Point, ...]) -> float | None:
    """Fraction of comparable pairs where the admissible one has the **lower**
    share. `None` when no pair is comparable; 0.5 is independence."""
    pairs = _comparable(points)
    if not pairs:
        return None
    agree = 0
    for a, b in pairs:
        adm, ref = (a, b) if a.admissible else (b, a)
        agree += adm.residual_share < ref.residual_share
    return agree / len(pairs)


@dataclass(frozen=True)
class Screen:
    """The reading over one population of nulls."""

    population: str
    points: tuple[Point, ...]

    @property
    def n(self) -> int:
        return len(self.points)

    @property
    def n_admissible(self) -> int:
        return sum(1 for p in self.points if p.admissible)

    @property
    def n_refused(self) -> int:
        return self.n - self.n_admissible

    @property
    def comparable_pairs(self) -> int:
        return len(_comparable(self.points))

    @property
    def coupling(self) -> float | None:
        """See :func:`_coupling`. 1.0 means every admitted null was friendlier
        to the representation than every refused one."""
        return _coupling(self.points)

    def _null_distribution(self) -> list[float]:
        """Couplings over every re-assignment of the admissibility labels.

        The shares stay put and the labels move, which is the right exchange:
        the question is whether *this* labelling is special among the ones the
        filter could have produced with the same admitted count.
        """
        shares = [p.residual_share for p in self.points]
        out = []
        for idx in combinations(range(self.n), self.n_admissible):
            chosen = set(idx)
            relabelled = tuple(
                Point(p.label, i in chosen, shares[i], p.n_seeds, p.w_geom)
                for i, p in enumerate(self.points))
            c = _coupling(relabelled)
            if c is not None:
                out.append(c)
        return out

    @property
    def p_value(self) -> float | None:
        """Exact one-sided permutation p: `P(coupling ≥ observed)`.

        Exact rather than sampled — the populations here are 3 and 6 points, so
        the whole reference distribution is 3 and 15 assignments respectively
        and there is no reason to approximate it.
        """
        observed = self.coupling
        if observed is None:
            return None
        dist = self._null_distribution()
        if not dist:
            return None
        return sum(1 for c in dist if c >= observed) / len(dist)

    @property
    def min_achievable_p(self) -> float | None:
        """The p this population would return if the coupling were **perfect**.

        The power reading, and the one :attr:`verdict` consults first. It
        depends only on how the admissible/refused labels are split, never on
        the shares, so it answers "could this screen have found anything?"
        without reference to what it did find.
        """
        dist = self._null_distribution()
        if not dist:
            return None
        best = max(dist)
        return sum(1 for c in dist if c >= best) / len(dist)

    @property
    def powered(self) -> bool:
        m = self.min_achievable_p
        return m is not None and m <= ALPHA

    @property
    def points_needed(self) -> int:
        """How many further nulls would make this screen answerable at
        :data:`ALPHA`, given the freedom to label them either way.

        The reason :data:`SCREEN_UNDERPOWERED` is a bounded finding rather than
        a dead end. `min_achievable_p` is `1 / C(n, k)` whenever the shares are
        distinct — exactly one labelling achieves perfect coupling — so the
        question is how many points it takes to push that binomial past
        `1 / ALPHA`, maximised over the admissible counts reachable by adding
        `j` points to the current `k`.

        Reads **0** for a powered screen — which the ladder now does, having
        been a single rung short until D-175 walked one (it read 1, the rung
        landed, and it reads 0). The strict population still reads **3**.
        """
        if self.powered:
            return 0
        need = 1.0 / ALPHA
        j = 0
        while j < 64:
            j += 1
            n, k = self.n + j, self.n_admissible
            if any(_binom(n, k + extra) >= need for extra in range(j + 1)):
                return j
        return -1

    @property
    def admissible_span(self) -> tuple[float, float] | None:
        adm = [p.residual_share for p in self.points if p.admissible]
        return (min(adm), max(adm)) if adm else None

    @property
    def span_reading(self) -> str | None:
        """Where the refused shares sit relative to the admissible ones."""
        span = self.admissible_span
        refused = [p.residual_share for p in self.points if not p.admissible]
        if span is None or not refused:
            return None
        lo, hi = span
        inside = sum(1 for r in refused if lo <= r <= hi)
        if inside == len(refused):
            return ADMISSIBLE_SPANS_REFUSED
        if inside == 0:
            return ADMISSIBLE_SEPARATED
        return ADMISSIBLE_OVERLAPS

    @property
    def verdict(self) -> str:
        if self.coupling is None:
            return NO_COMPARABLE_PAIRS
        if not self.powered:
            return SCREEN_UNDERPOWERED
        p = self.p_value
        return (SELECTION_SUSPECTED if p is not None and p <= ALPHA
                else SELECTION_INDEPENDENT)

    def __str__(self) -> str:  # pragma: no cover - formatting
        c, p = self.coupling, self.p_value
        return (f"{self.population:<14} {self.verdict} "
                f"coupling={'n/a' if c is None else f'{c:.4f}'} "
                f"p={'n/a' if p is None else f'{p:.4f}'} "
                f"(min {self.min_achievable_p:.4f}, "
                f"needs +{self.points_needed}) "
                f"pairs={self.comparable_pairs} "
                f"adm={self.n_admissible}/{self.n} [{self.span_reading}]")


# ==========================================================================
# The two populations. Both are read off recorded constants — 0 sim runs, per
# STATE's requirement that the instrument be screened before a fourth null is
# bought.
# ==========================================================================


def _share(stock: tuple[float, ...], risk: tuple[float, ...],
           null: tuple[float, ...]) -> float:
    """`1 − Δ(risk − null) / Δ(risk − stock)`, computed the way both
    `Attribution.residual_share` and `StructuralRung.residual_share` compute
    it — paired per seed, mean difference, no margin anywhere.

    Recomputed here rather than imported so this module reads the same
    clearance constants the census does and does not inherit either class's
    admissibility gate: `Attribution.residual_share` is reachable only through
    an object that also carries a verdict, and the whole point of this screen
    is to put admissible and refused rungs in one table.
    """
    total = statistics.fmean(r - s for s, r in zip(stock, risk))
    if total == 0.0:
        raise ZeroDivisionError(
            "the mechanism has no gain over stock on this rung, so there is "
            "no share of it to attribute")
    return 1.0 - statistics.fmean(r - n for n, r in zip(null, risk)) / total


def walked_nulls() -> Screen:
    """The three nulls walked at 32 seeds — the census's own strictness.

    This is the population STATE's question is *about*, and the one that cannot
    answer it: one admissible point against two refused gives a best-case p of
    1/3, so :attr:`Screen.verdict` is :data:`SCREEN_UNDERPOWERED` regardless of
    the shares. Kept and reported anyway, because "the strict population cannot
    be screened" is the finding — hiding it would leave the ladder's clean
    `SELECTION_INDEPENDENT` looking like an answer about the census.
    """
    from .geometric_null import LOUDER_NULL, NULL_ADMISSIBILITY, NULL_CLEARANCES
    from .scene_transplant import CONVOY_W75_CLEARANCES
    from .structural_null import FROZEN_W75_CLEARANCES

    stock = CONVOY_W75_CLEARANCES["stock_mppi"]
    risk = CONVOY_W75_CLEARANCES["risk_mppi"]
    frozen = _frozen_admissible()
    from .geometric_null import NULL_W_GEOM
    return Screen("walked-32", (
        Point("geom w_geom=2.5", all(NULL_ADMISSIBILITY.values()),
              _share(stock, risk, NULL_CLEARANCES), 32, NULL_W_GEOM),
        Point("geom w_geom=5.0",
              bool(LOUDER_NULL["all_reached"]) and bool(LOUDER_NULL["ess_in_band"]),
              _share(stock, risk, LOUDER_NULL["clearances"]),  # type: ignore[arg-type]
              32, float(LOUDER_NULL["w_geom"])),  # type: ignore[arg-type]
        Point("frozen prediction", frozen,
              _share(stock, risk, FROZEN_W75_CLEARANCES), 32, None),
    ))


def _frozen_admissible() -> bool:
    """The structural null's admissibility, taken from its own rung object
    rather than restated — `StructuralRung.admissible` is the all-seeds rule
    and this screen must not quietly apply a different one."""
    from .structural_null import convoy_w75_frozen
    return convoy_w75_frozen().admissible


def ladder_rungs() -> Screen:
    """The seven `w_geom` rungs at 16 seeds — the population with the power.

    Same scene, same `w_obs_soft`, same λ; the arms are truncated to the
    ladder's seed prefix exactly as `NullRung._ladder_arms` truncates them, so
    each share is a paired comparison over one seed set.
    """
    from .geometric_null import (CONVOY_W75_CLEARANCE_LADDER,
                                 CONVOY_W75_LADDER_ADMISSIBILITY)
    from .scene_transplant import CONVOY_W75_CLEARANCES

    n = len(next(iter(CONVOY_W75_CLEARANCE_LADDER.values())))
    stock = CONVOY_W75_CLEARANCES["stock_mppi"][:n]
    risk = CONVOY_W75_CLEARANCES["risk_mppi"][:n]
    points = []
    for w, clearances in sorted(CONVOY_W75_CLEARANCE_LADDER.items()):
        reached, in_band = CONVOY_W75_LADDER_ADMISSIBILITY[w]
        points.append(Point(f"w_geom={w:g}",
                            reached == n and in_band == n,
                            _share(stock, risk, clearances), n, w))
    return Screen("ladder-16", tuple(points))


def licence_split() -> tuple[str, tuple[float, ...]]:
    """Coefficients the two populations judge differently, and the verdict.

    Returns :data:`LICENCE_SPLIT` plus the offending `w_geom` values,
    :data:`LICENCE_AGREED` plus an empty tuple, or :data:`LICENCE_NO_OVERLAP`
    when the two populations share no coefficient at all.

    Joined on the **numeric** coefficient: the frozen null carries
    `w_geom is None` and so is correctly absent, while `w_geom=5` and
    `w_geom=5.0` are correctly the same rung. The first version of this
    function joined on the formatted labels and therefore compared `"geom
    w_geom=5.0"` against `"w_geom=5"` — dropping the single rung the two
    populations disagree about and returning :data:`LICENCE_AGREED` from a
    comparison of one element.

    The `&` is the join, not a filter applied after one, which is why this
    function sits in `guard_reflexivity`'s `&`-shaped registry: a coefficient
    present in only one population cannot disagree with itself, so restricting
    to the intersection *is* the definition of comparable. That also makes the
    empty intersection a real state rather than a degenerate one — hence
    :data:`LICENCE_NO_OVERLAP`, so "nothing disagreed" and "nothing was
    compared" stay distinguishable.

    Measured :data:`LICENCE_SPLIT` at `w_geom = 5.0` — admissible on 16 seeds
    `(16, 16)` and refused on 32. Under an all-seeds band rule admissibility
    can only be lost as seeds are added, so this is D-163's permissive licence
    a fourth time and not a conflict to adjudicate.
    """
    strict = {p.w_geom: p.admissible for p in walked_nulls().points
              if p.w_geom is not None}
    loose = {p.w_geom: p.admissible for p in ladder_rungs().points
             if p.w_geom is not None}
    shared = set(strict) & set(loose)
    if not shared:
        return LICENCE_NO_OVERLAP, ()
    split = tuple(sorted(w for w in shared if strict[w] != loose[w]))
    return (LICENCE_SPLIT if split else LICENCE_AGREED), split


def report() -> str:  # pragma: no cover - formatting
    strict, loose = walked_nulls(), ladder_rungs()
    verdict, split = licence_split()
    lines = [str(strict), str(loose), f"{verdict} {split or ''}".strip()]
    for screen in (strict, loose):
        lines.append(f"  {screen.population}:")
        for p in screen.points:
            lines.append(
                f"    {p.label:<20} "
                f"{'admissible' if p.admissible else 'refused   '} "
                f"share={p.residual_share:.4f} n={p.n_seeds}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(report())
