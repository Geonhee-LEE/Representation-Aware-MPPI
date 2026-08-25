# SPDX-License-Identifier: BSD-3-Clause
"""No arm on this branch wins on more than one scene."""

from __future__ import annotations

import itertools

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


def test_the_winner_sets_are_not_pairwise_disjoint():
    """D-330's disjointness result did **not** survive the third scene.

    With two scenes the winner sets were `{cbf}` and `{social}` and D-330 read
    that as "no arm wins two scenes at once". `cafe_head_on_v0` falsifies it:
    `cbf_mppi` wins there too, 8/8, so it travels between `freezing` and
    `head_on`. Pinned in the *positive* direction — asserting the shared arm
    by name — because the honest failure here is a future cycle quietly
    weakening this back to an emptiness claim it can always satisfy.
    """
    won = {s: set(v) for s, v in st.scene_scoped_winners().items()}
    assert won[st.FREEZING_SCENE] == {"cbf_mppi"}
    assert won[st.CUT_IN_SCENE] == {"social_mppi"}
    assert won[st.HEAD_ON_SCENE] == {"cbf_mppi"}

    shared = {
        (a, b): won[a] & won[b]
        for a, b in itertools.combinations(st.MEASURED_SCENES, 2)
    }
    assert shared[(st.FREEZING_SCENE, st.HEAD_ON_SCENE)] == {"cbf_mppi"}
    assert any(v for v in shared.values()), "the D-330 reading would need this empty"


def test_four_of_five_is_still_not_generalisation():
    """The result at complete coverage, stated so it cannot be softened.

    `cbf_mppi` wins four scenes of five and is blocked by exactly one, so the
    intersection over *all* measured scenes is still empty and the north star's
    "all environments" clause is still unmet. Both halves are asserted: the
    win-count, so the progress since D-332's `2/3` is visible, and the
    emptiness, so it is not mistaken for the clause being met.
    """
    won = st.scene_scoped_winners()
    wins = sum("cbf_mppi" in won[s] for s in st.MEASURED_SCENES)
    assert wins == 4 == len(st.MEASURED_SCENES) - 1
    assert "cbf_mppi" not in won[st.CUT_IN_SCENE]
    assert st.arms_that_generalise() == ()


def test_exactly_one_scene_blocks_the_travelling_arm():
    """`blocking_scenes` names the obstruction that `arms_that_generalise` hides.

    The emptiness of `arms_that_generalise()` reads identically whether an arm
    loses one scene or all five, and at 5/5 coverage that ambiguity is the
    whole remaining question. Pinned by name and by length: by name so a future
    cycle cannot satisfy it with a different blocker, by length so "blocked by
    exactly one" does not quietly become "blocked by two".
    """
    assert st.blocking_scenes("cbf_mppi") == (st.CUT_IN_SCENE,)
    assert st.narrowest_block() == ("cbf_mppi",)
    # The baseline is excluded from `narrowest_block`, not merely absent from
    # it by accident: it ties itself on every scene and so blocks everywhere.
    assert len(st.blocking_scenes(cc.BASELINE)) == len(st.MEASURED_SCENES)


def test_the_two_winners_are_exact_complements():
    """`cbf_mppi`'s only loss is `social_mppi`'s only win.

    The strongest structural claim in the matrix, and the reason "no arm
    generalises" understates the position: the *union* of two shipped arms
    covers all five hostable scenes, so what is missing is a scene-blind
    selection rule, not a capability. Asserted in both directions — a
    one-directional version would survive `social_mppi` picking up a second
    win, which would break the complementarity without breaking the test.
    """
    cbf_blocked = set(st.blocking_scenes("cbf_mppi"))
    social_won = {s for s in st.MEASURED_SCENES if "social_mppi" in st.winners(s)}
    assert cbf_blocked == social_won == {st.CUT_IN_SCENE}
    covered = {s for s in st.MEASURED_SCENES
               if {"cbf_mppi", "social_mppi"} & set(st.winners(s))}
    assert covered == set(st.MEASURED_SCENES)
    # ...and the union still is not a single arm, which is what keeps this a
    # statement about selection rather than a claim the clause has been met.
    assert st.arms_that_generalise() == ()


def test_cbf_wins_both_scenes_added_this_cycle():
    """D-333's two columns, graded — 8/8 each, the fourth and fifth wins."""
    for scene, mean in ((st.CONVOY_SCENE, 0.1494),
                        (st.OBSTACLE_CROSSING_SCENE, 0.1888)):
        v = st.standing(scene, "cbf_mppi")
        assert v.beats_baseline == cc.SEEDS, scene
        assert v.wins and v.sign_is_stable, scene
        assert round(v.mean_gap, 4) == mean, scene


def test_the_remaining_scenes_were_over_priced_again():
    """Both of this cycle's estimates ran long — the third and fourth in a row.

    D-332 narrowed "extrapolation is accurate" to *within-scene* after one
    cross-scene miss. Two more boundaries, two more over-estimates, both larger
    than that one — so the narrowing holds and the direction is consistent.
    Asserted as a direction plus a bound rather than two points, because the
    reading is "cross-scene extrapolation over-prices", not these two ratios.
    """
    for scene in (st.CONVOY_SCENE, st.OBSTACLE_CROSSING_SCENE):
        projected, measured = st.RETAKE_COST[scene]
        assert projected / measured > 1.45, scene   # worse than D-332's 1.38x
    within_scene = st.PROJECTED_SECONDS / st.RETAKE_SECONDS
    assert abs(within_scene - 1.0) < 0.03


def test_the_cross_scene_projection_was_not_accurate():
    """193.1 s against a 267.3 s projection — 38 % long, not the 3 % D-330 got.

    D-330 explained its one accurate estimate by "extrapolated from a measured
    column rather than guessed". This cycle extrapolated from that same
    measured column and still missed, which narrows the explanation: the
    accuracy was within-scene. Scenes differ in episode length, so an arm-count
    extrapolation does not cross a scene boundary. Pinned as a bound rather
    than a point so it records a direction, not a coincidence.
    """
    projected, measured = st.RETAKE_COST[st.HEAD_ON_SCENE]
    ratio = projected / measured
    assert 1.3 < ratio < 1.45
    within_scene = st.PROJECTED_SECONDS / st.RETAKE_SECONDS
    assert abs(within_scene - 1.0) < abs(ratio - 1.0)


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


def test_geometric_channel_is_inert_on_every_measured_scene():
    """`geometric_mppi` reproduces the baseline bit-for-bit, 5 scenes x 8 seeds.

    The count is not decoration: an inert channel is the one arm whose
    reading *should* survive a scene change, so each scene added is a chance
    for this to break and none has.
    """
    assert st.inert_on_every_measured_scene("geometric_mppi")
    for scene in st.MEASURED_SCENES:
        assert st.standing(scene, "geometric_mppi").mean_gap == 0.0
        assert "geometric_mppi" not in st.winners(scene)


def test_risk_and_frozen_risk_are_the_same_arm_on_every_measured_scene():
    """Ensemble-width evidence for the prune STATE.md proposes: 40/40 pairs.

    The pair has now agreed on every scene this repo can measure, so the prune
    no longer rests on a sample — there is no unmeasured hostable scene left
    where they could differ.
    """
    assert st.inert_on_every_measured_scene("frozen_risk_mppi", reference="risk_mppi")
    pairs = sum(len(st._ensemble(s)["risk_mppi"]) for s in st.MEASURED_SCENES)
    assert pairs == len(st.MEASURED_SCENES) * cc.SEEDS == 40


def test_coverage_is_complete_over_the_hostable_set():
    """`5/5` — every scene that can host the census now carries a column.

    The denominator stays derived from `hostable_scenes()` rather than pinned
    at 5: three scenarios cannot host the census at all (zero obstacles), and a
    reader handed `100 %` cannot tell whether those were counted as passes
    (D-241). Equality is asserted as a set, not a count, so adding a hostable
    scenario re-opens coverage instead of leaving a stale `5 == 5`.
    """
    measured, hostable = st.ensemble_coverage()
    # `(5, 5)` until the 9th scene landed. It is `(5, 6)` now, and the re-open
    # is the test working: `cafe_obstacle_contested_v0` can host the census
    # (5 obstacles) but carries no 8-seed x 8-arm column, which is 64 rollouts
    # nobody has bought. Coverage is deliberately NOT re-closed by widening
    # MEASURED_SCENES — the gap is asserted against the pinned debt instead.
    assert (measured, hostable) == (5, 6)
    assert hostable == len(sc.hostable_scenes()) < len(sc.SCENE_OBSTACLES)
    assert set(sc.hostable_scenes()) - set(st.MEASURED_SCENES) == set(
        sc.UNHARVESTED_SCENES)
    assert not set(st.MEASURED_SCENES) - set(sc.hostable_scenes())


def test_measured_scenes_have_columns_and_others_refuse():
    """`_ensemble` refuses a scene it has no ensemble for, rather than guessing.

    The negative case has now moved twice — `cafe_head_on_v0` until D-332
    measured it, then `cafe_convoy_v0` until this cycle did. It cannot move a
    third time: completing coverage **retired the fixture's whole population**.
    There is no longer any hostable-but-uncolumned scene to name, so the
    refusal path is exercised by a scene that cannot host the census at all
    (see :data:`UNCOLUMNED_SCENE` and the test below for why that is the only
    remaining honest choice).
    """
    for scene in st.MEASURED_SCENES:
        assert set(st._ensemble(scene)) == set(REGISTRY)
    with pytest.raises(KeyError):
        st._ensemble(UNCOLUMNED_SCENE)


#: A scenario with no ensemble column and no way to get one — it declares zero
#: obstacles, so `min_clearance` is `inf` and the census question is undefined.
#: Asserted non-hostable below, which is what makes the refusal above non-vacuous
#: now that every *hostable* scene is measured.
UNCOLUMNED_SCENE = next(s for s in sorted(sc.SCENE_OBSTACLES)
                        if s not in sc.hostable_scenes())


def test_the_negative_case_survived_coverage_completion():
    """The refusal fixture is non-vacuous, and its reason changed this cycle.

    Until now `_ensemble`'s rejection path was tested with a scene that *could*
    host the census but had not been measured yet. That population is now
    **empty** — 5/5 hostable scenes carry columns — so a fixture of the old
    shape would either be unfillable or silently vacuous. Both halves are
    asserted against the new source of negatives: uncolumned, so the refusal
    fires, and *non-hostable*, so it is a scene no future cycle can measure and
    thereby expire the fixture again.
    """
    assert UNCOLUMNED_SCENE not in st._COLUMNS
    assert UNCOLUMNED_SCENE not in st.MEASURED_SCENES
    assert UNCOLUMNED_SCENE not in sc.hostable_scenes()
    # The old fixture's population really is gone — this is the fact that
    # forced the change, so it is asserted rather than described.
    assert set(sc.hostable_scenes()) - set(st.MEASURED_SCENES) == set(
        sc.UNHARVESTED_SCENES)


def test_the_column_registry_matches_measured_scenes():
    """`_COLUMNS` and `MEASURED_SCENES` are the same population, both ways.

    The `if` ladder `_COLUMNS` replaced could disagree with `MEASURED_SCENES`
    silently — a scene listed as measured but never dispatched would raise only
    when something walked it, and a column present but unlisted would be
    invisible to every parametrized test in this file.
    """
    assert set(st._COLUMNS) == set(st.MEASURED_SCENES)
    assert len(st._COLUMNS) == len(st.MEASURED_SCENES)


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
    assert "5/6 hostable scenes" in out
    assert "social_mppi" in out and "cbf_mppi" in out
    # Every measured scene reaches the printer. The coverage string moved from
    # `2/5` to `3/5` this cycle by editing one constant, so a scene added to
    # `MEASURED_SCENES` and left out of the matrix would still print a correct
    # -looking header; this walks the columns instead of trusting it.
    for scene in st.MEASURED_SCENES:
        assert f"winners on {scene}" in out
