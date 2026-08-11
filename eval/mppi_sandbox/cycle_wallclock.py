"""Grade each executor run by wall clock against the cost of one suite run.

Five consecutive cycles on 2026-08-07 (03:00, 06:00, 07:00, 08:00, 09:00)
finished their work, committed it, and never pushed.  The 09:00 journal named
the open question — *"find out why the last four cycles never reached the push,
given ``git push --dry-run`` succeeds"* — and offered budget exhaustion at a
~12-min suite as the hypothesis.  The 10:00 cycle read the same cron log and
wrote that it *"supports the budget-exhaustion hypothesis"*.

The wrapper's own log refutes both, and the refutation needs one subtraction.
``scripts/daily_executor.sh`` brackets every run with ``=== executor start
<iso> ===`` / ``=== executor end <iso> rc=N ===``, so each cycle's wall clock is
already recorded.  On 2026-08-07 the cycles that **failed** to push ran 12, 13,
9, 8 and 4 minutes; the ones that pushed ran 55, 17 and 50.  Exhaustion predicts
the non-pushers are the *long* runs.  They are the short ones, and every single
one exited ``rc=0``.

The mechanism that subtraction exposes: one suite run costs ~717 s, so a cycle
that ended 8 minutes after it started **cannot have run the suite**.  No suite
means no receipt, and ``push_preflight.check`` answers ``NO_RECEIPT`` and fails
closed (D-082).  The push gate was never the thing that broke — it did exactly
its job on a cycle that never gave it anything to read.  What ended those runs
was the cycle backgrounding the suite and then emitting a text turn that says it
is *waiting* for it: under ``claude -p`` a turn with no tool call **is** the
final answer, so the wrapper reaps the run, rc=0, suite and all.  The 09:00 log
ends on the sentence "Suite is running (~12 min ...).  Waiting for the receipt
before the remaining REPORT writes and the push."  The 10:00 log ends on "Once
the receipt lands I'll append the row ... and push."  Neither ever resumed.

So the grade this module assigns is a statement about what a run *had time to
do*, not about what it claimed:

``PREMATURE``
    Did not publish, and ran for less than one suite *plus* the irreducible
    non-suite work of a cycle (:data:`MIN_OVERHEAD_SECONDS`).  It cannot have
    taken a receipt; the push refusal is entailed by the clock alone.
``OVERRUN``
    Did not publish, and ran long enough to have taken a receipt anyway.  This
    is the shape budget exhaustion actually predicts, and
    :func:`exhaustion_verdict` exists to report that the population is empty.
``PUBLISHED``
    Pushed.  Out of scope for the defect, kept in the reading as the control —
    a grader with no published runs beside the others is measuring one arm.
``NO_JOURNAL``
    The run wrote no journal, so it had nothing to publish and the clock has no
    question to answer about it.  Split out because the first cut of this module
    had no such grade and computed "published" as *not stranded*, which credited
    the three recovery cycles and the one that died producing nothing as
    successes — an empty population read as a clean one, which is the same
    mistake in a new place (D-107).
``KILLED`` / ``IN_FLIGHT``
    Start line with no end.  See :func:`graded` for why these are separated
    without consulting a clock.

Like :func:`cycle_artifacts.strand_report`, the renderer takes its populations
and reads no repository, and the parser takes log *text* rather than a path —
the executor log lives outside the repo (``~/.local/share/...``), so a test that
reached for the real file would grade whatever the machine happened to have run
and would pass or fail for reasons unrelated to the code.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: The cron's timezone.  ``daily_executor.sh`` names its log by KST date.
_KST = timezone(timedelta(hours=9))

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Every observed cost of one **local** full suite run, in seconds, oldest
#: first, with provenance.  Kept as a list rather than collapsed to one number
#: for :func:`nested_timeout.measured_suite_seconds`'s stated reason: a replaced
#: number cannot be compared against the one it replaced, and here the series is
#: the finding — it is monotone, and it tracks the suite's own growth.
#:
#: Deliberately **not** :data:`nested_timeout.OBSERVED_SUITE_SECONDS`, which
#: looks like the same quantity and is not: that registry times the nested suite
#: on GitHub Actions runners (its provenance strings are workflow run ids), this
#: one times the local suite the push gate actually runs.  Two populations, two
#: registries; folding them would price a local deadline off a CI runner.
#: **Serial-mode observations only.**  D-211 made the gate's suite sharded and it
#: now costs 488 s (×14, 2556 passed, receipt head ``75fd3fc``) — that number is
#: deliberately **not** in this tuple, and the reason is that neither consumer can
#: accept it (D-212).  STATE read the 2.4× gap as staleness and asked for a
#: re-price; the append was tried, and the suite refuted it:
#:
#: * :func:`observed_suite_max` (the ceiling) is **prospective under an unknown
#:   mode**.  It is consulted only when no receipt can be read, and a cycle in
#:   that position cannot know sharding will engage either —
#:   :func:`push_preflight.record_sharded` falls back to a serial run whenever the
#:   split cannot be planned.  Pricing the unknown case at 488 s licenses a suite
#:   the serial fallback cannot finish, which is the asymmetric failure this
#:   function exists to refuse (D-200).
#: * :func:`observed_suite_min` (the floor) is **retrospective over a population
#:   that is mostly serial**.  It grades recorded runs, and the recorded runs are
#:   the ones that already happened — every stranded hour of 2026-08-07 predates
#:   sharding by five days.  Admitting 488 s regraded ten of them from
#:   ``PREMATURE`` to ``OVERRUN``, i.e. asserted that a run in the serial era
#:   could have completed a suite at a price only the sharded era achieves.
#:
#: So a flat list cannot hold two execution modes: the ends are not "one per
#: mode", they are both anchored in the serial one for independent reasons.  The
#: sharded price needs its own registry with its own consumers before it can be
#: recorded here at all — see D-212, which promotes that split from a deferred
#: nicety to a precondition.  Until then this series stays serial and stays
#: monotone, and its documented meaning ("tracks the suite's own growth") holds.
OBSERVED_SUITE_SECONDS: tuple[tuple[int, str], ...] = (
    (717, "2026-08-06/07, push_preflight record ×3: 714, 717, 717 s"),
    (1091, "2026-08-10, at 2324 tests"),
    (1223, "2026-08-11, at 2478 passed; receipt head feefcf6, 1222.87 s"),
)


def observed_suite_max() -> int:
    """The fallback's basis: the **worst** local observation, not the latest.

    The argument is :func:`nested_timeout.measured_suite_seconds`'s, which this
    module owed and did not pay.  That sibling derives a CI timeout from the
    worst of its observations because *the failure is asymmetric*: too low kills
    every run by construction, too high costs nothing unless something is
    already hanging.  The asymmetry here is the same shape — a suite price that
    is too low licenses a suite the cycle cannot finish, while one that is too
    high only makes a cycle cut scope it could have afforded — and until D-200
    this module used the opposite rule, keeping the *oldest* reading as a
    self-described floor.  One module derived the principle; its sibling, with
    the same asymmetry, never had it applied.
    """
    return max(s for s, _ in OBSERVED_SUITE_SECONDS)


def observed_suite_min() -> int:
    """The **best** local observation — the basis for :func:`threshold`, not
    :func:`suite_deadline`.

    D-200 derived the ceiling rule for the *deadline* instrument and re-priced
    the shared constant to serve it.  This registry has a second consumer whose
    asymmetry runs the **other way**, and re-pricing silently inverted it.
    :func:`grade` asks *could this run have contained a suite at all* and
    answers ``PREMATURE`` when it could not; that answer is only safe if the
    suite price it subtracts is a price the suite has actually been seen to
    achieve.  Priced at the worst observation instead, the bar rises above runs
    that demonstrably ran one — so the failure direction is a **manufactured**
    finding, which is exactly what :data:`MIN_OVERHEAD_SECONDS` documents this
    grader as refusing to do.

    So the two directions are not a refinement of one rule, they are two rules:
    an unknown price must refuse a suite *prospectively* (the ceiling, because
    licensing an unfinishable suite is the costly error) and must credit one
    *retrospectively* (the floor, because calling a completed suite impossible
    is).  One registry, two extremes, and each named at the site that needs it.
    """
    return min(s for s, _ in OBSERVED_SUITE_SECONDS)

#: Fallback cost of one full suite run, in seconds, used when no receipt can be
#: read.  Prefer :func:`suite_price`, which reads the duration off the last
#: receipt and tags it :data:`MEASURED`.
#:
#: **A ceiling, not a floor** — re-priced 717 → 1223 on 2026-08-11 (D-200), and
#: the direction is the point.  This constant is consulted *only* when the price
#: is unknown, and an unknown price on a deadline instrument must fail toward
#: refusing a suite, never toward licensing one.  At 717 s it did the opposite:
#: the module documented its own staleness ("known to be *low*", 1091 s observed
#: against 717 s assumed) and kept the low value anyway, so the one code path
#: that exists for the case "we cannot price this suite" answered with the most
#: permissive number available.  A cycle at minute 15 was told
#: ``SUITE_AFFORDABLE`` against a deadline 6m14 too late.
#:
#: Being unreachable is not a defence.  ``/tmp`` here is on rootfs with 174 days
#: of uptime, so the receipt persists and this literal is read approximately
#: never on *this* machine — which means its staleness was invisible rather than
#: harmless, and the first fresh checkout or cleared ``/tmp`` would have spent a
#: cycle discovering it.
SUITE_SECONDS = observed_suite_max()

#: Where the constitution's Phase-3 push gate writes its receipt, and therefore
#: where the last measured suite price is found.  A cycle takes ``elapsed``
#: *before* running its own suite, so the receipt sitting here is the previous
#: cycle's — which is the right reading: the most recent measurement of the
#: suite this cycle is about to pay for.
DEFAULT_RECEIPT = Path("/tmp/suite-receipt.json")

#: Verdict words for where :func:`suite_price` got its number.
MEASURED = "MEASURED"
FALLBACK = "FALLBACK"


def suite_price(receipt_path: Path | None = None) -> tuple[int, str]:
    """``(seconds, source)`` — the suite's price, read rather than typed.

    Returns the last receipt's measured ``duration_seconds`` when there is one,
    else :data:`SUITE_SECONDS` tagged :data:`FALLBACK`.

    Reads the receipt through a bare ``json.loads`` rather than importing
    :mod:`push_preflight`: this module is dispatched before any git work
    specifically so ``elapsed`` costs one file read (D-181), and
    ``push_preflight`` pulls in :mod:`tree_provenance`, :mod:`suite_coverage`
    and :mod:`inert_surface` behind it.  The budget instrument must not become
    a line item in the budget.

    Every failure collapses to the fallback on purpose — missing file,
    unreadable JSON, absent or null ``duration_seconds``, a non-positive number.
    An unknown price is not a finding here: this is an advisory reading (D-115),
    and a cycle that cannot price its suite still needs *a* deadline.  The
    fallback is the low one, so the failure mode is the permissive direction,
    which is why the source word is printed and not swallowed.
    """
    path = receipt_path or DEFAULT_RECEIPT
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
        secs = blob.get("duration_seconds")
        if secs is None:
            return SUITE_SECONDS, FALLBACK
        secs = round(float(secs))
        return (secs, MEASURED) if secs > 0 else (SUITE_SECONDS, FALLBACK)
    except (OSError, ValueError, TypeError, AttributeError):
        return SUITE_SECONDS, FALLBACK

#: Lower bound on the non-suite work of a cycle that produced a commit: REVIEW's
#: reads, PLAN, the edits, the commit, the REPORT writes.
#:
#: This constant exists because comparing a whole run against ``SUITE_SECONDS``
#: alone assumes the suite is the *only* thing a cycle does, and that assumption
#: mis-grades the real 03:00 run: 721 s against a 717 s suite clears the bar by
#: four seconds, which would mean it ran a full suite and did REVIEW, PLAN,
#: EXECUTE and a commit in the remaining four.  Four minutes is deliberately far
#: below anything observed — the shortest run on record that did no EXECUTE at
#: all (10:00, REVIEW only) took 236 s — so it is a bound, not an estimate, and
#: :func:`grade` stays conservative: it under-reports ``PREMATURE`` rather than
#: manufacturing it.
#:
#: **That justification measured the wrong population and the floor was false.**
#: 236 s is the length of a whole *suite-less* run, and what this constant
#: bounds is the non-suite work of a run that **did** run a suite — a quantity
#: no reading in that argument contained.  Measured directly it is smaller: the
#: 18:00 run on 2026-08-11 took 1442 s and its receipt records a 1214.24 s
#: suite, leaving **228 s** for REVIEW, PLAN, the edits, the commit and the
#: REPORT writes.  So the "deliberately far below anything observed" bound sat
#: 12 s *above* an observation, and the direction of that error is the one the
#: docstring promised not to make.
#:
#: Derived from the registry below for D-200's reason: a replaced number cannot
#: be compared against the one it replaced.
OBSERVED_OVERHEAD_SECONDS: tuple[tuple[int, str], ...] = (
    (
        228,
        "2026-08-11 18:00: 1442 s run − 1214.24 s receipt (head f124265, 2485 passed)",
    ),
)


def observed_overhead_min() -> int:
    """The **best** observed non-suite cost of a run that also ran a suite.

    A floor, so the extreme is the minimum — the mirror of
    :func:`observed_suite_min`'s argument and for the same consumer.  Both feed
    :func:`threshold`, which must not exceed a duration a real cycle has been
    seen to achieve.
    """
    return min(s for s, _ in OBSERVED_OVERHEAD_SECONDS)


MIN_OVERHEAD_SECONDS = observed_overhead_min()

#: The constitution's per-cycle wall-clock budget, in seconds (35 min = 5+5+15+
#: 5+5).  Second axis, not a refinement of :func:`grade` — see
#: :func:`budget_grade` for why the two cannot be folded into one scale.
BUDGET_SECONDS = 35 * 60

_START_RE = re.compile(r"^=== executor start (\S+) ===$")
_END_RE = re.compile(r"^=== executor end (\S+) rc=(\d+) ===$")

#: ``daily_executor.sh`` line 20, emitted by the tick that could not take the
#: ``flock -n``.  The stamp is the *skipped* tick's time, not the holder's.
_SKIP_RE = re.compile(r"^\[(\S+)\] executor already running; skipping this tick$")


@dataclass(frozen=True)
class Run:
    """One bracketed executor invocation from the wrapper's log."""

    started: str
    """ISO-8601 stamp from the ``start`` line, verbatim."""

    ended: str
    """ISO-8601 stamp from the ``end`` line, or ``""`` when unpaired."""

    rc: int | None
    """Exit code, or ``None`` when unpaired."""

    @property
    def hour(self) -> str:
        """``YYYY-MM-DDTHH`` — the key a journal's ``**Cycle**`` stamp joins on.

        Cron fires at ``HH:00:01``, and a journal records ``HH:00``, so the hour
        is the only field both sides agree on without rounding.
        """
        return self.started[:13]

    @property
    def seconds(self) -> int | None:
        """Wall clock, or ``None`` when the run never wrote an end line."""
        if not self.ended:
            return None
        delta = datetime.fromisoformat(self.ended) - datetime.fromisoformat(
            self.started
        )
        return int(delta.total_seconds())


def parse_log(text: str) -> tuple[Run, ...]:
    """Pair ``start``/``end`` markers in one wrapper log.

    A start line closes any previous unpaired start rather than nesting: the
    wrapper holds ``flock -n`` for the whole run, so two overlapping brackets
    are impossible and an unpaired start followed by another start means the
    first run died without reaching its ``echo``.
    """
    runs: list[Run] = []
    pending: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if m := _START_RE.match(line):
            if pending is not None:
                runs.append(Run(started=pending, ended="", rc=None))
            pending = m.group(1)
        elif m := _END_RE.match(line):
            if pending is not None:
                runs.append(Run(started=pending, ended=m.group(1), rc=int(m.group(2))))
                pending = None
    if pending is not None:
        runs.append(Run(started=pending, ended="", rc=None))
    return tuple(runs)


def parse_skips(text: str) -> tuple[str, ...]:
    """ISO stamps of ticks that found the lock held and exited without running.

    Separate from :func:`parse_log` because a skipped tick is *not* a run: it
    has no bracket, does no work, and belongs to no grade.  Folding it into the
    ``Run`` stream would have made the histogram count non-events.
    """
    return tuple(
        m.group(1) for line in text.splitlines() if (m := _SKIP_RE.match(line.strip()))
    )


def budget_grade(run: Run, *, budget_seconds: int = BUDGET_SECONDS) -> str:
    """Second axis: did this run stay inside the constitutional budget?

    **Independent of :func:`grade`, not a sub-grade of it.**  ``grade`` answers
    *why was there no push*, so it is defined only where a push is missing and
    ``PUBLISHED`` is its terminal success.  That makes a run which published at
    any cost invisible to it: the 2026-08-07 12:00 run took **99m40** — ~3× the
    budget — and graded ``PUBLISHED``, no finding.  Splitting ``PUBLISHED`` in
    two instead (the rejected alternative) would have redefined the population
    ``exhaustion_verdict`` counts and retroactively reinterpreted D-113's
    ``MIXED``, which is a real conclusion resting on that population.

    Two axes because there are two questions, and the second one has a
    *measured* consequence rather than a stylistic one — see :func:`displaced`.

    ``UNKNOWN``
        No end line, so no clock.  Returned rather than assuming compliance:
        an unfinished run is exactly the one most likely to be overrunning, and
        defaulting it to ``WITHIN_BUDGET`` would read an empty measurement as a
        clean one (D-107).
    """
    if run.seconds is None:
        return "UNKNOWN"
    return "OVER_BUDGET" if run.seconds > budget_seconds else "WITHIN_BUDGET"


def over_budget_grades() -> frozenset[str]:
    """The budget grades that constitute a finding, derived by probing.

    Derived rather than declared for D-104's reason, and the two constants are
    passed **explicitly**: ``budget_grade`` takes ``budget_seconds`` as a
    default argument, and defaults bind at definition time, so a derivation
    that omitted it would be insulated from the constant it claims to follow.
    That is the exact defect D-115 shipped and its own test caught.
    """
    brief = budget_grade(
        Run(started="2026-01-01T00:00:00", ended="2026-01-01T00:01:00", rc=0),
        budget_seconds=BUDGET_SECONDS,
    )
    epic = budget_grade(
        Run(started="2026-01-01T00:00:00", ended="2026-01-01T09:00:00", rc=0),
        budget_seconds=BUDGET_SECONDS,
    )
    # Subtraction, not ``{epic}``: this way an inverted comparison in
    # ``budget_grade`` flips the set instead of silently renaming its member.
    return frozenset({epic}) - {brief}


def displaced(runs: tuple[Run, ...], skips: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    """Map each run's start stamp to the ticks it displaced by holding the lock.

    This is what makes the budget axis a measurement rather than a rule.
    ``flock -n`` guarantees the attribution is exact, not statistical: a tick
    can only print the skip line if some run held the lock at that instant, and
    the brackets say which one.  So an over-budget run's cost is not "it broke a
    guideline" — it is *n cycles that never happened*.

    A run with no end line is bounded by the next run's start (or by nothing,
    when it is the trailing in-flight one); its own missing ``echo`` cannot be
    used as the closing bracket.
    """
    bounds: list[tuple[Run, datetime, datetime | None]] = []
    for i, run in enumerate(runs):
        start = datetime.fromisoformat(run.started)
        if run.ended:
            end: datetime | None = datetime.fromisoformat(run.ended)
        elif i + 1 < len(runs):
            end = datetime.fromisoformat(runs[i + 1].started)
        else:
            end = None
        bounds.append((run, start, end))

    out: dict[str, list[str]] = {run.started: [] for run in runs}
    for stamp in skips:
        when = datetime.fromisoformat(stamp)
        for run, start, end in bounds:
            if when >= start and (end is None or when <= end):
                out[run.started].append(stamp)
                break
    return {k: tuple(v) for k, v in out.items()}


#: The suite price :func:`threshold` subtracts — the **floor**, deliberately not
#: :data:`SUITE_SECONDS`.  See :func:`observed_suite_min` for why one registry
#: has to be read at both extremes; the short version is that ``SUITE_SECONDS``
#: is consulted *before* a suite (refuse when unsure) and this one *after*
#: (credit when unsure), and a single constant cannot fail safely in both.
PREMATURE_SUITE_SECONDS = observed_suite_min()


def threshold(
    suite_seconds: int = PREMATURE_SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> int:
    """Shortest run that could have contained a suite *and* the rest of a cycle.

    Priced at the **cheapest** observed suite, because the claim being made is a
    possibility claim: a run below this could not have contained *any* suite
    this repo has ever completed.  Pricing it at the worst observation instead
    asserts something stronger and false — that a run below the *slowest* suite
    ran none — and 2026-08-11 18:00 is the standing counterexample, a 1442 s run
    that completed a 1214 s suite and published, 21 s under a ``SUITE_SECONDS``
    threshold.
    """
    return suite_seconds + overhead_seconds


def _clock(seconds: int) -> str:
    """``49m11`` — the duration format the rest of this module already prints."""
    return f"{seconds // 60}m{seconds % 60:02d}"


def suite_deadline(
    budget_seconds: int = BUDGET_SECONDS,
    suite_seconds: int = SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> int:
    """Latest elapsed second at which a suite can still start and fit the budget.

    **A bound in one direction only.**  ``overhead_seconds`` is
    :data:`MIN_OVERHEAD_SECONDS`, which is documented as a *lower* bound on a
    cycle's non-suite work and deliberately far below anything observed.  Using
    it here makes the deadline as late as arithmetic allows, so passing it means
    the suite is *certainly* unaffordable, while sitting inside it guarantees
    nothing.  The asymmetry is the same conservatism :func:`grade` already
    carries — under-report the finding rather than manufacture it.
    """
    return budget_seconds - suite_seconds - overhead_seconds


def in_flight(runs: tuple[Run, ...], *, now: datetime | None = None) -> tuple | None:
    """The currently-executing run and its elapsed seconds, or ``None``.

    Only the **last** run in a log can be in flight.  ``parse_log`` closes an
    earlier unpaired start when it meets the next one, so a run left unpaired at
    the end of the file is the one holding the wrapper's ``flock`` — i.e. this
    cycle, reading its own clock.  A log whose last run is paired has nothing in
    flight: the reading was taken outside a cycle, and that is not a finding.
    """
    if not runs or runs[-1].ended:
        return None
    run = runs[-1]
    started = datetime.fromisoformat(run.started)
    when = now or datetime.now(started.tzinfo or _KST)
    return run, int((when - started).total_seconds())


def budget_room(
    elapsed_seconds: int,
    *,
    budget_seconds: int = BUDGET_SECONDS,
    suite_seconds: int = SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> str:
    """Prospective verdict on what the remaining budget still pays for.

    ``SUITE_AFFORDABLE``
        A full suite started now could still finish inside the budget.
    ``SUITE_UNAFFORDABLE``
        Inside the budget, but a suite started now would end outside it — the
        moment to cut scope, which is the one thing minute 34 is too late for.
    ``OVER_BUDGET``
        The budget is already spent.
    """
    if elapsed_seconds >= budget_seconds:
        return "OVER_BUDGET"
    if elapsed_seconds >= suite_deadline(
        budget_seconds, suite_seconds, overhead_seconds
    ):
        return "SUITE_UNAFFORDABLE"
    return "SUITE_AFFORDABLE"


def elapsed_reading(
    flight: tuple | None,
    *,
    budget_seconds: int = BUDGET_SECONDS,
    suite_seconds: int | None = None,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
    price_source: str = MEASURED,
) -> str:
    """One line: how long this cycle has been running and what it can still buy.

    ``suite_seconds=None`` means *price it yourself* — the caller has not
    measured anything and :func:`suite_price` should read the last receipt.
    Passing an explicit price keeps the function pure for tests, and
    ``price_source`` is what the caller learned from :func:`suite_price`; it is
    printed so a reading built on the stale literal cannot be mistaken for one
    built on a measurement.
    """
    if flight is None:
        return "cycle_wallclock — no run in flight; nothing to read."
    if suite_seconds is None:
        suite_seconds, price_source = suite_price()
    run, secs = flight
    verdict = budget_room(
        secs,
        budget_seconds=budget_seconds,
        suite_seconds=suite_seconds,
        overhead_seconds=overhead_seconds,
    )
    deadline = suite_deadline(budget_seconds, suite_seconds, overhead_seconds)
    head = (
        f"cycle_wallclock — this run ({run.started}) is at {_clock(secs)}"
        f" of a {budget_seconds // 60}m budget; {verdict}."
    )
    # The word matters more than the number.  A deadline built on the fallback
    # is known to be *late* (SUITE_SECONDS is a floor), so a reader who cannot
    # tell the two apart reads a permissive deadline as a measured one.
    priced = (
        f"{suite_seconds}s measured"
        if price_source == MEASURED
        else f"{suite_seconds}s unmeasured — no receipt; this deadline is a"
        " known-late fallback"
    )
    if verdict == "SUITE_AFFORDABLE":
        return head + (
            f"  Suite ({priced}) must start by {_clock(deadline)}"
            f" — {_clock(deadline - secs)} left to reach it."
        )
    if verdict == "SUITE_UNAFFORDABLE":
        return head + (
            f"  The {_clock(deadline)} suite deadline passed"
            f" {_clock(secs - deadline)} ago: cut scope now, do not start a"
            " second suite."
        )
    return head + (
        f"  {_clock(secs - budget_seconds)} over. Finish the current commit,"
        " mark the TSV row in_progress, write the journal anyway, and stop."
    )


def grade(
    run: Run,
    *,
    published: bool,
    newest: bool,
    wrote_journal: bool = True,
    suite_seconds: int = PREMATURE_SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> str:
    """Grade one run.  ``newest`` decides the unpaired case; see :func:`graded`."""
    if run.seconds is None:
        return "IN_FLIGHT" if newest else "KILLED"
    if published:
        return "PUBLISHED"
    if not wrote_journal:
        return "NO_JOURNAL"
    if run.seconds < threshold(suite_seconds, overhead_seconds):
        return "PREMATURE"
    return "OVERRUN"


def graded(
    runs: tuple[Run, ...],
    published_hours: frozenset[str],
    *,
    journal_hours: frozenset[str] | None = None,
    suite_seconds: int = PREMATURE_SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> tuple[tuple[Run, str], ...]:
    """Grade every run against an injected set of hours that reached ``origin``.

    ``published_hours`` is injected rather than derived because the two facts
    come from different places — the wrapper's log for the clock, git for the
    push — and a module that reached for both would be untestable without a
    scratch repo *and* a machine log.  :func:`main` does the wiring.

    **The in-flight slot is decided without a clock.** Only a *trailing*
    unpaired start is ``IN_FLIGHT``; an unpaired start with any later start
    after it is ``KILLED``.  ``flock -n`` makes this exact rather than
    heuristic: the next tick could not have acquired the lock unless the
    previous run had already released it, so a later start proves the earlier
    run is dead.  D-110 is the reason this is spelled out — an exemption slot
    granted by position alone held a corpse for four cycles, and the fix there
    was to make the exemption something a caller has to justify rather than
    something the newest row inherits by being newest.
    """
    out: list[tuple[Run, str]] = []
    for i, run in enumerate(runs):
        out.append(
            (
                run,
                grade(
                    run,
                    published=run.hour in published_hours,
                    newest=(i == len(runs) - 1),
                    wrote_journal=(
                        journal_hours is None or run.hour in journal_hours
                    ),
                    suite_seconds=suite_seconds,
                    overhead_seconds=overhead_seconds,
                ),
            )
        )
    return tuple(out)


def counts(rows: tuple[tuple[Run, str], ...]) -> dict[str, int]:
    """Grade histogram.  All five keys always present, so ``0`` is reportable."""
    out = {
        k: 0
        for k in (
            "PUBLISHED",
            "PREMATURE",
            "OVERRUN",
            "NO_JOURNAL",
            "KILLED",
            "IN_FLIGHT",
        )
    }
    for _, g in rows:
        out[g] += 1
    return out


def exhaustion_verdict(rows: tuple[tuple[Run, str], ...]) -> str:
    """Does the clock support budget exhaustion as the cause of non-pushing?

    ``REFUTED``
        There are non-publishing runs and **none** of them ran long enough to
        have run the suite.  Exhaustion predicts long runs; these are short.
    ``SUPPORTED``
        Every non-publishing run ran at least one suite.
    ``MIXED``
        Both populations occupied — the clock alone does not decide it.
    ``NO_EVIDENCE``
        Nothing failed to publish.  Returned rather than defaulting to
        ``REFUTED`` so an empty population cannot be read as a finding: that
        conflation is what let a dark instrument look like a clean branch for
        four cycles (D-107).
    """
    c = counts(rows)
    premature, overrun = c["PREMATURE"], c["OVERRUN"]
    if not premature and not overrun:
        return "NO_EVIDENCE"
    if premature and not overrun:
        return "REFUTED"
    if overrun and not premature:
        return "SUPPORTED"
    return "MIXED"


def report(
    rows: tuple[tuple[Run, str], ...],
    *,
    cost: dict[str, tuple[str, ...]] | None = None,
    suite_seconds: int = SUITE_SECONDS,
    overhead_seconds: int = MIN_OVERHEAD_SECONDS,
) -> str:
    """Render a wall-clock reading.  Takes its populations, reads no repository."""
    if not rows:
        return "cycle_wallclock — no executor runs in the log."
    c = counts(rows)
    verdict = exhaustion_verdict(rows)
    lines = [
        f"cycle_wallclock — {len(rows)} run(s); suite {suite_seconds}s"
        f" + overhead {overhead_seconds}s = {threshold(suite_seconds, overhead_seconds)}s."
        f"  budget-exhaustion hypothesis: {verdict}",
        "",
    ]
    for run, g in rows:
        secs = run.seconds
        clock = "     --" if secs is None else f"{secs // 60:4d}m{secs % 60:02d}"
        mark = ""
        if g == "PREMATURE":
            mark = "  ← no suite fits; receipt impossible"
        elif g == "OVERRUN":
            mark = "  ← ran a suite and still did not push"
        ticks = (cost or {}).get(run.started, ())
        budget = budget_grade(run)
        if budget in over_budget_grades():
            mark += f"  ⏱ over budget, displaced {len(ticks)}"
        lines.append(f"  {g:<9} {clock}  {run.started}{mark}")
    over = tuple(r for r, _ in rows if budget_grade(r) in over_budget_grades())
    lost = sum(len((cost or {}).get(r.started, ())) for r in over)
    lines += [
        "",
        f"  PUBLISHED={c['PUBLISHED']} PREMATURE={c['PREMATURE']}"
        f" OVERRUN={c['OVERRUN']} NO_JOURNAL={c['NO_JOURNAL']}"
        f" KILLED={c['KILLED']} IN_FLIGHT={c['IN_FLIGHT']}",
        f"  budget axis: OVER_BUDGET={len(over)} of {len(rows)};"
        f" ticks displaced={lost}",
    ]
    if verdict == "REFUTED":
        lines.append(
            "  every non-pushing run is too short to have run the suite:"
            " the cause is an early exit, not an exhausted budget."
        )
    elif verdict == "MIXED":
        lines.append(
            f"  two failure modes, not one: {c['PREMATURE']} run(s) ended before a"
            f" suite could fit, {c['OVERRUN']} ran one and still did not push."
            "  A single explanation covers neither group."
        )
    return "\n".join(lines)


def finding_grades() -> frozenset[str]:
    """The grades that constitute a finding, derived by probing :func:`grade`.

    Spelled as a derivation rather than a module-level ``frozenset`` literal for
    D-104's reason: a typed allow-list with no enumerator drives
    ``predicate_vacuity.unwatched_exemptions`` five-to-six, which this package
    has now paid five separate times.  Deriving it means whatever watches
    :func:`grade` watches this too — change the threshold branch and this set
    follows, instead of silently disagreeing with it.
    """
    short = Run(started="2026-01-01T00:00:00", ended="2026-01-01T00:01:00", rc=0)
    long = Run(started="2026-01-01T00:00:00", ended="2026-01-01T09:00:00", rc=0)
    # The two constants are passed explicitly rather than left to ``grade``'s
    # defaults.  Default arguments bind at definition time, so a derivation that
    # omitted them would be insulated from the very constants it claims to
    # follow — the first cut did exactly that and its own test caught it.
    return frozenset(
        grade(
            r,
            published=False,
            newest=False,
            wrote_journal=True,
            suite_seconds=SUITE_SECONDS,
            overhead_seconds=MIN_OVERHEAD_SECONDS,
        )
        for r in (short, long)
    )


def preceding(rows: tuple[tuple[Run, str], ...]) -> tuple[Run, str] | None:
    """The most recently *ended* run — the one this cycle directly follows.

    Not simply ``rows[-1]``: when REVIEW calls this, the running cycle's own
    start line is already in the log and grades ``IN_FLIGHT``.  Reading the last
    row would hand a cycle its own unfinished clock and never the run it is
    supposed to learn from.  ``None`` when no run has ended yet.
    """
    for run, g in reversed(rows):
        if g != "IN_FLIGHT":
            return run, g
    return None


def actionable(rows: tuple[tuple[Run, str], ...]) -> bool:
    """Does the reading say something *this* cycle can still act on?

    **Scoped to the preceding run, deliberately not to the day.**  A gate that
    fired on any ``PREMATURE``/``OVERRUN`` anywhere in the day's log would be
    permanently red from the first bad run until midnight — 2026-08-07 had five
    before 10:00 — and a check that cannot go green is one that gets muted.
    D-044 is the standing precedent: an ordering-blind tree check "is red every
    cycle and gets muted", and the repair there was to scope *when* it runs.
    The same repair applies to *what* it reads.

    The scope is not a convenience.  A finding about a run that already ended is
    not repairable — no cycle can un-overrun a predecessor — so the reading's
    only live use is prospective: it tells this cycle that the budgeting which
    just failed is the budgeting it is about to repeat.  Exactly one run carries
    that signal, and it is the one immediately before.
    """
    row = preceding(rows)
    return row is not None and row[1] in finding_grades()


def budget_clause(
    run: Run,
    cost: tuple[str, ...] = (),
    *,
    budget_seconds: int = BUDGET_SECONDS,
) -> str:
    """The budget axis' sentence for one run.  ``""`` when there is nothing to say.

    Reports the displaced ticks whenever there are any, because that is the
    part a reader cannot argue with.  "Over budget" invites the reply *so what,
    it published*; "cost the 13:00 cycle, which never ran" does not.
    """
    if budget_grade(run, budget_seconds=budget_seconds) not in over_budget_grades():
        return ""
    secs = run.seconds or 0
    over = secs - budget_seconds
    clause = (
        f"  Budget: {secs // 60}m{secs % 60:02d} against a {budget_seconds // 60}m"
        f" budget — {over // 60}m{over % 60:02d} over."
    )
    if cost:
        ticks = ", ".join(s[11:16] for s in cost)
        cycles = "cycle" if len(cost) == 1 else "cycles"
        clause += (
            f"  It held the lock through {len(cost)} {cycles} that never ran"
            f" ({ticks}).  Cut scope before the suite, not after it."
        )
    return clause


def advisory(
    rows: tuple[tuple[Run, str], ...],
    cost: dict[str, tuple[str, ...]] | None = None,
) -> str:
    """REVIEW-facing reading: what the preceding run did, and what it implies.

    Deliberately an *advisory* and not a gate, which is the whole difference
    between this reading and ``cycle_artifacts stranded``.  A strand names
    finished work sitting on disk and clearing it is an action available right
    now, so REVIEW is right to treat it as an obligation that outranks the
    decision tree.  A wall-clock grade names a run that is already over.  Giving
    the two the same authority would either stall cycles on an unrepairable
    fact, or teach the reader that a non-zero exit is ignorable — and that
    lesson does not stay confined to the check that taught it.
    """
    row = preceding(rows)
    if row is None:
        return "cycle_wallclock — no completed run precedes this cycle."
    run, g = row
    secs = run.seconds
    clock = "unknown" if secs is None else f"{secs // 60}m{secs % 60:02d}"
    if g == "PREMATURE":
        head = (
            f"cycle_wallclock — the preceding run ({run.started}) ended in"
            f" {clock}, under the {threshold()}s a suite plus a cycle needs."
            "  It cannot have taken a receipt.  Budget the suite as the first"
            " long-running step of EXECUTE, and never end a turn waiting on it."
        )
    elif g == "OVERRUN":
        head = (
            f"cycle_wallclock — the preceding run ({run.started}) ran {clock},"
            " long enough for a receipt, and still did not publish.  Cut scope"
            " this cycle: the failure mode ahead is running out of budget after"
            " the suite, not before it."
        )
    else:
        head = (
            f"cycle_wallclock — the preceding run ({run.started}, {clock}) graded"
            f" {g}."
        )
        # The budget axis speaks here or nowhere.  ``PUBLISHED`` is exactly the
        # grade that used to end the reading at "no finding" while a 99m40 run
        # was eating the next tick.
        clause = budget_clause(run, (cost or {}).get(run.started, ()))
        return head + (clause or "  No budgeting finding.")
    return head + budget_clause(run, (cost or {}).get(run.started, ()))


def log_path(day: str, *, log_dir: Path | None = None) -> Path:
    """Path to one day's wrapper log.  Mirrors ``daily_executor.sh``'s ``LOG``."""
    base = log_dir or Path.home() / ".local/share/representation-aware-mppi/logs"
    return base / f"executor-{day}.log"


def main(argv: list[str] | None = None) -> int:
    """``grade <YYYY-MM-DD>`` — read one day's log, join to git, print a reading.

    Exits non-zero when the reading has a finding (any ``PREMATURE`` or
    ``OVERRUN`` run), so a caller can gate on it the way REVIEW gates on
    ``cycle_artifacts stranded``.
    """
    import argparse

    from . import cycle_artifacts

    ap = argparse.ArgumentParser(prog="cycle_wallclock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("grade", "review", "elapsed"):
        p = sub.add_parser(name)
        p.add_argument("day", nargs="?", default=None, help="YYYY-MM-DD")
        p.add_argument("--log-dir", default=None)
        p.add_argument("--branch", default=None)
    args = ap.parse_args(argv)

    # REVIEW runs this without arguments, so "today" has to mean the day the
    # wrapper names its log after, which is KST — the cron's timezone, not the
    # machine's.  A UTC default would read yesterday's log for every cycle
    # between 00:00 and 09:00 KST.
    day = args.day or datetime.now(_KST).strftime("%Y-%m-%d")

    path = log_path(day, log_dir=Path(args.log_dir) if args.log_dir else None)
    if not path.exists():
        print(f"cycle_wallclock — no log for {day} at {path}")
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    runs = parse_log(text)

    # Dispatched before the git reads below on purpose.  ``elapsed`` is meant to
    # be taken repeatedly *during* a cycle, so its cost has to stay at one file
    # read — the journal/branch joins that ``grade`` and ``review`` need would
    # make the instrument that polices the budget a line item in it.  Always
    # rc=0, for D-115's reason: the reading is prospective, but the clock only
    # moves one way, so a non-zero exit could never be cleared and would be
    # muted within a cycle (D-044).
    if args.cmd == "elapsed":
        print(elapsed_reading(in_flight(runs)))
        return 0

    cost = displaced(runs, parse_skips(text))

    branch = args.branch or cycle_artifacts.current_branch()

    def _hour(c) -> str:
        return f"{c.stamp[:10]}T{c.stamp[11:13]}"

    # Three states, not two.  Deriving "published" as *not stranded* silently
    # credits every run that wrote no journal — the recovery cycles and the one
    # that died producing nothing — with a success it never had.
    journal_hours = frozenset(_hour(c) for c in cycle_artifacts.cycles(branch))
    stranded_hours = frozenset(_hour(c) for c in cycle_artifacts.stranded(branch))
    published_hours = journal_hours - stranded_hours
    rows = graded(runs, published_hours, journal_hours=journal_hours)

    if args.cmd == "review":
        # Always rc=0.  See :func:`advisory` — the finding is about a run that
        # has already ended, so there is nothing for a non-zero exit to gate.
        print(advisory(rows, cost))
        return 0

    print(report(rows, cost=cost))
    c = counts(rows)
    return 1 if (c["PREMATURE"] or c["OVERRUN"]) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
