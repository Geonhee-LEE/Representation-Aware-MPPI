# The solved temperature holds the band — and costs 37% of the clock

- **Cycle**: 2026-08-17 15:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-156 (c) — wire `essps_mppi` and compare per-step band retention
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared D-112's stranding finding first: 14:00's two commits (`286f788`,
  `f7087ed`) were on disk, `origin` was at `8c4955c`. Gate 1 read 6 (cap 6),
  but D-140/D-267 say the gate counts *new* review bandwidth and PR #67 is
  already open on this branch — so continuing here is allowed, and no new
  branch was cut.
- Broke the four-cycle meta streak by taking a science item. STATE's top-ranked
  claude-actionable (Q-155) turned out to be **already resolved → D-274**, so
  the pick came from Q-156 instead: the per-*iteration* ESSPS form.
- Added a `_softmax_lam(cost)` hook to `StockMPPI.command` and
  `controllers/essps_mppi.py` = `RiskMPPI` with only that method overridden;
  one registry line. Measured both arms at `(lam=0.8, w_voo=5)` on
  `cafe_freezing_v0`, seed 0, in `ess_at_peak.ISOLATION`.

## What worked / what failed

- **157 of 157 steps in band** for the solved arm against the control's
  **69 of 115** — and the control reproduces both provenance anchors exactly
  (median ESS `31.2344` = D-270; `69` = D-274's `COMPLIANCE_OPTIMAL`).
- **The compliance number is not the finding.** Target `10/32·K = 80` sits
  *inside* the band `(12.8, 128.0)` and ESS is monotone in `lam`, so a step
  that solves is a step in band by construction. `157/157` was guaranteed
  before the run.
- **The real reading is the price: 157 steps vs 115 — 1.37×** to the same
  endpoint (`completion` 0.9931 / 0.9926, `goal_dist` `0.0455` for both). Not a
  timeout artifact; genuinely slower to the same place.
- Circular import (`controllers → essps → ab → controllers`) on first wiring;
  fixed by deferring the solver import to call time rather than restating the
  root-find.

## North-star delta

- **First non-zero movement in five cycles** — a runnable controller arm, not a
  doc. `essps_mppi` is in the registry and any existing sweep that takes a
  controller name (`arm_audibility`, `ess_at_goal`, `ab`) can now address it.
- **Time-to-goal regressed 37%** on the one scene measured. That is a north-star
  metric moving the wrong way, and it is recorded as such rather than buried
  under the compliance win.
- Zero existing numbers re-dated: the base hook is a `p.lam` pass-through, so
  D-270/D-271/D-272/D-273 still describe the controller they were measured on.

## Key learnings

- **A guaranteed result read as a win is the same error D-274 just caught**, one
  layer up. The cheapest version of this cycle reports `157/157` and stops; it
  took one extra run to learn the arm is slower. `ArmComparison` now splits
  `holds_band` from `time_to_goal_ratio` so the collapse is not available.
- **Counts lie when episode lengths differ.** `157 > 69` is true for the wrong
  reason — a worse arm that merely ran longer would also "win". The comparison
  is on rates, pinned by a synthetic counter-case.
- **STATE's top priority was stale** (Q-155 resolved two days earlier). PLAN
  should verify a Q's Status before ranking it, not trust STATE's copy.
- Naming the fork (Q-156 (c)) cost ~15 LOC and bought the whole comparison
  without the re-measurement debt option (a) would have triggered.

## Recommended next 1–3 priorities

1. **Q-157 — price the 1.37×**: add min-clearance / near-miss to `compare_arms`.
   No new runs beyond the two already scripted; cheapest possible falsifier.
2. **Seed ensemble on both arms** (D-019's ~5× per-seed ESS spread makes the
   single-seed step count weak evidence).
3. Wire `queue_debt` into the gate-1 snippet + escalation message (carried).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: `eval/mppi_sandbox/controllers/essps_mppi.py`,
  `eval/mppi_sandbox/controllers/__init__.py`,
  `eval/mppi_sandbox/controllers/stock_mppi.py`,
  `eval/mppi_sandbox/essps.py`,
  `eval/mppi_sandbox/tests/test_essps_mppi.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
