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

The cost
---------

``1 + len(EXCLUDED_TESTS)`` full runs of the fast suite — four, at roughly a
minute each.  That is stated rather than hidden: :func:`measure_exclusion_effect`
is the expensive call and every pure function here takes its result as an
argument, so the partition's semantics are testable without paying for it.  The
same discipline :mod:`predicate_vacuity` uses to keep :func:`classify` pure.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

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
