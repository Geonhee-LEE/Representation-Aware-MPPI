# SPDX-License-Identifier: BSD-3-Clause
"""Does D-363's spread separation survive eight seeds? — the unpaired reading says no.

:mod:`excursion_tracking` finding #2 is the load-bearing claim on the
cross-track column: partition the eight scenes by forced excursion and the arm
*spread* separates with **no overlap**, excited min `0.1441` against unexcited
max `0.0730` — `1.97x`. Gradeability is made of spread, so that separation is
what says which scenes a `cte_rms_max` bar can discriminate in at all.

Its own scope note flagged the hole: both input tables are **seed 0**, so a
spread of `0.0070 m` "could in principle be dwarfed by seed noise that this
harvest cannot see", and :data:`excursion_tracking.SEED_SCOPE` has carried that
caveat unpaid since D-363. D-369 confirmed the debt is real code-side — every
`*_ENSEMBLE` on disk is `min_clearance`-valued and every cross-track harvest is
seed-0 by construction, because :data:`clearance_census.SEED_ENSEMBLE` kept only
the clearance column at harvest time.

This module pays the debt at its **binding pair** rather than across all eight
scenes. Only two numbers set the `1.97x` gap: `cafe_convoy_v0` supplies the
excited minimum and `city_curved_v0` the unexcited maximum. Widening those two
to `8 arms x 8 seeds` is **128 rollouts, 116.8 s measured**, against the 448 the
full column would cost — and no third scene can change a min-vs-max comparison
without first crossing one of these two.

**Finding #1 — the separation does not survive the unpaired reading, and it
inverts.** Per-seed arm spread, in metres:

    cafe_convoy_v0   0.1441  0.1343  0.0854  0.1376  0.0863  0.1206  0.1515  0.0612
    city_curved_v0   0.0730  0.0661  0.0127  0.0205  0.0432  0.0608  0.0260  0.0253

Seed 0 reproduces `excursion_tracking.CENSUS` to 4 dp on both scenes, so this is
the same measurement widened, not a different one. But the seed-robust form of
finding #2 — worst excited seed against best unexcited seed, the comparison a
claim of "no overlap" has to make — is `0.0612` against `0.0730`: **`0.838x`,
the wrong side of 1.** :data:`ROBUST_SEPARATION` pins the pair. The excited
scene's *worst* seed spreads less than the unexcited scene's *widest*, so the
two populations do overlap and D-363's "with no overlap" is a seed-0 statement
that a seed-width harvest contradicts.

**Finding #2 — paired by seed index it holds 8/8, and D-367's own source says
that reading is not licensed here.** On every individual seed, convoy out-
spreads curved (`8/8`, sign-test `p = 2^-8 = 0.0039`). That is the pairing D-367
imported from the `2512.24145` rider — and the *same* entry's limit #3 states
that common random numbers reduce the variance of an arm-vs-arm difference **on
a shared seed**, and say nothing about a **scene-vs-scene** contrast, where
there is no shared draw to hold common. Two scenes at seed index `s` share an
RNG seed but not the geometry that seed drives, so the `8/8` is suggestive and
is *not* the licensed reading. :data:`PAIRED_HOLDS` records it at that strength.
The honest verdict is therefore neither "refuted" nor "survives": D-363 finding
#2 must be **downgraded from `no overlap` to `holds at seed 0, unproven at seed
width`**, and :data:`VERDICT` says exactly that.

**Finding #3 — the reason the unexcited ceiling is small is not a small spread
among eight arms, it is that there are not eight arms.** On `city_curved_v0`,
**seven of the eight** arms emit *bit-identical* `cte_max` on **all eight**
seeds; only `essps_mppi` differs. The whole `0.0730` is one arm against a
seven-fold tie. This is `clearance_census`'s inert-channel signature — the one
D-367 identified as a per-seed correlation of exactly `+1.0000` — reproduced on
the cross-track column and at maximum scale: an obstacle-free scene gives seven
of eight cost functions nothing to bite on, so they collapse onto one
trajectory. :data:`EFFECTIVE_ARMS` counts the distinct rows: **2** on
`city_curved_v0` against **7** on `cafe_convoy_v0` (`geometric_mppi` reproduces
`stock_mppi`, the known inert channel).

That re-reads :data:`excursion_tracking.HIGH_LEVEL_LOW_SPREAD` on a firmer
mechanism. `city_curved_v0` was named as a scene that *looks* gradeable on the
level and is not on the spread; the sharper statement is that its arm
population is **near-degenerate**, so no bar can split it for a reason that has
nothing to do with where the bar is put. A scene with two distinct arms is not a
scene with a narrow spread — it is a scene with almost no population.

**Finding #4 — on the unexcited scene, seed noise exceeds arm spread outright.**
Intersecting the eight per-seed attained ranges (D-366/D-368's construction: a
bar inside the intersection cuts the population on *every* seed) gives
`cafe_convoy_v0` a width of **`+0.0550`** and `city_curved_v0` a width of
**`-0.0392`** — *negative*, i.e. the per-seed ranges do not all overlap.
:data:`INTERSECTION` pins both. A negative intersection width is the direct
measurement of the hypothetical `SEED_SCOPE` raised: on `city_curved_v0` the
whole arm population moves further between seeds than it spreads within one, so
no single bar value can cut it consistently across seeds at any placement. On
`cafe_convoy_v0` the intersection stays positive, so that scene remains barrable
at seed width — which is the one piece of D-363's proposal this module leaves
standing.

Scope, stated before the numbers are used:

* **Two scenes, not eight.** The other six keep their seed-0 spreads, so
  `excursion_tracking.SPREAD_SEPARATES` is widened only at its two endpoints.
  That is sufficient to *refute* the unpaired separation (a min-vs-max claim
  dies at its extremes) and **insufficient to re-derive** a corrected gap — the
  remaining scenes could reorder under seeds and this harvest cannot see it. The
  residual debt is `5 x 64 = 320` rollouts (`6 x 64 = 384` before
  `cafe_head_on_v0` was bought). :data:`REMAINING_DEBT` carries it.
* `cte_max`, not `cte_rms`. D-358's vacuous column is the RMS one;
  :mod:`cte_peak_vacuity` finding #1 measured that the peak bar grades the exact
  same partition, which is why the peak column is the admissible stand-in here.
  It is a stand-in, not the same statistic.
* Finding #3's tie is exact equality of the rounded 4-dp value on all eight
  seeds. Two arms agreeing to 4 dp on eight independent seeds is not proof of a
  shared code path, but it is the same evidence `clearance_census` uses by hand
  for `geometric_mppi`, and that case is independently known to be inert.

CLI:
    python -m eval.mppi_sandbox.excursion_seed_width   # rc=1 on drift from the seed-0 pins
"""

from __future__ import annotations

import sys

from . import excursion_tracking

#: Number of seeds in :data:`SEED_ENSEMBLE`, matching
#: :data:`clearance_census.SEEDS` so the two ensembles are positionally paired.
SEEDS = 8

#: `scene -> {arm: (cte_max,) * SEEDS}` for the two scenes that set the endpoints
#: of :data:`excursion_tracking.SPREAD_SEPARATES`. 128 closed-loop rollouts,
#: `116.8 s` measured 2026-08-19, via `run_scenario(..., seed=s)` reading
#: `metrics["cte_max"]` — the same construction as
#: :data:`cte_peak_vacuity.CTE_MAX_SEED0`, whose seed-0 column this reproduces.
SEED_ENSEMBLE: dict[str, dict[str, tuple[float, ...]]] = {
    "cafe_convoy_v0": {
        "cbf_mppi": (0.108, 0.0509, 0.0754, 0.1359, 0.0936, 0.0563, 0.1155, 0.0688),
        "essps_mppi": (0.1234, 0.1162, 0.075, 0.1261, 0.1244, 0.1154, 0.0969, 0.0843),
        "frozen_risk_mppi": (0.0626, 0.1361, 0.1459, 0.0544, 0.0745, 0.0595, 0.0473, 0.13),
        "gap_gated_mppi": (0.1923, 0.1852, 0.1445, 0.132, 0.1608, 0.1243, 0.1482, 0.1234),
        "geometric_mppi": (0.0902, 0.1467, 0.1604, 0.116, 0.1553, 0.1769, 0.0841, 0.1247),
        "risk_mppi": (0.0482, 0.0808, 0.1093, 0.1531, 0.1527, 0.122, 0.1988, 0.1193),
        "social_mppi": (0.1707, 0.1295, 0.1422, 0.192, 0.123, 0.0887, 0.1323, 0.1063),
        "stock_mppi": (0.0902, 0.1467, 0.1604, 0.116, 0.1553, 0.1769, 0.0841, 0.1247),
    },
    "city_curved_v0": {
        "cbf_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "essps_mppi": (0.3853, 0.4133, 0.4033, 0.3644, 0.4208, 0.4532, 0.4241, 0.4051),
        "frozen_risk_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "gap_gated_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "geometric_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "risk_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "social_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
        "stock_mppi": (0.4583, 0.4794, 0.3906, 0.3849, 0.464, 0.3924, 0.4501, 0.3798),
    },
    # Third scene, harvested 2026-08-20 (64 rollouts, `52.5 s`) for one purpose:
    # `tail_mean.THIRD_SCENE` graded TVaR there with no same-scene maximum to
    # contrast against, so `tail_mean.third_paired()` was `False` and the
    # cte_max-fails/TVaR-clears contrast rested on one scene. This is the
    # missing half. Two independent reproductions of the pinned seed-0 harvest:
    # every seed-0 value equals `cte_peak_vacuity.CTE_MAX_SEED0[scene]`, and the
    # seed-0 spread equals `excursion_tracking.CENSUS[scene][3]` = `0.2804`.
    "cafe_head_on_v0": {
        "cbf_mppi": (0.8632, 0.8185, 0.8756, 0.9875, 0.861, 0.9029, 0.9246, 1.037),
        "essps_mppi": (0.7063, 0.7026, 0.725, 0.7155, 0.6996, 0.7407, 0.6965, 0.7033),
        "frozen_risk_mppi": (0.6941, 0.7574, 0.7236, 0.7228, 0.8324, 0.7378, 0.7595, 0.6939),
        "gap_gated_mppi": (0.6093, 0.6126, 0.6095, 0.6148, 0.6087, 0.613, 0.6368, 0.5977),
        "geometric_mppi": (0.6093, 0.6126, 0.6095, 0.6148, 0.6087, 0.613, 0.6368, 0.5977),
        "risk_mppi": (0.8035, 0.7583, 0.7852, 0.687, 0.6836, 0.7519, 0.7202, 0.717),
        "social_mppi": (0.8897, 0.8584, 0.931, 0.863, 0.8011, 0.832, 0.8418, 0.874),
        "stock_mppi": (0.6093, 0.6126, 0.6095, 0.6148, 0.6087, 0.613, 0.6368, 0.5977),
    },
}

#: The excited scene (supplies :data:`excursion_tracking.SPREAD_SEPARATES`'s
#: minimum) and the unexcited one (its maximum), in that order.
ENDPOINTS: tuple[str, str] = ("cafe_convoy_v0", "city_curved_v0")

#: `(worst excited seed spread, widest unexcited seed spread)` in metres, 4 dp.
#: Finding #2 of D-363 claims "no overlap", which requires the first to exceed
#: the second. It does **not** — see finding #1.
#:
#: **Both endpoints are below their own scene's A-A null floor** (`0.91x`,
#: `0.96x`) — :mod:`floor_reach` carries the rows and
#: :data:`aa_calibration.BOTH_BELOW_FLOOR` the original finding. So the
#: inversion in finding #1 is undecidable rather than refuted.
ROBUST_SEPARATION: tuple[float, float] = (0.0612, 0.073)

#: `(seeds where excited out-spreads unexcited, SEEDS)`. Paired by seed index,
#: which D-367's source's limit #3 says is not licensed across scenes.
PAIRED_HOLDS: tuple[int, int] = (8, 8)

#: `scene -> number of distinct per-seed rows` — the arm population that a bar
#: on this scene actually has to split. Finding #3.
EFFECTIVE_ARMS: dict[str, int] = {
    "cafe_convoy_v0": 7, "city_curved_v0": 2, "cafe_head_on_v0": 6,
}

#: `scene -> width of the intersection of the per-seed attained ranges`, metres,
#: 4 dp. **Negative means no bar value cuts the population on every seed.**
#:
#: The positive endpoint is **not** a licence to bar convoy: `0.0550` is
#: `0.82x` of that scene's own max A-A null floor, so it is a window this
#: harness manufactures from a zero effect. See
#: :data:`floor_reach.INTERSECTION_UNDER_FLOOR`. The midpoint bar really does
#: cut all eight seeds; that verification and the floor ask different
#: questions, and only the floor bounds the claim.
#: `cafe_head_on_v0`'s `+0.2216` is the first entry here that is **not** under
#: its own scene's A-A null floor: `2.34x` the p95 floor (`0.0948`) and `2.04x`
#: the adversarial one (`0.1084`), against convoy's `0.82x`. So the bar window
#: on that scene is not a window this harness manufactures from a zero effect —
#: the caveat :data:`floor_reach.INTERSECTION_UNDER_FLOOR` carries is specific
#: to convoy and does not generalise to every positive width.
INTERSECTION: dict[str, float] = {
    "cafe_convoy_v0": 0.055, "city_curved_v0": -0.0392, "cafe_head_on_v0": 0.2216,
}

#: What this module leaves standing of D-363 finding #2, in one string. Pinned
#: so the downgrade cannot be dropped silently the way `SEED_SCOPE`'s caveat was.
VERDICT: str = "holds at seed 0; unproven at seed width (unpaired reading inverts)"

#: Rollouts still unbought: the **five** scenes whose seed-0 spreads this module
#: did not widen. A corrected separation gap needs them; a refutation did not.
#: `384 -> 320` when `cafe_head_on_v0` was harvested — the debt is derived from
#: the census in `test_seed_ensemble_prices_its_own_residual_debt`, so it cannot
#: drift from the ensemble it prices.
REMAINING_DEBT: int = 320


def per_seed_spread(scene: str) -> tuple[float, ...]:
    """Arm spread (`max - min` over arms) at each seed, seed-ordered."""
    cols = SEED_ENSEMBLE[scene]
    return tuple(
        round(max(r[s] for r in cols.values()) - min(r[s] for r in cols.values()), 4)
        for s in range(SEEDS)
    )


def robust_separation() -> tuple[float, float]:
    """`(min spread on the excited endpoint, max spread on the unexcited one)`.

    D-363 finding #2's "no overlap" holds iff the first strictly exceeds the
    second. :func:`separates` is that comparison.
    """
    exc, unexc = ENDPOINTS
    return (min(per_seed_spread(exc)), max(per_seed_spread(unexc)))


def separates() -> bool:
    """Whether the seed-robust, **unpaired** separation holds. It does not."""
    lo, hi = robust_separation()
    return lo > hi


def paired_holds() -> tuple[int, int]:
    """`(seeds on which the excited endpoint out-spreads the unexcited, SEEDS)`.

    Reported, not relied on: pairing two *scenes* by seed index has no shared
    draw to hold common (D-367's source, limit #3), so this is suggestive
    evidence and not the licensed reading. See :data:`VERDICT`.
    """
    exc, unexc = ENDPOINTS
    a, b = per_seed_spread(exc), per_seed_spread(unexc)
    return (sum(1 for s in range(SEEDS) if a[s] > b[s]), SEEDS)


def effective_arms(scene: str) -> int:
    """Distinct per-seed rows on `scene` — the population a bar must split.

    Arms whose eight values coincide to 4 dp count once. On an obstacle-free
    scene most cost channels are inert and this collapses far below eight.
    """
    return len({tuple(r) for r in SEED_ENSEMBLE[scene].values()})


def tied_arms(scene: str) -> tuple[tuple[str, ...], ...]:
    """Groups of arms sharing an identical row, sorted; singletons omitted."""
    groups: dict[tuple[float, ...], list[str]] = {}
    for arm, row in SEED_ENSEMBLE[scene].items():
        groups.setdefault(tuple(row), []).append(arm)
    return tuple(sorted(tuple(sorted(g)) for g in groups.values() if len(g) > 1))


def intersection(scene: str) -> tuple[float, float, float]:
    """`(lo, hi, width)` of the intersection of the per-seed attained ranges.

    A bar strictly inside `(lo, hi)` cuts the arm population on **every** seed;
    a non-positive width means no such value exists (D-366/D-368's construction).
    """
    cols = SEED_ENSEMBLE[scene]
    lo = max(min(r[s] for r in cols.values()) for s in range(SEEDS))
    hi = min(max(r[s] for r in cols.values()) for s in range(SEEDS))
    return (round(lo, 4), round(hi, 4), round(hi - lo, 4))


def barrable_at_seed_width() -> tuple[str, ...]:
    """Endpoint scenes whose per-seed ranges still admit a single bar value."""
    return tuple(sorted(s for s in SEED_ENSEMBLE if intersection(s)[2] > 0.0))


def seed0_agrees() -> tuple[str, ...]:
    """Scenes whose seed-0 spread here disagrees with the pinned seed-0 harvest.

    Empty is the pass: this ensemble must reproduce
    :data:`excursion_tracking.CENSUS`'s spread column at seed 0, or it is
    measuring something other than what D-363 measured.
    """
    bad = []
    for scene in sorted(SEED_ENSEMBLE):
        pinned = excursion_tracking.CENSUS[scene][3]
        if abs(per_seed_spread(scene)[0] - pinned) > 5e-5:
            bad.append(f"{scene}: seed0 {per_seed_spread(scene)[0]} != pinned {pinned}")
    return tuple(bad)


def drift() -> tuple[str, ...]:
    """Cells where the live reading disagrees with this module's own pins."""
    bad = list(seed0_agrees())
    if robust_separation() != ROBUST_SEPARATION:
        bad.append(f"robust: {robust_separation()} != {ROBUST_SEPARATION}")
    if paired_holds() != PAIRED_HOLDS:
        bad.append(f"paired: {paired_holds()} != {PAIRED_HOLDS}")
    for scene in sorted(SEED_ENSEMBLE):
        if effective_arms(scene) != EFFECTIVE_ARMS[scene]:
            bad.append(f"{scene}: arms {effective_arms(scene)} != {EFFECTIVE_ARMS[scene]}")
        if intersection(scene)[2] != INTERSECTION[scene]:
            bad.append(f"{scene}: width {intersection(scene)[2]} != {INTERSECTION[scene]}")
    return tuple(bad)


def main(argv: list[str] | None = None) -> int:
    exc, unexc = ENDPOINTS
    for scene in (exc, unexc):
        print(f"{scene:20s} spread/seed " +
              " ".join(f"{v:.4f}" for v in per_seed_spread(scene)))
        lo, hi, w = intersection(scene)
        print(f"{'':20s} arms={effective_arms(scene)}/{len(SEED_ENSEMBLE[scene])} "
              f"tied={tied_arms(scene) or '()'} intersection=({lo}, {hi}) w={w:+.4f}")
    lo, hi = robust_separation()
    print(f"\nunpaired robust: excited min {lo:.4f} vs unexcited max {hi:.4f} "
          f"-> {'SEPARATES' if separates() else 'OVERLAPS'} ({lo / hi:.3f}x)")
    print(f"paired by seed index: {paired_holds()[0]}/{paired_holds()[1]} "
          f"(reported, not licensed — cross-scene)")
    print(f"barrable at seed width: {barrable_at_seed_width() or '()'}")
    print(f"verdict: {VERDICT}")
    print(f"remaining debt: {REMAINING_DEBT} rollouts "
          f"({len(excursion_tracking.CENSUS) - len(SEED_ENSEMBLE)} scenes)")
    bad = drift()
    if bad:
        print("\nDRIFT:", *bad, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
