# The 256-rollout seed debt was paid two days ago and nobody looked

- **Cycle**: 2026-08-19 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — does `cafe_head_on_v0`'s `0.1964` interval survive 8 seeds?
- **Phase**: P3 (grading surface; P5 by calendar)
- **Status**: keep

## What I tried

- Picked STATE next-action #1 (priced at **64 rollouts / ~90 s**): intersect
  `cafe_head_on_v0`'s per-seed attained clearance ranges over 8 seeds, and take
  D-367's per-pair `rho` on a **second, non-`freezing`** scene while the
  ensemble was in hand.
- Started the 64-rollout measurement in the background first — then, looking for
  the arm list, found `scene_transfer.HEAD_ON_ENSEMBLE`: **8 arms × 8 seeds on
  this exact scene, on disk since D-332**. STATE #2's `256 rollouts` for four
  scenes are likewise all four already pinned (`CONVOY`/`CUT_IN`/`HEAD_ON`/
  `OBSTACLE_CROSSING_ENSEMBLE`). The debt costs **zero rollouts**.
- Let the background run finish anyway as a validity check on a two-day-old pin,
  then shipped `eval/mppi_sandbox/seed_debt.py` + 35 pytest pins.

## What worked / what failed

- **The pinned matrix reproduces bit-for-bit**: all 64 values equal to 4 dp
  after 117 s. First determinism check this branch has taken across a two-day
  gap — the sandbox is seed-reproducible at ensemble width, which nothing had
  verified. The `~90 s` was not wasted-if-spent, just unnecessary.
- **Finding #1 — the interval survives, at half the width.** Intersection is
  `(0.0043, 0.1044)`, width `0.1001` vs D-365's seed-0 `0.1964`: **1.96×
  narrower**. The floor barely moves (`0.0039→0.0043`); the **ceiling collapses
  `0.2003→0.1044`** (`0.0959 m`). One seed binds it — `cbf_mppi` attains
  `0.1044` on seed 4 against `0.18`–`0.22` on the other seven.
- **My first guess at the mechanism was wrong and the test caught it.** I pinned
  "seed 0 is the widest seed"; it is **third of eight** (seeds 3 and 6 are
  wider). The cause is not a lucky seed — *any* single seed overstates an
  intersection, since a per-seed range is a superset of it by construction.
- **Finding #2 — D-366's ordering is right, by 2× more than it knew.** Freezing
  `0.4354` / head_on `0.1001` = **`4.35×`**. STATE quotes `2.2×`, which is
  freezing against head_on's *seed-0 spread* — an unequal-width comparison.
- **Finding #3 — D-367's shape transfers, its balance flips.** On `head_on`
  **17 of 26** non-degenerate pairs are negative (D-367 on `freezing`: 9 of 26),
  range `-0.5614`…`+0.7218`, straddling zero again. Baseline column is worse:
  **4 of 6** `stock_mppi` pairs grade `PAIRED_HURTS` (D-367: 3 of 6), worst
  `social_mppi` at `rho=-0.5614` → `sd_ratio 1.2496`, i.e. pairing **widens**
  that interval 25 %. Second scene running, the negative end sits on the
  comparison the deficit claim is made in.
- All four scenes' windows are **non-empty** — every scene STATE wanted to widen
  is gradeable at seed width, not just `head_on`.
- Bonus: the two `+1.0000` pairs are again `geometric_mppi × stock_mppi` and
  `frozen_risk_mppi × risk_mppi`. D-367 called perfect seed correlation the
  inert-channel signature; it reproduces on different geometry, and here it is
  **derived** from the measurement, so it is a check rather than a restatement.

## North-star delta

- No new avoidance/tracking metre. What moved is **price**: the branch's largest
  outstanding measurement (`256` rollouts, carried across D-360…D-367) is
  discharged at `0` and the four windows are now pinned.
- The **user-blocked repair queue is re-priced**: `head_on`'s target interval is
  half as wide as STATE advertised and its ceiling is `0.1044`, not `0.2003`. A
  value chosen from the old range could miss on 7 of 8 seeds.

## Key learnings

- **Three cycles running, the cheapest act was reading what the branch already
  measured** (D-315 receipt, D-367 rho matrix, this). The pattern is that the
  *price* gets written in `STATE.md` prose while the *data* lands in a module,
  and nothing joins them. That is a structural gap, not three accidents.
- **A per-seed range is a superset of the intersection**, so any single-seed
  interval overstates a seed-robust one — independent of which seed. Every
  seed-0 interval on this branch is an upper bound, not an estimate.
- **`rho`'s sign varies by scene as well as by pair**, and the majority flipped
  between the only two scenes measured. D-367 was right to refuse to extend its
  values; anyone tempted to now has two disagreeing scenes to explain.

## Recommended next 1–3 priorities

1. **Re-price the user-blocked `head_on` declaration to `(0.0043, 0.1044)`** —
   the STATE entry still quotes `0.1964`/seed-0 and would mislead the choice.
2. **The cross-track column's seed debt is genuinely unpaid** — no `cte_rms`
   ensemble exists at seed width, and that is the column D-362/D-363 turn on.
   Check `scene_transfer`-style pins before budgeting it, per this cycle.
3. **Join the price to the data**: a check that flags a `STATE.md` rollout
   estimate for a scene whose ensemble is already pinned would have saved three
   cycles' worth of misbudgeting.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/seed_debt.py, eval/mppi_sandbox/tests/test_seed_debt.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
