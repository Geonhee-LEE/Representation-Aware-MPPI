# The two-cycle strand clears on one green receipt

- **Cycle**: 2026-08-14 07:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `STATE-strand` Clear the 05:00+06:00 strand (D-112 first obligation)
- **Phase**: P3
- **Status**: keep

## What I tried

- Took the D-112 reading first: rc=1, **two** stranded cycles (05:00, 06:00),
  both flagged "unwatched (Artifacts claims honest)" — neither was lying, both
  were simply unpublished.
- Took D-115's advisory in the same breath: the 06:00 run went **35m40 against
  a 35m budget** and still did not publish. That reading, not the decision tree,
  set this cycle's scope.
- Confirmed the strand needed nothing but a receipt: both cycles' TSV rows were
  already appended (05:07:44, 06:33:44), and PR #67 was already **open**, so no
  `gh pr create` and no missing-row repair were owed.
- Started `push_preflight record` as the **first long act** (elapsed 1m05,
  `SUITE_AFFORDABLE`), against the already-committed tree, then did REVIEW
  while it ran.

## What worked / what failed

- **The suite came back green: 2942 passed, 164 skipped, 1 xfailed in 565.65s
  across 14 shards.** The 06:00 cycle's four-pin census repair holds against the
  full suite, not just the three files it targeted.
- **Starting the suite before REVIEW is what made the cycle fit.** 06:00 spent
  its first ~10 min diagnosing and hit `SUITE_UNAFFORDABLE` by 11 minutes; the
  same suite here started at 1m05 and left 11m of slack at its end. Identical
  work, opposite outcome, and the only difference was ordering.
- **`check`'s inert-path tolerance is what allows that ordering.** The receipt
  is a claim about the worktree *now*, but `tree_match` ignores drift on paths
  no test can read — so this journal and the TSV row, both written after the
  run, do not stale the receipt. Reading that before ordering the writes is why
  the suite did not have to run twice.
- **I deliberately did not issue a D-NNN this cycle.** The learning below earns
  one, but `docs/decisions.md` is in `citation_audit.SCANNED_DOCS`: writing it
  invalidates the receipt under D-044 and buys a second 10-min suite plus a live
  risk of the census bill that has hit this branch three times in four days.
  Publishing a two-cycle strand outranks recording a decision about it.

## North-star delta

- **No movement on the planner.** Third consecutive repair-and-publish cycle;
  the standing `ProgressPriceCritic` claim (no supported cell at any tested
  weight at either temperature, D-250/D-253) is unchanged.
- **What moved is real anyway**: four cycles of finished P3 work — the
  arrival-scope re-grade (D-252), the D-243/D-244 voiding (D-253), and the
  census repair — went from disk-only to origin. Unpublished results are worth
  what unrun experiments are worth.
- The branch is now **green on a full-suite receipt taken on the pushed tree**,
  which is the strongest state it has been in for 32 days open.

## Key learnings

- **A strand's cost is measured in cycles, not in pushes.** 05:00 stranded
  because it was red; 06:00 stranded because diagnosing red ate the budget. The
  defect propagated forward by one cycle each time, and only an *ordering*
  change broke the chain — not more budget, not a better diagnosis.
- **D-112's repair recipe is still wrong in the same way 06:00 found.** It says
  clear a strand by "appending any missing TSV rows and pushing", which presumes
  soundness; the honest recipe is *record a receipt, then push, and expect the
  receipt to be the expensive part*. This is now twice-demonstrated and is the
  D-NNN the next cycle should issue.
- **Read the gate before ordering the writes.** Ten minutes of suite time were
  saved by one `grep` of `push_preflight.check` establishing that inert drift is
  tolerated. The gates on this branch are better documented than they are read.

## Recommended next 1–3 priorities

1. **Issue the D-NNN amending D-112's strand recipe** — "a strand is unverified
   work, not finished-but-unpublished; clear it with a receipt, not a push."
   Twice-demonstrated (05:00 red, 06:00 budget). Cheap now that the branch is
   published: it is a doc-only cycle with a suite to pay for it.
2. **Then STATE #1 unchanged**: mark D-243–D-246 superseded by D-253, using
   D-036's precedent (in-place rescope blockquote at the section head + amended
   `Status:` line), with the rescope-vs-retract split applied asymmetrically.
3. **Resolve Q-146** — `admissible` clause 2 reads `n_reached` where the scope
   needs `n_arrived`; they differ 12 vs 7 at `1e5`.

## Artifacts
- PR: https://github.com/Geonhee-LEE/Representation-Aware-MPPI/pull/67 (already open; this push updates it)
- Files touched: journal/2026-08/14-07-the-two-cycle-strand-clears.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: yes
