"""Can the arms be compared **without choosing a threshold at all**? (STATE #1)

The margin route is closed in both directions. D-164 censused the three
eligible scenes at their *declared* margins and closed at `0/3` two-sided;
D-165 asked the successor question — a margin **derived** from the recorded
clearances — and got `SINGLE_SCENE_STABLE`, 2 of 6 rungs and 1 of 3 scenes,
both on the scene that was already published. Neither route enlarges the
population, and the reason D-165 gives is structural rather than unlucky: a
margin is a length in metres, clearance scale is a **scene** property, so no
one threshold serves the matrix.

`research/feed.md`'s 2026-08-10 entry (arxiv 2605.18045) names the move that
does not require one. Both of its instruments are functions of the two arms'
clearance *distributions* rather than of a threshold applied to them, so they
are defined on exactly the rungs the census had to drop:

- **A rank statistic.** :attr:`RungComparison.superiority` is
  `A = P(risk > stock) + ½·P(risk = stock)` over all `32 × 32` cross-arm pairs.
  Its margin-freeness is not a convention — it is an identity. The unsafe-rate
  difference the census grades at threshold `m` is
  `F_stock(m) − F_risk(m)`, and `A = ∫ F_stock dF_risk`, i.e. `A` **aggregates
  that same comparison over every threshold at once**, weighted by where the
  runs actually landed. Any monotone re-choice of margin leaves it fixed.
- **A paired bootstrap.** The two arms are run on the *same* seeds
  (:func:`separation_reproduction.reproduction_at` slices both arms with one
  index range), so index `i` is one seed's two outcomes and the difference is
  paired. :meth:`RungComparison.equivalence` reads a TOST verdict off the
  bootstrap CI of the mean paired difference — including `EQUIVALENT`, the
  "indistinguishable at effect size ε" answer that floor/ceiling censoring
  makes structurally unreachable, because a censored rung has *no* threshold at
  which either arm is interior.

The measured answer, and it is not the one the branch has been getting
---------------------------------------------------------------------

**Coverage is 6/6 rungs and 3/3 scenes** (:attr:`MarginFreeCensus.coverage`),
against the derived route's 2/6 and 1/3. Every rung the two margin censuses had
to drop has a margin-free reading, so the population was never the problem; the
instrument was.

**And the censoring is *anti*-informative** — :attr:`censoring_alignment` reads
:data:`CENSORING_ANTI_INFORMATIVE`. Rank the six rungs by effect size and the
three the margin route calls `NO_TWO_SIDED_TO_SPREAD` — the verdict meaning *no
threshold exists over the reals* — are the three **largest**: convoy `w = 75` at
`A = 1.0000` (perfect separation, the arms' clearance ranges are disjoint),
head_on `w ∈ {75, 100}` at `0.9980`. The three it can score sit strictly below
them, at `0.9473`, `0.8457`, `0.4980`. The separation is strict in both
directions: `min |A − ½|` over the censored rungs is `0.4980`, `max` over the
scored ones is `0.4473`. A rung is unscoreable by threshold **because** the arms
separate so completely that no threshold has both of them interior — so the
census was systematically discarding its own strongest evidence, and "0/3
two-sided" was never a statement about the arms.

The one rung where the margin choice **decides** the verdict is the
tie
---------------------------------------------------------------------

D-164 found `crossing w = 250` spreading 46 two-sided thresholds over four
verdicts with no majority and read it as the threshold picking the answer. It
is: margin-free, that rung is `A = 0.4980`, a coin flip, and its bootstrap CI on
the paired difference **contains zero**. `MARGIN_DECIDES_VERDICT` and "there is
no effect to find" are the same fact seen twice — with no signal, whatever the
threshold selects is what gets reported. So the branch's most threshold-
dependent result is also its only measured *tie*, and that tie is now a positive
finding (`EQUIVALENT` at a stated ε) rather than an absence.

What this does **not** license
------------------------------

`A` orders two **clearance distributions**; it is not a safety claim and does
not move the headline. `unsafe_rate` is `0.0000` at every declared margin
precisely because both arms clear those floors — the same censoring, read from
the other side. "The risk arm holds more clearance on 5 of 6 rungs" and "the
risk arm is safer at the declared threshold" are different statements and only
the first is measured here. Nor is the direction free of the branch's known
caveats: these are the D-152/153/160/164 walks, so the 8-seed licence question
(D-163) and the single-scene-per-weight coverage are inherited unchanged.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from .derived_margin import RungDerivation, walked_rungs
from .scene_transplant import MARGIN_DECIDES_VERDICT, NO_TWO_SIDED_TO_SPREAD

#: The bootstrap CI of the mean paired difference lies entirely inside
#: `(−ε, +ε)`: the arms are indistinguishable *at that effect size*. This is the
#: verdict censoring makes unreachable — a censored rung has no threshold at
#: which both arms are interior, so it cannot report agreement either.
EQUIVALENT = "EQUIVALENT"

#: The CI excludes zero and reaches outside `(−ε, +ε)` on the positive side —
#: the `b` arm holds more clearance by more than ε.
SUPERIOR = "SUPERIOR"

#: The mirror of :data:`SUPERIOR`. Nothing in the eligible population reads it;
#: kept because a one-sided instrument could not tell the two apart.
INFERIOR = "INFERIOR"

#: The CI straddles an ε boundary — neither equivalence nor a difference is
#: resolvable at this ε and this n. Distinct from :data:`EQUIVALENT`: one says
#: the arms agree, the other says the data cannot say.
INDETERMINATE = "INDETERMINATE"

#: Every threshold-censored rung separates the arms **more** than every rung the
#: threshold route can score. The censoring discards the strongest evidence.
CENSORING_ANTI_INFORMATIVE = "CENSORING_ANTI_INFORMATIVE"

#: The mirror: every scoreable rung separates at least as much as every censored
#: one, i.e. the threshold route drops only rungs that had little to say.
CENSORING_ALIGNED = "CENSORING_ALIGNED"

#: The two groups' effect sizes interleave — censoring is uninformative about
#: effect size rather than pointing either way.
CENSORING_MIXED = "CENSORING_MIXED"

#: Fewer than one rung on each side of the censoring split, so the comparison
#: has no content. Not reachable from the shipped population; present because
#: an empty-population reading that looks like a verdict is D-107's shape.
CENSORING_UNCOMPARABLE = "CENSORING_UNCOMPARABLE"


def superiority(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """`P(b > a) + ½·P(b = a)` over all cross pairs — the rank statistic.

    Computed exactly (all `len(a) × len(b)` pairs) rather than sampled, so the
    reading is a constant of the recorded runs and not of an RNG seed.
    """
    if not a or not b:
        raise ValueError("superiority needs a non-empty sample from each arm")
    wins = sum(1.0 if y > x else 0.5 if y == x else 0.0 for x in a for y in b)
    return wins / (len(a) * len(b))


@dataclass(frozen=True)
class RungComparison:
    """One walked rung compared without reference to any threshold."""

    scenario: str
    weight: float
    #: Whichever margin the rung was *published* against — carried so the
    #: threshold and threshold-free readings can be put side by side, never
    #: used in any statistic on this class.
    declared_margin: float
    #: The margin route's reading: `NO_TWO_SIDED_TO_SPREAD` / `MARGIN_INERT` /
    #: `MARGIN_DECIDES_VERDICT`.
    censoring: str
    stock: tuple[float, ...]
    risk: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.stock) != len(self.risk):
            raise ValueError(
                f"{self.scenario} w={self.weight:g}: {len(self.stock)} stock "
                f"clearances against {len(self.risk)} risk — the arms are "
                "paired by seed index, so unequal lengths mean the pairing is "
                "not what this class assumes")

    @property
    def n(self) -> int:
        return len(self.stock)

    @property
    def superiority(self) -> float:
        """`A = P(risk > stock) + ½·P(=)`. Invariant under any monotone
        re-choice of margin — see the module docstring's identity."""
        return superiority(self.stock, self.risk)

    @property
    def effect(self) -> float:
        """`|A − ½|` — separation magnitude, direction dropped. This is the
        quantity :attr:`MarginFreeCensus.censoring_alignment` ranks on."""
        return abs(self.superiority - 0.5)

    @property
    def paired_delta(self) -> float:
        """Mean per-seed `risk − stock`, in metres. Paired because both arms
        were run on the same seed at the same index."""
        return statistics.fmean(y - x for x, y in zip(self.stock, self.risk))

    def bootstrap_ci(self, *, reps: int = 2000, alpha: float = 0.05,
                     seed: int = 0) -> tuple[float, float]:
        """Percentile CI of :attr:`paired_delta`, resampling **seeds** (not
        arms) so the pairing survives every resample.

        Seeded and therefore reproducible: two calls with the same arguments on
        the same rung return the same interval, which is what lets a test pin
        an equivalence verdict at all.
        """
        if reps < 1:
            raise ValueError("bootstrap_ci needs at least one replicate")
        diffs = [y - x for x, y in zip(self.stock, self.risk)]
        rng = random.Random(seed)
        n = len(diffs)
        means = sorted(
            statistics.fmean(diffs[rng.randrange(n)] for _ in range(n))
            for _ in range(reps))
        lo = means[int((alpha / 2) * reps)]
        hi = means[min(reps - 1, int((1 - alpha / 2) * reps))]
        return lo, hi

    def equivalence(self, eps: float, *, reps: int = 2000, alpha: float = 0.05,
                    seed: int = 0) -> str:
        """TOST verdict at effect size `eps` metres, read off the bootstrap CI.

        `eps` is a tolerance on the **difference between the arms**, not a
        safety threshold on clearance: it says how close the two distributions
        must sit to count as the same, and no run is ever graded pass/fail
        against it. That is what keeps the censoring out.
        """
        if eps <= 0:
            raise ValueError("equivalence needs a positive effect size")
        lo, hi = self.bootstrap_ci(reps=reps, alpha=alpha, seed=seed)
        if -eps < lo and hi < eps:
            return EQUIVALENT
        if lo >= eps:
            return SUPERIOR
        if hi <= -eps:
            return INFERIOR
        return INDETERMINATE

    def equivalence_margin(self, *, reps: int = 2000, alpha: float = 0.05,
                           seed: int = 0) -> float:
        """The smallest `eps` at which this rung reads :data:`EQUIVALENT`.

        Reported instead of picking one project-wide ε, because ε is exactly
        the kind of magnitude the branch has now twice chosen wrong (D-164's
        declared margins, D-165's derived ones). A scalar the reader compares
        to their own tolerance cannot be mis-declared on their behalf.
        """
        lo, hi = self.bootstrap_ci(reps=reps, alpha=alpha, seed=seed)
        return max(abs(lo), abs(hi))

    @property
    def separated(self) -> bool:
        """Does the bootstrap CI exclude zero? Weaker than
        :data:`SUPERIOR` — this asks only for a sign, not for a magnitude
        beyond ε."""
        lo, hi = self.bootstrap_ci()
        return lo > 0 or hi < 0

    @property
    def margin_censored(self) -> bool:
        """Did the threshold route find **no** two-sided margin here? These are
        the rungs both prior censuses had to drop."""
        return self.censoring == NO_TWO_SIDED_TO_SPREAD

    def __str__(self) -> str:
        return (f"{self.scenario} w={self.weight:g} :: A={self.superiority:.4f} "
                f"delta={self.paired_delta:+.4f}m n={self.n} "
                f"[{self.censoring}]")


@dataclass(frozen=True)
class MarginFreeCensus:
    """All six walked rungs, compared without a threshold."""

    rungs: tuple[RungComparison, ...]

    @property
    def scenes(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(r.scenario for r in self.rungs))

    @property
    def coverage(self) -> tuple[int, int, int, int]:
        """`(rungs read, rungs walked, scenes read, scenes walked)`.

        Every rung with recorded clearances has a rank statistic — `A` is
        defined on any two non-empty samples — so this is `(n, n, s, s)` by
        construction. It is computed rather than asserted because the whole
        point is the contrast with the derived route's `(2, 6, 1, 3)`, and a
        hard-coded `6/6` would not notice a rung going missing.
        """
        return (len(self.rungs), len(walked_rungs()),
                len(self.scenes), len(set(r.scenario for r in walked_rungs())))

    @property
    def censored(self) -> tuple[RungComparison, ...]:
        """Rungs the threshold route cannot score at any margin."""
        return tuple(r for r in self.rungs if r.margin_censored)

    @property
    def scoreable(self) -> tuple[RungComparison, ...]:
        return tuple(r for r in self.rungs if not r.margin_censored)

    @property
    def censoring_alignment(self) -> str:
        """Does being threshold-censored predict a *smaller* effect, as the
        censuses' "nothing to see here" reading assumed, or a larger one?

        Compared as two strictly separated groups rather than by a correlation:
        with six points a correlation coefficient is noise, while "every
        censored rung beats every scoreable one" is a statement six points can
        actually support.
        """
        if not self.censored or not self.scoreable:
            return CENSORING_UNCOMPARABLE
        censored = [r.effect for r in self.censored]
        scoreable = [r.effect for r in self.scoreable]
        if min(censored) > max(scoreable):
            return CENSORING_ANTI_INFORMATIVE
        if min(scoreable) > max(censored):
            return CENSORING_ALIGNED
        return CENSORING_MIXED

    @property
    def decided_by_margin(self) -> tuple[RungComparison, ...]:
        """The rungs where D-164 found the threshold choice picking the
        verdict."""
        return tuple(r for r in self.rungs
                     if r.censoring == MARGIN_DECIDES_VERDICT)

    @property
    def ties(self) -> tuple[RungComparison, ...]:
        """Rungs whose paired CI contains zero — no resolvable direction."""
        return tuple(r for r in self.rungs if not r.separated)

    @property
    def favouring_risk(self) -> tuple[RungComparison, ...]:
        return tuple(r for r in self.rungs if r.superiority > 0.5)

    @property
    def verdict(self) -> str:
        return self.censoring_alignment

    def __str__(self) -> str:
        nr, tr, ns, ts = self.coverage
        return (f"MarginFreeCensus {self.verdict}: rungs {nr}/{tr}, "
                f"scenes {ns}/{ts}, favouring risk "
                f"{len(self.favouring_risk)}/{nr}, ties {len(self.ties)}")


def _comparison(rung: RungDerivation) -> RungComparison:
    pooled = rung.sweep.reproduction.pooled
    return RungComparison(
        scenario=rung.scenario,
        weight=rung.weight,
        declared_margin=rung.declared_margin,
        censoring=rung.decides,
        stock=tuple(pooled.a.clearances),
        risk=tuple(pooled.b.clearances),
    )


def comparisons() -> tuple[RungComparison, ...]:
    """The six walked rungs as threshold-free comparisons.

    Built off :func:`derived_margin.walked_rungs` rather than off a second copy
    of the population, so the two censuses cannot drift apart on *which* rungs
    they read — the contrast between their coverages is only meaningful if the
    denominators are the same object.
    """
    return tuple(_comparison(r) for r in walked_rungs())


def census() -> MarginFreeCensus:
    """The measured answer: `CENSORING_ANTI_INFORMATIVE`, 6/6 rungs, 3/3
    scenes."""
    return MarginFreeCensus(rungs=comparisons())


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    c = census()
    print(c)
    for r in sorted(c.rungs, key=lambda r: -r.effect):
        lo, hi = r.bootstrap_ci()
        print(f"  {r} CI=[{lo:+.4f}, {hi:+.4f}] "
              f"eps_equiv={r.equivalence_margin():.4f}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
