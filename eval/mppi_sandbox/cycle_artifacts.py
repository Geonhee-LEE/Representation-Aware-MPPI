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

Run over the whole branch, the population is **6 of 99** — the three above and
three nobody had looked for, on 2026-08-05 at 10:00, 13:00 and 14:00.  So the
rate is about one cycle in sixteen, and every one of them reads as a complete
cycle in the journal.

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

Matching is one row, one claim — and the row's own timestamp is not the key
---------------------------------------------------------------------------

A TSV row discharges the claim of the latest cycle at or before it.  Not a
tolerance window: a window wide enough to cover a cycle that overran is also
wide enough to let one row satisfy two claims, and *over*-crediting is the
direction that reads clean.

The first cut of this module read the row's ``timestamp`` column and reported
**nine** unsupported claims.  Two were wrong.  That column is hand-typed, and a
cycle that overruns its budget types the hour it finished in rather than the
hour it belongs to: the row stamped ``2026-08-06T04:05`` carries
``sandbox:pass=1048`` and the text of D-093, which is the **02:00** cycle's
work, and it was assigned to 04:00 — crediting a cycle that appended nothing and
convicting one that appended.  One error in each direction from one transcribed
field.

The row's ``commit`` column is not transcribed.  It is a git object, and git
knows when it was written: ``315d74f`` is dated 02:46.  So assignment keys on
the **commit date**, and the typed timestamp is used only for rows whose sha
does not resolve (``pending``, or a commit that never survived a rebase).  Those
are counted as ``undated_rows`` rather than silently mixed in, because a
fallback nobody can see is a second transcription wearing the first one's name —
D-047's shape, and D-104's.

Assignment is total and injective by construction, so a cycle is ``HONOURED``
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
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

#: git needs ``PATH``/``HOME``; the timezone is set per call so a run on a box
#: configured for another zone reads the same cycle hours the journals do.
_ENV = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}

JOURNAL_DIR = REPO_ROOT / "journal"

RESULTS_DIR = REPO_ROOT / "results"

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


def parse(path: Path) -> Cycle | None:
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
        rel = str(path.relative_to(REPO_ROOT))
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


def cycles(branch: str) -> tuple[Cycle, ...]:
    """Every journal entry naming ``branch``, oldest first.

    Skip cycles (``Branch: none``) are excluded here rather than dropped
    silently — :func:`census` publishes their count under ``no_branch`` so the
    exclusion is a number somebody can read, not an unstated filter.
    """
    found = [parse(p) for p in sorted(JOURNAL_DIR.rglob("*.md"))]
    return tuple(
        sorted(
            (c for c in found if c is not None and c.branch == branch),
            key=lambda c: (c.minute, c.path),
        )
    )


def skipped_cycles() -> tuple[Cycle, ...]:
    """Journal entries that name no branch — counted, never graded."""
    found = [parse(p) for p in sorted(JOURNAL_DIR.rglob("*.md"))]
    return tuple(c for c in found if c is not None and not c.branch)


def tsv_path(branch: str) -> Path:
    return RESULTS_DIR / f"{branch.split('/')[-1]}.tsv"


def _commit_minute(sha: str) -> int | None:
    """When git says the commit was written, or ``None`` if it does not resolve."""
    if not sha or not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        return None
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%cd", "--date=format-local:%Y-%m-%d %H %M", sha],
        cwd=REPO_ROOT,
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


def tsv_rows(branch: str) -> tuple[tuple[int, bool], ...]:
    """``(minute, dated_by_git)`` for each row of ``results/<slug>.tsv``.

    The minute comes from the row's ``commit`` sha wherever git can resolve it,
    and from the hand-typed ``timestamp`` column only when it cannot.  The flag
    is what makes the fallback countable.
    """
    path = tsv_path(branch)
    if not path.exists():
        return ()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _TSV_ROW_RE.match(line)
        if not m:
            continue
        fields = line.split("\t")
        by_git = _commit_minute(fields[1].strip()) if len(fields) > 1 else None
        if by_git is not None:
            out.append((by_git, True))
        else:
            out.append((_minutes(m.group(1), m.group(2), m.group(3)), False))
    return tuple(sorted(out))


def tsv_stamps(branch: str) -> tuple[int, ...]:
    return tuple(m for m, _ in tsv_rows(branch))


def assignment(branch: str) -> dict[str, int]:
    """How many TSV rows belong to each cycle.

    A row belongs to the latest cycle at or before it.  Rows earlier than every
    cycle belong to none and are reported by :func:`orphan_rows`; they are not
    an error, only evidence that the journal set does not reach back that far.
    """
    ordered = cycles(branch)
    counts = {c.path: 0 for c in ordered}
    for stamp in tsv_stamps(branch):
        owner = None
        for c in ordered:
            if c.minute <= stamp:
                owner = c
            else:
                break
        if owner is not None:
            counts[owner.path] += 1
    return counts


def orphan_rows(branch: str) -> int:
    """TSV rows predating every journal entry — outside this reading's reach."""
    ordered = cycles(branch)
    if not ordered:
        return len(tsv_stamps(branch))
    first = ordered[0].minute
    return sum(1 for s in tsv_stamps(branch) if s < first)


def grade_tsv(cycle: Cycle, rows: int) -> str:
    if cycle.tsv_claim not in ("yes", "no"):
        return "UNPARSED"
    if cycle.tsv_claim == "yes":
        return "HONOURED" if rows else "UNSUPPORTED"
    return "UNDERCLAIMED" if rows else "CONSISTENT_NO"


def graded(branch: str) -> tuple[tuple[Cycle, str, int], ...]:
    counts = assignment(branch)
    return tuple(
        (c, grade_tsv(c, counts[c.path]), counts[c.path]) for c in cycles(branch)
    )


def unsupported(branch: str) -> tuple[Cycle, ...]:
    """Cycles that claimed a TSV row and have none.  The finding."""
    return tuple(c for c, g, _ in graded(branch) if g in finding_grades())


def _remote_has(branch: str, path: str) -> bool | None:
    """Is ``path`` in ``origin/<branch>``?  ``None`` when the ref is unreadable."""
    proc = subprocess.run(
        ["git", "cat-file", "-e", f"origin/{branch}:{path}"],
        cwd=REPO_ROOT,
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
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return False if ref.returncode == 0 else None


def published(cycle: Cycle) -> bool | None:
    if not cycle.branch:
        return None
    return _remote_has(cycle.branch, cycle.path)


def unpublished(branch: str) -> tuple[Cycle, ...]:
    """Cycles whose journal never reached ``origin``, newest exempted.

    The exemption is the cycle currently in flight, identified by being last —
    never by name.  An unreadable remote yields ``()`` rather than a fabricated
    finding: not knowing is not the same as knowing there is nothing.
    """
    ordered = cycles(branch)
    if len(ordered) < 2:
        return ()
    out = []
    for c in ordered[:-1]:
        if published(c) is False:
            out.append(c)
    return tuple(out)


def census(branch: str) -> dict[str, int]:
    rows = graded(branch)
    counts = {g: 0 for g in GRADES}
    for _, g, _ in rows:
        counts[g] += 1
    counts["cycles"] = len(rows)
    rows_ = tsv_rows(branch)
    counts["tsv_rows"] = len(rows_)
    counts["undated_rows"] = sum(1 for _, dated in rows_ if not dated)
    counts["orphan_rows"] = orphan_rows(branch)
    counts["no_branch"] = len(skipped_cycles())
    counts["unpublished"] = len(unpublished(branch))
    return counts


def report(branch: str) -> str:
    rows = graded(branch)
    counts = census(branch)
    silent = {c.path for c in unpublished(branch)}
    lines = [
        f"cycle_artifacts — do the journals' Artifacts claims hold?  ({branch})",
        "",
        f"  cycles graded:      {counts['cycles']}"
        f"   (skip cycles excluded: {counts['no_branch']})",
        f"  TSV rows:           {counts['tsv_rows']}"
        f"   (predating the journal set: {counts['orphan_rows']})",
        f"  unsupported claims: {counts['UNSUPPORTED']}",
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


def current_branch() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
