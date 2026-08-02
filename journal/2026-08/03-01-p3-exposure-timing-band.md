# Q-044 answered: the screen keeps its cheap driver and loses its ordering

- **Cycle**: 2026-08-03 01:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic` (landed **in place** on PR #67 — 19th consecutive cycle, zero new review bandwidth)
- **TODO**: STATE claude-actionable **#1** — decide what `exposure.py` should be driven by
- **Phase**: P3
- **Status**: keep

## What I tried

- Took Q-044's option **(b)** — keep the declared nominal, carry the error bar — and
  made it operational rather than editorial. `nominal_traversal` gained a
  `duration_ratio` kwarg (same polyline, same actor schedules on their own absolute
  clock, **only** the traversal duration scaled — exactly the one-parameter perturbation
  D-022 measured, and nothing more). Default `1.0` leaves every existing caller
  bit-identical.
- Added `exposure_band` / `ExposureBand.separates` / `rank_with_band`: the screen now
  reports `contested_fraction` as an interval over the measured timing band and
  **refuses to order** any two scenes whose intervals overlap. CLI default flipped to
  the band; the old point estimate survives behind `--point-estimate`.
- **Re-measured the band constant instead of quoting D-022's headline.** Five sims,
  ~7 s total: crossing **0.557**, convoy 1.633, freezing 1.700, head_on 2.038,
  cut_in **15.0**.
- 14 new tests in `tests/test_exposure_timing_band.py`, all but the five band-constant
  sims simulation-free.

## What worked / what failed

- 🔴 **D-022's "0.56×–15×" conflates a timing error with a scene defect.** The entire
  upper end is `cafe_cut_in_v0`, which does not *finish* — it runs out the 120 s cap,
  and Q-037 already ruled that a scene defect and excluded it from every reportable
  matrix. Folding it into an error bar would widen the band **~27×** on the strength of
  a scene nobody may cite. Excluding it, the real band is **0.557–2.038** (≈3.7×). Kept
  beside it as `TIMING_RATIO_BAND_WITH_DEFECT` so the exclusion stays visible.
- ✅ **Static-obstacle scenes are exempt, exactly.** With nothing moving, `contested_s`
  and `traversal_s` scale by the same factor, so band width is **0** and the point
  estimate keeps full authority. The screen degrades in proportion to actor motion, not
  uniformly — which is what kills Q-044 option (c) and is the only constructive result
  here.
- 🔴 **On moving-obstacle scenes the ordering authority is effectively zero.** 5 scenes,
  10 pairs: **9 refused**, and the 1 survivor involves `cafe_cut_in_v0`, unreportable
  anyway. **D-018's cited 74 % vs 43 % is not citable**: `[22 %, 83 %]` vs `[15 %, 66 %]`.
  D-018's *refutation* of exposure-as-predictor is untouched and arguably strengthened —
  a statistic that cannot even order the pair is worse news for it, not better.
- ✅ **The band constant is pinned by live re-measurement**, so it cannot drift away from
  the plant that produced it, and a test asserts the ratios still straddle 1 in both
  directions (if they ever stopped, a scalar correction would beat a band).
- ✅ **Endpoints alone would have understated the interval** — `contested_fraction` is
  **not monotone** in the duration ratio (crossing peaks near 0.8, inside the band).
  41-point geometric grid, pinned by test.
- ✅ No repo default moved. `screen_scenarios` deliberately left alone so D-018's numbers
  stay reproducible; they just stop being citable on their own.

## North-star delta

- **No capability movement — seventh consecutive methodology cycle, and the third in a
  row that subtracts.** What this one buys is a bounded retraction: D-018's
  contested-fraction ranking is now formally withdrawn rather than informally doubted,
  and the withdrawal is mechanical (a test fails if a future cycle tightens the band
  enough to restore it).
- Scenes able to contribute an avoidance number: **5**, reportable: **4** — unchanged.
- One thing genuinely gained for later: the static-scene exemption means a
  simulation-free screen survives as a category, so P5's scene selection does not have
  to buy a sim per scene.

## Key learnings

- **An error bar has to be measured on the population the statistic is defined over.**
  Three of the eight scenes have no obstacles and cannot mis-time a rendezvous; one of
  the remaining five does not finish. Taking the band over "all eight scenes" — the
  obvious reading of D-022 — would have been 27× too wide and would have declared the
  screen dead. The exclusions are where the whole result lives.
- **A defect and an error are different quantities and must not share a summary
  statistic.** "0.56×–15×" is a true sentence that describes two unrelated phenomena.
- **Widening an interval is a stronger retraction than doubting a number**, because it
  is checkable: the overlap test is what a future cycle trips, not a docstring caveat.
- **Non-monotonicity was the near-miss.** Evaluating the band at its endpoints is the
  natural implementation and it understates the crossing scene's interval by >0.05 —
  enough to have manufactured a separation that is not there.

## Recommended next 1–3 priorities

1. **Explain the 1.8× `target_speed_mps` overshoot** (STATE #2, unchanged and now
   better motivated — it is the mechanism *behind* the band this cycle had to declare).
   `w_terminal = 30.0` vs `w_speed = 2.0` is the leading suspect. One-scene weight sweep.
2. **Re-run the audible/deaf partition through `reach_on_trajectory`** — with Q-044
   answered, the remaining blocker on STATE #1's original deliverable is gone. 8 sims.
3. **Decide whether `cafe_cut_in_v0` gets fixed or retired.** It has now distorted three
   separate results (Q-037, D-017's reportable matrix, this cycle's band). It is the
   cheapest scene-level debt in the repo.

## Artifacts
- PR: #67 (existing, updated in place)
- Files touched: `eval/mppi_sandbox/exposure.py`, `eval/mppi_sandbox/tests/test_exposure_timing_band.py`, `docs/decisions.md` (D-023), `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
