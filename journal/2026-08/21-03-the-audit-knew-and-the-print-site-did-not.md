# The audit knew and the print site did not

- **Cycle**: 2026-08-21 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE next-actionable #1 — mark the load-bearing claims at their print site
- **Phase**: P3
- **Status**: in_progress — work is committed and locally green, but the tree
  is **ungraded and unpushed**. The push gate refused (`STALE`), correctly.

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

## The suite came back red, and it was not mine (D-395)

- `3948 passed, 1 failed` — `test_key_discrimination::test_the_narrow_key_narrows_but_does_not_separate`,
  on a composition pin: `(18, 13)` expected, `(19, 14)` read.
- **Measured on both sides before touching it**, in a throwaway worktree:
  the last *pushed* commit `3e7ef18` reads `(18, 13)`; `b0f043f` — the end of
  the **01:00** cycle — already reads `(19, 14)`, same names. So 01:00 moved
  the census, 01:00 and 02:00 both ended stranded and ungraded, and this cycle
  inherited a red it did not cause by being the first to buy a suite.
- The test's own comment predicted this in the D-381 paragraph, about the
  D-380 strand. **It has now happened twice, for the same reason.**
- Verdict unmoved (`narrowing` 3.79 > 2.0, `discrimination` 0.152 < margin
  0.25), so it is an ordinary join: the pin moves and no rung does. Repaired,
  and the 16-test file passes in 223 s.
- **Cost of that repair: the receipt.** The pin lives in a test file, so the
  tree moved and `push_preflight check` returned `STALE`. A second suite is
  ~22 min and the clock was already `SUITE_UNAFFORDABLE`, so this cycle ends
  unpushed too — a third strand. That is the honest outcome, not a good one.

## A latent defect found by exercising the new detector

- Called `unmarked_print_sites()` on all three scenes rather than just the
  default. On the **gradeable** ones it returns findings — `baseline_ratio: 1
  of 3 bare`, `third_paired: 1 of 1 bare` — which are false: a gradeable scene
  needs no marks, so bare is correct there.
- And `drift()` only ever calls it with the default `SECOND_SCENE`. That is
  right *today* because that is the only ungradeable scene, but if
  `cafe_convoy_v0` ever flattens, `marked()` would start marking it (correctly,
  since `scene_mark` is derived) while `drift()` would never check it.
- Not fixed this cycle: the receipt suite was already in flight when this
  surfaced, and touching the tree would have invalidated it (D-315). Filed P0.

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

0. **Push this branch and re-run the suite.** Three cycles of finished work now
   sit on disk (01:00, 02:00, 03:00). D-395 is the measured price of letting
   that happen twice; a fourth strand pays it again. The tree is locally green
   — the one red is repaired — but green-by-argument is not a receipt.
1. **Fix `unmarked_print_sites()` on gradeable scenes + make `drift()` iterate
   `ungradeable_scenes()`** (P0, filed) — false findings today, a blind spot
   tomorrow.
2. **Decide whether the marked three should stop returning floats at all** —
   the question 02:00 left open. Marking is now in place, so this is a
   genuine choice rather than a fallback: `second_ratio` could return `None`
   and force every caller to handle the ungradeable case.
3. **Grep `second_ratio` for module-external callers** — the measurement
   Q-176 needs before the float-vs-`None` decision.

## Artifacts

- PR: #67 (open, this branch) — **nothing pushed this cycle; gate refused STALE**
- Files touched: `eval/mppi_sandbox/tail_mean.py`,
  `eval/mppi_sandbox/tests/test_tail_mean.py`,
  `eval/mppi_sandbox/loop_reach.py`,
  `eval/mppi_sandbox/tests/test_key_discrimination.py`
- TSV row appended: yes
