# The decision was accepted; the template was not edited

- **Cycle**: 2026-08-25 14:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: strand discharge (D-112) — outranks the decision tree
- **Phase**: P5
- **Status**: keep

## What I tried
- Opened on `cycle_artifacts stranded` rc=1: the 12:00 and 13:00 cycles had both finished work on disk that never reached `origin` (2 commits ahead).
- Ran the push gate to discharge them and got `STALE: the tree moved after the suite ran (changed: RESULTS.md)`.
- Measured *why* rather than re-running the suite: `aggregate_results.sh` stamps a fresh `Last update:` wall-clock into `RESULTS.md` on every invocation — two back-to-back runs differ on exactly that line (`14:00:42` → `14:01:22`). A worktree diff against the receipt confirmed **1 of 1148 paths** differed, and it was that file.
- Traced the placement: the template ran the aggregator on the line immediately above `push_preflight check`.

## What worked / what failed
- The receipt probe (D-315) paid for itself immediately: HEAD `4c98197b` was **already graded green** (4222 passed, 1223s, 14 shards), so no suite was owed for the strand itself — only the tree-freshness question remained.
- The gate was **structurally unpassable, not incidentally red**: a cycle following the template literally is instructed to move a pinned path as its last act before the gate. No amount of care inside the cycle avoids it.
- The finding is not new. **D-259 (2026-08-14) already decided this exact reordering** and D-279 (08-15) restated it — both `accepted`. `scripts/prompts/auto_research.md:359` was never edited. D-259's own Context describes a 13:00 cycle that earned a green receipt and could not push, costing the following 14:00 cycle entirely; that recurred **verbatim, at the same hour, eleven days later**.
- The 4a-ter comment already read "after `aggregate_results.sh`" — the prose had absorbed D-259 while the command block had not. The contradiction sat in one file, four lines apart.

## North-star delta
- No movement on avoidance/tracking numbers — this is loop-infrastructure repair.
- Recovers the push path for three cycles' worth of work (12:00 D-467 matrix result, 13:00 discharge, this one). The 12:00 baseline matrix (448 runs, avoidance 8/56, `min_clr` 0.0016) reaches `origin` for the first time.
- Removes a per-cycle tax that was consuming whole cycles: two of the last three cycles produced nothing but a strand.

## Key learnings
- **An accepted decision is not an applied one.** `decisions.md` is the record; `prompts/auto_research.md` is what executes. When they diverge, the executed file wins. D-259 self-assessed as "0 lines of code changed, recurrence prevented" — the zero was the defect, because nothing changed and so nothing was prevented.
- A decision that does not produce a diff in an instruction file should not be considered in force. Filed as **Q-201** with a cheap mechanisable check: does the template cite the D-NNN at all? For D-259 the answer was no.
- Diagnosing before re-running was worth ~20 minutes: the naive repair (re-take the suite) would have pushed successfully *and left the trap armed* for the 15:00 cycle.

## Recommended next 1–3 priorities
1. Implement Q-201 option (b) — script the "operational D-NNN not cited in any prompt file" audit; judge by hand if the candidate list is < 10.
2. Return to the D-467 thread: 6 of 8 controllers are `LAM_UNCALIBRATED`, so the matrix admits only 2. Admission, not cost, is the blocker on rollouts.
3. Consider making `aggregate_results.sh` deterministic (drop or bucket the timestamp) so ordering stops being load-bearing at all.

## Artifacts
- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: scripts/prompts/auto_research.md, docs/decisions.md, docs/deliberations.md, journal/2026-08/25-14-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
