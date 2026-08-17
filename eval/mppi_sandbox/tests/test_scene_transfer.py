# SPDX-License-Identifier: BSD-3-Clause
"""No arm on this branch wins on more than one scene."""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import clearance_census as cc
from eval.mppi_sandbox import scene_census as sc
from eval.mppi_sandbox import scene_transfer as st
from eval.mppi_sandbox.controllers import REGISTRY


def test_cut_in_column_covers_the_whole_registry_at_full_width():
    """A census, not a selection — every arm, every seed."""
    assert set(st.CUT_IN_ENSEMBLE) == set(REGISTRY)
    for arm, row in st.CUT_IN_ENSEMBLE.items():
        assert len(row) == cc.SEEDS, arm


def test_cut_in_column_reproduces_the_published_paired_pair():
    """D-329's two columns are this measurement, not a second one.

    `scene_census.PAIRED_ENSEMBLE` published the baseline and `social_mppi`
    columns on this scene. The full census re-took them; a re-take that moved
    either goes red here rather than quietly disagreeing with the D-329 pair.
    """
    base, social = sc.PAIRED_ENSEMBLE[(st.CUT_IN_SCENE, "social_mppi")]
    assert st.CUT_IN_ENSEMBLE[cc.BASELINE] == base
    assert st.CUT_IN_ENSEMBLE["social_mppi"] == social


def test_seed0_row_agrees_with_the_seed0_scene_census():
    """The new column's seed 0 is the column `scene_census` already recorded."""
    for arm, clearance in sc.SCENE_SEED0[st.CUT_IN_SCENE].items():
        assert st.CUT_IN_ENSEMBLE[arm][0] == clearance, arm


def test_social_wins_cut_in_on_every_seed():
    """The D-329 result, re-derived from the full column."""
    v = st.standing(st.CUT_IN_SCENE, "social_mppi")
    assert v.beats_baseline == cc.SEEDS
    assert v.wins and v.sign_is_stable
    assert round(v.mean_gap, 4) == 0.1187
    assert round(v.worst_gap, 4) == 0.0573


def test_social_loses_freezing_on_every_seed():
    """The same arm, the same test, the other scene — `0/8`."""
    v = st.standing(st.FREEZING_SCENE, "social_mppi")
    assert v.beats_baseline == 0
    assert not v.wins


def test_cbf_wins_freezing_and_loses_cut_in():
    """The freezing leader does not travel either.

    `cbf_mppi` is the arm with the best single-scene result on this branch, so
    its failure here is what makes the negative a statement about the registry
    rather than about representations specifically.
    """
    freezing = st.standing(st.FREEZING_SCENE, "cbf_mppi")
    cut_in = st.standing(st.CUT_IN_SCENE, "cbf_mppi")
    assert freezing.wins and freezing.beats_baseline == cc.SEEDS
    assert not cut_in.wins
    assert cut_in.mean_gap < 0.0
    assert 0 < cut_in.beats_baseline < cc.SEEDS  # mixed sign, not a clean loss


def test_the_two_winner_sets_are_disjoint():
    """The bottleneck's answer, as a set operation."""
    won = st.scene_scoped_winners()
    assert won[st.FREEZING_SCENE] == ("cbf_mppi",)
    assert won[st.CUT_IN_SCENE] == ("social_mppi",)
    assert set(won[st.FREEZING_SCENE]) & set(won[st.CUT_IN_SCENE]) == set()


def test_no_arm_generalises():
    """`arms_that_generalise` is empty — the north star clause is unmet."""
    assert st.arms_that_generalise() == ()
    assert st.any_arm_generalises() is False


def test_a_mixed_sign_lead_is_not_a_win():
    """`wins` needs both a positive mean and a stable sign.

    Guards the disjointness result above: without the stability half,
    `cbf_mppi`'s `2/8` on `cut_in` and `gap_gated_mppi`'s `2/8` would read as
    partial wins and the empty intersection would stop being checkable.
    """
    for arm in ("cbf_mppi", "gap_gated_mppi", "essps_mppi"):
        v = st.standing(st.CUT_IN_SCENE, arm)
        assert v.best_gap > 0.0 > v.worst_gap, arm
        assert not v.sign_is_stable and not v.wins, arm


def test_geometric_channel_is_inert_on_both_scenes():
    """`geometric_mppi` reproduces the baseline bit-for-bit, 2 scenes x 8 seeds."""
    assert st.inert_on_every_measured_scene("geometric_mppi")
    assert st.standing(st.CUT_IN_SCENE, "geometric_mppi").mean_gap == 0.0
    assert "geometric_mppi" not in st.winners(st.CUT_IN_SCENE)


def test_risk_and_frozen_risk_are_the_same_arm_on_both_scenes():
    """Ensemble-width evidence for the prune STATE.md proposes: 16/16 pairs."""
    assert st.inert_on_every_measured_scene("frozen_risk_mppi", reference="risk_mppi")
    pairs = sum(len(st._ensemble(s)["risk_mppi"]) for s in st.MEASURED_SCENES)
    assert pairs == 2 * cc.SEEDS == 16


def test_coverage_denominator_is_hostable_scenes_not_all_scenes():
    """`2/5`, derived — three scenarios cannot host the census at all."""
    measured, hostable = st.ensemble_coverage()
    assert (measured, hostable) == (2, 5)
    assert hostable == len(sc.hostable_scenes()) < len(sc.SCENE_OBSTACLES)
    assert set(st.MEASURED_SCENES) <= set(sc.hostable_scenes())


def test_measured_scenes_have_columns_and_others_refuse():
    """`_ensemble` refuses a scene it has no ensemble for, rather than guessing."""
    for scene in st.MEASURED_SCENES:
        assert set(st._ensemble(scene)) == set(REGISTRY)
    with pytest.raises(KeyError):
        st._ensemble("cafe_head_on_v0")


def test_freezing_column_is_not_duplicated_here():
    """One measurement, one home — the freezing column stays in its module."""
    assert st._ensemble(st.FREEZING_SCENE) is cc.SEED_ENSEMBLE


def test_the_projection_that_scoped_this_cycle_was_accurate():
    """267.3 s against a 275 s projection — inside 3 %.

    Pinned because the four estimates before it on this branch ran 15-20×
    long, and the difference is that this one was extrapolated from a measured
    two-arm column rather than guessed.
    """
    ratio = st.PROJECTED_SECONDS / st.RETAKE_SECONDS
    assert 0.97 < ratio < 1.03


@pytest.mark.parametrize("scene", st.MEASURED_SCENES)
def test_every_representation_arm_is_graded_on_every_measured_scene(scene):
    for arm in cc.REPRESENTATION_ARMS:
        v = st.standing(scene, arm)
        assert v.scene == scene and v.arm == arm
        assert v.worst_gap <= v.mean_gap <= v.best_gap


def test_format_grade_names_the_verdict():
    out = st.format_grade()
    assert "any_arm_generalises  = False" in out
    assert "2/5 hostable scenes" in out
    assert "social_mppi" in out and "cbf_mppi" in out
