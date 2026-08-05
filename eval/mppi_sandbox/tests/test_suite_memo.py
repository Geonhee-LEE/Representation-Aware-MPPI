"""Tests for :mod:`suite_memo`.

The memo's entire safety argument is that a hit returns what a re-run would
have produced.  So the tests here are mostly **negative controls**: pairs of
calls that look alike to a narrower key and must *not* share a run.  A memo
that is merely fast is not the deliverable; a memo that is fast and cannot
serve one measurement's answer to another question is.

Nothing here spawns a suite.  ``produce`` is a counter, which is exactly the
observable the module exists to reduce.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.mppi_sandbox import suite_memo as sm


@pytest.fixture(autouse=True)
def _isolated_cache():
    """Every test starts empty and leaves nothing behind.

    Load-bearing beyond hygiene: a stored fake reading whose key a *real*
    census call could hit would serve invented observations to the census.
    Combined with the scratch roots below (so ``cwd`` differs from any real
    call), the fakes here cannot reach anything outside this file.
    """
    sm.clear()
    yield
    sm.clear()


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """A scratch root the digest can see — one importable file under ``eval/``."""
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def _command(tree: Path, *, plugin="plugin-text", payload="sites",
             argv=("python", "-m", "pytest", "eval")) -> sm.Command:
    return sm.Command(argv=tuple(argv), cwd=str(tree),
                      plugin_digest=sm.digest_text(plugin),
                      payload_digest=sm.digest_text(payload))


class _Producer:
    """Counts calls; returns a distinguishable payload per call."""

    _DEFAULT = object()

    def __init__(self, result=_DEFAULT):
        self.calls = 0
        self._result = {"site": {"true": 1}} if result is self._DEFAULT else result

    def __call__(self):
        self.calls += 1
        return None if self._result is None else dict(self._result)


# --------------------------------------------------------------------------
# The saving
# --------------------------------------------------------------------------

def test_the_same_command_on_the_same_tree_runs_once(tree):
    """The 14-of-18 claim, at its smallest: issue one command twice, pay once."""
    produce = _Producer()
    cmd = _command(tree)
    first = sm.run_once(cmd, produce)
    second = sm.run_once(cmd, produce)
    assert produce.calls == 1
    assert first == second
    assert sm.stats().hits == 1
    assert sm.stats().runs == 1


def test_a_hit_is_a_copy_so_a_caller_cannot_corrupt_the_cache(tree):
    """These readings are handed to callers that reshape them in place."""
    produce = _Producer()
    cmd = _command(tree)
    first = sm.run_once(cmd, produce)
    first["site"] = "clobbered"
    first["extra"] = "added"
    second = sm.run_once(cmd, produce)
    assert second == {"site": {"true": 1}}
    assert produce.calls == 1


# --------------------------------------------------------------------------
# Negative controls — what must never share a run
# --------------------------------------------------------------------------

def test_the_same_argv_with_a_different_recorder_does_not_share(tree):
    """The defect the argv-keyed version of this would have shipped.

    ``predicate_vacuity`` writes ``_PLUGIN`` or ``_PLUGIN_ATTRIBUTED`` into a
    temporary directory and installs *both* as ``-p predicate_vacuity_plugin``.
    The argvs are then character-identical while the recorders tally different
    things, so a name-keyed memo would answer a plain census with an attributed
    one.  Keyed on the text, they are two commands.
    """
    produce = _Producer()
    plain = _command(tree, plugin="tally-values")
    attributed = _command(tree, plugin="tally-values-per-origin")
    assert plain.argv == attributed.argv
    sm.run_once(plain, produce)
    sm.run_once(attributed, produce)
    assert produce.calls == 2
    assert sm.stats().hits == 0


def test_a_different_population_does_not_share(tree):
    """The population travels in an environment variable, not in the argv."""
    produce = _Producer()
    sm.run_once(_command(tree, payload="sites-a"), produce)
    sm.run_once(_command(tree, payload="sites-b"), produce)
    assert produce.calls == 2


def test_a_changed_tree_does_not_share(tree):
    """Measure, edit, measure again — the second call asks a new question.

    Without this the memo would answer a negative control ("change the source,
    assert the reading moves") with the reading taken *before* the change,
    which is the failure that reads as a pass.
    """
    produce = _Producer()
    cmd = _command(tree)
    sm.run_once(cmd, produce)
    (tree / "eval" / "mod.py").write_text("x = 2\n", encoding="utf-8")
    sm.run_once(cmd, produce)
    assert produce.calls == 2


def test_a_new_file_in_the_tree_does_not_share(tree):
    """Digest over contents *and* paths: adding a file is a different tree."""
    produce = _Producer()
    cmd = _command(tree)
    sm.run_once(cmd, produce)
    (tree / "eval" / "other.py").write_text("x = 1\n", encoding="utf-8")
    sm.run_once(cmd, produce)
    assert produce.calls == 2


def test_droppings_do_not_count_as_a_tree_change(tree):
    """``__pycache__`` appears the moment the first nested run imports anything.

    If it counted, the memo would miss on every second call by construction and
    the saving would be zero while every test above still passed.
    """
    produce = _Producer()
    cmd = _command(tree)
    sm.run_once(cmd, produce)
    cache = tree / "eval" / "__pycache__"
    cache.mkdir()
    (cache / "mod.cpython-312.pyc").write_bytes(b"\x00")
    (cache / "mod.py").write_text("not a source\n", encoding="utf-8")
    sm.run_once(cmd, produce)
    assert produce.calls == 1


# --------------------------------------------------------------------------
# The two refusals — both fail closed
# --------------------------------------------------------------------------

def test_a_run_that_did_not_complete_is_never_stored(tree):
    """``None`` is a timeout or a missing dump file — a failure, not a reading.

    Caching it would make one timeout permanent for the process, and would
    hand a caller willing to wait 1800 s a result produced under 900 s.
    """
    produce = _Producer(result=None)
    cmd = _command(tree)
    assert sm.run_once(cmd, produce) is None
    sm.run_once(cmd, produce)
    assert produce.calls == 2
    assert sm.stats().failures == 2
    assert sm.stats().hits == 0


def test_observing_nothing_is_a_reading_and_is_cached(tree):
    """``{}`` is *ran fine, saw no calls* — a result, and a cacheable one.

    The recorders returned ``{}`` for this **and** for a run that never wrote
    its dump file.  Keying a cache on the conflation would have made it
    permanent: one timeout would have been served for the rest of the session
    as the finding "this predicate is never called".
    """
    produce = _Producer(result={})
    cmd = _command(tree)
    assert sm.run_once(cmd, produce) == {}
    assert sm.run_once(cmd, produce) == {}
    assert produce.calls == 1
    assert sm.stats().hits == 1
    assert sm.stats().failures == 0


def test_a_failure_then_a_success_caches_the_success(tree):
    """The refusal must not poison the key it declined to store under."""
    results = [None, {"site": {"true": 1}}]
    calls = []

    def produce():
        calls.append(1)
        return results[min(len(calls) - 1, len(results) - 1)]

    cmd = _command(tree)
    assert sm.run_once(cmd, produce) is None
    assert sm.run_once(cmd, produce) == {"site": {"true": 1}}
    assert sm.run_once(cmd, produce) == {"site": {"true": 1}}
    assert len(calls) == 2


def test_no_tree_means_no_cache(tmp_path):
    """Nothing to detect a change with ⇒ decline, and run every time.

    :mod:`exemption_masking`'s ``UNPOPULATED`` at the cache layer: an empty
    reading is not a reading, and a key built on one would claim the tree was
    unchanged when it was never looked at.
    """
    produce = _Producer()
    cmd = _command(tmp_path)
    assert sm.tree_digest(tmp_path) is None
    sm.run_once(cmd, produce)
    sm.run_once(cmd, produce)
    assert produce.calls == 2
    assert sm.stats().unkeyed == 2
    assert sm.stats().hits == 0


def test_the_digest_is_content_addressed_not_walk_ordered(tree):
    """Same contents ⇒ same digest, from two independently built trees."""
    twin = tree.parent / "twin"
    (twin / "eval").mkdir(parents=True)
    for name in ("b.py", "a.py", "mod.py"):
        (twin / "eval" / name).write_text("x = 1\n", encoding="utf-8")
    for name in ("a.py", "b.py"):
        (tree / "eval" / name).write_text("x = 1\n", encoding="utf-8")
    assert sm.tree_digest(tree) == sm.tree_digest(twin)


# --------------------------------------------------------------------------
# The wiring — the recorders actually go through it
# --------------------------------------------------------------------------

def test_the_value_census_recorder_is_memoised(tmp_path, monkeypatch):
    """``predicate_vacuity._run_recorder`` twice ⇒ one spawn.

    Patched at :mod:`subprocess`, so the "run" costs nothing; the scratch root
    keeps this call's key away from any real census reading.
    """
    from eval.mppi_sandbox import predicate_vacuity as pv

    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    spawns = _stub_recorder(monkeypatch, pv, {"m.p": {"true": 1, "false": 0,
                                                      "other": []}})
    population = pv.predicates()[:1]
    for _ in range(2):
        raw = pv._run_recorder(pv._PLUGIN, population, ("eval",), tmp_path,
                               (), 900)
    assert len(spawns) == 1
    assert raw == {"m.p": {"true": 1, "false": 0, "other": []}}


def test_the_two_value_recorders_do_not_share_a_run(tmp_path, monkeypatch):
    """Same argv, different recorder text — the wired version of the control."""
    from eval.mppi_sandbox import predicate_vacuity as pv

    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    spawns = _stub_recorder(monkeypatch, pv, {"m.p": {"true": 1, "false": 0,
                                                      "other": []}})
    population = pv.predicates()[:1]
    pv._run_recorder(pv._PLUGIN, population, ("eval",), tmp_path, (), 900)
    pv._run_recorder(pv._PLUGIN_ATTRIBUTED, population, ("eval",), tmp_path,
                     (), 900)
    assert len(spawns) == 2
    assert spawns[0] == spawns[1], "the argvs are identical; the texts are not"


def _stub_recorder(monkeypatch, module, payload):
    """Replace the spawn with one that writes ``payload`` where it is read."""
    import json
    import subprocess

    spawns: list[list[str]] = []

    def fake_run(argv, **kwargs):
        spawns.append(list(argv))
        out = kwargs["env"]["PREDICATE_VACUITY_OUT"]
        Path(out).write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.CompletedProcess(args=list(argv), returncode=0,
                                           stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return spawns
