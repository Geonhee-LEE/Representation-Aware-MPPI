"""Where, in `lam`, each registered claim was actually measured (Q-059 lean (c)).

D-036 made ``claim_scope`` stamp every registered claim with the **machine** it
was read on.  D-039 then showed that a claim can carry a correct machine stamp
and still invert — its three supporting mechanisms all held at ``lam = 1.6`` and
none survived at ``lam = 0.1``.  Q-059 asked whether ``operating_point`` should
therefore join ``machine`` as a mandatory scope field, and leaned (c): **count
first**.  ``claim_scope`` already records each claim's instrument, so the count
is a read of instrument defaults — no simulation.

This module is that count, and the count refuses the question as posed.

Q-059 framed the defect as *measured away from the value the repo ships*.  Under
that framing 4 of the 5 registered claims are defective.  But the shipped value
is :data:`SHIPPED_LAM` = ``0.1``, and ``eval/scenarios/lam_windows.yaml`` plus
its variants file record, per ``(scene, controller)``, the rungs where **every**
seed weighted inside the ESS band and reached the goal.  Across all 24 cells:

    rung   0.05  0.1  0.2  0.4  0.8  1.6  3.2  6.4
    cells     0    0    8   13    9    7    6    3

``0.1`` is **on the ladder** — every one of the 24 cells tested it — and
qualifies **nowhere**.  Neither does ``0.05``; the plant's usable band starts at
``0.2`` and peaks at ``0.4``.  So "measured away from shipped" cannot be the
defect: it is what a careful measurement has to do on this plant.  The two
properties are in fact *anti-correlated* over the registry (:func:`census`):

* 4 of 5 claims are measured off-shipped, and every one of their points is on an
  admissible rung — except a single point that is out of band **by design**
  (``ab_protocol_overstatement``'s single-`lam` risk arm, whose out-of-bandness
  *is* the effect the claim measures, and whose own test asserts it);
* the 1 claim measured **at** the shipped ``lam`` — ``exposure_band_hi``, which
  takes ``make_controller``'s default — is the only claim in the registry with
  **no admissible operating point at all**, on any of its five scenes.

That inverts the field this was going to justify.  A required
``operating_point == shipped`` field would have marked the four sound claims and
cleared the one unsound one.  The property worth recording is not *shipped* but
**admissible**, and admissibility is already a per-cell fact the repo computes.

It also rescopes D-039 one cycle after it landed, in the same direction D-039
rescoped D-028.  D-039 read the denominator on ``cafe_obstacle_crossing_v0`` /
``risk_mppi``, whose admissible window is ``[1.6, 3.2]``; its ``lam = 1.6`` arm
is inside that window and its ``lam = 0.1`` arm is outside it.  D-039's
measurements stand — but "the shipped temperature" is not a *better* vantage
than 1.6 for that cell, it is an out-of-band one, and the rule it proposed
("measure at the weight you ship") inherits that.  A rule of the form *measure
inside the cell's admissible window* is the one the ladder actually supports.

Nothing here simulates.  Every number is read from the two window files, the
``MPPIParams`` default, and the test constants the instruments import — all
files in the repo, so this suite is true on every machine, same as
:mod:`claim_scope`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .controllers.stock_mppi import MPPIParams

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The temperature a controller runs at when nobody passes one.  Read from the
#: dataclass rather than transcribed: a future default change must move this
#: census, not silently disagree with it.
SHIPPED_LAM: float = MPPIParams().lam

#: Both calibration files.  The variants file is separate because its scenes
#: are fixtures rather than reportable surfaces, but its cells are calibrated
#: identically and two registered claims run on them.
WINDOW_FILES: tuple[str, ...] = (
    "eval/scenarios/lam_windows.yaml",
    "eval/scenarios/variants/lam_windows_variants.yaml",
)


@dataclass(frozen=True)
class OperatingPoint:
    """One ``(scene, controller, lam)`` an instrument actually simulates at."""

    scene: str
    controller: str
    lam: float
    #: what this point contributes to the claim, one line -- several claims
    #: compare two points and the comparison is the quantity.
    role: str = ""

    @property
    def is_shipped(self) -> bool:
        return self.lam == SHIPPED_LAM


#: Per registered claim, the operating points its instrument runs at.  Keys
#: must match :data:`claim_scope.SCOPED_CLAIMS` exactly -- a test enforces it.
#: Transcribed from the instruments' own imports, cited per entry:
CLAIM_OPERATING_POINTS: dict[str, tuple[OperatingPoint, ...]] = {
    # dispatch_divergence::_horizon_weight_swing -> test_horizon_audit.LAM
    "horizon_weight_swing": (
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "risk_mppi", 1.6,
                       "both horizon rungs are priced at this one temperature"),
    ),
    # dispatch_divergence::_scale_match_achieved_ratio -> test_scale_match.LAM_HI
    "scale_match_achieved_ratio": (
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "risk_mppi", 3.2,
                       "upper rung of the recorded window"),
    ),
    # dispatch_divergence::_ab_protocol_overstatement -> _paired(0.4,0.4) vs (0.8,1.6)
    "ab_protocol_overstatement": (
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "stock_mppi", 0.4,
                       "single-lam protocol, stock arm"),
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "risk_mppi", 0.4,
                       "single-lam protocol, risk arm -- out of band BY DESIGN; "
                       "the test asserts it, and the overstatement is the effect"),
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "stock_mppi", 0.8,
                       "per-arm protocol, stock arm"),
        OperatingPoint("cafe_obstacle_crossing_v0.yaml", "risk_mppi", 1.6,
                       "per-arm protocol, risk arm"),
    ),
    # dispatch_divergence::_exposure_band_hi -> make_controller default
    "exposure_band_hi": tuple(
        OperatingPoint(scene, "risk_mppi", SHIPPED_LAM,
                       "make_controller default -- no temperature passed")
        for scene in ("cafe_convoy_v0.yaml", "cafe_freezing_v0.yaml",
                      "cafe_head_on_v0.yaml", "cafe_obstacle_crossing_v0.yaml",
                      "cafe_straight_v0.yaml")
    ),
    # dispatch_divergence::_hazard_shared_rungs -> lam_ladder(..., [0.4], ...)
    "hazard_shared_rungs": (
        OperatingPoint("cafe_convoy_staggered_v0.yaml", "stock_mppi", 0.4,
                       "the single rung the ladder is asked for"),
        OperatingPoint("cafe_convoy_staggered_v0.yaml", "risk_mppi", 0.4,
                       "the single rung the ladder is asked for"),
    ),
}

#: The claim whose only operating points are the shipped default, and which is
#: for that exact reason the one with no admissible point.  Named so the census
#: cannot quietly stop reproducing the inversion this module was written for.
SHIPPED_ONLY_CLAIM = "exposure_band_hi"


def windows(root: Path | None = None) -> dict[tuple[str, str], tuple[float, ...]]:
    """``(scene, controller) -> admissible rungs``, merged over both files.

    Scene keys are bare basenames: the variants file names its scenes the same
    way the main file does, and no basename collides across the two.
    """
    out: dict[tuple[str, str], tuple[float, ...]] = {}
    for rel in WINDOW_FILES:
        doc = yaml.safe_load(((root or REPO_ROOT) / rel).read_text(encoding="utf-8"))
        for cell in doc.get("cells", ()):
            key = (Path(cell["scenario"]).name, cell["controller"])
            out[key] = tuple(cell.get("admissible") or ())
    return out


def ladder_census(root: Path | None = None) -> dict[float, int]:
    """How many cells admit each rung -- the table in this module's docstring.

    The point of reading it this way: ``SHIPPED_LAM`` is not merely unpopular,
    it is the rung with a **zero** that every cell had the chance to fill.
    """
    counts: dict[float, int] = {}
    for adm in windows(root).values():
        for rung in adm:
            counts[rung] = counts.get(rung, 0) + 1
    return counts


def is_admissible(op: OperatingPoint, root: Path | None = None) -> bool:
    """Whether ``op``'s rung is in its own cell's calibrated window.

    A cell absent from both files raises rather than returning ``False``: an
    unknown cell is a stale registry entry, which is the failure this file
    exists to make loud (D-037's surface problem, one level up).
    """
    win = windows(root)
    key = (op.scene, op.controller)
    if key not in win:
        raise LookupError(f"no calibrated window for {key}")
    return op.lam in win[key]


@dataclass(frozen=True)
class ClaimCensus:
    claim: str
    n_points: int
    n_shipped: int
    n_admissible: int

    @property
    def all_shipped(self) -> bool:
        return self.n_shipped == self.n_points

    @property
    def any_admissible(self) -> bool:
        return self.n_admissible > 0


def census(root: Path | None = None) -> tuple[ClaimCensus, ...]:
    """Per-claim counts of shipped-ness and admissibility.

    Reported side by side on purpose: the finding is the *relation* between the
    two columns, and either column alone reads as the opposite conclusion.
    """
    return tuple(
        ClaimCensus(
            claim=claim,
            n_points=len(ops),
            n_shipped=sum(1 for o in ops if o.is_shipped),
            n_admissible=sum(1 for o in ops if is_admissible(o, root)),
        )
        for claim, ops in CLAIM_OPERATING_POINTS.items()
    )


def report(root: Path | None = None) -> str:
    rows = [f"shipped lam = {SHIPPED_LAM:g}  (MPPIParams default)", ""]
    counts = ladder_census(root)
    cells = len(windows(root))
    rows.append(f"admissible-rung census over {cells} calibrated cells:")
    for rung in sorted(counts | {SHIPPED_LAM: 0}):
        mark = "  <-- shipped" if rung == SHIPPED_LAM else ""
        rows.append(f"  lam={rung:<6g} {counts.get(rung, 0):>3d} cells{mark}")
    rows += ["", f"{'claim':<28} {'pts':>4} {'shipped':>8} {'admissible':>11}"]
    for c in census(root):
        rows.append(f"{c.claim:<28} {c.n_points:>4d} {c.n_shipped:>8d} "
                    f"{c.n_admissible:>11d}")
    shipped_only = [c.claim for c in census(root) if c.all_shipped]
    no_adm = [c.claim for c in census(root) if not c.any_admissible]
    rows += [
        "",
        f"measured entirely at the shipped lam: {shipped_only or 'none'}",
        f"with no admissible operating point:   {no_adm or 'none'}",
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
