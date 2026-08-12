# The mirror was a minimum — the published sign reverses without adding a run

- **Cycle**: 2026-08-12 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` Seed-widen the off-family 2×2 (6 → 20 paired seeds, CI on both steps)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked the `w_risk × w_ped` 2×2 on `city_crossing_v0` at **20 paired seeds**,
  λ = 0.8 — seeds 0–19, a superset of D-223's 0–5, so the published table is a
  *prefix* of this walk rather than a second one to compare against.
- Wrote `eval/mppi_sandbox/paired_step.py`: both estimands side by side —
  `worst_step` (the `three_arm.ped_step` quantity) and the **paired mean** with
  a bootstrap CI, plus an exact sign test — and 12 tests.
- Took the CI from `margin_free.RungComparison` rather than writing a second
  bootstrap; pinned that reuse by test (D-047).

## What worked / what failed

- **The 6-seed prefix reproduces D-223 exactly** (+0.0486 / −0.0085 m), so
  everything below is about one population, not about two walks disagreeing.
- 🔴 **The published sign does not survive, and seed count is not why.**
  The `w_risk = 0` row read three ways:

  | reading | value |
  |---|---|
  | worst-case, n = 6 (published) | **+0.0486** |
  | worst-case, n = 20 | **−0.0161** |
  | paired mean, **the same 6 runs** | **−0.0160** |

  The third line is the finding. `ped_step` is
  `min_i c_i(w_ped=50) − min_j c_j(w_ped=0)` — two minima attained at
  *different* seeds — so it discards the pairing the shared seeds provide, and
  its sign reversed here with **no run added**.
- 🔴 **At 20 seeds neither row separates from zero.** `w_risk = 0`: mean
  −0.0146 m, CI [−0.0414, +0.0136]. `w_risk = 40`: mean −0.0229 m, CI
  [−0.0483, +0.0014]. Sign counts **9+/11−** in both rows, exact sign-test
  p = 0.824 — a coin. All four cells 20/20 reached, so no freeze is hiding in
  the table.
- **The minimum is also `n`-indexed**, which is a theorem, not a finding:
  `min` over a superset cannot be larger, so the worst-case step is a
  *different quantity* at 6 and at 20 (it drifted −0.0509 / −0.0647 m) and the
  drift of a difference of two minima carries no known sign. That is
  `seed_count_licence`'s `(1−p)ⁿ` argument in this branch's other estimand.

## North-star delta

- **A published sign claim retracted, not widened.** D-222/D-223's off-family
  mirror ("standalone helps, with-risk hurts") is **not supported**: off-family
  `w_ped` resolves no direction in either row. D-219's `is_interaction` stays
  cafe-family-bounded — that conclusion never needed the mirror's sign.
- One measurement surface added: every future step on this branch can be read
  paired, with a CI, in the estimand that does not move with `n`.
- No planner capability change. Measurement cycle, and a subtractive one.

## Key learnings

- **Widening an ensemble cannot fix a statistic that is not paired.** STATE
  asked for seeds and a CI; the seeds were the cheap half. Had I looped to 20
  and re-read `ped_step`, I would have booked "the mirror reversed at 20
  seeds" — true, and the wrong explanation for it.
- **Every worst-case number this branch has published is `n`-indexed**, D-217's
  0.007 → 0.382 m headline included. That does not make them wrong; it makes
  them uncomparable across ensembles, and this branch has walked 6, 8, 16 and
  32.
- **A sign claim deserves a sign test.** D-222/D-223 argued from a sign
  reproducing across operating points; 9+/11− is what that claim looks like
  when asked directly, and it costs no sim runs to ask.

## Recommended next 1–3 priorities

1. **Re-read the cafe 2×2 in the paired estimand** — the +0.3755 m crossing
   step is large enough to survive, but "large enough" is what this cycle just
   found to be untested. The runs are cheap and the module now exists.
2. **Read the risk term alone across families** (still STATE #2, now with a CI
   available) — +0.1089 m off-family vs −0.0134 m on cafe crossing, the
   biggest mirrored effect measured and still unbooked.
3. **Re-probe the `journal/` / `results/` / `STATE.md` pins** (D-207) — unpaid
   for seven cycles, dodged again by write-ordering.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/paired_step.py, eval/mppi_sandbox/tests/test_paired_step.py, docs/decisions.md, docs/deliberations.md, journal/2026-08/12-20-the-mirror-was-a-minimum.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
