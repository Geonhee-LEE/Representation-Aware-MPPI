# ESS becomes a field of the run, not a probe you remember to write

- **Cycle**: 2026-08-02 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-item-1` Make ESS a first-class field of every sandbox A/B
- **Phase**: P3
- **Status**: keep

## What I tried

- `StockMPPI.command` now appends `1/sum(w^2)` to `self.ess_log` at the point
  it normalizes the weights — 2 lines, and it covers the whole registry
  (`risk_mppi` inherits `command`; `cbf_mppi` delegates to `.nominal`).
- `ab.ArmRun` gains `median_ess` / `n_samples` / `ess_in_band`; `ab.SweepStats`
  gains the same three; `ab.ess_band(K)` owns Q-026's `0.05K … 0.5K`; and
  `assert_ess_in_band(runs, label)` is the opt-in guard mirroring
  `assert_all_reached`.
- Retired the `_cost`-wrapping probe in `test_softmax_temperature_audibility.py`
  — it now reads `ArmRun.median_ess`, and `ESS_BAND` is `ab.ess_band(K)`.
- 8 new tests in `test_ab_harness.py` (new class, no existing assertion
  touched). Suite **94 → 102 passed + 1 xfailed**, 57 s.

## What worked / what failed

- ✅ **Recording beats reconstructing, and not only on style.** The retired
  probe re-derived `exp(-(cost-min)/lam)` itself, so it would have kept
  agreeing with a controller that had stopped weighting that way — it measured
  the formula, not the sampler. Four cycles hand-rolled that reconstruction.
- 🔴 **The arm-median ESS is a misleading verdict, measured.** `stock_mppi`,
  centred hazard, n=8:

  | `lam` | arm median | per-seed range | every seed in band? |
  |---|---|---|---|
  | 3.0 | 13.34 | 9.1 – 45.1 | **no** — 4/8 below the floor |
  | 5.0 | 33.09 | 23.1 – 92.7 | yes |
  | 8.0 | 77.65 | 58.1 – 223.6 | **no** — 2/8 above the ceiling |

  All three arm medians sit inside `[12.8, 128.0]`. A median-based check would
  have admitted **two of three** temperatures that leave half the seeds
  argmin-degenerate or near-uniform. So `ess_in_band` requires *every* seed.
- ✅ **`lam = 5.0` is the first temperature this scene has that is admissible
  at n=8** — all 8 seeds in band, all 8 reach the goal. 12:00's `lam=1.2` was
  picked against a seed-0 ESS.
- ✅ The guard is **opt-in**. The shipped `lam=0.1` puts every arm below the
  floor, so folding it into `summarize` would turn the suite red for exactly
  the re-baseline Q-032 defers until the queue drains.
- 🔴 **Not done**: `docs/deliberations.md` still says Q-026 is a proposal, and
  Q-017/Q-034 still carry superseded text. Deferred on purpose — that file is
  in #66's conflict set (STATE item #4 is unchanged by this cycle).

## North-star delta

- **The measurement substrate got its missing control.** Every P3 claim from
  here on reports the ESS it was measured at; "channel X changes behaviour" is
  now falsifiable in the one way it previously was not.
- **No movement on obstacle avoidance or path tracking itself** — this is
  instrumentation. Its value is that it retires a class of wrong answer
  (Q-017 was answered wrongly twice by reading a controller hyperparameter as
  a property of the scene) rather than producing a new number.
- The 5× per-seed ESS spread is a *new* constraint on the eventual re-baseline:
  picking one `lam` per scene is not enough; it has to be picked against the
  seed ensemble.

## Key learnings

- **A verdict computed from an aggregate is not the aggregate's verdict.**
  Arm-median ESS in band, arm not in band, on 2 of the 3 temperatures tried.
  The same shape as this project's other nuisance controls — the mean paired
  gap that looked decisive at 15/24, the clearance that was freeze.
- **"Unknown" has to raise as loudly as "out of band."** A controller that
  reports no ESS would otherwise be the way around the guard, so `None` is
  sticky across a sweep and `assert_ess_in_band` rejects it.
- **The fourth hand-rolled copy is the signal to move it into `ab`.** Seed,
  speed, completion, and now temperature — each was written ad hoc in the
  cycle where a result had just died on it.

## Recommended next 1–3 priorities

1. **Re-measure Q-017 at `lam = 5.0` with `assert_ess_in_band`** — 12:00's
   `lam=1.2` verdict rests on a seed-0 ESS that the n=8 sweep says is
   out-of-band for most seeds. This is the first claim the new guard can void.
2. **Measure Q-034's upper end admissibly** — `lam=30` reaches ESS ~194 with
   `all_reached=False` across the registry, confirming 12:00's inadmissibility
   at n=3 on a second scene. Give it a duration budget or declare it unmeasurable.
3. **Commit the orphaned journal entries** (now 25) and fix the ordering bug in
   `scripts/prompts/auto_research.md` that strands them. 100 % safe-surface.

## Artifacts

- PR: #67 (already in the review queue — no new review bandwidth consumed)
- Files touched: `eval/mppi_sandbox/ab.py`,
  `eval/mppi_sandbox/controllers/stock_mppi.py`,
  `eval/mppi_sandbox/tests/test_ab_harness.py`,
  `eval/mppi_sandbox/tests/test_softmax_temperature_audibility.py`
- TSV row appended: yes (`sandbox:pass=102/102`, keep)
