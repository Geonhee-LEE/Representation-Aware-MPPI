"""Tests for :mod:`eval.mppi_sandbox.cycle_wallclock`.

Every fixture is log *text*.  The real wrapper log lives outside the repo, so a
test that read it would grade whatever this machine last ran — it would pass or
fail for reasons that have nothing to do with the code, and it could be
discharged by someone simply pushing.  D-095 is the precedent.

The 2026-08-07 excerpt below is transcribed from the live incident, so the
central claim (the non-pushing cycles are the short ones) stays pinned to real
observed times rather than to numbers chosen to make the assertion pass.
"""

from __future__ import annotations

import json

import pytest

from eval.mppi_sandbox import cycle_wallclock as cw

# Verbatim start/end stamps from
# ~/.local/share/representation-aware-mppi/logs/executor-2026-08-07.log.
# 00:00, 02:00 and 05:00 pushed; 03:00, 07:00 and 09:00 did not.
LIVE_LOG = """\
=== executor start 2026-08-07T00:00:01+09:00 ===
=== executor end 2026-08-07T00:55:14+09:00 rc=0 ===
=== executor start 2026-08-07T02:00:01+09:00 ===
=== executor end 2026-08-07T02:17:14+09:00 rc=0 ===
=== executor start 2026-08-07T03:00:01+09:00 ===
=== executor end 2026-08-07T03:12:02+09:00 rc=0 ===
=== executor start 2026-08-07T07:00:01+09:00 ===
=== executor end 2026-08-07T07:09:05+09:00 rc=0 ===
=== executor start 2026-08-07T09:00:01+09:00 ===
=== executor end 2026-08-07T09:08:35+09:00 rc=0 ===
"""

LIVE_PUBLISHED = frozenset({"2026-08-07T00", "2026-08-07T02"})
LIVE_STRANDED = frozenset({"2026-08-07T03", "2026-08-07T07", "2026-08-07T09"})


def _rows(text=LIVE_LOG, published=LIVE_PUBLISHED, **kw):
    return cw.graded(cw.parse_log(text), published, **kw)


class TestParse:
    def test_pairs_start_and_end(self):
        runs = cw.parse_log(LIVE_LOG)
        assert len(runs) == 5
        assert runs[0].started == "2026-08-07T00:00:01+09:00"
        assert runs[0].ended == "2026-08-07T00:55:14+09:00"
        assert runs[0].rc == 0

    def test_ignores_interleaved_prose(self):
        """The log holds the whole agent transcript between the markers."""
        noisy = (
            "=== executor start 2026-08-07T09:00:01+09:00 ===\n"
            "Suite is running (~12 min). Waiting for the receipt.\n"
            "=== not a marker ===\n"
            "=== executor end 2026-08-07T09:08:35+09:00 rc=0 ===\n"
        )
        runs = cw.parse_log(noisy)
        assert len(runs) == 1
        assert runs[0].seconds == 514

    def test_trailing_unpaired_start_is_kept(self):
        runs = cw.parse_log(LIVE_LOG + "=== executor start 2026-08-07T11:00:01+09:00 ===\n")
        assert len(runs) == 6
        assert runs[-1].ended == ""
        assert runs[-1].rc is None
        assert runs[-1].seconds is None

    def test_empty_log(self):
        assert cw.parse_log("") == ()

    def test_hour_key_drops_the_cron_offset_second(self):
        """Cron fires at ``HH:00:01``; a journal writes ``HH:00``."""
        assert cw.parse_log(LIVE_LOG)[0].hour == "2026-08-07T00"

    def test_seconds_spans_midnight(self):
        runs = cw.parse_log(
            "=== executor start 2026-08-06T23:50:00+09:00 ===\n"
            "=== executor end 2026-08-07T00:10:00+09:00 rc=0 ===\n"
        )
        assert runs[0].seconds == 1200


class TestGrade:
    def test_live_incident_grades(self):
        assert [g for _, g in _rows()] == [
            "PUBLISHED",
            "PUBLISHED",
            "PREMATURE",
            "PREMATURE",
            "PREMATURE",
        ]

    def test_every_stranded_hour_is_too_short_to_have_run_a_suite(self):
        """The load-bearing measurement, stated directly against the clock.

        Against the 717 s suite of its own era this is false on the suite term
        alone — 03:00's 721 s clears 717 s by four seconds.  The true bound is a
        suite *plus* the rest of a cycle, which is what
        :func:`cycle_wallclock.threshold` states, and it is why this assertion
        is written against ``threshold()`` rather than a price.  (The D-200
        re-price to 1223 s makes the suite term alone sufficient here too, which
        is why the four-second argument is pinned at its era's price in
        :meth:`test_a_bare_suite_boundary_would_misgrade_the_real_0300_run`.)
        """
        for run, g in _rows():
            if run.hour in LIVE_STRANDED:
                assert g == "PREMATURE"
                assert run.seconds < cw.threshold()

    def test_the_published_runs_are_the_long_ones(self):
        """Negative control: exhaustion predicts this table upside down."""
        by_grade: dict[str, list[int]] = {}
        for run, g in _rows():
            by_grade.setdefault(g, []).append(run.seconds)
        assert min(by_grade["PUBLISHED"]) > max(by_grade["PREMATURE"])

    def test_long_nonpushing_run_is_overrun_not_premature(self):
        """The grade that budget exhaustion would actually produce."""
        text = (
            "=== executor start 2026-08-07T05:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T05:50:01+09:00 rc=0 ===\n"
        )
        rows = cw.graded(cw.parse_log(text), frozenset())
        assert [g for _, g in rows] == ["OVERRUN"]

    def test_boundary_is_a_suite_plus_the_cycle_overhead(self):
        """Exactly ``threshold()`` fits; one second less does not."""

        def at(secs):
            end = 1 + secs
            text = (
                "=== executor start 2026-08-07T05:00:01+09:00 ===\n"
                f"=== executor end 2026-08-07T0{5 + end // 3600}:"
                f"{end % 3600 // 60:02d}:{end % 60:02d}+09:00 rc=0 ===\n"
            )
            return cw.graded(cw.parse_log(text), frozenset())[0][1]

        assert at(cw.threshold()) == "OVERRUN"
        assert at(cw.threshold() - 1) == "PREMATURE"

    def test_a_bare_suite_boundary_would_misgrade_the_real_0300_run(self):
        """Why the overhead term exists, pinned to the run that forced it.

        03:00 ran 721 s against a 717 s suite.  Graded against the suite alone
        it clears the bar by four seconds — i.e. it would be credited with a
        full suite *and* a REVIEW, a PLAN, an EXECUTE and a commit in the
        remaining four.  It is known independently to have taken no receipt at
        all: the 05:00 recovery cycle took the one 03:00 never did.

        ``suite_seconds`` is pinned to 717 here rather than tracking
        :data:`cycle_wallclock.SUITE_SECONDS`: this is a claim about a run in
        2026-08-07's suite, and it is only *at that era's price* that the four
        seconds are tight enough to make the point.  After the D-200 re-price
        721 s is far under the suite alone, which would let the test pass while
        demonstrating nothing.
        """
        text = (
            "=== executor start 2026-08-07T03:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T03:12:02+09:00 rc=0 ===\n"
        )
        runs = cw.parse_log(text)
        assert runs[0].seconds == 721
        era = 717
        assert (
            cw.graded(runs, frozenset(), suite_seconds=era, overhead_seconds=0)[0][1]
            == "OVERRUN"
        )
        assert cw.graded(runs, frozenset(), suite_seconds=era)[0][1] == "PREMATURE"

    def test_overhead_is_far_below_the_shortest_real_cycle(self):
        """The bound must not be doing the conclusion's work.

        The shortest run on record (10:00, 236 s) did REVIEW only — no EXECUTE,
        no commit — so any cycle that produced a commit spent strictly more than
        that outside the suite.  Keeping the constant at or under it makes
        ``PREMATURE`` a floor rather than an estimate.
        """
        assert cw.MIN_OVERHEAD_SECONDS <= 240
        assert cw.threshold() == cw.SUITE_SECONDS + cw.MIN_OVERHEAD_SECONDS

    def test_suite_seconds_is_injectable(self):
        """A cheaper suite would move the boundary; the grade must follow it."""
        rows = cw.graded(cw.parse_log(LIVE_LOG), LIVE_PUBLISHED, suite_seconds=60)
        assert [g for _, g in rows] == ["PUBLISHED", "PUBLISHED"] + ["OVERRUN"] * 3

    def test_publication_beats_the_clock(self):
        """A short run that pushed is not a finding."""
        rows = cw.graded(cw.parse_log(LIVE_LOG), frozenset({"2026-08-07T09"}))
        assert rows[-1][1] == "PUBLISHED"


class TestLiveness:
    """The unpaired-start split, which D-110 is the reason to state carefully."""

    def test_trailing_unpaired_start_is_in_flight(self):
        text = LIVE_LOG + "=== executor start 2026-08-07T11:00:01+09:00 ===\n"
        assert cw.graded(cw.parse_log(text), LIVE_PUBLISHED)[-1][1] == "IN_FLIGHT"

    def test_unpaired_start_followed_by_another_start_is_killed(self):
        """``flock -n`` makes this exact: a later start proves the earlier died."""
        text = (
            "=== executor start 2026-08-07T04:00:01+09:00 ===\n"
            "=== executor start 2026-08-07T05:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T05:50:01+09:00 rc=0 ===\n"
        )
        rows = cw.graded(cw.parse_log(text), frozenset({"2026-08-07T05"}))
        assert [g for _, g in rows] == ["KILLED", "PUBLISHED"]

    def test_in_flight_slot_is_positional_only_at_the_end(self):
        """A corpse must not inherit the exemption by being unpaired (D-110)."""
        text = (
            "=== executor start 2026-08-07T04:00:01+09:00 ===\n"
            "=== executor start 2026-08-07T11:00:01+09:00 ===\n"
        )
        assert [g for _, g in cw.graded(cw.parse_log(text), frozenset())] == [
            "KILLED",
            "IN_FLIGHT",
        ]

    def test_unpaired_runs_are_not_counted_as_findings(self):
        """A killed run has no wall clock, so the clock says nothing about it."""
        text = "=== executor start 2026-08-07T04:00:01+09:00 ===\n" + LIVE_LOG
        rows = cw.graded(cw.parse_log(text), LIVE_PUBLISHED)
        assert cw.counts(rows)["KILLED"] == 1
        assert cw.exhaustion_verdict(rows) == "REFUTED"


class TestVerdict:
    def test_live_incident_refutes_exhaustion(self):
        assert cw.exhaustion_verdict(_rows()) == "REFUTED"

    def test_empty_population_is_not_a_refutation(self):
        """``NO_EVIDENCE`` rather than ``REFUTED`` — D-107's dark instrument."""
        rows = cw.graded(cw.parse_log(LIVE_LOG), frozenset(cw.parse_log(LIVE_LOG)[i].hour for i in range(5)))
        assert cw.counts(rows)["PUBLISHED"] == 5
        assert cw.exhaustion_verdict(rows) == "NO_EVIDENCE"

    def test_no_runs_at_all(self):
        assert cw.exhaustion_verdict(()) == "NO_EVIDENCE"

    def test_all_long_supports_exhaustion(self):
        rows = cw.graded(cw.parse_log(LIVE_LOG), LIVE_PUBLISHED, suite_seconds=60)
        assert cw.exhaustion_verdict(rows) == "SUPPORTED"

    def test_both_populations_is_mixed(self):
        text = LIVE_LOG + (
            "=== executor start 2026-08-07T05:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T05:50:01+09:00 rc=0 ===\n"
        )
        rows = cw.graded(cw.parse_log(text), LIVE_PUBLISHED)
        assert cw.exhaustion_verdict(rows) == "MIXED"

    def test_counts_always_carry_every_grade(self):
        """A zero has to be reportable, not absent."""
        assert set(cw.counts(())) == {
            "PUBLISHED",
            "PREMATURE",
            "OVERRUN",
            "NO_JOURNAL",
            "KILLED",
            "IN_FLIGHT",
        }
        assert set(cw.counts(_rows())) == set(cw.counts(()))


class TestNoJournal:
    """A run with nothing to publish is not a run that published."""

    def test_journalless_run_is_not_credited_as_published(self):
        rows = cw.graded(
            cw.parse_log(LIVE_LOG),
            frozenset({"2026-08-07T00"}),
            journal_hours=frozenset({"2026-08-07T00", "2026-08-07T03"}),
        )
        by_hour = {r.hour: g for r, g in rows}
        assert by_hour["2026-08-07T00"] == "PUBLISHED"
        assert by_hour["2026-08-07T03"] == "PREMATURE"
        # 02:00/07:00/09:00 wrote no journal in this fixture.
        assert by_hour["2026-08-07T02"] == "NO_JOURNAL"
        assert by_hour["2026-08-07T09"] == "NO_JOURNAL"

    def test_omitting_journal_hours_assumes_every_run_wrote_one(self):
        """Back-compat default: the parameter widens nothing when unset."""
        assert cw.counts(_rows())["NO_JOURNAL"] == 0

    def test_journalless_runs_do_not_move_the_verdict(self):
        """They are out of scope, so they must not create or mask a finding."""
        base = cw.graded(cw.parse_log(LIVE_LOG), LIVE_PUBLISHED)
        narrowed = cw.graded(
            cw.parse_log(LIVE_LOG),
            LIVE_PUBLISHED,
            journal_hours=frozenset(LIVE_PUBLISHED | LIVE_STRANDED),
        )
        assert cw.exhaustion_verdict(base) == cw.exhaustion_verdict(narrowed)

    def test_a_short_journalless_run_is_not_premature(self):
        """10:00 ran 4 min and produced nothing; that is not a push failure."""
        text = (
            "=== executor start 2026-08-07T10:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T10:03:57+09:00 rc=0 ===\n"
        )
        rows = cw.graded(
            cw.parse_log(text), frozenset(), journal_hours=frozenset()
        )
        assert [g for _, g in rows] == ["NO_JOURNAL"]
        assert cw.exhaustion_verdict(rows) == "NO_EVIDENCE"


class TestReport:
    def test_names_every_run_and_its_grade(self):
        out = cw.report(_rows())
        assert out.count("PREMATURE") == 3 + 1  # 3 rows + the tally line
        for stamp in ("00:00:01", "03:00:01", "09:00:01"):
            assert stamp in out

    def test_states_the_verdict_and_the_conclusion(self):
        out = cw.report(_rows())
        assert "REFUTED" in out
        assert "early exit, not an exhausted budget" in out

    def test_marks_the_premature_rows_individually(self):
        """Per-row, not just in the header — the header is one claim for five."""
        marked = [
            ln for ln in cw.report(_rows()).splitlines() if "receipt impossible" in ln
        ]
        assert len(marked) == 3

    def test_does_not_claim_a_conclusion_it_did_not_reach(self):
        rows = cw.graded(cw.parse_log(LIVE_LOG), LIVE_PUBLISHED, suite_seconds=60)
        out = cw.report(rows, suite_seconds=60)
        assert "SUPPORTED" in out
        assert "early exit, not an exhausted budget" not in out

    def test_empty(self):
        assert "no executor runs" in cw.report(())

    def test_reads_no_repository(self, tmp_path, monkeypatch):
        """The renderer must not depend on cwd, git, or the machine's log."""
        monkeypatch.chdir(tmp_path)
        assert "REFUTED" in cw.report(_rows())


class TestLogPath:
    def test_mirrors_the_wrapper(self):
        assert cw.log_path("2026-08-07").name == "executor-2026-08-07.log"

    def test_log_dir_is_overridable(self, tmp_path):
        assert cw.log_path("2026-08-07", log_dir=tmp_path).parent == tmp_path


class TestMain:
    def test_missing_log_is_not_a_finding(self, tmp_path, capsys):
        assert cw.main(["grade", "2026-01-01", "--log-dir", str(tmp_path)]) == 0
        assert "no log for" in capsys.readouterr().out

    def test_exit_code_is_the_finding(self, tmp_path, capsys, monkeypatch):
        (tmp_path / "executor-2026-08-07.log").write_text(LIVE_LOG)
        from eval.mppi_sandbox import cycle_artifacts

        def _cycles(hours):
            return lambda branch, **kw: tuple(
                cycle_artifacts.Cycle(
                    path=f"journal/x-{h}.md",
                    minute=0,
                    stamp=f"2026-08-07 {h}:00",
                    branch="b",
                    tsv_claim="yes",
                )
                for h in hours
            )

        monkeypatch.setattr(cycle_artifacts, "current_branch", lambda **kw: "b")
        monkeypatch.setattr(
            cycle_artifacts, "cycles", _cycles(("00", "02", "03", "07", "09"))
        )
        monkeypatch.setattr(cycle_artifacts, "stranded", _cycles(("03", "07", "09")))
        assert cw.main(["grade", "2026-08-07", "--log-dir", str(tmp_path)]) == 1
        assert "REFUTED" in capsys.readouterr().out

    def test_journalless_hours_are_not_counted_as_published(self, tmp_path, capsys, monkeypatch):
        """The join defect this module shipped with, pinned at the CLI seam."""
        (tmp_path / "executor-2026-08-07.log").write_text(LIVE_LOG)
        from eval.mppi_sandbox import cycle_artifacts

        monkeypatch.setattr(cycle_artifacts, "current_branch", lambda **kw: "b")
        monkeypatch.setattr(
            cycle_artifacts,
            "cycles",
            lambda branch, **kw: (
                cycle_artifacts.Cycle(
                    path="journal/x-00.md",
                    minute=0,
                    stamp="2026-08-07 00:00",
                    branch="b",
                    tsv_claim="yes",
                ),
            ),
        )
        monkeypatch.setattr(cycle_artifacts, "stranded", lambda branch, **kw: ())
        cw.main(["grade", "2026-08-07", "--log-dir", str(tmp_path)])
        out = capsys.readouterr().out
        assert "PUBLISHED=1" in out
        assert "NO_JOURNAL=4" in out


@pytest.mark.parametrize(
    "grade_name", ["PUBLISHED", "PREMATURE", "OVERRUN", "KILLED", "IN_FLIGHT"]
)
def test_every_documented_grade_is_reachable(grade_name):
    """No grade in the docstring that no input can produce."""
    text = (
        "=== executor start 2026-08-07T04:00:01+09:00 ===\n"  # KILLED
        "=== executor start 2026-08-07T05:00:01+09:00 ===\n"  # OVERRUN
        "=== executor end 2026-08-07T05:50:01+09:00 rc=0 ===\n"
        "=== executor start 2026-08-07T07:00:01+09:00 ===\n"  # PREMATURE
        "=== executor end 2026-08-07T07:09:05+09:00 rc=0 ===\n"
        "=== executor start 2026-08-07T08:00:01+09:00 ===\n"  # PUBLISHED
        "=== executor end 2026-08-07T08:34:55+09:00 rc=0 ===\n"
        "=== executor start 2026-08-07T11:00:01+09:00 ===\n"  # IN_FLIGHT
    )
    rows = cw.graded(cw.parse_log(text), frozenset({"2026-08-07T08"}))
    assert grade_name in {g for _, g in rows}


class TestFindingGrades:
    def test_derived_not_declared(self):
        """The set follows :func:`grade`, so the two cannot drift apart."""
        assert cw.finding_grades() == {"PREMATURE", "OVERRUN"}

    def test_tracks_the_threshold_branch(self, monkeypatch):
        """If ``grade`` stopped producing PREMATURE, the set would say so.

        A module-level ``frozenset({"PREMATURE", "OVERRUN"})`` would keep
        answering the old value forever — that is the failure this spelling
        buys out, and asserting the literal alone would not detect it.
        """
        monkeypatch.setattr(cw, "MIN_OVERHEAD_SECONDS", 0)
        monkeypatch.setattr(cw, "SUITE_SECONDS", 0)
        assert cw.finding_grades() == {"OVERRUN"}


class TestPreceding:
    def test_skips_the_callers_own_in_flight_row(self):
        """REVIEW calls this from inside a run whose start line is logged."""
        text = LIVE_LOG + "=== executor start 2026-08-07T14:00:01+09:00 ===\n"
        rows = _rows(text)
        assert rows[-1][1] == "IN_FLIGHT"
        run, grade = cw.preceding(rows)
        assert run.started == "2026-08-07T09:00:01+09:00"
        assert grade == "PREMATURE"

    def test_none_when_nothing_has_ended(self):
        text = "=== executor start 2026-08-07T14:00:01+09:00 ===\n"
        assert cw.preceding(_rows(text, frozenset())) is None

    def test_a_killed_run_still_counts_as_preceding(self):
        """KILLED is a run that ended, just without an end line.

        Skipping it would walk past a dead predecessor to a healthy one and
        report the healthy grade — the reading would be of the wrong run.
        """
        text = (
            "=== executor start 2026-08-07T05:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T05:50:01+09:00 rc=0 ===\n"
            "=== executor start 2026-08-07T06:00:01+09:00 ===\n"
            "=== executor start 2026-08-07T14:00:01+09:00 ===\n"
        )
        assert cw.preceding(_rows(text, frozenset()))[1] == "KILLED"


class TestActionable:
    def test_scoped_to_the_preceding_run_not_the_day(self):
        """The whole point of the scope, pinned on the real incident.

        2026-08-07 held three PREMATURE runs before 10:00.  A day-scoped check
        stays red for every remaining cycle that day no matter what any of them
        does, which is D-044's muting failure.  Here the 09:00 PREMATURE run is
        followed by a PUBLISHED one, and the reading goes quiet.
        """
        text = LIVE_LOG + (
            "=== executor start 2026-08-07T12:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T12:35:01+09:00 rc=0 ===\n"
        )
        rows = _rows(text, LIVE_PUBLISHED | {"2026-08-07T12"})
        assert {g for _, g in rows} & {"PREMATURE"}  # the day still has findings
        assert cw.actionable(rows) is False

    def test_fires_on_a_bad_predecessor(self):
        assert cw.actionable(_rows()) is True

    def test_quiet_with_no_completed_run(self):
        text = "=== executor start 2026-08-07T14:00:01+09:00 ===\n"
        assert cw.actionable(_rows(text, frozenset())) is False


class TestAdvisory:
    def test_premature_advice_names_the_turn_ending_mechanism(self):
        out = cw.advisory(_rows())
        assert "8m34" in out and "never end a turn waiting" in out

    def test_overrun_advice_is_the_opposite_instruction(self):
        text = (
            "=== executor start 2026-08-07T06:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T06:34:21+09:00 rc=0 ===\n"
        )
        out = cw.advisory(_rows(text, frozenset()))
        assert "Cut scope" in out and "34m20" in out

    def test_reads_no_repository(self):
        """Same property as :func:`report` — takes populations, reads nothing."""
        assert "no completed run" in cw.advisory(())


class TestReviewSubcommand:
    def _wire(self, monkeypatch, published, journals):
        from eval.mppi_sandbox import cycle_artifacts

        def _cycles(hours):
            return lambda branch, **kw: tuple(
                cycle_artifacts.Cycle(
                    path=f"journal/x-{h}.md",
                    minute=0,
                    stamp=f"2026-08-07 {h}:00",
                    branch="b",
                    tsv_claim="yes",
                )
                for h in hours
            )

        monkeypatch.setattr(cycle_artifacts, "current_branch", lambda **kw: "b")
        monkeypatch.setattr(cycle_artifacts, "cycles", _cycles(journals))
        monkeypatch.setattr(
            cycle_artifacts, "stranded", _cycles(set(journals) - set(published))
        )

    def test_advisory_never_gates(self, tmp_path, capsys, monkeypatch):
        """rc=0 even with a PREMATURE predecessor — an advisory, not a gate.

        ``grade`` returns 1 on the same log (pinned below), so this is the
        difference between the two subcommands and not an accident of fixture.
        """
        (tmp_path / "executor-2026-08-07.log").write_text(LIVE_LOG)
        self._wire(monkeypatch, ("00", "02"), ("00", "02", "03", "07", "09"))
        rc = cw.main(["review", "2026-08-07", "--log-dir", str(tmp_path)])
        assert rc == 0
        assert "cannot have taken a receipt" in capsys.readouterr().out
        self._wire(monkeypatch, ("00", "02"), ("00", "02", "03", "07", "09"))
        assert cw.main(["grade", "2026-08-07", "--log-dir", str(tmp_path)]) == 1

    def test_day_defaults_to_kst_not_utc(self, tmp_path, capsys):
        """Between 00:00 and 09:00 KST a UTC default reads yesterday's log."""
        from datetime import datetime

        today = datetime.now(cw._KST).strftime("%Y-%m-%d")
        (tmp_path / f"executor-{today}.log").write_text(
            "=== executor start 2026-08-07T06:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T06:34:21+09:00 rc=0 ===\n"
        )
        assert cw.main(["review", "--log-dir", str(tmp_path)]) == 0
        assert "no log for" not in capsys.readouterr().out

    def test_missing_log_is_still_not_a_finding(self, tmp_path, capsys):
        assert cw.main(["review", "2026-01-01", "--log-dir", str(tmp_path)]) == 0
        assert "no log for" in capsys.readouterr().out


# The 12:00→13:39 bracket and the 13:00 skip line, verbatim from the same log.
# This is the live control Q-105 was opened on: a run that published and cost a
# cycle to do it.  Kept as text so the pin is the incident, not a chosen number.
DISPLACING_LOG = """\
=== executor start 2026-08-07T11:00:01+09:00 ===
=== executor end 2026-08-07T11:39:41+09:00 rc=0 ===
=== executor start 2026-08-07T12:00:01+09:00 ===
[2026-08-07T13:00:01+09:00] executor already running; skipping this tick
=== executor end 2026-08-07T13:39:41+09:00 rc=0 ===
=== executor start 2026-08-07T14:00:01+09:00 ===
=== executor end 2026-08-07T14:22:42+09:00 rc=0 ===
"""


class TestBudgetAxis:
    """Q-105(b): budget compliance is a second axis, not a sub-grade."""

    def test_the_axes_are_independent_on_the_run_that_motivated_them(self):
        """12:00 published *and* blew the budget — one axis cannot say both."""
        runs = cw.parse_log(DISPLACING_LOG)
        twelve = next(r for r in runs if r.hour == "2026-08-07T12")
        assert twelve.seconds == 99 * 60 + 40
        rows = cw.graded(runs, frozenset({"2026-08-07T12"}))
        assert dict(rows)[twelve] == "PUBLISHED"  # unchanged by this cycle
        assert cw.budget_grade(twelve) == "OVER_BUDGET"

    def test_grade_vocabulary_is_untouched(self):
        """(a) was rejected because it would redefine D-113's population."""
        assert cw.finding_grades() == frozenset({"PREMATURE", "OVERRUN"})
        assert "PUBLISHED_OVER_BUDGET" not in cw.counts(_rows())

    def test_over_budget_grades_is_derived_not_declared(self):
        assert cw.over_budget_grades() == frozenset({"OVER_BUDGET"})

    def test_over_budget_grades_tracks_an_inverted_comparison(self):
        """D-115's defect: a 'derivation' insulated from its own constant.

        Perturb the predicate rather than assert its current value — a test
        that asserts ``{"OVER_BUDGET"}`` passes forever no matter what
        ``budget_grade`` does.
        """
        original = cw.budget_grade
        try:
            cw.budget_grade = lambda run, *, budget_seconds=cw.BUDGET_SECONDS: (
                "WITHIN_BUDGET" if (run.seconds or 0) > budget_seconds else "OVER_BUDGET"
            )
            assert cw.over_budget_grades() == frozenset({"WITHIN_BUDGET"})
        finally:
            cw.budget_grade = original

    def test_unfinished_run_is_unknown_not_compliant(self):
        """An empty measurement must not read as a clean one (D-107)."""
        run = cw.Run(started="2026-08-07T15:00:01+09:00", ended="", rc=None)
        assert cw.budget_grade(run) == "UNKNOWN"
        assert cw.budget_grade(run) not in cw.over_budget_grades()

    def test_boundary_is_exclusive(self):
        exact = cw.Run(
            started="2026-01-01T00:00:00", ended="2026-01-01T00:35:00", rc=0
        )
        assert exact.seconds == cw.BUDGET_SECONDS
        assert cw.budget_grade(exact) == "WITHIN_BUDGET"


class TestDisplacement:
    def test_skips_are_attributed_to_the_lock_holder(self):
        runs = cw.parse_log(DISPLACING_LOG)
        skips = cw.parse_skips(DISPLACING_LOG)
        assert skips == ("2026-08-07T13:00:01+09:00",)
        cost = cw.displaced(runs, skips)
        assert cost["2026-08-07T12:00:01+09:00"] == ("2026-08-07T13:00:01+09:00",)
        assert cost["2026-08-07T11:00:01+09:00"] == ()
        assert cost["2026-08-07T14:00:01+09:00"] == ()

    def test_skip_lines_are_not_runs(self):
        """A skipped tick did no work; counting it would inflate the histogram."""
        assert len(cw.parse_log(DISPLACING_LOG)) == 3

    def test_unpaired_run_is_bounded_by_the_next_start(self):
        text = (
            "=== executor start 2026-08-07T12:00:01+09:00 ===\n"
            "[2026-08-07T13:00:01+09:00] executor already running; skipping this tick\n"
            "=== executor start 2026-08-07T14:00:01+09:00 ===\n"
        )
        runs = cw.parse_log(text)
        cost = cw.displaced(runs, cw.parse_skips(text))
        assert cost["2026-08-07T12:00:01+09:00"] == ("2026-08-07T13:00:01+09:00",)
        assert cost["2026-08-07T14:00:01+09:00"] == ()

    def test_no_skips_costs_nothing(self):
        runs = cw.parse_log(LIVE_LOG)
        assert all(v == () for v in cw.displaced(runs, ()).values())


class TestBudgetAdvisory:
    def test_published_but_over_budget_is_no_longer_silent(self):
        """The exact regression Q-105 names: 'PUBLISHED. No budgeting finding.'"""
        runs = cw.parse_log(DISPLACING_LOG)
        rows = cw.graded(runs[:2], frozenset({"2026-08-07T12"}))
        cost = cw.displaced(runs, cw.parse_skips(DISPLACING_LOG))
        text = cw.advisory(rows, cost)
        assert "PUBLISHED" in text
        assert "No budgeting finding" not in text
        assert "99m40" in text and "64m40 over" in text
        assert "1 cycle that never ran" in text and "13:00" in text

    def test_within_budget_published_still_reads_clean(self):
        rows = _rows(published=frozenset({"2026-08-07T09"}))
        text = cw.advisory(rows[-1:])
        assert "No budgeting finding" in text

    def test_clause_attaches_to_premature_runs_too(self):
        """Independent axis: it is not conditioned on the grade being PUBLISHED."""
        run = cw.Run(
            started="2026-08-07T03:00:01+09:00",
            ended="2026-08-07T04:00:01+09:00",
            rc=0,
        )
        assert "over" in cw.budget_clause(run)

    def test_advisory_with_no_cost_map_still_renders(self):
        runs = cw.parse_log(DISPLACING_LOG)
        rows = cw.graded(runs[:2], frozenset({"2026-08-07T12"}))
        text = cw.advisory(rows)
        assert "64m40 over" in text
        assert "never ran" not in text

    def test_review_stays_rc_zero_when_over_budget(self, tmp_path, capsys, monkeypatch):
        """Still an advisory (D-115) — the new axis did not smuggle in a gate."""
        (tmp_path / "executor-2026-08-07.log").write_text(DISPLACING_LOG)
        from eval.mppi_sandbox import cycle_artifacts

        monkeypatch.setattr(cycle_artifacts, "current_branch", lambda: "b")
        assert cw.main(["review", "2026-08-07", "--log-dir", str(tmp_path)]) == 0

    def test_report_carries_the_second_axis(self):
        runs = cw.parse_log(DISPLACING_LOG)
        rows = cw.graded(runs, frozenset({"2026-08-07T12"}))
        cost = cw.displaced(runs, cw.parse_skips(DISPLACING_LOG))
        text = cw.report(rows, cost=cost)
        # 2, not 1: 11:00 ran 39m41, also over.  The first spelling of this
        # assertion said 1 and the instrument corrected it.
        assert "budget axis: OVER_BUDGET=2 of 3; ticks displaced=1" in text


class TestElapsed:
    """The prospective axis: what the *running* cycle can still afford.

    ``grade``/``review`` answer "did the last run publish"; both are about a run
    that has ended.  These read the one run that has not, which is the only
    reading a cycle can still act on.
    """

    # A cycle that started at 20:00 and has not written its end line.
    IN_FLIGHT_LOG = """\
=== executor start 2026-08-10T19:00:01+09:00 ===
=== executor end 2026-08-10T19:49:12+09:00 rc=0 ===
=== executor start 2026-08-10T20:00:01+09:00 ===
"""

    def _now(self, minute: int, second: int = 0):
        from datetime import datetime

        return datetime.fromisoformat(f"2026-08-10T20:{minute:02d}:{second:02d}+09:00")

    def test_unpaired_tail_is_the_run_in_flight(self):
        runs = cw.parse_log(self.IN_FLIGHT_LOG)
        run, secs = cw.in_flight(runs, now=self._now(12, 1))
        assert run.started == "2026-08-10T20:00:01+09:00"
        assert secs == 12 * 60

    def test_paired_tail_means_nothing_is_running(self):
        """Taken outside a cycle the reading is empty, not a finding."""
        runs = cw.parse_log(LIVE_LOG)
        assert cw.in_flight(runs) is None
        assert "no run in flight" in cw.elapsed_reading(None)

    def test_an_earlier_dead_run_is_not_mistaken_for_the_live_one(self):
        """``parse_log`` closes an unpaired start at the next one, so only the
        tail can be in flight — a crashed 19:00 must not supply the clock."""
        log = """\
=== executor start 2026-08-10T19:00:01+09:00 ===
=== executor start 2026-08-10T20:00:01+09:00 ===
"""
        run, secs = cw.in_flight(cw.parse_log(log), now=self._now(5, 1))
        assert run.started == "2026-08-10T20:00:01+09:00"
        assert secs == 5 * 60

    def test_empty_log_has_nothing_in_flight(self):
        assert cw.in_flight(()) is None

    def test_deadline_is_budget_minus_suite_minus_overhead(self):
        # 2100 - 1223 - 240 = 637s = 10m37.  Derived, not typed: a literal here
        # would stop tracking SUITE_SECONDS the next time the suite is repriced.
        # (It was repriced — 717 → 1223, D-200 — and this line is the one that
        # had to move, which is the comment above earning itself.)
        assert cw.suite_deadline() == (
            cw.BUDGET_SECONDS - cw.SUITE_SECONDS - cw.MIN_OVERHEAD_SECONDS
        )
        assert cw.suite_deadline() == 637

    def test_three_rooms_across_the_two_boundaries(self):
        assert cw.budget_room(0) == "SUITE_AFFORDABLE"
        assert cw.budget_room(cw.suite_deadline() - 1) == "SUITE_AFFORDABLE"
        assert cw.budget_room(cw.suite_deadline()) == "SUITE_UNAFFORDABLE"
        assert cw.budget_room(cw.BUDGET_SECONDS - 1) == "SUITE_UNAFFORDABLE"
        assert cw.budget_room(cw.BUDGET_SECONDS) == "OVER_BUDGET"

    def test_boundaries_are_inclusive_at_the_bad_end(self):
        """Exactly *at* the deadline the suite no longer fits — the arithmetic
        leaves zero slack, and rounding that in the cycle's favour is how a
        minute-19 decision becomes a minute-53 push."""
        assert cw.budget_room(cw.suite_deadline()) == "SUITE_UNAFFORDABLE"
        assert cw.budget_room(cw.suite_deadline() - 1) == "SUITE_AFFORDABLE"

    @staticmethod
    def _mmss(seconds: int) -> str:
        """Derived rather than typed — these strings are functions of
        ``SUITE_SECONDS``, and the D-200 re-price moved every one of them."""
        return f"{seconds // 60}m{seconds % 60:02d}"

    def test_affordable_reading_names_the_time_left_to_decide(self):
        text = cw.elapsed_reading((cw.parse_log(self.IN_FLIGHT_LOG)[-1], 600))
        assert "SUITE_AFFORDABLE" in text
        assert "10m00" in text  # elapsed
        # the room left to start a suite
        assert self._mmss(cw.suite_deadline() - 600) in text

    def test_unaffordable_reading_says_cut_scope(self):
        text = cw.elapsed_reading((cw.parse_log(self.IN_FLIGHT_LOG)[-1], 1400))
        assert "SUITE_UNAFFORDABLE" in text
        assert "cut scope now" in text
        # how long the deadline is gone
        assert self._mmss(1400 - cw.suite_deadline()) in text

    def test_over_budget_reading_quotes_the_constitutional_stop(self):
        text = cw.elapsed_reading((cw.parse_log(self.IN_FLIGHT_LOG)[-1], 2700))
        assert "OVER_BUDGET" in text
        assert "10m00 over" in text
        assert "in_progress" in text

    def test_the_19_00_overrun_would_have_been_called_at_minute_19(self):
        """The run this cycle's REVIEW graded: 49m11, 14m11 over.  A reading at
        the deadline would have refused it a suite while the scope was still
        cuttable — which is the whole claim being shipped."""
        assert cw.budget_room(cw.suite_deadline()) == "SUITE_UNAFFORDABLE"
        assert cw.budget_room(49 * 60 + 11) == "OVER_BUDGET"

    def test_elapsed_is_rc_zero_and_reads_no_git(self, tmp_path, capsys, monkeypatch):
        """Advisory like ``review`` (D-115), and cheap: the branch/journal joins
        are never reached, so a cycle can poll it without paying for it."""
        (tmp_path / "executor-2026-08-10.log").write_text(self.IN_FLIGHT_LOG)
        from eval.mppi_sandbox import cycle_artifacts

        def _boom():  # pragma: no cover - asserted not to run
            raise AssertionError("elapsed must not touch git")

        monkeypatch.setattr(cycle_artifacts, "current_branch", _boom)
        rc = cw.main(["elapsed", "2026-08-10", "--log-dir", str(tmp_path)])
        assert rc == 0
        assert "cycle_wallclock — this run" in capsys.readouterr().out

    def test_missing_log_is_not_a_finding(self, tmp_path, capsys):
        rc = cw.main(["elapsed", "2026-08-10", "--log-dir", str(tmp_path)])
        assert rc == 0
        assert "no log for" in capsys.readouterr().out

    def test_grade_and_review_vocabulary_is_untouched(self):
        """The new axis added a verdict set; it must not have edited the old
        one.  D-115 split these two questions deliberately."""
        runs = cw.parse_log(LIVE_LOG)
        rows = cw.graded(runs, frozenset({"2026-08-07T00"}))
        assert {g for _, g in rows} <= {
            "PUBLISHED",
            "PREMATURE",
            "OVERRUN",
            "IN_FLIGHT",
            "KILLED",
            "NO_JOURNAL",
        }


class TestSuitePrice:
    """The suite's price is *read*, not typed.

    ``SUITE_SECONDS`` was 717 s (measured 2026-08-06/07) while the same suite
    ran 1091 s on 2026-08-10 at 2324 tests and 1223 s on 2026-08-11 at 2478.
    The literal was stale in the **permissive** direction: a suite started at
    minute 15 was graded ``SUITE_AFFORDABLE`` against a deadline 6m14 too late.
    Every push already runs this suite, so the quantity is measured every cycle
    — these tests pin that it is the measurement, and not the literal, that
    reaches the deadline.

    Re-priced to 1223 s on 2026-08-11 (D-200).  The tests below pin the
    *direction* as an inequality, so the next growth of the suite cannot
    reintroduce a permissive fallback by leaving this literal behind.
    """

    def _receipt(self, tmp_path, **extra):
        path = tmp_path / "suite-receipt.json"
        path.write_text(json.dumps({"returncode": 0, **extra}))
        return path

    def test_measured_duration_is_preferred(self, tmp_path):
        path = self._receipt(tmp_path, duration_seconds=1091.01)
        assert cw.suite_price(path) == (1091, cw.MEASURED)

    def test_missing_receipt_falls_back_to_the_literal(self, tmp_path):
        secs, source = cw.suite_price(tmp_path / "absent.json")
        assert (secs, source) == (cw.SUITE_SECONDS, cw.FALLBACK)

    @pytest.mark.parametrize(
        "blob",
        [
            '{"returncode": 0}',  # pre-field receipt
            '{"duration_seconds": null}',
            '{"duration_seconds": 0}',
            '{"duration_seconds": -5}',
            '{"duration_seconds": "wat"}',
            "not json at all",
            "[]",
        ],
    )
    def test_every_unreadable_price_falls_back_rather_than_raising(
        self, tmp_path, blob
    ):
        """An advisory (D-115) that raised would make the budget instrument the
        thing that ends the cycle.  Unknown price ⇒ fallback, never an
        exception."""
        path = tmp_path / "suite-receipt.json"
        path.write_text(blob)
        assert cw.suite_price(path) == (cw.SUITE_SECONDS, cw.FALLBACK)

    def test_a_grown_suite_moves_the_deadline_earlier(self):
        """The whole point: the measured price must *tighten* the deadline."""
        stale = cw.suite_deadline(suite_seconds=717)
        measured = cw.suite_deadline(suite_seconds=1091)
        assert measured < stale
        assert stale - measured == 374

    def test_the_15th_minute_flips_verdict_under_the_measured_price(self):
        """The concrete mis-decision this fixes, pinned as a test.

        At minute 15 the 717 s literal says a suite still fits; the 1091 s
        measurement says it does not.  A cycle that believed the literal would
        overrun."""
        at_15 = 15 * 60
        assert cw.budget_room(at_15, suite_seconds=717) == "SUITE_AFFORDABLE"
        assert cw.budget_room(at_15, suite_seconds=1091) == "SUITE_UNAFFORDABLE"

    def test_reading_names_an_unmeasured_price_as_a_fallback(self):
        """A deadline built on the floor must not read as a measurement."""
        run = cw.Run(started="2026-08-10T21:00:01+09:00", ended=None, rc=None)
        line = cw.elapsed_reading(
            (run, 120), suite_seconds=717, price_source=cw.FALLBACK
        )
        assert "unmeasured" in line and "known-late fallback" in line

    def test_the_fallback_is_not_permissive_against_any_observed_suite(self):
        """The re-price's actual content (D-200): *direction*, not value.

        ``SUITE_SECONDS`` is consulted only when the price is unknown, so it is
        the answer to "we cannot price this suite".  On a deadline instrument
        that answer must fail toward refusing a suite.  At 717 s it failed the
        other way, and the module said so in its own docstring while keeping the
        value.  Pinned as an inequality rather than a literal so that re-pricing
        the constant again cannot silently reintroduce the permissive
        direction."""
        assert cw.SUITE_SECONDS >= cw.observed_suite_max()

    @pytest.mark.parametrize("at_minute", [5, 10, 15, 20, 25])
    def test_the_fallback_never_licenses_what_the_measurement_refuses(
        self, at_minute
    ):
        """The property the inequality buys, at every minute of the budget.

        A fallback verdict may be *more* conservative than the measured one; it
        may never be less.  This is the failing direction (D-058) — with
        ``SUITE_SECONDS = 717`` the 15-minute case fails, which is the concrete
        mis-decision the old value shipped."""
        elapsed = at_minute * 60
        measured = cw.budget_room(elapsed, suite_seconds=cw.observed_suite_max())
        fallback = cw.budget_room(elapsed, suite_seconds=cw.SUITE_SECONDS)
        if measured == "SUITE_UNAFFORDABLE":
            assert fallback == "SUITE_UNAFFORDABLE"

    def test_the_old_literal_is_the_counterexample(self):
        """Why the inequality is not vacuous: 717 s violates it, and does so at
        exactly the minute the shipped instrument was consulted."""
        at_15 = 15 * 60
        assert 717 < cw.observed_suite_max()
        assert cw.budget_room(at_15, suite_seconds=717) == "SUITE_AFFORDABLE"
        assert (
            cw.budget_room(at_15, suite_seconds=cw.observed_suite_max())
            == "SUITE_UNAFFORDABLE"
        )

    def test_reading_names_a_measured_price_as_measured(self):
        run = cw.Run(started="2026-08-10T21:00:01+09:00", ended=None, rc=None)
        line = cw.elapsed_reading(
            (run, 120), suite_seconds=1091, price_source=cw.MEASURED
        )
        assert "1091s measured" in line and "unmeasured" not in line

    def test_default_price_is_read_from_disk_not_the_literal(
        self, tmp_path, monkeypatch
    ):
        """``suite_seconds=None`` means *price it yourself*."""
        path = self._receipt(tmp_path, duration_seconds=1200)
        monkeypatch.setattr(cw, "DEFAULT_RECEIPT", path)
        run = cw.Run(started="2026-08-10T21:00:01+09:00", ended=None, rc=None)
        assert "1200s measured" in cw.elapsed_reading((run, 60))
