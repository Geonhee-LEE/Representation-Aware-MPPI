# Doubling the seeds does not resolve the two rows — and retracts the lean D-234 read off them

- **Cycle**: 2026-08-13 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-2` Widen `cafe_convoy_v0` / `cafe_head_on_v0` at `w_risk=0` past n=6
- **Phase**: P5
- **Status**: in_progress

## What I tried

- Walked the **full 2x2** of `cafe_convoy_v0` and `cafe_head_on_v0` at seeds
  0..11 (`lam = 0.8`, same scenes/temperature/resampler as D-234), not just the
  unresolved bottom row — so both rows are read at one `n` and the recorded
  6-seed cells are a **prefix** rather than a second measurement.
- Checked that prefix cell by cell before reading anything: all 8 cells of both
  scenes reproduce `WALK_CONVOY_6` / `WALK_HEADON_6` exactly.
- Recorded the walks as `WALK_*_12` + `*_12_REACHED`, added
  `cafe_family_steps_12` / `cafe_family_verdicts_12` / `unflipped_row_lean`.
- Fixed `three_arm`'s docstring table (STATE #1) — the stale 3-scene `SIGN_FLIP`
  summary — in the same edit, since it is the same claim surface.

## What worked / what failed

- **The rows still do not resolve.** Both `w_risk = 0` rows are `NOT_SEPARATED`
  at n=12 exactly as at n=6; both scenes stay `PAIRED_CONDITIONAL`. D-234's
  limit (i) is answered in the negative: these rows were not underpowered-with-
  a-direction, they have no direction to find at this `n`.
- **The lean does not survive, and that is a retraction.** D-234 read both means
  as positive (+0.0159, +0.0040) and built a claim on the sign — that the
  unpaired negative row *disagrees* with the paired reading rather than being a
  weak version of it. At n=12 both cross to **negative** (-0.0021, -0.0028) and
  the seed majorities go with them (4+/2- → 5+/7- and 6+/6-, p=0.774 / 1.000).
- **The top row got sharper, which D-234 predicted it could not.** Both top rows
  were unanimous at the n=6 sign-test floor p=0.031; at n=12 they are 11+/1- and
  p=0.006, CI still clear of zero. The floor was a property of `n`, not of the
  evidence — so "more seeds buy nothing here" was wrong about which row.
- 12/12 completion in all 8 cells, so no reading was bought by freezing.

## North-star delta

- The branch's surviving generalization — `w_ped` beside the risk term helps —
  is now carried at **p=0.006 on two scenes** instead of at the n=6 floor.
- One published sub-claim retracted at a cost of ~6 min of sim. Net movement
  toward "perfect obstacle avoidance" is zero; this is measurement hygiene on
  the table that will be quoted, not new avoidance capability.

## Key learnings

- **A point estimate inside an unresolved row is not a finding.** D-234 was
  careful to call the rows `NOT_SEPARATED` and then attributed a direction to
  them anyway via the mean's sign. The verdict was right and the sentence next
  to it was not; six seeds is where that distinction is cheapest to lose.
- **"More seeds buy nothing here" needs to name the statistic.** It was true of
  the sign test's floor and false of the CI, and D-234 applied it to the wrong
  row — it deferred the top rows and widened the bottom ones, when the top rows
  were the ones with headroom.
- The prefix discipline paid for itself again: because 0..5 reproduced exactly,
  the reversal is attributable to seed count and to nothing else.

## Recommended next 1–3 priorities

1. **Stop widening this 2x2.** Both remaining rows are unresolved in a way that
   n=12 shows is not a power problem at this effect size; the next seed is the
   most expensive information on the board.
2. Re-read whether any *other* branch claim rests on a point estimate inside a
   `NOT_SEPARATED` row — same defect class as the one retracted here.
3. Propose a capability successor to D-225: the instrument track is closed and
   nothing on the board adds avoidance machinery.

## Suite: red, and the cycle stopped rather than pushing

`2733 passed, 158 skipped, 1 failed` — `test_loop_reach.py::
test_recorded_reading_covers_exactly_todays_targets`. **The guard is correct
and the finding is mine**: the new tests above added population-claim loops
(over cells, over scenes) that `loop_reach.READING` has never measured, which
is exactly the corpus-grew-a-claim case that test exists to catch. Same class
as the red this branch took on 2026-08-11.

The documented fix is `loop_reach report` + update `READING`. It is quoted at
~90 s; it did not finish inside 200 s, and by then the cycle was at 32 min with
`cycle_wallclock` already reading `SUITE_UNAFFORDABLE`. Re-measuring would have
changed the tree and staled the receipt, so a green push needed a **second**
full suite (~8.5 min) that the budget does not contain.

So this cycle **does not push**, deliberately. `push_preflight check` would
refuse this receipt and it is right to. The work is committed at `a88b78a`;
next cycle's Phase 1 `cycle_artifacts stranded` will name this journal, and
clearing it is one `loop_reach report` + one suite — which is the cheap,
designed hand-off rather than a bypass.

## Artifacts
- PR: **not pushed this cycle** — commit `a88b78a` local on `autoresearch/p3-epistemic-shadow-cost-critic` (PR #67 open, unchanged)
- Files touched: eval/mppi_sandbox/paired_step.py, eval/mppi_sandbox/three_arm.py, eval/mppi_sandbox/tests/test_paired_step.py, docs/decisions.md
- TSV row appended: yes (`results/p3-epistemic-shadow-cost-critic.tsv`, status=in_progress)
