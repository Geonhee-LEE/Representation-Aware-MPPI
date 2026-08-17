# The queue is not uniformly expensive — five of its six PRs are inside the review envelope

- **Cycle**: 2026-08-17 13:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: `gate-1` [meta] measure the queue's merge cost, not just its depth
- **Phase**: P5
- **Status**: keep

## What I tried

- Gate 1 fired at the cap again (queue=6, no merge since 2026-07-12 — 36 days).
  D-322 had already ruled both of STATE's doors shut, so instead of re-deriving
  that verdict I asked the question D-322 did **not** ask. It asked whether the
  queued PRs were *closable* (they are not — #23/#44 are build-path per D-009,
  #66/#68/#69 were never superseded). The bottleneck is a **merge**, so the
  useful question is whether they are *mergeable*.
- Measured all six queued branches two ways: `main...branch` (three-dot — what
  GitHub shows as the PR diff, i.e. what a human reviews) and `main..branch`
  (two-dot — tree-vs-tree, i.e. whether merging changes a given file at all).
- Probed the D-011 snapshot surface on every branch and checked `merge-tree`
  cleanliness for the two oldest.

## What worked / what failed

- **The queue's cost is bimodal, and nobody had measured it.** Five PRs are
  4–9 files / +98…+513. One is **659 files / +156,230** (#67). The measured
  envelope this repo has actually absorbed is 41 files / +9,543 — so five of six
  are comfortably *inside* it and only #67 is `BEYOND_PRECEDENT`. "The queue is
  full" and "the queue is expensive" turned out to be different statements.
- **I got two readings wrong before I got them right, both from instrument
  choice.** (1) A 15-PR `gh pr list` page did not contain #23/#44, and I read
  their absence as "these branches have no PR" — they are both **open**. The
  gate snippet was correct; my inference from a truncated page was not.
  (2) `main...branch` showed #23 modifying `STATE.md`/`JOURNAL.md`/`RESULTS.md`,
  which read as a live D-011 violation that would re-dirty `main` on merge. The
  two-dot diff says branch and `main` are **byte-identical** on all three: commit
  `a19328d` already reverted them, so the merge effect is nil. I built a worktree
  to strip files that did not need stripping.
- Both oldest branches merge cleanly (`git merge-tree --write-tree`). No strip,
  no rebase, no executor action is required to make them mergeable — they have
  been mergeable the whole time.

## North-star delta

- No movement on the robot. Zero sim runs, no controller or representation
  changed. This is a meta cycle and says so.
- The one thing that moved: the project's binding constraint now has **data**
  attached instead of an adjective. The previous STATE told the user "PR #67 is
  the bottleneck, decide how to cut it" — a request for a 656-file judgement.
  The actual cheapest unblock is merging any two of five small PRs, which drops
  the queue to 4 and restores the executor's ability to open branches.

## Key learnings

- **`a..b` and `a...b` answer different questions and the queue needed both.**
  Three-dot gives review cost (what the PR adds since the fork). Two-dot gives
  merge effect (whether the file differs at all today). Reading three-dot as
  merge effect manufactured a D-011 alarm; reading two-dot as review cost would
  have reported #23 as a 152-file/-9,326-line monster. Neither alone is the
  merge question.
- **Absence in a paginated query is not absence.** `gh pr list --limit 15` not
  containing #44 is a statement about the page, not about the PR. This is D-322's
  shape exactly — a number steered by, never measured — and it cost me two
  wrong turns in one cycle.
- **D-322's "the executor has run out of moves" was true and also too broad.**
  It had run out of moves that change the queue's *depth*. It had not run out of
  moves that change the queue's *legibility*, and that is the one the human
  actually needs, since only a human can merge.

## Recommended next 1–3 priorities

1. **`queue_debt` reading** — the standing-place repair (D-199/D-315/D-322
   precedent): a module that ranks open PRs by three-dot size against the
   self-derived envelope, so Phase 1 REVIEW reads a merge-order table instead of
   a depth count. Gate 1 currently reports 6/6 and stops; it should report
   "6/6, five of them inside the envelope."
2. **Place the 4a `claim` fill beside `tsv_timestamp check`** — five consecutive
   `UNPARSED` journals, D-199 is the precedent, costs no runs.
3. **Wire `branch_debt` into Phase 1 REVIEW readings** — direct follow-through
   on D-322.

## Artifacts

- PR: pending merge (autoresearch/p3-epistemic-shadow-cost-critic, #67)
- Files touched: journal/2026-08/17-13-queue-merge-cost-measured.md, docs/decisions.md, results/p3-epistemic-shadow-cost-critic.tsv
- TSV row appended: pending
