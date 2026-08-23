# A doc-only commit moved a census over the call graph — and the strand is why it cost a suite

- **Cycle**: 2026-08-24 05:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand repair (D-112 Step 0) — outranks the decision tree
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the Phase 1 Step 0 reading first. `cycle_artifacts stranded` returned
  rc=1: the 02:00 cycle's commit `e1a8d6f` (D-451) was finished on disk and had
  never reached origin. Clearing it is the cycle's first obligation.
- The probe added the part the strand check cannot see: the receipt for
  `e1a8d6f0` was **red**, 2 failures in `test_key_discrimination.py`. So the
  repair was not "push" — it was "find out why the suite is red, fix it, push".
- Diffed the narrow and wide key hit sets across `b256b51 → e1a8d6f` directly,
  rather than inferring the cause from the failure text.

## What worked / what failed

- **The cause is D-451's own prose.** `e1a8d6f` is `qual:doc-only` — two files
  in `docs/`, one journal file, **zero lines of code**. Its Decision (3) wrote
  ``calibrated_cruise(0.8) = 0.723`` and, sixty-odd characters later, the token
  `CRUISE_BY_VMAX`. The narrow key is "backticked call syntax with an argument,
  with a recorded return token within 160 chars", matched against
  `citation_audit.SCANNED_DOCS` — which *is* `docs/decisions.md`. The measured
  entrant set across that commit is exactly one name, both keys:

  | key | entrants | leavers |
  |---|---|---|
  | narrow | `calibrated_cruise` | — |
  | wide | `calibrated_cruise` | — |

  A commit that changed no code moved a census over the call graph, because the
  census reads the decision log and the decision log is written by the cycles
  the census grades.
- **It is the first non-LIVE entrant since D-332.** D-377 / D-381 / D-395 /
  D-404 each moved `hits` and `live` together (17/12 → 20/15) — "ordinary
  joins". This one moves `hits` alone: **(20, 15) → (21, 15)**, so it raises
  the narrow key's non-LIVE fraction on its own account and `discrimination`
  goes **0.152 → 0.173**. Against `SEPARATION_MARGIN` 0.25 the verdict is
  unmoved and no rung was touched — but D-342's finding was that this number
  moves from either end, and this is the first move since D-342 that comes from
  the end that actually licenses the verdict.
- **The strand is the reason it cost 24 minutes.** This is the *third* recorded
  instance of the same sequence, and the test file already narrates the first
  two (D-381, D-395): a cycle moves this census, ends stranded and ungraded,
  and the red sits latent until the next cycle that pays for a suite inherits
  it. An unpushed tree is an unmeasured one.
- **`census_preempt` again read clean without covering it.** All 6 censuses
  clean in ~2 s, and this one was in neither `CENSUSES` nor `UNCOVERED` — the
  D-317 shape the test file complains about at D-404 and which had been
  restated rather than fixed. Fixed this cycle: it is now an `UNCOVERED` entry,
  so the scope clause names it. That buys honesty about the gap, not coverage.

## North-star delta

- **No acceptance metric moved.** Zero sim, zero controller lines. This is
  verification-surface repair, and it is honest to call it that.
- What it does buy is the branch's push: thirteen cycles of P3 work (D-442 →
  D-452) were sitting behind a red suite caused by a doc paragraph.

## Key learnings

- **A `qual:doc-only` metric string is not a claim that the tree did not move.**
  D-043 says REPORT-phase writes are inside the verification surface; this is
  that principle with the code term set to zero. Any cycle writing a `D-NNN`
  entry that quotes a call with a result is editing a census.
- **The self-referential hazard is live for this entry too.** D-452 is itself
  prose in `SCANNED_DOCS`, so writing it carelessly would move the pin it just
  re-set. Written under the rule: no backticked call-with-argument syntax for
  any name not already in the pinned narrow set.
- **`census_preempt`'s silence still is not coverage** — but the failure mode
  is now one entry cheaper to notice, which is the only repair available
  without spending the full `consumer_reach` walk in a ~2 s budget.

## Recommended next 1–3 priorities

1. **Q-195 — pick the crossing scene's canonical speed** (unchanged from STATE;
   lean (b), rewrite the yaml comment to the measured transit window).
2. **Derive the `key_discrimination` census instead of listing it** — it has now
   gone red four times (D-381 / D-395 / D-404 / D-452) while unwatched.
3. **Merge the queue** — user-blocked, 43 days, cap 6.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: eval/mppi_sandbox/tests/test_key_discrimination.py, eval/mppi_sandbox/census_preempt.py, docs/decisions.md, journal/2026-08/24-05-a-doc-only-commit-moved-a-code-census.md
- TSV row appended: yes
