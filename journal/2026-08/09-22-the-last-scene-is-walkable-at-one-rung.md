# The last eligible scene is walkable after all — at one rung

- **Cycle**: 2026-08-09 22:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-calibrate `cafe_obstacle_crossing_v0` at `w ∈ {150, 250}`
- **Phase**: P5
- **Status**: keep

## What I tried

- Spent the `calibrate_lam` run that D-161's two `UNCALIBRATED` rungs ask for:
  `cafe_obstacle_crossing_v0` only, both arms, `w ∈ {150, 250}`, 8-rung ladder
  × 8 seeds = **256 runs** (~9 min), one file per weight.
- Joined each into the existing one-scene table with D-146's `merge_tables`
  (2 → 4 cells at both weights). No matrix re-walk, no hand edit.
- Re-read `scene_transplant.crossing_screen`, `lam_window_index.coverage` and
  `lam_window_key.seed_census` off the widened tables, and updated the four
  places whose prose stated the pre-measurement reading.

## What worked / what failed

- 🟢 **D-161's `0/4` was two refusals and two blanks, and one blank moved.**
  At `w = 250` both arms come back `[0.4, 0.8]` — the band's own λ = 0.8 is
  admissible on both — so the screen is `PARTIAL_TRANSPLANT` **1/4** and the
  walkable-scene population closes at **3**, not 2.
- 🟢 **The two unmeasured rungs did not come back alike**, which is why buying
  both was worth more than buying the cheap one. `w = 150`'s stock arm has no
  admissible λ at all, even after the bisection refine widened its ladder 8 →
  10 rungs: `NO_ADMISSIBLE_LAM`. Measuring an unknown can produce a *known
  irreparable* refusal, not just a walkable rung.
- 🟢 **The 8-seed caveat bit for the first time, for free.** The merge widened
  the `w = 150` seed census from 2 compared cells to 4, and crossing/risk drew
  the census's first non-`WINDOW_HELD` grade: `WINDOW_SHIFTED`, 8 seeds
  `[0.4, 0.8]` vs the 16-seed hand walk's `[0.8]`. The **cheap** measurement
  reports the **wider** window — λ = 0.4 clears 8 seeds and fails 16.
- 🔴 **Buying the cells killed D-149's `absent` witness.** The shipped `w = 150`
  table was the only artifact producing a non-empty `absent`; after the merge
  no shipped table does. Reconstructed rather than deleted — the tests now
  render a crossing-free one-scene table through `calibrate_lam`'s own
  loader/renderer and pin the defect there.
- 🟡 Seven existing tests failed on the new tables. All seven pinned the
  pre-measurement reading and all seven were rewritten to the measured one;
  none were deleted or loosened. `UNCALIBRATED` stays reachable through convoy,
  which is still uncalibrated at both weights.
- 🟢 **STATE #3's collected-count drift is resolved, and it was not here.** The
  suite reads **2087 passed** where 21:00 reported 2088, and this cycle adds no
  test cases — so the delta was checked rather than assumed. Collecting both
  trees gives **2246 each**, differing by exactly one rename
  (`…cannot_be_walked_at_all` → `…is_walkable_at_exactly_one_rung`). This run
  reconciles exactly: 2087 + 158 skipped + 1 xfailed = 2246. The previous
  headline, 2088 + 158 + 1 = 2247, is **one more than its own tree collects**
  (the skip count is 157 slow + 1), so the off-by-one is in the 21:00 quote,
  not in this tree.

## North-star delta

- **First non-hygiene cycle in four**, and it moves a real number: the
  successor question's walkable population 2 → **3**, with a named operating
  point (`w = 250`, λ = 0.8, margin 0.30) where 64 runs would be admissible.
- No controller, representation or cost-critic code was written, and the safety
  headline is untouched: `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000**. Walkable is a statement about admissible
  temperature, not about two-sidedness — it buys the right to spend the runs.
- The project's standing 8-seed caveat has its first counter-example, so every
  table-derived window is now known to be permissive on at least one cell.

## Key learnings

- **An `UNCALIBRATED` row is not evidence and must not be summed with
  refusals.** D-161 read 2 + 2 as 4 and published a population conclusion from
  it. The verdict's own docstring said not to; the count is what lost the
  distinction, and a census that reports "0/4" without its `blocked` reasons
  will lose it again.
- **`WINDOW_HELD` everywhere was consistent with never having asked a cell that
  could disagree.** One disagreement is worth more than twenty agreements here,
  and it arrived by widening the denominator rather than by re-measuring.
- **A guard's last artifact can be bought away by a good change.** Reconstruct
  the witness in the test rather than deleting the guard — otherwise the repo
  improves and the check that would catch the regression quietly becomes prose.

## Recommended next 1–3 priorities

1. **Walk `cafe_obstacle_crossing_v0` at `w = 250`, λ = 0.8, both arms, margin
   0.30, seeds 0–31** — the run this cycle bought the right to spend, and the
   third scene's first entry into the two-sidedness census.
2. **Re-measure the `w = 250` crossing cell at 16 seeds** before leaning on it —
   the one cell where 8 and 16 seeds have both been walked now disagrees, and
   the transplant rests on an 8-seed row (agreeing rung 0.8, disagreeing 0.4).
3. **Teach the wall-clock advisory to name the suite cost it implies** — carried
   from STATE #2, still unaddressed; ~16 of 35 budgeted minutes are one suite.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/scenarios/variants/lam_windows_w150.yaml`, `eval/scenarios/variants/lam_windows_w250.yaml`, `eval/mppi_sandbox/scene_transplant.py`, `eval/mppi_sandbox/margin_placement.py`, `eval/mppi_sandbox/tests/test_scene_transplant.py`, `eval/mppi_sandbox/tests/test_lam_window_index.py`, `eval/mppi_sandbox/tests/test_lam_window_seed_count.py`, `docs/decisions.md`
- TSV row appended: yes
