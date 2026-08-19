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

Scope limits, stated before the numbers are used:

* **Only the `cte_max` column is joined here.** `clearance` clears its floor on
  5 of 5 scenes (D-372) and no clearance claim site is in doubt, so adding them
  would grow :data:`SITES` without changing a verdict.
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

from . import aa_calibration, excursion_seed_width, excursion_tracking


class Site(NamedTuple):
    """One claim-site endpoint: where it is stated and what scene it is about."""

    #: `module.ATTR` as a reader would cite it.
    name: str
    #: Module object holding the pin, used by :func:`carries_bound`.
    module: object
    #: Attribute name on that module.
    attr: str
    #: Key into the attribute: an index for tuple pins, a scene for dict pins.
    key: int | str
    #: The calibrated column the value belongs to.
    column: str
    #: The scene the value was measured on — its floor is the only one that bounds it.
    scene: str


class Row(NamedTuple):
    """One endpoint graded against its own scene's null floor."""

    site: str
    scene: str
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
)

#: `(endpoints, endpoints clearing the p95 floor, endpoints clearing the max
#: floor)`. Finding #1, derived from :func:`audit` rather than typed.
SITE_TALLY: tuple[int, int, int] = (6, 3, 1)

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
    "undecidable at 8 seeds, in either direction"
)


def _value(site: Site) -> float:
    """The number the claim site states, pulled live from the pin."""
    pin = getattr(site.module, site.attr)
    return float(pin[site.key])


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
                round(value, 4),
                p95,
                mx,
                ratio,
                "ABOVE" if value > mx else "BELOW",
            )
        )
    return tuple(rows)


def tally() -> tuple[int, int, int]:
    """`(endpoints, clearing p95, clearing max)` — derives :data:`SITE_TALLY`."""
    rows = audit()
    return (
        len(rows),
        sum(1 for r in rows if r.value > r.p95_floor),
        sum(1 for r in rows if r.value > r.max_floor),
    )


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
    print(f"\ntally (endpoints, >p95, >max): {tally()}")
    print(f"verdict: {VERDICT}")

    rc = 0
    if tally() != SITE_TALLY:
        print(f"DRIFT: tally {tally()} != SITE_TALLY {SITE_TALLY}", file=sys.stderr)
        rc = 1
    if unjoined() != UNJOINED:
        print(f"DRIFT: unjoined {unjoined()} != UNJOINED {UNJOINED}", file=sys.stderr)
        rc = 1
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
