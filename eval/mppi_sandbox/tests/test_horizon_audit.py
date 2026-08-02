# SPDX-License-Identifier: BSD-3-Clause
"""Pins for `horizon_audit` — the rollout horizon is not a sweepable axis on
the crossing scene, and the reason is a cause leave-one-out cannot see.

Kept cheap on purpose. Every closed-loop assertion here runs at
`max_steps=VERDICT_STEPS` (160) rather than the scenario timeout, because each
question is *driving or frozen*, which is legible at ~1.5× the healthy run
length. The full-timeout versions of these same measurements cost ~15 s per
run and are recorded in the module docstring instead of re-derived here — the
one place that matters (`redundant_sets`' verdict) is checked to agree under
both caps in the module docstring's table, which was produced both ways.
"""

from __future__ import annotations

import numpy as np
import pytest

from .. import horizon_audit as ha
from .. import scale_match
from ..scenario import load_scenario

CROSSING = "eval/scenarios/cafe_obstacle_crossing_v0.yaml"

#: D-029's admissible window for this scene is [1.6, 3.2]; 1.6 is its floor.
#: Not the shipped 0.1 — see `horizon_audit.scan`.
LAM = 1.6

#: One rung either side of the observed edge (34 free / 35 frozen).
FREE_H, FROZEN_H = 34, 45

#: Zeroing overrides for the two obstacle terms, as `ablate` wants them.
OBSTACLE_GROUPS = {
    "collision": {"w_collision": 0.0},
    "barrier": {"w_obs_soft": 0.0},
}


@pytest.fixture(scope="module")
def crossing():
    return load_scenario(CROSSING)


@pytest.fixture(scope="module")
def edge_rows(crossing):
    """The two rungs bracketing the freeze, plus the shipped reference."""
    return ha.scan(crossing, horizons=(ha.SHIPPED_HORIZON, FREE_H, FROZEN_H),
                   seeds=range(2), lam=LAM, max_steps=ha.VERDICT_STEPS)


@pytest.fixture(scope="module")
def ablation(crossing):
    """One seed, not two: the effect is 5.6× restored vs 0.90–0.97× for the
    singletons, so seed variance would have to be an order of magnitude larger
    than anything measured on this scene to change the verdict. The n = 2
    version is in the module docstring."""
    return ha.ablate(crossing, groups=OBSTACLE_GROUPS, horizon=FROZEN_H,
                     seeds=range(1), lam=LAM, max_steps=ha.VERDICT_STEPS)


@pytest.fixture(scope="module")
def rates(crossing):
    """`w_voo` exchange rate at three horizons — two healthy, one frozen.

    Module-scoped because each is two closed-loop runs and the frozen one runs
    to the full timeout by construction (the freeze is what it is measuring).
    """
    return {H: scale_match.exchange_rate(crossing, "w_voo", lam=LAM, horizon=H)
            for H in (ha.SHIPPED_HORIZON, FREE_H, FROZEN_H)}


class TestHorizonIsNotSweepable:
    """Q-043's "lengthen the rollout cone" branch, refuted at the baseline."""

    def test_the_sweepable_ceiling_is_below_twice_the_shipped_horizon(
            self, edge_rows):
        ceiling, margin = ha.cruise_ceiling(edge_rows)
        assert ceiling < 2 * ha.SHIPPED_HORIZON, (
            f"H={ceiling} is still driving — if the horizon really is "
            f"sweepable to 2x the shipped value then the (w_voo, horizon) 2x2 "
            f"is runnable after all and this module's premise is wrong")
        assert margin > 0.9, (
            f"ceiling margin {margin:.3f} — the last admissible rung is only "
            f"marginally faster than the freeze threshold, so FROZEN_BELOW is "
            f"doing the work and the edge is not a real edge")

    def test_the_frozen_rung_cruises_far_slower_than_the_shipped_one(
            self, edge_rows):
        by_h = {r.horizon: r for r in edge_rows}
        ratio = by_h[FROZEN_H].cruise / by_h[ha.SHIPPED_HORIZON].cruise
        assert ratio < 0.35, (
            f"H={FROZEN_H} cruises at {ratio:.2f}x the shipped horizon — the "
            f"collapse this module is about did not reproduce")

    def test_completion_does_not_separate_the_rungs(self, crossing):
        """`all_reached` is True on the frozen arm at the full timeout.

        The guard that catches freeze-buys-berth elsewhere in this repo is
        blind here, which is why `scan` reports cruise at all. Run untruncated
        precisely because truncation would make the frozen arm fail for the
        *wrong* reason and hide the point.
        """
        rows = ha.scan(crossing, horizons=(FROZEN_H,), seeds=range(1),
                       lam=LAM, max_steps=None)
        assert rows[0].all_reached, (
            "the frozen arm no longer reaches the goal — if that is now true, "
            "`assert_all_reached` catches this class and the cruise column is "
            "no longer load-bearing")
        assert rows[0].cruise < 0.35 * 0.7998

    def test_clearance_alone_would_say_the_opposite(self, edge_rows):
        """The confound, stated as an assertion so it cannot be forgotten."""
        by_h = {r.horizon: r for r in edge_rows}
        assert by_h[FROZEN_H].mean_clearance > by_h[FREE_H].mean_clearance, (
            "the frozen rung no longer looks safer — the freeze-buys-berth "
            "confound this module warns about would then not apply here")


class TestLeaveOneOutIsBlindToRedundantCauses:
    """The finding worth carrying: `weight_units.measure` cannot see this."""

    def test_neither_obstacle_term_alone_restores_cruise(self, ablation):
        intact = ablation[frozenset()].cruise
        for name in OBSTACLE_GROUPS:
            solo = ablation[frozenset({name})].cruise
            assert solo < 2.0 * intact, (
                f"zeroing {name} alone restored cruise "
                f"({solo:.4f} vs intact {intact:.4f}) — the cause would then "
                f"be attributable term-by-term and leave-one-out would suffice")

    def test_zeroing_both_restores_cruise(self, ablation):
        intact = ablation[frozenset()].cruise
        both = ablation[frozenset(OBSTACLE_GROUPS)].cruise
        assert both > 4.0 * intact, (
            f"zeroing both obstacle terms left cruise at {both:.4f} vs intact "
            f"{intact:.4f} — the freeze is then not caused by the obstacle "
            f"terms at all and the attribution in the docstring is wrong")

    def test_redundant_sets_names_the_pair_and_nothing_smaller(self, ablation):
        found = ha.redundant_sets(ablation)
        assert found == [frozenset(OBSTACLE_GROUPS)], (
            f"expected exactly the {{collision, barrier}} pair as the minimal "
            f"restoring set, got {[sorted(s) for s in found]}")

    def test_the_restored_arm_collides(self, ablation):
        """Other half of the sentence — the freeze buys real safety, badly."""
        assert ablation[frozenset(OBSTACLE_GROUPS)].mean_clearance < 0.0

    def test_redundant_sets_rejects_a_stalled_intact_arm(self):
        """A ratio against a stalled reference is not a measurement."""
        row = ha.HorizonRow(horizon=45, n_seeds=1, median_steps=1.0,
                            cruise=float("nan"), mean_clearance=0.0,
                            all_reached=False, median_ess=float("nan"),
                            truncated=True)
        with pytest.raises(ValueError, match="stalled"):
            ha.redundant_sets({frozenset(): row})


class TestScaleMatchedWeightIsHorizonDependent:
    """The 2×2's weight axis does not survive its horizon axis either."""

    def test_the_prescribed_weight_moves_with_the_horizon(self, rates):
        for H in (ha.SHIPPED_HORIZON, FREE_H):
            assert rates[H].is_undamaged, f"probe damaged the arm: {rates[H]}"
        swing = (rates[FREE_H].weight_for_ratio(0.25)
                 / rates[ha.SHIPPED_HORIZON].weight_for_ratio(0.25))
        assert swing > 1.2, (
            f"scale-matched w_voo moved only {swing:.3f}x over H "
            f"{ha.SHIPPED_HORIZON}->{FREE_H} — if the weight really is "
            f"horizon-transferable, a fixed-w_voo horizon column is honest "
            f"after all")

    def test_the_damage_guard_passes_on_a_frozen_baseline(self, rates):
        """D-028's guard is relative — it cannot see a broken reference.

        Pinned as a *limitation*, not a bug to fix in place: the repair is the
        absolute `cruise_ceiling` precondition, and this test exists so that
        anyone who tightens `check_undamaged` learns it was load-bearing here.
        """
        rate = rates[FROZEN_H]
        assert rate.is_undamaged, (
            "the damage guard now rejects the frozen-baseline arm — if that is "
            "deliberate, drop this test and say so; the docstring's claim that "
            "the guard is blind to a frozen reference would be stale")
        assert rate.rest < rates[ha.SHIPPED_HORIZON].rest, (
            "the frozen arm no longer presents a flatter landscape than the "
            "healthy one — the mechanism behind the flattering weight is then "
            "not the one recorded")


class TestScanContract:
    def test_cruise_ceiling_needs_the_reference_rung(self, edge_rows):
        with pytest.raises(KeyError, match="reference rung"):
            ha.cruise_ceiling(edge_rows, reference=999)

    def test_truncation_is_reported(self, edge_rows):
        by_h = {r.horizon: r for r in edge_rows}
        assert by_h[FROZEN_H].truncated, (
            "the frozen rung finished inside VERDICT_STEPS — either it is no "
            "longer frozen or the cap is too generous to be a saving")
        assert not by_h[ha.SHIPPED_HORIZON].truncated, (
            "the healthy rung is being truncated — VERDICT_STEPS is too tight "
            "and the shipped arm's cruise is measured on a partial run")

    def test_max_steps_default_is_bit_identical(self, crossing):
        """`run.simulate`'s new parameter must not move any existing result."""
        from ..ab import run_arm
        from ..controllers.stock_mppi import MPPIParams
        params = MPPIParams(lam=LAM)
        a = run_arm(crossing, "risk_mppi", 0, params=params)
        b = run_arm(crossing, "risk_mppi", 0, params=params, max_steps=None)
        np.testing.assert_array_equal(a.traj, b.traj)
