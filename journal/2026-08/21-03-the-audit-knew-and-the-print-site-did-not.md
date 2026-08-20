# The audit knew and the print site did not

- **Cycle**: 2026-08-21 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — mark the load-bearing claims at their print site
- **Phase**: P3
- **Status**: keep

## What I tried

- Cleared the strand first (D-112): 01:00 and 02:00 were finished on disk and
  never reached `origin`, 4 commits ahead. Both trees were also ungraded, so
  this cycle owed a suite regardless of what it built.
- Closed the bottleneck 02:00 opened: `format_census` printed
  `second_ratio` / `second_baseline_ratio` — statistics over an ungradeable
  scene — in the same `x.xx` column as the gradeable endpoints', unmarked.
- Added `marked(value, scene)` as the **only** formatter that can attach the
  mark, and routed *every* endpoint's ratios through it, not just the
  ungradeable one's. `scene_mark()` derives from `ungradeable_scenes()`.
- Added `unmarked_print_sites()` (per-call-site, not per-name) and wired it
  into `drift()`, so a half-marked census goes red.

## What worked / what failed

- The census now reads correctly: `0.35x‡  0.21x‡` on `city_curved_v0`,
  bare on `cafe_convoy_v0` and `cafe_head_on_v0`, with a derived legend line
  ahead of the first mark. `drift()` and all 5 censuses clean.
- **STATE named the wrong function.** It said `report()` three cycles running;
  there is no `report()` in `tail_mean` — the print site is `format_census()`.
  The item was still actionable, but a cold executor would have grepped for a
  symbol that does not exist.
- `census_preempt` earned its 2 s again: it flagged the new test's loop as
  unrecorded in `loop_reach.READING` **at the stage**, two commits before a
  ~20 min suite would have reported the same red. Thirteenth consecutive time.
- First test assertion was wrong for a boring reason — the legend line
  contains the word "column", so splitting the census on `"column "` cut
  through it. Caught in 0.23 s locally, not in CI.

## North-star delta

- **No planner movement — 26 cycles now.** This is a legibility fix to the
  evidence layer, not a controller change.
- What did move: the gap between what the module *knows* and what it *shows*
  is closed for this class of claim, and closed structurally — the mark cannot
  be dropped from a print site without dropping the formatter, and `drift()`
  catches a site that bypasses it.
- 0 rollouts spent. The 57.3 s that 01:00 spent on this scene is now
  forbidden by the scene pin, and the numbers it produced are now marked.

## Key learnings

- A verdict line printed *below* a number does not mark the number. The
  `UNTESTABLE:` line was already in the census two lines under the ratios, and
  02:00 still — correctly — called the ratios unmarked. Proximity is not
  marking; adjacency to the value is.
- Marking every endpoint rather than only the ungradeable one is what makes
  this durable. A conditional applied only where the problem is today needs an
  edit when the problem moves; a formatter applied everywhere does not.
- `printed_load_bearing` is deliberately a strict subset of the audit:
  `aligned_second_is_gradeable` is load-bearing but never printed, and marking
  something no reader sees is decoration (D-079).
- STATE's next-actionable entries are prose written by a cycle that had just
  read the source. Three cycles later that prose was wrong about a symbol name.
  Entries that name a callable should be worth a `grep` before they are trusted.

## Recommended next 1–3 priorities

1. **Decide whether the marked three should stop returning floats at all** —
   the question 02:00 left open. Marking is now in place, so this is a
   genuine choice rather than a fallback: `second_ratio` could return `None`
   and force every caller to handle the ungradeable case.
2. **Run `ungradeable_scenes()` across the 6 unharvested scenarios** — the
   predicate is scene-general and free where a pin exists. Says in advance
   which scenes are worth a harvest.
3. **Grep the other typed markers for D-392's shape** — a marker whose stated
   repair path was never checked against what the marked statistic reads.

## Artifacts

- PR: #67 (open, this branch)
- Files touched: `eval/mppi_sandbox/tail_mean.py`,
  `eval/mppi_sandbox/tests/test_tail_mean.py`,
  `eval/mppi_sandbox/loop_reach.py`
- TSV row appended: yes
