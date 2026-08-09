"""Is the published band's censoring a property of the *margin*, or of the arms?

`ReplicationCensus.arm_verdict` came back `NONE_TWO_SIDED` (D-157): all four
separated rungs of the published band have been replicated, and **not one** of
those replications was a test of both arms — in every rung at least one arm sat
at a floor or a ceiling and so had nowhere to move. STATE read that as a defect
of the *threshold*: `stock_mppi`'s best run at `w ∈ {75, 100}` is under the
0.40 m margin, so its rate is pinned at 1.0 and the separation is carried by the
risk arm alone. The natural next question, and the one this module answers, is
**whether some other margin would have made those rungs two-sided** — which is
pure computation, because the 32 per-seed clearances for all four rungs are
already constants in `separation_reproduction`.

The answer is *not* the one the framing expected, in both directions:

- **Two of the four rungs have no two-sided margin at all** — not at any
  threshold, not just not at 0.40. At `w = 75` and `w = 100` the two arms'
  clearance distributions are so nearly disjoint (range overlap **7.6 mm** and
  **9.9 mm**) that no threshold can sit interior to both arms in both blocks.
  Censoring there is not a badly-chosen margin; it is what the band's *largest*
  effects look like. A two-sided test requires the arms to overlap, and these
  do not — so `NONE_TWO_SIDED` at those rungs is not repairable by re-grading.
- **Two of them do**, and they are the band's two *weaker* rungs — the opposite
  of the usual worry that a threshold is flattering a result. `w = 150` is
  two-sided over `[0.4194, 0.4437]` (9 breakpoints) and its `REPRODUCED`
  verdict holds at every one of them.
- **And `w = 250`'s reversal does not survive being read two-sided.** That rung
  is the band's `SIGN_REVERSED` one (D-151): at the published margin its two
  blocks separate in *opposite* directions. But at 0.40 m the rung is censored
  precisely because almost nothing crosses — the sign is carried by **one run
  per block** (stock 0/16 then 1/16, risk 1/16 then 0/16). Re-graded at any of
  its 23 two-sided margins, `[0.5467, 0.5938]`, the same 32 runs come back
  `REPRODUCED` — *every one of the 23*, in the mechanism's direction. The
  reversal is a property of reading a 16-run block in a tail, not of the runs.

  This is a qualification of D-151 and not a retraction of it: 0.5467 m is not
  the scene's margin, so the re-graded reading is a statement about the
  ordering of two clearance distributions, **not** a safety claim. (An earlier
  draft of this paragraph justified that with "at that threshold most runs of
  *both* arms count as unsafe", which `derived_margin` measured and found
  false — at the window's lower end `stock_mppi` is 11/32 and `risk_mppi`
  **3/32**. Two-sidedness requires the arms *interior*, not mostly unsafe. The
  caveat rests on the threshold being undeclared.) What it removes is the
  reading that the seeds pointed *against* the mechanism at `w = 250`; what it
  cannot do is put the rung back into the published band.

And the two windows are **disjoint**, which is the band-level consequence:
`Headroom` refuses to grade two arms against different margins by construction,
so a band is scored at one margin, and **no single margin makes more than one
of the four rungs two-sided** (:class:`BandSweep`). Arm coverage over the
published band is not merely 0/4 as measured — its **ceiling is 1/4**, and
buying that one costs re-grading the whole band at a margin nobody declared.

Nothing here re-publishes anything. The published margin is the scene's
(`PUBLISHED_MARGIN = 0.40`); a sweep says what *would* have been seen at other
thresholds, which is a fact about the recorded clearances and not a licence to
pick the flattering one. Reported, never thresholded — the `one_run_rungs`
discipline (D-133) again.

Exhaustiveness is the load-bearing claim, since two of the four answers are
"none". An arm's unsafe count at margin `m` is `#{c : c < m}` (`near_miss`
grades the boundary closed on the safe side), so as a function of `m` it is a
step function constant on each interval `(c_i, c_{i+1}]` between consecutive
recorded clearances. Every attainable rate-vector therefore has a **recorded
clearance** as its representative, and enumerating the distinct clearances of
both arms over both blocks visits all of them — bar the two trivial tails,
`m <= min(c)` (every arm at a floor) and `m > max(c)` (every arm at a ceiling),
which are pinned by inspection. `test_margin_sweep` pins this against a dense
grid rather than trusting the argument.
"""

from dataclasses import dataclass

from .comparison_headroom import ArmSafety, Headroom
from .separation_reproduction import (
    NO_SEPARATION_TO_REPRODUCE,
    UNCENSORED,
    Reproduction,
    SeedBlock,
    w75_reproduction,
    w100_reproduction,
    w150_reproduction,
    w250_reproduction,
)

#: No margin makes this rung a two-sided test of both arms. The arms' clearance
#: distributions do not overlap enough for a threshold to sit interior to both
#: of them in both blocks, so the rung's censoring is a property of the *effect*
#: and not of the threshold — re-grading cannot fix it, and only a rung whose
#: arms overlap more (i.e. a *weaker* separation) could.
NO_TWO_SIDED_MARGIN = "NO_TWO_SIDED_MARGIN"

#: Some margin makes the rung two-sided, and the rung's recorded verdict holds
#: at **every** such margin. The separation is not an artifact of the published
#: threshold: it survives being read where both arms had room to move.
TWO_SIDED_AND_HELD = "TWO_SIDED_AND_HELD"

#: Some margin makes the rung two-sided, and the recorded verdict does **not**
#: hold at all of them. Strictly the interesting case — it says the rung's
#: verdict and its two-sidedness cannot be had at once — and it is why
#: :attr:`MarginSweep.verdict` grades survival separately from existence
#: instead of returning a single "a window exists" boolean.
TWO_SIDED_BUT_LOST = "TWO_SIDED_BUT_LOST"

#: The rung's reference block does not separate, so it has no verdict for a
#: re-grading to preserve and `held`/`lost` would both read `()` exactly as they
#: do when no margin is two-sided at all. Eighth instance of the empty
#: denominator (D-107 / D-120 / D-127 / D-145 / D-150 / D-151 / D-157).
#:
#: Keyed on :data:`NO_SEPARATION_TO_REPRODUCE` and **not** on "the verdict is
#: not `REPRODUCED`": `SIGN_REVERSED` is a recorded separation — both blocks
#: separated, in opposite directions — and it is precisely the verdict most
#: worth asking a margin question about, since a sign carried by one or two runs
#: at a censored threshold is the case where re-grading can overturn it.
NO_RECORDED_SEPARATION = "NO_RECORDED_SEPARATION"


def regrade(reproduction: Reproduction, margin: float) -> Reproduction:
    """The same two seed blocks, the same runs, graded at a different margin.

    Rebuilt rather than mutated because `Headroom` is frozen and validates the
    margin at construction — a sweep that reached past that check could grade a
    rung at a threshold `near_miss` refuses to score.
    """
    def block(source: SeedBlock) -> SeedBlock:
        h = source.headroom
        return SeedBlock(
            seeds=source.seeds,
            headroom=Headroom(
                scenario=h.scenario, weight=h.weight, lam=h.lam,
                a=ArmSafety(arm=h.a.arm, clearances=h.a.clearances,
                            margin=margin),
                b=ArmSafety(arm=h.b.arm, clearances=h.b.clearances,
                            margin=margin),
            ),
        )

    return Reproduction(reference=block(reproduction.reference),
                        replication=block(reproduction.replication))


def breakpoints(reproduction: Reproduction) -> tuple[float, ...]:
    """Every margin at which some arm's rate can differ, ascending.

    The distinct clearances of both arms over both blocks. See the module
    docstring for why this is exhaustive over the non-trivial margins; the two
    tails it omits (`m <= min`, `m > max`) pin every arm by construction and so
    can only be censored.
    """
    seen: set[float] = set()
    for block in (reproduction.reference, reproduction.replication):
        for arm in (block.headroom.a, block.headroom.b):
            seen.update(arm.clearances)
    return tuple(sorted(seen))


@dataclass(frozen=True)
class MarginSweep:
    """One replicated rung re-graded at every margin its own runs can express."""

    reproduction: Reproduction

    @property
    def weight(self) -> float:
        return self.reproduction.reference.headroom.weight

    @property
    def recorded_verdict(self) -> str:
        """The rung's verdict at the margin it was published against."""
        return self.reproduction.verdict

    @property
    def two_sided(self) -> tuple[float, ...]:
        """Margins at which **both** arms had room to move in **both** blocks.

        `Reproduction.censoring` unions the two blocks' pinned arms (D-157), so
        `UNCENSORED` here is the rung-level reading and not a per-block one: a
        margin that frees an arm in the reference but pins it in the replication
        does not make the rung a two-sided test.
        """
        return tuple(m for m in breakpoints(self.reproduction)
                     if regrade(self.reproduction, m).censoring == UNCENSORED)

    @property
    def held(self) -> tuple[float, ...]:
        """Two-sided margins at which the recorded verdict still stands."""
        recorded = self.recorded_verdict
        return tuple(m for m in self.two_sided
                     if regrade(self.reproduction, m).verdict == recorded)

    @property
    def lost(self) -> tuple[float, ...]:
        """Two-sided margins at which the recorded verdict does **not** stand."""
        held = set(self.held)
        return tuple(m for m in self.two_sided if m not in held)

    @property
    def window(self) -> tuple[float, float] | None:
        """The span of two-sided margins, or `None` if there are none.

        A complete description and not merely the extremes: every breakpoint
        between them is two-sided too. An arm's unsafe rate is **monotone
        non-decreasing** in the margin, so the margins at which it is interior
        (rate strictly between 0 and 1) form one contiguous run; two-sidedness
        is the intersection of four such runs — two arms × two blocks — and an
        intersection of intervals is an interval. Pinned in `test_margin_sweep`
        rather than left as an argument, since :attr:`window` is the summary
        every caller will read instead of :attr:`two_sided`.
        """
        ms = self.two_sided
        return (ms[0], ms[-1]) if ms else None

    @property
    def verdict(self) -> str:
        if self.recorded_verdict == NO_SEPARATION_TO_REPRODUCE:
            return NO_RECORDED_SEPARATION
        if not self.two_sided:
            return NO_TWO_SIDED_MARGIN
        return TWO_SIDED_AND_HELD if not self.lost else TWO_SIDED_BUT_LOST

    @property
    def regraded_verdicts(self) -> tuple[str, ...]:
        """The rung's verdict at each two-sided margin, in ascending order.

        What :attr:`lost` deliberately does not say. `lost` counts margins where
        the recorded verdict fails; it does not say what replaced it, and the
        replacement is the finding at `w = 250` — every one of its 23 two-sided
        margins reads `REPRODUCED`, so the rung does not merely stop being
        `SIGN_REVERSED`, it lands in the mechanism's direction and stays there.
        """
        return tuple(regrade(self.reproduction, m).verdict
                     for m in self.two_sided)

    @property
    def arm_overlap(self) -> float:
        """Width of the two arms' pooled clearance-range overlap, in metres.

        Why :data:`NO_TWO_SIDED_MARGIN` happens, in one number: a threshold can
        only be interior to both arms inside this span, so a rung whose arms
        barely overlap has almost nowhere to be two-sided. It is **necessary and
        not sufficient** — the span is pooled over the 32 runs while
        two-sidedness is required in each block of 16, so a positive overlap can
        still admit no two-sided margin (`w = 75` and `w = 100` both do).
        """
        h = self.reproduction.pooled
        lo = max(min(h.a.clearances), min(h.b.clearances))
        hi = min(max(h.a.clearances), max(h.b.clearances))
        return hi - lo

    def __str__(self) -> str:
        w = self.window
        span = f"[{w[0]:.4f}, {w[1]:.4f}]" if w else "—"
        return (f"w={self.weight:g} :: {self.verdict} "
                f"two_sided={len(self.two_sided)} {span} "
                f"overlap={self.arm_overlap:+.4f}m")


#: No margin makes even one rung of the band two-sided.
NO_TWO_SIDED_RUNG = "NO_TWO_SIDED_RUNG"

#: Some margin makes exactly one rung two-sided, and no margin makes two. The
#: band's arm coverage is capped at 1/4 by the data, whatever threshold is
#: chosen — distinct from "we measured 0/4", which is a fact about the margin
#: that *was* used.
SINGLE_RUNG_CEILING = "SINGLE_RUNG_CEILING"

#: Some margin makes two or more rungs two-sided at once, so a single re-grading
#: of the whole band could raise arm coverage above 1/4. Not the state of the
#: published band; named because :data:`SINGLE_RUNG_CEILING` reads identically
#: to it in `best_margins` (which reports witnesses either way) and the
#: distinction is the entire point of the band-level reading.
MULTI_RUNG_REACHABLE = "MULTI_RUNG_REACHABLE"


@dataclass(frozen=True)
class BandSweep:
    """The band's rungs swept together — how many can be two-sided *at once*?

    Separate from :class:`MarginSweep` because the per-rung answer does not
    compose: `Headroom` refuses two arms graded against different margins, so a
    band is scored at **one** threshold, and a band whose rungs each have a
    two-sided window may still have no margin at which two of them are two-sided
    together. That is exactly the published band's state.
    """

    sweeps: tuple[MarginSweep, ...]

    def __post_init__(self) -> None:
        weights = [s.weight for s in self.sweeps]
        if len(set(weights)) != len(weights):
            raise ValueError(
                f"repeated weights {sorted(weights)} — a band sweep over two "
                "readings of one rung would double-count its coverage"
            )

    @property
    def candidates(self) -> tuple[float, ...]:
        """Every margin two-sided for at least one rung, ascending."""
        return tuple(sorted({m for s in self.sweeps for m in s.two_sided}))

    def coverage(self, margin: float) -> tuple[float, ...]:
        """Weights of the rungs that are two-sided at this one margin."""
        return tuple(s.weight for s in self.sweeps
                     if regrade(s.reproduction, margin).censoring == UNCENSORED)

    @property
    def ceiling(self) -> int:
        """The most rungs any single margin can make two-sided."""
        return max((len(self.coverage(m)) for m in self.candidates), default=0)

    @property
    def best_margins(self) -> tuple[float, ...]:
        """Margins attaining :attr:`ceiling`. Empty iff the ceiling is 0."""
        top = self.ceiling
        if top == 0:
            return ()
        return tuple(m for m in self.candidates if len(self.coverage(m)) == top)

    @property
    def verdict(self) -> str:
        top = self.ceiling
        if top == 0:
            return NO_TWO_SIDED_RUNG
        return SINGLE_RUNG_CEILING if top == 1 else MULTI_RUNG_REACHABLE

    def __str__(self) -> str:
        return (f"{len(self.sweeps)} rungs :: {self.verdict} "
                f"ceiling={self.ceiling}/{len(self.sweeps)} "
                f"over {len(self.candidates)} candidate margins")


def published_sweep() -> BandSweep:
    """The four replicated rungs of the published band, swept.

    `SINGLE_RUNG_CEILING`: `w = 75` and `w = 100` are `NO_TWO_SIDED_MARGIN`,
    `w = 150` and `w = 250` are `TWO_SIDED_AND_HELD` over disjoint windows.
    """
    return BandSweep(sweeps=tuple(
        MarginSweep(reproduction=r) for r in (
            w75_reproduction(), w100_reproduction(),
            w150_reproduction(), w250_reproduction(),
        )
    ))
