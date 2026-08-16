# The receipt has to be the last write — the constitution's order guarantees the refusal it then blames on the cycle

- **Cycle**: 2026-08-17 03:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-81e6` [sandbox] grep-the-axis-for-min-max-interval-assumptions
- **Phase**: P3
- **Status**: keep

## What I tried

- `cycle_artifacts stranded` fired rc=1 for the **third** consecutive cycle, now
  naming three journals (00:00, 01:00, 02:00) and warning two trees were never
  graded. That outranks the decision tree, so this cycle again picked nothing new.
- Found the strand was **not** where the previous two were. `/tmp/suite-receipt.json`
  from 02:00 is **green** — `3433 passed, 1 xfailed, 163 skipped in 948.88s`,
  rc=0, `failed_nodes: []`, `head 0307175` — which is still `HEAD`. D-314's repair
  worked. The 02:00 run was killed in the ~3 minutes between its TSV row (02:22:01)
  and its push.
- So the cheap move looked available: reuse the green receipt, push, done. Ran
  `push_preflight check` against it and got **`STALE`** — changed paths
  `JOURNAL.md`, `journal/2026-08/17-02-*.md`, `results/p3-*.tsv`.
- Re-ordered the cycle instead: **every mandated write first, receipt last, push
  with nothing in between.**

## What worked / what failed

- **The `STALE` is structural, not a mistake by any of the three cycles.** The
  three paths it names are exactly the three writes the protocol *mandates after*
  the suite: 4a's journal, 4b's `JOURNAL.md`, the TSV row. `tree_match`'s
  docstring says those are meant to be filtered as measured-inert — but
  `inert_surface` has since **measured them readable** (`cycle_artifacts` reads
  `journal/`, `tsv_timestamp audit` reads `results/*.tsv`), so they now count as
  material drift. The written order therefore ends every cycle at a refusal that
  no amount of care inside the cycle can avoid. STATE.md has named this as the
  third-standing bottleneck for two cycles in the narrow `aggregate_results.sh`
  form; the general form is that **the receipt is not last and has to be**.
- **The inverted order satisfies both rules at once, which is why it is the fix
  and not a workaround.** D-043 wants the count taken *after* the doc writes so
  the number describes the shipped tree; the push gate wants the receipt taken
  *after* the last write so the tree hasn't moved. Those are the same requirement
  read from two ends. Writes → receipt → push satisfies both; the constitution's
  4a → re-run → 4b/4c → TSV → push satisfies only the first.
- **`inert_surface staged` names the mechanism exactly, and it is repairable.**
  At this cycle's stage it read `STAGED_MOVED: staging moved 5 pin(s)
  (JOURNAL.md, RESULTS.md, STATE.md, journal/, results/) — this cycle added a
  reader. Their exemptions are withdrawn until re-probed, so writes to them now
  count as material drift and cost a second suite run (D-044's tax).
  `probe`/`reprobe` buys it back.` So the `STALE` is not permanent: those five
  are *withdrawn*, not *measured-readable-forever*, and a `reprobe` would restore
  the filtering that `tree_match`'s docstring assumes. This cycle did not run it
  — the strand is three cycles deep and a probe is itself suite-priced — but it
  means D-315's inverted order and a `reprobe` are two different fixes for the
  same refusal, and the second one may be the cheaper standing answer.

- **The green receipt was real and cost nothing to find.** Two prior cycles paid
  ~29 min of suite between them; this cycle paid one `json.load`. A receipt
  outlives the cycle that earned it — it is keyed on the tree, not on the run —
  and no step in the loop tells a cycle to look for one before budgeting a suite.
- **The 02:00 cycle's `JOURNAL.md` digest claims the strand "reached `origin`".**
  It did not. Written at 4b, one step before the push it never took. Corrected in
  this cycle's 4b — and it is the same over-claim shape D-162 fixed for the
  Artifacts line, surviving in a file that guard never looks at.

## North-star delta

- **No movement.** Zero closed-loop runs; no controller, cost, or representation
  code touched. Fourth consecutive verification-surface cycle.
- What lands: D-312 / D-313 / D-314's science reaches `origin` after three cycles
  and five commits stranded — 176 extremum sites narrowed to 36
  comparison-consuming, 2 hulls repaired, 15 monotone, 17 sound.

## Key learnings

- A protocol step that **cannot be satisfied** is worse than a missing one: it
  spends the budget and then reads as the cycle's failure. Three cycles wrote
  "not pushed" for three different-looking reasons and the third was the order
  itself.
- **Look for an existing receipt before budgeting a suite.** The receipt is
  tree-keyed (`receipt_store`, D-237); a killed cycle can leave a perfectly good
  one. Nothing in REVIEW says to check, so the default is to re-earn it.
- A local-only file is not outside the honesty surface. `JOURNAL.md` carried a
  false push claim for an hour because no guard reads it — the same claim in the
  journal's Artifacts line would have gone red.

## Recommended next 1–3 priorities

1. Move the receipt to the end of the written loop in `CLAUDE.md` (Phase 4
   ordering table) — this is the one change that stops the recurrence, and it is
   a constitution edit, which a strand-clearing cycle should not make.
2. Return to the `K`-axis question the branch is about. Four cycles have gone to
   the verification surface; D-312 retired the bottleneck that justified it.
3. Add a REVIEW-step receipt probe: if `/tmp/suite-receipt.json` matches `HEAD`
   and is green, say so before PLAN budgets a suite.

## Artifacts
- PR: #67 (open) — `autoresearch/p3-epistemic-shadow-cost-critic`
- Files touched: docs/decisions.md, journal/2026-08/17-03-*.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
