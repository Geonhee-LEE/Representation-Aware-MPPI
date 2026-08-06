"""A push must be licensed by a green receipt, not by memory (STATE #1).

Fast tests only: throwaway git repos, hand-built receipts, and one real
``pytest`` subprocess over a two-test fixture.  Nothing simulates.

The controls are the point of the file.  D-075 shipped a guard that passed
because its population was empty; D-076 needed a second cycle to separate
"removes nothing" from "is not wired"; D-078 made a control ship in the same
commit as the thing it controls; D-081's first draft of a control read ``0/0``
and proved nothing.  So every verdict here is exercised in **both** directions:
each refusal has an input that reaches it, and :data:`GREEN` has an input that
reaches it too — a gate that always refuses is as useless as one that always
clears, and only the pair shows which this is.

What these tests deliberately do **not** assert: that the real repo is currently
green.  That is the executor's question at one specific moment (before the
push), not a property the suite can hold true while an EXECUTE phase is midway
through editing.  Same reasoning as ``test_tree_provenance``'s note.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import tree_provenance as tp


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=str(cwd), check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A one-commit git repo: one code file, one declared-local-only file."""
    _run("git", "init", "-q", "-b", "main", cwd=tmp_path)
    (tmp_path / "code.py").write_text("VALUE = 1\n")
    (tmp_path / "STATE.md").write_text("snapshot\n")
    _run("git", "add", "-A", cwd=tmp_path)
    _run(
        "git",
        "-c",
        "user.email=t@t",
        "-c",
        "user.name=t",
        "commit",
        "-qm",
        "init",
        cwd=tmp_path,
    )
    return tmp_path


def _receipt_for(repo: Path, **over) -> pp.Receipt:
    """A receipt describing *repo* as it stands right now, green by default."""
    st = tp.stamp(repo)
    fields = dict(
        head=st.head,
        worktree_fingerprint=st.worktree_fingerprint,
        committed_fingerprint=st.committed_fingerprint,
        returncode=0,
        counts={"passed": 7, "skipped": 2},
        command=("python3", "-m", "pytest", "-q"),
    )
    fields.update(over)
    return pp.Receipt(**fields)


def _write(repo: Path, receipt: pp.Receipt, name: str = "receipt.json") -> Path:
    """Write *receipt* under *name*.

    The name is a parameter because the exhaustiveness test needs several
    receipts alive at once, and a single shared path silently overwrites the one
    a later assertion is about — which is how its first draft reported STALE
    unreachable when it is the verdict this module was written for.
    """
    path = repo / name
    path.write_text(receipt.to_json())
    return path


# --- the decision procedure is exhaustive and ordered -----------------------


def test_verdicts_registry_matches_the_constants():
    """Every verdict constant is in VERDICTS, and nothing else is.

    The registry is what the exhaustiveness test below iterates.  If a future
    verdict is added to :func:`check` but not here, that test would silently
    stop covering it — the D-036 shape (a registry policing only what someone
    remembered to type in), applied to this module.
    """
    constants = {
        v
        for name, v in vars(pp).items()
        if name.isupper() and isinstance(v, str) and name == v
    }
    assert constants == set(pp.VERDICTS)


def test_green_is_last_so_every_refusal_precedes_it():
    assert pp.VERDICTS[-1] == pp.GREEN


# --- GREEN: the gate can clear (without this, every refusal below is vacuous) ---


def test_green_when_the_receipt_matches_a_clean_tree(repo: Path):
    path = _write(repo, _receipt_for(repo))
    v = pp.check(path, root=repo)
    assert v.verdict == pp.GREEN, v.describe()
    assert v.ok


def test_green_survives_drift_confined_to_declared_local_only_paths(repo: Path):
    """D-011 *requires* STATE.md to differ from HEAD.  That must not block a push.

    This is the asymmetry D-042 warns about, in this module's terms: a gate that
    fired on the drift the project mandates would be red every cycle and muted
    within a week.
    """
    (repo / "STATE.md").write_text("rewritten this cycle\n")
    path = _write(repo, _receipt_for(repo))
    v = pp.check(path, root=repo, declared={"STATE.md": "D-011"})
    assert v.verdict == pp.GREEN, v.describe()


# --- NO_RECEIPT: the three 2026-08-05 crashes --------------------------------


def test_absent_receipt_refuses_rather_than_clears(repo: Path):
    """The defect this module exists for: nothing was measured, so nothing said no."""
    v = pp.check(repo / "nope.json", root=repo)
    assert v.verdict == pp.NO_RECEIPT
    assert not v.ok


def test_truncated_receipt_is_no_receipt_not_a_crash(repo: Path):
    """A cycle that dies mid-write leaves a partial file; that is still no evidence."""
    path = repo / "receipt.json"
    path.write_text('{"head": "abc", "returnc')
    assert pp.check(path, root=repo).verdict == pp.NO_RECEIPT


def test_receipt_missing_a_required_field_is_no_receipt(repo: Path):
    path = repo / "receipt.json"
    path.write_text(json.dumps({"head": "abc"}))
    assert pp.check(path, root=repo).verdict == pp.NO_RECEIPT


# --- STALE: D-043's defect, at push time -------------------------------------


def test_editing_a_tracked_file_after_the_run_goes_stale(repo: Path):
    path = _write(repo, _receipt_for(repo))
    (repo / "code.py").write_text("VALUE = 2\n")
    v = pp.check(path, root=repo)
    assert v.verdict == pp.STALE, v.describe()


def test_stale_fires_even_when_the_edit_is_a_declared_local_only_file(repo: Path):
    """A receipt is a claim about the worktree, and STATE.md is in the worktree.

    D-043's own instance was a ``docs/`` write, and :func:`tree_provenance.verify`
    is deliberately not exempt there.  The declared set exempts a path from the
    *worktree-vs-HEAD* comparison, not from the *did-the-tree-move-since-the-run*
    one.  Conflating the two would re-open D-043 for exactly the files the
    project rewrites every cycle.
    """
    path = _write(repo, _receipt_for(repo))
    (repo / "STATE.md").write_text("rewritten after the run\n")
    v = pp.check(path, root=repo, declared={"STATE.md": "D-011"})
    assert v.verdict == pp.STALE, v.describe()


def test_a_new_commit_after_the_run_goes_stale(repo: Path):
    """``git commit`` does not move the worktree — but ``git add`` of a new file does."""
    path = _write(repo, _receipt_for(repo))
    (repo / "extra.py").write_text("X = 1\n")
    _run("git", "add", "extra.py", cwd=repo)
    v = pp.check(path, root=repo)
    assert v.verdict == pp.STALE, v.describe()


# --- VACUOUS: 'did not fail' is not 'passed' (D-075/D-076/D-081) -------------


def test_zero_executed_tests_is_vacuous_not_green(repo: Path):
    """pytest exits 5 having collected nothing; rc-only logic would call that fine."""
    path = _write(repo, _receipt_for(repo, returncode=0, counts={}))
    v = pp.check(path, root=repo)
    assert v.verdict == pp.VACUOUS, v.describe()


def test_an_all_skipped_run_is_vacuous(repo: Path):
    """400 collected, 400 skipped, zero assertions executed.

    ``skipped`` is excluded from :data:`EXECUTED_OUTCOMES` for this case alone.
    A gate that counted skips would clear a suite that ran no test body — which
    is D-075's vacuous survival with a larger denominator.
    """
    path = _write(repo, _receipt_for(repo, counts={"skipped": 400}))
    assert pp.check(path, root=repo).verdict == pp.VACUOUS


def test_unparseable_summary_is_vacuous_not_green(repo: Path):
    """An outcome that could not be read is an unknown outcome, and unknown refuses."""
    path = _write(repo, _receipt_for(repo, counts=pp.parse_summary("boom\n")))
    assert pp.check(path, root=repo).verdict == pp.VACUOUS


def test_xfailed_alone_counts_as_executed(repo: Path):
    """The wrong-direction control for the skip rule.

    If :data:`EXECUTED_OUTCOMES` were narrowed to ``passed`` the vacuity check
    would start refusing real runs, so the boundary is pinned from both sides.
    """
    path = _write(repo, _receipt_for(repo, counts={"xfailed": 1}))
    assert pp.check(path, root=repo).verdict == pp.GREEN


# --- RED: the wrong-direction control ----------------------------------------


def test_nonzero_returncode_is_red(repo: Path):
    path = _write(repo, _receipt_for(repo, returncode=1, counts={"passed": 5}))
    v = pp.check(path, root=repo)
    assert v.verdict == pp.RED, v.describe()


def test_failures_are_red_even_if_the_returncode_says_zero(repo: Path):
    """``1f69128``'s shape: the count is what convicts, not the exit status."""
    path = _write(
        repo, _receipt_for(repo, returncode=0, counts={"passed": 843, "failed": 3})
    )
    assert pp.check(path, root=repo).verdict == pp.RED


def test_errors_count_as_failures(repo: Path):
    path = _write(repo, _receipt_for(repo, returncode=0, counts={"passed": 5, "error": 1}))
    assert pp.check(path, root=repo).verdict == pp.RED


# --- UNDECLARED: the measured tree is not the shipped tree -------------------


def test_undeclared_worktree_vs_head_drift_refuses(repo: Path):
    """A green run on a worktree whose code file is not what HEAD ships."""
    (repo / "code.py").write_text("VALUE = 99\n")
    path = _write(repo, _receipt_for(repo))  # receipt stamped *after* the edit
    v = pp.check(path, root=repo, declared={})
    assert v.verdict == pp.UNDECLARED, v.describe()
    assert v.drift is not None and "code.py" in v.drift.paths


def test_declaring_the_path_clears_it(repo: Path):
    """The same tree, one declaration different — so UNDECLARED is about the
    declaration and not about some other property of the edit."""
    (repo / "code.py").write_text("VALUE = 99\n")
    path = _write(repo, _receipt_for(repo))
    assert pp.check(path, root=repo, declared={"code.py": "test"}).verdict == pp.GREEN


# --- ordering is contractual --------------------------------------------------


def test_a_red_stale_receipt_reports_stale_first(repo: Path):
    """Both conditions hold; the earlier verdict is the more useful diagnosis.

    A red-but-stale receipt's failures are facts about a tree that no longer
    exists, so re-running is the action — reporting RED would send the executor
    to debug failures that may not reproduce.
    """
    path = _write(repo, _receipt_for(repo, returncode=1, counts={"failed": 2}))
    (repo / "code.py").write_text("VALUE = 3\n")
    assert pp.check(path, root=repo).verdict == pp.STALE


def test_a_red_run_reports_red_not_undeclared(repo: Path):
    (repo / "code.py").write_text("VALUE = 99\n")
    path = _write(repo, _receipt_for(repo, returncode=1, counts={"failed": 1}))
    assert pp.check(path, root=repo, declared={}).verdict == pp.RED


def test_every_verdict_is_reachable(repo: Path):
    """Exhaustiveness: no verdict in the registry is unreachable dead code.

    D-079's rule — an exemption or branch nobody can reach is not a control —
    applied to the verdict set itself.  Each entry below is produced by one of
    the tests above; this asserts the *set* is covered, so adding a seventh
    verdict without a path to it fails here.
    """
    reached = set()

    reached.add(pp.check(repo / "absent.json", root=repo).verdict)

    good = _write(repo, _receipt_for(repo), "green.json")
    reached.add(pp.check(good, root=repo).verdict)
    reached.add(
        pp.check(_write(repo, _receipt_for(repo, counts={}), "empty.json"), root=repo).verdict
    )
    reached.add(
        pp.check(_write(repo, _receipt_for(repo, returncode=1), "red.json"), root=repo).verdict
    )

    # A green run over a *part* of the suite, whose remainder CI reports failing
    # (D-097).  Needs both halves: the same receipt with no verdict for the
    # uncovered part is GREEN, which is the negative control in
    # test_suite_coverage.
    from eval.mppi_sandbox import ci_verdict as cv

    reached.add(
        pp.check(
            _write(
                repo,
                _receipt_for(repo, counts={"passed": 3, "skipped": 2}),
                "partial.json",
            ),
            root=repo,
            uncovered_verdict=cv.FAIL,
        ).verdict
    )

    # A green, correctly-declared tree shipping a journal that claims a TSV row
    # it never appended (D-108).  Needs a repo with cycles in it, which the
    # `repo` fixture deliberately has none of — see test_push_claim_gate.
    from eval.mppi_sandbox import guard_direction as gd

    cycles_repo = repo / "cycles"
    gd.build_cycle_artifacts_repo(cycles_repo)
    gd._git(cycles_repo, "branch", "-M", gd.CA_BRANCH)
    gd._ca_offend(cycles_repo, gd.CA_PLAIN)
    reached.add(
        pp.check(
            _write(cycles_repo, _receipt_for(cycles_repo), "claim.json"),
            root=cycles_repo,
            declared={},
        ).verdict
    )

    (repo / "code.py").write_text("VALUE = 42\n")
    reached.add(
        pp.check(
            _write(repo, _receipt_for(repo), "shipped.json"), root=repo, declared={}
        ).verdict
    )
    reached.add(pp.check(good, root=repo).verdict)  # the tree moved under it

    assert reached == set(pp.VERDICTS)


# --- parse_summary ------------------------------------------------------------


@pytest.mark.parametrize(
    "line, expect",
    [
        ("846 passed, 153 skipped, 1 xfailed in 42.30s", 847),
        ("843 passed, 3 failed in 40.00s", 846),
        ("5 failed, 2 errors in 1.00s", 7),
        ("no tests ran in 0.01s", 0),
        ("", 0),
    ],
)
def test_parse_summary_executed_counts(line: str, expect: int):
    counts = pp.parse_summary(line)
    assert sum(counts.get(w, 0) for w in pp.EXECUTED_OUTCOMES) == expect


def test_parse_summary_reads_the_last_summary_line(repo: Path):
    """A traceback can contain the word ``failed``; the counts line is the last one."""
    text = "E   assert 3 failed\n1 failed, 2 passed in 0.1s\n"
    assert pp.parse_summary(text) == {"failed": 1, "passed": 2}


# --- record(): the receipt is observed, not typed ----------------------------


def test_record_runs_the_command_and_binds_the_result_to_the_tree(repo: Path):
    """End-to-end over a real pytest subprocess, so the parse and the stamp are
    exercised against actual output rather than a hand-written string."""
    (repo / "test_fixture.py").write_text(
        "def test_a():\n    assert True\n\n\ndef test_b():\n    assert True\n"
    )
    _run("git", "add", "-A", cwd=repo)
    receipt, output = pp.record(
        ("python3", "-m", "pytest", "test_fixture.py", "-q", "-p", "no:cacheprovider"),
        root=repo,
    )
    assert receipt.returncode == 0, output[-500:]
    assert receipt.executed == 2
    assert receipt.worktree_fingerprint == tp.stamp(repo).worktree_fingerprint


def test_record_of_a_failing_suite_produces_a_red_receipt(repo: Path):
    """The wrong-direction control for :func:`record` itself: a real failing run
    must survive the round-trip as RED, or the recorder launders red into green."""
    (repo / "test_fixture.py").write_text("def test_a():\n    assert False\n")
    _run("git", "add", "-A", cwd=repo)
    receipt, _ = pp.record(
        ("python3", "-m", "pytest", "test_fixture.py", "-q", "-p", "no:cacheprovider"),
        root=repo,
    )
    assert receipt.returncode != 0 and receipt.failures == 1
    path = _write(repo, receipt)
    assert pp.check(path, root=repo, declared={}).verdict == pp.RED


def test_receipt_round_trips_through_json(repo: Path):
    receipt = _receipt_for(repo, counts={"passed": 3, "xfailed": 1})
    assert pp.Receipt.from_json(receipt.to_json()) == receipt


def test_record_removes_a_prior_receipt_before_it_runs(tmp_path, monkeypatch):
    """A crash during ``record`` must leave NO_RECEIPT, not yesterday's green.

    The cycle order hands ``record`` a **fixed** ``--out`` path and the run
    takes minutes, so "the recorder died" and "the recorder succeeded" were
    distinguishable only by the file's mtime — which :func:`check` does not
    read.  The three crashes in this module's own docstring are exactly this
    shape, and the gate built to catch them would have cleared the next one off
    a receipt describing the previous tree.
    """
    out = tmp_path / "suite-receipt.json"
    out.write_text(_receipt_json(counts={"passed": 900}))

    def _die(*a, **k):
        raise KeyboardInterrupt("suite killed mid-run")

    monkeypatch.setattr(pp, "record", _die)
    with pytest.raises(KeyboardInterrupt):
        pp._main(["record", "--out", str(out), "--", "-q"])
    assert not out.exists(), "a dead run left a receipt that check() would trust"


def _receipt_json(**over) -> str:
    base = dict(
        head="0" * 40,
        worktree_fingerprint="fp",
        committed_fingerprint="cfp",
        returncode=0,
        counts={"passed": 1},
        command=("python3", "-m", "pytest"),
    )
    base.update(over)
    return pp.Receipt(**base).to_json()
