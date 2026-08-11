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
