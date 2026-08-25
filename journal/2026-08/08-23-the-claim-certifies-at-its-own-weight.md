# The claim certifies at its own weight — and the 8-seed caveat gets its first price

- **Cycle**: 2026-08-08 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-key `w = 100`
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked the full matrix at `--w-obs-soft 100` — 8 scenes × 2 controllers × 8
  rungs × 8 seeds = **1024 closed-loop runs**, ~15 min on 16 jobs — into
  `eval/scenarios/variants/lam_windows_w100.yaml`. Same ladder, seed count and
  generator as D-141's `w = 10` and D-142's `w = 75` tables, so the three-way
  contrast isolates the weight alone.
- Registered it in `lam_window_index.TABLES`, which is the whole integration
  cost D-143 predicted: one tuple entry, no migration.
- Shipped `lam_window_key.seed_census()` + `SeedContrast` — grading a generated
  table against the hand-walked `REMEASURED` cells **at its own weight**, which
  isolates the seed count for the first time.
- Rewrote the certification test that recorded the refusal as a standing debt.

## What worked / what failed

- 🟢 **The project's only scorable mechanism claim certifies for the first
  time.** `certify()` graded the risk channel's `w = 100` rung
  `NO_TABLE_AT_WEIGHT` yesterday; both head_on arms now read `[0.2, 0.4, 0.8]`
  at `w = 100`, so λ = 0.8 — the temperature D-131/D-132 actually walked — is
  inside both windows *at the weight the claim was taken at*. This could have
  gone the other way: D-142 moved 6 of 14 arm-cells between `w = 10` and
  `w = 75`, and had head_on/risk been one of them the test would now be
  recording a retraction instead.
- 🟢 **The 8-seed caveat is priced on one cell, and priced exactly.** It has
  stood unpriceable since D-142 — pricing it needs one cell measured at both
  seed counts, and no table existed at a weight `REMEASURED` also held.
  `w = 100` is the first that does: the 8-seed table reproduces D-135's 16-seed
  hand walk on **both** arms, as **set equality** and not containment. A cheap
  measurement agreeing by being conservative is a different claim, and D-135
  drew that distinction about its own result.
- 🟡 **Two confounds had to be handled, not assumed away.** The tables walk 8
  rungs and the hand walks walked 4, so grading unscoped would let a rung the
  16-seed source was never asked read as a seed disagreement; the grade is
  scoped to the registry cell's ladder and the 4 dropped rungs are named in
  `unwalked`. And 2 of the 3 registry cells sit at `w = 150` and can price
  nothing — they are listed in `uncompared` rather than omitted, since a census
  showing only its one comparable cell reads as "the caveat is priced".
- 🔴 **`convoy` is the mover, and it moves on both axes.** Both its arms grade
  `WINDOW_DISJOINT` from `w = 10` **and** from `w = 75` to `w = 100`. `crossing`
  closes outright. 10 of 14 arm-cells hold on both contrasts — so the weight
  axis is not a uniform drift, and there is still no correction factor.
- 🔴 **First cut of the non-vacuity test was itself vacuous.** It graded
  `crossing`@w=150 against the new table, and both crossing arms are windowless
  at `w = 100` — an empty recorded window is a subset of everything, so it came
  back `WINDOW_HELD`. The witness now reads the `w = 10` table, where D-134's
  `DISJOINT` is real. Exactly the failure direction Q-120 opened.
- 🟡 Three existing tests pinned the two-weight index (`available == (10, 75)`,
  `coverage <= {10, 75}`, the reachability case list). Each moved to `w = 150`
  — D-132's top rung, still unmeasured — so the refusal keeps a witness.

## North-star delta

- The safety headline is unchanged (`unsafe_rate` 0.0000 / `min_clearance`
  0.3579 / `success_rate` 1.0000, 5 cells / 40 seeds). No new closed-loop
  safety numbers.
- What moved is **the standing of the number we already publish**: it is now
  certified at its own operating point rather than refused, and its seed count
  is priced against a 2× walk on the cell it was measured on.
- Calibrated coverage: 2 weights → 3, 32 arm-cells → 48.

## Key learnings

- **A refusal test should name the gap, not the weight.** The `w = 100`
  assertion was written to fail loudly when somebody paid for the table — and
  it did exactly that. Re-pointing it at `w = 150` keeps the check alive; a
  test pinned to a specific weight forever would have outlived the gap it
  watched.
- **An axis becomes measurable when two sources overlap, not when someone
  decides to measure it.** The seed caveat was unpriceable for three cycles for
  a purely structural reason, and re-keying `w = 100` cleared it as a side
  effect of a run taken for a different purpose.
- **Vacuity has a direction on the empty set too.** `WINDOW_HELD` is `recorded
  ⊆ remeasured`, so any comparison against a windowless cell passes. Q-120's
  refuses-everything failure and this accepts-everything one share a root: a
  grade read without checking its denominator is non-empty.
- **`convoy` deserves the next hand walk**, not head_on. It is the only cell
  that disagrees on both weight contrasts, and the registry has no cell on it.

## Recommended next 1–3 priorities

1. **Calibrate `gap_gated_mppi`** — D-124's published claim still grades
   `NO_CELL` at every weight; one controller column added to the matrix clears
   a standing refusal against a shipped claim.
2. **Point the sweep drivers at `assert_certified`** — `scorable_band` and the
   ladder walks still take λ as a free argument. Pure code + tests, no sweep.
3. **Hand-walk `convoy` at 16 seeds** — the one cell that moves on both weight
   contrasts, and the one that would add a second cell to the seed census.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `eval/scenarios/variants/lam_windows_w100.yaml`,
  `eval/mppi_sandbox/lam_window_key.py`,
  `eval/mppi_sandbox/lam_window_index.py`,
  `eval/mppi_sandbox/tests/test_lam_window_seed_count.py`,
  `eval/mppi_sandbox/tests/test_operating_point_certification.py`,
  `eval/mppi_sandbox/tests/test_lam_window_index.py`, `docs/decisions.md`
- TSV row appended: yes
