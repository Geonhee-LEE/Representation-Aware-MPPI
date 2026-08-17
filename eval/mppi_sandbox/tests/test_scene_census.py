# SPDX-License-Identifier: BSD-3-Clause
"""The scene axis overturns the branch's central negative claim."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import clearance_census as cc
from eval.mppi_sandbox import scene_census as sc


def test_obstacle_census_is_derived_not_typed():
    """The pinned census equals the one loaded off disk.

    A new scenario yaml makes this fail, which is the point: every reading in
    this module is scoped by which scenes can host it.
    """
    assert sc.scene_obstacle_counts() == sc.SCENE_OBSTACLES


def test_three_scenarios_cannot_host_a_clearance_census():
    """Zero obstacles ⇒ `min_clearance` is `+inf` ⇒ the question is undefined."""
    assert sc.unmeasurable_scenes() == (
        "cafe_straight_v0", "city_curved_v0", "city_figure8_v0",
    )
    assert set(sc.unmeasurable_scenes()) & set(sc.hostable_scenes()) == set()
    assert len(sc.unmeasurable_scenes()) + len(sc.hostable_scenes()) \
        == len(sc.SCENE_OBSTACLES)


def test_the_seed_axis_scene_is_hostable_and_not_duplicated_here():
    """`cafe_freezing_v0` hosts the census, and its column lives in one place."""
    assert sc.SCENE_OBSTACLES[cc.SCENE_PATH.split("/")[-1][:-len(".yaml")]] > 0
    assert "cafe_freezing_v0" not in sc.SCENE_SEED0


@pytest.mark.parametrize("scene", sorted(sc.SCENE_SEED0))
def test_seed0_columns_cover_the_whole_registry(scene):
    """Every recorded scene carries every arm — no scene is a partial census."""
    from eval.mppi_sandbox.controllers import REGISTRY

    assert set(sc.SCENE_SEED0[scene]) == set(REGISTRY)


@pytest.mark.parametrize("scene", sorted(sc.SCENE_SEED0))
def test_geometric_arm_still_reproduces_the_baseline(scene):
    """The inert-channel signature D-327 pinned on one scene holds on four.

    `geometric_mppi` matching `stock_mppi` exactly is not two controllers
    agreeing — it is a channel that never bites. Pinned per scene so a later
    cycle that makes it bite finds out on all of them.
    """
    assert sc.SCENE_SEED0[scene]["geometric_mppi"] == sc.SCENE_SEED0[scene][cc.BASELINE]


def test_paired_columns_are_seeds_wide():
    for key, (base, arm) in sc.PAIRED_ENSEMBLE.items():
        assert len(base) == len(arm) == cc.SEEDS, key


def test_a_representation_arm_out_clears_plain_mppi_on_a_second_scene():
    """The counterexample. This is the cycle's result.

    D-328 measured `beats_baseline = 0/8` for all five representation arms on
    `cafe_freezing_v0`. On `cafe_cut_in_v0` the same paired-per-seed test gives
    `social_mppi` **8/8**, so the negative result is a fact about that scene
    and not about the arms.
    """
    v = sc.paired_grade("cafe_cut_in_v0", "social_mppi")
    assert v.arm in cc.REPRESENTATION_ARMS
    assert v.beats_baseline == cc.SEEDS
    assert v.sign_is_stable and v.buys_clearance
    assert v.mean_gap == pytest.approx(0.1187, abs=5e-4)
    assert v.worst_gap > 0.05


def test_the_same_arm_loses_on_the_seed_axis_scene():
    """`social_mppi` is not a better arm — it is better *there*.

    The two verdicts are computed the same way to the same width, so this is a
    scene difference and not a methods difference.
    """
    there = cc.seed_grade("social_mppi")
    here = sc.paired_grade("cafe_cut_in_v0", "social_mppi")
    assert there.beats_baseline == 0 and there.mean_gap < 0.0
    assert here.beats_baseline == cc.SEEDS and here.mean_gap > 0.0


def test_the_convoy_flip_does_not_survive_its_seeds():
    """The control: the procedure demotes as well as promotes.

    `risk_mppi` leads at seed 0 on `cafe_convoy_v0` and the ensemble kills it.
    Without this row the `cut_in` result would be a search that stopped on a
    win.
    """
    assert "risk_mppi" in sc.seed0_winners("cafe_convoy_v0")
    v = sc.paired_grade("cafe_convoy_v0", "risk_mppi")
    assert v.mean_gap < 0.0
    assert 0 < v.beats_baseline < cc.SEEDS
    assert not v.sign_is_stable and not v.buys_clearance


def test_the_branch_level_question_now_answers_true():
    """Both halves, so the re-scoping is visible in one place."""
    assert cc.any_representation_arm_wins_on_any_seed() is False
    assert sc.representation_buys_clearance_somewhere() is True


def test_the_constraint_arm_is_not_a_scene_independent_bar():
    """`cbf_mppi` leads `cafe_freezing_v0` 8/8 and *loses* on `cafe_cut_in_v0`."""
    assert cc.seed_grade.__module__  # the freezing column lives there
    assert all(g > 0 for g in (
        a - b for a, b in zip(cc.SEED_ENSEMBLE["cbf_mppi"],
                              cc.SEED_ENSEMBLE[cc.BASELINE])))
    col = sc.SCENE_SEED0["cafe_cut_in_v0"]
    assert col["cbf_mppi"] < col[cc.BASELINE]
    assert "cbf_mppi" not in sc.seed0_winners("cafe_cut_in_v0")


def test_the_unmeasured_flip_sits_below_the_declared_floor():
    """`cafe_head_on_v0`'s `+0.0021 m` is not measured, and the reason is a constant."""
    scene, arm, gap = sc.UNMEASURED_FLIP
    assert arm in sc.seed0_winners(scene)
    assert (scene, arm) not in sc.PAIRED_ENSEMBLE
    assert gap < sc.DISCRIMINATION_FLOOR_M
    col = sc.SCENE_SEED0[scene]
    assert col[arm] - col[cc.BASELINE] == pytest.approx(gap, abs=5e-5)


def test_seed0_winners_is_ranked_and_strict():
    for scene in sc.SCENE_SEED0:
        col = sc.SCENE_SEED0[scene]
        won = sc.seed0_winners(scene)
        assert all(col[a] > col[cc.BASELINE] for a in won)
        assert list(won) == sorted(won, key=lambda a: -col[a])
        # the baseline and its inert twin never beat the baseline
        assert cc.BASELINE not in won and "geometric_mppi" not in won


def test_format_grade_reports_the_reversal():
    out = sc.format_grade()
    assert "representation_buys_clearance_somewhere = True" in out
    assert "cafe_straight_v0" in out and "city_figure8_v0" in out
    assert "social_mppi" in out
