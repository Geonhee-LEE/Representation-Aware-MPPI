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

from .comparison_headroom import Headroom
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
