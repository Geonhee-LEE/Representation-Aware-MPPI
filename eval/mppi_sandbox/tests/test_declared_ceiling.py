"""The ceiling must be readable where it is enforced, and red when outgrown.

Three CI ceiling raises on this branch were each set from the last reading and
each silently became the thing under test.  These tests are the mechanism that
makes a fourth one impossible to do quietly: the requirement is derived from a
measured floor, the declared value is read from the workflow rather than from a
copy, and every way of *not knowing* is asserted to produce a verdict rather
than a pass.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import declared_ceiling as dc
from eval.mppi_sandbox import nested_run_ledger as nrl
from eval.mppi_sandbox import nested_suite_cost as nsc


def _workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "wf.yml"
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# The live tree.  These are the assertions that go red when the suite grows.
# ---------------------------------------------------------------------------

def test_the_copy_still_says_what_the_workflow_enforces():
    """D-047's defect class: the ceiling is stated twice.

    ``nested_suite_cost.SLOW_CEILING_SECONDS`` is what every ``grade()`` in this
    package measures against; ``timeout-minutes`` is what CI applies.  Raise one
    without the other and the instruments report on a ceiling that does not
    exist — in whichever direction happens to read clean.
    """
    assert dc.agreement() == dc.AGREES, (
        f"workflow says {dc.ceiling_seconds()} s, the copy says "
        f"{nsc.SLOW_CEILING_SECONDS} s")


def test_the_declared_ceiling_clears_the_measured_collapsed_floor():
    reading = dc.grade()
    assert reading.verdict == dc.SUFFICIENT, (
        f"{reading.verdict}: floor {reading.floor_seconds} s needs "
        f"timeout-minutes: {reading.required_minutes}, workflow declares "
        f"{reading.declared_seconds} s")
    assert reading.headroom_seconds is not None
    assert reading.headroom_seconds >= 0


def test_the_floor_is_the_upper_bound_over_runner_classes():
    """Sufficiency may only ever be certified from the *upper* bound.

    D-092's first draft read 5 classes where the population is 6, and 5 x 1396
    fits the old ceiling while 6 x 1396 does not — one missing name inverted the
    verdict.  So this pins the floor to ``declared_classes``, the bound that
    unions both scans, and not to anything cheaper.
    """
    assert (dc.collapsed_floor_seconds()
            == len(nrl.declared_classes()) * nsc.CI_FAST_HALF_SECONDS)


# ---------------------------------------------------------------------------
# The runway.  A number is only a measurement if it is falsifiable.
# ---------------------------------------------------------------------------

def test_the_runway_is_where_no_declarable_ceiling_exists():
    """One more runner class fits; the one after that cannot be fixed by any
    ``timeout-minutes`` value at all.

    Stated as a boundary rather than as a count, so the claim fails if the
    boundary moves: at ``runway`` extra classes the requirement is still
    declarable, and at ``runway + 1`` it is :data:`UNENFORCEABLE`.
    """
    room = dc.runway()
    assert room is not None
    classes = len(nrl.declared_classes())
    unit = nsc.CI_FAST_HALF_SECONDS
    cap_seconds = dc.PLATFORM_MAX_MINUTES * 60

    assert dc.required_seconds((classes + room) * unit) <= cap_seconds
    assert dc.required_seconds((classes + room + 1) * unit) > cap_seconds

    over = dc.grade(floor_seconds=(classes + room + 1) * unit)
    assert over.verdict == dc.UNENFORCEABLE


def test_an_unverified_cap_yields_no_runway_number():
    """The cap is an input this cycle could not fetch, so it may not be printed
    in the shape of a measurement."""
    assert dc.runway(cap_minutes=None) is None


def test_an_unverified_cap_does_not_certify_a_short_ceiling(tmp_path):
    wf = _workflow(tmp_path, "jobs:\n  slow:\n    timeout-minutes: 5\n")
    reading = dc.grade(workflow=wf, cap_minutes=None)
    assert reading.verdict == dc.CAP_UNVERIFIED
    assert reading.verdict != dc.SUFFICIENT


# ---------------------------------------------------------------------------
# Every way of not knowing.  This package has now named six of these; each one
# arrived as a pass that meant nothing.
# ---------------------------------------------------------------------------

def test_an_unreadable_workflow_is_not_a_clean_bill(tmp_path):
    missing = tmp_path / "nope.yml"
    assert dc.declared_ceilings(missing) is None
    assert dc.grade(workflow=missing).verdict == dc.UNREAD


def test_malformed_yaml_is_not_a_clean_bill(tmp_path):
    wf = _workflow(tmp_path, "jobs: [this, is, not, a, mapping]\n")
    assert dc.declared_ceilings(wf) is None
    assert dc.grade(workflow=wf).verdict == dc.UNREAD


def test_a_job_declaring_no_timeout_is_UNDECLARED_not_unlimited(tmp_path):
    """An absent ``timeout-minutes`` is the platform default, not the absence of
    a limit.  Reading a missing key as a missing constraint is the shape that
    hid six red tests for twelve runs."""
    wf = _workflow(tmp_path, "jobs:\n  slow:\n    runs-on: ubuntu-24.04\n")
    assert dc.declared_ceilings(wf) == {"slow": None}
    assert dc.grade(workflow=wf).verdict == dc.UNDECLARED


def test_a_job_absent_from_the_workflow_reads_UNREAD(tmp_path):
    wf = _workflow(tmp_path, "jobs:\n  fast:\n    timeout-minutes: 30\n")
    assert dc.grade(job="slow", workflow=wf).verdict == dc.UNREAD


# ---------------------------------------------------------------------------
# The bound belongs to one job.  D-090's shape, twice a verdict-inverter here.
# ---------------------------------------------------------------------------

def test_the_collapsed_floor_refuses_to_grade_another_job():
    """The nested runs live in ``slow``-marked tests, so the floor is a
    statement about ``slow``.  Applying it to ``fast`` would be a bound computed
    for one purpose used for another — and it would read ``INSUFFICIENT``,
    i.e. a confident wrong answer rather than a refusal."""
    assert dc.grade(job="fast").verdict == dc.WRONG_SUBJECT


def test_another_job_grades_fine_when_its_own_floor_is_supplied(tmp_path):
    """The refusal above is about an *unsupplied* floor, not about the job.

    Without this the previous test is satisfied by a module that simply never
    grades ``fast``, which is the vacuous-guard shape D-075 / D-081 / D-088 each
    shipped once.
    """
    wf = _workflow(tmp_path, "jobs:\n  fast:\n    timeout-minutes: 30\n")
    reading = dc.grade(job="fast", workflow=wf, floor_seconds=600)
    assert reading.verdict == dc.SUFFICIENT
    assert reading.floor_seconds == 600


# ---------------------------------------------------------------------------
# Arithmetic that may not round in its own favour.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("floor,expected", [(1, 2), (100, 200), (8376, 16752)])
def test_the_requirement_is_the_floor_doubled(floor, expected):
    assert dc.required_seconds(floor) == expected


def test_the_requirement_rounds_up_never_down():
    """A requirement that rounds down is a ceiling set below what was measured,
    which is the entire failure this module exists to stop."""
    assert dc.required_seconds(3, factor=1.5) == 5      # 4.5 -> 5, not 4
    assert dc.required_seconds(7, factor=1.1) == 8      # 7.7 -> 8, not 7


def test_required_minutes_rounds_up_to_a_declarable_line():
    reading = dc.grade()
    assert reading.required_minutes * 60 >= reading.required_seconds
    assert (reading.required_minutes - 1) * 60 < reading.required_seconds
