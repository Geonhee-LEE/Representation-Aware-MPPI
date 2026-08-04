"""Which boolean predicates has the suite only ever seen answer one way? — Q-072 (b).

:mod:`guard_vacuity` closed the ``if <cond>: raise`` half of the search and its
yield was a measured **zero** (D-060: 8/8 candidates raise on a constructed
input, 0 of D-058's shape).  Q-072 (b) is where the other three of the four
motivating findings live — D-055's fixture reading, D-056's verdict comparison,
D-057's boolean bar all **return** rather than raise — and it names the reason
the same instrument cannot follow them:

    a ``raise`` is an observable event, so one coverage line reads it; a
    predicate has to be read off its **return-value distribution**, and that is
    a different instrument.

This is that instrument.  It records, for every boolean-returning function in
the package, the set of values the suite ever observed it return, and reports
the ones that only ever answered one way.

Why one-sidedness is the right reading
---------------------------------------

``NEVER_FIRED`` meant *offered its population, declined every one*.  Its
predicate analogue is not "never called" — that is the ``UNREACHED`` case again
— but **called, repeatedly, and constant**.  D-057's bar is exactly that:
``unseen.min() > 0.0`` was ``True`` on every scene the suite ever rendered,
including the obstacle-free ones it existed to exclude, because a renderer floor
of 112 corner cells sat underneath it.  A predicate that has answered ``True``
ten thousand times and ``False`` never has not been tested; it has been
*recited*.

Five verdicts, and the two extra ones are not padding
-------------------------------------------------------

``BOTH``
    Observed ``True`` and observed ``False``.  The predicate discriminates on
    inputs the suite actually supplies.  Nothing to ask.
``ALWAYS_TRUE`` / ``ALWAYS_FALSE``
    **The candidate set.**  Called at least once, and constant across every
    call.  Split rather than merged because the two have different smells: a
    constant ``True`` is usually a bar sitting on a floor (D-057), a constant
    ``False`` is usually a screen whose population never arrives (D-055).
``UNOBSERVED``
    Never called.  :mod:`guard_vacuity`'s ``UNREACHED``, and D-050's rule
    applies unchanged — silence from something nobody asked is not evidence.
``NON_BOOLEAN``
    Called, and at least one observed return value was not a ``bool``.  This
    falls out of the mechanism rather than being designed in, and it is worth
    keeping: ``arr > 0`` is syntactically a comparison and returns an *array*,
    whose truthiness raises.  A function the scan admitted by shape but which
    does not actually produce booleans is a population error, and a population
    error that reports itself is the one thing five hand-written registries in
    this package did not do (D-045 through D-052).

One-sidedness is arithmetic; the call count is the evidence
------------------------------------------------------------

``ALWAYS_FALSE`` after **one** call and ``ALWAYS_FALSE`` after **5694** are the
same verdict and nothing like the same claim.  The first says the suite called
it once; the second says the suite offered it a population five thousand times
over and it declined every member — which is precisely what made D-058's guard
damning and D-057's bar worth chasing.  So :func:`by_evidence` orders the
candidate set by call count and the report leads with it.

What this module deliberately does **not** do is pick a floor.  A threshold
separating "recited" from "barely called" would be the fourth unjustified
constant in this package (STATE still carries "justify a threshold for
``wilson_lower_at_least``", shipped without one by D-020), and there is no
reason to think the right floor is a constant rather than a function of the
predicate's arity and the size of the population its callers draw from.  The
count is reported; grading it is left open.

Candidates, not findings — the same bound as ``NEVER_FIRED``
-------------------------------------------------------------

One-sidedness is a **necessary** condition for the D-057 shape and not a
sufficient one.  A predicate can be perfectly discriminating over its real input
space and constant over the inputs this suite happens to supply; that is a
statement about the suite.  Confirming a candidate means the D-058 move — work
out what the callers guarantee, then show the other answer is unreachable.  This
module says where to look and how short the list is.

The calibration set is **0**, and that is the finding it ships with
--------------------------------------------------------------------

D-059's census had exactly one ground-truth member where STATE claimed three.
This one has **none**, for a reason worth stating: of the four findings that
motivated the whole search, the one with precisely this shape — D-057's
``unseen.min() > 0.0`` — lives in a **test**, and the population here excludes
tests for the same reason :mod:`guard_vacuity` does (a predicate inside a test
is that test's assertion machinery, not a subject).  So the scan that finally
reaches D-057's *shape* still cannot reach D-057's *instance*.

Rather than ship a mirror with an empty registry — which asserts nothing and
reads as a clean bill (D-046's shape) — calibration here is **constructed**:
:func:`calibration_census` builds a scratch package whose four predicates have
known behaviour, runs the real measurement against it, and requires all four
verdicts back.  That is D-060's move: a witness beats a reading.  The
test-surface gap is filed as a question, not papered over.

Known bounds on the reading
----------------------------

- **Fast half only.**  Same as :mod:`guard_vacuity`; a predicate that only sees
  its second answer under ``--slow`` scores one-sided here.  Reported by
  :attr:`Census.suite`.
- **Patchability.**  The recorder replaces attributes on modules and top-level
  classes.  A predicate nested deeper than that cannot be reached and is
  refused, not silently dropped — :func:`unpatchable` carries the set and its
  size.
- **Aliases.**  ``from m import pred`` binds before the recorder patches ``m``.
  The recorder therefore sweeps every loaded module for surviving references to
  each original function object and rebinds those too; what it cannot catch is
  an alias created *after* wrapping, which nothing in this package does.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

VERDICT_BOTH = "BOTH"
VERDICT_ALWAYS_TRUE = "ALWAYS_TRUE"
VERDICT_ALWAYS_FALSE = "ALWAYS_FALSE"
VERDICT_UNOBSERVED = "UNOBSERVED"
VERDICT_NON_BOOLEAN = "NON_BOOLEAN"

#: Package root scanned for predicates.  Tests inside it are not subjects.
PACKAGE = Path(__file__).resolve().parent

#: Directory names under :data:`PACKAGE` whose modules are not subjects.
EXCLUDED_DIRS = frozenset({"tests", "__pycache__"})

#: The suite run to produce the reading.  Fast half only — see the module
#: docstring's bounds.  Deliberately the same tuple :mod:`guard_vacuity` uses,
#: so the two censuses describe the same suite.
DEFAULT_SUITE = (
    "eval/mppi_sandbox/tests/",
    "eval/tests/test_path_tracking_metrics.py",
    "eval/tests/test_run_metrics.py",
)

#: Test files the census must **not** observe, as ``--ignore`` paths.
#:
#: D-060's lesson, applied before it could bite: this module's own tests call
#: its predicates with inputs chosen to exercise both answers.  A census that
#: watched them would score its own predicates ``BOTH`` for free — the
#: instrument eating its own signal, exactly as a census watching
#: :mod:`guard_witness` scores all 8 candidates ``FIRES``.
#:
#: :mod:`predicate_inputs` joins the list on the same ground: it is the second
#: instrument built out of this recorder, its tests call its predicates with
#: inputs chosen to be *diverse*, and diversity is precisely what it measures.
#: :mod:`exclusion_scope` joins on the same ground and then audits the list it
#: joined: its tests exercise its own predicates both ways by design, and its
#: whole finding is that a *file*-scoped entry hides more than its subject.  Its
#: own entry is inside its own measurement, which is the honest place for it.
EXCLUDED_TESTS = (
    "eval/mppi_sandbox/tests/test_exclusion_scope.py",
    "eval/mppi_sandbox/tests/test_guard_witness.py",
    "eval/mppi_sandbox/tests/test_predicate_inputs.py",
    "eval/mppi_sandbox/tests/test_predicate_vacuity.py",
)

#: Builtins whose call is a boolean by construction.
BOOL_BUILTINS = frozenset({"bool", "all", "any", "isinstance", "issubclass",
                           "callable", "hasattr"})

#: How a function got into the population.  Recorded because the two criteria
#: have different failure modes: shape over-admits (``arr > 0``), annotation
#: under-admits (nothing forces one to be written).
ADMIT_SHAPE = "shape"
ADMIT_ANNOTATION = "annotation"

KIND_FUNCTION = "function"
KIND_METHOD = "method"
KIND_PROPERTY = "property"


@dataclass(frozen=True)
class Predicate:
    """One boolean-returning function of the package."""

    module: str
    #: Dotted name within the module.  ``Class.method`` or ``func``.
    qualname: str
    kind: str
    lineno: int
    admitted_by: str
    #: Unparsed source of each ``return`` expression, for the report.
    returns: tuple[str, ...]
    path: Path

    @property
    def site(self) -> str:
        return f"{self.module}.{self.qualname}"

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return f"{self.site} ({self.kind}, by {self.admitted_by})"


@dataclass(frozen=True)
class Observation:
    """What the suite saw one predicate return."""

    site: str
    true_calls: int
    false_calls: int
    #: Type names of returned values that were not booleans, first seen first.
    other_types: tuple[str, ...] = ()

    @property
    def calls(self) -> int:
        return self.true_calls + self.false_calls + len(self.other_types)


@dataclass(frozen=True)
class Reading:
    """A predicate plus the verdict the suite's calls give it."""

    predicate: Predicate
    verdict: str
    observation: Observation | None

    @property
    def is_candidate(self) -> bool:
        """Called repeatedly and constant — the set Q-072 (b) asked for."""
        return self.verdict in (VERDICT_ALWAYS_TRUE, VERDICT_ALWAYS_FALSE)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        obs = self.observation
        counts = "" if obs is None else f"  [T={obs.true_calls} F={obs.false_calls}]"
        return f"{self.verdict:<13} {self.predicate}{counts}"


# --------------------------------------------------------------------------
# Population — derived from the AST, never typed
# --------------------------------------------------------------------------


def _boolean_shaped(node: ast.expr) -> bool:
    """Is this expression a boolean by syntax alone?

    Deliberately syntactic and deliberately over-admitting: ``arr > 0`` passes
    here and returns an array at runtime.  The ``NON_BOOLEAN`` verdict is what
    catches that, and it catches it by **execution** rather than by a cleverer
    predicate that would have its own blind spots.
    """
    if isinstance(node, ast.Compare):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return True
    if isinstance(node, ast.BoolOp):
        return all(_boolean_shaped(v) for v in node.values)
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return True
    if isinstance(node, ast.IfExp):
        return _boolean_shaped(node.body) and _boolean_shaped(node.orelse)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in BOOL_BUILTINS
    return False


def _annotated_bool(fn: ast.AST) -> bool:
    ann = getattr(fn, "returns", None)
    return isinstance(ann, ast.Name) and ann.id == "bool"


def _own_returns(fn: ast.AST) -> list[ast.Return]:
    """``return`` statements of ``fn`` itself, not of anything nested in it."""
    out: list[ast.Return] = []

    def walk(node: ast.AST):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, ast.Return):
                out.append(child)
            walk(child)

    walk(fn)
    return out


def _decorator_kind(fn: ast.AST) -> str | None:
    """``KIND_PROPERTY`` for a property, ``None`` for a plain def, else refuse.

    ``staticmethod``/``classmethod``/``cached_property`` and every third-party
    decorator change what lives in the class ``__dict__``, so the recorder
    cannot wrap them by the one mechanism it has.  Refusing by name keeps the
    refusal visible in :func:`unpatchable` instead of producing a silently
    unobserved site.
    """
    for dec in getattr(fn, "decorator_list", []):
        name = dec.id if isinstance(dec, ast.Name) else (
            dec.attr if isinstance(dec, ast.Attribute) else None)
        if name == "property":
            return KIND_PROPERTY
        return "REFUSED"
    return None


def _modules(package: Path = PACKAGE) -> list[Path]:
    return sorted(p for p in package.rglob("*.py")
                  if not (EXCLUDED_DIRS & set(p.relative_to(package).parts)))


def _scan(package: Path = PACKAGE) -> tuple[list[Predicate], list[str]]:
    """``(patchable, refused)`` — the population and what it could not reach."""
    found: list[Predicate] = []
    refused: list[str] = []
    for path in _modules(package):
        module = path.relative_to(package).with_suffix("").as_posix().replace("/", ".")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for owner, fn, reachable in _candidate_defs(tree):
            returns = _own_returns(fn)
            exprs = [r.value for r in returns if r.value is not None]
            if not exprs or len(exprs) != len(returns):
                continue  # a bare ``return`` mixed in — not a predicate
            by_shape = all(_boolean_shaped(e) for e in exprs)
            if not (by_shape or _annotated_bool(fn)):
                continue
            qualname = f"{owner}.{fn.name}" if owner else fn.name
            deco = _decorator_kind(fn)
            if deco == "REFUSED" or not reachable:
                refused.append(f"{module}.{qualname}")
                continue
            kind = deco or (KIND_METHOD if owner else KIND_FUNCTION)
            found.append(Predicate(
                module=module,
                qualname=qualname,
                kind=kind,
                lineno=fn.lineno,
                admitted_by=ADMIT_SHAPE if by_shape else ADMIT_ANNOTATION,
                returns=tuple(ast.unparse(e) for e in exprs),
                path=path,
            ))
    return found, refused


def _candidate_defs(tree: ast.Module):
    """``(owner, node, reachable)`` for defs at module level or one class deep.

    ``reachable`` is ``False`` for anything nested further — a closure or a
    method of a class defined inside a function.  Those are real predicates the
    recorder has no handle on, so they are yielded and refused rather than
    filtered out before anyone can count them.
    """
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield "", node, True
            yield from _nested(node, node.name)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield node.name, sub, True
                    yield from _nested(sub, f"{node.name}.{sub.name}")


def _nested(fn: ast.AST, prefix: str):
    for child in ast.walk(fn):
        if child is fn:
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield prefix, child, False


def predicates(package: Path = PACKAGE) -> tuple[Predicate, ...]:
    """Every reachable boolean-returning function, derived from the AST."""
    return tuple(_scan(package)[0])


def unpatchable(package: Path = PACKAGE) -> tuple[str, ...]:
    """Predicates the recorder cannot wrap — refused, and counted.

    Nested defs and decorated ones.  Their exclusion is a bound on the census,
    and a bound nobody wrote down is the thing D-045 through D-052 kept finding.
    """
    return tuple(sorted(_scan(package)[1]))


# --------------------------------------------------------------------------
# Measurement — a recorder installed into a subprocess suite run
# --------------------------------------------------------------------------

#: The plugin source in three pieces.  The middle one — what to record on each
#: call — is the only part that differs between this census and
#: :mod:`predicate_inputs`, which reads the *argument* distribution of the same
#: sites through the same patching machinery.  Split so that machinery has
#: exactly one statement of itself; :data:`_PLUGIN` below is unchanged by the
#: split, and :func:`_measure_scratch`'s textual substitution still applies to
#: the assembled whole.
_PLUGIN_PRELUDE = '''\
"""Generated recorder — wraps each site and dumps its observed values."""
import atexit, json, os, sys

SITES = json.loads(os.environ["PREDICATE_VACUITY_SITES"])
OUT = os.environ["PREDICATE_VACUITY_OUT"]
OBS = {}


'''

_PLUGIN_RECORD_VALUES = '''\
def _record(site, value):
    slot = OBS.setdefault(site, {"true": 0, "false": 0, "other": []})
    if value is True or value is False:
        slot["true" if value else "false"] += 1
        return
    name = type(value).__name__
    if name in ("bool_", "bool8"):  # numpy scalar booleans are booleans
        slot["true" if bool(value) else "false"] += 1
        return
    if name not in slot["other"]:
        slot["other"].append(name)


def _wrap(fn, site):
    def recorder(*a, **kw):
        out = fn(*a, **kw)
        _record(site, out)
        return out
    recorder.__name__ = getattr(fn, "__name__", "recorder")
    recorder.__doc__ = getattr(fn, "__doc__", None)
    recorder.__wrapped__ = fn
    return recorder


'''

_PLUGIN_INSTALL = '''\
def _rebind_aliases(original, wrapped):
    """Catch ``from m import pred`` bindings made before we patched ``m``."""
    for mod in list(sys.modules.values()):
        d = getattr(mod, "__dict__", None)
        if not isinstance(d, dict):
            continue
        for key, val in list(d.items()):
            if val is original:
                d[key] = wrapped


def _install():
    import importlib
    for module, qualname, kind, site in SITES:
        try:
            mod = importlib.import_module("eval.mppi_sandbox." + module)
        except Exception:
            continue
        parts = qualname.split(".")
        owner = mod
        for part in parts[:-1]:
            owner = getattr(owner, part, None)
            if owner is None:
                break
        if owner is None:
            continue
        attr = parts[-1]
        raw = owner.__dict__.get(attr) if hasattr(owner, "__dict__") else None
        if raw is None:
            continue
        if kind == "property":
            if not isinstance(raw, property) or raw.fget is None:
                continue
            setattr(owner, attr, property(_wrap(raw.fget, site),
                                          raw.fset, raw.fdel, raw.__doc__))
        elif callable(raw):
            wrapped = _wrap(raw, site)
            setattr(owner, attr, wrapped)
            _rebind_aliases(raw, wrapped)


'''

#: How the reading leaves the subprocess.  Split from the install half because
#: :mod:`predicate_inputs` accumulates a ``set`` that JSON cannot carry and so
#: needs its own serializer — and because ``atexit`` is LIFO, a second
#: registration here would clobber whatever the other census had just written.
_PLUGIN_DUMP = '''\
def _dump():
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(OBS, fh)


_install()
atexit.register(_dump)


def pytest_sessionfinish(session, exitstatus):  # pragma: no cover - in subprocess
    _dump()
'''

#: The value-recording plugin, assembled.  Byte-identical to what stood here
#: before the split — the seams are internal.
_PLUGIN = (_PLUGIN_PRELUDE + _PLUGIN_RECORD_VALUES + _PLUGIN_INSTALL
           + _PLUGIN_DUMP)


def _sites_payload(population: Iterable[Predicate]) -> str:
    return json.dumps([[p.module, p.qualname, p.kind, p.site] for p in population])


def measure(population: Sequence[Predicate],
            suite: Sequence[str] = DEFAULT_SUITE,
            root: Path | None = None,
            excluded: Sequence[str] = EXCLUDED_TESTS,
            timeout: int = 900) -> dict[str, Observation]:
    """Run ``suite`` with the recorder installed; return per-site observations.

    A subprocess for the same reason :func:`guard_vacuity.measure` uses one: the
    suite imports the modules under measurement, so an in-process install would
    race whatever the parent already imported.
    """
    root = root or PACKAGE.parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "predicate_vacuity_plugin.py").write_text(_PLUGIN, encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = _sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(tmpdir), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        subprocess.run(
            [sys.executable, "-m", "pytest", *suite,
             *(f"--ignore={p}" for p in excluded),
             "-p", "predicate_vacuity_plugin", "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=timeout, check=False,
            env=env,
        )
        if not out.exists():
            return {}
        raw = json.loads(out.read_text(encoding="utf-8"))
    return {site: Observation(site=site,
                              true_calls=slot["true"],
                              false_calls=slot["false"],
                              other_types=tuple(slot["other"]))
            for site, slot in raw.items()}


def classify(population: Iterable[Predicate],
             observations: dict[str, Observation]) -> tuple[Reading, ...]:
    """Score each predicate against what the suite saw it return.

    Pure — the suite run is :func:`measure`'s job.  Kept separate so the
    partition's semantics are testable without one.
    """
    out = []
    for pred in population:
        obs = observations.get(pred.site)
        if obs is None or obs.calls == 0:
            verdict = VERDICT_UNOBSERVED
        elif obs.other_types:
            verdict = VERDICT_NON_BOOLEAN
        elif obs.true_calls and obs.false_calls:
            verdict = VERDICT_BOTH
        elif obs.true_calls:
            verdict = VERDICT_ALWAYS_TRUE
        else:
            verdict = VERDICT_ALWAYS_FALSE
        out.append(Reading(predicate=pred, verdict=verdict, observation=obs))
    return tuple(out)


@dataclass(frozen=True)
class Census:
    """The partition, plus the bounds it was taken under."""

    readings: tuple[Reading, ...]
    refused: tuple[str, ...]
    suite: tuple[str, ...]

    def of(self, verdict: str) -> tuple[Reading, ...]:
        return tuple(r for r in self.readings if r.verdict == verdict)

    @property
    def candidates(self) -> tuple[Reading, ...]:
        return tuple(r for r in self.readings if r.is_candidate)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        counts = " ".join(
            f"{v}={len(self.of(v))}"
            for v in (VERDICT_BOTH, VERDICT_ALWAYS_TRUE, VERDICT_ALWAYS_FALSE,
                      VERDICT_UNOBSERVED, VERDICT_NON_BOOLEAN))
        return (f"{len(self.readings)} boolean predicates ({counts}); "
                f"{len(self.refused)} refused as unpatchable")


def census(package: Path = PACKAGE,
           suite: Sequence[str] = DEFAULT_SUITE,
           observations: dict[str, Observation] | None = None) -> Census:
    """Discover, measure, partition.  Pass ``observations`` to skip the run."""
    population, refused = _scan(package)
    obs = measure(population, suite) if observations is None else observations
    return Census(readings=classify(population, obs),
                  refused=tuple(sorted(refused)),
                  suite=tuple(suite))


def one_sided(cens: Census) -> tuple[Reading, ...]:
    """The candidate set: called, and constant across every call.

    Candidates, not findings — one-sidedness is necessary for D-057's shape and
    not sufficient.  Confirming one is D-058's move and cannot be done by
    counting.
    """
    return cens.candidates


def by_evidence(readings: Iterable[Reading]) -> tuple[Reading, ...]:
    """Candidates ordered by how many times the suite made the call, descending.

    The ordering *is* the reading — see the module docstring.  A one-sided
    predicate with one call is a statement about the suite's coverage; the same
    verdict at four figures is a statement about the predicate.  No floor is
    imposed, because none has been justified.
    """
    return tuple(sorted(readings,
                        key=lambda r: (-(r.observation.calls if r.observation
                                         else 0), r.predicate.site)))


# --------------------------------------------------------------------------
# Calibration — constructed, because the historical registry would be empty
# --------------------------------------------------------------------------

#: The scratch package :func:`calibration_census` measures: four predicates
#: whose verdicts are known by construction, plus the suite that exercises them.
CALIBRATION_SOURCES = {
    "subject.py": '''\
        def always_true(x) -> bool:
            return x >= 0

        def always_false(x) -> bool:
            return x > 1000

        def both(x) -> bool:
            return x > 5

        def unobserved(x) -> bool:
            return x < 0
        ''',
    "tests/test_subject.py": '''\
        from subject import always_true, always_false, both

        def test_calls():
            for x in (0, 1, 7, 9):
                assert always_true(x) or True
                assert always_false(x) or True
                assert both(x) or True
        ''',
}

#: What the instrument must report for each scratch predicate.  A *witness* set
#: rather than a registry of past findings — D-060's move, applied to a scan
#: whose historical calibration set is genuinely 0.
CALIBRATION_EXPECTED = {
    "subject.always_true": VERDICT_ALWAYS_TRUE,
    "subject.always_false": VERDICT_ALWAYS_FALSE,
    "subject.both": VERDICT_BOTH,
    "subject.unobserved": VERDICT_UNOBSERVED,
}


def calibration_census(root: Path) -> Census:
    """Build the scratch package under ``root`` and measure it for real.

    Uses the production :func:`measure` — same subprocess, same recorder, same
    patching mechanism — so a green calibration is evidence about the shipped
    path and not about a parallel one.
    """
    for rel, body in CALIBRATION_SOURCES.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(textwrap.dedent(body), encoding="utf-8")
    population, refused = _scan(root)
    # The scratch tree is imported as a top-level ``subject``, not as a
    # submodule of the sandbox, so the recorder's import prefix is stripped.
    obs = _measure_scratch(population, root)
    return Census(readings=classify(population, obs),
                  refused=tuple(sorted(refused)),
                  suite=("tests/",))


def _measure_scratch(population: Sequence[Predicate], root: Path
                     ) -> dict[str, Observation]:
    """:func:`measure` against a scratch tree whose modules are top-level."""
    plugin = _PLUGIN.replace('"eval.mppi_sandbox." + module', "module")
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "predicate_vacuity_plugin.py").write_text(plugin, encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = _sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join([str(tmpdir), str(root)])
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-p",
             "predicate_vacuity_plugin", "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=300, check=False,
            env=env,
        )
        if not out.exists():
            return {}
        raw = json.loads(out.read_text(encoding="utf-8"))
    return {site: Observation(site=site, true_calls=slot["true"],
                              false_calls=slot["false"],
                              other_types=tuple(slot["other"]))
            for site, slot in raw.items()}


def miscalibrated(cens: Census) -> tuple[str, ...]:
    """Scratch predicates the instrument scores wrongly — pinned empty.

    The mirror over :data:`CALIBRATION_EXPECTED`.  Unlike a registry of past
    findings, this one cannot silently read clean by being empty: every member
    is constructed, so an absent member is itself a failure.
    """
    by_site = {r.predicate.site: r for r in cens.readings}
    out = []
    for site, expected in sorted(CALIBRATION_EXPECTED.items()):
        found = by_site.get(site)
        if found is None:
            out.append(f"{site} — not discovered by the scan")
        elif found.verdict != expected:
            out.append(f"{site} — {found.verdict}, expected {expected}")
    return tuple(out)


def report(cens: Census) -> str:  # pragma: no cover - reporting sugar
    lines = [str(cens), ""]
    for reading in by_evidence(cens.candidates):
        lines.append(f"  {reading}")
    non_bool = cens.of(VERDICT_NON_BOOLEAN)
    if non_bool:
        lines.append("")
        lines.append(f"  ({len(non_bool)} NON_BOOLEAN — admitted by shape, "
                     f"returns something else)")
        lines.extend(f"    {r.predicate.site} → "
                     f"{', '.join(r.observation.other_types)}" for r in non_bool)
    unobserved = cens.of(VERDICT_UNOBSERVED)
    if unobserved:
        lines.append("")
        lines.append(f"  ({len(unobserved)} UNOBSERVED — never called; "
                     f"silence uninformative)")
    if cens.refused:
        lines.append("")
        lines.append(f"  ({len(cens.refused)} refused as unpatchable)")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report(census()))
