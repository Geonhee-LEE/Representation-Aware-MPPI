"""How many nested suite runs does the slow half actually attempt — and how few could it?

:mod:`nested_suite_cost` established the inequality that dooms the ``slow`` job:
one nested suite run costs the whole fast half (**1396 s** on CI) and the
timeout guarding it is **900 s**, so every full-suite nested call times out
arithmetically.  D-091 then closed the cheap escape — the census genuinely needs
that subject, so no subject cut brings the run under 900 s.  What remains is
D-089's option (a): **collapse the several nested runs into one, and raise the
timeout above the measured cost**.

"Collapse the several runs into one" contains a number nobody has measured.
The static reading gives *call sites in source* — :func:`nested_suite_cost.suite_runners`
lists them — but a call site is not a run: one site called by four tests is four
runs, and a site nobody exercises is none.  Multiply the wrong number and the
repair either clears the ceiling on paper and not in fact, or is abandoned as
insufficient when it would have worked.  D-090 was exactly this shape: a sound
static bound on one population, used as a proxy for a different one.

So this module **counts the spawns** instead, and it counts them without paying
for them.  :func:`observe` runs a selection under a plugin that replaces
``subprocess.run`` with a recorder: any argv containing ``pytest`` is logged and
answered with an empty :class:`~subprocess.CompletedProcess` instead of being
executed; everything else is delegated untouched.  The nested runs therefore
cost nothing and the ledger of what *would* have been spawned is exact.

Two readings come out, and they are bounds in **opposite** directions — which is
the point, because one of them alone cannot decide the repair:

``attempted``  (:func:`Ledger.full_suite_runs`)
    A **lower** bound.  A stubbed spawn returns no observations, so a caller
    that asserts on them fails and never reaches whatever it would have spawned
    next.  Every such loss removes a run from the ledger and none adds one.

``classes``  (:func:`Ledger.collapse_classes`)
    The distinct :func:`collapse_key` values among those runs — two spawns
    sharing a key are the *same command*, so one memoised run serves both with
    no semantic change.  Also a **lower** bound, for the same reason.

A lower bound on ``classes`` is the direction that reads clean: it makes the
collapsed cost look smaller than it is, which is precisely how a repair gets
certified as sufficient when it is not.  So :func:`grade` refuses to certify
sufficiency from the ledger alone.  It takes the **static** class count as the
upper bound (distinct full-suite runners in source, from
:mod:`nested_suite_cost`), and certifies only what the *upper* bound supports —
the ledger's job is to falsify, never to approve.  This is D-090's lesson
applied with the inequality pointed the other way.

The verdict vocabulary keeps the two silences apart, the distinction
:mod:`exemption_masking` had to add as ``UNPOPULATED`` and :mod:`ci_verdict` as
``UNRUN``: a selection that collected nothing (:data:`UNCOLLECTED`) is not a
selection that ran and spawned nothing (:data:`NO_SPAWNS`).  The first says the
measurement did not happen; the second is a finding.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from . import nested_suite_cost as nsc
from . import predicate_vacuity as pv

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent.parent

#: Test files that call a full-suite nested runner.  The default subject: the
#: whole slow half is minutes of genuinely slow closed-loop work that spawns
#: nothing, and paying for it would make this instrument one of the costs it
#: exists to measure.  Derived, not hand-listed — see :func:`spawning_tests`.
_SPAWN_CALLERS = ("measure", "measure_attributed", "record")

#: Verdicts for :func:`Ledger.verdict`.
OBSERVED = "OBSERVED"
NO_SPAWNS = "NO_SPAWNS"
UNCOLLECTED = "UNCOLLECTED"
UNIDENTIFIED = "UNIDENTIFIED"

#: Verdicts for :func:`grade`.
SUFFICIENT = "SUFFICIENT"
INSUFFICIENT = "INSUFFICIENT"
UNDECIDED = "UNDECIDED"

#: Plugin names that carry no measurement identity and so cannot distinguish
#: two spawns.  ``no:cacheprovider`` is passed by every recorder here.
_INERT_PLUGINS = frozenset({"no:cacheprovider"})


# --------------------------------------------------------------------------
# The recorded spawn
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Spawn:
    """One nested ``python -m pytest`` the subject attempted."""

    argv: tuple[str, ...]
    timeout: float | None
    cwd: str | None
    #: ``-p NAME`` -> digest of the recorder text that name loaded, read at
    #: spawn time from the temporary directory on ``PYTHONPATH``.  Empty for a
    #: spawn recorded before this was captured, which :func:`collapse_key`
    #: treats as *unknown*, never as *same*.
    plugin_texts: tuple[tuple[str, str], ...] = ()
    #: Digest of ``PREDICATE_VACUITY_SITES`` — the population the recorder is
    #: asked about.  Two runs of the same argv over different populations
    #: produce different readings and may not share a run.
    payload: str = ""

    @property
    def plugins(self) -> tuple[str, ...]:
        """``-p NAME`` values that carry measurement identity, sorted.

        The plugin is what makes two same-suite runs different measurements:
        :mod:`predicate_vacuity` and :mod:`predicate_inputs` both run the whole
        fast half and record different things, so they may not share a run
        without co-installing both recorders.
        """
        out = []
        for i, tok in enumerate(self.argv):
            if tok == "-p" and i + 1 < len(self.argv):
                name = self.argv[i + 1]
                if name not in _INERT_PLUGINS:
                    out.append(name)
        return tuple(sorted(out))

    @property
    def ignores(self) -> tuple[str, ...]:
        """``--ignore=PATH`` values, sorted.  Part of what the run measures."""
        return tuple(sorted(tok.split("=", 1)[1] for tok in self.argv
                            if tok.startswith("--ignore=")))

    @property
    def selection(self) -> tuple[str, ...]:
        """The paths the nested run collects, in the order given.

        Everything after the ``pytest`` token that is not a flag and not a
        flag's operand.  Returns ``()`` for an argv with no ``pytest`` token,
        which :func:`_is_pytest` has already excluded from a ledger.
        """
        try:
            start = self.argv.index("pytest") + 1
        except ValueError:  # pragma: no cover - excluded upstream
            return ()
        out: list[str] = []
        skip = False
        for tok in self.argv[start:]:
            if skip:
                skip = False
                continue
            if tok == "-p" or tok == "-m" or tok == "-k":
                skip = True
                continue
            if tok.startswith("-"):
                continue
            out.append(tok)
        return tuple(out)

    @property
    def is_full_suite(self) -> bool:
        """Does this run collect the whole fast half?

        Compared as a **set** against :data:`predicate_vacuity.DEFAULT_SUITE`:
        the ordering of the paths is not part of what the run costs, and the
        recorders build the list by splatting a sequence whose order is theirs
        to choose.
        """
        return set(self.selection) == set(pv.DEFAULT_SUITE)

    @property
    def identified(self) -> bool:
        """Was a recorder text captured for every plugin the argv names?

        False means the spawn's identity is **unknown**, not that it matches
        anything: :func:`Ledger.duplicates` refuses to count in that state.
        """
        seen = dict(self.plugin_texts)
        return all(name in seen for name in self.plugins)


def collapse_key(spawn: Spawn) -> tuple:
    """What has to match for two spawns to be servable by **one** run.

    Deliberately conservative: same recorder **text**, same collection, same
    ignores, same population.  Two spawns sharing this key issue the identical
    command over the identical inputs, so memoising the first and returning it
    to the second changes no reading.  A looser key (e.g. ignoring ``ignores``)
    would collapse more and would be a claim about equivalence rather than
    identity — the wrong side of D-090's line, since over-collapsing removes
    evidence and reads as a saving.

    The first version of this function keyed on the plugin **names** in the
    argv and claimed that two spawns sharing the key "issue the identical
    command".  They do — and it is not enough.  ``predicate_vacuity`` installs
    both ``_PLUGIN`` and ``_PLUGIN_ATTRIBUTED`` as the *same* name
    ``predicate_vacuity_plugin``, written into a temporary directory placed on
    ``PYTHONPATH``; the argv names the file, the file is what differs, and the
    two record different things.  Likewise the population under measurement
    travels in ``PREDICATE_VACUITY_SITES``, which no argv mentions.  So an
    argv-only key would have merged a plain census with an attributed one the
    moment they were called with matching ``--ignore`` sets — over-collapsing
    in exactly the direction that reads as a saving.  This is
    :mod:`key_conflation`'s defect class, found in the key built to avoid it.
    """
    return (spawn.plugins, tuple(sorted(spawn.selection)), spawn.ignores,
            tuple(sorted(spawn.plugin_texts)), spawn.payload)


# --------------------------------------------------------------------------
# The ledger
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Ledger:
    """The spawns a subject attempted, and what they collapse to."""

    spawns: tuple[Spawn, ...]
    collected: int

    @property
    def full_suite_spawns(self) -> tuple[Spawn, ...]:
        return tuple(s for s in self.spawns if s.is_full_suite)

    @property
    def full_suite_runs(self) -> int:
        """**Lower** bound on full-suite nested runs the subject attempts."""
        return len(self.full_suite_spawns)

    @property
    def collapse_classes(self) -> tuple[tuple, ...]:
        """Distinct :func:`collapse_key` values, sorted.  Lower bound."""
        return tuple(sorted({collapse_key(s) for s in self.full_suite_spawns}))

    @property
    def unidentified(self) -> tuple[Spawn, ...]:
        """Full-suite spawns whose recorder text was not captured."""
        return tuple(s for s in self.full_suite_spawns if not s.identified)

    @property
    def duplicates(self) -> int:
        """Runs a pure memo would remove, with no co-install and no semantics
        change.  ``full_suite_runs - len(collapse_classes)``, and **-1** when
        any spawn is :attr:`unidentified` — an unknown identity cannot be
        counted as a duplicate, and returning a number anyway is how a
        collapse gets certified on a key that was never identity."""
        if self.unidentified:
            return -1
        return self.full_suite_runs - len(self.collapse_classes)

    def verdict(self) -> str:
        """:data:`UNCOLLECTED` / :data:`NO_SPAWNS` / :data:`UNIDENTIFIED` /
        :data:`OBSERVED`.

        The first two are different facts and the module that conflated them
        (``INERT`` before D-088) shipped the conflation for weeks.  The third
        is the same distinction one level in: spawns were seen, but what they
        would have run is not known well enough to say what collapses.
        """
        if self.collected == 0:
            return UNCOLLECTED
        if not self.spawns:
            return NO_SPAWNS
        if self.unidentified:
            return UNIDENTIFIED
        return OBSERVED


# --------------------------------------------------------------------------
# Measuring it — the non-spawning recorder
# --------------------------------------------------------------------------

#: The recorder.  Replaces ``subprocess.run`` on the :mod:`subprocess` module
#: itself, which is where every caller here resolves it from (`import
#: subprocess` then `subprocess.run(...)`), so one patch catches them all
#: without naming a single caller.  Non-pytest spawns are delegated untouched —
#: this instrument must not change what it is not measuring.
_PLUGIN = '''\
import atexit
import hashlib
import json
import os
import subprocess

OUT = os.environ["NESTED_RUN_LEDGER_OUT"]
SPAWNS = []
_real_run = subprocess.run


def _is_pytest(argv):
    try:
        return "pytest" in list(argv)
    except TypeError:
        return False


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _plugin_texts(argv, env):
    """``-p NAME`` -> digest of the file NAME resolves to on PYTHONPATH.

    The argv carries the plugin's *name*; the recorder that name loads is a
    file written into a temporary directory put on PYTHONPATH.  Two spawns can
    therefore share an argv and load different recorders, so the text has to be
    read here, while the temporary directory still exists.
    """
    roots = [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]
    out = {}
    for i, tok in enumerate(argv):
        if tok != "-p" or i + 1 >= len(argv):
            continue
        name = str(argv[i + 1])
        for r in roots:
            path = os.path.join(r, name + ".py")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    out[name] = _digest(fh.read())
                break
    return out


def _record(*args, **kwargs):
    argv = args[0] if args else kwargs.get("args")
    if not _is_pytest(argv):
        return _real_run(*args, **kwargs)
    env = kwargs.get("env") or os.environ
    SPAWNS.append({
        "argv": [str(a) for a in argv],
        "timeout": kwargs.get("timeout"),
        "cwd": str(kwargs["cwd"]) if kwargs.get("cwd") is not None else None,
        "plugin_texts": _plugin_texts(argv, env),
        "payload": _digest(env.get("PREDICATE_VACUITY_SITES", "")),
    })
    return subprocess.CompletedProcess(args=list(argv), returncode=0,
                                       stdout="", stderr="")


subprocess.run = _record
COLLECTED = [0]


def pytest_collection_modifyitems(session, config, items):
    COLLECTED[0] = len(items)


def _dump():
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"spawns": SPAWNS, "collected": COLLECTED[0]}, fh)


atexit.register(_dump)


def pytest_sessionfinish(session, exitstatus):
    _dump()
'''


def spawning_tests(root: Path | None = None) -> tuple[str, ...]:
    """Test files that name a full-suite runner — the subject of :func:`observe`.

    Derived from :func:`nested_suite_cost.suite_runners`, so the subject tracks
    the source rather than a list that goes stale silently.  A file is included
    if it mentions any runner's function name; over-inclusion costs a cheap
    collected test, under-inclusion loses a spawn, so the match is loose on
    purpose and in the direction that cannot hide a run.
    """
    root = Path(root) if root is not None else ROOT
    names = {site.function for site in nsc.suite_runners()} | set(_SPAWN_CALLERS)
    tests = root / "eval" / "mppi_sandbox" / "tests"
    out = []
    for path in sorted(tests.glob("test_*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover - defended
            continue
        if any(f".{name}(" in text for name in names):
            out.append(str(path.relative_to(root)))
    return tuple(out)


def observe(selection: Sequence[str] | None = None,
            root: Path | None = None,
            timeout: int = 600,
            slow: bool = True) -> Ledger:
    """Run ``selection`` with every nested pytest stubbed; return the ledger.

    ``selection`` defaults to :func:`spawning_tests`.  ``slow`` passes
    ``--slow`` so the marked instrument tests — the ones that spawn — actually
    run; without it the subject collects and deselects exactly the tests this
    module exists to count.
    """
    root = Path(root) if root is not None else ROOT
    selection = tuple(selection) if selection is not None else spawning_tests(root)
    if not selection:
        return Ledger(spawns=(), collected=0)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "nested_run_ledger_plugin.py").write_text(_PLUGIN,
                                                            encoding="utf-8")
        out = tmpdir / "ledger.json"
        env = dict(os.environ)
        env["NESTED_RUN_LEDGER_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(tmpdir), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        subprocess.run(
            [sys.executable, "-m", "pytest", *selection,
             *(("--slow",) if slow else ()),
             "-p", "nested_run_ledger_plugin", "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=timeout,
            check=False, env=env,
        )
        if not out.exists():
            return Ledger(spawns=(), collected=0)
        raw = json.loads(out.read_text(encoding="utf-8"))
    return _ledger(raw)


def _ledger(raw: dict) -> Ledger:
    return Ledger(
        spawns=tuple(Spawn(argv=tuple(s["argv"]), timeout=s.get("timeout"),
                           cwd=s.get("cwd"),
                           plugin_texts=tuple(sorted(
                               (s.get("plugin_texts") or {}).items())),
                           payload=s.get("payload", ""))
                     for s in raw.get("spawns", ())),
        collected=int(raw.get("collected", 0)),
    )


# --------------------------------------------------------------------------
# The static upper bound, and the grade
# --------------------------------------------------------------------------

def declared_classes(root: Path | None = None) -> tuple[str, ...]:
    """**Upper** bound on collapse classes: distinct full-suite runners in source.

    Two runners cannot share a nested run unless their recorders co-install, so
    the count of runners bounds from above what a pure collapse can reach — and
    an upper bound is the only direction that may certify "the collapse fits".

    :func:`nested_suite_cost.suite_runners` alone is **not** that bound, and the
    first run of this module proved it.  ``suite_runners`` reads *signatures*:
    a function is a full-suite runner if it defaults ``suite`` to
    ``DEFAULT_SUITE`` **and** declares an integer ``timeout`` default.  That
    second clause was written to find the two offenders whose 900 lives one
    frame up from the spawn, and it silently excludes
    :func:`guard_vacuity.measure`, which defaults ``suite`` to its own
    ``DEFAULT_SUITE`` and hard-codes ``timeout=900`` **at the call site**.  So
    the signature scan returns 5, the true population is 6, and 5 x 1396 s fits
    the ceiling while 6 x 1396 s does not: the missing runner is the whole
    verdict.  A bound computed for one purpose, used for another — D-090's
    shape, caught here by a name that was missing from a list claiming to be
    complete.

    So the two scans are unioned **per module**: where ``suite_runners`` names
    runners in a module, those are the classes; where it names none, the
    module's ``FULL_SUITE`` call sites stand in.  The per-module rule is what
    keeps ``predicate_vacuity._run_recorder`` — the inner frame *shared* by
    ``measure`` and ``measure_attributed`` — from being counted as a third
    class in a module that already has two.
    """
    del root  # both scans read the installed package
    by_module: dict[str, set[str]] = {}
    for site in nsc.suite_runners():
        by_module.setdefault(site.module, set()).add(site.function)
    for site in nsc.nested_call_sites():
        if site.subject != nsc.FULL_SUITE or site.module in by_module:
            continue
        by_module.setdefault(site.module, set()).add(site.function)
    return tuple(sorted(f"{module}.{fn}"
                        for module, fns in by_module.items() for fn in fns))


@dataclass(frozen=True)
class Grade:
    """Does collapsing clear the ceiling?  Answered on the *upper* bound."""

    verdict: str
    collapsed_seconds: int
    ceiling_seconds: int
    classes_upper: int
    classes_observed: int
    runs_observed: int

    @property
    def headroom_seconds(self) -> int:
        return self.ceiling_seconds - self.collapsed_seconds


def grade(ledger: Ledger | None = None,
          suite_seconds: int = nsc.CI_FAST_HALF_SECONDS,
          ceiling_seconds: int = nsc.SLOW_CEILING_SECONDS,
          root: Path | None = None) -> Grade:
    """Certify sufficiency only from the upper bound; report the ledger beside it.

    :data:`SUFFICIENT` means the collapse fits *even if every declared runner
    needs its own nested run* — the worst case a pure collapse can produce.
    :data:`INSUFFICIENT` means it does not, and then no amount of memoising
    helps: the remaining moves are co-installing the recorders into one run, or
    raising the ceiling.  :data:`UNDECIDED` is reserved for a subject that
    produced no reading at all, so an unmeasured tree cannot be reported as
    either.
    """
    upper = len(declared_classes(root))
    collapsed = upper * suite_seconds
    if upper == 0:
        verdict = UNDECIDED
    elif collapsed <= ceiling_seconds:
        verdict = SUFFICIENT
    else:
        verdict = INSUFFICIENT
    return Grade(verdict=verdict,
                 collapsed_seconds=collapsed,
                 ceiling_seconds=ceiling_seconds,
                 classes_upper=upper,
                 classes_observed=len(ledger.collapse_classes) if ledger else 0,
                 runs_observed=ledger.full_suite_runs if ledger else 0)


def spawns_no_suite(module_path: Path | None = None) -> bool:
    """Does this module's own source contain a full-suite nested run?

    It contains exactly one ``subprocess.run([... pytest ...])`` — the stubbed
    subject in :func:`observe` — and that call must never splat
    ``DEFAULT_SUITE``.  An instrument that measures the cost of running the
    whole suite by running the whole suite is the joke that writes itself;
    :mod:`nested_suite_cost` pins the stronger property (no spawn at all) and
    cannot here, because the measurement *is* a spawn.
    """
    path = module_path or Path(__file__)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"):
            continue
        names = {n.id for arg in node.args for n in ast.walk(arg)
                 if isinstance(n, ast.Name)}
        attrs = {n.attr for arg in node.args for n in ast.walk(arg)
                 if isinstance(n, ast.Attribute)}
        if "DEFAULT_SUITE" in names | attrs:
            return False
    return True


def _main() -> None:  # pragma: no cover - CLI
    led = observe()
    g = grade(led)
    print(f"subject: {len(spawning_tests())} test files, "
          f"{led.collected} collected [{led.verdict()}]")
    print(f"full-suite nested runs attempted: >= {led.full_suite_runs}")
    print(f"  distinct collapse classes:      >= {len(led.collapse_classes)}"
          f"  (memo removes {led.duplicates})")
    print(f"  declared runners (upper bound):    {g.classes_upper}"
          f"  -> {', '.join(declared_classes())}")
    print(f"collapse to {g.classes_upper} x {nsc.CI_FAST_HALF_SECONDS}s "
          f"= {g.collapsed_seconds}s vs ceiling {g.ceiling_seconds}s: {g.verdict}"
          f" (headroom {g.headroom_seconds}s)")
    for s in led.full_suite_spawns:
        print(f"  - plugins={s.plugins or ('<none>',)} "
              f"ignores={len(s.ignores)} timeout={s.timeout}")


if __name__ == "__main__":  # pragma: no cover - CLI
    _main()
