"""What did the census's own exclusion list hide? — auditing `EXCLUDED_TESTS`.

:mod:`predicate_vacuity` ignores three test files while it measures, and the
reason is sound: a census that watched :mod:`guard_witness`'s tests would score
that module's predicates ``BOTH`` for free, the instrument eating its own signal
(D-060).  :mod:`guard_vacuity` established the pattern and
:mod:`predicate_vacuity` inherited the same tuple **verbatim**.

Inheriting it verbatim is the defect this module measures.  The two censuses
read different things and the exclusion means different things to each:

``guard_vacuity`` reads **coverage of a line**.
    A witness test exists to execute the guard's ``raise``.  Its entire content
    is the thing that must not be counted, so hiding the file hides exactly the
    contamination and nothing else.
``predicate_vacuity`` reads a **return-value distribution over all predicates**.
    A test file calls far more predicates than the ones it is the instrument
    for.  ``test_guard_witness.py`` builds a repo whose push guard is a stale
    literal — so it calls :func:`local_only_audit.guard_is_derived` and gets
    ``False`` — and it shells out through :mod:`guard_reflexivity`.  Neither is
    a predicate the file is testing; both are ordinary suite calls.  Hiding the
    file hides them too.

So an exclusion whose *intent* is per-subject was applied per-file, and the
difference is not academic: it is the difference between a candidate set and an
artifact of the ignore list.

What the reading is
--------------------

Two censuses over one population — one under :data:`predicate_vacuity.EXCLUDED_TESTS`,
one with the list lifted — and the predicates whose verdict differs.  Each move
is then attributed to a specific file **by execution**: the list is lifted one
entry at a time and a move is attributed to the file whose individual lift
reproduces it.  Attribution by filename (``test_x.py`` tests ``x``) would be the
sixth hand-written registry this package presented as a derivation; it is used
only for the *subject* judgement below, where it is checkable.

Two verdicts, and the split is the whole point
------------------------------------------------

``SELF_ENTRY``
    The hidden predicate lives in the module the excluded file is the test for.
    Hiding it is correct and is what the exclusion was written to do.
``COLLATERAL``
    The hidden predicate lives in some other module.  The excluded file is not
    that predicate's instrument, merely one of its callers, and its call carries
    exactly as much evidence as any other test's.  Hiding it is a measurement
    error, and one that runs in the direction that manufactures candidates:
    a suppressed ``False`` turns ``BOTH`` into ``ALWAYS_TRUE``.

``UNATTRIBUTED``
    Reported, not dropped.  The per-file lifts are independent, so a move that
    needs two files lifted at once reproduces under neither.  A population this
    module cannot attribute is a population error, and a population error that
    reports itself is the thing D-045 through D-052 kept finding nobody had
    written down.

What this does not claim
-------------------------

That the exclusion list is wrong.  It is right for ``guard_vacuity`` and right
for the ``SELF_ENTRY`` half here.  The claim is narrower and checkable: the
*scope* is wrong for a return-value census, and :func:`corrected_candidates`
says by how much.

The cost — and the correction to it (D-064)
--------------------------------------------

This docstring used to read "``1 + len(EXCLUDED_TESTS)`` full runs of the fast
suite — four, at roughly a minute each."  Both halves were wrong, and the module
whose subject is *state your population rather than assume it* is the wrong
place for an assumed cost:

* :func:`measure_exclusion_effect` runs the suite ``2 + len(EXCLUDED_TESTS)``
  times, not ``1 + …`` — a base reading **and** a fully-lifted one, then one per
  held-out file.  With four exclusions that is **six** runs, not four.
* An instrumented run is not "roughly a minute".  Every site in the population
  is wrapped, so the recorder pays a call-cost on top of the suite's own.
  Timed on this tree: **4 min 57 s**.

So the true bill is ``6 × ~5 min ≈ 30 min`` against a stated ``4 × ~1 min ≈
4 min`` — mispriced **7.5×**, and by a factor nobody could have noticed without
running it once.  That is the whole reason D-063 could not finish its
attribution half inside a cycle budget: it was not over-ambitious, it was
working from a number that had never been measured.  :func:`price` now derives
the run count from the constant it depends on, so at least that half cannot
drift again.

The cheap reading
------------------

:func:`effect_from_one_run` gets the same partition from **one** run.  With an
origin recorded on every observation
(:func:`predicate_vacuity.measure_attributed`), "what would this predicate's
verdict be if file *X* had been ``--ignore``-d" is a filter over the record
rather than another run: drop *X*'s observations, re-:func:`predicate_vacuity.classify`.
Base, lifted and all four per-file lifts fall out of a single measurement.

It is a **counterfactual**, and that is a weaker thing than the six runs it
replaces: it assumes removing a file does not change what the surviving files
observe.  Test order, module-level caches and fixture scope can all break that,
so the assumption is not argued — it is checked.  :func:`reconstruction_disagreements`
compares the reconstructed base against a *measured* base run, site by site, and
the slow test pins it empty.  That is one extra run: **two** total against six,
and unlike six it comes with its own calibration.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from eval.mppi_sandbox import predicate_inputs as pi
from eval.mppi_sandbox import predicate_vacuity as pv

#: The hidden predicate belongs to the module its excluding file is the test for.
SELF_ENTRY = "SELF_ENTRY"
#: The hidden predicate belongs to some other module — the excluding file is a
#: caller, not an instrument.
COLLATERAL = "COLLATERAL"
#: No single-file lift reproduced the move.  Interaction, or drift mid-run.
UNATTRIBUTED = "UNATTRIBUTED"


def subject_of(test_path: str) -> str:
    """The module a test file is the instrument for, from its stem.

    ``eval/mppi_sandbox/tests/test_guard_witness.py`` → ``guard_witness``.  A
    naming convention, and used only for the :data:`SELF_ENTRY` judgement — the
    *attribution* is measured.  :func:`unresolved_subjects` is the mirror that
    makes the convention falsifiable: a test file whose derived subject is not a
    module of the package makes it non-empty rather than silently mis-grading.
    """
    stem = Path(test_path).stem
    return stem[len("test_"):] if stem.startswith("test_") else stem


def unresolved_subjects(excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                        package: Path = pv.PACKAGE) -> tuple[str, ...]:
    """Excluded files whose derived subject is not a module of the package.

    Empty means every exclusion's name resolves, so :data:`SELF_ENTRY` is being
    decided against a real module rather than against a string.  Non-empty means
    someone renamed a module and the grading below is guessing.
    """
    modules = {p.stem for p in package.glob("*.py")}
    return tuple(sorted(p for p in excluded if subject_of(p) not in modules))


@dataclass(frozen=True)
class Masked:
    """One predicate whose verdict the exclusion list changed."""

    site: str
    #: Verdict under :data:`predicate_vacuity.EXCLUDED_TESTS`.
    excluded_verdict: str
    #: Verdict with the list lifted — what the suite actually saw.
    lifted_verdict: str
    #: Excluded files whose individual lift reproduces the move.  Measured.
    attributed_to: tuple[str, ...]
    grade: str

    @property
    def module(self) -> str:
        return self.site.rsplit(".", 1)[0] if "." in self.site else self.site

    @property
    def manufactured_candidate(self) -> bool:
        """Did the exclusion turn a two-sided predicate into a candidate?

        The direction that matters.  A move from ``BOTH`` to ``ALWAYS_TRUE`` or
        ``ALWAYS_FALSE`` is the exclusion inventing a suspect; a move out of
        ``UNOBSERVED`` only means the file was the predicate's sole caller.
        """
        return (self.lifted_verdict == pv.VERDICT_BOTH
                and self.excluded_verdict in (pv.VERDICT_ALWAYS_TRUE,
                                              pv.VERDICT_ALWAYS_FALSE))

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.grade:<13} {self.site}: "
                f"{self.excluded_verdict} → {self.lifted_verdict}")


@dataclass(frozen=True)
class Effect:
    """The full reading, plus the bounds it was taken under."""

    masked: tuple[Masked, ...]
    #: Site → verdict, under the shipped exclusion list.
    excluded: dict[str, str]
    #: Site → verdict, with the list lifted entirely.
    lifted: dict[str, str]
    excluded_tests: tuple[str, ...]

    def of(self, grade: str) -> tuple[Masked, ...]:
        return tuple(m for m in self.masked if m.grade == grade)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        counts = " ".join(f"{g}={len(self.of(g))}"
                          for g in (SELF_ENTRY, COLLATERAL, UNATTRIBUTED))
        return (f"{len(self.masked)} predicates moved by "
                f"{len(self.excluded_tests)} exclusions ({counts})")


def grade(site: str, attributed_to: Iterable[str]) -> str:
    """``SELF_ENTRY`` iff every attributing file is the site's module's test."""
    files = tuple(attributed_to)
    if not files:
        return UNATTRIBUTED
    module = site.rsplit(".", 1)[0] if "." in site else site
    module = module.split(".")[0]
    return SELF_ENTRY if all(subject_of(f) == module for f in files) else COLLATERAL


def classify(excluded: dict[str, str],
             lifted: dict[str, str],
             per_file: dict[str, dict[str, str]]) -> tuple[Masked, ...]:
    """Build the masked set from three readings.  Pure — no suite runs.

    ``per_file`` maps an excluded path to the verdicts that differ from
    ``excluded`` when *that one file alone* is lifted.
    """
    out = []
    for site, before in sorted(excluded.items()):
        after = lifted.get(site)
        if after is None or after == before:
            continue
        attributed = tuple(sorted(f for f, moved in per_file.items()
                                  if moved.get(site) == after))
        out.append(Masked(site=site, excluded_verdict=before, lifted_verdict=after,
                          attributed_to=attributed,
                          grade=grade(site, attributed)))
    return tuple(out)


def measure_exclusion_effect(population: Sequence[pv.Predicate] | None = None,
                             excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                             suite: Sequence[str] = pv.DEFAULT_SUITE) -> Effect:
    """The expensive call: ``1 + len(excluded)`` runs of ``suite``.

    Separated from :func:`classify` so that everything about the partition is
    testable at zero cost and only the headline number pays.
    """
    if population is None:
        population, _ = pv._scan(pv.PACKAGE)

    def verdicts(ignore: Sequence[str]) -> dict[str, str]:
        obs = pv.measure(population, suite=suite, excluded=ignore)
        return {r.predicate.site: r.verdict for r in pv.classify(population, obs)}

    base = verdicts(excluded)
    full = verdicts(())
    per_file = {}
    for held in excluded:
        keep = tuple(p for p in excluded if p != held)
        one = verdicts(keep)
        per_file[held] = {s: v for s, v in one.items() if base.get(s) != v}
    return Effect(masked=classify(base, full, per_file),
                  excluded=base, lifted=full, excluded_tests=tuple(excluded))


def price(excluded: Sequence[str] = pv.EXCLUDED_TESTS) -> int:
    """Suite runs :func:`measure_exclusion_effect` costs.  Derived, not typed.

    ``2 + len(excluded)``: a base reading, a fully-lifted one, and one per
    held-out file.  The docstring that said ``1 + len(excluded)`` was off by a
    run and nothing checked it, so the count now lives next to the loop that
    spends it and a test reads both.
    """
    return 2 + len(excluded)


# --------------------------------------------------------------------------
# the same partition from one run (D-064)
# --------------------------------------------------------------------------

#: Origin recorded for a call made outside any test file's collection or
#: execution — a session-scoped teardown, an ``atexit`` hook.  Such a call
#: survives every ``--ignore``, so it is folded into every reconstruction.
UNATTRIBUTABLE = ""


def reconstruct(population: Sequence[pv.Predicate],
                attributed: dict[str, dict[str, pv.Observation]],
                hidden: Sequence[str] = ()) -> dict[str, str]:
    """Site → verdict as if ``hidden`` had been ``--ignore``-d.  No suite run."""
    folded = pv.fold(attributed, hidden)
    return {r.predicate.site: r.verdict for r in pv.classify(population, folded)}


def effect_from_one_run(population: Sequence[pv.Predicate],
                        attributed: dict[str, dict[str, pv.Observation]],
                        excluded: Sequence[str] = pv.EXCLUDED_TESTS) -> Effect:
    """:func:`measure_exclusion_effect`'s reading, reconstructed from one record.

    Same :class:`Effect`, same :func:`classify` — only the six measurements are
    replaced by six folds of one. Calibrated by :func:`reconstruction_disagreements`,
    not by assertion.
    """
    base = reconstruct(population, attributed, excluded)
    full = reconstruct(population, attributed, ())
    per_file = {}
    for held in excluded:
        keep = tuple(p for p in excluded if p != held)
        one = reconstruct(population, attributed, keep)
        per_file[held] = {s: v for s, v in one.items() if base.get(s) != v}
    return Effect(masked=classify(base, full, per_file),
                  excluded=base, lifted=full, excluded_tests=tuple(excluded))


def reconstruction_disagreements(population: Sequence[pv.Predicate],
                                 attributed: dict[str, dict[str, pv.Observation]],
                                 measured: dict[str, str],
                                 hidden: Sequence[str] = pv.EXCLUDED_TESTS,
                                 ) -> tuple[tuple[str, str, str], ...]:
    """Where the fold and a real run under the same exclusion disagree.

    ``(site, reconstructed, measured)`` triples.  Empty means the counterfactual
    held on this tree for this exclusion — evidence over 61 predicates and **one**
    exclusion set, which is what the slow test claims and no more.  Non-empty
    means a file's removal changes what the survivors observe, and then
    :func:`effect_from_one_run` is not a substitute for the six runs.
    """
    got = reconstruct(population, attributed, hidden)
    sites = set(got) | set(measured)
    return tuple(sorted((s, got.get(s, "-"), measured.get(s, "-"))
                        for s in sites if got.get(s) != measured.get(s)))


def unattributable_calls(attributed: dict[str, dict[str, pv.Observation]]
                         ) -> tuple[tuple[str, int], ...]:
    """Sites with calls no test file owns, and how many — reported, not dropped.

    These survive every ``--ignore``, so they weaken nothing; they are surfaced
    because a site whose evidence is *mostly* unattributable is a site whose
    per-file attribution says less than its count suggests.
    """
    out = []
    for site, per in sorted(attributed.items()):
        obs = per.get(UNATTRIBUTABLE)
        if obs is not None and obs.calls:
            out.append((site, obs.calls))
    return tuple(out)


def origins(attributed: dict[str, dict[str, pv.Observation]],
            site: str) -> tuple[tuple[str, int], ...]:
    """Which test files called ``site``, and how often.  Descending by count."""
    per = attributed.get(site, {})
    return tuple(sorted(((o, obs.calls) for o, obs in per.items() if obs.calls),
                        key=lambda pair: (-pair[1], pair[0])))


# --------------------------------------------------------------------------
# what the reading is for
# --------------------------------------------------------------------------

def collateral(effect: Effect) -> tuple[str, ...]:
    """Sites hidden by a file that is not their instrument — **the finding**."""
    return tuple(sorted(m.site for m in effect.of(COLLATERAL)))


def manufactured_candidates(effect: Effect) -> tuple[str, ...]:
    """One-sided verdicts the exclusion list created out of two-sided ones.

    The subset of :func:`collateral` that costs something: these sites are in
    :func:`predicate_vacuity.Census.candidates` and should not be.  Everything
    downstream that ranked them — ``by_evidence``, ``by_input_diversity``, and
    the two decisions those rankings led to — was ordering an artifact.
    """
    return tuple(sorted(m.site for m in effect.masked if m.manufactured_candidate))


def corrected_candidates(census: pv.Census, effect: Effect) -> tuple[str, ...]:
    """The candidate set with the exclusion's artifacts removed.

    What ``predicate_vacuity``'s candidate list would read if the exclusion were
    scoped to subjects instead of files.  Reported as a corrected *set* rather
    than folded into the census, because the census's number is the honest
    reading of the suite it declares it ran — the correction is a second
    measurement over a second suite and merging them would hide which is which.
    """
    artifacts = set(manufactured_candidates(effect))
    return tuple(sorted(r.predicate.site for r in census.candidates
                        if r.predicate.site not in artifacts))


# --------------------------------------------------------------------------
# re-taking the rankings over the population that survived (D-065)
# --------------------------------------------------------------------------


def surviving(census: pv.Census, effect: Effect) -> tuple[pv.Reading, ...]:
    """:func:`corrected_candidates` as ``Reading``\\ s, so it can be re-ranked.

    ``corrected_candidates`` returns site strings, which is enough to *state*
    the correction and not enough to re-take anything computed from the set —
    both published rankings need the readings.  Same filter, richer return.
    """
    keep = set(corrected_candidates(census, effect))
    return tuple(r for r in census.candidates if r.predicate.site in keep)


@dataclass(frozen=True)
class Rerank:
    """One site's rank pair before and after the artifacts were removed."""

    site: str
    #: ``(by_calls, by_distinct)`` over the contaminated set — what was published.
    published: tuple[int, int]
    #: The same pair over the surviving set.
    corrected: tuple[int, int]

    @property
    def moved(self) -> bool:
        return self.published != self.corrected

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        mark = "→" if self.moved else "="
        return (f"{self.site}: calls {self.published[0]}{mark}{self.corrected[0]}  "
                f"distinct {self.published[1]}{mark}{self.corrected[1]}")


def _ranks(readings: Sequence[pv.Reading], inputs: pi.InputCensus
           ) -> dict[str, tuple[int, int]]:
    by_calls = {r.predicate.site: i
                for i, r in enumerate(pv.by_evidence(readings))}
    by_distinct = {r.predicate.site: i
                   for i, r in enumerate(pi.by_input_diversity(readings, inputs))}
    return {s: (i, by_distinct[s]) for s, i in by_calls.items()}


def rerank(census: pv.Census, effect: Effect, inputs: pi.InputCensus
           ) -> tuple[Rerank, ...]:
    """Every surviving candidate's published rank pair against its corrected one.

    Rank is **positional**, so removing a member renumbers everything below it:
    a published ordering over a set containing artifacts is not a claim about
    the subset that survives them, even though the *relative* order of the
    survivors is untouched.  D-061 and D-062 both led with their rank-0 site,
    and that is the number this recomputes.  Ordered by corrected call rank.
    """
    alive = surviving(census, effect)
    before = _ranks(census.candidates, inputs)
    after = _ranks(alive, inputs)
    return tuple(sorted((Rerank(site=r.predicate.site,
                                published=before[r.predicate.site],
                                corrected=after[r.predicate.site])
                         for r in alive),
                        key=lambda rr: (rr.corrected[0], rr.site)))


def corrected_shift(census: pv.Census, effect: Effect, inputs: pi.InputCensus
                    ) -> tuple[tuple[str, int, int], ...]:
    """D-062's ``ordering_shift``, re-taken over the surviving candidates.

    The falsifiable half.  D-062's whole claim was that ranking by calls and
    ranking by distinct inputs *disagree*; if the sites generating the
    disagreement were the two the exclusion list manufactured, this comes back
    empty and the claim was an artifact of the population rather than a finding
    about it.
    """
    return pi.shift_over(surviving(census, effect), inputs)


def voided_leaders(census: pv.Census, effect: Effect, inputs: pi.InputCensus
                   ) -> tuple[str, ...]:
    """Artifact sites that held rank 0 of a published ordering.

    A headline is a rank-0 claim, so an artifact anywhere in the set costs a
    renumbering but an artifact *at the head* costs the sentence the decision
    was written around.  Names which, rather than leaving it to be re-derived
    from :func:`rerank`'s gaps.
    """
    artifacts = set(manufactured_candidates(effect))
    if not artifacts:
        return ()
    ordered = (pv.by_evidence(census.candidates),
               pi.by_input_diversity(census.candidates, inputs))
    return tuple(sorted({o[0].predicate.site for o in ordered
                         if o and o[0].predicate.site in artifacts}))


def report(effect: Effect | None = None) -> str:  # pragma: no cover - reporting
    effect = effect or measure_exclusion_effect()
    lines = [str(effect), ""]
    lines.extend(f"  {m}" for m in effect.masked)
    lines += ["",
              f"  collateral:              {collateral(effect) or '()'}",
              f"  manufactured candidates: {manufactured_candidates(effect) or '()'}",
              f"  unresolved subjects:     {unresolved_subjects() or '()'}"]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
