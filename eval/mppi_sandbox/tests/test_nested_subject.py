"""Tests for :mod:`nested_subject`.

The load-bearing one is :func:`test_the_recorder_does_not_cross_a_process_boundary`
— it runs the shipped plugin over a constructed two-file suite and reads back
what each leg recorded.  Everything else in this file is a control on the
static layer, whose two published numbers (spawner functions, spawning files)
are bounds and are pinned as bounds rather than as values.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

from eval.mppi_sandbox import nested_subject as ns
from eval.mppi_sandbox import predicate_vacuity as pv


# --------------------------------------------------------------------------
# The measured claim
# --------------------------------------------------------------------------


def test_the_recorder_does_not_cross_a_process_boundary(tmp_path):
    """The finding, measured through the shipped plugin.

    Both legs call the same predicate; the only difference is the process.  The
    in-process leg is the positive control — without it a zero from the
    subprocess leg would be indistinguishable from a broken probe.
    """
    reading = ns.probe(tmp_path)
    assert reading.in_process_calls == 2, reading
    assert reading.subprocess_calls == 0, reading
    assert reading.verdict == ns.CONFINED


def test_two_zeroes_are_graded_inconclusive_not_confined():
    """A broken probe and a confirmed finding must not share a verdict.

    D-088's rule one layer on: an empty reading is not a negative reading.  If
    the in-process leg records nothing then the instrument saw nothing at all,
    and ``CONFINED`` drawn from that is a conclusion about the probe.
    """
    assert ns._grade(0, 0) == ns.INCONCLUSIVE
    assert ns._grade(0, 5) == ns.INCONCLUSIVE
    assert ns._grade(2, 0) == ns.CONFINED
    assert ns._grade(2, 1) == ns.PROPAGATES


def test_the_probe_site_is_actually_in_the_scratch_population(tmp_path):
    """The site spelling is a real coupling, so it gets its own check.

    :func:`ns.probe` reads one key out of the recorder's JSON.  A typo there
    returns 0/0, which :func:`ns._grade` correctly calls ``INCONCLUSIVE`` — but
    only this test says *why*, and without it a renamed scratch predicate would
    look like a mechanism finding rather than a broken constant.
    """
    for rel, body in ns.PROBE_SOURCES.items():
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(textwrap.dedent(body), encoding="utf-8")
    population, _ = pv._scan(tmp_path)
    assert ns.PROBE_SITE in {f"{p.module}.{p.qualname}" for p in population}


# --------------------------------------------------------------------------
# The static layer — controls in both directions (D-079)
# --------------------------------------------------------------------------


IN_PROCESS_SOURCE = '''\
    from subject import flag

    def test_calls_it():
        assert flag(1.0)
'''

SPAWNING_SOURCE = '''\
    import subprocess, sys

    def test_calls_it():
        subprocess.run([sys.executable, "-c", "pass"])
'''

NO_TEST_SOURCE = '''\
    import subprocess, sys

    def helper():
        subprocess.run([sys.executable, "-c", "pass"])
'''


def test_classify_answers_both_ways_on_constructed_source():
    empty = frozenset()
    assert ns.classify(textwrap.dedent(IN_PROCESS_SOURCE), empty) == ns.IN_PROCESS
    assert ns.classify(textwrap.dedent(SPAWNING_SOURCE), empty) == ns.SPAWNS


def test_a_file_with_no_tests_is_not_folded_into_the_in_process_population():
    """``NO_TESTS`` stays distinct, and the file chosen *does* spawn.

    Picking a spawning body makes the check say something: it pins that the
    absence of tests is decided before the spawn question, so an empty file
    cannot be counted as either kind of evidence.
    """
    assert ns.classify(textwrap.dedent(NO_TEST_SOURCE), frozenset()) == ns.NO_TESTS


def test_a_shell_out_to_something_that_is_not_a_python_is_not_a_spawn():
    """``git`` runs in a child too and never calls a subject predicate.

    The negative control on :data:`ns.PYTHON_TOKENS` — without it the module
    would count every subprocess in the package and the bound would be
    meaningless.
    """
    source = textwrap.dedent('''\
        import subprocess

        def test_reads_the_repo():
            subprocess.run(["git", "status"])
    ''')
    assert ns.classify(source, frozenset()) == ns.IN_PROCESS


def test_the_dumped_spelling_is_what_is_matched_not_the_source_spelling():
    """Pins the first draft's defect: ``sys.executable`` never appears dumped.

    That draft read **0 of 58** — a miss whose output is "nothing to see here",
    which is the absence-read-as-clean shape this branch has found six times.
    """
    call = ast.parse("subprocess.run([sys.executable])").body[0].value
    assert ns._mentions_python(call)
    assert "sys.executable" not in ast.dump(call)


def test_spawners_closes_transitively_over_package_internal_calls(tmp_path):
    """``record`` spawns nothing itself; it calls ``_run``, which does.

    A one-level reading graded ``test_push_preflight.py`` by accident rather
    than by the reason, so the closure is pinned on a constructed package where
    the chain length is known.
    """
    (tmp_path / "m.py").write_text(textwrap.dedent('''\
        import subprocess, sys

        def leaf():
            subprocess.run([sys.executable, "-c", "pass"])

        def middle():
            leaf()

        def top():
            middle()

        def unrelated():
            return 1
    '''), encoding="utf-8")
    found = ns.spawners(tmp_path)
    assert found == {"leaf", "middle", "top"}


def test_subject_files_applies_the_exclusions_the_census_pays_for():
    """The population is what the nested run collects, not what is on disk."""
    excluded = ("eval/mppi_sandbox/tests/test_predicate_vacuity.py",)
    with_it = ns.subject_files(excluded=())
    without = ns.subject_files(excluded=excluded)
    assert len(with_it) - len(without) == 1
    assert not any(p.name == "test_predicate_vacuity.py" for p in without)


# --------------------------------------------------------------------------
# Reflexivity (D-083) and non-vacuity (D-075)
# --------------------------------------------------------------------------


def test_this_files_own_grade_is_spawns_and_is_not_silently_exempted():
    """The probe spawns, so this file spawns, and that is stated not discovered.

    D-083 found ``inert_surface`` grading itself clean because its scan ran over
    a corpus containing its own test.  A classifier that quietly exempts itself
    is the same defect; pinning the self-grade is what makes it visible.
    """
    here = Path(__file__)
    assert ns.classify(here.read_text(encoding="utf-8"), ns.spawners()) == ns.SPAWNS


def test_the_published_populations_are_non_empty_and_proper_subsets():
    """Neither bound may be vacuous, and neither may be everything.

    An empty ``spawning()`` would say the census is already affordable; a
    ``spawning()`` equal to the whole subject would say the census observes
    nothing at all.  Both are readings a broken classifier produces, so the
    claim is pinned strictly between them rather than at a value that moves
    every time a test file is added.
    """
    graded = ns.readings()
    spawning = ns.spawning()
    assert 0 < len(spawning) < len(graded)
    assert set(spawning) <= set(graded)
    assert len(ns.spawners()) > 0


@pytest.mark.parametrize("verdict", [ns.IN_PROCESS, ns.SPAWNS])
def test_every_grade_in_the_reading_is_a_declared_verdict(verdict):
    assert verdict in set(ns.readings().values())
