# SPDX-License-Identifier: BSD-3-Clause
"""Which of D-243..D-246's headlines survive the arrival-scoped key?

D-252 re-graded `freeze_duration_max` against `freeze_duration_graded`, and
D-250 re-read the `w_freeze` grid's internal reading. Neither touched the
**sentences**. Four accepted decisions still state their headline in the
whole-trajectory language that D-248 measured as 99.1-99.9 % post-arrival
idling, and STATE has carried "which of those four survive" as the top
actionable since.

The two halves of that question are not equally answered
--------------------------------------------------------

D-245 and D-246 were measured at :data:`freeze_weight.PAIRED_LAM` (0.8), and
**D-250 re-read that exact grid at that exact temperature** — 0/12 exceed at
every one of ten weights, `NONE_ADMISSIBLE` -> `NO_FREEZE_TO_PRICE`. Those two
headlines are already graded, by a reading taken on their own curve.

D-243 and D-244 were measured at :data:`freeze_weight.D243_LAM` (0.1), and
**nothing has re-read them.** D-250's journal nonetheless calls D-243's
`2/3 -> 0/3` headline "an artifact". That conclusion is reached from the
`lam = 0.8` grid, and D-244 is the decision that established — and
`test_the_freeze_reading_is_not_comparable_across_temperatures` is the test
that pins — that a `w_freeze` cell quoted without its lam is not a claim about
anything. The same seed, arm and scene move from 3.30 s to 81.90 s across those
two temperatures. So D-250 graded a `lam = 0.1` claim with a `lam = 0.8`
measurement: the right verdict, reached across the one gap this branch has
already convicted itself of crossing.

That is the defect class this module exists to make unrepeatable, and it is why
the refusal below is a verdict rather than a caveat.

Why the refusal is the load-bearing part
----------------------------------------

:func:`regrade` will not grade a headline against cells taken at a different
temperature or a different seed count. It returns
:data:`NOT_COMPARABLE_LAM` / :data:`NOT_COMPARABLE_N` and stops. A re-read that
crosses either axis is not weaker evidence about the claim — it is evidence
about a different curve, and the honest output is that it declines.

The complementary check runs in the same call and is what makes a `before`
reading admissible as a re-read at all: :data:`NOT_REPRODUCED` fires when the
*whole*-scope column of the fresh cells disagrees with the exceedance sequence
the decision published. Both readings come off one simulation
(`freeze_weight.sweep`), so a re-read that reproduces the old column digit for
digit and disagrees on the new one has isolated the scope and nothing else.
Without that clause a `before` column could differ because the sweep drifted,
and the module would blame the scope.

The grading rule itself
-----------------------

Every one of the four headlines is a claim of the form "the ablation fails and
weight `w` fixes it" (D-243/D-244) or "no weight fixes it" (D-245/D-246). All
four therefore presume the same thing: **the ablation fails**. That is the
single predicate the scope moves, so it is the one this module grades on —
`freeze_weight.verdict`'s own `NO_FREEZE_TO_PRICE` clause, which is checked
before every other verdict for exactly this reason.

A headline whose ablation passes under `before` is :data:`VOID_POST_ARRIVAL`:
there was no freeze to buy, so both the optimum and the absence of one were
measuring how long the harness kept simulating a finished run.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

from eval.mppi_sandbox import freeze_weight as fw

#: The re-read reproduces the decision's own column and the claim still holds
#: under the arrival-scoped key.
SURVIVES = "SURVIVES"

#: The ablation does not fail under `before`, so the headline is denominated
#: against post-arrival idling. Neither an optimum nor its absence is readable.
VOID_POST_ARRIVAL = "VOID_POST_ARRIVAL"

#: The cells were taken at a different temperature than the claim. D-244's
#: finding, mechanised as a refusal.
NOT_COMPARABLE_LAM = "NOT_COMPARABLE_LAM"

#: The cells were taken at a different seed count than the claim. Weaker than
#: the lam axis but the same shape of error — D-244 itself recorded that
#: D-243's n=3 ablation (2/3) reads 6/12 at n=12.
NOT_COMPARABLE_N = "NOT_COMPARABLE_N"

#: The fresh cells' **whole**-scope column disagrees with the published one, so
#: the re-read is not on the claim's curve and cannot grade it.
NOT_REPRODUCED = "NOT_REPRODUCED"


@dataclass(frozen=True)
class Headline:
    """One published claim, with the coordinates that make it re-readable.

    `quoted` is the exceedance sequence the decision printed, aligned to
    `weights`, in the scope it was measured in — always
    :data:`freeze_weight.SCOPE_WHOLE` for these four, because the arrival-scoped
    reading did not exist until D-250.
    """

    decision: str
    claim: str
    lam: float
    n: int
    weights: tuple[float, ...]
    #: `None` where the decision printed the grid point but not its exceedance.
    #: Carried as a hole rather than dropped so `weights` stays the decision's
    #: own grid — a re-read must not silently regrade a narrower one.
    quoted: tuple[int | None, ...]
    scope: str = fw.SCOPE_WHOLE

    def __post_init__(self) -> None:
        if len(self.weights) != len(self.quoted):
            raise ValueError(
                f"{self.decision}: {len(self.weights)} weights against "
                f"{len(self.quoted)} quoted exceedances — a published column "
                "must align to the grid it was read off")
        if self.weights[0] != 0.0:
            raise ValueError(
                f"{self.decision}: weights[0] must be the ablation; the "
                "headline is denominated against it")


#: The four headlines, transcribed from `docs/decisions.md` with their
#: coordinates. Only the exceedance column is carried: it is the quantity all
#: four headlines turn on and the only one the scope moves.
#:
#: D-243 and D-244 are at :data:`freeze_weight.D243_LAM`; D-245 and D-246 at
#: :data:`freeze_weight.PAIRED_LAM`. That split is the whole reason this module
#: has a temperature refusal.
CLAIMS = (
    Headline(
        decision="D-243",
        claim="w_freeze = 1e4 takes social_mppi from 2/3 to 0/3 exceeding "
              "the declared 2.0 s, and 1e2 (3/3) is worse than not wiring "
              "the term at all",
        lam=fw.D243_LAM, n=3,
        weights=(0.0, 1e2, 1e3, 1e4, 1e5),
        quoted=(2, 3, 1, 0, 3),
    ),
    Headline(
        decision="D-244",
        claim="the optimum has width 2 — 3e3 and 1e4 are both 0/12 — and the "
              "n=3 ablation was optimistic at 2/3 against 6/12",
        lam=fw.D243_LAM, n=12,
        weights=(0.0, 1e2, 1e3, 3e3, 1e4),
        quoted=(6, 6, None, 0, 0),
    ),
    Headline(
        decision="D-245",
        claim="the admissible set is empty at the paired lam — 3e3 and 1e4 "
              "are 12/12 — and the grid ends still improving",
        lam=fw.PAIRED_LAM, n=12,
        weights=(0.0, 3e3, 1e4, 3e4, 1e5),
        quoted=(12, 12, 12, 8, 6),
    ),
    Headline(
        decision="D-246",
        claim="the curve turns around — 3e5 and 1e6 are both 12/12 — so 1e5 "
              "is an interior minimum and NONE_ADMISSIBLE is a result",
        lam=fw.PAIRED_LAM, n=12,
        weights=(0.0, 3e4, 1e5, 3e5, 1e6),
        quoted=(12, 8, 6, 12, 12),
    ),
)


def _cells_by_weight(cells: Sequence[fw.WeightCell]) -> dict[float, fw.WeightCell]:
    return {c.w_freeze: c for c in cells}


def reproduces(headline: Headline,
               cells: Sequence[fw.WeightCell]) -> bool:
    """Does the fresh cells' whole-scope column match the published one?

    Cells absent from `cells`, and published entries recorded as `None`, are
    skipped rather than failed: a decision that quoted five of ten grid points
    is not thereby contradicted by the five it did not print. What this checks
    is that every point the decision *did* publish is reproduced.
    """
    by_w = _cells_by_weight(cells)
    for w, q in zip(headline.weights, headline.quoted):
        if q is None or w not in by_w:
            continue
        if by_w[w].n_exceed_in(fw.SCOPE_WHOLE) != q:
            return False
    return True


def regrade(headline: Headline, cells: Sequence[fw.WeightCell], *,
            lam: float, n: int,
            eps: float = fw.EPS_CLEARANCE) -> str:
    """Grade one published headline against a fresh, same-curve re-read.

    The refusals come first and they are not advisory — see the module
    docstring. Only once the cells are on the claim's curve does the scope
    question get asked, and it is asked of the ablation, because that is the
    predicate all four headlines presume.
    """
    if lam != headline.lam:
        return NOT_COMPARABLE_LAM
    if n != headline.n:
        return NOT_COMPARABLE_N
    if not reproduces(headline, cells):
        return NOT_REPRODUCED
    if fw.verdict(cells, eps=eps,
                  scope=fw.SCOPE_BEFORE) == "NO_FREEZE_TO_PRICE":
        return VOID_POST_ARRIVAL
    return SURVIVES


def claims_at(lam: float, n: int) -> tuple[Headline, ...]:
    """The headlines a re-read at `(lam, n)` is entitled to grade."""
    return tuple(h for h in CLAIMS if h.lam == lam and h.n == n)


def main(argv: Sequence[str] | None = None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scene", default=fw.FREEZING_SCENE)
    ap.add_argument("--arm", default=fw.ARM)
    ap.add_argument("--lam", type=float, default=fw.D243_LAM)
    ap.add_argument("--seeds", type=int, default=3)
    args = ap.parse_args(argv)

    graded = claims_at(args.lam, args.seeds)
    if not graded:
        print(f"headline_rescope — no published headline sits at "
              f"lam={args.lam} n={args.seeds}; nothing to grade.")
        print("  (the refusal is the point — see NOT_COMPARABLE_LAM)")
        return 0

    weights = sorted({w for h in graded for w in h.weights})
    cells = fw.sweep(args.scene, args.arm, weights=weights,
                     seeds=tuple(range(args.seeds)), lam=args.lam)
    print(f"headline_rescope — {args.scene} arm={args.arm} "
          f"lam={args.lam} n={args.seeds}\n")
    for cell in cells:
        print(f"  {cell}")
    print(f"\n  before={fw.verdict(cells, scope=fw.SCOPE_BEFORE)} | "
          f"whole={fw.verdict(cells, scope=fw.SCOPE_WHOLE)}\n")
    for h in CLAIMS:
        v = regrade(h, cells, lam=args.lam, n=args.seeds)
        print(f"  {h.decision}  {v}")
        print(f"      {h.claim}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
