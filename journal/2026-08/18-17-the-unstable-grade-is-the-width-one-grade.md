# The unstable grade is the width-1 grade — `freezing` was never the fragile scene

- **Cycle**: 2026-08-18 17:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — ask why `freezing` alone is seed-unstable
- **Phase**: P3
- **Status**: keep

## What I tried

- The bottleneck's own question, carried unshipped three cycles, at zero
  rollout cost against the tables D-344 recorded: why does `freezing` alone
  move grade under a seed doubling?
- Read the **evidence base** underneath the census rather than the census —
  `nonconstant_cell_margins(tables)` returns every `(scene, observable, policy,
  margin)` informative cell as one population, thinnest first, and
  `evidence_widths` groups it per scene.
- Deliberately **no** set difference or intersection in module code: the cells
  the doubling removed are the reader's subtraction of two value-pinned tuples.
  D-344 already paid for the other choice (guard entrant 123, thirteen red pins).

## What worked / what failed

- **The question presupposed the wrong subject.** Widths at 8 seeds are
  `freezing 1`, `head_on 4`, and `0` for the other three. The doubling deleted
  **one cell from each** of the two non-empty scenes — equal losses. Only the
  width-1 grade moved. `freezing` is not more fragile than `head_on`; it is the
  scene whose verdict rested on a single cell.
- **Three of the four "stable" verdicts are vacuously stable.** `cut_in`,
  `convoy`, `obstacle_crossing` have width 0 at both counts, so the 4/5-stable
  census reads as four independent confirmations when only one grade was ever
  at risk of moving.
- **The obvious hypothesis is refuted by the ranked table.** "Thinnest margin
  dies first" is wrong: rank 1 (`head_on`/`closing_speed`@first_detection,
  `+0.0228` — also the one D-343 found survives all 40 deletions) still
  separates at 16 (`+0.0196`), while ranks 2 and 3 (`+0.0390`, `+0.0458`) both
  go negative (`-0.0125`, `-0.0373`).
- **The two lost cells are the whole TTC family.** `min_ttc` and `ttc` are the
  only two time-to-collision observables measured and are exactly the two
  deleted; `closing_speed` / `lateralness` survive everywhere they held. Pinned
  as a coincidence, not as a mechanism — the tail-of-a-ratio reading is a
  hypothesis this cycle does not verify.

## North-star delta

- No planner movement — this is representation *diagnostics*, and honestly so.
- What moved is the standard of evidence for every visibility claim this branch
  has made since D-341: a grade now reports the width of its own support, so
  "the census is stable" can no longer be quoted without the column that says
  how much of that stability was earned.

## Key learnings

- **A stable verdict census is not a stable evidence base.** D-344 found a
  stable *count* over a churning population; this is the same shape one level
  up — stable *verdicts* over an evidence base that lost 2 of its 5 cells.
- **Asking "why is X unstable" presupposes X has a property.** The measurement
  that answered it was a groupby, not a study of X: nothing about `freezing`'s
  geometry entered the answer.
- **Margin is not the fragility coordinate.** The separation rule is pure
  min/max, so what decides survival under resampling is the column's tail, not
  the size of its gap. A cheap next probe would test that directly.

## Recommended next 1–3 priorities

1. Test the TTC-family reading: measure the across-seed spread of `ttc` /
   `min_ttc` vs `closing_speed` / `lateralness` at both counts. If the ratio
   columns are heavy-tailed the mechanism is named, still at zero rollout cost.
2. Audit the remaining composite magnitude pins (carried from 11:00, D-342).
3. Give `UNCOVERED` a standing re-derivation (carried from 16:00, D-345).

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/test_scene_separability.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
