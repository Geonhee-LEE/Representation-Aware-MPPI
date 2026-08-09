# Two of the four rungs have no two-sided margin at all

- **Cycle**: 2026-08-09 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE#1 — price the ceiling: a margin sweep over the recorded clearances
- **Phase**: P3
- **Status**: keep

## What I tried

- D-157 left arm coverage at **0/4** (`NONE_TWO_SIDED`) and STATE read it as a
  defect of the *threshold*: `stock_mppi` never clears 0.40 m at
  `w ∈ {75, 100}`, so its rate is pinned and the separation is carried by one
  arm. The stated next slice was to ask **which margin, if any, would have made
  each rung two-sided** — pure computation, since the 32 per-seed clearances
  for all four rungs are already constants in `separation_reproduction.py`.
- `margin_sweep.py`: `regrade` (same runs, new threshold), `breakpoints` (the
  distinct recorded clearances — exhaustive, because the unsafe count
  `#{c : c < m}` is a step function that only moves as `m` crosses one),
  `MarginSweep` per rung, and `BandSweep` for the question the per-rung answers
  do not compose into.
- Zero sim runs. Zero controller/representation code. Headline unchanged.

## What worked / what failed

- 🔴 **Two of the four rungs have no two-sided margin at any threshold** — not
  "not at 0.40". At `w = 75` and `w = 100` the arms' pooled clearance ranges
  overlap by **7.6 mm** and **9.9 mm**, so no margin sits interior to both arms
  in both blocks. Their censoring is a property of the *effect being large*,
  not of a badly-chosen margin: a two-sided test needs the two distributions to
  overlap, and these barely do. **That half of `NONE_TWO_SIDED` is not
  repairable by re-grading**, which is the opposite of what the slice was
  authored to find.
- 🔴 **And `w = 250`'s reversal does not survive being read two-sided.** That
  rung is D-151's `SIGN_REVERSED`. At the published margin its sign rests on
  **one run per block** (stock 0/16 → 1/16, risk 1/16 → 0/16) — the rung is
  censored there precisely because almost nothing crosses. Re-graded at any of
  its 23 two-sided margins `[0.5467, 0.5938]`, the same 32 runs come back
  `REPRODUCED` — *all 23*, in the mechanism's direction. A **qualification** of
  D-151, not a retraction: 0.55 m is not the scene's margin and at that
  threshold most runs of both arms are "unsafe", so this orders two clearance
  distributions and makes no safety claim. What it removes is the reading that
  the seeds pointed *against* the mechanism at `w = 250`.
- 🔴 **The band-level number is worse than 0/4.** The two windows are disjoint
  (`[0.4194, 0.4437]` vs `[0.5467, 0.5938]`) and `Headroom` refuses two arms
  graded against different margins, so a band is scored at **one** threshold —
  therefore **no margin makes two of these four rungs two-sided at once**. Arm
  coverage over the published band has a **ceiling of 1/4**, where 0/4 was only
  a fact about the margin that was used.
- 🟢 **The exhaustiveness claim is probed, not argued.** Two of four answers are
  "no margin exists" — a claim over the reals made from a 64-item list. A dense
  2000-point grid per rung asserts every uncensored margin it finds was already
  enumerated. Without it the two `NO_TWO_SIDED_MARGIN` verdicts are unfounded.
- 🟡 **I had the `w = 250` result wrong in the first draft and the type system
  caught it, not me.** My scratch sweep recomputed the verdict at each margin
  and printed `REPRODUCED`, so I wrote "both windows hold their recorded
  verdict" into the module docstring. The rung's *recorded* verdict is
  `SIGN_REVERSED`; my `verdict` guard was keyed on `!= REPRODUCED` and routed
  it to the empty-denominator case, which is how the mistake surfaced. Keying
  on `NO_SEPARATION_TO_REPRODUCE` instead turned the one rung where re-grading
  changes the answer from a swallowed case into the cycle's finding — and made
  `TWO_SIDED_BUT_LOST` reachable over shipped data instead of needing a
  synthetic.
- 🟡 **A hedge I wrote was false and cheap to check.** `window`'s docstring said
  the two-sided set "need not be an interval". An arm's unsafe rate is monotone
  in the margin, so interiority is one contiguous run per arm and the four-way
  intersection is contiguous — always. `window` is a complete description, not
  a summary, and that is now a test rather than a caveat.
- 🟢 23 new tests, green first time; the coupled subset (`citation_audit`,
  `inert_surface`, `separation_reproduction`, `scorable_band`, `gap_gate`,
  `exclusion_scope`) 278 passed before any doc write.

## North-star delta

- **No movement, and this cycle sharpens why.** Zero sim runs; `unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 unchanged over the
  same 5 cells / 40 seeds.
- What moved is the **price of the evidence**: the band's arm coverage was
  reported as 0/4 with an implied repair (pick a better margin). Two rungs
  cannot be repaired at all, and the reachable ceiling is 1/4 — so the
  published band will not become a two-sided comparison by re-grading, only by
  a scene where the arms' clearance distributions overlap.
- One reversal reading retired: `w = 250`'s sign is a tail artifact, so the
  band no longer holds a rung whose seeds point against the mechanism.

## Key learnings

- **"Censored" and "under-powered" are opposite diagnoses and read identically
  in the census.** `w = 75`/`w = 100` are censored because their effect is so
  large the distributions barely overlap; a rung censored for that reason gets
  *worse* as the mechanism gets better. Any future gate on arm coverage would
  therefore penalise the band's strongest results — which is the concrete
  reason to keep `arm_verdict` reported and unthresholded (D-044).
- **A verdict comparison keyed on the wrong constant hides exactly the
  interesting row.** `!= REPRODUCED` swallowed the only rung whose answer the
  margin changes. When routing on a verdict enum, key on the case being
  excluded, never on the case being kept.
- **The re-graded verdict, not the lost one, is the finding.** `lost` says a
  margin was load-bearing; `regraded_verdicts` says what replaced it. A rung
  going `SIGN_REVERSED → NOT_REPRODUCED` would have been a much weaker result
  than `SIGN_REVERSED → REPRODUCED` ×23, and `lost` alone cannot tell them apart.

## Recommended next 1–3 priorities

1. **Ask the overlap question of the *scene*, not the rungs.** Arm coverage is
   capped at 1/4 because at three rungs the arms barely overlap on
   `cafe_head_on_v0`. A rung with real overlap is what a two-sided test needs —
   so the reading to take next is which of the 8 matrix scenes have overlapping
   arm clearance distributions at the published margin. Recorded data may
   already answer it; if not it is one cheap walk.
2. **Carry "unmeasured" in the strand verdict (D-156 follow-up)** — unchanged
   for two cycles; one field, one test.
3. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged for eleven
   cycles; needs `shift_census` promoted to a dataclass.

## Artifacts

- PR: #67 (continuing, D-140)
- Files touched: `eval/mppi_sandbox/margin_sweep.py`, `eval/mppi_sandbox/tests/test_margin_sweep.py`, `docs/decisions.md`
- TSV row appended: yes
