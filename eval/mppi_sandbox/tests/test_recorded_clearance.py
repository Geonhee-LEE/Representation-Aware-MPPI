"""The derivation that replaced `scene_eligibility`'s one-element literal.

The load-bearing test here is not the census shape — it is
`test_a_source_that_repins_itself_moves_the_census`, which is the whole reason
this module exists rather than a second, longer literal. A typed set cannot be
wrong about spelling once the name is imported (D-047) and can still be wrong
about *membership* forever, which is what happened: the old set named one scene
while the tree held two ensembles.

`test_only_the_under_reporting_direction_is_graded` pins the asymmetry. A scene
this module cannot source is reported (`UNSOURCED`) and not convicted, because
an ensemble may live in a module the registry has not been taught to read;
convicting there would make the honest response "delete the declaration", which
is the direction that loses coverage.
"""

import pytest

from eval.mppi_sandbox.recorded_clearance import (
    IN_SYNC,
    MIN_SEEDS,
    MISSING,
    SOURCES,
    UNSOURCED,
    Drift,
    Ensemble,
    drift,
    ensembles,
    format_grade,
    recorded_scenes,
)


@pytest.fixture(scope="module")
def rows():
    return ensembles()


# --- the census reads source, and source is what it reports ----------------

def test_every_registered_source_resolves(rows):
    """A reader that stops resolving must be a loud failure, not a silent drop:
    a dropped source under-reports coverage in exactly the way the old literal
    did."""
    # Not `len(SOURCES)`: one reader may own several scenes, so the row count
    # is at least the reader count and the readers are what must all resolve.
    assert len(rows) >= len(SOURCES)
    assert len({e.source for e in rows}) == len(SOURCES)
    for e in rows:
        assert e.scenario and e.source
        assert e.n_seeds > 0 and e.n_arms > 0


def test_all_known_ensembles_are_found(rows):
    """The five that exist today, named so a future deletion is visible.

    `cafe_obstacle_crossing_v0` joined when `scene_transfer` was registered
    (D-417's demanded follow-up). It is the member that cost something: the
    census printed it `ELIGIBLE (unmeasured)` and STATE called it "the only
    eligible scene genuinely unmeasured" while an 8 arms x 8 seeds column sat
    in `scene_transfer` — the same shape as the `cafe_convoy_v0` miss one
    layer down, and the second time this set was wrong in this direction.
    """
    by_scene = {e.scenario: e for e in rows}
    assert set(by_scene) == {"cafe_head_on_v0", "cafe_freezing_v0",
                             "cafe_convoy_v0", "cafe_cut_in_v0",
                             "cafe_obstacle_crossing_v0"}
    # The one the literal missed, and the count that makes it an ensemble
    # rather than a reading.
    assert by_scene["cafe_freezing_v0"].n_seeds == 8
    assert by_scene["cafe_freezing_v0"].n_arms == 8
    assert by_scene["cafe_head_on_v0"].n_seeds == 32


def test_the_paired_ensemble_source_is_registered(rows):
    """The source D-413's own derivation missed. `cafe_convoy_v0` is the member
    that costs something: `scene_eligibility` printed it `ELIGIBLE (unmeasured)`
    and STATE's first claude-actionable was to go and measure it, while these
    8 seeds x 2 arms sat in the tree from 2026-08-18."""
    # Indexed by (scene, source), not by scene: since `scene_transfer` was
    # registered these two scenes each carry *two* rows, and a
    # `{e.scenario: e}` comprehension would silently keep whichever sorted
    # last and stop testing this source at all. Two modules measuring one
    # scene is a fact the census is meant to show, not a duplicate to collapse.
    by_key = {(e.scenario, e.source): e for e in rows}
    for scene in ("cafe_convoy_v0", "cafe_cut_in_v0"):
        row = by_key[(scene, "scene_census.PAIRED_ENSEMBLE")]
        assert row.n_seeds == 8
        # baseline + the one challenger arm the pair was taken on
        assert row.n_arms == 2
        # The other reader on the same scene walks the full arm set, so the
        # overlap is genuinely two different measurements, not one counted twice.
        assert by_key[(scene, "scene_transfer.columns()")].n_arms == 8


def test_the_missed_source_was_masked_the_same_way_the_last_one_was():
    """Why `drift()` stayed `IN_SYNC` while the registry was incomplete: the
    declared set is *derived from* the same readers, so a missing reader moves
    both sides together and the census cannot see itself. `cafe_cut_in_v0` is
    the harmless half (excluded `GOAL_BALL_BLOCKED`) and `cafe_convoy_v0` is
    the half that sent a cycle to re-measure measured work."""
    from eval.mppi_sandbox.scene_eligibility import census

    before = frozenset({"cafe_freezing_v0", "cafe_head_on_v0"})
    assert Drift(derived=recorded_scenes(), declared=before).verdict == MISSING
    assert Drift(derived=recorded_scenes(),
                 declared=before).missing == frozenset(
        {"cafe_convoy_v0", "cafe_cut_in_v0", "cafe_obstacle_crossing_v0"})

    measured = {s.scenario for s in census().measured}
    assert "cafe_convoy_v0" in measured
    # cut_in is recorded but excluded — recorded data is not coverage.
    assert "cafe_cut_in_v0" not in measured


def test_a_source_that_repins_itself_moves_the_census(monkeypatch):
    """The property a literal cannot have. Re-pin `clearance_census` to another
    scene and the derived set follows it — no edit here, no stale member."""
    import eval.mppi_sandbox.clearance_census as cc

    monkeypatch.setattr(cc, "PEAK_SCENE", "cafe_convoy_v0", raising=True)
    # Asserted on this reader's own row rather than on `recorded_scenes()`:
    # since `scene_transfer` was registered it covers `cafe_freezing_v0`
    # independently, so the union no longer drops the scene when this source
    # is re-pinned. The property under test is that the row *follows* its
    # module — a set-membership check would now pass for the wrong reason.
    row = next(e for e in ensembles()
               if e.source == "clearance_census.SEED_ENSEMBLE")
    assert row.scenario == "cafe_convoy_v0"


def test_one_seed_is_a_reading_not_an_ensemble():
    """Every scene in `runs/*.json` has exactly seed 0. Folding those in would
    mark all eight scenes measured and make the coverage count meaningless, so
    the floor is stated rather than assumed."""
    assert MIN_SEEDS == 2
    single = Ensemble(source="s", scenario="x", n_seeds=1, n_arms=1)
    assert single.n_seeds < MIN_SEEDS


# --- the grade, and the direction it grades in -----------------------------

def test_shipped_declaration_is_in_sync():
    """`scene_eligibility.RECORDED_SCENES` is the derivation, so this holds by
    construction — and fails loudly if anyone types it back."""
    d = drift()
    assert d.verdict == IN_SYNC
    assert d.in_sync


def test_only_the_under_reporting_direction_is_graded():
    derived = recorded_scenes()
    short = Drift(derived=derived, declared=frozenset())
    assert short.verdict == MISSING
    assert not short.in_sync

    wide = Drift(derived=derived, declared=derived | {"scene_from_a_module_we_cannot_read"})
    assert wide.verdict == UNSOURCED
    assert wide.in_sync          # reported, not convicted
    assert wide.unsourced == frozenset({"scene_from_a_module_we_cannot_read"})


def test_the_exact_drift_the_old_literal_carried():
    """Reproduce the shipped bug against the derivation, so the finding is a
    test rather than a paragraph in a journal."""
    from eval.mppi_sandbox.scorable_band import PUBLISHED_SCENARIO

    old = Drift(derived=recorded_scenes(), declared=frozenset({PUBLISHED_SCENARIO}))
    assert old.verdict == MISSING
    assert old.missing == frozenset(
        {"cafe_freezing_v0", "cafe_convoy_v0", "cafe_cut_in_v0",
         "cafe_obstacle_crossing_v0"})


def test_render_names_the_missing_member_not_just_a_count():
    """A count of ensembles is not actionable; the scene name is. D-318's
    lesson about a check whose scope reads narrower than it looks."""
    text = format_grade()
    assert "cafe_freezing_v0" in text and "cafe_head_on_v0" in text
    assert "8 seeds" in text and "32 seeds" in text
    assert IN_SYNC in text
