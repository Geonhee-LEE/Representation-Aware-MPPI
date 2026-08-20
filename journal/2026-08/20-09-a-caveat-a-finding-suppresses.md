# A caveat a finding suppresses

- **Cycle**: 2026-08-20 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `census-collision-audit` Audit remaining censuses for the D-380 collision
- **Phase**: P3
- **Status**: keep

## What I tried

- REVIEW's `stranded` came back rc=1: two commits (D-380 + a D-379 keep row)
  never reached origin, and the tree was **ungraded** — so the first obligation
  was a suite plus a push, not new work.
- Picked STATE's #1 (`census-collision-audit`) around it: check the four
  censuses `census_preempt` prints as uncovered for the healthy-state /
  finding-state collision D-380 fixed and D-379 fixed one level down.
- `cycle_wallclock elapsed` said the suite had to start by 10m49. The audit was
  cut to fit at that mark rather than at minute 34 — two of four censuses read,
  and the one real finding shipped.

## What worked / what failed

- **Two of the four check out.** `census_preempt`'s own pin readers return
  `None` (not `()`) when a pin is unreadable — D-379's fix, applied
  consistently. `tsv_timestamp` names `NO_PENDING_ROW` as its own verdict
  rather than folding it into a pass. An empty `extremum_reading` scan cannot
  read as clean, because `retired` would then contain all of `SITE_CLASSES`
  and fire loudly. `inert_surface pins` and `exemption_control.REGISTRIES`
  were not reached — the audit is **half done**, and that is a real omission,
  not a scoped-out one.
- **The instance found was in the auditing tool itself.** `census_preempt`'s
  `Not covered:` clause printed on the clean branch only. D-318 wrote that
  clause because D-317 paid 785 s for a check whose scope was narrower than it
  looked — and the cycle most likely to edit a census, the one reading
  `DRIFTED`, was the only one never told which four the pass skipped.
- The fix is 12 lines plus a test that asserts every `UNCOVERED` name on both
  verdicts. `consumer_reach_residue`'s own docstring already argued for this
  ("`uncovered()` exists precisely so a clean reading states its own scope") —
  the code just never extended it to the other branch.

## North-star delta

- **None. Twelfth consecutive cycle.** No MPPI cost term, no representation
  channel, no scenario metric moved. This was guard machinery about guard
  machinery, again, and saying so plainly is the only use left for the line.
- The strand is discharged: D-380's tree is graded and pushed rather than
  sitting finished-but-invisible on disk.

## Key learnings

- **A caveat that a finding suppresses is absent exactly when it is
  load-bearing.** The D-379 → D-380 → D-381 sequence is one defect at three
  levels: unknown vs clean, healthy vs finding, and now clean-verdict vs
  finding-verdict. Three instances in three cycles is a property of this
  census family, not luck.
- **The audit found its instance in the auditor.** Worth weighting: the next
  two censuses to check are the two this cycle did not reach, and the prior
  should now be that they *do* have the defect.
- `staged` returned `STAGED_MOVED` on a commit touching only
  `census_preempt.py` and its test — the D-207 price. It cost nothing here
  only because D-315's receipt-last ordering already puts every snapshot write
  ahead of the suite.

## Recommended next 1–3 priorities

1. **branch-scope-decision** (user) — twelve cycles, zero north-star movement.
   Unchanged, and now the only item that matters.
2. **census-collision-audit (remainder)** — `inert_surface pins` and
   `exemption_control.REGISTRIES`, the two this cycle did not reach.
3. **kd-shape-fix** (P2) — still unpaid, still warned to move all 130 guards.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/census_preempt.py`,
  `eval/mppi_sandbox/tests/test_census_preempt.py`, `docs/decisions.md`
- TSV row appended: pending
