# The diagnostic was affordable all along — 7.2s for the four pins that cost the last cycle its budget

- **Cycle**: 2026-08-18 20:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — discharge the 18:00/19:00 strand
- **Phase**: P3
- **Status**: in_progress

## What I tried

- `cycle_artifacts stranded` fired on **two** journals (18:00, 19:00) and four
  unpushed commits. Per D-112 that outranks the decision tree, so no new TODO
  again — third consecutive cycle spent on the same strand.
- D-348 handed over node IDs for two of the six carried pins and described the
  other four as unconfirmed, having been unable to afford the diagnostic.
  Ran those two files directly rather than trusting the estimate.
- Repaired all six, then took one suite for the receipt.

## What worked / what failed

- **The four unconfirmed pins were confirmed in 7.21 seconds.** D-348 concluded
  the diagnostic was unaffordable from a four-file run its own 900s timeout
  killed. The two files that actually held the failures —
  `test_extremum_reading.py` + `test_guard_direction.py`, 41 tests — cost 7.21s
  together. The 318s D-348 measured belongs to `test_guard_reflexivity.py`
  alone, which was *in* the killed run and is why it died.
- **So D-348's arithmetic survives and its cost model does not.** The suite
  really is 1341s against a 35-min budget. But "an inheriting cycle cannot
  afford to diagnose" was generalised from one slow file to the whole suite,
  and it is the reason 19:00 stopped. The rule that replaces it: diagnose the
  named files, and never include the file already known to be slow.
- **Five of six repairs were pin bumps**; the sixth was not. `TTC_FAMILY` had
  to enter `exemption_control`'s controlled set, and the obvious target for the
  control does not work — `ttc_family_has_the_heavier_tail` returns a `bool`
  that **does not move** when the family is shrunk to one member (measured:
  the surviving `min(ttc)` still loses to `max(rest)`). A control pointed there
  would have passed while demonstrating nothing. Wrote a reader that does move
  — the count of tail-table columns the family admits.
- **That reader then walked into D-334's trap, which is the second finding.**
  Written set-shaped it grades `DIFFERENCE`/`COLLECTION`, making it a revocable
  collection that owes a hand-written `guard_direction.PROBES` fixture.
  `census_preempt` caught the tally half at the stage in ~2s (124 → 125) and
  read **CLEAN on all five censuses** with the fixture unwritten — correctly,
  since placement is not a population. That is the gap D-333/D-334 recorded
  twice, walked into by the first cycle to add a guard since.
- **The repair inverted my own first conclusion inside the cycle.** I had
  written that controlling a registry grows the masking screen (23 → 26) — a
  "third mode of entrant". Re-spelling the reader predicate-shaped
  (`is_ttc_family`, D-334's repair) drops it out of the pool entirely, owes no
  fixture, and leaves the screen at **25**. So whether controlling a registry
  grows the screen is a property of the *spelling of the control*, not of
  controlling. The cost is D-104's objection, unwaived: a repair that deletes
  the guard from the census reads as a disappearance rather than a payment.

## North-star delta

- **No planner movement. Third consecutive honest zero**, and all three were
  spent on verification machinery rather than representation.
- What moved: the strand is discharged and the branch is publishable, which
  unblocks the six queued commits behind it. The cost of *inheriting* a red
  receipt is now measured at ~8 min rather than believed to be a whole cycle.

## Key learnings

- **A timing number measured on one member is not the population's.** This is
  the same error `worst_tail_extension` (D-347) and `evidence_widths` (D-346)
  exist to prevent on the observable and scene axes — arriving on the
  suite-timing axis, where this package has no instrument and therefore reached
  for the most recent number to hand. That absence is the real gap; Q-167's
  node-ID rule is right but would not have caught this, since 19:00 *had* the
  file names and believed them unaffordable.
- **The pessimistic estimate was the expensive one.** D-348 spent its budget
  not running a 7s command. A wrong cost model does not merely mis-schedule
  work, it forecloses it — and the foreclosure is invisible, because the cycle
  that declines to measure has no reading to be wrong about.
- **`census_preempt` was clean for a third consecutive cycle while six pins
  were red**, all in its declared `UNCOVERED` gap. Three clean readings
  carrying no information about the receipt is now a pattern, not an anecdote.

## Recommended next 1–3 priorities

1. **Build the suite-timing instrument** (per-file cost recorded from the
   receipt run, so a cycle can price a diagnostic instead of guessing). Q-168.
2. Resolve Q-167 — add the node-ID line to the 4a template now that the strand
   is closed, and pair it with per-file timings from (1).
3. Carried twice now: apply the facing-end rule to the invisible class
   (`convoy` / `obstacle_crossing` have no facing end). Zero rollout, and it is
   the first item on this list that is actually about the north star.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/extremum_reading.py, eval/mppi_sandbox/exemption_control.py, eval/mppi_sandbox/scene_separability.py, eval/mppi_sandbox/tests/{test_extremum_reading,test_guard_direction,test_exemption_control,test_exemption_masking,test_guard_reflexivity}.py, docs/decisions.md, docs/deliberations.md
- TSV row appended: pending
