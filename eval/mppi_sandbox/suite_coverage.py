"""A green is a claim about the population the invocation selected (STATE #1).

:mod:`push_preflight` refuses a push whose receipt is missing, stale, red, or
**vacuous** — and its vacuity rule is stated exactly right::

    a run that collected 400 tests and skipped all 400 asserted nothing, and
    grading it GREEN is precisely the vacuous-survival defect this module
    refuses to reproduce.

It then applies that rule to one number: ``executed == 0``.  A run that executes
1092 tests and skips 154 is not empty, so the rule never fires, and the receipt
grades ``GREEN`` with the 154 nowhere in the verdict.

That is not a hypothetical either.  On 2026-08-06 the counts were:

* the local gate — the command in the constitution, no ``--slow`` — executed
  **1092** of **1246** collected and reported ``sandbox:pass=1091/1091``;
* CI run ``31042602721``, the first ``slow`` job ever allowed to finish, ran the
  other **154** and published ``12 failed, 138 passed, 2 errors``.

So the number quoted in the journal, the TSV row and the Telegram message of
**eighty-nine consecutive cycles** was a true statement about 87.6% of the
suite, and **every one of the 14 failures lived in the 12.4% it excluded**.  The
gate was not wrong about what it measured.  It was silent about what it did not.

Why the counts were already there
---------------------------------

:class:`push_preflight.Receipt` has parsed ``skipped`` and ``deselected`` since
it was written — :data:`push_preflight.EXECUTED_OUTCOMES` names both, with a
comment explaining why they are excluded from ``executed``.  The subtraction was
performed correctly and the remainder was thrown away.  This module keeps the
remainder.  D-095 spent a cycle on an instrument that was complete and whose
dial nobody read; this is the same finding one cycle later, in the gate that
stands between every cycle and its push.

Why this is not another always-on alarm
---------------------------------------

D-042 is in :mod:`push_preflight`'s own ``Refs`` line: *a check whose default is
alarm gets muted*.  The local suite **always** skips the slow half — running it
costs 162 min against a 35 min cycle — so "refuse every partial receipt" would
refuse every push forever and be deleted within a day.  It would also be the
wrong rule: a partial receipt is not a defect, it is a division of labour
between the two CI jobs, and the split is deliberate (``eval/conftest.py``).

The defect is a partial receipt whose *uncovered part is known to be red*, and
that is a fact about the world this module can be told.  So:

* :data:`FULL` — nothing was left out; the green covers the suite.
* :data:`PARTIAL` — something was left out.  Not a refusal on its own.
* :data:`EMPTY` — no population at all, which is :mod:`push_preflight`'s
  ``VACUOUS`` seen from here; graded **before** :data:`FULL`, because an empty
  suite trivially leaves nothing out and would otherwise read as full coverage.
  Emptiness before success, the rule this package keeps re-learning.

and the refusal, :data:`UNCOVERED_RED`, needs *both* a partial receipt and a
failing verdict for the uncovered half.  Today that fires.  On a day when CI's
slow job is green it does not, and no push is blocked by it.

What a partial receipt may still not say
----------------------------------------

Even when :data:`UNCOVERED_RED` does not fire, a partial green must not be
quoted as a total.  :func:`describe_metric` is the one place the metric string
is built, so ``1091/1091`` cannot be written again without the ``+154
uncovered`` that makes it a claim about a part.

The uncovered verdict is **injected**, never fetched here.  :mod:`ci_verdict`
knows how to ask GitHub; a gate that runs before every push must work with no
network, and a fetch failure inside a refusal is a refusal nobody can clear.

Refs: D-095 (the instrument was complete; nobody read the dial), D-042 (a check
whose default is alarm gets muted), D-076/D-081 (emptiness before success),
D-043/D-082 (bind a count to its tree, and to its population).
"""

from __future__ import annotations

from dataclasses import dataclass

#: Coverage grades, in the order :func:`grade` decides them.  ``EMPTY`` is first
#: for the reason :mod:`push_preflight` decides ``VACUOUS`` before ``RED``: a
#: reading with no population leaves nothing uncovered, so every later test
#: would pass it through as fully covered.
EMPTY = "EMPTY"
PARTIAL = "PARTIAL"
FULL = "FULL"

GRADES: tuple[str, ...] = (EMPTY, PARTIAL, FULL)

#: Outcome words meaning "collected, but no body ran".  The complement of
#: :data:`push_preflight.EXECUTED_OUTCOMES` over the words
#: :func:`push_preflight.parse_summary` can produce — the two lists are pinned
#: against each other by a test, so a new outcome word cannot land in neither
#: and silently shrink the population.
UNCOVERED_OUTCOMES: tuple[str, ...] = ("skipped", "deselected")


@dataclass(frozen=True)
class Coverage:
    """What a receipt's green does and does not cover."""

    executed: int
    skipped: int
    deselected: int

    @property
    def uncovered(self) -> int:
        """Collected but never run.  The part the verdict says nothing about."""
        return self.skipped + self.deselected

    @property
    def population(self) -> int:
        return self.executed + self.uncovered

    @property
    def fraction(self) -> float:
        """Share of the collected population the run actually executed.

        ``0.0`` for an empty population rather than a ``ZeroDivisionError``:
        callers grade :data:`EMPTY` from :attr:`population`, and a grade that
        raises on its own degenerate case is a grade nobody puts in a gate.
        """
        return self.executed / self.population if self.population else 0.0

    @property
    def asserts_nothing(self) -> bool:
        """``True`` when no test body ran — :data:`EMPTY` by another name.

        Named so the agreement with :data:`push_preflight.VACUOUS` is something
        a test can state, rather than a coincidence of two modules summing the
        same tuple.
        """
        return self.executed == 0

    @property
    def grade(self) -> str:
        # Keyed on ``executed``, not ``population``.  An all-skipped run has a
        # population of 400 and asserts nothing about any of them, so keying on
        # population would grade it PARTIAL — a reading with a remainder rather
        # than a reading with no content — and PARTIAL is not a refusal.  That
        # is push_preflight's VACUOUS case arriving through the back door as a
        # near-miss.  Emptiness is about what ran, which is the same quantity
        # ``VACUOUS`` is decided on, so the two agree by construction.
        if self.executed == 0:
            return EMPTY
        return FULL if self.uncovered == 0 else PARTIAL

    def describe(self) -> str:
        if self.grade == EMPTY:
            return "no tests collected — the run has no population"
        if self.grade == FULL:
            return f"{self.executed} executed, none left out"
        return (
            f"{self.executed} of {self.population} executed "
            f"({self.fraction:.1%}); {self.uncovered} uncovered "
            f"({self.skipped} skipped, {self.deselected} deselected)"
        )


def of(counts: dict[str, int]) -> Coverage:
    """Coverage from a :func:`push_preflight.parse_summary` count map.

    Takes the counts rather than the ``Receipt`` so this module does not import
    :mod:`push_preflight`, which imports it.
    """
    from . import push_preflight as pp

    executed = sum(counts.get(w, 0) for w in pp.EXECUTED_OUTCOMES)
    return Coverage(
        executed=executed,
        skipped=counts.get("skipped", 0),
        deselected=counts.get("deselected", 0),
    )


def describe_metric(counts: dict[str, int]) -> str:
    """The ``sandbox:pass=`` string, with its population attached.

    The constitution's metric vocabulary is ``sandbox:pass=<n>/<m>``, and on a
    partial receipt both ``n`` and ``m`` are counted over the executed part
    only — which is how ``1091/1091`` came to be written 89 times about a suite
    with 154 tests nobody ran.  A partial reading carries its remainder here so
    the string cannot be quoted as a total.
    """
    cov = of(counts)
    passed = counts.get("passed", 0)
    if cov.grade == EMPTY:
        return "sandbox:pass=0/0 (EMPTY — no tests collected)"
    base = f"sandbox:pass={passed}/{cov.executed}"
    if cov.grade == FULL:
        return base
    return f"{base} (+{cov.uncovered} uncovered — {cov.fraction:.1%} of suite)"


def uncovered_is_red(counts: dict[str, int], uncovered_verdict: str | None) -> bool:
    """Does this receipt's green sit on top of a known-failing remainder?

    *uncovered_verdict* is a :mod:`ci_verdict` verdict for the job that runs the
    part this receipt skipped, or ``None`` when it is not known.  ``None`` is
    **not** treated as failure: unknown-fails-closed is right for a receipt that
    may not exist, and wrong for a network fact a local gate cannot obtain — it
    would block every offline push and be muted within a day (D-042).
    """
    from . import ci_verdict as cv

    if uncovered_verdict != cv.FAIL:
        return False
    return of(counts).grade == PARTIAL
