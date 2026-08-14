# SPDX-License-Identifier: BSD-3-Clause
"""Is `epistemic_sign.cancelling_ratio` a property of the critics, or of one scene?

D-256 reported the summed epistemic sign as a one-parameter family and put its
root at `w_epist : w_voo = 0.3587 : 1` — the weight ratio at which the repel and
attract arms cancel exactly. Q-148's four-arm A/B then places its both-arms-on
cell relative to that root. **One disc at one radius, sampled at one stride, is
a single cell**, and a number that places an experiment's arm deserves to be
asked whether it moves.

It moves, and the two axes it moves on are not the same kind of thing:

- **radius** is the scene. If the root moves here, the root is scene-dependent
  and Q-148's both-on cell must be declared per-scene. That is a finding.
- **stride** is the *sampling* of the BEV window into candidate points. It
  changes no physical quantity whatsoever. If the root moves here, the reading
  is an instrument artifact, and any radius trend read at a single stride is
  confounded by it.

Both move it. So the question this module answers is not "how much does the
root vary" but **"does the radius trend survive the sampling band"** — and it is
answered by refusing to compare two radii whose stride-ensembles overlap.

## The repel arm contributes a constant, so the "ratio" reads one arm

`ShadowCostCritic` is `w · σ` pointwise, and on the rendered BEV the EPISTEMIC
channel is exactly binary — `σ ∈ {0, 1}` — while `SHADOW_TAU = 0.5` splits
precisely on that. So the repel arm's unit-weight split is **exactly 1.0 at
every geometry and every stride** (`REPEL_SPLIT_UNIT`, pinned by test). Since
`cancelling_ratio` returns `−v₁ / s₁`, that makes it `−v₁` verbatim: not a
ratio of two measurements but a reading of the **attract arm alone**, with the
repel arm acting as a unit denominator. Every bit of the variation catalogued
below therefore belongs to `ObservationValueCritic`, whose `V(q)` is a ray
aggregate over the shadow and has no reason to be scale-free.

This is why the sweep is over the attract arm's geometry sensitivity even
though the quantity is named for both.

## What the grade means

`sweep()` returns a `RootBand` per radius — the min/max over a stride ensemble.
Two radii are `SEPARATED` only if their bands are disjoint; otherwise they are
`CONFOUNDED` and the module declines to rank them. `grade_single(value, band)`
grades a quoted single-stride number against the band it was drawn from, which
is how D-256's `0.3587` is placed: inside its band, and therefore a valid
sample whose *fourth decimal* is not.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .epistemic_sign import arm_costs, classify

# The repel arm's unit-weight split, which is a structural constant rather than
# a measurement: σ is binary on the rendered EPISTEMIC channel and SHADOW_TAU
# splits on it, so mean_exposed − mean_observed is 1 − 0 at every geometry.
REPEL_SPLIT_UNIT = 1.0

# Sampling ensemble. Coprime-ish strides spanning a ~10x range in candidate
# count, so the band is a spread over *sampling* rather than over one lattice
# alignment. Declared here, not passed per-call, so a band is never quietly
# narrowed by choosing a friendlier ensemble.
DEFAULT_STRIDES = (3, 5, 7, 11, 13, 17, 23, 31)
DEFAULT_RADII = (0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25)

SEPARATED = "SEPARATED"       # bands disjoint — the geometry difference is real
CONFOUNDED = "CONFOUNDED"     # bands overlap — sampling could explain the gap

IN_BAND = "IN_BAND"           # a quoted single-stride value its band contains
OUT_OF_BAND = "OUT_OF_BAND"   # a quoted value its own band does not contain

# Absorbs the float error in `hi - lo` so a width that *is* a power of ten does
# not read as one digit short. See `grade_single`.
_LOG_EPS = 1e-9


@dataclass(frozen=True)
class RootBand:
    """The cancelling root at one geometry, as a band over the stride ensemble.

    `lo`/`hi` are the extremes over `strides`. The band is the honest unit of
    this reading: no single stride is privileged, and the width is how much of
    the number is instrument rather than scene.
    """

    radius: float
    roots: tuple[float, ...]
    strides: tuple[int, ...]

    @property
    def lo(self) -> float:
        return min(self.roots)

    @property
    def hi(self) -> float:
        return max(self.roots)

    @property
    def mean(self) -> float:
        return float(np.mean(self.roots))

    @property
    def width(self) -> float:
        """Absolute band width — the sampling-only spread at fixed geometry."""
        return self.hi - self.lo

    @property
    def relative_width(self) -> float:
        """Band width as a fraction of the band's own mean.

        This is the number that says how much precision a single-stride quote
        can carry: a relative width of 0.35 means the fourth decimal place of
        any one sample is noise.
        """
        return self.width / self.mean if self.mean else float("nan")

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi


def repel_split_unit(radius: float = 0.5, stride: int = 13) -> float:
    """The repel arm's unit-weight split at one geometry.

    Exists to be *measured* rather than asserted: `REPEL_SPLIT_UNIT` is claimed
    to be a structural constant, and a constant nobody re-measures is a comment.
    """
    costs, sigma = arm_costs(1.0, 1.0, radius=radius, stride=stride)
    return classify(costs["ShadowCostCritic"], sigma).split


def root_at(radius: float, stride: int) -> float:
    """The cancelling `w_epist : w_voo` root at one geometry, one stride.

    Recomputed here rather than calling `epistemic_sign.cancelling_ratio` so the
    sweep pays one geometry build per cell instead of two, and so the repel
    split is available to the caller. Pinned equal to `cancelling_ratio` by
    test — two names for one number is exactly what D-047 forbids leaving
    unchecked.
    """
    costs, sigma = arm_costs(1.0, 1.0, radius=radius, stride=stride)
    s1 = classify(costs["ShadowCostCritic"], sigma).split
    v1 = classify(costs["ObservationValueCritic"], sigma).split
    if s1 <= 0.0:
        raise ValueError(
            f"repel arm is not repel at unit weight (split={s1}); the root is "
            "only defined against an opposed pair")
    return -v1 / s1


def band_at(radius: float, strides=DEFAULT_STRIDES) -> RootBand:
    """The root's band at one radius, over the whole stride ensemble."""
    strides = tuple(strides)
    if len(strides) < 2:
        raise ValueError(
            "a band needs at least two strides; a single-stride reading is a "
            "sample, not a band — that conflation is what this module exists "
            "to prevent")
    return RootBand(radius, tuple(root_at(radius, st) for st in strides), strides)


def sweep(radii=DEFAULT_RADII, strides=DEFAULT_STRIDES) -> list[RootBand]:
    return [band_at(r, strides) for r in radii]


def separation(a: RootBand, b: RootBand) -> str:
    """`SEPARATED` iff the two bands are disjoint, else `CONFOUNDED`.

    The asymmetry is deliberate: disjoint bands license the claim "these two
    geometries have different roots", overlapping bands license **nothing** —
    not "the same root", merely "this reading cannot tell". Returning a verdict
    that sounds like equality would be the same silent-vacuity shape D-241
    named, one level up.
    """
    return SEPARATED if (a.hi < b.lo or b.hi < a.lo) else CONFOUNDED


def geometry_moves_the_root(bands: list[RootBand]) -> bool:
    """True iff *some* pair of radii is `SEPARATED`.

    One separated pair is enough to kill "the root is a constant of the
    critics": no resampling can make those two geometries read alike.
    """
    return any(separation(a, b) == SEPARATED
               for i, a in enumerate(bands) for b in bands[i + 1:])


def confounded_neighbours(bands: list[RootBand]) -> list[tuple[float, float]]:
    """Adjacent radius pairs whose bands overlap — the ones not to rank.

    A single-stride sweep prints these as a clean monotone trend. They are the
    cells where that trend is not established.
    """
    return [(a.radius, b.radius)
            for a, b in zip(bands, bands[1:])
            if separation(a, b) == CONFOUNDED]


def grade_single(value: float, band: RootBand) -> tuple[str, float]:
    """Place a quoted single-stride root inside the band it was drawn from.

    Returns `(verdict, supported_decimals)`. `supported_decimals` is how many
    decimal places of `value` the band actually pins — `floor(-log10(width))`,
    floored at zero — so quoting more digits than that reports sampling noise
    as precision. This is the function that grades D-256's `0.3587`.

    The `_LOG_EPS` nudge is not cosmetic: a band built by subtracting two floats
    lands on `0.010000000000000009` rather than `0.01`, whose `-log10` is
    `1.9999999999999996`, and the bare floor would answer **1** for a width that
    pins 2 decimals by construction. The bias is toward the round number,
    exactly at the powers of ten a caller would think in.
    """
    verdict = IN_BAND if band.contains(value) else OUT_OF_BAND
    if band.width <= 0.0:
        return verdict, float("inf")
    digits = float(np.floor(-np.log10(band.width) + _LOG_EPS))
    return verdict, max(0.0, digits)


def format_sweep(bands: list[RootBand]) -> str:
    lines = [
        f"cancelling_stability — strides={bands[0].strides if bands else ()} "
        f"repel_split_unit={REPEL_SPLIT_UNIT}",
        f"  {'radius':>7} {'mean':>8} {'lo':>8} {'hi':>8} {'width':>8} {'rel':>7}",
    ]
    for b in bands:
        lines.append(
            f"  {b.radius:7.2f} {b.mean:8.4f} {b.lo:8.4f} {b.hi:8.4f} "
            f"{b.width:8.4f} {b.relative_width:7.1%}")
    conf = confounded_neighbours(bands)
    lines.append(f"  geometry_moves_the_root={geometry_moves_the_root(bands)}")
    lines.append(f"  confounded adjacent pairs: {conf if conf else 'none'}")
    return "\n".join(lines)


if __name__ == "__main__":     # pragma: no cover - manual read
    bands = sweep()
    print(format_sweep(bands))
    at_half = next(b for b in bands if b.radius == 0.5)
    verdict, digits = grade_single(0.3587, at_half)
    print(f"  D-256's 0.3587 at radius=0.5: {verdict}, "
          f"band pins {digits:.0f} decimal place(s)")
