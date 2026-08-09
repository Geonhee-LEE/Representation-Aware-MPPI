# A derived margin re-finds the published scene and nothing else

- **Cycle**: 2026-08-10 00:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — derive a margin from the recorded clearances and re-grade all three scenes
- **Phase**: P3
- **Status**: keep

## What I tried

- Composed `derived_margin.py` over the **6 walked rungs** of the 3 eligible
  scenes (D-159): head_on `w ∈ {75,100,150,250}`, convoy `w = 75`, crossing
  `w = 250`. Each asked two questions — does a threshold derived from its own
  recorded clearances exist, and does the verdict survive the choice.
- Added the two cross-scene readings no per-scene sweep can see:
  `shared_window` (a threshold two-sided on *every* rung) and
  `declared_placement` (where each scenario yaml's margin sits relative to its
  own derived window).
- Zero sim runs — the 192 per-seed clearances are constants.

## What worked / what failed

- 🔴 **Scene coverage is 1/3 and it is the scene that was already published.**
  `SINGLE_SCENE_STABLE`, rungs **2/6**. Only head_on (`w = 150`: 9 two-sided
  margins, all `REPRODUCED`; `w = 250`: 23, all `REPRODUCED`) yields a
  margin-independent verdict. Convoy and crossing — the two scenes walked
  specifically to widen the evidence base — contribute **zero** between them
  at any threshold their own runs can express. The derived-margin route does
  not enlarge the population; it re-finds head_on.
- 🔴 **No threshold is shared by even two rungs.** The three non-empty windows
  `[0.4194, 0.4437]`, `[0.5467, 0.5938]`, `[0.9712, 1.0906]` are pairwise
  disjoint. `BandSweep` capped arm coverage at 1/4 *within* the band (D-158);
  the same ceiling holds across scenes, and structurally — a margin is a length
  in metres and clearance scale is a **scene** property.
- 🔴 **One direction, no exceptions**: every declared margin that has a derived
  window at all sits **strictly below** it (`BELOW_WINDOW` 3/3, `INSIDE_WINDOW`
  0). The matrix's thresholds are not three unrelated mis-choices — they are
  uniformly on the permissive side.
- 🟢 **A test caught a live bug in my own `shared_window`.** I wrote it to skip
  windowless rungs while its docstring claimed the opposite; skipping *is* the
  vacuous-compatibility it claims to avoid, and would let one windowed rung
  plus five windowless ones report a shared window. Today's census reads `None`
  either way only because the three windows happen to be disjoint — the
  headline was right by accident. Now `None` by construction.
- 🟢 **And caught a false claim in shipped D-158 prose.** `margin_sweep`'s
  docstring justifies the "not a safety claim" caveat with "at that threshold
  most runs of *both* arms count as unsafe". Measured: at `w = 250`'s window
  `stock_mppi` is 11/32 and `risk_mppi` **3/32**; at `w = 150`, 19/32 against
  **2/32**. Neither rung has a majority-unsafe risk arm anywhere. Two-sidedness
  needs the arms *interior*, which is far weaker. Corrected at the source; the
  caveat survives on the threshold being **undeclared**, not on the runs.

- 🟡 **Process error, mine, recorded rather than smoothed**: I sent the 72h PR-queue
  escalation at **71.6h** (last 2026-08-07 00:54, sent 2026-08-10 00:29) after
  asserting ">72h eligible" from an *estimated* elapsed time. STATE had the
  correct next-eligible time (00:54) written down. This is D-154's lesson one
  layer out: the same inflated self-timing that corrupts TSV stamps also
  corrupts cooldown arithmetic, and the fix is the same — read the clock, do
  not estimate it. Harmless here (one message, 25 min early); noted because the
  cooldown exists to protect the user's attention.

## North-star delta

- **No movement, and this cycle argues the current instrument cannot produce
  any.** Headline `unsafe_rate` **0.0000** / `min_clearance` **0.3579** /
  `success_rate` **1.0000** unchanged. No controller or representation code.
- What it does close: the "wrong threshold" hypothesis. Declared margins are
  censored *and* derived margins re-find one scene, so the branch's premise
  needs a different **measurement**, not a different threshold.

## Key learnings

- **"Re-gradable" now has a third failure mode.** D-164 showed re-gradable ≠
  re-grades to an answer. This adds: re-grades to an answer ≠ *adds a scene*.
  Both stable verdicts sit on the scene that was already published.
- **A vacuity-skip flatters an intersection.** Excluding a no-window rung from
  a shared-threshold computation makes the census *more* confident the more
  scenes admit no threshold — the same shape as D-107's empty-population read.
- **Docstring magnitudes are inside the verification surface too.** D-158's
  wrong 'both arms mostly unsafe' survived because no test computed it. The
  correction cost one assertion.

## Recommended next 1–3 priorities

1. **Run the feed's one-variable ablation (2607.16591)** — a plain min-lidar
   term in the same cost slot as the epistemic term, same scenes/seeds. Now
   the strongest candidate: the margin route is closed in both directions.
2. **Re-measure the `w = 250` crossing cell at 16 seeds** — carried from D-163.
3. **Make `sandbox:pass=N` state passed vs executed** — carried three cycles.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/derived_margin.py, eval/mppi_sandbox/tests/test_derived_margin.py, eval/mppi_sandbox/margin_sweep.py, docs/decisions.md
- TSV row appended: yes
