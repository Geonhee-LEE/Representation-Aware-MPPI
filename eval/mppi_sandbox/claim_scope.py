"""Bind every dispatch-fragile claim to the prose that cites it (STATE #1, #3).

D-035 priced what it would cost to make each of the five flipping claims hold on
both SIMD dispatches, and answered in units of the **assertion**: the
``horizon_weight_swing`` threshold would have to drop ``1.2 -> 1.0289``, keeping
14.4 % of the asserted effect.  That is the right unit for deciding whether a
test still tests anything.  It is *not* the unit that propagates.

What propagates is the **citation** — the number a later document writes down
when it reuses the result.  Two things can go wrong there, and only one of them
is what D-032/D-033/D-034/D-035 were about:

1. **dispatch fragility** — the instrument's own reading collapses when the
   machine changes (``1.30078`` on AVX-512, ``1.02888`` on AVX2).  Priced.
2. **citation drift** — the prose states a number the instrument never measured,
   because it was computed over a different span, a different pair of rungs, or
   a different statistic.  Unpriced, unnoticed, and strictly more dangerous:
   fragility at least shows up as a red test somewhere.

This module exists because the two are currently **entangled** in this repo's
own record.  ``D-030`` reports the scale-matched ``w_voo`` amplitude as
``2.0×``, which is ``w(H=34)/w(H=15)``.  The instrument that flips —
:func:`dispatch_divergence._horizon_weight_swing` — computes
``w(H=34)/w(H=30) = 1.30078``.  Every downstream citation (D-032, D-033, Q-054,
Q-055) then paired the prose's ``2.0×`` against the instrument's AVX2 reading
``1.029×`` and read a near-total collapse.  The collapse is real; **its size was
never that large**.  The honest pair is ``1.301 vs 1.029``.

So the registry below records, per claim: the oracle the calibrated number came
off (D-033's coordinate, the "reference oracle" field of a kernel contract), the
instrument that defines the quantity, both readings, and **every place in
``docs/`` that states a number for it** — tagged with whether that number is the
instrument's or a different quantity's.  The tests turn each into a check:

* a citation tagged ``instrument`` must state the calibrated reading (± 1 %);
* a citation tagged ``other-quantity`` must name the instrument's reading too,
  so the two can never again be compared as if they were one;
* every cited section must carry the oracle stamp, so no reader meets one of
  these numbers without meeting the machine it is conditional on.

This asserts nothing about the *simulated* values — same rule as
:mod:`dispatch_divergence` and :mod:`repair_admissibility`, and for the same
reason.  It asserts only that the prose and the banked readings agree, which is
a property of files in the repo and is therefore true on every machine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: The SIMD extension whose presence selects the calibrated numeric path
#: (D-033).  Stamped into every doc section that states one of these numbers.
ORACLE = "AVX512_SKX"

#: Null of a one-sided ratio claim: 1.0 means "no effect".
RATIO_NULL = 1.0

#: How far a cited number may sit from the reading it claims to be.  Tight on
#: purpose -- the point is to catch a *different quantity*, not rounding.
CITATION_TOLERANCE = 0.01

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Citation:
    """One place in ``docs/`` that states a number for a contested claim."""

    doc: str
    #: heading prefix that opens the section, e.g. ``"## D-030"``
    anchor: str
    #: the number the prose writes down
    states: float
    #: ``instrument`` -- this IS the claim's own statistic.
    #: ``other-quantity`` -- a related but different number that has been
    #: compared against the claim's readings as though it were the same.
    kind: str
    #: for ``other-quantity``: what it actually measures, in one line
    quantity: str = ""


@dataclass(frozen=True)
class ScopedClaim:
    """A dispatch-fragile claim, its oracle, its readings, and its citations."""

    claim: str
    #: ``module::function`` that defines the quantity -- the single place the
    #: number may be recomputed from.
    instrument: str
    oracle: str
    #: reading on the oracle the constants were calibrated on
    reading_calibrated: float
    #: reading on the arm they fail on
    reading_other: float
    #: the assertion's own lower bound (``None`` for band/categorical claims)
    asserted_lo: float | None
    citations: tuple[Citation, ...] = ()

    @property
    def retained_of_assertion(self) -> float | None:
        """D-035's unit: what the repaired threshold keeps of the asserted effect."""
        if self.asserted_lo is None:
            return None
        asserted = self.asserted_lo - RATIO_NULL
        if not asserted:
            return None
        return (self.reading_other - RATIO_NULL) / asserted

    @property
    def retained_of_reading(self) -> float:
        """What the other machine keeps of the *measured* effect over the null.

        Strictly smaller than :attr:`retained_of_assertion` whenever the
        calibrated reading cleared its own threshold -- which is the usual case,
        since a test that barely passed would have been noticed.
        """
        measured = self.reading_calibrated - RATIO_NULL
        if not measured:
            return 0.0
        return (self.reading_other - RATIO_NULL) / measured

    def retained_of_citation(self, cited: float) -> float:
        """What survives of the number a *document* actually propagates.

        This is the figure that belongs in a retraction notice: readers met the
        cited number, not the assertion and not the reading.
        """
        if cited == RATIO_NULL:
            return 0.0
        return (self.reading_other - RATIO_NULL) / (cited - RATIO_NULL)


#: Registry.  Readings are transcribed from ``results/dispatch-divergence/``
#: (both arms of the same box, numpy pinned at 1.26.4) -- banked measurements,
#: not recomputed here, because recomputing them on a reader's machine is
#: exactly the operation this file documents as unsafe.
SCOPED_CLAIMS: tuple[ScopedClaim, ...] = (
    ScopedClaim(
        claim="horizon_weight_swing",
        instrument="dispatch_divergence::_horizon_weight_swing",
        oracle=ORACLE,
        reading_calibrated=1.3007806733194093,
        reading_other=1.0288801880989747,
        asserted_lo=1.2,
        citations=(
            Citation(
                doc="docs/decisions.md", anchor="## D-030", states=2.0,
                kind="other-quantity",
                quantity="w_voo amplitude over H=15->34 (13.97/7.00), not the "
                         "H=30->34 span the flipping assertion measures",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-032", states=2.0,
                kind="other-quantity",
                quantity="D-030's H=15->34 amplitude, paired against the "
                         "H=30->34 instrument's AVX2 reading",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-033", states=2.0,
                kind="other-quantity",
                quantity="same H=15->34 amplitude, carried forward",
            ),
            Citation(
                doc="docs/deliberations.md", anchor="## Q-054", states=2.0,
                kind="other-quantity",
                quantity="same H=15->34 amplitude, carried forward",
            ),
            Citation(
                doc="docs/deliberations.md", anchor="## Q-055", states=2.0,
                kind="other-quantity",
                quantity="same H=15->34 amplitude, carried forward",
            ),
        ),
    ),
    ScopedClaim(
        claim="ab_protocol_overstatement",
        instrument="dispatch_divergence::_ab_protocol_overstatement",
        oracle=ORACLE,
        reading_calibrated=1.6956279596371452,
        reading_other=1.0545692336178126,
        asserted_lo=1.25,
        citations=(
            Citation(
                doc="docs/decisions.md", anchor="## D-017", states=1.9,
                kind="other-quantity",
                quantity="ratio of the two reported clearance gains "
                         "(+0.0957/+0.0492 = 1.945), rounded; the instrument "
                         "takes the same ratio over paired seed means",
            ),
        ),
    ),
    ScopedClaim(
        claim="scale_match_achieved_ratio",
        instrument="dispatch_divergence::_scale_match_achieved_ratio",
        oracle=ORACLE,
        reading_calibrated=0.2511455153541066,
        reading_other=0.17901224534675504,
        asserted_lo=None,
        citations=(),
    ),
    ScopedClaim(
        claim="exposure_band_hi",
        instrument="dispatch_divergence::_exposure_band_hi",
        oracle=ORACLE,
        reading_calibrated=2.0375,
        reading_other=2.1857142857142864,
        asserted_lo=None,
        citations=(),
    ),
    ScopedClaim(
        claim="hazard_shared_rungs",
        instrument="dispatch_divergence::_hazard_shared_rungs",
        oracle=ORACLE,
        reading_calibrated=1.0,
        reading_other=0.0,
        asserted_lo=None,
        citations=(),
    ),
)


def section(doc: str, anchor: str, root: Path | None = None) -> str:
    """Text of the ``anchor`` section, up to the next same-level heading.

    Raises rather than returning empty: a citation naming a section that no
    longer exists is a stale citation, which is the failure this file is for.
    """
    path = (root or REPO_ROOT) / doc
    text = path.read_text(encoding="utf-8")
    start = text.find(f"\n{anchor}")
    if start < 0:
        if not text.startswith(anchor):
            raise LookupError(f"{doc}: no section starting {anchor!r}")
        start = 0
    else:
        start += 1
    nxt = re.search(r"^## ", text[start + len(anchor):], flags=re.M)
    end = len(text) if nxt is None else start + len(anchor) + nxt.start()
    return text[start:end]


def unstamped(root: Path | None = None) -> list[tuple[str, Citation]]:
    """Cited sections missing the oracle stamp -- the propagation guard."""
    out = []
    for sc in SCOPED_CLAIMS:
        for cit in sc.citations:
            if sc.oracle not in section(cit.doc, cit.anchor, root):
                out.append((sc.claim, cit))
    return out


def _renders(value: float, text: str) -> bool:
    """Whether ``text`` writes ``value`` to at least 3 significant figures.

    Accepts the handful of spellings this repo's prose actually uses, rather
    than parsing every number and comparing -- a citation that rounds to two
    digits has, for these ratios, already lost the distinction being enforced.
    """
    for spelling in (f"{value:.3f}", f"{value:.4f}", f"{value:.5g}", f"{value:.4g}"):
        if spelling in text:
            return True
    return False


def undisambiguated(root: Path | None = None) -> list[tuple[str, Citation]]:
    """``other-quantity`` citations that do not also state the instrument's reading.

    Without this, a section can keep comparing its own number against the
    instrument's AVX2 reading -- the entanglement D-036 found.
    """
    out = []
    for sc in SCOPED_CLAIMS:
        for cit in sc.citations:
            if cit.kind != "other-quantity":
                continue
            if not _renders(sc.reading_calibrated, section(cit.doc, cit.anchor, root)):
                out.append((sc.claim, cit))
    return out


def report() -> str:
    rows = [
        f"{'claim':<28} {'oracle':<12} {'calib':>9} {'other':>9} "
        f"{'keeps(assert)':>14} {'keeps(read)':>12} {'cites':>6}",
    ]
    for sc in SCOPED_CLAIMS:
        ra = sc.retained_of_assertion
        rows.append(
            f"{sc.claim:<28} {sc.oracle:<12} {sc.reading_calibrated:>9.4f} "
            f"{sc.reading_other:>9.4f} {'n/a' if ra is None else f'{ra:.1%}':>14} "
            f"{sc.retained_of_reading:>11.1%} {len(sc.citations):>6}")
    rows.append("")
    for sc in SCOPED_CLAIMS:
        for cit in sc.citations:
            if cit.kind != "other-quantity":
                continue
            rows.append(
                f"  {cit.doc} {cit.anchor}: states {cit.states:g}x for "
                f"{sc.claim}, but that is {cit.quantity}. Instrument reads "
                f"{sc.reading_calibrated:.4f}; of the cited {cit.states:g}x the "
                f"other machine keeps {sc.retained_of_citation(cit.states):.1%}.")
    miss = unstamped()
    rows += ["", f"unstamped cited sections: {len(miss)}"
                 + ("" if not miss else " -> " + ", ".join(
                     f"{d.anchor}@{d.doc}" for _, d in miss))]
    return "\n".join(rows)


if __name__ == "__main__":
    print(report())
