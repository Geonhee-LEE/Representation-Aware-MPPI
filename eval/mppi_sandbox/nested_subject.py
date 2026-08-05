"""The nested suite's largest cost buys observations it cannot receive.

D-089 measured the inequality that kills the ``slow`` job: one nested suite run
costs **1396 s** on CI and the timeout guarding it is **900 s**, so every
:func:`predicate_vacuity.measure` call times out arithmetically.  It named two
repairs and declined to pick one, because the load-bearing question was left
open: *does the census need the whole fast half as its subject?*  A
session-scoped fixture collapsing the nested calls is the cheap half, but one
run still costs 1396 s, so collapsing alone does not clear the ceiling.

This module answers the subject question, and the answer is not a budget
opinion.  The recorder is installed on the nested pytest with ``-p
<plugin_module>`` — a **command-line flag**.  Nothing carries it across a
process boundary: there is no ``PYTEST_PLUGINS`` in the environment
:func:`predicate_vacuity._run_recorder` builds, and a test that shells out to
its own ``python -m pytest`` passes no ``-p`` of its own.  So predicate calls
made inside a grandchild process are **invisible to the recorder that paid for
them**.

That is a claim about a mechanism, so it is measured rather than asserted.
:func:`probe` builds a two-file scratch suite — one test calling the subject
predicate in-process, one calling it inside a ``subprocess`` python — measures
both legs through the shipped plugin, and returns the two counts.  A leg that
records nothing is the finding; a probe whose *in-process* leg also records
nothing is graded :data:`INCONCLUSIVE` rather than confirming, because two
zeroes are what a broken probe returns too and this package has now shipped
that mistake three times (D-075's vacuous survival, D-081's overwritten
fixture, D-088's unpopulated reading).

The static layer then asks how much of the real subject is in that position.
:func:`spawning` names the test files in :data:`predicate_vacuity.DEFAULT_SUITE`
whose work goes through a spawned Python — the files the CI workflow comment
already fingered ("cost is superlinear in instrument count — the instrument
tests verify by spawning subprocess pytest runs") without noticing that the
same property makes their contribution to the census **zero**.

What this module deliberately does **not** claim: a *share of seconds*.  Counts
of files are what it measures; per-file wall clock on the CI runner is not in
any artifact it can read, so the saving is reported as a population, not a
percentage.  Q-090 carries the timing question.  D-084's half-fix — a per-job
reading taken by hand and reported as if it were per-run — is the shape being
avoided.

Reflexivity, per D-083: this module's own test file spawns a subprocess (the
probe does), so it classifies itself :data:`SPAWNS`.  That is pinned as a
property rather than left to be discovered, because a classifier that silently
exempts itself is the contamination D-083 found in ``inert_surface``.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import predicate_vacuity as pv

PACKAGE = Path(__file__).resolve().parent

#: Verdicts for :func:`probe` — does the recorder cross a process boundary?
CONFINED = "CONFINED"
PROPAGATES = "PROPAGATES"
INCONCLUSIVE = "INCONCLUSIVE"

#: Verdicts for :func:`classify` — how a test file does its work.
IN_PROCESS = "IN_PROCESS"
SPAWNS = "SPAWNS"
NO_TESTS = "NO_TESTS"

#: Callables that start a process.  ``subprocess.run`` and friends, by attribute
#: name — the module alias is not required to be ``subprocess``.
SPAWN_CALLS = frozenset({"run", "Popen", "check_output", "check_call", "call"})

#: A spawn only counts if the thing being started is a Python.  A test shelling
#: out to ``git`` runs in a child too, but it never calls a subject predicate,
#: so counting it would inflate the population this module exists to bound.
#:
#: Spelled as they appear in :func:`ast.dump`, not as they appear in source —
#: the first draft looked for the string ``"sys.executable"`` and read **0 of
#: 58**, because a dumped attribute access is ``attr='executable'`` and the
#: source spelling never occurs.  A detector whose miss produces the answer
#: "nothing to see here" is exactly the absence-read-as-clean shape this branch
#: has now found six times, so the reading is pinned by test rather than
#: eyeballed.
PYTHON_TOKENS = ("'executable'", "python")

#: The scratch subject.  One predicate, two callers, and the only difference
#: between them is the process the call happens in.
PROBE_SOURCES = {
    "subject.py": '''\
        def observed_flag(x) -> bool:
            return x > 0.0
        ''',
    "tests/test_in_process.py": '''\
        from subject import observed_flag

        def test_calls_in_this_process():
            assert observed_flag(1.0)
            assert not observed_flag(-1.0)
        ''',
    "tests/test_in_subprocess.py": '''\
        import subprocess, sys

        def test_calls_in_a_child_process():
            code = "from subject import observed_flag; assert observed_flag(1.0)"
            out = subprocess.run([sys.executable, "-c", code], capture_output=True)
            assert out.returncode == 0, out.stderr
        ''',
}

#: The site the probe reads back, as :func:`predicate_vacuity` spells sites.
PROBE_SITE = "subject.observed_flag"


@dataclass(frozen=True)
class Propagation:
    """What each leg of :func:`probe` recorded, and the verdict over the pair."""

    in_process_calls: int
    subprocess_calls: int
    verdict: str

    @property
    def confined(self) -> bool:
        return self.verdict == CONFINED


def probe(root: Path, timeout: int = 120) -> Propagation:
    """Measure whether the recorder observes calls made in a child process.

    Builds :data:`PROBE_SOURCES` under ``root`` and runs the shipped recorder
    over each test file **separately**, so the two counts are attributable
    without needing the per-origin plugin.  Returns the pair plus a verdict.
    """
    for rel, body in PROBE_SOURCES.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(textwrap.dedent(body), encoding="utf-8")

    population, _ = pv._scan(root)
    subjects = [p for p in population if p.module == "subject"]

    here = _record(subjects, root, "tests/test_in_process.py", timeout)
    there = _record(subjects, root, "tests/test_in_subprocess.py", timeout)
    return Propagation(in_process_calls=here,
                       subprocess_calls=there,
                       verdict=_grade(here, there))


def _grade(here: int, there: int) -> str:
    """Two zeroes are a broken probe, not a finding — D-088's rule, one layer on.

    The in-process leg is the positive control: it calls the same predicate
    through the same plugin and differs only in the process.  If *it* recorded
    nothing then the instrument, the scratch tree or the site spelling is
    broken, and ``CONFINED`` would be a conclusion drawn from an instrument that
    demonstrably cannot see anything at all.
    """
    if here == 0:
        return INCONCLUSIVE
    return CONFINED if there == 0 else PROPAGATES


def _record(population: Sequence[pv.Predicate], root: Path, test: str,
            timeout: int) -> int:
    """Total recorded calls at :data:`PROBE_SITE` from running one test file.

    A scratch copy of :func:`predicate_vacuity._run_recorder`: the modules here
    are top-level rather than ``eval.mppi_sandbox.*``, which is the one edit
    :func:`predicate_inputs._measure_scratch` makes for the same reason.
    """
    plugin = pv._PLUGIN.replace('"eval.mppi_sandbox." + module', "module")
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "nested_subject_plugin.py").write_text(plugin, encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = pv._sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join([str(tmpdir), str(root)])
        subprocess.run(
            [sys.executable, "-m", "pytest", test, "-p", "nested_subject_plugin",
             "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=timeout,
            check=False, env=env,
        )
        if not out.exists():
            return 0
        raw = json.loads(out.read_text(encoding="utf-8"))
        slot = raw.get(PROBE_SITE)
        return 0 if slot is None else slot["true"] + slot["false"]


# --------------------------------------------------------------------------
# The static layer — how much of the real subject is in that position
# --------------------------------------------------------------------------


def spawners(package: Path | None = None) -> frozenset[str]:
    """Package functions that start a Python, by bare name.

    The second draft of this module looked for ``subprocess.run`` **in the test
    file** and read *1 of 58*, which is wrong in the direction that makes the
    census look affordable.  Almost no test spawns directly: it calls
    :func:`predicate_vacuity.measure`, :func:`guard_vacuity.measure`,
    :func:`inert_surface.measure` or :func:`push_preflight.record`, and the
    spawn is one frame down inside the package.  So the population has to be
    computed from the package first and the test files matched against it.

    Bare names, deliberately — this is :mod:`key_conflation`'s defect class and
    it is accepted here **with** its consequence stated: a test naming an
    unrelated ``measure`` is counted.  The reading is therefore an *upper*
    bound on spawning files, which is the safe direction for a claim that a
    population is expensive; :func:`spawning` says so where it is published.

    Closed transitively, and that is not a refinement: ``push_preflight.record``
    spawns nothing itself, it calls ``_run`` which does, and the direct-only
    draft graded its test file by accident rather than by the reason.  A
    one-level reading is a *lower* bound while the bare-name matching is an
    *upper* one, and a number that is loose in both directions at once cannot
    be reported as either.  The fixed point removes one of the two.
    """
    package = package or PACKAGE
    bodies: dict[str, ast.AST] = {}
    direct: set[str] = set()
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            bodies[node.name] = node
            if _spawns_python(node):
                direct.add(node.name)

    found = set(direct)
    while True:
        grown = {name for name, body in bodies.items()
                 if name not in found and _calls_any(body, frozenset(found))}
        if not grown:
            return frozenset(found)
        found |= grown


def classify(source: str, spawner_names: frozenset[str] | None = None) -> str:
    """Grade one test file's source: does its work go through a spawned Python?

    ``NO_TESTS`` is kept distinct from ``IN_PROCESS`` for D-088's reason: a file
    with no test functions contributes nothing either way, and folding it into
    the in-process population would let an empty file read as evidence that the
    census is getting its money's worth.
    """
    names = spawners() if spawner_names is None else spawner_names
    tree = ast.parse(source)
    if not _has_tests(tree):
        return NO_TESTS
    if _spawns_python(tree) or _calls_any(tree, names):
        return SPAWNS
    return IN_PROCESS


def _calls_any(tree: ast.AST, names: frozenset[str]) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in names:
            return True
        if isinstance(func, ast.Attribute) and func.attr in names:
            return True
    return False


def _has_tests(tree: ast.AST) -> bool:
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name.startswith("test_")
               for n in ast.walk(tree))


def _spawns_python(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in SPAWN_CALLS:
            continue
        if _mentions_python(node):
            return True
    return False


def _mentions_python(call: ast.Call) -> bool:
    """Does this call's argument list name a Python interpreter?

    Deliberately textual over the call's own subtree rather than a resolved
    value: the command is often built from a tuple constant defined elsewhere,
    and a resolver that missed those would under-count in the direction that
    makes this module's conclusion look better.
    """
    text = ast.dump(call)
    return any(tok in text for tok in PYTHON_TOKENS)


def subject_files(suite: Sequence[str] = pv.DEFAULT_SUITE,
                  root: Path | None = None,
                  excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                  ) -> tuple[Path, ...]:
    """Test files the nested run actually collects, ``--ignore`` applied.

    The exclusions are applied here rather than after grading so the population
    is the one the census pays for, not the one on disk.
    """
    root = root or PACKAGE.parent.parent
    skip = {(root / p).resolve() for p in excluded}
    found: list[Path] = []
    for entry in suite:
        target = root / entry
        candidates = sorted(target.rglob("test_*.py")) if target.is_dir() else [target]
        found.extend(p for p in candidates
                     if p.is_file() and p.resolve() not in skip)
    return tuple(sorted(set(found)))


def readings(suite: Sequence[str] = pv.DEFAULT_SUITE,
             root: Path | None = None,
             excluded: Sequence[str] = pv.EXCLUDED_TESTS,
             ) -> dict[Path, str]:
    """Every collected test file, graded."""
    names = spawners()
    return {p: classify(p.read_text(encoding="utf-8"), names)
            for p in subject_files(suite, root, excluded)}


def spawning(suite: Sequence[str] = pv.DEFAULT_SUITE,
             root: Path | None = None,
             excluded: Sequence[str] = pv.EXCLUDED_TESTS,
             ) -> tuple[Path, ...]:
    """Collected files whose work happens in a child process.

    These are the files the nested run pays full wall clock for and receives no
    observation from — *given* :func:`probe` grading ``CONFINED``.  The
    conditional is the whole content: without the measurement this is a list of
    files that merely look expensive.

    An **upper** bound, for the bare-name reason :func:`spawners` states.  The
    direction is chosen and not accidental: an over-count here proposes cutting
    a file that was in fact contributing, which the census would catch as a
    changed reading, whereas an under-count leaves the ceiling uncleared and
    looks like success.
    """
    return tuple(p for p, v in readings(suite, root, excluded).items()
                 if v == SPAWNS)
