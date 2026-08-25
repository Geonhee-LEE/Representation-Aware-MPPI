# The published span is fully calibrated, and the census that never asked

- **Cycle**: 2026-08-09 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — the published span's last uncalibrated rung, `w = 250`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked `cafe_head_on_v0` at `--w-obs-soft 250` (1 scene × 2 arms × 8 rungs ×
  8 seeds = **128 runs, ~4 min**) into `lam_windows_w250.yaml`, registered it in
  `lam_window_index.TABLES`. Same one-scene scope cut as D-149, for the same
  reason: the published span only runs through that scene.
- Wired `NO_SEED_CONTRAST` — a constant D-145 wrote and nothing returned — into
  `SeedContrast.verdict`.
- Replaced the refusal tests' hard-coded probe weight with a derived one
  (`TableIndex.uncalibrated_probe`).

## What worked / what failed

- 🟢 **`SPAN_CERTIFIED`, 4 of 4.** `certified` goes `(75, 100, 150)` →
  `(75, 100, 150, 250)`, `unmeasured` empty, `refused` empty. The arc is
  D-148 2/4 → D-149 3/4 → 4/4. `require_calibration=True` now **accepts** the
  published band — the first band in the repo to clear the strict form, and
  the flag D-147 argued had to default off because it would refuse nearly
  everything.
- 🟢 **It could have retracted, and this rung more easily than the last.** The
  stock arm's window *did* move: `[0.4, 0.8]` at `w = 250` against
  `[0.2, 0.4, 0.8]` at 10/75/100/150 — the first head_on arm-cell to move at
  all across the calibrated weights. It narrowed from the bottom, so λ = 0.8
  survived. Had it closed from the top this would be a retraction of a rung
  D-133 publishes.
- 🟡 **`w = 250` is also the first weight where the two head_on arms disagree**
  (stock `[0.4, 0.8]`, risk `[0.2, 0.4, 0.8]`). The certification is true and
  reads wider than it is; pinned in its own test so "λ = 0.8 is admissible
  everywhere" is not what the green is taken to mean.
- 🔴 **`seed_census` has never said when it compared nothing.** With no registry
  cell at the table's weight, `graded` is `{}`, `exact` is `()`, and — since
  D-149 — `absent` is `()` too, because `absent` means "hand-walked here and
  missing from the table" and nothing was hand-walked at all. Every field reads
  exactly as under total agreement. **Three of the five shipped tables are in
  that state** (`w = 10`, `w = 75`, `w = 250`).
- 🔴 **This was not new with `w = 250`** — `w = 10` and `w = 75` have been silent
  since the first keyed table, so the honest statement is that the defect has
  been reachable the whole time and this cycle is the third instance, not the
  trigger. `NO_SEED_CONTRAST` named the case in D-145's own docstring
  ("Distinct from 'the seed count does not matter': nothing was compared") and
  no code path returned it, while `attribution` had already made the identical
  split one function over: `FACTOR_INERT if compared else NO_CONTRAST`.
- 🟢 **The 14 red tests were predicted before the suite ran, not by it.** Last
  cycle's key learning was to grep the test tree for the *weight literal*
  rather than the modules touched. Did that first: it found all four coupled
  modules, including `test_operating_point_certification.py`, which is exactly
  the file D-149's targeted subset missed and paid a second 15-min suite for.
- 🟡 **I misread a partial artifact as a lost cell.** Read
  `lam_windows_w250.yaml` while the background walk was still writing, saw one
  arm, and concluded the `-j 16` run had dropped `risk_mppi`. It had not. Cost
  ~2 min re-walking the arm — which did buy an independent reproduction at
  `-j 2` (`[0.2, 0.4, 0.8]`, min_spread 1.00, identical).

## North-star delta

- No new safety/tracking dynamics. The headline is unchanged: `unsafe_rate`
  **0.0000** / `min_clearance` **0.3579** / `success_rate` **1.0000**, 5 cells /
  40 seeds.
- What moved is the **standing of the published claim, to complete**: the band
  the project publishes is now certified on the λ axis at every rung that sets
  it. That closes the arc D-148 opened three cycles ago.
- Calibrated coverage 58 → **60 arm-cells**, weights 4 → **5**.

## Key learnings

- **A constant that names a case is not the same as a branch that returns it.**
  `NO_SEED_CONTRAST` was written, documented with the exact trap it prevents,
  cross-referenced to its sibling — and never returned. The docstring made it
  *look* handled at every subsequent read. Worth grepping the other refusal
  constants for the same shape.
- **The empty denominator keeps arriving one layer out.** D-107/D-120/D-127
  booked it, D-145 hit it in `window_shift`, D-149 hit it in `recorded`, and it
  was sitting in `seed_census`'s own return value the whole time. The recurring
  form is: *some* field of the result is empty for two different reasons, and
  only one of them is a pass.
- **A refusal test that names a weight will be migrated, and D-145 said so and
  then named one anyway.** Three hand-migrations (100 → 150 → 250), three red
  suites. The invariant is about the complement of the index's domain, so it is
  now derived from it. Buying a weight can no longer redden or empty that path.
- **Also: a refusal witness must not live on the object being certified.** Once
  the published band cleared `require_calibration=True`, the test asserting the
  flag *can* refuse had nothing left to refuse. Moved onto the derived probe.
- **Operational**: an `on_cell=flush` table is byte-valid after every cell, so a
  partial and a finished run are indistinguishable on disk — recorded as Q-122.
  Cheap defence: check the process exited before reading its output, which I
  did not, because `cmd | tail` reports `tail`'s exit code and not the walk's.

## Recommended next 1–3 priorities

1. **Re-walk `w = 250` at 16 seeds** — now the *only* remaining weakness on that
   rung, and the band's sole structural claim (`BAND_SPLIT`) still rests on a
   separation of one run in sixteen with the sign against the mechanism.
   Calibration cannot touch this; only seeds can. ~256 runs.
2. **Fix `shift_census`'s absent-cell path (Q-121)** — unchanged, and now with a
   sibling: audit whether `shift_census` also lacks a compared-nothing verdict.
3. **Walk `gap_gated_mppi` at `w = 75`** — unchanged; widens `COMPARED_ARMS` to
   three and gives D-146's column its first weight contrast. ~512 runs.

## Artifacts

- PR: #67 (continued per D-140 — no new branch, no new review bandwidth)
- Files touched: `eval/mppi_sandbox/lam_window_index.py`,
  `eval/mppi_sandbox/lam_window_key.py`,
  `eval/scenarios/variants/lam_windows_w250.yaml`,
  `eval/mppi_sandbox/tests/test_published_band.py`,
  `eval/mppi_sandbox/tests/test_span_certification.py`,
  `eval/mppi_sandbox/tests/test_operating_point_certification.py`,
  `eval/mppi_sandbox/tests/test_lam_window_index.py`,
  `eval/mppi_sandbox/tests/test_lam_window_seed_count.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
