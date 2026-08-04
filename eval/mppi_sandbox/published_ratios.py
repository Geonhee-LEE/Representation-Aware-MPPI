"""Can the published record answer Q-078 without buying another batch?

D-071 retired both branches of Q-077 and named exactly one survivor: grade the
reconstruction gaps on the **gap/control ratio** rather than on stationarity,
because across four trees not one magnitude reproduced but the *ordering* of
the ratios did.  Its own journal put a number on that survivor --- "ratios
spanning 2.5x (``_pure``: 214 vs 87) to 13x (``_is_set_valued``: 13 vs 1), and
that ordering has now reproduced on four trees" --- and STATE #1 proposed the
cheap next step: no new run, just pull the per-site ratios out of D-066..D-071's
artifacts and rank-correlate them.

This module is that step, and it is a **negative**.  There are no artifacts.
D-066..D-071 emitted prose; the numbers live in ``docs/decisions.md`` and in the
cycle journals, one hand-picked site at a time, and nothing wrote a per-site
record to disk.  So "pull the ratios out of the artifacts" is really "retype
whichever numbers six cycles happened to quote", and the first honest thing to
do is count what that leaves.

What it leaves
---------------

A ratio needs a gap and a control on the same tree.  Two of the six readings are
licensed (D-070's four-run batch and D-071's six-run batch --- the rest are
:data:`exclusion_scope.ATTR_TRANSPORTED` under D-069's guard, so their gaps and
controls are not even on one tree).  Across those two:

- **five** sites carry a gap and an exclusion-frame control on D-070's tree,
- **two** carry both on D-071's tree,
- **two** carry both on *both* --- ``lam_dependence._pure`` and
  ``guard_reflexivity._is_set_valued``,
- and the **source-frame** control, the second half of the denominator D-068
  established when it summed both frames against the gaps, is published for
  **zero** sites on **zero** trees.

Two consequences, and the second is the one worth the cycle:

1. A cross-tree rank correlation over ``n = 2`` is not a weak statistic, it is
   not a statistic --- every pair of distinct 2-orderings correlates at exactly
   +/-1.  That is what :data:`exclusion_scope.RANK_MIN_N` refuses, so Q-078's
   no-new-run half is **unanswerable from the record**, and by a margin.
2. D-071's own "2.5x to 13x, reproduced on four trees" was computed over those
   same two sites, against a one-frame denominator.  A two-point ordering
   reproduces trivially --- there are only two of them --- so the claim that
   licensed D-071's (c) as the last candidate standing is, on the record it
   cites, an ordering of one pair.  It may well be right; nothing published
   makes it checkable.

The numbers below are a **transcription**, not a measurement, and the whole
point of writing them down is to make that visible rather than to launder it.
:func:`unverified` re-locates every one of them in the file it was copied from,
so a typo is caught; it cannot and does not check that the number means what the
prose said it meant.  The fix for *that* is to stop transcribing --- persist the
per-site record when the reading is taken (STATE #3), which is the action this
negative recommends.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from eval.mppi_sandbox import claim_scope

REPO_ROOT = claim_scope.REPO_ROOT

#: The seven sites whose reconstructed and measured counts have disagreed in
#: every reading since D-066 --- the same membership five times over.  Fully
#: qualified, because D-066..D-069 named only five of them and two
#: (``lam_dependence._is_pure_literal`` / ``._numeric``) appeared in no
#: published artifact until D-070.
SITES: tuple[str, ...] = (
    "guard_reflexivity._has_git_diff_literal",
    "guard_reflexivity._is_set_valued",
    "guard_reflexivity._shells_out_to_git_diff",
    "lam_dependence._is_pure_literal",
    "lam_dependence._is_structural",
    "lam_dependence._numeric",
    "lam_dependence._pure",
)


@dataclass(frozen=True)
class Cell:
    """One site's published numbers from one reading.

    ``None`` means *the record does not carry it*, which is the field this
    module exists to count.  It never means zero --- a zero control is
    :data:`exclusion_scope.ATTR_FOLD`'s whole content and is always published
    when it happens.
    """

    decision: str
    tree: str
    site: str
    gap: int | None
    measured_delta: int | None
    source_delta: int | None
    source: str
    licensed: bool

    @property
    def one_frame(self) -> bool:
        """Enough for a gap/exclusion-frame ratio --- the one D-071 quoted."""
        return self.gap is not None and self.measured_delta is not None

    @property
    def both_frames(self) -> bool:
        """Enough for the ratio as :class:`exclusion_scope.RatioGrade` defines it."""
        return self.one_frame and self.source_delta is not None

    @property
    def numbers(self) -> tuple[int, ...]:
        """Every value actually published here --- what :func:`unverified` checks."""
        return tuple(v for v in (self.gap, self.measured_delta,
                                 self.source_delta) if v is not None)

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        def show(v: int | None) -> str:
            return "--" if v is None else str(v)
        return (f"{self.decision} {self.site}: gap {show(self.gap)}, "
                f"exclusion {show(self.measured_delta)}, "
                f"source {show(self.source_delta)}")


_D070 = "journal/2026-08/05-00-licensed-four-run-batch.md"
_D071 = "journal/2026-08/05-01-replicated-band-distribution.md"
_D066 = "docs/decisions.md"

#: Every per-site number D-066..D-071 published, with the file it came from.
#:
#: Licensed readings first.  The unlicensed ones are kept rather than dropped
#: because their absence would be the more misleading record --- they are what
#: the "four trees" in D-071's claim counts, and seeing that two of the four
#: cannot supply a same-tree ratio at all is part of the answer.
PUBLISHED: tuple[Cell, ...] = (
    # ---- D-070, tree 5eb5123d, k=2, licensed -----------------------------
    Cell("D-070", "5eb5123d", "lam_dependence._pure", 175, 13, None, _D070, True),
    Cell("D-070", "5eb5123d", "lam_dependence._numeric", 79, 5, None, _D070, True),
    Cell("D-070", "5eb5123d", "lam_dependence._is_pure_literal", 77, 30, None,
         _D070, True),
    Cell("D-070", "5eb5123d", "lam_dependence._is_structural", 66, 2, None,
         _D070, True),
    Cell("D-070", "5eb5123d", "guard_reflexivity._is_set_valued", 15, 2, None,
         _D070, True),
    Cell("D-070", "5eb5123d", "guard_reflexivity._has_git_diff_literal", 30, None,
         None, _D070, True),
    Cell("D-070", "5eb5123d", "guard_reflexivity._shells_out_to_git_diff", None,
         None, None, _D070, True),
    # ---- D-071, tree 9338e10e, k=3, licensed ------------------------------
    Cell("D-071", "9338e10e", "lam_dependence._pure", 214, 87, None, _D071, True),
    Cell("D-071", "9338e10e", "guard_reflexivity._is_set_valued", 13, 1, None,
         _D071, True),
    Cell("D-071", "9338e10e", "guard_reflexivity._has_git_diff_literal", 65, None,
         None, _D071, True),
    Cell("D-071", "9338e10e", "lam_dependence._numeric", None, 47, None, _D071,
         True),
    # ---- D-066 / D-067, 64- and 69-tree: TRANSPORTED under D-069 ----------
    Cell("D-066", "", "lam_dependence._pure", 142, 7, None, _D066, False),
    Cell("D-066", "", "lam_dependence._is_structural", 84, 1, None, _D066, False),
    Cell("D-066", "", "guard_reflexivity._has_git_diff_literal", 95, 30, None,
         _D066, False),
    Cell("D-066", "", "guard_reflexivity._is_set_valued", 12, 0, None, _D066, False),
    # ---- D-069, 70-tree gaps, no controls published -----------------------
    Cell("D-069", "", "lam_dependence._pure", 196, None, None, _D066, False),
    Cell("D-069", "", "guard_reflexivity._has_git_diff_literal", 29, None, None,
         _D066, False),
    Cell("D-069", "", "guard_reflexivity._shells_out_to_git_diff", 9, None, None,
         _D066, False),
    Cell("D-069", "", "guard_reflexivity._is_set_valued", 20, None, None, _D066,
         False),
    Cell("D-069", "", "lam_dependence._is_pure_literal", 88, None, None, _D066,
         False),
    Cell("D-069", "", "lam_dependence._numeric", 81, None, None, _D066, False),
    Cell("D-069", "", "lam_dependence._is_structural", 73, None, None, _D066, False),
)


def licensed(cells: Sequence[Cell] = PUBLISHED) -> tuple[Cell, ...]:
    """Only the readings D-069's :func:`exclusion_scope.single_tree` admits."""
    return tuple(c for c in cells if c.licensed)


def readings(cells: Sequence[Cell] = PUBLISHED) -> tuple[str, ...]:
    """Decision ids present, in first-appearance order."""
    out: list[str] = []
    for c in cells:
        if c.decision not in out:
            out.append(c.decision)
    return tuple(out)


def usable_sites(decision: str, cells: Sequence[Cell] = PUBLISHED,
                 both_frames: bool = False) -> tuple[str, ...]:
    """Sites in ``decision`` carrying enough numbers to form a ratio."""
    return tuple(sorted(c.site for c in cells if c.decision == decision
                        and (c.both_frames if both_frames else c.one_frame)))


def common_sites(cells: Sequence[Cell] = PUBLISHED,
                 both_frames: bool = False) -> tuple[str, ...]:
    """Sites usable in **every** licensed reading --- Q-078's actual denominator.

    The intersection, not the union: a cross-tree rank correlation ranks the
    same sites twice, and a site only one tree published cannot be ranked on the
    other without imputing a measurement nobody took.
    """
    lic = licensed(cells)
    decisions = readings(lic)
    if not decisions:
        return ()
    sets = [set(usable_sites(d, lic, both_frames)) for d in decisions]
    return tuple(sorted(set.intersection(*sets)))


def missing(cells: Sequence[Cell] = PUBLISHED) -> tuple[tuple[str, str, str], ...]:
    """``(decision, site, field)`` for every number a licensed reading omits.

    This is the shopping list.  Every entry is a quantity that *was* measured ---
    :func:`exclusion_scope.paired_reading` and :func:`~exclusion_scope.
    replicated_reading` both compute all three per site --- and then discarded
    when the cycle wrote prose instead of an artifact.
    """
    out = []
    for c in licensed(cells):
        for field, value in (("gap", c.gap), ("measured_delta", c.measured_delta),
                             ("source_delta", c.source_delta)):
            if value is None:
                out.append((c.decision, c.site, field))
    return tuple(out)


@dataclass(frozen=True)
class Answerable:
    """Whether the published record can supply Q-078's rank correlation."""

    n: int
    sites: tuple[str, ...]
    floor: int
    both_frames: bool

    @property
    def enough(self) -> bool:
        return self.n >= self.floor

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        frame = "both frames" if self.both_frames else "exclusion frame only"
        return (f"n={self.n} common sites ({frame}), floor={self.floor} -> "
                f"{'answerable' if self.enough else 'UNANSWERABLE'}")


def answerable(cells: Sequence[Cell] = PUBLISHED,
               both_frames: bool = False) -> Answerable:
    """Q-078's no-new-run half, costed against :data:`exclusion_scope.RANK_MIN_N`.

    Imported lazily so this module stays readable without pulling the measurement
    stack in; the floor belongs next to the statistic that uses it, not here.
    """
    from eval.mppi_sandbox import exclusion_scope as es

    sites = common_sites(cells, both_frames)
    return Answerable(n=len(sites), sites=sites, floor=es.RANK_MIN_N,
                      both_frames=both_frames)


def _mentions(text: str, site: str, value: int) -> bool:
    """Is ``value`` written near ``site``'s short name in ``text``?

    "Near" is one paragraph --- the prose puts a site and its numbers on the
    same line or the next one, and widening it further would make the check pass
    on any document containing enough integers.  Deliberately weak in one
    direction and not the other: a number that is absent is definitely a
    transcription error, a number that is present may still have been copied out
    of the wrong column.  Only the first failure mode is mechanisable here.
    """
    short = site.split(".")[-1]
    pattern = re.compile(rf"`{re.escape(short)}`[^\n]*(?:\n[^\n]*)?")
    return any(re.search(rf"(?<![\d.]){value}(?![\d.])", m)
               for m in pattern.findall(text))


def unverified(cells: Sequence[Cell] = PUBLISHED,
               root: Path | None = None) -> tuple[tuple[str, str, int], ...]:
    """``(decision, site, value)`` for every transcribed number not re-locatable.

    Empty is the only acceptable result and it certifies exactly one thing: the
    digits here match digits printed next to that site in the file named.  It
    does **not** certify that the number is the quantity claimed --- see the
    module docstring.  A record that needs this function is a record that should
    have been serialised at measurement time.
    """
    base = root or REPO_ROOT
    texts: dict[str, str] = {}
    out = []
    for c in cells:
        if c.source not in texts:
            path = base / c.source
            texts[c.source] = path.read_text(encoding="utf-8") if path.exists() else ""
        for value in c.numbers:
            if not _mentions(texts[c.source], c.site, value):
                out.append((c.decision, c.site, value))
    return tuple(out)


def report(cells: Sequence[Cell] = PUBLISHED) -> str:  # pragma: no cover - reporting
    one = answerable(cells, both_frames=False)
    both = answerable(cells, both_frames=True)
    lines = [f"licensed readings: {', '.join(readings(licensed(cells))) or '(none)'}",
             f"  one-frame ratio:  {one}",
             f"  both-frame ratio: {both}",
             f"  common sites:     {', '.join(one.sites) or '(none)'}",
             f"  missing cells:    {len(missing(cells))}",
             f"  unverified:       {len(unverified(cells))}",
             ""]
    for d in readings(licensed(cells)):
        lines.append(f"  {d}: usable {len(usable_sites(d, licensed(cells)))}"
                     f"/{len(SITES)} sites")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
