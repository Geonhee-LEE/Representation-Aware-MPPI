"""Did the cycle do what its journal says it did?

The journal's ``## Artifacts`` block is the one part of a cycle report that is
not a description of the work but a **claim about the repository**::

    - PR: #67 (existing — no new review bandwidth)
    - Files touched: `eval/mppi_sandbox/loop_reach.py` (new), ...
    - TSV row appended: yes

Every other section is prose, answerable only by reading.  These lines are
checkable, and nothing has ever checked them.

Why now: the claims are written **before** the cycle ends
---------------------------------------------------------

Phase 4a writes the journal; the TSV row and the push come after it.  So
``TSV row appended: yes`` is not a record of an append, it is a *prediction*
that one is about to happen — and a cycle that runs out of budget, or dies, or
simply forgets, leaves the prediction standing as though it were a reading.

That is not hypothetical.  Three cases were known before this module existed:

==================  ==========================================  ================
cycle               what the journal says                       what the tree says
==================  ==========================================  ================
2026-08-06 09:00    ``TSV row appended: yes``                   no row
2026-08-06 18:00    ``yes``, and the TSV in *Files touched*     no row, not in diff
2026-08-06 21:00    ``yes``                                     no row
==================  ==========================================  ================

The 09:00 case is this module's **negative control**: it was found by hand by
the 10:00 cycle, which recovered the orphaned commits and wrote the finding
down, so its answer is known independently of anything here.  An instrument
whose first test is a case whose answer is already known is D-102's lesson,
learned when a first cut returned a clean "nothing found" and was simply too
weak to see anything.

Run over the whole branch, **4 cycles are flagged by both dating keys and 5
more by exactly one** — so the population is somewhere in ``[4, 9]`` out of 100,
and the reading deliberately stops there rather than picking a key.  The three
cases above are inside it on evidence that needs no key at all.  Every one of
them reads as a complete cycle in the journal.

The second claim is the one that goes quiet
-------------------------------------------

D-104's own key learning reads: *a cycle that never pushes leaves no red
anywhere*.  Its journal, TSV and STATE all describe a tree that never left the
machine.  It wrote that sentence about the 18:00 cycle **and then did the same
thing** — ``origin`` sat at ``85e0bc7`` while two cycles of work, two ``D-NNN``
entries and a repaired red accumulated locally.  The push gate (D-082) is not at
fault: it fails closed and it never ran, because nothing reached it.  A gate
that is never reached raises no alarm, which is precisely why the absence needs
its own instrument.

So :func:`published` asks the only question that distinguishes the two states —
is this cycle's journal file present in ``origin/<branch>``?  The journal is
committed in 4a and travels with the work, so its absence from the remote is
exactly the absence of the cycle.

The newest cycle is exempt, and the exemption is derived
--------------------------------------------------------

A cycle in flight has written its journal and not yet pushed; that is the normal
state, not a finding.  So :func:`unpublished` skips the **newest** cycle — not a
named one, not a list to maintain, but whichever is last by stamp.  Two
consecutive silent cycles therefore go red on the second, which is one cycle of
detection latency and is what would have fired at 21:00.

Dating a row: three candidate keys, and none of them is sound alone
-------------------------------------------------------------------

A TSV row discharges the claim of the latest cycle at or before it.  Not a
tolerance window: a window wide enough to cover a cycle that overran is also
wide enough to let one row satisfy two claims, and *over*-crediting is the
direction that reads clean.  The hard part is not the matching rule.  It is
**what time a row happens at**, and three fields answer differently.

``timestamp`` (hand-typed)
    Refuted first.  A cycle that overruns types the hour it *finished* in: the
    row stamped ``2026-08-06T04:05`` carries ``sandbox:pass=1048`` and the text
    of D-093, which is the **02:00** cycle's work.  Reading this column
    convicted 02:00 and credited 04:00 — one error in each direction from one
    transcribed field, and the first cut of this module shipped it.

``commit`` (what the row *records*)
    The sha is a git object with a real date (``315d74f`` → 02:46), so it says
    which cycle's work the row is about.  Its failure mode: a row appended
    **retroactively** by a later cycle still names the earlier cycle's sha, so
    the silent cycle reads ``HONOURED`` for a row it did not write.  This is not
    hypothetical — repairing the 18:00 and 21:00 rows made both findings vanish
    under this key, which is D-102's lesson (a repair deletes its own evidence)
    arriving from a new direction.

``git blame`` (when the row was *appended*)
    Answers the question the claim actually makes.  Its failure mode: cycles
    that batch two rows into one TSV commit.  ``a165d1f`` and ``9fe05a0`` each
    appended two, so both rows land on one cycle and its neighbour reads as
    silent — falsely convicting 08-05 07:00 and 11:00.

Both surviving keys fail in the **same** direction, over-reporting, and on
disjoint cases.  So :func:`unsupported` publishes their **intersection** and
:func:`disputed` publishes the residue, and the module declines to pick a
winner: an instrument built to catch over-claiming may not itself over-claim.
The size of the true population is therefore **not settled here** — see Q-099.

What *is* settled is the three cases established independently of any key: the
09:00 cycle (found by hand by the 10:00 cycle) and the 18:00 and 21:00 cycles
(read directly out of `git show --stat`, which shows neither commit touching
the TSV at all).  Those are findings on evidence, not on a dating rule, and
:data:`KNOWN_UNSUPPORTED` in the tests pins them.

Assignment is total and injective under either key, so a cycle is ``HONOURED``
only if a row is its own.

Grades, and only one of them is a finding
-----------------------------------------

==================  ===========================================================
``HONOURED``        claimed yes, a row is assigned to it
``UNSUPPORTED``     claimed yes, no row — **the finding**
``CONSISTENT_NO``   claimed no, no row
``UNDERCLAIMED``    claimed no, but a row is assigned — harmless, still named
``UNPARSED``        no ``TSV row appended`` line to grade
==================  ===========================================================

``UNDERCLAIMED`` is reported and is not a finding.  Grading it as one would make
the honest direction expensive, and the asymmetry between the two directions is
the whole reason this module exists.

Usage::

    python3 -m eval.mppi_sandbox.cycle_artifacts report
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: git needs ``PATH``/``HOME``; the timezone is set per call so a run on a box
#: configured for another zone reads the same cycle hours the journals do.
_ENV = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}

JOURNAL_DIR = REPO_ROOT / "journal"

RESULTS_DIR = REPO_ROOT / "results"


def _root(root: Path | None) -> Path:
    """Which repository to read.  ``None`` means this one.

    Every reader below takes a keyword-only ``root`` rather than closing over
    :data:`REPO_ROOT`, because a guard that can only be run against the repo it
    lives in cannot be **executed** against a constructed failure — which is
    precisely what :mod:`guard_direction` has to do to answer whether the guard
    goes quiet when its rule breaks.  The two existing probed guards took a
    ``root`` from the start; this module did not, and that was the whole of why
    it could not be probed.
    """
    return REPO_ROOT if root is None else Path(root)

#: Ordered worst-last so :func:`census` and reports sort stably.
GRADES: tuple[str, ...] = (
    "UNSUPPORTED",
    "UNDERCLAIMED",
    "UNPARSED",
    "CONSISTENT_NO",
    "HONOURED",
)


def finding_grades() -> frozenset[str]:
    """Which grades are findings — recomputed, not typed.

    A finding is the **over-claiming** direction: the journal said a row exists
    and none does.  So the set is derived by handing :func:`grade_tsv` exactly
    that probe, which makes it watched by whatever watches the grader (D-077's
    cheap repair) instead of being a typed allow-list with no enumerator —
    which is what the first cut shipped, and what `unwatched_exemptions` went
    five-to-six over within one test run of it being written, for the fifth
    time on this branch (D-073 / D-080 / D-101 / D-103).

    Spelled as a call at each use site rather than assigned to a module
    constant, per D-104: assigning it back to a global reads ``TYPED`` however
    it was computed, and would take the guard out of the census entirely —
    recording this repair as a disappearance rather than as a payment.
    """
    over_claim = Cycle(path="<probe>", minute=0, stamp="", branch="", tsv_claim="yes")
    return frozenset({grade_tsv(over_claim, 0)})


_CYCLE_RE = re.compile(r"^-\s+\*\*Cycle\*\*:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2})")
_BRANCH_RE = re.compile(r"^-\s+\*\*Branch\*\*:.*?`(autoresearch/[\w./-]+)`")
_TSV_CLAIM_RE = re.compile(r"^-\s+TSV row appended:\s*([A-Za-z]+)", re.MULTILINE)
_TSV_ROW_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})")


@dataclass(frozen=True)
class Cycle:
    """One journal file's checkable claims."""

    path: str
    """Repo-relative path, which is also the key :func:`published` asks git for."""

    minute: int
    """Minutes since epoch-of-file-set.  Only ordering and comparison matter."""

    stamp: str
    """``YYYY-MM-DD HH:MM``, as written in the file."""

    branch: str
    """``autoresearch/...`` or ``""`` for a skip cycle that produced none."""

    tsv_claim: str
    """Lowercased claim word, or ``""`` when the line is absent."""


def _minutes(date: str, hh: str, mm: str) -> int:
    y, mo, d = (int(p) for p in date.split("-"))
    return ((y * 12 + mo) * 31 + d) * 1440 + int(hh) * 60 + int(mm)


def parse(path: Path, *, root: Path | None = None) -> Cycle | None:
    """Read one journal file's header and TSV claim.

    Returns ``None`` for a file with no ``Cycle`` stamp — ``journal/README.md``
    and the monthly index files are not cycle reports and must not be graded as
    silent ones.
    """
    text = path.read_text(encoding="utf-8")
    stamp_m = branch = None
    for line in text.splitlines():
        if stamp_m is None:
            stamp_m = _CYCLE_RE.match(line)
        if branch is None:
            b = _BRANCH_RE.match(line)
            if b:
                branch = b.group(1)
        if stamp_m is not None and branch is not None:
            break
    if stamp_m is None:
        return None
    claim_m = _TSV_CLAIM_RE.search(text)
    date, hh, mm = stamp_m.group(1), stamp_m.group(2), stamp_m.group(3)
    try:
        rel = str(path.relative_to(_root(root)))
    except ValueError:
        # A file outside the repo — only the tests construct these.  Keep the
        # absolute path rather than inventing a repo-relative one, so a git
        # question asked about it fails loudly instead of hitting a real file.
        rel = str(path)
    return Cycle(
        path=rel,
        minute=_minutes(date, hh, mm),
        stamp=f"{date} {hh}:{mm}",
        branch=branch or "",
        tsv_claim=(claim_m.group(1).lower() if claim_m else ""),
    )


def _parsed(root: Path | None) -> list[Cycle]:
    base = _root(root) / "journal"
    return [c for c in (parse(p, root=root) for p in sorted(base.rglob("*.md")))
            if c is not None]


def cycles(branch: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """Every journal entry naming ``branch``, oldest first.

    Skip cycles (``Branch: none``) are excluded here rather than dropped
    silently — :func:`census` publishes their count under ``no_branch`` so the
    exclusion is a number somebody can read, not an unstated filter.
    """
    return tuple(
        sorted(
            (c for c in _parsed(root) if c.branch == branch),
            key=lambda c: (c.minute, c.path),
        )
    )


def skipped_cycles(*, root: Path | None = None) -> tuple[Cycle, ...]:
    """Journal entries that name no branch — counted, never graded."""
    return tuple(c for c in _parsed(root) if not c.branch)


def tsv_path(branch: str, *, root: Path | None = None) -> Path:
    return _root(root) / "results" / f"{branch.split('/')[-1]}.tsv"


def _commit_minute(sha: str, root: Path | None = None) -> int | None:
    """When git says the commit was written, or ``None`` if it does not resolve."""
    if not sha or not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        return None
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%cd", "--date=format-local:%Y-%m-%d %H %M", sha],
        cwd=_root(root),
        capture_output=True,
        text=True,
        env={**_ENV, "TZ": "Asia/Seoul"},
    )
    if proc.returncode != 0:
        return None
    parts = proc.stdout.strip().split()
    if len(parts) != 3:
        return None
    return _minutes(parts[0], parts[1], parts[2])


def _blame_minutes(path: Path, root: Path | None = None) -> dict[int, int]:
    """Line number (1-based) → minute of the commit that **added** that line.

    ``git blame`` answers *when the row was appended*, which is a different
    question from the row's ``commit`` column — and the difference is the whole
    point.  A retroactive row appended by a later cycle names an earlier
    cycle's sha in its own text; keying on that text would credit the silent
    cycle with a row it did not write, which is exactly the over-crediting this
    module exists to refuse.  Lines not yet committed blame to the all-zero sha
    and are reported as absent.
    """
    proc = subprocess.run(
        ["git", "blame", "--line-porcelain", "--", str(path)],
        cwd=_root(root),
        capture_output=True,
        text=True,
        env={**_ENV, "TZ": "Asia/Seoul"},
    )
    if proc.returncode != 0:
        return {}
    out: dict[int, int] = {}
    lineno = None
    for line in proc.stdout.splitlines():
        head = line.split(" ")
        if len(head) >= 3 and re.fullmatch(r"[0-9a-f]{40}", head[0]):
            lineno = int(head[2]) if head[2].isdigit() else None
            uncommitted = head[0] == "0" * 40
        elif line.startswith("committer-time ") and lineno is not None:
            if not uncommitted:
                t = time.localtime(int(line.split(" ", 1)[1]))
                out[lineno] = _minutes(
                    f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}",
                    f"{t.tm_hour:02d}",
                    f"{t.tm_min:02d}",
                )
            lineno = None
    return out


KEYS: tuple[str, ...] = ("appended", "records")
"""The two ways to date a TSV row.  Neither alone is sound — see the module
docstring; :func:`unsupported` publishes only what both agree on."""


def tsv_rows(branch: str, key: str = "appended",
             *, root: Path | None = None) -> tuple[tuple[int, bool], ...]:
    """``(minute, dated_by_git)`` for each row of ``results/<slug>.tsv``.

    The minute is **when the row was appended**, read from ``git blame``.  The
    hand-typed ``timestamp`` column is used only for rows git cannot date — a
    line not yet committed — and the flag is what makes that fallback
    countable rather than silently mixed in.

    The row's own ``commit`` column is deliberately *not* the key.  It was the
    key for one draft of this module, and it is right for the ordinary case and
    wrong for the case that matters: a row appended retroactively by a later
    cycle carries the silent cycle's sha in its text, and keying on the text
    would mark that cycle ``HONOURED`` for a row it did not write.  Two fields
    that agree in the common case and disagree in the interesting one — D-104's
    shape a third time on this branch.
    """
    if key not in KEYS:
        raise ValueError(f"unknown key {key!r}; expected one of {KEYS}")
    path = tsv_path(branch, root=root)
    if not path.exists():
        return ()
    blame = _blame_minutes(path, root) if key == "appended" else {}
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        m = _TSV_ROW_RE.match(line)
        if not m:
            continue
        if key == "appended" and i in blame:
            out.append((blame[i], True))
            continue
        if key == "records":
            fields = line.split("\t")
            by_sha = _commit_minute(fields[1].strip(), root) if len(fields) > 1 else None
            if by_sha is not None:
                out.append((by_sha, True))
                continue
        out.append((_minutes(m.group(1), m.group(2), m.group(3)), False))
    return tuple(sorted(out))


def tsv_stamps(branch: str, key: str = "appended",
               *, root: Path | None = None) -> tuple[int, ...]:
    return tuple(m for m, _ in tsv_rows(branch, key, root=root))


def assignment(branch: str, key: str = "appended",
               *, root: Path | None = None) -> dict[str, int]:
    """How many TSV rows belong to each cycle.

    A row belongs to the latest cycle at or before it.  Rows earlier than every
    cycle belong to none and are reported by :func:`orphan_rows`; they are not
    an error, only evidence that the journal set does not reach back that far.
    """
    ordered = cycles(branch, root=root)
    counts = {c.path: 0 for c in ordered}
    for stamp in tsv_stamps(branch, key, root=root):
        owner = None
        for c in ordered:
            if c.minute <= stamp:
                owner = c
            else:
                break
        if owner is not None:
            counts[owner.path] += 1
    return counts


def orphan_rows(branch: str, *, root: Path | None = None) -> int:
    """TSV rows predating every journal entry — outside this reading's reach."""
    ordered = cycles(branch, root=root)
    if not ordered:
        return len(tsv_stamps(branch, root=root))
    first = ordered[0].minute
    return sum(1 for s in tsv_stamps(branch, root=root) if s < first)


def grade_tsv(cycle: Cycle, rows: int) -> str:
    if cycle.tsv_claim not in ("yes", "no"):
        return "UNPARSED"
    if cycle.tsv_claim == "yes":
        return "HONOURED" if rows else "UNSUPPORTED"
    return "UNDERCLAIMED" if rows else "CONSISTENT_NO"


def graded(branch: str, key: str = "appended",
           *, root: Path | None = None) -> tuple[tuple[Cycle, str, int], ...]:
    counts = assignment(branch, key, root=root)
    return tuple(
        (c, grade_tsv(c, counts[c.path]), counts[c.path])
        for c in cycles(branch, root=root)
    )


def _flagged(branch: str, key: str, root: Path | None = None) -> set[str]:
    return {c.path for c, g, _ in graded(branch, key, root=root)
            if g in finding_grades()}


def unsupported(branch: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """Cycles both keys agree claimed a TSV row and have none.  The finding.

    The intersection, not either key alone.  Each key has a failure mode the
    other does not, both in the over-reporting direction, so their agreement is
    the only part of the reading that does not rest on an unverified choice.
    """
    both = _flagged(branch, "appended", root) & _flagged(branch, "records", root)
    return tuple(c for c in cycles(branch, root=root) if c.path in both)


def disputed(branch: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """Cycles exactly one key flags — reported, never published as a finding."""
    a = _flagged(branch, "appended", root)
    r = _flagged(branch, "records", root)
    return tuple(c for c in cycles(branch, root=root) if c.path in (a ^ r))


def unsupported_by(branch: str, key: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """:func:`unsupported` with the second key's agreement **suppressed**.

    The same population read through one key instead of the intersection of two
    — the ``read_unexempted`` half of :mod:`guard_direction`'s probe.  It is
    written as a call into :func:`_flagged` rather than as a second copy of the
    grading, for the reason every ``read_unexempted`` in that module is: a
    re-implementation would be a second statement of the rule, and D-045/D-047
    are both about what happens to the copy nobody re-derives.
    """
    flagged = _flagged(branch, key, root)
    return tuple(c for c in cycles(branch, root=root) if c.path in flagged)


def _remote_has(branch: str, path: str, root: Path | None = None) -> bool | None:
    """Is ``path`` in ``origin/<branch>``?  ``None`` when the ref is unreadable."""
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"origin/{branch}:{path}"],
        cwd=_root(root),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if "Not a valid object name" in proc.stderr or "does not exist" in proc.stderr:
        return False
    # A missing ref and a missing path fail the same way on some git versions,
    # so distinguish them explicitly rather than reading absence as clean.
    ref = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"origin/{branch}"],
        cwd=_root(root),
        capture_output=True,
        text=True,
    )
    return False if ref.returncode == 0 else None


def published(cycle: Cycle, *, root: Path | None = None) -> bool | None:
    if not cycle.branch:
        return None
    return _remote_has(cycle.branch, cycle.path, root)


def unpublished(branch: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """Cycles whose journal never reached ``origin``, newest exempted.

    The exemption is the cycle currently in flight, identified by being last —
    never by name.  An unreadable remote yields ``()`` rather than a fabricated
    finding: not knowing is not the same as knowing there is nothing.
    """
    ordered = cycles(branch, root=root)
    if len(ordered) < 2:
        return ()
    out = []
    for c in ordered[:-1]:
        if published(c, root=root) is False:
            out.append(c)
    return tuple(out)


def census(branch: str, *, root: Path | None = None) -> dict[str, int]:
    rows = graded(branch, root=root)
    counts = {g: 0 for g in GRADES}
    for _, g, _ in rows:
        counts[g] += 1
    counts["cycles"] = len(rows)
    rows_ = tsv_rows(branch, root=root)
    counts["tsv_rows"] = len(rows_)
    counts["undated_rows"] = sum(1 for _, dated in rows_ if not dated)
    counts["orphan_rows"] = orphan_rows(branch, root=root)
    counts["no_branch"] = len(skipped_cycles(root=root))
    counts["unpublished"] = len(unpublished(branch, root=root))
    counts["confirmed"] = len(unsupported(branch, root=root))
    counts["disputed"] = len(disputed(branch, root=root))
    return counts


def report(branch: str, *, root: Path | None = None) -> str:
    rows = graded(branch, root=root)
    counts = census(branch, root=root)
    silent = {c.path for c in unpublished(branch, root=root)}
    lines = [
        f"cycle_artifacts — do the journals' Artifacts claims hold?  ({branch})",
        "",
        f"  cycles graded:      {counts['cycles']}"
        f"   (skip cycles excluded: {counts['no_branch']})",
        f"  TSV rows:           {counts['tsv_rows']}"
        f"   (predating the journal set: {counts['orphan_rows']})",
        f"  unsupported claims: {counts['confirmed']} confirmed by both keys"
        f"  (+{counts['disputed']} disputed, one key only)",
        f"  never pushed:       {counts['unpublished']}  (newest cycle exempt)",
        "  by grade: " + ", ".join(f"{g}={counts[g]}" for g in GRADES if counts[g]),
        "",
    ]
    for c, g, n in rows:
        mark = "  SILENT" if c.path in silent else ""
        lines.append(f"  {g:<14} rows={n}  {c.stamp}  {c.path}{mark}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] != "report":
        print(
            "usage: python3 -m eval.mppi_sandbox.cycle_artifacts report [branch]",
            file=sys.stderr,
        )
        return 2
    branch = argv[1] if len(argv) > 1 else current_branch()
    print(report(branch))
    return 0


def current_branch(*, root: Path | None = None) -> str:
    """Which branch's cycles to grade.  ``""`` when git cannot say.

    Takes a ``root`` for the same reason every reader above does: a caller that
    wants to grade a *constructed* repository — which is the only way to test a
    guard against a failure that is not in this repo's history — cannot do it
    against a hard-coded :data:`REPO_ROOT`.  This one was the last hold-out, and
    it was the one :func:`push_preflight._unsupported_frontier` needed.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=_root(root),
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
