# SPDX-License-Identifier: BSD-3-Clause
"""The admissibility gate is a function of seed count, and the census mixes two.

Three rungs have now been walked against the all-seeds ESS band rule and all
three were refused — two of them at exactly **31/32**, one seed outside the
band (`geometric_null` head_on `w = 75`, seed 25 at ESS 134.15 above the
ceiling; `structural_null` frozen `w = 75`, seed 8 at 11.78 below the floor).
The census reads `NO_GRADED_RUNG`, coverage **0/6**.

D-171 bought a rule and this module applies it to a different object. That
rule was: *before walking a ladder in an instrument, screen the instrument* —
because the screen costs 0 sim runs and the ladder does not. D-171 screened the
**match quantity** and found it coupled to the verdict. Nobody has screened the
**admissibility gate**, and it is the gate, not the match quantity, that has
refused every rung this branch has walked.

What the screen finds
---------------------

The gate is `n_in_band == n` — an all-seeds rule, i.e. a conjunction over the
sample. If seeds are exchangeable with per-seed out-of-band rate `p`, the gate
passes with probability `(1 − p)ⁿ`. That is **strictly decreasing in n** for
every `p ∈ (0, 1)`. So:

1. **The direction needs no data.** "A smaller ensemble is a more permissive
   admissibility test" is a property of the conjunction, not a finding about
   these arms. D-163 recorded that direction three separate times as an
   empirical observation (8/8 → 31/32 being the third, D-173); all three were
   re-measuring a theorem. :func:`licence_direction` returns it as an analytic
   verdict and does not consult the data to do so.

2. **The magnitude is not identified by anything on disk.** One complete
   per-seed ESS population exists (`structural_null.FROZEN_W75_ESS`, 32 seeds,
   `k = 1` out of band). Wilson at 95% puts `p ∈ [0.0055, 0.1574]`, so
   `(1 − p)³²` ∈ `[0.0042, 0.8372]` — 83% of the unit interval. The point
   estimate says the 8-seed pre-read is ~2.14× likelier to pass than the
   32-seed walk it licenses; the interval says that ratio is anywhere in
   `[1.14, 60.9]`. This module reports the point estimate **and** the interval, and
   its verdict on the magnitude is `MAGNITUDE_UNIDENTIFIED`, because this
   branch has been bitten three times (D-167 0.7725, D-168 0.0485, D-169) by a
   number quoted from a knob nobody showed was inert.

3. **The census grades two populations with two different gates.** D-170's
   `matched_ladder` selects rungs by **16-seed** ladder-admissibility
   (`CONVOY_W75_LADDER_ADMISSIBILITY`, `HEADON_W75_LADDER_ADMISSIBILITY`) while
   the walked rungs it grades are refused at **32**. By (1) those are not the
   same predicate and the 16-seed one is the looser of the two, in the
   direction that admits ladder rungs the walk would refuse.
   :func:`predicate_match` answers this for a pair of seed counts and
   :func:`census_predicate_reading` applies it to the census's own two numbers.

Why this is not an argument for relaxing the rule
--------------------------------------------------

It is not. D-170 alternative (b)/(c) already refused loosening admissibility to
rescue a number, and nothing here reopens that — the all-seeds rule is the
right rule and `31/32` is a real refusal. The finding is narrower and it cuts
the other way: a refusal rate measured at one `n` **may not be quoted at
another**, and the census currently does exactly that. The fix is to state the
`n` beside every admissibility reading, not to weaken the gate.

Everything here is arithmetic over recorded floats: **0 sim runs**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "MONOTONE_PERMISSIVE",
    "DEGENERATE_RATE",
    "NO_POPULATION",
    "MAGNITUDE_UNIDENTIFIED",
    "MAGNITUDE_IDENTIFIED",
    "SAME_PREDICATE",
    "PREDICATE_DIFFERS_BY_N",
    "WILSON_Z",
    "LadderRate",
    "LicenceReading",
    "out_of_band",
    "wilson_interval",
    "all_seeds_pass",
    "licence_direction",
    "licence_reading",
    "predicate_match",
    "census_predicate_reading",
    "CENSUS_LADDER_SEEDS",
    "CENSUS_WALK_SEEDS",
]


#: The analytic verdict of :func:`licence_direction`. `(1 − p)ⁿ` is strictly
#: decreasing in `n` for every `p ∈ (0, 1)`, so a smaller ensemble is always
#: the more permissive all-seeds test. Returned **without reading the data**.
MONOTONE_PERMISSIVE = "MONOTONE_PERMISSIVE"

#: `p == 0` or `p == 1`: the gate is constant in `n` and the direction above is
#: vacuous. A recorded population with zero out-of-band seeds lands here, and
#: it is not evidence that seed count does not matter — it is evidence that
#: this population cannot see whether it does. Fail-closed: distinct from
#: :data:`MONOTONE_PERMISSIVE`, never folded into it.
DEGENERATE_RATE = "DEGENERATE_RATE"

#: No per-seed ESS values were supplied. A rate over an empty sample and a rate
#: of zero print alike and only one of them is a measurement (D-183's shape:
#: an empty diff and "nothing changed" are the same string).
NO_POPULATION = "NO_POPULATION"

#: The interval on `p` is wide enough that `(1 − p)ⁿ` spans more than
#: :data:`IDENTIFICATION_SPAN` of the unit interval — the pass probability is
#: not pinned by this population, only its direction is.
MAGNITUDE_UNIDENTIFIED = "MAGNITUDE_UNIDENTIFIED"

#: The interval is tight enough to quote a magnitude. Not reached by any
#: population currently on disk; present so the verdict is two-sided rather
#: than a constant wearing a verdict's name.
MAGNITUDE_IDENTIFIED = "MAGNITUDE_IDENTIFIED"

#: Two readings were taken at the same `n`, so the same predicate graded both.
SAME_PREDICATE = "SAME_PREDICATE"

#: Two readings were taken at different `n`. By :data:`MONOTONE_PERMISSIVE`
#: they are different predicates and the smaller `n` is the looser one — so
#: neither reading's admissibility may be quoted about the other's population.
PREDICATE_DIFFERS_BY_N = "PREDICATE_DIFFERS_BY_N"

#: Two-sided 95%.
WILSON_Z = 1.959963984540054

#: Fraction of the unit interval the pass-probability CI may span and still be
#: called identified. Deliberately generous: at 0.25 the recorded population
#: still fails, and a threshold that only just fails is not the reason.
IDENTIFICATION_SPAN = 0.25

#: The two seed counts the census actually mixes. Ladder rungs are walked at 16
#: (`geometric_null` lines 402, 713, 812 — "The ladder is walked at 16 seeds
#: and the recorded arms hold 32"), the graded walks at 32. Held here as data
#: so :func:`census_predicate_reading` states the mix rather than asserting it.
CENSUS_LADDER_SEEDS = 16
CENSUS_WALK_SEEDS = 32


@dataclass(frozen=True)
class LadderRate:
    """A per-seed out-of-band count over one recorded ESS population."""

    k: int
    n: int

    @property
    def rate(self) -> float | None:
        """`k / n`, or `None` on an empty population — never `0.0`."""
        return None if self.n == 0 else self.k / self.n


@dataclass(frozen=True)
class LicenceReading:
    """What one recorded population licenses about the all-seeds gate."""

    rate: LadderRate
    interval: tuple[float, float]
    #: Seed counts compared: the cheap pre-read and the walk it licenses.
    n_cheap: int
    n_walk: int

    @property
    def point_pass_cheap(self) -> float | None:
        p = self.rate.rate
        return None if p is None else all_seeds_pass(p, self.n_cheap)

    @property
    def point_pass_walk(self) -> float | None:
        p = self.rate.rate
        return None if p is None else all_seeds_pass(p, self.n_walk)

    @property
    def point_ratio(self) -> float | None:
        """How much likelier the cheap read is to pass than the walk."""
        cheap, walk = self.point_pass_cheap, self.point_pass_walk
        if cheap is None or walk is None or walk == 0.0:
            return None
        return cheap / walk

    @property
    def walk_pass_interval(self) -> tuple[float, float] | None:
        """`(1 − p)ⁿ` over the CI on `p`. Decreasing in `p`, so the ends swap."""
        if self.rate.rate is None:
            return None
        lo, hi = self.interval
        return (all_seeds_pass(hi, self.n_walk), all_seeds_pass(lo, self.n_walk))

    @property
    def magnitude(self) -> str:
        """Is the pass probability pinned by this population, or only signed?"""
        span = self.walk_pass_interval
        if span is None:
            return NO_POPULATION
        return (
            MAGNITUDE_IDENTIFIED
            if (span[1] - span[0]) <= IDENTIFICATION_SPAN
            else MAGNITUDE_UNIDENTIFIED
        )

    @property
    def direction(self) -> str:
        return licence_direction(self.rate.rate)

    def summary(self) -> str:
        p = self.rate.rate
        if p is None:
            return f"[{NO_POPULATION}] no per-seed ESS on this population"
        span = self.walk_pass_interval
        assert span is not None
        return (
            f"[{self.direction}/{self.magnitude}] "
            f"p={self.rate.k}/{self.rate.n}={p:.4f} "
            f"CI=[{self.interval[0]:.4f}, {self.interval[1]:.4f}] "
            f"pass(n={self.n_cheap})={self.point_pass_cheap:.4f} "
            f"pass(n={self.n_walk})={self.point_pass_walk:.4f} "
            f"in [{span[0]:.4f}, {span[1]:.4f}] "
            f"ratio={self.point_ratio:.4f}"
        )


def out_of_band(ess, band: tuple[float, float]) -> LadderRate:
    """Count seeds outside `band` (inclusive ends, as `ab.assert_ess_in_band`)."""
    lo, hi = band
    values = tuple(ess)
    k = sum(1 for e in values if e < lo or e > hi)
    return LadderRate(k=k, n=len(values))


def wilson_interval(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    """Wilson score interval on `k/n`, clamped to `[0, 1]`.

    Wilson rather than normal-approximation, and the recorded population is
    exactly why: at `k = 1, n = 32` the normal interval's lower end is
    **−0.029**, so it must be clamped to zero — which reports `p = 0` as
    attainable and hence `(1 − p)³²` as possibly `1.0`, i.e. "seed count might
    not matter at all". Wilson's lower end is **+0.0055**, strictly positive,
    and it is the strict positivity that makes the pass probability strictly
    less than one at every `n`. The clamps below are therefore inert on this
    population and present only for the general case.
    """
    if n == 0:
        return (0.0, 1.0)
    phat = k / n
    denom = 1.0 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return (max(0.0, centre - half), min(1.0, centre + half))


def all_seeds_pass(p: float, n: int) -> float:
    """`(1 − p)ⁿ` — the all-seeds gate's pass probability at rate `p`."""
    return (1.0 - p) ** n


def licence_direction(p: float | None) -> str:
    """Does a smaller ensemble pass the all-seeds gate more easily?

    Analytic. `(1 − p)ⁿ` is strictly decreasing in `n` whenever
    `0 < p < 1`, so the answer is :data:`MONOTONE_PERMISSIVE` for **every**
    non-degenerate rate and the data is consulted only to rule the degenerate
    cases out. This is the point of the function: D-163 spent three separate
    measurements establishing a direction that follows from the shape of the
    conjunction.
    """
    if p is None:
        return NO_POPULATION
    if p <= 0.0 or p >= 1.0:
        return DEGENERATE_RATE
    return MONOTONE_PERMISSIVE


def licence_reading(
    ess, band: tuple[float, float], n_cheap: int, n_walk: int
) -> LicenceReading:
    rate = out_of_band(ess, band)
    return LicenceReading(
        rate=rate,
        interval=wilson_interval(rate.k, rate.n),
        n_cheap=n_cheap,
        n_walk=n_walk,
    )


def predicate_match(n_a: int, n_b: int) -> str:
    """Are two admissibility readings taken at `n_a` and `n_b` comparable?"""
    return SAME_PREDICATE if n_a == n_b else PREDICATE_DIFFERS_BY_N


def census_predicate_reading() -> str:
    """The census's own mix: 16-seed ladder admissibility vs 32-seed walks.

    D-170 builds `matched_ladder` out of rungs that are ladder-admissible at
    :data:`CENSUS_LADDER_SEEDS` and grades walks refused at
    :data:`CENSUS_WALK_SEEDS`. This returns what that mix is.
    """
    return predicate_match(CENSUS_LADDER_SEEDS, CENSUS_WALK_SEEDS)


def recorded_reading() -> LicenceReading:
    """The one complete per-seed ESS population on disk.

    Imported lazily so this module stays arithmetic-over-floats for every
    caller that brings its own population.
    """
    from eval.mppi_sandbox import structural_null as sn

    return licence_reading(
        sn.FROZEN_W75_ESS,
        sn.FROZEN_ESS_BAND,
        n_cheap=int(sn.FROZEN_PREREAD["n"]),  # type: ignore[arg-type]
        n_walk=len(sn.FROZEN_W75_ESS),
    )


def main(argv: list[str] | None = None) -> int:
    reading = recorded_reading()
    print(f"seed_count_licence — {reading.summary()}")
    print(f"seed_count_licence — census gate mix: {census_predicate_reading()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
