"""How many *distinct* questions did the suite ask each predicate? — Q-074 (c).

D-061 measured the return-value distribution of every boolean predicate in the
package and ordered the one-sided ones by call count, on the stated reasoning
that ``ALWAYS_FALSE`` after one call and ``ALWAYS_FALSE`` after 5694 are the
same verdict and nothing like the same claim.  That reasoning is right and the
statistic it picked is wrong, for a reason this module measures rather than
argues:

    a call count counts *answers*.  What makes a one-sided predicate damning is
    that the suite offered it a **population** and it declined every member —
    and the size of that population is the number of **distinct inputs**, not
    the number of calls.  5694 calls carrying one argument is one question asked
    5694 times.

Q-074 is where this came from.  Both vacuity scans exclude ``tests/`` from their
population, so the finding that motivated the whole search — D-057's
``unseen.min() > 0.0``, an assertion that passed on empty worlds because a
renderer floor of 112 corner cells sat under it — is structurally invisible to
them, and D-061 shipped with a calibration set of exactly 0 as a result.  Q-074
weighed three ways out and leaned (c): don't try to read the assert, read the
**argument distribution of the subject predicates the tests call**.  D-057's
real defect was never the bar.  It was that the bar was only ever evaluated on
one kind of scene.  That is a statement about inputs, and this is the instrument
for it.

What it shares with D-061 and what it does not
-----------------------------------------------

Same population (:func:`predicate_vacuity.predicates`), same patching recorder,
same subprocess suite, same excluded tests — the two censuses describe the same
suite by construction, so their readings can be joined per site.  The only
difference is what the wrapper writes down: values there, a **fingerprint of the
arguments** here.

No threshold, and 1 is not one
-------------------------------

:mod:`predicate_vacuity` declined to pick a floor separating "recited" from
"barely called", because an unjustified constant is the fourth of its kind in
this package.  That restraint holds here and costs nothing, because the split
that carries the finding is **degenerate rather than chosen**: a predicate whose
arguments never varied was asked one question.  ``distinct == 1`` is not a
threshold, it is the boundary of the concept.  Everything above it is reported
as a count and left ungraded, exactly as D-061 left the call count.

The fingerprint, and which way it is wrong
-------------------------------------------

Arguments are fingerprinted by a bounded, deterministic summary: numpy arrays by
``(shape, dtype, content hash)``, everything else by a truncated ``repr`` with a
type-name fallback.  Both directions of error exist and they are not symmetric,
which is the point:

- An object with no value-based ``__repr__`` renders as ``<C object at 0x…>``,
  so two *equal* instances fingerprint **differently**.  This **over**-counts
  distinct inputs.
- A ``repr`` longer than :data:`REPR_LIMIT` is truncated, so two values agreeing
  on their first 200 characters collide.  This **under**-counts.

The first dominates in this package (bound methods, live objects, and the
``self`` of every non-dataclass receiver all render with addresses), and it
biases the mechanism **against** the finding this module exists to make.  A site
that still reads ``distinct == 1`` reached that verdict through a fingerprint
trying to inflate it, which makes the reading strong.  A *high* distinct count
on an address-repr site says nothing at all — so :attr:`InputObservation.
address_reprs` records whether any fingerprint at that site carried an address,
and the report flags those readings as uninformative-when-high rather than
quietly ranking them.

Candidates, not findings — unchanged
-------------------------------------

``SINGLE_INPUT`` is a necessary condition for the D-057 shape and not a
sufficient one.  A predicate of no arguments has exactly one possible input and
is not thereby defective; a predicate called once trivially has one.  What the
join with D-061's census buys is the conjunction — one-sided **and** asked one
question — and confirming a member of that set is still D-058's move: work out
what the callers guarantee, then show the other answer is unreachable.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from eval.mppi_sandbox import predicate_vacuity as pv
from eval.mppi_sandbox import suite_memo
from eval.mppi_sandbox.predicate_vacuity import Predicate
from .nested_suite_cost import NESTED_TIMEOUT_SECONDS

#: How many characters of an argument's ``repr`` enter its fingerprint.  Beyond
#: this the summary truncates, which collides distinct values — see the module
#: docstring for why that direction of error is the rarer one here.
REPR_LIMIT = 200

VERDICT_SINGLE_INPUT = "SINGLE_INPUT"
VERDICT_MANY_INPUTS = "MANY_INPUTS"
VERDICT_UNOBSERVED = "UNOBSERVED"


@dataclass(frozen=True)
class InputObservation:
    """What the suite fed one predicate."""

    site: str
    calls: int
    #: Number of distinct argument fingerprints seen.
    distinct: int
    #: Whether any fingerprint at this site carried a memory address, meaning
    #: :attr:`distinct` is inflated by identity and a high value is uninformative.
    address_reprs: bool = False
    #: Up to :data:`_SAMPLE` fingerprints, for the report.  First seen first.
    sample: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputSlice:
    """One test file's share of what a predicate was asked (D-066).

    The per-origin unit :func:`measure_attributed` records.  It carries the
    **set** of fingerprint digests rather than a distinct *count*, because a
    count does not fold: distinct inputs union across files, and two origins
    that asked the same question contribute one between them.
    """

    calls: int
    digests: frozenset[str]
    address_reprs: bool = False
    sample: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputReading:
    """A predicate plus how many distinct questions the suite asked it."""

    predicate: Predicate
    verdict: str
    observation: InputObservation | None

    @property
    def is_single(self) -> bool:
        return self.verdict == VERDICT_SINGLE_INPUT

    @property
    def informative(self) -> bool:
        """Does this reading's :attr:`distinct` mean what it says?

        ``SINGLE_INPUT`` always does — an address-based fingerprint can only
        push a site *out* of it.  ``MANY_INPUTS`` does only when no address
        repr contributed, since otherwise the count may be counting instances.
        """
        obs = self.observation
        if obs is None or self.verdict == VERDICT_UNOBSERVED:
            return False
        return self.is_single or not obs.address_reprs

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        obs = self.observation
        detail = "" if obs is None else (
            f"  [{obs.distinct} distinct / {obs.calls} calls"
            + ("; addr" if obs.address_reprs else "") + "]")
        return f"{self.verdict:<13} {self.predicate.site}{detail}"


# --------------------------------------------------------------------------
# Measurement — the D-061 recorder with a different thing written down
# --------------------------------------------------------------------------

_SAMPLE = 3

#: Swaps into :data:`predicate_vacuity._PLUGIN_RECORD_VALUES`.  The install,
#: alias-rebinding and dump halves are imported verbatim from there, so the two
#: censuses cannot drift apart in how they reach a site.
#:
#: One difference from D-061's recorder is deliberate and shows up in the
#: counts: this one writes the fingerprint down **before** calling through, so a
#: call that raises still counts as a question asked.  ``InputObservation.calls``
#: is therefore ``>=`` the matching ``Observation.calls``, and the join in
#: :func:`recited` is by site rather than by total for that reason.
#: The fingerprint half — the constants and :func:`_fp_one`, which both tallies
#: need.  Split from the tally at a line boundary so :data:`_PLUGIN_RECORD_INPUTS`
#: below reassembles byte-identical to the single constant that stood here for
#: D-062 through D-065; the seam exists because the per-origin recorder (D-066)
#: needs to replace the *tally* and nothing else, exactly as
#: :data:`predicate_vacuity._PLUGIN_TALLY_ATTRIBUTED` does for the value census.
_PLUGIN_FINGERPRINT_INPUTS = '''\
_SAMPLE = __SAMPLE__
_REPR_LIMIT = __REPR_LIMIT__


def _fp_one(value):
    """Bounded, deterministic summary of one argument."""
    shape = getattr(value, "shape", None)
    if shape is not None and hasattr(value, "dtype") and hasattr(value, "tobytes"):
        try:
            import hashlib
            digest = hashlib.blake2b(value.tobytes(), digest_size=8).hexdigest()
            return "arr(%s,%s,%s)" % (shape, value.dtype, digest)
        except Exception:
            return "arr(%s,%s,?)" % (shape, getattr(value, "dtype", "?"))
    try:
        text = repr(value)
    except Exception:
        return "<repr-failed %s>" % type(value).__name__
    return text[:_REPR_LIMIT]


'''

#: The tally half — one flat slot per site, summed over the whole run.
_PLUGIN_TALLY_INPUTS = '''\
def _record(site, args, kwargs):
    slot = OBS.setdefault(
        site, {"calls": 0, "fps": [], "distinct": 0, "addr": False, "seen": set()})
    parts = [_fp_one(a) for a in args]
    parts += ["%s=%s" % (k, _fp_one(v)) for k, v in sorted(kwargs.items())]
    fp = "(" + ", ".join(parts) + ")"
    slot["calls"] += 1
    if " object at 0x" in fp or " method of " in fp or " at 0x" in fp:
        slot["addr"] = True
    if fp not in slot["seen"]:
        slot["seen"].add(fp)
        slot["distinct"] += 1
        if len(slot["fps"]) < _SAMPLE:
            slot["fps"].append(fp)


'''

#: The wrap half — shared verbatim by both tallies.
_PLUGIN_WRAP_INPUTS = '''\
def _wrap(fn, site):
    def recorder(*a, **kw):
        _record(site, a, kw)
        return fn(*a, **kw)
    recorder.__name__ = getattr(fn, "__name__", "recorder")
    recorder.__doc__ = getattr(fn, "__doc__", None)
    recorder.__wrapped__ = fn
    return recorder


'''

#: Reassembled from the three halves — byte-identical to the single constant
#: that stood here for D-062 through D-065.  Asserted by a test, not by this
#: comment.
_PLUGIN_RECORD_INPUTS = (_PLUGIN_FINGERPRINT_INPUTS + _PLUGIN_TALLY_INPUTS
                         + _PLUGIN_WRAP_INPUTS)

#: The tally half again, keyed by **which test file was running**.
#:
#: The value census could partition a *sum* by origin and re-add it (D-064).  A
#: distinct-input count is a **union**, not a sum, so a per-origin count cannot
#: be re-added: two files that ask the same question contribute one distinct
#: input between them, and no pair of counts says whether they did.  What
#: reconstructs is the *set*, so this records one per origin — as blake2b
#: digests of the fingerprint, because the fingerprints themselves are up to
#: :data:`REPR_LIMIT` characters each and the union at the busiest site runs to
#: four figures.
#:
#: The digest is a third place a collision can under-count, after truncation and
#: after the ``repr``.  At 8 bytes over ~3k fingerprints the birthday load is
#: ~2e-13, which is small next to the truncation collisions the module docstring
#: already declares — and it errs in the direction that *deflates* a distinct
#: count, i.e. toward the ``SINGLE_INPUT`` finding, which is why
#: :func:`digest_collisions` checks it against the flat census rather than
#: asserting it away.
_PLUGIN_TALLY_INPUTS_ATTRIBUTED = '''\
import hashlib as _hashlib

CURRENT = [""]


def pytest_collectstart(collector):  # pragma: no cover - in subprocess
    nodeid = getattr(collector, "nodeid", "") or ""
    if nodeid.endswith(".py"):
        CURRENT[0] = nodeid


def pytest_runtest_logstart(nodeid, location):  # pragma: no cover - in subprocess
    CURRENT[0] = nodeid.split("::")[0]


def _record(site, args, kwargs):
    per = OBS.setdefault(site, {})
    slot = per.setdefault(
        CURRENT[0], {"calls": 0, "fps": [], "addr": False, "seen": set()})
    parts = [_fp_one(a) for a in args]
    parts += ["%s=%s" % (k, _fp_one(v)) for k, v in sorted(kwargs.items())]
    fp = "(" + ", ".join(parts) + ")"
    slot["calls"] += 1
    if " object at 0x" in fp or " method of " in fp or " at 0x" in fp:
        slot["addr"] = True
    digest = _hashlib.blake2b(fp.encode("utf-8", "replace"),
                              digest_size=8).hexdigest()
    if digest not in slot["seen"]:
        slot["seen"].add(digest)
        if len(slot["fps"]) < _SAMPLE:
            slot["fps"].append(fp)


'''

#: ``seen`` is a ``set`` and JSON cannot carry one, so the dump drops it.  This
#: replaces :data:`predicate_vacuity._PLUGIN_DUMP` rather than following it —
#: two registrations would fight over the same output file at exit.
_PLUGIN_DUMP_INPUTS = '''\
def _dump():
    payload = {k: {"calls": v["calls"], "distinct": v["distinct"],
                   "addr": v["addr"], "fps": v["fps"]}
               for k, v in OBS.items()}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


_install()
atexit.register(_dump)


def pytest_sessionfinish(session, exitstatus):  # pragma: no cover - in subprocess
    _dump()
'''


#: The per-origin dump.  ``seen`` is the reading here rather than a scratch set,
#: so unlike :data:`_PLUGIN_DUMP_INPUTS` this one **serializes** it — sorted, so
#: the payload is deterministic and a diff of two runs is readable.
_PLUGIN_DUMP_INPUTS_ATTRIBUTED = '''\
def _dump():
    payload = {site: {origin: {"calls": v["calls"], "addr": v["addr"],
                               "fps": v["fps"], "seen": sorted(v["seen"])}
                      for origin, v in per.items()}
               for site, per in OBS.items()}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


_install()
atexit.register(_dump)


def pytest_sessionfinish(session, exitstatus):  # pragma: no cover - in subprocess
    _dump()
'''


def plugin_source(sample: int = _SAMPLE, repr_limit: int = REPR_LIMIT) -> str:
    """The generated recorder, assembled from D-061's install machinery.

    Token substitution rather than ``str.format`` — the body is full of dict
    literals, and a format string cannot hold a brace it does not mean.
    """
    record = (_PLUGIN_RECORD_INPUTS
              .replace("__SAMPLE__", str(int(sample)))
              .replace("__REPR_LIMIT__", str(int(repr_limit))))
    return (pv._PLUGIN_PRELUDE + record + pv._PLUGIN_INSTALL
            + _PLUGIN_DUMP_INPUTS)


def plugin_source_attributed(sample: int = _SAMPLE,
                             repr_limit: int = REPR_LIMIT) -> str:
    """:func:`plugin_source` with the per-origin tally swapped in.

    Fingerprint, wrap, install and prelude are the *same objects* the flat
    recorder uses, so the two censuses cannot drift apart in how they reach a
    site or in what they consider one question — which is the only reason
    :func:`fold_inputs`'s reconstruction is comparable to a measured run.
    """
    record = ((_PLUGIN_FINGERPRINT_INPUTS + _PLUGIN_TALLY_INPUTS_ATTRIBUTED
               + _PLUGIN_WRAP_INPUTS)
              .replace("__SAMPLE__", str(int(sample)))
              .replace("__REPR_LIMIT__", str(int(repr_limit))))
    return (pv._PLUGIN_PRELUDE + record + pv._PLUGIN_INSTALL
            + _PLUGIN_DUMP_INPUTS_ATTRIBUTED)


def measure(population: Sequence[Predicate],
            suite: Sequence[str] = pv.DEFAULT_SUITE,
            root: Path | None = None,
            excluded: Sequence[str] = pv.EXCLUDED_TESTS,
            timeout: int = NESTED_TIMEOUT_SECONDS) -> dict[str, InputObservation]:
    """Run ``suite`` with the argument recorder installed.

    A subprocess for :func:`predicate_vacuity.measure`'s reason: the suite
    imports the modules under measurement, so an in-process install would race
    whatever the parent already imported.
    """
    return _observations(_run_recorder(plugin_source(), population, suite, root,
                                       excluded, timeout))


def _run_recorder(plugin: str, population: Sequence[Predicate],
                  suite: Sequence[str], root: Path | None,
                  excluded: Sequence[str], timeout: int) -> dict:
    """Write ``plugin``, run ``suite`` under it, return the raw payload.

    Shared by :func:`measure` and :func:`measure_attributed` so the two differ
    only in the plugin text and in how the result is shaped — the same seam
    :func:`predicate_vacuity._run_recorder` has for the value census.

    Memoised on the effective command exactly as that one is; the ledger found
    **13 of the 18** nested runs on this module's side of the pair.
    """
    root = root or pv.PACKAGE.parent.parent
    command = suite_memo.Command(
        argv=tuple(_recorder_argv(suite, excluded)),
        cwd=str(root),
        plugin_digest=suite_memo.digest_text(plugin),
        payload_digest=suite_memo.digest_text(pv._sites_payload(population)),
    )
    raw = suite_memo.run_once(
        command,
        lambda: _spawn_recorder(plugin, population, suite, root, excluded,
                                timeout),
    )
    # The ``None``/``{}`` distinction is the memo's business, not the callers':
    # they have always read "no observations" off an empty mapping.
    return {} if raw is None else raw


def _recorder_argv(suite: Sequence[str], excluded: Sequence[str]) -> list[str]:
    return [sys.executable, "-m", "pytest", *suite,
            *(f"--ignore={p}" for p in excluded),
            "-p", "predicate_inputs_plugin", "-q", "-p", "no:cacheprovider"]


def _spawn_recorder(plugin: str, population: Sequence[Predicate],
                    suite: Sequence[str], root: Path,
                    excluded: Sequence[str], timeout: int) -> dict:
    """The run itself — one nested pytest, uncached."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "predicate_inputs_plugin.py").write_text(plugin, encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = pv._sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(tmpdir), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        subprocess.run(
            _recorder_argv(suite, excluded),
            cwd=root, capture_output=True, text=True, timeout=timeout,
            check=False, env=env,
        )
        if not out.exists():
            return None  # the run did not complete; not a reading of nothing
        return json.loads(out.read_text(encoding="utf-8"))


def measure_attributed(population: Sequence[Predicate],
                       suite: Sequence[str] = pv.DEFAULT_SUITE,
                       root: Path | None = None,
                       excluded: Sequence[str] = (),
                       timeout: int = NESTED_TIMEOUT_SECONDS,
                       ) -> dict[str, dict[str, InputSlice]]:
    """As :func:`measure`, but each site's record is split by test file.

    ``site -> origin -> InputSlice``.  ``excluded`` defaults to **empty** for
    :func:`predicate_vacuity.measure_attributed`'s reason: the point of the
    per-origin record is to run once with nothing hidden and reconstruct the
    hidden readings, and passing an exclusion here throws that away.

    This is the run D-065 declared and did not buy.  Its bound was that the
    survivors' distinct counts were still read under
    :data:`predicate_vacuity.EXCLUDED_TESTS`, so a survivor whose questions came
    only from an excluded file was under-counted.  One run of this answers it
    for *every* subset of the list at once.
    """
    raw = _run_recorder(plugin_source_attributed(), population, suite, root,
                        excluded, timeout)
    return {site: {origin: InputSlice(calls=slot["calls"],
                                      digests=frozenset(slot["seen"]),
                                      address_reprs=bool(slot["addr"]),
                                      sample=tuple(slot["fps"]))
                   for origin, slot in per.items()}
            for site, per in raw.items()}


def fold_inputs(attributed: dict[str, dict[str, InputSlice]],
                hidden: Sequence[str] = ()) -> dict[str, InputObservation]:
    """Sum a per-origin record back to :func:`measure`'s shape.

    ``hidden`` names origins to drop — the counterfactual "as if these files had
    been ``--ignore``-d".  Calls add and ``address_reprs`` ors, but ``distinct``
    is the size of the **union** of the surviving origins' digest sets, which is
    the whole reason the slices carry sets rather than counts: two files asking
    the same question contribute one distinct input between them.

    A site left with no calls is omitted, so :func:`classify` scores it
    ``UNOBSERVED`` exactly as an absent site.
    """
    drop = set(hidden)
    out: dict[str, InputObservation] = {}
    for site, per in attributed.items():
        calls = 0
        digests: set[str] = set()
        addr = False
        sample: list[str] = []
        for origin, sl in sorted(per.items()):
            if origin in drop:
                continue
            calls += sl.calls
            digests |= sl.digests
            addr = addr or sl.address_reprs
            sample.extend(f for f in sl.sample if f not in sample)
        if calls:
            out[site] = InputObservation(site=site, calls=calls,
                                         distinct=len(digests),
                                         address_reprs=addr,
                                         sample=tuple(sample[:_SAMPLE]))
    return out


def _observations(raw: dict) -> dict[str, InputObservation]:
    return {site: InputObservation(site=site, calls=slot["calls"],
                                   distinct=slot["distinct"],
                                   address_reprs=bool(slot["addr"]),
                                   sample=tuple(slot["fps"]))
            for site, slot in raw.items()}


def classify(population: Iterable[Predicate],
             observations: dict[str, InputObservation]
             ) -> tuple[InputReading, ...]:
    """Score each predicate by how many distinct inputs the suite supplied.

    Pure — the suite run is :func:`measure`'s job, kept separate so the
    partition's semantics are testable without one.
    """
    out = []
    for pred in population:
        obs = observations.get(pred.site)
        if obs is None or obs.calls == 0:
            verdict = VERDICT_UNOBSERVED
        elif obs.distinct == 1:
            verdict = VERDICT_SINGLE_INPUT
        else:
            verdict = VERDICT_MANY_INPUTS
        out.append(InputReading(predicate=pred, verdict=verdict,
                                observation=obs))
    return tuple(out)


@dataclass(frozen=True)
class InputCensus:
    """The partition, plus the bounds it was taken under."""

    readings: tuple[InputReading, ...]
    refused: tuple[str, ...]
    suite: tuple[str, ...]

    def of(self, verdict: str) -> tuple[InputReading, ...]:
        return tuple(r for r in self.readings if r.verdict == verdict)

    @property
    def single_input(self) -> tuple[InputReading, ...]:
        return tuple(r for r in self.readings if r.is_single)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        counts = " ".join(f"{v}={len(self.of(v))}" for v in
                          (VERDICT_SINGLE_INPUT, VERDICT_MANY_INPUTS,
                           VERDICT_UNOBSERVED))
        inflated = sum(1 for r in self.of(VERDICT_MANY_INPUTS)
                       if not r.informative)
        return (f"{len(self.readings)} boolean predicates ({counts}); "
                f"{inflated} MANY_INPUTS inflated by address reprs; "
                f"{len(self.refused)} refused as unpatchable")


def census(package: Path = pv.PACKAGE,
           suite: Sequence[str] = pv.DEFAULT_SUITE,
           observations: dict[str, InputObservation] | None = None
           ) -> InputCensus:
    """Discover, measure, partition.  Pass ``observations`` to skip the run."""
    population, refused = pv._scan(package)
    obs = measure(population, suite) if observations is None else observations
    return InputCensus(readings=classify(population, obs),
                       refused=tuple(sorted(refused)),
                       suite=tuple(suite))


# --------------------------------------------------------------------------
# The join — where D-061's ordering was reading the wrong number
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Recited:
    """A one-sided predicate the suite asked exactly one question.

    The conjunction Q-074 (c) was after: D-061 says the answer never varied,
    this says neither did the question.  The call count, which D-061 led with,
    is then an artifact of *where the callers sit* rather than evidence about
    the predicate — which is the thing to know before spending a witness on it.
    """

    site: str
    verdict: str
    calls: int
    distinct: int
    sample: tuple[str, ...] = ()


def recited(vacuity: pv.Census, inputs: InputCensus) -> tuple[Recited, ...]:
    """One-sided **and** single-input, ordered by the call count they refute.

    Both censuses run the same population over the same suite, so the join is
    by site and total.  Ordering by ``calls`` descending is deliberate: the
    head of this list is exactly where D-061's report led, and each member is a
    site whose four-figure evidence was one question repeated.
    """
    by_site = {r.predicate.site: r for r in inputs.readings}
    out = []
    for reading in vacuity.candidates:
        seen = by_site.get(reading.predicate.site)
        if seen is None or not seen.is_single:
            continue
        obs = seen.observation
        out.append(Recited(site=reading.predicate.site,
                           verdict=reading.verdict,
                           calls=obs.calls if obs else 0,
                           distinct=obs.distinct if obs else 0,
                           sample=obs.sample if obs else ()))
    return tuple(sorted(out, key=lambda r: (-r.calls, r.site)))


# --------------------------------------------------------------------------
# Is the reconstruction band stationary? — D-066's undecided residual
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Drift:
    """One site's distinct count across two **independent** flat censuses.

    D-066 compared a folded per-origin record against a measured run and found
    7 of 53 sites disagreeing, by at most 0.487 %.  It could name two causes and
    separate neither: a biased fold, or fingerprints that simply do not repeat
    across processes.  The sign eliminated the digest and nothing else.

    This is the control that decides it, and its whole point is that **the fold
    does not appear in it**.  Two runs of :func:`measure`, same tree, same
    exclusion, two processes; any site that moves here moves for reasons the
    reconstruction cannot be blamed for.  A site that is *stationary* here and
    still disagrees under the fold is a site where the fold is the only
    remaining suspect.
    """

    site: str
    first: int
    second: int
    calls_first: int
    calls_second: int
    address_reprs: bool

    @property
    def delta(self) -> int:
        return self.second - self.first

    @property
    def stationary(self) -> bool:
        """Did the distinct count repeat exactly?"""
        return self.first == self.second

    @property
    def calls_stationary(self) -> bool:
        """Did the *call* count repeat exactly?

        Reported separately because it is the load-bearing half of the
        interpretation: calls are a sum over executions and carry no
        fingerprint, so a suite that re-runs identically must reproduce them.
        Calls moving too would mean the two runs did not do the same work, and
        then nothing else here is about fingerprints at all.
        """
        return self.calls_first == self.calls_second

    @property
    def movement(self) -> int:
        """How far the site moved, unsigned.

        The name :func:`exclusion_scope.attribute_two_frame` grades on, shared
        with :class:`Spread` so that a k-run control and a 2-run one can be read
        by the same grader.  For a pair it is the absolute delta; for k runs it
        is the span, and the two coincide at k=2.
        """
        return abs(self.delta)

    @property
    def relative(self) -> float:
        base = max(self.first, self.second)
        return abs(self.delta) / base if base else 0.0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.site:<46} {self.first:>7} → {self.second:<7} "
                f"({self.delta:+d}, {self.relative:.3%})"
                + ("  addr" if self.address_reprs else ""))


def drift(first: dict[str, InputObservation],
          second: dict[str, InputObservation]) -> tuple[Drift, ...]:
    """Per-site comparison of two independent flat censuses.

    Every site observed by *either* run is returned, moving or not, so that
    :func:`fold_implicated` can ask "was this site stationary?" and get an
    answer rather than a missing key — an absent site is indistinguishable from
    a stable one otherwise, and that is exactly the confusion this control
    exists to remove.
    """
    out = []
    for site in sorted(set(first) | set(second)):
        a = first.get(site)
        b = second.get(site)
        out.append(Drift(site=site,
                         first=a.distinct if a else 0,
                         second=b.distinct if b else 0,
                         calls_first=a.calls if a else 0,
                         calls_second=b.calls if b else 0,
                         address_reprs=bool((a and a.address_reprs)
                                            or (b and b.address_reprs))))
    return tuple(out)


def unstable(drifts: Iterable[Drift]) -> tuple[Drift, ...]:
    """The sites whose distinct count did not repeat."""
    return tuple(d for d in drifts if not d.stationary)


def drift_band(drifts: Iterable[Drift]) -> float:
    """Worst relative movement across the pair — the measurement's own band.

    The number D-066's 0.487 % has to be read against.  If this is of the same
    order, that band was never a property of the reconstruction.
    """
    return max((d.relative for d in drifts), default=0.0)


def address_confined(drifts: Iterable[Drift]) -> bool:
    """Did every moving site carry an address-based fingerprint?

    The mechanism check.  ``<C object at 0x…>`` renders differently in a second
    process, so address sites are the ones with a *reason* to move; a site whose
    arguments all fingerprint by value has none.  True here says the instability
    is identity, not arithmetic, and it is the same predicate the disagreement
    set satisfies — see :func:`exclusion_scope.disagreements_address_confined`.
    """
    return all(d.address_reprs for d in unstable(drifts))


def work_repeated(drifts: Iterable[Drift]) -> bool:
    """Did both runs execute the same number of calls at every site?

    The precondition for reading anything else here.  False means the two runs
    are not two samples of one measurement and the comparison is void.
    """
    return all(d.calls_stationary for d in drifts)


def fold_drift(first: dict[str, dict[str, InputSlice]],
               second: dict[str, dict[str, InputSlice]],
               hidden: Sequence[str] = pv.EXCLUDED_TESTS) -> tuple[Drift, ...]:
    """The control D-067 did **not** take: the reconstruction's *own input*.

    A reconstruction disagreement has two runs in it, not one.  The right-hand
    side is :func:`measure` under the exclusion, and D-067 controlled that one —
    two flat censuses in the same frame.  The left-hand side is a *different*
    run in a *different* frame: :func:`measure_attributed` with nothing hidden,
    whose per-origin digests :func:`fold_inputs` then filters.  Nobody has
    measured whether that run repeats.

    So D-067's ``FOLD_IMPLICATED`` is a conclusion about a residual containing an
    unmeasured term.  "The measured side is stationary" leaves two suspects, not
    one: the fold's arithmetic, and the fold's input.  This function takes the
    missing half — two attributed runs, folded under the same ``hidden`` — so
    the two can be told apart.

    The distinction is not academic for an **address-repr** site, where it is
    forced: ``<C object at 0x…>`` is a property of the process, and the
    attributed run is a different process running a *larger file set*.  There is
    no construction under which its addresses match the exclusion frame's, so
    for those sites the source term cannot be assumed zero — it has to be read.
    A value-fingerprinted site is the opposite: same question ⇒ same fingerprint
    in any frame, so given :func:`work_repeated` its source term *is* zero by
    construction and D-067's one-frame control was sufficient there.
    """
    return drift(fold_inputs(first, hidden), fold_inputs(second, hidden))


# --------------------------------------------------------------------------
# k censuses of one frame — Q-077's replicate, replacing a 1-sample threshold
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Spread:
    """One site's distinct count across **k** independent censuses of a frame.

    :class:`Drift` at k=2, and it exists because at k=2 the statement "this site
    did not move" is one coin flip wide.  D-070 measured a 0.1 % band over ~9600
    distinct inputs and then graded a site on whether it moved 0 or 2 — the one
    threshold a banded measurement cannot support, which is Q-077.

    There are two ways out and this is the cheaper one.  The first is to keep
    the pair and *widen* the threshold to the band, which buys a defensible
    grade at the cost of a number nobody can justify — the fourth unjustified
    floor in this package (see :func:`claim_scope.wilson_lower_at_least`).  The
    second is to keep the threshold at exactly zero and make it *harder to
    meet*: a site graded stationary here repeated its count in **k** runs, not
    2, so no constant has to be picked and the evidence strengthens with k
    instead of the criterion loosening.

    :attr:`span` is a single statistic over k samples, deliberately not a mean
    of the C(k,2) pairwise deltas: those pairs share runs, so k=3 gives 3 pairs
    and 2 degrees of freedom, and averaging them would report a precision the
    batch did not buy.
    """

    site: str
    counts: tuple[int, ...]
    calls: tuple[int, ...]
    address_reprs: bool

    @property
    def replicates(self) -> int:
        return len(self.counts)

    @property
    def span(self) -> int:
        """Widest disagreement among the k runs — the site's observed range."""
        return max(self.counts) - min(self.counts) if self.counts else 0

    #: :class:`Drift`'s grading name.  Identical at k=2.
    movement = span

    @property
    def stationary(self) -> bool:
        """Did the distinct count repeat exactly in **every** run?"""
        return self.span == 0

    @property
    def calls_stationary(self) -> bool:
        return not self.calls or max(self.calls) == min(self.calls)

    @property
    def relative(self) -> float:
        base = max(self.counts) if self.counts else 0
        return self.span / base if base else 0.0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        seen = "/".join(str(c) for c in self.counts)
        return (f"{self.site:<46} {seen:<24} "
                f"(span {self.span}, {self.relative:.3%}, k={self.replicates})"
                + ("  addr" if self.address_reprs else ""))


def spread(*censuses: dict[str, InputObservation]) -> tuple[Spread, ...]:
    """:func:`drift` over k flat censuses instead of 2.

    Every site observed by *any* run is returned, for :func:`drift`'s reason: an
    absent site has to be distinguishable from a stable one.  A site missing
    from one run counts 0 there, which makes it move — the honest reading, since
    a site that vanishes between two runs of the same suite is exactly the
    instability being looked for.
    """
    sites = sorted(set().union(*(set(c) for c in censuses)) if censuses else ())
    out = []
    for site in sites:
        obs = [c.get(site) for c in censuses]
        out.append(Spread(site=site,
                          counts=tuple(o.distinct if o else 0 for o in obs),
                          calls=tuple(o.calls if o else 0 for o in obs),
                          address_reprs=any(o.address_reprs for o in obs if o)))
    return tuple(out)


def fold_spread(*attributed: dict[str, dict[str, InputSlice]],
                hidden: Sequence[str] = pv.EXCLUDED_TESTS
                ) -> tuple[Spread, ...]:
    """:func:`fold_drift` over k attributed censuses — the source frame at k>2."""
    return spread(*(fold_inputs(a, hidden) for a in attributed))


def spread_band(spreads: Iterable[Spread]) -> float:
    """Worst relative span across the k runs — the frame's band, replicated.

    Read against :func:`drift_band`, which is this at k=2.  It can only grow
    with k (a wider sample of the same population cannot narrow a max), so a
    band that grows sharply from k=2 to k=3 is the direct evidence that the
    single-pair bands D-066..D-070 reported were underestimates.
    """
    return max((s.relative for s in spreads), default=0.0)


def tree_key(root: Path | None = None) -> str:
    """The identity of the tree a measurement is being taken on, as one hash.

    Three cycles running, the frame's identity has been carried in prose: D-066
    measured its gap on a **64**-predicate tree, D-067 controlled it on a
    **69**-predicate one, D-068 controlled the other half on 69 as well — and
    each said so in a "한계" paragraph a reader has to find and believe.

    A *binary* transports across an edit (whether a site fingerprints by
    identity is a property of its argument types).  A **magnitude** does not:
    the gap is a difference of two counts, and both counts move when the suite
    the recorder runs does.  So the artifact should carry the tree it was taken
    on, and the comparison should be able to refuse rather than caveat — see
    :func:`exclusion_scope.single_tree`.

    Delegates to :mod:`tree_provenance`, which already owns this question for
    pass counts (D-043/D-044); reusing its fingerprint keeps one definition of
    "the same tree" instead of a second, subtly different one here.
    """
    from eval.mppi_sandbox import tree_provenance as tp
    return tp.stamp(root).worktree_fingerprint


def by_input_diversity(readings: Iterable[pv.Reading],
                       inputs: InputCensus) -> tuple[pv.Reading, ...]:
    """D-061's candidates, re-ordered by distinct inputs instead of calls.

    The replacement statistic, applied to the list it changes.  Ties break on
    call count and then on site, so the ordering is total and reproducible.
    """
    by_site = {r.predicate.site: r for r in inputs.readings}

    def key(reading: pv.Reading):
        seen = by_site.get(reading.predicate.site)
        distinct = seen.observation.distinct if seen and seen.observation else 0
        calls = reading.observation.calls if reading.observation else 0
        return (-distinct, -calls, reading.predicate.site)

    return tuple(sorted(readings, key=key))


def shift_over(readings: Iterable[pv.Reading], inputs: InputCensus
               ) -> tuple[tuple[str, int, int], ...]:
    """:func:`ordering_shift` over an explicitly supplied population.

    Split out because **rank is positional**: a shift is a statement about a
    *set*, and dropping a member renumbers everyone below it.  So the reading
    cannot be transported from one candidate set to a subset of it — it has to
    be re-taken, which is only possible if the population is a parameter.
    :mod:`exclusion_scope` re-takes it over the set with the exclusion list's
    artifacts removed (D-065).
    """
    pop = tuple(readings)
    by_calls = [r.predicate.site for r in pv.by_evidence(pop)]
    by_distinct = [r.predicate.site for r in by_input_diversity(pop, inputs)]
    rank_d = {site: i for i, site in enumerate(by_distinct)}
    return tuple((site, i, rank_d[site])
                 for i, site in enumerate(by_calls) if rank_d[site] != i)


def ordering_shift(vacuity: pv.Census, inputs: InputCensus
                   ) -> tuple[tuple[str, int, int], ...]:
    """``(site, rank_by_calls, rank_by_distinct)`` wherever the two disagree.

    The falsifiable form of this module's claim.  If the two orderings agree,
    D-061's call count was a fine proxy and this instrument bought a bound and
    nothing else — a result worth being able to report.
    """
    return shift_over(vacuity.candidates, inputs)


# --------------------------------------------------------------------------
# Calibration — constructed, for D-061's reason
# --------------------------------------------------------------------------

#: A scratch package whose input diversity is known by construction.  Note
#: ``recited_bar``: called many times, always one argument — D-057's shape,
#: which is the member the historical registry could not supply.
CALIBRATION_SOURCES = {
    "subject.py": '''\
        def recited_bar(x) -> bool:
            return x > 0.0

        def varied_bar(x) -> bool:
            return x > 0.0

        def no_arguments() -> bool:
            return True

        def unobserved(x) -> bool:
            return x < 0
        ''',
    "tests/test_subject.py": '''\
        from subject import recited_bar, varied_bar, no_arguments

        def test_calls():
            for _ in range(50):
                assert recited_bar(1.0)
                assert no_arguments()
            for x in (1.0, 2.0, 3.0, 4.0):
                assert varied_bar(x)
        ''',
}

#: ``(verdict, distinct)`` required back for each scratch predicate.  The
#: distinct count is pinned alongside the verdict because the verdict alone
#: would pass with a recorder that fingerprinted nothing at all.
CALIBRATION_EXPECTED = {
    "subject.recited_bar": (VERDICT_SINGLE_INPUT, 1),
    "subject.varied_bar": (VERDICT_MANY_INPUTS, 4),
    "subject.no_arguments": (VERDICT_SINGLE_INPUT, 1),
    "subject.unobserved": (VERDICT_UNOBSERVED, 0),
}


def calibration_census(root: Path) -> InputCensus:
    """Build the scratch package under ``root`` and measure it for real.

    Uses the shipped plugin, patching and subprocess path, so a green
    calibration is evidence about the production instrument.
    """
    for rel, body in CALIBRATION_SOURCES.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(textwrap.dedent(body), encoding="utf-8")
    population, refused = pv._scan(root)
    return InputCensus(readings=classify(population, _measure_scratch(population, root)),
                       refused=tuple(sorted(refused)),
                       suite=("tests/",))


def _measure_scratch(population: Sequence[Predicate], root: Path
                     ) -> dict[str, InputObservation]:
    """:func:`measure` against a scratch tree whose modules are top-level."""
    plugin = plugin_source().replace('"eval.mppi_sandbox." + module', "module")
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "predicate_inputs_plugin.py").write_text(plugin, encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = pv._sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join([str(tmpdir), str(root)])
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-p",
             "predicate_inputs_plugin", "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=300, check=False,
            env=env,
        )
        if not out.exists():
            return {}
        return _observations(json.loads(out.read_text(encoding="utf-8")))


def miscalibrated(cens: InputCensus) -> tuple[str, ...]:
    """Scratch predicates the instrument reads wrongly — pinned empty.

    Every member of :data:`CALIBRATION_EXPECTED` is constructed, so an *absent*
    member is itself a failure.  That is what keeps this mirror from reading as
    a clean bill by being empty (D-046).
    """
    by_site = {r.predicate.site: r for r in cens.readings}
    out = []
    for site, (verdict, distinct) in sorted(CALIBRATION_EXPECTED.items()):
        found = by_site.get(site)
        if found is None:
            out.append(f"{site} — not discovered by the scan")
            continue
        if found.verdict != verdict:
            out.append(f"{site} — {found.verdict}, expected {verdict}")
            continue
        seen = found.observation.distinct if found.observation else 0
        if seen != distinct:
            out.append(f"{site} — {seen} distinct inputs, expected {distinct}")
    return tuple(out)


def report(vacuity: pv.Census, inputs: InputCensus) -> str:  # pragma: no cover
    lines = [str(inputs), ""]
    hits = recited(vacuity, inputs)
    lines.append(f"  {len(hits)} one-sided AND single-input "
                 f"(of {len(vacuity.candidates)} one-sided):")
    for hit in hits:
        lines.append(f"    {hit.verdict:<13} {hit.site}  "
                     f"[{hit.calls} calls, 1 distinct]")
        for fp in hit.sample:
            lines.append(f"        {fp}")
    shift = ordering_shift(vacuity, inputs)
    lines.append("")
    if shift:
        lines.append(f"  ordering shift on {len(shift)} of "
                     f"{len(vacuity.candidates)} candidates "
                     f"(rank by calls → rank by distinct inputs):")
        lines.extend(f"    {site}: {a} → {b}" for site, a, b in shift)
    else:
        lines.append("  no ordering shift — the call count was a fine proxy.")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    population, _ = pv._scan()
    values = pv.census(observations=pv.measure(population))
    print(report(values, census(observations=measure(population))))
