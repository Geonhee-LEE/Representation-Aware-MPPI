# The span's uncalibrated half is bought — and the table that buys it catches the census inventing a comparison

- **Cycle**: 2026-08-09 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — calibrate `cafe_head_on_v0` at `w = 150`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `cafe_head_on_v0` at `--w-obs-soft 150` — 1 scene × 2 arms × 8 rungs ×
  8 seeds = **128 runs**, ~4 min — into
  `eval/scenarios/variants/lam_windows_w150.yaml`, and registered it in
  `lam_window_index.TABLES`. Same ladder / seed count / generator as the
  `w ∈ {10, 75, 100}` tables, so the weight is the only thing that moved.
- Scope was deliberately **one scene, not the matrix**: `w = 150` was wanted
  because the published span runs through it on that scene, and the full walk
  is 1024 runs / ~15 min against a cycle that was already told it overran.
- Re-read `certify_span(published_band())` and `seed_census` off the new table.
- Fixed the defect the second read exposed, and pinned it with four tests.

## What worked / what failed

- 🟢 **The published span's larger gap closes, and the measurement was free to
  refuse it.** Both head_on arms read `[0.2, 0.4, 0.8]` at `w = 150`, so
  λ = 0.8 — the temperature D-133's walk was taken at — is in-band and the rung
  certifies. `certified` goes `(75, 100)` → **`(75, 100, 150)`**, 3 of 4. This
  could have gone the other way: D-142 moved 6 of 14 arm-cells between `w = 10`
  and `w = 75`, and a shifted head_on arm would have made this a retraction of
  a rung the project publishes.
- 🟢 **The 8-seed caveat is priced at a second weight, not just a second cell.**
  The table reproduces D-136's 16-seed hand walk **exactly** (set equality, both
  arms) at a different margin (0.40 vs 0.30). D-145 priced the caveat at
  `w = 100`; one pair could not separate "8 seeds suffice" from "8 seeds suffice
  at `w = 100`". Two pairs across a 1.5× weight move can.
- 🔴 **And the new table made `seed_census` fabricate a comparison.**
  `REMEASURED` holds two cells at `w = 150` — head_on, which this table walked,
  and crossing, which it did not. `Remeasurement.recorded` resolves through
  `lookup`, which returns an empty `admissible` for a **missing** cell exactly
  as for a measured-and-windowless one; `window_shift` reads an empty recorded
  side as `recorded <= remeasured`. So crossing graded **`WINDOW_HELD`** — and
  because crossing's stock arm is windowless at `w = 150` too, `set() == set()`
  put it in **`exact`**, the strongest grade the census has. The census reported
  4 cells compared where 2 were, and claimed the cheap table exactly reproduced
  an expensive walk on a scene it never visited.
- 🟢 The fix is where the bit was dropped, not where it was noticed: `lookup`
  has always carried `found`, `recorded` discarded it. `seed_census` now checks
  `found` and diverts to a new `absent` field **before** grading. Non-vacuous in
  both directions — `w = 100` (8 scenes) has `absent == ()`, `w = 150` (1 scene)
  does not.
- 🟡 Three tests moved, each written by an earlier cycle to fail exactly here:
  the index refusal witness walks 150 → **250**, coverage admits a fourth
  weight, and D-148's "half the span is uncalibrated" becomes "the last
  uncalibrated rung is the weakest one".

## North-star delta

- No new safety/tracking numbers — headline unchanged (`unsafe_rate` 0.0000 /
  `min_clearance` 0.3579 / `success_rate` 1.0000, 5 cells / 40 seeds).
- The **standing** of the published band moves up: 2/4 → **3/4** scorable rungs
  certified on the λ axis, and the one left is `w = 250`, already flagged
  one-run. Calibrated coverage 56 → **58** arm-cells, weights 3 → **4**.
- One false-pass path removed from a guard that had a live consumer. That is
  the north star only distantly, but a census that grades scenes it never read
  is how a wrong number reaches a report.

## Key learnings

- **A guard's first partial input is where its empty-set handling gets
  audited.** Every table until now walked all 8 scenes, so "cell missing" was
  unreachable and the `NO_CELL`/`EMPTY_WINDOW` conflation sat harmlessly inside
  `seed_census` for four cycles. Buying a *cheaper* measurement is what made it
  fire. Worth expecting: the next narrow artifact will find the next one.
- **The dangerous direction is the empty side of a subset test.** `rec <= new`
  is true for `rec = ∅` whatever `new` is, so every absent-input path through
  `window_shift` grades HELD. D-145 booked this once for windowless cells and
  the note stayed scoped to that case; the general statement is that a
  containment grade needs its left side proven non-empty *or* proven present.
- **`shift_census` has the same shape and has not fired.** It grades registry
  cells against a default table that still covers all 8 scenes, so it is safe
  today and wrong the moment somebody passes it a narrow table. Recorded as
  Q-121 rather than fixed blind — the fix needs an `ABSENT` key in its
  grade→labels return, which is a signature change, not a diversion.
- **Operational, and the honest version**: the overrun advisory *was* acted on
  — scope cut to one scene at PLAN time on its strength, the 128-run
  measurement launched in the first tool call so it walked while REVIEW
  happened, both new loop-body asserts unrolled rather than registered with
  `loop_reach` (the ~90 s the 04:00 cycle said it lost). And the suite still
  ran **twice**, so the cycle took ~110 min against 35.
- **The pre-suite subset was selected on the wrong key.** I ran the tests whose
  *modules* the change touched. The four that broke were in
  `test_operating_point_certification`, which mentions neither `seed_census`
  nor `published_band` — its coupling to this change is the **literal `150.0`**,
  used as its "no table at this weight" fixture. Buying that weight is exactly
  what makes such a fixture stop refusing. Grepping the test tree for the
  literal, not just for the touched modules, is the cheap version of the 15 min
  this cost. The push gate caught it, which is what it is for (D-082) — a red
  tree never reached `origin`.

## Recommended next 1–3 priorities

1. **Re-walk `w = 250` at 16 seeds, or drop it from the published band** — now
   the *only* uncalibrated rung in the span and still the sole reason the band
   grades `BAND_SPLIT`. Both weaknesses now sit alone on one rung.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — same defect, one
   function over, currently unreachable only by luck of the default table.
3. **Walk `gap_gated_mppi` at `w = 75`** — unchanged; gives D-146's column its
   first weight contrast, widens `COMPARED_ARMS` to three. ~512 runs, ~6 min.

## Artifacts
- PR: pending merge (`autoresearch/p3-epistemic-shadow-cost-critic`, PR #67)
- Files touched: `eval/scenarios/variants/lam_windows_w150.yaml`,
  `eval/mppi_sandbox/lam_window_index.py`, `eval/mppi_sandbox/lam_window_key.py`,
  `eval/mppi_sandbox/tests/test_lam_window_index.py`,
  `eval/mppi_sandbox/tests/test_published_band.py`,
  `eval/mppi_sandbox/tests/test_lam_window_seed_count.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
