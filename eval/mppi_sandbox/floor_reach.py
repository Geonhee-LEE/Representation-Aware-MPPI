# SPDX-License-Identifier: BSD-3-Clause
"""Carry the A-A floor to the sites that state the cross-track claim — and count what survives.

D-371 measured the null floor and D-372 widened it to seven cells, but both
findings live in :mod:`aa_calibration`. The modules that *state* the claims the
floor bounds — :data:`excursion_tracking.SPREAD_SEPARATES`,
:data:`excursion_seed_width.ROBUST_SEPARATION`, :data:`excursion_seed_width.INTERSECTION`
— still read exactly as they did before the calibration existed. `STATE.md` has
named this gap ("the answer sits beside the question, unjoined") for **five
consecutive cycles**. This module is the join, built rather than named a sixth
time.

Nothing here is a new measurement. Every number is
:mod:`aa_calibration`'s floor divided into a value the claim sites already pin,
which is why it costs **zero rollouts**. What it buys is that the division now
happens in code that a test runs, instead of in prose a reader has to remember.

**The join is by pointer, not by import.** :mod:`aa_calibration` already reads
:data:`excursion_seed_width.SEED_ENSEMBLE`, so a floor pin placed *inside* the
claim-site modules would close an import cycle. The claim sites therefore carry
a **textual** cross-reference to this module and :func:`carries_bound` checks
the source for it — see finding #3.

**Finding #1 — of the six cross-track endpoints this branch states, exactly
one clears its own null floor on the adversarial reading, and it is the one no
claim rests on alone.** Each endpoint against the floors of the scene it was
measured on:

    site                    scene              value    p95 floor  max floor  vs max
    SPREAD_SEPARATES[0]     cafe_convoy_v0     0.1441      0.0659     0.0673   2.14x  ABOVE
    SPREAD_SEPARATES[1]     city_curved_v0     0.0730      0.0472     0.0760   0.96x  below
    ROBUST_SEPARATION[0]    cafe_convoy_v0     0.0612      0.0659     0.0673   0.91x  below
    ROBUST_SEPARATION[1]    city_curved_v0     0.0730      0.0472     0.0760   0.96x  below
    INTERSECTION[convoy]    cafe_convoy_v0     0.0550      0.0659     0.0673   0.82x  below
    INTERSECTION[curved]    city_curved_v0    -0.0392      0.0472     0.0760     n/a  below

:data:`SITE_TALLY` pins `(6, 3, 1)`, derived from :func:`audit` rather than
typed — and the gap between its second and third entries is itself the point.
**Three** endpoints clear the p95 floor and only **one** clears the max, so on
`city_curved_v0` the choice of reading decides the answer: its two floors are
`0.0472` and `0.0760`, a `1.61x` spread, and the `0.0730` endpoints sit between
them. D-371's scope limit already called `max_floor` adversarial and `p95_floor`
the fairer reading; this is the first place on the branch where the two give
opposite verdicts on the same number, so both are reported and no claim below
rests on the p95 reading alone.

The single max-clearing endpoint is `SPREAD_SEPARATES`'s **excited** minimum,
and `SPREAD_SEPARATES` is a min-vs-max claim: it needs *both* endpoints to be
real for "with no overlap" to mean anything, and its maximum is `0.96x`. So one
endpoint clearing licenses nothing on its own. :data:`ONLY_CLEARING_ENDPOINT`
names it so the asymmetry is not read as partial support.

The typed-then-corrected history of this pin is worth one line: it was first
written `(6, 1, 1)` from the docstring table above, and the CLI's own drift
check caught it before the suite did. A pin derived from :func:`audit` cannot
be wrong for longer than one run of the module.

**Finding #2 — the one cross-track result D-370 left standing does not survive
the floor either.** D-370's finding #4 separated the two scenes by per-seed
intersection width: `city_curved_v0` came out **negative** (`-0.0392`, no bar
cuts every seed) while `cafe_convoy_v0` stayed `+0.0550` and was reported as
"barrable at seed width with a midpoint bar verified to cut all eight seeds".
That verification is sound on its own terms — the bar really does cut all eight
seeds. But `0.0550` is **`0.82x`** of convoy's own max null floor, so a window
that width is one this harness manufactures from a zero effect. The
verification and the floor are asking different questions and only the second
one bounds the claim.

This closes the last cross-track number on the branch that had not been put
against a floor. D-371 finding #2 found `ROBUST_SEPARATION`'s two endpoints
below; D-372 found the column split; this finds that the survivor D-370
explicitly carried forward is below as well. The cross-track column is not
*mostly* unreadable at eight seeds — :data:`VERDICT` states the tally.

**Finding #3 — the gap `STATE.md` kept naming is structural, and it is
checkable.** Before this module, neither claim-site file mentioned
:mod:`aa_calibration` anywhere in its source: a reader arriving at
`ROBUST_SEPARATION` had no path to the finding that voids it, and five cycles
of prose did not change that. :func:`carries_bound` reads each site module's
source and reports whether it names this module, so "unjoined" becomes a test
failure rather than a `STATE.md` bullet. :data:`UNJOINED` pins the set that
still fails; it is empty, and the CLI goes `rc=1` if it stops being.

**Finding #4 — the clearance column joined too, and the number that licenses a
bar declaration is not the number D-372 reported.** D-373 left `clearance` out
on the reasoning that it clears 5 of 5 (D-372) so joining it "would grow
:data:`SITES` without changing a verdict". That reasoning graded the wrong
quantity. D-372's `2.44x`–`6.28x` are ratios of the **A-B gap between arm
means**; what sits in `STATE.md`'s user-blocked queue is a **bar window** —
`declaration_gap.COMMON_WINDOW` and `seed_debt.WINDOWS` — whose width is set by
per-seed *extremes*, not by means. A window is the narrower object, and grading
it against the same floor gives a uniformly tighter set of margins. Both columns
below are the **adversarial `max` reading**, which is this module's `ratio`
field; D-372's quoted `2.44x`–`6.28x` are `p95`-based, and restating its gaps on
`max` gives `2.12x`–`5.76x`. Comparing a window against a `p95` gap would have
manufactured most of finding #4, so the comparison is like-for-like:

    site                                  scene                       width  max floor  window   D-372 gap
    declaration_gap.COMMON_WINDOW         cafe_freezing_v0           0.4354     0.0800   5.44x       5.76x
    seed_debt.WINDOWS[cafe_convoy_v0]     cafe_convoy_v0             0.2224     0.0572   3.89x       4.73x
    seed_debt.WINDOWS[cafe_cut_in_v0]     cafe_cut_in_v0             0.2664     0.1543   1.73x       2.12x
    seed_debt.WINDOWS[cafe_head_on_v0]    cafe_head_on_v0            0.1001     0.0433   2.31x       4.11x
    seed_debt.WINDOWS[obstacle_crossing]  cafe_obstacle_crossing_v0  0.1298     0.0855   1.52x       2.46x

All five still clear on the adversarial reading — :data:`CLEARANCE_TALLY` pins
`(5, 5, 5)`, so the *direction* of D-373's guess was right and the clearance
column stays licensed. What it got wrong is the **margin**, on every scene
without exception: :data:`WINDOW_UNDER_GAP` records that the window ratio is
below the gap ratio 5 times out of 5, by as much as `1.78x` on `cafe_head_on_v0`
(`4.11x` → `2.31x`). The thinnest is `cafe_obstacle_crossing_v0` at **`1.52x`**
(:data:`THINNEST_WINDOW`), the smallest clearance margin anywhere on the branch
and a little over half what the same scene's gap ratio suggests.

The asymmetry this closes is the one `STATE.md` named: after D-373 the
cross-track claims were bounded by a census a test runs, while the clearance
claims — the ones actually awaiting a human decision — were bounded only by
D-372's prose. Both columns now go through :func:`audit`.

Scope limits, stated before the numbers are used:

* **Both calibrated columns are joined.** `cte_max` endpoints are graded as
  values (finding #1); `clearance` sites are graded as **window widths**
  (finding #4), via :attr:`Site.reading`. The two readings are not comparable to
  each other and no pin mixes them — :func:`tally` takes a column.
* **A window ratio and a gap ratio answer different questions.** The gap asks
  *can the harness see this difference at all*; the window asks *is the range of
  bar values that separates the arms wider than the range a zero effect
  manufactures*. The second is the one a declaration needs, which is why
  finding #4 supersedes D-372's numbers for the user-blocked items rather than
  contradicting them.
* **The floors are `aa_calibration`'s and inherit its scope**, including that a
  calibration does not transfer across scenes (D-371 finding #3). Every row
  here is matched to the scene it was measured on; no endpoint is graded
  against another scene's floor.
* **A ratio below `1.0` is not a refutation of the claim** — it says the
  harness cannot resolve a difference that size at eight seeds, in either
  direction. That symmetry is D-371 finding #2's and it is preserved:
  :data:`VERDICT` says `undecidable`, never `false`.
* **`INTERSECTION[city_curved_v0]` is negative** and so cannot be a ratio; it is
  carried as `BELOW` by inspection (a negative width is under any positive
  floor) and :func:`audit` reports it with `ratio=None`.

CLI:
    python -m eval.mppi_sandbox.floor_reach   # rc=1 on drift from the pins
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NamedTuple

from . import (
    aa_calibration,
    declaration_gap,
    excursion_seed_width,
    excursion_tracking,
    seed_debt,
)


class Site(NamedTuple):
    """One claim-site endpoint: where it is stated and what scene it is about."""

    #: `module.ATTR` as a reader would cite it.
    name: str
    #: Module object holding the pin, used by :func:`carries_bound`.
    module: object
    #: Attribute name on that module.
    attr: str
    #: Key into the attribute: an index for tuple pins, a scene for dict pins,
    #: `None` when the attribute itself is the value.
    key: int | str | None
    #: The calibrated column the value belongs to.
    column: str
    #: The scene the value was measured on — its floor is the only one that bounds it.
    scene: str
    #: How to turn the pin into the graded number. `"endpoint"` takes it as a
    #: scalar (`cte_max` sites); `"width"` takes `hi - lo` of a two-element
    #: interval (`clearance` bar windows — finding #4).
    reading: str = "endpoint"


class Row(NamedTuple):
    """One endpoint graded against its own scene's null floor."""

    site: str
    scene: str
    #: The calibrated column, so a consumer never mixes the two readings.
    column: str
    value: float
    p95_floor: float
    max_floor: float
    #: `value / max_floor`, or `None` when `value` is negative.
    ratio: float | None
    #: `"ABOVE"` iff the value exceeds the adversarial max floor.
    verdict: str


#: The cross-track endpoints this branch states, each with the scene whose floor
#: bounds it. Ordered as the module docstring's table.
SITES: tuple[Site, ...] = (
    Site(
        "excursion_tracking.SPREAD_SEPARATES[0]",
        excursion_tracking,
        "SPREAD_SEPARATES",
        0,
        "cte_max",
        "cafe_convoy_v0",
    ),
    Site(
        "excursion_tracking.SPREAD_SEPARATES[1]",
        excursion_tracking,
        "SPREAD_SEPARATES",
        1,
        "cte_max",
        "city_curved_v0",
    ),
    Site(
        "excursion_seed_width.ROBUST_SEPARATION[0]",
        excursion_seed_width,
        "ROBUST_SEPARATION",
        0,
        "cte_max",
        "cafe_convoy_v0",
    ),
    Site(
        "excursion_seed_width.ROBUST_SEPARATION[1]",
        excursion_seed_width,
        "ROBUST_SEPARATION",
        1,
        "cte_max",
        "city_curved_v0",
    ),
    Site(
        "excursion_seed_width.INTERSECTION[cafe_convoy_v0]",
        excursion_seed_width,
        "INTERSECTION",
        "cafe_convoy_v0",
        "cte_max",
        "cafe_convoy_v0",
    ),
    Site(
        "excursion_seed_width.INTERSECTION[city_curved_v0]",
        excursion_seed_width,
        "INTERSECTION",
        "city_curved_v0",
        "cte_max",
        "city_curved_v0",
    ),
    # Finding #4 — the clearance bar windows, graded as widths.
    Site(
        "declaration_gap.COMMON_WINDOW",
        declaration_gap,
        "COMMON_WINDOW",
        None,
        "clearance",
        "cafe_freezing_v0",
        "width",
    ),
    Site(
        "seed_debt.WINDOWS[cafe_convoy_v0]",
        seed_debt,
        "WINDOWS",
        "cafe_convoy_v0",
        "clearance",
        "cafe_convoy_v0",
        "width",
    ),
    Site(
        "seed_debt.WINDOWS[cafe_cut_in_v0]",
        seed_debt,
        "WINDOWS",
        "cafe_cut_in_v0",
        "clearance",
        "cafe_cut_in_v0",
        "width",
    ),
    Site(
        "seed_debt.WINDOWS[cafe_head_on_v0]",
        seed_debt,
        "WINDOWS",
        "cafe_head_on_v0",
        "clearance",
        "cafe_head_on_v0",
        "width",
    ),
    Site(
        "seed_debt.WINDOWS[cafe_obstacle_crossing_v0]",
        seed_debt,
        "WINDOWS",
        "cafe_obstacle_crossing_v0",
        "clearance",
        "cafe_obstacle_crossing_v0",
        "width",
    ),
)

#: `(endpoints, endpoints clearing the p95 floor, endpoints clearing the max
#: floor)` for the **`cte_max`** column. Finding #1, derived from :func:`audit`
#: rather than typed. Scoped to one column since D-374 added the other.
SITE_TALLY: tuple[int, int, int] = (6, 3, 1)

#: The same tally for the **`clearance`** column's bar windows — `(5, 5, 5)`.
#: Finding #4: every declarable window still clears, on both readings.
CLEARANCE_TALLY: tuple[int, int, int] = (5, 5, 5)

#: Finding #4's comparison, `scene -> (window ratio, D-372 gap ratio)`, both
#: against the same **max** floor. The window is the narrower object on **all
#: five** scenes, which is why a gap ratio must not be quoted to license a
#: declaration.
WINDOW_UNDER_GAP: dict[str, tuple[float, float]] = {
    "cafe_freezing_v0": (5.4425, 5.7575),
    "cafe_convoy_v0": (3.8881, 4.7273),
    "cafe_cut_in_v0": (1.7265, 2.116),
    "cafe_head_on_v0": (2.3118, 4.1132),
    "cafe_obstacle_crossing_v0": (1.5181, 2.4573),
}

#: The thinnest clearance margin on the branch: `(scene, window ratio)`. A
#: little over half the same scene's `2.46x` gap ratio.
THINNEST_WINDOW: tuple[str, float] = ("cafe_obstacle_crossing_v0", 1.5181)

#: The only endpoint that clears its own floor, and by how much against the max
#: floor. It is a min-vs-max claim's *minimum*, so it licenses nothing alone.
ONLY_CLEARING_ENDPOINT: tuple[str, float] = (
    "excursion_tracking.SPREAD_SEPARATES[0]",
    2.1412,
)

#: Finding #2 — D-370's surviving cross-track result against convoy's own max
#: floor: `(value, max floor, ratio)`. A window this harness manufactures.
INTERSECTION_UNDER_FLOOR: tuple[float, float, float] = (0.055, 0.0673, 0.8172)

#: Claim-site modules whose source does not name this module, i.e. that still
#: state a bounded number with no path to its bound. Finding #3 — empty, and
#: the CLI fails if it stops being.
UNJOINED: tuple[str, ...] = ()

#: What the join leaves standing of the cross-track comparison, in one string.
#: `undecidable`, never `false` — the floor is symmetric (scope limit 3).
VERDICT: str = (
    "5 of 6 cross-track endpoints sit below their own scene's max null floor; "
    "the 6th is a min-vs-max minimum whose maximum does not clear — "
    "undecidable at 8 seeds, in either direction. All 5 clearance bar windows "
    "clear their own floor (1.52x-5.44x) but every one of them clears by less "
    "than its scene's arm-gap ratio, so a declaration must quote the window"
)


def _value(site: Site) -> float:
    """The number the claim site states, pulled live from the pin.

    Two readings (see :attr:`Site.reading`): a `cte_max` endpoint is the pin
    itself, a `clearance` bar window is the pin's **width**.
    """
    pin = getattr(site.module, site.attr)
    if site.key is not None:
        pin = pin[site.key]
    if site.reading == "width":
        lo, hi = pin
        return float(hi) - float(lo)
    return float(pin)


def audit() -> tuple[Row, ...]:
    """Grade every endpoint in :data:`SITES` against its own scene's floors.

    Zero rollouts: :mod:`aa_calibration` computes both floors from seed
    ensembles already on disk, and the values come from the claim-site pins.
    """
    rows: list[Row] = []
    for site in SITES:
        value = _value(site)
        p95 = round(aa_calibration.p95_floor(site.column, site.scene), 4)
        mx = round(aa_calibration.max_floor(site.column, site.scene), 4)
        ratio = round(value / mx, 4) if value > 0 else None
        rows.append(
            Row(
                site.name,
                site.scene,
                site.column,
                round(value, 4),
                p95,
                mx,
                ratio,
                "ABOVE" if value > mx else "BELOW",
            )
        )
    return tuple(rows)


def tally(column: str = "cte_max") -> tuple[int, int, int]:
    """`(endpoints, clearing p95, clearing max)` for one calibrated column.

    Takes a column because the two readings are not comparable (scope limit 2):
    `cte_max` derives :data:`SITE_TALLY`, `clearance` derives
    :data:`CLEARANCE_TALLY`.
    """
    rows = [r for r in audit() if r.column == column]
    return (
        len(rows),
        sum(1 for r in rows if r.value > r.p95_floor),
        sum(1 for r in rows if r.value > r.max_floor),
    )


def window_vs_gap() -> dict[str, tuple[float, float]]:
    """`scene -> (window ratio, D-372 gap ratio)` — derives :data:`WINDOW_UNDER_GAP`.

    Both ratios are taken against the **max** floor, so the comparison is
    like-for-like (see the docstring table). The gap numerators come from
    :data:`aa_calibration.FLOOR_VERDICT` rather than being re-typed here, which
    is why `aa_calibration` moving a cell moves this pin.
    """
    out: dict[str, tuple[float, float]] = {}
    for r in audit():
        if r.column != "clearance" or r.ratio is None:
            continue
        gap, _p95, mx = aa_calibration.FLOOR_VERDICT[(r.column, r.scene)]
        out[r.scene] = (r.ratio, round(gap / mx, 4))
    return out


def carries_bound(root: Path | None = None) -> dict[str, bool]:
    """`module -> does its source name this module?` — finding #3's check.

    The join is textual by necessity (see the module docstring): an import from
    a claim-site module into :mod:`aa_calibration` would close a cycle, so the
    sites point at :mod:`floor_reach` in prose and this reads the source back.
    """
    base = root or Path(__file__).resolve().parent
    out: dict[str, bool] = {}
    for site in SITES:
        mod = site.module.__name__.rsplit(".", 1)[-1]
        if mod in out:
            continue
        out[mod] = "floor_reach" in (base / f"{mod}.py").read_text(encoding="utf-8")
    return out


def unjoined(root: Path | None = None) -> tuple[str, ...]:
    """Claim-site modules still stating a bounded number with no path to it."""
    return tuple(sorted(m for m, ok in carries_bound(root).items() if not ok))


def main() -> int:
    rows = audit()
    for r in rows:
        ratio = "n/a" if r.ratio is None else f"{r.ratio:.4f}x"
        print(
            f"{r.site:<48} {r.scene:<18} {r.value:>8.4f} "
            f"p95={r.p95_floor:.4f} max={r.max_floor:.4f} {ratio:>9} {r.verdict}"
        )
    print(f"\ncte_max   tally (endpoints, >p95, >max): {tally('cte_max')}")
    print(f"clearance tally (windows,   >p95, >max): {tally('clearance')}")
    for scene, (win, gap) in sorted(window_vs_gap().items()):
        print(f"  {scene:<28} window={win:.4f}x  gap={gap:.4f}x")
    print(f"verdict: {VERDICT}")

    rc = 0
    if tally("cte_max") != SITE_TALLY:
        print(
            f"DRIFT: tally {tally('cte_max')} != SITE_TALLY {SITE_TALLY}",
            file=sys.stderr,
        )
        rc = 1
    if tally("clearance") != CLEARANCE_TALLY:
        print(
            f"DRIFT: clearance tally {tally('clearance')} != "
            f"CLEARANCE_TALLY {CLEARANCE_TALLY}",
            file=sys.stderr,
        )
        rc = 1
    if window_vs_gap() != WINDOW_UNDER_GAP:
        print(
            f"DRIFT: window_vs_gap {window_vs_gap()} != "
            f"WINDOW_UNDER_GAP {WINDOW_UNDER_GAP}",
            file=sys.stderr,
        )
        rc = 1
    if unjoined() != UNJOINED:
        print(f"DRIFT: unjoined {unjoined()} != UNJOINED {UNJOINED}", file=sys.stderr)
        rc = 1
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
