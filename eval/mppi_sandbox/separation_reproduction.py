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

**Third rung, 2026-08-09** — `w_obs_soft = 100`, the *interior* rung of the
band's contiguous island `{75, 100, 150}`, so a reversal here would have split
the island rather than trimmed its edge. It did not: 32/32 reached::

    block           stock       risk        verdict
    seeds 0–15      16/16       6/16        SEPARATED   (D-133's, reproduced)
    seeds 16–31     16/16       2/16        SEPARATED   (same direction)
    pooled 0–31     32/32       8/32        SEPARATED

:data:`REPRODUCED`, the island is intact, and this is the widest separation in
the band — every one of the 32 `stock_mppi` runs breaks the 0.40 m margin while
three quarters of the `risk_mppi` runs hold it.

It is also the rung that shows the sign/size caveat is not merely about
sampling noise. `stock_mppi` here is **at the ceiling in both blocks** — its
best run anywhere in the 32 is 0.3705 m — so its rate did not so much replicate
as have nowhere else to be, and the whole separation is carried by the risk arm,
whose rate moves 6/16 → 2/16 across the blocks. That is what
:attr:`SeedBlock.censoring` names: at `w = 100` and at `w = 250` (stock 0/16, a
:data:`FLOOR`) the reference block is :data:`ONE_ARM_CENSORED`, and `w = 150`
is the only reference block that is a two-sided test of both arms.

**Fourth reading, 2026-08-09** — and that last sentence is why censoring needed
a census of its own rather than a per-block field. Read over reference blocks
the band looks 1/4 two-sided; read over *rungs* — :attr:`Reproduction.censored`,
the union of both blocks — it is **0/4**. `w = 150`'s reference block is free
on both arms, but its replication pins `risk_mppi` at 0/16, so the rung was
never a two-sided test either. `w = 250` is worse than a per-block reading
shows: its two blocks pin *different* arms (stock at a floor in the reference,
risk at a floor in the replication), making the rung
:data:`BOTH_ARMS_CENSORED`::

    rung        reference           replication         rung
    w = 75      stock CEILING       stock CEILING       ONE_ARM_CENSORED
    w = 100     stock CEILING       stock CEILING       ONE_ARM_CENSORED
    w = 150     UNCENSORED          risk FLOOR          ONE_ARM_CENSORED
    w = 250     stock FLOOR         risk FLOOR          BOTH_ARMS_CENSORED

So the band is :data:`FULLY_REPLICATED` and :data:`NONE_TWO_SIDED` at once.
Rung coverage 4/4, arm coverage 0/4: every rung has been walked twice and not
one of them was a test of the pair. The two verdicts are independent by
construction, which is why :class:`ReplicationCensus` carries both.

Typical use::

    rep = Reproduction(reference=block_a, replication=block_b)
    print(rep.verdict)   # SIGN_REVERSED
    print(rep.pooled.verdict)  # TIED — the honest single number at n = 32
    print(rep.reference.censoring)  # ONE_ARM_CENSORED — this block
    print(rep.censoring)  # BOTH_ARMS_CENSORED — the rung, over both blocks
    print(published_census())  # FULLY_REPLICATED … | NONE_TWO_SIDED :: 0/4
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


#: An arm whose reference rate is **0** — every run held the margin. The block
#: could not have shown it safer, so a replication that finds it equal has
#: confirmed nothing about it: the only direction available to a second block
#: is *worse*.
FLOOR = "floor"

#: An arm whose reference rate is **1** — every run broke the margin. The
#: mirror of :data:`FLOOR`: the only direction available is *better*.
CEILING = "ceiling"

#: Neither arm's reference rate sits at a boundary, so the replication is a
#: two-sided test of both arms and the verdict is about the pair.
UNCENSORED = "UNCENSORED"

#: Exactly one arm's reference rate is at a boundary. The rung's separation was
#: produced entirely by the *free* arm — the censored one had no room to make
#: it — and a `REPRODUCED` verdict here is a statement about that free arm.
ONE_ARM_CENSORED = "ONE_ARM_CENSORED"

#: Both arms sit at boundaries. On a `SEPARATED` rung they must sit at opposite
#: ones (same boundary is `NO_HEADROOM_SAFE`/`NO_HEADROOM_UNSAFE`, not a
#: separation), so the delta is ±1 by construction and cannot be reproduced
#: *larger*. Named because it reads in every other field exactly like the
#: strongest result the module can return.
BOTH_ARMS_CENSORED = "BOTH_ARMS_CENSORED"


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

    @property
    def censored(self) -> tuple[tuple[str, str], ...]:
        """Arms whose unsafe rate sits at a boundary, and which boundary.

        A rate of 0 or 1 is not just an extreme value, it is a value with **no
        room on one side**, so the block that recorded it cannot be replicated
        in that direction — not because the mechanism is stable but because the
        statistic has nowhere to go. Reported here rather than folded into the
        verdict, on the `one_run_rungs` discipline: the census says what is
        unwitnessed and leaves the reader to price it.
        """
        out = []
        for arm in (self.headroom.a, self.headroom.b):
            if arm.unsafe_rate == 0.0:
                out.append((arm.arm, FLOOR))
            elif arm.unsafe_rate == 1.0:
                out.append((arm.arm, CEILING))
        return tuple(out)

    @property
    def censoring(self) -> str:
        return (UNCENSORED, ONE_ARM_CENSORED,
                BOTH_ARMS_CENSORED)[len(self.censored)]

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

    @property
    def censored(self) -> tuple[tuple[str, str], ...]:
        """Arms pinned at a boundary in **either** block, and which boundary.

        The union and not the intersection, because the question this answers
        is whether the *rung* was tested on both sides: an arm with no room to
        move in one of the two blocks contributed a fixed number to that block
        whatever the mechanism did, so the comparison there was one-sided even
        if the other block was free.

        The distinction is not academic — it is the whole finding at `w = 150`,
        whose reference block is :data:`UNCENSORED` while its replication pins
        `risk_mppi` at a :data:`FLOOR`. Reading censoring off reference blocks
        alone (which is how the 2026-08-09 12:00 STATE arrived at "1/4
        two-sided") counts that rung as a two-sided test of both arms. It was
        not one.

        An arm may appear twice if the two blocks pin it at *opposite*
        boundaries; :attr:`censoring` therefore counts distinct **arms**, not
        entries.
        """
        seen = dict.fromkeys(self.reference.censored + self.replication.censored)
        return tuple(sorted(seen))

    @property
    def censoring(self) -> str:
        return (UNCENSORED, ONE_ARM_CENSORED,
                BOTH_ARMS_CENSORED)[len({arm for arm, _ in self.censored})]

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
#:
#: The reference block's `stock_mppi` rate is **0/16** — see :data:`FLOOR`.
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
#: D-133 published 16 seeds per rung, so every walk re-walks 0–15 before adding
#: 16–31 — the entitlement check of D-139, paid on the seed axis.
W250_REFERENCE_SEEDS = 16
W150_REFERENCE_SEEDS = 16
W100_REFERENCE_SEEDS = 16
W75_REFERENCE_SEEDS = 16


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


#: The `w = 100` rung, walked 2026-08-09 under the same protocol: minimum
#: clearance in metres per seed on `cafe_head_on_v0` at λ = 0.8, seeds 0–31 in
#: order, both arms, all 32 runs reaching the goal.
#:
#: Seeds 0–15 are D-133's block and reproduce its row exactly — stock **16/16**
#: sub-margin, risk 6/16. Seeds 16–31 are fresh: stock **16/16** again, risk
#: **2/16**. Same direction, so `REPRODUCED`.
#:
#: And the reason this rung needed its own reading: `stock_mppi` is at
#: :data:`CEILING` in *both* blocks — the highest clearance it records anywhere
#: in the 32 runs is 0.3705 m, under the 0.40 m margin. The rate could not have
#: replicated upward, so the rung's separation is carried entirely by the risk
#: arm, whose rate moves 6/16 → 2/16. `ONE_ARM_CENSORED`.
W100_CLEARANCES: dict[str, tuple[float, ...]] = {
    "stock_mppi": (
        0.2624, 0.3417, 0.3234, 0.3705, 0.3125, 0.3116, 0.2697, 0.2360,
        0.2643, 0.2395, 0.3356, 0.3005, 0.2988, 0.2738, 0.2712, 0.3039,
        0.3266, 0.2931, 0.2665, 0.2216, 0.3229, 0.2354, 0.3062, 0.3227,
        0.3258, 0.2616, 0.2449, 0.2793, 0.3048, 0.2618, 0.2918, 0.2994,
    ),
    "risk_mppi": (
        0.4176, 0.4560, 0.4438, 0.4282, 0.4784, 0.3942, 0.4683, 0.3952,
        0.4441, 0.4015, 0.3664, 0.4841, 0.3755, 0.3606, 0.4232, 0.3809,
        0.4845, 0.4199, 0.4069, 0.4554, 0.5194, 0.4381, 0.4286, 0.4422,
        0.3990, 0.4151, 0.4272, 0.3848, 0.5370, 0.5155, 0.4897, 0.4800,
    ),
}


#: The `w = 75` rung, walked 2026-08-09 under the same protocol: minimum
#: clearance in metres per seed on `cafe_head_on_v0` at λ = 0.8, seeds 0–31 in
#: order, both arms, all 32 runs reaching the goal.
#:
#: The last rung nobody had looked at twice, and the island's **lower** edge —
#: so a reversal here would have trimmed `{75, 100, 150}` rather than split it,
#: which is why it was walked after `w = 100`.
#:
#: Seeds 0–15 are D-133's block and reproduce its row exactly — stock 16/16
#: sub-margin, risk **11/16**. Seeds 16–31 are fresh: stock 16/16 again, risk
#: **8/16**. Same direction, so `REPRODUCED`, and the census closes at 4/4.
#:
#: `stock_mppi` is at :data:`CEILING` in both blocks — its best run anywhere in
#: the 32 is 0.3176 m against a 0.40 m margin, the *deepest* ceiling of the
#: three censored rungs. `ONE_ARM_CENSORED`, the same shape as `w = 100`.
W75_CLEARANCES: dict[str, tuple[float, ...]] = {
    "stock_mppi": (
        0.2427, 0.1801, 0.2770, 0.2632, 0.1597, 0.2404, 0.2396, 0.2097,
        0.1677, 0.1845, 0.2409, 0.2471, 0.2080, 0.2392, 0.2291, 0.3031,
        0.3176, 0.2325, 0.2069, 0.2646, 0.2553, 0.2956, 0.2451, 0.2161,
        0.2252, 0.2114, 0.2107, 0.2424, 0.2860, 0.2793, 0.2376, 0.2322,
    ),
    "risk_mppi": (
        0.3590, 0.4294, 0.3160, 0.3952, 0.4374, 0.4341, 0.4045, 0.3648,
        0.3904, 0.3820, 0.3849, 0.3533, 0.4634, 0.3815, 0.3549, 0.3459,
        0.4604, 0.4272, 0.4587, 0.4295, 0.3195, 0.4173, 0.4576, 0.3260,
        0.3429, 0.4710, 0.3505, 0.3896, 0.3430, 0.3916, 0.3100, 0.4060,
    ),
}


def w250_reproduction() -> Reproduction:
    """The measured replication of the published band's one-run rung."""
    return _reproduction(250.0, W250_CLEARANCES, W250_REFERENCE_SEEDS)


def w150_reproduction() -> Reproduction:
    """The measured replication of the band's upper-edge rung."""
    return _reproduction(150.0, W150_CLEARANCES, W150_REFERENCE_SEEDS)


def w100_reproduction() -> Reproduction:
    """The measured replication of the island's interior rung."""
    return _reproduction(100.0, W100_CLEARANCES, W100_REFERENCE_SEEDS)


def w75_reproduction() -> Reproduction:
    """The measured replication of the island's lower edge — the last rung."""
    return _reproduction(75.0, W75_CLEARANCES, W75_REFERENCE_SEEDS)


# --- which of the band's separated rungs have actually been replicated? ------

#: The band publishes no `SEPARATED` rung, so there is nothing replication
#: could speak about and every other field would read as under full coverage.
#: Sixth instance of the empty denominator
#: (D-107 / D-120 / D-127 / D-145 / D-150 / D-151).
NO_SEPARATED_RUNG = "NO_SEPARATED_RUNG"

#: No rung has been replicated, so no rung's arms have been tested twice
#: either. Named for the same reason as :data:`NO_SEPARATED_RUNG`: under it
#: `two_sided` and `one_armed` are both `()`, which is exactly how they read
#: when every replicated rung was a two-sided test of both arms. Seventh
#: instance of the empty denominator — the same six as
#: :data:`NO_SEPARATED_RUNG` (D-107 / D-120 / D-127 / D-145 / D-150 / D-151),
#: plus this one.
NO_REPLICATED_RUNG = "NO_REPLICATED_RUNG"

#: Every replicated rung had both arms free to move in both blocks — the only
#: state under which "the rung replicated" is a claim about the pair.
FULLY_TWO_SIDED = "FULLY_TWO_SIDED"

#: Some replicated rungs were two-sided and some were not.
PARTIALLY_TWO_SIDED = "PARTIALLY_TWO_SIDED"

#: Rungs were replicated and **not one** of them was a two-sided test. The
#: band's state as of 2026-08-09: rung coverage 4/4, arm coverage **0/4**.
#: Distinct from :data:`NO_REPLICATED_RUNG` — there the question was never
#: asked; here it was asked four times and answered one-sided every time.
NONE_TWO_SIDED = "NONE_TWO_SIDED"

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
    before this it was answerable only by reading the journal.

    As of 2026-08-09 the published band's answer is *all four* — but full
    coverage is not full agreement: three rungs held and `w = 250` was
    overturned. `FULLY_REPLICATED` grades the **denominator**, which is why
    `held` and `overturned` stay separate fields rather than folding into the
    verdict. A reader who takes the verdict for a result reads the band as
    stronger than it is.

    Coverage is reported, never thresholded: like `one_run_rungs`, the census
    says what is unwitnessed and leaves the reader to price it.

    Rung coverage is also not **arm** coverage, and that is a second verdict
    (:attr:`arm_verdict`) rather than a caveat on the first. As of 2026-08-09
    the band is `FULLY_REPLICATED` and `NONE_TWO_SIDED` simultaneously: all
    four rungs walked twice, none of them with both arms free to move. A
    reader who takes `4/4` for the whole answer reads four one-sided tests as
    four two-sided ones.
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

    @property
    def two_sided(self) -> tuple[float, ...]:
        """Replicated rungs with both arms free to move in **both** blocks."""
        return tuple(sorted(w for w, r in self.reproductions
                            if r.censoring == UNCENSORED))

    @property
    def one_armed(self) -> tuple[float, ...]:
        """Replicated rungs where at least one arm was pinned somewhere.

        :data:`ONE_ARM_CENSORED` and :data:`BOTH_ARMS_CENSORED` are both here,
        exactly as `overturned` folds two verdicts: they differ in how much
        was pinned, but neither leaves the rung a two-sided test of the pair.
        """
        return tuple(sorted(w for w, r in self.reproductions
                            if r.censoring != UNCENSORED))

    @property
    def arm_verdict(self) -> str:
        """Arm coverage, which :attr:`verdict` does not grade.

        `verdict` counts *rungs looked at twice*; this counts *rungs whose two
        arms were both free to move*. They are independent — the band is
        `FULLY_REPLICATED` and `NONE_TWO_SIDED` at the same time — and the
        second is the one that says how much of each `REPRODUCED` is a claim
        about the mechanism rather than about an arm with nowhere to go.
        """
        if not self.replicated:
            return NO_REPLICATED_RUNG
        if not self.two_sided:
            return NONE_TWO_SIDED
        return FULLY_TWO_SIDED if not self.one_armed else PARTIALLY_TWO_SIDED

    def __str__(self) -> str:
        return (f"{self.verdict} :: {len(self.replicated)}/"
                f"{len(self.separated)} separated rungs replicated, "
                f"held {self.held or '()'} overturned {self.overturned or '()'}"
                f" | {self.arm_verdict} :: {len(self.two_sided)}/"
                f"{len(self.replicated)} two-sided, "
                f"one-armed {self.one_armed or '()'}")


def published_census() -> ReplicationCensus:
    """The published band's separated rungs against the replications on record."""
    from .scorable_band import published_band

    band = published_band()
    separated = tuple(r.weight for r in band.rungs
                      if r.scorable and r.headroom.verdict == SEPARATED)
    return ReplicationCensus(
        separated=separated,
        reproductions=((75.0, w75_reproduction()),
                       (100.0, w100_reproduction()),
                       (150.0, w150_reproduction()),
                       (250.0, w250_reproduction())),
    )
