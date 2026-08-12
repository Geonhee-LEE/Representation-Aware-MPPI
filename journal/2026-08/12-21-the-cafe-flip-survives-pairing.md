# The cafe flip survives pairing — D-224 was a verdict on the arms, not on the statistic

- **Cycle**: 2026-08-12 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE#1` Re-read the cafe 2×2 in the paired estimand (Q-135)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `cafe_obstacle_crossing_v0`'s 2×2 (`w_risk ∈ {40, 0}` × `w_ped ∈ {0, 50}`)
  at `lam = 0.8` on D-217's **same six seeds**, recording **per-seed** clearances
  instead of `SweepStats` — the reduction is exactly where `three_arm.risk_interaction`
  loses the pairing.
- Put the walk in the module as `walk_cells()` rather than a scratch script, so
  `WALK_CAFE_6` has a re-derivation path, and read it with the **unchanged**
  `PairedStep` class the off-family retraction used.
- Answered Q-135, opened Q-136 for the two cafe scenes still read unpaired.

## What worked / what failed

- **The sign survives.** `w_risk=40`: mean **+0.3501 m** CI [+0.3181, +0.3936]
  `SEPARATED_POSITIVE`; `w_risk=0`: mean **−0.0339 m** CI [−0.0443, −0.0235]
  `SEPARATED_NEGATIVE`. Both rows 6/6 unanimous (6+/0−, 0+/6−). Off-family the
  same reading gave 9+/11− and `NOT_SEPARATED` twice.
- **The reproduction is exact.** `worst_step` on this walk is **+0.3755 / −0.0192**
  — D-218's published pair to four decimals. That is what makes this a
  *re-reading*; the estimand changed, the runs did not.
- **Pairing moved both rows, in opposite directions**: top `+0.3755 → +0.3501`
  (smaller), bottom `−0.0192 → −0.0339` (**larger**). I had half-expected the
  paired mean to be a rounding of the minimum difference. It is not, in either
  row, so reporting both is load-bearing rather than ceremonial.
- Cost was far below the estimate: the 24-run walk took ~2 min, not the ~5 the
  Q-135 lean implied. The first walk attempt died on `ModuleNotFoundError`
  (`/tmp` script without `PYTHONPATH`) — 40 s lost, and the reason the walk now
  lives in the module.

## North-star delta

- **The branch's largest measured effect (+0.3755 m) now has a confidence
  interval and a paired estimand behind it.** Every clearance headline from
  D-217 onward rested on a difference of ensemble minima; the biggest one has
  now been re-read in a statistic that is fixed under `n`, and it holds.
- `is_interaction` / `interaction_sign_flip` keep their cafe-family basis —
  D-219's line is not retracted. No planner change: this cycle re-grounded a
  published claim rather than adding one.

## Key learnings

- **A retraction needs a control.** D-224 alone reads as "the statistic is
  broken"; D-224 + this cycle reads as "those arms were noise, and here is the
  scene where the same reading separates cleanly". The second is a much
  narrower — and more useful — claim, and it cost one walk.
- **`p = 0.031` at `n = 6` is a floor, not a margin.** The minimum attainable
  two-sided sign-test p at six pairs is `2/2⁶ = 0.03125`, so unanimity is the
  strongest statement this ensemble can make. Pinned in a test so a later
  reader does not mistake it for comfortable headroom.
- The weakest remaining link is `cafe_head_on_v0`'s **−0.0002 m** cell — same
  order of magnitude as the off-family steps that dissolved, and
  `interaction_sign_flip` judges on a *product* of signs, so that one cell
  decides that scene's flip verdict (Q-136).

## Recommended next 1–3 priorities

1. **Walk the remaining two cafe scenes paired** (Q-136) — `walk_cells` already
   takes the scene; head_on's −0.0002 is the one that could move a verdict.
2. **Read the risk term alone across families** — +0.1089 m off-family vs
   −0.0134 m on cafe crossing, still unbooked, now readable with a CI.
3. **Re-probe the `journal/` / `results/` / `STATE.md` pins** (D-207) — unpaid
   for eight cycles; `inert_surface probe journal/` exceeded 240 s, so it needs
   a cycle that does not also run a suite.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/paired_step.py`,
  `eval/mppi_sandbox/tests/test_paired_step.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `journal/2026-08/12-21-the-cafe-flip-survives-pairing.md`
- TSV row appended: pending
