# The whole matrix reproduces at its own weight — 16 cells, 80 fields, zero drift

- **Cycle**: 2026-08-08 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — regenerate the remaining scenes at `w = 10` into `lam_windows_w10.yaml`
- **Phase**: P5
- **Status**: keep

## What I tried

- Ran the **full** calibration matrix at an explicit `--w-obs-soft 10` —
  8 scenes × 2 controllers × 8 rungs × 8 seeds = **1024 closed-loop runs**,
  ~17 min wall on 16 jobs — into `eval/scenarios/variants/lam_windows_w10.yaml`.
  STATE planned this as 2–3 scenes per cycle; `calibrate_matrix` parallelises
  over cells and `on_cell=flush` rewrites the file after each one, so the whole
  matrix was one pass with a valid artifact at every intermediate point.
- Diffed all 16 regenerated cells against the shipped `lam_windows.yaml` across
  **every** recorded field, not just `admissible`.
- Rewrote `test_lam_window_regeneration.py` from the one-scene shape D-139 left
  it in to a matrix-wide one: per-(cell, field) parametrised comparison, the
  `ON_KEY`/`EMPTY_WINDOW` split, and honest scope assertions.

## What worked / what failed

- 🟢 **Exact reproduction, 16/16 cells, 80/80 field comparisons** — `admissible`,
  `ladder`, `min_spread` (to two decimals), `completes_anywhere`, `calibratable`
  all identical. The narrow cells are the ones that could have drifted and did
  not: `city_figure8` is a single-rung window `[0.4]` on both arms, and
  `cafe_obstacle_crossing`'s two arms stay asymmetric at `[0.4, 0.8]` / `[1.6, 3.2]`.
- 🟢 **The `UNKEYED` era is over for the calibrated matrix.** 14 cells now grade
  `ON_KEY` with a usable window; the 2 `cafe_cut_in_v0` cells grade
  `EMPTY_WINDOW`, which is the honest answer rather than a lookup failure — an
  arm that reaches the goal at no temperature has no window at any weight.
- 🟢 **`shared_window` regenerates empty**, so Q-036's "no single temperature
  serves the matrix" survives re-measurement. Asserted separately because every
  cell could match while the intersection changed.
- 🔴 **First cut of the tests was red on a container type, not a measurement**:
  `lwk._rows` returns `list` for rung sequences and `lookup().usable` returns
  `tuple`, so 16 assertions failed on `[0.2, 0.4] != (0.2, 0.4)`. D-139's helper
  had coerced and I dropped the coercion when generalising it. Normalised inside
  `_cells` with a comment saying why.
- 🟡 Refinement never fired: both `cut_in` cells came back at exactly the default
  8 rungs, so the empty windows are structural and the regenerated ladders match
  the shipped ones rung-for-rung.

## North-star delta

- No new dynamics. The headline stands where D-136 left it — `unsafe_rate`
  0.0000 / `min_clearance` 0.3579 / `success_rate` 1.0000 over 5 cells / 40 seeds.
- What moved is **provenance, at matrix scale**: every λ window the sandbox reads
  now has a weight attached to it and a re-run that produced it. Before D-139 no
  `lookup` in the repo could return a window; now 14 of 16 cells do.
- The negative result is worth as much as the positive one: 1024 runs bought the
  knowledge that the weight-threading changed **nothing**, which is what lets the
  shipped table's ~24 consumers be believed rather than re-derived.

## Key learnings

- **A generator validated on one cell is not validated on the narrow ones.**
  head_on (D-139) has a comfortable 3-rung window; `city_figure8`'s is a single
  rung and `cut_in`'s is empty. Those are where a threading bug would surface,
  and they only got walked because the full pass was cheap enough to just run.
- **"Chunk it over cycles" was the wrong estimate.** STATE budgeted 2–3 scenes
  per cycle from a per-scene cost; the cost is per *cell* and 16 cells fit on 16
  cores. Checking the parallelism before planning the chunking would have saved
  the plan.
- **An incrementally-flushed artifact makes a long sweep safe to start**, which
  is what let this run inside the wall-clock rule: a kill at any point leaves a
  valid file with fewer cells, not a corrupt one.
- The shipped table stays `UNKEYED` **because** the two tables now agree — the
  agreement is the argument for trusting the variant, not for hand-stamping the
  original (D-107).

## Recommended next 1–3 priorities

1. **Answer Q-119's remaining half** — the weight *subset*. (c) is done; lean (b)
   is D-132's band `{75, 100, 150}`, ~1500 runs across three files, and it is the
   only option that re-keys the rungs the project's one significant claim lives on.
2. **Give `SEPARATED` a resolution floor (Q-115)** — still open, still untouched.
3. **Point a consumer at the keyed table.** 14 cells answer `ON_KEY` and nothing
   reads them yet; a rescore that picks its λ from `lookup` instead of the
   unkeyed table would make the guard load-bearing rather than available.

## Artifacts

- PR: #67 (open, continued per D-140)
- Files touched: `eval/scenarios/variants/lam_windows_w10.yaml`,
  `eval/mppi_sandbox/tests/test_lam_window_regeneration.py`,
  `docs/decisions.md`, `docs/deliberations.md`
- TSV row appended: yes
