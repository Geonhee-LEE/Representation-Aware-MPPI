"""Q-081: does any published magnitude survive its own ``gap_spread``?

D-074 measured the thing six cycles of magnitude comparison had assumed: how far
a gap moves when **nothing** changes.  Three replicates of one frozen tree, one
batch, and the answer was 1.14x to 4.50x depending on the site.  D-069's
*cross-tree* ratios over the same seven sites spanned 0.31 to 1.67 --- a fold of
at most 3.2x --- so the same-tree spread brackets and exceeds the cross-tree
spread, and the variable four cycles were reading was the run, not the tree.

That retired an explanation.  It did not touch the numbers themselves, and this
branch has published a lot of numbers.  Q-081 asks the follow-up in the only
form that costs nothing: :mod:`published_ratios` already transcribes every
per-site digit D-066..D-071 printed, and the D-074 record is on disk with a
per-site band.  The join is one pass, and **the size of the answer is the
finding**.

What is actually being asked
----------------------------

Two different questions, and keeping them apart is most of the work:

**Containment** --- is a published gap inside its site's same-tree band?  This
is the weaker question and it is nearly uninformative on its own.  A gap outside
the band is not thereby a survivor: it is a number from a *different tree*, and
"differs from a band measured elsewhere" is the transported reading D-069
already forbids.  :func:`standings` reports it because it is cheap and because
the direction is occasionally interesting, not because it grades anything.

**Movement** --- prose on this branch did not usually quote one magnitude; it
quoted a *series*.  ``_pure``'s gap was published as 142, then 196, then 175,
then 214, and each step was written as though the tree had moved.  A step
survives iff the fold between the two published numbers **exceeds the site's
own same-tree spread**.  This is the graded question, it is what
:func:`movements` answers, and it is licensed by exactly one thing: that both
endpoints are the same quantity measured by the same instrument, so a fold
smaller than the instrument's own reproducibility is not evidence of anything.

Both questions are asked of gaps (:data:`KIND_GAP`) and of ratios
(:data:`KIND_RATIO`) --- the ratio is what D-071's headline "2.5x to 13x"
quoted, so a survival audit that only looked at gaps would miss the most-cited
numbers on the branch.

The license, stated rather than assumed
---------------------------------------

The band is measured on tree ``c4b76066``.  Not one published magnitude is from
that tree.  So under D-069-as-written this entire join is
:data:`exclusion_scope.ATTR_TRANSPORTED` and may not be read --- and under
D-074-as-measured, D-069's premise is false and the join is the correct thing to
do.  **Those two cannot both be quoted**, which is why :func:`license_status`
returns the tension instead of a boolean, and why :func:`report` prints it
first.  The resolution this module proposes and does not assume: a *spread* is a
fold, folds were never shown to transport either, and the honest scope is
"these numbers do not survive the noise floor of the instrument that produced
them", not "these numbers are wrong".

One number is deliberately excluded.  D-074 published ``_pure``'s gap as **326**;
326 is the ``hi`` of ``_pure``'s own band in this record.  Grading it against a
band it defines is circular, and :data:`SELF_DEFINING` names it so a future
cycle does not quietly re-add it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from eval.mppi_sandbox import claim_scope, published_ratios, reading_record

REPO_ROOT = claim_scope.REPO_ROOT

#: The D-074 record --- the only reading on this branch that carries replicates
#: of one frozen tree, hence the only one that can supply a band at all.
DEFAULT_RECORD = Path("results/readings/2026-08-05-04-ordering-control.json")

#: The two quantities this branch published per site.
KIND_GAP = "gap"
KIND_RATIO = "ratio"
KINDS: tuple[str, ...] = (KIND_GAP, KIND_RATIO)

#: ``(decision, site, kind)`` whose published value came **out of the banding
#: record itself**, so it cannot be graded against that band without circularity.
#: See the module docstring's last paragraph.
SELF_DEFINING: tuple[tuple[str, str, str], ...] = (
    ("D-074", "lam_dependence._pure", KIND_GAP),
)

#: What :func:`license_status` reports.  Not a boolean, because the two clauses
#: are both live and contradict each other --- see the module docstring.
LICENSE_CONTESTED = (
    "CONTESTED: the band is tree c4b76066 and no published magnitude is; "
    "D-069-as-written grades this join TRANSPORTED, D-074-as-measured says "
    "D-069's premise is false.  Scope claims to 'below the instrument's own "
    "noise floor', not to 'wrong'."
)


@dataclass(frozen=True)
class Band:
    """One site's same-tree spread for one quantity."""

    site: str
    kind: str
    lo: float
    hi: float

    @property
    def spread(self) -> float:
        """``hi / lo`` --- the fold the instrument produces under no change."""
        return self.hi / self.lo

    def contains(self, value: float) -> bool:
        return self.lo <= value <= self.hi

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.site} [{self.kind}] {self.lo:g}..{self.hi:g} "
                f"({self.spread:.2f}x)")


def bands(record: reading_record.Record, kind: str = KIND_GAP) -> dict[str, Band]:
    """Per-site same-tree band, keyed on site.

    Reads the record's own spread properties rather than recomputing from cells:
    two spellings of one statistic is D-047's defect in miniature, and the
    record already had to get this right for D-074.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    rows = (record.gap_spread if kind == KIND_GAP else record.ratio_spread())
    return {site: Band(site, kind, lo, hi) for site, lo, hi, _ in rows}


def published(cells: Sequence[published_ratios.Cell] | None = None,
              kind: str = KIND_GAP) -> tuple[tuple[str, str, float], ...]:
    """``(decision, site, value)`` for every published value of ``kind``.

    The ratio is reconstructed as ``gap / measured_delta`` --- the exclusion
    frame alone, because that is the denominator every one of these numbers was
    actually divided by (Q-079).  A cell missing either half supplies no ratio
    and is simply absent; :func:`unbanded` is where that absence gets counted.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    src = published_ratios.PUBLISHED if cells is None else cells
    out: list[tuple[str, str, float]] = []
    for c in src:
        if kind == KIND_GAP:
            if c.gap is not None:
                out.append((c.decision, c.site, float(c.gap)))
        elif c.one_frame and c.measured_delta:
            out.append((c.decision, c.site, c.gap / c.measured_delta))
    return tuple(o for o in out if (o[0], o[1], kind) not in SELF_DEFINING)


#: A published ratio whose denominator is at or below this is one or two counts
#: away from :data:`exclusion_scope.ATTR_FOLD`, i.e. from being infinite.  Its
#: fold against another reading is then driven almost entirely by a
#: single-digit control, and calling that a surviving magnitude would launder
#: the same defect :meth:`reading_record.Record.ratio_spread` drops a site for.
#: 2, not 1: ``ratio_spread`` already refuses 0, and a control of 2 moving to 1
#: --- one count --- doubles the ratio on its own.
FRAGILE_CONTROL = 2


def fragile(cells: Sequence[published_ratios.Cell] | None = None
            ) -> tuple[tuple[str, str, int], ...]:
    """``(decision, site, control)`` for published ratios resting on a tiny control.

    Reported alongside the ratio survival rate rather than subtracted from it:
    these movements are not *refuted*, they are movements whose denominator this
    record cannot show to be stable, and the two deserve different words.
    """
    src = published_ratios.PUBLISHED if cells is None else cells
    return tuple((c.decision, c.site, c.measured_delta) for c in src
                 if c.one_frame and c.measured_delta
                 and c.measured_delta <= FRAGILE_CONTROL)


@dataclass(frozen=True)
class Standing:
    """One published value against its site's band.  The *weak* question."""

    decision: str
    site: str
    kind: str
    value: float
    band: Band

    @property
    def inside(self) -> bool:
        return self.band.contains(self.value)

    @property
    def side(self) -> str:
        """``inside`` / ``below`` / ``above`` --- direction, not a grade."""
        if self.inside:
            return "inside"
        return "below" if self.value < self.band.lo else "above"


def standings(record: reading_record.Record,
              cells: Sequence[published_ratios.Cell] | None = None,
              kind: str = KIND_GAP) -> tuple[Standing, ...]:
    """Every published value that has a band, against it."""
    banded = bands(record, kind)
    return tuple(Standing(d, s, kind, v, banded[s])
                 for d, s, v in published(cells, kind) if s in banded)


def unbanded(record: reading_record.Record,
             cells: Sequence[published_ratios.Cell] | None = None,
             kind: str = KIND_GAP) -> tuple[tuple[str, str], ...]:
    """``(decision, site)`` published without a band to grade it against.

    Two causes, both real and neither a defect in the record: the site's control
    was 0 in some replicate (a fold --- see :meth:`reading_record.Record.
    ratio_spread`), or the record's replicates never produced a non-zero gap
    there.  Counted so the survival rate below is quoted over a denominator
    somebody can check.
    """
    banded = bands(record, kind)
    return tuple((d, s) for d, s, _ in published(cells, kind) if s not in banded)


@dataclass(frozen=True)
class Movement:
    """A fold between two published values of one site, against its band.

    This is the graded question.  ``earlier`` / ``later`` are publication order
    in :data:`published_ratios.PUBLISHED`, not chronology --- the decisions
    interleave, and nothing here depends on which came first.
    """

    site: str
    kind: str
    earlier: tuple[str, float]
    later: tuple[str, float]
    band: Band

    @property
    def fold(self) -> float:
        a, b = self.earlier[1], self.later[1]
        lo, hi = min(a, b), max(a, b)
        return float("inf") if lo == 0 else hi / lo

    @property
    def survives(self) -> bool:
        """Strictly exceeds the same-tree spread.

        Strict, not ``>=``: a fold exactly equal to the instrument's own
        reproducibility is precisely the case the instrument cannot distinguish.
        """
        return self.fold > self.band.spread

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        mark = "survives" if self.survives else "NOISE"
        return (f"{self.site} [{self.kind}] {self.earlier[0]} {self.earlier[1]:g}"
                f" vs {self.later[0]} {self.later[1]:g}: fold {self.fold:.2f}x "
                f"vs spread {self.band.spread:.2f}x -> {mark}")


def movements(record: reading_record.Record,
              cells: Sequence[published_ratios.Cell] | None = None,
              kind: str = KIND_GAP) -> tuple[Movement, ...]:
    """Every same-site pair of published values, graded against the band.

    Sorted survivors-first then by descending fold, so the head of the list is
    the set of magnitude claims this branch can still make.
    """
    banded = bands(record, kind)
    by_site: dict[str, list[tuple[str, float]]] = {}
    for decision, site, value in published(cells, kind):
        if site in banded:
            by_site.setdefault(site, []).append((decision, value))
    out: list[Movement] = []
    for site, vals in by_site.items():
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                out.append(Movement(site, kind, vals[i], vals[j], banded[site]))
    return tuple(sorted(out, key=lambda m: (not m.survives, -m.fold, m.site)))


@dataclass(frozen=True)
class Survival:
    """The answer to Q-081 for one quantity, as counts."""

    kind: str
    total: int
    surviving: int
    sites_total: int
    sites_surviving: int
    unbanded: int

    @property
    def rate(self) -> float:
        return 0.0 if not self.total else self.surviving / self.total

    def __str__(self) -> str:  # pragma: no cover - reporting sugar
        return (f"{self.kind}: {self.surviving}/{self.total} movements survive "
                f"({self.rate:.0%}) across {self.sites_surviving}/"
                f"{self.sites_total} sites; {self.unbanded} published values "
                f"unbanded")


def survival(record: reading_record.Record,
             cells: Sequence[published_ratios.Cell] | None = None,
             kind: str = KIND_GAP) -> Survival:
    """Q-081, counted."""
    moves = movements(record, cells, kind)
    lived = [m for m in moves if m.survives]
    return Survival(kind=kind, total=len(moves), surviving=len(lived),
                    sites_total=len({m.site for m in moves}),
                    sites_surviving=len({m.site for m in lived}),
                    unbanded=len(unbanded(record, cells, kind)))


def license_status() -> str:
    """The tension, not a verdict.  See the module docstring."""
    return LICENSE_CONTESTED


def load(path: Path | None = None, root: Path | None = None
         ) -> reading_record.Record:
    """The D-074 record off disk."""
    base = root or REPO_ROOT
    return reading_record.read(base / (path or DEFAULT_RECORD))


def report(record: reading_record.Record | None = None
           ) -> str:  # pragma: no cover - reporting
    rec = record or load()
    lines = [f"license: {license_status()}", ""]
    for kind in KINDS:
        lines.append(str(survival(rec, None, kind)))
        for m in movements(rec, None, kind):
            lines.append(f"  {m}")
        lines.append("")
    lines.append("fragile ratio denominators (<= "
                 f"{FRAGILE_CONTROL}): {len(fragile())}")
    for decision, site, control in fragile():
        lines.append(f"  {decision} {site}: control {control}")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - CLI
    print(report())
