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

**The premise has a window, and D-110 names it.**  "Newest == in flight" is true
only *after* the running cycle writes its journal at 4a.  Before that write the
newest journal on disk belongs to the cycle that just **ended** — so a
predecessor that committed and died before pushing occupies the exempt slot and
grades clean.  That is not an edge case; it is the state every cycle is in
during REVIEW, which is the one moment the stranding is still cheap to repair.
Measured on 2026-08-07 07:00: two cycles stranded (``07-03``, ``07-06``),
:func:`unpublished` named **one**.  Two repairs, neither of which changes the
default: *in_flight* lets a caller state what is actually in flight instead of
inferring it from order, and :func:`frontier_stranded` **publishes** the
observation the exemption discards.  Discarding it was the defect — the
exemption itself is sound (D-038: an exclusion stated is auditable, one implied
is a hole).

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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .tsv_timestamp import KST as _KST

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

    ``committer-time`` is a **raw epoch**, so the ``TZ`` pinned on the
    subprocess below does not reach it — that env var only steers git's own
    date *formatting*, which ``--line-porcelain`` does not use for this field.
    The conversion therefore happens here, and it must name its zone: an
    ambient ``time.localtime`` reads KST on the developer's machine and **UTC
    on a GitHub runner**, shifting every row nine hours earlier and reassigning
    it to whichever cycle then precedes it.  That is D-231 — the whole of the
    CI/local census divergence that D-228 → D-230 spent four cycles excluding
    tree, commit, depth, process shape and (wrongly) timezone from.
    :func:`tsv_timestamp._blame_times` parses the same field and always got
    this right; ``KST`` is imported from there rather than respelled so the two
    readers cannot drift apart again (D-047).
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
                t = datetime.fromtimestamp(int(line.split(" ", 1)[1]), tz=_KST)
                out[lineno] = _minutes(
                    f"{t.year:04d}-{t.month:02d}-{t.day:02d}",
                    f"{t.hour:02d}",
                    f"{t.minute:02d}",
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


PENDING_CLAIM = "pending"
"""The word 4a writes **in place of** a claim, before the append has happened.

:func:`grade_tsv` sends anything that is not ``yes``/``no`` to ``UNPARSED``, so a
journal carrying this word states nothing and is graded as stating nothing.  That
is the entire mechanism: the over-claim that this module was built to catch is
not prevented by checking the claim harder, it is prevented by **not making it
yet**.  A cycle that dies between 4a and the append then leaves an honest
journal rather than a permanent scar.
"""

NO_CYCLE = "NO_CYCLE"
"""No journal to grade — distinct from grading one and finding nothing wrong."""

IDENTIFIED = "IDENTIFIED"
"""The newest journal is this cycle's own 4a — the claim reading means what it says."""

INFLIGHT_UNKNOWN = "INFLIGHT_UNKNOWN"
"""No wrapper log to read an hour off — the caller is not inside a cron cycle.

Fails **open**: manual invocations and the tests have no run in flight, and a
guard that refused there would be a guard nobody could run by hand.  The
misidentification this module now catches is specific — *a cycle grading its
predecessor while believing it is grading itself* — and that requires knowing
which hour is in flight.  Not knowing is not evidence of the defect.
"""

NO_INFLIGHT_JOURNAL = "NO_INFLIGHT_JOURNAL"
"""The newest journal belongs to a **previous** cycle: this one has no 4a yet.

The trap D-202 pins.  On 2026-08-11 20:00 a repair cycle ran ``claim`` after its
TSV append but before writing its own 4a; :func:`_claim_rows` fell through to
``ordered[-1]``, which was the *19:00* journal, and the CLI announced it as "the
in-flight cycle's TSV claim" and printed ``yes`` as the line to paste.  Pasting
it into 19:00 made that cycle ``UNSUPPORTED`` the instant this cycle's own 4a
landed and the row reassigned by timestamp — a scar no later repair can reach.

The instrument was not wrong about the rows.  It was wrong about **whose** rows,
and it said so in a sentence that asserted the opposite.  ``cycle_path`` already
existed as the opt-in repair (D-110's, applied a second time), but an opt-in
that the default path silently declines is not a guard: the caller who needed it
was the caller who did not know to pass it.
"""


def _hour_key(stamp: str) -> str:
    """``"2026-08-11 21:00"`` → ``"2026-08-11T21"``, :attr:`Run.hour`'s spelling."""
    return stamp[:13].replace(" ", "T")


def inflight_hour(*, root: Path | None = None,
                  now: "datetime | None" = None) -> str | None:
    """Which hour is holding the wrapper's ``flock``, or ``None`` if unreadable.

    Read from the wrapper's own log rather than from the wall clock, because the
    two disagree exactly when it matters: a cycle that starts at 21:00 and runs
    a 20-minute suite asks this question at 21:3x, and ``datetime.now()`` would
    answer ``21`` today and ``22`` on any cycle that overran the hour.  The
    wrapper's ``start`` marker is the invoking cycle's identity; the clock is
    only a reading taken during it.
    """
    from . import cycle_wallclock as _cw

    day = (now or datetime.now(_cw._KST)).strftime("%Y-%m-%d")
    path = _cw.log_path(day)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    flight = _cw.in_flight(_cw.parse_log(text), now=now)
    return flight[0].hour if flight else None


def identification(branch: str, *, root: Path | None = None,
                   cycle_path: str | None = None,
                   hour: str | None = None,
                   now: "datetime | None" = None) -> str:
    """Can this reading name the cycle it is about?

    ``IDENTIFIED``
        The graded cycle is the invoking one — either named outright via
        *cycle_path*, or the newest journal's stamp falls in the in-flight hour.
    ``INFLIGHT_UNKNOWN``
        No run in flight to compare against.  Fails open, per that constant.
    ``NO_INFLIGHT_JOURNAL``
        A run *is* in flight and the newest journal is not its 4a.  The reading
        is about a previous cycle and must not be pasted anywhere.

    A caller that passed *cycle_path* is ``IDENTIFIED`` by construction: it was
    told which cycle it is grading, which is the whole point of that parameter.
    """
    if cycle_path is not None:
        return IDENTIFIED
    if hour is None and root is not None:
        # A constructed repo has no relationship to this machine's wrapper log:
        # the run in flight is the *test runner's* cycle, and joining it to a
        # tmp_path journal would grade one repo's hour against another's file.
        # Every caller that wants this guard exercised passes ``hour``.
        return INFLIGHT_UNKNOWN
    running = hour if hour is not None else inflight_hour(root=root, now=now)
    if running is None:
        return INFLIGHT_UNKNOWN
    cycle, _ = _claim_rows(branch, root=root)
    if cycle is None:
        return INFLIGHT_UNKNOWN
    return IDENTIFIED if _hour_key(cycle.stamp) == running else NO_INFLIGHT_JOURNAL


def claim_support(branch: str, *, root: Path | None = None,
                  cycle_path: str | None = None,
                  hour: str | None = None,
                  now: "datetime | None" = None) -> str:
    """Grade one cycle's TSV claim against the tree **as it stands right now**.

    Every other reader in this module grades *committed history*, which is the
    only thing available after the fact and is also why none of them can stop
    the thing they measure.  The scars of 2026-08-09 (09:00, 11:00 and 18:00,
    all ``UNSUPPORTED rows=0``) were not missed by the push gate — the gate
    consumes exactly this population via
    :func:`push_preflight._unsupported_frontier` and it is correct.  Those three
    cycles **never reached it**: they wrote the claim at 4a, died, and pushed
    nothing.  A gate that is never reached raises no alarm, the same sentence
    :func:`unwatched_strandings` was written for, arriving at the write site.

    And the repair cannot follow them.  Row assignment is by timestamp, so a row
    appended at 19:xx to cover the 18:00 cycle assigns to the *19:00* cycle; the
    rescued cycle still reads ``UNSUPPORTED`` forever.  The only hour in which
    the claim is repairable is the one that made it, which is why this reading
    is taken **before the push** and not by a later cycle's census.

    Uncommitted rows count.  :func:`tsv_rows` falls back to the typed timestamp
    column for lines ``git blame`` cannot date, so the row appended moments ago
    and not yet staged is visible here — and after it *is* committed, blame
    dates it and it is visible for the other reason.  Both states read the same
    number, which is what makes this safe to chain onto the push gate:
    :mod:`tsv_timestamp`'s ``check`` grades only *uncommitted* rows and so goes
    vacuous the instant ``git add`` runs, which is why the constitution has to
    place that one by hand rather than chain it.  This one does not go vacuous.

    Only the over-claiming direction is a finding, per the module's standing
    asymmetry: a journal left on :data:`PENDING_CLAIM` because the cycle
    forgot to fill it in grades ``UNPARSED``, which is not a finding and is not
    meant to become one.  Making the honest direction expensive is how a guard
    teaches cycles to write ``yes`` and hope.

    *cycle_path* names the cycle instead of inferring it from position, which is
    D-110's repair applied a second time: "newest == the running cycle" is only
    true after 4a has written the journal, and a caller that can be *told* which
    cycle it is grading should not be made to rely on the ordering.
    """
    state = identification(branch, root=root, cycle_path=cycle_path,
                           hour=hour, now=now)
    if state == NO_INFLIGHT_JOURNAL:
        return NO_INFLIGHT_JOURNAL
    cycle, rows = _claim_rows(branch, root=root, cycle_path=cycle_path)
    return NO_CYCLE if cycle is None else grade_tsv(cycle, rows)


REFUSED_LINE = "(refused — no 4a for the in-flight cycle yet; write it, then re-run)"
"""What :func:`claim_line` emits instead of a claim it cannot attribute.

Deliberately not a valid Artifacts line.  The failure mode being closed is a
caller **pasting** this output, so the refusal has to be unusable as a paste,
not merely accompanied by a warning next to a usable one.
"""


def claim_line(branch: str, *, root: Path | None = None,
               cycle_path: str | None = None,
               hour: str | None = None,
               now: "datetime | None" = None) -> str:
    """The Artifacts line the journal should carry, **read off the tree**.

    The writer half of the same fact :func:`claim_support` grades.  4a used to
    type this line from intent two steps before the append that would make it
    true; the point of emitting it here is that the word comes from counting
    rows, so there is no moment at which a cycle is trusted to predict its own
    future.  D-154 made the same move for the TSV ``timestamp`` field, for the
    same reason: a cycle does not know what it is about to do.
    """
    if identification(branch, root=root, cycle_path=cycle_path,
                      hour=hour, now=now) == NO_INFLIGHT_JOURNAL:
        return REFUSED_LINE
    _, rows = _claim_rows(branch, root=root, cycle_path=cycle_path)
    return f"- TSV row appended: {'yes' if rows else 'no'}"


def _claim_rows(branch: str, *, root: Path | None = None,
                cycle_path: str | None = None) -> tuple[Cycle | None, int]:
    """The cycle being graded and how many rows are assigned to it right now."""
    ordered = cycles(branch, root=root)
    if not ordered:
        return None, 0
    if cycle_path is None:
        cycle = ordered[-1]
    else:
        named = [c for c in ordered if c.path == cycle_path]
        if not named:
            return None, 0
        cycle = named[0]
    return cycle, assignment(branch, "appended", root=root).get(cycle.path, 0)


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


#: ``in_flight`` was not supplied — fall back to the positional exemption.
#: Distinct from ``None``, which is the caller stating that **no** cycle is in
#: flight and every cycle is therefore gradable.
_POSITIONAL = object()


def unpublished(
    branch: str,
    *,
    root: Path | None = None,
    in_flight: object = _POSITIONAL,
) -> tuple[Cycle, ...]:
    """Cycles whose journal never reached ``origin``, the in-flight one exempted.

    The exemption is the cycle currently in flight.  By default it is identified
    by being last — never by name.  An unreadable remote yields ``()`` rather
    than a fabricated finding: not knowing is not the same as knowing there is
    nothing.

    *in_flight* names the exempt cycle's path instead of inferring it, which is
    D-110's repair.  The positional default rests on a premise — "newest ==
    in flight" — that is only true **after** the running cycle has written its
    journal at 4a.  Before that write, the newest journal on disk belongs to the
    *previous* cycle, so a predecessor that committed and died before pushing
    occupies the exempt slot and grades clean.  That is not a corner case: it is
    the state every cycle is in during REVIEW, which is the one moment the
    stranding is still cheap to repair.  Pass ``in_flight=None`` to state that
    no cycle is in flight and grade the whole population; see
    :func:`frontier_stranded` for the fact the default drops.
    """
    ordered = cycles(branch, root=root)
    if len(ordered) < 2:
        return ()
    if in_flight is _POSITIONAL:
        pool = ordered[:-1]
    else:
        pool = [c for c in ordered if c.path != in_flight]
    out = []
    for c in pool:
        if published(c, root=root) is False:
            out.append(c)
    return tuple(out)


def frontier_stranded(branch: str, *, root: Path | None = None) -> Cycle | None:
    """The newest cycle, iff its journal never reached ``origin``.

    Exactly the fact :func:`unpublished`'s positional exemption discards.  The
    exemption is defensible — a cycle in flight has a journal and no push — but
    discarding the observation rather than *reporting* it is what made the
    2026-08-07 06:00 stranding invisible to the 07:00 cycle that could still fix
    it: two cycles were stranded, ``unpublished`` named one.

    Reported, never raised as a finding on its own.  Whether the newest cycle is
    in flight or dead is not knowable from the journal set, and this package's
    standing rule is that an exclusion stated is auditable while one implied is a
    hole (D-038).  ``None`` covers both "published" and "cannot tell".
    """
    ordered = cycles(branch, root=root)
    if not ordered:
        return None
    newest = ordered[-1]
    return newest if published(newest, root=root) is False else None


def stranded(branch: str, *, root: Path | None = None) -> tuple[Cycle, ...]:
    """Every cycle on this branch whose journal never reached ``origin``.

    :func:`unpublished` with the positional exemption **declined**, which is
    what ``in_flight=None`` says.  The body is that one call and nothing else on
    purpose: what was missing was never a rule, it was a *caller*.  D-110 added
    the parameter, Q-103 recorded that nothing passed it, and an instrument with
    no caller is indistinguishable from an instrument with no finding — the same
    sentence :func:`push_preflight._unsupported_frontier` was written to answer,
    one layer up.

    Honest only **before** the running cycle writes its journal at 4a.  Until
    that write, every journal on disk belongs to a cycle that has finished, so
    declining the exemption is not a widening — there is genuinely nobody in
    flight to exempt.  That moment is the REVIEW phase, and it is also the last
    one at which the stranding is still cheap to repair, so the precondition and
    the use case are the same moment.  Called after 4a it names the in-flight
    cycle too, which is precisely why this reading is wired into REVIEW and
    **not** into the push gate.
    """
    return unpublished(branch, root=root, in_flight=None)


def unwatched_strandings(
    branch: str, *, root: Path | None = None
) -> tuple[Cycle, ...]:
    """Stranded cycles that no reading anybody takes would name.

    The push gate consumes ``unsupported ∩ unpublished``
    (:func:`push_preflight._unsupported_frontier`), so a stranded cycle whose
    Artifacts claims happen to be **honest** falls in no population at all: not
    the gate's, because it is not lying; not :func:`unsupported`'s, for the same
    reason; and not a human's, because nothing prints it.  It is the *difference*
    of two sets each of which has a reader.

    Measured on 2026-08-07 09:00: ``07-03`` and ``07-06`` had been stranded six
    hours, both graded ``HONOURED``, and the 06:00 cycle's ``STATE.md`` said
    "pushed" over the top of them.  Two later cycles ran a full REVIEW against
    that state and neither could have seen it.

    Named rather than folded into :func:`stranded`, because the count that
    matters for the wiring decision is this one: if it is empty the gate already
    covers the branch and REVIEW's reading is redundant; if it is not, the gate
    structurally cannot cover it and the reading has to live somewhere else.
    """
    lying = {c.path for c in unsupported(branch, root=root)}
    return tuple(c for c in stranded(branch, root=root) if c.path not in lying)


#: How a stranded cycle's own commit graded the tree it left behind.  Ordered
#: best-first: only :data:`GRADED` means a suite ran and said a number.
MEASUREMENTS: tuple[str, ...] = ("GRADED", "PENDING", "UNSTATED", "UNCOMMITTED")

GRADED = "GRADED"
"""The introducing commit states a real metric — a count, or a ``qual:`` claim."""

_METRIC_RE = re.compile(r"^Metric:[ \t]*(.*?)[ \t]*$", re.MULTILINE)


def _introducing_message(path: str, root: Path | None = None) -> str:
    """The message of the commit that **added** ``path``; ``""`` if none did.

    ``--diff-filter=A`` rather than the newest touching commit: a later cycle
    that edits an older journal (the 09:00 correction on 2026-08-09 did exactly
    that) must not relabel that journal with *its* metric.  The grade being
    asked about belongs to the cycle that wrote the file.
    """
    proc = subprocess.run(
        ["git", "log", "--diff-filter=A", "-1", "--format=%B", "--", path],
        cwd=_root(root),
        capture_output=True,
        text=True,
        env=_ENV,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def measurement(cycle: Cycle, *, root: Path | None = None) -> str:
    """Whether this cycle's tree was ever graded — one of :data:`MEASUREMENTS`.

    D-156's second clause, and the half of a strand that costs more than the
    delay.  ``push_preflight record`` is the only place a receipt is taken and
    only a *pushing* cycle runs it, so **a stranded cycle is by construction an
    unmeasured one**: its commit is stamped ``Metric: sandbox:pass=pending`` and
    no suite ever contradicted the ``Status: keep`` written above it.  On
    2026-08-09 that tree was red for an hour and 11:00's journal called it kept.

    Read off the commit message rather than inferred, because the cycle *stated*
    this about itself.  Four answers, not two, because the ways of not having a
    grade are not interchangeable: ``PENDING`` is a cycle that knew it owed one,
    ``UNSTATED`` wrote no ``Metric:`` line at all, and ``UNCOMMITTED`` is a
    journal git has never seen — which is a strand at an earlier step, before
    even the commit.  Collapsing the three would make the reading say "ungraded"
    where the repair differs: the first two need a suite run, the third needs a
    commit first.
    """
    msg = _introducing_message(cycle.path, root)
    if not msg:
        return "UNCOMMITTED"
    m = _METRIC_RE.search(msg)
    if m is None or not m.group(1):
        return "UNSTATED"
    return "PENDING" if m.group(1).split("=")[-1].strip().lower() == "pending" else GRADED


def strand_report(
    all_stranded: tuple[Cycle, ...],
    unwatched: tuple[Cycle, ...],
    measurements: dict[str, str] | None = None,
) -> str:
    """Render a stranding reading.  Takes its populations, reads no repository.

    Split from the query so the wording is testable without building a scratch
    git repo — the renderer is the half a cycle actually reads, and it was the
    half with no test in :func:`report`'s case until D-105.

    *measurements* maps ``cycle.path`` to a :data:`MEASUREMENTS` verdict.  Absent
    (or missing a path) the line renders as it always did: the grade is a fact
    the caller supplies, and a renderer that invented ``GRADED`` for a path
    nobody measured would be claiming the opposite of what it knows.
    """
    if not all_stranded:
        return "cycle_artifacts — no stranded cycles: every journal is on origin."
    blind = {c.path for c in unwatched}
    grades = measurements or {}
    ungraded = [c for c in all_stranded if grades.get(c.path, GRADED) != GRADED]
    lines = [
        f"cycle_artifacts — {len(all_stranded)} cycle(s) never reached origin;"
        f" {len(unwatched)} of them are invisible to the push gate:",
        "",
    ]
    for c in all_stranded:
        marks = []
        if c.path in blind:
            marks.append("unwatched (Artifacts claims honest)")
        verdict = grades.get(c.path)
        if verdict is not None and verdict != GRADED:
            marks.append(f"ungraded ({verdict})")
        mark = f"  ← {', '.join(marks)}" if marks else ""
        lines.append(f"  STRANDED  {c.stamp}  {c.path}{mark}")
    lines += ["", "  push this branch before writing a new journal."]
    if ungraded:
        # The budget line, not a second scolding.  Clearing an ungraded strand
        # means running the suite the authoring cycle never ran (~16 min here),
        # and 19:00 on 2026-08-09 discovered that mid-cycle because the reading
        # it took at minute one said only "never reached origin".
        lines.append(
            f"  {len(ungraded)} of these tree(s) were never graded — budget a"
            " suite run to clear, not just a push."
        )
    return "\n".join(lines)


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
    counts["frontier_stranded"] = int(frontier_stranded(branch, root=root) is not None)
    strandings = stranded(branch, root=root)
    counts["stranded"] = len(strandings)
    counts["stranded_ungraded"] = sum(
        1 for c in strandings if measurement(c, root=root) != GRADED
    )
    counts["confirmed"] = len(unsupported(branch, root=root))
    counts["disputed"] = len(disputed(branch, root=root))
    return counts


def divergence_digest(branch: str, *, root: Path | None = None,
                      paths: "tuple[str, ...] | None" = None) -> str:
    """The grades behind a failing assertion, for the assertion to carry.

    Written because of D-230.  CI graded this branch 183 HONOURED / 38
    UNSUPPORTED while every local reading of a byte-identical tree — the repo
    itself, a full-depth clone, and that clone at the exact merge ref CI checks
    out — graded it 204/17 on the same 221 parsed cycles.  Roughly 21 cycles are
    graded differently in the two places, in *both* directions, and no local run
    can reproduce it: **the divergent grades exist only inside the run that
    computed them**.  A bare ``assert 183 > 38 * 5`` throws that run away.

    So the reading is attached to the failure rather than recomputed after it.
    ``paths`` restricts the listing to the cycles an assertion is actually about
    (the hand-established controls); ``None`` lists every cycle carrying a
    finding grade, which is the population that moved.
    """
    counts = census(branch, root=root)
    if paths is None:
        # The population the two live assertions are about, taken from the
        # registered readers rather than re-filtering `finding_grades()` here.
        # A second spelling of "what counts as a finding" would be a second
        # statement of it (D-047), and a formatter that owns one is a guard
        # with all a guard's obligations — which this is deliberately not.
        wanted = ({c.path for c in unsupported(branch, root=root)}
                  | {c.path for c in disputed(branch, root=root)})
    else:
        wanted = set(paths)
    lines = [
        "grades behind this assertion (D-230 — CI and local disagree here):",
        "  census: " + ", ".join(
            f"{k}={counts[k]}" for k in
            (*GRADES, "cycles", "tsv_rows", "undated_rows", "orphan_rows",
             "confirmed", "disputed")
        ),
    ]
    for c, g, n in graded(branch, root=root):
        if c.path not in wanted:
            continue
        lines.append(f"  {g:<14} rows={n}  {c.stamp}  {c.path}")
    return "\n".join(lines)


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
        f"  frontier stranded:  {counts['frontier_stranded']}"
        f"   (the exempt newest cycle, graded separately — D-110)",
        f"  stranded:           {counts['stranded']}"
        f"   (of which never graded: {counts['stranded_ungraded']} — D-156)",
        "  by grade: " + ", ".join(f"{g}={counts[g]}" for g in GRADES if counts[g]),
        "",
    ]
    for c, g, n in rows:
        mark = "  SILENT" if c.path in silent else ""
        lines.append(f"  {g:<14} rows={n}  {c.stamp}  {c.path}{mark}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("report", "stranded", "claim"):
        print(
            "usage: python3 -m eval.mppi_sandbox.cycle_artifacts "
            "{report|stranded|claim} [branch]",
            file=sys.stderr,
        )
        return 2
    branch = argv[1] if len(argv) > 1 else current_branch()
    if argv[0] == "claim":
        # Both halves of the write-site repair in one call: the verdict is the
        # guard, the emitted line is what 4a should paste.  Non-zero only on the
        # over-claiming direction, so it is safe in the push gate's ``&&`` chain
        # -- and unlike ``tsv_timestamp check`` it does not go vacuous once the
        # row is committed, so it does not have to be placed by hand.
        grade = claim_support(branch)
        cycle, rows = _claim_rows(branch)
        where = f"{cycle.stamp}  {cycle.path}" if cycle is not None else "(no journal)"
        if grade == NO_INFLIGHT_JOURNAL:
            # rc=2 is "you asked too early", not "a claim is wrong" -- D-199's
            # split, which exists because the two are clearable in opposite
            # ways.  The caveat is cleared by writing 4a and re-running; the
            # rc=1 finding cannot be cleared at all.  Naming the journal it
            # would have graded is the whole repair: the old line asserted that
            # journal *was* this cycle's.
            print(f"cycle_artifacts — NO_INFLIGHT_JOURNAL: the newest journal is "
                  f"{where}, which belongs to a previous cycle, not this one.")
            print(f"  the line 4a should carry:  {claim_line(branch)}")
            return 2
        print(f"cycle_artifacts — the in-flight cycle's TSV claim: "
              f"{grade}  rows={rows}  {where}")
        print(f"  the line 4a should carry:  {claim_line(branch)}")
        return 1 if grade in finding_grades() else 0
    if argv[0] == "stranded":
        # Exit non-zero on a finding: REVIEW runs this under ``&&``/``||``, and a
        # reading a caller has to parse to act on is a reading callers stop
        # taking.  ``report`` stays exit-0 — it is a census, not a verdict.
        rows = stranded(branch)
        grades = {c.path: measurement(c) for c in rows}
        print(strand_report(rows, unwatched_strandings(branch), grades))
        return 1 if rows else 0
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
