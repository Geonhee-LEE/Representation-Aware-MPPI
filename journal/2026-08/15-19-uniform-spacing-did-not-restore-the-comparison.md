# Uniform spacing did not restore the comparison

- **Cycle**: 2026-08-15 19:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bdc5d39` epistemic shadow cost critic 으로 복귀 (04:00 이후 미접촉)
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked the same two interior rungs D-286 walked at `lam = 1.0` — `w_voo ∈
  {8, 12}` — at the **other two** temperatures, `0.8` and `1.2`. 4 closed-loop
  runs + 4 leave-one-out cost-field reads, **10.4 s**.
- Added `MEASURED_LAM08_FINE` / `MEASURED_LAM12_FINE` and the uniform table
  `MEASURED_ALL_LAMS_UNIFORM`, where every temperature walks `{5, 8, 12, 20}`.
- Added `uniform_resolution_trend()`: re-take `gap_trend`'s bar with the
  spacing objection (D-019) removed, and report separately whether the
  *comparison* survives. 9 tests.

## What worked / what failed

- **The spacing objection is answered.** `resolution_uniform = True` — all
  three temperatures now walk the same four rungs across the bracket, so
  D-286's mixed `1.6x`-vs-`4x` reading is gone.
- **The comparison is not.** `lam = 1.2`'s refined ladder is **non-monotone**:
  `88.59 → 4.58` from `w = 5` to `8`, then back **up** to `9.14` at `12`.
  `ceiling_resolution` returns `CROSSING_NON_MONOTONE` and withholds, exactly
  as built — a bracket reader assumes one crossing and this ladder has none.
  Verdict is `UNIFORM_TREND_WITHHELD`, not a re-taken trend.
- **Both temperatures that *can* be checked flip the same way `1.0` did.**
  `0.8`: `16.33x → 4.517x` (overstated `3.62x`, the largest on the axis).
  `1.0`: `11.96x → 6.485x` (`1.84x`). So `any_lam_fits_band = False` was not a
  quirk of one temperature — it is resolution-dependent **everywhere it can be
  checked**, and D-286's `1.84x` was the milder of the two, not the typical one.
- `1.2`'s refined gap (`19.36x`) is excluded from `min_gap_refined` on purpose,
  not carried with a caveat. Excluding it is not what produces the flip — it
  would not have fitted the band either.
- **No two-point trend reported.** `trend_verdict` stays `None` with
  `n_comparable = 2`, because D-285's own lesson (two points are a segment, not
  a direction) applies to the reader that supersedes it.
- **Pin tax paid twice, and the second one was not the census.**
  `uniform_resolution_trend` is the **113th** guard (D-287), caught before the
  suite. What the suite caught was `loop_reach.READING`: the new
  `test_the_spacing_is_now_uniform...` loops a set-equality claim over the
  three temperatures, so the population-claim corpus grew and the recorded
  reading stopped describing it. Cost: the ~90 s re-take plus a second full
  suite. Two pins, two different registries, one new test — the census is not
  the only thing a new reader owes.

## North-star delta

- No obstacle, clearance or near-miss number moved — still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- The strongest arm recovered so far on this axis: at `lam = 0.8` the ceiling's
  two sides are **`4.517x`** apart, not `16.33x`. That is the smallest measured
  gap anywhere on the walked rungs and it sits well inside the `10.0x` band.
- One temperature is now **disqualified by shape** rather than by margin, which
  is a different kind of exclusion than any prior cycle on this branch produced.

## Key learnings

- **Removing an objection is not the same as getting an answer.** The cheap
  4-run fix did exactly what it promised to the spacing and revealed a second,
  unrelated obstacle sitting underneath it. Worth expecting: a caveat cleared
  cheaply is where the next one becomes visible.
- **Refining can make a ladder *less* readable, not more.** At `4x` spacing
  `lam = 1.2` looked like a clean monotone crossing; the interior pair is what
  showed it is not. Coarse ladders hide non-monotonicity by not sampling it.
- **`bars_shared_rung` is still `False`, and now for two independent reasons** —
  D-284's false common-factor premise, and the fact that the temperature with
  the best gap (`0.8`) is not the one anything else recommends.

## Recommended next 1–3 priorities

1. Is `lam = 1.2`'s rise real or seed noise? One re-run at `(1.2, 12)` on a
   second seed (~5 s) separates "the sampler does something non-monotone here"
   from "one seed did". The withholding is correct either way, but the two
   readings license very different next moves.
2. Test the shared-rung question directly at `lam = 0.8`, where the gap is now
   smallest (`4.517x`): is there a temperature holding `w = 5` and `w = 8` in
   band at once? Must be measured, not derived — the premise is false.
3. Buy back the 5 withdrawn `inert_surface` exemptions — **ninth** consecutive
   cycle carrying it.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md
- TSV row appended: pending
