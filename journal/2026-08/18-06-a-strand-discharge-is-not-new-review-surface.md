# A strand discharge is not new review surface

- **Cycle**: 2026-08-18 06:00 KST
- **Branch**: `autoresearch/p3-epistemic-shadow-cost-critic`
- **TODO**: (none picked — gate 1 fired; strand repair only)
- **Phase**: P3
- **Status**: keep

## What I tried

- REVIEW step 0 returned `rc=1`: the 05:00 cycle's work — two commits
  (`ab7acb0` D-336 + `1fa7e5d` its TSV row) and
  `journal/2026-08/18-05-…md` — was finished on disk and had never reached
  `origin`, which still sat at `a77c705`. `cycle_wallclock review` agreed on the
  cause: that run had **16m37**, ample for a receipt, and still did not publish.
- Gate 1 then measured the PR queue at **6** — at cap. The two readings point
  opposite ways, so the cycle is exactly the collision D-112 anticipated: a
  strand I am obliged to clear, behind a gate that says stop.
- Resolved it by asking what the gate is *for*. It bounds **human review
  bandwidth**. This branch's PR (**#67**) is already open and already one of the
  6; pushing two finished commits onto it adds **zero** new review surface. So
  the discharge proceeds and the *new-work* half of the cycle does not — no new
  branch, no new PR, `EXECUTOR_SKIP reason=pr-queue-full count=6`.
- Recorded that reading as **D-337** so the next cycle to hit it does not have to
  re-derive it under a clock.

## What worked / what failed

- ✅ **The strand cleared cheaply.** Everything the repair needed was already
  committed — the journal inside `ab7acb0`, the TSV row as `1fa7e5d`. The only
  missing artifact was the grade: `push_preflight probe` read `UNMEASURED`, which
  is why the strand notice said "budget a suite run to clear, not just a push."
- ❌ **The 05:00 journal's 4a claim is permanently `pending`.** `cycle_artifacts
  claim` refuses with `NO_INFLIGHT_JOURNAL` — it fills the *in-flight* cycle's
  line, and 05:00 is not in flight. Per D-162 that is the intended shape:
  `pending` grades `UNPARSED`, no claim was made, nothing is owed. Worth stating
  plainly because a future cycle will see the line and reach for it.
- ⚠️ **The queue is the standing problem, not this cycle.** 6 open PRs, last
  merge **2026-07-12 — 37 days**. The deadlock-breaker's 72h escalation is not
  due (last sent 2026-08-16 02:17, ~52h ago), so this cycle stays silent by rule.

## North-star delta

- **No movement.** Zero new capability; this is pure discharge of the 05:00
  cycle's already-measured D-336 result. That result's own delta — the
  `OBSTACLE_SIDE_OBSERVABLES` class closure — was booked at 05:00 and is not
  re-claimed here.
- What the push *does* buy is that D-336 stops being invisible: it is now on a
  PR where CI grades it, rather than a finding held on one machine's disk.

## Key learnings

- **A gate that counts branches was asked a question about commits.** Gate 1's
  unit is the review queue, and the queue's unit is the PR. Every prior cycle hit
  the gate while wanting a *new* branch, so the two units never came apart and
  the distinction was never needed. The strand made them come apart, and reading
  the gate literally would have stranded finished work a second time.
- **`stranded` and `probe` answer different halves of one question.** `stranded`
  said work had not shipped; `probe` said the tree was never graded. Either alone
  under-describes the repair — a push without the suite would have satisfied the
  first check and pushed an ungraded tree past the second.

## Recommended next 1–3 priorities

- **Ask whether a reactive obstacle is a precondition for separability work** —
  unchanged from STATE #1, and D-336's class closure sharpens it: nothing on the
  obstacle side can carry seed variance while every obstacle is an open-loop yaml
  script.
- **Merge two of #68 / #67 / #66** — 37 days, cap reached. This is now the
  binding constraint on the executor, not any research question.
- **Prune the `risk`/`frozen_risk` duplicate** — 40/40 identical arm-seed pairs;
  the evidence cannot improve and the pair costs a registry slot per census.

## Artifacts

- PR: #67 (existing — this push adds commits, not a new PR)
- Files touched: `docs/decisions.md`, `journal/2026-08/18-06-*.md`, `results/p3-epistemic-shadow-cost-critic.tsv`
- TSV row appended: yes
