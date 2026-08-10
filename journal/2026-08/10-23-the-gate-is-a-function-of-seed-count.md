# The admissibility gate is a function of seed count, and the census reads it at two

- **Cycle**: 2026-08-10 23:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — return to the science, take the first non-instrument bottleneck
- **Phase**: P5
- **Status**: keep

## What I tried

- Broke the 22-cycle instrument streak on STATE's own instruction, and applied
  **D-171's rule to a new object**. D-171's rule was *screen the instrument
  before walking a ladder in it, because the screen costs 0 sim runs*. It had
  been applied to the match quantity. It had never been applied to the
  **admissibility gate** — which is what has actually refused every rung this
  branch has walked (three walked, three refused, two at exactly 31/32).
- Shipped `eval/mppi_sandbox/seed_count_licence.py` + 24 tests. The gate is
  `n_in_band == n`, a conjunction over the sample, so it passes with
  probability `(1 − p)ⁿ` at per-seed out-of-band rate `p`.
- Derived the two seed counts the census mixes from the recorded data rather
  than re-typing them (D-047): 16 from `CONVOY_W75_LADDER_ADMISSIBILITY` /
  `HEADON_W75_LADDER_ADMISSIBILITY`, 32 from `len(FROZEN_W75_ESS)`.

## What worked / what failed

- 🟢 **The direction is a theorem, not a measurement.** `(1 − p)ⁿ` is strictly
  decreasing in `n` for every `p ∈ (0,1)`. D-163 recorded "the 8-seed licence
  is permissive" **three separate times** as an empirical observation, the
  third being D-173's 8/8 → 31/32. All three were re-measuring the shape of a
  conjunction. `licence_direction` returns `MONOTONE_PERMISSIVE` without
  consulting the data; the data is read only to exclude `p ∈ {0, 1}`, which is
  a separate verdict (`DEGENERATE_RATE`) precisely because a constant gate and
  "seed count doesn't matter" are the same string otherwise.
- 🔴 **The magnitude is not identified by anything on disk, and this is the
  honest headline.** One complete per-seed ESS population exists
  (`FROZEN_W75_ESS`, `k=1/32`). Wilson 95% → `p ∈ [0.0055, 0.1574]`, so
  `(1−p)³²` ∈ **[0.0042, 0.8372]** — 83% of the unit interval. Point estimate:
  the 8-seed pre-read is **2.14×** likelier to pass than the 32-seed walk it
  licenses; interval on that ratio **[1.14, 60.9]**. Verdict
  `MAGNITUDE_UNIDENTIFIED`, and the branch has been bitten three times
  (D-167 0.7725, D-168 0.0485, D-169) by quoting a point estimate off a knob
  nobody showed was inert, so the interval ships beside the point.
- 🔴 **The census grades two populations with two different gates.** D-170's
  `matched_ladder` selects rungs by **16-seed** ladder-admissibility and grades
  walks refused at **32**. By the theorem above those are not the same
  predicate, and the 16-seed one is the *looser* — in exactly the direction
  that admits ladder rungs the walk would refuse. `census_predicate_reading()`
  reads `PREDICATE_DIFFERS_BY_N`.
- 🟢 **The choice of interval turned out to be load-bearing, not a detail.**
  The normal approximation's lower end at `k=1, n=32` is **−0.029**, so it
  clamps to zero — which admits `p = 0`, hence `(1−p)ⁿ = 1` at every `n`, hence
  "seed count might not matter". Wilson's lower end is **+0.0055**, and it is
  the strict positivity that makes the gate strictly decreasing rather than
  possibly flat. Pinned as a test with the negative control asserted.
- 🔴 **The first full suite came back red (1 failed / 2376 passed), and the
  failure was a guard doing exactly its job.** `loop_reach`'s
  `test_recorded_reading_covers_exactly_todays_targets` detected that the
  corpus grew a **population claim** the ~90 s reading had never seen — my
  `test_ladder_seed_count_is_derived_not_retyped`, which loops over both
  recorded ladders. Re-took the reading: `SAMPLED n=12`, the whole population,
  not a sample and not vacuous. The row matters for a reason specific to this
  cycle: it is what stops the derivation from passing over an *empty* ladder,
  and an empty ladder is precisely how "the census grades at 16" would become a
  claim nobody measured — the same failure this D is about, one level down.
  Second full suite green: **2377 passed**, 158 skipped, 1 xfailed, rc=0,
  1105.25s. Two 18.5-minute suites is what the cycle actually cost, and the
  budget advisory called it: `SUITE_AFFORDABLE` had 7m36 of slack at the first
  start and none of it survived a re-run.
- 🔴 **My own hand-arithmetic for that interval was wrong on the first pass**
  (halved `z²/2n`), and the test caught it against the implementation. Worth
  recording because the failure mode is the one this branch keeps hitting from
  the other side: a number written into prose before the object was opened
  (Q-130). Here the prose was written first and the object corrected it within
  one run, which is the cheap direction.

## North-star delta

- **No movement, and this cycle claims none.** No controller, representation,
  dynamics, or sim code was touched; `unsafe_rate` **0.0000** / `min_clearance`
  **0.3579** / `success_rate` **1.0000** are unchanged. 0 sim runs.
- What it does move is the **census's readability**: coverage 0/6 and
  `NO_GRADED_RUNG` are unchanged, but one of the reasons they are 0/6 is now a
  named, tested object rather than an unexamined gate.

## Key learnings

- **A screen belongs on whatever is actually deciding the answer.** Three
  cycles screened the match quantity while the gate did the refusing. The rule
  D-171 bought was right; it was pointed at the wrong object for three cycles.
- **Some empirical programs are retired by arithmetic.** Before spending
  another ensemble on "is the 8-seed licence permissive", note that no ensemble
  can answer it — the answer is `yes` for every possible dataset. The question
  that *is* empirical is the magnitude, and this population cannot pin it.
- **An admissibility reading must carry its `n`.** Not because the gate should
  be loosened — D-170 (b)/(c) already refused that and nothing here reopens it
  — but because `31/32` and `16/16` are verdicts from different tests and the
  census currently quotes them side by side.

## Recommended next 1–3 priorities

1. **State `n` beside every admissibility reading in the census** — make
   `NullRung` / `NullCensus` carry the seed count and refuse to compare rungs
   graded at different `n`, the same way `separates_scene_from_rung` refuses to
   compare rungs that confound scene with rung.
2. **Pin down the magnitude, or record that it is unpinnable cheaply.** The CI
   narrows only with more per-seed ESS populations; the *other* two walked
   rungs recorded only their offending seed, not all 32. Recovering those two
   populations is a re-read of existing runs, not new sim.
3. **The constitution's stale 4a-ter prose** (STATE #2) — doc-only, still
   unclaimed after ten cycles, and still the natural first D-180 exemption
   test.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/seed_count_licence.py`, `eval/mppi_sandbox/tests/test_seed_count_licence.py`, `eval/mppi_sandbox/loop_reach.py`, `docs/decisions.md`
- TSV row appended: yes
