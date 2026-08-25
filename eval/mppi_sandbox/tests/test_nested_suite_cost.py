"""The `slow` job is not slow — it is waiting, and the wait cannot be won.

Fixtures below are **verbatim** lines from the `slow closed-loop` job of run
30987013397 (2026-08-05, head 70e2863), trimmed to the interesting window.  The
defect is an arithmetic relation between two real numbers, so a hand-invented
log would be assuming exactly what is to be shown — :mod:`ci_verdict`'s rule,
applied to a different record.
"""

from __future__ import annotations

import ast
from pathlib import Path

from eval.mppi_sandbox import nested_suite_cost as nsc

# --------------------------------------------------------------------------
# Live record — the job that was killed at its 120-minute ceiling.
# --------------------------------------------------------------------------

KILLED_JOB_LOG = """
2026-08-05T08:04:49.3460252Z eval/mppi_sandbox/tests/test_epistemic_reach_screen.py::TestTheNominalTimingModelIsFalsified::test_the_controller_does_not_track_target_speed PASSED [ 24%]
2026-08-05T08:26:34.0363275Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_the_exclusion_list_manufactured_exactly_two_candidates FAILED [ 25%]
2026-08-05T08:26:34.0394861Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_the_headline_sites_are_attributed_to_a_measured_file PASSED [ 26%]
2026-08-05T08:26:34.0640509Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_self_entries_are_the_majority_and_are_left_alone FAILED [ 27%]
2026-08-05T08:41:34.1790793Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_the_reconstruction_agrees_with_a_measured_run FAILED [ 28%]
2026-08-05T08:56:34.6182035Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_both_published_rankings_were_taken_over_a_population_with_artifacts ERROR [ 28%]
2026-08-05T09:19:08.1322478Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_the_input_fold_reproduces_a_measured_run_under_the_same_exclusion ERROR [ 29%]
2026-08-05T09:34:08.7630735Z eval/mppi_sandbox/tests/test_exclusion_scope.py::test_two_independent_flat_censuses_move_only_where_addresses_do FAILED [ 31%]
2026-08-05T09:57:20.8161906Z ##[error]The operation was canceled.
"""

#: The negative control: a job doing genuine spread work, no wait anywhere.
#: Same shape, same parser, same red results — only the *gaps* differ.
BUSY_JOB_LOG = """
2026-08-05T08:00:00.0000000Z eval/mppi_sandbox/tests/test_a.py::test_one PASSED [ 10%]
2026-08-05T08:00:12.0000000Z eval/mppi_sandbox/tests/test_a.py::test_two FAILED [ 20%]
2026-08-05T08:00:31.0000000Z eval/mppi_sandbox/tests/test_b.py::test_three PASSED [ 30%]
2026-08-05T08:01:40.0000000Z eval/mppi_sandbox/tests/test_b.py::test_four ERROR [ 40%]
2026-08-05T08:02:05.0000000Z eval/mppi_sandbox/tests/test_c.py::test_five PASSED [ 50%]
"""

#: A job that finished and *printed its summary* — its failures are visible
#: through the ordinary channel, so `unreported` must add nothing.
#: The timeout every finding below was measured under.  D-096 collapsed the
#: seven statements of it into one and raised it to 2792 s (worst observed suite
#: cost x the headroom factor), which makes each of these a claim about a value
#: the tree no longer ships.  Pinned to the epoch rather than blanket-updated:
#: D-094 showed that re-pointing such a test at the new number can leave it
#: passing whichever way the code goes, i.e. discriminating nothing.  Each has a
#: live companion asserting what changed.
D089_TIMEOUT_SECONDS = 900

REPORTED_JOB_LOG = BUSY_JOB_LOG + (
    "2026-08-05T08:02:06.0000000Z ===== 3 passed, 2 failed in 126.00s =====\n")


# --------------------------------------------------------------------------
# The inequality — the thing three ceiling raises never compared.
# --------------------------------------------------------------------------

def test_the_shipped_numbers_make_every_nested_call_impossible():
    """1396 s of suite inside a 900 s timeout is not a budget nit."""
    assert nsc.CI_FAST_HALF_SECONDS > D089_TIMEOUT_SECONDS
    assert nsc.grade(nsc.CI_FAST_HALF_SECONDS, D089_TIMEOUT_SECONDS) == nsc.DOOMED


def test_the_shipped_timeout_now_clears_the_suite():
    """Live companion: the inequality above has been inverted, not deleted.

    Without this, pinning the epoch would quietly convert a fixed defect into a
    museum piece and nothing would notice a regression back to 900 s.
    """
    assert nsc.NESTED_TIMEOUT_SECONDS > nsc.CI_FAST_HALF_SECONDS
    assert nsc.grade() == nsc.AFFORDABLE


def test_grade_separates_doomed_from_merely_tight():
    assert nsc.grade(400, 900) == nsc.AFFORDABLE
    assert nsc.grade(700, 900) == nsc.MARGINAL   # 0.78 — one growth cycle away
    assert nsc.grade(900, 900) == nsc.DOOMED     # equal is already unwinnable
    assert nsc.grade(1396, 900) == nsc.DOOMED


def test_a_ceiling_raise_cannot_reach_the_defect():
    """The refutation of "raise 120 to 240", stated as a property.

    `grade` does not mention the job ceiling at all — which is the point.  No
    value of `timeout-minutes` appears in the inequality, so no value of it can
    change the verdict.
    """
    for ceiling in (60, 120, 240, 480):
        assert nsc.grade(nsc.CI_FAST_HALF_SECONDS,
                         D089_TIMEOUT_SECONDS) == nsc.DOOMED
        # The burn is a fact about the waits, not the ceiling: at the epoch's
        # 900 s it was nonzero for every one of these denominators.
        assert (6 * D089_TIMEOUT_SECONDS) / (ceiling * 60) > 0


def test_the_doomed_sites_are_named_and_are_full_suite_runners():
    named = {("predicate_vacuity", "measure"),
             ("predicate_inputs", "measure"),
             ("guard_vacuity", "measure")}
    runners = {s.key: s for s in nsc.suite_runners()}
    # The three D-089 named are still full-suite runners...
    assert all(k in runners or k == ("guard_vacuity", "measure") for k in named)
    # ...and none of them is doomed any more, because all seven statements of
    # the timeout collapsed into one that clears the suite (D-096).
    assert nsc.doomed_sites() == ()
    assert all(s.timeout == nsc.NESTED_TIMEOUT_SECONDS
               for s in nsc.suite_runners())
    # The epoch claim, still falsifiable: at 900 s they were all doomed.
    assert all(nsc.grade(nsc.CI_FAST_HALF_SECONDS, D089_TIMEOUT_SECONDS)
               == nsc.DOOMED for _ in named)


def test_the_floor_burn_exceeded_a_third_of_the_ceiling_it_was_measured_against():
    """D-089's share, against the 120-min ceiling it was taken under.

    ``budget()`` is a ratio, so raising the denominator moves it without any
    change to the burn: D-094 took the ceiling 120 -> 360 and this reading fell
    to 12.5% while the doomed waits it counts stayed exactly where they were.
    Pinning the epoch keeps the finding a statement about the burn rather than
    an accidental statement about the ceiling.
    """
    epoch_burn = 6 * D089_TIMEOUT_SECONDS      # the six runner classes D-092 counted
    assert epoch_burn / (120 * 60) >= 0.30


def test_the_raised_ceiling_dilutes_the_ratio_without_touching_the_burn():
    """Falsifiable companion: the burn is unchanged, only the denominator moved."""
    epoch_burn = 6 * D089_TIMEOUT_SECONDS
    assert epoch_burn / (120 * 60) > epoch_burn / nsc.SLOW_CEILING_SECONDS
    # Live: the burn this metric counts is now zero — no site is doomed at all,
    # which is a stronger statement than a diluted ratio.
    assert nsc.budget() == 0.0


def test_measure_attributed_is_the_next_one_to_fall():
    """1800 s against a 1396 s suite is MARGINAL, not safe — 78% consumed."""
    # Epoch: at 1800 s it was 78% consumed and one growth cycle from DOOMED.
    assert nsc.grade(nsc.CI_FAST_HALF_SECONDS, 1800) == nsc.MARGINAL
    # Live: it shares the single statement now, so it fell *with* the others
    # rather than after them — and 1800 s never cleared the requirement either.
    runners = {s.key: s for s in nsc.suite_runners()}
    attributed = runners[("predicate_vacuity", "measure_attributed")]
    assert attributed.timeout == nsc.NESTED_TIMEOUT_SECONDS
    assert nsc.grade(nsc.CI_FAST_HALF_SECONDS, attributed.timeout) == nsc.AFFORDABLE


# --------------------------------------------------------------------------
# Subject — the false positive the first draft shipped.
# --------------------------------------------------------------------------

def test_a_scratch_suite_is_not_graded_against_the_full_suite():
    """The bug this scan had, pinned so it cannot come back.

    `_measure_scratch` waits 300 s and runs a two-file synthetic suite.  Graded
    against the 1396 s *full* suite it reads DOOMED, which is a category error:
    that site never runs the work the 1396 was measured on.
    """
    scratch = [s for s in nsc.nested_call_sites() if s.subject == nsc.SCRATCH]
    assert scratch, "expected the scratch-suite runners to still exist"
    assert all(s.key not in {d.key for d in nsc.doomed_sites()} for s in scratch)


def test_an_unresolved_timeout_is_carried_not_cleared():
    """A site the scan could not read must not land in the clean pile."""
    unresolved = {s.key for s in nsc.unresolved_sites()}
    doomed = {s.key for s in nsc.doomed_sites()}
    assert not (unresolved & doomed)
    assert all(s.timeout is None for s in nsc.unresolved_sites())


def test_the_scan_finds_sites_from_source_not_from_a_list(tmp_path):
    """A new module that shells out to the suite joins the count by itself."""
    (tmp_path / "newcomer.py").write_text(
        "import subprocess\n"
        "DEFAULT_SUITE = ('tests/',)\n"
        "def measure(suite=DEFAULT_SUITE, timeout: int = 120):\n"
        "    subprocess.run(['python', '-m', 'pytest', *suite], timeout=timeout)\n",
        encoding="utf-8")
    found = {s.key for s in nsc.nested_call_sites(tmp_path)}
    assert ("newcomer", "measure") in found
    assert ("newcomer", "measure") in {s.key for s in nsc.suite_runners(tmp_path)}


# --------------------------------------------------------------------------
# Log attribution — work vs waiting.
# --------------------------------------------------------------------------

def test_the_killed_job_grades_stall_not_work():
    reading = nsc.read_log(KILLED_JOB_LOG, quantum=D089_TIMEOUT_SECONDS)
    assert reading.verdict == nsc.STALL
    assert reading.stall_share >= 0.40


def test_a_busy_job_is_the_negative_control():
    """Same parser, same red results, no waits — must NOT grade STALL.

    Without this the STALL verdict is unfalsifiable: a grader that says STALL
    for every log it can read has measured nothing.
    """
    reading = nsc.read_log(BUSY_JOB_LOG, quantum=D089_TIMEOUT_SECONDS)
    assert reading.verdict == nsc.WORK
    assert reading.stall_share == 0.0
    assert not [g for g in reading.gaps if g.is_stall]


def test_only_unambiguous_gaps_are_claimed_as_waits():
    """1354 s is a timeout plus work; claiming it as two would inflate."""
    reading = nsc.read_log(KILLED_JOB_LOG, quantum=D089_TIMEOUT_SECONDS)
    by_seconds = {round(g.seconds): g.quanta for g in reading.gaps}
    assert by_seconds[900] == 1
    assert by_seconds[1354] == 0
    assert by_seconds[1305] == 0


def test_a_true_double_wait_is_counted_as_two():
    events = nsc.parse_events(
        "2026-08-05T08:00:00.0000000Z a.py::t1 PASSED [ 1%]\n"
        "2026-08-05T08:30:00.0000000Z a.py::t2 FAILED [ 2%]\n")
    (gap,) = nsc.gaps(events, quantum=D089_TIMEOUT_SECONDS)
    assert gap.seconds == 1800.0
    assert gap.quanta == 2


# --------------------------------------------------------------------------
# The sixth instance of absence-read-as-clean.
# --------------------------------------------------------------------------

def test_the_killed_job_hides_red_results_from_every_other_reader():
    """`gh` says cancelled; the stream had already published six failures."""
    reading = nsc.read_log(KILLED_JOB_LOG, quantum=D089_TIMEOUT_SECONDS)
    assert reading.reported is False
    hidden = nsc.unreported(reading)
    assert len(hidden) == 6
    assert all(e.is_red for e in hidden)
    assert {e.origin for e in hidden} == {
        "eval/mppi_sandbox/tests/test_exclusion_scope.py"}


def test_a_reported_job_hides_nothing():
    """Bite, from the other side: red results a summary already published."""
    reading = nsc.read_log(REPORTED_JOB_LOG, quantum=D089_TIMEOUT_SECONDS)
    assert reading.reported is True
    assert nsc.unreported(reading) == ()
    assert [e for e in reading.events if e.is_red], "control needs red results"


def test_an_unreadable_log_is_unparsed_not_healthy():
    """`exemption_masking`'s UNPOPULATED, one module over.

    An empty event tuple would flow into `unreported` as "no failures" and into
    `stall_share` as 0.0 — both indistinguishable from a healthy job.  So
    emptiness is decided before health.
    """
    reading = nsc.read_log("Set up job\nInstall deps\n##[error]boom\n")
    assert reading.verdict == nsc.UNPARSED
    assert reading.verdict != nsc.WORK
    assert reading.events == ()
    assert nsc.unreported(reading) == ()


def test_the_parser_reads_outcomes_it_must_not_call_red():
    reading = nsc.read_log(
        "2026-08-05T08:00:00.0000000Z a.py::t1 SKIPPED [ 1%]\n"
        "2026-08-05T08:00:01.0000000Z a.py::t2 XFAIL [ 2%]\n")
    assert reading.verdict == nsc.WORK
    assert not [e for e in reading.events if e.is_red]


# --------------------------------------------------------------------------
# Self-consistency — the joke this module must not be.
# --------------------------------------------------------------------------

def test_this_module_spawns_no_subprocess():
    """An instrument that diagnoses nested-suite cost by nesting a suite.

    It would also add itself to the very count it publishes, so the measurement
    would move when the instrument was installed.
    """
    tree = ast.parse(Path(nsc.__file__).read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if nsc._is_pytest_subprocess(n)]
    assert calls == []
    assert ("nested_suite_cost", "measure") not in {
        s.key for s in nsc.nested_call_sites()}


def test_this_modules_own_tests_stay_out_of_the_slow_half():
    """Pure text and AST — nothing here needs the `--slow` marker."""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    marks = [d for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             for d in n.decorator_list
             if "slow" in ast.dump(d)]
    assert marks == []
