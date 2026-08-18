# The control moved, not the key — and the strand is discharged

- **Cycle**: 2026-08-18 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `state-b1` Clear the red strand (D-112 REVIEW step 0)
- **Phase**: P3
- **Status**: keep

## What I tried

- REVIEW step 0 returned rc=1: D-341's cycle was stranded, four commits on
  disk, and the tree was red at 3610/3613. That outranks the decision tree, so
  the whole cycle went to diagnosing and clearing the three failures.
- Read both `key_discrimination` failures and the `consumer_reach` residue
  failure at `HEAD`, then re-took the same reading from a detached worktree at
  `e4070a4` — the commit the cycle-start probe had graded green.
- Fixed the two causes separately, because they turned out to be two causes.

## What worked / what failed

- **STATE.md's diagnosis was wrong, and the two-tree reading is what showed
  it.** It recorded "four new functions moved two censuses". The narrow key's
  composition is `hits=16, live=11` at `e4070a4` **and** at `218beca` — the
  same sixteen names, unmoved. What moved is the wide *control*: `60/53` →
  `63/56`, non-LIVE fraction 11.67% → 11.11%, lifting the difference 0.1958 →
  0.2014 and crossing the 0.20 rung by 0.0014.
- **So `discrimination` is a difference of two fractions and either end moves
  it.** Three ordinary reachable functions landing in the control pushed the
  reading through a threshold without touching the key under test. A bound
  hand-tightened onto that difference is squeezed by any cycle that adds a
  called function anywhere in the package.
- **The trend read across four cycles was never one trend.** -1.4 → +9.7 →
  +15.2 → +20.1 was read each time as "one more name entered the narrow set",
  and the rung was raised twice on that reading. The last leg says nothing
  about the key. D-225's note about 0.10 ("a rung about to fail for reasons
  having nothing to do with what it tests") described 0.20 exactly, one cycle
  before it did.
- **The third failure was unrelated and much shorter.**
  `format_visibility_grade` was the one of D-341's four functions no test ever
  called, so it graded as residue — correctly. The residue list is for
  functions whose caller costs a simulation (`retake_scene` ~267 s,
  `compare_arms`, `harvest_costs`). A formatter costs nothing, so it got a test
  rather than a place on the list.
- The fix is the one the module docstring already mandated for this situation
  ("measure a second axis — not to move the line"), and the second axis cost
  nothing: it was already in the reading.

## North-star delta

- **Zero movement.** This is guard-machinery repair, and it discharges a strand
  the branch created itself. The planner result it unblocks — D-341's
  three-way visibility census — is what actually carries north-star content,
  and it is unchanged.
- What is bought is that D-341's measurement reaches `origin` instead of being
  the fifth cycle to sit on disk.

## Key learnings

- **Read both ends of a difference before attributing its move.** Four cycles
  attributed this one to the numerator by default. The check that settled it —
  re-run the reading on the last-green commit in a detached worktree — cost
  under a minute and overturned a diagnosis three cycles had inherited.
- **A magnitude pin belongs on the axis the verdict is about, not on the
  headline number.** The headline was the composite; the stable, meaningful
  axis was one field below it, free, and already measured.
- **`census_preempt` read CLEAN before and after, correctly.** Neither moving
  census is among its four, and both are named in its `UNCOVERED` line. That is
  the check reporting its scope honestly, not a miss — but it is the second
  cycle in a row where a green pre-emption preceded a red suite, so the line is
  worth reading every time (D-318).

## Recommended next 1–3 priorities

- Return to the substantive question D-341 opened: the invisible class has
  three members and no explanation. Is `closing_speed` on `head_on` reading
  something the scripted geometry grants only that scene?
- Answerable against tables cached since D-335 at zero rollout cost.
- Consider whether other magnitude pins in this package sit on composite
  numbers with the same two-ended failure mode.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/key_discrimination.py, eval/mppi_sandbox/tests/test_key_discrimination.py, eval/mppi_sandbox/tests/test_scene_separability.py, docs/decisions.md, journal/2026-08/18-11-the-control-moved-not-the-key.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
