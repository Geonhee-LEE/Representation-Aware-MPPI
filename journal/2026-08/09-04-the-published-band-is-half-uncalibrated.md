# The published band is half uncalibrated — and the uncertified rung is the one holding the claim up

- **Cycle**: 2026-08-09 04:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — wire one real sweep driver to `assert_span_certified`
- **Phase**: P3 (calendar P5; the branch's thrust is still the P3 uncertainty axis)
- **Status**: keep

## What I tried

- D-147 shipped `certify_span` / `assert_span_certified` and its own journal
  named the gap: **nothing calls them**. Every `ScorableBand` in the repo is a
  test fixture, so the guard had never been shown a band the project publishes.
- Went looking for the "sweep driver" STATE #1 asked me to wire and found there
  isn't one. `scorable_band` has **zero non-test importers**, and the one band
  the project actually publishes — D-133's eight-rung walk on `cafe_head_on_v0`
  — lives only as a prose table in the module's own docstring.
- So the deliverable became the missing input rather than a missing call site:
  `published_band()` reconstructs that walk as an object, and the certification
  is run against it.
- No closed-loop runs. The preceding cycle graded `PUBLISHED` at 43m02 against
  a 35m budget with the whole overrun in one avoidable suite run, so scope was
  cut to pure code + tests and the suite was run once.

## What worked / what failed

- 🟢 **The guard's first non-fixture input does not come back clean.** Tables
  exist at `w ∈ {10, 75, 100}`; the published span runs `[75, 250]`. Two of its
  four scorable rungs — **150 and 250** — sit at weights no calibration speaks
  at. Verdict `SPAN_UNCALIBRATED`, `2/4` certified. `require_calibration=True`
  raises on it.
- 🔴 **The finding is sharper than a coverage gap.** `w = 250` carries two
  independent weaknesses simultaneously: its `SEPARATED` verdict is bought by
  **one run out of sixteen** with the sign *against* the mechanism (already
  known — `one_run_rungs`), and it is **uncalibrated** (new). It is also the
  sole reason the band grades `BAND_SPLIT` rather than `BAND_CLOSED`. So the
  walk's one structural claim about the *shape* of the scorable set rests
  entirely on its weakest rung, and a test pins that by deleting the rung and
  watching the verdict change.
- 🟢 **`SPAN_UNCALIBRATED` and not `SPAN_UNCERTIFIED`, which is D-147's split
  earning itself.** Nothing contradicts λ = 0.8 at 150/250; nobody has looked.
  Had the split not existed this would have read as a defect in the published
  band, and the honest reading is a hole in the calibration coverage.
- 🟢 **The reconstruction is falsifiable rather than trusted.** The record is a
  table of unsafe *rates*, and a rate does not determine clearances — so the
  rebuild is graded against the verdict column D-133 wrote down, rung by rung,
  plus the four structural claims the docstring makes (`BAND_SPLIT`, span
  `[75, 250]`, one-run rung `250`, one-sided refusal at `30`). A filler that
  got a count wrong moves a verdict and fails. This is D-139's rule — only a
  cell whose answer is already written down can test the thing generating it.
- 🟡 **The filler had to refuse magnitudes, not supply them.** First cut put
  the unsafe seeds just below the margin, which is the obvious choice and is
  wrong: `sub_margin` then reads `True` across the whole band — a live D-124
  claim this walk never made. `mean_clearance` / `sub_margin` now **raise**
  (`UnreconstructedMagnitude`, an `AttributeError` so `hasattr` probing
  degrades cleanly), with `±inf` sentinels as a second layer so any magnitude
  escaping the refusal is non-physical rather than believable. The failure mode
  being blocked is a *plausible* number, not a missing one.
- 🔴 **The suite went red on the first full run, and the guard that caught it
  was right.** `loop_reach`'s registry test failed: the new arm-naming test is
  a *population-claim loop*, and this repo refuses to accept one without a
  runtime reading of how many elements it actually checked (a green loop over
  an empty sequence establishes nothing). Took the reading — `SAMPLED n = 8`,
  the whole ladder — and registered it. The reflex to reach for was rewriting
  the loop as a set comprehension to dodge the guard; the reading is 90 s and
  the question it asks about my test is the correct one.
- 🟡 **Cost of that: a second full suite run, and the cycle ran long.** The
  D-043 ordering was followed and still cost 15 min extra, because the guard
  fires on a *tracked code* edit rather than on a doc write — the class of
  movement the 4a-ter re-run is positioned for. Nothing in the current ordering
  prevents this; a registry edit discovered by the full suite is always a
  second full suite. The cheap defence is running `loop_reach report` in Phase 3
  whenever a new test contains a loop-body assert, which is a ~90 s check, not
  a 15 min one.
- 🟢 The one-sided ESS refusal at `w = 30` survives the round trip:
  `sole_refuser == "stock_mppi"`, so the *baseline* left the band while the
  mechanism arm held it — a statement about this temperature's suitability as a
  shared operating point, not a bound on the mechanism.

## North-star delta

- No safety/tracking numbers moved. `unsafe_rate` **0.0000** / `min_clearance`
  **0.3579** / `success_rate` **1.0000** still stand where D-136 left them.
- What moved is the **standing of the band-width claim**, and it moved *down*:
  "the band is three rungs wide, not one" is now known to be published across a
  weight range that is half uncalibrated, with its shape claim resting on a
  one-run uncalibrated rung. That is a retraction-shaped result, and it is the
  first one the λ guard has produced against a published object.
- The guard itself moved from *available* to *load-bearing*: it has a real
  input, and that input fails it.

## Key learnings

- **"Wire a driver to the guard" can be the wrong shape of task when the guard
  has no data to eat.** The gap was not an uncalled function, it was that the
  published band was prose. Building the input found a defect; building another
  call site would have found nothing.
- **A reconstruction should refuse the quantities it cannot reconstruct.** The
  tempting move is to fill clearances plausibly and note the caveat in a
  docstring; the caveat then rides every downstream read. Raising is cheaper
  than remembering, and it converted a silent false `sub_margin` into a stack
  trace at the exact line that read it.
- **Two weaknesses on the same rung compound rather than add.** `250` was
  already flagged one-run and is now also uncalibrated; neither alone would
  justify revisiting the band's verdict, and together they mean the structural
  claim has no support at all.
- The affordability argument D-147 made for `require_calibration` defaulting
  off is confirmed empirically: the project's *own* flagship band fails it.

## Recommended next 1–3 priorities

1. **Calibrate `cafe_head_on_v0` at `w = 150`** — the cheapest way to convert
   this finding into a certified span. One scene × two arms × 8 rungs × 8 seeds
   ≈ 128 runs, ~6 min, and it retires the larger half of the uncalibrated pair
   (150 is inside the contiguous island; 250 is the detached one-run rung).
2. **Re-walk `w = 250` at 16 seeds, or drop it from the published band** — the
   `BAND_SPLIT` verdict should not rest on one run at an uncalibrated weight.
   Either measurement settles it; leaving it is the only bad option.
3. **Walk `gap_gated_mppi` at `w = 75`** — unchanged from last cycle, gives
   D-146's new column its first weight contrast and widens `COMPARED_ARMS` to
   three. ~512 runs, ~6 min.

## Suite

**1926 passed** (158 skipped, 1 xfailed, rc=0). 1912 → 1926, exactly the 14
tests added. Receipt-gated (`push_preflight record`), `tree_provenance verify`
clean at `5d018a06`, `declared` clean. Two full runs: the first was red on the
`loop_reach` registry and its count is not quoted anywhere.

## Artifacts

- PR: #67 (open, continuing per D-140)
- Files touched: `eval/mppi_sandbox/scorable_band.py`,
  `eval/mppi_sandbox/tests/test_published_band.py`, `docs/decisions.md`
- TSV row appended: yes
