# Seven of eight, and the miss is the band

- **Cycle**: 2026-08-15 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bcc5d39` [sandbox] operating-point-seed-ensemble
- **Phase**: P3
- **Status**: keep

## What I tried

- Re-took D-270's single co-satisfying cell — `cafe_freezing_v0`,
  `(lam = 0.8, w_voo = 5)` — over `ab.DEFAULT_SEEDS` (`n = 8`, the seed count
  D-019 was measured at), in `ess_at_peak.ISOLATION`, one closed-loop run plus
  one leave-one-out cost-field read per seed.
- Added `seed_points` / `seed_census` / `ess_span` / `seed_verdict` /
  `sweep_seeds` to `calibrated_ladder.py`, with the verdict vocabulary written
  **before** the counts were read.
- 8 new tests; the whole file is 23.

## What worked / what failed

- **7 of 8 seeds are usable.** Seed 0 reproduces D-270 to the recorded digits
  (ESS `31.2344`, ratio `0.228470`), so the ensemble and the ladder are the
  same measurement. The cell is therefore **neither** of the two things the
  TODO offered: not a seed-0 artefact (7 seeds hold, and seed 0 is not even
  the best of them), and not a window (D-019 makes `admissible` an all-seeds
  conjunction, so `7/8` is a rate).
- **The single miss is a band miss, and that is the informative part.** All 8
  seeds clear the audibility bar (`min ratio 0.1384` vs the `0.1` bar) and all
  8 reach goal. Seed 4's ESS is `4.5329`, under the `12.8` floor. So what
  fails at this cell is the **sampler**, not the arm — the opposite axis from
  the one D-264/D-265/D-266 spent three cycles chasing.
- **Per-seed ESS span is `12.68×`** (`57.48` at seed 5 vs `4.53` at seed 4),
  roughly 2.5× wider than the `~5×` D-019 measured on the cell that motivated
  seed ensembles in the first place. Seed 6 lands at `13.43` against a floor
  of `12.8` — a second near-miss a stored boolean would have printed as a
  clean pass.
- My first cut of the "unanimity" test asserted only that the verdict is not
  `UNANIMOUS_WINDOW`, which any always-`MAJORITY_USABLE` implementation
  satisfies; it now also drops seed 4 and asserts the same census grades
  `UNANIMOUS_WINDOW` at `n = 7`.

## North-star delta

- The branch's one operating point survives contact with a seed ensemble at
  `7/8` — it is a usable foothold rather than a fluke, which is more than any
  previous cell here has earned, but it is **not** a certificate.
- Direction for the next repair is now measured rather than guessed: at this
  cell, audibility is solved and the ESS floor is what leaks. Nothing about
  obstacle avoidance or path tracking moved.

## Key learnings

- **"Window or artefact" was a false dichotomy, and the answer sits between
  them.** The useful output was not the label but the *decomposition* — which
  condition each failing seed failed on. A cell that misses on band has a
  temperature repair; one that misses on audibility has a scale repair.
- **D-019's `~5×` was optimistic for this cell.** The figure was carried across
  scenes as if it were a plant constant; measured here it is `12.68×`. Future
  cycles quoting a per-seed spread should quote the cell they measured it on.
- `n = 8` licenses nothing about `n = 16`, and `seed_count_licence` records
  that the census walks ladders at 16. This reading is deliberately labelled
  `comparable_to: readings at n=8 only` rather than quietly compared.

## Recommended next 1–3 priorities

1. **`seed-4-band-miss-repair`** — is seed 4 recoverable inside the calibrated
   window (`0.4`/`0.2` rungs), or is `(0.8, 5)` simply the best cell available?
   One cell, 2 extra temperatures, decides whether `8/8` exists at all.
2. **`ensemble-at-n16`** — re-take at `CENSUS_LADDER_SEEDS = 16` so this
   reading becomes comparable to the census's own predicate (D-019(b)).
3. **`calibration-weight-in-lam-windows`** — still unstarted; the window under
   all of this remains `UNKEYED`.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py
- TSV row appended: yes
