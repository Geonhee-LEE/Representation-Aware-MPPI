# The detector graded scenes that needed no mark

- **Cycle**: 2026-08-21 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — fix `unmarked_print_sites()` + `drift()`
- **Phase**: P3
- **Status**: keep

## What I tried

- Split `unmarked_print_sites()` into a **precondition** and a **scan**. The
  scan is now `bare_print_sites(scene)` — the old body, unchanged. The
  precondition is one line: a scene whose `scene_mark()` is `""` has no marks
  to have dropped, so it returns `()` before scanning.
- Made `drift()` iterate `ungradeable_scenes()` instead of asking
  `unmarked_print_sites()` with its default argument, so the guard's population
  is the same one the mark is derived from.
- Two tests. One pins that both gradeable scenes report `()` **while
  `bare_print_sites` on them is non-empty** — the empty tuple has to be
  provably the precondition talking. One pins the loop in `drift()`'s source
  and that `unmarked_print_sites()` (no argument) appears nowhere in it.
- Registered the new loop-body reading in `loop_reach.READING` at a
  **measured** `(SAMPLED, 2)`, taken with the D-305 file-scoped `run(paths=...)`.

## What worked / what failed

- **The defect was larger than STATE described and in the same direction.**
  STATE named one false finding (`baseline_ratio: 1 of 3 bare` on
  `cafe_convoy_v0`). Measured before touching anything: **5** false findings on
  `cafe_convoy_v0` and **2** on `cafe_head_on_v0` — `baseline_ratio`,
  `distinct_arms`, `max_floor`, `p95_floor`, `real_gap`, `column_licensed`,
  `third_paired`. All seven are correct code being reported as defective.
- **`drift()` was green only by coincidence, and that is the more serious
  half.** The guard asked about exactly one scene — the default argument — and
  that scene happened to be the ungradeable one, so seven false findings sat in
  a function whose whole job is to surface findings and none of them reached
  it. Had the default pointed anywhere else, `drift()` would have been red on
  fictional defects for as long as the argument stayed put.
- The D-388 trap did not fire: `unprobed_revocable()` is still `()` and
  `tail_mean.drift` did not enter `revocable_collections()`. A plain `for` over
  a pinned tuple is not difference-shaped, unlike the set-difference clause that
  cost 12 tests three cycles ago. Checked rather than assumed.
- `census_preempt` earned its 2 s a **seventh** consecutive cycle: the new test
  was unrecorded in `loop_reach.READING`, caught at the stage instead of
  thirteen minutes into a suite.
- The wall-clock reading went `SUITE_UNAFFORDABLE` at 9m56, before the writes.
  Scope was frozen there — no Q-176 grep, no second thrust — because the last
  four cycles establish that a cycle which does not push bills the next one.

## North-star delta

- **Zero planner movement, 28 cycles.** No controller, no scenario, no rollout.
- What moved is a guard's honesty: seven of the branch's bare-print findings
  were fictional, and the one guard positioned to say so was asking about a
  single hard-coded scene. Both are now derived from the same pin.
- The subtraction is real but small: the branch has one fewer instrument that
  reports defects that are not there.

## Key learnings

- **A detector needs its precondition and its scan to fail distinguishably.**
  Both return `()`. D-394 already paid for exactly this — an empty population
  reading like a clean one — and the fix would have re-created it one frame
  over if the two had stayed in one function. The test asserts
  `bare_print_sites(scene)` is *non-empty* on the scenes the precondition
  short-circuits; that assertion is the whole guarantee.
- **A guard that takes a default argument is pinned to whatever was true the
  day it was written.** `scene_mark` was carefully derived so a scene gains and
  loses its mark on one event; `drift()` then read it through a constant. The
  derivation was undone at the call site, which is not a place anyone looks.
- Green does not mean checked. `drift()` returned `()` for three cycles across
  a defect it structurally could not see.

## Recommended next 1–3 priorities

1. **Grep `second_ratio` / `second_baseline_ratio` for module-external
   callers** — the free measurement Q-176 says to take before the
   float-vs-`None` decision. Converts an open trade-off into a priced one.
2. **branch-scope decision (user)** — 28 cycles, zero planner change. This
   cycle again found a real defect in the branch's own instrumentation.
3. **Merge or close PRs #66–#69** (user) — 41 days without a merge.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/tail_mean.py`, `eval/mppi_sandbox/loop_reach.py`, `eval/mppi_sandbox/tests/test_tail_mean.py`
- TSV row appended: yes
