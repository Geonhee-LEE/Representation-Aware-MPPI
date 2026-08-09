# SPDX-License-Identifier: BSD-3-Clause
"""`separation_reproduction` — the one-run rung, measured a second time.

Three separable things are under test. The **grade**: what a pair of disjoint
blocks says about a separation, including the case where the reference had none
to begin with. The **refusals**: a pair that shares seeds, or that is not two
measurements of the same rung, is not a replication and is rejected at
construction rather than graded. And the **measurement**: the walk recorded in
`W250_CLEARANCES` has to reproduce D-133's block before its disagreement on the
fresh block means anything — a pipeline that could not re-derive the old answer
would not be entitled to a new one (D-139's rule).

A fourth arrived with the second walk. `W150_CLEARANCES` grades `REPRODUCED`
where `W250_CLEARANCES` graded `SIGN_REVERSED`, so the two recorded walks now
**disagree** — which is what makes the measurement tests non-vacuous, since a
`verdict` hard-coded to either constant used to pass all of them. And the
**census** is the population question the single-rung grade cannot answer: of
the rungs the band's shape rests on, which have been looked at twice.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox.comparison_headroom import (
    NO_HEADROOM_SAFE,
    SEPARATED,
    TIED,
    ArmSafety,
    Headroom,
)
from eval.mppi_sandbox.scorable_band import (
    PUBLISHED_ARMS,
    PUBLISHED_LADDER,
    PUBLISHED_LAM,
    PUBLISHED_MARGIN,
    PUBLISHED_SCENARIO,
    PUBLISHED_SEEDS,
    BandRung,
)
from eval.mppi_sandbox.separation_reproduction import (
    BOTH_ARMS_CENSORED,
    CEILING,
    FLOOR,
    FULLY_REPLICATED,
    NO_SEPARATED_RUNG,
    ONE_ARM_CENSORED,
    NO_SEPARATION_TO_REPRODUCE,
    NOT_REPRODUCED,
    PARTIALLY_REPLICATED,
    REPRODUCED,
    SIGN_REVERSED,
    UNCENSORED,
    UNREPLICATED,
    W100_CLEARANCES,
    W100_REFERENCE_SEEDS,
    W150_CLEARANCES,
    W150_REFERENCE_SEEDS,
    W250_CLEARANCES,
    W250_REFERENCE_SEEDS,
    OverlappingBlocks,
    ReplicationCensus,
    Reproduction,
    SeedBlock,
    published_census,
    w100_reproduction,
    w150_reproduction,
    w250_reproduction,
)

STOCK, RISK = PUBLISHED_ARMS
SAFE, UNSAFE = 0.60, 0.30


def _arm(name: str, unsafe: int, n: int) -> ArmSafety:
    return ArmSafety(arm=name,
                     clearances=(UNSAFE,) * unsafe + (SAFE,) * (n - unsafe),
                     margin=PUBLISHED_MARGIN)


def _block(lo: int, n: int, n_stock: int, n_risk: int,
           weight: float = 250.0, lam: float = PUBLISHED_LAM,
           scenario: str = PUBLISHED_SCENARIO) -> SeedBlock:
    return SeedBlock(
        seeds=tuple(range(lo, lo + n)),
        headroom=Headroom(scenario=scenario, weight=weight, lam=lam,
                          a=_arm(STOCK, n_stock, n), b=_arm(RISK, n_risk, n)),
    )


# --- the grade ---------------------------------------------------------------

@pytest.mark.parametrize("ref, rep, expected", [
    # reference separates one way, replication the same way
    ((0, 2), (0, 2), REPRODUCED),
    # ... the other way: the sign the reference carried was the seeds'
    ((0, 2), (2, 0), SIGN_REVERSED),
    # ... replication finds no separation at all
    ((0, 2), (1, 1), NOT_REPRODUCED),
    # ... reference never separated, so nothing was replicated
    ((1, 1), (0, 2), NO_SEPARATION_TO_REPRODUCE),
    ((1, 1), (1, 1), NO_SEPARATION_TO_REPRODUCE),
])
def test_verdict_over_the_four_cases(ref, rep, expected):
    r = Reproduction(reference=_block(0, 8, *ref),
                     replication=_block(8, 8, *rep))
    assert r.verdict == expected


def test_an_unscorable_reference_is_not_a_reproduction():
    """`NO_SEPARATION_TO_REPRODUCE` covers the unscorable reference too.

    A block where every run held the margin is `NO_HEADROOM_SAFE`, not a null
    separation — and it must not read as agreement just because the replication
    also failed to separate. This is the case that made the constant necessary:
    both blocks look identical in every field, and only the verdict says the
    question was never asked.
    """
    ref = _block(0, 8, 0, 0)
    assert ref.verdict == NO_HEADROOM_SAFE
    r = Reproduction(reference=ref, replication=_block(8, 8, 0, 0))
    assert r.verdict == NO_SEPARATION_TO_REPRODUCE


def test_pooled_is_the_whole_ensemble():
    r = Reproduction(reference=_block(0, 8, 0, 2),
                     replication=_block(8, 8, 2, 0))
    assert r.seeds == tuple(range(16))
    pooled = r.pooled
    assert len(pooled.a.clearances) == 16
    assert pooled.a.unsafe_rate == pooled.b.unsafe_rate == 2 / 16
    assert pooled.verdict == TIED


# --- the refusals ------------------------------------------------------------

def test_overlapping_blocks_are_refused():
    with pytest.raises(OverlappingBlocks, match="share seeds"):
        Reproduction(reference=_block(0, 8, 0, 2),
                     replication=_block(4, 8, 0, 2))


@pytest.mark.parametrize("kwargs", [
    {"weight": 100.0},
    {"lam": 0.4},
    {"scenario": "cafe_convoy_v0"},
])
def test_blocks_must_measure_the_same_rung(kwargs):
    with pytest.raises(ValueError, match="not two measurements"):
        Reproduction(reference=_block(0, 8, 0, 2),
                     replication=_block(8, 8, 0, 2, **kwargs))


def test_a_block_must_name_one_seed_per_run():
    with pytest.raises(ValueError, match="cannot say which"):
        SeedBlock(seeds=(0, 1, 2), headroom=_block(0, 8, 0, 2).headroom)


def test_a_block_may_not_repeat_a_seed():
    with pytest.raises(ValueError, match="seeds repeat"):
        SeedBlock(seeds=(0,) * 8, headroom=_block(0, 8, 0, 2).headroom)


# --- the measurement ---------------------------------------------------------

def test_the_reference_block_reproduces_the_published_rung():
    """D-133's `w = 250` row, re-walked. This is the entitlement check.

    The fresh block's disagreement is only evidence if the walk that produced
    it can re-derive the answer already on record. `PUBLISHED_LADDER` is not
    amended by this cycle — it stays the record of its own 16 seeds — so the
    two are compared, not merged.
    """
    recorded = {w: (a, b) for w, a, b, _, _ in PUBLISHED_LADDER}
    n_stock, n_risk = recorded[250.0]
    ref = w250_reproduction().reference
    assert len(ref.seeds) == PUBLISHED_SEEDS == W250_REFERENCE_SEEDS
    assert ref.headroom.a.unsafe_rate == n_stock / PUBLISHED_SEEDS == 0.0
    assert ref.headroom.b.unsafe_rate == n_risk / PUBLISHED_SEEDS == 1 / 16
    assert ref.verdict == SEPARATED


def test_the_witness_run_is_the_one_the_band_quotes():
    """`scorable_band`'s docstring names the 0.3472 m run by its magnitude.

    Reproduced to four decimals, on `risk_mppi` and inside the reference block
    — so the prose and the measurement are pinned to each other rather than
    both being maintained by hand.
    """
    risk = W250_CLEARANCES[RISK][:W250_REFERENCE_SEEDS]
    assert min(risk) == pytest.approx(0.3472, abs=5e-5)
    assert sum(c < PUBLISHED_MARGIN for c in risk) == 1


def test_the_separation_reverses_and_pools_to_tied():
    """The finding: at 32 seeds the rung is a null, not a delta against risk."""
    r = w250_reproduction()
    assert r.verdict == SIGN_REVERSED
    assert r.reference.delta_unsafe == pytest.approx(+1 / 16)
    assert r.replication.delta_unsafe == pytest.approx(-1 / 16)
    assert r.pooled.verdict == TIED
    assert r.pooled.a.unsafe_rate == r.pooled.b.unsafe_rate == 1 / 32


def test_the_pooled_rung_leaves_one_run_rungs():
    """What the reversal costs the band: the rung stops being a one-run rung.

    It stays `scorable` — `TIED` is in `SCORABLE`, so `published_band()`'s
    `BAND_SPLIT` is untouched — but `separation_runs` goes 1 → 0, which is the
    exact predicate `ScorableBand.one_run_rungs` selects on. The structural
    claim no longer rests on a single seed.
    """
    pooled = BandRung(headroom=w250_reproduction().pooled, ess_in_band=True)
    assert pooled.scorable
    assert pooled.separation_runs == 0

    published = BandRung(
        headroom=Headroom(
            scenario=PUBLISHED_SCENARIO, weight=250.0, lam=PUBLISHED_LAM,
            a=_arm(STOCK, 0, PUBLISHED_SEEDS), b=_arm(RISK, 1, PUBLISHED_SEEDS)),
        ess_in_band=True)
    assert published.separation_runs == 1


def test_every_run_of_the_walk_is_recorded():
    """32 seeds per arm, both arms, no arm shorter than the other."""
    assert set(W250_CLEARANCES) == {STOCK, RISK}
    lengths = {len(v) for v in W250_CLEARANCES.values()}
    assert lengths == {2 * W250_REFERENCE_SEEDS}


def test_the_clearance_delta_is_not_sub_margin():
    """D-124's trap does not apply here: both arms mean well above 0.40 m.

    Worth asserting because the pooled verdict is `TIED` on *rates* while the
    arms differ by ~7 cm in mean clearance — a reader could take that delta for
    a safety result, and `sub_margin` is the field that says whether it is one.
    """
    pooled = w250_reproduction().pooled
    assert not pooled.sub_margin
    assert pooled.b.mean_clearance > pooled.a.mean_clearance > PUBLISHED_MARGIN


# --- the second walk: w = 150, the island's upper edge ------------------------

def test_the_w150_reference_block_reproduces_the_published_rung():
    """The entitlement check again, on the rung with nine runs of separation.

    Same rule as `w = 250`: the fresh block is only evidence if the walk can
    re-derive the answer already on record. Both arms match D-133 exactly.
    """
    recorded = {w: (a, b) for w, a, b, _, _ in PUBLISHED_LADDER}
    n_stock, n_risk = recorded[150.0]
    ref = w150_reproduction().reference
    assert len(ref.seeds) == PUBLISHED_SEEDS == W150_REFERENCE_SEEDS
    assert ref.headroom.a.unsafe_rate == n_stock / PUBLISHED_SEEDS == 10 / 16
    assert ref.headroom.b.unsafe_rate == n_risk / PUBLISHED_SEEDS == 1 / 16
    assert ref.verdict == SEPARATED


def test_the_upper_edge_rung_reproduces():
    """The finding: the band's upper-edge rung survives a disjoint block.

    `SEPARATED` on both blocks, in the direction the mechanism predicts —
    `risk_mppi` is the safer arm — and `SEPARATED` again when pooled at n = 32.
    """
    r = w150_reproduction()
    assert r.verdict == REPRODUCED
    assert r.reference.delta_unsafe == pytest.approx(-9 / 16)
    assert r.replication.delta_unsafe == pytest.approx(-5 / 16)
    assert r.pooled.verdict == SEPARATED
    assert r.pooled.a.unsafe_rate == 15 / 32
    assert r.pooled.b.unsafe_rate == 1 / 32


def test_the_replication_confirms_the_sign_and_not_the_size():
    """A rung can be solid and still not licence its own effect size.

    `REPRODUCED` grades the *direction*, which is all the band's shape needs.
    The magnitude moves by a factor of ~1.8 between the two blocks (stock 10/16
    → 5/16), so a reader who takes the reference block's delta as the rung's
    effect is reading more than replication bought. Pinned because the module's
    verdict deliberately says nothing about it.
    """
    r = w150_reproduction()
    assert abs(r.reference.delta_unsafe) > abs(r.replication.delta_unsafe)
    assert r.reference.headroom.a.unsafe_rate == 2 * \
        r.replication.headroom.a.unsafe_rate


def test_the_reproduced_rung_was_never_a_one_run_rung():
    """Why this rung needed replication for a different reason than `w = 250`.

    `w = 250` was thin — one run — and replication found the run was a seed.
    `w = 150` is nine runs and pools to fourteen, so `one_run_rungs` never
    flagged it; what was unwitnessed was the *second block*, not the margin.
    """
    r = w150_reproduction()
    assert BandRung(headroom=r.reference.headroom, ess_in_band=True) \
        .separation_runs == 9
    pooled = BandRung(headroom=r.pooled, ess_in_band=True)
    assert pooled.scorable
    assert pooled.separation_runs == 14


def test_the_reference_block_count_rests_on_a_knife_edge_run():
    """One of the ten sub-margin stock runs clears the margin by 0.7 mm.

    Recorded because the exact `10/16` agreement with D-133 is what entitles
    this walk to its fresh block, and a reader should know that agreement is
    one run away from `9/16`. It does not weaken the verdict — `REPRODUCED`
    survives either count — but the *exactness* is luckier than it looks.
    """
    stock = W150_CLEARANCES[STOCK][:W150_REFERENCE_SEEDS]
    closest = min((c for c in stock if c < PUBLISHED_MARGIN),
                  key=lambda c: PUBLISHED_MARGIN - c)
    assert closest == pytest.approx(0.3993, abs=5e-5)
    assert PUBLISHED_MARGIN - closest < 1e-3


def test_all_recorded_walks_are_complete_and_they_disagree():
    """32 seeds per arm on every walk, and the verdicts are not all the same.

    The second half is the non-vacuity check: with only `w = 250` on record a
    `verdict` hard-coded to `SIGN_REVERSED` passed every measurement test in
    this file. Walks that disagree make that implementation fail.
    """
    walks = (W100_CLEARANCES, W150_CLEARANCES, W250_CLEARANCES)
    assert all(set(w) == {STOCK, RISK} for w in walks)
    lengths = {len(v) for w in walks for v in w.values()}
    assert lengths == {2 * W150_REFERENCE_SEEDS}
    assert w150_reproduction().verdict != w250_reproduction().verdict


# --- the third walk: w = 100, the island's interior ---------------------------

def test_the_w100_reference_block_reproduces_the_published_rung():
    """The entitlement check on the band's widest rung. Both arms match D-133."""
    recorded = {w: (a, b) for w, a, b, _, _ in PUBLISHED_LADDER}
    n_stock, n_risk = recorded[100.0]
    ref = w100_reproduction().reference
    assert len(ref.seeds) == PUBLISHED_SEEDS == W100_REFERENCE_SEEDS
    assert ref.headroom.a.unsafe_rate == n_stock / PUBLISHED_SEEDS == 1.0
    assert ref.headroom.b.unsafe_rate == n_risk / PUBLISHED_SEEDS == 6 / 16
    assert ref.verdict == SEPARATED


def test_the_interior_rung_reproduces_so_the_island_holds():
    """The finding: `{75, 100, 150}` is not split by its middle rung.

    `w = 150` is an *edge* of the contiguous separated island, so its
    replication could only ever have trimmed the island. `w = 100` is interior:
    a reversal here would have broken it into two. It reproduced instead, in
    the mechanism's direction, and pools to the band's widest separation.
    """
    r = w100_reproduction()
    assert r.verdict == REPRODUCED
    assert r.reference.delta_unsafe == pytest.approx(-10 / 16)
    assert r.replication.delta_unsafe == pytest.approx(-14 / 16)
    assert r.pooled.verdict == SEPARATED
    assert r.pooled.a.unsafe_rate == 1.0
    assert r.pooled.b.unsafe_rate == 8 / 32
    assert BandRung(headroom=r.pooled, ess_in_band=True).separation_runs == 24


def test_the_effect_size_moves_in_both_directions_across_rungs():
    """Sign and size replicate independently — and not always the same way.

    At `w = 150` the separation *shrank* between blocks (10/16 → 5/16 on
    stock), which on its own reads as regression to the mean. At `w = 100` it
    **grew** (risk 6/16 → 2/16). Two rungs moving opposite ways is what makes
    "the verdict grades direction, not magnitude" a property of the grade
    rather than an apology for one unlucky walk.
    """
    grew = w100_reproduction()
    shrank = w150_reproduction()
    assert abs(grew.replication.delta_unsafe) > abs(grew.reference.delta_unsafe)
    assert abs(shrank.replication.delta_unsafe) < \
        abs(shrank.reference.delta_unsafe)
    assert grew.verdict == shrank.verdict == REPRODUCED


# --- censoring: which arm could the second block actually have moved? ---------

def test_the_stock_arm_is_at_the_ceiling_in_both_blocks():
    """`stock_mppi` breaks the margin on all 32 seeds at `w = 100`.

    So its rate did not replicate so much as have nowhere else to be, and the
    whole separation is carried by the risk arm. The magnitude check is the
    honest form of it: the best stock run in the entire walk is still under the
    margin, so this is a ceiling in the data and not just in the rate.
    """
    r = w100_reproduction()
    assert r.reference.censored == r.replication.censored == \
        ((STOCK, CEILING),)
    assert max(W100_CLEARANCES[STOCK]) == pytest.approx(0.3705, abs=5e-5)
    assert max(W100_CLEARANCES[STOCK]) < PUBLISHED_MARGIN
    assert r.reference.headroom.b.unsafe_rate != \
        r.replication.headroom.b.unsafe_rate


@pytest.mark.parametrize("reproduction, expected, boundary", [
    (w100_reproduction, ONE_ARM_CENSORED, ((STOCK, CEILING),)),
    (w150_reproduction, UNCENSORED, ()),
    (w250_reproduction, ONE_ARM_CENSORED, ((STOCK, FLOOR),)),
])
def test_censoring_over_the_recorded_reference_blocks(reproduction, expected,
                                                      boundary):
    """Both boundaries and the free case are reached by shipped measurements.

    Only `w = 150` is a two-sided test of both arms; the other two rungs each
    have an arm that could not have moved in one direction. A `censored`
    hard-coded to either boundary — or to `()` — fails one of these rows.
    """
    ref = reproduction().reference
    assert ref.censoring == expected
    assert ref.censored == boundary


def test_both_arms_censored_is_a_separation_and_is_named():
    """The maximal delta reads in every other field like the strongest result.

    Stock 8/8 against risk 0/8 is `SEPARATED` with `delta_unsafe == -1`: real,
    but ±1 by construction and impossible to reproduce *larger*. Reached only
    when the arms sit at **opposite** boundaries — the same boundary on both is
    `NO_HEADROOM_*`, which is not a separation at all.
    """
    block = _block(0, 8, 8, 0)
    assert block.verdict == SEPARATED
    assert block.delta_unsafe == -1.0
    assert block.censoring == BOTH_ARMS_CENSORED
    assert block.censored == ((STOCK, CEILING), (RISK, FLOOR))
    assert _block(0, 8, 0, 0).verdict == NO_HEADROOM_SAFE


# --- the census: how much of the band has been looked at twice? ---------------

def test_the_published_census_is_partially_replicated():
    """Three of the band's four separated rungs have a second block — and they
    do not all agree, which is the whole reason to report coverage rather than
    a single headline. `w = 75` is the one nobody has looked at twice."""
    c = published_census()
    assert c.separated == (75.0, 100.0, 150.0, 250.0)
    assert c.replicated == (100.0, 150.0, 250.0)
    assert c.unreplicated == (75.0,)
    assert c.held == (100.0, 150.0)
    assert c.overturned == (250.0,)
    assert c.verdict == PARTIALLY_REPLICATED


@pytest.mark.parametrize("separated, weights, expected", [
    ((), (), NO_SEPARATED_RUNG),
    ((75.0, 150.0), (), UNREPLICATED),
    ((75.0, 150.0), (150.0,), PARTIALLY_REPLICATED),
    ((150.0,), (150.0,), FULLY_REPLICATED),
])
def test_the_census_verdicts_are_all_reachable(separated, weights, expected):
    """Including the empty denominator, which reads identically to full
    coverage in every other field: `replicated`, `unreplicated`, `held` and
    `overturned` are all `()` under both `NO_SEPARATED_RUNG` and a band whose
    every rung replicated. Only the verdict tells them apart."""
    reps = tuple((w, w150_reproduction()) for w in weights)
    census = ReplicationCensus(separated=separated, reproductions=reps)
    assert census.verdict == expected


def test_a_census_may_not_count_a_rung_the_band_never_separated():
    """Coverage of a rung the band does not report as `SEPARATED` is coverage
    the band cannot use, and would make `replicated` outrun `separated`."""
    with pytest.raises(ValueError, match="does not report as SEPARATED"):
        ReplicationCensus(separated=(75.0,),
                          reproductions=((150.0, w150_reproduction()),))


def test_a_census_may_not_replicate_one_weight_twice():
    """Two blocks at one weight are one `Reproduction`, not two rows — the
    second would inflate `replicated` against a fixed `separated`."""
    with pytest.raises(ValueError, match="replicated twice"):
        ReplicationCensus(separated=(150.0,),
                          reproductions=((150.0, w150_reproduction()),
                                         (150.0, w150_reproduction())))
