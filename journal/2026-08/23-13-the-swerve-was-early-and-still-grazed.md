# The swerve was early — and it still grazed

- **Cycle**: 2026-08-23 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: Q-187 timing reading (STATE next-actionable #1)
- **Phase**: P5
- **Status**: in_progress (STRANDED — suite red on one pin, repaired but unpushed)

## What I tried

- Built `eval/mppi_sandbox/avoidance_timing.py`: per-seed **lead time**
  `t_closest − t_deviate` on `cafe_obstacle_crossing_v0`, scored over a
  **ladder** of deviation thresholds (0.10 / 0.20 / 0.30 / 0.40 m) so the
  verdict is not an artefact of one hand-picked value.
- Ran both D-442 arms (`w_heading` 0 and 32), 32 integrations, ~20 s, **zero
  source change to the controller** — the reading Q-187 asked for.
- 14 unit tests pinning the *scoring*, including the cross-check that
  `clearance_series(...).min()` equals the scalar `obstacles.min_clearance` it
  generalises.

## What worked / what failed

- **Q-187 answers (a)-refuted, and it is not close.** At the 0.10 m threshold
  **16/16 seeds in both arms** deviate *before* closest approach, by
  **0.9–2.7 s** (w=0) and **0.9–2.5 s** (w=32). Across all four thresholds and
  both arms, **reactive count = 1 of 122 scored rows**, and that one is a
  0.0 s tie. There is no late-swerve to fix.
- **The free catch is sharper than the headline.** Clearance at closest
  approach is **0.00–0.06 m in both arms** — the robot deviates ~1.5 s early
  and *still* grazes. Early **and** ineffective.
- That range independently reproduces D-426's default-arm crossing clearance
  (0.0003–0.056) from a separately-derived series, which is a real cross-check:
  two derivations of the same quantity agree.
- **The threshold ladder paid for itself.** `never_deviated` climbs 0 → 8 → 13
  (w=0) as the bar rises to 0.40 m: half the seeds never leave the path by
  0.3 m at all. The deviation is not just ineffective, it is **small**.
- **The suite came back red on one test, and it was mine**:
  `test_lam_dependence::test_two_sites_are_not_tests_and_neither_bills_a_sim`.
  `measure_arm` is a fifth non-test lam site, and that pin lives in
  `test_lam_dependence.py` — a file `census_preempt` covers in **neither** its
  covered list nor its `UNCOVERED` list. That is the D-436 shape, a **fourth**
  time: `loop_reach` (D-317), `consumer_reach` (D-344), `default_lam_sites`
  (D-436), now `lam_dependence`.
- The repair is done and verified (6.76 s, passes including the `SILENT`-kind
  assertion — the `raise`-not-`assert` pattern D-443 established held). But it
  landed *after* the receipt, so `push_preflight` reads `STALE` and refuses.
  **Nothing reached origin.** Next cycle's step-0 `stranded` reading will name
  this commit; clearing it costs exactly one suite and no investigation.
- Budget blown: the suite start slipped past the `cycle_wallclock` 8m00
  advisory by 2m30, and the red pin cost the rest.

## North-star delta

- **One open question closed on measurement, not argument**: the avoidance
  response's *timing* is excluded as the heading-residual lever. That removes
  horizon / lookahead / `collision_margin` re-tuning from the menu before a
  cycle was spent on them — D-426 had already priced that knee at 1:1.
- No change to any pass count: this is a reading, not a fix. Net matrix
  unchanged.

## Key learnings

- Q-187's dichotomy was **incomplete**, and the data shows it. (a) timing is
  dead and (b) reference is *not* thereby proven — the measurement exposes a
  third branch the question never named: the response is anticipatory but
  **too small / wrongly aimed**. Filed as Q-188 rather than quietly folded
  into (b), because folding it in is how a dichotomy launders itself into a
  conclusion.
- Reporting an ordinal question with a sign count instead of a mean was the
  right call on a scene D-429 already measured as bimodal — the per-seed leads
  span 0.9–2.7 s and a mean would have reported a middle no seed occupies.
- A vacuity bucket earned its keep immediately: `never_deviated` was not noise
  to drop but the finding that the deviation is small in magnitude.

## Recommended next 1–3 priorities

1. **Q-188 magnitude reading** — per-seed peak lateral deviation vs the
   lateral offset actually *needed* to clear the actor band. Same 32 runs,
   zero new sim; separates "aimed wrong" from "too small".
2. **Q-186 (ii) cheap de-contamination** — `readings()` twice, take `min`,
   compare to standalone 7.63 s; re-tighten the cost guard from 40.0.
3. Do **not** touch horizon or `collision_margin` — this cycle is the number
   Q-187 said to see first, and it says that axis is not the lever.

## Artifacts
- PR: #67 (open, continuing under D-140) — **this cycle's commits are NOT on it yet**
- Files touched: `eval/mppi_sandbox/avoidance_timing.py`, `eval/mppi_sandbox/tests/test_avoidance_timing.py`, `docs/decisions.md`, `docs/deliberations.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
