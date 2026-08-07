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

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: The cron's timezone.  ``daily_executor.sh`` names its log by KST date.
_KST = timezone(timedelta(hours=9))

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Cost of one full suite run, in seconds.  Measured three times on 2026-08-06
#: and 2026-08-07 by ``push_preflight record``: 714 s, 717 s, 717 s.
SUITE_SECONDS = 717

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
MIN_OVERHEAD_SECONDS = 240

_START_RE = re.compile(r"^=== executor start (\S+) ===$")
_END_RE = re.compile(r"^=== executor end (\S+) rc=(\d+) ===$")


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


def threshold(
    suite_seconds: int = SUITE_SECONDS, overhead_seconds: int = MIN_OVERHEAD_SECONDS
) -> int:
    """Shortest run that could have contained a suite *and* the rest of a cycle."""
    return suite_seconds + overhead_seconds


def grade(
    run: Run,
    *,
    published: bool,
    newest: bool,
    wrote_journal: bool = True,
    suite_seconds: int = SUITE_SECONDS,
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
    suite_seconds: int = SUITE_SECONDS,
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
        lines.append(f"  {g:<9} {clock}  {run.started}{mark}")
    lines += [
        "",
        f"  PUBLISHED={c['PUBLISHED']} PREMATURE={c['PREMATURE']}"
        f" OVERRUN={c['OVERRUN']} NO_JOURNAL={c['NO_JOURNAL']}"
        f" KILLED={c['KILLED']} IN_FLIGHT={c['IN_FLIGHT']}",
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


def advisory(rows: tuple[tuple[Run, str], ...]) -> str:
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
        return (
            f"cycle_wallclock — the preceding run ({run.started}) ended in"
            f" {clock}, under the {threshold()}s a suite plus a cycle needs."
            "  It cannot have taken a receipt.  Budget the suite as the first"
            " long-running step of EXECUTE, and never end a turn waiting on it."
        )
    if g == "OVERRUN":
        return (
            f"cycle_wallclock — the preceding run ({run.started}) ran {clock},"
            " long enough for a receipt, and still did not publish.  Cut scope"
            " this cycle: the failure mode ahead is running out of budget after"
            " the suite, not before it."
        )
    return (
        f"cycle_wallclock — the preceding run ({run.started}, {clock}) graded"
        f" {g}.  No budgeting finding."
    )


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
    for name in ("grade", "review"):
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
    runs = parse_log(path.read_text(encoding="utf-8", errors="replace"))

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
        print(advisory(rows))
        return 0

    print(report(rows))
    c = counts(rows)
    return 1 if (c["PREMATURE"] or c["OVERRUN"]) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
