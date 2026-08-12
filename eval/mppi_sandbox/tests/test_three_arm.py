# SPDX-License-Identifier: BSD-3-Clause
"""The three-arm head-to-head's verdict logic, and the one reading worth pinning.

Cost discipline is deliberate here. The full `head_to_head()` is **3m40** on
this machine (9 readings x 12 runs) and `risk_interaction()` is **1m10** — both
are far outside a suite that already runs 483 s sharded, so neither is called.
The verdict logic is exercised on synthetic `SweepStats`, which is where the
actual reasoning lives, and the closed-loop surface is pinned by one two-seed
walk.

The measured tables live in the module docstring and in this cycle's report;
re-taking them is a CLI action (`python3 -m eval.mppi_sandbox.three_arm`), not a
test. No path under the snapshot surfaces is named here on purpose — a literal
one would enter the D-207 pin set as a reader and withdraw its exemption.
"""

from __future__ import annotations

import numpy as np
import pytest

from eval.mppi_sandbox.ab import ArmRun, SweepStats
from eval.mppi_sandbox.three_arm import (ARMS, LAM, SCENES, ArmReading,
                                         freezing_tax, interaction_sign_flip,
                                         read_arm)


def _stats(min_clearance: float, n_reached: int, n: int = 6) -> SweepStats:
    return SweepStats(
        n=n, collisions=0, collision_rate=0.0,
        mean_clearance=min_clearance, median_clearance=min_clearance,
        min_clearance=min_clearance, mean_speed=0.3,
        all_reached=(n_reached == n), median_ess=30.0, n_samples=256,
        ess_in_band=True, n_in_band=n, n_reached=n_reached,
    )


def _reading(arm_clr: float, arm_reached: int,
             base_clr: float = 0.10, base_reached: int = 6,
             distinct: bool = True) -> ArmReading:
    """Synthetic reading. `distinct` controls whether the arm looks inert."""
    base_traj = np.zeros((4, 5))
    arm_traj = np.ones((4, 5)) if distinct else np.zeros((4, 5))

    def runs(traj):
        return tuple(ArmRun(seed=i, traj=traj, clearance=0.0,
                            reached_goal=True, mean_speed=0.3)
                     for i in range(2))

    return ArmReading(scene="synthetic", arm="probe",
                      stats=_stats(arm_clr, arm_reached),
                      base=_stats(base_clr, base_reached),
                      runs=runs(arm_traj), base_runs=runs(base_traj))


class TestVerdictIsJoint:
    """Clearance is never readable on its own — the feed's metric-selection point."""

    def test_clearance_bought_by_not_finishing_is_not_an_improvement(self):
        """PGIF's own Hard level: 82% collisions -> 59% timeouts, headline '0%'.

        The arm holds a *quarter metre* more clearance than baseline here. It is
        still not an improvement, because it stopped driving to get it.
        """
        r = _reading(arm_clr=0.35, arm_reached=3)
        assert r.verdict == "BOUGHT_WITH_FREEZE"
        assert r.d_worst_clearance > 0.0, "the trade must stay visible, not be hidden"
        assert r.timeout_rate == pytest.approx(0.5)

    def test_losing_both_columns_is_degraded_not_frozen(self):
        assert _reading(arm_clr=0.05, arm_reached=3).verdict == "DEGRADED"

    def test_improvement_requires_completion_to_hold(self):
        assert _reading(arm_clr=0.35, arm_reached=6).verdict == "IMPROVED"

    def test_completion_gain_alone_does_not_manufacture_an_improvement(self):
        """Reaching *more* goals at equal clearance is a tie on this axis."""
        r = _reading(arm_clr=0.10, arm_reached=6, base_reached=4)
        assert r.verdict == "TIED"

    @pytest.mark.parametrize("clr,expected", [(0.05, "WORSE"), (0.10, "TIED")])
    def test_directions_at_held_completion(self, clr, expected):
        assert _reading(arm_clr=clr, arm_reached=6).verdict == expected

    def test_freezing_tax_selects_exactly_the_frozen_readings(self):
        rs = [_reading(0.35, 3), _reading(0.35, 6), _reading(0.05, 3)]
        assert [r.verdict for r in freezing_tax(rs)] == ["BOUGHT_WITH_FREEZE"]


class TestInertArmIsNotATie:
    """D-021: `ShadowCostCritic` was signal-free, and an absence is not a tie."""

    def test_byte_identical_trajectories_read_as_inert(self):
        r = _reading(arm_clr=0.10, arm_reached=6, distinct=False)
        assert r.inert
        assert r.verdict == "INERT", "an inert arm must not be reported as TIED"

    def test_a_moving_arm_is_not_inert(self):
        assert not _reading(arm_clr=0.10, arm_reached=6).inert


class TestInteractionPredicate:
    """The sign flip that separates D-217's denomination from this module's."""

    def test_opposite_signed_steps_flip(self):
        cells = {(40.0, 0.0): _stats(0.0068, 6), (40.0, 50.0): _stats(0.3823, 6),
                 (0.0, 0.0): _stats(0.0202, 6), (0.0, 50.0): _stats(0.0010, 6)}
        assert interaction_sign_flip(cells), "the measured 2x2 flips sign"

    def test_same_signed_steps_do_not_flip(self):
        cells = {(40.0, 0.0): _stats(0.01, 6), (40.0, 50.0): _stats(0.30, 6),
                 (0.0, 0.0): _stats(0.02, 6), (0.0, 50.0): _stats(0.20, 6)}
        assert not interaction_sign_flip(cells)


class TestArmSetIsWellFormed:
    def test_every_arm_isolates_its_knob(self):
        """`w_risk = 0` on every `risk_mppi` arm — the module's denomination.

        If this ever regresses to the shipped default, the head-to-head silently
        becomes D-217's comparison again and the two tables stop being distinct.
        """
        for arm, (controller, kwargs) in ARMS.items():
            if controller == "risk_mppi":
                assert kwargs["w_risk"] == 0.0, f"{arm} is not isolated"

    def test_baseline_carries_no_weight_at_all(self):
        assert all(v == 0.0 for v in ARMS["baseline"][1].values())

    def test_scenes_are_the_eligible_ones(self):
        """`scene_eligibility` admits exactly 3 of 8; the rest cannot score."""
        from eval.mppi_sandbox import scene_eligibility as se
        eligible = {s.replace(".yaml", "").rsplit("/", 1)[-1] for s in SCENES}
        assert eligible == {"cafe_obstacle_crossing_v0", "cafe_convoy_v0",
                            "cafe_head_on_v0"}
        assert len(eligible) == len(SCENES), "no duplicate scenes"
        del se  # imported to assert the dependency exists, not to re-derive it


class TestClosedLoopSurface:
    """One real walk — two seeds, one scene. Everything above is synthetic."""

    def test_read_arm_pairs_against_a_shared_baseline(self):
        r = read_arm(SCENES[0], "predicted", seeds=(0, 1), lam=LAM)
        assert r.stats.n == r.base.n == 2
        assert len(r.runs) == len(r.base_runs) == 2
        assert r.verdict in {"INERT", "IMPROVED", "WORSE", "TIED",
                             "DEGRADED", "BOUGHT_WITH_FREEZE"}
        assert np.isfinite(r.d_worst_clearance)
        assert 0.0 <= r.timeout_rate <= 1.0
