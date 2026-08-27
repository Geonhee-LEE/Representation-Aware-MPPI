"""Which denominator may an admission-gap claim be quoted over — 72 or 64?

The table is 72 cells and no test here disputes that; `test_lam_window_keying`
already pins it and should. What these tests pin is the narrower claim P5
reports, because the two numbers answer different questions and the project
spent three cycles carrying the wrong one in `STATE.md`'s headline.

The load-bearing test is `test_blocked_scene_cells_are_excluded_not_counted`.
It does not assert 64; it asserts the **relationship** — that the excluded
cells are exactly the blocked scene's row and that they are absent from
`empty`. A test that only pinned the integer would still pass if the screen
were dropped and some unrelated scene went missing, which is the substitution
the whole reading exists to prevent.

`test_denominator_follows_the_screen_not_a_literal` is the D-047 check on this
module: it moves a scene's goal ball in a synthetic table and requires the
denominator to move with it. That is what distinguishes a derived count from a
hand-typed 64 that happens to be right today.
"""

import pytest

from eval.mppi_sandbox.baseline_matrix import (
    ReportableSurface,
    reportable_surface,
    scene_admission_gap,
)
from eval.mppi_sandbox.calibrate_lam import load_windows
from eval.mppi_sandbox.scene_eligibility import GOAL_BALL_BLOCKED, screen
from eval.mppi_sandbox.scenario import load_scenario


BLOCKED_SCENE = "cafe_cut_in_v0.yaml"

#: The one cell inside the reportable surface with an empty window. D-482 /
#: Q-206 measured it structural (17 temperatures x 8 seeds, best 6/8 in band
#: against an 8/8 requirement), so it is explained rather than open — but it is
#: still empty, and the surface reports it as such.
EXPLAINED_CELL = ("cafe_obstacle_crossing_v0.yaml", "cbf_mppi")


@pytest.fixture(scope="module")
def surface():
    return reportable_surface()


def test_the_shipped_reading_is_63_of_64(surface):
    """The sentence P5 reports, pinned against the shipped table."""
    assert surface.cells == 64
    assert surface.admissible == 63
    assert len(surface.controllers) == 8
    assert len(surface.completable) == 8


def test_blocked_scene_cells_are_excluded_not_counted(surface):
    """The 8 `cafe_cut_in_v0` cells are geometry's verdict, not a gap.

    Asserted as a relationship rather than as the integer 8: the claim is that
    *every* excluded cell sits on the blocked scene and *no* excluded cell is
    also reported as a gap. An integer-only assertion survives the screen being
    dropped and a different scene disappearing instead.
    """
    assert surface.uncompletable == (BLOCKED_SCENE,)
    assert {s for s, _c in surface.excluded_empty} == {BLOCKED_SCENE}
    assert len(surface.excluded_empty) == len(surface.controllers)
    assert not set(surface.excluded_empty) & set(surface.empty)
    assert BLOCKED_SCENE not in surface.completable


def test_the_one_empty_cell_is_the_explained_one(surface):
    """`empty` names the D-482 cell and nothing else.

    "1 empty" and "1 empty *and it is this cell*" differ by exactly the
    substitution that would let a newly-broken cell hide behind the closed
    one's count.
    """
    assert surface.empty == (EXPLAINED_CELL,)


def test_the_blocked_scene_really_is_blocked_by_proof():
    """The exclusion rests on the screen, not on this test's say-so.

    If `cafe_cut_in_v0`'s geometry is ever fixed, this fails first and names
    the reason the denominator must move — rather than leaving the 64 pinned
    against a scene that has since become completable.
    """
    verdict = screen(load_scenario(f"eval/scenarios/{BLOCKED_SCENE}"),
                     "cafe_cut_in_v0")
    assert GOAL_BALL_BLOCKED in verdict.exclusions
    assert verdict.best_goal_clearance < 0.0


def test_it_agrees_with_the_scene_axis_gap():
    """Two functions, one fact — the scene the headline cannot see.

    `scene_admission_gap` finds it by asking which scene every controller
    declined; `reportable_surface` finds it by screening geometry. They are
    independent derivations and a disagreement means one of them is reading a
    stale table.
    """
    _uncalibrated, inadmissible = scene_admission_gap()
    assert set(reportable_surface().uncompletable) <= set(inadmissible)


def test_denominator_follows_the_screen_not_a_literal(tmp_path):
    """D-047 on this module: block a second scene, lose a second row.

    Built as a synthetic table so the assertion is about the *derivation*. A
    hand-typed 64 passes every test above and fails this one.
    """
    windows = load_windows()
    controllers = sorted({c for _s, c in windows})
    # Two scenes, one of which the real screen convicts.
    scenes = [BLOCKED_SCENE, "cafe_straight_v0.yaml"]
    synthetic = {
        (s, c): {"admissible": [(0.2, 0.4)]}
        for s in scenes for c in controllers
    }

    reading = reportable_surface(windows=synthetic)

    assert reading.uncompletable == (BLOCKED_SCENE,)
    assert reading.completable == ("cafe_straight_v0.yaml",)
    assert reading.cells == len(controllers)          # one scene, not two
    assert len(reading.excluded_empty) == 0           # all marked admissible
    assert reading.admissible == len(controllers)


def test_a_table_with_no_blocked_scene_excludes_nothing():
    """The screen must be capable of convicting nobody.

    Without this, a `reportable_surface` that unconditionally dropped one scene
    would pass every shipped-table assertion above.
    """
    synthetic = {
        ("cafe_straight_v0.yaml", "stock_mppi"): {"admissible": [(0.2, 0.4)]},
    }
    reading = reportable_surface(windows=synthetic)

    assert reading.uncompletable == ()
    assert reading.cells == 1
    assert reading.admissible == 1
    assert reading.excluded_empty == ()


def test_untabled_scene_is_not_silently_called_completable(tmp_path):
    """A scene with no yaml cannot be screened, so it is not counted.

    Counting it would put a cell in the denominator that no screen ever
    cleared — the failure mode `scene_admission_gap`'s `uncalibrated` half
    exists to keep separate from a measured verdict.
    """
    synthetic = {("no_such_scene_v0.yaml", "stock_mppi"): {"admissible": []}}
    reading = reportable_surface(windows=synthetic)

    assert reading.uncompletable == ()
    assert "no_such_scene_v0.yaml" in reading.completable
    assert reading.empty == (("no_such_scene_v0.yaml", "stock_mppi"),)


def test_str_names_the_cell_rather_than_only_counting_it(surface):
    """The printed line has to survive being pasted into a journal alone."""
    text = str(surface)
    assert "63 of 64" in text
    assert "cbf_mppi" in text
    assert "cafe_cut_in_v0" in text


def test_surface_is_frozen():
    with pytest.raises(Exception):
        reportable_surface().controllers = ()


def test_dataclass_cells_is_a_product_not_a_stored_count():
    """`cells` is computed, so it cannot disagree with the axes it counts."""
    s = ReportableSurface(
        controllers=("a", "b"),
        completable=("x.yaml", "y.yaml", "z.yaml"),
        uncompletable=(),
        empty=(),
        excluded_empty=(),
    )
    assert s.cells == 6
    assert s.admissible == 6
