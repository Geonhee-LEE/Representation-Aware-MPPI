# D-043 mechanised — and the declared local-only set was an undercount

- **Cycle**: 2026-08-03 21:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: STATE #1 — re-run the fast half after the doc writes, every cycle
- **Phase**: P3
- **Status**: keep

## What I tried

- Took STATE item **#1**, the cheapest item on the list and the one the other 24
  depend on for record-keeping. Static, no sim.
- Rather than land D-043's rule as ~2 lines of prose, wrote it as an instrument:
  `eval/mppi_sandbox/tree_provenance.py` (stamp / verify / undeclared-drift) plus
  19 fast tests, and wired it into Phase 4 of the executor prompt as **4a-ter**.
- Reproduced D-043's exact defect shape on a throwaway repo: stamp, append prose
  to a doc, verify → the changed path is named back.

## What worked / what failed

- ✅ **The naive instrument was wrong, and finding out why was the cycle's
  content.** One fingerprint over the worktree goes red *every* cycle, because
  D-011 **requires** worktree drift. The surface has to split by **destination**
  (worktree = what the tests read; `HEAD` = what gets pushed), not by directory.
- 🔴 **D-011 declares 3 local-only files; the worktree diverges by 5.** `TODO.md`
  (`mirror_todos.sh`) and `research/feed.md` (`researcher.sh`) are the same
  full-overwrite class, no branch commits either, and neither is named anywhere
  in the 🚫 rule they obey. Not exempted — **unnoticed**. The "3 snapshot files"
  figure in the push rule has been an undercount for as long as both scripts
  have existed.
- 🔴 **Second finding, not fixed**: `citation_audit.SCANNED_MODULES` is a
  hand-written tuple, so this new module restating a banked magnitude would have
  been **unpoliced** — Q-056's hole, this time demonstrated by a freshly created
  file rather than argued. Resolved by not spelling the magnitude at all, which
  is cheaper than widening the policed surface.
- ✅ **The verification surface has an ordering.** `docs/` is scanned, so a
  `D-NNN` write is inside it; `results/*.tsv` is read by no test (checked, not
  assumed — the one hit is a prose mention). So the last write before push must
  be the TSV, or the re-taken count is again about a tree that stopped existing.
- Fast half: **407 passed** / 135 deselected / 1 xfailed (was 388) — and per the
  rule this cycle lands, that number was taken *after* every doc write.

## North-star delta

- **No avoidance or tracking number moved — twelfth consecutive instrument
  cycle.** Scenes able to contribute an avoidance number: 5, reportable: 4 —
  unchanged.
- What moved: every *future* reported pass count is now bindable to one tree by a
  command instead of by an executor's memory, and the local-only exemption list
  went from prose-with-a-hole to code-with-reasons. This is record-keeping, not
  capability — but D-043 showed the record was silently wrong, and a wrong record
  is worse than a thin one.

## Key learnings

- **A check whose default state is alarm has no default at all.** D-042's
  asymmetry lesson runs in both directions: an instrument that only ever clears
  work can't be trusted to clear it, and one that fires every cycle gets muted
  within a week. Both fail-opens; only the second looks safe while it happens.
- **Enumerating an exemption is how you discover it was never enumerated.** The
  5-vs-3 gap wasn't found by auditing D-011; it fell out of being forced to write
  the allow-list down to make the check not-always-red. Mechanising a prose rule
  is a way of *reading* the prose rule.
- **The fix for an unpoliced restatement can be to not restate.** Adding the new
  module to `SCANNED_MODULES` would have worked and would have grown the surface
  that needs hand-maintenance — the same surface whose hand-maintenance is the
  defect. Not creating the citation site is strictly cheaper.

## Recommended next 1–3 priorities

1. **Add `SCANNED_MODULES` auto-discovery** — glob `eval/mppi_sandbox/*.py`
   instead of the hand-written tuple, and let the registry go red on a new
   module that restates a magnitude. Closes Q-056's mechanism rather than
   dodging it (this cycle dodged it, deliberately and cheaply).
2. **Count distinct `(scenario, controller, seed, params)` tuples across the 30
   D-042 lower-bound sites** — Q-062's static half; prices the re-baseline bill
   in the unit the re-run actually consumes (sims, not sites).
3. **Reproduce the D-039 flip on a second scene**, with rungs drawn from that
   scene's own window (D-040) rather than from 1.6/0.1.

## Artifacts
- PR: #67 (already in the queue — this cycle added no review bandwidth)
- Files touched: `eval/mppi_sandbox/tree_provenance.py`, `eval/mppi_sandbox/tests/test_tree_provenance.py`, `scripts/prompts/auto_research.md`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
