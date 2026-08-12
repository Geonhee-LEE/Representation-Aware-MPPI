"""The split must be a partition, and every unknown must fall back to serial.

These tests carry the soundness argument that :mod:`suite_shard`'s docstring
makes in prose: sharding is safe *because* it runs the same tests, so every
assertion here is about the split not losing, duplicating, or silently
narrowing what the caller asked for.
"""

from __future__ import annotations

import pytest

from eval.mppi_sandbox import push_preflight as pp
from eval.mppi_sandbox import suite_shard as ss


# --- plan() is a partition, or it raises -------------------------------------


def test_plan_partitions_its_input():
    files = [f"t{i}.py" for i in range(37)]
    shards = ss.plan(files, 8)
    flat = [f for s in shards for f in s]
    assert sorted(flat) == sorted(files)
    assert len(flat) == len(set(flat))


def test_plan_drops_empty_shards_rather_than_emitting_them():
    # pytest exits 5 on an empty target list, which merge_returncode reddens.
    # Three files at jobs=16 must therefore give three shards, not sixteen.
    assert len(ss.plan(["a.py", "b.py", "c.py"], 16)) == 3


def test_plan_is_deterministic():
    files = [f"t{i}.py" for i in range(20)]
    w = {f: len(f) for f in files}
    assert ss.plan(files, 5, w) == ss.plan(files, 5, w)


def test_plan_dedupes_so_a_file_is_never_run_twice():
    # A directory arg that also names one of its own files would otherwise
    # double-count in the merged totals.
    shards = ss.plan(["a.py", "a.py", "b.py"], 4)
    flat = [f for s in shards for f in s]
    assert sorted(flat) == ["a.py", "b.py"]


def test_plan_balances_by_weight():
    # One heavy file and many light ones: the heavy one must not share a shard
    # with the bulk of the rest.
    files = ["heavy.py"] + [f"light{i}.py" for i in range(10)]
    w = {f: (1000 if f == "heavy.py" else 1) for f in files}
    shards = ss.plan(files, 2, w)
    heavy = next(s for s in shards if "heavy.py" in s)
    assert len(heavy) == 1


def test_plan_rejects_zero_jobs():
    with pytest.raises(ValueError):
        ss.plan(["a.py"], 0)


def test_plan_empty_input_is_empty_not_an_error():
    assert ss.plan([], 4) == []


# --- merge_counts fails closed ------------------------------------------------


def test_merge_counts_sums_outcomes():
    got = ss.merge_counts([{"passed": 10, "skipped": 2}, {"passed": 5, "xfailed": 1}])
    assert got == {"passed": 15, "skipped": 2, "xfailed": 1}


def test_merge_counts_is_empty_if_any_shard_is_unreadable():
    # The failure this guards: summing over the shards that *did* parse yields a
    # smaller-but-healthy-looking total, which `check` would grade on `executed`
    # and pass.  {} routes to VACUOUS instead.
    assert ss.merge_counts([{"passed": 10}, {}]) == {}


def test_merge_counts_of_nothing_is_empty():
    assert ss.merge_counts([]) == {}


def test_merged_empty_counts_grade_vacuous_not_green():
    r = pp.Receipt(
        head="h",
        worktree_fingerprint="w",
        committed_fingerprint="c",
        returncode=0,
        counts=ss.merge_counts([{"passed": 10}, {}]),
    )
    assert r.executed == 0
    assert r.failures == 0  # green-looking on both counters...
    assert not r.counts  # ...and still refused, because there is no reading


# --- merge_returncode reddens on any shard -----------------------------------


def test_merge_returncode_keeps_first_nonzero():
    assert ss.merge_returncode([0, 0, 1, 0]) == 1


def test_merge_returncode_reddens_on_collected_nothing():
    # pytest's 5 means the shard got files it could not read — a broken split,
    # not an empty one.
    assert ss.merge_returncode([0, 5]) == 5


def test_merge_returncode_all_green():
    assert ss.merge_returncode([0, 0, 0]) == 0


# --- flags survive the split -------------------------------------------------


def test_split_args_separates_paths_from_flags():
    paths, flags = ss.split_args(["eval/x/", "-q", "eval/y.py", "--slow"])
    assert paths == ["eval/x/", "eval/y.py"]
    assert flags == ["-q", "--slow"]


def test_split_args_drops_the_bare_separator():
    paths, flags = ss.split_args(["--", "a.py", "-q"])
    assert paths == ["a.py"] and flags == ["-q"]


@pytest.mark.parametrize("flag", ["-k", "-m", "-p", "--deselect"])
def test_a_separate_flag_value_is_caught_by_the_filesystem(tmp_path, flag):
    # `-k expr` leaves `expr` among the paths.  Rather than carry a table of
    # which flags take values (D-047's stale-copy shape, and itself an
    # unwatched module-level allow-list), ask the tree: `expr` is not a file,
    # so the whole run falls back to serial and the flag keeps its value.
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "test_a.py").write_text("")
    paths, _ = ss.split_args(["pkg", flag, "some_expr"])
    assert paths == ["pkg", "some_expr"]
    assert ss.expand_targets(paths, tmp_path) == []


def test_selection_flags_are_what_must_not_be_lost():
    # --slow changes *which tests run*; losing it would turn the split into a
    # subset, which is the thing sharding exists to avoid.
    _, flags = ss.split_args(["eval/x/", "--slow", "-q"])
    assert "--slow" in flags


# --- expand_targets ----------------------------------------------------------


def test_expand_targets_expands_a_directory(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "test_a.py").write_text("")
    (d / "test_b.py").write_text("")
    (d / "helper.py").write_text("")  # not a test file
    got = ss.expand_targets(["pkg"], tmp_path)
    assert got == ["pkg/test_a.py", "pkg/test_b.py"]


def test_expand_targets_recurses(tmp_path):
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    (tmp_path / "pkg" / "sub" / "test_deep.py").write_text("")
    assert ss.expand_targets(["pkg"], tmp_path) == ["pkg/sub/test_deep.py"]


def test_expand_targets_keeps_explicit_files(tmp_path):
    (tmp_path / "test_one.py").write_text("")
    assert ss.expand_targets(["test_one.py"], tmp_path) == ["test_one.py"]


def test_expand_targets_dedupes_dir_plus_member(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "test_a.py").write_text("")
    assert ss.expand_targets(["pkg", "pkg/test_a.py"], tmp_path) == ["pkg/test_a.py"]


def test_expand_targets_refuses_on_an_unmatched_path(tmp_path):
    # [] means "run serially", so the typo'd target reaches pytest intact
    # instead of being silently dropped from a shard.
    assert ss.expand_targets(["nope/"], tmp_path) == []


def test_expand_targets_refuses_on_an_empty_dir(tmp_path):
    # A shard given a test-less directory collects nothing and pytest exits 5,
    # which merge_returncode reddens.  Refuse to shard instead.
    (tmp_path / "empty").mkdir()
    assert ss.expand_targets(["empty"], tmp_path) == []


def test_one_bad_target_refuses_the_whole_split(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "test_a.py").write_text("")
    assert ss.expand_targets(["pkg", "nope.py"], tmp_path) == []


# --- jobs --------------------------------------------------------------------


def test_default_jobs_reserves_cores():
    assert ss.default_jobs(16) == 14


def test_default_jobs_is_capped():
    assert ss.default_jobs(128) == ss.JOBS_CEILING


def test_default_jobs_never_zero():
    assert ss.default_jobs(1) == 1
    assert ss.default_jobs(2) == 1


# --- the receipt field round-trips -------------------------------------------


def test_shards_round_trip_through_json():
    r = pp.Receipt(
        head="h",
        worktree_fingerprint="w",
        committed_fingerprint="c",
        returncode=0,
        counts={"passed": 3},
        shards=(("a.py", "b.py"), ("c.py",)),
    )
    back = pp.Receipt.from_json(r.to_json())
    assert back.shards == (("a.py", "b.py"), ("c.py",))


def test_serial_receipt_reads_as_not_sharded():
    r = pp.Receipt(
        head="h",
        worktree_fingerprint="w",
        committed_fingerprint="c",
        returncode=0,
        counts={"passed": 3},
    )
    assert pp.Receipt.from_json(r.to_json()).shards == ()


def test_older_receipts_without_the_field_still_load():
    import json

    blob = json.dumps(
        {
            "head": "h",
            "worktree_fingerprint": "w",
            "committed_fingerprint": "c",
            "returncode": 0,
            "counts": {"passed": 1},
        }
    )
    assert pp.Receipt.from_json(blob).shards == ()


# --- record_sharded keeps the caller's command -------------------------------


def _tiny_suite(tmp_path, n=6):
    """A real git repo holding *n* trivial test files.

    Git-backed because :func:`push_preflight.record_sharded` stamps the tree it
    read via :func:`tree_provenance.stamp`, which shells out to ``git
    ls-files``.  A bare tmp dir makes these tests fail on the stamp rather than
    on anything about sharding.
    """
    import subprocess

    d = tmp_path / "pkg"
    d.mkdir()
    for i in range(n):
        (d / f"test_m{i}.py").write_text(f"def test_{i}():\n    assert True\n")
    for cmd in (
        ["git", "init", "-q"],
        ["git", "config", "user.email", "t@t"],
        ["git", "config", "user.name", "t"],
        ["git", "add", "-A"],
        ["git", "commit", "-qm", "t"],
    ):
        subprocess.run(cmd, cwd=str(tmp_path), check=True, capture_output=True)
    return d


def test_record_sharded_reports_the_logical_command_not_the_file_list(tmp_path):
    # receipt_cost._receipt_is_full reads narrowing off `command`.  A rewritten
    # 114-file command carries no `--ignore=` and would grade "full" by
    # accident; the logical command makes that predicate answer its own
    # question.
    _tiny_suite(tmp_path)
    cmd = ("python3", "-m", "pytest", "pkg", "-q")
    receipt, _ = pp.record_sharded(cmd, root=tmp_path, jobs=3)
    assert receipt.command == cmd
    assert len(receipt.shards) == 3


def test_record_sharded_counts_every_test_exactly_once(tmp_path):
    _tiny_suite(tmp_path, n=9)
    receipt, _ = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q"), root=tmp_path, jobs=4
    )
    assert receipt.returncode == 0
    assert receipt.counts.get("passed") == 9


def test_record_sharded_reddens_when_one_shard_fails(tmp_path):
    d = _tiny_suite(tmp_path, n=5)
    (d / "test_bad.py").write_text("def test_bad():\n    assert False\n")
    receipt, _ = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q"), root=tmp_path, jobs=3
    )
    assert receipt.returncode != 0
    assert receipt.failures == 1


def test_record_sharded_falls_back_to_serial_on_one_file(tmp_path):
    _tiny_suite(tmp_path, n=1)
    receipt, _ = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q"), root=tmp_path, jobs=8
    )
    assert receipt.shards == ()
    assert receipt.counts.get("passed") == 1


def test_record_sharded_falls_back_to_serial_on_jobs_one(tmp_path):
    _tiny_suite(tmp_path, n=4)
    receipt, _ = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q"), root=tmp_path, jobs=1
    )
    assert receipt.shards == ()
    assert receipt.counts.get("passed") == 4


def test_record_sharded_falls_back_on_an_ambiguous_flag(tmp_path):
    _tiny_suite(tmp_path, n=4)
    receipt, _ = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q", "-k", "test_m1"),
        root=tmp_path,
        jobs=4,
    )
    assert receipt.shards == ()  # serial, and `-k` therefore still applied
    assert receipt.counts.get("passed") == 1


def test_record_sharded_merged_log_names_every_shard(tmp_path):
    _tiny_suite(tmp_path, n=6)
    _, output = pp.record_sharded(
        ("python3", "-m", "pytest", "pkg", "-q"), root=tmp_path, jobs=3
    )
    for i in (1, 2, 3):
        assert f"shard {i}/3" in output


# ---------------------------------------------------------------------------
# The split, addressed by index from outside the process (D-227).
#
# These pin the two answers that are NOT "here are your files", because both
# are ways a matrix can silently stop being a split: a serial fallback makes
# every shard run everything, and an empty shard invoking pytest with no paths
# collects the whole rootdir.
# ---------------------------------------------------------------------------


def _files(tmp_path, shard, of, args=("pkg",)):
    return ss.shard_files(list(args), shard, of, tmp_path)


def test_the_shards_of_a_split_are_exactly_the_suite(tmp_path):
    _tiny_suite(tmp_path, n=9)
    seen = []
    for i in range(1, 4):
        seen.extend(_files(tmp_path, i, 3))
    assert sorted(seen) == sorted(ss.expand_targets(["pkg"], tmp_path))
    assert len(seen) == len(set(seen)) == 9


def test_shard_files_agrees_with_plan_index_for_index(tmp_path):
    _tiny_suite(tmp_path, n=7)
    files = ss.expand_targets(["pkg"], tmp_path)
    buckets = ss.plan(files, 4, {f: ss.file_weight(f, tmp_path) for f in files})
    for i, bucket in enumerate(buckets, start=1):
        assert _files(tmp_path, i, 4) == bucket


def test_a_matrix_wider_than_the_suite_gets_empty_tails_not_errors(tmp_path):
    _tiny_suite(tmp_path, n=2)
    assert _files(tmp_path, 1, 5)
    assert _files(tmp_path, 5, 5) == ()


def test_an_unshardable_target_is_none_rather_than_a_serial_fallback(tmp_path):
    # `expand_targets` returns [] here, which LOCALLY means "run serially".
    # Across a matrix that reading would make every shard run the whole suite.
    _tiny_suite(tmp_path, n=3)
    assert ss.shard_files(["pkg", "-k", "test_m1"], 1, 3, tmp_path) is None
    assert ss.shard_files(["nope"], 1, 3, tmp_path) is None


def test_shard_index_outside_the_matrix_is_refused(tmp_path):
    _tiny_suite(tmp_path, n=3)
    for shard, of in ((0, 3), (4, 3), (1, 0)):
        with pytest.raises(ValueError):
            _files(tmp_path, shard, of)


def test_cli_prints_one_file_per_line(tmp_path, capsys):
    _tiny_suite(tmp_path, n=6)
    rc = ss._main(["--shard", "1", "--of", "3", "--root", str(tmp_path), "--", "pkg"])
    assert rc == 0
    out = capsys.readouterr().out.split()
    assert out == list(_files(tmp_path, 1, 3))


def test_cli_reports_unshardable_loudly(tmp_path, capsys):
    _tiny_suite(tmp_path, n=3)
    rc = ss._main(["--shard", "1", "--of", "2", "--root", str(tmp_path), "--", "nope"])
    assert rc == ss.UNSHARDABLE
    assert "UNSHARDABLE" in capsys.readouterr().err


def test_cli_empty_tail_shard_prints_nothing_and_succeeds(tmp_path, capsys):
    # rc=0 with no output is what lets the workflow step skip pytest; a nonzero
    # rc here would redden a run for a shard that correctly has no work.
    _tiny_suite(tmp_path, n=2)
    rc = ss._main(["--shard", "5", "--of", "5", "--root", str(tmp_path), "--", "pkg"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == ""


def test_cli_keeps_pytest_flags_out_of_its_own_options(tmp_path):
    # `-q` after `--` must not be parsed as this CLI's flag, and must not be
    # mistaken for a target either.
    _tiny_suite(tmp_path, n=4)
    assert ss.shard_files(["pkg", "-q", "-v"], 1, 2, tmp_path) == _files(tmp_path, 1, 2)


class TestCIRunsTheSplitItPlans:
    """CI must ask *this module* for its slice, not re-type the split (D-227).

    The twelve-run `cancelled` streak happened because CI ran serially while
    the local receipt ran sharded, and nothing in the tree stated that the two
    should agree. These derive the requirement from the workflow rather than
    asserting a remembered shape, so a revert to a single serial invocation --
    or a matrix whose width stops being the number the CLI is told -- goes red
    here instead of going silent for another twelve runs.
    """

    WORKFLOW = ".github/workflows/sandbox-ci.yml"

    @staticmethod
    def _fast():
        from pathlib import Path

        import yaml

        return yaml.safe_load(Path(TestCIRunsTheSplitItPlans.WORKFLOW).read_text())[
            "jobs"
        ]["fast"]

    def test_the_fast_job_is_a_matrix(self):
        shards = self._fast()["strategy"]["matrix"]["shard"]
        assert len(shards) > 1, "fast is serial again; the ceiling will be re-crossed"
        assert shards == list(range(1, len(shards) + 1)), "shard indices are 1..N"

    def test_a_red_shard_does_not_cancel_its_siblings(self):
        # fail-fast would discard the other shards' verdicts, which is the same
        # loss of authority `merge_counts` refuses locally by returning {}.
        assert self._fast()["strategy"]["fail-fast"] is False

    def test_the_matrix_width_is_stated_once(self):
        # `--of` must come from `strategy.job-total`, not a second literal that
        # can drift from the matrix above it (D-047).
        step = self._step_containing("suite_shard")
        assert "--of ${{ strategy.job-total }}" in step["run"]

    def test_ci_asks_this_module_for_the_split(self):
        step = self._step_containing("suite_shard")
        assert "eval.mppi_sandbox.suite_shard" in step["run"]
        assert "--shard ${{ matrix.shard }}" in step["run"]

    def test_the_split_is_not_piped_so_its_failure_survives(self):
        # D-221: the default shell is `bash -e` without pipefail, so a pipe
        # would report the last command's status and swallow UNSHARDABLE.
        run = self._step_containing("suite_shard")["run"]
        cmd = run.split("suite_shard", 1)[1].split("\n cat")[0]
        assert "| tee" not in cmd and "|tee" not in cmd

    def test_an_empty_shard_skips_pytest_rather_than_collecting_everything(self):
        step = self._step_containing("python -m pytest")
        assert step.get("if"), "no guard: pytest with no paths collects the rootdir"
        assert "count" in step["if"]

    def test_the_pytest_step_still_runs_the_fast_half(self):
        # The sibling guard in test_suite_coverage keys off a `python -m pytest`
        # line with no `--slow`; keep that shape reachable through the shard.
        step = self._step_containing("python -m pytest")
        assert "--slow" not in step["run"]

    def _step_containing(self, needle):
        for s in self._fast()["steps"]:
            if needle in (s.get("run") or ""):
                return s
        raise AssertionError(f"no fast-job step runs {needle!r}")
