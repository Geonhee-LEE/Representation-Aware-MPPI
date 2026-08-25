# The repair line said how much, not when — and the omission costs a suite

- **Cycle**: 2026-08-20 10:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand-discharge + D-382
- **Phase**: P3
- **Status**: keep

## What I tried

- REVIEW step 0 returned **rc=1**: two stranded cycles (08:00, 09:00), five
  commits ahead of origin, and `2 of these tree(s) were never graded — budget a
  suite run to clear, not just a push`. That outranks the decision tree, so the
  cycle's whole job was: grade this tree, push it.
- I read "budget a suite" as "start a suite" and started one at minute one,
  before any REPORT write. Then noticed it was a guaranteed `STALE` under D-315,
  killed it, and reordered to writes → commit → receipt → push.
- Fixed the line that misled me rather than only the cycle it misled:
  `strand_report()` now appends the deferral and its reason to the budget line.
- Pinned both halves in `test_cycle_artifacts.py` — that the clause names the
  deferral *and* `D-315`/`STALE`, that it follows the budget line it qualifies,
  and that it **vanishes on a graded strand** where no suite is owed.

## What worked / what failed

- **Failed, and it is the finding**: ~9 min of suite burned on a receipt that
  could not have been used. The reading is taken at REVIEW step 0 — minute one —
  and D-315 puts the receipt after every mandated REPORT write (4a `journal/`,
  4a-bis `docs/`, 4b/4c, the TSV row), all of which are inside the read surface.
  So the one moment the line is read is the one moment a suite must *not* start.
- **A second, self-inflicted failure worth recording**: I launched the first
  suite with `nohup … &` *inside* a `run_in_background` call. The wrapper exited
  0 immediately, I read that as the suite passing, and the orphan kept running —
  so a second suite raced it on the same `--out` path. Both had to be killed by
  PID. The exit code of a backgrounded backgrounding says nothing about the job.
- Worked: `census_preempt` 5/5 CLEAN either side of the edit; targeted
  `test_cycle_artifacts.py` 91 passed (up from 90) before the full suite.

## North-star delta

- **Zero — thirteenth consecutive cycle.** No MPPI cost term, no representation
  channel, no scenario metric moved. This is guard machinery about guard
  machinery, and D-382 is guard machinery about the *ordering* of guard
  machinery, which is one level worse.
- The honest defence is narrow: the fix is ~10 lines and returns a suite to
  every future ungraded-strand cycle. It does not make the branch worth running.

## Key learnings

- **An instruction read at a fixed moment must be true at that moment.** The
  budget line was correct about *cost* and silent about *timing*, and the moment
  it is read is precisely when acting on it is wrong. D-315 already knew the
  order; nothing carried that knowledge to the one reading that provokes the
  violation. A rule stated in the loop file is not stated where it is needed.
- **The D-315 ordering has now cost four cycles** (D-312/313/314 stranded, plus
  this one). Each paid it a different way, which is the signature of a rule
  living in prose rather than in the readings that trigger it.
- The strand is *still* the thing that keeps happening. Twelve cycles of guard
  work have not made pushing more reliable — they have made the reasons for not
  pushing better documented.

## Recommended next 1–3 priorities

1. **branch-scope-decision (user)** — thirteen cycles, zero north-star movement.
   Unchanged and now the only item that matters.
2. **census-preempt-coverage** — `key_discrimination` is in neither
   `census_preempt.CENSUSES` nor its `UNCOVERED` list (D-381 paid an 18-min
   suite for exactly this).
3. **Audit the remaining REVIEW-step readings for the same defect as D-382** —
   does any other minute-one reading print an instruction that D-315's ordering
   forbids at that minute?

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/cycle_artifacts.py`,
  `eval/mppi_sandbox/tests/test_cycle_artifacts.py`, `docs/decisions.md`,
  `journal/2026-08/20-10-the-repair-line-does-not-say-when.md`,
  `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
