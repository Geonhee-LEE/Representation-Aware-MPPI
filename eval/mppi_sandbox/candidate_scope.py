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

What is **not** measured here
-----------------------------

The log grades exactly **one** of the four residue sites.  The self-entry test
fails on the first violating site it reaches, so it names ``RankAgreement.
reportable`` and stops; the other three carry no grade in the log.  Their
membership in the set is measured, their *kind* is not.

D-098's own error was generalising six readable rows onto two unreadable ones.
Committing it here — declaring all four ``SELF_ENTRY`` because one is, and
therefore that the headline pair is untouched — would be the same step.  So
:func:`reading` returns ``UNREAD`` for those three and :func:`coverage` reports
``1/4``; the scoped assertions below are written so that they hold *without*
the unmeasured three, and fail if a seventh member ever appears.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import exclusion_scope as es
from . import predicate_vacuity as pv

#: The CI job the reading below was taken from.  D-086: a local green is not
#: evidence about CI, and the converse holds — this is a CI reading and is not
#: revalidated by anything this box runs.
PROVENANCE = {
    "run": "31058173229",
    "job": "92480149564",
    "sha": "210eeb0a",
    "workflow": "Sandbox CI / pytest (slow closed-loop)",
}

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

#: Site → grade, for the residue sites the log actually grades.  One entry.
#: The self-entry assertion names its first violator and stops, so this is the
#: whole of what was read — not a sample somebody chose.
GRADED = {
    "exclusion_scope.RankAgreement.reportable": es.SELF_ENTRY,
}


def observed() -> tuple[str, ...]:
    """The full six-member set CI measured, sorted as the assertion prints it."""
    return tuple(sorted(HEADLINE + RESIDUE))


def reading() -> dict[str, str]:
    """Every observed site → its grade, or :data:`UNREAD`.

    The headline pair carries ``COLLATERAL`` because that is what D-061/D-062
    measured for it and what ``manufactured_candidates``' docstring describes;
    the residue carries whatever the log stated, which for three of four is
    nothing.
    """
    out = {site: es.COLLATERAL for site in HEADLINE}
    for site in RESIDUE:
        out[site] = GRADED.get(site, UNREAD)
    return out


def coverage() -> tuple[int, int]:
    """``(graded, total)`` over :data:`RESIDUE` — currently ``(1, 4)``.

    The number that stops this module from repeating D-098's step.  Any prose
    that speaks about "the four extras" as a kind is over-claiming by ``3``.
    """
    return len(GRADED), len(RESIDUE)


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
    """Q-092, answered — ``REAL``, one finding, residue read ``1/4``.

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
