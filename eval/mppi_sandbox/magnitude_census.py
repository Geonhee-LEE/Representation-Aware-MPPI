"""Q-083: is :data:`published_ratios.PUBLISHED` a census or a convenience sample?

D-076 found the typed exemption ``magnitude_survival.SELF_DEFINING`` removing
**0 of 22** rows, and the cause was not the exemption.  It was the population:
``PUBLISHED`` transcribes four decisions --- D-066, D-069, D-070, D-071 --- out
of the **76** in ``docs/decisions.md``, so ``SELF_DEFINING`` named a D-074 value
that the set it filters had never contained.  The vacuity was downstream of a
sampling question nobody had asked.

That question is Q-083, and it decides the standing of every ratio D-075
published.  ``8/23``, ``5/23`` and ``4/5`` are counts over ``PUBLISHED``'s
cells.  If ``PUBLISHED`` is the complete record of per-site magnitudes on this
branch, those are ratios over a census and they mean what they say.  If it is
whichever numbers four cycles happened to retype, the denominator is unknown and
so is every ratio built on it.

Counting is not the whole answer
--------------------------------

The crude count is available in one pass and it is **18**: eighteen of the 76
decisions print an integer next to one of :data:`published_ratios.SITES`.  Four
are transcribed.  Stopping there would repeat exactly the error D-076 caught ---
deciding "is this magnitude one of this record's readings" on the value alone,
which over-derived and produced only false positives.  A site-adjacent integer
is not a published reading.  D-066 prints ``23509`` next to
``_has_git_diff_literal``; that is a **call count**, not a reconstruction gap.
D-050 and D-051 print magnitudes for ``_is_set_valued`` from an era measuring a
different quantity entirely.

So this module reports the 18 and then spends its length on the three
discriminators that make it interpretable, each mechanised rather than argued:

**Novelty** (:func:`novel`).  A magnitude is novel to a decision iff no earlier
decision printed that ``(site, value)`` pair.  This separates *publishing a
reading* from *re-quoting one*, which is the difference between a decision the
record is missing and a decision the record has no reason to carry.  It is the
load-bearing discriminator: a decision with zero novel magnitudes cannot be an
uncovered reading no matter how many digits it prints.

**Qualification** (:attr:`SiteMagnitude.qualified`).  ``` `lam_dependence._pure` ```
names a site; bare ``` `_pure` ``` names it only if the reader supplies the
module.  Both are counted, separately, because the bare spelling is where a
scan of this shape goes wrong.

**Crosstalk** (:attr:`SiteMagnitude.crosstalk`).  The window is one line plus
the next --- the same width :func:`published_ratios.unverified` reads at --- and
prose on this branch routinely puts two sites and four numbers on one line.  A
digit with *another* site's name between it and the anchor is flagged, because
it may well be that site's.  This is the scan measuring its own precision, and
it is the field D-076 would have wanted: the bite of a filter reported as an
integer rather than asserted in prose.

What this module does not do
----------------------------

It does not classify a magnitude by **quantity**.  Whether D-067's ``12`` and
D-070's ``15`` are two readings of one thing or readings of two things is a
claim about what the surrounding prose meant, and no scan settles it --- that is
the same gap ``published_ratios.unverified`` names in its own docstring, one
level up.  :func:`uncovered` therefore returns the decisions and their
magnitudes and stops; it does not pronounce them missing.  The honest output is
a shopping list with its noise measured, not a verdict.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from eval.mppi_sandbox import claim_scope, published_ratios

REPO_ROOT = claim_scope.REPO_ROOT

#: The document this census reads.  ``docs/decisions.md`` is the branch's
#: published record; the journals carry more numbers still, and that they are
#: out of scope here is a limit, not an oversight --- a decision is what
#: ``PUBLISHED`` cites as a source for D-066.
DECISIONS_DOC = "docs/decisions.md"

#: Window width in *additional* lines after the anchor line.  Kept equal to the
#: one :func:`published_ratios._mentions` reads at, so a magnitude this census
#: finds is one that module could verify and vice versa.  Widening it makes the
#: scan pass on any document containing enough integers.
WINDOW_LINES = 1

#: Short names of the sites ``PUBLISHED`` is a record of, derived from it rather
#: than retyped (D-047).  A site added there is censused here in the same commit.
SHORT_NAMES: tuple[str, ...] = tuple(
    dict.fromkeys(site.split(".")[-1] for site in published_ratios.SITES)
)

_SECTION_RE = re.compile(r"(?m)^## (D-(\d+))\b")
#: An integer that is not part of a decimal and not embedded in a word.
#:
#: The trailing guard is ``(?!\.\d)`` rather than ``(?![\w.])`` --- the wider
#: form, copied from :func:`published_ratios._mentions`, also rejects a number
#: at the **end of a sentence**, and this branch's prose ends sentences with
#: magnitudes constantly.  There it is harmless (a verifier that misses raises a
#: false alarm); here it would silently shrink the population Q-083 is counting,
#: which is the one thing this module must not do.
_INT_RE = re.compile(r"(?<![\w.])(\d+)(?!\.\d)(?!\w)")


def _anchor_re(short: str) -> re.Pattern[str]:
    """Backticked site name, optionally module-qualified.

    The closing backtick is what keeps ``` `_pure` ``` from matching inside
    ``` `_is_pure_literal` ``` --- the two share a suffix and a substring test
    would conflate them.
    """
    return re.compile(rf"`(?P<qual>[\w.]*\.)?{re.escape(short)}`")


@dataclass(frozen=True)
class Section:
    """One ``## D-NNN`` block of :data:`DECISIONS_DOC`."""

    decision: str
    number: int
    body: str


@dataclass(frozen=True)
class SiteMagnitude:
    """One integer printed within :data:`WINDOW_LINES` of one site's name."""

    decision: str
    number: int
    site: str
    value: int
    qualified: bool
    crosstalk: bool

    @property
    def clean(self) -> bool:
        """Fully qualified and with no other site between the name and the digit.

        The subset a reader can attribute without re-opening the source.  Its
        size against the total is this scan's precision, reported by
        :func:`precision` rather than claimed.
        """
        return self.qualified and not self.crosstalk


def sections(text: str) -> tuple[Section, ...]:
    """Split the decisions document into blocks, oldest first.

    The file is written newest-first; :func:`novel` needs chronological order
    and gets it by sorting on the number, not by reversing the file --- an entry
    inserted out of order would otherwise silently invert a novelty verdict.
    """
    marks = list(_SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append(Section(m.group(1), int(m.group(2)), text[m.end():end]))
    return tuple(sorted(out, key=lambda s: s.number))


def _window(body: str, start: int) -> str:
    """From ``start`` to the end of the line ``WINDOW_LINES`` below it."""
    end = start
    for _ in range(WINDOW_LINES + 1):
        nl = body.find("\n", end)
        if nl == -1:
            return body[start:]
        end = nl + 1
    return body[start:end]


def _scan_section(section: Section) -> tuple[SiteMagnitude, ...]:
    out: list[SiteMagnitude] = []
    anchors = {short: _anchor_re(short) for short in SHORT_NAMES}
    for short, pattern in anchors.items():
        for match in pattern.finditer(section.body):
            window = _window(section.body, match.start())
            for digit in _INT_RE.finditer(window):
                before = window[: digit.start()]
                crosstalk = any(
                    other != short and anchors[other].search(before)
                    for other in SHORT_NAMES
                )
                out.append(SiteMagnitude(
                    decision=section.decision,
                    number=section.number,
                    site=short,
                    value=int(digit.group(1)),
                    qualified=match.group("qual") is not None,
                    crosstalk=crosstalk,
                ))
    return tuple(out)


def scan(doc: Sequence[Section] | None = None,
         root: Path | None = None) -> tuple[SiteMagnitude, ...]:
    """Every site-adjacent integer in the decisions document, oldest first."""
    if doc is None:
        path = (root or REPO_ROOT) / DECISIONS_DOC
        doc = sections(path.read_text(encoding="utf-8")) if path.exists() else ()
    out: list[SiteMagnitude] = []
    for section in doc:
        out.extend(_scan_section(section))
    return tuple(out)


def printing(mags: Sequence[SiteMagnitude]) -> tuple[str, ...]:
    """Decisions carrying at least one site-adjacent integer, oldest first."""
    return tuple(dict.fromkeys(m.decision for m in mags))


def novel(mags: Sequence[SiteMagnitude]) -> tuple[SiteMagnitude, ...]:
    """First appearance of each ``(site, value)`` pair in decision order.

    Re-quoting is the dominant mode on this branch --- D-072 through D-076 argue
    *about* D-070's and D-071's numbers --- so the count of decisions printing a
    magnitude badly overstates the count of decisions that *took a reading*.
    Novelty is a lower bound on the latter and an honest one: it cannot tell a
    genuinely new reading that happens to collide with an old value from a
    re-quote, and D-076 measured exactly how often small integers collide.
    """
    seen: set[tuple[str, int]] = set()
    out = []
    for m in sorted(mags, key=lambda m: m.number):
        key = (m.site, m.value)
        if key not in seen:
            seen.add(key)
            out.append(m)
    return tuple(out)


def transcribed(cells: Sequence[published_ratios.Cell] | None = None
                ) -> tuple[str, ...]:
    """Decisions ``PUBLISHED`` carries a cell for."""
    return published_ratios.readings(
        published_ratios.PUBLISHED if cells is None else cells)


@dataclass(frozen=True)
class Uncovered:
    """One decision that prints magnitudes and appears in no ``PUBLISHED`` cell."""

    decision: str
    total: int
    novel: int
    clean: int

    @property
    def candidate(self) -> bool:
        """Prints at least one first-appearance magnitude.

        Necessary, not sufficient: a decision with zero novel magnitudes is
        re-quoting and the record loses nothing by omitting it, but a decision
        with several may still be printing a different *quantity* --- the
        distinction this module declines to make (see the docstring).
        """
        return self.novel > 0


def uncovered(mags: Sequence[SiteMagnitude] | None = None,
              cells: Sequence[published_ratios.Cell] | None = None,
              ) -> tuple[Uncovered, ...]:
    """The shopping list: what prints magnitudes that ``PUBLISHED`` does not carry."""
    scanned = scan() if mags is None else tuple(mags)
    covered = set(transcribed(cells))
    fresh = {(m.decision, m.site, m.value) for m in novel(scanned)}
    out = []
    for decision in printing(scanned):
        if decision in covered:
            continue
        rows = [m for m in scanned if m.decision == decision]
        out.append(Uncovered(
            decision=decision,
            total=len(rows),
            novel=sum(1 for m in rows if (m.decision, m.site, m.value) in fresh),
            clean=sum(1 for m in rows if m.clean),
        ))
    return tuple(out)


@dataclass(frozen=True)
class Census:
    """Q-083's answer, with the denominator it is a fraction of."""

    decisions: int
    printing: int
    transcribed: int
    uncovered_candidates: int

    @property
    def is_census(self) -> bool:
        """Does ``PUBLISHED`` cover every decision that could have supplied a cell?"""
        return self.uncovered_candidates == 0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        verdict = "CENSUS" if self.is_census else "SAMPLE"
        return (f"{self.transcribed} of {self.printing} magnitude-printing "
                f"decisions transcribed ({self.decisions} total), "
                f"{self.uncovered_candidates} uncovered with novel values "
                f"-> {verdict}")


def census(mags: Sequence[SiteMagnitude] | None = None,
           doc: Sequence[Section] | None = None,
           root: Path | None = None) -> Census:
    """Count the population ``PUBLISHED`` samples from."""
    if doc is None:
        path = (root or REPO_ROOT) / DECISIONS_DOC
        doc = sections(path.read_text(encoding="utf-8")) if path.exists() else ()
    scanned = scan(doc, root) if mags is None else tuple(mags)
    unc = uncovered(scanned)
    return Census(
        decisions=len(doc),
        printing=len(printing(scanned)),
        transcribed=len(transcribed()),
        uncovered_candidates=sum(1 for u in unc if u.candidate),
    )


@dataclass(frozen=True)
class Precision:
    """How much of the scan a reader can attribute without re-opening the source."""

    total: int
    qualified: int
    crosstalk: int
    clean: int

    @property
    def clean_fraction(self) -> float:
        return self.clean / self.total if self.total else 0.0

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.clean}/{self.total} clean "
                f"({self.clean_fraction:.0%}); {self.crosstalk} crosstalk, "
                f"{self.total - self.qualified} bare")


def precision(mags: Sequence[SiteMagnitude] | None = None) -> Precision:
    """The scan's own error rate, as integers.

    D-076's cheapest finding was that a filter nobody had counted removed
    nothing.  This is the same question asked of a *scanner*: of the pairs it
    emits, how many are attributable?  A low fraction does not invalidate
    :func:`census` --- ``uncovered`` is keyed on decisions, and a decision needs
    only one clean magnitude --- but it bounds how far any per-value claim built
    on this scan may be pushed.
    """
    scanned = scan() if mags is None else tuple(mags)
    return Precision(
        total=len(scanned),
        qualified=sum(1 for m in scanned if m.qualified),
        crosstalk=sum(1 for m in scanned if m.crosstalk),
        clean=sum(1 for m in scanned if m.clean),
    )


def as_of(decision: str,
          doc: Sequence[Section] | None = None,
          root: Path | None = None) -> Census:
    """The census as it stood when ``decision`` was the newest entry.

    :func:`census` reads the document as it is *now*, which is the right reading
    for "is ``PUBLISHED`` a census today" and the wrong one for "was the number
    D-077 printed correct".  Those are different questions and D-077 answered the
    second with the first's instrument, one write too early --- see
    :func:`drifted`.

    One caveat, stated rather than papered over: only the **document** side is
    rewound.  ``transcribed`` counts :data:`published_ratios.PUBLISHED`, which is
    a code registry with no history in this file, so an as-of view reports
    today's transcription against that date's population.  For the drift check
    below that is exactly right --- a quoted verdict is re-checkable only while
    the registry it quoted still stands, and a registry change that broke one
    would be a finding, not a false alarm.
    """
    if doc is None:
        path = (root or REPO_ROOT) / DECISIONS_DOC
        doc = sections(path.read_text(encoding="utf-8")) if path.exists() else ()
    number = _number_of(decision, doc)
    upto = tuple(s for s in doc if s.number <= number)
    return census(doc=upto, root=root)


def _number_of(decision: str, doc: Sequence[Section]) -> int:
    for section in doc:
        if section.decision == decision:
            return section.number
    raise KeyError(f"{decision} is not a section of {DECISIONS_DOC}")


#: The canonical spelling a decision entry states a census verdict in.
#:
#: D-077 stated its verdict in prose three ways (a title, a Decision line, a
#: closing count) and corrected none of them when the re-take moved the numbers.
#: A verdict written in this one spelling is machine-checkable against
#: :func:`as_of`; one written any other way is not policed, and that limit is
#: real --- this pins the spelling, not the prose around it.
_VERDICT_RE = re.compile(
    r"(?P<printing>\d+) printing / (?P<transcribed>\d+) transcribed"
    r" / (?P<uncovered>\d+) uncovered"
    r" \((?P<decisions>\d+) decisions\)"
)


@dataclass(frozen=True)
class QuotedVerdict:
    """A census verdict restated in the published record."""

    decision: str
    printing: int
    transcribed: int
    uncovered_candidates: int
    decisions: int

    def agrees_with(self, measured: Census) -> bool:
        return (self.printing == measured.printing
                and self.transcribed == measured.transcribed
                and self.uncovered_candidates == measured.uncovered_candidates
                and self.decisions == measured.decisions)


def quoted(doc: Sequence[Section] | None = None,
           root: Path | None = None) -> tuple[QuotedVerdict, ...]:
    """Every census verdict stated in the canonical spelling, oldest first."""
    if doc is None:
        path = (root or REPO_ROOT) / DECISIONS_DOC
        doc = sections(path.read_text(encoding="utf-8")) if path.exists() else ()
    out: list[QuotedVerdict] = []
    for section in doc:
        for m in _VERDICT_RE.finditer(section.body):
            out.append(QuotedVerdict(
                decision=section.decision,
                printing=int(m.group("printing")),
                transcribed=int(m.group("transcribed")),
                uncovered_candidates=int(m.group("uncovered")),
                decisions=int(m.group("decisions")),
            ))
    return tuple(out)


def drifted(doc: Sequence[Section] | None = None,
            root: Path | None = None
            ) -> tuple[tuple[QuotedVerdict, Census], ...]:
    """Quoted verdicts that disagree with the census as of their own entry.

    This is the guard D-077 needed and did not have.  ``citation_audit`` polices
    magnitude drift in this same document, but only for the claims in its
    ``MEASURED_CLAIMS`` registry, and a census count cannot join that registry as
    it stands: every entry quoting it correctly quotes a *different* number,
    because writing the entry changes the document being counted.  A registry
    keyed on one magnitude per claim has no vocabulary for that.  Indexing the
    quote by its own entry is what makes it a fixed, checkable claim again --- so
    the repair is a spelling (``N printing / ... (M decisions)``) plus this
    comparison, not a seventh registry entry.
    """
    if doc is None:
        path = (root or REPO_ROOT) / DECISIONS_DOC
        doc = sections(path.read_text(encoding="utf-8")) if path.exists() else ()
    out = []
    for q in quoted(doc, root):
        measured = as_of(q.decision, doc=doc, root=root)
        if not q.agrees_with(measured):
            out.append((q, measured))
    return tuple(out)


def report() -> str:  # pragma: no cover - reporting
    mags = scan()
    lines = [str(census(mags)),
             f"  scan precision: {precision(mags)}",
             f"  transcribed:    {', '.join(transcribed())}",
             "  uncovered (decision: total/novel/clean):"]
    for u in uncovered(mags):
        flag = "  <- candidate" if u.candidate else ""
        lines.append(f"    {u.decision}: {u.total}/{u.novel}/{u.clean}{flag}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
