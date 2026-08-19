# The max was never still climbing — the cheap exit from the fork is closed

- **Cycle**: 2026-08-20 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: research-flagged (Phase 0 candidate) — tail-stability check before authorising the 512 rollouts
- **Phase**: P3
- **Status**: keep

## What I tried

- `research/feed.md`'s newest entry (Krishnamachari `2605.00428`, §17) offered the
  cheapest hypothesis yet against STATE's standing fork: `cte_max` is a per-run
  **extreme order statistic**, and the paper says tail statistics are limited by
  the *within-run* sample count, not the run count — so the 512 rollouts would
  buy a `2.10x` smaller floor on a quantity that stays unreadable.
- The feed named the test and named it free: on the runs already reachable,
  count CTE timesteps per run and check whether `max|cte|` is still climbing.
- Built `eval/mppi_sandbox/tail_stability.py` — harvests the CTE **series** (not
  just the scalar) for 8 arms × 2 scenes at seed 0, and records per run:
  `n_steps`, `cte_max`, `half_max / cte_max`, and the even/odd split-half gap of
  the maximum. Scenes are the binding pair for the `1.97x` separation:
  `cafe_convoy_v0` (excited min, the scene the fork is priced for) and
  `city_curved_v0` (unexcited max, control).
- 9 pytest cases pin the three findings, the drift check, and the threshold's
  real headroom.

## What worked / what failed

- **The hypothesis is refuted, by the paper's own test.** `half_max / cte_max`
  is `1.0000` for **16 of 16** runs — every arm on both scenes attains its
  whole-run maximum *before the midpoint*. `argmax` lands at `0.068`–`0.410` of
  the run on the deciding scene. Doubling within-run samples would not have
  moved `cte_max` in a single run.
- **The estimator-class story does not survive where it was supposed to bite.**
  On `cafe_convoy_v0` the arm spread (`0.1187`) is **198x** the median split-half
  instability and **66x** the worst arm's. The maximum is stable to a fraction of
  a percent of what a bar must resolve.
- **The instability that exists sits on the wrong scene.** `city_curved_v0` —
  the scene nobody proposed to grade — is `6.1x`/`2.1x`, i.e. **31x** less stable
  relative to its own spread. `tail_limited()` returns it alone.
- **A first pass shipped two wrong magnitudes and a miscalibrated test bar.**
  The prose said `194x` (actual `197.8x`) and `15x` (actual `31x`), and the
  "10x stricter" guard failed because the worst arm only clears `5x`. Caught by
  running the module and the test rather than by reading the draft.

## North-star delta

- **An option was removed, not added.** The fork had a possible third exit —
  "the seed axis is the wrong axis, so decline to buy" — which would have let the
  branch skip the expensive decision on a technical argument. That exit is now
  closed by measurement. 물체회피/경로추종 numbers themselves are unmoved.
- Zero new information destroyed and zero rollouts *spent on the fork*: the
  harvest is ~90 s of sim on the pair already established as binding.

## Key learnings

- **The feed's cheapest hypothesis was worth testing precisely because it was
  cheap, and it was wrong.** Four cycles read the `clearance` vs `cte_max`
  asymmetry as evidence about scenes, bars, geometry, arms, then seeds; the
  paper supplied a fifth reading (estimator class) that is now measured and
  does not hold. Reading #6 should not be reached for without the same test.
- **Even/odd split-half understates instability on an autocorrelated series** —
  adjacent CTE timesteps are near-duplicate poses, the same autocorrelation the
  feed's Islam entry warns inflated that paper's `p = 0.0016`. So findings #2/#3
  are **lower bounds**. The refutation deliberately rests on finding #1, where
  `half_max / cte_max = 1.0000` is a statement about *where* the max lands and
  autocorrelation cannot manufacture it.
- **A scope note that names which finding carries the weight is worth more than
  one that lists caveats.** Two of the three findings here are construction-limited;
  saying so explicitly is what keeps the module quotable at its real strength.

## Recommended next 1–3 priorities

1. **Price `s` before the 512** — the same feed entry's §17 gives `n ≈ 8/(Δ/s)²`
   and the project has never measured `s`. A 10-seed pilot on the deciding scene
   prices both prongs; 32 seeds is the `d≈0.5` point and may be over- or
   under-kill.
2. **Audit the branch for mixed floor denominators** (STATE #1, carried) — every
   `Nx` names which floor it was divided by. Zero rollouts.
3. **Adopt §18's exclusion protocol** while the run count is still small —
   pre-declared criteria, never exclude on the outcome variable, report counts.

## Artifacts

- PR: #67 (already open — D-140: continuing on an open PR adds nothing to the queue)
- Files touched: `eval/mppi_sandbox/tail_stability.py`, `eval/mppi_sandbox/tests/test_tail_stability.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: pending
