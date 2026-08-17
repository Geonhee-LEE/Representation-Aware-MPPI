# The branch is the trunk — STATE said sixteen commits, the tree holds 840

- **Cycle**: 2026-08-17 12:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `3bec5d39-9c22` [meta] Decide whether this branch closes
- **Phase**: P5
- **Status**: keep

## What I tried

- Took the scoping call STATE named as the bottleneck: does this branch close and
  the `K` work continue on a fresh one?
- Measured the branch before deciding (D-186's discipline), and the measurement
  changed the deliverable: **840 commits, 656 files, +155,753 lines** against
  main, not the "sixteen commits" STATE carried.
- Re-derived the deadlock-breaker criteria rather than inheriting the prior
  cycles' conclusion: #23/#44 are build-path per D-009, #66/#68/#69 were never
  superseded — no closable PR, confirmed this cycle.
- Shipped `branch_debt` — a reading that grades a branch's review debt against
  the componentwise envelope of every diff `main` has actually absorbed.

## What worked / what failed

- **The threshold did not have to be invented.** `main` is squash-merged, so
  each first-parent commit is one accepted review. The envelope is 41 files
  (`4220969`) and +9,543 lines (`4ec669e`) — two different reviews, so the
  comparison is generous by construction and the branch still loses 16x on both
  axes.
- **The two-way question STATE asked has both doors shut.** A fresh branch makes
  the queue 7 (gate 1); closing #67 discards 36 days of the project's entire
  output and fails the deadlock-breaker's crit (b) anyway. That is the finding,
  not a preference.
- **The 50x error survived three cycles because no place in the loop cost a
  second to check it.** `git rev-list --count main..HEAD` was always in the same
  shell. Same shape as D-199 (`staged`) and D-315 (receipt probe): the fix is a
  standing place, not more care.
- Test file deliberately pins `UNDECIDABLE`'s reachability rather than the
  magnitude — pinning the magnitude would go red the day the branch merges,
  which is the reading working.

## North-star delta

- **No movement toward the north star, and this cycle is honest that it is
  infrastructure.** Zero sim runs, one scene, no A/B reading; `transfers_to_ab_scene`
  is still `False` and still blocked behind PR #68.
- What moved is the reliability of the *scoping* judgement the project keeps
  making about itself — the number that judgement rests on is now measured
  instead of remembered.

## Key learnings

- **A bottleneck stated in prose can be wrong by 50x and still read as
  actionable.** STATE's sentence was specific, confident, well-argued, and off
  by a factor of fifty. Specificity is not measurement.
- **Gate 1's "zero new review bandwidth" workaround has a compounding cost.** It
  was sound at commit 20; at commit 840 the deferred debt *is* the bottleneck.
  The workaround converts "cannot get review" into "make the unreviewable thing
  larger", one cycle at a time.
- **This is now a hard user-merge dependency**, not a scoping call the executor
  can make. Queue 6, zero closable PRs, last merge 2026-07-12.

## Recommended next 1–3 priorities

1. **User merges #67 (or a subset of it).** Nothing the executor can do reduces
   the debt; every further cycle enlarges it. This is the project's binding
   constraint, above every technical item.
2. **Place the 4a `claim` fill beside `tsv_timestamp check` in `CLAUDE.md`** —
   five consecutive `UNPARSED` journals now, and D-199 is the precedent for
   exactly this repair.
3. **Wire `branch_debt` into the Phase 1 REVIEW readings**, so the next STATE
   cannot type an adjective where a number belongs.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic)
- Files touched: `eval/mppi_sandbox/branch_debt.py`, `eval/mppi_sandbox/tests/test_branch_debt.py`, `docs/decisions.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
