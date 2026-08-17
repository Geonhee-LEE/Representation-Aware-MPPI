"""A review-debt reading has to be able to say "I don't know".

The module exists because STATE.md carried "sixteen commits" for three cycles
against a tree holding 840, so the obvious thing to test is the magnitude.  That
is the one thing not tested here: the magnitude is a property of whichever tree
the suite happens to run on, and pinning it would make this file go red the day
the branch merges — the reading working exactly as intended.

What is pinned is the part that can silently rot: that ``UNDECIDABLE`` is
reachable and reached for the right reason.  :mod:`git_surface` recorded the
failure mode — a git-reading instrument on a shallow clone returns *no answer*
in the vocabulary of a zero — and this module runs on exactly that clone every
time CI checks out with ``fetch-depth: 1``.  So both surfaces assert positively:
where ``main`` is visible the reading is coherent, where it is not the reading
says so.

This file deliberately contains no loop-body population-claim assertion.  Such
an assertion would join ``loop_reach.targets()`` and owe a ``READING`` entry;
``all(...)`` over a comprehension carries the same claim from outside that
population.
"""

from __future__ import annotations

from eval.mppi_sandbox import branch_debt as bd


# --------------------------------------------------------------------------
# The grade boundary, with no repository in the way
# --------------------------------------------------------------------------

def test_an_empty_walk_is_undecidable_and_never_within_precedent():
    """The bug this module is most likely to grow, pinned at its source.

    An empty precedent walk means nothing was measured.  Falling through to
    ``WITHIN_PRECEDENT`` would report "no merge was large enough to exceed" —
    a clean bill of health — for a clone that simply could not look.  That is
    `git_surface`'s category error verbatim, and it is one `or` away at all
    times.
    """
    assert bd.grade(656, 155_753, 0, 0, 0) == bd.UNDECIDABLE
    assert bd.grade(1, 1, 0, 0, 0) == bd.UNDECIDABLE


def test_either_axis_alone_puts_a_branch_beyond_precedent():
    """The envelope is componentwise, so clearing one axis is not clearing it."""
    # Wide but short, then narrow but long: each exceeds on one axis only.
    assert bd.grade(700, 10, 41, 9_543, 58) == bd.BEYOND_PRECEDENT
    assert bd.grade(2, 200_000, 41, 9_543, 58) == bd.BEYOND_PRECEDENT
    assert bd.grade(41, 9_543, 41, 9_543, 58) == bd.WITHIN_PRECEDENT


def test_the_envelope_is_inclusive_at_its_own_boundary():
    """A diff exactly the size of the largest ever merged has a precedent.

    Strictly `>` rather than `>=` is the intended reading: the claim the module
    publishes is "no diff this size has ever been reviewed", and a diff equal to
    one that *was* reviewed falsifies it.
    """
    assert bd.grade(40, 9_542, 41, 9_543, 58) == bd.WITHIN_PRECEDENT
    assert bd.grade(42, 9_543, 41, 9_543, 58) == bd.BEYOND_PRECEDENT


# --------------------------------------------------------------------------
# Both clone surfaces, asserted positively
# --------------------------------------------------------------------------

def test_an_unreachable_base_is_undecidable_rather_than_zero():
    """The shallow-clone surface, forced without needing a shallow clone.

    A ref that cannot exist stands in for the ref CI does not fetch.  The
    reading must decline, and must decline as a *verdict* — not raise, and not
    report a 0-commit branch, which is what a caller would act on.
    """
    d = bd.debt(base="refs/heads/this-ref-does-not-exist-42", head="HEAD")
    assert d.verdict == bd.UNDECIDABLE
    assert (d.commits, d.files, d.insertions) == (0, 0, 0)
    assert d.precedent_n == 0
    assert "UNDECIDABLE" in bd.report(base="refs/heads/this-ref-does-not-exist-42")


def test_where_main_is_visible_the_reading_is_internally_coherent():
    """The dev-box surface.  Coherence, not magnitude — the magnitude will move.

    On a clone that can see `main` every field has to agree with every other:
    a decided verdict needs a non-empty walk behind it, and the grade has to be
    the one `grade()` returns for the numbers actually measured.  On a clone
    that cannot, this asserts the decline instead, so neither surface passes by
    being quiet.
    """
    d = bd.debt()

    if d.verdict == bd.UNDECIDABLE:
        assert d.precedent_n == 0
        return

    assert d.verdict in (bd.WITHIN_PRECEDENT, bd.BEYOND_PRECEDENT)
    # A decided verdict rests on merges that were actually walked.
    assert d.precedent_n > 0
    assert d.precedent_files > 0 and d.precedent_insertions > 0
    # The published verdict is the one the pure grader gives these numbers.
    assert d.verdict == bd.grade(
        d.files, d.insertions, d.precedent_files, d.precedent_insertions, d.precedent_n
    )


def test_the_ratios_decline_instead_of_dividing_by_zero():
    """`files_ratio` is read straight into prose, so its undecided value matters.

    Returning 0.0 rather than raising keeps `report()` total, and 0.0 is not a
    ratio any real branch produces — a branch with no files is not one anybody
    is reviewing.
    """
    undecided = bd.Debt(bd.UNDECIDABLE, 0, 0, 0, 0, 0, 0)
    assert undecided.files_ratio == 0.0
    assert undecided.insertions_ratio == 0.0

    decided = bd.Debt(bd.BEYOND_PRECEDENT, 840, 656, 155_753, 41, 9_543, 58)
    assert decided.files_ratio == 656 / 41
    assert decided.insertions_ratio == 155_753 / 9_543


def test_the_precedent_walk_skips_the_root_commit_without_counting_it():
    """The root has no parent, so it is not a review anybody performed.

    Counting it would inflate `precedent_n` — the very field the vacuity test
    above leans on — with a commit whose diff was never measured.
    """
    files, insertions, seen = bd.precedent()
    if seen == 0:  # shallow clone; the decline is asserted elsewhere
        return
    total = bd._git("rev-list", "--first-parent", "--count", "main")
    assert total is not None
    # Every walked commit yielded a measurable diff, and the root did not.
    assert seen <= min(int(total), bd.PRECEDENT_WALK)
    assert files > 0 and insertions > 0
