# The carry is not a strand — and STATE had already started saying so in prose

- **Cycle**: 2026-08-20 08:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #2 — fold the third reading of the strand question into one
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the D-112 readings at REVIEW. `stranded` returned **rc=1** naming
  `a028205` — the 07:00 cycle's post-receipt bookkeeping, which D-378 mandates
  be committed and **not pushed alone**. The printed repair was
  `push this branch`, which the push gate refuses (`NO_RECEIPT`) and D-378
  forbids in terms.
- Rather than build STATE #2 as written ("stop paying for a third reading"),
  used what the third reading exposed: D-379 taught the census to see commits
  but left **carry** and **strand** collapsed into one verdict.
- Added `strand_kind()` — a three-rule classifier over the commit census —
  plus `BOOKKEEPING_SURFACES` and `CARRY_MAX_AGE_MIN`. The `stranded`
  subcommand now raises on `STRAND` only; `CARRY` prints in full at rc=0.
- 6 new tests (84 → 90 in this file), each pinning one rule and one negative
  control.

## What worked / what failed

- The live reading now prints `CARRY — 1 commit(s) ahead`, names it "not a
  defect", and states the repair D-378 actually mandates: commit on top, one
  receipt licenses both, **do not push it alone**. rc=0.
- The bug was not hypothetical and was not going to stay quiet. It fires on
  the **healthy steady state of every cycle that follows a green push** —
  which from D-378 onward is every cycle. A gate that is red when nothing is
  wrong is a gate that gets muted.
- **It had already begun.** `STATE.md` for 07:00 carries a four-paragraph
  section (`⚠️ Carry this commit`) telling its successor to *expect rc=1 and
  not treat it as a defect*. That is the mute, written in prose a cycle later
  copies forward without re-deriving. Worth naming plainly: the previous cycle
  did the honest thing available to it — the defect is that prose was the only
  place to put it.
- `census_preempt` 5/5 CLEAN both before and after the edit. No new CLI entry
  point, so the 130-guard tally and `loop_reach`'s 89 claims are untouched.

## North-star delta

- **Zero, and stated as zero.** No cost term, no representation channel, no
  scenario metric moved. D-370 through D-380 are all guard machinery.
- This is the eleventh consecutive such cycle. The honest reading is that the
  branch is now servicing its own instrumentation faster than it services the
  north star, and no executor cycle can decide to stop.

## Key learnings

- **The unknown/clean collision has a third instance, one level up.** D-379
  fixed `None` vs `()` (unknown-state must not read as clean-state). The same
  shape reappeared immediately as *healthy*-state reading as *finding*-state.
  Two instances in two cycles suggests this is the characteristic defect of
  this census family, not a coincidence — worth checking the other censuses
  for it directly rather than waiting for each to fire.
- **An exemption without an expiry is a hole.** `CARRY_MAX_AGE_MIN = 120`
  exists because D-378's "a strand lives at most one cycle" was prose. The
  age bound is what stops D-380 from re-introducing, one level down, exactly
  the blindness it removes.
- **When a decision has to be re-explained in STATE every cycle, it belongs in
  code.** The four paragraphs 07:00 wrote are the diagnostic signal, not the
  fix.

## Recommended next 1–3 priorities

1. **branch-scope-decision** (user) — eleven cycles, zero north-star movement.
   Unchanged and now the only item that matters.
2. **kd-shape-fix** (P2) — still unpaid, still warned to move all 130 guards.
3. Audit the remaining censuses for the healthy-state/finding-state collision
   before each one fires on its own.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `docs/decisions.md`
- TSV row appended: pending
