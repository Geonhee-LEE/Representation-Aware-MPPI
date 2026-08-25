"""An empty queue and an unreadable one must not spell the same thing.

The magnitudes are not pinned here, for :mod:`test_branch_debt`'s reason: they
are properties of whichever tree and whichever queue the suite runs against, and
pinning them makes this file go red the day a human merges something — the
reading working exactly as intended.

What is pinned is the part that would fail silently and in the dangerous
direction.  :mod:`queue_debt`'s consumer is gate 1, which decides whether the
executor may add to the queue.  ``gh`` unavailable produces zero PRs, and zero
PRs read as a measurement authorise exactly the branch-opening the gate exists
to prevent — the failure fires precisely when the executor cannot see what it is
adding to.  So both surfaces assert positively: an unreadable listing declines,
a genuinely empty one does not.

This file deliberately contains no loop-body population-claim assertion.  Such
an assertion would join ``loop_reach.targets()`` and owe a ``READING`` entry;
``all(...)`` over a comprehension carries the same claim from outside that
population.
"""

from __future__ import annotations

from eval.mppi_sandbox import branch_debt as bd
from eval.mppi_sandbox import queue_debt as qd


def _entry(number: int, review_files: int, review_insertions: int,
           merge_files: int = 1, merge_insertions: int = 1,
           verdict: str = qd.UNGRADED) -> qd.Entry:
    """A measured-but-arbitrary entry, so the grade boundary needs no git."""
    return qd.Entry(
        number=number,
        branch=f"autoresearch/p3-{number}",
        verdict=verdict,
        review_files=review_files,
        review_insertions=review_insertions,
        merge_files=merge_files,
        merge_insertions=merge_insertions,
    )


# --------------------------------------------------------------------------
# The two zeros, kept apart
# --------------------------------------------------------------------------

def test_an_unreadable_listing_is_undecidable_rather_than_an_empty_queue(monkeypatch):
    """`gh` could not answer, so the queue's depth is unknown — not zero.

    This is the whole exposure.  A caller acting on "0 open PRs" opens a branch;
    a caller acting on UNDECIDABLE does not.
    """
    monkeypatch.setattr(qd, "_listing", lambda prefix=qd.QUEUE_PREFIX: None)
    reading = qd.read()
    assert reading.verdict == qd.UNDECIDABLE
    assert reading.entries == ()
    assert "not an empty queue" in qd.summary(reading)


def test_a_genuinely_empty_queue_is_measured_not_undecidable(monkeypatch):
    """The other side of the same boundary, so the refusal cannot be vacuous.

    Without this, `read` could return UNDECIDABLE unconditionally and the test
    above would still pass.
    """
    monkeypatch.setattr(qd, "_listing", lambda prefix=qd.QUEUE_PREFIX: [])
    reading = qd.read()
    assert reading.verdict == qd.MEASURED
    assert reading.entries == ()
    assert reading.precedent_n > 0


def test_an_underived_envelope_refuses_the_whole_queue(monkeypatch):
    """A listing that reads against a history that does not is still no answer.

    The shallow-clone surface: `gh` is authenticated but `main` was never
    fetched, so there is no precedent to grade against.  Grading anyway would
    publish `WITHIN_PRECEDENT` for every entry — "no merge was large enough to
    exceed" from a clone that could not look.
    """
    monkeypatch.setattr(
        qd, "_listing",
        lambda prefix=qd.QUEUE_PREFIX: [(67, "autoresearch/p3-x")],
    )
    monkeypatch.setattr(bd, "precedent", lambda base="main", walk=80: (0, 0, 0))
    assert qd.read().verdict == qd.UNDECIDABLE


# --------------------------------------------------------------------------
# A measurement does not acquire a grade by default
# --------------------------------------------------------------------------

def test_measure_does_not_invent_a_grade():
    """`measure` has no envelope, so it must not spell a verdict.

    A placeholder that happens to be a real verdict reads as a grade to every
    caller that forgets `graded`.
    """
    assert qd.UNGRADED not in (qd.WITHIN_PRECEDENT, qd.BEYOND_PRECEDENT)
    assert qd.UNGRADED != qd.UNDECIDABLE


def test_an_unmeasurable_branch_is_undecidable_rather_than_zero_sized():
    """A branch with no remote ref in this clone declines, and does not raise.

    A ref that cannot exist stands in for the queued branches a fresh clone has
    not fetched.  Reporting it as 0 files would rank it *first* — the cheapest
    merge in the queue is the one nobody can see.
    """
    e = qd.measure(999, "no-such-branch-ever-42")
    assert e.verdict == qd.UNDECIDABLE
    assert (e.review_files, e.review_insertions) == (0, 0)
    assert (e.merge_files, e.merge_insertions) == (0, 0)


def test_grading_cannot_launder_an_undecidable_entry():
    """Passing an unmeasured entry through the grader must not grade it."""
    unmeasured = _entry(1, 0, 0, 0, 0, verdict=qd.UNDECIDABLE)
    out = qd.graded(unmeasured, 41, 9_543, 58)
    assert out.verdict == qd.UNDECIDABLE


# --------------------------------------------------------------------------
# The two instruments, kept apart
# --------------------------------------------------------------------------

def test_review_cost_and_merge_effect_are_independent_fields():
    """The `#23` shape: expensive to read, byte-identical to merge.

    D-323 read three-dot as merge effect and went looking for files that were
    not there.  Reading two-dot as review cost would have called the same PR a
    152-file monster.  Neither number is recoverable from the other, so the
    grade must come from review cost while `is_no_op_merge` reports the other.
    """
    no_op = qd.graded(_entry(23, 7, 347, merge_files=0, merge_insertions=0),
                      41, 9_543, 58)
    assert no_op.is_no_op_merge
    assert no_op.verdict == qd.WITHIN_PRECEDENT

    # A PR that changes `main` is not a no-op, at identical review cost.
    real = qd.graded(_entry(24, 7, 347, merge_files=7, merge_insertions=347),
                     41, 9_543, 58)
    assert not real.is_no_op_merge
    assert real.verdict == no_op.verdict


def test_an_empty_pathspec_measures_nothing_rather_than_everything():
    """`git diff base head --` with no paths diffs *every* path.

    The scoping is what keeps merge effect bounded by review cost; a branch that
    touched nothing must therefore short-circuit rather than fall through to an
    unscoped comparison, which is the 152-file reading this module removed.
    """
    assert qd._merge_effect("main", "HEAD", []) == (0, 0)


def test_the_grade_follows_review_cost_and_not_merge_effect():
    """A no-op merge of a huge branch is still a huge review."""
    huge = qd.graded(_entry(67, 659, 156_230, merge_files=0, merge_insertions=0),
                     41, 9_543, 58)
    assert huge.verdict == qd.BEYOND_PRECEDENT


# --------------------------------------------------------------------------
# The ordering is the deliverable
# --------------------------------------------------------------------------

def test_rank_puts_the_cheapest_review_first():
    """Gate 1 exists to name a cheap merge, so cheap must come first."""
    ranked = qd.rank([_entry(67, 659, 156_230), _entry(66, 4, 98),
                      _entry(69, 7, 513)])
    assert [e.number for e in ranked] == [66, 69, 67]


def test_rank_sinks_unmeasurable_entries_below_measured_ones():
    """An entry measured at zero because it could not be measured must not lead.

    Sorting on size alone would put every UNDECIDABLE entry — all zeros — at the
    top of a list whose entire purpose is "act on the first row".
    """
    ranked = qd.rank([
        _entry(9, 0, 0, 0, 0, verdict=qd.UNDECIDABLE),
        _entry(66, 4, 98, verdict=qd.WITHIN_PRECEDENT),
    ])
    assert [e.number for e in ranked] == [66, 9]
