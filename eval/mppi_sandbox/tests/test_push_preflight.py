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
from eval.mppi_sandbox.declared_suite import DECLARED_SUITE


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
        command=("python3", "-m", "pytest", *DECLARED_SUITE, "-q"),
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
    # The probe's outcomes have the same `name == value` shape but are not push
    # verdicts (see PROBE_OUTCOMES).  Subtracting a *registry* rather than
    # loosening the predicate is deliberate: an unregistered probe outcome still
    # lands in `constants` and still fails here, so neither set can grow in
    # silence.
    assert constants - set(pp.PROBE_OUTCOMES) == set(pp.VERDICTS)
    assert not set(pp.PROBE_OUTCOMES) & set(pp.VERDICTS)


def test_probe_outcomes_registry_is_exhaustive():
    """Every outcome `probe` can return is registered.

    The negative control for the subtraction above: without this, a new probe
    outcome could be added to PROBE_OUTCOMES to silence the verdict test while
    never being returned, or returned while never being registered.
    """
    import inspect

    src = inspect.getsource(pp.probe)
    returned = {v for v in pp.PROBE_OUTCOMES if v in src}
    assert returned == set(pp.PROBE_OUTCOMES)


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

    # A green run whose invocation never *named* part of the declared suite
    # (D-404).  Distinct from the partial receipt above: that one collected the
    # tests and skipped them, this one never pointed pytest at them, so they
    # appear in no count and `suite_coverage` reads it as clean.
    reached.add(
        pp.check(
            _write(
                repo,
                _receipt_for(repo, command=("python3", "-m", "pytest", "-q")),
                "scoped.json",
            ),
            root=repo,
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
        command=("python3", "-m", "pytest", *DECLARED_SUITE),
    )
    base.update(over)
    return pp.Receipt(**base).to_json()


# --- parse_failures: which tests failed, not just how many --------------------
#
# The count and the node ids are read from one run's output, so the pair cannot
# disagree.  What these tests police is the direction of the dependency: the
# verdict must stay a function of the *count*, so that a parser that misses
# every node id still refuses a red suite.  The reverse — grading on the node
# list — would make a regex miss look green, and that is the one outcome this
# module exists to make unreachable.

_RED_OUTPUT = """\
eval/mppi_sandbox/tests/test_census_narrowing.py .....F...            [ 33%]
eval/mppi_sandbox/tests/test_inert_surface.py ......                  [ 99%]
=================================== FAILURES ===================================
_____________________ test_pool_pin _____________________
E   AssertionError: assert 92 == 91
=========================== short test summary info ============================
FAILED eval/mppi_sandbox/tests/test_census_narrowing.py::test_pool_pin - Asser...
ERROR eval/mppi_sandbox/tests/test_guard_direction.py::test_probe_registered
1 failed, 1 error, 1439 passed, 156 skipped, 1 xfailed in 756.02s
"""


def test_parse_failures_names_both_failed_and_error_nodes():
    assert pp.parse_failures(_RED_OUTPUT) == (
        "eval/mppi_sandbox/tests/test_census_narrowing.py::test_pool_pin",
        "eval/mppi_sandbox/tests/test_guard_direction.py::test_probe_registered",
    )


def test_parse_failures_ignores_the_word_failed_inside_a_traceback():
    """The negative control, and it is the reason the regex is anchored.

    A traceback quotes assertion text verbatim, and a suite that tests a *gate*
    has failure strings containing the word FAILED all over it.  Only the short
    summary block puts it in column zero followed by a node id.
    """
    noisy = (
        "E   AssertionError: expected FAILED tests/test_x.py::test_y in detail\n"
        "    assert 'FAILED nowhere.py::nope' in message\n"
        "=========================== short test summary info ====================\n"
        "FAILED tests/test_real.py::test_thing - AssertionError\n"
        "1 failed, 3 passed in 1.00s\n"
    )
    assert pp.parse_failures(noisy) == ("tests/test_real.py::test_thing",)


def test_parse_failures_is_empty_on_a_green_run():
    green = "eval/mppi_sandbox/tests/test_x.py ....\n1440 passed in 756.02s\n"
    assert pp.parse_failures(green) == ()
    # ...and empty is *not* how the verdict is reached — see the pair below.


def test_parse_failures_deduplicates_and_keeps_first_seen_order():
    """pytest reruns (``-p rerunfailures``, ``--lf`` chains) can list a node
    twice; a diagnostic that says the same test twice reads as two bills."""
    dupes = (
        "FAILED a.py::t1 - boom\n"
        "FAILED b.py::t2 - boom\n"
        "FAILED a.py::t1 - boom\n"
    )
    assert pp.parse_failures(dupes) == ("a.py::t1", "b.py::t2")


def test_node_ids_do_not_decide_the_verdict(repo: Path):
    """The load-bearing control: grading stays on the count.

    A receipt with an unparseable summary block — no node ids at all — and a
    non-zero return code must still be :data:`RED`.  If this ever goes green,
    the regex above has become a way to launder a red suite.
    """
    path = _write(repo, _receipt_for(repo, returncode=1, counts={"passed": 5}))
    v = pp.check(path, root=repo)
    assert v.verdict == pp.RED
    assert "failing:" not in v.detail, "named nothing, so it must claim nothing"


def test_node_ids_alone_cannot_turn_a_green_run_red(repo: Path):
    """The mirror control.  ``failed_nodes`` is diagnostic; a green count with a
    stray node id is still a licensed push, because the count is the evidence."""
    path = _write(
        repo,
        _receipt_for(repo, returncode=0, counts={"passed": 9}),
    )
    receipt = pp.Receipt.from_json(path.read_text())
    path.write_text(
        json.dumps({**json.loads(receipt.to_json()), "failed_nodes": ["a.py::t1"]})
    )
    assert pp.check(path, root=repo).verdict == pp.GREEN


def test_a_red_refusal_names_the_failing_tests(repo: Path):
    """What the whole change is for: one run locates the failure.

    On 2026-08-07 15:00 the suite went red at one census pin, the receipt gave
    the count alone, and three further ~750 s runs were spent narrowing to the
    node id that the first run had already printed.
    """
    path = _write(repo, _receipt_for(repo, returncode=1, counts={"failed": 1, "passed": 9}))
    receipt = pp.Receipt.from_json(path.read_text())
    path.write_text(
        json.dumps(
            {
                **json.loads(receipt.to_json()),
                "failed_nodes": ["tests/test_census_narrowing.py::test_pool_pin"],
            }
        )
    )
    v = pp.check(path, root=repo)
    assert v.verdict == pp.RED
    assert "tests/test_census_narrowing.py::test_pool_pin" in v.detail


def test_many_failures_are_truncated_with_a_count_of_the_rest():
    nodes = tuple(f"t.py::test_{i}" for i in range(pp.NAMED_FAILURE_LIMIT + 5))
    rendered = pp._name_failures(nodes)
    assert rendered.count("::") == pp.NAMED_FAILURE_LIMIT
    assert "(+5 more)" in rendered


def test_a_receipt_written_before_this_field_existed_still_loads(repo: Path):
    """Backward compatibility, and it matters because the field was added while
    a receipt from the previous cycle may still be on disk at the fixed
    ``--out`` path.  An older receipt must degrade to "named nothing", not to a
    crash that :func:`load` would swallow into ``NO_RECEIPT``."""
    blob = json.loads(_receipt_json(counts={"passed": 3}))
    del blob["failed_nodes"]
    assert pp.Receipt.from_json(json.dumps(blob)).failed_nodes == ()


def test_record_captures_node_ids_from_a_real_pytest_run(tmp_path: Path):
    """End-to-end over a real subprocess: the format is pytest's, not mine.

    Every assertion above reads a hand-written fixture, so all of them would
    survive pytest changing its summary format.  This one would not, which is
    the point — it is the only test here that can tell me the regex still
    matches the tool.
    """
    (tmp_path / "test_fixture.py").write_text(
        "def test_ok():\n    assert True\n\n\ndef test_bad():\n    assert 1 == 2\n"
    )
    _run("git", "init", "-q", "-b", "main", cwd=tmp_path)
    _run("git", "add", "-A", cwd=tmp_path)
    _run(
        "git", "-c", "user.email=t@t", "-c", "user.name=t",
        "commit", "-q", "-m", "fixture", cwd=tmp_path,
    )
    receipt, output = pp.record(
        ("python3", "-m", "pytest", "test_fixture.py", "-q", "-p", "no:cacheprovider"),
        root=tmp_path,
    )
    assert receipt.returncode != 0
    assert receipt.failures == 1
    assert receipt.failed_nodes == ("test_fixture.py::test_bad",), output[-800:]


# --------------------------------------------------------------------------
# the kept run log (D-176)
# --------------------------------------------------------------------------


def test_log_path_defaults_beside_the_receipt():
    """Derived from ``--out``, so no cycle has to remember a flag.

    D-162's scar is a guard that must be placed by hand; the cycle that forgets
    is the one under time pressure, which is the same cycle whose suite run is
    the expensive one.  A default cannot be forgotten.
    """
    assert pp.log_path(Path("/tmp/suite-receipt.json")) == Path(
        "/tmp/suite-receipt.json.log"
    )


def test_log_path_is_keyed_to_the_receipt_not_fixed():
    """Two receipts in one cycle must not share one log.

    A fixed path would let a second ``record`` silently overwrite the first
    run's output while both receipts survived — a log that describes a
    different run than the receipt beside it is worse than no log.
    """
    assert pp.log_path(Path("/tmp/a.json")) != pp.log_path(Path("/tmp/b.json"))


def test_explicit_log_overrides_the_default():
    assert pp.log_path(Path("/tmp/r.json"), Path("/tmp/elsewhere.log")) == Path(
        "/tmp/elsewhere.log"
    )


def test_record_cli_keeps_the_full_output_not_just_the_counts(tmp_path, monkeypatch):
    """The regression this exists for.

    2026-08-10 14:00 ran its one affordable suite with ``--durations=0`` so the
    subset pricing would be free, and ``record`` kept only ``counts`` and
    ``failed_nodes``.  ``receipt_cost.price()`` returned ``NO_DURATIONS``: the
    durations were printed, parsed past, and dropped.  At one affordable run per
    cycle, discarding the output means the next question costs a whole cycle.
    """
    out = tmp_path / "receipt.json"
    fake = (
        "0.50s call     eval/mppi_sandbox/tests/test_x.py::test_y\n"
        "==== 1 passed in 1.00s ====\n"
    )

    def fake_record(command, root=None, timeout=1800):
        st_receipt = pp.Receipt(
            head="deadbeef",
            worktree_fingerprint="wf",
            committed_fingerprint="cf",
            returncode=0,
            counts={"passed": 1},
            command=command,
        )
        return st_receipt, fake

    monkeypatch.setattr(pp, "record", fake_record)
    assert pp._main(["record", "--out", str(out), "--", "-q", "--durations=0"]) == 0

    log = pp.log_path(out)
    assert log.exists()
    assert log.read_text() == fake
    # ...and the whole point: that log can now be priced.
    from eval.mppi_sandbox import receipt_cost as rcost

    assert rcost.price(log.read_text(), ()).verdict != rcost.NO_DURATIONS


def test_record_cli_clears_a_stale_log_the_way_it_clears_a_stale_receipt(
    tmp_path, monkeypatch
):
    """A previous run's log beside a fresh receipt would price the wrong run.

    Same argument the CLI already makes for ``--out``: ``record`` takes minutes
    and the failure mode is a cycle dying *during* it.
    """
    out = tmp_path / "receipt.json"
    log = pp.log_path(out)
    log.write_text("0.50s call     stale/test_old.py::test_old\n==== 1 passed in 1.00s ====\n")

    def dying_record(command, root=None, timeout=1800):
        raise RuntimeError("cycle died mid-suite")

    monkeypatch.setattr(pp, "record", dying_record)
    with pytest.raises(RuntimeError):
        pp._main(["record", "--out", str(out), "--", "-q"])
    assert not log.exists(), "the corpse of the previous run must not survive"


class TestReceiptDuration:
    """``record`` measures what the suite cost, so nobody has to type it.

    The price of a suite run is the one number the budget instrument
    (:mod:`cycle_wallclock`) needs, and until now it was the only one being
    hand-maintained: a literal measured on 2026-08-06/07 that read 374 s low by
    2026-08-10.  Every push runs this suite, so the measurement is free.
    """

    def test_record_measures_the_run(self):
        """Runs against the real repo root because :func:`record` stamps the
        tree, and ``tree_provenance.stamp`` needs a git worktree.  The command
        is a trivial print, so the assertion is about the timing wrapper and not
        about any suite."""
        r, _ = pp.record(("python3", "-c", "print('1 passed')"))
        assert r.duration_seconds is not None
        assert r.duration_seconds >= 0.0
        assert r.counts.get("passed") == 1

    def test_duration_round_trips_through_json(self):
        r = pp.Receipt(
            head="h",
            worktree_fingerprint="w",
            committed_fingerprint="c",
            returncode=0,
            counts={"passed": 1},
            duration_seconds=1091.01,
        )
        assert pp.Receipt.from_json(r.to_json()).duration_seconds == 1091.01

    def test_pre_field_receipts_still_load_with_no_duration(self):
        """Receipts written before this field must keep loading — the field is
        additive, and an old receipt simply has an unknown price."""
        blob = json.dumps(
            {
                "head": "h",
                "worktree_fingerprint": "w",
                "committed_fingerprint": "c",
                "returncode": 0,
                "counts": {"passed": 1},
            }
        )
        assert pp.Receipt.from_json(blob).duration_seconds is None

    def test_duration_does_not_enter_the_verdict(self):
        """:func:`check` grades green/stale/vacuous.  A price is diagnostic —
        making the gate depend on it would let a clock reading refuse a push."""
        base = dict(
            head="h",
            worktree_fingerprint="w",
            committed_fingerprint="c",
            returncode=0,
            counts={"passed": 10},
        )
        fast = pp.Receipt(**base, duration_seconds=0.5)
        slow = pp.Receipt(**base, duration_seconds=5000.0)
        none = pp.Receipt(**base)
        assert fast.executed == slow.executed == none.executed
        assert fast.failures == slow.failures == none.failures


class TestFormatCounts:
    """The ``record`` CLI's human-facing line must state the **run's** counts.

    D-211 made the suite sharded, and the summary line kept tailing the captured
    output — which under sharding is the shard processes' streams concatenated,
    so its last summary line belongs to whichever shard finished last.  The
    receipt held the merged total the whole time; the display threw it away.
    """

    _BASE = dict(
        head="h",
        worktree_fingerprint="w",
        committed_fingerprint="c",
        returncode=0,
    )

    def test_reports_the_merged_total_not_one_shards(self):
        """The defect, driven in its own direction.

        A 14-shard run of 2556 tests: every individual shard's summary line is a
        two-to-three digit number, and exactly one of them used to be printed as
        the run's.  The assertion is not "2556 appears" but that the *shard-sized*
        number does not — a formatter that concatenated both would pass the
        weaker test.
        """
        r = pp.Receipt(
            **self._BASE,
            counts={"passed": 2556, "skipped": 158, "xfailed": 1},
            duration_seconds=488.22,
            shards=tuple(("f.py",) for _ in range(14)),
        )
        line = pp.format_counts(r)
        assert "2556 passed" in line
        assert "150 passed" not in line
        assert "14 shards" in line

    def test_serial_run_says_nothing_about_shards(self):
        """``shards=()`` means "not sharded", so the line must not invent a count.

        Same reading :attr:`Receipt.shards` documents: empty is a mode, not a
        zero, and printing ``across 0 shards`` would be a false claim about how
        the run executed.
        """
        r = pp.Receipt(**self._BASE, counts={"passed": 7}, duration_seconds=1.5)
        line = pp.format_counts(r)
        assert "shard" not in line
        assert "7 passed" in line

    def test_unparseable_counts_do_not_read_as_clean(self):
        """``{}`` is what :func:`check` grades ``VACUOUS``.

        An empty string here would render as ``rc=0`` followed by nothing, which
        reads as a clean run — the one direction this line must never fail in.
        """
        r = pp.Receipt(**self._BASE, counts={})
        assert pp.format_counts(r) == "(counts unparseable)"

    def test_missing_duration_is_omitted_rather_than_guessed(self):
        """Older receipts carry no price; the line drops it instead of typing one."""
        r = pp.Receipt(**self._BASE, counts={"passed": 3})
        line = pp.format_counts(r)
        assert "3 passed" == line


# --- probe: is this commit already graded? (D-315) -------------------------
#
# The probe exists because a receipt outlives the cycle that paid for it, and
# nothing in the loop told anyone to look for one.  Its whole value is that it
# answers a *narrower* question than `check`, so the tests that matter are the
# ones pinning the two apart — a probe that merely wrapped `check` would be
# worse than nothing, since it would re-teach cycles to re-earn green receipts.


def test_probe_reports_graded_for_a_green_receipt_on_this_commit(repo: Path):
    path = _write(repo, _receipt_for(repo))
    outcome, sentence = pp.probe(path, root=repo)
    assert outcome == pp.GRADED
    assert "already graded green" in sentence


def test_probe_and_check_split_on_a_dirty_worktree(repo: Path):
    """The reason the probe is not `check` with a softer exit code.

    A tracked path moves *after* the suite — the case the Researcher's 4-hourly
    `research/feed.md` rewrite creates for every cycle that has not run yet.
    `check` must refuse (it licenses a push of this worktree); the probe must
    still say GRADED, because the *commit* is measured and that is what decides
    whether PLAN owes ~16 min of suite.  If these two ever agree here, the probe
    has silently become a second push gate.
    """
    path = _write(repo, _receipt_for(repo))
    (repo / "code.py").write_text("VALUE = 2\n")  # dirty, uncommitted

    assert pp.check(path, root=repo).verdict == pp.STALE
    assert pp.probe(path, root=repo)[0] == pp.GRADED


def test_probe_reports_other_tree_when_the_receipt_grades_another_commit(repo: Path):
    path = _write(repo, _receipt_for(repo, head="0" * 40))
    outcome, sentence = pp.probe(path, root=repo)
    assert outcome == pp.OTHER_TREE
    assert "budget a suite" in sentence


def test_probe_reports_unmeasured_when_no_receipt_exists(repo: Path):
    outcome, sentence = pp.probe(repo / "absent.json", root=repo)
    assert outcome == pp.UNMEASURED
    assert "budget a suite" in sentence


@pytest.mark.parametrize(
    "over",
    [
        {"returncode": 1, "counts": {"passed": 3, "failed": 1}},
        {"counts": {}},  # executed nothing — 'did not fail' is not 'passed'
    ],
    ids=["red", "vacuous"],
)
def test_probe_never_reports_graded_for_a_run_that_did_not_pass(repo: Path, over):
    path = _write(repo, _receipt_for(repo, **over))
    assert pp.probe(path, root=repo)[0] == pp.NOT_GREEN


def test_probe_cli_is_advisory_in_every_outcome(repo: Path, monkeypatch, capsys):
    """rc=0 unconditionally — D-044: a REVIEW reading nobody can clear gets muted.

    Walking the outcomes rather than asserting one is the point: the failure mode
    is a future edit that makes one branch exit non-zero, which would put a gate
    in Phase 1 that no cycle can act on.

    `_main` takes no ``root`` — it reads the repository from the working
    directory, which is exactly how the cycle invokes it — so the chdir is what
    makes each receipt reach the branch it is named for.  Without it every case
    lands on OTHER_TREE and the test passes while checking one branch.
    """
    monkeypatch.chdir(repo)
    for name, receipt in (
        ("green.json", _receipt_for(repo)),
        ("other.json", _receipt_for(repo, head="0" * 40)),
        ("red.json", _receipt_for(repo, returncode=1, counts={"passed": 1, "failed": 1})),
    ):
        path = _write(repo, receipt, name=name)
        assert pp._main(["probe", str(path)]) == 0
    assert pp._main(["probe", str(repo / "absent.json")]) == 0


class TestScopedVerdict:
    """D-404: the gate reads the receipt's argv, not only its counts.

    D-400 measured the hole these tests close — on one tree, a nine-test
    one-file receipt and the 3954-test receipt earned the *same* ``GREEN``,
    and the narrow one described itself as ``none left out`` while the full one
    reported ``96.0%; 164 uncovered``.  Narrowing the invocation made the
    reading look better, which is the direction a gate must never reward.
    """

    def test_a_receipt_that_named_no_target_is_refused(self, repo: Path):
        v = pp.check(
            _write(repo, _receipt_for(repo, command=("python3", "-m", "pytest", "-q")), "s.json"),
            root=repo,
        )
        assert v.verdict == pp.SCOPED
        assert not v.ok

    def test_one_of_three_targets_is_refused(self, repo: Path):
        v = pp.check(
            _write(
                repo,
                _receipt_for(repo, command=("python3", "-m", "pytest", DECLARED_SUITE[0])),
                "one.json",
            ),
            root=repo,
        )
        assert v.verdict == pp.SCOPED
        # The refusal names the targets that were never invoked; a verdict that
        # only said "too narrow" would leave the cycle guessing which.
        for missing in DECLARED_SUITE[1:]:
            assert missing in v.detail

    def test_the_full_command_still_reaches_green(self, repo: Path):
        """The negative control, and the one that matters operationally.

        Every cycle's push runs this argv.  If it ever grades SCOPED the loop
        halts, so this asserts the gate stayed passable in the same file that
        asserts it got stricter.
        """
        v = pp.check(_write(repo, _receipt_for(repo), "full.json"), root=repo)
        assert v.verdict == pp.GREEN

    def test_scope_is_decided_before_coverage(self, repo: Path):
        """Ordering is the fix, not the verdict.

        A narrow receipt collects only what it named, so there is no remainder
        for `uncovered_is_red` to catch — asking coverage first would let this
        exact receipt past on the strength of its own narrowness.  Handing the
        check a FAIL verdict for the uncovered half proves SCOPED wins the race
        rather than merely existing.
        """
        from eval.mppi_sandbox import ci_verdict as cv

        v = pp.check(
            _write(
                repo,
                _receipt_for(
                    repo,
                    counts={"passed": 3, "skipped": 2},
                    command=("python3", "-m", "pytest", "-q"),
                ),
                "race.json",
            ),
            root=repo,
            uncovered_verdict=cv.FAIL,
        )
        assert v.verdict == pp.SCOPED

    def test_a_red_narrow_receipt_is_reported_red(self, repo: Path):
        """RED outranks SCOPED: a run that failed is described by its failure.

        The same precedence UNCOVERED_RED already has, asserted here because a
        new verdict inserted mid-list is exactly where an ordering regression
        would land.
        """
        v = pp.check(
            _write(
                repo,
                _receipt_for(repo, returncode=1, command=("python3", "-m", "pytest", "-q")),
                "redn.json",
            ),
            root=repo,
        )
        assert v.verdict == pp.RED
