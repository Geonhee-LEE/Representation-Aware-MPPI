# SPDX-License-Identifier: BSD-3-Clause
"""The all-seeds gate is a function of `n`, and the census reads it at two."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import geometric_null as gn
from eval.mppi_sandbox import seed_count_licence as scl
from eval.mppi_sandbox import structural_null as sn
from eval.mppi_sandbox.seed_count_licence import (
    CENSUS_LADDER_SEEDS,
    CENSUS_WALK_SEEDS,
    DEGENERATE_RATE,
    IDENTIFICATION_SPAN,
    MAGNITUDE_IDENTIFIED,
    MAGNITUDE_UNIDENTIFIED,
    MONOTONE_PERMISSIVE,
    NO_POPULATION,
    PREDICATE_DIFFERS_BY_N,
    SAME_PREDICATE,
    WILSON_Z,
    LadderRate,
    all_seeds_pass,
    census_predicate_reading,
    licence_direction,
    licence_reading,
    out_of_band,
    predicate_match,
    recorded_reading,
    wilson_interval,
)


class TestRecordedPopulation:
    """The one complete per-seed ESS population this branch owns."""

    def test_one_seed_out_of_band(self):
        rate = out_of_band(sn.FROZEN_W75_ESS, sn.FROZEN_ESS_BAND)
        assert (rate.k, rate.n) == (1, 32)

    def test_the_offending_seed_is_below_the_floor(self):
        """D-173's `REFUSAL_AT_FLOOR`, re-derived here rather than quoted."""
        lo, _hi = sn.FROZEN_ESS_BAND
        below = [i for i, e in enumerate(sn.FROZEN_W75_ESS) if e < lo]
        assert below == [8]

    def test_empty_population_is_not_a_rate_of_zero(self):
        """Fail-closed: an empty sample and a clean sample must not print alike."""
        assert LadderRate(k=0, n=0).rate is None
        assert LadderRate(k=0, n=32).rate == 0.0
        assert licence_direction(LadderRate(k=0, n=0).rate) == NO_POPULATION


class TestDirectionIsAnalytic:
    """The direction follows from the conjunction; the data only excludes
    the degenerate cases. This is the claim D-163 measured three times."""

    @pytest.mark.parametrize("p", [1e-6, 0.005, 1 / 32, 0.1, 0.5, 0.9, 0.999])
    def test_smaller_n_is_strictly_more_permissive(self, p):
        assert all_seeds_pass(p, 8) > all_seeds_pass(p, 32)
        assert licence_direction(p) == MONOTONE_PERMISSIVE

    @pytest.mark.parametrize("p", [0.0, 1.0])
    def test_degenerate_rates_are_named_not_folded_in(self, p):
        """`p = 0` makes the gate constant in `n`; that is not the same
        statement as "seed count does not matter" and must not print as it."""
        assert all_seeds_pass(p, 8) == all_seeds_pass(p, 32)
        assert licence_direction(p) == DEGENERATE_RATE

    def test_no_population_is_a_third_state(self):
        assert licence_direction(None) == NO_POPULATION


class TestWilson:
    def test_wilson_keeps_the_lower_end_off_zero(self):
        """The reason the choice of interval is load-bearing here.

        The normal approximation runs **negative** at `k=1, n=32` and must be
        clamped to zero — which would admit `p = 0`, hence `(1 − p)ⁿ = 1` at
        every `n`, hence "seed count might not matter". Wilson's lower end is
        strictly positive, and that strict positivity is what makes the pass
        probability strictly decreasing rather than possibly flat.
        """
        k, n = 1, 32
        phat = k / n
        normal_lo = phat - WILSON_Z * ((phat * (1 - phat) / n) ** 0.5)
        assert normal_lo < 0.0

        lo, hi = wilson_interval(k, n)
        assert lo > 0.0
        assert lo == pytest.approx(0.0055, abs=5e-4)
        assert hi == pytest.approx(0.1574, abs=5e-4)
        assert lo < phat < hi
        assert all_seeds_pass(lo, 32) < 1.0

    def test_empty_sample_yields_the_whole_interval(self):
        assert wilson_interval(0, 0) == (0.0, 1.0)


class TestMagnitudeIsNotIdentified:
    def test_recorded_population_pins_only_the_sign(self):
        reading = recorded_reading()
        assert reading.direction == MONOTONE_PERMISSIVE
        assert reading.magnitude == MAGNITUDE_UNIDENTIFIED

        span = reading.walk_pass_interval
        assert span is not None
        lo, hi = span
        assert lo == pytest.approx(0.0042, abs=5e-4)
        assert hi == pytest.approx(0.8372, abs=5e-4)
        assert (hi - lo) > IDENTIFICATION_SPAN
        # Strictly inside the unit interval on both ends: the population does
        # bound the answer, it just does not bound it usefully.
        assert 0.0 < lo and hi < 1.0

    def test_point_estimate_says_the_cheap_read_is_twice_as_easy(self):
        reading = recorded_reading()
        assert reading.n_cheap == 8
        assert reading.n_walk == 32
        assert reading.point_ratio == pytest.approx(2.1426, abs=5e-4)

    def test_the_verdict_is_two_sided(self):
        """`MAGNITUDE_IDENTIFIED` must be reachable, or the other branch is a
        constant wearing a verdict's name."""
        ess = tuple([0.0] * 200 + [50.0] * 200)
        reading = licence_reading(ess, (1.0, 100.0), n_cheap=8, n_walk=32)
        assert reading.rate.rate == 0.5
        assert reading.magnitude == MAGNITUDE_IDENTIFIED


class TestCensusMixesTwoPredicates:
    def test_ladder_seed_count_is_derived_not_retyped(self):
        """`CENSUS_LADDER_SEEDS` must equal what the recorded ladders hold."""
        for admissibility in (
            gn.CONVOY_W75_LADDER_ADMISSIBILITY,
            gn.HEADON_W75_LADDER_ADMISSIBILITY,
        ):
            assert admissibility
            for reached, in_band in admissibility.values():
                assert reached == CENSUS_LADDER_SEEDS
                assert in_band <= CENSUS_LADDER_SEEDS

    def test_walk_seed_count_is_derived_not_retyped(self):
        assert len(sn.FROZEN_W75_ESS) == CENSUS_WALK_SEEDS
        assert len(sn.FROZEN_W75_CLEARANCES) == CENSUS_WALK_SEEDS

    def test_the_census_grades_with_two_different_gates(self):
        assert CENSUS_LADDER_SEEDS != CENSUS_WALK_SEEDS
        assert census_predicate_reading() == PREDICATE_DIFFERS_BY_N

    def test_same_n_is_the_negative_control(self):
        assert predicate_match(32, 32) == SAME_PREDICATE
        assert predicate_match(CENSUS_LADDER_SEEDS, CENSUS_LADDER_SEEDS) == SAME_PREDICATE

    def test_the_looser_gate_is_the_ladders(self):
        """Direction of the mix, not just its existence: the 16-seed ladder
        admits rungs the 32-seed walk would refuse, never the reverse."""
        p = out_of_band(sn.FROZEN_W75_ESS, sn.FROZEN_ESS_BAND).rate
        assert p is not None
        assert all_seeds_pass(p, CENSUS_LADDER_SEEDS) > all_seeds_pass(
            p, CENSUS_WALK_SEEDS
        )


class TestSummaryDoesNotCrashOnDegenerates:
    def test_empty_population_summarises(self):
        reading = licence_reading((), (12.8, 128.0), n_cheap=8, n_walk=32)
        assert NO_POPULATION in reading.summary()
        assert reading.point_ratio is None
        assert reading.magnitude == NO_POPULATION


class TestPooledIdentifiedSet:
    """Pooling every walked rung, not just the one with a population.

    D-184 read the magnitude off `FROZEN_W75_ESS` because it is the only
    complete per-seed population on disk, and STATE asked for the other two to
    be recovered so the interval would narrow. The premise is wrong in the
    cheap direction: :func:`wilson_interval` consumes `(k, n)` and never the
    per-seed values, so no population was ever needed — only a count. These
    tests pin what the counts that *are* on disk buy, and what they do not.
    """

    def test_every_walked_rung_is_counted(self):
        walks = scl.recorded_walk_counts()
        assert len(walks) == 4
        assert {w.n for w in walks} == {CENSUS_WALK_SEEDS}

    def test_counts_are_derived_from_the_recorded_arrays(self):
        """D-047: `n` is a length, never a typed literal."""
        pooled = scl.recorded_pooled_reading()
        assert pooled.n == (
            len(sn.FROZEN_W75_ESS)
            + len(gn.CONVOY_W75_NULL.clearances)
            + len(gn.LOUDER_NULL["clearances"])
            + len(gn.HEADON_W75_NULL.clearances)
        )

    def test_the_admissibility_flag_is_asymmetric(self):
        """`True` pins `k = 0`; `False` pins only `k ≥ 1`.

        This is the finding. An all-seeds gate that *passed* says every seed
        was in band, which is an exact count. One that refused says one seed
        was outside — not which, not how many. So the walks that carry
        information about the rate are exactly the walks that withhold its
        magnitude.
        """
        by_name = {w.source: w for w in scl.recorded_walk_counts()}
        admitted = by_name[scl.FROM_FLAG_ADMISSIBLE]
        refused = by_name[scl.FROM_FLAG_REFUSED]
        assert (admitted.k_min, admitted.k_max) == (0, 0)
        assert admitted.certainty == scl.COUNT_EXACT
        assert refused.k_min == 1 and refused.k_max == refused.n
        assert refused.certainty == scl.COUNT_BOUNDED_BELOW

    def test_the_prose_exact_count_is_not_consumed(self):
        """`geometric_null` names head_on's offending seed (25, ESS 134.15) in
        a **comment**. A comment is not a measurement; if this module read it,
        head_on would come back exact and the pooled interval would be a
        fiction with a citation. It comes back bounded."""
        head_on = [w for w in scl.recorded_walk_counts() if "head_on" in w.name]
        assert len(head_on) == 1
        assert not head_on[0].exact

    def test_pooling_raises_the_floor_and_widens_the_ceiling(self):
        """Pooling bounded counts moves the two ends in opposite directions."""
        single = recorded_reading().interval
        pooled = scl.recorded_pooled_reading().interval
        assert pooled is not None
        assert pooled[0] > single[0]   # floor up: more out-of-band seeds seen
        assert pooled[1] > single[1]   # ceiling up: `k_max` is unbounded by disk
        assert scl.pooling_effect() == scl.POOLING_RAISES_FLOOR_ONLY

    def test_the_floor_is_what_kills_a_flat_gate(self):
        """The gain is a real one and this names it. D-184's side finding was
        that strict positivity of the floor on `p` is what makes `(1 − p)ⁿ`
        strictly decreasing; pooling nearly doubles that floor, so the ceiling
        on the gate's pass probability drops."""
        single = recorded_reading()
        pooled = scl.recorded_pooled_reading()
        single_gate, pooled_gate = single.walk_pass_interval, pooled.walk_pass_interval
        assert single_gate is not None and pooled_gate is not None
        assert pooled_gate[1] < single_gate[1]
        assert pooled.interval[0] > 0.0

    def test_the_pooled_verdict_is_two_sided(self):
        """Negative control: an all-exact pool identifies. Without this the
        `POOLED_FLOOR_ONLY` string is a constant wearing a verdict's name."""
        exact = (
            scl.WalkCount(name="a", n=32, k_min=1, k_max=1,
                          source=scl.FROM_POPULATION),
            scl.WalkCount(name="b", n=32, k_min=2, k_max=2,
                          source=scl.FROM_POPULATION),
        )
        reading = scl.pooled_reading(exact)
        assert reading.identification == scl.POOLED_IDENTIFIED
        lo, hi = reading.interval
        assert lo < 3 / 64 < hi
        assert scl.recorded_pooled_reading().identification == scl.POOLED_FLOOR_ONLY

    def test_recording_the_two_populations_is_what_would_identify_it(self):
        """What STATE asked for, priced. Substituting the prose counts (`k = 1`
        each) for the two bounded walks collapses the union to a point — so the
        ask is right, but what it recovers is the *ceiling*, not the interval
        as a whole, and it needs the per-seed values only as a way of counting."""
        hypothetical = tuple(
            scl.WalkCount(name=w.name, n=w.n, k_min=w.k_min, k_max=w.k_min,
                          source=w.source)
            for w in scl.recorded_walk_counts()
        )
        reading = scl.pooled_reading(hypothetical)
        assert reading.identification == scl.POOLED_IDENTIFIED
        assert reading.interval[1] < scl.recorded_pooled_reading().interval[1]

    def test_empty_pool_is_not_a_rate_of_zero(self):
        empty = scl.pooled_reading(())
        assert empty.identification == scl.NO_WALKS
        assert empty.interval is None
        assert empty.walk_pass_interval is None
        assert scl.NO_WALKS in empty.summary()

    def test_wilson_ends_increase_with_k_so_the_union_needs_no_scan(self):
        """`PooledReading.interval` takes the extremes of `k` rather than
        scanning. That is only valid if both ends are monotone in `k`."""
        los, his = [], []
        for k in range(0, 33):
            lo, hi = wilson_interval(k, 32)
            los.append(lo)
            his.append(hi)
        assert los == sorted(los)
        assert his == sorted(his)
