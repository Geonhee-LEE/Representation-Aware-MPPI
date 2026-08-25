# SPDX-License-Identifier: BSD-3-Clause
"""STATE #1: sweep for other `all()`/`any()` reductions that destroy a count
the producer already holds — `all_reached` first, being the other half of the
gate D-187 fixed.

Two findings, in ascending order of how much they cost to get.

1. **The literal ask, confirmed.** `ab.summarize` computed
   `all(r.reached_goal for r in runs)` and kept no count, so `all_reached=False`
   was consistent with any `n_reached` in `[0, n)` — the same asymmetry
   `LamProbe.n_reached` was given a field for on 2026-08-02 (Q-042), on the
   same gate, two objects apart. Fixed by `SweepStats.n_reached` / `n_froze`.

2. **The count D-187 shipped never left `SweepStats`.** `barrier_ceiling._rung`
   — the constructor for the object a census walk actually *records* — read
   `stats.ess_in_band` and dropped `stats.n_in_band` on the floor, and
   `WalkCount.from_sweep` had **no non-test caller**. So D-187's prospective
   claim (a walk taken from here pools as a point) was false as shipped:
   `COUNT_EXACT` was unreachable from any real walk. That is the D-138
   reader-only-contract shape, and D-044's mute-able check. Fixed by carrying
   both witnesses through `Rung`.

The negative controls matter more than the positives here: a count that is
absent must stay absent. Back-filling `n_reached` from `all_reached=True`
would be right, and back-filling from `False` would be a guess — so neither is
done, and a legacy record still degrades to the flag's asymmetric bounds.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox import ab, barrier_ceiling as bc
from eval.mppi_sandbox import seed_count_licence as scl


def _run(*, reached: bool, in_band: bool | None = True) -> ab.ArmRun:
    """One `ArmRun` with only the fields `summarize` reads."""
    traj = np.zeros((4, 6), dtype=float)
    return ab.ArmRun(
        seed=0, clearance=0.5, mean_speed=0.4, traj=traj,
        reached_goal=reached,
        median_ess=64.0 if in_band else (1.0 if in_band is False else float("nan")),
        n_samples=256 if in_band is not None else 0,
    )


def _rung(**kw) -> bc.Rung:
    base = dict(knob=bc.WEIGHT_KNOB, value=75.0, n=32, unsafe_rate=0.0,
                mean_clearance=0.5, min_clearance=0.35, all_reached=True,
                median_ess=80.31, ess_in_band=False)
    base.update(kw)
    return bc.Rung(**base)


class TestCompletionCarriesItsWitness:
    def test_summarize_records_how_many_seeds_finished(self):
        stats = ab.summarize([_run(reached=True)] * 29 + [_run(reached=False)] * 3)
        assert stats.all_reached is False
        assert stats.n_reached == 29
        assert stats.n_froze == 3

    def test_the_flag_alone_would_have_admitted_any_count(self):
        """The asymmetry, stated as a test rather than as prose: two arms that
        differ 29-vs-1 on completion are indistinguishable through the bool."""
        near = ab.summarize([_run(reached=True)] * 31 + [_run(reached=False)])
        far = ab.summarize([_run(reached=True)] + [_run(reached=False)] * 31)
        assert near.all_reached == far.all_reached is False
        assert (near.n_froze, far.n_froze) == (1, 31)

    def test_a_stats_object_may_not_contradict_its_completion_count(self):
        with pytest.raises(ValueError, match="contradicts"):
            ab.SweepStats(
                n=8, collisions=0, collision_rate=0.0, mean_clearance=0.5,
                median_clearance=0.5, min_clearance=0.5, mean_speed=0.4,
                all_reached=True, n_reached=7)

    def test_a_record_predating_the_count_is_exempt_not_guessed(self):
        """`None` is the honest reading for a walk that destroyed its count."""
        stats = ab.SweepStats(
            n=8, collisions=0, collision_rate=0.0, mean_clearance=0.5,
            median_clearance=0.5, min_clearance=0.5, mean_speed=0.4,
            all_reached=False)
        assert stats.n_reached is None and stats.n_froze is None


class TestTheCountSurvivesTheRungBoundary:
    """The regression D-187 needed and did not have."""

    def test_rung_carries_both_witnesses(self):
        rung = _rung(n_in_band=29, n_reached=32, ess_in_band=False)
        assert (rung.n_out_of_band, rung.n_froze) == (3, 0)

    def test_a_rung_may_not_contradict_its_own_counts(self):
        with pytest.raises(ValueError, match="contradicts"):
            _rung(n_in_band=32, ess_in_band=False)
        with pytest.raises(ValueError, match="contradicts"):
            _rung(n_reached=31, all_reached=True)

    def test_a_counted_rung_reaches_COUNT_EXACT(self):
        """The point of the whole cycle: `from_sweep` now has a shape a real
        walk produces, so a refused rung pools as a point instead of a bound."""
        walk = scl.WalkCount.from_sweep("counted-rung", _rung(n_in_band=29))
        assert walk.source == scl.FROM_SWEEP_COUNT
        assert walk.certainty == scl.COUNT_EXACT
        assert (walk.k_min, walk.k_max) == (3, 3)
        assert scl.pooled_reading((walk,)).identification == scl.POOLED_IDENTIFIED

    def test_a_countless_rung_still_degrades_to_the_flags_bounds(self):
        """Historical rungs are not retroactively rescued — `POOLED_FLOOR_ONLY`
        on the two refused walks is a fact about the disk, not a bug here."""
        walk = scl.WalkCount.from_sweep("legacy-rung", _rung())
        assert walk.source == scl.FROM_FLAG_REFUSED
        assert (walk.k_min, walk.k_max) == (1, 32)
        assert walk.certainty == scl.COUNT_BOUNDED_BELOW
