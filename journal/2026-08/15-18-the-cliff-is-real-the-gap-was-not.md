# The cliff is real, the gap was not

- **Cycle**: 2026-08-15 18:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `probe-inside-the-ceiling-bracket` Probe inside D-027's ceiling bracket
- **Phase**: P3
- **Status**: keep

## What I tried

- Walked two rungs **inside** D-284's `(5, 20]` bracket at `lam = 1.0` —
  `w_voo ∈ {8, 12}`, spacing `1.6x` / `1.5x` where the ladder's own spacing is
  `4x`. 2 closed-loop runs + 2 leave-one-out cost-field reads, **5.2 s**.
- Added `ceiling_resolution()`: does a finer ladder widen the usable region
  (slope — the one-rung region was a spacing artifact) or not (cliff — it is a
  fact about the sampler)? The call is a **band-membership test**, so no
  steepness threshold is declared.
- Registered the rows as `MEASURED_LAM10_FINE`, concatenated into
  `MEASURED_LAM10_REFINED` / `MEASURED_ALL_LAMS_REFINED`. 10 tests.

## What worked / what failed

- **Cliff, unambiguously.** Neither interior rung is in band — ESS `4.84` at
  `w = 8` and `4.20` at `12`, against a floor of `12.8`. The usable set is
  `{w = 5}` at both resolutions; `region_is_artifact = False`. The bracket
  tightens `(5, 20] → (5, 8]` (log-width `2.95x`).
- **The gap was an artifact, and this was not the question I asked.**
  `ceiling_gap`'s `11.96x` bundles the crossing together with `1.84x` of decay
  from `8` to `20` that happens **entirely below the band** and so is not the
  sampler leaving it. The crossing alone is **`6.485x`** — *inside* the `10.0x`
  band, where the coarse reading was outside. `gap_verdict_flips = True`.
- So D-285's `any_lam_fits_band = False` and the `GAP_EXCEEDS_BAND` under it
  are **resolution-dependent** at this temperature. Not wrong at `4x` — the bar
  was met partly by the ladder's spacing.
- I did **not** restate `gap_trend` at the finer spacing. `0.8` and `1.2` have
  no interior rung walked; `refined_at_lams = (1.0,)` carries that.
- `bars_shared_rung` stays `False`. A fitting gap is arithmetic; the
  common-factor premise D-284 measured false is not repaired by a finer ladder.
- **Pin tax paid, and the entrant is interesting.** The first receipt came back
  red on one test — `len(pool) == 111` → **112**. `ceiling_resolution` entered
  the guard census via `set(usable_now) - set(usable_was)`, which is
  `region_is_artifact` itself: the first entrant whose visible narrowing is the
  module's **conclusion** rather than its bookkeeping, so D-089's across-function
  rule fails after nine straight predictions. Cost: one 11-min suite.

## North-star delta

- No obstacle, clearance or near-miss number moved — still one scene
  (`cafe_freezing_v0`), still `transfers_to_ab_scene = False`.
- The `w_voo` operating region is now **bounded on both sides at 2.5x finer
  resolution**: usable at `5`, gone by `8`. That is the tightest statement this
  branch has about where the epistemic channel can be turned up at all.
- One live arm recovered: the ceiling's two sides are `6.485x` apart, not
  `11.96x`, so a shared temperature is no longer excluded by arithmetic.

## Key learnings

- **A bracket is never tighter than the ladder that produced it, and neither is
  a ratio measured across one.** The cliff/slope question was asked about the
  *region*; the answer that mattered came back about the *gap*, because the gap
  is a quantity the rung spacing silently inflates.
- **Refining changed one reading's verdict and left the other's alone.** Same
  two rungs, same measurement: `usable_weights` was resolution-robust,
  `ess_drop` was not. Worth knowing which published fields are which.
- **The band-membership call needed no threshold.** `local_exponents` shows the
  crossing rung is `11x` steeper than its neighbours, and nothing in the
  verdict reads it — which is what keeps this from being another declared bar.

## Recommended next 1–3 priorities

1. Refine `lam = 0.8` and `1.2` at `w_voo ∈ {8, 12}` (4 runs, ~11 s) and re-take
   `gap_trend` at uniform resolution — `any_lam_fits_band` is currently a
   mixed-resolution reading and that is not a legal comparison (D-019).
2. Test the shared-rung question directly now that arithmetic permits it: is
   there a `lam` holding `w = 5` and `w = 8` in band at once? The premise is
   false, so this must be measured, not derived.
3. Buy back the 5 withdrawn `inert_surface` exemptions — **eighth** consecutive
   cycle carrying it; it forced all-writes-before-suite again.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/calibrated_ladder.py, eval/mppi_sandbox/tests/test_calibrated_ladder.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
