"""Which queued PR is the cheap one to merge?

Gate 1 counts the review queue and stops at a number: ``6/6``.  For 36 days that
number was the whole of what the executor could say about the thing blocking it,
and it carried an assumption nobody had measured — that a full queue is an
*expensive* queue.  D-323 measured it by hand and the assumption was false: five
of the six open PRs are 4–9 files, comfortably inside the envelope this
repository has actually absorbed, and only ``#67`` is beyond it.  The request
handed to the human shrank from "decide how to cut a 656-file branch" to "merge
any two of the small ones".

That measurement took a cycle and lives in a journal.  This module is the
standing place for it, which is the repair shape this project keeps re-deriving
(D-199, D-315, D-322): the cheap command existed every one of those 36 days and
nobody was told to stand there.

Two instruments, because the merge question needs both
------------------------------------------------------

D-323 got its readings wrong twice, in opposite directions, and both times from
choosing one instrument for a question that has two halves:

``base...head`` (three-dot, from the merge base) is **review cost** — what a
human is asked to read.  ``base..head`` (two-dot) is **merge effect** — what
actually changes on ``main``.  Reading three-dot as merge effect manufactured a
live D-011 violation on ``#23`` that two-dot shows is byte-identical to ``main``
(an earlier commit had already reverted it); a worktree was created to strip
files that were not there.  Reading two-dot as review cost would have reported
the same PR as a 152-file monster.

So both are measured and published side by side, and neither is derived from the
other.  A PR can be large to read and a no-op to merge; that is not a
contradiction, it is the two numbers doing their separate jobs.

``UNDECIDABLE`` is a verdict, and here it is the load-bearing one
----------------------------------------------------------------

:mod:`git_surface` recorded the category error this module is most exposed to:
an instrument that reads its source, gets nothing, and returns the nothing in
the vocabulary of a measurement.  The exposure is worse here than in
:mod:`branch_debt`, because the consumer is **gate 1**.  ``gh`` unavailable —
no auth, no network, a CI runner without a token — yields zero PRs, and zero
PRs read as a measurement means *the queue is empty, open as many branches as
you like*.  The failure would fire precisely when the executor cannot see what
it is about to add to.  So an unavailable listing is :data:`UNDECIDABLE`, never
an empty queue, and the tests assert that branch positively.

Usage::

    python3 -m eval.mppi_sandbox.queue_debt report
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from eval.mppi_sandbox import branch_debt as bd

#: The listing could not be read, so no queue statement is available.
UNDECIDABLE = bd.UNDECIDABLE
#: The queue was read and every entry graded.
MEASURED = "MEASURED"

#: Re-exported so a caller grading one entry does not reach into two modules.
WITHIN_PRECEDENT = bd.WITHIN_PRECEDENT
BEYOND_PRECEDENT = bd.BEYOND_PRECEDENT

#: Measured but not yet compared to an envelope.  A distinct verdict rather than
#: a default one: :func:`measure` does not hold the precedent, and a placeholder
#: that happens to spell a real verdict is the same category error this module
#: exists to refuse — it would read as a grade to every caller that forgot to
#: call :func:`graded`.  Nothing published by :func:`report` may carry it.
UNGRADED = "UNGRADED"

#: Branch prefix the executor owns.  The queue gate counts these and no others.
QUEUE_PREFIX = "autoresearch/"


@dataclass(frozen=True)
class Entry:
    """One open PR, measured with both instruments.

    ``review_*`` is three-dot (what a human reads); ``merge_*`` is two-dot (what
    lands on the base).  They are separate fields on purpose — see the module
    docstring.  ``UNDECIDABLE`` here means this one branch could not be measured
    (its remote ref is absent from the clone) while others were.
    """

    number: int
    branch: str
    verdict: str
    review_files: int
    review_insertions: int
    merge_files: int
    merge_insertions: int

    @property
    def is_no_op_merge(self) -> bool:
        """True when reviewing costs something but merging changes nothing.

        The ``#23`` shape.  Published as a property rather than left for a
        reader to infer, because inferring it from the review numbers is exactly
        the mistake D-323 made.
        """
        return (
            self.verdict != UNDECIDABLE
            and self.review_files > 0
            and self.merge_files == 0
            and self.merge_insertions == 0
        )


@dataclass(frozen=True)
class QueueReading:
    """The whole queue, ranked cheapest-review-first."""

    verdict: str
    entries: tuple[Entry, ...]
    precedent_files: int
    precedent_insertions: int
    precedent_n: int

    @property
    def within(self) -> tuple[Entry, ...]:
        """Entries a human could merge without exceeding any prior review."""
        return tuple(e for e in self.entries if e.verdict == WITHIN_PRECEDENT)

    @property
    def beyond(self) -> tuple[Entry, ...]:
        """Entries larger than anything this repository has ever merged."""
        return tuple(e for e in self.entries if e.verdict == BEYOND_PRECEDENT)


def _listing(prefix: str = QUEUE_PREFIX) -> list[tuple[int, str]] | None:
    """Open executor PRs as ``(number, branch)``, or ``None`` if unreadable.

    ``None`` and ``[]`` are different answers and the caller must keep them
    apart: the first is "``gh`` could not tell me", the second is "the queue is
    genuinely empty".  Collapsing them is the failure this module's docstring
    names.
    """
    try:
        out = subprocess.run(
            (
                "gh", "pr", "list", "--state", "open",
                "--json", "number,headRefName", "--limit", "100",
            ),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    try:
        rows = json.loads(out.stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(rows, list):
        return None

    found: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        branch = row.get("headRefName")
        number = row.get("number")
        if not isinstance(branch, str) or not isinstance(number, int):
            return None
        if branch.startswith(prefix):
            found.append((number, branch))
    return found


def _merge_effect(base: str, head: str, paths: list[str]) -> tuple[int, int] | None:
    """How much of ``base`` would actually change, scoped to what ``head`` touched.

    **Not** bare ``git diff base head``.  That comparison is symmetric, so once
    ``base`` has advanced past the merge point it reports ``base``'s own progress
    as though the branch reverted it: measured 2026-08-17, ``#23`` reads 152
    files that way against the 7 it actually touched.  A number labelled "merge
    effect" that is dominated by commits the branch never saw is the mislabelled
    reading this module's docstring is about.

    Scoping the two-dot comparison to the branch's own paths asks the question
    that refuted D-323's false alarm — *of the files this branch changed, how
    many still differ from ``base``* — and is bounded above by the review cost,
    as a merge effect should be.  ``#23`` answers 4 of 7: the other three are the
    ``STATE``/``JOURNAL``/``RESULTS`` files an earlier commit already reverted.
    """
    if not paths:
        return 0, 0
    line = bd._git("diff", "--shortstat", base, head, "--", *paths)
    if line is None:
        return None
    return bd.parse_shortstat(line)


def measure(number: int, branch: str, base: str = "main") -> Entry:
    """Measure one PR with both instruments.

    The head is read from ``origin/<branch>`` rather than a local checkout: the
    queue is a property of what the remote holds, and all but one of these
    branches has no local ref on any given machine.
    """
    empty = Entry(number, branch, UNDECIDABLE, 0, 0, 0, 0)

    head = f"origin/{branch}"
    fork = bd._git("merge-base", base, head)
    if not fork:
        return empty

    # Three-dot: `git diff a...b` is by definition the diff from the merge base,
    # so the review cost needs no second parser.
    review = bd._shortstat(fork, head)
    listing = bd._git("diff", "--name-only", fork, head)
    if review is None or listing is None:
        return empty
    touched = [p for p in listing.splitlines() if p.strip()]

    merge = _merge_effect(base, head, touched)
    if merge is None:
        return empty

    return Entry(
        number=number,
        branch=branch,
        # Not graded here: this function does not hold the envelope.  Grading
        # happens in `graded`, against review cost — the envelope is a statement
        # about what a human has been willing to read, not about what landed.
        verdict=UNGRADED,
        review_files=review[0],
        review_insertions=review[1],
        merge_files=merge[0],
        merge_insertions=merge[1],
    )


def graded(entry: Entry, precedent_files: int, precedent_insertions: int,
           precedent_n: int) -> Entry:
    """Attach a verdict to a measured entry, preserving ``UNDECIDABLE``.

    Split from :func:`measure` so the grade boundary is testable with no
    repository in the way, and so a branch that could not be measured cannot
    acquire a verdict by passing through the grader.
    """
    if entry.verdict == UNDECIDABLE:
        return entry
    verdict = bd.grade(
        entry.review_files,
        entry.review_insertions,
        precedent_files,
        precedent_insertions,
        precedent_n,
    )
    return Entry(
        number=entry.number,
        branch=entry.branch,
        verdict=verdict,
        review_files=entry.review_files,
        review_insertions=entry.review_insertions,
        merge_files=entry.merge_files,
        merge_insertions=entry.merge_insertions,
    )


def rank(entries: tuple[Entry, ...] | list[Entry]) -> tuple[Entry, ...]:
    """Cheapest review first; unmeasurable entries last.

    The ordering is the deliverable.  Gate 1's report exists to tell a human
    which merge is cheap, so the entry a reader's eye lands on first must be the
    one that costs least to act on — not the lowest PR number, which is the
    order ``gh`` happens to return.
    """
    return tuple(
        sorted(
            entries,
            key=lambda e: (
                e.verdict == UNDECIDABLE,
                e.review_files,
                e.review_insertions,
                e.number,
            ),
        )
    )


def read(base: str = "main", prefix: str = QUEUE_PREFIX) -> QueueReading:
    """Measure the whole queue.

    :data:`UNDECIDABLE` unless *both* the listing and the precedent walk
    answered.  A queue measured against an envelope derived from nothing would
    grade every entry ``UNDECIDABLE`` anyway; refusing as a whole says why.
    """
    rows = _listing(prefix)
    if rows is None:
        return QueueReading(UNDECIDABLE, (), 0, 0, 0)

    best_files, best_insertions, seen = bd.precedent(base)
    if seen == 0:
        return QueueReading(UNDECIDABLE, (), 0, 0, 0)

    measured = [
        graded(measure(number, branch, base), best_files, best_insertions, seen)
        for number, branch in rows
    ]
    return QueueReading(
        verdict=MEASURED,
        entries=rank(measured),
        precedent_files=best_files,
        precedent_insertions=best_insertions,
        precedent_n=seen,
    )


def summary(reading: QueueReading) -> str:
    """The one line gate 1 should print instead of ``6/6``."""
    if reading.verdict == UNDECIDABLE:
        return (
            "queue_debt — UNDECIDABLE: the PR listing or the merge history "
            "could not be read, so the queue's depth is unknown.  This is not "
            "an empty queue."
        )
    total = len(reading.entries)
    inside = len(reading.within)
    return (
        f"queue_debt — {total} open, {inside} inside the envelope "
        f"({reading.precedent_files} files / +{reading.precedent_insertions} "
        f"over {reading.precedent_n} merged commits)."
    )


def report(base: str = "main", prefix: str = QUEUE_PREFIX) -> str:
    """Full ranked reading — the cheapest merge is the first row."""
    reading = read(base, prefix)
    lines = [summary(reading)]
    if reading.verdict == UNDECIDABLE:
        return lines[0]

    lines.append("")
    lines.append("  cheapest review first — review cost | merge effect")
    for e in reading.entries:
        if e.verdict == UNDECIDABLE:
            lines.append(
                f"  UNDECIDABLE      #{e.number} {e.branch} "
                "— no remote ref in this clone"
            )
            continue
        tail = "  (no-op merge)" if e.is_no_op_merge else ""
        lines.append(
            f"  {e.verdict:<16} #{e.number} {e.branch}: "
            f"{e.review_files}f/+{e.review_insertions} | "
            f"{e.merge_files}f/+{e.merge_insertions}{tail}"
        )
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI shim
    import sys

    print(report())
    sys.exit(0)
