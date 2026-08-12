"""Audit the pass counts this branch's journals quote against archived receipts.

Why this exists
---------------

On 2026-08-12 07:00 ``push_preflight record``'s CLI summary printed
``150 passed`` for a run whose receipt correctly held **2556**: the summary
tailed the captured output, which under ``record_sharded`` is fourteen shard
streams concatenated, so it reported the *last shard's* line as the run's
(D-212's first half).  The counts a cycle quotes into its journal, its TSV row
and Telegram come off that line.  The defect was fixed the same day, but nobody
had checked what the broken line had already been quoted into, and STATE has
carried "audit the last month's quoted counts" as the top actionable ever since.

This module is that check, mechanised.  It is read-only and costs no suite run:
:mod:`receipt_store` keys archives by tree fingerprint, so the evidence is
already on disk.

What corroboration can and cannot mean here
-------------------------------------------

A receipt carries ``counts`` and a tree fingerprint.  It does **not** carry the
cycle that took it, so a quote cannot be matched to *its own* receipt — only to
the archived population.  That asymmetry decides the whole verdict vocabulary,
and stating it plainly is the difference between an instrument and a rubber
stamp:

* a quoted value that **no** archived receipt carries is a number this branch
  has no measurement for.  That is a real finding — :data:`UNCORROBORATED`.
* a quoted value that **some** archived receipt carries is merely *not refuted*.
  It is not proof the quote came from that run.  The verdict is therefore
  :data:`CORROBORATED`, not "verified", and no test may read it as attribution.

The one-directional strength is the point.  This pass can convict; it cannot
acquit, and it does not claim to.

The reach is the headline, not a caveat
---------------------------------------

The store's first archive landed **2026-08-11 22:04** — the cycle that built it
(D-200).  Every count quoted before that instant was measured by a run whose
receipt was deliberately unlinked at the next cycle's start, so no evidence for
it exists or can be recovered.  STATE asked for "the last month"; the auditable
window is what the store reaches, and calling the rest *unsupported* would be
the same error in the opposite direction — grading absence of evidence as
evidence of absence.  Those quotes grade :data:`OUT_OF_REACH`, which is a
statement about this instrument, not about the cycle that wrote them.

:func:`reach` derives that boundary from the receipts themselves — each
receipt's ``head`` dated by ``git``, earliest wins — rather than from file
mtimes, which a copy or a rsync silently rewrites.

Restatement, and why it is separated
------------------------------------

Journals quote each other.  ``367 passed`` appears in the cycle that measured it
and again in two later cycles discussing it, and a scan that treats all three as
readings would report two phantom findings per real one.  A quote whose value
appeared in a **strictly earlier** journal is :data:`RESTATED` and carries no
verdict — the same novelty discriminator :func:`magnitude_census.novel` uses,
for the same reason: re-quoting a reading is not publishing one.

Not every count quoted is a claim about the suite
--------------------------------------------------

The first run of this audit flagged three quotes inside the reach, and **all
three were true negatives of one kind**: ``141 passed`` and ``150 passed`` are
the 07:00/08:00 journals *diagnosing the broken summary line itself*, and
``319 passed`` is a deliberately partial run — the census slice D-211 taught
cycles to check early.  None is a claim about the full suite, so none can be
corroborated by a full-suite receipt, and a gate that stays red on all three is
one that gets muted within a week (D-044).

:data:`PARTIAL` is that discriminator, and its shape is deliberately weak.  It
fires on a **local token in the quote's own line** — ``shard``, ``slice``,
``census``, ``subset`` — the same device :mod:`citation_audit` used when its
widened scan turned up five false positives that each "carried a local token
saying it is a different quantity".  Two properties keep it from becoming a
loophole:

* it can only **withdraw** a conviction, never manufacture one.  A quote with no
  archived receipt and no token is still ``UNCORROBORATED``; a token never
  promotes anything to ``CORROBORATED``.
* it reads one line, not the paragraph.  Widening it to the surrounding prose
  is how a scan of this shape starts deciding what an author *meant*, which is
  the over-derivation D-076 caught and no scan settles.

The residue is what the number means: :func:`audit` reports ``PARTIAL`` as its
own tally so the precision of the pass is an integer rather than an assurance.

Refs: D-212 (the misreporting summary line), D-082 (a push is licensed by a
receipt), D-200 (the store), D-043/D-044 (a count belongs to one tree),
Q-083/D-076 (novelty as the discriminator that makes a prose scan readable),
D-037/D-038 (a local token distinguishing a different quantity).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import push_preflight as pp
from . import receipt_store as rs
from . import tree_provenance as tp

#: Prose directory scanned.  Journals only: ``docs/decisions.md`` restates
#: counts too, but a decision cites the journal that measured them, so scanning
#: both would double-count every reading as its own restatement.
JOURNAL_DIR = Path("journal")

#: KST — the timezone every cycle stamp on this branch is written in.
KST = timezone(timedelta(hours=9))

#: A quoted suite count.  Three digits minimum: the suite passed 100 tests on
#: 2026-08-02 and has not been smaller since, so a two-digit "passed" on this
#: branch is a per-file or per-shard number, which is not what this audits.
_QUOTE = re.compile(r"(?<![\d.])(\d{3,5})\s+passed\b")

#: A journal path, ``journal/YYYY-MM/DD-HH-slug.md``.
_JOURNAL_NAME = re.compile(r"(?P<day>\d{2})-(?P<hour>\d{2})-(?P<slug>.+)\.md$")

#: Tokens whose presence in the quote's **own line** says the number is not the
#: full suite's.  Deliberately short and literal: every entry names a run this
#: branch actually takes (a shard, a census slice, an explicit subset), and
#: adding one is a claim that a *kind of partial run* exists, not that a
#: particular quote should be let off.
PARTIAL_TOKENS = ("shard", "slice", "census", "subset")

CORROBORATED = "CORROBORATED"
UNCORROBORATED = "UNCORROBORATED"
OUT_OF_REACH = "OUT_OF_REACH"
RESTATED = "RESTATED"
PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class Quote:
    """One ``N passed`` occurrence, bound to the cycle whose journal states it."""

    path: str
    line: int
    value: int
    cycle: datetime
    #: The line the quote sits on, kept so :func:`is_partial` reads the text the
    #: scan actually matched rather than re-opening the file at a line number
    #: some later edit has moved.
    text: str = ""

    @property
    def is_partial(self) -> bool:
        """Whether this line says the number is not the whole suite's."""
        lowered = self.text.lower()
        return any(token in lowered for token in PARTIAL_TOKENS)

    @property
    def slug(self) -> str:
        match = _JOURNAL_NAME.search(self.path)
        return match.group("slug") if match else ""


@dataclass(frozen=True)
class Finding:
    quote: Quote
    verdict: str

    @property
    def is_defect(self) -> bool:
        """Only the convicting verdict.  See the module docstring: this pass is
        one-directional, so ``CORROBORATED`` is not a pass mark and
        ``OUT_OF_REACH`` is a statement about the store's age."""
        return self.verdict == UNCORROBORATED


def cycle_of(path: Path) -> datetime | None:
    """The cycle instant a journal path names, or ``None`` if it names none.

    The month comes from the parent directory and the day/hour from the
    filename, which is the convention Phase 4a writes and the only place a
    cycle's own instant is recorded — the file's mtime is not it (a rebase or a
    checkout rewrites mtimes and leaves the name alone).
    """
    match = _JOURNAL_NAME.search(path.name)
    if match is None:
        return None
    try:
        year, month = (int(part) for part in path.parent.name.split("-"))
        return datetime(
            year, month, int(match.group("day")), int(match.group("hour")), tzinfo=KST
        )
    except ValueError:
        return None


def quotes(root: Path | None = None) -> tuple[Quote, ...]:
    """Every ``N passed`` in every dated journal, oldest cycle first."""
    base = (root or tp.REPO_ROOT) / JOURNAL_DIR
    found: list[Quote] = []
    for path in sorted(base.glob("*/*.md")):
        cycle = cycle_of(path)
        if cycle is None:
            continue
        rel = path.relative_to(root or tp.REPO_ROOT).as_posix()
        for number, text in enumerate(path.read_text().splitlines(), start=1):
            for match in _QUOTE.finditer(text):
                found.append(Quote(rel, number, int(match.group(1)), cycle, text))
    return tuple(sorted(found, key=lambda q: (q.cycle, q.path, q.line)))


def archived(root: Path | None = None) -> tuple[pp.Receipt, ...]:
    """Every readable archived receipt.

    Unreadable files are dropped rather than raised on, matching
    :func:`receipt_store.recall`: a corrupt archive is *no evidence*, and the
    audit's job is to report what evidence exists.
    """
    loaded = (pp.load(path) for path in rs.entries(root))
    return tuple(receipt for receipt in loaded if receipt is not None)


def _commit_instant(sha: str, root: Path | None = None) -> datetime | None:
    try:
        out = subprocess.run(
            ["git", "show", "-s", "--format=%cI", sha],
            cwd=root or tp.REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        return datetime.fromisoformat(out.stdout.strip())
    except ValueError:
        return None


def reach(root: Path | None = None) -> datetime | None:
    """The earliest instant this audit has evidence for, or ``None`` if never.

    Derived from the receipts' own ``head`` commits, not from file mtimes.  A
    receipt whose head is unreachable (a dropped branch, a fresh clone) cannot
    date itself and simply does not extend the reach — the conservative
    direction, since an undatable receipt grades nothing ``OUT_OF_REACH`` that
    it might not cover.
    """
    instants = [
        instant
        for instant in (_commit_instant(r.head, root) for r in archived(root))
        if instant is not None
    ]
    return min(instants) if instants else None


def audit(root: Path | None = None) -> tuple[Finding, ...]:
    """Grade every journal-quoted pass count against the archived population."""
    population = {receipt.counts.get("passed", 0) for receipt in archived(root)}
    boundary = reach(root)
    seen: set[int] = set()
    findings: list[Finding] = []
    for quote in quotes(root):
        if quote.value in seen:
            findings.append(Finding(quote, RESTATED))
            continue
        seen.add(quote.value)
        if boundary is None or quote.cycle < boundary:
            findings.append(Finding(quote, OUT_OF_REACH))
        elif quote.value in population:
            findings.append(Finding(quote, CORROBORATED))
        elif quote.is_partial:
            # Withdrawal only — see the module docstring.  Reached solely on the
            # branch that would otherwise convict, so a token can never turn an
            # unmeasured number into a corroborated one.
            findings.append(Finding(quote, PARTIAL))
        else:
            findings.append(Finding(quote, UNCORROBORATED))
    return tuple(findings)


def defects(root: Path | None = None) -> tuple[Finding, ...]:
    return tuple(f for f in audit(root) if f.is_defect)


def _main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python3 -m eval.mppi_sandbox.quoted_counts",
        description="Audit journal-quoted pass counts against archived receipts.",
    )
    ap.add_argument(
        "cmd", nargs="?", default="audit", choices=["audit", "reach"], help="what to do"
    )
    args = ap.parse_args(argv)

    boundary = reach()
    if args.cmd == "reach":
        if boundary is None:
            print("quoted_counts — no datable archived receipt; reach is empty.")
            return 0
        print(
            f"quoted_counts — {len(archived())} archived receipt(s); "
            f"evidence reaches back to {boundary.astimezone(KST):%Y-%m-%d %H:%M} KST. "
            "Anything quoted earlier is OUT_OF_REACH by construction."
        )
        return 0

    findings = audit()
    tally = {
        verdict: 0
        for verdict in (CORROBORATED, UNCORROBORATED, OUT_OF_REACH, RESTATED, PARTIAL)
    }
    for finding in findings:
        tally[finding.verdict] += 1
    where = (
        f"back to {boundary.astimezone(KST):%Y-%m-%d %H:%M} KST"
        if boundary is not None
        else "nowhere — the store holds no datable receipt"
    )
    print(
        f"quoted_counts — {len(findings)} quoted count(s) across "
        f"{len({f.quote.path for f in findings})} journal(s); evidence reaches {where}.\n"
        f"  {tally[CORROBORATED]} corroborated, {tally[UNCORROBORATED]} uncorroborated, "
        f"{tally[OUT_OF_REACH]} out of reach, {tally[RESTATED]} restated, "
        f"{tally[PARTIAL]} partial-run."
    )
    bad = [f for f in findings if f.is_defect]
    if not bad:
        print("  No quoted count inside the reach lacks an archived measurement.")
        return 0
    print("  UNCORROBORATED — quoted inside the reach, no receipt carries the value:")
    for finding in bad:
        print(
            f"    {finding.quote.value} passed  "
            f"{finding.quote.path}:{finding.quote.line}  "
            f"({finding.quote.cycle:%m-%d %H:%M})"
        )
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
