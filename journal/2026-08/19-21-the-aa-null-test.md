# The A-A null test: both cross-track claims sit below the gap a zero effect manufactures

- **Cycle**: 2026-08-19 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-aa-cal` Run the A-A calibration before widening to more seeds (Phase 0 candidate)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the 20:00 feed's suggested TODO (Islam et al. 2017, `1708.04133`) rather
  than STATE #1. The suggestion was to run an A-A test — one identical
  configuration, split in half — before spending more seeds, on the ground that
  it is strictly cheaper and it is the thing that says whether the seeds already
  spent are enough.
- Found the test needs **no rollouts at all**: one arm's eight seed values in
  `excursion_seed_width.SEED_ENSEMBLE` (D-370) and `clearance_census.SEED_ENSEMBLE`
  (D-332) are already eight draws from a single configuration. Splitting 8 into
  two 4s gives `C(8,4)/2 = 35` splits — the *entire* null distribution, enumerated
  rather than sampled.
- New `eval/mppi_sandbox/aa_calibration.py` + 26 tests. Compares each scene's
  largest true between-arm gap against its own null floor at two readings: the
  p95 quantile and the adversarial max over all 35 splits.

## What worked / what failed

- **The calibration separates the graded column from the vacuous one**, which is
  what a working null test should do. `clearance`/`cafe_freezing_v0` clears its
  floor by `6.28x`; `cte_max` clears it on **neither** scene and by **neither**
  reading — `cafe_convoy_v0` is `0.96x` its p95 floor, `city_curved_v0` `0.35x`.
- **The number D-370 used to refute D-363 is itself below the floor.**
  `ROBUST_SEPARATION` is `(0.0612, 0.0730)`; the max floors of the scenes those
  came from are `0.0673` and `0.0760`. Both endpoints are under. The `0.0118`
  inversion D-370 reported is finer than the resolution that produced it.
- Guessed the p95 index wrong in scratch (`g[32]` vs ceiling rank `g[33]`), which
  moved convoy from `INSIDE` to `BELOW` — a stronger finding, caught only because
  the module recomputes rather than copying the scratch number.
- First empirical test of the `1/sqrt(n)` scaling **failed** — I subsampled by
  duplicating four seeds into eight, which forces pairing and is not a 4-seed
  null. Replaced it with the exact permutation identity
  `rms = 2*sigma_pop/sqrt(n-1)`, verified to `1e-12` on all 24 arm-rows.
- `census_preempt` caught both drifts at the stage (guard tally `128->129`,
  two unrecorded `loop_reach` targets) — seconds instead of a red 22-min suite.
- **And then lost a 22-min suite to a census it does not cover.** Registering the
  new guard, I inserted it into `test_and_shaped_guards_are_exactly_these_four`'s
  literal instead of the pool — a set my own comment argued it does **not**
  belong to (`0 not in group` is a canonicalisation, not an `&`). `guard_tally`
  read clean throughout because it counts the `pool` fixture, not that literal.
  This is precisely the class D-318's `UNCOVERED` line warns about: the pre-empt
  names four censuses it omits, and the AND-set pin is a fifth that is neither
  listed nor covered. The gate refused on the red receipt, which is it working.
- **Blew the wall clock.** `cycle_wallclock elapsed` said the suite had to start
  by 9m12; the census repairs put the start past 20m. Chose the overrun over a
  strand.

## North-star delta

- No movement in metres. This cycle **removes** a claim rather than adding one:
  the cross-track (경로추종) grading column now carries a measured resolution
  floor that its own best signal does not clear.
- 물체회피 (clearance) is **strengthened by contrast** — it is now the one column
  demonstrated to sit above the noise its own harness generates, by `6.28x`.
  The three user-blocked bar declarations are untouched and better founded.
- The branch's standing 384-rollout next action is re-priced as answering the
  wrong question: more scenes at eight seeds all land under floors of the same
  size.

## Key learnings

- **A caveat about seed *scope* is not a caveat about seed *resolution*.**
  `SEED_SCOPE` has asked "is one seed enough?" for eight cycles and never "is a
  number this size readable at all?". D-370 was careful in every way the branch
  knows how to be careful and still quoted two numbers a zero effect reaches.
- **The null test is cheap and was available the whole time.** It needed no new
  rollouts, only the recognition that a single arm's seed row *is* an A-A
  experiment. Two cycles (D-368, D-370) harvested exactly this data for other
  purposes.
- **The per-scene lesson replicated.** Islam et al. get spurious separation on
  one environment and not another; here the floor-to-gap ratio is `1.06x` on
  convoy against `4.66x` on curved. So a calibration licenses nothing about a
  scene it was not run on — six scenes remain uncalibrated.
- The guard registry gained its first **canonicalisation**-shaped entrant in
  four (`0 not in group`, deduping complementary splits), breaking a three-cycle
  run of baseline-restriction entrants. The run was a property of what those
  cycles measured, not of the registry.

## Recommended next 1–3 priorities

1. **Spend 512 rollouts on 32 seeds for the binding pair**, not 384 on six more
   scenes at eight. The exact identity says this shrinks the floor `2.10x`; it
   is the only one of the two purchases that can decide the claim.
2. **Carry the floor to the sites that need it.** `excursion_tracking.SPREAD_SEPARATES`,
   `SEED_SCOPE` and `excursion_seed_width.VERDICT` all still read as if the
   comparison were decidable. This is the fourth consecutive cycle to name an
   "answer sits beside the question, unjoined" gap.
3. **Calibrate `cafe_head_on_v0` before the user declares its bar.** Its
   `(0.0043, 0.1044)` interval is the top user-blocked item and the scene is
   `UNCALIBRATED`; clearance cleared its floor on `freezing` but that transfers
   to nothing.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/aa_calibration.py, eval/mppi_sandbox/tests/test_aa_calibration.py, eval/mppi_sandbox/loop_reach.py, eval/mppi_sandbox/tests/test_guard_reflexivity.py, results/p3-epistemic-shadow-cost-critic.tsv, docs/decisions.md
- TSV row appended: yes
