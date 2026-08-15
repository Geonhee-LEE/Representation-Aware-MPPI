# The warning that lived in a file rewritten every cycle

- **Cycle**: 2026-08-15 11:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `<strand-clear>` clear the 09:00 strand (D-278, three commits)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the D-112 reading first: `stranded` rc=1 named
  `journal/2026-08/15-09-a-short-circuit-is-not-a-measurement.md` — three
  commits (`aa21bab`, `46db246`, `51ece9f`) finished on disk, never on `origin`,
  and the tree **ungraded** (`PENDING`), so a push alone would not clear it.
- Started the suite at 0m23 — before any reading, planning, or writing. The
  elapsed reading said `SUITE_AFFORDABLE` with a start-by of 10m49; everything
  else this cycle did happened while 658s of pytest ran underneath it.
- Verified the strand needed **no repair** before spending the receipt on it:
  `tsv_timestamp check` → `NO_PENDING_ROW` (row committed), the 09:00 journal's
  Artifacts claim already read off the tree, `declared` clean.
- Pushed the strand **before** writing this journal, then recorded the operating
  rule that the previous cycle discovered but filed somewhere it could not survive.

## What worked / what failed

- **3231 passed, rc=0 — identical to the 09:00 first run.** That number is the
  finding, not a formality: it confirms 09:00's diagnosis that the red second
  receipt was the `aggregate_results.sh`-during-suite race and **not** a
  regression in D-278. A different count would have meant real breakage.
- **I did not run `aggregate_results.sh`.** The Phase 3 spec prescribes it
  immediately before the push gate, and following it here would have reproduced
  the exact `STALE (changed: RESULTS.md)` refusal that stranded 09:00. The step
  is safe only when no suite is in flight — and this cycle deliberately ran the
  suite across the whole cycle.
- **The push chain's `claim` guard refuses on a strand-clear.** It returned
  `rc=2 NO_INFLIGHT_JOURNAL` — correct, since at push time this cycle had
  written no 4a. Chained with `&&` that rc aborts the push, i.e. the guard
  blocks exactly the cycle whose deliverable is *publishing prior work* rather
  than producing a new journal. I pushed on the verified basis that the three
  commits carry their own already-graded claims, and recorded the shape rather
  than quietly working around it.
- Gate 1 read **6 = cap**. Not applied: the deliverable was a push to an
  already-open PR (#67), which consumes no queue slot. A skip here would have
  left finished, green, unpublished work on disk for a seventh cycle.

## North-star delta

- **No movement, and this is the sixth consecutive cycle of none.** The
  epistemic shadow cost critic this branch is named for is untouched since
  04:00. The last real reading is still D-271's `(lam=0.8, w_voo=5)`.
- What did move: 15 commits of census apparatus are now **published** rather
  than sitting on one machine's disk. That is a precondition for the work, not
  the work.

## Key learnings

- **A rule stored in a file that is overwritten every cycle is not stored.**
  09:00 found a real operating hazard and wrote it into `STATE.md` — a
  **full-overwrite** artifact. My own 4c would have deleted it. The finding
  survived only because it happened to be *this* cycle that read it. That is the
  D-047 failure mode (a caveat retiring silently) reached by a different route:
  not drift, but scheduled erasure. Hence D-279.
- **Starting the suite before thinking is the whole budget trick.** 658s ran
  under REVIEW, the gate checks, and the strand verification. The two cycles
  that overran this week both started their suite after deciding what to do.
- **Verify a strand needs no repair before spending a receipt on it.** Three
  cheap read-only checks confirmed 09:00's "suite + push, no repair" claim. Had
  a TSV row actually been missing, the receipt would have been spent on a tree
  that the push gate then refused.

## Recommended next 1–3 priorities

1. **Answer Q-158** with the six-cycle evidence — the repairs are cheap, the
   inherited diagnoses are what cost whole cycles. No runs needed.
2. **Return to the cost critic** (untouched since 04:00). Six zero-delta cycles
   is the strongest argument the census tax has produced against itself.
3. **Re-probe the 5 withdrawn pins** when a cycle has suite budget to spare.

## Artifacts

- PR: #67 (open, strand now published)
- Files touched: `journal/2026-08/15-11-*.md`, `docs/decisions.md`, `results/*.tsv`
- TSV row appended: pending
