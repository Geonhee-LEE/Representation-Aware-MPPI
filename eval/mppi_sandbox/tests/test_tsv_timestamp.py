"""The TSV ``timestamp`` column: measure the typed one, refuse the next one.

The load-bearing cases here are the two negative controls and the D-044 split.
Without ``test_the_ordinary_write_then_commit_lag_is_not_a_finding`` the audit
would pass for a module that flags every row it meets; without
``test_a_committed_impossible_row_does_not_make_the_gate_red`` the gate would be
red on 40 unrepairable rows forever, which is the state D-044 says gets muted.
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta

import pytest

from eval.mppi_sandbox import tsv_timestamp as tt


KST = tt.KST


def _repo(root, rows_spec, *, branch="probe"):
    """A git tree whose TSV rows have chosen (stamp, commit-time) pairs.

    ``rows_spec`` is a list of ``(stamp, commit_time)``; ``commit_time=None``
    leaves the row uncommitted, which is the only way to reach the gate's
    population.  Built rather than observed — the live repo's 40 bad rows are
    real and are asserted separately, but an *invariant* must not be hostage to
    a population any cycle can append to.
    """
    root.mkdir(parents=True, exist_ok=True)

    def git(*args, when=None):
        env = dict(os.environ)
        if when is not None:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
        subprocess.run(("git", *args), cwd=str(root), check=True,
                       capture_output=True, env=env)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "probe@local")
    git("config", "user.name", "probe")
    path = root / "results" / f"{branch}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\t".join(tt.HEADER) + "\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "header", when="2026-08-01T00:00:00+09:00")

    for i, (stamp, commit_at) in enumerate(rows_spec):
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp.isoformat()}\tdeadbee\tsandbox:pass=1/1\tkeep\trow {i}\n")
        if commit_at is not None:
            git("add", "-A")
            git("commit", "-qm", f"row {i}", when=commit_at.isoformat())
    return root


def _at(day, hour, minute, second=0):
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


# --- the audit: what a typed column looks like -----------------------------


def test_a_stamp_after_its_own_commit_is_impossible(tmp_path):
    """The deduction the whole module rests on.

    The row is written and *then* committed, so a stamp later than the commit
    that introduced the line is a clock reading taken after the commit that
    contains it.  No threshold, no tolerance — the direction is the finding.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 30), _at(2, 12, 0))])
    a = tt.audit(root)
    assert a.verdict == "TYPED"
    assert len(a.impossible) == 1
    assert a.worst_overshoot_min == pytest.approx(30.0)


def test_the_ordinary_write_then_commit_lag_is_not_a_finding(tmp_path):
    """Negative control — without it the audit passes for a flag-everything module.

    A row stamped a minute before its commit is the *normal* case, and it is
    what 143 of the live repo's 183 rows look like.  A test suite containing
    only the impossible case cannot tell a broken column from a broken blame
    key, because both would produce findings everywhere.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 0), _at(2, 12, 1))])
    a = tt.audit(root)
    assert a.verdict == "CLOCK_READ"
    assert a.impossible == ()
    assert a.honest_lag_min == pytest.approx((1.0,))


def test_no_row_is_named_rather_than_grading_clean(tmp_path):
    """Vacuity: an empty population reads identically to a clean one everywhere else.

    ``dated`` is empty, ``impossible`` is empty and ``worst_overshoot_min`` is
    ``None`` under both "the column is fine" and "there was no column".  Only
    the verdict distinguishes them — the D-107 shape, and the reason it gets its
    own constant instead of falling through to ``CLOCK_READ``.
    """
    root = _repo(tmp_path / "r", [])
    a = tt.audit(root)
    assert a.verdict == "NO_ROW"
    assert (a.dated, a.impossible, a.worst_overshoot_min) == ((), (), None)


def test_the_round_second_signature_is_reported_and_never_graded(tmp_path):
    """A verdict keyed on roundness would fail this; the shipped one does not.

    Three rows, all on ``seconds == 00`` — the typed signature, 60× over
    chance — and all stamped before their commits.  The corroborating evidence
    is *published* (``round_seconds`` is full) and the verdict stays
    ``CLOCK_READ``, because grading on it needs a cutoff between "suspiciously
    round" and "round" that nobody can defend.  ``scorable_band.one_run_rungs``
    discipline: reported, never thresholded.
    """
    root = _repo(tmp_path / "r", [
        (_at(2, 10, 0), _at(2, 10, 1)),
        (_at(2, 11, 0), _at(2, 11, 1)),
        (_at(2, 12, 0), _at(2, 12, 1)),
    ])
    a = tt.audit(root)
    assert len(a.round_seconds) == 3
    assert a.expected_round_seconds == pytest.approx(3 / 60)
    assert a.verdict == "CLOCK_READ"
    assert a.corroborated == ()


def test_an_uncommitted_row_is_undated_not_impossible(tmp_path):
    """The audit's denominator excludes what git cannot date.

    Counting an uncommitted row as impossible would make every cycle's own
    fresh row a finding — the audit would convict the one row that has not had
    a chance to be wrong yet.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 0), None)])
    a = tt.audit(root)
    assert (len(a.undated), a.dated, a.verdict) == (1, (), "CLOCK_READ")


def test_the_epoch_separates_a_regression_from_the_frozen_legacy(tmp_path):
    """The verdict is ``TYPED`` forever; this is the field that can still move.

    Two impossible rows, one committed before the epoch and one after.  The
    verdict cannot distinguish them — it reads ``TYPED`` for the legacy row
    alone — so without the split, "did this cycle add a 41st?" is unanswerable
    from the audit, and a reading nobody can act on is one nobody re-reads.
    """
    before = tt.EPOCH - timedelta(days=1)
    after = tt.EPOCH + timedelta(days=1)
    root = _repo(tmp_path / "r", [
        (before + timedelta(minutes=30), before),
        (after + timedelta(minutes=30), after),
    ])
    a = tt.audit(root)
    assert len(a.impossible) == 2
    assert len(a.legacy_impossible) == 1
    assert len(a.post_epoch_impossible) == 1


def test_a_clean_post_epoch_row_leaves_the_regression_set_empty(tmp_path):
    """Negative control for the epoch split — otherwise it just counts recency.

    A *good* row committed after the epoch must not appear as a regression; a
    version that partitioned on date alone would report one here.
    """
    after = tt.EPOCH + timedelta(days=1)
    root = _repo(tmp_path / "r", [(after, after + timedelta(minutes=1))])
    a = tt.audit(root)
    assert (a.post_epoch_impossible, a.verdict) == ((), "CLOCK_READ")


# --- the gate: D-044's split by reparability -------------------------------


def test_a_committed_impossible_row_does_not_make_the_gate_red(tmp_path):
    """D-044, and the reason the audit and the gate are two functions.

    The live repo holds 40 impossible rows and the soft limits make
    ``results/*.tsv`` append-only ("Never edit past rows"), so they cannot be
    repaired — rewriting them would also destroy the blame key that convicts
    them.  A gate over them is red on every cycle forever, and a check nobody
    can clear is a check that gets muted.  So the gate sees only rows that are
    still editable.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 30), _at(2, 12, 0))])
    assert tt.audit(root).verdict == "TYPED"
    assert tt.check(root, now=_at(3, 0, 0)).verdict == "NO_PENDING_ROW"


def test_a_future_stamped_new_row_is_refused(tmp_path):
    """The measured mechanism, caught at the one moment it is still fixable.

    Start hour plus an estimate that runs ~3× long lands *ahead* of the real
    clock.  Here the row claims 12:30 while it is 12:00.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 30), None)])
    c = tt.check(root, now=_at(2, 12, 0))
    assert c.verdict == "STAMP_AHEAD"
    assert len(c.future) == 1


def test_a_clock_read_new_row_passes(tmp_path):
    """Negative control for the gate: zero false positives on an honest read.

    This is what lets the gate fail closed.  A refusal that fires on correct
    rows becomes the one everybody routes around.
    """
    root = _repo(tmp_path / "r", [(_at(2, 12, 0), None)])
    c = tt.check(root, now=_at(2, 12, 1))
    assert (c.verdict, c.future) == ("STAMP_READ", ())


def test_no_pending_row_is_distinguished_from_a_good_pending_row(tmp_path):
    """Vacuity for the gate: appending nothing is not the same as appending well.

    Both read ``future == ()``.  The constitution requires a row per cycle, so
    the difference is exactly whether that step was discharged.
    """
    empty = tt.check(_repo(tmp_path / "a", []), now=_at(2, 12, 0))
    good = tt.check(_repo(tmp_path / "b", [(_at(2, 12, 0), None)]), now=_at(2, 12, 1))
    assert (empty.verdict, good.verdict) == ("NO_PENDING_ROW", "STAMP_READ")
    assert empty.future == good.future == ()


# --- the writer: stop typing the field -------------------------------------


def test_row_reads_the_clock_rather_than_taking_an_estimate():
    """The half :mod:`cycle_artifacts` skipped: detection is worse than not typing.

    ``now`` is injectable so the format is pinnable, and defaults to the real
    clock so a caller cannot pass an estimate without saying so.
    """
    line = tt.row("9d2ef1a", "sandbox:pass=1/1", "keep", "probe", now=_at(2, 12, 34, 56))
    assert line.split("\t") == [
        "2026-08-02T12:34:56+09:00", "9d2ef1a", "sandbox:pass=1/1", "keep", "probe"]


def test_the_default_clock_is_the_real_one():
    """No ``now`` supplied ⇒ the stamp is a reading, and it is not round.

    Pinned because the whole point of the writer is that the field stops being
    an argument the caller supplies.
    """
    before = datetime.now(tz=KST) - timedelta(seconds=1)
    stamp = datetime.fromisoformat(tt.row("abc", "m", "keep", "d").split("\t")[0])
    assert before <= stamp <= datetime.now(tz=KST) + timedelta(seconds=1)


def test_an_unknown_status_is_refused():
    """The constitution's four-value domain, enforced where the row is built."""
    with pytest.raises(ValueError, match="unknown status"):
        tt.row("abc", "m", "done", "d")


def test_a_tab_in_the_description_cannot_forge_a_column():
    """A description is free text; a TSV row is positional.

    Left unhandled this is a silent field-shift — the audit would then read a
    description fragment as the ``commit`` column.
    """
    line = tt.row("abc", "m", "keep", "a\tb", now=_at(2, 12, 0))
    assert len(line.split("\t")) == len(tt.HEADER)


def test_append_writes_the_header_only_on_a_new_file(tmp_path):
    """Two appends, one header — and the second row is a row, not a second header."""
    root = tmp_path / "r"
    (root / "results").mkdir(parents=True)
    tt.append("autoresearch/p3-probe", "a1", "m", "keep", "first", root=root,
              now=_at(2, 12, 0))
    path = tt.append("autoresearch/p3-probe", "a2", "m", "keep", "second", root=root,
                     now=_at(2, 13, 0))
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0].split("\t") == list(tt.HEADER)
    assert len(lines) == 3
    assert path.name == "p3-probe.tsv"


def test_an_appended_row_is_one_the_gate_accepts(tmp_path):
    """End to end: the writer's output passes the checker it ships with.

    A writer and a gate that disagreed about the format would leave every cycle
    choosing which one to believe.
    """
    root = _repo(tmp_path / "r", [])
    tt.append("probe", "a1", "sandbox:pass=1/1", "keep", "written", root=root,
              now=_at(2, 12, 0))
    assert tt.check(root, now=_at(2, 12, 1)).verdict == "STAMP_READ"


# --- the live population ---------------------------------------------------


def test_both_classes_are_reachable_over_the_real_tsv_corpus():
    """Non-vacuity over shipped data: neither branch of the audit is dead code.

    Scoped to *both classes are non-empty* rather than to the counts (40 and
    143 at the time of writing), so appending rows cannot turn it red.  The
    impossible class cannot empty out either: the rows are append-only, so the
    finding is not discharge-able the way a live-repo assertion usually is.
    """
    a = tt.audit()
    assert a.verdict == "TYPED"
    assert len(a.impossible) >= 1
    assert len(a.honest_lag_min) >= 1
