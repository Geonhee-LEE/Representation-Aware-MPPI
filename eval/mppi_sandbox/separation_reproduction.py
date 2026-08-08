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

Typical use::

    rep = Reproduction(reference=block_a, replication=block_b)
    print(rep.verdict)   # SIGN_REVERSED
    print(rep.pooled.verdict)  # TIED — the honest single number at n = 32
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


def w250_reproduction() -> Reproduction:
    """The measured replication of the published band's one-run rung.

    Built from :data:`W250_CLEARANCES` rather than by re-simulating, so a test
    of the grade costs no runs; the runs are the constant.
    """
    from .scorable_band import (
        PUBLISHED_ARMS,
        PUBLISHED_LAM,
        PUBLISHED_MARGIN,
        PUBLISHED_SCENARIO,
    )

    cut = W250_REFERENCE_SEEDS
    stock, risk = PUBLISHED_ARMS

    def block(lo: int, hi: int) -> SeedBlock:
        return SeedBlock(
            seeds=tuple(range(lo, hi)),
            headroom=Headroom(
                scenario=PUBLISHED_SCENARIO, weight=250.0, lam=PUBLISHED_LAM,
                a=ArmSafety(arm=stock,
                            clearances=W250_CLEARANCES[stock][lo:hi],
                            margin=PUBLISHED_MARGIN),
                b=ArmSafety(arm=risk,
                            clearances=W250_CLEARANCES[risk][lo:hi],
                            margin=PUBLISHED_MARGIN),
            ),
        )

    n = len(W250_CLEARANCES[stock])
    return Reproduction(reference=block(0, cut), replication=block(cut, n))
