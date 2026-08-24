"""A partial CI run must not be readable as a complete one.

These pin the refusal, not the snapshot's contents -- the numbers in
``run_completeness`` are a measurement of one run and will be superseded by the next.
What must survive is the property that made 2026-08-25 06:00 misread run
32756918395: a count taken from shards that reported looks identical to a count
taken from all of them.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import run_completeness


def test_the_snapshot_covers_exactly_the_shards_the_workflow_declares():
    """Derived vs typed (D-047) -- a matrix-width change must not slip past.

    If the fast job's matrix grows to 12, this snapshot is grading 8 of 12 and
    every reading off it silently becomes a floor for a second reason.
    """
    declared = run_completeness.shards_declared_by_workflow()
    snapshot_shards = {
        int(name.rsplit("(", 1)[1].rstrip(")"))
        for name, _, _ in run_completeness.RUN_32756918395
        if name.startswith("pytest (fast) (")
    }
    assert snapshot_shards == set(declared), (
        f"snapshot covers shards {sorted(snapshot_shards)} but the workflow "
        f"declares {list(declared)}"
    )


def test_failing_tests_refuses_on_a_run_with_no_verdict():
    """The whole point: the complete reader is not available on a partial run."""
    with pytest.raises(run_completeness.IncompleteRun) as excinfo:
        run_completeness.failing_tests()
    message = str(excinfo.value)
    assert "slow closed-loop" in message
    assert "lower bound" in message


def test_the_floor_reader_always_says_it_is_a_floor():
    floor = run_completeness.failure_floor()
    assert floor["is_floor"] is True
    assert floor["count"] == len(run_completeness.OBSERVED_FAILURES)
    assert floor["unverdicted_jobs"], "a floor with nothing missing is not a floor"
    assert "CI_PARTIAL" in run_completeness.reading()
    assert ">= 7" in run_completeness.reading()


def test_a_cancelled_job_is_not_a_passing_one():
    """``cancelled`` and ``in_progress`` are the absence of a verdict.

    Run-level ``conclusion`` reports both as non-success, which is how D-084
    describes STATE reading a cancelled run as green.
    """
    missing = dict(run_completeness.unverdicted())
    assert missing["pytest (fast) (6)"] == "cancelled"
    assert missing["pytest (slow closed-loop)"] == "in_progress"
    assert len(missing) == 2

    complete = tuple(
        (name, "success" if conclusion != "failure" else conclusion, seconds)
        for name, conclusion, seconds in run_completeness.RUN_32756918395
    )
    assert run_completeness.is_complete(complete)
    assert run_completeness.failure_floor(complete)["is_floor"] is False


def test_state_undercounted_and_the_gap_is_a_strict_subset():
    """The 06:00 misreading, pinned as a datum.

    STATE named 4 of the 7. The three it missed are all in files it never
    mentioned -- which is why "two failure classes" read as a complete
    taxonomy.
    """
    observed = set(run_completeness.OBSERVED_FAILURES)
    state = set(run_completeness.STATE_READING)
    assert state < observed, "STATE's reading should be a strict subset"
    missed = observed - state
    assert len(missed) == 3
    missed_files = {t.split("::", 1)[0] for t in missed}
    state_files = {t.split("::", 1)[0] for t in state}
    assert missed_files.isdisjoint(state_files), (
        "the missed failures should sit in files STATE never named -- that is "
        "the mechanism, not the count"
    )


def test_shard_six_breached_the_declared_ceiling():
    """Fourth crossing of the D-084/D-094/D-227 shape; the workflow forbids a bump."""
    breaches = run_completeness.ceiling_breaches()
    assert breaches == ("pytest (fast) (6)",)
    # And it is not a breach against a ceiling we invented here.
    assert "timeout-minutes: 30" in run_completeness._WORKFLOW.read_text(encoding="utf-8")


def test_every_ci_red_test_is_green_locally():
    """The divergence is total, and that is the finding.

    Not "some tests are flaky": all seven pass on the dev box in 39.77 s. A
    local receipt therefore carries **zero** information about this class --
    D-462's lesson on a third axis.
    """
    assert run_completeness.LOCAL_VERDICT_ALL_PASS is True
    files = {t.split("::", 1)[0] for t in run_completeness.OBSERVED_FAILURES}
    assert len(files) == 4, "the class spans four files, not one"


def test_both_job_ceilings_are_read_from_the_workflow():
    """Two jobs, two ceilings -- and neither is typed here (D-047)."""
    declared = run_completeness.timeouts_declared_by_workflow()
    assert declared == {"pytest (fast)": 30, "pytest (slow closed-loop)": 360}


def test_a_matrix_shard_inherits_its_declared_jobs_ceiling():
    """Observed names carry the matrix suffix; the declaration does not."""
    assert run_completeness.declared_ceiling_minutes("pytest (fast) (6)") == 30
    assert run_completeness.declared_ceiling_minutes("pytest (slow closed-loop)") == 360
    with pytest.raises(run_completeness.IncompleteRun):
        run_completeness.declared_ceiling_minutes("pytest (nonexistent)")


def test_the_slow_job_is_not_graded_against_the_fast_jobs_ceiling():
    """Regression guard for the hand-typed ``limit_minutes=30`` this replaced.

    A cancelled slow job at 40 minutes is nowhere near its 360-minute ceiling.
    Under the old typed default it would have been reported as a breach --
    wrong by 12x, and wrong in the direction that manufactures evidence for a
    ceiling bump the workflow's own comment forbids.
    """
    snapshot = (("pytest (slow closed-loop)", "cancelled", 2400),)
    assert run_completeness.ceiling_breaches(snapshot) == ()
    # Same job, past its real ceiling: still detected.
    past = (("pytest (slow closed-loop)", "cancelled", 360 * 60),)
    assert run_completeness.ceiling_breaches(past) == ("pytest (slow closed-loop)",)


def test_an_open_job_has_a_deadline_derived_from_its_own_timeout():
    """The wait is bounded: GitHub cancels at ``timeout-minutes``.

    Start 17:29:28Z + 360 min = 23:29:28Z = 08:29:28 KST. This is what turns
    STATE's open-ended "re-read once it concludes" into a schedulable instant.
    """
    assert run_completeness.verdict_deadline() == "2026-08-25T08:29:28+09:00"


def test_a_terminal_verdictless_job_contributes_no_deadline():
    """``cancelled`` is not "still coming" -- waiting cannot fix it.

    Shard 6 lacks a verdict and always will. If it were given a deadline the
    caller would be told to re-read at a time when nothing can have changed.
    """
    only_cancelled = (("pytest (fast) (6)", "cancelled", 1804),)
    assert run_completeness.unverdicted(only_cancelled)  # it IS verdictless
    assert run_completeness.verdict_deadline(only_cancelled) is None


def test_a_complete_run_has_no_deadline_to_wait_for():
    complete = (("pytest (fast) (1)", "success", 10),)
    assert run_completeness.verdict_deadline(complete) is None


def test_the_partial_reading_names_when_to_re_read():
    """A floor that does not say when it stops being a floor invites a poll."""
    text = run_completeness.reading()
    assert "CI_PARTIAL" in text
    assert "2026-08-25T08:29:28+09:00" in text
