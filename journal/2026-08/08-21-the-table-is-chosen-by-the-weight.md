# The table is chosen by the weight — the λ guard gets its first consumer

- **Cycle**: 2026-08-08 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #3 — point a consumer at the keyed tables
- **Phase**: P3
- **Status**: keep

## What I tried

- Shipped `eval/mppi_sandbox/lam_window_index.py`: `build_index()` reads each
  calibration table's own `calibration_weight:` and maps weight → path;
  `resolve(scene, controller, weight)` picks the table **from** the weight and
  delegates the cell lookup to the existing `lam_window_key.lookup`.
- Added `NO_TABLE_AT_WEIGHT` — the refusal for a weight no table was
  calibrated at — carrying `available` (the weights that *do* exist).
- Added `coverage()` (per-cell → weights with a usable window) and
  `reachable_verdicts()` (which verdicts the index can actually return).
- 13 tests in `tests/test_lam_window_index.py`, anchored on D-133's cell.

## What worked / what failed

- 🟢 **The guard had no consumer, and that was the whole gap.** Every
  `lookup` call site in the repo is a test — grep confirms it. With one table
  per weight, a caller must already know which file matches its weight, and a
  caller that knows that does not need the guard, while one that does not will
  open the wrong file and get a confidently `ON_KEY` answer about someone
  else's operating point. Choosing the file from the weight is what makes the
  refusal load-bearing.
- 🟢 **D-133's error is now structurally unreachable.** `crossing`/`risk_mppi`
  resolves to `[1.6, 3.2]` at `w = 10` and to `EMPTY_WINDOW` at `w = 75` —
  not to the `w = 10` row. That cell is the one D-133 walked at λ = 3.2 on the
  strength of an off-key read.
- 🟢 **Two refusals are converted, not softened.** `OFF_KEY` and `UNKEYED` are
  unreachable through the index by construction (checked by
  `reachable_verdicts`, not merely claimed in prose): the index only ever hands
  `lookup` a table already on key, and an unkeyed table is not in it. Both
  become `NO_TABLE_AT_WEIGHT`, which names the weights that would work — the
  difference between "your number is untrustworthy" and "measure at 100, or
  run at 10 or 75" (D-044).
- 🟢 **The excluded table is named, not dropped.** `lam_windows.yaml` appears
  in `TableIndex.unkeyed`. Its non-participation is a finding about the file
  ~24 cells of project history were read from, so silence would be the wrong
  report.
- 🟡 **`coverage()` says the calibration is patchy, and that is the honest
  read**: 16 arm-cells, of which `crossing`/risk is usable at `w = 10` only and
  both `cut_in` cells at neither weight. Listing never-open cells as `()`
  rather than omitting them keeps "not covered here" distinct from "not a
  cell" — the denominator pollution D-142's `NEVER_OPEN` grade fixed one layer
  up.
- 🟢 Meta-guard subset (census / citation / loop_reach / provenance /
  local_only, 426 tests) green with **no registry edits** — the new module
  needed no census rows, unlike the last three cycles.

## North-star delta

- No new safety/tracking dynamics: `unsafe_rate` 0.0000 / `min_clearance`
  0.3579 / `success_rate` 1.0000 stand where D-136 left them.
- What moved is **usability of the calibration**: for the first time a caller
  can ask for λ by `(scene, controller, weight)` and be refused by name
  instead of silently handed a window measured elsewhere. D-142 made the
  off-key read *known* to be wrong at 6/14 cells; this makes it *unavailable*.
- Zero new closed-loop runs — a deliberate scope cut after two consecutive
  cycles overran (56m and ~95m against a 35m budget).

## Key learnings

- **A guard with no consumer is not half-finished; it is untested in the way
  that matters.** `lookup` has been correct since D-134 and graded nothing that
  any production path depended on. The missing piece was never more grading —
  it was the file *choice*, which is where the weight actually enters.
- **Q-119's schema fork is a false binary.** File-per-weight and
  weight-indexed answer different layers: per-file on disk because each file is
  one ~1024-run measurement and provenance is per-run; weight-indexed in the
  API because that is the key callers hold. Deriving the index at read time
  gets both, and adding `w = 100` becomes one `calibrate_lam` run plus one
  tuple entry with no migration.
- **The cheap cycle was available the whole time.** STATE ranked two more
  ~16-min sweeps above this; the advisory to cut scope is what surfaced that
  the third item was both cheaper and more load-bearing, since it prices what
  the two completed sweeps already bought.

## Recommended next 1–3 priorities

1. **Re-key `w = 100`** — now strictly more valuable: the index turns a third
   table into a resolvable operating point, and D-135's 16-seed hand walk at
   `w = 100` prices the standing 8-seed caveat.
2. **Point `comparison_headroom` / a ladder walk at `resolve()`** — the index
   exists but the sweep drivers still take λ as an argument; making one of them
   refuse to run off-key is the next step from available to enforced.
3. **Re-key `w = 150`** — completes D-132's band.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: `eval/mppi_sandbox/lam_window_index.py`, `eval/mppi_sandbox/tests/test_lam_window_index.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
