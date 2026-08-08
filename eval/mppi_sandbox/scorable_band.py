# SPDX-License-Identifier: BSD-3-Clause
"""How wide is the region of the weight axis where an A/B can separate its arms?

D-131 measured `risk_mppi` against `stock_mppi` on `cafe_head_on_v0` and found
exactly one rung where the headline could move: `w_obs_soft = 100`, unsafe rate
**1.0000 → 0.2500**. Every other rung on that ladder was degenerate —
`NO_HEADROOM_UNSAFE` at 30 (both arms fail everywhere) and `NO_HEADROOM_SAFE`
at 300 and above (the barrier weight alone solves the scene). So the project's
first scored mechanism claim rested on a **single point**, and nothing in the
report could say whether the scorable region was one rung wide or five: the
ladder's rungs were 30 / 100 / 300, and three points cannot describe an
interval whose interior was never visited.

This module is the shape of that answer. It takes the per-rung
`comparison_headroom.Headroom` verdicts a ladder walk produces and reports the
**set** of scorable rungs, whether that set is contiguous, whether it runs off
either end of what was tested, and — the part a bare width would hide — the
untested brackets its edges actually live in.

Four things it deliberately refuses to do, each because the project has already
paid for the mistake one axis over.

**It does not report a width in weight units.** `width_rungs` counts rungs and
says so in its name. A band of three rungs on {100, 150, 200} and a band of
three on {100, 1000, 10000} are not the same claim, and a scalar "width" makes
them print identically. The weight extent is `span`, and `span` is annotated by
`edge_below` / `edge_above` — the two untested intervals the true edges lie in,
because a ladder locates an edge only to its own resolution. A band measured on
a coarse ladder knows its edges coarsely; the report should not round that away.

**It does not assume the scorable set is an interval.** D-127 measured the
*admissible* set on this same axis and found **two islands** — `{10, 3000}`
with five failing rungs between them — after `relief_interval`'s preamble had
declined to assume contiguity on stated grounds and had only a synthetic
witness for it. Monotonicity is not known here either: headroom dies at the
bottom for one reason (both arms fail) and at the top for the opposite one
(both arms pass), and nothing forbids a hole in between. A non-contiguous
scorable set grades `BAND_SPLIT` and keeps its rungs; it is not silently
bridged into a span.

**It does not count a rung the sampler was not compliant on.** D-131's side
finding is that λ calibration is *not* weight-invariant: `lam_windows.yaml` was
measured at the shipped `w_obs_soft = 10`, and at `w = 30` both arms leave the
ESS band at the same λ = 0.8 that is in-band at 10, 100 and 300. A rung where
the softmax has gone greedy produces a verdict about the sampler wearing the
mechanism's name, so such rungs are **refused by name** (`ESS_OUT_OF_BAND`)
rather than graded. A rung whose ESS was never measured is refused too
(`ESS_UNMEASURED`) — `ess_in_band` has no default for exactly that reason.
Grading an unmeasured rung as compliant is the empty-denominator failure
D-107 / D-120 / D-127 have each booked once.

**And a refused rung does not close an edge.** If the rung below the band was
refused, the band's lower edge is unwitnessed — we know nothing about that rung,
which is not the same as knowing it is unscorable. Openness is therefore
computed over the *graded* rungs only, and refused rungs falling strictly
inside the span are surfaced as `interior_refused` rather than being quietly
spanned over.

Openness itself delegates to `relief_interval.open_above` / `open_below` rather
than restating `max(chosen) >= max(tested)` inline — the same rule has now been
re-derived by hand in `resolve` (D-127), `admits` (D-128) and `knife_edge`
(D-129), and the third of those sat three lines below the extraction that was
meant to prevent it (D-047).

**Measured 2026-08-08 on `cafe_head_on_v0`, λ = 0.8, margin 0.40 m, 16 seeds
per arm (D-131's 8 doubled), `risk_mppi` against `stock_mppi`.** All 16/16
reached at every rung::

    w      stock    risk     verdict              Fisher (2-sided)
    30     1.0000   1.0000   —  refused: stock ESS out of band
    55     1.0000   1.0000   NO_HEADROOM_UNSAFE
    75     1.0000   0.6875   SEPARATED            0.043
    100    1.0000   0.3750   SEPARATED            0.00025
    150    0.6250   0.0625   SEPARATED            0.0021
    200    0.0000   0.0000   NO_HEADROOM_SAFE
    250    0.0000   0.0625   SEPARATED            1.0     (one run, sign flipped)
    300    0.0000   0.0000   NO_HEADROOM_SAFE

**The band is three rungs wide, not one.** D-131's single scorable point was an
artefact of a ladder whose neighbours were 30 and 300; densifying finds
`{75, 100, 150}` contiguous, each significant on its own, with the lower edge
bracketed in (55, 75] and the transition ending at 200 where relief begins. The
`w = 100` rung also survives the doubling — 1.0000 → 0.3750 at n = 16, Fisher
**p = 2.5e-4** — so the project's first scored mechanism claim is now its first
significant one.

**And the split is real but bought by one seed.** `w = 250` is `SEPARATED`
solely because one of sixteen risk seeds came 0.3472 m against a 0.40 m margin
while stock had none — p = 1.0, direction *against* the mechanism. It is what
makes the verdict `BAND_SPLIT` rather than `BAND_CLOSED`, so it is named by
`one_run_rungs` rather than left to be read as a second island.

Typical use::

    rungs = [BandRung(headroom_at(w), ess_in_band=ess[w]) for w in ladder]
    band = ScorableBand(tuple(rungs))
    print(band)   # verdict, rung set, span, and both edge brackets
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .comparison_headroom import (
    NO_HEADROOM_SAFE,
    NO_HEADROOM_UNSAFE,
    SEPARATED,
    UNCERTIFIED,
    ArmSafety,
    Certification,
    Headroom,
    certify,
)
from .lam_window_index import NO_CELL, NO_TABLE_AT_WEIGHT, TableIndex
from .relief_interval import open_above, open_below

#: No rung on the ladder could separate the arms. The A/B has no operating
#: point on this axis at this resolution — which is a finding about the ladder
#: as much as about the mechanism, hence `tested` is always printed with it.
NO_SCORABLE_RUNG = "NO_SCORABLE_RUNG"

#: A contiguous run of scorable rungs with a graded, unscorable rung on **both**
#: sides. The only verdict under which `span` is bracketed from both ends.
BAND_CLOSED = "BAND_CLOSED"

#: The band runs down to the lowest graded rung: its lower edge is unmeasured.
BAND_OPEN_BELOW = "BAND_OPEN_BELOW"

#: The band runs up to the highest graded rung: its upper edge is unmeasured.
BAND_OPEN_ABOVE = "BAND_OPEN_ABOVE"

#: Every graded rung is scorable. The ladder is entirely inside the band and
#: says nothing about where it ends — a lower bound of `width_rungs`, no more.
BAND_OPEN_BOTH = "BAND_OPEN_BOTH"

#: Scorable rungs with a graded, unscorable rung between them: the scorable set
#: is not an interval (the D-127 two-islands shape, one axis over).
BAND_SPLIT = "BAND_SPLIT"

#: Verdicts under which the measured `span` is bounded by witnesses at both
#: ends. Everything else carries a `span` that is a lower bound.
BOUNDED = (BAND_CLOSED, BAND_SPLIT)

#: The rung ran, but at a temperature the sampler was not compliant at — the
#: verdict would be about the softmax, not the mechanism (D-131).
ESS_OUT_OF_BAND = "ess_out_of_band"

#: The rung ran and nobody recorded its ESS. Not graded: an unmeasured
#: compliance check is not a passed one.
ESS_UNMEASURED = "ess_unmeasured"


@dataclass(frozen=True)
class BandRung:
    """One rung of a ladder walk: a headroom verdict plus its ESS compliance.

    `ess_in_band` has no default. A caller that has not measured it must say
    `None`, which refuses the rung — the alternative is an omitted keyword
    reading as compliance.

    `ess_arms` is optional and names *which* arm was out of band. It is empty
    for a caller that only has the conjunction, and the conjunction is all the
    grading needs — a rung is admissible only if both arms are compliant, and
    `refusal` is unchanged either way. What the attribution buys is the reading
    of a refusal, and D-133 is the cycle where the two readings diverged:
    `cafe_obstacle_crossing_v0` has **disjoint** calibrated `lam` windows
    (stock `[0.4, 0.8]`, risk `[1.6, 3.2]` — recorded in the scene file's own
    notes since the 5-actor block landed), so a refused rung there is the
    expected consequence of running two arms at one temperature, and knowing it
    was the *baseline* that left the band is a different fact about the
    experiment than the mechanism arm leaving it. `cafe_head_on_v0`'s refusal at
    `w = 30` (D-132) was already one-sided in exactly this way and the report
    could only say so in prose.
    """

    headroom: Headroom
    ess_in_band: bool | None
    ess_arms: tuple[tuple[str, bool | None], ...] = ()

    def __post_init__(self) -> None:
        if not self.ess_arms:
            return
        names = tuple(n for n, _ in self.ess_arms)
        expected = (self.headroom.a.arm, self.headroom.b.arm)
        if sorted(names) != sorted(expected):
            raise ValueError(
                f"ess_arms names {names} but the rung's arms are {expected} — "
                "an attribution to an arm that did not run is not evidence"
            )
        flags = [f for _, f in self.ess_arms]
        conj = None if any(f is None for f in flags) else all(flags)
        if conj != self.ess_in_band:
            raise ValueError(
                f"ess_in_band={self.ess_in_band} but the per-arm flags conjoin "
                f"to {conj} — that is a disagreement to resolve, not a rung to "
                "grade (cf. the duplicate-rung check one level up)"
            )

    @property
    def out_of_band_arms(self) -> tuple[str, ...]:
        """Arms measured outside the ESS band at this rung. Empty when the
        attribution was not supplied — which is not the same as nobody being
        out of band, so read it beside `refusal`."""
        return tuple(n for n, f in self.ess_arms if f is False)

    @property
    def weight(self) -> float:
        return self.headroom.weight

    @property
    def refusal(self) -> str | None:
        """Why this rung is not graded, or `None` if it is."""
        if self.ess_in_band is None:
            return ESS_UNMEASURED
        if not self.ess_in_band:
            return ESS_OUT_OF_BAND
        return None

    @property
    def graded(self) -> bool:
        return self.refusal is None

    @property
    def scorable(self) -> bool:
        """Graded **and** able to separate the arms. Never true for a refused
        rung: `Headroom.scorable` is a statement about the margin, and this one
        is a statement about the experiment being admissible at all."""
        return self.graded and self.headroom.scorable

    @property
    def separation_runs(self) -> int | None:
        """How many runs of difference the arms' unsafe counts amount to.

        `SEPARATED` asks only that the two rates differ, so **one** run out of
        sixteen buys the verdict — and D-132 measured exactly that at `w = 250`
        (stock 0/16, risk 1/16, Fisher p = 1.0, sign *against* the mechanism),
        which is what made the band print `BAND_SPLIT`. That is the shape
        `relief_interval.SUBRESOLUTION` already books one axis over: a
        difference the survey cannot resolve should not be allowed to look
        structural. Reported rather than thresholded — `comparison_headroom`
        deliberately does not rank arms, and a cutoff here would be this
        module deciding what counts as a real delta.

        `None` when the arms ran different seed counts, since the quantity is
        then not a count of runs.
        """
        a, b = self.headroom.a, self.headroom.b
        if len(a.clearances) != len(b.clearances):
            return None
        return round(abs(self.headroom.delta_unsafe) * len(a.clearances))

    def __str__(self) -> str:
        tail = self.refusal or self.headroom.verdict
        return f"w={self.weight:g} :: {tail}"


@dataclass(frozen=True)
class ScorableBand:
    """The scorable region of one scene's weight ladder, at one temperature."""

    rungs: tuple[BandRung, ...]

    def __post_init__(self) -> None:
        if not self.rungs:
            raise ValueError("a band over zero rungs is not a measurement")
        scenes = {r.headroom.scenario for r in self.rungs}
        if len(scenes) != 1:
            raise ValueError(
                f"band walks {sorted(scenes)} — a band is one scene's weight "
                "axis, and pooling scenes would grade the scenery"
            )
        lams = {r.headroom.lam for r in self.rungs}
        if len(lams) != 1:
            raise ValueError(
                f"band walks lam={sorted(lams)} — the weight axis is only a "
                "band at a fixed temperature (D-131: lam windows are not "
                "weight-invariant, so a mixed walk confounds the two axes)"
            )
        weights = [r.weight for r in self.rungs]
        if len(set(weights)) != len(weights):
            raise ValueError(
                f"duplicate rung in {weights} — two verdicts for one weight is "
                "a disagreement to resolve, not a band to summarise"
            )
        object.__setattr__(
            self, "rungs", tuple(sorted(self.rungs, key=lambda r: r.weight))
        )

    @property
    def scenario(self) -> str:
        return self.rungs[0].headroom.scenario

    @property
    def lam(self) -> float:
        return self.rungs[0].headroom.lam

    @property
    def tested(self) -> tuple[float, ...]:
        """Every rung the walk visited, refused ones included. Carried because
        a band without its ladder cannot be told from a band whose ladder
        stopped (D-130's `ReliefInterval.tested`, same argument)."""
        return tuple(r.weight for r in self.rungs)

    @property
    def graded(self) -> tuple[float, ...]:
        """The rungs whose verdict is interpretable — the edge witnesses."""
        return tuple(r.weight for r in self.rungs if r.graded)

    @property
    def scorable(self) -> tuple[float, ...]:
        return tuple(r.weight for r in self.rungs if r.scorable)

    @property
    def refused(self) -> tuple[tuple[float, str], ...]:
        """`(weight, reason)` for every ungraded rung, by name."""
        return tuple(
            (r.weight, r.refusal) for r in self.rungs if r.refusal is not None
        )

    @property
    def refused_by_arm(self) -> tuple[tuple[str, tuple[float, ...]], ...]:
        """`(arm, weights)` for every arm that took a rung out of the ESS band.

        Only rungs whose caller supplied `ess_arms` can appear here, so an
        empty result means either nobody was out of band or nobody said who.
        """
        seen: dict[str, list[float]] = {}
        for r in self.rungs:
            for name in r.out_of_band_arms:
                seen.setdefault(name, []).append(r.weight)
        return tuple((n, tuple(ws)) for n, ws in sorted(seen.items()))

    @property
    def sole_refuser(self) -> str | None:
        """The one arm responsible for every attributed ESS refusal, if there
        is one.

        A band that grades `NO_SCORABLE_RUNG` because the *mechanism* arm never
        held its temperature is a different claim from one where the *baseline*
        never did: the first bounds the mechanism, the second bounds only this
        temperature's suitability as a shared operating point. Without this the
        two print identically, and `cafe_obstacle_crossing_v0` — whose two arms
        are calibrated to disjoint `lam` windows — is a scene where the second
        reading is the likely one and the first would be the wrong headline.

        `None` when no refusal was attributed, or when both arms refused
        somewhere: a two-sided refusal has no single owner to name.
        """
        by_arm = self.refused_by_arm
        return by_arm[0][0] if len(by_arm) == 1 else None

    @property
    def width_rungs(self) -> int:
        """Count of scorable rungs. Rungs, not weight — see the module note."""
        return len(self.scorable)

    @property
    def single_rung(self) -> bool:
        """The D-131 state: the whole positive result is one measurement."""
        return self.width_rungs == 1

    @property
    def span(self) -> tuple[float, float] | None:
        """`(lowest, highest)` scorable rung, or `None`. A lower bound on the
        band's extent unless `verdict in BOUNDED`, and known only to the
        resolution of `edge_below` / `edge_above` even then."""
        if not self.scorable:
            return None
        return (min(self.scorable), max(self.scorable))

    @property
    def open_below(self) -> bool:
        return open_below(self.scorable, self.graded)

    @property
    def open_above(self) -> bool:
        return open_above(self.scorable, self.graded)

    @property
    def contiguous(self) -> bool:
        """Are the scorable rungs consecutive among the *graded* ones? A refused
        rung inside the span does not break this (it is no evidence either way)
        — it surfaces as `interior_refused` instead."""
        if not self.scorable:
            return True
        graded = self.graded
        idx = [graded.index(w) for w in self.scorable]
        return idx == list(range(min(idx), min(idx) + len(idx)))

    @property
    def interior_refused(self) -> tuple[float, ...]:
        """Refused rungs strictly inside the span — holes the band spans over
        without evidence. Non-empty means `contiguous` is a claim about the
        graded subsequence, not about the weight interval."""
        sp = self.span
        if sp is None:
            return ()
        lo, hi = sp
        return tuple(w for w, _ in self.refused if lo < w < hi)

    @property
    def one_run_rungs(self) -> tuple[float, ...]:
        """Scorable rungs whose entire separation is a single run.

        A rung here is `SEPARATED` by the letter of the definition and by
        nothing else. If one is what makes a band `BAND_SPLIT` or open at an
        end, that structural claim rests on one seed and the report has to say
        so — the same reason `relief_interval` gave `SUBRESOLUTION` its own
        verdict rather than letting an unresolvable difference vote.
        """
        return tuple(
            r.weight for r in self.rungs if r.scorable and r.separation_runs == 1
        )

    @property
    def edge_below(self) -> tuple[float, float] | None:
        """The untested interval `(last graded unscorable, lowest scorable)`
        the band's lower edge lies in, or `None` when it is unwitnessed."""
        sp = self.span
        if sp is None or self.open_below:
            return None
        below = [w for w in self.graded if w < sp[0] and w not in self.scorable]
        return (max(below), sp[0])

    @property
    def edge_above(self) -> tuple[float, float] | None:
        """The untested interval `(highest scorable, first graded unscorable)`
        the band's upper edge lies in, or `None` when it is unwitnessed."""
        sp = self.span
        if sp is None or self.open_above:
            return None
        above = [w for w in self.graded if w > sp[1] and w not in self.scorable]
        return (sp[1], min(above))

    @property
    def verdict(self) -> str:
        if not self.scorable:
            return NO_SCORABLE_RUNG
        if not self.contiguous:
            return BAND_SPLIT
        if self.open_below and self.open_above:
            return BAND_OPEN_BOTH
        if self.open_above:
            return BAND_OPEN_ABOVE
        if self.open_below:
            return BAND_OPEN_BELOW
        return BAND_CLOSED

    def __str__(self) -> str:
        sp = self.span
        span = "—" if sp is None else f"[{sp[0]:g}, {sp[1]:g}]"
        line = (
            f"{self.scenario} lam={self.lam:g} :: {self.verdict} "
            f"{self.width_rungs} rung(s) of {len(self.graded)} graded "
            f"(tested {len(self.tested)}), span {span}"
        )
        if self.edge_below is not None:
            line += f", lower edge in ({self.edge_below[0]:g}, {self.edge_below[1]:g}]"
        if self.edge_above is not None:
            line += f", upper edge in [{self.edge_above[0]:g}, {self.edge_above[1]:g})"
        if self.refused:
            line += "  refused: " + ", ".join(
                f"{w:g}={why}" for w, why in self.refused
            )
        if self.interior_refused:
            line += "  interior holes: " + ", ".join(
                f"{w:g}" for w in self.interior_refused
            )
        if self.one_run_rungs:
            line += "  one-run separations: " + ", ".join(
                f"{w:g}" for w in self.one_run_rungs
            )
        return line


def render(bands: Sequence[ScorableBand]) -> str:
    """One line per band, in the order given."""
    return "\n".join(str(b) for b in bands)


# --------------------------------------------------------------------------
# Span certification — the λ guard applied to the rungs that carry the claim.
#
# D-144 gave `Headroom` an enforcing consumer (`comparison_headroom.certify`),
# and D-145/D-146 cleared both of the calibration refusals standing against the
# project's published rows. What was left open is that nothing *forces* the
# guard: a band walks the weight axis at a fixed λ and takes that λ as a free
# argument, so a `span` can still be published over rungs nobody ever certified.
#
# The trap here is the one D-144 fell into and Q-120 named: only three weights
# carry a calibration table, so a certification that demanded one per rung would
# refuse essentially every band — and a guard that refuses everything reads as
# maximal strictness while checking nothing. The split below is therefore on
# **whether a measurement exists that disagrees**, not on whether a measurement
# exists:
#
#   * `NO_TABLE_AT_WEIGHT` / `NO_CELL` — nothing was measured here. The band is
#     unmeasured at that rung, not wrong. Reported, never raised.
#   * `OFF_WINDOW` / `EMPTY_WINDOW` — a table speaks at that weight and says λ
#     is not admissible. That is a defect in the published span, and it raises.
#
# This is D-044's axis one level up: name the gap ("measure w=250, or re-run at
# a rung in the window") rather than declaring the number untrustworthy.
# --------------------------------------------------------------------------

#: Refusals that mean *nobody measured this operating point*. Not a defect in
#: the band — a gap in the calibration coverage, which the certification names
#: so it cannot be read as a pass.
SPAN_UNMEASURED = frozenset({NO_TABLE_AT_WEIGHT, NO_CELL})

#: Refusals that mean *a measurement exists and it disagrees*. Derived from
#: `comparison_headroom.UNCERTIFIED` rather than listed, so a refusal added
#: upstream lands here loudly instead of being silently absent from both sets
#: (D-047: the partition should have exactly one statement of itself).
SPAN_REFUSING = frozenset(UNCERTIFIED) - SPAN_UNMEASURED

#: Every scorable rung is at an operating point both arms were calibrated at.
SPAN_CERTIFIED = "SPAN_CERTIFIED"

#: At least one scorable rung is refused by a calibration that exists at its
#: weight. The span is published at a temperature the scene does not admit.
SPAN_UNCERTIFIED = "SPAN_UNCERTIFIED"

#: No scorable rung is refused by an existing table, but at least one was never
#: measured. The span is not contradicted — it is unwitnessed on the λ axis.
SPAN_UNCALIBRATED = "SPAN_UNCALIBRATED"


class UncertifiedSpan(ValueError):
    """A band's scorable rungs include one the calibration refuses."""


@dataclass(frozen=True)
class SpanCertification:
    """Per-rung certification of the rungs that set a band's `span`.

    Scoped to `band.scorable` on purpose. The refused and merely-graded rungs
    bound the band from outside; they do not carry the claim, and demanding a
    calibrated operating point for a rung whose only job is to witness an edge
    would count coverage the headline never rests on.
    """

    band: ScorableBand
    #: `(weight, Certification)` for each scorable rung, ascending.
    certs: tuple[tuple[float, Certification], ...]

    @property
    def certified(self) -> tuple[float, ...]:
        return tuple(w for w, c in self.certs if c.certified)

    @property
    def refused(self) -> tuple[tuple[float, str], ...]:
        """`(weight, verdict)` where a table exists at the weight and refuses."""
        return tuple(
            (w, c.verdict) for w, c in self.certs if c.verdict in SPAN_REFUSING
        )

    @property
    def unmeasured(self) -> tuple[tuple[float, str], ...]:
        """`(weight, verdict)` where no calibration speaks. The coverage gap,
        named so a `SPAN_UNCALIBRATED` band cannot be read as a certified one."""
        return tuple(
            (w, c.verdict) for w, c in self.certs if c.verdict in SPAN_UNMEASURED
        )

    @property
    def sole_uncertified(self) -> str | None:
        """The one arm carrying every refusal, or `None`.

        Same reading as `ScorableBand.sole_refuser` and
        `Certification.sole_uncertified`: an asymmetric refusal points at the
        mechanism, a symmetric one points at the scene.
        """
        arms = {
            c.sole_uncertified
            for _, c in self.certs
            if c.verdict in SPAN_REFUSING and c.sole_uncertified is not None
        }
        return next(iter(arms)) if len(arms) == 1 else None

    @property
    def verdict(self) -> str:
        if self.refused:
            return SPAN_UNCERTIFIED
        if self.unmeasured:
            return SPAN_UNCALIBRATED
        return SPAN_CERTIFIED

    @property
    def ok(self) -> bool:
        """Every scorable rung certified. Strictly stronger than "did not
        raise" — `SPAN_UNCALIBRATED` does not raise and is not `ok`."""
        return self.verdict == SPAN_CERTIFIED

    def __str__(self) -> str:
        line = (
            f"{self.band.scenario} lam={self.band.lam:g} :: {self.verdict} "
            f"{len(self.certified)}/{len(self.certs)} scorable rung(s) certified"
        )
        if self.refused:
            line += "  refused: " + ", ".join(
                f"{w:g}={v}" for w, v in self.refused
            )
        if self.unmeasured:
            line += "  unmeasured: " + ", ".join(
                f"{w:g}={v}" for w, v in self.unmeasured
            )
        sole = self.sole_uncertified
        if sole is not None:
            line += f"  (sole={sole})"
        return line


def certify_span(band: ScorableBand, index: TableIndex | None = None) -> SpanCertification:
    """Certify every rung that contributes to `band.span`.

    Raises on a band with no scorable rung rather than certifying it. A band
    that publishes nothing would pass every check vacuously, and an empty
    denominator reading as a pass is the shape D-107 / D-120 / D-127 each
    booked one axis over — `NO_SCORABLE_RUNG` is already the honest verdict for
    that band and this function has nothing to add to it.
    """
    if not band.scorable:
        raise ValueError(
            f"{band.scenario} grades {NO_SCORABLE_RUNG} — a band with no "
            "scorable rung publishes no operating point, so there is nothing "
            "to certify (certifying it would pass on an empty denominator)"
        )
    return SpanCertification(
        band=band,
        certs=tuple(
            (r.weight, certify(r.headroom, index)) for r in band.rungs if r.scorable
        ),
    )


def assert_span_certified(band: ScorableBand, index: TableIndex | None = None, *,
                          require_calibration: bool = False) -> SpanCertification:
    """Return the certification, or raise if the band's span is refused.

    This is the enforcing entry point the ladder walks were missing: a driver
    that calls it can no longer publish a `span` at a λ the calibration
    contradicts.

    `require_calibration` promotes `SPAN_UNCALIBRATED` to a failure too. It is
    off by default because only three weights carry a table today, so a
    default-on version would refuse nearly every band — the accept-nothing
    vacuity of D-144, which reads as strictness and checks nothing. Turn it on
    at a call site that genuinely walks calibrated weights only; the flag is
    the record of which those are.

    **Bootstrap caveat**: the walk that *builds* a calibration table cannot
    call this — its whole job is to visit rungs no table admits yet.
    `calibrate_lam` is therefore deliberately not a consumer.
    """
    cert = certify_span(band, index)
    if cert.verdict == SPAN_UNCERTIFIED or (require_calibration and not cert.ok):
        raise UncertifiedSpan(str(cert))
    return cert


# --------------------------------------------------------------------------
# The published band, as an object.
#
# Every `ScorableBand` in this repo has been a test fixture. The one band the
# project actually *publishes* — D-133's eight-rung walk on `cafe_head_on_v0`,
# tabulated in this module's own docstring — existed only as prose, so the
# certification `assert_span_certified` performs had nothing real to refuse.
# A guard whose only inputs are fixtures is untested in the way that matters
# (D-143, and D-144 one level down); this is the walk that supplies it.
#
# What is faithful and what is not
# --------------------------------
# The published table records **unsafe rates**, not per-seed clearances, and a
# rate does not determine the clearances that produced it. So the rungs below
# are reconstructed to be exact in the quantities the record actually pins —
# `verdict`, `scorable`, `unsafe_rate`, `delta_unsafe`, `separation_runs`, and
# every band property derived from them — and to have **no magnitudes at all**.
# `mean_clearance` and `sub_margin` raise rather than return, because the
# alternative is a plausible-looking number nobody measured: with the obvious
# below-margin filler, `sub_margin` reads `True` for the whole band, which is a
# D-124 claim this walk never made. The sentinels are `±inf` as a second layer,
# so a magnitude that somehow escapes the refusal is non-physical rather than
# believable.
#
# The reconstruction is falsifiable, which is the point (D-139: only a cell
# whose answer is already recorded can test the thing that generates it). The
# docstring table carries a verdict column, and `test_published_band` grades
# the reconstruction against it rung by rung — a filler that got the counts
# wrong would move a verdict and fail.
# --------------------------------------------------------------------------

PUBLISHED_SCENARIO = "cafe_head_on_v0"
PUBLISHED_LAM = 0.8
PUBLISHED_MARGIN = 0.40
PUBLISHED_SEEDS = 16
PUBLISHED_ARMS = ("stock_mppi", "risk_mppi")

_UNSAFE_FILLER = float("-inf")
_SAFE_FILLER = float("inf")


class UnreconstructedMagnitude(AttributeError):
    """A clearance magnitude was read off a band rebuilt from published rates.

    `AttributeError` and not `ValueError` so that `hasattr`-style probing
    degrades the way a genuinely absent attribute would, rather than
    propagating out of a caller that was only checking.
    """


class _RateOnlyArm(ArmSafety):
    """An arm whose per-seed clearances reproduce a recorded unsafe count and
    encode nothing else. Rates are exact; magnitudes are refused by name."""

    @property
    def mean_clearance(self) -> float:
        raise UnreconstructedMagnitude(
            f"{self.arm} was rebuilt from a published unsafe rate, which does "
            "not determine clearances — there is no mean to report here. Read "
            "unsafe_rate, or go back to the run artifacts for a magnitude."
        )


def _rate_only_arm(arm: str, unsafe: int, n: int = PUBLISHED_SEEDS,
                   margin: float = PUBLISHED_MARGIN) -> _RateOnlyArm:
    if not 0 <= unsafe <= n:
        raise ValueError(f"{arm}: {unsafe} unsafe of {n} is not a count")
    return _RateOnlyArm(
        arm=arm,
        clearances=(_UNSAFE_FILLER,) * unsafe + (_SAFE_FILLER,) * (n - unsafe),
        margin=margin,
    )


#: D-133's walk, verbatim from this module's docstring table: `(weight, stock
#: unsafe count, risk unsafe count, per-arm ESS flags, recorded verdict)`.
#: Counts are the published rates × 16 seeds. The recorded verdict is carried
#: so the reconstruction can be graded against it rather than trusted; it is
#: `None` for the one rung the walk refused.
#:
#: `w = 30` is refused one-sidedly — the *baseline* left the ESS band while the
#: mechanism arm held it (D-132). That asymmetry is why the flags are per-arm
#: here and not a conjunction: it makes `sole_refuser` name `stock_mppi`, which
#: is a statement about this temperature's suitability as a shared operating
#: point rather than a bound on the mechanism.
PUBLISHED_LADDER: tuple[tuple[float, int, int, tuple[tuple[str, bool], ...], str | None], ...] = (
    (30.0,  16, 16, (("stock_mppi", False), ("risk_mppi", True)), None),
    (55.0,  16, 16, (("stock_mppi", True), ("risk_mppi", True)), NO_HEADROOM_UNSAFE),
    (75.0,  16, 11, (("stock_mppi", True), ("risk_mppi", True)), SEPARATED),
    (100.0, 16,  6, (("stock_mppi", True), ("risk_mppi", True)), SEPARATED),
    (150.0, 10,  1, (("stock_mppi", True), ("risk_mppi", True)), SEPARATED),
    (200.0,  0,  0, (("stock_mppi", True), ("risk_mppi", True)), NO_HEADROOM_SAFE),
    (250.0,  0,  1, (("stock_mppi", True), ("risk_mppi", True)), SEPARATED),
    (300.0,  0,  0, (("stock_mppi", True), ("risk_mppi", True)), NO_HEADROOM_SAFE),
)


def published_band() -> ScorableBand:
    """D-133's measured band on `cafe_head_on_v0`, rebuilt from `PUBLISHED_LADDER`.

    The band this repo's headline band-width claim is about. Magnitudes are
    refused (see `_RateOnlyArm`); everything the claim rests on is exact.
    """
    stock, risk = PUBLISHED_ARMS
    rungs = []
    for weight, n_stock, n_risk, ess_arms, _recorded in PUBLISHED_LADDER:
        flags = [f for _, f in ess_arms]
        rungs.append(BandRung(
            headroom=Headroom(
                scenario=PUBLISHED_SCENARIO,
                weight=weight,
                lam=PUBLISHED_LAM,
                a=_rate_only_arm(stock, n_stock),
                b=_rate_only_arm(risk, n_risk),
            ),
            ess_in_band=all(flags),
            ess_arms=ess_arms,
        ))
    return ScorableBand(tuple(rungs))
