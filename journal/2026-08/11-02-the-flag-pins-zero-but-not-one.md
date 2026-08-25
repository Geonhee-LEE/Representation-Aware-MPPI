# The admissibility flag pins `k = 0` exactly and `k = 1` not at all

- **Cycle**: 2026-08-11 02:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — recover the two missing per-seed ESS populations
- **Phase**: P5
- **Status**: keep

## What I tried

- STATE #1 asked for the two missing per-seed ESS populations (`geometric_null`
  head_on `w=75`, convoy `w_geom=5.0`) to be recovered from recorded walks, so
  D-184's magnitude interval would narrow from its single `k=1/32`.
- Before recovering anything, checked what the interval actually consumes:
  `wilson_interval(k, n)`. It takes **counts**, never per-seed values. So the
  populations were never the binding constraint — the *counts* are.
- Shipped `WalkCount` / `PooledReading` / `recorded_walk_counts()` /
  `pooled_reading()` / `pooling_effect()` in `seed_count_licence.py`: every
  walked rung on disk, with `k` bounded as tightly as disk allows, pooled into
  one **partially identified** set for `p`.
- 11 tests. 0 sim runs — arithmetic over recorded floats throughout.

## What worked / what failed

- 🔴 **STATE's premise was wrong in the cheap direction, for the third cycle
  running** (Q-129 → D-183, D-184's own base, now this). The ask was priced as
  recovering two populations; the work was a count.
- 🔴 **The finding is that the `ess_in_band` flag fails asymmetrically.**
  `True` pins `k = 0` **exactly** — an all-seeds gate that passed says every
  seed was in band. `False` pins only `k ≥ 1`. So the walks that carry
  information about the rate are precisely the ones that withhold its
  magnitude. Four walks on disk: one population (`k=1/32`), one admissible flag
  (`k=0/32`, exact), two refused flags (`k ∈ [1, 32]` each).
- 🔴 **Pooling therefore moves the two ends in opposite directions** —
  `POOLING_RAISES_FLOOR_ONLY`, a verdict worth naming because it is not what
  "narrow the interval" leads one to expect. Pooled `k ∈ [3, 65]/128` gives
  `p ∈ [0.0080, 0.5929]` against the single population's `[0.0055, 0.1574]`.
- 🟢 **The floor is the end that was worth buying.** D-184's side finding was
  that strict positivity of the floor on `p` is what makes `(1 − p)ⁿ` strictly
  decreasing rather than possibly flat. Pooling raises it **1.45×**
  (0.0055 → 0.0080), so the ceiling on the gate's pass probability drops
  **0.8372 → 0.7733**. That bound is now supported by 128 seeds, not 32.
- 🟢 The exact `k = 1` values sit in `geometric_null` **comments** ("seed 25 at
  ESS 134.15"). A comment is not a measurement, so they are not consumed;
  head_on comes back bounded, and a test pins that it does.
- 🟢 `loop_reach` did **not** fire — the streak of two consecutive cycles
  losing the D-181 deadline to it is broken. Reason is mechanical: these tests
  assert over comprehensions rather than looping asserts, so no new population
  claim entered the corpus. Reading taken at minute 5, per STATE #3.

## North-star delta

- **No movement, and none is claimed.** No controller, representation, or
  dynamics code; `unsafe_rate` 0.0000 / `min_clearance` 0.3579 / `success_rate`
  1.0000 unchanged; census attribution coverage still **0/6**, `NO_GRADED_RUNG`.
  0 sim runs.
- What moved is one bound: the gate's pass probability at `n = 32` is now
  ceilinged at **0.7733** on 128 pooled seeds rather than 0.8372 on 32.
- What did **not** move, and now has a name for why: the ceiling on `p`. No
  amount of re-reading recovers it, because `k_max` is unbounded by disk.

## Key learnings

- **Check what the estimator consumes before recovering data for it.** Three
  cycles in a row have now costed a fix against the wrong quantity. The pattern
  is stable enough to plan against: read the function signature first.
- **An admissibility flag is not a measurement of the thing it gates on.**
  Recording `ess_in_band=False` is enough to refuse a walk and not enough to
  quote a rate — and the branch has been quoting rates from walks like these.
- **Partial identification is the honest shape here**, not a wider Wilson
  interval. `POOLED_FLOOR_ONLY` says which end is informative; folding it into
  one interval would quote a bound as an estimate.
- What would change my mind: recording the two refused walks' per-seed ESS
  would flip `POOLED_FLOOR_ONLY` → `POOLED_IDENTIFIED` and pin the ceiling.
  A test prices exactly that, so the ask is still worth doing — for the
  ceiling, not for the interval as a whole.

## Recommended next 1–3 priorities

1. **Record the two refused walks' per-seed ESS** — now priced precisely: it
   buys the ceiling on `p`, and `test_recording_the_two_populations_is_what_would_identify_it`
   already asserts what it would produce. Needs the runs re-read, 0 new sim.
2. **Point the constitution's Phase-3 pin check at `inert_surface pins`** and
   correct the stale 4a-ter prose. Doc-only, unclaimed for 12 cycles.
3. **Q-131 stays blocked** on coverage leaving 0/6 — unchanged.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, PR #67)
- Files touched: eval/mppi_sandbox/seed_count_licence.py, eval/mppi_sandbox/tests/test_seed_count_licence.py, docs/decisions.md
- TSV row appended: yes
