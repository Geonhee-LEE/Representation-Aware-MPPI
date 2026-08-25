"""Is a retired decision reachable *from the entry that was retired*?

Q-194's backward half.  D-449 found that D-430, D-433 and D-440 had all been
retired as cost-side levers — and that all three still read ``Status:
accepted``.  The retirement was written **only in the entries that did the
retiring** (D-446 / D-447 / D-448).  A reader who arrives by ``grep D-433``,
which D-439 measured as the way readers actually arrive, sees a live decision
and cites a withdrawn conclusion.

Q-194's lean was that this backward direction is *a digit cheaper* than the
forward one (Q-184, "which prior D already settled this?"): forward is semantic
and its recall is unknown, backward is "구문 문제 — 정확, 재현율 100%,
오탐이 없다".  **The measurement does not support that.**  Scanning both
:data:`~eval.mppi_sandbox.citation_audit.SCANNED_DOCS` for the obvious rule —
a line carrying a retirement verb and naming some other ``D-NNN`` — yields
**306** candidate pairs across 449 entries against a true population of
**11**, and reading them shows why the promised precision is not available:

1. **Direction is not recoverable from the syntax.**  D-449 writes ``은퇴
   (D-446)``.  That names the *retirer*, not the retired; the retired entry is
   the one the sentence is about, which is a semantic fact.  The same shape
   ``retired (D-NNN)`` occurs with both roles across the corpus.
2. **A line names several decisions and the verb binds to one.**  D-449's
   ``Refs`` line carries six references and one ``은퇴``; five of the six pairs
   are noise.  Proximity windows shrink the noise but do not remove it, and
   they buy that with a threshold nobody can justify.
3. **Structural lines mention retirement without performing one.**
   ``Context``, ``Alternatives`` and ``Refs`` discuss retirements that happened
   elsewhere.

So the backward half splits into a part that *is* syntactic and a part that is
not, and only the first can be a gate:

* :func:`unbacked_retirements` — **the gate.**  An entry whose own ``Status``
  line says it is retired must, on that same line, name the entry that retired
  it.  No direction problem: the entry is the subject of its own Status line by
  construction, so every ``D-NNN`` on it is the other role.  Zero false
  positives, and the population is currently **empty** — D-449's hand repair of
  D-430 / D-433 / D-440 satisfies it, as do the eight older retirements
  (D-437, D-372, D-74, D-70, D-65, D-55, D-33, D-32) written before anyone
  asked for the rule.  What it catches is *drift*: the next retirement written
  as a bare ``Status: retired``.
* :func:`retirement_statements` — **advisory only.**  The 305.  Reported so the
  scope of what the gate does not cover is a declared decision rather than an
  oversight (D-037's finding, applied to this module).

What the gate does **not** catch is D-449's own case at the moment it arose:
D-430's Status line read ``accepted`` with no verb at all, so there was nothing
for a Status-line rule to bind to.  Catching *that* requires knowing that some
other entry retired it — i.e. requires resolving direction, i.e. is the
semantic half.  This module therefore does not close Q-194; it closes the
half that was genuinely cheap and measures the price of the other half instead
of assuming it.

**What counts as a back-reference.**  The retired entry's ``- **Status**:``
line naming another ``D-NNN``.  Deliberately narrow: ``D-433`` appears in
plenty of entries with nothing to do with its withdrawal, so "somewhere in the
body" would pass entries whose reader still sees a bare verdict at a glance.
The Status line is the line a grep-arriving reader reads to decide whether a
decision is live, so it is the line that has to carry the correction.  D-449
wrote exactly this form by hand::

    - **Status**: accepted · **cost-side lever 로서는 은퇴 (D-446), band ≤ 0.707
      에서 (D-448)** — ... 상세는 D-449.

The self-membership rule applies (D-045, D-317): this module's own docstring is
inside :func:`~eval.mppi_sandbox.citation_audit.scanned_modules`, and it names
``D-430``/``D-433``/``D-440`` beside ``은퇴`` above.  A module that polices
unreachable retirements while exempting its own prose would reproduce the
defect it was written for.  It is not exempt — it escapes only because the
docstring is not a ``## D-NNN`` entry, so :func:`entries` never yields it and
there is no Status line to check.  That is a property of the parser, stated
here so a later reader does not mistake it for an oversight.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .citation_audit import REPO_ROOT, SCANNED_DOCS

#: Verbs (ko + en) that assert a decision has been withdrawn.  Matched
#: case-insensitively as substrings, because Korean attaches particles
#: (``은퇴는``, ``은퇴시킨``) and English inflects (``supersedes``,
#: ``superseded``).  Kept deliberately small — every addition widens the
#: population, and a verb that fired on "이 결정을 유지한다" would invent
#: retirements nobody claimed.
RETIREMENT_VERBS: tuple[str, ...] = (
    "은퇴",
    "철회",
    "폐기",
    "무효화",
    "supersede",
    "superseded",
    "supersedes",
    "retire",
    "retired",
    "retires",
    "withdraw",
    "withdrawn",
    "withdraws",
)

_ENTRY_HEAD = re.compile(r"^##\s+(D-\d+)\s")
_DECISION_REF = re.compile(r"\bD-(\d+)\b")
_STATUS_LINE = re.compile(r"^\s*-\s*\*\*Status\*\*\s*:")


@dataclass(frozen=True)
class Entry:
    """One ``## D-NNN`` section of a scanned doc."""

    number: int
    doc: str
    line: int
    body: tuple[str, ...]

    @property
    def name(self) -> str:
        return f"D-{self.number}"

    @property
    def status_line(self) -> str:
        """The ``- **Status**:`` line, or ``""`` if the entry has none."""
        for text in self.body:
            if _STATUS_LINE.match(text):
                return text
        return ""

    def referenced_decisions(self, text: str) -> frozenset[str]:
        """Every ``D-NNN`` in *text* other than this entry's own number."""
        found = {f"D-{int(m.group(1))}" for m in _DECISION_REF.finditer(text)}
        return frozenset(found - {self.name, f"D-{self.number:03d}"})


@dataclass(frozen=True)
class Retirement:
    """A line claiming, in ``source``, that some decision was withdrawn."""

    source: str
    target: str
    doc: str
    line: int
    text: str


def entries(root: Path | None = None) -> tuple[Entry, ...]:
    """Every ``## D-NNN`` entry across :data:`SCANNED_DOCS`, in file order."""
    base = root or REPO_ROOT
    out: list[Entry] = []
    for doc in SCANNED_DOCS:
        path = base / doc
        if not path.is_file():
            continue
        head: tuple[str, int] | None = None
        body: list[str] = []
        for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = _ENTRY_HEAD.match(text)
            if match:
                if head is not None:
                    out.append(Entry(int(head[0]), doc, head[1], tuple(body)))
                head, body = (match.group(1)[2:], lineno), [text]
            elif head is not None:
                body.append(text)
        if head is not None:
            out.append(Entry(int(head[0]), doc, head[1], tuple(body)))
    return tuple(out)


def names_a_retirement_verb(text: str) -> bool:
    """Does *text* carry any of :data:`RETIREMENT_VERBS`?"""
    low = text.lower()
    return any(verb in low for verb in RETIREMENT_VERBS)


def retired_entries(root: Path | None = None) -> tuple[Entry, ...]:
    """Entries whose **own** ``Status`` line says they have been withdrawn.

    The subject of a Status line is the entry it sits in, so this reading needs
    no direction inference — which is exactly what separates it from
    :func:`retirement_statements`.
    """
    return tuple(e for e in entries(root) if names_a_retirement_verb(e.status_line))


def unbacked_retirements(root: Path | None = None) -> tuple[Entry, ...]:
    """Retired entries whose ``Status`` line names no other decision.

    The gate.  A reader arriving at such an entry learns that it is withdrawn
    and has no way to reach the entry that withdrew it — the correction is
    stated but unreachable, which is the weaker half of D-449's finding.
    """
    return tuple(e for e in retired_entries(root) if not e.referenced_decisions(e.status_line))


def retirement_statements(root: Path | None = None) -> tuple[Retirement, ...]:
    """Every line carrying a retirement verb and naming some other decision.

    **Advisory.**  Direction is not recoverable from the syntax and a line may
    name several decisions while the verb binds to one, so this over-reports by
    a wide margin — see the module docstring for the three failure shapes and
    the measured size.  Kept because the alternative to a declared over-report
    is an undeclared blind spot (D-037).
    """
    out: list[Retirement] = []
    for entry in entries(root):
        for offset, text in enumerate(entry.body):
            if not names_a_retirement_verb(text):
                continue
            for target in sorted(entry.referenced_decisions(text)):
                out.append(Retirement(
                    source=entry.name,
                    target=target,
                    doc=entry.doc,
                    line=entry.line + offset,
                    text=text.strip(),
                ))
    return tuple(out)


def _render(root: Path | None = None) -> str:
    retired = retired_entries(root)
    unbacked = unbacked_retirements(root)
    lines: list[str] = []
    if unbacked:
        lines.append(f"retirement_reach — {len(unbacked)} retired entries name no retirer:")
        for entry in unbacked:
            lines.append(f"  {entry.name}  {entry.doc}:{entry.line}")
            lines.append(f"      {entry.status_line.strip()[:110]}")
    else:
        lines.append(
            f"retirement_reach — CLEAN: {len(retired)} retired entries, "
            "every one names the entry that retired it."
        )
    advisory = retirement_statements(root)
    lines.append(
        f"  advisory: {len(advisory)} retirement-verb citations across {len(SCANNED_DOCS)} docs "
        "— over-reports; direction is not syntactic (see docstring)."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    list(sys.argv[1:] if argv is None else argv)
    print(_render())
    return 1 if unbacked_retirements() else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
