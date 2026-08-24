"""The CI authority, read per job.

Every fixture below is a **verbatim** GitHub REST record taken from this repo on
2026-08-05, not a hand-written shape.  That matters: the defect this module
exists for is a disagreement between two real fields, and a fixture invented to
demonstrate it would be assuming what it set out to show.
"""

from __future__ import annotations

import textwrap
from datetime import datetime, timezone

import pytest

from eval.mppi_sandbox import ci_verdict as cv

# --------------------------------------------------------------------------
# Live records — `gh api repos/{owner}/{repo}/actions/runs/<id>[/jobs]`,
# read 2026-08-05T08:00Z on autoresearch/p3-epistemic-shadow-cost-critic.
# --------------------------------------------------------------------------

#: The record that forced this module.  Run says nothing; `fast` already failed.
RUN_PENDING_WITH_FAILED_JOB = {
    "id": 30981826577,
    "status": "in_progress",
    "conclusion": None,
    "head_sha": "70e2863e232b1dda2184acacfcde027bb30d1630",
    "created_at": "2026-08-05T06:34:27Z",
    "updated_at": "2026-08-05T06:34:39Z",
}
JOBS_PENDING_WITH_FAILED_JOB = [
    {
        "name": "pytest (slow closed-loop)",
        "status": "in_progress",
        "conclusion": None,
        "started_at": "2026-08-05T06:34:37Z",
        "completed_at": None,
    },
    {
        "name": "pytest (fast)",
        "status": "completed",
        "conclusion": "failure",
        "started_at": "2026-08-05T06:34:38Z",
        "completed_at": "2026-08-05T06:57:09Z",
    },
]

#: Both jobs killed at their ceilings — the 27-push silent streak (D-084/D-085).
RUN_CANCELLED = {
    "id": 30972659889,
    "status": "completed",
    "conclusion": "cancelled",
    "head_sha": "9fe05a0ca7f17452bc409dad7f075bde337c79a6",
}
JOBS_CANCELLED = [
    {
        "name": "pytest (fast)",
        "status": "completed",
        "conclusion": "cancelled",
        "started_at": "2026-08-05T03:34:46Z",
        "completed_at": "2026-08-05T03:45:02Z",
    },
    {
        "name": "pytest (slow closed-loop)",
        "status": "completed",
        "conclusion": "cancelled",
        "started_at": "2026-08-05T03:34:39Z",
        "completed_at": "2026-08-05T04:34:54Z",
    },
]

#: Nothing has started yet.
RUN_ALL_PENDING = {
    "id": 30987013397,
    "status": "in_progress",
    "conclusion": None,
    "head_sha": "adeca21f29dd6fc2c2e71bbf28a1a0fbe8855ded",
}
JOBS_ALL_PENDING = [
    {
        "name": "pytest (fast)",
        "status": "in_progress",
        "conclusion": None,
        "started_at": "2026-08-05T07:57:13Z",
        "completed_at": None,
    },
    {
        "name": "pytest (slow closed-loop)",
        "status": "in_progress",
        "conclusion": None,
        "started_at": "2026-08-05T07:57:07Z",
        "completed_at": None,
    },
]

#: Caps as declared in the workflow at the time the fixtures were taken
#: (2026-08-05, before D-094 took ``slow`` 120 -> 360).  **Epoch constant — do
#: not track the live workflow.**  Every fixture below is a record of a run that
#: executed under these ceilings, and metering it against today's would be the
#: error ``job_caps``' own docstring warns about.
FIXTURE_CAPS = {"pytest (fast)": 30 * 60.0, "pytest (slow closed-loop)": 120 * 60.0}


# --------------------------------------------------------------------------
# The load-bearing claim
# --------------------------------------------------------------------------


def test_a_failed_job_outranks_a_pending_sibling():
    """The whole module in one assertion, against the record that motivated it.

    GitHub publishes ``conclusion=null``.  Reading that field — which is what
    ``gh run list --json conclusion`` and every prior instrument here does —
    yields "no verdict yet" for a branch whose required fast job had failed 63
    minutes earlier.  The jobs are the authority; the run is a summary that has
    not been written.
    """
    reading = cv.read_run(
        RUN_PENDING_WITH_FAILED_JOB, JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS
    )

    assert reading.verdict == cv.FAIL
    assert not reading.ok
    assert RUN_PENDING_WITH_FAILED_JOB["conclusion"] is None
    assert reading.disagrees_with_run_level
    assert [j.name for j in reading.failed_jobs()] == ["pytest (fast)"]


def test_the_run_level_field_alone_would_have_said_pending():
    """Pin the counterfactual, so the disagreement cannot be argued away later."""
    published = cv._verdict_of(
        RUN_PENDING_WITH_FAILED_JOB["status"], RUN_PENDING_WITH_FAILED_JOB["conclusion"]
    )
    assert published == cv.PENDING

    derived = cv.read_run(
        RUN_PENDING_WITH_FAILED_JOB, JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS
    ).verdict
    assert derived == cv.FAIL
    assert published != derived


def test_pending_is_not_evidence_of_health():
    """A run still in flight is neither green nor red — and must not be `ok`."""
    reading = cv.read_run(RUN_ALL_PENDING, JOBS_ALL_PENDING, FIXTURE_CAPS)
    assert reading.verdict == cv.PENDING
    assert not reading.ok
    assert not reading.disagrees_with_run_level  # run-level agrees here


# --------------------------------------------------------------------------
# UNRUN: cancelled is neither pass nor fail
# --------------------------------------------------------------------------


def test_cancelled_is_unrun_not_fail_and_not_pass():
    reading = cv.read_run(RUN_CANCELLED, JOBS_CANCELLED, FIXTURE_CAPS)
    assert reading.verdict == cv.UNRUN
    assert reading.verdict not in (cv.FAIL, cv.PASS)
    assert not reading.ok
    assert reading.failed_jobs() == ()


@pytest.mark.parametrize("conclusion", sorted(cv._UNRUN_CONCLUSIONS))
def test_every_verdictless_conclusion_maps_to_unrun(conclusion):
    assert cv._verdict_of("completed", conclusion) == cv.UNRUN


def test_unrun_at_the_ceiling_is_distinguished_from_a_human_cancel():
    """D-084's hand-read diagnosis, mechanised.

    ``slow`` ran 60.25 min against a 60-min cap — the ceiling bit.  ``fast`` was
    cancelled at 10.3 min against the *same* 60-min cap, because a sibling died
    and GitHub tore the run down.  Both read ``cancelled``; only one is a signal
    that the cap has become the thing under test.
    """
    caps_at_the_time = {"pytest (fast)": 60 * 60.0, "pytest (slow closed-loop)": 60 * 60.0}
    reading = cv.read_run(RUN_CANCELLED, JOBS_CANCELLED, caps_at_the_time)
    by_name = {j.name: j for j in reading.jobs}

    slow = by_name["pytest (slow closed-loop)"]
    assert slow.duration_s == pytest.approx(60.25 * 60, rel=1e-3)
    assert slow.at_ceiling
    assert slow.headroom < 0  # it overran the declared cap

    fast = by_name["pytest (fast)"]
    assert not fast.at_ceiling
    assert fast.headroom > 0.8

    assert [j.name for j in reading.ceiling_breaches()] == ["pytest (slow closed-loop)"]


def test_the_raised_caps_put_both_of_those_jobs_back_in_headroom():
    """D-085's raise, checked against the same durations rather than asserted."""
    reading = cv.read_run(RUN_CANCELLED, JOBS_CANCELLED, FIXTURE_CAPS)
    assert reading.ceiling_breaches() == ()
    assert all(j.headroom > 0 for j in reading.jobs)


def test_a_verdict_reaching_job_is_metered_against_its_cap():
    """The 22m31s `fast` run of 08-05T06:34Z, under D-084's 30-min cap."""
    (fast,) = [
        j
        for j in cv.read_jobs(JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS)
        if j.name == "pytest (fast)"
    ]
    assert fast.duration_s == pytest.approx(22 * 60 + 31, abs=1)
    assert fast.headroom == pytest.approx(0.25, abs=0.01)
    assert not fast.at_ceiling


# --------------------------------------------------------------------------
# Fail-closed behaviour
# --------------------------------------------------------------------------


def test_a_run_with_no_jobs_is_never_pass():
    reading = cv.read_run(RUN_ALL_PENDING, [], FIXTURE_CAPS)
    assert reading.verdict == cv.NO_JOBS
    assert not reading.ok


@pytest.mark.parametrize(
    "job",
    [
        {"name": "x"},
        {"name": "x", "status": "completed", "conclusion": "action_required"},
        {"name": "x", "status": "nonsense", "conclusion": None},
    ],
)
def test_an_unparseable_job_is_unreadable_and_not_green(job):
    reading = cv.read_run({"id": 1}, [job], {})
    assert reading.verdict == cv.UNREADABLE
    assert not reading.ok


def test_unreadable_outranks_unrun_and_pending_but_not_fail():
    """Precedence is fail-closed at every step, including against itself."""
    assert cv._PRECEDENCE.index(cv.FAIL) < cv._PRECEDENCE.index(cv.UNREADABLE)
    assert cv._PRECEDENCE.index(cv.UNREADABLE) < cv._PRECEDENCE.index(cv.UNRUN)
    assert cv._PRECEDENCE.index(cv.UNRUN) < cv._PRECEDENCE.index(cv.PENDING)
    assert cv._PRECEDENCE[-1] == cv.PASS

    mixed = cv.read_run(
        {"id": 1},
        [
            {"name": "a", "status": "completed", "conclusion": "success"},
            {"name": "b", "status": "completed", "conclusion": "cancelled"},
        ],
        {},
    )
    assert mixed.verdict == cv.UNRUN, "one silent job voids an all-green claim"


def test_all_green_is_the_only_route_to_pass():
    reading = cv.read_run(
        {"id": 1, "status": "completed", "conclusion": "success"},
        [
            {"name": "a", "status": "completed", "conclusion": "success"},
            {"name": "b", "status": "completed", "conclusion": "success"},
        ],
        {},
    )
    assert reading.verdict == cv.PASS
    assert reading.ok
    assert not reading.disagrees_with_run_level


# --------------------------------------------------------------------------
# Caps come from the workflow, not from memory
# --------------------------------------------------------------------------


def test_caps_are_read_from_the_real_workflow_and_cover_both_jobs():
    """If someone renames a job, this goes red rather than silently unmetering it.

    The assertion is over the **names**, not the values.  It used to also pin
    ``caps == FIXTURE_CAPS``, which conflated two different things that happened
    to be equal: the caps in force *now*, and the caps in force when these
    fixtures were captured.  :func:`ci_verdict.job_caps` warns in its own
    docstring that a historical run must be metered against its epoch's caps —
    and this test was the one place breaking that rule.  It only ever passed
    because no ceiling had moved since the fixtures were taken; D-094's
    120 -> 360 raise moved one, and the test went red about a drift that is not
    a drift.  ``FIXTURE_CAPS`` stays frozen at its epoch, where it belongs.
    """
    caps = cv.job_caps()
    assert set(caps) == set(FIXTURE_CAPS), (
        "the workflow's job display names drifted from the ones this module "
        "meters; unmetered jobs get headroom None and stop reporting ceilings"
    )
    assert all(v > 0 for v in caps.values())


def test_an_undeclared_ceiling_is_absent_rather_than_defaulted(tmp_path):
    """No `timeout-minutes` ⇒ no cap ⇒ no headroom — not GitHub's 360-min default.

    Defaulting would manufacture 97% headroom for a job nobody gave a ceiling,
    which reads as reassurance derived from an omission.
    """
    wf = tmp_path / "wf.yml"
    wf.write_text(
        textwrap.dedent(
            """
            name: x
            jobs:
              capped:
                name: has a cap
                timeout-minutes: 5
              uncapped:
                name: has none
            """
        )
    )
    caps = cv.job_caps(wf)
    assert caps == {"has a cap": 300.0}

    (uncapped,) = cv.read_jobs(
        [
            {
                "name": "has none",
                "status": "completed",
                "conclusion": "cancelled",
                "started_at": "2026-08-05T00:00:00Z",
                "completed_at": "2026-08-05T06:00:00Z",
            }
        ],
        caps,
    )
    assert uncapped.headroom is None
    assert not uncapped.at_ceiling  # unmetered, so no ceiling claim either way


def test_a_missing_workflow_yields_no_caps_rather_than_raising(tmp_path):
    assert cv.job_caps(tmp_path / "absent.yml") == {}


# --------------------------------------------------------------------------
# Durations
# --------------------------------------------------------------------------


def test_an_in_flight_job_is_metered_forward_off_elapsed_time():
    """The forward half of the meter, on the live 08-05T06:34Z `slow` job.

    At 08:00Z it had been running 85.4 min against D-085's 120-min cap — 71%
    used, no verdict, and nothing anywhere in this project able to say so.  The
    post-mortem `at_ceiling` cannot speak until it dies.
    """
    now = datetime(2026, 8, 5, 8, 0, 0, tzinfo=timezone.utc)
    (slow,) = [
        j
        for j in cv.read_jobs(JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS, now)
        if j.name == "pytest (slow closed-loop)"
    ]
    assert slow.verdict == cv.PENDING
    assert slow.running
    assert slow.duration_s == pytest.approx(85.4 * 60, rel=1e-3)
    assert slow.headroom == pytest.approx(0.29, abs=0.01)
    assert not slow.approaching_ceiling  # 71% used — real, not yet alarming
    assert not slow.at_ceiling  # and never, while it still lives


def test_a_running_job_near_its_cap_warns_before_it_is_killed():
    """Same job, 33 minutes later: 99% of the cap, still alive, now visible."""
    now = datetime(2026, 8, 5, 8, 33, 0, tzinfo=timezone.utc)
    reading = cv.read_run(
        RUN_PENDING_WITH_FAILED_JOB, JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS, now
    )
    (warned,) = reading.ceiling_warnings()
    assert warned.name == "pytest (slow closed-loop)"
    assert warned.approaching_ceiling
    assert not warned.at_ceiling, "still running — the post-mortem must stay silent"
    assert reading.ceiling_breaches() == ()
    assert "APPROACHING CEILING" in reading.describe()


def test_elapsed_is_flagged_running_so_it_cannot_be_quoted_as_a_runtime():
    """`duration_s` on a live job is a lower bound; `running` is what says so."""
    now = datetime(2026, 8, 5, 8, 0, 0, tzinfo=timezone.utc)
    live = cv.read_jobs(JOBS_ALL_PENDING, FIXTURE_CAPS, now)
    assert all(j.running for j in live)
    assert all("+" in j.describe() for j in live)

    done = cv.read_jobs(JOBS_CANCELLED, FIXTURE_CAPS, now)
    assert not any(j.running for j in done), "completed jobs keep their real runtime"


def test_without_a_clock_the_module_declines_rather_than_inventing_one():
    """No `now` ⇒ no elapsed reading. A duration off the local clock would be a
    measurement of this box, and this package has been burned by exactly that
    class of substitution (D-086)."""
    (slow,) = [
        j
        for j in cv.read_jobs(JOBS_ALL_PENDING, FIXTURE_CAPS)
        if j.name == "pytest (slow closed-loop)"
    ]
    assert slow.duration_s is None
    assert not slow.running
    assert slow.headroom is None


def test_an_unfinished_job_has_no_duration_and_no_ceiling_claim():
    (slow,) = [
        j
        for j in cv.read_jobs(JOBS_ALL_PENDING, FIXTURE_CAPS)
        if j.name == "pytest (slow closed-loop)"
    ]
    assert slow.verdict == cv.PENDING
    assert slow.duration_s is None
    assert slow.headroom is None
    assert not slow.at_ceiling


def test_describe_names_the_disagreement_in_words():
    """The CLI's one job is to make the run/job split legible to a human."""
    text = cv.read_run(
        RUN_PENDING_WITH_FAILED_JOB, JOBS_PENDING_WITH_FAILED_JOB, FIXTURE_CAPS
    ).describe()
    assert "FAIL" in text
    assert "the jobs disagree" in text
    assert "pytest (fast)" in text
