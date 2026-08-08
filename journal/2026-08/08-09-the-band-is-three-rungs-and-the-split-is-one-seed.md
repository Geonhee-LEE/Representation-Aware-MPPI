# The band is three rungs wide, and the split at the top is one seed

- **Cycle**: 2026-08-08 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — densify the transition band 100 → 300 and re-score `risk_mppi` with more seeds
- **Phase**: P5
- **Status**: keep

## What I tried

- D-131 found exactly one rung where `risk_mppi` could beat `stock_mppi` on
  `cafe_head_on_v0` (`w_obs_soft = 100`, unsafe 1.0000 → 0.2500, n = 8), and
  its neighbours on that ladder were 30 and 300. So the whole positive result
  was a point, and nothing could say whether the scorable region was one rung
  wide or five.
- Walked a densified ladder — `w ∈ {30, 55, 75, 100, 150, 200, 250, 300}` — at
  λ = 0.8, both arms, **16 seeds** (D-131's 8 doubled), margin 0.40 m.
- Shipped `scorable_band.py` to hold the answer's shape: the scorable rung
  **set**, whether it is contiguous, whether it runs off either end of what was
  tested, and the untested brackets its edges actually live in.
- Added `relief_interval.open_below` — the floor mirror `open_above`'s own
  docstring names as the gap that made convoy's ceiling-at-30 read as a
  footnote instead of as an openness verdict (D-126/D-130, Q-112's axis).

## What worked / what failed

- ✅ **The band is three rungs, not one.** `{75, 100, 150}` are contiguous and
  each separates on its own: Fisher two-sided **0.043 / 2.5e-4 / 0.0021**
  (stock 16/16, 16/16, 10/16 unsafe against risk 11/16, 6/16, 1/16). Lower edge
  bracketed in **(55, 75]**; the transition ends at 200, where relief begins and
  both arms go 0.0000 — D-131's structural claim reproduced at 2× the seeds.
- ✅ **The one rung D-131 had survives the doubling and is now significant.** At
  `w = 100`, 1.0000 → **0.3750** at n = 16, **p = 2.5e-4**. This is the
  project's first mechanism claim that is both scored at an admissible
  operating point *and* significant — every earlier one was either pinned by
  construction or n = 8 on one rung.
- 🔴 **The band is `BAND_SPLIT`, and the split is one seed.** `w = 250` grades
  `SEPARATED` because **one** of sixteen risk seeds came 0.3472 m against the
  0.40 m margin while stock had none — Fisher **p = 1.0**, direction *against*
  the mechanism. `SEPARATED` asks only that two rates differ, so one run out of
  sixteen buys a verdict that then makes the whole band print as two islands.
  Named by `one_run_rungs` rather than thresholded away: this is the shape
  `relief_interval.SUBRESOLUTION` already books one axis over.
- ✅ **D-131's ESS side finding reproduces at 16 seeds, on the arm it named.**
  `w = 30` is refused — `stock_mppi` leaves the ESS band at the same λ = 0.8
  that is compliant at 55 and above. So the module refuses rungs rather than
  grading them, and a refused rung is **not** allowed to witness an edge: at
  w = 30 we know nothing, which is not the same as knowing it fails.
- 🟡 **Three script failures cost ~7 minutes of the budget** — `NearMissStats.
  unsafe`, `ArmRun.min_clearance`, and a `ProcessPoolExecutor` worker with no
  repo on `sys.path`. Each surfaced only after a full 30 s–2 min sweep had run.
  A two-seed smoke of the driver before the real sweep would have caught all
  three in 7 seconds, and is what finally did.

## North-star delta

- **First significant safety improvement from a representation channel.**
  `risk_mppi` cuts `unsafe_rate` 1.0000 → 0.3750 at `w = 100` (n = 16,
  p = 2.5e-4) and 0.6250 → 0.0625 at 150 (p = 0.0021), on a scene where every
  seed reaches the goal and both arms are ESS-compliant.
- **The result has a width now, not a point.** A claim attached to one rung is
  one ladder choice away from vanishing; a claim attached to a bracketed
  three-rung band is a property of the scene.
- Headline unchanged: the 5-cell / 40-seed `unsafe_rate = 0.0000` matrix result
  is measured at each scene's operating weight and this cycle did not touch it.

## Key learnings

- **A verdict about a set needs the ladder that found it, at both ends.** The
  band's rung count, its span, and its two edge brackets are three different
  statements, and collapsing them into a scalar "width" makes a coarse ladder
  and a dense one print identically.
- **`SEPARATED` has no magnitude, and at n = 16 one seed buys it.** The verdict
  vocabulary grades whether a comparison *could* discriminate; it does not
  grade whether the discrimination it found is resolvable. Logged as Q-115.
- **Smoke the driver, not just the module.** Three of this cycle's four sweep
  launches died on an attribute name, each after paying full sim cost. The
  measurement code is outside the test suite by construction, so it needs its
  own cheap first pass.

## Recommended next 1–3 priorities

1. **Walk the same densified ladder on `cafe_obstacle_crossing_v0`** — the other
   scene D-125 relieved. If `risk_mppi` has a band there too, the mechanism
   claim stops being about one scene; if it has none, that absence bounds it.
2. **Give `SEPARATED` a resolution floor** (Q-115) — a `SUBRESOLUTION`-style
   verdict for a separation of one run, so a singleton cannot change a band's
   shape verdict.
3. **Key `lam_windows.yaml` by weight, or refuse rescores at unmeasured
   weights.** `w = 30` refused for the second cycle running; the calibration
   table still carries no record of the weight it was measured at.

## Artifacts
- PR: #67 (already open, `autoresearch/p3-epistemic-shadow-cost-critic`)
- Files touched: `eval/mppi_sandbox/scorable_band.py`, `eval/mppi_sandbox/tests/test_scorable_band.py`, `eval/mppi_sandbox/relief_interval.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
