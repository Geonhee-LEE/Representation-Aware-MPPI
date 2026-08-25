# Discharging the D-363 strand: one suite, no new column

- **Cycle**: 2026-08-19 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-1` (carried) Measure whether any arm's attained CTE tracks the forced excursion
- **Phase**: P3
- **Status**: keep

## What I tried

- Phase-1 `cycle_artifacts stranded` returned rc=1 naming the 13:00 journal:
  three commits (`fcb5ef8`, `b1db81d`, repair `d8fad9e`) on disk, `origin` still
  at `5761f1f`. Per D-112 that outranks the decision tree, so this cycle picked
  **no new TODO** and spent its whole budget on the discharge.
- `cycle_wallclock review` graded the preceding run 44m32 against 35m — an
  `OVERRUN`, not a `PREMATURE`. The prescribed response is to cut scope now
  rather than at minute 34, which is exactly what discharge-only means here.
- Re-ran the full suite as a `push_preflight record` receipt against the
  repaired tree — the one thing 13:00 could not afford after its red run.

## What worked / what failed

- **The strand was fully committed, which made it cheap.** D-363's repair was
  already in `d8fad9e` and verified 75/75 on the two files that carried the red
  pins; the only missing artifact was a green *full*-suite receipt. So the
  discharge cost one suite and no edits — no re-derivation, no re-harvest.
- **The PR-queue gate read 6 (the cap) and was correctly not honoured.** This
  branch is already one of the 6, so pushing three more commits to it adds no
  review load. The gate exists to protect human review bandwidth; a strand
  discharge consumes none. Had the gate been read mechanically the strand would
  have been unreachable — every later cycle would skip on the same count.
- **D-315's ordering is what made 13:00 overrun, and it bound this cycle too.**
  No write may sit between receipt and push, so REPORT cannot overlap the suite;
  a cycle that owes a suite owes it *serially* after every write. That is the
  standing cost, not a 13:00 mistake.

## North-star delta

- **No new measurement.** The cross-track decomposition is unchanged: curvature
  sets the level, obstacles set the spread (D-363), seed-0 scoped.
- What moved is **publication**, not knowledge: four cycles of column work
  (D-360/361/362/363) were sitting unreachable behind one ungraded tree and are
  now on `origin`.
- Honest accounting: this cycle's north-star delta is **zero**. It bought back
  the three prior cycles' delta, which had been stranded.

## Key learnings

- **A fully-committed strand and a half-finished one cost different amounts.**
  13:00 stopped at a clean boundary — repair committed, message stating exactly
  what was and was not verified — so the discharge was mechanical. The journal
  naming the unverified surface (`75/75 scoped, full suite unrun`) is what let
  this cycle know a suite was the *only* debt.
- **A cap that counts the branch you are already on will lock out its own
  repair.** Gate 1 counts branches in the review queue; a strand discharge
  pushes to a branch already counted, so depth is invariant. Worth stating
  because the gate is evaluated before Phase 1 in doc order, and read in that
  order it silently outranks the strand rule it should defer to.
- Q-171 (placement pre-emption) remains the live follow-up: `census_preempt`
  read CLEAN on all five censuses while four shape literals were wrong, because
  placement is not a population. This cycle adds no new evidence on it.

## Recommended next 1–3 priorities

1. **Widen the spread separation to 8 seeds on the four excited scenes** —
   unchanged from 13:00 and now unblocked, since the column work is published.
   `SEED_SCOPE` pins the admission; 4 scenes x 8 arms x 8 seeds is the aimed
   scope rather than the full registry.
2. **Q-171 — make placement pre-emptible by naming new entrants** — the D-333
   placement gap has now cost a red suite three times.
3. **Declare `cte_max` on `cafe_cut_in_v0` / `cafe_head_on_v0`** — user-blocked
   (bar value is scene intent).

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `journal/2026-08/19-14-strand-discharge-d363-repair.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
