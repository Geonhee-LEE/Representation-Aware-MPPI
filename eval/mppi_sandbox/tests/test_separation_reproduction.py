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
    NO_SEPARATION_TO_REPRODUCE,
    NOT_REPRODUCED,
    REPRODUCED,
    SIGN_REVERSED,
    W250_CLEARANCES,
    W250_REFERENCE_SEEDS,
    OverlappingBlocks,
    Reproduction,
    SeedBlock,
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
