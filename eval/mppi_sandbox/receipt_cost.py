"""Price the suite against the cycle budget (STATE #1).

STATE's ``## Current bottleneck`` names a number and three remedies: the suite
costs **17m43 of a 35-min cycle budget**, and a *fast receipt subset*, a
*no-new-thrust-after-minute-N* rule, or *splitting grading out* would each fix
it.  It also says the three are "all real and all unpriced", and that is the
gap this module closes.  Unpriced is the operative word — the 12:00 cycle on
2026-08-10 reached EXECUTE with less than the suite's cost left, could not take
a receipt, and stranded; the 13:00 cycle spent itself entirely clearing that
strand.  Neither cycle was careless.  Both were spending against a budget
nobody had written down in the same units as the bill.

What this module is *not*
-------------------------

It is not a fast subset.  Choosing one is a decision with a cost — a receipt
taken over a subset is a weaker claim than one taken over the suite, and how
much weaker depends on which tests the subset drops.  Shipping the subset
before the price is the D-016 shape in reverse: a runnable slice that nobody
can say is the right slice.  So this module answers the question a subset
proposal has to survive — *what would it cost and what would it stop
watching* — and leaves the choosing to Q-126.

The truncation trap
-------------------

``pytest --durations=N`` prints the **slowest N** and silently omits the rest.
Summing what it printed therefore yields a number that is not the suite's cost
and is not labelled as such: it is a lower bound wearing a total's clothes.
The failure is quiet in the dangerous direction — a truncated report makes the
dropped tail look free, so a subset priced off it looks cheaper and safer than
it is, which is precisely backwards.

So :func:`price` refuses unless it can reconcile the report against an
independently known suite total: :data:`COMPLETE` when the reported durations
account for the run, :data:`TRUNCATED` when they do not.  A ``TRUNCATED``
report still yields *bounds* — the omitted tail has a known aggregate size even
when its per-test breakdown is gone — and those are returned as bounds rather
than as an estimate.  D-042's asymmetry: an instrument that can only clear a
proposal should not be trusted to clear one.

Nothing here simulates.  It parses text and does arithmetic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: The report accounts for the run: per-test detail exists for effectively all
#: of the wall clock, so a subset's price is a measurement.
COMPLETE = "COMPLETE"

#: The report omits a tail.  A subset's price is bracketed, not known: every
#: dropped-but-unreported test could be anywhere from free to the whole gap.
TRUNCATED = "TRUNCATED"

#: No durations lines at all.  Distinct from ``TRUNCATED`` — a report with no
#: rows is not a very truncated report, it is the absence of a measurement, and
#: collapsing the two would let an empty file price a subset at zero.
NO_DURATIONS = "NO_DURATIONS"

#: pytest's duration line: ``12.34s call     path/to/test_x.py::test_y``.
#: The phase is captured because ``setup``/``teardown`` rows for one test are
#: separate lines, and a per-test cost that ignores its own fixture setup would
#: under-price exactly the sim-bound tests this exists to find.
_DURATION_RE = re.compile(
    r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+"
    r"(?P<phase>setup|call|teardown)\s+"
    r"(?P<nodeid>\S+)\s*$"
)

#: pytest's summary line, e.g. ``==== 2263 passed, 158 skipped in 1063.21s ====``
#: (optionally ``(0:17:43)``).  This is the independent total the reported rows
#: are reconciled against — independent because pytest measures it separately
#: from the per-test clocks, so agreement between them is evidence rather than
#: a tautology.
_SUMMARY_RE = re.compile(r"\bin\s+(?P<seconds>\d+(?:\.\d+)?)s\b")


@dataclass(frozen=True)
class Duration:
    """One ``(phase, test)`` timing row."""

    seconds: float
    phase: str
    nodeid: str

    @property
    def module(self) -> str:
        """The file part of the nodeid.

        Grouping is by module rather than by test because that is the
        granularity a subset can actually be expressed in — pytest selects
        files and directories cheaply, individual nodeids only via a growing
        literal list that goes stale the moment someone adds a test.
        """
        return self.nodeid.split("::", 1)[0]


def parse_durations(text: str) -> tuple[Duration, ...]:
    """Every duration row in *text*, in file order.

    Lines that are not duration rows are ignored rather than raising: the input
    is a whole pytest run's stdout, most of which is not this.
    """
    out: list[Duration] = []
    for line in text.splitlines():
        m = _DURATION_RE.match(line)
        if m:
            out.append(
                Duration(
                    seconds=float(m.group("seconds")),
                    phase=m.group("phase"),
                    nodeid=m.group("nodeid"),
                )
            )
    return tuple(out)


def parse_total(text: str) -> float | None:
    """Wall-clock seconds from pytest's summary line, or ``None`` if absent.

    ``None`` is not zero and is not an error — it means the reconciliation
    :func:`price` performs cannot be performed, which downgrades the verdict
    rather than failing it.
    """
    matches = _SUMMARY_RE.findall(text)
    return float(matches[-1]) if matches else None


def by_module(durations: tuple[Duration, ...]) -> dict[str, float]:
    """Total seconds per module, summed across all phases.

    Summed across phases deliberately: a sim-bound test that pays its cost in a
    session fixture would otherwise read as free at ``call`` time, which is the
    reading that would most mislead a subset proposal.
    """
    out: dict[str, float] = {}
    for d in durations:
        out[d.module] = out.get(d.module, 0.0) + d.seconds
    return out


@dataclass(frozen=True)
class Price:
    """What a candidate subset costs, and what it stops watching."""

    verdict: str
    #: Seconds the subset would spend.
    kept_seconds: float
    #: Seconds the subset would not spend — the saving, on reported rows only.
    dropped_seconds: float
    #: Wall clock the run actually took, if the summary line was present.
    total_seconds: float | None
    #: Reported seconds unaccounted for by any row — the truncated tail.  Zero
    #: when the report is complete.
    unreported_seconds: float
    kept_modules: tuple[str, ...] = ()
    dropped_modules: tuple[str, ...] = ()

    @property
    def kept_upper_bound(self) -> float:
        """Worst case for the subset: the whole unreported tail is inside it.

        The bound that matters.  A subset is proposed because it fits a budget,
        so the question it has to survive is not "what did the rows say" but
        "how bad can this be given what the rows did not say".
        """
        return self.kept_seconds + self.unreported_seconds

    @property
    def is_priced(self) -> bool:
        """Is ``kept_seconds`` a measurement rather than a lower bound?"""
        return self.verdict == COMPLETE

    def describe(self) -> str:
        if self.verdict == NO_DURATIONS:
            return (
                "NO_DURATIONS: no duration rows parsed — rerun with "
                "`--durations=0`; a subset cannot be priced off an empty report"
            )
        head = (
            f"{self.verdict}: subset costs {self.kept_seconds:.1f}s "
            f"({len(self.kept_modules)} modules), drops {self.dropped_seconds:.1f}s "
            f"({len(self.dropped_modules)} modules)"
        )
        if self.verdict == TRUNCATED:
            head += (
                f"; {self.unreported_seconds:.1f}s unreported, so the subset is "
                f"bounded by {self.kept_upper_bound:.1f}s, not priced at "
                f"{self.kept_seconds:.1f}s"
            )
        return head


def price(
    text: str,
    keep: tuple[str, ...],
    tolerance: float = 0.02,
) -> Price:
    """Price the subset consisting of modules in *keep*.

    *tolerance* is the fraction of the run's wall clock the reported rows may
    fail to account for while still grading :data:`COMPLETE`.  It is not zero
    because pytest's own collection and reporting overhead is real and is not
    attributable to any test — insisting on exact reconciliation would grade
    every honest complete report ``TRUNCATED``, and a check that is red on the
    good case is D-044's muted check.
    """
    durations = parse_durations(text)
    if not durations:
        return Price(
            verdict=NO_DURATIONS,
            kept_seconds=0.0,
            dropped_seconds=0.0,
            total_seconds=parse_total(text),
            unreported_seconds=0.0,
        )

    grouped = by_module(durations)
    keep_set = set(keep)
    kept = {m: s for m, s in grouped.items() if m in keep_set}
    dropped = {m: s for m, s in grouped.items() if m not in keep_set}

    total = parse_total(text)
    reported = sum(grouped.values())
    # Clamped at zero: rows can exceed the summary total (phases overlap under
    # xdist, and setup shared by many tests is billed to each), and a negative
    # "unreported tail" is not a thing a bound can be built from.
    unreported = max(0.0, (total - reported)) if total is not None else 0.0

    if total is None:
        verdict = TRUNCATED
    elif unreported <= tolerance * total:
        verdict = COMPLETE
    else:
        verdict = TRUNCATED

    return Price(
        verdict=verdict,
        kept_seconds=sum(kept.values()),
        dropped_seconds=sum(dropped.values()),
        total_seconds=total,
        unreported_seconds=unreported,
        kept_modules=tuple(sorted(kept)),
        dropped_modules=tuple(sorted(dropped)),
    )


@dataclass(frozen=True)
class Budget:
    """Cycle-budget arithmetic in the units the bill arrives in."""

    suite_seconds: float
    budget_seconds: float
    #: Seconds a cycle spends on everything that is not the suite.
    overhead_seconds: float

    @property
    def runs_affordable(self) -> int:
        """How many suite runs fit after overhead.  Floor, never rounded up."""
        spare = self.budget_seconds - self.overhead_seconds
        if self.suite_seconds <= 0:
            return 0
        return max(0, int(spare // self.suite_seconds))

    @property
    def latest_start_seconds(self) -> float:
        """Minute-of-cycle after which starting the suite strands the cycle.

        This is the number the 12:00 strand needed and did not have.  Negative
        means the suite cannot fit at all — reported as a negative rather than
        clamped to zero, because "you had -190s of slack" and "you had none"
        are different situations and only one of them is fixed by starting
        earlier.
        """
        return self.budget_seconds - self.suite_seconds

    def strands(self, started_at_seconds: float) -> bool:
        """Would a suite started at *started_at_seconds* overrun the budget?"""
        return started_at_seconds > self.latest_start_seconds
