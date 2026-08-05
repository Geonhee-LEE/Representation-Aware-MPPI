"""Tests for :mod:`nested_run_ledger`.

The expensive one — actually running the subject under the stub — is marked
``slow``.  Everything else is pure parsing over constructed argvs, because the
claims this module makes are about *arithmetic over a ledger*, and those must
be falsifiable without paying for a suite run.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from eval.mppi_sandbox import nested_run_ledger as nrl
from eval.mppi_sandbox import nested_suite_cost as nsc
from eval.mppi_sandbox import predicate_vacuity as pv

PACKAGE = Path(nrl.__file__).resolve().parent


def _argv(selection, plugin=None, ignores=()):
    argv = ["/usr/bin/python3", "-m", "pytest", *selection]
    argv += [f"--ignore={p}" for p in ignores]
    if plugin:
        argv += ["-p", plugin]
    argv += ["-q", "-p", "no:cacheprovider"]
    return tuple(argv)


def _spawn(selection, plugin=None, ignores=(), timeout=900, text=None):
    """A spawn whose recorder text *was* captured.

    ``text`` defaults to the plugin's own name, so two spawns of the same
    plugin are identical and two of different plugins are not — the ordinary
    case.  The tests that need one name over two texts, or no text at all,
    build their :class:`~nested_run_ledger.Spawn` directly.
    """
    texts = ((plugin, text or plugin),) if plugin else ()
    return nrl.Spawn(argv=_argv(selection, plugin, ignores), timeout=timeout,
                     cwd=None, plugin_texts=texts)


# --------------------------------------------------------------------------
# Parsing an argv back into what the run measures
# --------------------------------------------------------------------------

def test_the_selection_skips_flags_and_their_operands():
    """``-p NAME`` must not leave ``NAME`` in the collected paths.

    The whole collapse key rests on two runs being compared by what they
    collect; a parse that lets a plugin name through makes two identical
    commands look like different selections.
    """
    spawn = _spawn(("a.py", "b.py"), plugin="some_plugin")
    assert spawn.selection == ("a.py", "b.py")
    assert "some_plugin" not in spawn.selection
    assert "no:cacheprovider" not in spawn.selection


def test_the_inert_plugin_carries_no_measurement_identity():
    """``no:cacheprovider`` is on every recorder here, so it cannot tell two apart."""
    assert _spawn(("a.py",), plugin="pv_plugin").plugins == ("pv_plugin",)
    assert _spawn(("a.py",)).plugins == ()


def test_full_suite_is_judged_as_a_set_not_a_sequence():
    """The recorders splat a sequence whose order is theirs; order is not cost."""
    forward = _spawn(tuple(pv.DEFAULT_SUITE))
    reversed_ = _spawn(tuple(reversed(pv.DEFAULT_SUITE)))
    assert forward.is_full_suite
    assert reversed_.is_full_suite
    assert not _spawn(("eval/mppi_sandbox/tests/test_reach.py",)).is_full_suite


def test_two_identical_commands_share_a_collapse_key():
    """Identity, not equivalence — this is what a memo may safely serve."""
    a = _spawn(tuple(pv.DEFAULT_SUITE), plugin="pv_plugin", ignores=("x.py",))
    b = _spawn(tuple(pv.DEFAULT_SUITE), plugin="pv_plugin", ignores=("x.py",))
    assert nrl.collapse_key(a) == nrl.collapse_key(b)


@pytest.mark.parametrize("differ", ["plugin", "ignores", "selection"])
def test_a_run_that_measures_something_else_does_not_collapse(differ):
    """Each component of the key must be load-bearing on its own.

    A key that ignored ``ignores`` would fold ``measure`` (4 exclusions) into
    ``measure_attributed`` (none) — and the per-origin record exists precisely
    to run with nothing hidden.  That collapse would remove evidence and read
    as a saving, which is the D-091 failure with the sign flipped.
    """
    base = _spawn(tuple(pv.DEFAULT_SUITE), plugin="pv_plugin", ignores=("x.py",))
    other = {
        "plugin": _spawn(tuple(pv.DEFAULT_SUITE), plugin="pi_plugin",
                         ignores=("x.py",)),
        "ignores": _spawn(tuple(pv.DEFAULT_SUITE), plugin="pv_plugin"),
        "selection": _spawn(("a.py",), plugin="pv_plugin", ignores=("x.py",)),
    }[differ]
    assert nrl.collapse_key(base) != nrl.collapse_key(other)


def test_one_plugin_name_over_two_recorder_texts_does_not_collapse():
    """The key's own defect class, found in the key built to avoid it.

    ``predicate_vacuity`` installs ``_PLUGIN`` and ``_PLUGIN_ATTRIBUTED`` under
    the **one** name ``predicate_vacuity_plugin``, by writing whichever is
    wanted into a temporary directory on ``PYTHONPATH``.  So an argv names the
    recorder and does not carry it, and two spawns can be character-identical
    on the command line while tallying different things.  Today the two happen
    to differ in their ``--ignore`` sets and the argv-only key separated them by
    accident; call ``measure_attributed`` with the exclusions and the accident
    is gone.  This is :mod:`key_conflation`'s shape — a key that identifies less
    than the name suggests — and over-collapsing reads as a saving.
    """
    full = tuple(pv.DEFAULT_SUITE)
    plain = nrl.Spawn(argv=_argv(full, "predicate_vacuity_plugin"),
                      timeout=900, cwd=None,
                      plugin_texts=(("predicate_vacuity_plugin", "aaa"),))
    attributed = nrl.Spawn(argv=_argv(full, "predicate_vacuity_plugin"),
                           timeout=1800, cwd=None,
                           plugin_texts=(("predicate_vacuity_plugin", "bbb"),))
    assert plain.argv == attributed.argv
    assert nrl.collapse_key(plain) != nrl.collapse_key(attributed)


def test_two_populations_over_one_argv_do_not_collapse():
    """``PREDICATE_VACUITY_SITES`` decides what is recorded and is not in argv."""
    full = tuple(pv.DEFAULT_SUITE)
    a = nrl.Spawn(argv=_argv(full, "pv_plugin"), timeout=900, cwd=None,
                  plugin_texts=(("pv_plugin", "aaa"),), payload="sites-a")
    b = nrl.Spawn(argv=_argv(full, "pv_plugin"), timeout=900, cwd=None,
                  plugin_texts=(("pv_plugin", "aaa"),), payload="sites-b")
    assert nrl.collapse_key(a) != nrl.collapse_key(b)


def test_an_uncaptured_recorder_text_is_unknown_not_matching():
    """A spawn whose plugin text was never read cannot be called a duplicate.

    The ledger under-counts by construction and that direction is deliberate;
    *this* silence points the other way — it would let two unknowns collapse
    into one and shrink the collapsed cost, which is the direction that reads
    clean.  So the count refuses rather than guesses.
    """
    full = tuple(pv.DEFAULT_SUITE)
    blind = (nrl.Spawn(argv=_argv(full, "pv_plugin"), timeout=900, cwd=None),
             nrl.Spawn(argv=_argv(full, "pv_plugin"), timeout=900, cwd=None))
    led = nrl.Ledger(spawns=blind, collected=10)
    assert not blind[0].identified
    assert led.verdict() == nrl.UNIDENTIFIED
    assert led.duplicates == -1


# --------------------------------------------------------------------------
# The ledger's arithmetic
# --------------------------------------------------------------------------

def test_duplicates_are_what_a_pure_memo_removes():
    full = tuple(pv.DEFAULT_SUITE)
    spawns = (_spawn(full, plugin="pv_plugin"),
              _spawn(full, plugin="pv_plugin"),
              _spawn(full, plugin="pi_plugin"))
    led = nrl.Ledger(spawns=spawns, collected=10)
    assert led.full_suite_runs == 3
    assert len(led.collapse_classes) == 2
    assert led.duplicates == 1


def test_a_scratch_run_is_not_counted_against_the_full_suite_cost():
    """``_measure_scratch``'s two-file suite costs 300 s, not 1396 s.

    :mod:`nested_suite_cost` shipped this exact false positive and caught it by
    measuring a subject; the ledger must not re-import it.
    """
    led = nrl.Ledger(spawns=(_spawn(("a.py", "b.py"), plugin="pv_plugin"),),
                     collected=10)
    assert led.spawns and led.full_suite_runs == 0


def test_a_selection_that_collected_nothing_is_not_a_selection_that_spawned_nothing():
    """D-088's distinction, one module over: no measurement != a finding."""
    assert nrl.Ledger(spawns=(), collected=0).verdict() == nrl.UNCOLLECTED
    assert nrl.Ledger(spawns=(), collected=7).verdict() == nrl.NO_SPAWNS
    assert nrl.Ledger(spawns=(_spawn(("a.py",)),), collected=7).verdict() == nrl.OBSERVED


# --------------------------------------------------------------------------
# The upper bound, and the defect it was shipped with
# --------------------------------------------------------------------------

def test_guard_vacuity_is_in_the_upper_bound_and_the_signature_scan_misses_it():
    """The finding that flipped this module's verdict, pinned as a property.

    ``guard_vacuity.measure`` defaults ``suite`` to a ``DEFAULT_SUITE`` and
    hard-codes ``timeout=900`` at the call site, so
    :func:`nested_suite_cost.suite_runners` — which requires an integer
    ``timeout`` *default* on the signature — cannot see it.  Read as the upper
    bound, that omission grades the collapse ``SUFFICIENT``; it is not.
    """
    signature_scan = {f"{s.module}.{s.function}" for s in nsc.suite_runners()}
    assert "guard_vacuity.measure" not in signature_scan
    assert "guard_vacuity.measure" in nrl.declared_classes()


def test_the_inner_frame_is_not_counted_beside_the_runners_that_share_it():
    """``predicate_vacuity._run_recorder`` is the frame under both runners.

    Counting it as well would report three classes for a module with two
    recorders — an upper bound is allowed to be loose, but not by
    double-counting one run under two names.
    """
    declared = nrl.declared_classes()
    assert "predicate_vacuity._run_recorder" not in declared
    pv_classes = [d for d in declared if d.startswith("predicate_vacuity.")]
    assert sorted(pv_classes) == ["predicate_vacuity.measure",
                                  "predicate_vacuity.measure_attributed"]


def test_collapsing_alone_does_not_clear_the_ceiling():
    """The cycle's headline, as an inequality over the two measured numbers.

    Six runners at 1396 s each is 8376 s against a 7200 s ceiling.  This is the
    claim that makes the timeout raise **mandatory** rather than a second
    option: no amount of memoising reaches the ceiling from here.
    """
    g = nrl.grade(None)
    assert g.classes_upper == 6
    assert g.verdict == nrl.INSUFFICIENT
    assert g.headroom_seconds < 0


def test_sufficiency_is_certified_from_the_upper_bound_not_the_ledger():
    """A ledger claiming one class must not talk the grade into ``SUFFICIENT``.

    The ledger under-counts by construction (a stubbed spawn fails its caller,
    which then never reaches its next spawn), and under-counting classes makes
    the collapsed cost look smaller.  That is the direction that reads clean,
    so the certification may not depend on it.
    """
    optimistic = nrl.Ledger(spawns=(_spawn(tuple(pv.DEFAULT_SUITE),
                                           plugin="pv_plugin"),), collected=99)
    assert nrl.grade(optimistic).verdict == nrl.INSUFFICIENT


def test_a_smaller_suite_would_make_the_collapse_fit():
    """Falsifiable: the verdict tracks the numbers, it is not hard-coded."""
    g = nrl.grade(None, suite_seconds=600)
    assert g.verdict == nrl.SUFFICIENT
    assert g.headroom_seconds > 0


# --------------------------------------------------------------------------
# The instrument's own cost
# --------------------------------------------------------------------------

def test_this_module_never_spawns_the_full_suite():
    """It spawns — that is the measurement — but never ``DEFAULT_SUITE``.

    :mod:`nested_suite_cost` can pin "no subprocess at all"; this one cannot,
    so it pins the property that actually matters: the instrument that measures
    what a full-suite run costs must not perform one.
    """
    assert nrl.spawns_no_suite()


def test_the_subject_is_derived_from_source_not_hand_listed():
    """A hand-listed subject goes stale silently; this one tracks the runners."""
    tests = nrl.spawning_tests()
    assert tests, "no spawning test files found — the derivation is broken"
    for path in tests:
        assert path.startswith("eval/mppi_sandbox/tests/test_")
        assert (Path(nrl.ROOT) / path).exists()


def test_the_recorder_delegates_spawns_that_are_not_pytest():
    """An instrument must not change what it is not measuring.

    The plugin text is executed in a subprocess, so it is checked here as
    source: the non-pytest branch must call through to the real ``run``.
    """
    tree = ast.parse(nrl._PLUGIN)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_record")
    guard = fn.body[1]
    assert isinstance(guard, ast.If)
    returned = guard.body[0]
    assert isinstance(returned, ast.Return)
    assert isinstance(returned.value, ast.Call)
    assert returned.value.func.id == "_real_run"


@pytest.mark.slow
def test_the_ledger_reproduces_a_measured_run():
    """The reading this cycle published, re-taken.

    Bounds, not equalities: the ledger under-counts and the source may grow a
    runner.  What is pinned is the shape of the finding — many more runs than
    classes, so a pure memo is the large saving — and that it is measured on
    the tree under test rather than quoted from a journal.
    """
    led = nrl.observe()
    assert led.verdict() == nrl.OBSERVED
    assert led.full_suite_runs >= 18
    assert len(led.collapse_classes) <= len(nrl.declared_classes())
    assert led.duplicates >= led.full_suite_runs - len(nrl.declared_classes())
