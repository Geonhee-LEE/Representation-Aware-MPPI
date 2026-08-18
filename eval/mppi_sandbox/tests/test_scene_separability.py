# SPDX-License-Identifier: BSD-3-Clause
"""Q-162: `cut_in` separates — and so does every other scene, which is the point.

The tests split into three groups on purpose:

* the **operator** tests drive :func:`scene_separability.separates` off a
  synthetic table, so they say what the no-overlap rule means and keep saying
  it when a re-take moves the measured numbers;
* the **measurement** pins hold the recorded verdict, including the control
  row that is the actual answer to Q-162;
* the **provenance** pins hold the two properties that make the measurement
  mean what it claims — baseline-only rollouts, and a registry that matches
  the recorded keys in both directions.
"""


from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import scene_separability as sep
from eval.mppi_sandbox.clearance_census import BASELINE, SEEDS
from eval.mppi_sandbox.scene_transfer import MEASURED_SCENES

# --------------------------------------------------------------------------
# the operator
# --------------------------------------------------------------------------


def _table(values: dict[str, tuple[float, ...]]) -> dict:
    """A synthetic `OBSERVED` carrying one observable over the five scenes."""
    return {scene: {"probe": values[scene]} for scene in MEASURED_SCENES}


def test_separation_needs_a_gap_on_one_side_or_the_other(monkeypatch):
    """Above the rest and below the rest both count; overlapping does not."""
    below = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    below[sep.QUESTION_SCENE] = (0.0, 1.0)
    monkeypatch.setattr(sep, "OBSERVED", _table(below))
    assert sep.separates(sep.QUESTION_SCENE, "probe")

    above = dict.fromkeys(MEASURED_SCENES, (0.0, 1.0))
    above[sep.QUESTION_SCENE] = (5.0, 6.0)
    monkeypatch.setattr(sep, "OBSERVED", _table(above))
    assert sep.separates(sep.QUESTION_SCENE, "probe")


def test_a_single_overlapping_seed_defeats_separation(monkeypatch):
    """The rule is strict — one seed inside the other range is enough.

    This is the direction that matters for a *switch*: a threshold that eight
    seeds straddle is a threshold that mis-fires, so a rule tolerant of one
    crossing would be reporting a switch that does not exist.
    """
    values = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    values[sep.QUESTION_SCENE] = (0.0, 5.5)      # 5.5 sits inside [5, 6]
    monkeypatch.setattr(sep, "OBSERVED", _table(values))
    assert not sep.separates(sep.QUESTION_SCENE, "probe")


def test_an_infinite_value_never_separates(monkeypatch):
    """`min_ttc` is `inf` when nothing ever closes; that is absence, not signal.

    Without this branch an all-`inf` scene would read as separated from any
    finite one, and a switch keyed on it would be keyed on "no obstacle is
    approaching" — which is exactly the case where the choice of arm does not
    matter. The negative case is drawn from the **coded** branch rather than
    from a measured pair, so no re-take can retire it.
    """
    values = dict.fromkeys(MEASURED_SCENES, (5.0, 6.0))
    values[sep.QUESTION_SCENE] = (float("inf"), float("inf"))
    monkeypatch.setattr(sep, "OBSERVED", _table(values))
    assert not sep.separates(sep.QUESTION_SCENE, "probe")


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------


def test_observed_covers_every_measured_scene_at_ensemble_width():
    """Every hostable scene, every observable, all `SEEDS` seeds — a census.

    The claim under test ("`cut_in` is separable, and so is everything else")
    is a statement about the *whole* measured set, so a table missing a scene
    or short a seed would make the control row weaker without making any
    assertion fail.
    """
    assert tuple(sep.OBSERVED) == MEASURED_SCENES
    for scene in MEASURED_SCENES:
        assert tuple(sep.OBSERVED[scene]) == sep.OBSERVABLES
        for observable in sep.OBSERVABLES:
            assert len(sep.OBSERVED[scene][observable]) == SEEDS


def test_the_question_scene_separates():
    """Q-162's literal question, answered yes — and this is the weaker half."""
    assert sep.separating_observables(sep.QUESTION_SCENE) == ("obstacle_speed",)


def test_the_scene_level_control_does_not_by_itself_sink_the_question():
    """**The control that did *not* fire, pinned so nobody re-reads it as if it had.**

    If every scene separated, `cut_in` separating would be a restatement of
    "the five scenarios are five different files". Only three of five do, so
    `separation_is_distinctive` is True and the scene-level reading gives
    Q-162's option (A) qualified support. That support is withdrawn one control
    later, by the zero-spread test below — and the withdrawal is the finding.
    Recording the intermediate verdict is what keeps the two from being
    conflated by a later cycle reading only the headline.

    Pinned as an equality on the full table rather than as a count, so an
    observable that stops separating some scene shows up as a changed row
    instead of silently holding the total at three.
    """
    assert sep.separation_table() == sep.SEPARATION
    assert sep.scenes_that_separate() == ("cafe_freezing_v0", "cafe_cut_in_v0",
                                          "cafe_head_on_v0")
    assert sep.separation_is_distinctive()


def test_the_question_scenes_only_separator_is_a_scenario_constant():
    """**The verdict.** `obstacle_speed` never moves across eight seeds.

    `cut_in`'s single separation is carried by this one observable, whose
    within-scene spread is exactly zero in all five scenes — one value per
    scene, copied from the yaml through a rollout-shaped function. A switch
    keyed on it is a switch keyed on the scene label, which is Q-162's option
    (C). (`head_on`'s `min_ttc` is a genuine reading and is *not* covered by
    this test; that is the next one's job.)

    Pinned as an equality on the constant set, not as a property of
    `obstacle_speed` alone: a future observable that also fails to move is the
    same mistake, and this goes red when one is added.
    """
    assert sep.constant_observables() == ("obstacle_speed", "path_lateral_speed")
    for observable in sep.constant_observables():
        for scene in MEASURED_SCENES:
            values = sep.OBSERVED[scene][observable]
            assert len(set(values)) == 1, (observable, scene)


def test_the_question_scene_is_not_informatively_separable():
    """Strip the constant and `cut_in` separates on **nothing**.

    The scene D-333 named as the switch's decision point is the scene these
    plan-time observables cannot see. The one informative separation in the
    whole matrix belongs to `head_on` — a different scene, and one the switch
    does not need, since `cbf_mppi` already wins it.
    """
    assert sep.informative_separators(sep.QUESTION_SCENE) == ()
    assert not sep.question_scene_is_informatively_separable()
    assert sep.scenes_that_separate_informatively() == ("cafe_head_on_v0",)
    assert {s: sep.informative_separators(s) for s in MEASURED_SCENES} \
        == sep.INFORMATIVE_SEPARATION


def test_no_observable_separates_the_question_scene_alone():
    """The sharper form: not one of the five observables is `cut_in`-specific.

    `separation_is_distinctive` asks whether *some* scene fails to separate.
    This asks the dual — whether some **observable** separates `cut_in` and
    nothing else — because that observable, if it existed, would be the channel
    Q-162 is looking for even though the scene-level count is uninformative.
    """
    for observable in sep.OBSERVABLES:
        separated = [s for s in MEASURED_SCENES if sep.separates(s, observable)]
        assert separated != [sep.QUESTION_SCENE], observable


# --------------------------------------------------------------------------
# provenance
# --------------------------------------------------------------------------


def test_the_rollouts_are_the_baseline_arms():
    """A switch runs before an arm is chosen, so the observables must not read one.

    Checked against the source rather than by running the 40 rollouts: the
    property is "this module names exactly one arm, and it is the baseline",
    which is a statement about the code, not about a measurement.
    """
    source = Path(sep.__file__).read_text()
    assert "make_controller(BASELINE" in source
    assert BASELINE == "stock_mppi"
    for arm in ("cbf_mppi", "social_mppi"):
        assert f'"{arm}"' not in source, arm


def test_the_observable_registry_and_the_recorded_keys_pin_each_other():
    """Bidirectional, per `scene_transfer`'s `MEASURED_SCENES` precedent.

    One direction alone lets a new observable be measured and never graded, or
    graded and never measured; the pair makes either a red test.
    """
    for scene in MEASURED_SCENES:
        assert set(sep.OBSERVED[scene]) == set(sep.OBSERVABLES)
    assert set(sep.SEPARATION) == set(MEASURED_SCENES)
    for scene, observables in sep.SEPARATION.items():
        assert set(observables) <= set(sep.OBSERVABLES), scene


def test_the_question_scene_is_the_one_the_complement_result_named():
    """`QUESTION_SCENE` is `cbf_mppi`'s only block — not a scene chosen here.

    D-333's complement result is what makes Q-162 a question at all; if a later
    cycle's measurement moved the blocking scene, this module would be asking
    about the wrong one and every row above would be answering a dead question.
    """
    from eval.mppi_sandbox.scene_transfer import blocking_scenes
    assert blocking_scenes("cbf_mppi") == (sep.QUESTION_SCENE,)


@pytest.mark.parametrize("scene", MEASURED_SCENES)
def test_separating_observables_is_ordered_by_the_registry(scene):
    """Registry order, not dict-iteration order — the table is read by humans."""
    got = sep.separating_observables(scene)
    assert list(got) == [o for o in sep.OBSERVABLES if o in got]


# --------------------------------------------------------------------------
# the causal indices (D-335)
# --------------------------------------------------------------------------
#
# D-334 read every observable at the episode's minimum-clearance instant, which
# a planner cannot know in advance, and said so: the reading was an *upper
# bound* on what a switch could see. These pins hold the follow-through — the
# same rule applied to the same 40 rollouts at two indices a switch could
# actually reach.


def test_cut_in_has_no_informative_separator_at_any_measured_index():
    """**The D-335 verdict.** The invisibility is not an artefact of reading late.

    This is the reading D-334 could not make. Had `cut_in` separated at a
    causal index, D-334's negative would have been an artefact of the hindsight
    instant and the switch would still have been on the table; it does not, at
    either causal policy, so the negative survives the one objection that could
    have overturned it.
    """
    assert sep.policies_that_separate_question_scene() == ()
    for policy in sep.INDEX_POLICIES[1:]:
        assert not sep.question_scene_is_causally_separable(policy), policy


def test_cut_in_fails_at_the_causal_indices_before_the_constant_filter_runs():
    """Empty even *un*filtered — a strictly stronger failure than D-334's.

    At the critical index `cut_in` did separate, on a constant, and the verdict
    needed :func:`constant_observables` to strike it out. At both causal
    indices there is nothing to strike out: the raw row is already empty. So
    the causal negative does not depend on the zero-spread control at all, and
    would stand even if that control were wrong.
    """
    assert sep.separating_observables(sep.QUESTION_SCENE) != ()      # D-334, filtered later
    for policy in sep.INDEX_POLICIES[1:]:
        raw = sep.causal_separation_table(policy)
        assert raw[sep.QUESTION_SCENE] == (), (policy, raw)
        # ...and the un-filtered table is not empty everywhere, so the empty row
        # above is a reading about `cut_in` rather than a broken table.
        assert any(raw[s] for s in MEASURED_SCENES), policy


def test_the_constant_stops_singling_out_cut_in_once_the_index_is_causal():
    """Why the raw row empties: the constant is read off a *different obstacle*.

    At the critical instant `cut_in`'s nearest obstacle is a static one, so
    `obstacle_speed` reads `0.0` and is unique among the five scenes. At first
    detection the nearest obstacle is the moving one, `0.75` — which
    `cafe_obstacle_crossing_v0` also carries, so the constant no longer
    separates anything. D-334 called its separator a scenario parameter; this
    is the sharper statement, that it was a parameter of an obstacle the switch
    would not even have been looking at.
    """
    assert sep.OBSERVED[sep.QUESTION_SCENE]["obstacle_speed"] == (0.0,) * SEEDS
    for policy in sep.INDEX_POLICIES[1:]:
        table = sep.CAUSAL_OBSERVED[policy]
        assert table[sep.QUESTION_SCENE]["obstacle_speed"] == (0.75,) * SEEDS
        assert (table["cafe_obstacle_crossing_v0"]["obstacle_speed"]
                == table[sep.QUESTION_SCENE]["obstacle_speed"])
        assert sep.is_constant("obstacle_speed", table), policy


def test_the_policies_disagree_away_from_the_question_scene():
    """The control fires, **and it fires red** — the table is index-dependent.

    `freezing` separates on `ttc` at a fixed 1 s and on nothing at first
    detection; `head_on` picks up `lateralness` at one index and not the other.
    Pinned as a disagreement rather than quietly narrowed to `cut_in`'s row,
    because the honest scope of every other row in this module is "at this
    index" and a green whole-table control would erase that.
    """
    assert not sep.causal_policies_agree()
    first = sep.causal_informative_table("first_detection")
    fixed = sep.causal_informative_table("fixed_time")
    assert first["cafe_freezing_v0"] == ()
    assert fixed["cafe_freezing_v0"] == ("ttc",)
    assert first["cafe_head_on_v0"] == ("closing_speed",)
    assert fixed["cafe_head_on_v0"] == ("lateralness", "closing_speed")


def test_the_path_relative_channel_never_separates_the_question_scene():
    """D-336: the channel the bottleneck asked for, measured, and it does not bite.

    `path_lateral_speed` is the obstacle's velocity component *across* the
    reference path — proposed precisely because `cafe_cut_in_v0`'s pedestrian is
    piecewise (perpendicular for 2 s, then turning to travel along the robot's
    line), so the projection had a route to within-scene spread that
    `obstacle_speed` did not have.

    It fails on **both** counts, which is why it gets its own test rather than a
    line in the constant-set pin: it never separates `cut_in` at any index, and
    where it does separate (`freezing`, `head_on`) it is zero-spread and the
    filter strikes it out.
    """
    for policy in sep.INDEX_POLICIES:
        table = None if policy == "critical" else sep.CAUSAL_OBSERVED[policy]
        assert not sep.separates(sep.QUESTION_SCENE, "path_lateral_speed", table), policy
        assert sep.is_constant("path_lateral_speed", table), policy


def test_both_obstacle_side_channels_are_constant_at_every_index():
    """The general form of D-336, and the reason a third velocity channel is futile.

    Both members of :data:`OBSTACLE_SIDE_OBSERVABLES` are built from the
    obstacle's scripted velocity and the reference path, and nothing else. Every
    obstacle in the suite runs a piecewise-linear yaml schedule and every path is
    a fixed polyline, so on whichever segment the read index lands the value is a
    yaml constant — seed moves the index, not the segment. Any further channel of
    the same construction inherits the same zero spread, so the remaining route
    to a `cut_in` separator has to read something the *robot* did.

    Pinned as a re-derived census equal to the literal, so adding a third such
    channel without noticing goes red here.
    """
    assert sep.obstacle_side_observables() == sep.OBSTACLE_SIDE_OBSERVABLES
    for observable in sep.OBSTACLE_SIDE_OBSERVABLES:
        assert sep.constant_at_every_index(observable), observable
    # the contrast that makes the claim non-vacuous: the robot-side channels do
    # move, so "constant" is a property of these two and not of the reader.
    assert not sep.constant_at_every_index("bearing_rate")


def test_the_question_scene_row_is_the_one_thing_all_three_indices_agree_on():
    """The narrow claim the verdict rests on, pinned apart from the broad one.

    Separated from :func:`causal_policies_agree` on purpose: that one is False
    and this one is True, and a reader who conflates them concludes either that
    the index never matters (it does) or that `cut_in`'s row is as shaky as the
    rest (it is not).
    """
    assert sep.policies_agree_on_question_scene()
    assert not sep.causal_policies_agree()


def test_the_causal_readers_never_look_past_the_read_index():
    """Causality as a property of the operator, not of the recorded numbers.

    Drives `_observables_at` off a synthetic trajectory whose future is
    *poisoned* — every quantity after the read index is garbage. A centred
    `np.gradient`, which is what the critical reader uses, would pull `k + 1`
    into the closing speed and the bearing rate and this would blow up; the
    backward difference cannot see it. This is the test that would have caught
    a re-index that forgot to change the derivative.
    """
    import numpy as np

    class _Ob:
        radius = 0.1

        def position(self, t):
            t = np.atleast_1d(t)
            xs = np.where(t <= 1.0, 5.0 - t, 1e9)      # poisoned after t = 1
            return np.stack([xs, np.zeros_like(xs)], axis=-1).squeeze()

        def velocity(self, t):
            return np.array([-1.0, 0.0])

    t = np.linspace(0.0, 2.0, 21)
    traj = np.zeros((t.size, 6))
    traj[:, 0] = t
    k = int(np.argmin(np.abs(t - 1.0)))
    # a reference path along +y, so its normal is the x axis and the obstacle's
    # velocity (-1, 0) projects onto it in full — the projection is exercised
    # here rather than left to read 0 by accident.
    path = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    got = sep._observables_at(traj, [_Ob()], 0.1, k, path)
    assert all(np.isfinite(v) for v in got.values()), got
    assert got["closing_speed"] == pytest.approx(1.0, abs=1e-6)
    assert got["path_lateral_speed"] == pytest.approx(1.0, abs=1e-6)


def test_every_causal_policy_is_recorded_and_every_recorded_policy_is_causal():
    """Bidirectional, per the `OBSERVABLES`/`OBSERVED` pin above.

    `critical` is deliberately absent from `CAUSAL_OBSERVED` — its table *is*
    `OBSERVED`, and a second copy could drift from the first.
    """
    assert set(sep.CAUSAL_OBSERVED) == set(sep.INDEX_POLICIES[1:])
    assert "critical" not in sep.CAUSAL_OBSERVED
    for policy, table in sep.CAUSAL_OBSERVED.items():
        assert set(table) == set(MEASURED_SCENES), policy
        for scene, row in table.items():
            assert set(row) == set(sep.CAUSAL_OBSERVABLES), (policy, scene)
            for observable, values in row.items():
                assert len(values) == SEEDS, (policy, scene, observable)


def test_the_causal_registry_swaps_exactly_the_hindsight_column():
    """`min_ttc` has no causal counterpart; `ttc` replaces it, and only it.

    An episode-wide minimum needs the episode to have finished. Pinned as a
    set difference so a later cycle that adds an observable to one registry and
    not the other goes red rather than producing two tables that silently
    cannot be compared.
    """
    assert set(sep.OBSERVABLES) - set(sep.CAUSAL_OBSERVABLES) == {"min_ttc"}
    assert set(sep.CAUSAL_OBSERVABLES) - set(sep.OBSERVABLES) == {"ttc"}


def test_the_table_argument_leaves_the_hindsight_reading_untouched():
    """The refactor is a widening, not a re-measurement.

    Every operator grew an optional `table`; the default path must still be the
    D-334 reading, byte for byte. The re-take also confirmed this at the source
    — its `critical` sub-table reproduced `OBSERVED` exactly — but that costs
    40 rollouts and this costs nothing.
    """
    assert sep.separation_table() == sep.SEPARATION
    assert {s: sep.informative_separators(s) for s in MEASURED_SCENES} \
        == sep.INFORMATIVE_SEPARATION
    for scene in MEASURED_SCENES:
        assert (sep.separating_observables(scene, None)
                == sep.separating_observables(scene, sep.OBSERVED))


def test_the_four_other_scenes_split_three_ways_not_into_a_second_null():
    """The four-scene question does **not** answer the way `cut_in` did.

    `STATE.md` carried this as "a second null there would be a statement about
    the scenario suite itself". It is not a second null: one scene separates at
    both causal indices on an observable that moves. Pinned as the whole census
    so a re-take that flips any scene between classes goes red here rather than
    quietly changing what the branch believes about the suite.
    """
    assert sep.visibility_census() == {
        "robust": ("cafe_head_on_v0",),
        "index_fragile": ("cafe_freezing_v0",),
        "invisible": ("cafe_cut_in_v0", "cafe_convoy_v0",
                      "cafe_obstacle_crossing_v0"),
    }


def test_the_one_robustly_visible_scene_is_the_one_no_switch_needs():
    """`head_on` is visible; D-333 says `cbf_mppi` already wins it.

    The sting of the result, pinned so it is not read as progress toward the
    switch. Every scene a switch would have to arbitrate — `cut_in` above all —
    is in the invisible class, so the visibility that exists is spent on the
    scene that does not need it.
    """
    assert sep.robust_causal_separators("cafe_head_on_v0") == ("closing_speed",)
    assert sep.scene_visibility(sep.QUESTION_SCENE) == "invisible"
    assert sep.QUESTION_SCENE in sep.visibility_census()["invisible"]


def test_robustness_is_an_intersection_so_a_one_index_hit_is_not_robust():
    """`freezing` separates at `fixed_time` only, and that is not enough.

    The discriminant is the intersection across causal indices, not the union,
    because `causal_policies_agree` is measured False. Pinned on the one scene
    that exercises the difference: a union-valued implementation would call
    `freezing` robust and would be green on every other row.
    """
    assert sep.causal_informative_table("fixed_time")["cafe_freezing_v0"] == ("ttc",)
    assert sep.causal_informative_table("first_detection")["cafe_freezing_v0"] == ()
    assert sep.robust_causal_separators("cafe_freezing_v0") == ()
    assert sep.scene_visibility("cafe_freezing_v0") == "index_fragile"


def test_the_census_partitions_the_measured_scenes_exactly_once():
    """Every scene lands in exactly one class, and the classes cover the five.

    A structural pin rather than a value pin: it survives a re-take that moves
    scenes between classes, and it is what makes `visibility_census` readable
    as a partition rather than as three overlapping lists.
    """
    census = sep.visibility_census()
    assert set(census) <= {"robust", "index_fragile", "invisible"}
    flat = [scene for scenes in census.values() for scene in scenes]
    assert sorted(flat) == sorted(MEASURED_SCENES)
    assert len(flat) == len(set(flat))


def test_the_census_has_a_human_readout_and_it_names_every_scene():
    """D-342. The formatter had no caller at all, which made it real residue.

    `consumer_reach` graded `format_visibility_grade` UNREACHED the moment
    D-341 added it, and that grading was right: it is the only one of the four
    new functions the D-341 tests never called. The residue list is for
    functions whose caller would cost a simulation to write — `retake_scene`
    at ~267 s, `compare_arms`, `harvest_costs`. A pure formatter costs nothing,
    so it does not belong on that list; it belongs here. Grading it TEST_ONLY
    rather than pinning it as unreachable is the difference between a consumer
    that is expensive and one that was merely absent.
    """
    grade = sep.format_visibility_grade()
    for scene in MEASURED_SCENES:
        assert scene in grade
    for klass in ("robust", "index_fragile", "invisible"):
        assert klass in grade
    assert "closing_speed" in grade, "the one robust separator is legible"
    assert "Q-162" in grade, "the question scene is marked for the reader"


def test_the_invisible_class_is_two_reasons_not_one():
    """D-341's largest class splits, and the split is what says what would fix it.

    Three scenes shared the `invisible` verdict; they do not share a cause.
    `cut_in` *is* separable at the hindsight index — by `obstacle_speed`, a yaml
    scalar — so a representation carrying something the rollout produced could
    in principle reach it. `convoy` and `obstacle_crossing` have no gap at any
    index against any observable, constants included: no oracle read of the
    scenario file gates them either. Pinned as the whole census, matching the
    visibility census above, so a re-take that moves a scene between reasons is
    red here rather than silently changing what the branch believes.
    """
    assert sep.invisibility_census() == {
        "oracle_only": ("cafe_cut_in_v0",),
        "no_gap_anywhere": ("cafe_convoy_v0", "cafe_obstacle_crossing_v0"),
    }
    assert sep.invisibility_reason(sep.QUESTION_SCENE) == "oracle_only"


def test_invisibility_reason_is_total_so_the_class_cannot_be_scoped_by_accident():
    """Every scene grades, and exactly the non-invisible ones grade `not_invisible`.

    The guard on the census above: if the reason function only answered for
    scenes the caller had already filtered, a caller that filtered wrongly would
    get a reason for a scene that has none, and the census would agree with it.
    Tied to `scene_visibility` in both directions instead.
    """
    for scene in sep.MEASURED_SCENES:
        graded_invisible = sep.scene_visibility(scene) == "invisible"
        reason = sep.invisibility_reason(scene)
        assert (reason != "not_invisible") == graded_invisible, scene
    census = sep.invisibility_census()
    assert sum(len(v) for v in census.values()) == len(
        sep.visibility_census()["invisible"])


def test_a_thin_margin_is_not_a_fragile_one():
    """The reading that refutes the obvious hypothesis about `closing_speed`.

    The suite's one robust separator clears the no-overlap rule by **2.3% of the
    combined spread** at first detection, which invites reading D-341's census as
    a sign-bit artefact — a threshold at zero applied to a quantity sitting on
    top of it. It is not. The separation survives every single-seed deletion on
    both sides, because the combined spread is set by the scene furthest away
    and says nothing about the seed scatter at the boundary.

    Asserted as the *disagreement* rather than as a bound on either number:
    a small margin together with total deletion-stability. Pinning a threshold
    on the margin itself would be D-342's mistake again — the margin is a ratio,
    and either end can move it without touching what the verdict is about.
    """
    table = sep.CAUSAL_OBSERVED["first_detection"]
    margin = sep.separation_margin("cafe_head_on_v0", "closing_speed", table)
    assert 0.0 < margin < 0.05                      # thin by the margin's own units
    assert sep.separation_survives_seed_deletion(
        "cafe_head_on_v0", "closing_speed", table)  # and not fragile at all
    assert sep.separates("cafe_head_on_v0", "closing_speed", table)


def test_the_nearest_miss_is_also_not_one_seed_from_flipping():
    """The other side of the boundary, so the claim is about both directions.

    `obstacle_crossing`/`lateralness` overlaps by 1.7% of spread — closer to zero
    than the separation above — and no single-seed deletion makes it separate.
    So the census boundary is not seed-fragile in either direction, and the two
    scenes straddling it are genuinely on the sides they are recorded on.
    """
    table = sep.CAUSAL_OBSERVED["first_detection"]
    margin = sep.separation_margin("cafe_obstacle_crossing_v0", "lateralness", table)
    assert -0.05 < margin < 0.0
    assert not sep.separates("cafe_obstacle_crossing_v0", "lateralness", table)
    assert not sep.separation_survives_seed_deletion(
        "cafe_obstacle_crossing_v0", "lateralness", table)


def test_every_robust_grade_in_the_census_survives_resampling():
    """The census-wide version: no `robust` grade rests on a single seed."""
    for scene in sep.MEASURED_SCENES:
        assert sep.robust_separators_survive_deletion(scene), scene
    assert sep.robust_causal_separators("cafe_head_on_v0") == ("closing_speed",)


def test_separation_margin_is_the_quantity_separates_thresholds_at_zero():
    """Operator test: the two must agree on sign across the whole measured table.

    Driven over every scene x observable x index rather than the interesting
    rows, so the pair cannot drift apart on a column nobody looked at. Non-finite
    columns are excluded in the same breath both functions exclude them.
    """
    for policy in sep.INDEX_POLICIES:
        table = None if policy == "critical" else sep.CAUSAL_OBSERVED[policy]
        for scene in sep.MEASURED_SCENES:
            for obs in sep._observables_of(table):
                margin = sep.separation_margin(scene, obs, table)
                if margin != margin:                  # nan => not finite
                    assert not sep.separates(scene, obs, table)
                    continue
                assert sep.separates(scene, obs, table) == (margin > 0), (
                    scene, obs, policy)


def test_no_positive_is_seed_fragile_anywhere_in_the_suite():
    """Written to find separating-but-fragile pairs; there are none, and that is
    the result.

    The first draft of this test asserted such a pair must exist, on the
    assumption that a check coinciding with `separates` is a redundant check.
    It went red, and the red was right: across all three indices, every pair
    that separates survives every single-seed deletion on both sides. So the
    positives in D-341's census are not threshold artefacts — the equivalence
    is a measured clean bill, not a tautology, and it is pinned as one so that
    a re-take introducing a fragile positive turns this red.
    """
    for policy in sep.INDEX_POLICIES:
        table = None if policy == "critical" else sep.CAUSAL_OBSERVED[policy]
        for scene in sep.MEASURED_SCENES:
            for obs in sep._observables_of(table):
                if sep.separates(scene, obs, table):
                    assert sep.separation_survives_seed_deletion(
                        scene, obs, table), (scene, obs, policy)


def test_the_seed_fragility_is_all_on_the_negative_side():
    """Where the deletion check does bite — and it bites the invisibility verdict.

    Four negatives would flip to separations if one seed were dropped, while no
    positive would flip the other way. That asymmetry is the honest caveat on
    D-341: its load-bearing claims are all negatives ("nothing separates this
    scene"), and negatives are exactly the class this measurement finds
    seed-sensitive. Pinned as the population, not a count, so a re-take that
    swaps one entry for another cannot stay green.
    """
    assert sep.deletion_fragile_negatives() == (
        ("cafe_freezing_v0", "lateralness", "critical"),
        ("cafe_head_on_v0", "lateralness", "first_detection"),
        ("cafe_head_on_v0", "ttc", "first_detection"),
        ("cafe_obstacle_crossing_v0", "lateralness", "first_detection"),
    )


def test_one_invisible_scene_rests_on_a_flippable_negative_and_one_does_not():
    """The sting, and the reason the two `no_gap_anywhere` scenes are not equals.

    `obstacle_crossing`'s invisibility includes a near-miss one seed-deletion
    could have flipped; `convoy`'s does not appear in the fragile population at
    any index. So of the three invisible scenes, exactly one has a sturdy
    negative, one is oracle-only, and one is a verdict at eight seeds.
    """
    fragile_scenes = {scene for scene, _, _ in sep.deletion_fragile_negatives()}
    assert "cafe_obstacle_crossing_v0" in fragile_scenes
    assert "cafe_convoy_v0" not in fragile_scenes
    assert sep.invisibility_reason("cafe_convoy_v0") == "no_gap_anywhere"
    assert sep.invisibility_reason("cafe_obstacle_crossing_v0") == "no_gap_anywhere"


def test_the_reason_partition_has_a_human_readout_too():
    """Same slot as the D-342 test above, for the same reason.

    `format_invisibility_grade` is a pure formatter, so `consumer_reach` graded
    it UNREACHED the instant it was written and the receipt went red on exactly
    that. D-342 settled which way this resolves: the residue list is for
    functions whose caller would cost a simulation, and a formatter costs
    nothing, so it gets a test rather than a slot. Recorded because the same
    red arrived one cycle after the rule was written — the rule was right, and
    the cost of forgetting it is one full suite.
    """
    grade = sep.format_invisibility_grade()
    for scene in MEASURED_SCENES:
        assert scene in grade
    for reason in ("oracle_only", "no_gap_anywhere", "not_invisible"):
        assert reason in grade
    assert "lateralness" in grade, "the nearest-miss observable is legible"
    assert "invisibility_census" in grade


# --------------------------------------------------------------------------
# the re-take at sixteen seeds (D-344)
# --------------------------------------------------------------------------


def test_the_sixteen_seed_tables_carry_sixteen_seeds_in_every_cell():
    """Provenance before verdict — a short row would separate for free.

    The whole reading is a range comparison, so a scene that silently dropped
    seeds would have a narrower range and could acquire a separation it did not
    earn. Checked in both tables and every cell rather than sampled, because
    the failure this guards is exactly the one that looks like a result.
    """
    for policy, table in sep.doubled_tables().items():
        for scene in MEASURED_SCENES:
            for obs, values in table[scene].items():
                assert len(values) == 16, f"{policy}/{scene}/{obs}"


def test_the_seed_count_walk_reproduces_the_recorded_grade():
    """**The control on the parallel implementation.**

    `_invisibility_reason_from` is a second copy of the grading rule, written
    so the eight-seed functions every other pin reads could stay untouched. A
    second copy is only safe while it agrees with the first, so this runs the
    new walk over the *old* tables and requires the recorded verdict back on
    all five scenes. If it ever drifts, this goes red before any 16-seed claim
    can be quoted — which is the point of asserting it here rather than
    trusting the transcription.
    """
    for scene in MEASURED_SCENES:
        assert (sep._invisibility_reason_from(scene, sep.eight_seed_tables())
                == sep.invisibility_reason(scene)), scene
        assert (sep._visibility_from(scene, sep.eight_seed_tables())
                == sep.scene_visibility(scene)), scene


def test_the_invisible_class_has_two_structural_members_not_one():
    """**The answer STATE.md asked for.**

    `obstacle_crossing`'s `no_gap_anywhere` was a verdict at eight seeds with a
    single-deletion near-miss inside it, so it might have been the sample
    rather than the scene. Doubling the seeds leaves it `no_gap_anywhere`, and
    leaves `convoy` there too. So the class has two structural members, and
    D-341's conclusion does not rest on a coin flip.
    """
    assert sep.invisibility_reason_at_16("cafe_obstacle_crossing_v0") == "no_gap_anywhere"
    assert sep.invisibility_reason_at_16("cafe_convoy_v0") == "no_gap_anywhere"
    assert sep.invisibility_survives_doubling("cafe_obstacle_crossing_v0")
    assert sep.invisibility_survives_doubling("cafe_convoy_v0")
    assert sep.invisibility_reason_at_16("cafe_cut_in_v0") == "oracle_only"


def test_the_one_grade_the_doubling_moves_is_not_the_one_it_was_run_for():
    """The re-take's own surprise, pinned as a population.

    Run to settle `obstacle_crossing`, it settled it — and moved `freezing`
    instead, from `index_fragile` (a separator at one causal index, absent at
    the other) to `invisible`. Pinned as the whole disagreement set rather than
    as the one row, so a later re-take that moves a *different* scene cannot
    stay green by coincidence.
    """
    assert sep.doubling_disagreements() == (
        ("cafe_freezing_v0", "not_invisible", "oracle_only"),
    )
    assert sep.scene_visibility("cafe_freezing_v0") == "index_fragile"
    assert sep.visibility_at_16("cafe_freezing_v0") == "invisible"
    assert sep.visibility_at_16("cafe_head_on_v0") == "robust", "the robust grade holds"


def test_doubling_the_seeds_does_not_shrink_the_fragile_population():
    """The half of the reading that does **not** resolve, and it must stay visible.

    Four deletion-fragile negatives at eight seeds, four at sixteen, with half
    the membership swapped. So more data did not make the near-misses go away;
    it moved them. The honest reading is that deletion fragility is a standing
    property of samples this size, not a specific near-miss that more seeds
    would settle — which bounds how much a further re-take could ever buy.
    """
    assert len(sep.deletion_fragile_negatives()) == 4
    assert len(sep.fragile_negatives_at_16()) == 4
    assert sep.fragile_negatives_at_16() != sep.deletion_fragile_negatives()


def test_the_motivating_near_miss_persists_across_the_doubling():
    """It is not noise, and that is a different claim from the verdict holding.

    `obstacle_crossing` / `lateralness` at first detection is deletion-fragile
    at eight seeds and at sixteen. Its *verdict* is stable (the scene stays
    `no_gap_anywhere`) while its *margin* stays one deletion from flipping —
    both facts are true, and quoting either alone misreads the scene.
    """
    entry = ("cafe_obstacle_crossing_v0", "lateralness", "first_detection")
    assert entry in sep.deletion_fragile_negatives()
    assert entry in sep.fragile_negatives_at_16()
    shared = tuple(e for e in sep.deletion_fragile_negatives()
                   if e in sep.fragile_negatives_at_16())
    assert shared == (
        ("cafe_head_on_v0", "ttc", "first_detection"),
        ("cafe_obstacle_crossing_v0", "lateralness", "first_detection"),
    ), "the intersection is subtracted here, not accessed — see D-344 in the module"


def test_the_doubling_has_a_human_readout_and_it_names_every_scene():
    """Formatter, so it gets a test rather than a residue slot (D-342, D-343)."""
    grade = sep.format_doubling_grade()
    for scene in MEASURED_SCENES:
        assert scene in grade
    assert "reason@8" in grade and "reason@16" in grade
    assert "doubling_disagreements" in grade
    assert "at 8 seeds" in grade and "at 16" in grade, "both counts are legible"
