# SPDX-License-Identifier: BSD-3-Clause
"""Whether an A/B could have separated its arms at the weight it was run at.

Two shipped mechanism claims — D-119's risk channel and D-124's gap gate — were
both scored on `cafe_head_on_v0` at the shipped `w_obs_soft = 10`, and both
reported `unsafe_rate = 1.0000` **in every arm**. D-125 then measured that this
scene's unsafe rate goes 1.0000 → 0.0000 somewhere between 10 and 300, and
D-126/D-130 closed the admissible set from both ends (`relieving = {300, 1000,
3000, 10000, 30000}`, `pick_weight` → **3000**). So the two comparisons were
taken roughly **300× below** the cheapest weight at which either arm can pass.

That is not a weak result; it is a comparison with no *headroom*. If every run
in both arms lands on the same side of the scene's declared margin, the headline
is pinned by construction and the two arms are indistinguishable on it **no
matter what the mechanism does**. A p-value computed there is a p-value about a
constant. This module is the predicate that says so before the claim ships.

**The trap is the secondary metric, and D-124 walked into it.** Its headline
finding is `mean_clearance` **0.0056 → 0.0095** — a real 1.7× on a real number.
But this scene's declared margin is **0.40 m**, so *both* ends of that
improvement sit ~50× below the line the scene grades on: the gate moved the
robot from deeply unsafe to slightly-less-deeply unsafe, and no run changed
verdict. `sub_margin` is the name for a delta whose entire span lies on one side
of the boundary — reportable as a mechanism signal, inadmissible as a safety
improvement, and the distinction is exactly the one `near_miss` was built to
stop collapsing.

**Measured 2026-08-08 on `cafe_head_on_v0`, λ = 0.8, 8 seeds, margin 0.40 m.**
`unsafe_rate` per arm, walking the weight ladder (all arms 8/8 reached)::

    w        stock    gap_gated   risk     verdict vs stock (gap / risk)
    10       1.0000   1.0000      —        NO_HEADROOM_UNSAFE / —
    30       1.0000   1.0000      1.0000   NO_HEADROOM_UNSAFE / NO_HEADROOM_UNSAFE
    100      1.0000   1.0000      0.2500   NO_HEADROOM_UNSAFE / **SEPARATED**
    300      0.0000   0.0000      0.0000   NO_HEADROOM_SAFE   / NO_HEADROOM_SAFE
    3000     0.0000   0.0000      —        NO_HEADROOM_SAFE   / —

Two findings, and the first is a refutation of the plan that produced this
module. **Re-running above the relief threshold does not rescue an A/B.** For
the gap gate, 10 → 3000 swaps `NO_HEADROOM_UNSAFE` for `NO_HEADROOM_SAFE`
(`shift` → `STILL_UNSCORABLE`): the barrier weight alone already solves the
scene at its own operating point, so both arms pass everywhere and the mechanism
has nothing to be measured against. The gate is **unscorable at every rung on
the ladder** — its mean-clearance deltas alternate sign (0.0293/0.0289,
0.3035/0.3068, 0.5806/0.5791), which is D-124's own "directionless" verdict now
reproduced on the scene D-124 had read as 1.7× favourable.

**Second: the risk channel separates, and only at `w = 100`.** 1.0000 → 0.2500
unsafe, both arms in the ESS band, 8/8 reached — the first mechanism claim this
project has scored at an operating point where the headline could have moved
either way. Note where that rung sits: **below** the relief threshold of 300.
"Run it above the threshold" and "run it where the arms can differ" are
different instructions, and on this scene they point at **disjoint** regions —
a threshold is the weight above which the *scene* passes, which is precisely the
weight above which a *comparison* stops discriminating. Expect this, do not
patch around it: the scorable band is the transition, and the transition ends
where relief begins.

**And λ calibration is not weight-invariant.** `lam_windows.yaml` was measured
at the shipped `w_obs_soft = 10`; at `w = 30` both stock and gap_gated leave the
ESS band (`ess_in_band = False`) at the same λ = 0.8 that is admissible at 10,
100 and 300. Re-scoring at a new weight therefore owes an ESS check per rung —
`ab.assert_ess_in_band` already exists for it, and a rescore that skips it can
report a delta from a sampler that has quietly gone greedy.

Three things this deliberately does **not** do:

  * It does not re-rank the arms. `SEPARATED` says the headline can tell the
    arms apart at this operating point; which arm is better and whether the
    margin of victory survives `sign_counts` is `ab`'s job, not this module's.
  * It does not treat `NO_HEADROOM_SAFE` as a synonym for `NO_HEADROOM_UNSAFE`.
    Both are unscorable A/Bs, but one is a scene the system already solves and
    the other is a scene it fails everywhere; merging them would let "we fixed
    it" and "we cannot touch it" print the same word. They are one verdict apart
    and stay two names apart (the `relief_interval.UNDERPOWERED`/`UNRELIEVED`
    argument, one axis over).
  * It does not pick the operating weight. `operating_weight.resolve` already
    owns that rule and its ladder is measured; restating it here would be the
    second statement D-047 forbids. Callers pass the weight in.

**Honest scope limit.** Headroom is a property of a (scene, margin, weight,
temperature) tuple, and the weight this module is meant to be used at was
surveyed at `lam = 0.4` while D-124's A/B ran at `lam = 0.8` — both admissible
for both arms on this scene, but not the same rung. `Headroom.lam` is recorded
for that reason: a comparison re-scored at a weight measured on a different rung
is an extrapolation across the temperature axis, and it should show up as a
field rather than as a number whose provenance has to be reconstructed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .lam_window_index import (
    INDEX_REFUSALS,
    NO_TABLE_AT_WEIGHT,
    Resolution,
    TableIndex,
    resolve,
)
from .near_miss import NearMissStats, is_scorable_margin, score

#: Every run in both arms came closer than the margin. The headline cannot
#: move, so the A/B is not a test of the mechanism — it is a measurement taken
#: inside the failure region.
NO_HEADROOM_UNSAFE = "NO_HEADROOM_UNSAFE"

#: Every run in both arms held the margin. Also unscorable, and for the mirror
#: reason — but this one is the outcome the north star asks for, so it is a
#: different sentence about the system even though it is the same sentence
#: about the experiment.
NO_HEADROOM_SAFE = "NO_HEADROOM_SAFE"

#: The margin is crossed somewhere in the pooled ensemble, and both arms report
#: the same `unsafe_rate`. The comparison *could* have separated them and did
#: not — a real null, unlike the two above.
TIED = "TIED"

#: The margin is crossed and the arms' unsafe rates differ. The only verdict
#: under which a headline safety delta is attributable to the mechanism.
SEPARATED = "SEPARATED"

#: Verdicts under which a published safety delta means something.
SCORABLE = (TIED, SEPARATED)


@dataclass(frozen=True)
class ArmSafety:
    """One arm's per-seed clearances graded against the scene's margin."""

    arm: str
    clearances: tuple[float, ...]
    margin: float

    @property
    def stats(self) -> NearMissStats:
        return score(self.clearances, self.margin)

    @property
    def unsafe_rate(self) -> float:
        return self.stats.unsafe_rate

    @property
    def mean_clearance(self) -> float:
        return sum(self.clearances) / len(self.clearances)


@dataclass(frozen=True)
class Headroom:
    """Can this A/B's headline separate its two arms at this operating point?"""

    scenario: str
    weight: float
    lam: float
    a: ArmSafety
    b: ArmSafety

    def __post_init__(self) -> None:
        if self.a.margin != self.b.margin:
            raise ValueError(
                f"arms graded against different margins "
                f"({self.a.margin} vs {self.b.margin}) — a headroom verdict "
                "over two boundaries is not a verdict"
            )
        if not is_scorable_margin(self.margin):
            raise ValueError(
                f"margin {self.margin!r} is not scorable; a scene with no "
                "declared margin is excluded by name, not graded (near_miss)"
            )

    @property
    def margin(self) -> float:
        return self.a.margin

    @property
    def pooled(self) -> tuple[float, ...]:
        return tuple(self.a.clearances) + tuple(self.b.clearances)

    @property
    def verdict(self) -> str:
        if all(c < self.margin for c in self.pooled):
            return NO_HEADROOM_UNSAFE
        if all(c >= self.margin for c in self.pooled):
            return NO_HEADROOM_SAFE
        return TIED if self.a.unsafe_rate == self.b.unsafe_rate else SEPARATED

    @property
    def scorable(self) -> bool:
        """Whether a safety delta read off this A/B is admissible at all."""
        return self.verdict in SCORABLE

    @property
    def sub_margin(self) -> bool:
        """Whether a *clearance* delta between these arms is entirely below the
        margin — the D-124 trap. True does not make the delta false; it makes
        it a mechanism signal rather than a safety improvement, and the report
        has to say which one it is."""
        hi = max(self.a.mean_clearance, self.b.mean_clearance)
        return hi < self.margin

    @property
    def delta_unsafe(self) -> float:
        """`b − a` on the headline. Signed, so a negative number is `b` safer."""
        return self.b.unsafe_rate - self.a.unsafe_rate

    def __str__(self) -> str:
        return (
            f"{self.scenario} w={self.weight:g} lam={self.lam:g} "
            f"margin={self.margin:.2f} :: {self.verdict} "
            f"[{self.a.arm} {self.a.unsafe_rate:.4f} / "
            f"{self.b.arm} {self.b.unsafe_rate:.4f}]"
            + ("  (clearance delta SUB_MARGIN)" if self.sub_margin else "")
        )


#: How a comparison's discriminating power changed when it was re-run at the
#: operating weight. `BOUGHT_HEADROOM` is the one that retro-actively grades the
#: original claim as unscored rather than merely weak.
BOUGHT_HEADROOM = "BOUGHT_HEADROOM"
LOST_HEADROOM = "LOST_HEADROOM"
STILL_UNSCORABLE = "STILL_UNSCORABLE"
SCORABLE_THROUGHOUT = "SCORABLE_THROUGHOUT"


def shift(before: Headroom, after: Headroom) -> str:
    """Grade a re-run: did moving the operating point make the A/B a test?

    `before` is the weight the claim was published at, `after` the weight the
    scene admits. Both must be the same scene — re-scoring is a claim about one
    scene's operating point, and comparing across scenes would grade the
    scenery.
    """
    if before.scenario != after.scenario:
        raise ValueError(
            f"shift across scenes ({before.scenario} → {after.scenario}); "
            "a re-score is a claim about one scene's operating point"
        )
    if before.scorable and after.scorable:
        return SCORABLE_THROUGHOUT
    if after.scorable:
        return BOUGHT_HEADROOM
    if before.scorable:
        return LOST_HEADROOM
    return STILL_UNSCORABLE


def render(rows: Sequence[Headroom]) -> str:
    """One line per operating point, in the order given."""
    return "\n".join(str(r) for r in rows)


# --------------------------------------------------------------------------
# Certifying the operating point (D-144)
#
# Everything above grades a comparison against the scene's *margin*. Nothing
# above checks that the comparison was taken at a temperature the scene was
# ever calibrated for — `Headroom.lam` is recorded (see the docstring's honest
# scope limit) and then read by no one. D-134→D-143 built the machinery to
# answer that question: `lookup` grades a table, and `lam_window_index.resolve`
# picks the table **from** the weight. But `resolve` still has no consumer
# outside its own tests, so the λ guard is *available* rather than
# load-bearing: every sweep driver and every published `Headroom` still takes λ
# as a free argument and no code path can refuse one.
#
# This is that consumer. It is deliberately placed here rather than in a fourth
# guard module: the thing that needs gating is the *publication* of a safety
# delta at an operating point, and `Headroom` is what this repo publishes.
#
# Two names are added and no more. The index's own verdicts
# (`NO_TABLE_AT_WEIGHT`, `NO_CELL`, `EMPTY_WINDOW`) pass through **verbatim**,
# because a certification that renamed them would be D-047's second statement
# of a fact `lam_window_index` already owns — and the two vocabularies would
# then drift independently.
# --------------------------------------------------------------------------

#: Both arms have a calibrated window at this weight and the recorded λ lies in
#: both. The only verdict under which a headline read off this `Headroom` was
#: taken at a temperature the scene admits.
CERTIFIED = "CERTIFIED"

#: Both arms have a non-empty window at this weight and λ is outside at least
#: one of them. Distinct from `EMPTY_WINDOW` on purpose: there *is* an
#: admissible temperature here, the comparison simply was not run at it — so
#: the action is "re-run at a rung in the window", not "this cell is not an
#: ablation surface". :attr:`Certification.sole_uncertified` names the arm.
OFF_WINDOW = "OFF_WINDOW"

#: Verdicts under which a delta read off the `Headroom` is not attributable to
#: the mechanism at a calibrated operating point.
UNCERTIFIED = INDEX_REFUSALS | {OFF_WINDOW}


class UncertifiedOperatingPoint(ValueError):
    """A `Headroom` was asserted at a `(weight, λ)` the calibration refuses."""


@dataclass(frozen=True)
class Certification:
    """Whether a `Headroom`'s `(weight, λ)` is an operating point both arms
    were calibrated at.

    Per-arm by construction. D-133 measured that a refusal usually belongs to
    **one** arm — `crossing`'s two arms have windows disjoint from each other —
    and a certification that collapsed to a single boolean would print the same
    word for "neither arm was calibrated here" and "the baseline was, the
    mechanism was not". The second is a finding about the comparison; the first
    is a finding about the scene.
    """

    row: Headroom
    #: `arm name → Resolution`, in `(a, b)` order.
    arms: Mapping[str, Resolution]

    @property
    def available(self) -> tuple[float, ...]:
        """Weights the index carries — the actionable half of a refusal."""
        for res in self.arms.values():
            return res.available
        return ()

    @property
    def uncertified(self) -> tuple[str, ...]:
        """Arms whose window does not admit `row.lam`, in `(a, b)` order."""
        return tuple(
            arm for arm, res in self.arms.items()
            if res.usable is None or self.row.lam not in res.usable
        )

    @property
    def sole_uncertified(self) -> str | None:
        """The single arm carrying the refusal, or `None` if both do (or
        neither). Mirrors `scorable_band.sole_refuser`: an asymmetric refusal
        points at the mechanism, a symmetric one points at the scene."""
        out = self.uncertified
        return out[0] if len(out) == 1 else None

    @property
    def verdict(self) -> str:
        """The index's verdict when a table or cell is missing, else
        `CERTIFIED` / `OFF_WINDOW`.

        Worst-first when the arms disagree in kind: a missing table outranks a
        missing cell outranks an empty window, because each names a strictly
        larger thing to go and measure.
        """
        by_arm = [res.verdict for res in self.arms.values()]
        for refusal in (NO_TABLE_AT_WEIGHT, *sorted(INDEX_REFUSALS - {NO_TABLE_AT_WEIGHT})):
            if refusal in by_arm:
                return refusal
        return CERTIFIED if not self.uncertified else OFF_WINDOW

    @property
    def certified(self) -> bool:
        return self.verdict == CERTIFIED

    def __str__(self) -> str:
        have = ", ".join(f"{w:g}" for w in self.available) or "none"
        windows = "; ".join(
            f"{arm}={'—' if res.usable is None else list(res.usable)}"
            for arm, res in self.arms.items()
        )
        sole = self.sole_uncertified
        return (
            f"{self.row.scenario} w={self.row.weight:g} lam={self.row.lam:g} "
            f":: {self.verdict} [{windows} calibrated_at={have}]"
            + (f"  (sole={sole})" if sole is not None else "")
        )


def certify(row: Headroom, index: TableIndex | None = None) -> Certification:
    """Resolve both of `row`'s arms at `row.weight` and grade `row.lam`.

    The arm *names* are used as controller keys — that is the whole coupling,
    and it is why an A/B whose arms are named `"a"` / `"b"` grades `NO_CELL`
    rather than silently passing. An arm that is not in the calibration table
    has no window, and a comparison published at a temperature nobody measured
    for that controller is exactly what this is meant to catch.
    """
    arms = {
        arm.arm: resolve(row.scenario, arm.arm, row.weight, index)
        for arm in (row.a, row.b)
    }
    return Certification(row=row, arms=arms)


def assert_certified(row: Headroom, index: TableIndex | None = None) -> Certification:
    """Return the certification, or raise if the operating point is refused.

    This is the *enforcing* entry point — the one that makes the λ guard cost
    something. `certify` reports; this refuses. A driver that calls it can no
    longer accept λ as a free argument, which was the gap D-143 left open:
    `resolve` supplied the window and nothing consumed it.
    """
    cert = certify(row, index)
    if not cert.certified:
        raise UncertifiedOperatingPoint(str(cert))
    return cert
