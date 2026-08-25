# The two arms never charge the same point

- **Cycle**: 2026-08-14 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `Q-148-arm-freeze` (re-framed by the Phase 0 candidate set)
- **Phase**: P3
- **Status**: keep

## What I tried

- STATE's #1 was to freeze the four `(w_epist, w_voo)` pairs now that D-261 fixed
  the both-on cell at `0.4121 : 1`. Phase 0's top feed entry — RAZER
  (2309.05582, 16:00) — attacks the step *upstream* of that: it says attract and
  repel are not two candidates for one slot but **two channels with two
  independent weights** (Eqs. 9–11), with the collision job in a separate
  constraint term. On a tie the Phase 0 candidate wins, and freezing a ratio
  derived from an instrument that may be the wrong one is not a tie.
- Made the challenge falsifiable instead of citable. RAZER's claim has a spatial
  consequence: separate channels should not charge the same candidates. New
  `eval/mppi_sandbox/channel_support.py` evaluates both arms at unit weight on
  D-258's `ROLLOUT` support and reduces each to its **live set** — points where
  its cost departs from its own minimum (deviation-from-min, because MPPI's
  softmax is shift-invariant, so a flat arm is not a force).
- Read the overlap at three radii and across all eight `DEFAULT_SEEDS`.

## What worked / what failed

- **The live sets are disjoint.** At the scene's radius (`r=0.3`) the Jaccard is
  `0.0072` — 2 shared points in a 277-point union — and at `r=0.5` it is exactly
  `0.0`. The 2-point overlap carries `<0.1%` of the attract arm's deviation mass,
  so it is not a small overlap hiding all the force.
- **The load-bearing half is an identity, not a threshold.** The repel arm's live
  set is **exactly** `classify`'s exposed partition at every radius and at 8/8
  seeds. That is the same partition the split statistic is taken across, so
  `-v1/s1` divides one arm's mean over the shadow by the other's mean over the
  shadow's complement. The root is a **between-region exchange rate**; reading it
  as "which arm wins" over-claims.
- **A band-width mechanism falls out.** The repel arm is live on **8 of 316**
  candidates at seed 0, and the count swings `8 … 42` (5.25×) across seeds. The
  root's numerator is a mean whose sample size is single-digit and itself
  seed-dependent — a concrete cause for the D-257/D-258 spread that neither
  named.
- **One test asserted what I wanted and was rewritten.** `CHANNEL_SEPARATED` at
  every seed is false: seed 3 reads `PARTIAL` at Jaccard `0.0565`, just over the
  `0.05` constant. Lowering the constant to reach 8/8 would be picking the
  threshold to fit the finding. The test now pins the measured **7/8** split, and
  the seed-robust claim was moved to the two statements that do hold at 8/8
  (`jaccard_hi ≤ 0.06`, exposed-partition identity).
- 25 tests, all green locally.

## North-star delta

- No closed-loop movement — still a cost-field reading, still blocked on PR #68
  for the scene. Zero sim.
- What moved is the **standing of a number the A/B was about to be built on**.
  D-261's `0.4121` is not wrong, but its `INDETERMINATE` sign is now explained
  rather than merely accepted: the bracket straddles zero because it is pricing
  two regional means against each other, not because the scene is genuinely
  balanced.

## Key learnings

- A framing challenge from the literature can be **measured**, not just argued,
  when it implies a spatial fact. RAZER runs no sign-flip ablation, so citing it
  would have settled nothing; the branch's own instrument settled the half that
  is checkable in ten minutes.
- `probe_all`'s docstring already said the arms' supports differ ("repel charges
  points inside the shadow, attract discounts points that see into it"). It was
  written as the reason the sum *need not cancel*. Nobody had asked what the same
  fact does to the **interpretation of the root**, which is the opposite
  direction and the more consequential one.
- Disjointness does **not** void the A/B. MPPI scores whole trajectories, so a
  rollout that enters the shadow pays one arm and forgoes the other; the arms do
  trade, just not at a point. The finding narrows the instrument's claim, it does
  not cancel the experiment.

## Recommended next 1–3 priorities

1. Freeze the four `(w_epist, w_voo)` pairs as an explicit config (STATE #1,
   still the right next step) — but record alongside them that the both-on cell's
   sign is a between-region rate, so the A/B is adjudicated on near-miss and
   clearance only.
2. Ask whether the repel arm's 8-point live set is a **scene** fact or a
   **support** fact: re-read the live count on the grid at matched K. If the grid
   gives a far larger repel live set, the sample-size problem is the planner's
   support, not the critic.
3. RAZER's third term (`cS`, source-agnostic constraint) is unadoptable here —
   the branch has no aleatoric estimator. Record that as the boundary of the
   borrow rather than leaving it as an open option.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/channel_support.py`,
  `eval/mppi_sandbox/tests/test_channel_support.py`, `docs/decisions.md`,
  `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
