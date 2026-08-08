"""Does a rung's separation survive an **independent seed block**?

`scorable_band.one_run_rungs` names the rungs whose entire separation is a
single run, and says the report has to disclose them. Disclosure is where it
stopped: a one-run rung stayed `SEPARATED`, stayed `scorable`, and kept voting
on the band's structure, because nothing in the repo could ask the only
question that settles it — *does it happen again on seeds nobody has looked
at?* Calibration cannot answer it (D-148/D-149/D-150 bought every rung of the
published span a λ table and the rung did not move), Fisher cannot answer it
(p = 1.0 says the block is consistent with noise, not that a second block
disagrees), and a bigger single block only dilutes it. Only a **disjoint**
block does, and this module is the grade over the pair.

**Measured 2026-08-09 on the rung that motivated it** — `cafe_head_on_v0`,
λ = 0.8, `w_obs_soft = 250`, margin 0.40 m, `risk_mppi` against `stock_mppi`,
32/32 reached::

    block           stock       risk        verdict
    seeds 0–15      0/16        1/16        SEPARATED   (D-133's, reproduced)
    seeds 16–31     1/16        0/16        SEPARATED   (sign reversed)
    pooled 0–31     1/32        1/32        TIED

The reference block reproduces D-133 **exactly**, down to the 0.3472 m run its
docstring quotes, so the walk is faithful and the disagreement is not a
pipeline difference. And on the fresh block the separation comes back the same
size and the **other way round**: the arm that was one run worse is now one run
better. Pooled over 32 seeds the rung is `TIED`.

That is :data:`SIGN_REVERSED`, and the two things it settles are opposite in
direction. It **retires an objection to the mechanism** — D-133 recorded this
rung's separation as pointing *against* `risk_mppi`, and half of that sign was
seeds. It also **retires the rung as evidence for anything**: `TIED` is a real
null, not a delta, so the one weight where the headline could be read as the
mechanism doing harm is now the one weight where it demonstrably does neither.

The rung stays `scorable` — `TIED` is in `comparison_headroom.SCORABLE` — so
`published_band()`'s `BAND_SPLIT` still holds; what changes is what the split
is *made of*. `scorable_band`'s own docstring called it "real but bought by one
seed". At 32 seeds it is not bought by a seed at all.

:data:`PUBLISHED_LADDER` is deliberately **not** amended. It is the record of
D-133's block, it remains a true statement about those 16 seeds, and rewriting
a measurement in place because a later one disagreed is how a table stops being
evidence. The replication is a second record, graded against the first.

**Second rung, 2026-08-09** — the same protocol at `w_obs_soft = 150`, the rung
that sets the *upper edge* of the band's contiguous island `{75, 100, 150}`.
Nine runs of separation rather than one, and 32/32 reached::

    block           stock       risk        verdict
    seeds 0–15      10/16       1/16        SEPARATED   (D-133's, reproduced)
    seeds 16–31      5/16       0/16        SEPARATED   (same direction)
    pooled 0–31     15/32       1/32        SEPARATED

:data:`REPRODUCED`, and the **first** one — the protocol had until now only ever
returned a reversal, so this is the reading that says it can come back either
way rather than being a machine for overturning things. The direction is the
mechanism's: `risk_mppi` is the safer arm on both blocks and on the pool.

What it does **not** confirm is the size. The stock arm's sub-margin rate halves
between the blocks (10/16 → 5/16) while the risk arm's goes 1/16 → 0/16, so the
*sign* survives replication and the *magnitude* is seed-dependent by a factor of
two. A rung can be solid and still not licence its own effect size, which is why
:class:`ReplicationCensus` reports `held` / `overturned` and not a delta.

Typical use::

    rep = Reproduction(reference=block_a, replication=block_b)
    print(rep.verdict)   # SIGN_REVERSED
    print(rep.pooled.verdict)  # TIED — the honest single number at n = 32
    print(published_census())  # PARTIALLY_REPLICATED :: 2/4 rungs
"""

from __future__ import annotations

from dataclasses import dataclass

from .comparison_headroom import (
    SEPARATED,
    ArmSafety,
    Headroom,
)

#: Both blocks separate the arms, in the **same** direction. The only verdict
#: under which a one-run rung's separation may be read as a property of the
#: mechanism rather than of the seed block. It does not make the delta large —
#: `separation_runs` still says how many runs bought it.
REPRODUCED = "REPRODUCED"

#: Both blocks separate, in **opposite** directions. Strictly more informative
#: than :data:`NOT_REPRODUCED`: the replication did not merely fail to find the
#: effect, it found the mirror of it, so the sign carried by the reference is
#: attributable to the seeds and the pooled verdict is the one to publish.
SIGN_REVERSED = "SIGN_REVERSED"

#: The reference separated and the replication did not. The separation is not a
#: property of the operating point at this seed count.
NOT_REPRODUCED = "NOT_REPRODUCED"

#: The **reference** block does not separate, so there is no separation to
#: replicate and every other field would read exactly as under a successful
#: reproduction. Named rather than returned as `REPRODUCED`-because-both-agree:
#: this is the empty denominator the repo keeps meeting one layer out
#: (D-107 / D-120 / D-127 / D-145 / D-150), and the shape of the fix is the
#: same one `lam_window_key.SeedContrast.verdict` uses — the verdict says
#: whether the question was asked, the fields say what it answered.
NO_SEPARATION_TO_REPRODUCE = "NO_SEPARATION_TO_REPRODUCE"


class OverlappingBlocks(ValueError):
    """Two blocks share a seed, so they are not independent replication.

    The whole value of a replication is that its runs are ones the reference
    never saw; a pair that overlaps grades a rung against a superset of itself
    and cannot come back anything but agreeing. Refused by name at construction
    rather than caveated, for the same reason `Headroom` refuses two arms
    graded against different margins.
    """


@dataclass(frozen=True)
class SeedBlock:
    """One rung measured over a named, disjoint set of seeds.

    `Headroom` carries the scene, weight, λ and both arms but not *which* seeds
    produced the clearances — which is exactly the field this question turns
    on, so it is carried here beside it rather than added there. Keeping it out
    of `Headroom` also keeps `published_band()`'s rate-only reconstruction
    legal: those rungs have no seeds to name.
    """

    seeds: tuple[int, ...]
    headroom: Headroom

    def __post_init__(self) -> None:
        n = len(self.headroom.a.clearances)
        if len(self.seeds) != n:
            raise ValueError(
                f"{len(self.seeds)} seeds against {n} clearances — a block "
                "whose seed list does not match its runs cannot say which "
                "runs a replication must avoid"
            )
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError(f"seeds repeat within one block: {self.seeds}")

    @property
    def verdict(self) -> str:
        return self.headroom.verdict

    @property
    def delta_unsafe(self) -> float:
        """`b − a` on the headline, signed — see `Headroom.delta_unsafe`."""
        return self.headroom.delta_unsafe

    def __str__(self) -> str:
        lo, hi = min(self.seeds), max(self.seeds)
        return (f"seeds {lo}–{hi} (n={len(self.seeds)}) :: "
                f"{self.verdict} delta={self.delta_unsafe:+.4f}")


@dataclass(frozen=True)
class Reproduction:
    """A rung's reference block graded against a disjoint replication of it."""

    reference: SeedBlock
    replication: SeedBlock

    def __post_init__(self) -> None:
        shared = set(self.reference.seeds) & set(self.replication.seeds)
        if shared:
            raise OverlappingBlocks(
                f"blocks share seeds {sorted(shared)} — a replication that "
                "re-runs the reference's own seeds is not independent"
            )
        for field in ("scenario", "weight", "lam", "margin"):
            a = getattr(self.reference.headroom, field)
            b = getattr(self.replication.headroom, field)
            if a != b:
                raise ValueError(
                    f"blocks disagree on {field} ({a!r} vs {b!r}) — they are "
                    "not two measurements of the same rung"
                )

    @property
    def verdict(self) -> str:
        if self.reference.verdict != SEPARATED:
            return NO_SEPARATION_TO_REPRODUCE
        if self.replication.verdict != SEPARATED:
            return NOT_REPRODUCED
        same_sign = (self.reference.delta_unsafe > 0) == \
                    (self.replication.delta_unsafe > 0)
        return REPRODUCED if same_sign else SIGN_REVERSED

    @property
    def pooled(self) -> Headroom:
        """Both blocks as one `Headroom` at the summed seed count.

        The number to publish once a rung has been replicated: it is the whole
        ensemble, and unlike either block alone it is not selected by having
        been looked at first.
        """
        ref, rep = self.reference.headroom, self.replication.headroom
        return Headroom(
            scenario=ref.scenario, weight=ref.weight, lam=ref.lam,
            a=ArmSafety(arm=ref.a.arm,
                        clearances=ref.a.clearances + rep.a.clearances,
                        margin=ref.margin),
            b=ArmSafety(arm=ref.b.arm,
                        clearances=ref.b.clearances + rep.b.clearances,
                        margin=ref.margin),
        )

    @property
    def seeds(self) -> tuple[int, ...]:
        return tuple(sorted(self.reference.seeds + self.replication.seeds))

    def __str__(self) -> str:
        return (f"{self.reference.headroom.scenario} "
                f"w={self.reference.headroom.weight:g} :: {self.verdict} "
                f"[{self.reference.verdict} → {self.replication.verdict}] "
                f"pooled(n={len(self.seeds)}) {self.pooled.verdict}")


#: The walk this module was written for, verbatim: minimum clearance in metres
#: per seed on `cafe_head_on_v0` at λ = 0.8, `w_obs_soft = 250`, seeds 0–31 in
#: order, both arms, all 32 runs reaching the goal. Magnitudes and not rates —
#: `published_band()` stores counts because it is rebuilt from a published
#: table, whereas this is the measurement itself, so `mean_clearance` and
#: `sub_margin` are answerable here.
#:
#: Seeds 0–15 are D-133's block: `risk_mppi` seed 6 is the 0.3472 m run that
#: `scorable_band`'s docstring quotes, reproduced to four decimals.
W250_CLEARANCES: dict[str, tuple[float, ...]] = {
    "stock_mppi": (
        0.5665, 0.5522, 0.5617, 0.5409, 0.5574, 0.5583, 0.5306, 0.4386,
        0.4983, 0.5901, 0.4831, 0.4830, 0.5879, 0.6334, 0.6651, 0.5277,
        0.5938, 0.5467, 0.3811, 0.5806, 0.5641, 0.5882, 0.5550, 0.5648,
        0.5555, 0.5472, 0.5229, 0.4060, 0.5659, 0.5265, 0.5609, 0.5799,
    ),
    "risk_mppi": (
        0.6334, 0.4419, 0.6281, 0.6060, 0.6219, 0.6034, 0.3472, 0.6187,
        0.6052, 0.5985, 0.6400, 0.5963, 0.6698, 0.6796, 0.6362, 0.5847,
        0.5545, 0.6763, 0.6693, 0.6621, 0.6239, 0.6594, 0.7481, 0.6627,
        0.6783, 0.6343, 0.5648, 0.6614, 0.5824, 0.6468, 0.5735, 0.5449,
    ),
}

#: Where the reference block ends and the replication begins. D-133 walked
#: 0–15; this cycle added 16–31 and re-walked 0–15 to check the pipeline first.
W250_REFERENCE_SEEDS = 16


#: The `w = 150` rung, walked 2026-08-09 under the same protocol: minimum
#: clearance in metres per seed on `cafe_head_on_v0` at λ = 0.8, seeds 0–31 in
#: order, both arms, all 32 runs reaching the goal.
#:
#: Seeds 0–15 are D-133's block and reproduce its row exactly — stock 10/16
#: sub-margin, risk 1/16. Seeds 16–31 are fresh: stock **5/16**, risk **0/16**,
#: the same direction. This is the rung `w = 250` was not.
W150_CLEARANCES: dict[str, tuple[float, ...]] = {
    "stock_mppi": (
        0.4747, 0.4959, 0.3993, 0.4251, 0.2808, 0.3692, 0.4539, 0.3740,
        0.3789, 0.3165, 0.4601, 0.3653, 0.3560, 0.4177, 0.3668, 0.3841,
        0.3721, 0.4029, 0.3786, 0.3852, 0.4198, 0.4103, 0.3935, 0.4299,
        0.4208, 0.4153, 0.4326, 0.4194, 0.3262, 0.4437, 0.4382, 0.4224,
    ),
    "risk_mppi": (
        0.5446, 0.5008, 0.5431, 0.2237, 0.5623, 0.5338, 0.5548, 0.5028,
        0.4484, 0.6196, 0.5020, 0.4829, 0.5357, 0.5713, 0.5037, 0.5164,
        0.5412, 0.4821, 0.5582, 0.4178, 0.5507, 0.5050, 0.5488, 0.5601,
        0.5654, 0.5226, 0.5194, 0.4987, 0.5026, 0.4656, 0.4856, 0.5418,
    ),
}

#: Where each recorded walk's reference block ends and its replication begins.
#: D-133 published 16 seeds per rung, so both walks re-walk 0–15 before adding
#: 16–31 — the entitlement check of D-139, paid on the seed axis.
W250_REFERENCE_SEEDS = 16
W150_REFERENCE_SEEDS = 16


def _reproduction(weight: float, clearances: dict[str, tuple[float, ...]],
                  cut: int) -> Reproduction:
    """A recorded 32-seed walk split into its reference and replication blocks.

    Built from the stored clearances rather than by re-simulating, so a test of
    the grade costs no runs; the runs are the constant.
    """
    from .scorable_band import (
        PUBLISHED_ARMS,
        PUBLISHED_LAM,
        PUBLISHED_MARGIN,
        PUBLISHED_SCENARIO,
    )

    stock, risk = PUBLISHED_ARMS

    def block(lo: int, hi: int) -> SeedBlock:
        return SeedBlock(
            seeds=tuple(range(lo, hi)),
            headroom=Headroom(
                scenario=PUBLISHED_SCENARIO, weight=weight, lam=PUBLISHED_LAM,
                a=ArmSafety(arm=stock, clearances=clearances[stock][lo:hi],
                            margin=PUBLISHED_MARGIN),
                b=ArmSafety(arm=risk, clearances=clearances[risk][lo:hi],
                            margin=PUBLISHED_MARGIN),
            ),
        )

    n = len(clearances[stock])
    return Reproduction(reference=block(0, cut), replication=block(cut, n))


def w250_reproduction() -> Reproduction:
    """The measured replication of the published band's one-run rung."""
    return _reproduction(250.0, W250_CLEARANCES, W250_REFERENCE_SEEDS)


def w150_reproduction() -> Reproduction:
    """The measured replication of the band's upper-edge rung."""
    return _reproduction(150.0, W150_CLEARANCES, W150_REFERENCE_SEEDS)
# --- which of the band's separated rungs have actually been replicated? ------

#: The band publishes no `SEPARATED` rung, so there is nothing replication
#: could speak about and every other field would read as under full coverage.
#: Sixth instance of the empty denominator
#: (D-107 / D-120 / D-127 / D-145 / D-150 / D-151).
NO_SEPARATED_RUNG = "NO_SEPARATED_RUNG"

#: Separated rungs exist and **none** has a disjoint second block.
UNREPLICATED = "UNREPLICATED"

#: Some separated rungs are replicated, some are not. The honest state of the
#: published band while the replication programme is mid-flight.
PARTIALLY_REPLICATED = "PARTIALLY_REPLICATED"

#: Every separated rung has been walked on a disjoint block.
FULLY_REPLICATED = "FULLY_REPLICATED"


@dataclass(frozen=True)
class ReplicationCensus:
    """Coverage of a band's `SEPARATED` rungs by disjoint-block replication.

    `Reproduction` grades **one** rung. The question a reader of the published
    band actually has is the population one — *of the rungs whose separation
    the band's shape rests on, how many has anybody looked at twice?* — and
    before this it was answerable only by reading the journal. Two rungs have
    now been replicated and both changed their reading, which makes the
    unreplicated remainder a live risk rather than a formality.

    Coverage is reported, never thresholded: like `one_run_rungs`, the census
    says what is unwitnessed and leaves the reader to price it.
    """

    separated: tuple[float, ...]
    reproductions: tuple[tuple[float, Reproduction], ...]

    def __post_init__(self) -> None:
        weights = [w for w, _ in self.reproductions]
        if len(set(weights)) != len(weights):
            raise ValueError(f"a weight is replicated twice: {weights}")
        stray = sorted(set(weights) - set(self.separated))
        if stray:
            raise ValueError(
                f"replications at {stray} grade rungs the band does not "
                "report as SEPARATED — a census over a rung the band never "
                "separated counts coverage the band cannot use"
            )

    @property
    def replicated(self) -> tuple[float, ...]:
        return tuple(sorted(w for w, _ in self.reproductions))

    @property
    def unreplicated(self) -> tuple[float, ...]:
        return tuple(sorted(set(self.separated) - set(self.replicated)))

    @property
    def held(self) -> tuple[float, ...]:
        """Replicated rungs whose separation survived the second block."""
        return tuple(sorted(w for w, r in self.reproductions
                            if r.verdict == REPRODUCED))

    @property
    def overturned(self) -> tuple[float, ...]:
        """Replicated rungs the second block did **not** confirm.

        `SIGN_REVERSED` and `NOT_REPRODUCED` are both here: they differ in how
        much they say, but neither leaves the rung's separation standing.
        """
        return tuple(sorted(w for w, r in self.reproductions
                            if r.verdict in (SIGN_REVERSED, NOT_REPRODUCED)))

    @property
    def verdict(self) -> str:
        if not self.separated:
            return NO_SEPARATED_RUNG
        if not self.replicated:
            return UNREPLICATED
        if self.unreplicated:
            return PARTIALLY_REPLICATED
        return FULLY_REPLICATED

    def __str__(self) -> str:
        return (f"{self.verdict} :: {len(self.replicated)}/"
                f"{len(self.separated)} separated rungs replicated, "
                f"held {self.held or '()'} overturned {self.overturned or '()'}")


def published_census() -> ReplicationCensus:
    """The published band's separated rungs against the replications on record."""
    from .scorable_band import published_band

    band = published_band()
    separated = tuple(r.weight for r in band.rungs
                      if r.scorable and r.headroom.verdict == SEPARATED)
    return ReplicationCensus(
        separated=separated,
        reproductions=((150.0, w150_reproduction()),
                       (250.0, w250_reproduction())),
    )
