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

        Against ``SUITE_SECONDS`` alone this is false — 03:00's 721 s clears
        717 s.  The true bound is a suite *plus* the rest of a cycle, which is
        what :func:`cycle_wallclock.threshold` states.
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
        """
        text = (
            "=== executor start 2026-08-07T03:00:01+09:00 ===\n"
            "=== executor end 2026-08-07T03:12:02+09:00 rc=0 ===\n"
        )
        runs = cw.parse_log(text)
        assert runs[0].seconds == 721
        assert cw.graded(runs, frozenset(), overhead_seconds=0)[0][1] == "OVERRUN"
        assert cw.graded(runs, frozenset())[0][1] == "PREMATURE"

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
