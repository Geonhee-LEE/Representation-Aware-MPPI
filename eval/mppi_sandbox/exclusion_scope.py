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


# --------------------------------------------------------------------------
# the same audit, applied to the *input* census — D-065's declared bound (D-066)
# --------------------------------------------------------------------------
#
# D-065 re-took both rankings over the surviving population and wrote down what
# it could not afford: the survivors' distinct-input counts were still read
# under `EXCLUDED_TESTS`, so a survivor whose questions came only from an
# excluded file is under-counted, and under-counted toward `SINGLE_INPUT` —
# the same candidate-manufacturing direction `manufactured_candidates` names on
# the value side.  What follows buys it.
#
# One structural difference from the value census, and it is in this side's
# favour.  A verdict is a fold of a *sum*, so a move needing two files lifted at
# once reproduces under no single lift and `UNATTRIBUTED` is a real outcome.  A
# distinct count is a fold of a *union*, and every element of a union came from
# at least one member: if lifting the whole list raises a site's count, some
# single file's lift raises it too.  `unattributed_undercounts` asserts that
# rather than trusting it.


@dataclass(frozen=True)
class Undercount:
    """One predicate whose distinct-input count the exclusion list deflated."""

    site: str
    #: Distinct inputs under :data:`predicate_vacuity.EXCLUDED_TESTS`.
    excluded_distinct: int
    #: Distinct inputs with the list lifted — what the suite actually asked.
    lifted_distinct: int
    #: Excluded files that contribute at least one question no surviving file
    #: asked.  Measured from the digest sets, not derived from the filename.
    attributed_to: tuple[str, ...]
    grade: str

    @property
    def hidden(self) -> int:
        """Questions the exclusion list hid at this site."""
        return self.lifted_distinct - self.excluded_distinct

    @property
    def manufactured_single(self) -> bool:
        """Did the exclusion make this site look like it was asked one question?

        The direction that costs something.  ``SINGLE_INPUT`` is Q-074 (c)'s
        whole finding shape — D-057's bar evaluated on one kind of scene — so a
        site the *ignore list* pushed to ``distinct == 1`` is a manufactured
        finding in exactly the sense :attr:`Masked.manufactured_candidate` is.
        """
        return self.excluded_distinct == 1 and self.lifted_distinct > 1

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.grade:<13} {self.site}: "
                f"{self.excluded_distinct} → {self.lifted_distinct} distinct")


def scoped_exclusion(site: str, excluded: Sequence[str] = pv.EXCLUDED_TESTS
                     ) -> tuple[str, ...]:
    """The excluded files that are *this site's* own instrument.

    The module's thesis made computable: the exclusion's intent is per-subject,
    it was written per-file, and this is the per-subject form of it for one
    site.  Hiding these is the contamination control working as designed;
    hiding anything else is :data:`COLLATERAL`.
    """
    module = site.rsplit(".", 1)[0] if "." in site else site
    module = module.split(".")[0]
    return tuple(f for f in excluded if subject_of(f) == module)


def corrected_inputs(population: Sequence[pv.Predicate],
                     attributed: dict[str, dict[str, pi.InputSlice]],
                     excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                     suite: Sequence[str] = pv.DEFAULT_SUITE,
                     refused: Sequence[str] = (),
                     ) -> pi.InputCensus:
    """The input census with the exclusion applied **per subject** (D-066).

    Every site is folded under its own :func:`scoped_exclusion` rather than
    under the whole list: the file that is a site's instrument stays hidden,
    every other excluded file's questions are restored.  That is neither the
    shipped reading (which hides all four everywhere) nor the fully-lifted one
    (which lets each instrument inflate its own subject) — it is the reading the
    exclusion list was written to produce.

    One run, because a fold is not a run.  The distinct sets are unioned per
    site, so a scoped fold costs a set union rather than a suite.
    """
    folds = {hidden: pi.fold_inputs(attributed, hidden) for hidden in
             {scoped_exclusion(p.site, excluded) for p in population}}
    obs = {p.site: folds[scoped_exclusion(p.site, excluded)].get(p.site)
           for p in population}
    return pi.InputCensus(
        readings=pi.classify(population,
                             {s: o for s, o in obs.items() if o is not None}),
        refused=tuple(sorted(refused)), suite=tuple(suite))


def input_undercounts(population: Sequence[pv.Predicate],
                      attributed: dict[str, dict[str, pi.InputSlice]],
                      excluded: Sequence[str] = pv.EXCLUDED_TESTS,
                      ) -> tuple[Undercount, ...]:
    """Every site whose distinct-input count rises when the list is lifted.

    Attribution is by execution as on the value side, but it comes out of the
    digest sets rather than out of one lift per file: an excluded file is an
    attributing file iff it supplies at least one digest no surviving file
    supplied.  That is precisely "lifting this file alone raises the count",
    computed rather than re-measured.
    """
    base = pi.fold_inputs(attributed, excluded)
    lifted = pi.fold_inputs(attributed, ())
    drop = set(excluded)
    out = []
    for pred in population:
        site = pred.site
        before = base.get(site)
        after = lifted.get(site)
        if after is None:
            continue
        n_before = before.distinct if before is not None else 0
        if after.distinct <= n_before:
            continue
        kept = frozenset().union(
            *[sl.digests for origin, sl in attributed.get(site, {}).items()
              if origin not in drop] or [frozenset()])
        attrib = tuple(sorted(
            f for f in excluded
            if attributed.get(site, {}).get(f) is not None
            and attributed[site][f].digests - kept))
        out.append(Undercount(site=site, excluded_distinct=n_before,
                              lifted_distinct=after.distinct,
                              attributed_to=attrib,
                              grade=grade(site, attrib)))
    return tuple(out)


def collateral_undercounts(undercounts: Sequence[Undercount]) -> tuple[str, ...]:
    """Sites under-counted by a file that is not their instrument — the finding."""
    return tuple(sorted(u.site for u in undercounts if u.grade == COLLATERAL))


def manufactured_singles(undercounts: Sequence[Undercount]) -> tuple[str, ...]:
    """``SINGLE_INPUT`` readings the exclusion list created.

    The input-census twin of :func:`manufactured_candidates`, and the reason
    D-065's declared bound was worth buying rather than declaring twice: a site
    here is one whose "asked exactly one question" reading is the ignore list's
    doing, and Q-074 (c)'s conjunction — one-sided **and** single-input — would
    have promoted it to a witness.
    """
    return tuple(sorted(u.site for u in undercounts if u.manufactured_single))


def unattributed_undercounts(undercounts: Sequence[Undercount]) -> tuple[str, ...]:
    """Under-counts no single excluded file explains.

    Structurally empty — a union's every element has a source — so this is a
    **wiring check**, not a reading: non-empty means the digest sets and the
    folded counts disagree, and then nothing above this line can be trusted.
    """
    return tuple(sorted(u.site for u in undercounts if not u.attributed_to))


def input_reconstruction_disagreements(
        attributed: dict[str, dict[str, pi.InputSlice]],
        measured: dict[str, pi.InputObservation],
        hidden: Sequence[str] = pv.EXCLUDED_TESTS,
        ) -> tuple[tuple[str, int, int], ...]:
    """Where the fold and a real run under the same exclusion disagree.

    ``(site, reconstructed, measured)`` distinct counts.  The calibration
    :func:`reconstruction_disagreements` is for the value census, and this side
    needs its own because it has a second way to be wrong: the per-origin record
    fingerprints identically but stores an 8-byte **digest** of each
    fingerprint, so a collision here would deflate a reconstructed count that
    the flat recorder — which keeps whole fingerprints — got right.

    Both error sources push the same way (a collision merges two questions into
    one), so a clean comparison bounds them together — and a comparison that
    comes back dirty **in both directions** rules the digest out on its own, a
    collision being unable to raise a count.  That is what it did (D-066): 7 of
    53 observed sites disagree, six low and one high, none by more than 0.49 %.

    So this is reported as a **magnitude**, not asserted empty the way
    :func:`reconstruction_disagreements` is.  The pairing check that *is* clean
    is :func:`verdict_disagreements` — see there for why the split matters.
    """
    sites = set(attributed) | set(measured)
    folded = pi.fold_inputs(attributed, hidden)
    out = []
    for site in sorted(sites):
        got = folded.get(site)
        want = measured.get(site)
        n_got = got.distinct if got is not None else 0
        n_want = want.distinct if want is not None else 0
        if n_got != n_want:
            out.append((site, n_got, n_want))
    return tuple(out)


#: A disagreeing site the flat-vs-flat control shows repeating exactly.  The
#: measurement is stationary there, so the fold is the only remaining suspect.
ATTR_FOLD = "FOLD_IMPLICATED"
#: The control moves the site by at least as much as the fold gap.
ATTR_DRIFT = "DRIFT_COVERS"
#: The control moves the site, but by less than the fold gap.  Weak — one pair
#: of runs is one sample of a spread, so this ranks a magnitude it cannot bound.
ATTR_DRIFT_UNDER = "DRIFT_UNDERSHOOTS"
#: The control never observed the site, so it says nothing about it.
ATTR_UNCONTROLLED = "UNCONTROLLED"


@dataclass(frozen=True)
class Attribution:
    """One of D-066's count disagreements, put to the drift control."""

    site: str
    reconstructed: int
    measured: int
    control_delta: int
    control_stationary: bool
    verdict: str

    @property
    def gap(self) -> int:
        return abs(self.reconstructed - self.measured)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.verdict:<18} {self.site}: fold off by {self.gap}, "
                f"control moved {self.control_delta}")


def attribute_disagreements(
        disagreements: Sequence[tuple[str, int, int]],
        drifts: Sequence[pi.Drift]) -> tuple[Attribution, ...]:
    """Split D-066's residual into measurement and fold.

    D-066 closed a bound and left a question open: its reconstruction matched
    the measured run on verdicts and missed on 7 of 53 counts, and it could not
    say whether that was the fold being approximate or the *measurement* not
    repeating.  Both candidates predicted the same evidence, and the only thing
    the sign bought was that the 8-byte digest was not the cause.

    The discriminator is a control with no fold in it (:func:`predicate_inputs.
    drift`).  Read one site at a time:

    - the control moves it ⇒ two honest runs of the same measurement disagree
      there, and a reconstruction cannot be held to a standard the instrument
      does not meet itself;
    - the control repeats it exactly ⇒ the site is reproducible and the fold
      still missed, which is a defect in the fold.

    The magnitude comparison is deliberately reported and deliberately weak: two
    runs give one sample, so ``DRIFT_COVERS`` versus ``DRIFT_UNDERSHOOTS`` ranks
    a spread nobody has estimated.  The binary — stationary or not — is the part
    that carries.
    """
    by_site = {d.site: d for d in drifts}
    out = []
    for site, reconstructed, measured in disagreements:
        control = by_site.get(site)
        gap = abs(reconstructed - measured)
        if control is None:
            verdict, delta, stationary = ATTR_UNCONTROLLED, 0, False
        elif control.stationary:
            verdict, delta, stationary = ATTR_FOLD, 0, True
        else:
            delta = abs(control.delta)
            stationary = False
            verdict = ATTR_DRIFT if delta >= gap else ATTR_DRIFT_UNDER
        out.append(Attribution(site=site, reconstructed=reconstructed,
                               measured=measured, control_delta=delta,
                               control_stationary=stationary, verdict=verdict))
    return tuple(out)


def fold_implicated(attributions: Sequence[Attribution]) -> tuple[str, ...]:
    """Disagreeing sites the control cannot excuse.

    Empty means D-066's residual is measurement noise end to end and the fold
    is exonerated; non-empty names exactly which sites owe an explanation.
    """
    return tuple(a.site for a in attributions if a.verdict == ATTR_FOLD)


#: The exclusion-frame control repeats the site, but the *attributed* run the
#: fold reads from does not, by at least the gap.  The fold's input moved.
ATTR_SOURCE = "SOURCE_COVERS"
#: As above, but the source frame moves by less than the gap.  Same weakness as
#: :data:`ATTR_DRIFT_UNDER` — one pair is one sample.
ATTR_SOURCE_UNDER = "SOURCE_UNDERSHOOTS"
#: The reading's frames were not all measured on the same tree, so its
#: arithmetic has no single subject.  Not a cause — a refusal to name one.
ATTR_TRANSPORTED = "TRANSPORTED"


def single_tree(*keys: str) -> bool:
    """Were every frame of a reading measured on one and the same tree?

    ``keys`` are :func:`predicate_inputs.tree_key` values, one per run the
    reading folds together.  An **empty or missing** key makes this ``False``:
    an unstamped frame cannot claim to be the same tree as anything, and the
    default has to be the one that refuses, because the three cycles this
    exists for (D-066/D-067/D-068) each *did* compare across trees and each
    discovered it only afterwards, by hand.

    Cheap and necessary rather than sufficient — identical worktrees can still
    differ in installed packages or CPU dispatch (D-033), which this does not
    see.
    """
    return bool(keys) and all(keys) and len(set(keys)) == 1


@dataclass(frozen=True)
class FrameAttribution:
    """D-067's residual re-asked with **both** of the fold's inputs controlled."""

    site: str
    reconstructed: int
    measured: int
    measured_delta: int
    source_delta: int
    verdict: str

    @property
    def gap(self) -> int:
        return abs(self.reconstructed - self.measured)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.verdict:<20} {self.site}: fold off by {self.gap}, "
                f"exclusion frame moved {self.measured_delta}, "
                f"attributed frame moved {self.source_delta}")


def attribute_two_frame(
        disagreements: Sequence[tuple[str, int, int]],
        measured_drifts: Sequence[pi.Drift | pi.Spread],
        source_drifts: Sequence[pi.Drift | pi.Spread],
        trees: Sequence[str] = ()) -> tuple[FrameAttribution, ...]:
    """Grade each disagreement against the controls for **both** its runs.

    D-067 built one control and read it as exonerating or implicating the fold.
    It could only ever do the first.  A reconstruction disagreement is
    ``fold(attributed run) != measure(exclusion run)``, so a control over the
    right-hand run alone splits the residual into *measurement* and
    *everything else* — and "everything else" contains the fold's arithmetic
    **and** the attributed run's own reproducibility, which D-067 never
    measured and which is not zero for an address site (see
    :func:`predicate_inputs.fold_drift`).

    Precedence is deliberate: the exclusion frame is asked first, so every grade
    D-067 issued from it stands unchanged, and the only sites that can move are
    the ones it called ``FOLD_IMPLICATED``.  That makes this a strictly-narrower
    re-reading rather than a competing one — if ``fold_implicated`` is still
    non-empty afterwards, the fold really is the last suspect standing.

    ``trees`` is the optional guard D-068 needed and did not have: the
    :func:`predicate_inputs.tree_key` of every run folded in here.  Supplied and
    not all equal ⇒ every verdict is :data:`ATTR_TRANSPORTED`, because a gap and
    a drift measured on different trees are differences of four counts, not two,
    and no amount of precedence between the frames repairs that.  Omitted ⇒ the
    pre-D-069 behaviour, so the grades already published still reproduce; the
    guard is opt-in on purpose, since retro-fitting it would silently rewrite
    them instead of letting a fresh single-tree run replace them.

    Both frames' controls are read through ``.stationary`` and ``.movement``
    only, so a :class:`predicate_inputs.Spread` over k runs grades here exactly
    as a :class:`predicate_inputs.Drift` over 2 does — the k=2 case is the same
    numbers, and k>2 makes ``FOLD_IMPLICATED`` strictly harder to earn without
    moving the threshold off zero (Q-077).
    """
    by_measured = {d.site: d for d in measured_drifts}
    by_source = {d.site: d for d in source_drifts}
    transported = bool(trees) and not single_tree(*trees)
    out = []
    for site, reconstructed, measured in disagreements:
        gap = abs(reconstructed - measured)
        m = by_measured.get(site)
        s = by_source.get(site)
        m_delta = m.movement if m is not None else 0
        s_delta = s.movement if s is not None else 0
        if transported:
            verdict = ATTR_TRANSPORTED
        elif m is None or s is None:
            verdict = ATTR_UNCONTROLLED
        elif not m.stationary:
            verdict = ATTR_DRIFT if m_delta >= gap else ATTR_DRIFT_UNDER
        elif not s.stationary:
            verdict = ATTR_SOURCE if s_delta >= gap else ATTR_SOURCE_UNDER
        else:
            verdict = ATTR_FOLD
        out.append(FrameAttribution(site=site, reconstructed=reconstructed,
                                    measured=measured, measured_delta=m_delta,
                                    source_delta=s_delta, verdict=verdict))
    return tuple(out)


def fold_implicated_two_frame(
        attributions: Sequence[FrameAttribution]) -> tuple[str, ...]:
    """Sites neither frame's control can excuse — the licensed version."""
    return tuple(a.site for a in attributions if a.verdict == ATTR_FOLD)


def unlicensed_fold_verdicts(
        attributions: Sequence[Attribution],
        measured: dict[str, pi.InputObservation]) -> tuple[str, ...]:
    """D-067's ``FOLD_IMPLICATED`` verdicts a one-frame control could not issue.

    The free reading — a join of D-067's own two artifacts, no run.  A
    ``FOLD_IMPLICATED`` verdict says "the measurement repeats, so the fold is
    the only suspect left".  That inference needs the fold's *input* to repeat
    too, and for an address-repr site it demonstrably need not: the attributed
    run is a second process over a larger file set, and every ``<C object at
    0x…>`` in it is drawn from a different heap.  So at an address site the
    verdict names a suspect the evidence does not isolate.

    Value-fingerprinted sites are unaffected and that asymmetry is the point:
    there the source term is zero by construction, so a one-frame control is
    genuinely sufficient and the verdict stands as issued.
    """
    return tuple(sorted(a.site for a in attributions
                        if a.verdict == ATTR_FOLD
                        and (o := measured.get(a.site)) is not None
                        and o.address_reprs))


def disagreements_address_confined(
        disagreements: Sequence[tuple[str, int, int]],
        measured: dict[str, pi.InputObservation]) -> bool:
    """Did every disagreeing site fingerprint by identity rather than by value?

    The reading that needs no new run — it is a join of D-066's own two
    artifacts.  An argument with no value-based ``__repr__`` renders as ``<C
    object at 0x…>``, which is the *only* documented way a fingerprint can
    differ between two runs of the same suite.  So if the disagreements sit
    entirely inside the address-repr sites, the instability has a named
    mechanism and it is not arithmetic; if even one value-fingerprinted site
    disagrees, something is wrong that addresses do not explain.

    This is correlational where :func:`attribute_disagreements` is
    experimental — it cannot separate "addresses differ between processes" from
    "hiding a file perturbs the surviving files' allocations", both of which are
    address-driven.  It is cheap and it is a necessary condition, so it is worth
    stating on its own.
    """
    return all(bool(o := measured.get(site)) and o.address_reprs
               for site, _, _ in disagreements)


def verdict_disagreements(
        population: Sequence[pv.Predicate],
        attributed: dict[str, dict[str, pi.InputSlice]],
        measured: dict[str, pi.InputObservation],
        hidden: Sequence[str] = pv.EXCLUDED_TESTS,
        ) -> tuple[tuple[str, str, str], ...]:
    """:func:`input_reconstruction_disagreements` at the granularity that is read.

    The counts disagree and the **verdicts do not**, and the gap between those
    two sentences is the whole calibration on this side.
    :func:`predicate_inputs.classify` splits at ``distinct == 1`` and nowhere
    else — deliberately, because an unjustified floor is the fourth of its kind
    in this package — so a reconstruction that is off by 142 questions out of
    136 242 is off by nothing that any reading consumes.

    Stating it this way is not a softer bar, it is a *different* one, and it can
    fail while the counts agree: a site the fold puts at 1 and the run puts at 2
    disagrees by one question and by an entire finding.  So both are reported.
    A count claim near a tie — a rank, which is what D-061 and D-062 published —
    is the case this does **not** cover, and the ~0.5 % band is the reason
    :func:`corrected_inputs` is safe to re-rank on only where the gaps are wider
    than that.
    """
    folded = pi.fold_inputs(attributed, hidden)
    got = {r.predicate.site: r.verdict for r in pi.classify(population, folded)}
    want = {r.predicate.site: r.verdict for r in pi.classify(population, measured)}
    return tuple(sorted((s, got[s], want[s]) for s in got if got[s] != want[s]))


# --------------------------------------------------------------------------
# The batch `single_tree` licenses — D-069's requirement, bought
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LicensedReading:
    """The gap and both of its frame controls, measured on one tree.

    D-069 built :func:`single_tree` and it immediately voided the reading it was
    built to defend: the gap was a 70-predicate tree, both controls were 69, so
    all seven sites graded :data:`ATTR_TRANSPORTED` and D-068's
    ``FOLD_IMPLICATED`` was withdrawn pending exactly this.  Four runs — two
    :func:`predicate_inputs.measure_attributed` and two
    :func:`predicate_inputs.measure` — are the smallest set that supplies a gap
    and a control for each of its two frames without any of them being
    transported.

    Which run goes where is deliberate.  The gap's left-hand side is attributed
    run **A1**, its right-hand side exclusion run **M1**, and the second run in
    each frame exists only to bound its own frame.  So the source control is
    ``|A1 - A2|``, which is the pairing the question actually asks: *could A1 —
    the very run the fold read — have come out differently?*  In D-066..D-069
    the gap's runs and the controls' runs were disjoint sets, which answered a
    slightly different and weaker question.
    """

    trees: tuple[str, ...]
    disagreements: tuple[tuple[str, int, int], ...]
    measured_drifts: tuple[pi.Drift, ...]
    source_drifts: tuple[pi.Drift, ...]
    attributions: tuple[FrameAttribution, ...]

    @property
    def licensed(self) -> bool:
        """Did every one of the four runs see the same tree?"""
        return single_tree(*self.trees)

    @property
    def fold_implicated(self) -> tuple[str, ...]:
        return fold_implicated_two_frame(self.attributions)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        head = (f"licensed={self.licensed} "
                f"tree={self.trees[0][:12] if self.trees else '?'} "
                f"gap_sites={len(self.disagreements)}")
        return "\n".join([head, *(str(a) for a in self.attributions)])


def _stamped(call, root: Path | None) -> tuple[object, str]:
    """Run ``call`` and return it with the tree key it held **throughout**.

    :func:`single_tree` takes one key per run, which quietly assumes a run is
    instantaneous.  It is not — these are five-minute suite runs, and a batch of
    four spans long enough for an edit to land in the middle of it.  A key
    stamped only before the run would then certify a frame that changed under
    the recorder's feet, which is the same defect one level up from the one
    :func:`single_tree` exists to catch.

    So each frame is stamped on both sides and the key is only issued if they
    agree.  A frame that moved gets the **empty** key, and :func:`single_tree`
    already refuses on an empty key — the refusal path is reused rather than
    given a second spelling.
    """
    before = pi.tree_key(root)
    value = call()
    after = pi.tree_key(root)
    return value, (before if before == after else "")


def paired_reading(population: Sequence[pv.Predicate] | None = None,
                   root: Path | None = None,
                   hidden: Sequence[str] = pv.EXCLUDED_TESTS,
                   ) -> LicensedReading:
    """Take the four-run batch concurrently and grade it.

    Concurrent for a reason beyond wall clock: four sequential runs span ~20
    minutes, and the longer the batch, the wider the window in which the tree
    can move and void the whole thing.  Running them together makes the batch
    about as long as its slowest member, so the frozen-tree requirement is
    cheap to meet rather than a thing to hope for.

    Threads rather than processes because every run is already a
    :func:`subprocess.run` — the parent does nothing but wait on four pipes.

    The result grades through :func:`attribute_two_frame` with ``trees``
    supplied, so a batch that failed to stay on one tree comes back all
    :data:`ATTR_TRANSPORTED` instead of quietly reporting arithmetic across
    frames.  That is the whole contract: this function can return *no* usable
    verdict, and that outcome is a success of the instrument.
    """
    from concurrent.futures import ThreadPoolExecutor

    if population is None:
        package = (root / "eval" / "mppi_sandbox") if root is not None else pv.PACKAGE
        population, _ = pv._scan(package)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(_stamped, lambda: pi.measure_attributed(population,
                                                                root=root), root),
            pool.submit(_stamped, lambda: pi.measure_attributed(population,
                                                                root=root), root),
            pool.submit(_stamped, lambda: pi.measure(population, root=root), root),
            pool.submit(_stamped, lambda: pi.measure(population, root=root), root),
        ]
        (a1, k_a1), (a2, k_a2), (m1, k_m1), (m2, k_m2) = (f.result()
                                                          for f in futures)

    trees = (k_a1, k_a2, k_m1, k_m2)
    disagreements = input_reconstruction_disagreements(a1, m1, hidden)
    measured_drifts = pi.drift(m1, m2)
    source_drifts = pi.fold_drift(a1, a2, hidden)
    return LicensedReading(
        trees=trees,
        disagreements=disagreements,
        measured_drifts=measured_drifts,
        source_drifts=source_drifts,
        attributions=attribute_two_frame(disagreements, measured_drifts,
                                         source_drifts, trees=trees),
    )


# --------------------------------------------------------------------------
# k replicates per frame — Q-077's answer to a threshold at exactly zero
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReplicatedReading:
    """:class:`LicensedReading` with k runs per frame instead of 2.

    D-070 bought the licensed batch and its headline turned on **2 counts out of
    ~9600**: ``FOLD_IMPLICATED`` requires movement of exactly zero, the exclusion
    frame moved 2 at ``_is_set_valued``, and D-068's verdict was gone.  Three
    cycles had argued over that one bit.  Q-077 asked whether to widen the
    threshold to the frame's band; this takes the other branch and holds the
    threshold at zero while making it **harder to meet** — a site stationary
    across k runs is a stronger claim than one stationary across 2, and no
    constant is picked, so no fifth unjustified floor is created.

    What this can therefore report and D-070 could not:

    - :attr:`fragile` — sites whose verdict *changes* between the first pair and
      the full replicate set.  That is Q-077's coin-flip, priced rather than
      argued: an empty tuple says the knife-edge did not actually cut here, a
      non-empty one names the verdicts that were one run away from reversing.
    - :attr:`bands` — the C(k,2) pairwise bands per frame.  Not averaged (the
      pairs share runs), just listed, so the spread of the *band itself* is
      visible next to the single number D-066..D-070 each reported.
    - :attr:`ordering_control` — the ratio ranking's **own noise floor**, taken
      on one tree.  See its docstring: D-071's surviving claim (c) is about an
      ordering that reproduces across trees, and it was published without ever
      measuring what the ordering does when the tree does *not* move.

    The k replicates were previously spent entirely on the control: the gap came
    from ``(A1, M1)`` and the other 2(k-1) runs only widened the frames' bands.
    :attr:`replicate_disagreements` keeps all k gap readings instead — same
    batch, same tree, no extra runs — because ``(A_i, M_i)`` is a gap by exactly
    the pairing D-070 fixed, and throwing k-1 of them away is what left the
    numerator at n=1 while the denominator got replicated.
    """

    k: int
    trees: tuple[str, ...]
    disagreements: tuple[tuple[str, int, int], ...]
    measured_spreads: tuple[pi.Spread, ...]
    source_spreads: tuple[pi.Spread, ...]
    measured_bands: tuple[float, ...]
    source_bands: tuple[float, ...]
    attributions: tuple[FrameAttribution, ...]
    pair_attributions: tuple[FrameAttribution, ...]
    #: One disagreement set per replicate pair ``(A_i, M_i)``.  Defaults empty so
    #: a reading built before this field existed still constructs; a reading that
    #: has it exposes k gap readings instead of one.
    replicate_disagreements: tuple[tuple[tuple[str, int, int], ...], ...] = ()

    @property
    def licensed(self) -> bool:
        return single_tree(*self.trees)

    @property
    def replicate_attributions(self) -> tuple[tuple[FrameAttribution, ...], ...]:
        """Each replicate pair's gap, graded against the **shared** controls.

        The controls are deliberately not re-estimated per replicate.  Every
        replicate is a gap on the same tree inside the same batch, so the frames'
        movement is one quantity measured over all k runs; splitting it per pair
        would give each numerator its own denominator and turn a ranking
        comparison into a comparison of two different scores.  Holding the
        denominator fixed makes :attr:`ordering_control` a statement about the
        **gap** ordering, which is the thing D-071 claimed reproduced.
        """
        return tuple(
            attribute_two_frame(d, self.measured_spreads, self.source_spreads,
                                trees=self.trees)
            for d in self.replicate_disagreements)

    @property
    def ordering_control(self) -> tuple[RankAgreement, ...]:
        """C(k,2) rank agreements **within one tree** — the missing control.

        D-071 retired stationarity from both ends and left exactly one candidate
        standing: "not one magnitude reproduced, but the ordering did", offered
        over four trees' prose.  D-072 then found that claim rested on **two**
        sites, and :data:`RANK_MIN_N` refuses n=2.  Both of those are objections
        to the *evidence*.  This is an objection to the **experiment**: a
        cross-tree agreement has no meaning without knowing what agreement looks
        like when nothing changed, and nobody ever took that reading.

        Every pair here shares a tree, shares a batch, and shares its
        denominator, so whatever it reports is the ceiling.  A cross-tree rho is
        only evidence of structure insofar as it approaches this; a cross-tree
        rho *at* this value says the tree never mattered.  If this comes back
        low, (c) is dead without needing a second tree at all — an ordering that
        does not reproduce against itself cannot reproduce against anything.

        :func:`reading_record.comparable` refuses a same-tree pair of *records*
        and is right to: that comparison measures nothing about reproduction
        across trees.  It is the same arithmetic put to the opposite use, and
        the difference is which question is being asked, not which number comes
        out — so this deliberately does not route through that refusal.
        """
        rankings = self.replicate_attributions
        return tuple(rank_agreement(ratio_grades(rankings[i]),
                                    ratio_grades(rankings[j]))
                     for i in range(len(rankings))
                     for j in range(i + 1, len(rankings)))

    @property
    def fold_implicated(self) -> tuple[str, ...]:
        return fold_implicated_two_frame(self.attributions)

    @property
    def bands(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        return (self.measured_bands, self.source_bands)

    @property
    def fragile(self) -> tuple[tuple[str, str, str], ...]:
        """``(site, verdict at k=2, verdict at k)`` wherever replication moved it.

        The measured answer to Q-077.  A verdict that survives k runs was not
        resting on the threshold; one that appears here was.
        """
        at_k = {a.site: a.verdict for a in self.attributions}
        return tuple((a.site, a.verdict, at_k[a.site])
                     for a in self.pair_attributions
                     if at_k.get(a.site) != a.verdict)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        head = (f"licensed={self.licensed} k={self.k} "
                f"tree={self.trees[0][:12] if self.trees else '?'} "
                f"gap_sites={len(self.disagreements)} "
                f"fragile={len(self.fragile)}")
        return "\n".join([head, *(str(a) for a in self.attributions)])


def _pairwise_bands(censuses: Sequence, pair) -> tuple[float, ...]:
    """Every C(k,2) pair's band, in index order — a distribution, not a mean."""
    return tuple(pi.drift_band(pair(censuses[i], censuses[j]))
                 for i in range(len(censuses))
                 for j in range(i + 1, len(censuses)))


def replicated_reading(k: int = 3,
                       population: Sequence[pv.Predicate] | None = None,
                       root: Path | None = None,
                       hidden: Sequence[str] = pv.EXCLUDED_TESTS,
                       ) -> ReplicatedReading:
    """:func:`paired_reading` at k runs per frame, all 2k concurrent.

    The gap is still ``fold(A1)`` against ``M1`` and each frame still controls
    *itself* — the pairing D-070 fixed is unchanged, because the question is
    still whether the run the fold actually read could have come out
    differently.  The replicates widen the control, not the gap.

    Cost is 2k suite runs; they are subprocesses and the batch is about as long
    as its slowest member, so k=3 is 6 runs on 16 cores rather than 6× the wall
    clock.  It is still 2k chances for the tree to move mid-batch, and every one
    of them is stamped on both sides — a bigger batch is a *weaker* prior on
    staying licensed, which is the honest cost of asking for more replicates.
    """
    from concurrent.futures import ThreadPoolExecutor

    if k < 2:
        raise ValueError(f"k must be at least 2, got {k}")
    if population is None:
        package = (root / "eval" / "mppi_sandbox") if root is not None else pv.PACKAGE
        population, _ = pv._scan(package)
    with ThreadPoolExecutor(max_workers=2 * k) as pool:
        att = [pool.submit(_stamped,
                           lambda: pi.measure_attributed(population, root=root),
                           root) for _ in range(k)]
        mea = [pool.submit(_stamped,
                           lambda: pi.measure(population, root=root), root)
               for _ in range(k)]
        attributed = [f.result() for f in att]
        measured = [f.result() for f in mea]

    trees = tuple(key for _, key in attributed + measured)
    a, m = [r for r, _ in attributed], [r for r, _ in measured]
    replicate_disagreements = tuple(
        input_reconstruction_disagreements(a[i], m[i], hidden)
        for i in range(k))
    disagreements = replicate_disagreements[0]
    measured_spreads = pi.spread(*m)
    source_spreads = pi.fold_spread(*a, hidden=hidden)
    return ReplicatedReading(
        k=k,
        trees=trees,
        disagreements=disagreements,
        replicate_disagreements=replicate_disagreements,
        measured_spreads=measured_spreads,
        source_spreads=source_spreads,
        measured_bands=_pairwise_bands(m, pi.drift),
        source_bands=_pairwise_bands(
            a, lambda x, y: pi.fold_drift(x, y, hidden)),
        attributions=attribute_two_frame(disagreements, measured_spreads,
                                         source_spreads, trees=trees),
        pair_attributions=attribute_two_frame(
            disagreements, pi.drift(m[0], m[1]),
            pi.fold_drift(a[0], a[1], hidden), trees=trees),
    )


# --------------------------------------------------------------------------
# The gap/control ratio — D-071's (c), the last candidate standing
# --------------------------------------------------------------------------

#: Fewer common sites than this and a rank correlation is not worth computing.
#: Not a significance threshold — with n=2 every pair of distinct rankings is
#: either +1 or -1, so the statistic carries no information at all, and at n=3
#: the six possible orderings give only five distinct rho.  Stated as the floor
#: below which the number is meaningless rather than merely weak.
RANK_MIN_N = 3


@dataclass(frozen=True)
class RatioGrade:
    """One disagreement scored by *how far* it exceeds its own noise budget.

    D-066..D-071 all graded on **stationarity**: did the control move at all?
    D-071 retired that scheme from both ends — held at exactly zero the grade
    becomes unreachable as replicates grow (P(exact repeat) falls with k
    regardless of whether the fold is guilty), and widened to the frame's band
    the threshold is estimated from a quantity that spreads 7.7x within one
    frame on one tree.  Both branches of Q-077 died measuring, not arguing.

    What survived four trees is the **ordering**.  Not one magnitude reproduced
    (``_pure`` went 142 -> 196 -> 175 -> 214, ``_has_git_diff_literal``
    95 -> 29 -> 30 -> 65) but the gap sat above its control by a per-site
    factor that kept its rank.  So this scores the ratio and refuses to cut it:
    :attr:`ratio` is reported, :func:`ratio_ranking` orders it, and nothing
    here calls a site implicated.  A ratio grade with a threshold would be the
    fifth unjustified constant in this package; a ratio *ranking* needs none.

    The denominator sums both frames.  That is D-068's own noise budget --- it
    summed 47 / 42 / 58 across frames against gaps of 142 / 84 / 95 --- and it
    is the conservative choice, since each frame's control bounds only its own
    run and the fold reads one of each.
    """

    site: str
    gap: int
    measured_delta: int
    source_delta: int
    verdict: str

    @property
    def control(self) -> int:
        """Both frames' movement — the budget the gap has to clear."""
        return self.measured_delta + self.source_delta

    @property
    def ratio(self) -> float:
        """``gap / control``; ``inf`` when neither frame moved.

        The infinity is the old scheme's ``FOLD_IMPLICATED`` showing through,
        and it is left visible rather than clipped: a site whose control is
        exactly zero *is* rank 1 under any monotone reading of the ratio.  What
        changes is that it is no longer a separate verdict — it is the top of a
        continuum, so a site that misses zero by 2 counts lands next to it
        instead of in a different class (Q-077's coin flip, dissolved rather
        than adjudicated).
        """
        return float("inf") if self.control == 0 else self.gap / self.control

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.ratio:>8.2f}x  {self.site}: gap {self.gap}, "
                f"control {self.measured_delta}+{self.source_delta}")


def ratio_grades(attributions: Sequence[FrameAttribution]
                 ) -> tuple[RatioGrade, ...]:
    """Re-score a licensed reading's attributions as ratios, in place order."""
    return tuple(RatioGrade(site=a.site, gap=a.gap,
                            measured_delta=a.measured_delta,
                            source_delta=a.source_delta, verdict=a.verdict)
                 for a in attributions)


def ratio_ranking(attributions: Sequence[FrameAttribution]
                  ) -> tuple[RatioGrade, ...]:
    """The same grades, largest ratio first — the quantity D-071 left standing.

    Ties break on site name so the ordering is total and reproducible; a tie in
    the ratio is a tie in the evidence, and which of two tied sites is printed
    first must not depend on dict order.
    """
    return tuple(sorted(ratio_grades(attributions),
                        key=lambda g: (-g.ratio, g.site)))


def _rank_positions(ordered: Sequence[str]) -> dict[str, float]:
    """Position of each name, 1-based.  No ties: the caller's order is total."""
    return {name: float(i + 1) for i, name in enumerate(ordered)}


@dataclass(frozen=True)
class RankAgreement:
    """Do two readings of the ratio put the sites in the same order?

    This is the falsifiable form of D-071's (c).  "The magnitudes do not
    reproduce but the ordering does" was an eyeball claim over four trees'
    prose; :attr:`rho` is that claim as a number, and :attr:`n` is the honest
    denominator underneath it.
    """

    n: int
    common: tuple[str, ...]
    rho: float | None

    @property
    def reportable(self) -> bool:
        """``n`` at or above :data:`RANK_MIN_N`."""
        return self.rho is not None

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        body = f"rho={self.rho:+.3f}" if self.reportable else "rho=unreportable"
        return f"{body} over n={self.n} common sites"


def rank_agreement(first: Sequence[RatioGrade],
                   second: Sequence[RatioGrade]) -> RankAgreement:
    """Spearman rank correlation of two ratio rankings over their common sites.

    Deliberately unadorned: no p-value, no confidence interval, no threshold on
    ``rho``.  Five cycles of this branch have shown what happens when a
    threshold arrives before the distribution it is meant to cut, so this
    returns the statistic and its ``n`` and stops.  Below :data:`RANK_MIN_N`
    common sites ``rho`` is ``None`` --- not 0, not 1, *absent*, because at that
    size the value is a function of the arithmetic rather than of the data.

    Restricted to sites present in both readings on purpose.  Two trees need
    not disagree at the same sites, and scoring a site that only one reading
    saw would silently impute a rank to a missing measurement.
    """
    a = {g.site: g for g in first}
    b = {g.site: g for g in second}
    common = tuple(sorted(set(a) & set(b)))
    n = len(common)
    if n < RANK_MIN_N:
        return RankAgreement(n=n, common=common, rho=None)
    ra = _rank_positions(
        [g.site for g in ratio_ranking_of([a[s] for s in common])])
    rb = _rank_positions(
        [g.site for g in ratio_ranking_of([b[s] for s in common])])
    d2 = sum((ra[s] - rb[s]) ** 2 for s in common)
    return RankAgreement(n=n, common=common,
                         rho=1.0 - (6.0 * d2) / (n * (n * n - 1)))


def ratio_ranking_of(grades: Sequence[RatioGrade]) -> tuple[RatioGrade, ...]:
    """:func:`ratio_ranking`'s ordering applied to grades that already exist."""
    return tuple(sorted(grades, key=lambda g: (-g.ratio, g.site)))


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
