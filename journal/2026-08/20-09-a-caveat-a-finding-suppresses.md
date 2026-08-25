# A caveat a finding suppresses

- **Cycle**: 2026-08-20 09:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `census-collision-audit` Audit remaining censuses for the D-380 collision
- **Phase**: P3
- **Status**: in_progress

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
- **The suite came back red — and not on my change.** `test_key_discrimination`
  pinned the narrow key at `(17, 12)`; the tree reads `(18, 13)`. Measured on
  both sides: `8b2c9f9` reads 17/12, D-380's `9fb0bce` reads 18/13. **D-380
  moved the census and was never graded**, so the red sat latent on the
  stranded tree and this cycle inherited it. Pin re-pointed with the note; the
  verdict `NARROWED_NOT_SEPARATED` is unmoved.
- **Nothing was pushed.** The receipt is red (`3890 passed, 1 failed`), the
  push gate refuses, and at ~60 min the budget for a second 18-minute suite is
  gone. The repair is committed so the next cycle's suite grades a tree that
  should be green in one pass.

## North-star delta

- **None. Twelfth consecutive cycle.** No MPPI cost term, no representation
  channel, no scenario metric moved. This was guard machinery about guard
  machinery, again, and saying so plainly is the only use left for the line.
- The strand is **graded but not discharged** — it grew from 2 commits to 4.
  The grading is the real gain: it converted a latent red that had been sitting
  invisibly on an unpushed tree into a one-line repair.

## Key learnings

- **A caveat that a finding suppresses is absent exactly when it is
  load-bearing.** The D-379 → D-380 → D-381 sequence is one defect at three
  levels: unknown vs clean, healthy vs finding, and now clean-verdict vs
  finding-verdict. Three instances in three cycles is a property of this
  census family, not luck.
- **The audit found its instance in the auditor.** Worth weighting: the next
  two censuses to check are the two this cycle did not reach, and the prior
  should now be that they *do* have the defect.
- **An unpushed tree is an unmeasured tree, and that is the whole cost of a
  strand.** D-112's reading says "budget a suite run to clear, not just a
  push"; this cycle is the first to actually pay that and find out why. D-380
  broke a pin, and nothing could have told anyone until someone spent a suite.
- **`key_discrimination` is in neither `census_preempt.CENSUSES` nor its
  `UNCOVERED` list.** The ~2 s pre-empt pass could not have caught this *and
  did not admit it wasn't looking* — the exact defect `consumer_reach_residue`'s
  own docstring names (D-344), one census over. That is a sharper follow-up
  than the remaining half of the audit.
- `staged` returned `STAGED_MOVED` on a commit touching only
  `census_preempt.py` and its test — the D-207 price. It cost nothing here
  only because D-315's receipt-last ordering already puts every snapshot write
  ahead of the suite.

## Recommended next 1–3 priorities

1. **Clear the strand** (4 commits) with one suite — the repair is already
   committed, so this should be a single green pass and a push.
2. **census-preempt-coverage** (P1) — `key_discrimination` sits in neither of
   `census_preempt`'s two lists. Join it or scope it out loud; D-381 just paid
   an 18-minute suite for the omission that D-344 already described.
3. **branch-scope-decision** (user) — twelve cycles, zero north-star movement.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/census_preempt.py`,
  `eval/mppi_sandbox/tests/test_census_preempt.py`,
  `eval/mppi_sandbox/tests/test_key_discrimination.py`, `docs/decisions.md`
- TSV row appended: pending
- Receipt: **red** — `3890 passed, 164 skipped, 1 failed` in 1062 s,
  `results/receipts/c7fea95363795595.json`. Nothing pushed.
