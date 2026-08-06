"""The two residue CI failures, read — and they are one finding, not two.

Q-092 named two ``test_exclusion_scope.py`` failures that D-098's dispatch
reading was not entitled to speak about: both are set/registry assertions, not
float comparisons, so ``AVX512_SKX ABSENT`` cannot be the cause.  STATE called
them unreadable locally because both take the ``measured`` fixture, which
spawns a nested suite.  That was the wrong place to look: **both reached their
assertion on CI**, so the reading was already in the log and nobody had opened
it.

What the log says (run ``31058173229``, job ``92480149564``, sha ``210eeb0a``):

* ``test_the_exclusion_list_manufactured_exactly_two_candidates`` — the actual
  ``manufactured_candidates`` set has **six** members, not two.  The pinned
  headline pair is still there; :data:`RESIDUE` is what joined it.
* ``test_self_entries_are_the_majority_and_are_left_alone`` —
  ``exclusion_scope.RankAgreement.reportable is a self-entry whose verdict the
  exclusion inverted``.

That site appears in **both** failures.  So the two rows are one finding.

The mechanism
-------------

:func:`exclusion_scope.grade` answers *who hid it* — ``SELF_ENTRY`` iff every
attributing file is the site's own module's test.  :attr:`Masked.
manufactured_candidate` answers *which way it moved* — ``BOTH`` → one-sided.
Nothing in either couples them: they read different fields.  They are
**orthogonal axes**, and :func:`orthogonality_witness` constructs the
conjunction in four lines with no suite run at all.

The refuted assertion — "no self-entry is ever a manufactured candidate" — was
never an invariant.  It was an *empirical property of the population as it stood
when it was written*, promoted to an assertion.  The population then grew a
predicate whose two-sidedness comes only from its own module's test file, and
the property stopped holding.  This is D-095's shape again: a claim whose
population nobody supplied.

Why this is not fixed by widening the literal to six
-----------------------------------------------------

D-099 priced widening and found it repairs 1 of 6.  Here it would be worse than
useless: the set assertion's stated job is to catch *"a future widening of
``EXCLUDED_TESTS`` that starts hiding other modules' predicates"*.  Replacing
``{2 sites}`` with ``{6 sites}`` because six were observed is not a repair, it
is deleting the instrument and keeping its name — the same move D-097 caught as
a green over a partial population.

What is actually owed is a **scope**: state which population each claim is over.
The headline pair is the ``COLLATERAL`` kind (a *foreign* file hid them — the
D-061/D-062 finding worth acting on).  ``RankAgreement.reportable`` is the
``SELF_ENTRY`` kind (a module's own instrument inverted its own predicate —
bookkeeping, weaker).  The literal was right about the first kind and was
silently reading the union of both.

The three sites the log stopped short of — now read (D-101)
-----------------------------------------------------------

The log graded exactly **one** of the four residue sites, because the self-entry
test asserted inside its loop and so died on the first violating site it
reached.  The other three carried ``UNREAD``: their membership in the set was
measured, their *kind* was not, and D-098's error would have been to declare all
four ``SELF_ENTRY`` because one was.

Collecting instead of stopping costs the same run, and one attributed run
grades all four.  The split is **2 / 2**, and the half nobody had read is the
half that matters:

* ``exclusion_scope.RankAgreement.reportable`` — ``SELF_ENTRY``
* ``exclusion_scope.ReplicatedReading.licensed`` — ``SELF_ENTRY``
* ``predicate_inputs.Drift.stationary`` — ``COLLATERAL``
* ``predicate_inputs.Spread.stationary`` — ``COLLATERAL``

So the ``COLLATERAL`` finding is **four** sites, not the two the literal pinned:
``test_exclusion_scope.py``'s exclusion is hiding ``predicate_inputs``
predicates, and for ``Spread.stationary`` it is the *sole* hider.  That is
verbatim what the self-entry assertion's docstring says it exists to catch — "a
future widening of ``EXCLUDED_TESTS`` that starts hiding other modules'
predicates".  It fired, and it reported the first site it reached, which was one
of the two harmless ones.

Before paying for the run, ask what the exclusion list settles alone
--------------------------------------------------------------------

:func:`self_entry_is_impossible` is a one-sided bound needing no suite at all:
``SELF_ENTRY`` requires an excluded file that is the site's own instrument, so a
site whose module has no excluded test is ``COLLATERAL`` by construction.  It
settles **both** headline sites — the D-061/D-062 finding never needed a
measurement to be the kind of finding it is — and **none** of the residue, whose
four sites live in the two modules ``EXCLUDED_TESTS`` does exclude.
:data:`RUN_FREE_DISCHARGED` records that emptiness rather than deleting it,
because it is the price tag on the run below.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import exclusion_scope as es
from . import predicate_vacuity as pv

#: Every reading this module pins, and where it was taken.  D-086: a local green
#: is not evidence about CI, and the converse holds — so the two are separate
#: entries and :data:`SOURCE` says which one each site's grade came from, rather
#: than letting a module-level ``PROVENANCE`` imply the stronger of the two for
#: all of them.
SOURCES = {
    "ci:31058173229": {
        "kind": "ci",
        "run": "31058173229",
        "job": "92480149564",
        "sha": "210eeb0a",
        "workflow": "Sandbox CI / pytest (slow closed-loop)",
    },
    "local:04c445f7": {
        "kind": "local",
        "sha": "04c445f7",
        "call": "exclusion_scope.effect_from_one_run(pop, "
                "predicate_vacuity.measure_attributed(pop, excluded=()))",
        "why_admissible": "a grade is which *file* hid the site — string "
                          "identity over per-origin call tallies, with no "
                          "float comparison anywhere in it, so the dispatch "
                          "difference D-098 measured cannot reach it",
    },
}

#: The CI job this module was born from.  Kept as a name because the headline
#: pair, the six-member set and the one CI-stated grade all come from it.
PROVENANCE = SOURCES["ci:31058173229"]

#: The pair the assertion pinned, and still the whole of the ``COLLATERAL``
#: finding as D-061/D-062 measured it.  Both were hidden by a *foreign* file.
HEADLINE = (
    "guard_reflexivity._shells_out_to_git_diff",
    "local_only_audit.guard_is_derived",
)

#: The four sites that joined the set since the literal was written.  Measured
#: from the ``Extra items in the left set`` block of the assertion diff.
RESIDUE = (
    "exclusion_scope.RankAgreement.reportable",
    "exclusion_scope.ReplicatedReading.licensed",
    "predicate_inputs.Drift.stationary",
    "predicate_inputs.Spread.stationary",
)

#: Verdict for a residue site whose *kind* the log does not state.  Distinct
#: from any :mod:`exclusion_scope` grade on purpose: ``UNREAD`` is a fact about
#: the reading, ``UNATTRIBUTED`` is a fact about the site.
UNREAD = "UNREAD"

#: Verdict of the **run-free** bound below when it settles nothing.  A third
#: distinct word on purpose: ``UNREAD`` says nobody looked, ``INDETERMINATE``
#: says somebody looked with an instrument that cannot see this, and neither is
#: an :mod:`exclusion_scope` grade.
INDETERMINATE = "INDETERMINATE"

#: Site → grade, for every residue site.  Was **one** entry for as long as the
#: self-entry assertion named its first violator and stopped; the loop now
#: collects, and one attributed run states all four.
#:
#: The split is the finding: two are the harmless kind, and two are not.
GRADED = {
    "exclusion_scope.RankAgreement.reportable": es.SELF_ENTRY,
    "exclusion_scope.ReplicatedReading.licensed": es.SELF_ENTRY,
    "predicate_inputs.Drift.stationary": es.COLLATERAL,
    "predicate_inputs.Spread.stationary": es.COLLATERAL,
}

#: Which reading each grade came from.  The one CI stated stays attributed to
#: CI; the three it stopped short of were taken here.  Kept per-site rather than
#: per-module so that "this came off CI" cannot be inherited by a sibling entry.
SOURCE = {
    "exclusion_scope.RankAgreement.reportable": "ci:31058173229",
    "exclusion_scope.ReplicatedReading.licensed": "local:04c445f7",
    "predicate_inputs.Drift.stationary": "local:04c445f7",
    "predicate_inputs.Spread.stationary": "local:04c445f7",
}

#: The measured hider(s) per residue site.  ``Spread.stationary`` is the one to
#: read: its **only** attributing file is ``test_exclusion_scope.py``, which is
#: not its instrument.  ``Drift.stationary`` is hidden by that file *and* by its
#: own, and :func:`es.grade` reads ``COLLATERAL`` because the rule is *every*
#: attributing file, not *some* — a site a foreign file can hide is hidden.
ATTRIBUTED = {
    "exclusion_scope.RankAgreement.reportable": (
        "eval/mppi_sandbox/tests/test_exclusion_scope.py",),
    "exclusion_scope.ReplicatedReading.licensed": (
        "eval/mppi_sandbox/tests/test_exclusion_scope.py",),
    "predicate_inputs.Drift.stationary": (
        "eval/mppi_sandbox/tests/test_exclusion_scope.py",
        "eval/mppi_sandbox/tests/test_predicate_inputs.py"),
    "predicate_inputs.Spread.stationary": (
        "eval/mppi_sandbox/tests/test_exclusion_scope.py",),
}


def observed() -> tuple[str, ...]:
    """The full six-member set CI measured, sorted as the assertion prints it."""
    return tuple(sorted(HEADLINE + RESIDUE))


def reading(graded: dict[str, str] | None = None,
            residue: tuple[str, ...] = RESIDUE) -> dict[str, str]:
    """Every observed site → its grade, or :data:`UNREAD`.

    The headline pair carries ``COLLATERAL`` because that is what D-061/D-062
    measured for it and what ``manufactured_candidates``' docstring describes;
    the residue carries whatever the reading stated.

    ``graded`` resolves to :data:`GRADED` **in the body, per call**, and the
    parameter exists for one reason: the "an ungraded site reads ``UNREAD``"
    rule went from covering three sites to covering none the moment the residue
    was fully graded, and a rule whose only witness is the live population dies
    silently when that population changes.  Two of this branch's own tests were
    already found green-and-vacuous over an empty dict (06-06); the parameter is
    what lets the rule be exercised on a site that does not exist yet.
    """
    table = GRADED if graded is None else graded
    out = {site: es.COLLATERAL for site in HEADLINE}
    for site in residue:
        out[site] = table.get(site, UNREAD)
    return out


def coverage(graded: dict[str, str] | None = None,
             residue: tuple[str, ...] = RESIDUE) -> tuple[int, int]:
    """``(graded, total)`` over :data:`RESIDUE` — now ``(4, 4)``.

    The number that stops this module from repeating D-098's step.  It read
    ``1/4`` for as long as the self-entry assertion stopped at its first
    violator; the loop now collects, so one run states all four and any prose
    about "the four extras" is finally entitled to the plural.
    """
    table = GRADED if graded is None else graded
    return len([s for s in residue if s in table]), len(residue)


def of_grade(kind: str, graded: dict[str, str] | None = None) -> tuple[str, ...]:
    """Every observed site carrying ``kind``, sorted.

    The partition the refuted assertion was reading as one population.  With
    the residue graded, ``COLLATERAL`` answers **four** sites, not the two the
    literal pinned: the D-061/D-062 pair plus both ``predicate_inputs``
    predicates that ``test_exclusion_scope.py``'s exclusion hides.  That is the
    thing the self-entry assertion says it exists to catch — *"a future widening
    of EXCLUDED_TESTS that starts hiding other modules' predicates"* — and it
    had already happened while the loop was reporting the first violator it met,
    which was one of the harmless ones.
    """
    return tuple(sorted(s for s, g in reading(graded).items() if g == kind))


# --------------------------------------------------------------------------
# the run-free bound, and why it did not discharge the residue
# --------------------------------------------------------------------------
#
# STATE called grading the residue "cheap: collect all violators instead of
# stopping".  Before paying for a run, ask what the exclusion list alone
# settles.  :func:`es.grade` is ``SELF_ENTRY`` iff *every* attributing file is
# the site's own module's test, and the attributing files are drawn from
# ``EXCLUDED_TESTS`` — so if that list contains no test for the site's module,
# ``SELF_ENTRY`` is unreachable **by construction**, with no suite run at all.
#
# The bound is one-sided on purpose.  It can refute ``SELF_ENTRY``; it can never
# confirm one, because confirming needs to know *which* file did the hiding, and
# that is measured.  :data:`RUN_FREE_DISCHARGED` records what it actually
# settled here — nothing — which is the price tag on the measurement below.


def self_hiders(site: str, excluded: tuple[str, ...] = tuple(pv.EXCLUDED_TESTS)
                ) -> tuple[str, ...]:
    """Excluded files that are the instrument for ``site``'s own module.

    Same module derivation as :func:`es.grade`, read from the same registry, so
    the bound and the grade cannot disagree about what "own module" means.
    """
    module = site.rsplit(".", 1)[0] if "." in site else site
    module = module.split(".")[0]
    return tuple(f for f in excluded if es.subject_of(f) == module)


def self_entry_is_impossible(site: str,
                             excluded: tuple[str, ...] = tuple(pv.EXCLUDED_TESTS)
                             ) -> bool:
    """``True`` iff no excluded file could make ``site`` a ``SELF_ENTRY``."""
    return not self_hiders(site, excluded)


def run_free_reading(sites: tuple[str, ...] = RESIDUE,
                     excluded: tuple[str, ...] = tuple(pv.EXCLUDED_TESTS),
                     ) -> dict[str, str]:
    """Site → what the exclusion list alone settles.

    ``COLLATERAL`` only where ``SELF_ENTRY`` is unreachable *and* the site is a
    manufactured candidate (so it moved, so something attributed it);
    :data:`INDETERMINATE` otherwise.  Never ``SELF_ENTRY`` — see the one-sided
    note above.
    """
    return {site: (es.COLLATERAL if self_entry_is_impossible(site, excluded)
                   else INDETERMINATE)
            for site in sites}


#: What the run-free bound settled about :data:`RESIDUE`.  **Empty**: all four
#: sites live in ``exclusion_scope`` or ``predicate_inputs``, and
#: ``EXCLUDED_TESTS`` excludes the test for both, so ``SELF_ENTRY`` was
#: reachable for every one of them.  Recorded rather than deleted because an
#: empty result here is the argument for having paid for the run.
RUN_FREE_DISCHARGED = tuple(
    s for s, g in run_free_reading().items() if g != INDETERMINATE)

#: What the same bound settles about :data:`HEADLINE` — **both of them**.
#: Neither ``guard_reflexivity`` nor ``local_only_audit`` has a test in
#: ``EXCLUDED_TESTS``, so ``SELF_ENTRY`` is unreachable for either and the
#: D-061/D-062 finding is ``COLLATERAL`` *by construction*.  Worth stating
#: because the assertion this whole module exists to repair was reading the
#: headline and the residue as one population: the half that carries the
#: finding needed no measurement at all, and the half that needed one is
#: exactly the half nobody had measured.
HEADLINE_FORCED = tuple(s for s in HEADLINE if self_entry_is_impossible(s))


def orthogonality_witness() -> es.Masked:
    """A ``SELF_ENTRY`` that is also a manufactured candidate.

    The refutation of the assertion's premise, constructed rather than observed
    — and that is the point.  If the conjunction is constructible from the two
    functions' own definitions, then no run was ever needed to know it was
    reachable, and the assertion was resting on the population, not the code.
    """
    site = "exclusion_scope.RankAgreement.reportable"
    hider = "eval/mppi_sandbox/tests/test_exclusion_scope.py"
    return es.Masked(
        site=site,
        excluded_verdict=pv.VERDICT_ALWAYS_TRUE,
        lifted_verdict=pv.VERDICT_BOTH,
        attributed_to=(hider,),
        grade=es.grade(site, (hider,)),
    )


@dataclass(frozen=True)
class Residue:
    """The verdict on Q-092's pair."""

    #: ``True`` iff the failures are a property of the tree, not of the runner.
    real: bool
    #: How many distinct findings the two rows amount to.
    findings: int
    #: The site both rows name.
    shared_site: str
    graded: int
    total: int

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        kind = "REAL" if self.real else "MACHINE"
        return (f"{kind}: {self.findings} finding across 2 rows "
                f"({self.shared_site}); residue graded {self.graded}/{self.total}")


def verdict() -> Residue:
    """Q-092, answered — ``REAL``, one finding, residue read ``4/4`` (D-101).

    ``real`` is not a judgement call: a dispatch difference cannot change which
    strings are in a set, and :func:`orthogonality_witness` reproduces the
    conjunction on this box with no floating-point arithmetic anywhere in it.
    """
    graded, total = coverage()
    return Residue(
        real=True,
        findings=1,
        shared_site="exclusion_scope.RankAgreement.reportable",
        graded=graded,
        total=total,
    )
