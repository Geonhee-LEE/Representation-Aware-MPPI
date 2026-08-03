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
    #: which arm's reading the prose states -- ``calibrated`` or ``other``.
    #: Added by D-046: the derived scan found sections citing the *AVX2*
    #: reading (``D-035``'s repaired thresholds, ``D-045``'s ``1.029x``), and
    #: checking those against the calibrated number would reject a correct
    #: citation for stating the number it means to state.
    arm: str = "calibrated"

    def reading_of(self, sc: "ScopedClaim") -> float:
        return sc.reading_other if self.arm == "other" else sc.reading_calibrated


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
            Citation(
                doc="docs/decisions.md", anchor="## D-034", states=1.30078,
                kind="instrument", arm="calibrated",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- the excursion table, which tabulates every "
                         "contested reading at once and carried no oracle stamp",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-046", states=1.30078,
                kind="instrument", arm="calibrated",
                quantity="D-046: this decision's own section, registered by the invariant it adds",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-035", states=1.0289,
                kind="instrument", arm="other",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- the repaired threshold IS the AVX2 reading",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-036", states=1.3008,
                kind="instrument", arm="calibrated", quantity="D-046: found by derived_citations(), not by re-reading the list",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-037", states=1.3008,
                kind="instrument", arm="calibrated", quantity="D-046: found by derived_citations(), not by re-reading the list",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-038", states=1.301,
                kind="instrument", arm="calibrated",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- quoted while explaining the 11.301 substring bug",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-045", states=1.029,
                kind="instrument", arm="other",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- the numpy-pin rationale's AVX2 reading",
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
            Citation(
                doc="docs/decisions.md", anchor="## D-034", states=1.69563,
                kind="instrument", arm="calibrated", quantity="D-046: found by derived_citations(), not by re-reading the list",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-046", states=1.69563,
                kind="instrument", arm="calibrated",
                quantity="D-046: this decision's own section, registered by the invariant it adds",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-035", states=1.0546,
                kind="instrument", arm="other",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- the repaired threshold IS the AVX2 reading",
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
        citations=(
            Citation(
                doc="docs/decisions.md", anchor="## D-033", states=0.17901180719252627,
                kind="instrument", arm="other",
                quantity="D-046: found by derived_citations(), not by re-reading the list -- the mask-arm reproduction, quoted to 17 digits; "
                         "differs from the banked AVX2 reading in the 7th, which is "
                         "inside SIGNIFICANT_TOLERANCE and outside CITATION_TOLERANCE",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-034", states=0.251146,
                kind="instrument", arm="calibrated", quantity="D-046: found by derived_citations(), not by re-reading the list",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-046", states=0.251146,
                kind="instrument", arm="calibrated",
                quantity="D-046: this decision's own section, registered by the invariant it adds",
            ),
        ),
    ),
    ScopedClaim(
        claim="exposure_band_hi",
        instrument="dispatch_divergence::_exposure_band_hi",
        oracle=ORACLE,
        reading_calibrated=2.0375,
        reading_other=2.1857142857142864,
        asserted_lo=None,
        citations=(
            Citation(
                doc="docs/decisions.md", anchor="## D-034", states=2.0375,
                kind="instrument", arm="calibrated", quantity="D-046: found by derived_citations(), not by re-reading the list",
            ),
            Citation(
                doc="docs/decisions.md", anchor="## D-046", states=2.0375,
                kind="instrument", arm="calibrated",
                quantity="D-046: this decision's own section, registered by the invariant it adds",
            ),
        ),
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


#: A decimal number, with a left boundary so ``1.301`` is not found inside
#: ``11.301``.  Not hypothetical here: ``D-038``'s own section quotes exactly
#: that pair while *explaining* the identical bug in :mod:`citation_audit`'s
#: bare-magnitude pattern.
_NUMBER = re.compile(r"(?<![\d.])(\d+\.\d+)")

#: Relative distance within which a written number *is* a reading.  5e-4 is the
#: worst-case error of rounding to three significant figures, so this accepts
#: every rendering at or above the precision the citation guard cares about --
#: including ones *more* precise than the registry's own spellings.
SIGNIFICANT_TOLERANCE = 5e-4


def _states(value: float, text: str) -> str | None:
    """The spelling *text* uses for *value*, or ``None``.

    Compares numerically rather than by substring.  A substring test has to
    pick a rendering, and then fails in **both** directions: it finds a shorter
    reading inside a longer unrelated number, and -- the direction that bit the
    first draft of this function -- it *misses* a section that states the
    reading to more digits than the spelling chosen.  ``D-034``'s excursion
    table writes ``0.251146`` where the registry banks ``0.2511``, so a
    right-boundary rule hid the one section that tabulates every contested
    reading at once.  Missing a citation is the failure this module exists to
    prevent, so the matcher must not have that direction.
    """
    if not value:
        return None
    for m in _NUMBER.finditer(text):
        try:
            written = float(m.group(1))
        except ValueError:  # pragma: no cover - regex guarantees parseability
            continue
        if abs(written - value) <= SIGNIFICANT_TOLERANCE * abs(value):
            return m.group(1)
    return None


def _renders(value: float, text: str) -> bool:
    """Whether ``text`` writes ``value`` to at least 3 significant figures."""
    return _states(value, text) is not None


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


# ---------------------------------------------------------------------------
# Registry completeness (D-046, STATE #1)
#
# Everything above trusts :data:`SCOPED_CLAIMS` to name every place a reading is
# stated.  That tuple is hand-typed, and two consecutive cycles found a
# hand-typed list short the moment it was enumerated as code: D-044 (D-011's
# local-only set was 3 of 5) and D-045 (the exclusion list was 2 of 3).  The fix
# in both cases had the same shape -- derive the set from the tree, diff against
# the list -- so the same shape is applied here to the list those two cycles did
# not reach.
# ---------------------------------------------------------------------------

#: The docs a citation can live in.  Same two files :mod:`citation_audit`
#: scans; imported there rather than re-typed would be circular, so the
#: agreement is asserted by test instead.
CITED_DOCS: tuple[str, ...] = ("docs/decisions.md", "docs/deliberations.md")

#: Readings no prose scan can look for, with the reason.  ``hazard_shared_rungs``
#: reads 1.0 on the oracle and 0.0 on the other arm: both render as bare ``1``
#: and ``0``, which occur in essentially every section, so a scan for them
#: reports everything and therefore nothing.  Declared rather than skipped --
#: D-042's rule is that an instrument which can only *clear* work must not be
#: trusted to clear it, and a silently unscanned claim reads exactly like a
#: claim with no unregistered citations.
DEGENERATE_READINGS: tuple[float, ...] = (0.0, RATIO_NULL)

#: Derived matches confirmed to be a *different quantity* that happens to round
#: to the same spelling, with the reason.  A declared rejection is auditable and
#: an undeclared one is indistinguishable from an oversight (D-038); the
#: difference from the list this section exists to fix is that the *population*
#: is derived and only the rejections are typed.
COINCIDENTAL: tuple[tuple[str, str, str, str], ...] = (
    (
        "exposure_band_hi", "docs/decisions.md", "## D-023",
        "2.038 here is TIMING_RATIO_BAND's upper edge (0.557, 2.038) -- a "
        "traversal-time ratio, not the exposure band; collides only at 4 s.f.",
    ),
    (
        "exposure_band_hi", "docs/decisions.md", "## D-024",
        "same TIMING_RATIO_BAND edge, quoted from D-023",
    ),
    (
        "exposure_band_hi", "docs/decisions.md", "## D-025",
        "same TIMING_RATIO_BAND edge, quoted from D-023",
    ),
)


@dataclass(frozen=True)
class DerivedCitation:
    """A ``docs/`` section found to state one of a claim's banked readings."""

    claim: str
    doc: str
    anchor: str
    #: ``calibrated`` or ``other`` -- which arm's reading the section spells
    reading: str
    spelling: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.claim, self.doc, self.anchor)


def instrumented_claims() -> tuple[str, ...]:
    """Claim names :mod:`dispatch_divergence` *defines*, read off the module.

    :data:`dispatch_divergence.CLAIMS` is itself a hand-written dict, so
    checking :data:`SCOPED_CLAIMS` against it only pushes the same failure one
    file left: a ``_foo() -> Claim`` nobody added to ``CLAIMS`` is invisible to
    both.  This walks the module's own members instead, which is the last
    surface before the code itself.
    """
    import inspect

    from . import dispatch_divergence as dd

    out = []
    for name, obj in vars(dd).items():
        if not name.startswith("_") or not inspect.isfunction(obj):
            continue
        if obj.__module__ != dd.__name__:
            continue
        try:
            ret = inspect.signature(obj).return_annotation
        except (TypeError, ValueError):  # pragma: no cover - builtins
            continue
        if ret in ("Claim", dd.Claim):
            out.append(name.lstrip("_"))
    return tuple(sorted(out))


def _sections(doc: str, root: Path | None = None) -> list[tuple[str, str]]:
    """``(anchor, body)`` per ``##`` section of *doc*, anchor = the ``## X`` prefix."""
    text = ((root or REPO_ROOT) / doc).read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r"^## ", text, flags=re.M)]
    out = []
    for a, b in zip(starts, starts[1:] + [len(text)]):
        body = text[a:b]
        head = body.split("\n", 1)[0]
        # Anchor is the heading up to its first separator, e.g. "## D-030".
        anchor = re.match(r"##\s+\S+", head)
        if anchor:
            out.append((anchor.group(0), body))
    return out


def derived_citations(root: Path | None = None) -> list[DerivedCitation]:
    """Every ``docs/`` section that spells a banked reading, found by scanning.

    This is the population :data:`SCOPED_CLAIMS`'s ``citations`` tuples are
    supposed to enumerate.  Degenerate readings are excluded by declaration
    (:data:`DEGENERATE_READINGS`), not by silence -- see
    :func:`unscannable_readings`.
    """
    out: list[DerivedCitation] = []
    for doc in CITED_DOCS:
        for anchor, body in _sections(doc, root):
            for sc in SCOPED_CLAIMS:
                for which, value in (("calibrated", sc.reading_calibrated),
                                     ("other", sc.reading_other)):
                    if value in DEGENERATE_READINGS:
                        continue
                    hit = _states(value, body)
                    if hit is not None:
                        out.append(DerivedCitation(sc.claim, doc, anchor, which, hit))
    return out


def unscannable_readings() -> tuple[tuple[str, str, float], ...]:
    """``(claim, which, value)`` for readings :func:`derived_citations` cannot see.

    Reported so that "no unregistered citations" is never read as a statement
    about these.
    """
    out = []
    for sc in SCOPED_CLAIMS:
        for which, value in (("calibrated", sc.reading_calibrated),
                             ("other", sc.reading_other)):
            if value in DEGENERATE_READINGS:
                out.append((sc.claim, which, value))
    return tuple(out)


def unregistered_citations(root: Path | None = None) -> list[DerivedCitation]:
    """Derived sites that are in neither ``citations`` nor :data:`COINCIDENTAL`.

    Non-empty means a section states a dispatch-fragile reading while sitting
    outside every guard built on the registry -- no oracle stamp is required of
    it, and no disambiguation.  A reader meets the number without meeting the
    machine.
    """
    registered = {(sc.claim, cit.doc, cit.anchor)
                  for sc in SCOPED_CLAIMS for cit in sc.citations}
    declared = {(c, d, a) for c, d, a, _ in COINCIDENTAL}
    seen: set[tuple[str, str, str]] = set()
    out = []
    for dc in derived_citations(root):
        if dc.key in registered or dc.key in declared or dc.key in seen:
            continue
        seen.add(dc.key)
        out.append(dc)
    return out


def stale_coincidences(root: Path | None = None) -> tuple[tuple[str, str, str], ...]:
    """Declared coincidences the scan no longer finds.

    The mirror of :func:`unregistered_citations`, and the reason a declaration
    list is safe to keep: a rejection for a match that has since been edited
    away would silently re-admit the section if the number came back meaning
    something else.
    """
    found = {dc.key for dc in derived_citations(root)}
    return tuple(sorted(k for k in ((c, d, a) for c, d, a, _ in COINCIDENTAL)
                        if k not in found))


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
