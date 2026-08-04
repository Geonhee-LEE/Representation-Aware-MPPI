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
from eval.mppi_sandbox.predicate_vacuity import Predicate

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
_PLUGIN_RECORD_INPUTS = '''\
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


def _wrap(fn, site):
    def recorder(*a, **kw):
        _record(site, a, kw)
        return fn(*a, **kw)
    recorder.__name__ = getattr(fn, "__name__", "recorder")
    recorder.__doc__ = getattr(fn, "__doc__", None)
    recorder.__wrapped__ = fn
    return recorder


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


def measure(population: Sequence[Predicate],
            suite: Sequence[str] = pv.DEFAULT_SUITE,
            root: Path | None = None,
            excluded: Sequence[str] = pv.EXCLUDED_TESTS,
            timeout: int = 900) -> dict[str, InputObservation]:
    """Run ``suite`` with the argument recorder installed.

    A subprocess for :func:`predicate_vacuity.measure`'s reason: the suite
    imports the modules under measurement, so an in-process install would race
    whatever the parent already imported.
    """
    root = root or pv.PACKAGE.parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "predicate_inputs_plugin.py").write_text(
            plugin_source(), encoding="utf-8")
        out = tmpdir / "observations.json"
        env = dict(os.environ)
        env["PREDICATE_VACUITY_SITES"] = pv._sites_payload(population)
        env["PREDICATE_VACUITY_OUT"] = str(out)
        env["PYTHONPATH"] = os.pathsep.join(
            [str(tmpdir), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        subprocess.run(
            [sys.executable, "-m", "pytest", *suite,
             *(f"--ignore={p}" for p in excluded),
             "-p", "predicate_inputs_plugin", "-q", "-p", "no:cacheprovider"],
            cwd=root, capture_output=True, text=True, timeout=timeout,
            check=False, env=env,
        )
        if not out.exists():
            return {}
        raw = json.loads(out.read_text(encoding="utf-8"))
    return _observations(raw)


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
